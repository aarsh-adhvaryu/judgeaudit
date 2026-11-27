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

## Results (27 November 2026)

Five local judges (Llama 3.1 8B at 4 and 8 bit, Llama 3.2 3B at 4 bit, Qwen3
8B at 4 and 8 bit) on one RTX 5070 Ti Laptop GPU, 44 set-ups each: 220 audits,
about 52,000 judge calls, none failed. Set-ups were chosen on the 50 dev items
and are reported on the 50 held-out items. Full tables: `results/recommendation.md`,
`results/comparison.md`, and `results/dashboard.html` to explore them.

**With a reference answer, there is a set-up to trust.** Llama 3.1 8B 4-bit,
hardened prompt, swap and regex screen passed every check on held-out items:
99.3% accuracy, 0% of injected wrong answers accepted (tuning, unseen and fresh
phrasings alike), 0.6% of verdicts withheld, 10.3 verdicts/s at 1.3 judge calls
per verdict. Llama 3.1 8B 8-bit with the `guarded_v2` prompt and no guard also
passed, at one call per verdict but 8.7 verdicts/s.

**Without a reference answer, nothing passes.** Llama rejects 19 to 52% of
correct answers once they are politely padded; Qwen accepts 14 to 20% of padded
wrong ones. No defence here fixes either, so this case needs a human.

| Finding | Evidence (held-out) |
|---|---|
| Plain 8B judges follow injected instructions | 100% of injected wrong answers accepted, every 8B model, with or without a reference |
| A free rule-based screen plus the judge stops the known forms | 0% accepted with `swap-regex`; regex recall 100% on the tuning phrasing, 80% on unseen ones, no false alarms |
| Rules do not generalise to new phrasings | regex recall on the fresh phrasings: 0%. They were mostly stopped by the judge itself (0 to 7% accepted even unguarded) |
| The LLM screen, round 1, was worse and dearer | 2 calls per verdict, 18 to 20% recall on unseen phrasings, 32 to 45% false alarms on Llama |
| Round-2 tuning on dev fixed what dev showed | screen false alarms 30 to 46% to 0%; `guarded` prompt over-rejection of padded correct answers 94 to 100% to 4 to 8% (Llama, with reference) |
| Asking in both orders removes position bias | position flips 8 to 22% to 0%, at 2 to 17% of verdicts withheld |
| Withholding flagged answers is the wrong policy here | 25 to 50% of verdicts withheld with `on_flag: abstain` |
| Biases are model-specific | Llama punishes padding, Qwen rewards it; Qwen's injection resistance from the guarded prompt is much weaker than Llama's |
| Quantization moves biases, not accuracy | Llama 8B: padded correct rejected 52% at 4-bit vs 20% at 8-bit (no reference); accuracy within 1 point |
| Decoding barely matters | repeat agreement 99.7% greedy, 99.8% at temperature 0.7 |
| Prefix cache and batching | 7.3 to 11.3 verdicts/s with prefix reuse; 5.8, 7.9, 10.9, 13.3 verdicts/s at 1, 2, 4, 8 slots |

## Run it

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aarsh-adhvaryu/judgeaudit/blob/main/notebooks/colab_quickstart.ipynb)

Pick the path that matches your machine. All of them end with the same three
files in `results/`: `recommendation.md`, `comparison.md` and `dashboard.html`.

| Path | Needs | Time | What you get |
|---|---|---|---|
| A. No GPU | Python 3.10+ | 2 min | The whole pipeline against two mock judges with planted biases |
| B. Google Colab | A Google account | 30 to 50 min | One real judge (Llama 3.1 8B, 4-bit), 8 set-ups, on a free T4 |
| C. Linux with an NVIDIA GPU | CUDA toolkit, CMake, about 10 GB VRAM | 20 min to several hours | Any or all of the 5 judges, 8 or 44 set-ups each |
| D. Windows with an NVIDIA GPU | PowerShell | 1 to 2 hours | The full published experiment, with laptop power and heat protection |

Times for B and C are estimates for a T4 or a laptop GPU; a fresh machine has
no verdict cache, so every judge call is made once.

### A. No GPU

```bash
git clone https://github.com/aarsh-adhvaryu/judgeaudit.git
cd judgeaudit
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q                            # 61 tests
python scripts/run_grid.py --mock --quick
```

Open `results-mock/dashboard.html` in a browser. The mock judges' numbers
describe the planted biases, not any real model; this path checks the install
and shows what every output looks like.

### B. Google Colab

Click the badge above, or open `notebooks/colab_quickstart.ipynb` in Colab, set
Runtime > Change runtime type > T4 GPU, and run the cells in order. The notebook
installs judgeaudit, builds `llama-server` with CUDA, downloads the model, runs
the quick grid, and shows the recommendation and the dashboard inline. Set
`LIMIT_ITEMS = 20` in the run cell for a 5 to 10 minute demo.

### C. Linux with an NVIDIA GPU

Build `llama-server` with CUDA (the published results used llama.cpp `b12752`):

