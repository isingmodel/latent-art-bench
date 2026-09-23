# Retrospective within-cell request-timing diagnostic v1

Written before inspecting feature-outcome associations with request time. This is
an additional descriptive diagnostic of the completed six-configuration,
1,008-image collection. It does not extend the original 21-endpoint test family.
No images will be generated and no frozen input will be edited.

## Question and design

Do separately requested repeats exhibit a reproducible linear feature drift over
the short elapsed times separating requests within the same model/scene/arm cell?
All six arms enter this diagnostic. For each requested configuration there are
14 scenes × 6 arms = 84 paired differences in the same 31 development-IQR units
as the primary analysis.

For pair i, retain the arbitrary recorded repeat labels and compute

- `delta_z_i = z_(repeat 1) - z_(repeat 0)`;
- `delta_t_i = (start_time_(repeat 1) - start_time_(repeat 0)) / 60`, in minutes.

Fit one 31-coordinate slope per model through the origin:
`b = sum_i(delta_t_i * delta_z_i) / sum_i(delta_t_i ** 2)`.
Swapping both repeat labels leaves the fit and all squared-error summaries
unchanged. Differencing removes stable model/scene/arm means. The model assumes
one common within-cell drift vector per configuration and need not describe
nonlinear changes or arm-specific drift.

## Fixed summaries

1. Full-panel slope vector in development-IQR units per minute and its Euclidean
   norm multiplied by 10 minutes. The norm is descriptive and noise can inflate it.
2. Leave-one-scene-out prediction: estimate b from the other 13 scenes (78 pairs)
   and predict the six held-out paired differences. Pool squared errors over all
   84 held-out pairs. Compare with the zero-difference predictor using
   `(MSE_zero - MSE_held_out) / MSE_zero`. Negative values mean the fitted drift
   predicts less well. This predictive gain is the primary diagnostic summary.
3. The RMS norm of the fitted held-out drift at the observed pair time gaps and
   the observed RMS repeat-difference norm, in standardized feature units.
4. Delete each scene, refit the complete cross-validation on the remaining 13,
   and report the range of predictive gains. Also retain every fold and slope.

No p-values, confidence intervals, significance labels, or model-ranking tests
will be added. Overlapping folds are dependent. Scene-deletion ranges are
sensitivity descriptions, not confidence intervals. Results do not select new
models, endpoints, filters, or tests.

## Timing and interpretation limits

The observed starts follow the fixed randomized schedule with one contiguous
72-request block per scene. Within each block model/arm/repeat combinations were
randomized, but request times also reflect the three-worker dispatcher and service
latency. The 14 scenes are therefore confounded with global collection time.
A regression of score on global time would not separate content from drift.

A positive held-out gain would flag predictable time-associated repeat changes,
not identify a service mechanism. A zero or negative gain would mean this
particular common linear drift model lacks demonstrated predictive value; it
would not establish independence, stationarity, absence of dependence, or absence
of more complex changes. Do not automatically detrend primary scores: estimating
and sharing a nuisance slope can alter the cross-repeat estimator's interpretation.

## Frozen inputs and replay

Join `requests.jsonl`, `attempts.jsonl`, and `measurements.jsonl` by request ID in
`data/manifests/painter_specificity_v2/psv2-20260911/`. Require exactly one successful
attempt and two labeled repeats in each complete cell. Use start events (not
response completion order). Standardize with the existing development scaler.
Store input SHA-256 values, this plan's SHA-256, implementation hash, and all
computed summaries in a new report. A check mode must replay exactly.

## Meaningful verification

Use synthetic data to verify recovery of a known shared linear drift and
out-of-scene prediction; verify invariance to joint swapping of repeat differences
and signed gaps; reject incomplete cells or malformed dimensions. These tests
address the estimand and schedule join, not only formatting.
