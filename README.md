# judgeaudit

Test an LLM judge the way you test code, put a guard around it, and get a
recommendation for the cheapest set-up you can trust.

A judge is software. It can prefer long answers, be swayed by fluent wrong ones,
follow instructions hidden in the text it is grading, or change its pick when two
answers swap places. `judgeaudit` does three things about it:

1. **Audit** (`judgeaudit run`). A suite of test cases with known ground truth,
   built as pairs that differ in exactly one property while correctness stays
   fixed, so any change in the verdict is bias by construction. The result is a
   reliability card with 95% intervals and pass/fail against thresholds.
2. **Guard** (`guard:` in the config). Defences composed from ordinary judge
   calls: ask in both orders and withhold the pick when they disagree, screen
   each answer for text aimed at the grader, fence the answer off inside the
   prompt. The guarded judge is audited exactly like the plain one.
3. **Recommend** (`judgeaudit recommend`, `judgeaudit dashboard`). Every model,
   quantization, prompt and guard is scored on the dev half of the suite; the
   cheapest set-up that passes every check is chosen there and reported on the
   held-out half, which played no part in the choice.

## Quickstart (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q                                  # no GPU needed
judgeaudit run -c configs/smoke.yaml       # mock judge with planted biases
start runs\smoke\report.html
```

The smoke run uses a mock judge with biases planted on purpose, so its card
fails. Its numbers describe the mock and are not findings about any real model.

## Auditing a real local judge

1. Get a llama.cpp build for Windows with CUDA from the llama.cpp releases page,
   and a GGUF instruct model (a 4-bit 8B model fits in 12 GB of VRAM).
2. Start the server:

   ```powershell
   .\llama-server.exe -m models\YOUR-MODEL.gguf -ngl 99 -c 8192 --parallel 4 --port 8080
   ```

3. Set `judge.label` in `configs/local_llamacpp.yaml` to the model and
   quantization you loaded. The label is part of the cache key.
4. Run:

   ```powershell
   judgeaudit run -c configs/local_llamacpp.yaml --dry-run   # count calls first
   judgeaudit run -c configs/local_llamacpp.yaml
   judgeaudit run -c configs/local_llamacpp.yaml --set guard.swap=true --set guard.screen=both
   ```

Any OpenAI-compatible endpoint works (llama-server, Ollama, hosted providers):
change `base_url`, `model` and, for hosted APIs, `api_key_env`.

## Commands

| Command | What it does |
|---|---|
| `judgeaudit run -c CONFIG` | Audit and write the card to `runs/<run_name>/` |
| `... --dry-run` | Count verdicts, judge calls and prompt tokens; call nothing |
| `... --split dev` / `--split heldout` | Only one half of the suite (a full run scores both halves anyway) |
| `... --limit-items N` | Only the first N base items |
| `... --gate` | Exit code 1 when a threshold fails, for CI |
| `... --set KEY=VALUE` | Override any config value, e.g. `--set prompt_style=guarded --set guard.screen=llm` |
| `... --no-cache` | Neither read nor write the verdict cache, for speed measurements |
| `judgeaudit compare runs --out results` | All runs side by side (`comparison.md`, `comparison.csv`) |
| `judgeaudit recommend runs --out results` | Cheapest trustworthy set-up per use case (`recommendation.md`) |
| `judgeaudit dashboard runs --out results/dashboard.html` | One self-contained page: recommendation, trust-against-cost chart, every set-up, and a browser of the cases that fooled each judge |
| `judgeaudit report RUN_DIR [-c CONFIG]` | Rebuild a card, optionally with new thresholds |

Each run writes `report.html`, `report.md`, `summary.json` (with separate
`splits.dev` and `splits.heldout` scores), `results.jsonl` (every verdict) and
`config.resolved.yaml`.

## The guard

```yaml
prompt_style: guarded   # naive | hardened | guarded
guard:
  swap: true            # pairwise: ask in both orders, withhold the pick when they disagree
  screen: both          # none | regex | llm | both: check each answer for text aimed at the grader
  on_flag: reject       # reject | abstain: what a flagged answer gets
