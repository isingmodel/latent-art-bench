# Round 03 substantive revision

This version adds a retrospective held-scene prompted-name decision task on
retained embeddings. The complete three-rule plan and its implementation/tests
were frozen before computing translated outcomes. Baseline confusions had
already been inspected, so this is not an untouched confirmatory experiment.

## Added evidence

- All six configurations, two encoders and four original/audited × primary/
  development reference settings; 48 combinations and three fixed rules.
- Reference prototype baseline, scale-one pooled mean translation fitted on
  the other 13 scenes, and supervised generated class centroids fitted on those
  same scenes. Both repeats of the evaluated scene are jointly excluded.
- Complete predictions, scores, confusion counts, painter recalls, paired
  corrected/harmed counts and scene deltas. All harmful and null outcomes stay.
- On original primary references, translation changes CLIP accuracy by
  −5.36 to +12.50 percentage points (two declines, one tie, three gains) and CSD
  by +0.89 to +26.79 (six gains). Equal-configuration averages are +2.68 and
  +9.97 points. One CSD audited-primary sensitivity declines.
- Supervised generated prototypes exceed both reference rules in all 12
  original-primary combinations, with an explicitly different information budget.
- 39 constructed/protocol tests pass. An independent NumPy reconstruction
  verifies all 16,128 predictions across all 48 combinations and three rules,
  with exact counts and scalar scores agreeing within 3e-15. These repeated
  outputs reuse 672 named images; they are not new generated observations.
- Input binding: bdcf38bb09da53c890a1a62ce268c0336824ccadfb6ba90ee711bdaf1a6f1baf.
  Analysis: e1d1fbb924feb797f67e0907677511ed7c745335a4f2827e99d2f286e6be5448.


## Additional covariance sensitivity

A separately specified and hash-bound retrospective analysis quantifies all
six primary-D point curves at rho={0,.1,.25,.5,.75} under an assumed equal
normalized cross-repeat trace correlation. Repeat differences estimate V−C,
not V; the scenario correction is Dhat−rho qhat/(1−rho). It identifies no actual
correlation, imposes no plausible-range bound and does not shift intervals.
All 15 pair curves are retained. Three positive point-order crossings occur:
Image 1 vs Image 2 at .245650, Image 1 vs FLUX at .688029, and Nano Banana 2 vs
FLUX at .250751. Eight negative model-grid points remain flagged.

All 26 constructed/provenance tests and exact replay pass. Independent raw-array
reconstruction confirms all 84 scene D/q values, 30 model-grid points, 75 pair
points and 15 crossing classifications. The result hash is
`e5031ccad955b289b0d8dec110e8ee6b2ec39b43dfd8a6f2e150cc1dea1ce0c9`.
This answers a quantitative point-sensitivity question; it does not supply fresh
service evidence, a shared-fraction correction or a confidence guarantee.

## Manuscript changes

The abstract, contribution, main decision-task section and conclusion now
separate common proximity gain from cross-domain decision offsets and supervised
within-generator label structure. Translation changes class intercepts but leaves
artist-centered geometry unchanged; it is not the named-minus-generic causal
component. Related work acknowledges centroid-based domain adaptation.
Complete reporting tables also now include absolute learned gain components,
real-development confusions, generated confusions and learned scalar calibration.
Existing magnitude and source-comparison detail moved to the appendix to retain
the official eight-main-page layout; original evidence has not been deleted.

## Remaining limits

No new image collection, paid request, independent service session, artist panel,
human evaluation, shared-family prompt control or public complete pixel release
is added. The same fixed authored scenes and related encoders remain. Existing
baseline outcomes influenced the retrospective question. No new significance
family, uncertainty guarantee, algorithmic novelty or artistic-fidelity criterion
is claimed. Expected common-mode invariances alone do not constitute empirical
validation of every metric.

## Review and preservation

The complete final PDF and included sources are frozen under input/ before
review. Every review uses the unchanged scientific rubric and records its exact
PDF hash. Implementers and QA agents do not score their own work. No prior
recommendation, target threshold or another review is supplied to the reviewers.
All completed reviews from every round remain; the new scientific analysis,
not reporting polish alone, motivates this round. This is an AI scientific
review simulation, not an official conference decision.
