# Research Proposal

## Working title

**LatentArtBench: A Measurement-Qualified Benchmark for Artist-Distribution Fidelity in Generative Image Systems**

## Abstract

Generative image systems can produce images that are readily associated with named artists and art movements. Visual resemblance, however, does not establish that a system has reproduced the statistical structure of a style. A generated image may match familiar iconography while deviating in color organization, spatial composition, complexity, formal representation, or the relationships among these properties. It may also converge on a narrow prototype rather than reproduce the breadth of a historical oeuvre.

This project proposes LatentArtBench, a measurement-qualified and multiscale benchmark for measuring how closely generated images reproduce artist- and movement-associated distributions in complementary feature spaces. The long-term program spans physics-inspired observables, information-theoretic image partitioning, entropy-complexity measures, classical and pretrained vision features, and learned formal and contextual representations. The first benchmark will use only a small preregistered core. Before any model comparison, each feature must pass three gates: functional replication on real artworks, stability under digitization and resolution perturbations, and out-of-sample validity for the relevant art-historical grouping.

The empirical program uses a Western canonical development corpus, a separate external-validity and ontology-transfer corpus, a reproduction-calibration corpus containing multiple digital surrogates of the same works, acquisition-domain controls, and generated corpora from multiple open and closed model families. The resulting benchmark reports formal fit, contextual fit, specificity, distributional coverage, diversity contraction, cross-layer coherence, and robustness. It operationalizes **artist-distribution fidelity** as recovery of measured statistical regularities associated with a target under a specified prompt protocol. It does not treat those regularities as timeless invariants or equate them with human aesthetic judgment, intention, or metaphysical understanding.

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

Prior work has evaluated broad artwork classes, style transfer, artist prototypes, prompted-artist recognition, set-level artist signatures, AI-versus-human statistics, and artist-level diversity. LatentArtBench does not claim priority for those ideas individually. Its contribution is a protocol for deciding which measurements support distributional claims, at which target level, and above what reproduction and acquisition uncertainty, before comparing generators.

## 2. Research objective

The primary objective is to construct and validate a benchmark that answers:

> Under a frozen prompt and sampling protocol, how well do generative image systems reproduce formal, contextual, and distributional regularities associated with a specified artist or movement?

The project distinguishes five related capabilities:

1. **Fidelity:** proximity to the target real-work distribution.
2. **Specificity:** preference for the intended target over plausible neighboring artists or movements.
3. **Coverage:** recovery of the target distribution's variability rather than only its centroid.
4. **Prompt-conditional generalization:** persistence of target-associated formal structure across shared contents, templates, and repetitions rather than isolated exemplars.
5. **Coherence:** recovery of validated dependencies among formal and contextual feature families on a common eligible work set.

### Initial-study boundary

The initial study is deliberately smaller than the full program: text-only generation, a provisional 8–12 public-domain artists, shared content prompts, three measurement layers, and two co-primary endpoints. It focuses on prototype contraction and target specificity. Movement analysis, contextual asymmetry, and evaluator dependence are supporting diagnostics. Image conditioning, exposure proxies, memorization, and ontology transfer are deferred extensions.

Implementation begins with an even smaller development precursor: four artists, two measurements, one open-weight generator, and target-gap and specificity estimates only. This precursor exists to obtain the corpus, reliability, and variance evidence needed to plan the initial study; it is not itself the confirmatory benchmark.

## 3. Research questions

### RQ0: Measurement validity

Which observables remain stable across resolution, resampling, compression, color conversion, border removal, and alternative digital reproductions of the same work?

### RQ1: Target fidelity

How close are generated images to the held-out real distribution of the requested artist or movement in each feature family?

### RQ2: Target-level heterogeneity

How does difficulty vary across movement and artist targets after accounting for real-sample size, target distinctiveness, genre, source, and evaluator headroom?

### RQ3: Formal-contextual asymmetry

Are generated images systematically closer to target distributions in contextual or semantic representations than in physical and formal representations?

### RQ4: Distributional coverage

