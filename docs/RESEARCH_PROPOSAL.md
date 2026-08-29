# Research Proposal

## Working title

**LatentArtBench: Do Generative Vision-Language Systems Reproduce the Latent Structure of Artists and Art Movements?**

## Abstract

Generative image systems can produce images that are readily associated with named artists and art movements. Visual resemblance, however, does not establish that a system has reproduced the statistical structure of a style. A generated image may match familiar iconography while deviating in color organization, spatial composition, complexity, formal representation, or the relationships among these properties. It may also converge on a narrow prototype rather than reproduce the breadth of a historical oeuvre.

This project proposes LatentArtBench, an automated and multiscale benchmark for measuring how closely generated images reproduce artist- and movement-specific distributions in complementary feature spaces. The benchmark integrates physics-inspired observables, information-theoretic image partitioning, entropy-complexity measures, classical and pretrained vision features, and learned formal and contextual representations. Before any model comparison, each feature must pass three gates: functional replication on real artworks, stability under digitization and resolution perturbations, and out-of-sample validity for the relevant art-historical grouping.

The empirical program uses a Western canonical discovery corpus, a separate non-Western and long-tail challenge corpus, a reproduction-calibration corpus containing multiple digital surrogates of the same works, and generated corpora from multiple open and closed model families. The resulting benchmark reports target fit, specificity, distributional coverage, diversity contraction, cross-feature coherence, and robustness. It does not equate these measurements with human aesthetic judgment or metaphysical understanding. Instead, it operationalizes **latent style fidelity** as the reproducible recovery of multilevel statistical invariants associated with a target artist or movement.

## 1. Background and rationale

Quantitative art-history research has developed a coherent progression of representations. Early work characterized color use, color diversity, and brightness roughness. Later work introduced the distribution of adjacent-pixel chromatic distances and the seamlessness statistic, information-theoretic partitions of color and landscape composition, and the complexity-entropy plane derived from ordinal pixel patterns. Recent work has shifted toward learned formal and contextual representations extracted from generative and vision-language models.

These representations offer a useful basis for evaluating generated imitations because they describe different layers of an image:

- local color differences and surface organization;
- multiscale color interaction;
- global and recursive composition;
- spatial order, disorder, and complexity;
- low- and high-level visual structure;
- learned formal features;
- semantic and cultural context.

No individual representation should be treated as the essence of style. The research opportunity lies in comparing their agreements and disagreements. An image that matches a target in contextual space but not in formal space is qualitatively different from one that matches both but covers only a small part of the target distribution.

Existing AI-versus-human painting research has used entropy and multiscale complexity to identify aggregate differences. LatentArtBench extends this direction by introducing hierarchical artist and movement targets, multiple independent feature families, reproduction-noise calibration, distributional coverage, and cross-feature coherence.

## 2. Research objective

The primary objective is to construct and validate a benchmark that answers:

> How well do generative models reproduce the multilevel statistical and latent distributions associated with a specified artist or art movement?

The project distinguishes five related capabilities:

1. **Fidelity:** proximity to the target real-work distribution.
2. **Specificity:** preference for the intended target over plausible neighboring artists or movements.
3. **Coverage:** recovery of the target distribution's variability rather than only its centroid.
4. **Generalization:** persistence of target-associated structure across generated outputs rather than isolated exemplars.
5. **Coherence:** recovery of the dependencies among color, composition, complexity, formal, and contextual features.

## 3. Research questions

### RQ0: Measurement validity

Which observables remain stable across resolution, resampling, compression, color conversion, border removal, and alternative digital reproductions of the same work?

### RQ1: Target fidelity

How close are generated images to the held-out real distribution of the requested artist or movement in each feature family?

### RQ2: Hierarchical fidelity

Does performance degrade as the target becomes more specific, from era to movement to artist to individual work?

### RQ3: Formal-contextual asymmetry

Are generated images systematically closer to target distributions in contextual or semantic representations than in physical and formal representations?

### RQ4: Distributional coverage

Do models reproduce within-target diversity, covariance, tails, and substructure, or do they contract toward a recognizable prototype?

### RQ5: Model and conditioning effects

How do results vary across open and closed model families and between text-only and image-conditioned generation?

### RQ6: Canon and exposure effects

Are canonical and highly exposed artists reproduced more faithfully than long-tail or non-Western targets, and is higher fidelity accompanied by stronger evidence of prototype repetition or memorization?

### RQ7: Representation dependence

Do conclusions remain stable when the evaluator architecture changes, or do generator-evaluator affinities create a home-field advantage?

## 4. Operational definition

Let a target group be denoted by \(t\), a feature family by \(k\), and a generator by \(g\). Real and generated feature distributions are

\[
P_{t,k}^{\mathrm{real}} \quad \text{and} \quad Q_{g,t,k}^{\mathrm{gen}}.
\]

Latent style fidelity is not a single Euclidean distance. It is a profile containing at least:

- the generated-to-target distributional distance;
- the generated-to-neighbor margin;
- the fraction of the real target support covered by generated works;
- the contraction or expansion of within-target variability;
- the preservation of dependencies across feature families;
- the stability of conclusions across preprocessing and evaluator choices.

