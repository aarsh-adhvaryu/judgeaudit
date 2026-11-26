from judgeaudit.cache import VerdictCache, make_key
from judgeaudit.parsing import parse_verdict


def test_parses_clean_and_wrapped_json():
    assert parse_verdict('{"verdict": "correct", "score": 5}', "pointwise") == {"verdict": "correct", "score": 5}
    wrapped = 'Sure!\n```json\n{"verdict": "Incorrect", "score": "2"}\n```'
    assert parse_verdict(wrapped, "pointwise") == {"verdict": "incorrect", "score": 2}
    assert parse_verdict('{"winner": "b"}', "pairwise") == {"winner": "B"}


def test_rejects_unusable_output():
    assert parse_verdict("I think it is right.", "pointwise") is None
    assert parse_verdict('{"verdict": "maybe"}', "pointwise") is None
    assert parse_verdict('{"winner": "C"}', "pairwise") is None
    assert parse_verdict("", "pairwise") is None
    assert parse_verdict('{"verdict": "correct", "score": 9}', "pointwise") == {"verdict": "correct", "score": None}


def test_cache_roundtrip_and_persistence(tmp_path):
    path = tmp_path / "c.sqlite"
    cache = VerdictCache(path)
    assert cache.get("k") is None
    cache.put("k", {"text": "x", "latency_s": 0.1})
    assert cache.get("k") == {"text": "x", "latency_s": 0.1}
    cache.close()
    assert VerdictCache(path).get("k")["text"] == "x"


def test_key_changes_with_anything_that_can_change_a_verdict():
    messages = [{"role": "user", "content": "q"}]
    base = make_key({"model": "m", "label": "q4"}, messages, {}, 0)
    assert base == make_key({"label": "q4", "model": "m"}, messages, {}, 0)
    assert base != make_key({"model": "m", "label": "q8"}, messages, {}, 0)
    assert base != make_key({"model": "m", "label": "q4"}, messages, {}, 1)
    assert base != make_key({"model": "m", "label": "q4"}, [{"role": "user", "content": "q2"}], {}, 0)
