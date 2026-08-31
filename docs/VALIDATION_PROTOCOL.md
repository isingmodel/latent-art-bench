# Validation Protocol

## 1. Purpose

This protocol prevents generated-image differences from being interpreted before the underlying measurements are shown to be reproducible, stable, and relevant to real art-historical groupings.

A feature enters the initial benchmark only after passing three gates:

1. functional replication;
2. measurement stability;
3. real-group validity.

A failed feature is not silently removed. Its failure, evidence, and restricted domain are documented.

The initial study qualifies only three layers: one local or physical measurement, one spatial-complexity measurement, and one learned formal evaluator with a contextual diagnostic. Other modules may be replicated independently without delaying the initial benchmark.

The development-pilot sequence attempts to qualify two measurements only: chromatic-distance/seamlessness and one frozen learned-formal evaluator. `pilot_0` failed and stopped before scientific generation. `pilot_1` is a separately versioned post-failure redesign; both of its measurement cards also fail. Its end-to-end run is an explicit `test_only` engineering traversal with scientific claims disabled. It cannot retroactively change the `pilot_0` decision or be called confirmatory because its design was informed by the failure and reuses the same corpus. Pilot qualification does not automatically qualify the remaining initial-study layers.

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

The source's empirical resolution-collapse behavior is a full-distribution requirement. Correct computation of scalar seamlessness `S` and synthetic scale invariance cannot substitute for comparing the complete mean-rescaled adjacent-distance distributions.

### 2.3 Color-interaction partitioning

Begin with the three paintings used in the source study. Recover representative recursive partitions, dominant regional hues, and scale-varying harmony assignments before extending the method to a larger corpus.

### 2.4 Landscape composition

Use the source preprocessing, including aspect-ratio preservation, long-side resizing, and paper-specified color quantization. Recover representative first partitions, first- and second-partition directions, normalized partition ratios, and the principal aggregate landscape patterns.

### 2.5 Complexity-entropy analysis

Validate grayscale conversion, ordinal-pattern construction, normalized permutation entropy, statistical complexity, and representative ordering in the complexity-entropy plane. Reproduce broad historical or style-level directions on a comparable real corpus.

### 2.6 Visual and learned representations

Verify exact model checkpoints, preprocessing, stochastic sampling or deterministic mode, latent scaling, layer extraction, flattening or pooling, dimensionality reduction, and vector dimensions for the source ResNet, formal A-vector, and contextual C-vector implementations. Preserve source-code commits and artifact hashes where public materials exist. When the source publishes neither a seed nor reference vector, a deterministic repair must receive a new feature version and may receive at most `conditional_pass`; that status does not open the scientific gate. Deterministic self-consistency is not byte-level replication of unpublished source output.

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

Test a limited, preregistered set of resampling kernels and compression conditions. Include lossless derived images and representative JPEG qualities. The purpose is not to enumerate every possible degradation but to determine whether model rankings or substantive conclusions depend on a plausible pipeline choice. A failed codec condition may delimit an explicitly lossless domain only when the source method makes no codec-invariance claim and every unsupported codec remains visible; it may not be reported as a general stability pass.

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

### 4.1 Cross-classified targets

Test movement and artist levels separately while recording era, genre, medium, artist phase, source, and other applicable covariates. A feature that distinguishes movements but not artists may be used only for movement-level claims. A nested model is used only when the selected corpus view actually supports nesting.

### 4.2 Held-out evaluation

Fit all standardization, density models, classifiers, PCA, and visualization transforms on real training works. Evaluate group signal on held-out canonical works. Alternative reproductions of one work must not cross the split boundary. A leave-source-out evaluation must refit centering, scaling, PCA, and every other learned transform inside each fold; a globally fitted transform would leak the held source into the diagnostic.

### 4.3 Confounds

Assess whether apparent group signal is explained by source platform, resolution, aspect ratio, digitization period, genre, subject, medium, artist phase, or other recorded nuisance variables. At minimum, report a source-prediction baseline and leave-source-out artist validity. Natural-oeuvre and content- or genre-matched analyses answer different questions and must be labeled separately.

### 4.4 Validity outcomes

For each feature and target level, report:

- held-out discrimination or calibrated target fit;
- uncertainty across works and artists;
- comparison with nuisance-only baselines;
- stability across corpus sources;
- the scope in which the feature is interpretable.

### 4.5 Limited human qualification

Human judgments are not another universal gate for every computational observable. They are required only when a metric will support a perceptual style claim. A small blinded study separates formal resemblance from subject or iconographic resemblance and includes image-level and set-level comparisons. Failure limits terminology to the named feature distribution; it does not automatically invalidate a reliable physical measurement.

## 5. Dual preprocessing tracks

### Track A: Source-faithful replication

Apply the original method's documented resizing, quantization, aspect-ratio, model, and layer choices. This track determines whether published findings can be functionally recovered.

### Track B: Harmonized comparison

Apply identical, versioned processing to real and generated images, preserve aspect ratio unless a model requires otherwise, use supported common scales, and retain multiscale outputs for sensitive features.

