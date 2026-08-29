# Benchmark Specification

## 1. Scope

The initial LatentArtBench study evaluates text-to-image systems under a shared, frozen content-prompt protocol. It compares multiple open-weight and closed systems. A model/version matrix will be frozen at preregistration time rather than encoded in this design document. Image conditioning is an optional later module with a separate estimand.

Before that study, the implementation plan defines a smaller development pilot with four artists, one open-weight generator, one interpretable measurement, one learned-formal measurement, and two outputs. Pilot estimates select future sample sizes and scope; they are not benchmark rankings.

The initial benchmark targets two art-historical groupings:

1. movement or conventional style period;
2. individual artist.

Era is descriptive context. Work-level similarity is reserved for later paired or memorization diagnostics and is not treated as style-level fidelity. Genre, medium, phase, and movement are cross-classified covariates rather than a mandatory tree.

## 2. Primary output

The primary output is an **artist-distribution profile**, not a scalar score. For the initial study it reports four coordinates:

\[
\Delta_{g,t,\pi} =
(\Delta_{\mathrm{local}},
\Delta_{\mathrm{spatial}},
\Delta_{\mathrm{formal}},
\Delta_{\mathrm{context}}).
\]

Here \(\pi\) is the frozen prompt distribution. The local coordinate uses one qualified chromatic or surface statistic, the spatial coordinate uses one qualified entropy-complexity representation, and learned formal and contextual evaluators remain separate. Low-dimensional cross-layer coherence is a secondary outcome. Every coordinate reports point estimates, uncertainty, held-out real baselines, and preprocessing sensitivity. Aggregate scoring and leaderboard policy are deliberately deferred.

### 2.1 Construct interpretation

**Artist-distribution fidelity** is agreement between a generated distribution and a held-out real-work distribution under a specified prompt, sampling, preprocessing, and evaluator protocol. It is conditional on the available digital corpus, not a property of the generator alone or the essence of an artist.

- **Formal feature fidelity** covers qualified color, surface, spatial, compositional, or learned-formal measurements.
- **Contextual or iconographic fidelity** covers subjects, objects, scenes, genre, and semantic or cultural associations; it is not treated as formal style.
- **Coverage** measures recovery of variability, effective rank, support, and, only when adequately powered, tails or substructure.
- **Cross-layer coherence** measures dependencies among qualified layers on a common eligible set.
- **Perceptual style fidelity** is reserved for measurements that pass the limited blinded human qualification described in the roadmap.

Classification accuracy establishes group predictability, not style validity. Human agreement provides convergent evidence for a narrow perceptual claim, not an aesthetic or historical ground truth.

## 3. Core and optional feature families

Only the following three layers are required for the initial benchmark:

1. one local or physical measurement;
2. one spatial-complexity measurement;
3. one learned formal evaluator plus one contextual diagnostic.

The remaining methods are an extension library. Their presence in the repository does not oblige the first study to replicate or combine all of them.

The preceding development pilot implements only normalized chromatic-distance/seamlessness and one frozen learned-formal evaluator. Spatial complexity and contextual diagnostics enter planning only after the pilot report.

### 3.1 Core candidate: color and surface structure

- rank-ordered color usage;
- box-counting color diversity in color space;
- brightness height-difference correlation and roughness exponent;
- local image entropy where supported by the source method;
- adjacent-pixel CIELab color-difference distribution;
- seamlessness and associated distributional descriptors.

### 3.2 Optional extension: multiscale color interaction

- recursive information-theoretic partitions into quasi-homogeneous regions;
- dominant regional hues;
- adjacent-region hue differences;
- color-harmony template assignments;
- scale-dependent interaction profiles.

Raw partition count is not assumed to be cross-resolution comparable. Harmonized analyses will use normalized region area or an equivalent relative-scale parameter.

### 3.3 Optional extension: information-theoretic composition

- first and second partition directions;
- normalized partition ratios;
- compositional information at each split;
- recursive partition-tree summaries;
- group-level distributions and similarities based on generalized Jensen-Shannon divergence.

The principal source method is landscape-specific. Its primary benchmark view therefore contains landscape paintings only.

### 3.4 Core candidate: entropy and statistical complexity

- normalized permutation entropy;
- statistical complexity;
- ordinal-pattern distributions;
- optional multiscale or relative-lag extensions when required by validation.

The original two-by-two local ordinal construction remains the paper-faithful baseline. A later 75-dimensional treatment that explicitly handles tied pixel values is included as a resolution-sensitivity and interpretability extension.

### 3.5 Optional extension: classical and pretrained visual features

- SIFT-derived descriptors or similarities;
- low- and high-level ResNet representations;
- independently selected modern visual encoders for robustness analysis.

Features that share known architecture, objective, or data relationships with a tested generator must be labeled so that evaluator-family dependence can be measured without assuming an unobservable causal relationship.

### 3.6 Core candidate: learned formal and contextual representations

- a Stable Diffusion autoencoder formal vector, following the cited A-vector construction;
- a CLIP-family semantic/contextual vector, following the cited C-vector construction;
- at least one independent formal evaluator and one independent contextual evaluator.

The source implementation and the harmonized implementation must be versioned separately when their input preprocessing differs.

## 4. Evaluation dimensions

### 4.1 Fidelity

Measure the distance between generated and real target distributions with one preregistered primary statistic, normalized by held-out real-to-real variability and target-to-neighbor separation. Energy distance or a real-only-kernel MMD will be selected without access to sealed benchmark results. Regularized or sliced Wasserstein distance is a sensitivity analysis.

### 4.2 Specificity

Measure whether a generated sample or distribution is closer to its requested target than to plausible neighboring targets. Comparisons should include nearby movements, contemporaneous artists, and artists within the same movement.

### 4.3 Coverage and diversity

The initial study uses equal-sample coverage and effective-rank contraction in a frozen real-only space. Covariance spectra, tail occupancy, and subcluster recovery are reported only when the number of independent real works supports them. A small centroid distance does not compensate for severe coverage loss.

### 4.4 Target-level heterogeneity

Report movement- and artist-level results separately and calibrate both against real-data difficulty. No monotonic degradation from broad to narrow labels is assumed.

### 4.5 Cross-feature coherence

On a common complete-case subset, estimate a preregistered low-dimensional dependence structure among the core layers and test whether generated works preserve it. Complex graphs and missing-data models are later extensions.

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

## 7. Prompt-conditional model comparison

The initial benchmark includes multiple text-to-image model families. The final model set will contain at least:

- one reproducible open-weight generator with fixed weights and seeds;
- one closed multimodal generator with version and access date recorded.

The development pilot uses one open-weight generator only. This tests the pipeline and estimates variance; it cannot support a model-family comparison.

Additional systems may be included, but all public comparisons must identify model version, interface, output resolution, generation date, and any nondeterminism that cannot be controlled.

All model claims are conditional on the frozen prompt protocol, conditioning mode, repetition policy, refusal and failure handling, and output-selection policy. Artist-only, shared-content, in- or out-of-oeuvre, and negative-control prompts are reported separately rather than silently pooled.

## 8. Reporting requirements

Every benchmark report must include:

- corpus version and split identifiers;
- target labels, covariates, and eligible paper-specific subset;
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
- “supports artist-distribution fidelity under the specified prompt and measurement protocol.”

Disallowed or unsupported formulations include:

- “understands art as a human does”;
- “captures the true essence of the artist”;
- “is creative” based on benchmark fit alone;
- “does not memorize” based solely on failure to find a known nearest neighbor;
- “objectively reconstructs art history” from a selected digital corpus.
