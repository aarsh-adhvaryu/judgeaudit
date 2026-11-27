# Which judge set-up to use

Chosen on the dev half of the suite; every number below is measured on the held-out half, which played no part in the choice. Ranges are 95% bootstrap intervals over items.

## You have a reference answer for each question

**Use `llama31-8b-q4` · prompt hardened · guard swap+screen=regex/reject.** It is the fastest set-up that passed every check on dev (10.7 verdicts/s, 1.333 judge calls per verdict, 7307 MiB VRAM in use).
On held-out items it passed every check.

Best set-up for each model (held-out numbers):

| Set-up | Verdicts/s | Calls/verdict | Dev checks failed | Accuracy | Pair accuracy | Injection accepted | Unseen injection accepted | Padded correct rejected | Position flips | Withheld |
|---|---|---|---|---|---|---|---|---|---|---|
| `llama31-8b-q8` · prompt hardened · guard swap+screen=regex/reject | 7.5 | 1.333 | none | 99.5% (98.8%-100.0%) | 98.0% (94.0%-100.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 4.0% (0.0%-10.0%) | 0.0% (0.0%-0.0%) | 2.7% (1.0%-4.3%) |
| `llama31-8b-q4` · prompt hardened · guard swap+screen=regex/reject | 10.7 | 1.333 | none | 99.2% (98.0%-100.0%) | 98.0% (94.0%-100.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 2.0% (0.0%-6.1%) | 0.0% (0.0%-0.0%) | 0.7% (0.0%-1.7%) |
| `qwen3-8b-q4` · prompt hardened · guard swap+screen=regex/reject | 10.1 | 1.333 | pair_accuracy | 100.0% (100.0%-100.0%) | 78.0% (66.0%-88.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 8.7% (5.7%-12.0%) |
| `qwen3-8b-q8` · prompt hardened · guard swap+screen=regex/reject | 7.2 | 1.333 | pair_accuracy | 100.0% (100.0%-100.0%) | 80.0% (68.0%-90.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 5.3% (3.0%-8.0%) |
| `llama32-3b-q4` · prompt guarded · guard none | 23.5 | 1 | position | 97.0% (95.0%-99.0%) | 91.0% (84.0%-97.0%) | 0.0% (0.0%-0.0%) | 2.0% (0.0%-6.0%) | 8.3% (2.1%-16.7%) | 10.0% (2.0%-20.0%) | 0.0% (0.0%-0.0%) |

Trust against cost: set-ups no other set-up beats on both (dev checks failed, verdicts/s):

- `llama32-3b-q4` · prompt guarded · guard none: 1 dev checks failed, 23.5 verdicts/s
- `llama31-8b-q4` · prompt hardened · guard swap+screen=regex/reject: 0 dev checks failed, 10.7 verdicts/s

## You have no reference answer

**No set-up passed every check on dev.** The closest is `qwen3-8b-q8` · prompt hardened · guard swap+screen=both/reject, which failed flip_to_accept.padded. Do not use an LLM judge unattended for this case.

Best set-up for each model (held-out numbers):

| Set-up | Verdicts/s | Calls/verdict | Dev checks failed | Accuracy | Pair accuracy | Injection accepted | Unseen injection accepted | Padded correct rejected | Position flips | Withheld |
|---|---|---|---|---|---|---|---|---|---|---|
| `qwen3-8b-q8` · prompt hardened · guard swap+screen=both/reject | 4.8 | 2 | accept.padded | 93.0% (89.0%-96.5%) | 90.0% (80.0%-98.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 4.1% (0.0%-10.2%) | 0.0% (0.0%-0.0%) | 2.3% (1.0%-4.0%) |
| `llama31-8b-q4` · prompt hardened · guard swap+screen=regex/reject | 10.7 | 1.333 | reject.padded | 90.0% (87.5%-92.5%) | 88.0% (78.0%-96.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 52.2% (37.0%-65.2%) | 0.0% (0.0%-0.0%) | 2.0% (0.7%-3.7%) |
| `qwen3-8b-q4` · prompt hardened · guard swap+screen=both/reject | 6.7 | 2 | pair_accuracy, accept.padded | 92.5% (88.5%-96.2%) | 82.0% (70.0%-92.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 4.1% (0.0%-10.2%) | 0.0% (0.0%-0.0%) | 8.7% (6.0%-11.3%) |
| `llama31-8b-q8` · prompt guarded · guard swap+screen=regex/reject | 7.5 | 1.333 | pointwise_accuracy, reject.padded | 83.8% (81.5%-85.8%) | 82.0% (70.0%-92.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 100.0% (100.0%-100.0%) | 0.0% (0.0%-0.0%) | 11.3% (8.3%-14.3%) |
| `llama32-3b-q4` · prompt guarded · guard swap+screen=regex/reject | 17.6 | 1.333 | pointwise_accuracy, pair_accuracy, accept.fluent, reject.padded | 83.8% (80.0%-87.2%) | 76.0% (64.0%-88.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 37.8% (24.4%-51.1%) | 0.0% (0.0%-0.0%) | 4.7% (2.7%-7.0%) |

Trust against cost: set-ups no other set-up beats on both (dev checks failed, verdicts/s):

- `llama32-3b-q4` · prompt hardened · guard none: 4 dev checks failed, 23.5 verdicts/s
- `llama31-8b-q4` · prompt guarded · guard none: 3 dev checks failed, 14.3 verdicts/s
- `llama31-8b-q4` · prompt hardened · guard none: 3 dev checks failed, 14.3 verdicts/s
- `llama31-8b-q4` · prompt hardened · guard swap+screen=regex/reject: 1 dev checks failed, 10.7 verdicts/s

110 set-ups compared. Full numbers: `comparison.csv`; per-run cards: `runs/<run>/report.html`.
