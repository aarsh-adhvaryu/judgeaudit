import pytest

from judgeaudit.metrics import compute_summary, trivial_baselines
from judgeaudit.runner import run_audit
from judgeaudit.tasks import load_cases

from conftest import SUITE, quiet


def _rows(verdict_for):
    rows = []
    for c in load_cases("qa", SUITE, "none"):
        row = dict(case_id=c.case_id, item_id=c.item_id, mode=c.mode, variant=c.variant, split=c.split,
                   expected=c.expected, meta=c.meta, repeat=0, parsed_ok=True, error=None,
                   question=c.question, answer=c.answer, answer_a=c.answer_a, answer_b=c.answer_b)
        if c.mode == "pointwise":
            row.update(verdict=verdict_for(c), score=None)
        else:
            row.update(winner="A")
        rows.append(row)
    return rows


def test_always_incorrect_scores_high_raw_accuracy_but_half_balanced_accuracy():
    rows = _rows(lambda c: "incorrect")
    s = compute_summary(rows, {}, {"repeats": 1})
    share_wrong = 7 / 9  # 7 of the 9 single-answer variants per question are wrong answers
    assert s["metrics"]["pointwise_accuracy"]["value"] == pytest.approx(share_wrong)
    assert s["metrics"]["balanced_accuracy"]["value"] == pytest.approx(0.5)
    assert s["metrics"]["accuracy_on_correct"]["value"] == 0.0
    assert s["baselines"]["always_incorrect"]["pointwise_accuracy"] == pytest.approx(share_wrong)
    assert trivial_baselines(rows)["always_correct"]["balanced_accuracy"] == 0.5


def test_a_perfect_judge_scores_full_balanced_accuracy(make_cfg):
    s = run_audit(make_cfg(), log=quiet)
    assert s["metrics"]["balanced_accuracy"]["value"] == 1.0
    assert s["splits"]["heldout"]["metrics"]["balanced_accuracy"]["value"] == 1.0


def test_report_command_rescores_saved_runs_with_new_thresholds(make_cfg, tmp_path):
    from judgeaudit.cli import main
    import json, yaml

    cfg = make_cfg(thresholds={"pointwise_accuracy": {"min": 0.5}})
    run_audit(cfg, log=quiet)
    run_dir = f"{cfg['out_dir']}/{cfg['run_name']}"
    new = tmp_path / "new.yaml"
    new.write_text(yaml.safe_dump({"suite": "x", "judge": {"kind": "mock"},
                                   "thresholds": {"balanced_accuracy": {"min": 0.9}}}), encoding="utf-8")
    assert main(["report", run_dir, "-c", str(new)]) == 0
    s = json.loads(open(f"{run_dir}/summary.json", encoding="utf-8").read())
    assert [c["metric"] for c in s["checks"]] == ["balanced_accuracy"] and s["splits"]["dev"]["checks"]
