# Readouts for the two further painter groups

Version 6, 2026-10-03. Written **during the second collection** (`psv3-r1`) and before any of its
images was measured, so it is fixed before the outcomes it summarizes. It applies definitions
already used for the four painters (versions 2 and 5 and the learned audit) to the two further
groups of `studies/painter_specificity_v3`. It extends versions 1–5, whose outputs stay unchanged,
and adds nothing to the prespecified tests H1 and H2 of the v3 protocol.

## Values already known when this plan was written

The four-painter results and the v3 reference panels and predictions
(`data/manifests/painter_specificity_v3/refs-20261002/predictions.json`). No output of the second
collection had been measured, and the v3 analysis (`reports/painter_specificity_v3`) did not exist.

## Definitions

In each representation (31 features, CLIP, CSD), for each group (century group, Hudson River
School: a six-arm slice with its own no-clause and generic arms) and each configuration, over the
scenes that the v3 analysis uses:

1. **Shared fraction intervals.** The 95% percentile interval of N/(N+B) from 5,000 scene
   resamples (seed 20261012), and the share of resamples in which the observed fraction is below
   the faithful benchmark recomputed on the same resample, as in version 2.
2. **Recognition** (CLIP and CSD). Each named image is assigned to the nearest unit-normalized
   reference prototype (mean reference embedding) among its group's four painters, ties to the
   first; macro accuracy over the four painters, as in the learned audit. Also among all eight
   painters of both groups (eight-way macro accuracy).
3. **Recognition and alignment.** Within each group and representation, the Spearman correlation
   across the six configurations between the alignment ratio (from the v3 analysis) and four-way
   recognition, as in version 5.
4. **Proximity across configurations** (CLIP and CSD). The centroid proximity gain and its shared
   term (Eq. 4), averaged over scenes for each configuration; the share of the gain carried by the
   shared term, and the Pearson correlation of the gain with each term across the six
   configurations, as in version 5 (without its intervals).

All are descriptive. Outputs: `reports/painter_tmlr_diagnostics_v6/analysis.json` and `REPORT.md`,
written once and replayed exactly, with constructed-data tests.