```bash
git clone --depth 1 --branch b12752 https://github.com/ggml-org/llama.cpp
cmake -S llama.cpp -B llama.cpp/build -DGGML_CUDA=ON -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build llama.cpp/build --config Release -j 8 --target llama-server
```

Add `-DCMAKE_CUDA_ARCHITECTURES=89` (your GPU's compute capability without the
dot, from `nvidia-smi --query-gpu=compute_cap --format=csv`) to compile only for
your card, which is much faster. Then, from the judgeaudit folder:

```bash
# one model, 8 set-ups
python scripts/run_grid.py --server llama.cpp/build/bin/llama-server --models llama31-8b-q4 --quick

# the full published grid: 5 models x 44 set-ups, plus the speed measurements
python scripts/run_grid.py --server llama.cpp/build/bin/llama-server --bench
```

Models (`--models`, comma-separated): `llama31-8b-q4`, `llama32-3b-q4`,
`llama31-8b-q8`, `qwen3-8b-q4`, `qwen3-8b-q8`. They are downloaded from Hugging
Face into `models/` (2 to 9 GB each; about 30 GB for all five). The 8-bit models
need about 10 GB of VRAM. Stop with Ctrl+C at any time; running the same
command again resumes from the verdict cache.

### D. Windows with an NVIDIA GPU

Install the CUDA build of llama.cpp for Windows from the
[llama.cpp releases](https://github.com/ggml-org/llama.cpp/releases) (the
`bin-win-cuda` zip and the matching `cudart` zip, unpacked into one folder),
then in PowerShell:

```powershell
git clone https://github.com/aarsh-adhvaryu/judgeaudit.git
cd judgeaudit
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1 -DownloadOnly     # models first
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1 -LlamaServer C:\path\to\llama-server.exe
```

