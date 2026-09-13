# Analysis and plotting catalog

Run commands from the repository root with the recorded Python 3.13.11 runtime
and locked environment. The [results index](../reports/README.md) links reports;
this document maps their computation and presentation. All commands below are
offline checks or manuscript builds, not collection or feature extraction.

## Current six-model experiment

Inputs are retained under
[data/manifests/painter_specificity_v2/psv2-20260911](../data/manifests/painter_specificity_v2/psv2-20260911/).
The [protocol](../studies/painter_specificity_v2/PROTOCOL.md) defines the 1,008-image
design. The [reader correction](../studies/painter_specificity_measurement_v1/CORRECTION.md)
preserves the intended 649 measured references and separate 221-work scaler.
The [content-weighting protocol](../studies/painter_specificity_reference_v1/PROTOCOL.md)
defines the additional reference sensitivity.

| Calculation | Source | Check |
| --- | --- | --- |
| Artist contrasts, corrected error and paired model regressions | [analysis.py](../src/latent_art_bench/painter_specificity_v2/analysis.py), [corrected workflow](../src/latent_art_bench/painter_specificity_measurement_v1/workflow.py) | `make specificity-check`: full/square × pooled/content-weighted reference views |
| Terminal report, collection accounting and raw-byte identity | [report.py](../src/latent_art_bench/painter_specificity_measurement_v1/report.py) | `make specificity-audit`; requires local responses/images |
| Post-result decomposition, calibration, artist pairs and reference controls | [painter_specificity_review_v1.py](../src/latent_art_bench/painter_specificity_review_v1.py), [plan](../studies/painter_specificity_review_v1/PLAN.md), [numerical record](../reports/painter_specificity_review_v1/analysis.json) | `make review-check` |

The direct numerical entry point is:

```bash
uv run --locked python -m latent_art_bench.painter_specificity_measurement_v1.workflow analyze --check
# Add --square, --reference, or both for the other three saved views.
```

Post-result diagnostics do not extend the original 21-comparison family.
The first, stopped 31-output attempt remains excluded. All collectors and
measurements are terminal.

## Manuscript presentation

Renderers read retained results. Example panels additionally read source images
only when explicitly requested. Source/report figures remain separate from the
editable manuscript displays.

| Presentation | Builder | Inputs |
| --- | --- | --- |
| Six-model comparisons, centered contrasts, error/spread and four-painter projections | [make_specificity_figures.py](../paper/make_specificity_figures.py) | Saved specificity results and reference-only projections |
| Primary numerical tables | [make_specificity_tables.py](../paper/make_specificity_tables.py) | Saved primary and sensitivity results |
| Diagnostic tables and artist-pair figure | [make_review_figures.py](../paper/make_review_figures.py) | Separate diagnostic `analysis.json` |
| 36 generated and four reference examples | Same builder with `--images` | Retained source bytes and [inspection manifest](../reports/painter_specificity_review_v1/inspection.json) |
| Earlier distribution, control and retrieval figures | [make_figures.py](../paper/make_figures.py) | Exploration coordinates, controlled/revision tables and responsiveness summaries |
| Palette block display | [replay_palette.py](../paper/replay_palette.py) | Committed chroma outcomes, request schedule and primary estimates |
| Measurement challenges and geometry displays | [make_validation_figure.py](../paper/make_validation_figure.py), [make_geometry_figure.py](../paper/make_geometry_figure.py) | Saved validation and naming-geometry results |

```bash
make figures-check       # Verify current and supporting figures/tables
make figures             # Rebuild presentation only
make paper               # Rebuild and compile; see paper/README.md
make review-images-check # Optional: verify image sources and example panels
```

Normal builds reuse the committed example PDFs. They do not need full-resolution
images. Image panels expose calibration strips and a title-class mismatch;
they do not constitute a full reference audit.

## Supporting analyses

Package paths below are relative to `src/latent_art_bench/`. Each namespace has
its protocol or methods in `studies/`, input bindings in `data/manifests/` or
report provenance, and outputs linked from the results index.

