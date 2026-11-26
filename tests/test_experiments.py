import csv

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
    assert judge.calls == 110
    assert second["run"]["new_calls"] == 55 and second["run"]["use_cache"] is False
    cached = run_audit(cfg, judge=judge, limit_items=5, log=quiet)
    assert cached["run"]["new_calls"] == 55  # nothing was written to the cache above


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