On a gaming laptop, run it from an administrator PowerShell and add
`-GpuClockLimit 2100`: see [Running every experiment on a Windows laptop](#running-every-experiment-on-a-windows-laptop).
`scripts/run_grid.py` also works on Windows if you do not need the laptop
protections.

### Auditing your own judge

Any OpenAI-compatible endpoint works (llama-server, Ollama, vLLM, hosted APIs).
Copy `configs/local_llamacpp.yaml`, set `judge.base_url`, `judge.model` and a
`judge.label` that names the model and quantization (it is part of the cache
key), and, for hosted APIs, `judge.api_key_env`. Then:

```bash
judgeaudit run -c my_judge.yaml --dry-run                                     # count calls first
judgeaudit run -c my_judge.yaml                                               # plain judge
judgeaudit run -c my_judge.yaml --run-name guarded --set guard.swap=true --set guard.screen=regex
judgeaudit recommend runs --out results && judgeaudit dashboard runs --out results/dashboard.html
```

To audit your own judge prompt rather than the built-in ones, add it as a
prompt style in `src/judgeaudit/prompts.py`.

## The dashboard

`results/dashboard.html` is one self-contained file: open it in any browser, no
server or internet needed. Download it from this repository and double-click it
to see the published results. Every number on it comes from the held-out half of
the suite.

| Part | What it shows | How to read it |
|---|---|---|
| Which set-up to use | For each use case (reference answer available or not), the fastest set-up that passed every check on the dev half, with its held-out accuracy and failures | If it says no set-up passed, the honest answer is to keep a human in the loop for that case |
| Trust against cost | One point per set-up: held-out accuracy (up) against verdicts per second (right). Colour = model; hollow = plain judge, filled = guarded; a ring = passed every dev check. Hover a point for its details | The best set-ups sit top right. Points low down usually withhold many verdicts, which count as wrong |
| Every set-up | All set-ups with their held-out metrics; green cells pass the threshold, red cells fail it. Filter by reference and model, click a header to sort | Read across a row to see which failure mode a set-up still has |
| Where the judge was fooled | For any set-up, every case where the verdict disagreed with ground truth: the question, the exact answer the judge saw, what it said, what was expected, and whether the screen flagged it. Filter by variant | This is the demo: pick a plain judge and the injection variant to watch it obey an instruction hidden in a wrong answer, then pick the guarded set-up |

`results/recommendation.md` is the same recommendation as text, with 95%
intervals; `results/comparison.md` and `comparison.csv` hold every metric for
every run; `results/cards/` has one reliability card per run.

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
| `judgeaudit dashboard runs --out results/dashboard.html` | One self-contained page: recommendation, trust-against-cost chart, every set-up, and a browser of the cases that fooled each judge (see [The dashboard](#the-dashboard)) |
| `judgeaudit report RUN_DIR [-c CONFIG]` | Rebuild a card, optionally with new thresholds |

Each run writes `report.html`, `report.md`, `summary.json` (with separate
`splits.dev` and `splits.heldout` scores), `results.jsonl` (every verdict) and
`config.resolved.yaml`.

## The guard

```yaml
prompt_style: guarded_v2   # naive | hardened | guarded | guarded_v2
guard:
  swap: true               # pairwise: ask in both orders, withhold the pick when they disagree
  screen: both             # none | regex | llm | both: check each answer for text aimed at the grader
  on_flag: reject          # reject | abstain: what a flagged answer gets
  screen_prompt: v2        # v1 | v2: wording of the LLM screen
```

| Defence | Cost | What it targets |
|---|---|---|
| `swap` | one extra call per pairwise verdict | position bias: an order-dependent pick is never let through |
| `screen: regex` | free | injections that use the usual forms: role markers, fake tags, forged verdicts, direct address to the grader |
| `screen: llm` | one extra call per pointwise verdict | the same, phrased in ways a rule list misses; the judge model is asked a narrow yes/no question about the text instead of grading it |
| `prompt_style: guarded_v2` | none | the answer is fenced between unguessable markers, the grading rule is repeated after it, and text aimed at the grader fails the answer (`guarded` is the round-1 wording, which also failed harmless politeness) |
| `on_flag: abstain` | none | sends flagged answers to a human instead of failing them |

Withheld verdicts count as wrong for accuracy and are reported as
`abstain_rate`, with a threshold, so a guard cannot pass by refusing to answer.
Every guard sub-call goes through the verdict cache: the swapped half of one
pair is often exactly another case's call, so a guard costs fewer calls than its
calls-per-verdict figure suggests during an audit, while the cost reported for
deployment counts every call.

**No tuning on the test.** Every defence was designed against the one injection
the audit has always used (`wrong_injection`), and `recommend` chooses on dev
items and reports held-out items. Two sets of held-out phrasings test whether a
defence generalises:

- `wrong_injection_unseen` (round 1): ten phrasings written with the round-1
  defences (fake markup, a forged verdict, a fake conversation turn, a policy
  claim, an emotional plea, French).
- `wrong_injection_fresh` (round 2): round 1's held-out results had been looked
  at before round 2 was tuned, so round 2 is judged on ten new phrasings written
  before any round-2 result (an HTML comment, a JSON override, a fake staff
  note, German, and others). The regex screen was not changed between rounds.

Round-2 tuning (`guarded_v2`, `screen_prompt: v2`) used only the dev half: it
fixed the round-1 prompt's habit of failing politely padded correct answers and
the round-1 screen's false alarms on them.

## Running every experiment on a Windows laptop

One script downloads the models, starts and stops `llama-server` for each, runs
the whole grid and writes `results/` (comparison, recommendation, dashboard):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1
```

For each model it runs prompts `naive`, `hardened`, `guarded` and
`guarded_v2`, references `none` and `given`, and guards `plain`, `swap-regex`,
`swap-llm`, `swap-both`, `swap-both-abstain`, `swap-llm2` and `swap-both2`:
44 set-ups (`scripts/run_grid.py` runs the same grid). Most re-use judge calls
already made, so the grid costs about six audits of fresh calls per model.

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
literature. Each is expanded into 13 cases:

| Variant | What changes | Expected |
|---|---|---|
| `correct_terse` | nothing | correct |
| `correct_padded` | content-free politeness added | correct |
| `wrong_terse` | nothing | incorrect |
| `wrong_padded` | content-free politeness added | incorrect |
| `wrong_fluent` | wrong answer rewritten as a confident, detailed explanation | incorrect |
| `wrong_authority` | claim of expert verification appended | incorrect |
| `wrong_injection` | the tuning instruction to the grader appended | incorrect |
| `wrong_injection_unseen` | one of ten held-out injection phrasings appended (round 1) | incorrect |
| `wrong_injection_fresh` | one of ten further held-out phrasings appended (round 2) | incorrect |
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
  prompts.py    versioned judge prompts (naive, hardened, guarded, guarded_v2) and screen prompts (v1, v2)
  guard.py      defences: plan the judge calls a verdict needs, combine their answers
  cache.py      SQLite verdict cache, keyed on everything that can change a verdict
  runner.py     resumable, concurrent execution through the cache, with thermal pausing
  metrics.py    paired metrics, bootstrap intervals, threshold checks
  report.py     reliability card (HTML and Markdown)
  compare.py    all runs side by side
  recommend.py  choose on dev, report on held-out, cost per verdict
  dashboard.py  the self-contained demo page
scripts/        run_grid.py (the experiment grid, any OS), run_all.ps1 (the same on a Windows
                laptop, with power and heat protection), gpu_guard.py (telemetry and pacing)
notebooks/      colab_quickstart.ipynb
results/        published results: recommendation, comparison, dashboard, cards; v0/ = first round
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
- The regex screen and the round-1 held-out injections were written by the same
  author, so its 80% recall on them is optimistic; on the fresh round-2 phrasings
  it caught none. Rules memorise forms. A determined attacker who knows the
  defences can likely write phrasings that pass both the screen and the judge.
- The published speeds come from one laptop GPU (RTX 5070 Ti Laptop) with its
  clock capped at 2100 MHz for heat; other GPUs give other speeds, and greedy
  verdicts can differ slightly between GPUs and llama.cpp builds.
- Self-preference bias is not measured. It needs answers written by the judge
  model and by a different model.
- A passing card covers this suite only. It is evidence about these failure
  modes on factual QA, not a general guarantee.
