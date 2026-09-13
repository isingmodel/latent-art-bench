# Review-driven reference-target diagnostics

This is a **post-result descriptive analysis** of retained vectors, responding
to the two supplied manuscript reviews. The [plan](../../studies/painter_specificity_review_v1/PLAN.md)
was recorded after the primary results were known. The original six slopes,
15 model contrasts, collection, measurements and report remain unchanged.

The [numerical record](analysis.json) binds source and input hashes. Its writer
refuses replacement; use `make review-check` for replay. The separate
[inspection manifest](inspection.json) identifies 36 generated examples and four
reference examples used in the current PDF. No generation, acquisition or feature
extraction was performed.

## Magnitude, alignment and scene dependence

| Model | Primary D | Aggregate D | Scene variation | Q | Corrected alignment | Held-scene calibrated D |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 1 | 1.572 | 1.239 | .333 | 2.449 | .600 | .645 |
| GPT Image 2 | 1.226 | 1.044 | .182 | 2.223 | .670 | .554 |
| GPT Image 2.5 Flare | 1.738 | 1.483 | .255 | 2.281 | .511 | .741 |
| GPT Image 2.5 Sunburst | 1.641 | 1.337 | .305 | 2.289 | .545 | .706 |
| Nano Banana 2 | 1.109 | .723 | .387 | .994 | .444 | .832 |
| FLUX.2 Max | .801 | .761 | .040 | .741 | .546 | .714 |

D equals aggregate mismatch plus cross-scene contrast variation, and also
1 − 2 beta + Q. The variation term is not necessarily artistic error.
Corrected alignment is beta/sqrt(Q), not a perceptually validated style score.
Each calibration scalar is nonnegative, fitted on the other 13 scenes and
assessed on the omitted scene. The counterfactual changes feature vectors and
need not describe realizable images. No model-ranking tests were added.

## Artist coverage

The reference components explain 66.34%, 20.64% and 13.01% of centroid variation.
Every model responds more strongly along the first than the other components.
Monet–Sisley slopes are .074, .402, −.011, −.249, −.044 and .129 in model order.
Removing Cézanne lowers FLUX's slope to .096 and GPT Image 2's to .651.
The correct label assignment has the lowest error for GPT Image 1, GPT Image 2
and FLUX. The other three have lower point error after swapping Monet and Sisley;
these are descriptive ranks among 24 assignments, not permutation p-values.

## Reference controls and weighting

On the 11 water/built/land briefs, class-specific errors are 1.366, 1.130, 1.539,
1.525, .948 and .786. These use their own target magnitude, 7.413; primary H is
5.915. Four-class genuine reference contrasts differ from the pooled target by
.438 H on average, including finite-sample mean error.

Across 1,000 stratified disjoint half-splits, median real/real errors and central
95% simulation ranges are:

| Control | Median | Central 95% range |
| --- | ---: | --- |
| Pooled real draws, pooled target | .233 | [−.758, 1.380] |
| Class-stratified real draws, pooled target | .721 | [−.554, 2.400] |
| Class-stratified real draws, class target | .702 | [−.248, 1.946] |

These distributions are not confidence intervals, calibrated artistic thresholds,
source-held-out comparisons or direct statistical comparisons with the model
scores. Target-estimation error and sparse repeat sampling contribute to their
width. Title classes and source artifacts remain shared limitations.

FLUX retains the smallest point error under equal-family weighting, a covariance
metric fitted on the separate 221-work development panel with fixed 50% shrinkage,
and every single-coordinate deletion. All coordinate contributions and deletion
values are retained, including negative terms. Persistence does not identify the
correct artistic weighting.

## Shared response, energy and uncertainty

The within-scene common fraction is 88.6–97.2%, versus 82.5–95.7% after global
averaging. These are cross-repeat squared-feature-change fractions, not fractions
of images or style. Centering removes only additive common changes.

A generated same-scene diagonal correction estimates energy between the uniformly
mixed scene-conditional outputs and the fixed empirical reference. Cross-scene
terms are already independent; no pooled IID correction is substituted. The
21 negative named-minus-generic signs remain unchanged.

In 5,000 synthetic repetitions per scenario, the 21-interval family has coverage
95.96% (Gaussian), 97.42% (heavy-tailed/heteroskedastic), 99.68% (fixed interactions),
and .04% (shared-state dependence). The last violates the repeat/scene independence
assumptions and biases D upward by about .25. These specified simulations are not
a fitted model of the actual API, whose noise distribution remains unverified.

## Image-inspection findings and unresolved validity

Two selected reference files contain calibration strips retained in primary
full-frame measurements: Sisley `Q104774055` and Pissarro `Q104773676`.
Cézanne `Q17490974` depicts a street despite its title-derived water class.
These four rule-selected examples do not establish contamination prevalence
or quantify its effect. The manuscript now makes the problem explicit.
A full source/region audit and any corrected extraction require a new scope.

See [current status](../../docs/STATUS.md#outstanding-review-requests)
for the remaining review requests. No human evaluation, learned-feature
validation, exact-pixel archive or independent replication is implied by replay.
