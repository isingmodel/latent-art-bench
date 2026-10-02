# Direction-only agreement, embedding intervals and configuration checks

Version 5, 2026-10-01. A **post-result analysis plan** written in response to the round-5 reviews
of the TMLR manuscript. It extends versions 1–4, whose outputs stay unchanged. Retained feature
vectors, embeddings and analysis outputs only.

## Values already known when this plan was written

All earlier results, including the recorded CLIP and CSD alignment ratios, Q and held-out rescaled
errors of `painter_learned_audit_v1` and the prespecified split of D into aligned-amplitude and
off-pattern parts in the primary output. The round-5 reviewers reported values they computed
themselves: the alignment ratio ranks GPT Image 2 highest in CLIP and CSD in about 99.7% and 100% of
paired scene resamples; Spearman correlations of about 0.94 (CLIP) and 0.89 (CSD) between alignment
ratio and recognition; rank correlations across representations of 0.60–0.77 for the alignment ratio
and −0.14 to 0.66 for D; Flare and Sunburst outputs more distant from each other than repeats in
about 92% (CLIP) and 100% (CSD) of scene × clause cells; leave-one-configuration-out ranges of about
0.91–0.99 (CLIP) and 0.84–0.98 (CSD) for the correlation of proximity gain with its shared term; a CSD
variance ratio of about 5.8; and paired-scene Student intervals for embedding D such as CSD GPT Image
1 [0.629, 0.842] and CLIP Sunburst [1.047, 1.225]. Nothing below was computed by this project
before the plan.

## Definitions

In each representation (31 features, CLIP, CSD), per configuration, with per-scene β_s, Q_s and D_s
as in the primary analysis and reference means from the full collections:

1. **Direction-only agreement.** Alignment ratio β̄/√Q̄ and held-out rescaled error (closed form:
   for each scene, κ fitted on the other scenes as max(0, β̄₋ₛ/Q̄₋ₛ)). From 5,000 paired scene
   resamples (seed 20261010), the share of resamples in which each configuration has the highest
   alignment ratio, the lowest held-out error and the lowest D. Spearman correlations across the six
   configurations between the alignment ratio and recognition accuracy (embeddings), and between
   representations for the alignment ratio and for D.
2. **Split of D.** The prespecified aligned-amplitude and off-pattern parts, (s₁−1)(s₂−1) and the
   cross-repeat product of the off-pattern residuals, computed in the embeddings as in the primary
   analysis; the 31-feature values must equal the recorded ones.
3. **Student intervals.** Unadjusted paired-scene Student 95% intervals (t with 13 degrees of
   freedom) for embedding β and D, and (10 degrees of freedom) for the content-matched embedding D
   of version 4 and the pooled-target D on the same 11 scenes.
4. **Repeat dependence.** Repeat noise, half the squared difference between the repeats' centered
   contrasts relative to H, in each representation, and the common repeat correlation ρ at which an
   error above 1 would fall to 1 under the model of `painter_repeat_covariance_v1`
   (bias ρ/(1−ρ) × repeat noise). The 31-feature noise must equal the recorded one.
5. **Proximity across configurations.** In CLIP and CSD, the Pearson correlation of the proximity
   gain with its shared and painter-specific terms across the six configurations and the variance
   ratio of the two terms, with leave-one-configuration-out ranges and 95% percentile intervals from
   5,000 paired scene resamples (seed 20261011).
6. **Distinct configurations.** For each pair of configurations and representation, the share of
   the 84 scene × clause cells in which the mean distance between the two configurations' images
   exceeds the mean distance between repeats within each configuration.
7. **Projection.** Coordinates of the reference differences r_a and of each configuration's
   scene- and repeat-averaged centered named means on the first two principal axes of the
   31-feature reference differences, for a descriptive figure (the protocol's reference PCA display
   of full distributions is not reproduced).

All are descriptive; intervals and shares describe dependence on the 14 authored scenes and add no
significance claims. Outputs: `reports/painter_tmlr_diagnostics_v5/analysis.json` and `REPORT.md`,
written once and replayed exactly, with constructed-data tests.
