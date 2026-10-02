# Content-matched agreement in the embeddings

Version 4, 2026-10-01. A **post-result analysis plan** written in response to the round-4 reviews
of the TMLR manuscript. It extends versions [1](../painter_tmlr_diagnostics_v1/PLAN.md),
[2](../painter_tmlr_diagnostics_v2/PLAN.md) and [3](../painter_tmlr_diagnostics_v3/PLAN.md),
whose outputs stay unchanged. Retained embeddings, feature vectors and analysis outputs only.

## Values already known when this plan was written

All earlier results, including the 31-feature content-matched errors of
`painter_specificity_review_v1` (pooled target on the 11 non-mixed scenes and title-derived class
targets) and the CLIP and CSD aligned amplitudes and errors against the pooled primary target
(diagnostics v3). All three round-4 reviewers asked for the embedding errors against
content-matched targets; none of their reviews reports such values. Nothing below was computed by
this project before the plan.

## Definitions

1. **Content-matched targets.** As in `painter_specificity_review_v1` (content block): for the 11
   scenes whose content class is water, built or land, each scene is compared with the
   title-derived class means of the four painters' reference works, centered across painters; the
   error normalizes by the mean over scenes of the class targets' spread. Computed in CLIP and CSD
   with the reference embeddings aligned by work identity (as in version 3), reporting the aligned
   amplitude β and the error D against the pooled target on the same 11 scenes and against the
   class targets. The 31-feature values are replayed and must equal the recorded ones.
2. **Scene intervals.** For the class-target β and D in each embedding: 95% percentile intervals
   from 5,000 resamples of the 11 scenes with replacement (seed 20261009), each scene keeping its
   class target, and the share of resamples with D below 1.
3. **How much of the reference differences is content.** For each representation, the mean over
   the 11 scenes of the squared distance between the class target and the pooled target, relative
   to the pooled spread H, and the mean class-target spread relative to H.

Intervals and shares describe dependence on the 11 authored scenes; they add no significance
claims. The class labels are title-derived; the AI-assigned visual labels are not used here.
Outputs: `reports/painter_tmlr_diagnostics_v4/analysis.json` and `REPORT.md`, written once and
replayed exactly, with constructed-data tests.
