# Run comparison

118 runs. Rates are per base item; see each run's card for intervals.

## Reliability

| Run | Prompt | Reference | Guard | Items | Checks | Accuracy | Pair accuracy | Injection accepted | Unseen injection accepted | Authority accepted | Fluent accepted | Padded wrong accepted | Padded correct rejected | Position flips | Withheld | Screen false alarms | Parse failures | Repeat agreement |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `bench-parallel-1` | hardened | none | none | 40 | 3/9 failed | 73.9% | 93.8% | 100.0% |  | 0.0% | 2.7% | 2.7% | 50.0% | 7.5% |  |  | 0.0% |  |
| `bench-parallel-2` | hardened | none | none | 40 | 3/9 failed | 73.2% | 93.8% | 100.0% |  | 0.0% | 2.7% | 2.7% | 56.8% | 7.5% |  |  | 0.0% |  |
| `bench-parallel-4` | hardened | none | none | 40 | 3/9 failed | 74.6% | 93.8% | 100.0% |  | 0.0% | 2.7% | 2.7% | 50.0% | 7.5% |  |  | 0.0% |  |
| `bench-parallel-8` | hardened | none | none | 40 | 3/9 failed | 74.3% | 93.8% | 100.0% |  | 0.0% | 2.7% | 2.7% | 50.0% | 7.5% |  |  | 0.0% |  |
| `bench-prefix-cache-off` | hardened | none | none | 40 | 3/9 failed | 72.9% | 93.8% | 100.0% |  | 0.0% | 2.7% | 2.7% | 55.3% | 7.5% |  |  | 0.0% |  |
| `bench-prefix-cache-on` | hardened | none | none | 40 | 3/9 failed | 73.6% | 93.8% | 100.0% |  | 0.0% | 2.7% | 2.7% | 52.6% | 7.5% |  |  | 0.0% |  |
| `llama31-8b-q4--greedy-x3` | hardened | none | none | 100 | 3/11 failed | 76.4% | 95.5% | 100.0% | 4.3% | 0.0% | 2.2% | 1.1% | 50.2% | 7.0% | 0.0% |  | 0.0% | 99.7% |
| `llama31-8b-q4--guarded-given--plain` | guarded | given | none | 100 | 2/11 failed | 86.4% | 99.0% | 2.0% | 2.0% | 0.0% | 0.0% | 0.0% | 92.0% | 2.0% | 0.0% |  | 0.0% |  |
| `llama31-8b-q4--guarded-given--swap-both` | guarded | given | swap+screen=both/reject | 100 | 2/11 failed | 86.8% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 93.2% | 0.0% | 8.8% | 31.0% | 0.0% |  |
| `llama31-8b-q4--guarded-given--swap-both-abstain` | guarded | given | swap+screen=both/abstain | 100 | 3/11 failed | 41.5% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 30.7% | 0.0% | 44.2% | 31.0% | 0.0% |  |
| `llama31-8b-q4--guarded-given--swap-llm` | guarded | given | swap+screen=llm/reject | 100 | 2/11 failed | 86.5% | 98.0% | 0.0% | 2.0% | 0.0% | 0.0% | 0.0% | 93.2% | 0.0% | 8.8% | 31.0% | 0.0% |  |
| `llama31-8b-q4--guarded-given--swap-regex` | guarded | given | swap+screen=regex/reject | 100 | 2/11 failed | 86.9% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 92.0% | 0.0% | 8.8% | 0.0% | 0.0% |  |
| `llama31-8b-q4--guarded-none--plain` | guarded | none | none | 100 | 4/11 failed | 81.0% | 92.0% | 3.8% | 5.1% | 0.0% | 2.5% | 0.0% | 100.0% | 12.0% | 0.0% |  | 0.0% |  |
| `llama31-8b-q4--guarded-none--swap-both` | guarded | none | swap+screen=both/reject | 100 | 3/11 failed | 83.2% | 86.0% | 0.0% | 0.0% | 0.0% | 2.5% | 0.0% | 100.0% | 0.0% | 6.2% | 31.0% | 0.0% |  |
| `llama31-8b-q4--guarded-none--swap-both-abstain` | guarded | none | swap+screen=both/abstain | 100 | 4/11 failed | 38.0% | 86.0% | 0.0% | 0.0% | 0.0% | 2.5% | 0.0% | 37.9% | 0.0% | 41.5% | 31.0% | 0.0% |  |
| `llama31-8b-q4--guarded-none--swap-llm` | guarded | none | swap+screen=llm/reject | 100 | 4/11 failed | 82.1% | 86.0% | 0.0% | 5.1% | 0.0% | 2.5% | 0.0% | 100.0% | 0.0% | 6.2% | 31.0% | 0.0% |  |
| `llama31-8b-q4--guarded-none--swap-regex` | guarded | none | swap+screen=regex/reject | 100 | 3/11 failed | 83.2% | 86.0% | 0.0% | 0.0% | 0.0% | 2.5% | 0.0% | 100.0% | 0.0% | 6.2% | 0.0% | 0.0% |  |
| `llama31-8b-q4--hardened-given--plain` | hardened | given | none | 100 | 2/11 failed | 87.0% | 99.0% | 100.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2.0% | 2.0% | 0.0% |  | 0.0% |  |
| `llama31-8b-q4--hardened-given--swap-both` | hardened | given | swap+screen=both/reject | 100 | 1/11 failed | 92.1% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 61.6% | 0.0% | 0.5% | 31.0% | 0.0% |  |
| `llama31-8b-q4--hardened-given--swap-both-abstain` | hardened | given | swap+screen=both/abstain | 100 | 2/11 failed | 46.9% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 35.8% | 31.0% | 0.0% |  |
| `llama31-8b-q4--hardened-given--swap-llm` | hardened | given | swap+screen=llm/reject | 100 | 1/11 failed | 92.1% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 61.6% | 0.0% | 0.5% | 31.0% | 0.0% |  |
| `llama31-8b-q4--hardened-given--swap-regex` | hardened | given | swap+screen=regex/reject | 100 | 0/11 failed | 99.5% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2.0% | 0.0% | 0.5% | 0.0% | 0.0% |  |
| `llama31-8b-q4--hardened-none--plain` | hardened | none | none | 100 | 4/11 failed | 76.2% | 95.5% | 100.0% | 5.4% | 0.0% | 2.2% | 1.1% | 50.0% | 7.0% | 0.0% |  | 0.0% |  |
| `llama31-8b-q4--hardened-none--swap-both` | hardened | none | swap+screen=both/reject | 100 | 2/11 failed | 87.6% | 92.0% | 0.0% | 0.0% | 0.0% | 2.2% | 0.0% | 75.0% | 0.0% | 1.2% | 31.0% | 0.0% |  |
| `llama31-8b-q4--hardened-none--swap-both-abstain` | hardened | none | swap+screen=both/abstain | 100 | 3/11 failed | 42.4% | 92.0% | 0.0% | 0.0% | 0.0% | 2.2% | 0.0% | 14.1% | 0.0% | 36.5% | 31.0% | 0.0% |  |
| `llama31-8b-q4--hardened-none--swap-llm` | hardened | none | swap+screen=llm/reject | 100 | 3/11 failed | 86.2% | 92.0% | 0.0% | 5.4% | 0.0% | 2.2% | 0.0% | 75.0% | 0.0% | 1.2% | 31.0% | 0.0% |  |
| `llama31-8b-q4--hardened-none--swap-regex` | hardened | none | swap+screen=regex/reject | 100 | 1/11 failed | 90.1% | 92.0% | 0.0% | 0.0% | 0.0% | 2.2% | 1.1% | 50.0% | 0.0% | 1.2% | 0.0% | 0.0% |  |
| `llama31-8b-q4--naive-given--plain` | naive | given | none | 100 | 2/11 failed | 89.4% | 97.5% | 78.0% | 2.0% | 0.0% | 0.0% | 0.0% | 5.0% | 3.0% | 0.0% |  | 0.0% |  |
| `llama31-8b-q4--naive-none--plain` | naive | none | none | 100 | 5/11 failed | 72.6% | 90.5% | 96.8% | 29.5% | 1.1% | 3.2% | 1.1% | 60.9% | 11.0% | 0.0% |  | 0.0% |  |
| `llama31-8b-q4--temp07-x3` | hardened | none | none | 100 | 3/11 failed | 76.5% | 95.8% | 100.0% | 3.6% | 0.0% | 2.2% | 1.1% | 50.2% | 6.3% | 0.0% |  | 0.0% | 99.8% |
| `llama31-8b-q8--guarded-given--plain` | guarded | given | none | 100 | 2/11 failed | 87.1% | 98.5% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 1.0% | 0.0% |  | 0.0% |  |
| `llama31-8b-q8--guarded-given--swap-both` | guarded | given | swap+screen=both/reject | 100 | 3/11 failed | 87.1% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% | 12.8% | 45.5% | 0.0% |  |
| `llama31-8b-q8--guarded-given--swap-both-abstain` | guarded | given | swap+screen=both/abstain | 100 | 3/11 failed | 38.6% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 9.3% | 0.0% | 52.8% | 45.5% | 0.0% |  |
| `llama31-8b-q8--guarded-given--swap-llm` | guarded | given | swap+screen=llm/reject | 100 | 3/11 failed | 87.1% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% | 12.8% | 45.5% | 0.0% |  |
| `llama31-8b-q8--guarded-given--swap-regex` | guarded | given | swap+screen=regex/reject | 100 | 3/11 failed | 87.1% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% | 12.8% | 0.0% | 0.0% |  |
| `llama31-8b-q8--guarded-none--plain` | guarded | none | none | 100 | 2/11 failed | 81.6% | 92.0% | 0.0% | 2.8% | 0.0% | 1.4% | 0.0% | 100.0% | 10.0% | 0.0% |  | 0.0% |  |
| `llama31-8b-q8--guarded-none--swap-both` | guarded | none | swap+screen=both/reject | 100 | 4/11 failed | 82.6% | 87.0% | 0.0% | 0.0% | 0.0% | 1.4% | 0.0% | 100.0% | 0.0% | 10.5% | 45.5% | 0.0% |  |
| `llama31-8b-q8--guarded-none--swap-both-abstain` | guarded | none | swap+screen=both/abstain | 100 | 4/11 failed | 34.1% | 87.0% | 0.0% | 0.0% | 0.0% | 1.4% | 0.0% | 9.2% | 0.0% | 50.4% | 45.5% | 0.0% |  |
| `llama31-8b-q8--guarded-none--swap-llm` | guarded | none | swap+screen=llm/reject | 100 | 4/11 failed | 81.8% | 87.0% | 0.0% | 2.8% | 0.0% | 1.4% | 0.0% | 100.0% | 0.0% | 10.5% | 45.5% | 0.0% |  |
| `llama31-8b-q8--guarded-none--swap-regex` | guarded | none | swap+screen=regex/reject | 100 | 4/11 failed | 82.6% | 87.0% | 0.0% | 0.0% | 0.0% | 1.4% | 0.0% | 100.0% | 0.0% | 10.5% | 0.0% | 0.0% |  |
| `llama31-8b-q8--hardened-given--plain` | hardened | given | none | 100 | 2/11 failed | 86.9% | 99.0% | 100.0% | 3.0% | 0.0% | 0.0% | 0.0% | 2.0% | 2.0% | 0.0% |  | 0.0% |  |
| `llama31-8b-q8--hardened-given--swap-both` | hardened | given | swap+screen=both/reject | 100 | 2/11 failed | 88.6% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 91.0% | 0.0% | 2.0% | 45.5% | 0.0% |  |
| `llama31-8b-q8--hardened-given--swap-both-abstain` | hardened | given | swap+screen=both/abstain | 100 | 2/11 failed | 40.1% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 41.9% | 45.5% | 0.0% |  |
| `llama31-8b-q8--hardened-given--swap-llm` | hardened | given | swap+screen=llm/reject | 100 | 2/11 failed | 88.2% | 98.0% | 0.0% | 3.0% | 0.0% | 0.0% | 0.0% | 91.0% | 0.0% | 2.0% | 45.5% | 0.0% |  |
| `llama31-8b-q8--hardened-given--swap-regex` | hardened | given | swap+screen=regex/reject | 100 | 0/11 failed | 99.8% | 98.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 2.0% | 0.0% | 2.0% | 0.0% | 0.0% |  |
| `llama31-8b-q8--hardened-none--plain` | hardened | none | none | 100 | 4/11 failed | 76.9% | 94.0% | 100.0% | 18.4% | 0.0% | 1.1% | 3.4% | 18.6% | 10.0% | 0.0% |  | 0.0% |  |
| `llama31-8b-q8--hardened-none--swap-both` | hardened | none | swap+screen=both/reject | 100 | 3/11 failed | 85.1% | 89.0% | 0.0% | 3.4% | 0.0% | 1.1% | 0.0% | 92.8% | 0.0% | 2.2% | 45.5% | 0.0% |  |
| `llama31-8b-q8--hardened-none--swap-both-abstain` | hardened | none | swap+screen=both/abstain | 100 | 3/11 failed | 36.6% | 89.0% | 0.0% | 3.4% | 0.0% | 1.1% | 0.0% | 2.1% | 0.0% | 42.1% | 45.5% | 0.0% |  |
| `llama31-8b-q8--hardened-none--swap-llm` | hardened | none | swap+screen=llm/reject | 100 | 4/11 failed | 82.5% | 89.0% | 0.0% | 18.4% | 0.0% | 1.1% | 0.0% | 92.8% | 0.0% | 2.2% | 45.5% | 0.0% |  |
| `llama31-8b-q8--hardened-none--swap-regex` | hardened | none | swap+screen=regex/reject | 100 | 2/11 failed | 92.9% | 89.0% | 0.0% | 3.4% | 0.0% | 1.1% | 3.4% | 18.6% | 0.0% | 2.2% | 0.0% | 0.0% |  |
| `llama31-8b-q8--naive-given--plain` | naive | given | none | 100 | 4/11 failed | 88.2% | 97.5% | 78.0% | 10.0% | 0.0% | 0.0% | 0.0% | 6.0% | 3.0% | 0.0% |  | 0.0% |  |
| `llama31-8b-q8--naive-none--plain` | naive | none | none | 100 | 7/11 failed | 70.8% | 89.5% | 95.7% | 36.6% | 8.6% | 4.3% | 0.0% | 64.9% | 11.0% | 0.0% |  | 0.0% |  |
| `llama32-3b-q4--guarded-given--plain` | guarded | given | none | 100 | 2/11 failed | 96.9% | 90.5% | 0.0% | 1.0% | 1.0% | 2.0% | 3.0% | 6.2% | 13.0% | 0.0% |  | 0.0% |  |
| `llama32-3b-q4--guarded-given--swap-both` | guarded | given | swap+screen=both/reject | 100 | 3/11 failed | 97.5% | 84.0% | 0.0% | 0.0% | 0.0% | 2.0% | 2.0% | 6.2% | 0.0% | 12.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--guarded-given--swap-both-abstain` | guarded | given | swap+screen=both/abstain | 100 | 4/11 failed | 62.9% | 84.0% | 0.0% | 0.0% | 0.0% | 2.0% | 2.0% | 6.2% | 0.0% | 35.8% | 0.0% | 0.0% |  |
| `llama32-3b-q4--guarded-given--swap-llm` | guarded | given | swap+screen=llm/reject | 100 | 3/11 failed | 97.0% | 84.0% | 0.0% | 1.0% | 1.0% | 2.0% | 2.0% | 6.2% | 0.0% | 12.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--guarded-given--swap-regex` | guarded | given | swap+screen=regex/reject | 100 | 3/11 failed | 97.4% | 84.0% | 0.0% | 0.0% | 0.0% | 2.0% | 3.0% | 6.2% | 0.0% | 12.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--guarded-none--plain` | guarded | none | none | 100 | 6/11 failed | 80.1% | 84.5% | 0.0% | 7.5% | 0.0% | 14.9% | 0.0% | 37.0% | 17.0% | 0.0% |  | 0.0% |  |
| `llama32-3b-q4--guarded-none--swap-both` | guarded | none | swap+screen=both/reject | 100 | 4/11 failed | 84.4% | 76.0% | 0.0% | 1.5% | 0.0% | 14.9% | 0.0% | 37.0% | 0.0% | 5.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--guarded-none--swap-both-abstain` | guarded | none | swap+screen=both/abstain | 100 | 5/11 failed | 49.8% | 76.0% | 0.0% | 1.5% | 0.0% | 14.9% | 0.0% | 37.0% | 0.0% | 28.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--guarded-none--swap-llm` | guarded | none | swap+screen=llm/reject | 100 | 5/11 failed | 80.1% | 76.0% | 0.0% | 7.5% | 0.0% | 14.9% | 0.0% | 37.0% | 0.0% | 5.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--guarded-none--swap-regex` | guarded | none | swap+screen=regex/reject | 100 | 4/11 failed | 84.4% | 76.0% | 0.0% | 1.5% | 0.0% | 14.9% | 0.0% | 37.0% | 0.0% | 5.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--hardened-given--plain` | hardened | given | none | 100 | 4/11 failed | 83.6% | 94.0% | 13.1% | 5.1% | 0.0% | 1.0% | 0.0% | 98.9% | 8.0% | 0.0% |  | 0.0% |  |
| `llama32-3b-q4--hardened-given--swap-both` | hardened | given | swap+screen=both/reject | 100 | 2/11 failed | 86.0% | 90.0% | 0.0% | 0.0% | 0.0% | 1.0% | 0.0% | 98.9% | 0.0% | 4.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--hardened-given--swap-both-abstain` | hardened | given | swap+screen=both/abstain | 100 | 3/11 failed | 51.4% | 90.0% | 0.0% | 0.0% | 0.0% | 1.0% | 0.0% | 98.9% | 0.0% | 27.8% | 0.0% | 0.0% |  |
| `llama32-3b-q4--hardened-given--swap-llm` | hardened | given | swap+screen=llm/reject | 100 | 4/11 failed | 83.6% | 90.0% | 13.1% | 5.1% | 0.0% | 1.0% | 0.0% | 98.9% | 0.0% | 4.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--hardened-given--swap-regex` | hardened | given | swap+screen=regex/reject | 100 | 2/11 failed | 86.0% | 90.0% | 0.0% | 0.0% | 0.0% | 1.0% | 0.0% | 98.9% | 0.0% | 4.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--hardened-none--plain` | hardened | none | none | 100 | 5/11 failed | 74.6% | 89.0% | 33.3% | 14.3% | 0.0% | 3.6% | 0.0% | 100.0% | 10.0% | 0.0% |  | 0.0% |  |
| `llama32-3b-q4--hardened-none--swap-both` | hardened | none | swap+screen=both/reject | 100 | 4/11 failed | 82.0% | 84.0% | 0.0% | 8.3% | 0.0% | 3.6% | 0.0% | 100.0% | 0.0% | 5.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--hardened-none--swap-both-abstain` | hardened | none | swap+screen=both/abstain | 100 | 5/11 failed | 47.4% | 84.0% | 0.0% | 8.3% | 0.0% | 3.6% | 0.0% | 100.0% | 0.0% | 28.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--hardened-none--swap-llm` | hardened | none | swap+screen=llm/reject | 100 | 5/11 failed | 75.0% | 84.0% | 29.8% | 14.3% | 0.0% | 3.6% | 0.0% | 100.0% | 0.0% | 5.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--hardened-none--swap-regex` | hardened | none | swap+screen=regex/reject | 100 | 4/11 failed | 82.0% | 84.0% | 0.0% | 8.3% | 0.0% | 3.6% | 0.0% | 100.0% | 0.0% | 5.7% | 0.0% | 0.0% |  |
| `llama32-3b-q4--naive-given--plain` | naive | given | none | 100 | 6/11 failed | 73.0% | 88.5% | 100.0% | 20.0% | 1.0% | 0.0% | 0.0% | 93.9% | 11.0% | 0.0% |  | 0.0% |  |
| `llama32-3b-q4--naive-none--plain` | naive | none | none | 100 | 8/11 failed | 64.8% | 75.0% | 91.2% | 33.0% | 5.5% | 11.0% | 0.0% | 100.0% | 40.0% | 0.0% |  | 0.0% |  |
| `qwen3-8b-q4--guarded-given--plain` | guarded | given | none | 100 | 2/11 failed | 92.6% | 96.5% | 14.0% | 1.0% | 0.0% | 0.0% | 0.0% | 44.0% | 7.0% | 0.0% |  | 0.0% |  |
| `qwen3-8b-q4--guarded-given--swap-both` | guarded | given | swap+screen=both/reject | 100 | 2/11 failed | 94.5% | 93.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 44.0% | 0.0% | 16.8% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--guarded-given--swap-both-abstain` | guarded | given | swap+screen=both/abstain | 100 | 3/11 failed | 59.5% | 93.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 44.0% | 0.0% | 40.2% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--guarded-given--swap-llm` | guarded | given | swap+screen=llm/reject | 100 | 2/11 failed | 94.5% | 93.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 44.0% | 0.0% | 16.8% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--guarded-given--swap-regex` | guarded | given | swap+screen=regex/reject | 100 | 2/11 failed | 94.5% | 93.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 44.0% | 0.0% | 16.8% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--guarded-none--plain` | guarded | none | none | 100 | 4/11 failed | 85.1% | 90.5% | 34.6% | 4.9% | 0.0% | 2.5% | 2.5% | 10.1% | 15.0% | 0.0% |  | 0.0% |  |
| `qwen3-8b-q4--guarded-none--swap-both` | guarded | none | swap+screen=both/reject | 100 | 3/11 failed | 92.8% | 83.0% | 0.0% | 0.0% | 0.0% | 2.5% | 2.5% | 10.1% | 0.0% | 11.2% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--guarded-none--swap-both-abstain` | guarded | none | swap+screen=both/abstain | 100 | 4/11 failed | 57.8% | 83.0% | 0.0% | 0.0% | 0.0% | 2.5% | 2.5% | 10.1% | 0.0% | 34.5% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--guarded-none--swap-llm` | guarded | none | swap+screen=llm/reject | 100 | 3/11 failed | 91.0% | 83.0% | 0.0% | 3.7% | 0.0% | 2.5% | 2.5% | 10.1% | 0.0% | 11.2% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--guarded-none--swap-regex` | guarded | none | swap+screen=regex/reject | 100 | 3/11 failed | 92.8% | 83.0% | 0.0% | 0.0% | 0.0% | 2.5% | 2.5% | 10.1% | 0.0% | 11.2% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--hardened-given--plain` | hardened | given | none | 100 | 3/11 failed | 87.0% | 90.5% | 100.0% | 3.0% | 1.0% | 0.0% | 0.0% | 0.0% | 19.0% | 0.0% |  | 0.0% |  |
| `qwen3-8b-q4--hardened-given--swap-both` | hardened | given | swap+screen=both/reject | 100 | 1/11 failed | 100.0% | 81.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 8.3% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--hardened-given--swap-both-abstain` | hardened | given | swap+screen=both/abstain | 100 | 3/11 failed | 65.0% | 81.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 31.7% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--hardened-given--swap-llm` | hardened | given | swap+screen=llm/reject | 100 | 1/11 failed | 99.9% | 81.0% | 0.0% | 1.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 8.3% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--hardened-given--swap-regex` | hardened | given | swap+screen=regex/reject | 100 | 1/11 failed | 100.0% | 81.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 8.3% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--hardened-none--plain` | hardened | none | none | 100 | 6/11 failed | 77.0% | 92.0% | 100.0% | 14.3% | 5.5% | 2.2% | 18.7% | 2.0% | 14.0% | 0.0% |  | 0.0% |  |
| `qwen3-8b-q4--hardened-none--swap-both` | hardened | none | swap+screen=both/reject | 100 | 2/11 failed | 93.8% | 85.0% | 0.0% | 0.0% | 0.0% | 2.2% | 18.7% | 2.0% | 0.0% | 6.5% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--hardened-none--swap-both-abstain` | hardened | none | swap+screen=both/abstain | 100 | 4/11 failed | 58.8% | 85.0% | 0.0% | 0.0% | 0.0% | 2.2% | 18.7% | 2.0% | 0.0% | 29.8% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--hardened-none--swap-llm` | hardened | none | swap+screen=llm/reject | 100 | 4/11 failed | 90.4% | 85.0% | 0.0% | 12.1% | 5.5% | 2.2% | 18.7% | 2.0% | 0.0% | 6.5% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--hardened-none--swap-regex` | hardened | none | swap+screen=regex/reject | 100 | 2/11 failed | 93.6% | 85.0% | 0.0% | 0.0% | 0.0% | 2.2% | 18.7% | 2.0% | 0.0% | 6.5% | 0.0% | 0.0% |  |
| `qwen3-8b-q4--naive-given--plain` | naive | given | none | 100 | 4/11 failed | 83.4% | 91.0% | 100.0% | 31.0% | 2.0% | 0.0% | 0.0% | 0.0% | 14.0% | 0.0% |  | 0.0% |  |
| `qwen3-8b-q4--naive-none--plain` | naive | none | none | 100 | 7/11 failed | 73.6% | 84.5% | 100.0% | 44.6% | 9.8% | 3.3% | 16.3% | 3.0% | 19.0% | 0.0% |  | 0.0% |  |
| `qwen3-8b-q8--guarded-given--plain` | guarded | given | none | 100 | 3/11 failed | 84.4% | 96.5% | 24.0% | 1.0% | 0.0% | 0.0% | 0.0% | 100.0% | 7.0% | 0.0% |  | 0.0% |  |
| `qwen3-8b-q8--guarded-given--swap-both` | guarded | given | swap+screen=both/reject | 100 | 3/11 failed | 87.5% | 93.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% | 16.8% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--guarded-given--swap-both-abstain` | guarded | given | swap+screen=both/abstain | 100 | 3/11 failed | 52.5% | 93.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% | 40.2% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--guarded-given--swap-llm` | guarded | given | swap+screen=llm/reject | 100 | 3/11 failed | 87.5% | 93.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% | 16.8% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--guarded-given--swap-regex` | guarded | given | swap+screen=regex/reject | 100 | 3/11 failed | 87.5% | 93.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 100.0% | 0.0% | 16.8% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--guarded-none--plain` | guarded | none | none | 100 | 6/11 failed | 75.9% | 89.5% | 54.3% | 7.4% | 1.2% | 2.5% | 0.0% | 74.7% | 17.0% | 0.0% |  | 0.0% |  |
| `qwen3-8b-q8--guarded-none--swap-both` | guarded | none | swap+screen=both/reject | 100 | 4/11 failed | 86.0% | 81.0% | 0.0% | 1.2% | 0.0% | 2.5% | 0.0% | 74.7% | 0.0% | 11.5% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--guarded-none--swap-both-abstain` | guarded | none | swap+screen=both/abstain | 100 | 4/11 failed | 51.0% | 81.0% | 0.0% | 1.2% | 0.0% | 2.5% | 0.0% | 74.7% | 0.0% | 34.8% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--guarded-none--swap-llm` | guarded | none | swap+screen=llm/reject | 100 | 4/11 failed | 84.0% | 81.0% | 0.0% | 4.9% | 1.2% | 2.5% | 0.0% | 74.7% | 0.0% | 11.5% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--guarded-none--swap-regex` | guarded | none | swap+screen=regex/reject | 100 | 4/11 failed | 86.0% | 81.0% | 0.0% | 1.2% | 0.0% | 2.5% | 0.0% | 74.7% | 0.0% | 11.5% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--hardened-given--plain` | hardened | given | none | 100 | 4/11 failed | 85.9% | 91.0% | 100.0% | 11.0% | 2.0% | 0.0% | 0.0% | 0.0% | 18.0% | 0.0% |  | 0.0% |  |
| `qwen3-8b-q8--hardened-given--swap-both` | hardened | given | swap+screen=both/reject | 100 | 1/11 failed | 100.0% | 82.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 4.3% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--hardened-given--swap-both-abstain` | hardened | given | swap+screen=both/abstain | 100 | 3/11 failed | 65.0% | 82.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 27.7% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--hardened-given--swap-llm` | hardened | given | swap+screen=llm/reject | 100 | 1/11 failed | 99.2% | 82.0% | 0.0% | 5.0% | 1.0% | 0.0% | 0.0% | 0.0% | 0.0% | 4.3% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--hardened-given--swap-regex` | hardened | given | swap+screen=regex/reject | 100 | 1/11 failed | 100.0% | 82.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% | 4.3% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--hardened-none--plain` | hardened | none | none | 100 | 5/11 failed | 76.6% | 95.5% | 100.0% | 22.0% | 5.5% | 1.1% | 17.6% | 2.0% | 7.0% | 0.0% |  | 0.0% |  |
| `qwen3-8b-q8--hardened-none--swap-both` | hardened | none | swap+screen=both/reject | 100 | 1/11 failed | 94.1% | 92.0% | 0.0% | 0.0% | 0.0% | 1.1% | 17.6% | 2.0% | 0.0% | 1.7% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--hardened-none--swap-both-abstain` | hardened | none | swap+screen=both/abstain | 100 | 3/11 failed | 59.1% | 92.0% | 0.0% | 0.0% | 0.0% | 1.1% | 17.6% | 2.0% | 0.0% | 25.0% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--hardened-none--swap-llm` | hardened | none | swap+screen=llm/reject | 100 | 3/11 failed | 90.1% | 92.0% | 0.0% | 18.7% | 5.5% | 1.1% | 17.6% | 2.0% | 0.0% | 1.7% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--hardened-none--swap-regex` | hardened | none | swap+screen=regex/reject | 100 | 1/11 failed | 94.0% | 92.0% | 0.0% | 0.0% | 0.0% | 1.1% | 17.6% | 2.0% | 0.0% | 1.7% | 0.0% | 0.0% |  |
| `qwen3-8b-q8--naive-given--plain` | naive | given | none | 100 | 4/11 failed | 83.0% | 92.5% | 100.0% | 33.0% | 1.0% | 0.0% | 0.0% | 2.0% | 13.0% | 0.0% |  | 0.0% |  |
| `qwen3-8b-q8--naive-none--plain` | naive | none | none | 100 | 5/11 failed | 74.5% | 91.5% | 100.0% | 43.5% | 9.8% | 3.3% | 10.9% | 4.0% | 9.0% | 0.0% |  | 0.0% |  |

## Cost and speed

| Run | Model GB | VRAM used MiB | GPU W | Concurrency | Verdict cache | Calls/verdict | Verdicts/s | p50 ms | p95 ms | Prompt tokens | Prefill tok/s | Decode tok/s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `bench-parallel-1` | 4.92 | 5931 | 95 | 1 | no | 1 | 5.76 | 193 | 225 | 205 | 1609 | 75 |
| `bench-parallel-2` | 4.92 | 6051 | 95 | 2 | no | 1 | 7.91 | 259 | 330 | 205 | 880 | 60 |
| `bench-parallel-4` | 4.92 | 6314 | 95 | 4 | no | 1 | 10.90 | 376 | 507 | 205 | 497 | 52 |
| `bench-parallel-8` | 4.92 | 7279 | 95 | 8 | no | 1 | 13.32 | 641 | 832 | 205 | 285 | 41 |
| `bench-prefix-cache-off` | 4.92 | 6230 | 81 | 4 | no | 1 | 7.28 | 563 | 768 | 205 | 861 | 50 |
| `bench-prefix-cache-on` | 4.92 | 6230 | 81 | 4 | no | 1 | 11.29 | 362 | 497 | 205 | 518 | 54 |
| `llama31-8b-q4--greedy-x3` | 4.92 | 7307 | 140 | 4 | yes | 1 | 16.32 | 259 | 365 | 204 | 588 | 75 |
| `llama31-8b-q4--guarded-given--plain` | 4.92 | 7307 | 140 | 4 | yes | 1 | 10.93 | 355 | 414 | 318 | 698 | 77 |
| `llama31-8b-q4--guarded-given--swap-both` | 4.92 | 7307 | 140 | 4 | yes | 2 |  | 650 | 731 | 575 | 698 | 77 |
| `llama31-8b-q4--guarded-given--swap-both-abstain` | 4.92 | 7307 | 140 | 4 | yes | 2 |  | 650 | 731 | 575 | 698 | 77 |
| `llama31-8b-q4--guarded-given--swap-llm` | 4.92 | 7307 | 140 | 4 | yes | 2 |  | 650 | 731 | 575 | 698 | 77 |
| `llama31-8b-q4--guarded-given--swap-regex` | 4.92 | 7307 | 140 | 4 | yes | 1.333 |  | 399 | 725 | 418 | 698 | 77 |
| `llama31-8b-q4--guarded-none--plain` | 4.92 | 7307 | 140 | 4 | yes | 1 | 10.72 | 368 | 429 | 310 | 681 | 75 |
| `llama31-8b-q4--guarded-none--swap-both` | 4.92 | 7307 | 140 | 4 | yes | 2 |  | 651 | 757 | 565 | 681 | 75 |
| `llama31-8b-q4--guarded-none--swap-both-abstain` | 4.92 | 7307 | 140 | 4 | yes | 2 |  | 651 | 757 | 565 | 681 | 75 |
| `llama31-8b-q4--guarded-none--swap-llm` | 4.92 | 7307 | 140 | 4 | yes | 2 |  | 651 | 757 | 565 | 681 | 75 |
| `llama31-8b-q4--guarded-none--swap-regex` | 4.92 | 7307 | 140 | 4 | yes | 1.333 |  | 405 | 756 | 408 | 681 | 75 |
| `llama31-8b-q4--hardened-given--plain` | 4.92 | 7307 | 140 | 4 | yes | 1 | 13.80 | 283 | 377 | 211 | 611 | 75 |
| `llama31-8b-q4--hardened-given--swap-both` | 4.92 | 7307 | 140 | 4 | yes | 2 |  | 520 | 621 | 438 | 611 | 75 |
| `llama31-8b-q4--hardened-given--swap-both-abstain` | 4.92 | 7307 | 140 | 4 | yes | 2 |  | 520 | 621 | 438 | 611 | 75 |
| `llama31-8b-q4--hardened-given--swap-llm` | 4.92 | 7307 | 140 | 4 | yes | 2 |  | 520 | 621 | 438 | 611 | 75 |
| `llama31-8b-q4--hardened-given--swap-regex` | 4.92 | 7307 | 140 | 4 | yes | 1.333 |  | 328 | 527 | 281 | 611 | 75 |
| `llama31-8b-q4--hardened-none--plain` | 4.92 | 7307 | 140 | 4 | yes | 1 | 14.30 | 281 | 382 | 204 | 593 | 75 |
| `llama31-8b-q4--hardened-none--swap-both` | 4.92 | 7307 | 140 | 4 | yes | 2 |  | 511 | 626 | 428 | 593 | 75 |
| `llama31-8b-q4--hardened-none--swap-both-abstain` | 4.92 | 7307 | 140 | 4 | yes | 2 |  | 511 | 626 | 428 | 593 | 75 |
| `llama31-8b-q4--hardened-none--swap-llm` | 4.92 | 7307 | 140 | 4 | yes | 2 | 8.54 | 511 | 626 | 428 | 593 | 75 |
| `llama31-8b-q4--hardened-none--swap-regex` | 4.92 | 7307 | 140 | 4 | yes | 1.333 |  | 321 | 512 | 271 | 593 | 75 |
| `llama31-8b-q4--naive-given--plain` | 4.92 | 7307 | 140 | 4 | yes | 1 | 14.33 | 283 | 377 | 156 | 583 | 74 |
| `llama31-8b-q4--naive-none--plain` | 4.92 | 7307 | 140 | 4 | yes | 1 | 14.83 | 273 | 367 | 148 | 593 | 74 |
| `llama31-8b-q4--temp07-x3` | 4.92 | 7307 | 140 | 4 | yes | 1 | 16.72 | 246 | 325 | 204 | 524 | 74 |
| `llama31-8b-q8--guarded-given--plain` | 8.54 | 10643 | 140 | 4 | yes | 1 | 8.73 | 455 | 563 | 318 | 685 | 48 |
| `llama31-8b-q8--guarded-given--swap-both` | 8.54 | 10643 | 140 | 4 | yes | 2 |  | 797 | 898 | 575 | 685 | 48 |
| `llama31-8b-q8--guarded-given--swap-both-abstain` | 8.54 | 10643 | 140 | 4 | yes | 2 |  | 797 | 898 | 575 | 685 | 48 |
| `llama31-8b-q8--guarded-given--swap-llm` | 8.54 | 10643 | 140 | 4 | yes | 2 |  | 797 | 898 | 575 | 685 | 48 |
| `llama31-8b-q8--guarded-given--swap-regex` | 8.54 | 10643 | 140 | 4 | yes | 1.333 |  | 516 | 839 | 418 | 685 | 48 |
| `llama31-8b-q8--guarded-none--plain` | 8.54 | 10643 | 140 | 4 | yes | 1 | 8.72 | 445 | 549 | 310 | 685 | 48 |
| `llama31-8b-q8--guarded-none--swap-both` | 8.54 | 10643 | 140 | 4 | yes | 2 |  | 780 | 877 | 565 | 685 | 48 |
| `llama31-8b-q8--guarded-none--swap-both-abstain` | 8.54 | 10643 | 140 | 4 | yes | 2 |  | 780 | 877 | 565 | 685 | 48 |
| `llama31-8b-q8--guarded-none--swap-llm` | 8.54 | 10643 | 140 | 4 | yes | 2 |  | 780 | 877 | 565 | 685 | 48 |
| `llama31-8b-q8--guarded-none--swap-regex` | 8.54 | 10643 | 140 | 4 | yes | 1.333 |  | 506 | 814 | 408 | 685 | 48 |
| `llama31-8b-q8--hardened-given--plain` | 8.54 | 10643 | 140 | 4 | yes | 1 | 9.90 | 438 | 627 | 211 | 526 | 40 |
| `llama31-8b-q8--hardened-given--swap-both` | 8.54 | 10643 | 140 | 4 | yes | 2 |  | 749 | 946 | 438 | 526 | 40 |
| `llama31-8b-q8--hardened-given--swap-both-abstain` | 8.54 | 10643 | 140 | 4 | yes | 2 |  | 749 | 946 | 438 | 526 | 40 |
| `llama31-8b-q8--hardened-given--swap-llm` | 8.54 | 10643 | 140 | 4 | yes | 2 |  | 749 | 946 | 438 | 526 | 40 |
| `llama31-8b-q8--hardened-given--swap-regex` | 8.54 | 10643 | 140 | 4 | yes | 1.333 |  | 547 | 716 | 281 | 526 | 40 |
| `llama31-8b-q8--hardened-none--plain` | 8.54 | 10643 | 140 | 4 | yes | 1 | 10.06 | 430 | 639 | 204 | 476 | 42 |
| `llama31-8b-q8--hardened-none--swap-both` | 8.54 | 10643 | 140 | 4 | yes | 2 |  | 740 | 964 | 428 | 476 | 42 |
| `llama31-8b-q8--hardened-none--swap-both-abstain` | 8.54 | 10643 | 140 | 4 | yes | 2 |  | 740 | 964 | 428 | 476 | 42 |
| `llama31-8b-q8--hardened-none--swap-llm` | 8.54 | 10643 | 140 | 4 | yes | 2 | 6.26 | 740 | 964 | 428 | 476 | 42 |
| `llama31-8b-q8--hardened-none--swap-regex` | 8.54 | 10643 | 140 | 4 | yes | 1.333 |  | 525 | 704 | 271 | 476 | 42 |
| `llama31-8b-q8--naive-given--plain` | 8.54 | 10643 | 140 | 4 | yes | 1 | 10.01 | 434 | 610 | 156 | 537 | 40 |
| `llama31-8b-q8--naive-none--plain` | 8.54 | 10643 | 140 | 4 | yes | 1 | 10.19 | 429 | 591 | 148 | 511 | 41 |
| `llama32-3b-q4--guarded-given--plain` | 2.02 | 4612 | 140 | 4 | yes | 1 | 17.83 | 213 | 256 | 318 | 1366 | 133 |
| `llama32-3b-q4--guarded-given--swap-both` | 2.02 | 4612 | 140 | 4 | yes | 2 |  | 405 | 452 | 575 | 1366 | 133 |
| `llama32-3b-q4--guarded-given--swap-both-abstain` | 2.02 | 4612 | 140 | 4 | yes | 2 |  | 405 | 452 | 575 | 1366 | 133 |
| `llama32-3b-q4--guarded-given--swap-llm` | 2.02 | 4612 | 140 | 4 | yes | 2 |  | 405 | 452 | 575 | 1366 | 133 |
| `llama32-3b-q4--guarded-given--swap-regex` | 2.02 | 4612 | 140 | 4 | yes | 1.333 |  | 246 | 444 | 418 | 1366 | 133 |
| `llama32-3b-q4--guarded-none--plain` | 2.02 | 4612 | 140 | 4 | yes | 1 | 18.30 | 210 | 257 | 310 | 1358 | 131 |
| `llama32-3b-q4--guarded-none--swap-both` | 2.02 | 4612 | 140 | 4 | yes | 2 |  | 396 | 432 | 565 | 1358 | 131 |
| `llama32-3b-q4--guarded-none--swap-both-abstain` | 2.02 | 4612 | 140 | 4 | yes | 2 |  | 396 | 432 | 565 | 1358 | 131 |
| `llama32-3b-q4--guarded-none--swap-llm` | 2.02 | 4612 | 140 | 4 | yes | 2 |  | 396 | 432 | 565 | 1358 | 131 |
| `llama32-3b-q4--guarded-none--swap-regex` | 2.02 | 4612 | 140 | 4 | yes | 1.333 |  | 245 | 421 | 408 | 1358 | 131 |
| `llama32-3b-q4--hardened-given--plain` | 2.02 | 4612 | 140 | 4 | yes | 1 | 23.20 | 174 | 259 | 211 | 1017 | 125 |
| `llama32-3b-q4--hardened-given--swap-both` | 2.02 | 4612 | 140 | 4 | yes | 2 |  | 321 | 423 | 438 | 1017 | 125 |
| `llama32-3b-q4--hardened-given--swap-both-abstain` | 2.02 | 4612 | 140 | 4 | yes | 2 |  | 321 | 423 | 438 | 1017 | 125 |
| `llama32-3b-q4--hardened-given--swap-llm` | 2.02 | 4612 | 140 | 4 | yes | 2 |  | 321 | 423 | 438 | 1017 | 125 |
| `llama32-3b-q4--hardened-given--swap-regex` | 2.02 | 4612 | 140 | 4 | yes | 1.333 |  | 220 | 314 | 281 | 1017 | 125 |
| `llama32-3b-q4--hardened-none--plain` | 2.02 | 4612 | 140 | 4 | yes | 1 | 23.74 | 174 | 268 | 204 | 996 | 125 |
| `llama32-3b-q4--hardened-none--swap-both` | 2.02 | 4612 | 140 | 4 | yes | 2 |  | 315 | 418 | 428 | 996 | 125 |
| `llama32-3b-q4--hardened-none--swap-both-abstain` | 2.02 | 4612 | 140 | 4 | yes | 2 |  | 315 | 418 | 428 | 996 | 125 |
| `llama32-3b-q4--hardened-none--swap-llm` | 2.02 | 4612 | 140 | 4 | yes | 2 | 13.25 | 315 | 418 | 428 | 996 | 125 |
| `llama32-3b-q4--hardened-none--swap-regex` | 2.02 | 4612 | 140 | 4 | yes | 1.333 |  | 209 | 309 | 271 | 996 | 125 |
| `llama32-3b-q4--naive-given--plain` | 2.02 | 4612 | 140 | 4 | yes | 1 | 23.46 | 173 | 261 | 156 | 1003 | 124 |
| `llama32-3b-q4--naive-none--plain` | 2.02 | 4612 | 140 | 4 | yes | 1 | 24.13 | 167 | 252 | 148 | 1006 | 126 |
| `qwen3-8b-q4--guarded-given--plain` | 5.03 | 7393 | 140 | 4 | yes | 1 | 10.03 | 386 | 461 | 309 | 698 | 72 |
| `qwen3-8b-q4--guarded-given--swap-both` | 5.03 | 7393 | 140 | 4 | yes | 2 |  | 713 | 800 | 557 | 698 | 72 |
| `qwen3-8b-q4--guarded-given--swap-both-abstain` | 5.03 | 7393 | 140 | 4 | yes | 2 |  | 713 | 800 | 557 | 698 | 72 |
| `qwen3-8b-q4--guarded-given--swap-llm` | 5.03 | 7393 | 140 | 4 | yes | 2 |  | 713 | 800 | 557 | 698 | 72 |
| `qwen3-8b-q4--guarded-given--swap-regex` | 5.03 | 7393 | 140 | 4 | yes | 1.333 |  | 434 | 798 | 408 | 698 | 72 |
| `qwen3-8b-q4--guarded-none--plain` | 5.03 | 7393 | 140 | 4 | yes | 1 | 10.00 | 392 | 460 | 301 | 683 | 71 |
| `qwen3-8b-q4--guarded-none--swap-both` | 5.03 | 7393 | 140 | 4 | yes | 2 |  | 708 | 813 | 547 | 683 | 71 |
| `qwen3-8b-q4--guarded-none--swap-both-abstain` | 5.03 | 7393 | 140 | 4 | yes | 2 |  | 708 | 813 | 547 | 683 | 71 |
| `qwen3-8b-q4--guarded-none--swap-llm` | 5.03 | 7393 | 140 | 4 | yes | 2 |  | 708 | 813 | 547 | 683 | 71 |
| `qwen3-8b-q4--guarded-none--swap-regex` | 5.03 | 7393 | 140 | 4 | yes | 1.333 |  | 434 | 810 | 397 | 683 | 71 |
| `qwen3-8b-q4--hardened-given--plain` | 5.03 | 7393 | 140 | 4 | yes | 1 | 12.84 | 317 | 498 | 194 | 542 | 65 |
| `qwen3-8b-q4--hardened-given--swap-both` | 5.03 | 7393 | 140 | 4 | yes | 2 |  | 577 | 765 | 408 | 542 | 65 |
| `qwen3-8b-q4--hardened-given--swap-both-abstain` | 5.03 | 7393 | 140 | 4 | yes | 2 |  | 577 | 765 | 408 | 542 | 65 |
| `qwen3-8b-q4--hardened-given--swap-llm` | 5.03 | 7393 | 140 | 4 | yes | 2 |  | 577 | 765 | 408 | 542 | 65 |
| `qwen3-8b-q4--hardened-given--swap-regex` | 5.03 | 7393 | 140 | 4 | yes | 1.333 |  | 417 | 606 | 259 | 542 | 65 |
| `qwen3-8b-q4--hardened-none--plain` | 5.03 | 7393 | 140 | 4 | yes | 1 | 13.42 | 307 | 483 | 187 | 530 | 67 |
| `qwen3-8b-q4--hardened-none--swap-both` | 5.03 | 7393 | 140 | 4 | yes | 2 |  | 564 | 750 | 398 | 530 | 67 |
| `qwen3-8b-q4--hardened-none--swap-both-abstain` | 5.03 | 7393 | 140 | 4 | yes | 2 |  | 564 | 750 | 398 | 530 | 67 |
| `qwen3-8b-q4--hardened-none--swap-llm` | 5.03 | 7393 | 140 | 4 | yes | 2 | 7.64 | 564 | 750 | 398 | 530 | 67 |
| `qwen3-8b-q4--hardened-none--swap-regex` | 5.03 | 7393 | 140 | 4 | yes | 1.333 |  | 394 | 566 | 249 | 530 | 67 |
| `qwen3-8b-q4--naive-given--plain` | 5.03 | 7393 | 140 | 4 | yes | 1 | 13.47 | 314 | 501 | 139 | 576 | 63 |
| `qwen3-8b-q4--naive-none--plain` | 5.03 | 7393 | 140 | 4 | yes | 1 | 13.55 | 306 | 492 | 131 | 525 | 65 |
| `qwen3-8b-q8--guarded-given--plain` | 8.71 | 10841 | 140 | 4 | yes | 1 | 8.03 | 500 | 602 | 309 | 682 | 44 |
| `qwen3-8b-q8--guarded-given--swap-both` | 8.71 | 10841 | 140 | 4 | yes | 2 |  | 859 | 975 | 557 | 682 | 44 |
| `qwen3-8b-q8--guarded-given--swap-both-abstain` | 8.71 | 10841 | 140 | 4 | yes | 2 |  | 859 | 975 | 557 | 682 | 44 |
| `qwen3-8b-q8--guarded-given--swap-llm` | 8.71 | 10841 | 140 | 4 | yes | 2 |  | 859 | 975 | 557 | 682 | 44 |
| `qwen3-8b-q8--guarded-given--swap-regex` | 8.71 | 10841 | 140 | 4 | yes | 1.333 |  | 573 | 902 | 408 | 682 | 44 |
| `qwen3-8b-q8--guarded-none--plain` | 8.71 | 10841 | 140 | 4 | yes | 1 | 8.49 | 464 | 565 | 301 | 698 | 47 |
| `qwen3-8b-q8--guarded-none--swap-both` | 8.71 | 10841 | 140 | 4 | yes | 2 |  | 828 | 930 | 547 | 698 | 47 |
| `qwen3-8b-q8--guarded-none--swap-both-abstain` | 8.71 | 10841 | 140 | 4 | yes | 2 |  | 828 | 930 | 547 | 698 | 47 |
| `qwen3-8b-q8--guarded-none--swap-llm` | 8.71 | 10841 | 140 | 4 | yes | 2 |  | 828 | 930 | 547 | 698 | 47 |
| `qwen3-8b-q8--guarded-none--swap-regex` | 8.71 | 10841 | 140 | 4 | yes | 1.333 |  | 523 | 851 | 397 | 698 | 47 |
| `qwen3-8b-q8--hardened-given--plain` | 8.71 | 10841 | 140 | 4 | yes | 1 | 9.47 | 458 | 661 | 194 | 492 | 41 |
| `qwen3-8b-q8--hardened-given--swap-both` | 8.71 | 10841 | 140 | 4 | yes | 2 |  | 784 | 1007 | 408 | 492 | 41 |
| `qwen3-8b-q8--hardened-given--swap-both-abstain` | 8.71 | 10841 | 140 | 4 | yes | 2 |  | 784 | 1007 | 408 | 492 | 41 |
| `qwen3-8b-q8--hardened-given--swap-llm` | 8.71 | 10841 | 140 | 4 | yes | 2 |  | 784 | 1007 | 408 | 492 | 41 |
| `qwen3-8b-q8--hardened-given--swap-regex` | 8.71 | 10841 | 140 | 4 | yes | 1.333 |  | 541 | 743 | 259 | 492 | 41 |
| `qwen3-8b-q8--hardened-none--plain` | 8.71 | 10841 | 140 | 4 | yes | 1 | 9.86 | 432 | 633 | 187 | 494 | 42 |
| `qwen3-8b-q8--hardened-none--swap-both` | 8.71 | 10841 | 140 | 4 | yes | 2 |  | 768 | 979 | 398 | 494 | 42 |
| `qwen3-8b-q8--hardened-none--swap-both-abstain` | 8.71 | 10841 | 140 | 4 | yes | 2 |  | 768 | 979 | 398 | 494 | 42 |
| `qwen3-8b-q8--hardened-none--swap-llm` | 8.71 | 10841 | 140 | 4 | yes | 2 | 5.94 | 768 | 979 | 398 | 494 | 42 |
| `qwen3-8b-q8--hardened-none--swap-regex` | 8.71 | 10841 | 140 | 4 | yes | 1.333 |  | 563 | 718 | 249 | 494 | 42 |
| `qwen3-8b-q8--naive-given--plain` | 8.71 | 10841 | 140 | 4 | yes | 1 | 9.64 | 454 | 665 | 139 | 503 | 39 |
| `qwen3-8b-q8--naive-none--plain` | 8.71 | 10841 | 140 | 4 | yes | 1 | 10.12 | 429 | 648 | 131 | 499 | 41 |

Verdicts/s is measured on calls that really ran, divided by the judge calls each verdict needs. GPU W is the power limit the laptop allowed while it was measured. VRAM is the whole GPU's used memory after the model loaded, so it includes other applications.