```

| Defence | Cost | What it targets |
|---|---|---|
| `swap` | one extra call per pairwise verdict | position bias: an order-dependent pick is never let through |
| `screen: regex` | free | injections that use the usual forms: role markers, fake tags, forged verdicts, direct address to the grader |
| `screen: llm` | one extra call per pointwise verdict | the same, phrased in ways a rule list misses; the judge model is asked a narrow yes/no question about the text instead of grading it |
| `prompt_style: guarded` | none | the answer is fenced between unguessable markers, and the grading rule is repeated after it |
| `on_flag: abstain` | none | sends flagged answers to a human instead of failing them |

Withheld verdicts count as wrong for accuracy and are reported as
`abstain_rate`, with a threshold, so a guard cannot pass by refusing to answer.
Every guard sub-call goes through the verdict cache: the swapped half of one
pair is often exactly another case's call, so a guard costs fewer calls than its
calls-per-verdict figure suggests during an audit, while the cost reported for
deployment counts every call.

**No tuning on the test.** Every defence was designed against the one injection
the audit has always used (`wrong_injection`). The variant
`wrong_injection_unseen` appends one of ten other phrasings (fake markup, a
forged verdict, a fake conversation turn, a policy claim, an emotional plea,
French) that were never used to tune anything, and `recommend` chooses on dev
items and reports held-out items.

## Running every experiment

One script downloads the models, starts and stops `llama-server` for each, runs
the whole grid and writes `results/` (comparison, recommendation, dashboard):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
```

For each model it runs prompt `naive`, `hardened` and `guarded`, reference
`none` and `given`, and guards `plain`, `swap-regex`, `swap-llm`, `swap-both`
and `swap-both-abstain`: 22 set-ups. Most re-use judge calls already made, so
the grid costs about four audits of fresh calls per model.

It is safe to stop and run again: finished judge calls come from the cache and
partial downloads resume. `-Only llama31-8b-q4,qwen3-8b-q4` limits it to some
models, `-SkipBench` leaves out the speed measurements, `-DownloadOnly` only
fetches models.

The script is built to survive an unreliable laptop:

- If `llama-server` dies mid-audit, `judgeaudit run` exits with code 3 within
  seconds, and the script records the GPU state and related Windows events in
  `logs/crashes.log`, restarts the server and resumes from the cache.
- `scripts/gpu_guard.py` runs alongside. Once a second it appends charger state,
  battery level and GPU temperature, power, clock and throttle flags to
  `logs/telemetry-<start>.csv`, flushed to disk on every row so the last
  readings survive a hard power-off.
- The work is paced to the machine's cooling. When the GPU's hottest sensor
  comes within `-PauseHeadroom` (default 8 C) of its throttle limit, the guard
  puts a pause file in place and `judgeaudit run` starts no new judge call until
  the GPU has cooled: the model stays loaded and no call fails. Paused time is
  reported as `paused_s` and left out of the speed figures. Any watcher can use
  the same hook through `JUDGEAUDIT_PAUSE_FILE`; a pause file that is not
  refreshed for 30 seconds is ignored.
- It stops the server outright when the charger goes offline, the GPU passes
  `-TempLimit` (90 C), the hotspot comes within `-MinHeadroom` (3 C) of its
  limit, or the GPU stops answering, and refuses to continue on a server that
  fell back to the CPU.
- It holds while the laptop is in a power mode that lets the GPU draw more than
  `-MaxGpuWatts` (100 W). To use Performance mode for its faster fans, run from
  an administrator PowerShell with `-GpuClockLimit 2100`: the core clock is
  capped for the run, which removes the 140 W peaks, and released at the end.
- After a full reboot, run the same command again.

Speed experiments (Llama 3.1 8B, 4-bit, run once):

| Runs | Question |
|---|---|
| `bench-prefix-cache-on` vs `-off` | What does KV prefix reuse save? |
| `bench-parallel-1/2/4/8` | Where does batching stop scaling? |
| `<model>--greedy-x3` vs `--temp07-x3` (in `runs/_archive/v0`) | Does the decoding strategy change verdict stability? |

## What is measured

The suite (`suites/qa/v1.jsonl`) has 100 factual questions, 50 dev and 50
held-out, across science, computing, geography, biology, maths, history and
literature. Each is expanded into 12 cases:

