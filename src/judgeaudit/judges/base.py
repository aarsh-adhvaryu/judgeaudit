"""The judge interface. A judge is anything that turns a request into text."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..schema import Case


class JudgeError(RuntimeError):
    """The judge could not produce a response (after retries)."""


@dataclass
class JudgeRequest:
    messages: list[dict]
    mode: str
    schema: dict
    repeat: int
    # Only the mock judge may look at the case. A real judge sees `messages` alone.
    case: Case


@dataclass
class JudgeResponse:
    text: str
    latency_s: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    timings: dict | None = None  # server-side timings when the server reports them


class Judge(Protocol):
    def fingerprint(self) -> dict:
        """Everything about this judge that can change a verdict (goes in the cache key)."""

    def judge(self, request: JudgeRequest) -> JudgeResponse: ...
