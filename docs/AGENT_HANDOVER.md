# Project handover — 2026-09-15

Read [STATUS.md](STATUS.md) for the current findings and revision state.
Inspect `git status --short --branch` before editing and preserve existing work.
The canonical manuscript is
[paper/paper.tex](../paper/paper.tex); build instructions are in
[paper/README.md](../paper/README.md).

## Current handover state

The final manuscript revision and repository cleanup were committed as
`f9e39354e4625e070c100a9ef2d55c77552e2076` and pushed to `origin/main`.
At handover, only `main` exists locally and remotely, with one worktree and no
pending manuscript changes. Keep `main` as the sole branch unless the user
changes that instruction; check the live Git state before starting new work.

The paper is **Artist-Name Responses beyond a Shared Painting Effect in
Text-to-Image Generation**. Its final PDF has **23 pages**, a **151-word abstract**
and 9,655 extracted PDF words. The user explicitly removed the manuscript
length limit; do not compress necessary explanations to recover the earlier
22-page layout. The instruction not to add human evaluation remains in force.
The [final snapshot](../reports/paper_editorial_review_v1/final_update/FINAL_SNAPSHOT.json)
binds the PDF, TeX inputs, figures and presentation builders to exact hashes.

The final edit explains three different comparisons: scene-by-scene error,
error after averaging scenes, and error after held-out calibration. Calibration
fits one nonnegative multiplier per model on the other 13 scenes and applies it
to centered generated contrasts in the omitted scene; it does not change images
or the reference target. Table 3 adds each model's corrected shared/generic
cosine and **squared** magnitude ratio from existing diagnostic records.

The conclusion now names the artist-free baseline and includes the oil-painting
clause in the shared response. Main-text pointers connect the recorded model
configurations to their version-verification limits and keep earlier experiments
separate. The original/generated image comparison, all four painters and the
overview/detail geometry figure remain. See the
[final revision decisions](../reports/paper_editorial_review_v1/final_update/README.md)
for accepted and rejected review suggestions.

## Review status and version boundaries

Editorial scores are model judgments about a particular manuscript snapshot,
not human evaluation or evidence of scientific validity.

| Manuscript snapshot | Assessment | Status |
| --- | --- | --- |
| Original round 33 | Three fresh agents; mean 9.2916666667/10 | Original goal completed; all 99 reviews across 33 rounds retained |
| Second revision, assessed in `_04` | Claude Opus 5: 8.0625; Astra xhigh: 8.8125; mean 8.4375 | Last independently scored version, preserved unchanged |
| Current final update after `_04` | No new independent score | Selected feedback incorporated; earlier scores do not apply |

The [review index](../reports/paper_editorial_review_v1/README.md) records the
full sequence, including the earlier `_01` and `_03` assessments and cancelled
`_02` requests. The review loop is closed; do not start another evaluation round
or treat the old stopping threshold as unfinished work.

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
| Portable editorial archive verification | [audit_paper_reviews.py](../scripts/audit_paper_reviews.py), [archive guide](../reports/paper_editorial_review_v1/ARCHIVE.md) |

The corrected reader selects the intended 649 measured references from a
historical manifest that also contains four failed records. It does not retry
those images. All four primary replay views use this reader. The separate
31-output first specificity attempt is excluded from analysis and remains closed.

The added diagnostics distinguish response magnitude, artist-pair alignment,
scene dependence and reference-target agreement. They are post-result analyses;
the original six slopes and 15 model comparisons remain preserved. The separate
870-source audit re-extracts 131 crops and varies development scaling and content
labels. FLUX retains the lowest uncalibrated error point estimate, but the
adjusted Sunburst comparison no longer excludes zero after source correction.
GPT Image 2 has the lowest held-out calibrated error estimate. No model is
established to beat the no-distinction benchmark before calibration.
See [STATUS.md](STATUS.md) for the findings and remaining limits.

## Last verified state

The [final validation receipt](../reports/paper_editorial_review_v1/final_update/VALIDATION.json)
records the checks completed for the final manuscript on 2026-09-15:

- Ruff and all **848 routine tests** passed.
- Figure/table replay passed; the current image panels replayed exactly and all
  **40 source hashes** were verified.
- The portable editorial audit passed. Its optional local check verified
  **36 historical manuscript snapshots** and **24 execution artifacts**.
- The PDF compiled without warnings, and all **23 pages** were rendered and
  visually inspected. Scientific source, protocols, measurements and results
  were unchanged.

The full historical test suite and crop-feature re-extraction were not rerun for
that editorial update. Earlier broader verification has its own dated receipts;
do not present it as newly performed. This handover-only update requires link
and command-reference checks, not a manuscript rebuild or another full test run.

## Continue work

Keep all four artists in the main scientific scope and write documentation and
the canonical paper in English. Paper prose and presentation scripts are editable.
For a scientific correction, define a separate versioned result with explicit
inputs and compare it against the preserved original; a frozen result is not a
reason to leave a demonstrated measurement problem uninvestigated.

The [analysis catalog](ANALYSES.md) maps supporting experiments and plotting code.
Run from the repository root using the recorded Python 3.13.11 environment and
`uv`; PDF compilation also requires Tectonic. Use targeted checks for the files changed:

```bash
make specificity-check  # Four numerical views; compact inputs only
make review-check       # Separate diagnostics and their numerical presentation
make reference-quality-check  # Source-region/scaler/label sensitivity
make figures-check      # Current and supporting figures/tables
make paper              # Compile after manuscript edits; inspect affected pages
make editorial-check    # Portable review integrity and arithmetic; no model calls
make check              # Ruff and the current routine test suite for code changes
```

`make specificity-audit`, `make example-images-check` and
`make review-images-check` additionally require retained local image/response
bytes. The two image-panel checks cover the current and historical examples,
respectively. `make reference-quality-images-check`
verifies all 870 source hashes and re-extracts the 131 crop features. A documentation-only change needs link and
dependency checks, not a full Python test run.

Normal `make paper` builds reuse the committed example PDFs. Rebuilding the
current image panels with `make example-images` requires retained source pixels;
`make review-images-check` checks the separate historical full-frame panels.
To verify available local review evidence as well as portable records, run:

```bash
uv run --locked python scripts/audit_paper_reviews.py --local-snapshots
```

That optional audit reports missing local evidence as missing; the portable
mode does not require it. Neither mode performs a new editorial evaluation.

The current six-model experiment still needs a dedicated public release and a
permissible exact-pixel archive or verified recovery route. Recorded cumulative
paid image-generation accounting remains $112.293676 against the user's $120
ceiling. These are remaining limitations, not instructions to restart collection
or publish a release as part of routine maintenance.

## Preserve

All existing collectors and measurements are terminal. Replaying results does
not authorize restarting acquisition or adding images. Preserve original source
bindings, protocols, vectors, ledgers, failed attempts and numerical reports.
In particular, the diagnostic `analysis.json` binds its implementation, plan and
inputs; manuscript edits must not silently change those bytes.

Ignored `research_workspace/`, `artifacts/` and bound files under `tmp/` can hold
unique evidence. Preserve local configuration, secrets and the user's Korean
manuscript. In particular, frozen reviewed PDF/source snapshots under `tmp/paper/`
are unique historical evidence, not disposable build output. The final unscored
snapshot is under `tmp/paper/final-update/final-paper/`.

The committed editorial archive retains all 99 original reviews and six completed
external reviews. Large image-bearing CLI traces and machine-local runners are
narrowly ignored but remain intact locally; their hashes and retention boundaries
are in the [archive guide](../reports/paper_editorial_review_v1/ARCHIVE.md).
Two historical `.diff` files preserve required blank context-line spaces through
exact-path `.gitattributes` rules. Do not rewrite the original review opinions,
scores, receipts or archived patches during cleanup.

See [ARTIFACTS.md](ARTIFACTS.md) for the retention boundary and Git recovery of
retired documentation. Avoid broad cleanup of ignored directories.