All distances are calibrated against two empirical baselines:

1. held-out real works relative to their own target group;
2. alternative digital reproductions of the same work.

## 5. Study architecture

### Stage A: Functional replication

Implement each source method and recover its defining image-level behavior and principal aggregate findings on real artworks. Exact numerical replication is not required when the original image versions are unavailable, but the implementation must recover representative partitions, distributions, orderings, or historical directions.

### Stage B: Measurement calibration

Construct feature-response curves across controlled image resolutions and degradation conditions. Estimate a reproduction noise floor from multiple digital surrogates of the same physical work. Retain, modify, or restrict each feature based on its measurement reliability.

### Stage C: Real reference atlas

Estimate hierarchical reference distributions using real training works only. Validate each feature's artist-, movement-, and era-level signal on held-out real works. Fit and freeze any standardization, PCA, UMAP, density model, or classifier before generated images are evaluated.

### Stage D: Generative benchmark

Generate target-conditioned corpora with multiple open and closed systems and both text-only and image-conditioned modes. Apply the frozen evaluation pipeline and report multidimensional diagnostic profiles.

### Stage E: Challenge evaluation

Apply the unchanged benchmark to non-Western, long-tail, and lower-exposure targets. Separate failures of the generator from failures of the reference representation.

## 6. Hypotheses

### H1: Semantic-formal gap

Generated images will be closer to their requested target in contextual representations than in physical and learned formal representations.

### H2: Hierarchical degradation

Target fidelity and specificity will decline from era to movement to artist level.

### H3: Prototype contraction

Generated distributions will approach target centroids while exhibiting smaller covariance, lower effective rank, reduced tail coverage, or fewer subclusters than held-out real distributions.

### H4: Exposure advantage

Canonical and frequently represented artists will show smaller average gaps than long-tail artists, but may also show stronger nearest-neighbor similarity to known works.

### H5: Conditioning asymmetry

Image-conditioned generation will reduce low-level color, composition, and formal gaps more strongly than contextual gaps, while text-only generation will show the reverse pattern.

### H6: Cross-feature incoherence

Some generated images will match target marginals in several feature families while exhibiting combinations that are rare in real target works.

### H7: Evaluator home-field advantage

Apparent fidelity will be higher when the generator and evaluator share related model families, representation objectives, or training distributions.

### H8: Residual measurement effects

Resolution and digitization controls will reduce some observed gaps, especially for local spatial features, but will not fully explain robust multifeature differences.

## 7. Statistical strategy

The primary analyses will operate in original or validated reduced feature spaces rather than in two-dimensional visualizations. Candidate distributional measures include energy distance, maximum mean discrepancy, and Wasserstein distance. Candidate coverage measures include k-nearest-neighbor support, covariance spectra, effective rank, and calibrated target percentiles. Specificity will be evaluated through target-versus-neighbor margins and held-out group classification.

Inference must respect the nested sampling structure. Generated seeds are not independent artists, and multiple digital files can represent the same physical work. Confidence intervals and hypothesis tests should therefore use hierarchical bootstrap or mixed-effects models with clustering at the canonical-work, target, and model levels as appropriate.

No aggregate benchmark score is specified at this stage. Raw module scores and uncertainty estimates will be retained so that any later weighting policy can be audited.

## 8. Interpretation policy

The benchmark supports constrained interpretations:

- contextual fit without formal fit indicates successful recovery of recognizable subject matter or iconography, not full formal fidelity;
- centroid fit with low coverage indicates prototype imitation;
- movement-level fit with low artist specificity indicates coarse stylistic recognition;
- marginal fit with abnormal cross-feature dependence indicates partial or assembled imitation;
- gaps within the reproduction noise floor are not interpretable as artistic differences;
- robust fit across feature families, evaluators, resolutions, and challenge targets is the strongest available computational evidence of transferable latent style fidelity.

The benchmark does not measure aesthetic quality, artistic value, intention, reception, consciousness, or human-perceived authenticity.

## 9. Expected contributions

1. A unified bridge between hand-designed statistical-physics observables and learned latent representations.
2. A digitization- and resolution-aware protocol for comparing historical reproductions with natively digital generated images.
3. A hierarchical benchmark spanning eras, movements, artists, and works.
4. A distributional account of fidelity that separates prototype similarity from diversity and coverage.
5. An explicit test of cross-feature coherence and evaluator-family bias.
6. A challenge design for measuring canon, exposure, and geographic limitations.
7. A reproducible public reference atlas and benchmark specification, subject to source-image rights.

## 10. Publication strategy

The research program is intentionally divisible into two papers:

### Paper 1: Measurement and reference atlas

Functional replication, resolution sensitivity, reproduction noise, feature validity, and construction of the frozen real-art reference atlas.

### Paper 2: Generative-model benchmark

Comparison of model families and conditioning modes; tests of semantic-formal asymmetry, prototype contraction, hierarchical degradation, exposure effects, and cross-feature incoherence.

This separation prevents benchmark claims from depending on an unvalidated measurement pipeline and allows the calibration work to stand as an independent methodological contribution.
