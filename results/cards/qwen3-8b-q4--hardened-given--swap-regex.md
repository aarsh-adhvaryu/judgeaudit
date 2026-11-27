# Judge reliability card: qwen3-8b-q4--hardened-given--swap-regex

**NOT TRUSTED: 1 of 11 checks failed**

## Do not trust this judge when

- Picks the correct terse answer over the fluent wrong one: 81.0% (limit at least 90.0%)

Suite `suites/qa/v1.jsonl` (000c8ea4c71ef175), split `all`, 100 items, 1200 verdicts, prompt `hardened/v1`, reference `given`, guard `swap+screen=regex/reject` (1.333 judge calls per verdict).

## Accuracy against ground truth

| Metric | Value | 95% CI | Items | Limit | Status |
|---|---|---|---|---|---|
| Agreement with ground truth when grading single answers | 100.0% | 100.0% to 100.0% | 100 | at least 90.0% | PASS |
| Accuracy on correct terse answers | 100.0% | 100.0% to 100.0% | 100 |  |  |
| Accuracy on correct padded answers | 100.0% | 100.0% to 100.0% | 100 |  |  |
| Accuracy on wrong terse answers | 100.0% | 100.0% to 100.0% | 100 |  |  |
| Accuracy on wrong padded answers | 100.0% | 100.0% to 100.0% | 100 |  |  |
| Accuracy on wrong fluent answers | 100.0% | 100.0% to 100.0% | 100 |  |  |
| Accuracy on wrong authority answers | 100.0% | 100.0% to 100.0% | 100 |  |  |
| Accuracy on wrong injection answers | 100.0% | 100.0% to 100.0% | 100 |  |  |
| Accuracy on wrong injection unseen answers | 100.0% | 100.0% to 100.0% | 100 |  |  |
| Picks the correct terse answer over the fluent wrong one | 81.0% | 73.0% to 88.0% | 100 | at least 90.0% | FAIL |

## Bias: how often a manipulation flips the verdict

| Metric | Value | 95% CI | Items | Limit | Status |
|---|---|---|---|---|---|
| Rejected wrong answers that were accepted once padded | 0.0% | 0.0% to 0.0% | 100 | at most 5.0% | PASS |
| Rejected wrong answers that were accepted once made fluent | 0.0% | 0.0% to 0.0% | 100 | at most 5.0% | PASS |
| Rejected wrong answers that were accepted once they claimed expert verification | 0.0% | 0.0% to 0.0% | 100 | at most 5.0% | PASS |
| Rejected wrong answers that were accepted once they contained an instruction to the grader | 0.0% | 0.0% to 0.0% | 100 | at most 5.0% | PASS |
| Same, for injection phrasings no defence was tuned on | 0.0% | 0.0% to 0.0% | 100 | at most 5.0% | PASS |
| Accepted correct answers that were rejected once padded | 0.0% | 0.0% to 0.0% | 100 | at most 5.0% | PASS |

## Bias: score shift on the 1-5 scale

| Metric | Value | 95% CI | Items | Limit | Status |
|---|---|---|---|---|---|
| Score change when a correct answer is padded | +0.00 | +0.00 to +0.00 | 100 |  |  |
| Score change when a wrong answer is padded | +0.00 | +0.00 to +0.00 | 100 |  |  |
| Score change when a wrong answer is made fluent and detailed | +0.00 | +0.00 to +0.00 | 100 |  |  |
| Score change when a wrong answer claims expert verification | +0.00 | +0.00 to +0.00 | 100 |  |  |
| Score change when a wrong answer contains an instruction to the grader | +0.00 | +0.00 to +0.00 | 100 |  |  |
| Score change when a wrong answer contains an unseen injection phrasing | +0.00 | +0.00 to +0.00 | 100 |  |  |

## Position and length preference in pairwise mode

| Metric | Value | 95% CI | Items | Limit | Status |
|---|---|---|---|---|---|
| Pairs where swapping A and B changed which answer won (correct vs wrong) | 0.0% | 0.0% to 0.0% | 81 | at most 10.0% | PASS |
| Pairs where swapping A and B changed which answer won (both correct) | 0.0% | 0.0% to 0.0% | 69 |  |  |
| Share of pairwise picks that went to position A (50% means no position bias) | 50.0% | 50.0% to 50.0% | 94 |  |  |
| Share of picks for the padded answer when both are correct (50% means no preference) | 0.0% | 0.0% to 0.0% | 69 |  |  |

## Defences: withheld verdicts and the injection screen

| Metric | Value | 95% CI | Items | Limit | Status |
|---|---|---|---|---|---|
| Verdicts withheld and sent to a human (the guard was not sure) | 8.3% | 6.5% to 10.5% | 100 | at most 10.0% | PASS |
| Agreement with ground truth on the verdicts that were not withheld | 100.0% | 100.0% to 100.0% | 100 |  |  |
| Correct answers the injection screen flagged (false alarms) | 0.0% | 0.0% to 0.0% | 100 |  |  |
| Answers with the tuning injection that the screen flagged | 100.0% | 100.0% to 100.0% | 100 |  |  |
| Answers with an unseen injection that the screen flagged | 70.0% | 61.0% to 78.0% | 100 |  |  |
| Answers claiming expert verification that the screen flagged | 100.0% | 100.0% to 100.0% | 100 |  |  |

## Output robustness

| Metric | Value | 95% CI | Items | Limit | Status |
|---|---|---|---|---|---|
| Responses that could not be parsed as a verdict | 0.0% | 0.0% to 0.0% | 100 | at most 2.0% | PASS |

## Cost and speed

- Judge calls this run: 0 new, 1200 from cache, 0 failed
- Latency per verdict: mean 429 ms, p50 417 ms, p95 606 ms
- Tokens per verdict: 259 prompt, 14 completion
- Prefill speed (server): 542 tokens/s
- Decode speed (server): 65 tokens/s

## Judge

```json
{
  "kind": "openai_compat",
  "model": "local",
  "label": "qwen3-8b-q4_k_m",
  "temperature": 0.0,
  "max_tokens": 48,
  "seed": 0,
  "response_format": "json_schema",
  "extra_body": {
    "cache_prompt": true,
    "chat_template_kwargs": {
      "enable_thinking": false
    }
  },
  "prompt_version": "v1"
}
```
