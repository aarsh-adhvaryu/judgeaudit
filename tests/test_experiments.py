import csv
import time

import pytest
import yaml
from conftest import quiet

from judgeaudit.cli import main
from judgeaudit.config import apply_overrides, load_config
from judgeaudit.judges import MockJudge
from judgeaudit.runner import run_audit


def test_set_overrides_nested_values_and_parses_types():
    cfg = apply_overrides(
        {"judge": {"kind": "mock"}},
        ["judge.temperature=0.7", "judge.extra_body.cache_prompt=false", "prompt_style=naive",
         "reference=none", "repeats=3", "judge.label=llama31-8b-q4_k_m"],
    )
    assert cfg["judge"]["temperature"] == 0.7
    assert cfg["judge"]["extra_body"] == {"cache_prompt": False}
    assert cfg["prompt_style"] == "naive" and cfg["reference"] == "none" and cfg["repeats"] == 3
    assert cfg["judge"]["label"] == "llama31-8b-q4_k_m"
    with pytest.raises(ValueError):
        apply_overrides({}, ["no-equals-sign"])


def test_no_cache_always_calls_the_judge(make_cfg):
    cfg = make_cfg()
    judge = MockJudge(knowledge=1.0, noise=0.0)
    run_audit(cfg, judge=judge, use_cache=False, limit_items=5, log=quiet)
    second = run_audit(cfg, judge=judge, use_cache=False, limit_items=5, log=quiet)
    assert judge.calls == 120
    assert second["run"]["new_calls"] == 60 and second["run"]["use_cache"] is False
    cached = run_audit(cfg, judge=judge, limit_items=5, log=quiet)
    assert cached["run"]["new_calls"] == 60  # nothing was written to the cache above


def test_throughput_survives_a_fully_cached_rerun(make_cfg):
    cfg = make_cfg()
    cfg["meta"] = {"model_gb": 4.92}
    first = run_audit(cfg, log=quiet)
    again = run_audit(cfg, log=quiet)
    assert first["run"]["calls_per_s"] and first["run"]["meta"] == {"model_gb": 4.92}
    assert again["run"]["new_calls"] == 0
    assert again["run"]["calls_per_s"] == first["run"]["calls_per_s"]
    assert again["run"]["throughput_from_earlier_run"] is True


def test_cli_set_and_compare(tmp_path, make_cfg):
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(make_cfg()), encoding="utf-8")
    runs, out = tmp_path / "runs", tmp_path / "results"
    assert main(["run", "-c", str(path), "--run-name", "clean", "--set", "meta.model_gb=4.92"]) == 0
    assert main(["run", "-c", str(path), "--run-name", "injected",
                 "--set", "judge.injection_susceptibility=1.0", "--set", "prompt_style=naive"]) == 0
    assert main(["compare", str(runs), "--out", str(out)]) == 0
    assert "0 runs" in (out / "comparison.md").read_text(encoding="utf-8")  # mock judges are hidden by default
    assert main(["compare", str(runs), "--out", str(out), "--include-mock"]) == 0
    text = (out / "comparison.md").read_text(encoding="utf-8")
    assert "`clean`" in text and "`injected`" in text and "Injection accepted" in text
    rows = {r["run"]: r for r in csv.DictReader(open(out / "comparison.csv", encoding="utf-8"))}
    assert float(rows["injected"]["flip_to_accept.injection"]) == 1.0
    assert float(rows["clean"]["flip_to_accept.injection"]) == 0.0
    assert rows["injected"]["prompt_style"] == "naive" and rows["clean"]["meta.model_gb"] == "4.92"


def test_pause_file_holds_new_calls_and_paused_time_is_not_counted_as_speed(make_cfg, tmp_path, monkeypatch):
    import threading

    flag = tmp_path / "pause.flag"
    flag.write_text("GPU hotspot 5 C from its throttle limit", encoding="utf-8")
    monkeypatch.setenv("JUDGEAUDIT_PAUSE_FILE", str(flag))
    threading.Timer(0.6, flag.unlink).start()  # the watcher lets go after 0.6 s
    lines = []
    summary = run_audit(make_cfg(), judge=MockJudge(knowledge=1.0, noise=0.0), log=lines.append)
    run = summary["run"]
    assert run["failed_calls"] == 0 and run["new_calls"] == 480
    assert run["pauses"] == 1 and 0.3 < run["paused_s"] <= run["wall_s"]
    assert run["calls_per_s"] > run["new_calls"] / run["wall_s"]   # the pause is not charged to the judge
    assert any("paused: GPU hotspot" in line for line in lines) and any("resumed" in line for line in lines)


def test_a_stale_pause_file_is_ignored(make_cfg, tmp_path, monkeypatch):
    import os

    flag = tmp_path / "pause.flag"
    flag.write_text("left behind by a watcher that died", encoding="utf-8")
    old = time.time() - 120
    os.utime(flag, (old, old))
    monkeypatch.setenv("JUDGEAUDIT_PAUSE_FILE", str(flag))
    run = run_audit(make_cfg(), judge=MockJudge(knowledge=1.0, noise=0.0), log=quiet)["run"]
    assert run["new_calls"] == 480 and run["pauses"] == 0 and run["paused_s"] == 0


class DeadServerJudge(MockJudge):
    """Answers the first N calls, then the server is gone."""

    def __init__(self, alive_for, **kwargs):
        super().__init__(**kwargs)
        self.alive_for = alive_for
        self.dead = True

    def judge(self, request):
        from judgeaudit.judges import JudgeUnreachable

        if self.dead and self.calls >= self.alive_for:
            self.calls += 1
            time.sleep(0.02)  # a refused connection is not instant either
            raise JudgeUnreachable("judge server unreachable: ConnectError")
        return super().judge(request)


def test_a_dead_server_stops_the_run_early_and_the_next_run_resumes(make_cfg):
    cfg = make_cfg()
    judge = DeadServerJudge(alive_for=100, knowledge=1.0, noise=0.0)
    first = run_audit(cfg, judge=judge, log=quiet)
    assert first["run"]["aborted"] is True
    assert judge.calls < 300  # the breaker stopped it well short of all 480 calls
    assert first["run"]["new_calls"] >= 90
    assert first["run"]["new_calls"] + first["run"]["failed_calls"] == 480
    assert first["verdict"].startswith("INCOMPLETE") or "run incomplete" in first["verdict"]
    assert first["passed"] is False

    judge.dead = False  # server restarted
    second = run_audit(cfg, judge=judge, log=quiet)
    assert second["run"]["aborted"] is False and second["run"]["failed_calls"] == 0
    assert second["run"]["cached_calls"] == first["run"]["new_calls"]
    assert second["passed"] and second["n_rows"] == 480


def test_cli_exit_code_3_when_the_server_is_unreachable(tmp_path, make_cfg):
    cfg = make_cfg()
    cfg["judge"] = {"kind": "openai_compat", "base_url": "http://127.0.0.1:9/v1", "max_retries": 0, "timeout_s": 2}
    path = tmp_path / "cfg.yaml"
    path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    assert main(["run", "-c", str(path), "--limit-items", "3"]) == 3
