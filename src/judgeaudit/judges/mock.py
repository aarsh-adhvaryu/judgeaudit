"""A deterministic judge with planted, configurable biases.

It exists for two reasons: the pipeline can be tested without a GPU, and the
auditor itself can be validated, because a correct audit must recover the
biases that were planted here.

All randomness is derived from a hash of (seed, item, repeat), and the same
draw is shared by every variant of an item. Two variants of one item therefore
differ only by the planted bias, never by noise.
"""
from __future__ import annotations

import hashlib
import json
import time

from .base import JudgeRequest, JudgeResponse


def _clamp(p: float) -> float:
    return max(0.0, min(1.0, p))


class MockJudge:
    def __init__(
        self,
        knowledge: float = 0.95,
        noise: float = 0.03,
        verbosity_bias: float = 0.0,
        fluency_bias: float = 0.0,
        authority_bias: float = 0.0,
        injection_susceptibility: float = 0.0,
        position_bias: float = 0.0,
        malformed_rate: float = 0.0,
        latency_ms: float = 0.0,
        seed: int = 0,
    ):
        self.knowledge = knowledge
        self.noise = noise
        self.verbosity_bias = verbosity_bias
        self.fluency_bias = fluency_bias
        self.authority_bias = authority_bias
        self.injection_susceptibility = injection_susceptibility
        self.position_bias = position_bias
        self.malformed_rate = malformed_rate
        self.latency_ms = latency_ms
        self.seed = seed
        self.calls = 0

    def fingerprint(self) -> dict:
        return {
            "kind": "mock",
            "knowledge": self.knowledge,
            "noise": self.noise,
            "verbosity_bias": self.verbosity_bias,
            "fluency_bias": self.fluency_bias,
            "authority_bias": self.authority_bias,
            "injection_susceptibility": self.injection_susceptibility,
            "position_bias": self.position_bias,
            "malformed_rate": self.malformed_rate,
            "seed": self.seed,
        }

    def _u(self, item_id: str, repeat: int, salt: str) -> float:
        digest = hashlib.sha256(f"{self.seed}|{item_id}|{repeat}|{salt}".encode()).digest()
        return int.from_bytes(digest[:8], "big") / 2**64

    def judge(self, request: JudgeRequest) -> JudgeResponse:
        self.calls += 1
        start = time.perf_counter()
        if self.latency_ms:
            time.sleep(self.latency_ms / 1000)
        case, repeat = request.case, request.repeat
        if self._u(case.case_id, repeat, "malformed") < self.malformed_rate:
            text = "I think this one is probably fine."
        elif request.mode == "pointwise":
            text = json.dumps(self._pointwise(case, repeat))
        else:
            text = json.dumps(self._pairwise(case, repeat))
        prompt_chars = sum(len(m["content"]) for m in request.messages)
        return JudgeResponse(
            text=text,
            latency_s=time.perf_counter() - start,
            prompt_tokens=prompt_chars // 4,
            completion_tokens=max(1, len(text) // 4),
        )

    def _pointwise(self, case, repeat: int) -> dict:
        truth = case.expected == "correct"
        knows = self._u(case.item_id, repeat, "know") < self.knowledge
        believes_correct = truth if knows else not truth
        p = 1.0 - self.noise if believes_correct else self.noise
        variant = case.variant
        if "padded" in variant:
            p += self.verbosity_bias
        if "fluent" in variant:
            p += self.fluency_bias
        if "authority" in variant:
            p += self.authority_bias
        if "injection" in variant:
            p = max(p, self.injection_susceptibility)
        p = _clamp(p)
        accept = self._u(case.item_id, repeat, "verdict") < p
        if accept:
            return {"verdict": "correct", "score": 5 if p > 0.8 else 4}
        return {"verdict": "incorrect", "score": 1 if p < 0.2 else 2}

    def _pairwise(self, case, repeat: int) -> dict:
        if self._u(case.item_id, repeat, "position") < self.position_bias:
            return {"winner": "A"}
        other = {"A": "B", "B": "A"}
        if case.expected in other:
            # the wrong side of a correct-vs-wrong pair is the fluent one
            p = _clamp(self.knowledge - self.fluency_bias)
            pick_correct = self._u(case.item_id, repeat, "pair") < p
            return {"winner": case.expected if pick_correct else other[case.expected]}
        padded = case.meta.get("padded_side", "B")
        p = _clamp(0.5 + self.verbosity_bias / 2)
        pick_padded = self._u(case.item_id, repeat, "pair_cc") < p
        return {"winner": padded if pick_padded else other[padded]}
