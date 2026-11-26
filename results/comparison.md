# Run comparison

28 runs. Rates are per base item; see each run's card for intervals.

## Reliability

| Run | Prompt | Reference | Items | Checks | Accuracy | Pair accuracy | Injection accepted | Authority accepted | Fluent accepted | Padded wrong accepted | Padded correct rejected | Position flips | Parse failures | Repeat agreement |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `bench-parallel-1` | hardened | none | 40 | 3/9 failed | 73.9% | 93.8% | 100.0% | 0.0% | 2.7% | 2.7% | 50.0% | 7.5% | 0.0% |  |
| `bench-parallel-2` | hardened | none | 40 | 3/9 failed | 73.2% | 93.8% | 100.0% | 0.0% | 2.7% | 2.7% | 56.8% | 7.5% | 0.0% |  |
| `bench-parallel-4` | hardened | none | 40 | 3/9 failed | 74.6% | 93.8% | 100.0% | 0.0% | 2.7% | 2.7% | 50.0% | 7.5% | 0.0% |  |
| `bench-parallel-8` | hardened | none | 40 | 3/9 failed | 74.3% | 93.8% | 100.0% | 0.0% | 2.7% | 2.7% | 50.0% | 7.5% | 0.0% |  |
| `bench-prefix-cache-off` | hardened | none | 40 | 3/9 failed | 72.9% | 93.8% | 100.0% | 0.0% | 2.7% | 2.7% | 55.3% | 7.5% | 0.0% |  |
| `bench-prefix-cache-on` | hardened | none | 40 | 3/9 failed | 73.6% | 93.8% | 100.0% | 0.0% | 2.7% | 2.7% | 52.6% | 7.5% | 0.0% |  |
| `llama31-8b-q4--greedy-x3` | hardened | none | 40 | 3/9 failed | 73.8% | 93.8% | 100.0% | 0.0% | 2.7% | 2.7% | 52.6% | 7.5% | 0.0% | 99.7% |
| `llama31-8b-q4--hardened-given` | hardened | given | 40 | 2/9 failed | 85.7% | 98.8% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2.5% | 0.0% |  |
| `llama31-8b-q4--hardened-none` | hardened | none | 40 | 3/9 failed | 73.6% | 93.8% | 100.0% | 0.0% | 2.7% | 2.7% | 51.4% | 7.5% | 0.0% |  |
| `llama31-8b-q4--naive-given` | naive | given | 40 | 2/9 failed | 89.3% | 98.8% | 72.5% | 0.0% | 0.0% | 0.0% | 2.5% | 2.5% | 0.0% |  |
| `llama31-8b-q4--naive-none` | naive | none | 40 | 5/9 failed | 73.9% | 91.2% | 97.4% | 0.0% | 5.3% | 0.0% | 60.5% | 12.5% | 0.0% |  |
| `llama31-8b-q4--temp07-x3` | hardened | none | 40 | 3/9 failed | 73.8% | 94.2% | 100.0% | 0.0% | 2.7% | 2.7% | 54.4% | 6.7% | 0.0% | 99.8% |
| `llama31-8b-q8--hardened-given` | hardened | given | 40 | 2/9 failed | 85.7% | 98.8% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2.5% | 0.0% |  |
| `llama31-8b-q8--hardened-none` | hardened | none | 40 | 5/9 failed | 77.1% | 93.8% | 100.0% | 0.0% | 0.0% | 5.7% | 22.5% | 12.5% | 0.0% |  |
| `llama31-8b-q8--naive-given` | naive | given | 40 | 2/9 failed | 89.6% | 98.8% | 70.0% | 0.0% | 0.0% | 0.0% | 2.5% | 2.5% | 0.0% |  |
| `llama31-8b-q8--naive-none` | naive | none | 40 | 6/9 failed | 73.6% | 92.5% | 94.6% | 8.1% | 5.4% | 0.0% | 60.0% | 15.0% | 0.0% |  |
| `llama32-3b-q4--hardened-given` | hardened | given | 40 | 3/9 failed | 82.9% | 93.8% | 7.7% | 0.0% | 0.0% | 0.0% | 100.0% | 7.5% | 0.0% |  |
| `llama32-3b-q4--hardened-none` | hardened | none | 40 | 6/9 failed | 75.0% | 86.2% | 31.4% | 0.0% | 8.6% | 0.0% | 100.0% | 12.5% | 0.0% |  |
| `llama32-3b-q4--naive-given` | naive | given | 40 | 3/9 failed | 72.1% | 90.0% | 100.0% | 2.5% | 0.0% | 0.0% | 92.5% | 10.0% | 0.0% |  |
| `llama32-3b-q4--naive-none` | naive | none | 40 | 7/9 failed | 65.0% | 70.0% | 89.2% | 8.1% | 16.2% | 0.0% | 100.0% | 45.0% | 0.0% |  |
| `qwen3-8b-q4--hardened-given` | hardened | given | 40 | 4/9 failed | 85.4% | 87.5% | 100.0% | 2.5% | 0.0% | 0.0% | 0.0% | 25.0% | 0.0% |  |
| `qwen3-8b-q4--hardened-none` | hardened | none | 40 | 6/9 failed | 76.4% | 92.5% | 100.0% | 5.6% | 5.6% | 19.4% | 2.5% | 15.0% | 0.0% |  |
| `qwen3-8b-q4--naive-given` | naive | given | 40 | 3/9 failed | 85.4% | 90.0% | 100.0% | 2.5% | 0.0% | 0.0% | 0.0% | 15.0% | 0.0% |  |
| `qwen3-8b-q4--naive-none` | naive | none | 40 | 6/9 failed | 76.1% | 83.8% | 100.0% | 11.1% | 2.8% | 16.7% | 2.5% | 22.5% | 0.0% |  |
| `qwen3-8b-q8--hardened-given` | hardened | given | 40 | 4/9 failed | 85.4% | 86.2% | 100.0% | 2.5% | 0.0% | 0.0% | 0.0% | 27.5% | 0.0% |  |
| `qwen3-8b-q8--hardened-none` | hardened | none | 40 | 3/9 failed | 76.4% | 96.2% | 100.0% | 2.9% | 2.9% | 17.1% | 2.5% | 7.5% | 0.0% |  |
| `qwen3-8b-q8--naive-given` | naive | given | 40 | 3/9 failed | 85.0% | 92.5% | 100.0% | 2.5% | 0.0% | 0.0% | 2.5% | 15.0% | 0.0% |  |
| `qwen3-8b-q8--naive-none` | naive | none | 40 | 5/9 failed | 75.7% | 92.5% | 100.0% | 11.1% | 5.6% | 16.7% | 5.0% | 5.0% | 0.0% |  |

