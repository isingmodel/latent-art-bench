# Benchmarks without the domain gap, uncertainty, pair intervals and feature separability

Version 2, 2026-10-01. A **post-result analysis plan** written in response to the round-2
reviews of the TMLR manuscript. It extends
[`painter_tmlr_diagnostics_v1`](../painter_tmlr_diagnostics_v1/PLAN.md), whose outputs stay
unchanged. Retained feature vectors, embeddings and analysis outputs only; no image is
generated, acquired or re-measured.

## Values already known when this plan was written

All results of v1 and the earlier analyses. The round-2 reviewers also reported values they
computed themselves, so these outcomes are partly known: the exact-differences fraction
N/(N+H) of 84.0, 83.3, 83.3, 79.9, 57.6 and 84.2% in the 31 features and its prototype-gain
analogue of 60.6–73.0% (CLIP) and 52.5–67.4% (CSD); a scene-bootstrap interval of about
77.6–94.2% for FLUX.2 Max's shared fraction, with the observed-below-faithful ordering reversed
in about 15% of resamples; a reference-resampling interval of about [−0.45, 0.21] for
Sunburst's Monet–Sisley β; a 31-feature nearest-centroid accuracy of 49.8% on the development
works (Monet 40%, Sisley 31%); and CSD scene-deletion ranges for GPT Image 2 of 52.4–55.6%.
Nothing below was computed by this project before the plan.

## Definitions

Notation follows the v1 plan. For each configuration and representation (31 features, the
three feature families, CLIP, CSD):

1. **Exact-differences benchmark.** Keep the observed shared change and replace the
   between-name differences by the reference differences: N/(N+H). In embeddings, for the
   proximity gain of Equation 4, S/(S+H/4) with S the observed shared term. Also report the
   coverage N/N* (squared shared change relative to the faithful one).
2. **Scene bootstrap.** 5,000 resamples of the 14 scenes with replacement (seed 20261002),
   the same scenes for every configuration and arm. Percentile 95% intervals for the observed,
   faithful and exact-differences fractions, for observed minus faithful, and the frequency with
   which observed < faithful; the same for the three prototype-gain shares in CLIP and CSD.
3. **Reference resampling.** 1,000 resamples of the reference works within painter (seed
   20261003), generated vectors fixed: intervals for the faithful and exact-differences
   fractions and for the prototype-gain shares.
4. **Painter pairs.** For each pair (a, b), the aligned amplitude
   mean over scenes and repeats of ⟨z_a − z_b, μ_a − μ_b⟩/‖μ_a − μ_b‖² and the cross-repeat
   error mean over scenes of ⟨d₁ − q, d₂ − q⟩/‖q‖², with q = μ_a − μ_b, in the 31 features,
   CLIP and CSD; scene-bootstrap and reference-resampling intervals as above.
5. **Joint resampling of D.** 2,000 draws resampling scenes and reference works together (seed
   20261004); for each configuration, the frequency with which the 31-feature D is below 1.
6. **Feature separability.** Nearest reference mean (Euclidean, 31 standardized features) for
   each of the 221 development works: macro accuracy and per-painter accuracy, next to the
   embedding values already reported.
7. **Feature families across configurations.** The mean over the six configurations of each
   family's shared fraction, with scene-bootstrap intervals, and each configuration's ordering
   of families.
8. **Per-painter proximity.** For each painter, the gain (g_a − g_g)ᵀμ_a and its split into
   (ḡ − g_g)ᵀμ_a and (g_a − ḡ)ᵀμ_a, in CLIP and CSD.
9. **SD-Turbo benchmarks.** With the SD-Turbo baseline (which already requests an oil painting)
   as the generic arm and cross-block products, the faithful fraction 4U(t)/(4U(t)+H) with
   t = μ̄ − baseline mean, and the exact-differences fraction C/(C+H), for all 31 features and
   each family.

Intervals describe dependence on the authored scenes or the finite reference panels; they are
not confidence intervals for new scenes or painters and add no significance claims. Outputs:
`reports/painter_tmlr_diagnostics_v2/analysis.json` and `REPORT.md`, written once and replayed
exactly; constructed-data tests accompany the module.