| Variant | What changes | Expected |
|---|---|---|
| `correct_terse` | nothing | correct |
| `correct_padded` | content-free politeness added | correct |
| `wrong_terse` | nothing | incorrect |
| `wrong_padded` | content-free politeness added | incorrect |
| `wrong_fluent` | wrong answer rewritten as a confident, detailed explanation | incorrect |
| `wrong_authority` | claim of expert verification appended | incorrect |
| `wrong_injection` | the tuning instruction to the grader appended | incorrect |
| `wrong_injection_unseen` | one of ten held-out injection phrasings appended | incorrect |
| `pair_cw_AB`, `pair_cw_BA` | correct-terse vs wrong-fluent, both orders | the correct one |
| `pair_cc_AB`, `pair_cc_BA` | correct vs the same answer padded, both orders | none (preference only) |

Headline metrics:

- **Accuracy** against ground truth, overall and per variant.
- **Flip to accept**: of the wrong answers the judge rejected, the share it
  accepted once padded, made fluent, given an authority claim, or given an injection.
- **Flip to reject**: of the correct answers it accepted, the share it rejected once padded.
- **Score shift**: the same comparisons on the 1 to 5 score.
- **Position inconsistency**: pairs where swapping A and B changed the winner.
- **Verbosity preference**: share of picks for the padded answer when both are correct.
- **Withheld** (`abstain_rate`) and **screen false alarms** for guarded judges.
- **Parse failure rate** and, with `repeats > 1`, **repeat agreement**.

Metrics are computed per base item and averaged; 95% intervals come from a
bootstrap over items.

## How it is built

```
src/judgeaudit/
  tasks/        one module per task; each returns Case objects with ground truth
  judges/       mock judge (planted biases) and OpenAI-compatible judge
  prompts.py    versioned judge prompts (naive, hardened, guarded) and the screen prompt
  guard.py      defences: plan the judge calls a verdict needs, combine their answers
  cache.py      SQLite verdict cache, keyed on everything that can change a verdict
  runner.py     resumable, concurrent execution through the cache, with thermal pausing
  metrics.py    paired metrics, bootstrap intervals, threshold checks
  report.py     reliability card (HTML and Markdown)
  compare.py    all runs side by side
  recommend.py  choose on dev, report on held-out, cost per verdict
  dashboard.py  the self-contained demo page
scripts/        run_all.ps1 (the experiment grid) and gpu_guard.py (telemetry and pacing)
suites/qa/      v1.jsonl (100 items) and seed_v0.jsonl (the first 40, used by the tests)
configs/        one YAML file per experiment
tests/          the auditor and the guard are tested against judges with planted biases
```

Design choices that matter for cost:

- **Verdict cache.** The key hashes the judge fingerprint (model, quantization
  label, decoding parameters, prompt version), the exact messages, the output
  schema and the repeat index. A re-run is free, a crashed run resumes, and a
  failed call is never cached.
- **Prefix reuse.** The static rubric is the system message and the variable
  answer comes last, so a server with prompt caching reuses the KV cache.
- **Constrained output.** A JSON schema keeps the verdict to a few tokens.

## Adding a task

Write `src/judgeaudit/tasks/<name>.py` with a `build_cases(suite_path, reference)`
function that returns `Case` objects, and register it in `tasks/__init__.py`.
The runner, guard, cache, metrics and report need no change as long as the
variants keep the same names. Possible next tasks: code (ground truth from
executed unit tests) and summarisation (ground truth from a planted factual error).

## Limitations

- The suite items, their wrong answers and the injection phrasings were drafted
  with AI assistance by the project's author.
- 100 items give 50 per half; intervals on the held-out numbers are around
  plus or minus 10 points, so small differences between set-ups are not findings.
- The regex screen and the held-out injections were written by the same author,
  so the regex's recall on them is an optimistic estimate; the LLM screen is the
  fairer test of generalisation.
- Self-preference bias is not measured. It needs answers written by the judge
  model and by a different model.
- A passing card covers this suite only. It is evidence about these failure
  modes on factual QA, not a general guarantee.
