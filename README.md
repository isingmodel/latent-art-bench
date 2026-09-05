# LatentArtBench

LatentArtBench analyzes **feature distances between image-generation outputs and original artists'
reference paintings**. The current analysis uses Monet, Sisley, Pissarro, and Cézanne; 31
interpretable color, spatial/orientation, and digital-texture features; and the existing SD-Turbo,
`gpt-image-1`, and `gpt-image-2` service outputs.

The [distance report with comparison plots](reports/painter_feature_distance_v1/REPORT.md) is the
main entry point. It contains absolute model–artist distances, complete generated-condition ×
reference-painter matrices, artist-free comparisons, painter specificity, feature diagnostics,
and an exploratory comparison using 16 generated images per condition in each recorded block.
Full-precision JSON and CSV exports accompany the report.

## Current status — 2026-09-05

The active extension is [repeated GPT Image generation with three prompt methods](docs/PROMPT_STUDY_WORKFLOW.md).
It adds a prospectively fixed request grid, calibrated primary prompt contrasts, resumable
generation and measurement, full outcome accounting, and comparison reports. The proposed
1,920-image design awaits the preferred cap (480/960/1,920 images); **no new images have
been generated in this extension**. The counts below describe the completed existing-data report.

- **Reference:** 649 measured confirmation paintings, from the existing 1,193-work frame.
- **Generated images:** 2,000 SD-Turbo outputs and 160 GPT Image service outputs.
- **Representation:** all 31 existing features, with the original normalization and frozen
  development-only scaler; no learned embeddings or new image extraction.
- **Distance analysis:** 180 complete matrix cells, 36 control/specificity summaries,
  372 coordinate diagnostics, 48 reference-to-reference distances, and 324 block-level comparisons.
- **Deliverable:** reproducible offline commands, a Markdown report, nine comparison plots in PNG
  and SVG, six CSV tables, numeric JSON, and source/code/output hash provenance.

Lower energy distance means closer measured feature distributions within the same feature family.
The analysis describes the observed data; it provides no combined model ranking or calibrated
reproduction threshold. GPT labels are requested service aliases with unverified underlying model
snapshots. Sample size, output geometry, subject matter and capture differences affect interpretation.

The original [v2 empirical report](reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS.md),
[its Korean translation](reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS_KO.md), and all
terminal study evidence are preserved. The original full paired crop analysis covered 3,340
measured images. Manuscript drafting remains deferred.

## Run and reproduce

Use the locked environment with both extras to preserve the shared environment's dependencies.
The delivered bundle already exists; verify it with:

```bash
uv run --locked --extra analysis --extra learned latent-art-bench feature-distances check \
  --output reports/painter_feature_distance_v1
```

To independently rebuild it at a new location:

```bash
uv run --locked --extra analysis --extra learned latent-art-bench feature-distances build \
  --output tmp/feature-distance-reproduction
```

The commands read existing numeric feature records and never request images or append to the
old study ledgers. Existing output directories are not overwritten. `check` verifies hashes and
reproduces numeric results, CSV tables, prose and plots byte-for-byte in temporary storage.
See [the analysis contract and command guide](docs/FEATURE_DISTANCE_ANALYSIS.md) for input
validation, formulas, output schemas and interpretation limits.

## Project map

| Path | Role |
| --- | --- |
| `src/latent_art_bench/painter_prompt_study_v1/` | Prospective repeated-prompt generation, calibrated analysis and separate module CLI |
| `studies/painter_prompt_study_v1/` | New prompt design and resource contract |
| `src/latent_art_bench/painter_feature_distance_v1/` | Current descriptive distance analysis, plotting and CLI |
| `reports/painter_feature_distance_v1/` | Distance report, plots, exports and provenance |
| `src/latent_art_bench/painter_feature_generation_v2/` | Preserved collection, generation, measurement and analysis pipeline |
| `studies/painter_feature_generation_v2/` | Source study protocol and prospective amendments |
| `data/manifests/painter_feature_generation_v2/` | Compact sealed numeric inputs and study evidence |
| `research_workspace/painter_feature_generation_v2/` | Ignored source images, generated images, weights and runtime evidence |
| `studies/painter_feature_generation_v1/` | Historical protocols; v1 code and evidence remain in their existing paths |
| `literature_reviews/` | Literature evidence and method rationale |
| `tests/` | Offline verification; live tests require separate authorization |
| `docs/` | Operational status, handover, analysis guide and evidence retention rules |

The `paper-study` CLI remains the stage interface for the completed v2 study. Its terminal
collection, generation, measurement and report commands must not be rerun in place. A distance
report build is a separate analysis of already exposed numeric evidence, not a restart of those
stages or a newly blinded experiment.

## Development and evidence

```bash
uv run --locked --extra analysis --extra learned ruff check .
uv run --locked --extra analysis --extra learned pytest -q -m "not live"
uv run --locked --extra analysis --extra learned latent-art-bench verify-evidence
uv run --locked --extra analysis --extra learned latent-art-bench paper-study audit
```

Read [current status](docs/STATUS.md), [artifact retention rules](docs/ARTIFACTS.md), and
[the agent handover](docs/AGENT_HANDOVER.md) before making changes. The [documentation
index](docs/INDEX.md) distinguishes current guidance from historical protocols.

Frozen protocols, receipts and ledgers are immutable; historical hashes resolve against their
recording commits. Ignored artwork, model weights and response bytes may be unique evidence.
A git clone alone does not preserve them. Never use `git clean -xfd` or broad deletion under
`artifacts/`, `data/`, or `research_workspace/`.

## License

Code and documentation use the [MIT License](LICENSE). Artwork, model weights, generated outputs,
museum metadata, and third-party sources retain their own rights.
