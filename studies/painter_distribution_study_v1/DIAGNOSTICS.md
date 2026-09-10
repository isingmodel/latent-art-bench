# Stage A: fixed existing-data diagnostics

Issued before this stage's computations. Existing scatter and distance results
were already exposed; this is explanatory development analysis, not preregistered
confirmation. The umbrella `PROTOCOL.md` supplies authority and stage boundaries.

Inputs: the same 649 measured confirmation paintings, 221-work development scaler,
and retry-derived 1,920 measured prompt outputs. Include all 384 artist-free outputs
alongside the 1,536 named outputs. Check source bindings and exact identities. Reuse
the four recorded content classes and original collection identifiers; these are
metadata labels, not new expert annotations or independent capture identities.

For every painter x two aliases x three methods x four feature sets (all31, color,
spatial, texture), report named and artist-free energy distance, sample-variance
trace ratio, squared-IQR-sum ratio and coordinate IQR ratios. An undefined original
IQR yields null, never division by an arbitrary epsilon. The family robust summary
is the ratio of sums of squared coordinate IQRs, not a new primary aesthetic score.

Report collected-mixture estimates and equal-four-content-class weights for both
sets. Use weighted empirical inverse-CDF quartiles and weighted population variance
for this standardized sensitivity; retain the ordinary sample-variance result
separately. Original class labels come from the existing frame; generated labels
come from the assigned prompt, so this checks intended content mixture and does
not establish actual content adherence. List counts and Kish weight effective size
as a weight-concentration diagnostic, not independent-observation sample size.

Original-versus-original reference: 128 deterministic disjoint splits of whole
works per painter, each group of n=min(64, floor(N/2)). Compute family energy and
spread. For each named and artist-free cell, compute matched-n generated/original
sensitivities using the same original subsets, with generated subsets selected
without feature values. Export every draw. These are finite-dataset subsampling
distributions, not confidence intervals, tests, equivalence margins or 128 studies.

Full-space classifiers reuse the previous fixed class-balanced kernel-ridge
contracts, ridge 0.01 and linear/RBF kernels; no tuning or PCA input. Evaluate each
named and artist-free cell with whole-scene generated folds and disjoint original
work folds. For 16 original-versus-original splits, use four balanced disjoint work
folds per class to provide a descriptive all31 chance baseline. Export predictions.

Cross-painter transfer is restricted to by-name generation to avoid a large new
factorial. For every ordered pair of different painters and each alias, train only
on source-painter originals and generations and test on the target painter. Use
four folds: exclude the held-out scene families from source generation and hold
out distinct target works. Cross-alias transfer within painter similarly excludes
the target original-work and scene folds from training. Score each target image
once and retain membership. The same physical work or exact scene family must not
be in a training set and its test set. Fit nothing to the target labels.

Seed strings and draw counts are fixed in `diagnostics.json`. PCA summaries and
plots use the shared deterministic routines; show all points with common axes
within each painter and balanced original/named/free weights. No projection or
feature subset is selected according to separation. Explain original source counts
and capture-workflow uncertainty. No independent-capture conclusion follows from
this metadata-only stage.

The report is create-once. Bind consumed evidence, methods, configuration, source
and tests to a commit before execution. Numerical replay compares every numeric
output; file hashes check the retained report. Corrective reruns use a new output
ID and preserve earlier evidence. Source tests must cover equal distributions,
known scale shifts, disjoint resampling, content reweighting and transfer leakage.
