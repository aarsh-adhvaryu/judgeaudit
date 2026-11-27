# judgeaudit: notes for Claude

Graded DS635 Machine Learning Systems Engineering project (DA-IICT), deadline
30 November 2026, graded on demo, report, code and course techniques (GPU
inference: quantization, KV/prefix cache, batching, decoding, serving). The user
builds it alone; do not plan work for teammates and do not ask for the suite
items to be verified by other people.

## What it is
Audit an LLM judge with paired test cases, guard it, and recommend the cheapest
set-up that passes every check: chosen on the `dev` half of the suite, reported
on `heldout`. See README.md for the design.

## Machine and how to run things
- Windows 11, PowerShell 5.1, Python 3.13 venv at `.venv` (use `.venv\Scripts\python.exe`).
- Tests: `.venv\Scripts\python.exe -m pytest -q`. If pytest's temp folder is
  locked, add `-p no:cacheprovider --basetemp=<scratch dir>`.
- Judge: llama.cpp `llama-server` at `D:\llama.cpp\llama-server.exe` (b12752,
  CUDA 13.5), port 8080, GGUF models in `models\`.
- Long GPU jobs: give the user the command and let them run it in their own
  window (`powershell -ExecutionPolicy Bypass -File scripts\run_all.ps1`). Do not
  run them as a child of the Claude session. Short smoke tests (a few dozen
  calls with the 3B model) are fine to run directly.
- Do not change GPU power, clock or driver settings yourself (the permission
  system refused `nvidia-smi -pl`); put them in commands for the user.

## The laptop overheats (read before any GPU work)
On 2026-11-26 the laptop (Legion Pro 5, RTX 5070 Ti Laptop) powered off three
times under load in Performance mode: the GPU drew up to 150 W, its hotspot
reached its throttle limit in about 25 s, the GPU hung ("CUDA error: unknown
error" in llama-server), and the machine lost power. It is a hardware or
firmware fault (the System log has GPU TDR bugchecks from the month before),
not a llama.cpp bug. What works: Balanced mode, or Performance mode with
`-GpuClockLimit` from an administrator PowerShell, plus `scripts\gpu_guard.py`
pacing (pause at 8 C of hotspot headroom). After any crash read the newest
`logs\telemetry-*.csv`, `logs\crashes.log` and `logs\run_all-*.log` first.

## Rules
- Never edit suite items to make a judge look better or worse.
- Never tune a prompt, screen rule or threshold on held-out items or on
  `wrong_injection_unseen` / `wrong_injection_fresh`; tune on dev and the
  `wrong_injection` variant only. Round-1 held-out results have been seen, so
  any round-3 defence needs a new set of phrasings to be tested on.
- A run with failed or unmeasured checks reports INCOMPLETE, never TRUSTED.
- Commit result tables (`results/`), not the cache, models, runs or logs.

## Where things are
- `results/v0/`: the first round (40 items, 26 Nov): 5 models, plain judges.
- `results/`: the current round (100 items, rounds 1 and 2 of tuning, 27 Nov): comparison, recommendation, dashboard. Headline findings are in README.md under Results.
- `runs/_archive/v0/`: the v0 run folders; their calls are still in the cache.
