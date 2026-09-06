# LatentArtBench

LatentArtBench analyzes **feature distances between image-generation outputs and original artists'
reference paintings**. The current analysis uses Monet, Sisley, Pissarro, and Cézanne; 31
interpretable color, spatial/orientation, and digital-texture features; and the existing SD-Turbo,
`gpt-image-1`, and `gpt-image-2` service outputs.

The new [distribution scatter and separability report](reports/painter_distribution_exploration_v1/REPORT.md)
compares original and generated point clouds in common PCA views and evaluates their separability
in the full feature space. This post-hoc exploration uses existing measurements and adds no images.

The [main distance report after two authorized retries](reports/painter_prompt_retry_v1/ppr1-two-refusals-20260906-r2/REPORT.md)
contains: **1,920 measured generated images**, three prompt methods, comparison
plots and full-precision tables. The
[pre-retry exploratory statistical report](reports/painter_prompt_supplement_v1/ppss1-missingness-20260905/REPORT.md)
retains its original 1,918-image data and inference. The earlier
[existing-data distance report](reports/painter_feature_distance_v1/REPORT.md) also covers
SD-Turbo, artist-free comparisons and painter specificity.

## Current status — 2026-09-06

**Both subsequently authorized retries succeeded.** The complete derived grid contains 1,920
measured images, 64 per alias/method/condition. Across the original run and two retries there
were 1,922 requests, with both original refusals preserved. By-name prompts are closest among
the three methods in 19/24 painter × alias × family cells; style plus aspects is closest in
the other five. Explicit style instruction has larger distance than by-name prompting in all
24 comparisons. The completed view is descriptive because the two later outputs were outside
the original randomized request sequence. See [current status](docs/STATUS.md) for exact retry
provenance, results and verification.

The following accounting describes the preserved pre-retry experiment:

The [repeated GPT Image study](docs/PROMPT_STUDY_WORKFLOW.md) is complete. All **1,920 approved
requests** were attempted once: **1,918 images generated and measured, two service refusals**.
The grid covers two requested aliases, three methods (by name, style instruction, style plus
aspects), four painters plus matched artist-free controls, 16 scenes and four repetitions.
There are 958 measured outputs under `gpt-image-1` and 960 under `gpt-image-2`.

A separate [post-registration supplement](docs/PROMPT_SUPPLEMENT_WORKFLOW.md) was specified after
the first refusal and before new feature measurement. Its [completed report](reports/painter_prompt_supplement_v1/ppss1-missingness-20260905/REPORT.md)
reports equal-scene-weighted available-output
distances and 48 exploratory matched-pair tests of a joint availability-and-feature sharp null,
with Holm adjustment and no confidence intervals. Its qualification passed and its design freeze
was committed before source measurement. The original complete-grid primary remains
[unavailable](reports/painter_prompt_study_v1/pps1-gpt-prompts-20260905/REPORT.md); neither refused
slot was retried or replaced. Numerical and report-byte replay passed.

On the observed matched supports, explicit style instruction increased distance relative to
by-name prompting in all 24 artist × alias × feature-family comparisons. Three of these reject
the exploratory joint null after Holm adjustment: Monet color under each alias and Pissarro
texture under `gpt-image-2`. Added aspects had mixed directions, with no Holm rejection. These
are finite-sample observations, not evidence of verified model superiority or aesthetic quality.
See [the workflow](docs/PROMPT_SUPPLEMENT_WORKFLOW.md) for estimates and interpretation limits.

The new bundle includes 360 distance cells, 744 coordinate diagnostics, all 48 exploratory tests,
10 CSV tables and three plots in PNG/SVG. It retains the same 649-painting reference, 221-painting
development scaler and 31 features. Reviews are maintainer-run LLM subagent reviews, not
institutionally independent. [Current status](docs/STATUS.md) records the terminal evidence.

The separately preserved existing-data report contains:

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
Verify the latest completed-grid report and corrected figure with:

```bash
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_retry_report_v2 check
```

Verify the pre-retry prompt supplement with:

```bash
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_supplement_v1.cli check ppss1-missingness-20260905
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_supplement_v1.cli audit
```

Verify the earlier existing-data bundle with:

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
| `src/latent_art_bench/painter_prompt_supplement_v1/` | Separate post-registration numeric supplement, qualification and module CLI |
| `studies/painter_prompt_supplement_v1/` | Missingness weighting, exploratory joint-null tests and preservation contract |
| `reports/painter_prompt_supplement_v1/ppss1-missingness-20260905/` | Completed prompt comparison report, full-precision tables and PNG/SVG plots |
| `reports/painter_prompt_study_v1/pps1-gpt-prompts-20260905/` | Original unavailable-primary report and complete request accounting |
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
