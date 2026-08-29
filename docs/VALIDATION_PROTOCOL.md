# Validation Protocol

## 1. Purpose

This protocol prevents generated-image differences from being interpreted before the underlying measurements are shown to be reproducible, stable, and relevant to real art-historical groupings.

A feature enters the benchmark only after passing three gates:

1. functional replication;
2. measurement stability;
3. real-group validity.

A failed feature is not silently removed. Its failure, evidence, and restricted domain are documented.

## 2. Gate 1: Functional replication

Functional replication asks whether an implementation recovers the defining behavior of the source method on real artworks.

### 2.1 Color usage and brightness structure

Validate rank-ordered color use, color-space box-counting behavior, brightness height-difference correlation, roughness exponents, and any fixed-size image-entropy calculation against reported examples and aggregate directions.

### 2.2 Chromatic-distance heterogeneity

Validate:

- conversion into the documented perceptual color space;
- adjacent-pixel color-distance distributions;
- resolution-dependent raw distributions;
- collapse after the source normalization;
- seamlessness calculations;
- representative contrast between patch-like and intertwined color structures.

### 2.3 Color-interaction partitioning

Begin with the three paintings used in the source study. Recover representative recursive partitions, dominant regional hues, and scale-varying harmony assignments before extending the method to a larger corpus.

### 2.4 Landscape composition

Use the source preprocessing, including aspect-ratio preservation, long-side resizing, and paper-specified color quantization. Recover representative first partitions, first- and second-partition directions, normalized partition ratios, and the principal aggregate landscape patterns.

### 2.5 Complexity-entropy analysis

Validate grayscale conversion, ordinal-pattern construction, normalized permutation entropy, statistical complexity, and representative ordering in the complexity-entropy plane. Reproduce broad historical or style-level directions on a comparable real corpus.

### 2.6 Visual and learned representations

Verify exact model checkpoints, preprocessing, layer extraction, pooling, dimensionality reduction, and vector dimensions for the source ResNet, formal A-vector, and contextual C-vector implementations. Preserve source-code commit identifiers where public code exists.

### 2.7 Functional replication outcome

Each method receives one status:

- **Pass:** defining image-level and aggregate behavior is recovered;
- **Conditional pass:** behavior is recovered only under a documented corpus or preprocessing restriction;
- **Fail:** defining behavior cannot be recovered or implementation ambiguity remains too large.

Exact numeric equality is not required when original image versions are unavailable. Differences must be attributable to documented corpus or software variation.

## 3. Gate 2: Measurement stability

### 3.1 Resolution response

For each eligible high-quality image, compute a feature response curve at supported long-side sizes such as 256, 400, 512, 768, and 1024 pixels. Only sizes at or below the native resolution are primary. Model-required resizing above native resolution is labeled separately.

The analysis compares:

- within-image feature drift across resolution;
- between-reproduction drift for the same work;
- between-work variability within a real target group;
- between-group variability.

### 3.2 Resampling and compression

Test a limited, preregistered set of resampling kernels and compression conditions. Include lossless derived images and representative JPEG qualities. The purpose is not to enumerate every possible degradation but to determine whether model rankings or substantive conclusions depend on a plausible pipeline choice.

### 3.3 Color management

Test embedded-profile handling, conversion to the project color space, and missing-profile assumptions. Color-sensitive modules must report whether source-specific profiles materially affect group or model comparisons.

### 3.4 Aspect ratio and borders

Separate aspect-preserving harmonized analyses from source methods that force square inputs. Evaluate borders, mats, frames, and photographic backgrounds because they can alter color, composition, ordinal, and learned features.

### 3.5 Reproduction noise floor

For feature family \(k\), estimate the distribution

\[
N_k = D_k(x_{w,a}, x_{w,b}),
\]

where \(x_{w,a}\) and \(x_{w,b}\) are independent digital reproductions of the same physical work \(w\). A generated-to-real gap that is not distinguishable from \(N_k\) is treated as unresolved at that measurement scale.

### 3.6 Reliability outcomes

A feature may be:

- retained at a canonical resolution;
- retained as a multiscale response curve or summary;
- residualized or normalized by a validated nuisance model;
- restricted to matched native-resolution strata;
- excluded from individual-work inference but retained for aggregate analysis;
- excluded from the benchmark.

Numeric reliability thresholds will be preregistered after pilot variance estimates. Candidate summaries include intraclass correlation, variance ratios, rank stability, and agreement of substantive model contrasts.

## 4. Gate 3: Real-group validity

The benchmark must establish what each feature can distinguish in held-out real art before evaluating generated images.

### 4.1 Hierarchical targets

Test era, movement, and artist levels separately. A feature that distinguishes movements but not artists may be used only for movement-level claims.

### 4.2 Held-out evaluation

Fit all standardization, density models, classifiers, PCA, and visualization transforms on real training works. Evaluate group signal on held-out canonical works. Alternative reproductions of one work must not cross the split boundary.

### 4.3 Confounds

Assess whether apparent group signal is explained by source platform, resolution, aspect ratio, digitization period, or other recorded nuisance variables. Genre and subject controls follow the domain and inclusion rules of each source method rather than being imposed uniformly on every module.

### 4.4 Validity outcomes

For each feature and target level, report:

- held-out discrimination or calibrated target fit;
- uncertainty across works and artists;
- comparison with nuisance-only baselines;
- stability across corpus sources;
- the scope in which the feature is interpretable.

## 5. Dual preprocessing tracks

### Track A: Source-faithful replication

Apply the original method's documented resizing, quantization, aspect-ratio, model, and layer choices. This track determines whether published findings can be functionally recovered.

### Track B: Harmonized comparison

Apply identical, versioned processing to real and generated images, preserve aspect ratio unless a model requires otherwise, use supported common scales, and retain multiscale outputs for sensitive features.

A benchmark result is strongest when it agrees across both tracks. Disagreement is itself reported as preprocessing dependence.

## 6. Dimensionality reduction

Dimensionality reduction cannot define the reference space after generated images have been observed.

- Fit PCA or related linear transformations on real training works only.
- Select retained dimensions without looking at generated-model rankings.
- Freeze and transform held-out real and generated images.
- Use distances in original or validated reduced spaces for inference.
- Use UMAP primarily for exploratory visualization; do not interpret two-dimensional distances as faithful high-dimensional distances.

## 7. Evaluator independence

The benchmark reproduces the source A-vector and C-vector methods but does not rely on them alone. At least one independent evaluator per learned feature family is required for robustness analysis. The generator-evaluator matrix must identify shared architecture families, representation objectives, and known data relationships.

If a result appears only with a closely related evaluator, it is classified as evaluator-dependent rather than a general fidelity effect.

## 8. Statistical inference

The inferential unit must match the claim. Large numbers of seeds do not compensate for few artists or few independent target works.

Recommended approaches include:

- hierarchical bootstrap over artists, works, and generation clusters;
- mixed-effects models with target and work-level random effects;
- permutation tests that preserve nested structure;
- false-discovery control across feature modules;
- sensitivity analyses across corpus and preprocessing versions.

Effect sizes and uncertainty intervals are primary. Statistical significance without a comparison to held-out real variability and reproduction noise is insufficient.

## 9. Audit artifacts

Every released feature module should provide:

- mathematical definition and implementation notes;
- source-paper version and code provenance;
- preprocessing manifest;
- representative replication cases;
- stability plots;
- reliability and validity tables;
- failure cases;
- unit tests using synthetic images with known properties;
- a machine-readable validation status.
