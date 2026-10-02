# Genuine-painting controls without repeated works, embedding intervals and family contrasts

Version 3, 2026-10-01. A **post-result analysis plan** written in response to the round-3 reviews
of the TMLR manuscript. It extends versions
[1](../painter_tmlr_diagnostics_v1/PLAN.md) and [2](../painter_tmlr_diagnostics_v2/PLAN.md),
whose outputs stay unchanged. Retained vectors, embeddings and analysis outputs only.

## Values already known when this plan was written

All earlier results. The round-3 reviewers reported values they computed themselves: genuine-
painting control means of 0.111, 0.252 and 0.373 in the 31 features when the two pseudo-repeats
use distinct works (against the recorded 0.234, 0.753 and 0.731 with replacement); genuine
controls above D = 1 in about 29–35% of splits; CSD errors below 1 in 100% of scene resamples for
GPT Image 1, GPT Image 2, Flare and FLUX.2 Max; five of six CLIP errors above 1; a texture-minus-
spatial difference of −2.9 points [−14.1, +10.2] (texture below spatial in about 68% of
resamples) and texture below color in about 99.6%; normalized-prototype shares within 0.5 points
of the unnormalized ones. Nothing below was computed by this project before the plan.

## Definitions

1. **Genuine-painting controls with distinct works.** As in
   `painter_specificity_review_v1.real_controls` (1,000 random half-splits within painter, or
   within painter and content class; the smaller half estimates the target), except that the two
   pseudo-repeats of each painter and pseudo-scene are two *distinct* works drawn without
   replacement from the held-out half (seed 20261005). Three variants: pooled sampling against the
   pooled target; content-class sampling against the pooled target; content-class sampling against
   content-class targets. Computed in the 31 features, CLIP and CSD (with the embeddings' own
   reference vectors, aligned by work identity), reporting the mean, the central 95% range and the
   share of splits with D above 1. The recorded with-replacement version is also replayed in CLIP
   and CSD for comparison.
2. **Embedding agreement intervals.** For CLIP and CSD, the aligned amplitude β and error D with
   95% intervals from 5,000 scene resamples (seed 20261006) and 1,000 reference resamples (seed
   20261007), and the share of 2,000 joint resamples (seed 20261008) with D below 1.
3. **Normalized-prototype proximity.** The shared share of the proximity gain when unit-normalized
   prototypes replace the unnormalized means in Equation 4 (still a linear score).
4. **Family contrasts.** From 5,000 paired scene resamples (seed 20261002, as in version 2), the
   mean over configurations of texture − color, texture − spatial and color − spatial shared
   fractions: point values, 95% intervals and the share of resamples below zero; draws with a
   non-positive denominator in any configuration are dropped and counted.

Intervals and shares describe dependence on the authored scenes or finite reference panels; they
add no significance claims. Outputs: `reports/painter_tmlr_diagnostics_v3/analysis.json` and
`REPORT.md`, written once and replayed exactly, with constructed-data tests.
