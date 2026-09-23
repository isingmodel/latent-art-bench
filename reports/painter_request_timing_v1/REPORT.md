# Retrospective within-cell request-timing diagnostic

One common 31-coordinate linear drift vector is fitted per requested configuration. The 84 paired differences per configuration include all six arms. Stable scene/arm means cancel within each pair. Time is signed repeat-1 minus repeat-0 start time.

| Configuration | 10-minute fitted slope norm | Repeat RMS | Predicted drift RMS | Held-out gain (%) | Scene-deletion gain range (%) |
|---|---:|---:|---:|---:|---:|
| GPT Image 1 | 0.863 | 2.991 | 0.421 | -0.86 | -1.87, -0.62 |
| GPT Image 2 | 0.267 | 2.299 | 0.209 | -3.38 | -3.92, -0.87 |
| GPT Image 2.5 Flare | 0.299 | 1.636 | 0.201 | -2.28 | -3.82, -1.19 |
| GPT Image 2.5 Sunburst | 0.243 | 1.631 | 0.153 | -2.62 | -3.01, -2.05 |
| Nano Banana 2 | 0.605 | 3.322 | 0.326 | -0.72 | -2.02, -0.43 |
| FLUX.2 Max | 0.743 | 3.141 | 0.350 | -1.19 | -1.80, -0.99 |

RMS quantities and the 10-minute slope norm use Euclidean combinations of development-IQR feature coordinates. The fitted slope norm can be inflated by noise. Predictive gain is `(MSE_zero - MSE_held_out) / MSE_zero`; negative values favor the zero-difference predictor. Each held-out scene uses a slope fitted on the other 13 scenes. Scene deletion refits the entire procedure.

## Interpretation limits

Held-out gain assesses a common linear short-window drift model; it does not test service independence or rule out nonlinear, arm-specific, or shared-state effects. Scene-deletion ranges are sensitivities, not confidence intervals. No primary scores are detrended or refit.

The planned start order matches the observed start order. Scenes were contiguous blocks of 72 randomized requests, so global collection time is confounded with scene identity. Recorded repeat 1 was later in 271 pairs and earlier in 233 pairs. The dispatcher and service latency also affect elapsed gaps. These are descriptive associations, not causal time effects.

There are no new hypothesis tests or confidence intervals. Overlapping folds are dependent, and the range of scene-deletion gains is not a confidence interval. A lack of predictive gain cannot establish stationarity or independent requests.

## Replay

`uv run --locked python -m latent_art_bench.painter_request_timing_v1 check`

The adjacent analysis JSON retains plan/input hashes, all slopes, folds, deletions, signed gaps, and request-pair identities. No original data or primary score is changed.
