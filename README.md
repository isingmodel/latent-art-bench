# LatentArtBench

**A multiscale benchmark for measuring how well generative vision-language systems reproduce the statistical and latent structure of artists and art movements.**

> Status: research design and validation planning. No model scores or leaderboard claims have been released.

## Motivation

An image can look superficially like an Impressionist painting while failing to reproduce the color organization, compositional structure, spatial complexity, or diversity observed in historical works. Conversely, a generated image may occupy a plausible semantic embedding without matching lower-level formal properties.

LatentArtBench is designed to evaluate these differences. It treats an artist or movement not as a single prototype but as a distribution of works in several complementary feature spaces. Generated images are evaluated against held-out real works after accounting for image resolution, compression, digitization, and reproduction noise.

The project connects a methodological lineage that moves from hand-designed physical observables to learned latent representations:

1. color usage, color diversity, and brightness roughness;
2. inter-pixel chromatic distance and seamlessness;
3. information-theoretic color interaction and composition;
4. permutation entropy and statistical complexity;
5. pretrained visual, formal, semantic, and contextual representations.

## Central question

> To what extent do generative models reproduce the multilevel statistical invariants of a target artist or art movement, rather than merely reproducing recognizable subjects or a narrow stylistic prototype?

The benchmark operationalizes this question as **latent style fidelity**. It does not claim to measure consciousness, intention, aesthetic value, or a metaphysical essence of style.

## Design principles

- **Validation before evaluation.** A feature enters the benchmark only after functional replication, measurement-stability testing, and real-group validation.
- **Distributions, not prototypes.** Fidelity includes central tendency, variability, coverage, and cross-feature dependence.
- **Hierarchical evaluation.** Era, movement, artist, and work-level relations are measured separately.
- **Paper-faithful and harmonized tracks.** Original preprocessing is retained for replication, while a matched multiscale track supports fair real-versus-generated comparison.
- **Real-only reference fitting.** Dimensionality reduction and group models are fitted on real training works, frozen, and then applied to held-out real and generated images.
- **Digitization-aware inference.** Differences must exceed the noise induced by alternative digital reproductions of the same artwork.
- **Model pluralism.** The benchmark will compare reproducible open-weight systems and closed multimodal systems rather than generalizing from one generator.
- **Automated evaluation.** Human ratings are outside the current scope.
- **Diagnostic reporting first.** A multidimensional score profile is primary; any aggregate score or leaderboard policy remains undecided.

## Repository guide

- [Research proposal](docs/RESEARCH_PROPOSAL.md)
- [Benchmark specification](docs/BENCHMARK_SPECIFICATION.md)
- [Source-method and resolution matrix](docs/SOURCE_METHOD_MATRIX.md)
- [Corpus design](docs/CORPUS_DESIGN.md)
- [Validation protocol](docs/VALIDATION_PROTOCOL.md)
- [Research roadmap](docs/ROADMAP.md)
- [Project decisions](docs/DECISIONS.md)
- [References](docs/REFERENCES.md)
- [Contributing](CONTRIBUTING.md)

## Planned research program

### Study 1: Measurement and reference atlas

Reproduce the source methods on real artworks, quantify resolution and digitization sensitivity, establish feature-specific noise floors, and build a frozen hierarchical reference atlas.

### Study 2: Generative-model benchmark

Evaluate multiple generators and conditioning modes against artist- and movement-level reference distributions. Test formal-contextual asymmetry, prototype contraction, hierarchy degradation, exposure effects, and cross-feature incoherence.

## Data and rights

This repository will not redistribute copyrighted artwork files unless their licenses explicitly permit redistribution. Public releases should prioritize code, checksums, canonical identifiers, source URLs, metadata, derived non-reconstructive features, and documented acquisition procedures. See the [corpus design](docs/CORPUS_DESIGN.md) for details.

## License

The repository is released under the [MIT License](LICENSE). Third-party datasets, images, model weights, and cited publications retain their own licenses and terms.
