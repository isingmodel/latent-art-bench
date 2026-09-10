# Painter distribution exploration v1

This is a user-requested post-hoc exploration, specified after the distance results were seen.
It is not a preregistration, a replacement primary analysis, or a new generation study.
Use only the already exposed 649 reference paintings and completed 1,920-image derived grid.
The scatter comparisons use the 1,536 painter-conditioned outputs; 384 artist-free controls
are outside this question. Preserve the two later retry identities and all predecessor evidence.
No artwork pixels, new measurements, provider requests, or additional holdout access are needed.

## Coordinates and visualization

Keep the frozen, independent 221-work development median/IQR scaler. Analyze all 31 coordinates
and each original family (color 11, spatial 8, digital texture 12). Do not select coordinates,
remove outliers, whiten, or change feature weights after seeing the scatter plots.

For each painter and feature set, fit one common weighted PCA basis to the original reference
and all six alias/method groups. Originals have total mass 1/2; each generated group has 1/12.
Within groups each image has equal mass. Thus larger original collections do not dominate PCA.
This uses domain membership for balancing, but does not optimize label separation. All methods
and both aliases use the identical basis and axis limits within a painter/feature set. Different
painters and feature sets have different PCA axes and must not be compared by their coordinates.
Export the center, loadings, explained variance and all point identities/coordinates.

Also describe full-space dispersion for each of the 96 cells: sum the coordinate sample
variances (denominator n-1) within each group, then divide generated total variance by original
total variance. Center each group separately; this measures spread, not centroid displacement.
This is sensitive to outliers and is not a calibrated diversity or equivalence measure. This
additional descriptive summary was added after inspecting the first PCA plots; it is post-hoc.

As a projection sensitivity, fit all-31 PCA on originals alone and project generated images into
that basis. Neither PCA is used to train or evaluate the classifiers. Show all points without
cropping; use equal aspect ratios. No confidence ellipses, density significance contours,
t-SNE/UMAP parameter searches, or hand-selected favorable projections.

## Full-space separability

For every painter x alias x method x feature set (96 cells), predict original versus generated
with two fixed kernel ridge classifiers: a linear kernel `x.dot(z)/d + 1` and an RBF kernel
`exp(-||x-z||^2/d) + 1`, where d is the feature count. The constant is a regularized intercept.
Minimize class-balanced mean squared error plus `0.01 * ||f||_H^2`, with labels -1/+1.
Training weights total 1/2 per class; score >= 0 predicts generated. No hyperparameter search,
classifier selection, PCA, or fitted preprocessing on the evaluation samples.

Primary descriptive validation: 16 folds hold out one complete generated scene template
(all four repetitions). Assign unique original work IDs to 16 balanced folds by SHA-256 order
with salt `painter-distribution-v1:`; reuse these assignments across all comparisons.
Each image receives exactly one out-of-fold prediction per classifier. Retried images retain
their original scene assignment and a retry flag. Sensitivity for all 31 coordinates: use four
folds holding out one original generation block, with original works assigned by the same rule.
Scene and block validation address different dependencies; neither holds out an independent
service session or capture source. The two retries were produced later, so their original block
labels are nominal, not actual generation-time membership.

Report pooled out-of-fold balanced accuracy, AUC, original specificity and generated recall;
include every classifier and cell. Balanced accuracy 0.5 is the chance reference, not a
significance cutoff. Pooled AUC compares scores across fitted folds and is a secondary diagnostic.
Save point-level predictions for the all-31 scene and block views. All results are descriptive:
no image-IID confidence intervals, p-values, equivalence thresholds or population claims.
Synthetic checks exercise identical distributions, shifted distributions, equal-mean variance
differences, and held-out leakage; they do not calibrate inference on the empirical corpus.

## Interpretation and reproduction

The existing energy distance already compares distributions, not just their means. PCA shows
where variation lies; overlap in two PCs cannot establish equality in the full feature space.
Classifier discrimination describes detectable differences in this finite corpus. It does not
isolate painter style from scene composition, digitization, color profiles, resolution, or
service processing, and high scores do not imply aesthetic failure. The aliases are not verified
independent model snapshots. These exposed references are no longer a fresh confirmatory set.
Assess practical pattern consistency across methods, families and validation splits, without
equating correlated cells to independent replications. New population claims need a separately
designed validation using independent works/captures and generated sessions.

Implementation uses NumPy/SciPy already in the locked analysis environment. Mathematical and
validation background: [kernel ridge regression](https://scikit-learn.org/stable/modules/kernel_ridge.html),
[PCA](https://scikit-learn.org/stable/modules/decomposition.html#pca), and
[grouped cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html#leave-one-group-out).

`python -m latent_art_bench.painter_distribution_exploration_v1.report build` creates a fresh
report directory with commit-bound input and output hashes. `check` validates those hashes and
recomputes numerical tables and figures. Use `uv run --locked --extra analysis --extra learned`
before either command. Existing bundles are never overwritten.
