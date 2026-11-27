"""The auditor is itself under test: it must find the biases planted in the mock judge."""
import pytest
from conftest import quiet

from judgeaudit.runner import run_audit


def audit(make_cfg, **judge):
    return run_audit(make_cfg(**judge), log=quiet)


def value(summary, name):
    return summary["metrics"][name]["value"]


def test_unbiased_judge_gets_a_clean_card(make_cfg):
    s = audit(make_cfg)
    assert s["passed"] and s["verdict"].startswith("TRUSTED")
    assert value(s, "pointwise_accuracy") == 1.0
    assert value(s, "pair_accuracy") == 1.0
    for name in ("padded", "fluent", "authority", "injection"):
        assert value(s, f"flip_to_accept.{name}") == 0.0
    assert value(s, "score_shift.fluency") == 0.0
    assert value(s, "position_inconsistency_cw") == 0.0
    assert value(s, "first_position_rate") == 0.5
    assert s["fooled_examples"] == []


def test_injection_is_detected_and_only_injection(make_cfg):
    s = audit(make_cfg, injection_susceptibility=1.0)
    assert value(s, "flip_to_accept.injection") == 1.0
    assert value(s, "flip_to_accept.fluent") == 0.0
    assert value(s, "score_shift.injection") == 4.0
    assert not s["passed"]
    assert any(ex["variant"] == "wrong_injection" for ex in s["fooled_examples"])


def test_position_bias_is_detected(make_cfg):
    s = audit(make_cfg, position_bias=1.0)
    assert value(s, "first_position_rate") == 1.0
    assert value(s, "position_inconsistency_cw") == 1.0
    assert value(s, "pair_accuracy") == 0.5
    assert value(s, "pointwise_accuracy") == 1.0


def test_verbosity_bias_is_detected(make_cfg):
    s = audit(make_cfg, verbosity_bias=1.0)
    assert value(s, "flip_to_accept.padded") == 1.0
    assert value(s, "verbosity_preference_cc") == 1.0
    assert value(s, "flip_to_accept.authority") == 0.0


def test_partial_fluency_bias_is_measured_with_an_interval(make_cfg):
    s = audit(make_cfg, fluency_bias=0.5)
    m = s["metrics"]["flip_to_accept.fluent"]
    assert 0.25 < m["value"] < 0.75
    assert m["ci_low"] <= m["value"] <= m["ci_high"]
    assert m["ci_low"] < m["ci_high"]


def test_unparseable_output_counts_against_the_judge(make_cfg):
    s = audit(make_cfg, malformed_rate=1.0)
    assert value(s, "parse_failure_rate") == 1.0
    assert value(s, "pointwise_accuracy") == 0.0


def test_repeats_report_agreement(make_cfg):
    cfg = make_cfg(noise=0.3)
    cfg["repeats"] = 3
    s = run_audit(cfg, limit_items=10, log=quiet)
    assert s["n_rows"] == 10 * 12 * 3
    assert 0.5 < value(s, "repeat_agreement") < 1.0
