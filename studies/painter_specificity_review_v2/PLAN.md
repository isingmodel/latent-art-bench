# Review clarification diagnostics — 13 September 2026

This is a post-result, descriptive extension of `painter_specificity_review_v1`
and `critics/assessment_v1/check_claims.py`. The numerical assessment is already
known. This plan therefore is not a preregistration. Preserve all frozen sources,
inputs, primary results, original review diagnostics and their 21-endpoint family.
No new images, feature extraction, human evaluation or external requests occur.

1. Compute the symmetric cross-repeat generic/common alignment ratio after scene
   averaging: numerator `(g0·c1 + g1·c0)/2`, denominator
   `sqrt((g0·g1)(c0·c1))`. Retain its two norm estimates, its numerator, the
   original plug-in cosine and all single-scene deletions. If either estimated
   squared norm is nonpositive, the ratio is unavailable. Do not clip the ratio:
   it is a ratio of noise-corrected moments, not a bounded sample cosine or an
   unbiased ratio estimator. Independent repeat errors are still required.
2. Replay the original 1,000 stratified disjoint reference half-splits and their
   random samples exactly (seed 2026091201). For each identical split, also
   integrate out the independent two-work sampling by evaluating the squared
   difference between held-pool and training-pool mean contrasts. Keep all
   observed and conditional expected scores for each of the three controls.
   Their central 95% ranges are finite-pool descriptive ranges, not intervals for
   a population or perceptual thresholds. Do not subtract variances as though
   the 1,000 paired sampling residuals had exact zero empirical covariance.
3. Compare the original held-scene calibrated errors for GPT Image 2 and FLUX.2
   Max, then delete each scene and refit the entire leave-one-scene-out procedure
   on the remaining 13 scenes (each inner fit uses 12). Preserve each fitted
   scalar and fold score. Overlapping folds are not independent replicates.
4. Estimate per-repeat centered named-arm noise power from the mean squared
   difference between independently repeated centered contrasts, divided by 2H.
   Also retain the assessment's `0.75 × summed marginal trace / H` approximation,
   which assumes zero cross-artist error covariance. Two repeats cannot verify
   the actual joint noise law or detect a state shared by both repeats.
5. Extend the original fixed-panel simulation with 5,000 repetitions for each
   combination of centered noise power 0.5, 1.5 and 3.0 and covariance form:
   isotropic in the 93-dimensional artist-centered space, or rank-three aligned
   with the reference SVD components, weighted by their squared singular values.
   Both forms have exactly the specified expected squared norm; repeats, scenes
   and models are independent. Reuse the original six slopes and residual
   magnitudes, with reference-orthogonal fixed residual directions drawn from
   seed 2026091202. A new seed 2026091302 supplies the six noise scenarios.
   Use precisely the six slopes and 15 paired error differences, and the same
   Student/Bonferroni critical value `t(13, 1−.05/(2×21))`. Retain family and
   marginal coverage, Monte Carlo standard errors and error bias. This compact
   sweep adds correlation and noise magnitude stress; it does not replace the
   original heavy-tail, scene-interaction or dependent-repeat diagnostics.

Bind the new source, plan, tests, inherited numerical sources and retained inputs
by SHA-256. The create-once writer refuses replacement; `check` recomputes and
requires exact equality, including all 1,000 original sampled control scores.
Any later scientific or computational change requires another version.
