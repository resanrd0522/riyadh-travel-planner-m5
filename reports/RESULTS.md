# M5 evaluation results

Offline checks passed. No model calls were made.

Historical V2 figures below are verified aggregate arithmetic, not rescored original outputs.

| Metric | Mean (%) | Run SD (n=60) | Seed-mean SD (n=3) |
|---|---:|---:|---:|
| APM | 96.8335 | 8.4683 | 0.0000 |
| RBM | 100.0000 | 0.0000 | 0.0000 |
| HBM | 100.0000 | 0.0000 | 0.0000 |
| IFR | 85.0000 | 36.0085 | 0.0000 |
| RTC | 100.0000 | 0.0000 | 0.0000 |

All SDs use the sample definition (n-1). Per-case and case-mean variation are in evaluation.json.

## Verified separately

- 20 later supplementary itineraries rescored; all 80 metric comparisons agree with historical seed-11 score rows. Output identity is not established.
- 60 case/tool contracts passed (120 offline tool calls including repeatability checks).
- G05/G08/G15 have APM ceilings of 90%, 66.67% and 80%; structural IFR need not be zero.

## Remaining limits

- Original V2 itineraries and full tool traces remain missing.
- Ground-truth acceptance rules await team human signoff.
- No provider-side seed effectiveness or current model availability was tested.
- Historical cost, token use and latency are unavailable and are not estimated.