| Evidence | Numerical code | Report plotting | Replay |
| --- | --- | --- | --- |
| Four-painter distribution exploration | `painter_distribution_exploration_v1/{analysis,statistics}.py` | `report.py` in the same package | `make four-painter-analysis` |
| Earlier content/reference controls | `painter_distribution_study_v1/diagnostics.py` | Same module | Included in `make four-painter-analysis` |
| Completed-grid retry presentation | Original `painter_prompt_retry_v1.py` results | `painter_prompt_retry_report_v2.py` | Included in `make four-painter-analysis` |
| Controlled named/free comparisons | `painter_distribution_study_v1/{analysis,statistics,inference}.py` | `main_report.py` | `make analysis`; report bundle: `make plots` |
| Content, reference/scaler and timing diagnostics | `painter_distribution_revision_v1/{analysis,metrics,diagnostics,timing}.py` | `report.py`, checked by `report_publication.py` | Included in `make analysis` and `make plots` |
| Palette intervention and scene retrieval | `painter_responsiveness_v2/{analysis,diagnostics}.py` | `report.py` | `make computational-responsiveness`; compact primary only: `make palette-check` |
| Palette quantile correction | `painter_responsiveness_quantiles_v1.py` | Same module | Included in `make computational-responsiveness` |
| Processing challenges and common-square sensitivity | `painter_measurement_validation_v1/{pipeline,statistics}.py` | `report.py` | `make validation-check` |
| Separate temporal naming/palette replication | `painter_naming_replication_v1/{analysis,workflow}.py` | Analysis output | `make replication-check` |
| Held-scene moment maps and evaluation centering | `painter_naming_geometry_v1/`, `painter_naming_centering_v1/` | Geometry `report.py`; centering has no plot | `make geometry-check` |
| Incomplete clause experiment and separate successor | `painter_clause_validation_v1/analysis.py`, `painter_clause_successor_v1/analysis.py` | Numerical reports; manuscript tables | `make clause-check`, `make clause-successor-check` |
| Prospective fixed-map comparison | `painter_map_validation_v2/analysis.py` | Numerical report; manuscript table | Command below |

```bash
uv run --locked python -m latent_art_bench.painter_map_validation_v2 check
```

The four-painter exploration is descriptive and retains the two later retries;
it does not restore the incomplete prompt study's primary inference. The
controlled naming, palette, temporal, clause and fixed-map panels remain separate.
The map-transfer result reverses the historical ordering on one endpoint and
must remain visible. Temporal replication was run by the same maintainer.

Some supporting checks authenticate local response hashes even though they
replay compact measurements. In particular, full palette and fixed-map checks
need retained responses; `make palette-check` provides the numeric-only palette
path. Use the versioned public adapters for the released standalone contracts.

## Earlier development and public replay

These records remain dependencies or context, without new primary claims.

| Scope | Source and result | Existing offline check |
| --- | --- | --- |
| Baseline 31-feature distances | [package](../src/latent_art_bench/painter_feature_distance_v1/), [report](../reports/painter_feature_distance_v1/REPORT.md) | `uv run --locked --extra analysis --extra learned latent-art-bench feature-distances check --output reports/painter_feature_distance_v1` |
| Original prompt grid, missingness supplement and retry | [study](../studies/painter_prompt_study_v1/), [supplement](../studies/painter_prompt_supplement_v1/), [retry](../studies/painter_prompt_retry_v1/) | Versioned CLI commands below |
| Earlier mechanism diagnostic | [package](../src/latent_art_bench/painter_responsiveness_v1/), [study guide](../studies/painter_responsiveness_v1/README.md) | `make responsiveness`; human-validation scope was not performed |
| Corpus census and empirical feature baseline | [v1 study](../studies/painter_feature_generation_v1/README.md), [v2 study](../studies/painter_feature_generation_v2/) | `make evidence`; v2 integrity: `uv run --locked latent-art-bench paper-study audit` |
| Synthetic qualification and technical pilots | Protocols and receipts in their originating study/manifests | Consult the fixed study guide; do not rerun create-once writers |

```bash
uv run --locked python -m latent_art_bench.painter_prompt_study_v1.cli check-run pps1-gpt-prompts-20260905
uv run --locked python -m latent_art_bench.painter_prompt_supplement_v1.cli check ppss1-missingness-20260905
uv run --locked python -m latent_art_bench.painter_prompt_retry_v1 check
```

Public adapters are `tools/paper_release.py`, `paper_geometry_release.py`,
`paper_clause_release.py`, `paper_map_release.py` and
`paper_map_validation_release.py`. Their study guides and verification receipts
are linked in the [results index](../reports/README.md#historical-public-releases).
Run them against the appropriate extracted archive, not an unrelated repository
tree. The separate `paper_map_portability_diagnostic.py` records the strict
Ubuntu mismatch; it does not change the failed replay contract.

Use [test scope](../tests/README.md) to choose between targeted tests,
`make check` and `make check-all`. Evidence integrity, numerical equality,
figure equality and measurement validity are different checks. Investigate
mismatches against recorded inputs; never refresh a stored hash to hide drift.
