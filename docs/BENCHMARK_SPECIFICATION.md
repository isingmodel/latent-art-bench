# Benchmark Specification

## 1. Scope

LatentArtBench evaluates image-generating systems that accept language instructions and may optionally accept image conditioning. The benchmark compares multiple open-weight and closed systems. A model/version matrix will be frozen at preregistration time rather than encoded in this initial design document.

The benchmark targets three levels of art-historical grouping:

1. era;
2. movement or conventional style period;
3. individual artist.

Work-level similarity is included for paired image-conditioned experiments and memorization diagnostics, but it is not treated as equivalent to style-level fidelity.

## 2. Primary output

The primary output is a **style gap profile**, not a scalar score:

\[
\Delta_{g,t} =
(\Delta_{\mathrm{color}},
\Delta_{\mathrm{interaction}},
\Delta_{\mathrm{composition}},
\Delta_{\mathrm{complexity}},
\Delta_{\mathrm{visual}},
\Delta_{\mathrm{formal}},
\Delta_{\mathrm{context}},
\Delta_{\mathrm{coherence}}).
\]

Every module must report point estimates, uncertainty, held-out real baselines, and preprocessing sensitivity. Aggregate scoring and leaderboard policy are deliberately deferred.

## 3. Feature families

### 3.1 Color and surface structure

- rank-ordered color usage;
- box-counting color diversity in color space;
- brightness height-difference correlation and roughness exponent;
- local image entropy where supported by the source method;
- adjacent-pixel CIELab color-difference distribution;
- seamlessness and associated distributional descriptors.

### 3.2 Multiscale color interaction

- recursive information-theoretic partitions into quasi-homogeneous regions;
- dominant regional hues;
- adjacent-region hue differences;
- color-harmony template assignments;
- scale-dependent interaction profiles.

Raw partition count is not assumed to be cross-resolution comparable. Harmonized analyses will use normalized region area or an equivalent relative-scale parameter.

### 3.3 Information-theoretic composition

- first and second partition directions;
- normalized partition ratios;
- compositional information at each split;
- recursive partition-tree summaries;
- group-level distributions and similarities based on generalized Jensen-Shannon divergence.

The principal source method is landscape-specific. Its primary benchmark view therefore contains landscape paintings only.

### 3.4 Entropy and statistical complexity

- normalized permutation entropy;
- statistical complexity;
- ordinal-pattern distributions;
- optional multiscale or relative-lag extensions when required by validation.

The original two-by-two local ordinal construction remains the paper-faithful baseline. A later 75-dimensional treatment that explicitly handles tied pixel values is included as a resolution-sensitivity and interpretability extension.

### 3.5 Classical and pretrained visual features

- SIFT-derived descriptors or similarities;
- low- and high-level ResNet representations;
- independently selected modern visual encoders for robustness analysis.

Features that share a model family with a tested generator must be labeled so that home-field effects can be measured.

### 3.6 Learned formal and contextual representations

- a Stable Diffusion autoencoder formal vector, following the cited A-vector construction;
- a CLIP-family semantic/contextual vector, following the cited C-vector construction;
- at least one independent formal evaluator and one independent contextual evaluator.

The source implementation and the harmonized implementation must be versioned separately when their input preprocessing differs.

## 4. Evaluation dimensions

### 4.1 Fidelity

Measure the distance between generated and real target distributions. No single distributional metric is assumed to be universally optimal; validated candidates include energy distance, maximum mean discrepancy, and regularized Wasserstein distance.

### 4.2 Specificity

Measure whether a generated sample or distribution is closer to its requested target than to plausible neighboring targets. Comparisons should include nearby movements, contemporaneous artists, and artists within the same movement.

### 4.3 Coverage and diversity

Compare generated and real within-target variability using covariance spectra, effective rank, local support coverage, tail occupancy, and subcluster recovery. A small centroid distance does not compensate for severe coverage loss.

### 4.4 Hierarchical consistency

Report era-, movement-, and artist-level results separately. A model may pass at a coarse level and fail at a fine level.

### 4.5 Cross-feature coherence

Estimate the dependence structure among feature families in real training works and test whether generated works preserve it. Candidate approaches include cross-covariance comparisons, conditional density models, graph-based dependence summaries, and joint two-sample tests.

### 4.6 Robustness

Recompute conclusions across validated resolutions, preprocessing tracks, and evaluator families. Report whether the sign and rank order of model effects are stable.

### 4.7 Memorization diagnostics

Work-level nearest-neighbor similarity is reported separately from style fidelity. Diagnostics may combine perceptual hashes, local feature matching, and independent embeddings. Because closed-model training sets are not fully observable, absence of a match cannot establish absence of memorization.

## 5. Reference fitting and freezing

All learned transformations used for evaluation must follow this order:

1. split real works by canonical work identity;
2. fit preprocessing statistics and dimensionality reduction on the real training split;
3. validate on held-out real works;
4. freeze the evaluator;
5. transform generated images without refitting.

UMAP is exploratory. High-dimensional distances must not be replaced by distances in a two-dimensional UMAP plot. If UMAP transformation is used for visualization, the mapper is fitted on real training works only.

## 6. Calibration baselines

Each module reports results relative to:

- held-out real-to-own-group distance;
- held-out real-to-neighbor-group distance;
- same-work, different-reproduction distance;
- same-file, different-preprocessing distance;
- a suitable null or shuffled-image model where inherited from the source method.

These baselines distinguish model failure from measurement noise and ordinary within-style variability.

## 7. Model comparison

The benchmark includes multiple model families and both text-only and image-conditioned generation. The final model set will contain at least:

- one reproducible open-weight generator with fixed weights and seeds;
- one closed multimodal generator with version and access date recorded.

Additional systems may be included, but all public comparisons must identify model version, interface, output resolution, generation date, and any nondeterminism that cannot be controlled.

## 8. Reporting requirements

Every benchmark report must include:

- corpus version and split identifiers;
- target hierarchy and eligible paper-specific subset;
- model and evaluator versions;
- native output size and all preprocessing operations;
- number of canonical real works, generated images, and generation clusters;
- uncertainty intervals that respect nested sampling;
- all module scores, not only selected favorable results;
- reproduction-noise and held-out-real baselines;
- failed validation gates and excluded features;
- known licensing, geographic, canon, and exposure limitations.

## 9. Claims policy

Allowed formulations include:

- “reproduces the target distribution in the measured feature family”;
- “shows higher contextual than formal fidelity”;
- “covers a narrower region than held-out real works”;
- “supports transferable latent style fidelity under the benchmark definition.”

Disallowed or unsupported formulations include:

- “understands art as a human does”;
- “captures the true essence of the artist”;
- “is creative” based on benchmark fit alone;
- “does not memorize” based solely on failure to find a known nearest neighbor;
- “objectively reconstructs art history” from a selected digital corpus.
