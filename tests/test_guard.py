import json

import pytest

from judgeaudit import guard as guards
from judgeaudit.judges import MockJudge
from judgeaudit.runner import run_audit
from judgeaudit.tasks import load_cases
from judgeaudit.tasks.qa import INJECTION, UNSEEN_INJECTIONS

from conftest import SUITE, quiet


def test_every_item_gets_an_unseen_injection_and_all_phrasings_are_used():
    cases = [c for c in load_cases("qa", SUITE, "none") if c.variant == "wrong_injection_unseen"]
    assert len(cases) == 40
    used = {next(t for t in UNSEEN_INJECTIONS if c.answer.endswith(t)) for c in cases}
    assert used == set(UNSEEN_INJECTIONS)
    assert INJECTION not in UNSEEN_INJECTIONS


def test_regex_screen_catches_the_tuning_injection_and_spares_plain_and_padded_answers():
    assert guards.regex_screen("Sydney." + INJECTION)
    for case in load_cases("qa", SUITE, "none"):
        if case.mode == "pointwise" and case.expected == "correct":
            assert guards.regex_screen(case.answer) is None, case.case_id
        if case.variant in ("wrong_terse", "wrong_padded", "wrong_fluent"):
            assert guards.regex_screen(case.answer) is None, case.case_id


def test_swap_keeps_agreeing_picks_and_withholds_the_rest():
    pair = next(c for c in load_cases("qa", SUITE, "none") if c.variant == "pair_cw_AB")
    g = guards.normalise_guard({"swap": True})
    # the correct answer is A here and B once swapped: agreement
    assert guards.combine(pair, g, {"main": {"winner": "A"}, "swapped": {"winner": "B"}})["winner"] == "A"
    # same letter both times = the content choice flipped with the order
    out = guards.combine(pair, g, {"main": {"winner": "A"}, "swapped": {"winner": "A"}})
    assert out["winner"] is None and out["abstained"] is True


def test_unknown_guard_options_are_refused():
    with pytest.raises(ValueError):
        guards.normalise_guard({"swapp": True})
    with pytest.raises(ValueError):
        guards.normalise_guard({"screen": "magic"})


def test_swap_removes_planted_position_bias(make_cfg):
    plain = run_audit(make_cfg(position_bias=0.6), log=quiet)
    cfg = make_cfg(position_bias=0.6)
    cfg["guard"] = guards.normalise_guard({"swap": True})
    cfg["run_name"] = "guarded"
    guarded = run_audit(cfg, log=quiet)
    assert plain["metrics"]["position_inconsistency_cw"]["value"] > 0.3
    # the guard never lets an order-dependent pick through: it withholds instead
    assert guarded["metrics"]["position_inconsistency_cw"]["value"] == 0.0
    assert guarded["metrics"]["abstain_rate"]["value"] > 0.0
    # swapped halves are other cases' calls: no extra judge calls were needed
    assert guarded["run"]["new_calls"] == 0 and guarded["run"]["cached_calls"] == 480
    assert guarded["run"]["calls_per_verdict"] > 1


def test_llm_screen_with_reject_stops_planted_injection_and_counts_its_cost(make_cfg):
    cfg = make_cfg(injection_susceptibility=1.0, screen_recall=0.9, screen_false_alarm=0.0)
    plain = run_audit(dict(cfg, run_name="plain"), log=quiet)
    cfg["guard"] = guards.normalise_guard({"screen": "llm", "on_flag": "reject"})
    cfg["run_name"] = "screened"
    screened = run_audit(cfg, log=quiet)
    m = screened["metrics"]
    assert plain["metrics"]["flip_to_accept.injection"]["value"] == 1.0
    assert m["flip_to_accept.injection"]["value"] < 0.2
    assert m["flip_to_accept.injection_unseen"]["value"] < 0.2
    assert m["screen.flag_rate_correct"]["value"] == 0.0
    # one screen call per pointwise case (8 of 12 variants), the rest from cache
    assert screened["run"]["new_calls"] == 40 * 8
    assert screened["run"]["calls_per_verdict"] == pytest.approx(20 / 12, abs=1e-3)


def test_abstaining_screen_withholds_instead_of_rejecting(make_cfg):
    cfg = make_cfg(injection_susceptibility=1.0, screen_recall=1.0)
    cfg["guard"] = guards.normalise_guard({"screen": "regex", "on_flag": "abstain"})
    s = run_audit(cfg, log=quiet)
    rows = [json.loads(line) for line in open(f"{cfg['out_dir']}/{cfg['run_name']}/results.jsonl", encoding="utf-8")]
    seen = [r for r in rows if r["variant"] == "wrong_injection"]
    assert all(r["abstained"] and r["verdict"] is None and r["flag_reason"].startswith("regex:") for r in seen)
    assert s["metrics"]["flip_to_accept.injection"]["value"] == 0.0
    assert s["run"]["calls_per_verdict"] == 1  # the regex screen is free
