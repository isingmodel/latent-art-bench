# Project handover

Read [STATUS.md](STATUS.md) for the current findings and revision state.
Inspect `git status --short --branch` before editing and preserve existing work.
The canonical manuscript is
[paper/paper.tex](../paper/paper.tex); build instructions are in
[paper/README.md](../paper/README.md).

## Current implementation

| Component | Entry point |
| --- | --- |
| Six-model design and numerical primitives | [painter_specificity_v2](../src/latent_art_bench/painter_specificity_v2/), [protocol](../studies/painter_specificity_v2/PROTOCOL.md) |
| Corrected reference reader and four replay views | [measurement workflow](../src/latent_art_bench/painter_specificity_measurement_v1/workflow.py), [correction record](../studies/painter_specificity_measurement_v1/CORRECTION.md) |
| Reference-content weighting | [reference protocol](../studies/painter_specificity_reference_v1/PROTOCOL.md) |
| Post-result target diagnostics | [painter_specificity_review_v1.py](../src/latent_art_bench/painter_specificity_review_v1.py), [recorded plan](../studies/painter_specificity_review_v1/PLAN.md) |
| Follow-up noise and stability checks | [painter_specificity_review_v2.py](../src/latent_art_bench/painter_specificity_review_v2.py), [report](../reports/painter_specificity_review_v2/REPORT.md) |
| Source-quality sensitivity | [painter_reference_quality_v1.py](../src/latent_art_bench/painter_reference_quality_v1.py), [report](../reports/painter_reference_quality_v1/REPORT.md) |
| Primary figures and tables | [make_specificity_figures.py](../paper/make_specificity_figures.py), [make_specificity_tables.py](../paper/make_specificity_tables.py) |
| Diagnostic tables, artist pairs and historical image panels | [make_review_figures.py](../paper/make_review_figures.py) |
| Current original/generated image panels | [make_example_figures.py](../paper/make_example_figures.py), [selection manifest](../paper/example_selection.json) |
| Editorial assessments and manuscript-version bindings | [review record](../reports/paper_editorial_review_v1/README.md) |

The corrected reader selects the intended 649 measured references from a
historical manifest that also contains four failed records. It does not retry
those images. All four primary replay views use this reader. The separate
31-output first specificity attempt is excluded from analysis and remains closed.

The added diagnostics distinguish response magnitude, artist-pair alignment,
scene dependence and reference-target agreement. They are post-result analyses;
the original six slopes and 15 model comparisons remain preserved. The separate
870-source audit re-extracts 131 crops and varies development scaling and content
labels. FLUX retains the lowest error point estimate, but the adjusted Sunburst
comparison no longer excludes zero. The user explicitly excluded adding human
evaluation. See [STATUS.md](STATUS.md) for the latest revision and remaining limits.

## Continue work

Keep all four artists in the main scientific scope and write documentation and
the canonical paper in English. Paper prose and presentation scripts are editable.
For a scientific correction, define a separate versioned result with explicit
inputs and compare it against the preserved original; a frozen result is not a
reason to leave a demonstrated measurement problem uninvestigated.

The [analysis catalog](ANALYSES.md) maps supporting experiments and plotting code.
Use targeted checks for the files changed:

```bash
make specificity-check  # Four numerical views; compact inputs only
make review-check       # Separate diagnostics and their numerical presentation
make reference-quality-check  # Source-region/scaler/label sensitivity
make figures-check      # Current and supporting figures/tables
make paper              # Compile after manuscript edits; inspect affected pages
```

`make specificity-audit`, `make example-images-check` and
`make review-images-check` additionally require retained local image/response
bytes. The two image-panel checks cover the current and historical examples,
respectively. `make reference-quality-images-check`
verifies all 870 source hashes and re-extracts the 131 crop features. A documentation-only change needs link and
dependency checks, not a full Python test run.

## Preserve

All existing collectors and measurements are terminal. Replaying results does
not authorize restarting acquisition or adding images. Preserve original source
bindings, protocols, vectors, ledgers, failed attempts and numerical reports.
In particular, the diagnostic `analysis.json` binds its implementation, plan and
inputs; manuscript edits must not silently change those bytes.

Ignored `research_workspace/`, `artifacts/` and bound files under `tmp/` can hold
unique evidence. Preserve local configuration, secrets and the user's Korean
manuscript. See [ARTIFACTS.md](ARTIFACTS.md) for the retention boundary and Git
recovery of retired documentation. Historical review-score loops are closed;
there is no automatic next review round or generation task. Editorial scores
apply only to the PDF hash recorded for each assessment, not to later revisions.
