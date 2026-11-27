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
    "guard": {},  # defences around the judge, see guard.py
    "meta": {},  # free-form notes recorded with the run (model size, VRAM, ...); never part of the cache key
}


def load_config(path: str | Path, overrides: list[str] | None = None) -> dict:
    with open(path, encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: config must be a mapping")
    return normalise(apply_overrides(raw, overrides or []))


def apply_overrides(raw: dict, pairs: list[str]) -> dict:
    """Apply `key.path=value` overrides, e.g. judge.temperature=0.7. Values are parsed as YAML."""
    cfg = copy.deepcopy(raw)
    for pair in pairs or []:
        key, sep, text = pair.partition("=")
        if not sep or not key:
            raise ValueError(f"--set expects key=value, got {pair!r}")
        node = cfg
        parts = key.split(".")
        for part in parts[:-1]:
            if not isinstance(node.get(part), dict):
                node[part] = {}
            node = node[part]
        node[parts[-1]] = yaml.safe_load(text)
    return cfg


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
    cfg["meta"] = cfg.get("meta") or {}
    from .guard import normalise_guard

    cfg["guard"] = normalise_guard(cfg.get("guard"))
    return cfg
