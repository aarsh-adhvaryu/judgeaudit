import json
from pathlib import Path

from conftest import quiet

from judgeaudit.judges import JudgeError, MockJudge
from judgeaudit.runner import run_audit


def test_second_run_is_served_entirely_from_cache(make_cfg):
    cfg = make_cfg()
    judge = MockJudge(knowledge=1.0, noise=0.0)
    first = run_audit(cfg, judge=judge, log=quiet)
    assert judge.calls == 480 and first["run"]["new_calls"] == 480
    second = run_audit(cfg, judge=judge, log=quiet)
    assert judge.calls == 480
    assert second["run"]["new_calls"] == 0 and second["run"]["cached_calls"] == 480
    assert second["metrics"] == first["metrics"]


def test_changing_the_judge_misses_the_cache(make_cfg):
    cfg = make_cfg()
    run_audit(cfg, judge=MockJudge(knowledge=1.0, noise=0.0), log=quiet)
    other = MockJudge(knowledge=1.0, noise=0.0, seed=7)
    run_audit(cfg, judge=other, log=quiet)
    assert other.calls == 480


def test_outputs_are_written(make_cfg):
    cfg = make_cfg(injection_susceptibility=1.0)
    run_audit(cfg, log=quiet)
    out = Path(cfg["out_dir"]) / "t"
    for name in ("results.jsonl", "summary.json", "report.md", "report.html", "config.resolved.yaml"):
        assert (out / name).stat().st_size > 0
    rows = [json.loads(line) for line in (out / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 480
    assert "NOT TRUSTED" in (out / "report.md").read_text(encoding="utf-8")
    assert "Do not trust this judge when" in (out / "report.html").read_text(encoding="utf-8")


def test_dry_run_calls_nothing(make_cfg):
    judge = MockJudge()
    result = run_audit(make_cfg(), judge=judge, dry_run=True, log=quiet)
    assert result == {"dry_run": True, "n_verdicts": 480, "n_calls": 480, "n_pending": 480}
    assert judge.calls == 0


def test_split_and_limit(make_cfg):
    s = run_audit(make_cfg(), split="heldout", limit_items=5, log=quiet)
    assert s["n_items"] == 5 and s["n_rows"] == 60


class FlakyJudge(MockJudge):
    """Fails every call for one item, to prove a failed call is not cached."""

    broken = True

    def judge(self, request):
        if self.broken and request.case.item_id == "qa001":
            raise JudgeError("server down")
        return super().judge(request)


def test_failed_calls_are_retried_on_the_next_run(make_cfg):
    cfg = make_cfg()
    judge = FlakyJudge(knowledge=1.0, noise=0.0)
    first = run_audit(cfg, judge=judge, log=quiet)
    assert first["run"]["failed_calls"] == 12 and first["n_items"] == 39
    assert first["verdict"].startswith("INCOMPLETE") and not first["passed"]
    judge.broken = False
    second = run_audit(cfg, judge=judge, log=quiet)
    assert second["run"]["new_calls"] == 12 and second["run"]["failed_calls"] == 0
    assert second["n_items"] == 40
    assert second["passed"] and second["verdict"].startswith("TRUSTED")


class DownJudge(MockJudge):
    """A judge whose server is not running."""

    def judge(self, request):
        raise JudgeError("connection refused")


def test_a_judge_that_is_down_never_gets_a_trusted_verdict(make_cfg):
    summary = run_audit(make_cfg(), judge=DownJudge(), log=quiet)
    assert summary["run"]["failed_calls"] == 480 and summary["n_rows"] == 0
    assert summary["passed"] is False
    assert summary["verdict"].startswith("INCOMPLETE")
    assert summary["unevaluated"]
    out = Path(make_cfg()["out_dir"])
    report = (out / "t" / "report.md").read_text(encoding="utf-8")
    assert "Incomplete run" in report and "480 judge calls failed" in report
