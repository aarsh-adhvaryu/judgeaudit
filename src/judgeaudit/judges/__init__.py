from __future__ import annotations

from .base import Judge, JudgeError, JudgeRequest, JudgeResponse
from .mock import MockJudge
from .openai_compat import OpenAICompatJudge

_KINDS = {"mock": MockJudge, "openai_compat": OpenAICompatJudge}


def build_judge(cfg: dict) -> Judge:
    options = dict(cfg)
    kind = options.pop("kind", None)
    if kind not in _KINDS:
        raise ValueError(f"judge.kind must be one of {sorted(_KINDS)}, got {kind!r}")
    return _KINDS[kind](**options)


__all__ = [
    "Judge",
    "JudgeError",
    "JudgeRequest",
    "JudgeResponse",
    "MockJudge",
    "OpenAICompatJudge",
    "build_judge",
]
