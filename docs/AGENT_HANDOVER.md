# Project handover

Read [STATUS.md](STATUS.md) for the current findings and outstanding review
requests. Inspect `git status --short --branch` before editing: the latest
user-supplied `critics/` files and the diagnostic prose report may be untracked.
They remain useful local work. The canonical manuscript is
[paper/paper.tex](../paper/paper.tex); build instructions are in
[paper/README.md](../paper/README.md).

## Current implementation

| Component | Entry point |
| --- | --- |
| Six-model design and numerical primitives | [painter_specificity_v2](../src/latent_art_bench/painter_specificity_v2/), [protocol](../studies/painter_specificity_v2/PROTOCOL.md) |
| Corrected reference reader and four replay views | [measurement workflow](../src/latent_art_bench/painter_specificity_measurement_v1/workflow.py), [correction record](../studies/painter_specificity_measurement_v1/CORRECTION.md) |
| Reference-content weighting | [reference protocol](../studies/painter_specificity_reference_v1/PROTOCOL.md) |
| Post-result target diagnostics | [painter_specificity_review_v1.py](../src/latent_art_bench/painter_specificity_review_v1.py), [recorded plan](../studies/painter_specificity_review_v1/PLAN.md) |
| Primary figures and tables | [make_specificity_figures.py](../paper/make_specificity_figures.py), [make_specificity_tables.py](../paper/make_specificity_tables.py) |
| Diagnostic tables, artist pairs and optional image panels | [make_review_figures.py](../paper/make_review_figures.py) |

The corrected reader selects the intended 649 measured references from a
historical manifest that also contains four failed records. It does not retry
those images. All four primary replay views use this reader. The separate
31-output first specificity attempt is excluded from analysis and remains closed.

The added diagnostics distinguish response magnitude, artist-pair alignment,
scene dependence and reference-target agreement. They are post-result analyses;
the original six slopes and 15 model comparisons are unchanged. The image
panels reveal source defects but do not measure or correct their population-wide
effect. See [STATUS.md](STATUS.md) before claiming a review request is resolved.

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
make figures-check      # Current and supporting figures/tables
make paper              # Compile after manuscript edits; inspect affected pages
```

`make specificity-audit` and `make review-images-check` additionally require
retained local image/response bytes. A documentation-only change needs link and
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
there is no automatic next review round or generation task.
