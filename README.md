# LatentArtBench

**A measurement-gated research framework for testing how well generative image systems reproduce formal, contextual, and distributional regularities associated with artists and art movements.**

> Status: `pilot_0` and `pilot_1` both ended with failed measurement qualification. The `pilot_1` scientific gate is closed. A separate test-only engineering traversal resolved 40 frozen generation cells through `~/dev/openai-oauth`, requesting only `gpt-image-1` and `gpt-image-2`; it does not enable a scientific score, ranking, or leaderboard claim.

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
- [Post-pilot roadmap and pilot_2 design](docs/ROADMAP.md)
- [Development-pilot implementation status](docs/IMPLEMENTATION_STATUS.md)
- [Failure investigation and source-paper audit](docs/FAILURE_INVESTIGATION.md)
- [Development-pilot artist selection](docs/ARTIST_SELECTION.md)
- [Project decisions and critique disposition](docs/DECISIONS.md)
- [Final pilot_1 test-only report](reports/pilot_1/REPORT.md)
- [Final pilot_1 evidence anchor](reports/pilot_1/EVIDENCE.md)

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
uv sync --locked --extra dev --extra learned
uv run --locked latent-art-bench synthetic-dry-run
uv run --locked pytest
```

The frozen corpus audit uses official AIC and CMA APIs plus frozen NGA and Met Open Access snapshots. After supplying those local snapshot paths, the historical `pilot_0` path is:

```bash
uv run --locked latent-art-bench audit-corpus --nga-data-dir /path/to/nga/data --met-csv /path/to/MetObjects.csv
uv run --locked latent-art-bench acquire-corpus
uv run --locked latent-art-bench preprocess
uv run --locked latent-art-bench extract-features artifacts/pilot_0/derived_views.jsonl
uv run --locked latent-art-bench evaluate-chromatic
uv run --locked latent-art-bench qualify \
  configs/pilot_0/qualification/evidence.chromatic.json \
  configs/pilot_0/qualification/evidence.learned_formal.json \
  --output-dir configs/pilot_0/qualification
uv run --locked latent-art-bench report-pilot
```

`pilot_1` tests repaired implementations without changing the historical `pilot_0` cards. Populate `artifacts/models/sd2-base-vae/` with the pinned VAE files documented in [the learned-formal feasibility report](docs/LEARNED_FORMAL_FEASIBILITY.md), then run the real-data preparation and extraction steps:

```bash
uv run --locked latent-art-bench preprocess \
  --config configs/pilot_1/pilot.yaml \
  --output-manifest artifacts/pilot_1/derived_views.jsonl \
  --output-dir artifacts/pilot_1/derived
uv run --locked latent-art-bench extract-features artifacts/pilot_1/derived_views.jsonl \
  --config configs/pilot_1/pilot.yaml \
  --output-manifest artifacts/pilot_1/chromatic_features.jsonl
uv run --locked latent-art-bench extract-learned-formal artifacts/pilot_1/derived_views.jsonl
```

The locked finalization sequence below verifies the recovered model, reruns both final real-only evaluations, writes the failed qualification cards, attests the already gathered generation ledger, and reproduces the engineering-only diagnostics. The checkpoint argument must be the pinned 5,214,864,007-byte file whose SHA-256 is recorded in the configuration.

```bash
uv run --locked latent-art-bench verify-learned-formal-model \
  --full-checkpoint /path/to/512-base-ema.ckpt
uv run --locked latent-art-bench evaluate-chromatic-v2
uv run --locked latent-art-bench evaluate-learned-formal-v2
uv run --locked latent-art-bench qualify \
  configs/pilot_1/qualification/evidence.chromatic.json \
  configs/pilot_1/qualification/evidence.learned_formal.json \
  --config configs/pilot_1/pilot.yaml \
  --output-dir configs/pilot_1/qualification
uv run --locked latent-art-bench attest-generation-manifest \
  artifacts/pilot_1/generation_calls.jsonl \
  --config configs/pilot_1/pilot.yaml
uv run --locked latent-art-bench prepare-generated-features \
  artifacts/pilot_1/generation_calls.jsonl \
  --config configs/pilot_1/pilot.yaml \
  --allow-unqualified-test-preparation
uv run --locked latent-art-bench build-pilot-analysis-cells \
  --config configs/pilot_1/pilot.yaml
uv run --locked latent-art-bench analyze-pilot \
  artifacts/pilot_1/analysis_cells.jsonl \
  --config configs/pilot_1/pilot.yaml \
  --output-manifest artifacts/pilot_1/analysis_results.jsonl \
  --allow-unqualified-test-analysis
uv run --locked latent-art-bench report-pilot \
  --config configs/pilot_1/pilot.yaml \
  --generation-manifest artifacts/pilot_1/generation_calls.jsonl \
  --analysis-cells artifacts/pilot_1/analysis_cells.jsonl \
  --analysis-manifest artifacts/pilot_1/analysis_results.jsonl \
  --output-dir reports/pilot_1
```

The two cards written by this sequence are both `fail`, so ordinary scientific feature preparation and analysis remain blocked. The two explicit flags above are the only route used to finish the engineering traversal; they mark the generated features and all downstream cells as `api_integration_test_only`.

The retained ledger contains 41 attempts for 40 resolved cells: 20 successful files per requested label plus one preserved `gpt-image-1` refusal before an exact-cell retry succeeded. All 40 requests asked for `1024x1024`; 0 of 40 returned files matched that size. The local proxy routes to the ChatGPT Codex backend, not the public `api.openai.com` Images API, and the retained responses do not verify which backend model executed. The resulting 16 named-artist cells and 64 artist-free matched pairs are therefore non-scientific diagnostics. All 16 specificity reference-resampling ranges include zero; they are not inferential confidence intervals.

See the [final report](reports/pilot_1/REPORT.md), [evidence anchor](reports/pilot_1/EVIDENCE.md), [failure investigation](docs/FAILURE_INVESTIGATION.md), [image API contract](docs/IMAGE_API_TESTING.md), [chromatic contract](docs/CHROMATIC_METHOD.md), and [learned-formal feasibility report](docs/LEARNED_FORMAL_FEASIBILITY.md).

A clean checkout contains the compact report, qualification, attestation, analysis, and evidence-index snapshots. Raw museum images, generated PNGs, model/source checkouts, derived views, and high-dimensional feature or vector manifests remain ignored local artifacts. Their identities are recorded in the evidence anchor, but a clean checkout cannot byte-verify or recompute absent local bytes.

## Planned research program

The completed development cycle used four artists, two measurements, and two requested image-model labels. It is smaller than the intended benchmark and makes no model-family or artist-population claims.

### Study 1: Measurement and reference atlas

Qualify a deliberately small core of complementary measurements, quantify resolution, reproduction, and acquisition-domain sensitivity, and build a frozen cross-classified reference atlas.

### Study 2: Generative-model benchmark

Evaluate text-to-image generators under content-matched prompts, with target specificity and prototype contraction as the primary questions and cross-layer incoherence as a secondary outcome. Image conditioning, exposure associations, memorization, and ontology transfer remain later modules.

## Data and rights

This repository will not redistribute copyrighted artwork files unless their licenses explicitly permit redistribution. Public releases prioritize code, checksums, canonical identifiers, source URLs, metadata, compact non-reconstructive evidence snapshots, and documented acquisition procedures. See the [corpus design](docs/CORPUS_DESIGN.md) for details.

## License

The repository is released under the [MIT License](LICENSE). Third-party datasets, images, model weights, and cited publications retain their own licenses and terms.
