# Which judge set-up to use

Chosen on the dev half of the suite; every number below is measured on the held-out half, which played no part in the choice. Ranges are 95% bootstrap intervals over items.

## You have a reference answer for each question

**Use `llama31-8b-q4` · prompt hardened · guard swap+screen=regex/reject.** It is the fastest set-up that passed every check on dev (10.3 verdicts/s, 1.308 judge calls per verdict, 7313 MiB VRAM in use).
On held-out items it passed every check.

Best set-up for each model (held-out numbers):

| Set-up | Verdicts/s | Calls/verdict | Dev checks failed | Accuracy | Pair accuracy | Injection accepted | Unseen injection accepted | Fresh injection accepted | Padded correct rejected | Position flips | Withheld |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `llama31-8b-q4` · prompt hardened · guard swap+screen=regex/reject | 10.3 | 1.308 | none | 99.3% (98.2%-100.0%) | 98.0% (94.0%-100.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 2.0% (0.0%-6.1%) | 0.0% (0.0%-0.0%) | 0.6% (0.0%-1.5%) |
| `llama31-8b-q8` · prompt guarded_v2 · guard none | 8.7 | 1 | none | 98.9% (97.8%-99.8%) | 97.0% (92.0%-100.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 4.1% (0.0%-10.2%) | 2.0% (0.0%-6.0%) | 0.0% (0.0%-0.0%) |
| `qwen3-8b-q4` · prompt guarded_v2 · guard swap+screen=regex/reject | 9.4 | 1.308 | abstain_rate | 99.3% (98.2%-100.0%) | 90.0% (80.0%-98.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 16.0% (14.5%-17.5%) |
| `qwen3-8b-q8` · prompt guarded_v2 · guard swap+screen=both(v2)/reject | 4.3 | 2 | accept.injection_fresh, abstain_rate | 99.6% (98.7%-100.0%) | 92.0% (84.0%-98.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 15.4% (13.8%-17.2%) |
| `llama32-3b-q4` · prompt guarded_v2 · guard none | 21.4 | 1 | accept.injection_fresh, reject.padded | 96.7% (94.9%-98.2%) | 91.0% (84.0%-97.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 12.8% (4.3%-23.4%) | 10.0% (2.0%-20.0%) | 0.0% (0.0%-0.0%) |

Trust against cost: set-ups no other set-up beats on both (dev checks failed, verdicts/s):

- `llama32-3b-q4` · prompt guarded · guard none: 2 dev checks failed, 21.4 verdicts/s
- `llama32-3b-q4` · prompt guarded_v2 · guard none: 2 dev checks failed, 21.4 verdicts/s
- `llama31-8b-q4` · prompt guarded_v2 · guard none: 1 dev checks failed, 13.4 verdicts/s
- `llama31-8b-q4` · prompt naive · guard none: 1 dev checks failed, 13.4 verdicts/s
- `llama31-8b-q4` · prompt hardened · guard swap+screen=regex/reject: 0 dev checks failed, 10.3 verdicts/s

## You have no reference answer

**No set-up passed every check on dev.** The closest is `qwen3-8b-q4` · prompt hardened · guard swap+screen=both(v2)/reject, which failed pair_accuracy, flip_to_accept.padded. Do not use an LLM judge unattended for this case.

Best set-up for each model (held-out numbers):

| Set-up | Verdicts/s | Calls/verdict | Dev checks failed | Accuracy | Pair accuracy | Injection accepted | Unseen injection accepted | Fresh injection accepted | Padded correct rejected | Position flips | Withheld |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `qwen3-8b-q4` · prompt hardened · guard swap+screen=both(v2)/reject | 6.1 | 2 | pair_accuracy, accept.padded | 92.7% (88.7%-96.2%) | 82.0% (70.0%-92.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 2.2% (0.0%-6.7%) | 4.1% (0.0%-10.2%) | 0.0% (0.0%-0.0%) | 8.0% (5.5%-10.5%) |
| `qwen3-8b-q8` · prompt hardened · guard swap+screen=both/reject | 4.3 | 2 | accept.padded, accept.injection_fresh | 92.9% (88.7%-96.7%) | 90.0% (80.0%-98.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 2.2% (0.0%-6.7%) | 4.1% (0.0%-10.2%) | 0.0% (0.0%-0.0%) | 2.2% (0.9%-3.7%) |
| `llama31-8b-q4` · prompt guarded_v2 · guard swap+screen=both(v2)/reject | 6.7 | 2 | accept.injection_fresh, reject.padded | 91.8% (88.7%-94.7%) | 80.0% (68.0%-90.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 2.4% (0.0%-7.3%) | 23.4% (12.8%-36.2%) | 0.0% (0.0%-0.0%) | 7.4% (4.9%-9.8%) |
| `llama31-8b-q8` · prompt guarded_v2 · guard swap+screen=both(v2)/reject | 4.3 | 2 | accept.injection_fresh, reject.padded, abstain_rate | 92.0% (88.7%-95.1%) | 82.0% (70.0%-92.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 18.8% (8.3%-29.2%) | 0.0% (0.0%-0.0%) | 10.8% (8.3%-13.5%) |
| `llama32-3b-q4` · prompt guarded_v2 · guard swap+screen=both(v2)/reject | 10.7 | 2 | pointwise_accuracy, pair_accuracy, accept.fluent, accept.injection_fresh, reject.padded | 83.8% (80.2%-87.6%) | 80.0% (68.0%-90.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 30.4% (17.4%-43.5%) | 0.0% (0.0%-0.0%) | 4.6% (2.8%-6.8%) |

Trust against cost: set-ups no other set-up beats on both (dev checks failed, verdicts/s):

- `llama32-3b-q4` · prompt hardened · guard none: 5 dev checks failed, 21.4 verdicts/s
- `llama31-8b-q4` · prompt guarded_v2 · guard none: 3 dev checks failed, 13.4 verdicts/s
- `llama31-8b-q4` · prompt guarded_v2 · guard swap+screen=regex/reject: 2 dev checks failed, 10.3 verdicts/s

220 set-ups compared. Full numbers: `comparison.csv`; per-run cards: `runs/<run>/report.html`.
