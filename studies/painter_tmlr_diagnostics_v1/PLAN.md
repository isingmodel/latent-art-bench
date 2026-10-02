# Reference values, direction, representation sensitivity and readout stability

Version 1, 2026-10-01. A **post-result analysis plan**, written in response to the
round-1 reviews of the TMLR manuscript (`reports/tmlr_review_v1/round_01/`). It is
not a preregistration: every earlier result is known. It uses only retained
feature vectors, embeddings and analysis outputs; no image is generated, acquired
or re-measured, and no earlier result is modified.

## What was known when this plan was written

All results in `painter_specificity_v2`, `painter_specificity_review_v1/v2/v3`,
`painter_learned_audit_v1`, `painter_prototype_transfer_v1`,
`painter_cross_cohort_v1`, `painter_reference_quality_v1` and
`painter_repeat_covariance_v1`, and the round-1 reviews. None of the quantities
defined below had been computed.

## Data

The complete 6-configuration by 14-scene by 2-repeat by 6-arm panel of 31
standardized full-frame features and the corrected 649-work reference panel,
loaded by `painter_specificity_measurement_v1.workflow.load`; the development
panel and weights from `painter_specificity_review_v1.labels_and_development`;
and the original-source CLIP and CSD embeddings from
`painter_learned_audit_v1.arrays`. Arm order is free, generic, Monet, Sisley,
Pissarro, Cezanne.

Notation, per configuration and representation: z̄[a,k] is arm a averaged over
scenes in repeat k; c[k] = mean of the four named z̄ minus the generic z̄ (the
shared change beyond the generic clause); e[a,k] = named z̄ minus the mean of the
four named z̄; μ[a] are reference means, μ̄ their mean, r[a] = μ[a] − μ̄,
H = Σ‖r[a]‖². All squared magnitudes of generated quantities use cross-repeat
products ⟨u[1],v[2]⟩, symmetrized when u ≠ v. Negative values are retained;
ratios are reported only for positive denominators.

## 1. Reference values for the shared fraction

- **Exchangeable null.** If the four named-minus-generic shifts were independent
  with mean zero and equal expected squared size, E[N]/(E[N]+E[B]) = 1/4. State
  this analytically; no computation.
- **Faithful-imitation value.** Replace each named mean by its reference mean,
  keeping the observed generic mean. With t[k] = μ̄ − z̄[generic,k]:
  N* = 4⟨t[1],t[2]⟩, B* = H, fraction N*/(N*+H). Report per configuration in the
  31 features, each feature family (with that family's H), CLIP and CSD. This
  value includes the difference between reproduction photographs and generated
  images, and the content difference between the reference subjects and the 14
  scenes; the report must say so.

## 2. Direction of the shared change and centroid proximity

- Corrected cosine between c and t:
  [⟨c[1],t[2]⟩+⟨c[2],t[1]⟩] / [2·sqrt(⟨c[1],c[2]⟩⟨t[1],t[2]⟩)], and the
  projection ratio λ = [⟨c[1],t[2]⟩+⟨c[2],t[1]⟩] / [2⟨t[1],t[2]⟩] (fraction of the
  generic-to-reference-centroid displacement covered along its direction).
- Centroid proximity gain: the mean over painters of the reduction in squared
  Euclidean distance from the scene-averaged generated mean to the painter's
  reference mean, from the generic clause to the named clause. With z̄[a] = z̄[g]
  + c + e[a], it splits exactly into a shared term 2⟨c,t⟩ − ‖c‖² and a
  between-name term ½Σ⟨e[a],r[a]⟩ − ¼Σ‖e[a]‖², estimated with cross-repeat
  products. Report both terms and the shared fraction of the gain when the gain
  is positive, in the 31 features, each family, CLIP and CSD.

## 3. Representation sensitivity of the main collection's shared fraction

For each configuration: N, B, N/(N+B), N/H and B/H in the color (11), spatial (8)
and texture (12) families, each with its own H; N/(N+B) under the equal-family
and development-covariance weightings of `painter_specificity_review_v1`
(the same linear maps, applied to generated vectors and reference means); and the
within-scene version of N/(N+B) against the generic baseline.

## 4. Stability of the readouts

For CLIP and CSD: named-minus-generic proximity gain, its shared fraction,
recognition macro accuracy (nearest unit-normalized reference prototype) and
centered error D; for the 31 features: D. Report (a) the range over the 14
single-scene deletions and (b) a scene bootstrap with 5,000 resamples of the 14
scenes with replacement (seed 20261001), recording for each readout how often
each configuration is best (largest gain or accuracy, smallest D) and, for every
pair of configurations, how often the first is better. These describe dependence
on the authored scenes; they are not confidence intervals for new scenes and add
no significance claims.

## Outputs and checks

`reports/painter_tmlr_diagnostics_v1/analysis.json` and `REPORT.md`, written once
(`analyze`) and replayed exactly (`check`). Constructed-data tests check the
exchangeable null, the proximity identity, the cross-repeat corrections, the
faithful-imitation value when named means equal reference means, and bootstrap
determinism. Nothing here changes the prespecified inferential family.

## Addendum A, 2026-10-01, before running the module

After the plan above was written, and before any quantity in it was computed by
this analysis, the round-1 empirical review reported values it had computed
itself from the retained vectors (so these outcomes are partly known):
4⟨t[1],t[2]⟩/H of 19.6, 8.3, 5.6, 6.6, 12.3 and 9.5 in model order; a cosine
between the shared change and t of 0.57–0.86; a faithful-imitation shared
fraction of 85–95%; texture shared fractions of 48.6–79.8%; a leave-one-feature-out
range of 64.8–89.6%; and a fraction of N along the generic shift of about 0 to 0.4.
The following quantities are added, defined before this module is run:

- **Along the generic shift.** With g[k] = z̄[generic,k] − z̄[free,k]: the
  fraction of N along g, 4·xrep(c,g)²/(xrep(g,g)·N) when both are positive, and the
  corrected cosine between c and g.
- **Leave-one-feature-out.** N/(N+B) after deleting each of the 31 coordinates, and
  each coordinate's contribution to N (4·xrep of that coordinate).
- **Finite-sample correction of H.** H_c = H − (3/4) Σ_a tr(S_a)/n_a, with S_a the
  unbiased within-painter covariance of the reference vectors and n_a their count;
  report H_c/H and the corresponding rescaled aligned amplitude β·H/H_c. This is a
  sensitivity of the reference normalizer, not a change to the primary analysis.
- **Repeat disagreement.** Per configuration, the noise power
  ½·Σ_{s,a}‖d[s,a,1] − d[s,a,2]‖²/(S·H) of the centered differences, as a
  noise-to-signal description.

## Addendum B, 2026-10-01, before running the module

The round-1 methods review, received after Addendum A and before this module was
run, also reported values it computed: a faithful-imitation shared fraction of
84.8–95.2% in the 31 features and Equation-4 faithful fractions of 71.3–82.9%
(CLIP) and 48.3–75.7% (CSD); from its own scene bootstrap, that FLUX.2 Max's lower
recognition than Flare and Sunburst is stable while the largest CLIP and CSD gains
and the lowest CSD error are not. No quantity is added or changed by this
addendum. The genuine-painting control for D and the prespecified reference
resampling it points to already exist (`painter_specificity_review_v1` and the
primary analysis) and are reported from those records, not recomputed here.
