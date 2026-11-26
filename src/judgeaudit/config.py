from __future__ import annotations

import copy
from pathlib import Path

import yaml

DEFAULTS = {
    "run_name": "run",
    "task": "qa",
    "reference": "none",
    "prompt_style": "hardened",
    "repeats": 1,
    "concurrency": 4,
    "cache": ".cache/verdicts.sqlite",
    "out_dir": "runs",
    "bootstrap_seed": 0,
    "thresholds": {},
}


def load_config(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: config must be a mapping")
    return normalise(raw)


def normalise(raw: dict) -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    cfg.update(copy.deepcopy(raw))
    for key in ("suite", "judge"):
        if key not in cfg:
            raise ValueError(f"config is missing required key {key!r}")
    if not isinstance(cfg["judge"], dict) or "kind" not in cfg["judge"]:
        raise ValueError("config.judge must be a mapping with a 'kind'")
    if int(cfg["repeats"]) < 1 or int(cfg["concurrency"]) < 1:
        raise ValueError("repeats and concurrency must be at least 1")
    cfg["thresholds"] = cfg.get("thresholds") or {}
    return cfg
