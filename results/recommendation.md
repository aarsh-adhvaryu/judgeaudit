# Which judge set-up to use

Chosen on the dev half of the suite; every number below is measured on the held-out half, which played no part in the choice. Ranges are 95% bootstrap intervals over items.

## You have a reference answer for each question

**Use `llama31-8b-q4` · prompt hardened · guard swap+screen=regex/reject.** It is the fastest set-up that passed every check on dev (10.3 verdicts/s, 1.308 judge calls per verdict, 7313 MiB VRAM in use).
On held-out items it passed every check.

Best set-up for each model (held-out numbers):

| Set-up | Verdicts/s | Calls/verdict | Dev checks failed | Balanced accuracy | Accuracy | Pair accuracy | Injection accepted | Unseen injection accepted | Fresh injection accepted | Padded correct rejected | Position flips | Withheld |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `llama31-8b-q4` · prompt hardened · guard swap+screen=regex/reject | 10.3 | 1.308 | none | 98.5% (96.0%-100.0%) | 99.3% (98.2%-100.0%) | 98.0% (94.0%-100.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 2.0% (0.0%-6.1%) | 0.0% (0.0%-0.0%) | 0.6% (0.0%-1.5%) |
| `llama31-8b-q8` · prompt guarded_v2 · guard none | 8.7 | 1 | none | 97.9% (95.1%-99.9%) | 98.9% (97.8%-99.8%) | 97.0% (92.0%-100.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 4.1% (0.0%-10.2%) | 2.0% (0.0%-6.0%) | 0.0% (0.0%-0.0%) |
| `qwen3-8b-q4` · prompt guarded_v2 · guard swap+screen=regex/reject | 9.4 | 1.308 | abstain_rate | 99.6% (98.9%-100.0%) | 99.3% (98.2%-100.0%) | 90.0% (80.0%-98.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 16.0% (14.5%-17.5%) |
| `qwen3-8b-q8` · prompt guarded_v2 · guard swap+screen=both(v2)/reject | 4.3 | 2 | accept.injection_fresh, abstain_rate | 99.7% (99.1%-100.0%) | 99.6% (98.7%-100.0%) | 92.0% (84.0%-98.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 15.4% (13.8%-17.2%) |
| `llama32-3b-q4` · prompt guarded_v2 · guard none | 21.4 | 1 | accept.injection_fresh, reject.padded | 93.6% (89.6%-97.1%) | 96.7% (94.9%-98.2%) | 91.0% (84.0%-97.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 12.8% (4.3%-23.4%) | 10.0% (2.0%-20.0%) | 0.0% (0.0%-0.0%) |

Trust against cost: set-ups no other set-up beats on both (dev checks failed, verdicts/s):

- `llama32-3b-q4` · prompt guarded · guard none: 2 dev checks failed, 21.4 verdicts/s
- `llama32-3b-q4` · prompt guarded_v2 · guard none: 2 dev checks failed, 21.4 verdicts/s
- `llama31-8b-q4` · prompt guarded_v2 · guard none: 1 dev checks failed, 13.4 verdicts/s
- `llama31-8b-q4` · prompt hardened · guard none: 1 dev checks failed, 13.4 verdicts/s
- `llama31-8b-q4` · prompt naive · guard none: 1 dev checks failed, 13.4 verdicts/s
- `llama31-8b-q4` · prompt hardened · guard swap+screen=regex/reject: 0 dev checks failed, 10.3 verdicts/s

## You have no reference answer

**No set-up passed every check on dev.** The closest is `qwen3-8b-q4` · prompt hardened · guard swap+screen=both(v2)/reject, which failed pair_accuracy, flip_to_accept.padded. Do not use an LLM judge unattended for this case.

Best set-up for each model (held-out numbers):

| Set-up | Verdicts/s | Calls/verdict | Dev checks failed | Balanced accuracy | Accuracy | Pair accuracy | Injection accepted | Unseen injection accepted | Fresh injection accepted | Padded correct rejected | Position flips | Withheld |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `qwen3-8b-q4` · prompt hardened · guard swap+screen=both(v2)/reject | 6.1 | 2 | pair_accuracy, accept.padded | 93.9% (90.0%-97.1%) | 92.7% (88.7%-96.2%) | 82.0% (70.0%-92.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 2.2% (0.0%-6.7%) | 4.1% (0.0%-10.2%) | 0.0% (0.0%-0.0%) | 8.0% (5.5%-10.5%) |
| `qwen3-8b-q8` · prompt hardened · guard swap+screen=both/reject | 4.3 | 2 | accept.padded, accept.injection_fresh | 94.0% (90.0%-97.3%) | 92.9% (88.7%-96.7%) | 90.0% (80.0%-98.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 2.2% (0.0%-6.7%) | 4.1% (0.0%-10.2%) | 0.0% (0.0%-0.0%) | 2.2% (0.9%-3.7%) |
| `llama31-8b-q4` · prompt guarded_v2 · guard swap+screen=both(v2)/reject | 6.7 | 2 | accept.injection_fresh, reject.padded | 89.0% (84.6%-93.0%) | 91.8% (88.7%-94.7%) | 80.0% (68.0%-90.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 2.4% (0.0%-7.3%) | 23.4% (12.8%-36.2%) | 0.0% (0.0%-0.0%) | 7.4% (4.9%-9.8%) |
| `llama31-8b-q8` · prompt guarded_v2 · guard none | 8.7 | 1 | accept.injection_fresh, reject.padded | 88.6% (83.8%-93.1%) | 89.6% (85.1%-93.6%) | 89.0% (81.0%-95.0%) | 2.5% (0.0%-7.5%) | 5.0% (0.0%-12.5%) | 0.0% (0.0%-0.0%) | 18.8% (8.3%-29.2%) | 14.0% (4.0%-24.0%) | 0.0% (0.0%-0.0%) |
| `llama32-3b-q4` · prompt guarded_v2 · guard swap+screen=both(v2)/reject | 10.7 | 2 | balanced_accuracy, pair_accuracy, accept.fluent, accept.injection_fresh, reject.padded | 81.7% (77.3%-86.0%) | 83.8% (80.2%-87.6%) | 80.0% (68.0%-90.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 0.0% (0.0%-0.0%) | 30.4% (17.4%-43.5%) | 0.0% (0.0%-0.0%) | 4.6% (2.8%-6.8%) |

Trust against cost: set-ups no other set-up beats on both (dev checks failed, verdicts/s):

- `llama32-3b-q4` · prompt hardened · guard none: 5 dev checks failed, 21.4 verdicts/s
- `llama31-8b-q4` · prompt guarded · guard none: 4 dev checks failed, 13.4 verdicts/s
- `llama31-8b-q4` · prompt guarded_v2 · guard none: 4 dev checks failed, 13.4 verdicts/s
- `llama31-8b-q4` · prompt hardened · guard none: 4 dev checks failed, 13.4 verdicts/s
- `llama31-8b-q4` · prompt guarded_v2 · guard swap+screen=regex/reject: 2 dev checks failed, 10.3 verdicts/s

## Against the baselines

A judge that always answers "incorrect" scores 77.8% accuracy on this suite, because most single answers in it are wrong, but only 50% balanced accuracy. The plain judge is what most teams deploy: the naive prompt and no guard. All numbers are held-out.

| Model | Reference | Plain judge: balanced accuracy | Plain judge: injections accepted | Best set-up | Best: balanced accuracy | Best: injections accepted | Checks failed: plain to best |
|---|---|---|---|---|---|---|---|
| `llama31-8b-q4` | given | 91.9% | 30.7% | prompt hardened · guard swap+screen=regex/reject | 98.5% | 0.0% | 3 to 0 |
| `llama31-8b-q8` | given | 91.7% | 29.3% | prompt guarded_v2 · guard none | 97.9% | 0.0% | 3 to 0 |
| `qwen3-8b-q4` | given | 90.6% | 43.3% | prompt guarded_v2 · guard swap+screen=regex/reject | 99.6% | 0.0% | 3 to 1 |
| `qwen3-8b-q8` | given | 89.7% | 43.3% | prompt guarded_v2 · guard swap+screen=both(v2)/reject | 99.7% | 0.0% | 4 to 1 |
| `llama32-3b-q4` | given | 66.6% | 46.0% | prompt guarded_v2 · guard none | 93.6% | 0.0% | 6 to 2 |
| `qwen3-8b-q4` | none | 79.2% | 62.3% | prompt hardened · guard swap+screen=both(v2)/reject | 93.9% | 0.7% | 9 to 2 |
| `qwen3-8b-q8` | none | 79.6% | 60.9% | prompt hardened · guard swap+screen=both/reject | 94.0% | 0.7% | 7 to 1 |
| `llama31-8b-q4` | none | 69.8% | 52.8% | prompt guarded_v2 · guard swap+screen=both(v2)/reject | 89.0% | 0.8% | 7 to 4 |
| `llama31-8b-q8` | none | 66.6% | 56.7% | prompt guarded_v2 · guard none | 88.6% | 2.5% | 9 to 4 |
| `llama32-3b-q4` | none | 54.6% | 61.0% | prompt guarded_v2 · guard swap+screen=both(v2)/reject | 81.7% | 0.0% | 9 to 4 |

Injections accepted is the mean over the three injection sets (tuning, unseen, fresh).

220 set-ups compared. Full numbers: `comparison.csv`; per-run cards: `runs/<run>/report.html`.
