# Readouts requested by review of the second collection

Version 7, 2026-10-04. Written after round 1 of the second review series
(`reports/tmlr_review_v2/round_01/`). That round found the manuscript's closeness claim too
strong. It extends versions 1–6, whose outputs stay unchanged, and adds nothing to the
prespecified tests H1 and H2 of `studies/painter_specificity_v3`. It reads the second collection
(`psv3-r1`) and its reference panels, the v3 analysis and the diagnostics-v2 analysis. It modifies
none of them. All readouts are descriptive.

## Values already known when this plan was written

Every output of the v3 analysis and of diagnostics v6. Reviewers in that round also computed the
following from them:

- the Spearman correlation of H2 restricted to pair types in the 31 features: 0.78 within the
  century group, 0.74 across the groups and 0.09 within the Hudson River School;
- the mean over configurations of the faithful benchmark's century-minus-Hudson difference,
  −30.9 points against the observed −72.7;
- the Impressionists' and the Hudson River School's mean observed (about 72.9% vs 94.4%) and
  faithful (about 89.9% vs 93.6%) shared fractions;
- 90 of the 5,000 H1 resamples with N + B ≤ 0, all for FLUX.2 Max on the Hudson River School.

The intervals in item 2 below had not been computed.

## Definitions

In each representation (31 features, CLIP, CSD), on the scenes used by the v3 analysis:

1. **H2 by pair type.** From the recorded pair distances of H2 (reference distances corrected for
   panel size, and cross-repeat name distances per configuration), compute the Spearman
   correlation over the 6 pairs within the century group, the 6 pairs within the Hudson River
   School and the 16 pairs across the groups. Compute each per configuration and averaged over
   configurations. Recomputing over all 28 pairs must reproduce the recorded H2 statistic. No
   p-values: within a group, only 24 relabellings exist.
2. **Closeness-only contrast.** For each configuration and group, take the observed shared fraction
   N/(N+B) and the faithful benchmark N*/(N*+H). The faithful benchmark is what closeness alone
   predicts, i.e. how close the painters are to one another relative to their distance from the
   generic outputs. Report the century-minus-Hudson difference of the faithful values and the
   excess, meaning the observed difference minus the faithful difference, per configuration and
   averaged over configurations. The averages get 95% percentile intervals from 5,000 paired scene
   resamples (seed 20261004). The same scenes are drawn for both groups and every configuration,
   as in H1, and each resample recomputes both fractions. The point values must reproduce the v3
   analysis.
3. **Matched closeness.** The Impressionists (first collection, 14 scenes, their own generic arm)
   and the Hudson River School (second collection) have similar reference spreads in the 31
   features. Report both groups' observed and faithful shared fractions per configuration, and the
   averages over configurations of the Impressionists-minus-Hudson differences, read from the
   recorded analyses. The groups come from different collections, so no interval is computed.
4. **Census of the H1 resamples.** Replay the resampling of the frozen H1 code with its seed
   (20261003, 5,000 draws). For each configuration and group, count the draws in which N + B ≤ 0
   and those in which N/(N+B) lies outside [0, 1]. The replay must reproduce the recorded H1
   interval.

## Outputs

`reports/painter_tmlr_diagnostics_v7/analysis.json` and `REPORT.md`, each written once and replayed
exactly by `check`, with constructed-data tests.
