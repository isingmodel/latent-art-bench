# TMLR revision diagnostics, version 2

Retrospective analysis under
[the plan](../../studies/painter_tmlr_diagnostics_v2/PLAN.md). Percentile intervals
describe dependence on the 14 authored scenes or the finite reference panels.

## Shared fraction, 31 features (%)

| Configuration | observed [scenes] | faithful [scenes] | exact differences | obs < faithful |
| --- | --- | --- | --- | ---: |
| GPT Image 1 | 71.3 [67.6, 74.9] | 95.2 [94.4, 96.0] | 84.0 | 100.0 |
| GPT Image 2 | 70.9 [66.5, 75.6] | 89.3 [88.0, 91.6] | 83.3 | 100.0 |
| GPT Image 2.5 Flare | 71.1 [66.7, 76.7] | 84.8 [81.4, 90.4] | 83.3 | 100.0 |
| GPT Image 2.5 Sunburst | 66.7 [63.3, 71.1] | 86.9 [82.7, 91.3] | 79.9 | 100.0 |
| Nano Banana 2 | 69.1 [52.0, 75.8] | 92.5 [90.3, 94.4] | 57.6 | 100.0 |
| FLUX.2 Max | 88.4 [76.8, 94.2] | 90.4 [84.4, 95.4] | 84.2 | 84.1 |

## Proximity-gain shares, CLIP (%)

| Configuration | observed [scenes] | faithful | exact differences |
| --- | --- | ---: | ---: |
| GPT Image 1 | 74.5 [69.9, 78.2] | 71.3 | 60.6 |
| GPT Image 2 | 73.2 [69.7, 75.9] | 76.0 | 67.7 |
| GPT Image 2.5 Flare | 78.8 [76.4, 80.7] | 77.1 | 67.5 |
| GPT Image 2.5 Sunburst | 77.7 [76.3, 79.2] | 77.6 | 69.4 |
| Nano Banana 2 | 83.8 [82.0, 85.3] | 82.9 | 73.0 |
| FLUX.2 Max | 81.7 [77.4, 84.9] | 80.7 | 66.2 |

## Proximity-gain shares, CSD (%)

| Configuration | observed [scenes] | faithful | exact differences |
| --- | --- | ---: | ---: |
| GPT Image 1 | 72.7 [69.7, 75.6] | 70.4 | 66.0 |
| GPT Image 2 | 54.2 [47.4, 59.3] | 48.3 | 52.5 |
| GPT Image 2.5 Flare | 65.0 [62.1, 67.6] | 62.7 | 59.9 |
| GPT Image 2.5 Sunburst | 67.4 [64.6, 69.6] | 65.4 | 64.0 |
| Nano Banana 2 | 79.7 [78.5, 80.8] | 75.7 | 67.3 |
| FLUX.2 Max | 77.6 [73.7, 80.3] | 71.0 | 67.4 |

31-feature development recognition: macro 49.8%, per painter 39.6, 30.6, 54.2, 75.0

Joint resampling, P(D < 1): GPT Image 1 0.006, GPT Image 2 0.099, GPT Image 2.5 Flare 0.000, GPT Image 2.5 Sunburst 0.001, Nano Banana 2 0.334, FLUX.2 Max 0.943

SD-Turbo: all31 faithful 92.5, exact 67.4, color faithful 79.7, exact 56.4, spatial faithful 96.8, exact 83.3, texture faithful 89.8, exact 46.5
