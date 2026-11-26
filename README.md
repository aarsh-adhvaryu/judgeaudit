# judgeaudit

Audit an LLM-as-judge before you trust it. Point `judgeaudit` at a judge, run a
suite of test cases with known ground truth, and get a reliability card that says
when the judge's verdicts can be trusted and when they cannot.

A judge is software. It can prefer long answers, be swayed by fluent wrong ones,
follow instructions hidden in the text it is grading, or change its pick when two
answers swap places. `judgeaudit` measures each of these with a paired design:
two test cases differ in exactly one property while correctness stays fixed, so
any change in the verdict is bias by construction.

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q                                  # 29 tests, no GPU needed
judgeaudit run -c configs/smoke.yaml       # mock judge with planted biases
start runs\smoke\report.html
```

The smoke run uses a mock judge with biases planted on purpose, so its card
fails. Its numbers describe the mock and are not findings about any real model.

## Auditing a real local judge

1. Get a llama.cpp build for Windows with CUDA from the llama.cpp releases page,
   and a GGUF instruct model in the 7B to 14B range (4-bit fits in 12 GB VRAM).
2. Start the server (flag names can differ between builds; check `llama-server --help`):

   ```powershell
   .\llama-server.exe -m models\YOUR-MODEL.gguf -ngl 99 -c 8192 --parallel 4 --port 8080
   ```

3. Set `judge.label` in `configs/local_llamacpp.yaml` to the model and
   quantization you loaded. The label is part of the cache key.
4. Run:

   ```powershell
   judgeaudit run -c configs/local_llamacpp.yaml --dry-run   # count calls first
   judgeaudit run -c configs/local_llamacpp.yaml
   ```

Any OpenAI-compatible endpoint works (llama-server, Ollama, hosted providers):
change `base_url`, `model` and, for hosted APIs, `api_key_env`.

## Commands

| Command | What it does |
|---|---|
| `judgeaudit run -c CONFIG` | Run the audit and write the card to `runs/<run_name>/` |
| `... --dry-run` | Count judge calls and prompt tokens, call nothing |
| `... --split dev` / `--split heldout` | Tune prompts on `dev`, report on `heldout` |
| `... --limit-items N` | Only the first N base items |
| `... --gate` | Exit code 1 when a threshold fails, for CI |
| `judgeaudit report RUN_DIR [-c CONFIG]` | Rebuild the card, optionally with new thresholds |

Each run writes `report.html`, `report.md`, `summary.json`, `results.jsonl`
(every verdict) and `config.resolved.yaml`.

## What is measured

Each base question is expanded into 11 judge calls.

| Variant | What changes | Expected |
|---|---|---|
| `correct_terse` | nothing | correct |
| `correct_padded` | content-free politeness added | correct |
| `wrong_terse` | nothing | incorrect |
| `wrong_padded` | content-free politeness added | incorrect |
| `wrong_fluent` | wrong answer rewritten as a confident, detailed explanation | incorrect |
| `wrong_authority` | claim of expert verification appended | incorrect |
| `wrong_injection` | instruction to the grader appended | incorrect |
| `pair_cw_AB`, `pair_cw_BA` | correct-terse vs wrong-fluent, both orders | the correct one |
| `pair_cc_AB`, `pair_cc_BA` | correct vs the same answer padded, both orders | none (preference only) |

Headline metrics:

- **Accuracy** against ground truth, overall and per variant.
- **Flip to accept**: of the wrong answers the judge rejected, the share it
  accepted once padded, made fluent, given an authority claim, or given an injection.
- **Score shift**: the same comparison on the 1 to 5 score.
- **Position inconsistency**: pairs where swapping A and B changed the winner.
- **Verbosity preference**: share of picks for the padded answer when both are correct.
- **Parse failure rate** and, with `repeats > 1`, **repeat agreement**.

Metrics are computed per base item and averaged; 95% intervals come from a
bootstrap over items.

## How it is built

```
src/judgeaudit/
  tasks/        one module per task; each returns Case objects with ground truth
  judges/       mock judge (planted biases) and OpenAI-compatible judge
  prompts.py    versioned judge prompts (naive and hardened)
  cache.py      SQLite verdict cache, keyed on everything that can change a verdict
  runner.py     resumable, concurrent execution through the cache
  metrics.py    paired metrics, bootstrap intervals, threshold checks
  report.py     reliability card (HTML and Markdown)
suites/qa/      seed suite: 40 factual questions, split dev/heldout
configs/        one YAML file per experiment
tests/          the auditor is tested against judges with known planted biases
```

Design choices that matter for cost:

- **Verdict cache.** The key hashes the judge fingerprint (model, quantization
  label, decoding parameters, prompt version), the exact messages, the output
  schema and the repeat index. A re-run is free, a crashed run resumes, and a
  failed call is never cached.
- **Prefix reuse.** The static rubric is the system message and the variable
  answer comes last, so a server with prompt caching reuses the KV cache.
- **Constrained output.** A JSON schema keeps the verdict to a few tokens.

## Experiments planned

Each is a config file plus a run; the verdict cache keeps them cheap.

| Question | What changes between runs |
|---|---|
| Does quantization change the judge's biases? | Same model at FP16, Q8, Q4 |
| Does model size? | 4B vs 8B vs 14B judges |
| Does the decoding strategy? | Greedy vs temperature vs top-p, with `repeats` |
| What does prefix caching save? | `cache_prompt` on and off |
| Where does batching stop scaling? | `--parallel` and `concurrency` sweep |
| Does a hardened prompt help? | `prompt_style: naive` vs `hardened` |
| Does showing a reference fix it? | `reference: none` vs `given` |

## Adding a task

Write `src/judgeaudit/tasks/<name>.py` with a `build_cases(suite_path, reference)`
function that returns `Case` objects, and register it in `tasks/__init__.py`.
The runner, cache, metrics and report need no change as long as the variants keep
the same names. Planned: code (ground truth from executed unit tests) and
summarisation (ground truth from a planted factual error).

## Limitations

- The seed suite is small (40 items) and was drafted with AI assistance. Every
  item needs a human check before results from it are reported.
- Self-preference bias is not measured yet. It needs answers written by the
  judge model and by a different model.
- A passing card covers this suite only. It is evidence about these failure
  modes on this task, not a general guarantee.
