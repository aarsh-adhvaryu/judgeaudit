"""Judge served over an OpenAI-compatible chat API.

Works with llama.cpp's llama-server, Ollama, and hosted providers that expose
the same endpoint, so the audited judge can be swapped by changing a config.
"""
from __future__ import annotations

import os
import time

import httpx

from .base import JudgeError, JudgeRequest, JudgeResponse

_RETRYABLE = {408, 409, 425, 429, 500, 502, 503, 504}


class OpenAICompatJudge:
    def __init__(
        self,
        base_url: str,
        model: str = "local",
        label: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 48,
        seed: int | None = 0,
        response_format: str = "json_schema",
        api_key_env: str | None = None,
        extra_body: dict | None = None,
        timeout_s: float = 300.0,
        max_retries: int = 5,
        transport: httpx.BaseTransport | None = None,
    ):
        if response_format not in ("json_schema", "json_object", "none"):
            raise ValueError("response_format must be json_schema, json_object or none")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.label = label or model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.seed = seed
        self.response_format = response_format
        self.extra_body = dict(extra_body or {})
        self.max_retries = max_retries
        headers = {}
        if api_key_env:
            key = os.environ.get(api_key_env)
            if not key:
                raise JudgeError(f"environment variable {api_key_env} is not set")
            headers["Authorization"] = f"Bearer {key}"
        self._client = httpx.Client(timeout=timeout_s, headers=headers, transport=transport)
        self._sleep = time.sleep

    def fingerprint(self) -> dict:
        # base_url is deliberately absent: the same model on another port is the same judge.
        return {
            "kind": "openai_compat",
            "model": self.model,
            "label": self.label,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "seed": self.seed,
            "response_format": self.response_format,
            "extra_body": self.extra_body,
        }

    def _body(self, request: JudgeRequest) -> dict:
        body = {
            "model": self.model,
            "messages": request.messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.seed is not None:
            body["seed"] = self.seed + request.repeat
        if self.response_format == "json_schema":
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "verdict", "strict": True, "schema": request.schema},
            }
        elif self.response_format == "json_object":
            body["response_format"] = {"type": "json_object"}
        body.update(self.extra_body)
        return body

    def judge(self, request: JudgeRequest) -> JudgeResponse:
        url = f"{self.base_url}/chat/completions"
        body = self._body(request)
        last_error = "no attempt made"
        for attempt in range(self.max_retries + 1):
            start = time.perf_counter()
            try:
                response = self._client.post(url, json=body)
            except httpx.TransportError as exc:
                last_error = f"{type(exc).__name__}: {exc}"
            else:
                latency = time.perf_counter() - start
                if response.status_code == 200:
                    return self._parse(response.json(), latency)
                last_error = f"HTTP {response.status_code}: {response.text[:300]}"
                if response.status_code not in _RETRYABLE:
                    break
                retry_after = response.headers.get("retry-after")
                if retry_after:
                    try:
                        self._sleep(min(float(retry_after), 60.0))
                        continue
                    except ValueError:
                        pass
            if attempt < self.max_retries:
                self._sleep(min(2.0**attempt, 30.0))
        raise JudgeError(f"judge request failed: {last_error}")

    @staticmethod
    def _parse(data: dict, latency: float) -> JudgeResponse:
        try:
            text = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise JudgeError(f"unexpected response shape: {str(data)[:300]}") from exc
        usage = data.get("usage") or {}
        timings = data.get("timings")
        return JudgeResponse(
            text=text,
            latency_s=latency,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            timings=timings if isinstance(timings, dict) else None,
        )
