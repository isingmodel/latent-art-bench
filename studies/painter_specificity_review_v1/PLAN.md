# Review-driven diagnostics — 12 September 2026

This is a post-result, offline response to `critics/01.md` and `critics/02.md`,
reviewing commit `6073c1b4bb1028cac635755e7b1511524bb707c5`. The reviews are
user-supplied reports, not evidence of independent human or institutional review.
The primary experiment and its 21-comparison family remain unchanged. No new
images, features, paid requests, human ratings or collection retries are involved.
All added results are descriptive; none retroactively enter that family.

The following diagnostic choices are recorded before running the new analysis,
but after the primary results and reviewers' calculations were known.

1. Decompose scene-wise error into aggregate mismatch and cross-scene contrast
   variation. Report generated contrast magnitude Q, beta/sqrt(Q), and scalar
   calibration fitted on 13 scenes and evaluated on the omitted scene. Use a
   nonnegative scalar beta/Q when Q is positive; otherwise mark it unavailable.
   These transformed vectors need not correspond to realizable images.
2. Report all three nonzero reference singular components, all six artist pairs,
   four leave-one-artist-out configurations, and all 24 artist-label assignments.
   Permutation ranks are descriptive, without an exchangeability test.
3. Report shared squared-change fractions before and after scene averaging.
   Centering removes only a common additive shift, not a common linear transform.
4. Compare pooled and class-specific targets on the 11 already designated water,
   built and land briefs, mapped respectively to water-organized,
   built-place-organized and open/wooded-land reference titles. Exclude the three
   mixed briefs; do not reclassify images. Normalize the conditional target by its
   own average squared magnitude. These metadata classes are not visually matched
   scenes. Also report the four genuine reference class contrasts and cell counts.
5. Run 1,000 stratified, disjoint half-splits of the existing reference works
   (seed 2026091201). In each split, construct the target from the training works;
   independently sample two works per painter per pseudo-scene, with replacement,
   from the held-out works. Compare a 14-scene pooled real/real control and an
   11-scene class-stratified control against both pooled and class-specific
   training targets. Retain actual work memberships through the source frame
   and deterministic seed. Quantiles describe this finite-pool experiment, not
   confidence intervals, source-held-out replication or an artistic threshold.
6. Inspect equal feature-family mass and a development-only covariance metric.
   Fit equal-painter-weighted covariance on the same 221 development works;
   use 50% shrinkage toward its mean variance times the identity, with no tuning.
   Report every coordinate's additive contribution and deletion sensitivity.
7. Retain the original empirical energy statistic. Add the correction appropriate
   to two independent draws in each of 14 scene strata, comparing the uniformly
   mixed conditional output distributions with the fixed empirical reference.
   This is not an ordinary pooled IID U-statistic or a calibrated fidelity score.
8. Use 5,000 synthetic repetitions (seed 2026091202) to stress the original
   Student/Bonferroni procedure under Gaussian, heavy-tailed/heteroskedastic,
   scene-interaction, and shared-state repeat-dependent errors. The simulated
   truths are known fixed-panel means. This examines the procedure under explicit
   models; it cannot establish the actual API noise distribution or independence.

The compact result records source/input hashes and has a create-once writer with
an offline check command. Keep historical protocols, sources and reports intact.
Public archiving, human validation, source-held-out references, learned features,
and new repeated collections are not completed by these diagnostics. The revised
paper must distinguish those remaining requirements from the additions above.