Do models reproduce within-target diversity, covariance, tails, and substructure, or do they contract toward a recognizable prototype?

### RQ5: Model effects

How do results vary across open and closed text-to-image model families under the same prompt protocol?

### RQ6: Canon and exposure effects

Are preregistered public-visibility and corpus-availability proxies associated with fidelity after accounting for corpus size, genre, period, source quality, and artist distinctiveness?

### RQ7: Representation dependence

Do conclusions remain stable when the evaluator architecture changes, or are apparent effects dependent on evaluator family?

RQ0, RQ1, RQ4, RQ5, and RQ7 define the initial study. RQ2 and RQ3 are secondary diagnostics. RQ6 belongs to a later extension and cannot expand the initial data collection.

## 4. Operational definition

Let a target group be denoted by \(t\), a feature family by \(k\), a generator and version by \(g\), a frozen prompt distribution by \(\pi\), and a conditioning mode by \(m\). Real and generated feature distributions are

\[
P_{t,k}^{\mathrm{real}} \quad \text{and} \quad Q_{g,t,\pi,m,k}^{\mathrm{gen}}.
\]

Artist-distribution fidelity is not a single Euclidean distance. It is a profile containing at least:

- the generated-to-target distributional distance;
- the generated-to-neighbor margin;
- the fraction of the real target support covered by generated works;
- the contraction or expansion of within-target variability;
- the preservation of dependencies across feature families;
- the stability of conclusions across preprocessing and evaluator choices.

All distances are calibrated against at least four empirical baselines:

1. held-out real works relative to their own target group;
2. held-out real works relative to neighboring target groups;
3. alternative digital reproductions of the same work;
4. source and acquisition-domain negative controls.

The profile has four named layers: formal feature fidelity, contextual or iconographic fidelity, distributional coverage, and cross-layer coherence. Only measurements that pass the limited human qualification study may additionally be described as perceptual style fidelity.

## 5. Study architecture

### Stage A: Functional replication

Implement the three retained core measurement layers and recover the defining image-level behavior and principal aggregate findings of their source methods on real artworks. Other source methods may be replicated later and cannot delay the initial study. Exact numerical replication is not required when the original image versions are unavailable, but the implementation must recover representative distributions, orderings, or historical directions.

### Stage B: Measurement calibration

Construct feature-response curves across controlled image resolutions and degradation conditions. Estimate variable reproduction uncertainty from multiple digital surrogates of the same physical work, then test source and acquisition-domain controls for systematic bias. Retain, modify, or restrict each feature based on its measurement reliability.

### Stage C: Real reference atlas and construct qualification

Estimate cross-classified reference distributions using real training works only. Validate each feature's artist- and movement-level signal on held-out real works, including leave-source-out tests and recorded nuisance variables. Use a limited blinded human study to qualify perceptual claims, not to create a general aesthetic score. Fit and freeze any standardization, PCA, UMAP, density model, or classifier before generated images are evaluated.

### Stage D: Generative benchmark

Generate text-conditioned corpora with multiple open and closed systems under shared content prompts, preregistered negative controls, and a complete failure and refusal log. Apply the frozen evaluation pipeline and report multidimensional diagnostic profiles. Image-conditioned generation is reserved for a later, separately identified study.

### Stage E: Challenge evaluation

Assess measurement invariance and ontology transfer with non-Western, long-tail, and lower-visibility targets. Use only domain-qualified features for generator comparisons, report evaluator and ontology failure separately, and do not combine these results into a universal leaderboard.

## 6. Initial-study hypotheses

### H1: Prototype contraction

Generated distributions will exhibit smaller effective rank or lower support coverage than equal-sized held-out real distributions, even when their target-centroid gap is small.

### H2: Content-controlled specificity

Adding the correct artist name to shared content prompts will improve the calibrated target-versus-neighbor margin relative to artist-free and wrong-artist controls.

### H3: Cross-layer incoherence

Generated distributions will show a larger calibrated joint formal-contextual discrepancy than held-out real-real splits, including cases where their qualified marginal gaps are individually small.

## Secondary diagnostics

