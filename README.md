# LatentArtBench

**A measurement-qualified benchmark for testing how well generative image systems reproduce formal, contextual, and distributional regularities associated with artists and art movements.**

> Status: development-pilot substrate implemented; real-corpus and learned-formal qualification remain pending. No model scores or leaderboard claims have been released.

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

> Under identical content prompts, do generative models reproduce the measured formal distribution and internal diversity of a target artist, or merely a recognizable prototype?

The benchmark operationalizes this question as **artist-distribution fidelity**. Formal style fidelity, contextual or iconographic fidelity, distributional coverage, and cross-layer coherence are reported separately. The project does not claim to measure consciousness, intention, aesthetic value, human-perceived authenticity, or a metaphysical essence of style.

## Design principles

- **Validation before evaluation.** A feature enters the benchmark only after functional replication, measurement-stability testing, and real-group validation.
- **Distributions, not prototypes.** Fidelity includes central tendency, variability, coverage, and cross-feature dependence.
- **Cross-classified evaluation.** Era, movement, artist, genre, medium, and artist phase are modeled as overlapping labels where the data require it; work-level similarity is a separate instance or memorization track.
- **Paper-faithful and harmonized tracks.** Original preprocessing is retained for replication, while a matched multiscale track supports fair real-versus-generated comparison.
- **Real-only reference fitting.** Dimensionality reduction and group models are fitted on real training works, frozen, and then applied to held-out real and generated images.
- **Digitization-aware inference.** Differences must exceed the noise induced by alternative digital reproductions of the same artwork.
- **Model pluralism.** The benchmark will compare reproducible open-weight systems and closed multimodal systems rather than generalizing from one generator.
- **Automated operation, limited human qualification.** The released benchmark remains automated, while a small blinded study may be used to test whether selected metrics support perceptual style claims.
- **Diagnostic reporting first.** A multidimensional score profile is primary; any aggregate score or leaderboard policy remains undecided.
- **Prompts define the estimand.** Results are conditional on a frozen prompt distribution, conditioning mode, model version, and output-selection policy.

## Repository guide

Start with:

- [Research proposal](docs/RESEARCH_PROPOSAL.md)
- [Initial implementation plan](docs/ROADMAP.md)
- [Development-pilot implementation status](docs/IMPLEMENTATION_STATUS.md)
- [Project decisions and critique disposition](docs/DECISIONS.md)

Technical reference:

- [Benchmark specification](docs/BENCHMARK_SPECIFICATION.md)
- [Corpus design](docs/CORPUS_DESIGN.md)
- [Validation protocol](docs/VALIDATION_PROTOCOL.md)
- [Source-method and resolution matrix](docs/SOURCE_METHOD_MATRIX.md)
- [References](docs/REFERENCES.md)
- [Contributing](CONTRIBUTING.md)

## Development-pilot commands

The implementation is config-driven and uses a locked Python environment. It includes strict JSONL schemas, canonical-work leakage checks, deterministic sRGB preprocessing, the Lee et al. chromatic-distance/seamlessness feature, qualification cards, target-gap analysis, and provenance-aware reporting.

```bash
uv sync --extra dev
uv run latent-art-bench synthetic-dry-run
uv run pytest
```

The image adapter is test-only and rejects every model except `gpt-image-1` and `gpt-image-2`. It defaults to the loopback endpoint exposed by `~/dev/openai-oauth` and needs no API key:

```bash
# Safe request-plan test; never contacts the endpoint.
uv run latent-art-bench generate --dry-run

# Live API smoke test before WP5 requires this conspicuous exception.
# The supplied manifest contains only a neutral prompt marked test_only=true.
uv run latent-art-bench generate --allow-unqualified-test-generation
```

Live bypassed images are API-test artifacts only. They cannot be used as benchmark evidence, and the normal command remains blocked until both real-only qualification cards pass or conditionally pass. See [the image API contract](docs/IMAGE_API_TESTING.md), [the chromatic contract](docs/CHROMATIC_METHOD.md), and [the learned-formal feasibility spike](docs/LEARNED_FORMAL_FEASIBILITY.md).

## Planned research program

Implementation begins with a four-artist, two-measurement, one-generator development pilot and stops for review after its first reproducible results. This pilot is smaller than the intended benchmark and makes no model-family or artist-population claims.

### Study 1: Measurement and reference atlas

Qualify a deliberately small core of complementary measurements, quantify resolution, reproduction, and acquisition-domain sensitivity, and build a frozen cross-classified reference atlas.

### Study 2: Generative-model benchmark

Evaluate text-to-image generators under content-matched prompts, with target specificity and prototype contraction as the primary questions and cross-layer incoherence as a secondary outcome. Image conditioning, exposure associations, memorization, and ontology transfer remain later modules.

## Data and rights

This repository will not redistribute copyrighted artwork files unless their licenses explicitly permit redistribution. Public releases should prioritize code, checksums, canonical identifiers, source URLs, metadata, derived non-reconstructive features, and documented acquisition procedures. See the [corpus design](docs/CORPUS_DESIGN.md) for details.

## License

The repository is released under the [MIT License](LICENSE). Third-party datasets, images, model weights, and cited publications retain their own licenses and terms.