A benchmark result is strongest when it agrees across both tracks. Disagreement is itself reported as preprocessing dependence.

## 6. Dimensionality reduction

Dimensionality reduction cannot define the reference space after generated images have been observed.

- Fit PCA or related linear transformations on one primary real training reproduction per independent work only.
- Select retained dimensions without looking at generated-model rankings.
- Freeze and transform held-out real and generated images.
- Refit the complete transformation inside every source- or group-held-out diagnostic.
- Record the fit-work identifiers, retained dimension, explained variance, solver, sign convention, and state hash. If a fixed component cap misses its variance target, report that miss as a limitation rather than implying the target was achieved.
- Use distances in original or validated reduced spaces for inference.
- Use UMAP primarily for exploratory visualization; do not interpret two-dimensional distances as faithful high-dimensional distances.

## 7. Evaluator independence

The benchmark reproduces the source A-vector and C-vector methods but does not rely on them alone. At least one independent evaluator per learned feature family is required for robustness analysis. The generator-evaluator matrix must identify shared architecture families, representation objectives, and known data relationships.

If a result appears only with a closely related evaluator, it is classified as evaluator-dependent rather than a general fidelity effect.

Raw distances across evaluator families are not directly comparable. Formal-contextual contrasts must be normalized by same-target real-to-real variability and target-to-neighbor separation so that evaluator headroom is not mistaken for generator behavior.

## 8. Statistical inference

The inferential unit must match the claim. Large numbers of seeds do not compensate for few artists or few independent target works.

Recommended approaches include:

- hierarchical bootstrap over artists, works, and generation clusters;
- mixed-effects models with target and work-level random effects;
- permutation tests that preserve nested structure;
- false-discovery control across feature modules;
- sensitivity analyses across corpus and preprocessing versions.

All primary distributional comparisons use equal-sample repeated subsampling. Covariance, effective-rank, and tail analyses require preregistered minimum real-work counts and dimensionality rules. Practical equivalence to a real or reproduction baseline is tested against a feature-specific margin; failure to reject a difference is not evidence of equivalence.

## 9. Separation of pilots and sealed tests

The calibration pilot uses real works, synthetic unit tests, reproduction pairs, and acquisition controls without examining generator rankings. It fixes preprocessing, reliability rules, nuisance checks, and candidate feature eligibility.

The benchmark pilot uses a limited development subset of artists and models. It fixes prompts, endpoints, sample-size rules, and exclusions. Final test artists, prompts where applicable, and model results remain sealed until the analysis plan is frozen. Changes after unsealing require a new benchmark version.

Effect sizes and uncertainty intervals are primary. Statistical significance without a comparison to held-out real variability and reproduction noise is insufficient. A redesign made after a frozen pilot fails must keep the old card immutable, receive a new protocol and feature identity, and be labeled development evidence. It becomes confirmatory only when frozen prospectively and applied to new or still-sealed data.

## 10. Audit artifacts

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

Git cleanliness has a narrow meaning in this repository. `.gitignore` excludes `artifacts/`, `outputs/`, `tmp/`, large media, checkpoints, and the local raw/vector manifests. A clean tracked checkout therefore does not show that museum images, generated PNGs, model weights, or extracted A-vectors are present or committed. Released evidence snapshots bind selected local artifacts by hash and preserve sanitized provenance, but they do not contain those ignored bytes. Reproduction requires reacquiring or retaining the exact files and verifying every recorded digest.

## 11. Pilot_1 application of the protocol

### 11.1 Chromatic decision: fail

Chromatic v2 uses Lee et al.'s scalar seamlessness `S` as the primary coordinate, independently derived native-to-500/400/256 lossless branches, matched 1024 codec parents, fold-local fitting, one independent alternate unit per work, and 2,000 artist-stratified bootstrap draws.

The scalar formula checks passed, but the source's defining full mean-rescaled distribution behavior was not recovered. The adapted diagnostic compares complete empirical CDFs for 500-vs-400 and 500-vs-256 branches using a project K-S equivalence margin of `D <= 0.05`. An image passes only if both pairs pass. Of 108 primary images, 91 passed and 17 missed at least one comparison. The source gate remains ineligible because the project branch set does not reproduce Figure 1's 500-3000 pixel set, 0/108 primary files support 3000 pixels without upsampling, 0/108 are border-cleared, and the manifest lacks explicit partial-capture and serious-damage reviews. Scalar `S` cannot satisfy this full-distribution gate.

The direct 400/500 ratio was `0.0819375820` with 95% interval `[0.0580938772, 0.1279254608]`; direct 256/500 was `0.2604446675` with `[0.1718565735, 0.3900617693]`. Q95 4:4:4 was `0.0558064356` with `[0.0414253939, 0.0804704261]` and remains a secondary sensitivity only. Q85 4:2:0 failed because its `0.4325558376` point ratio had upper bound `0.6231027032`. Grouped cross-reproduction stability also failed: point ratio `0.5882766278`, upper bound `1.8285907947`.