### D1: Semantic-formal asymmetry

Generated images may appear closer to their requested targets in contextual representations than in formal representations. The contrast is normalized by same-target real variability and target-to-neighbor separation so that evaluator headroom is not mistaken for model behavior.

### D2: Target heterogeneity

Artist results may vary with target distinctiveness, real-corpus size, genre, source, and movement. No monotonic broad-to-narrow hierarchy is assumed.

### D3: Evaluator-family dependence

Apparent fidelity and model ranking will vary with evaluator family. Known architectural or data relationships will be reported, but unobservable relationships for closed models will not be asserted as causal affinities.

### Calibration expectation: residual measurement effects

Resolution, reproduction, source, and acquisition controls are expected to reduce some apparent gaps, especially for local spatial features. This is a measurement-calibration objective rather than a primary substantive hypothesis.

## 7. Statistical strategy

The primary analyses will operate in original or validated reduced feature spaces rather than in two-dimensional visualizations. The first benchmark preregisters a single calibrated distributional-gap statistic and a target-versus-nearest-neighbor specificity margin as co-primary endpoints. Coverage, effective-rank contraction, joint coherence, and evaluator rank stability are secondary endpoints. Alternative distances are sensitivity analyses, not opportunities for post-hoc metric selection.

Inference must respect the nested sampling structure. Generated repetitions are not independent artists, and multiple digital files can represent the same physical work. Generated and real sample sizes will be matched through repeated subsampling, with uncertainty clustered at the canonical-work, prompt-content, target, and model levels as appropriate. High-dimensional covariance analyses require real-only dimensionality reduction or shrinkage and a preregistered dimension-to-sample rule. Bootstrap procedures quantify available information; they do not compensate for too few independent works or targets.

No aggregate benchmark score is specified at this stage. Raw module scores and uncertainty estimates will be retained so that any later weighting policy can be audited.

## 8. Interpretation policy

The benchmark supports constrained interpretations:

- contextual fit without formal fit indicates successful recovery of recognizable subject matter or iconography, not full formal fidelity;
- centroid fit with low coverage indicates prototype imitation;
- movement-level fit with low artist specificity indicates coarse stylistic recognition;
- marginal fit with abnormal cross-layer dependence indicates partial or assembled imitation;
- gaps shown practically equivalent to the preregistered reproduction or real-real margin are not interpretable as artistic differences;
- robust fit across qualified feature families, evaluators, resolutions, prompts, and external-validity targets is the strongest available computational evidence of transferable artist-distribution fidelity.

The benchmark does not measure aesthetic quality, artistic value, intention, reception, consciousness, or human-perceived authenticity. Human qualification supports only the narrow perceptual questions it asks.

## 9. Expected contributions

1. A measurement-qualified bridge between a small set of interpretable observables and learned formal representations.
2. A digitization- and acquisition-aware protocol for comparing historical reproductions with natively digital generated images.
3. A content-controlled artist benchmark that separates target proximity from specificity and coverage.
4. A test of prototype contraction, low-dimensional cross-layer coherence, and evaluator-family dependence.
5. A reproducible reference atlas and benchmark specification, subject to source-image rights.

## 10. Publication strategy

The research program is intentionally divisible into three studies. This is a program architecture, not a commitment to maximize scope in each manuscript.

### Study 1: Measurement qualification and reference atlas

Qualification of a small core of feature families; reproduction and acquisition uncertainty; source confounding; limited human construct validation; and construction of the frozen real-art reference atlas.

### Study 2: Content-controlled generative benchmark

Comparison of text-to-image model families under shared content prompts, centered on target specificity and prototype contraction, with cross-layer incoherence and evaluator-family dependence as secondary diagnostics.

### Study 3: External validity and conditioning

Image-conditioned modes, artist phases, visibility associations, memorization diagnostics, and cross-cultural measurement invariance or ontology transfer.

This separation prevents benchmark claims from depending on an unvalidated measurement pipeline, keeps the first generator comparison identifiable, and treats cultural transfer as a measurement problem rather than a harder leaderboard split.
