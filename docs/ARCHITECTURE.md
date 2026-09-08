# Architecture

LatentArtBench is a Python package with versioned research namespaces. The current
paper combines a completed controlled study with a separately frozen computational
revision. Both replay measured vectors and metadata offline. Historical acquisition
and generation implementations remain as reproducibility dependencies.

## Current analysis path

```text
retained development, reference and generated feature records
    -> painter_distribution_study_v1: original controlled analysis
    -> painter_distribution_revision_v1: descriptive diagnostics
    -> sealed numerical results in data/manifests/
    -> complete report tables and plots in reports/
    -> paper/make_figures.py: three selected manuscript figures
    -> paper/paper.tex -> paper/paper.pdf
```

The revision checks consistency with the original primary endpoints. Its report
renderer is separately bound and verified. The manuscript figure builder reads
hash-checked published values and saved PCA coordinates; it does not fit a new
projection or produce new statistical estimates.

The successor `painter_responsiveness_v1` reuses the retained loader, 31-feature
extractor and original development scalers. It adds equal-brief diagnostics,
prospective factorial inference/simulation, and a separate frozen reference-display
workflow. Generation/measurement entry points require actual stage evidence and
have no implicit live calls. Its complete component map and replay command are in
[ANALYSES.md](ANALYSES.md#mechanism-follow-up-painter-responsiveness). The old paper
pipeline is unchanged; D0 does not add a causal endpoint to the manuscript.

The new `painter_responsiveness_v2` reuses the same stable measurement and
factorial primitives for a computational-only, shared-control intervention.
`collection.py` binds a local OAuth source/process and stores every attempt;
`workflow.py` seals all slots, measures available images and reproduces analyses.
`diagnostics.py` tests held-repetition scene retrieval, `analysis.py` estimates
instruction interactions and exposed-reference chroma overlap, and `report.py`
renders only saved results. Human-rating prerequisites apply to the preserved v1
scope, not this explicitly narrower successor. All live calls require an explicit
CLI action, and all Makefile targets remain offline.

## Modules to read

All package paths below are under `src/latent_art_bench/`.

| Module or package | Responsibility |
| --- | --- |
| `painter_distribution_revision_v1/common.py` | Load, join and validate sealed vectors, requests and provenance attributes |
| `painter_distribution_revision_v1/analysis.py` | Verify inputs, orchestrate calculation and compare numerical replay |
| `painter_distribution_revision_v1/metrics.py` | Feature views, weighted energy, variance decomposition, reference/scaler influence and painter interactions |
| `painter_distribution_revision_v1/diagnostics.py` | Coverage controls, metadata associations and grouped cross-route classification |
| `painter_distribution_revision_v1/timing.py` | Request-group timing, attrition and retry sensitivities |
| `painter_distribution_revision_v1/report.py` | Full diagnostic report tables and plots |
| `painter_distribution_revision_v1/report_publication.py` | Bound report rendering and byte-replay verification |
| `painter_distribution_study_v1/analysis.py`, `statistics.py`, `inference.py` | Original controlled estimates, numerical primitives and conditional randomization design |
| `painter_distribution_study_v1/analysis_publication.py`, `main_report.py` | Original numerical and report replay entry points |
| `painter_feature_generation_v2/features.py`, `statistics.py` | The 31-feature representation and frozen development-based transformations |
| `painter_distribution_exploration_v1/statistics.py` | Shared fixed-kernel classification primitives |
| `io.py`, `evidence.py` | Structured records/hashes and historical commit-bound evidence verification |

The `latent-art-bench` Typer CLI exposes historical study commands and
`verify-evidence`. Current analysis modules also provide direct `python -m`
entry points. [ANALYSES.md](ANALYSES.md) maps each supported replay command to its
inputs and outputs; the root Makefile groups these commands by task.

## Storage boundaries

| Path | Role |
| --- | --- |
| `paper/` | Editable current manuscript, bibliography, selected figures and builder |
| `studies/` | Versioned protocols and study plans; many are immutable freeze inputs |
| `configs/` | Design and request configuration; terminal study configs remain preserved |
| `data/manifests/` | Compact tracked vectors, request identities, events, freezes and receipts |
| `reports/` | Terminal numerical tables, report text, plots and provenance |
| `research_workspace/` | Ignored content-addressed artwork, generation response bodies and runtime evidence |
| `artifacts/` | Ignored model/source material and other retained research bytes |
| `docs/` | Current guidance, analysis methods and retained research proposals/reviews |
| `tests/` | Offline numerical, contract, provenance and replay tests |

Large image bytes are not in Git. Numeric replay does not require API credentials
or model weights; image re-extraction requires the retained raw evidence. See
[ARTIFACTS.md](ARTIFACTS.md) before deleting anything in an ignored directory.

## Why older namespaces remain

The controlled study imports measurement, scaling, randomization, hashing and
classification primitives developed in earlier namespaces. Source paths and
versions also appear in scientific freezes. Removing or moving a historical
package merely because its collection has ended would break replay or obscure
what ran. New scientific work should use a new namespace while reusing stable,
tested primitives where their contracts still apply.

Acquisition and transport code is separate from numeric replay. The completed
collection modules encode terminal attempts, refusals, continuations and exact
technical retries; they are records of execution, not reusable commands for
silently extending a dataset. No current Makefile replay target opens collection.

The evidence audit verifies commit-bound records, while each study's replay check
verifies its own numerical or report outputs. Run both when relevant; success in
one does not replace the other. [AGENTS.md](../AGENTS.md) and
[CONTRIBUTING.md](../CONTRIBUTING.md) specify change and test requirements.