Held-out artist, held-out source, and pooled nested leave-source-out artist balanced accuracies were `0.3506944444`, `0.2416666667`, and `0.3369674185`. Not every held-source fold cleared the frozen `0.30` minimum. These are construct diagnostics, not evidence of source-invariant artist recognition. The combined status is `fail`, with no supported scientific scope.

### 11.2 Learned-formal decision: fail

Kim et al. use Stable Diffusion 2's 512-base autoencoder, force images to 512x512, and flatten the `4 x 64 x 64` latent to a 16,384-value A-vector. Their paper excludes paintings whose aspect ratio is at least 2 and low-resolution inputs. The public source writes each OpenCV-resized intermediate using the source file's original extension, reopens it with Pillow, and samples the encoder posterior. It publishes no RNG state, seed, author A-vector, or checkpoint digest.

The project therefore versions its implementation as a deterministic repair: it preserves the source's same-extension preprocessing, derives a per-image seed, samples the posterior, applies scale `0.18215`, and flattens in C order. Four repeated extractions matched exactly. The recovered VAE config and all 248 first-stage tensors were also checked bit-for-bit against the pinned 512-base checkpoint. These checks establish the project's vector and checkpoint-mapping contracts; they do not prove equality with an unpublished author vector or that the public mirror was the exact author-used checkpoint.

The current real run contains 119 feature rows and is pinned to Python `3.13.11`, Darwin `25.6.0` on `arm64`, PyTorch `2.13.0`, diffusers `0.40.0`, NumPy `2.5.2`, OpenCV `4.14.0` plus its build hash, Pillow `11.3.0`, JPEG codec `6.2`, and the MPS backend. A mismatch is a protocol failure rather than an unrecorded environment substitution. These pins make this run auditable; they do not establish cross-platform equivalence.

The learned-formal card fails four frozen requirements. All 108 primaries pass the
released source's strict native-area rule (`width * height > 410 * 410`), but that does
not cure the separate aspect-ratio failure:

- only 107/108 primary works satisfy Kim et al.'s strict aspect-ratio `< 2` domain; `reproduction-cma-136510-primary` violates it;
- the train-only 32-component PCA retains `61.521423%`, not the frozen 95% target;
- grouped reproduction stability has point ratio `0.7423170871` and 95% upper bound `1.1001825090`, above the `1.0` margin; and
- the artist-by-source split is incomplete: training lacks Alfred Sisley-CMA, Claude Monet-CMA, and Claude Monet-Met cells, while held-out data lacks Claude Monet-Met, so source confounding is not controlled.

The updated held-out artist, held-out source, and pooled nested leave-source-out artist balanced accuracies are `0.53125`, `0.5375`, and `0.4126566416`. They do not override the domain, PCA, stability, or joint-coverage failures.

There is also an origin-by-codec confound in generated comparisons. All 119 real sources are JPEG and therefore receive another lossy JPEG encode in the source-faithful same-extension intermediate. All 40 generated sources are PNG and retain a lossless PNG intermediate. Because origin perfectly predicts that intermediate codec, a real-generated A-vector contrast cannot distinguish image origin from preprocessing loss.

### 11.3 Test-only engineering traversal

Both qualification cards are `fail`, so the scientific gate is closed. The configuration remains restricted to requested labels `gpt-image-1` and `gpt-image-2`, a loopback endpoint, and `scientific_claims_enabled: false`.

The retained API run predates the current failed cards. Its 41 attempts are explicitly grandfathered for engineering use only; current attestation does not retroactively attribute the present qualification context to those calls. Generated-feature preparation used `--allow-unqualified-test-preparation`, and analysis used `--allow-unqualified-test-analysis`. Their manifests bind the generation attestation, request/output identities, feature manifests, failed qualification evidence, and learned PCA state. The resulting exact 16-cell grid and artist-free controls demonstrate pipeline traversal only. They cannot support model rankings, artist-style conclusions, or any scientific claim.

### 11.4 Prospective pilot_2 redesign

`pilot_2` must freeze its protocol before collection or unsealing and evaluate new or still-sealed real data. Reusing the observed `pilot_1` corpus can provide development diagnostics, not confirmation.

At minimum, the redesign must:

1. collect Lee-eligible images with explicit border, partial-capture, damage, painting-medium, and native-resolution reviews, then test the complete normalized distribution over a preregistered resolution set without upsampling;
2. either obtain native support for Lee et al.'s Figure 1 resolutions or label a different set as a new adapted protocol rather than source replication;
3. enforce both Kim et al.'s aspect-ratio rule and the prospectively selected low-resolution domain before extraction, recording the paper's dimensional description separately from the released source's strict area rule;
4. eliminate the real-JPEG/generated-PNG preprocessing confound, for example with a separately versioned harmonized lossless track or an origin-balanced source-faithful codec design;
5. prospectively choose a PCA cap that can meet the stated variance target, or freeze and justify a different representation target before generated outputs are observed;
6. construct complete, adequately populated artist-by-source train and held-out cells and acquire more independent same-work reproductions for hierarchical uncertainty; and
7. require generation provenance that proves the executed model identity and satisfies the requested image-size contract before allowing model-specific inference.

Only new `pass` cards under that frozen design can open the scientific generation and analysis path.
