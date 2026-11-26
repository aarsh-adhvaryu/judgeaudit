import json

import httpx
import pytest

from judgeaudit.judges import JudgeError, JudgeRequest, OpenAICompatJudge
from judgeaudit.prompts import POINTWISE_SCHEMA, build_messages
from judgeaudit.schema import Case

CASE = Case(
    case_id="x:correct_terse", item_id="x", task="qa", mode="pointwise", variant="correct_terse",
    split="dev", question="Q?", answer="A.", expected="correct",
)


def request(repeat=0):
    return JudgeRequest(messages=build_messages(CASE), mode="pointwise", schema=POINTWISE_SCHEMA, repeat=repeat, case=CASE)


def make_judge(handler, **kwargs):
    judge = OpenAICompatJudge("http://test/v1/", transport=httpx.MockTransport(handler), **kwargs)
    judge._sleep = lambda _s: None
    return judge


OK = {
    "choices": [{"message": {"content": '{"verdict": "correct", "score": 5}'}}],
    "usage": {"prompt_tokens": 120, "completion_tokens": 12},
    "timings": {"prompt_ms": 40.0, "predicted_ms": 90.0, "prompt_per_second": 3000.0, "predicted_per_second": 130.0},
}


def test_sends_schema_and_reads_usage_and_timings():
    seen = {}

    def handler(req):
        seen["url"] = str(req.url)
        seen["body"] = json.loads(req.content)
        return httpx.Response(200, json=OK)

    judge = make_judge(handler, label="m-q4", extra_body={"cache_prompt": True})
    response = judge.judge(request(repeat=2))
    assert seen["url"] == "http://test/v1/chat/completions"
    body = seen["body"]
    assert body["response_format"]["json_schema"]["schema"] == POINTWISE_SCHEMA
    assert body["cache_prompt"] is True and body["temperature"] == 0.0 and body["seed"] == 2
    assert body["messages"][0]["role"] == "system"
    assert response.prompt_tokens == 120 and response.timings["prompt_per_second"] == 3000.0
    assert judge.fingerprint()["label"] == "m-q4"


def test_retries_rate_limits_then_succeeds():
    calls = []

    def handler(_req):
        calls.append(1)
        if len(calls) < 3:
            return httpx.Response(429, text="slow down", headers={"retry-after": "1"})
        return httpx.Response(200, json=OK)

    assert make_judge(handler).judge(request()).text.startswith("{")
    assert len(calls) == 3


def test_gives_up_on_client_errors_without_retrying():
    calls = []

    def handler(_req):
        calls.append(1)
        return httpx.Response(400, text="bad request")

    with pytest.raises(JudgeError, match="HTTP 400"):
        make_judge(handler).judge(request())
    assert len(calls) == 1


def test_connection_errors_are_retried_then_reported():
    def handler(_req):
        raise httpx.ConnectError("refused")

    with pytest.raises(JudgeError, match="ConnectError"):
        make_judge(handler, max_retries=2).judge(request())


def test_other_response_formats():
    bodies = []

    def handler(req):
        bodies.append(json.loads(req.content))
        return httpx.Response(200, json=OK)

    make_judge(handler, response_format="json_object").judge(request())
    make_judge(handler, response_format="none", seed=None).judge(request())
    assert bodies[0]["response_format"] == {"type": "json_object"}
    assert "response_format" not in bodies[1] and "seed" not in bodies[1]
