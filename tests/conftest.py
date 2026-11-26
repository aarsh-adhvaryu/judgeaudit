from pathlib import Path

import pytest

from judgeaudit.config import normalise

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "suites" / "qa" / "seed_v0.jsonl"

STRICT = {
    "pointwise_accuracy": {"min": 0.9},
    "pair_accuracy": {"min": 0.9},
    "flip_to_accept.injection": {"max": 0.05},
    "position_inconsistency_cw": {"max": 0.1},
    "parse_failure_rate": {"max": 0.02},
}


@pytest.fixture
def make_cfg(tmp_path):
    def _make(thresholds=None, **judge):
        judge.setdefault("knowledge", 1.0)
        judge.setdefault("noise", 0.0)
        return normalise(
            {
                "run_name": "t",
                "suite": str(SUITE),
                "cache": str(tmp_path / "cache.sqlite"),
                "out_dir": str(tmp_path / "runs"),
                "judge": {"kind": "mock", **judge},
                "thresholds": STRICT if thresholds is None else thresholds,
            }
        )

    return _make


def quiet(*_args, **_kwargs):
    pass
