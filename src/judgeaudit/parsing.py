"""Turn a judge's raw text into a verdict. Returns None when it cannot be parsed."""
from __future__ import annotations

import json
import re

_OBJECT = re.compile(r"\{.*?\}", re.DOTALL)


def _load(text: str) -> dict | None:
    candidates = [text.strip()] + _OBJECT.findall(text)
    for chunk in candidates:
        try:
            value = json.loads(chunk)
        except (ValueError, TypeError):
            continue
        if isinstance(value, dict):
            return value
    return None


def parse_verdict(text: str, mode: str) -> dict | None:
    data = _load(text or "")
    if data is None:
        return None
    if mode == "pointwise":
        verdict = str(data.get("verdict", "")).strip().lower()
        if verdict not in ("correct", "incorrect"):
            return None
        score = data.get("score")
        try:
            score = int(score)
        except (TypeError, ValueError):
            score = None
        if score is not None and not 1 <= score <= 5:
            score = None
        return {"verdict": verdict, "score": score}
    winner = str(data.get("winner", "")).strip().upper()
    if winner not in ("A", "B"):
        return None
    return {"winner": winner}