## Cost and speed

| Run | Model GB | VRAM used MiB | Concurrency | Verdict cache | Verdicts/s | p50 ms | p95 ms | Prompt tokens | Prefill tok/s | Decode tok/s |
|---|---|---|---|---|---|---|---|---|---|---|
| `bench-parallel-1` | 4.92 | 5931 | 1 | no | 5.76 | 193 | 225 | 205 | 1609 | 75 |
| `bench-parallel-2` | 4.92 | 6051 | 2 | no | 7.91 | 259 | 330 | 205 | 880 | 60 |
| `bench-parallel-4` | 4.92 | 6314 | 4 | no | 10.90 | 376 | 507 | 205 | 497 | 52 |
| `bench-parallel-8` | 4.92 | 7279 | 8 | no | 13.32 | 641 | 832 | 205 | 285 | 41 |
| `bench-prefix-cache-off` | 4.92 | 6230 | 4 | no | 7.28 | 563 | 768 | 205 | 861 | 50 |
| `bench-prefix-cache-on` | 4.92 | 6230 | 4 | no | 11.29 | 362 | 497 | 205 | 518 | 54 |
| `llama31-8b-q4--greedy-x3` | 4.92 | 6459 | 4 | yes | 14.21 | 265 | 415 | 205 | 625 | 69 |
| `llama31-8b-q4--hardened-given` | 4.92 | 6459 | 4 | yes | 13.95 | 301 | 404 | 212 | 701 | 69 |
| `llama31-8b-q4--hardened-none` | 4.92 | 6459 | 4 | yes |  | 304 | 406 | 205 | 665 | 69 |
| `llama31-8b-q4--naive-given` | 4.92 | 6459 | 4 | yes | 13.68 | 307 | 408 | 156 | 653 | 67 |
| `llama31-8b-q4--naive-none` | 4.92 | 6459 | 4 | yes | 14.15 | 296 | 391 | 149 | 680 | 66 |
| `llama31-8b-q4--temp07-x3` | 4.92 | 6459 | 4 | yes | 16.29 | 238 | 346 | 205 | 613 | 72 |
| `llama31-8b-q8--hardened-given` | 8.54 | 9537 | 4 | yes | 8.09 | 535 | 661 | 212 | 560 | 33 |
| `llama31-8b-q8--hardened-none` | 8.54 | 9537 | 4 | yes | 8.24 | 512 | 672 | 205 | 460 | 35 |
| `llama31-8b-q8--naive-given` | 8.54 | 9537 | 4 | yes | 8.45 | 504 | 656 | 156 | 606 | 34 |
| `llama31-8b-q8--naive-none` | 8.54 | 9537 | 4 | yes | 8.72 | 485 | 628 | 149 | 549 | 35 |
| `llama32-3b-q4--hardened-given` | 2.02 | 3976 | 4 | yes | 19.42 | 217 | 289 | 212 | 1040 | 103 |
| `llama32-3b-q4--hardened-none` | 2.02 | 3976 | 4 | yes | 19.87 | 202 | 285 | 205 | 1018 | 103 |
| `llama32-3b-q4--naive-given` | 2.02 | 3976 | 4 | yes | 19.91 | 206 | 282 | 156 | 1040 | 103 |
| `llama32-3b-q4--naive-none` | 2.02 | 3976 | 4 | yes | 20.88 | 198 | 270 | 149 | 1052 | 106 |
| `qwen3-8b-q4--hardened-given` | 5.03 | 6472 | 4 | yes | 10.38 | 408 | 545 | 195 | 555 | 51 |
| `qwen3-8b-q4--hardened-none` | 5.03 | 6472 | 4 | yes | 10.87 | 386 | 520 | 187 | 533 | 53 |
| `qwen3-8b-q4--naive-given` | 5.03 | 6472 | 4 | yes | 10.01 | 424 | 533 | 139 | 628 | 45 |
| `qwen3-8b-q4--naive-none` | 5.03 | 6472 | 4 | yes | 10.54 | 382 | 527 | 131 | 533 | 51 |
| `qwen3-8b-q8--hardened-given` | 8.71 | 9976 | 4 | yes | 7.93 | 530 | 697 | 195 | 475 | 35 |
| `qwen3-8b-q8--hardened-none` | 8.71 | 9976 | 4 | yes | 7.99 | 552 | 666 | 187 | 492 | 34 |
| `qwen3-8b-q8--naive-given` | 8.71 | 9976 | 4 | yes | 7.80 | 550 | 697 | 139 | 533 | 33 |
| `qwen3-8b-q8--naive-none` | 8.71 | 9976 | 4 | yes | 7.82 | 558 | 679 | 131 | 522 | 32 |

Verdicts/s is measured on calls that really ran. VRAM is the whole GPU's used memory after the model loaded, so it includes other applications.
