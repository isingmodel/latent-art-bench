# Painter naming and the distribution of generated art

This is the current 11-page English research manuscript. `paper.tex` is a complete,
single-file rewrite organized around the scientific question, study design,
results and interpretation. It replaces the previous manuscript at the same
path; earlier writing remains in Git history. The previous controlled-study
paper in `../painter_distribution_study_v1/` remains historical.

The manuscript analyzes 1,006 generated images and 70 painting reproductions,
using a scaler fitted on 221 separate development works. Its central distinction
is between proximity to the original-painting distribution, aggregate generated
variation, and variation within versus between scene descriptions. The original
eight conditional randomization tests are unchanged. Later diagnostics remain
explicitly descriptive.

The paper contains three compact vector figures. Their builder reads saved
endpoints and PCA coordinates from hash-checked published tables; it fits no
projection and computes no new statistics. Operational history, budgets,
verification logs and planned recruitment details are outside the scientific
manuscript. The underlying scientific protocols, results and published report
figures have not changed.

## Scientific evidence

- [Controlled study report](../../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md)
- [Descriptive diagnostic report and complete tables](../../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md)
- [Original methodology review and revision plan](../../docs/reviews/20260907_methodology/REVIEW_AND_REVISION_PLAN.md)
- [Fixed diagnostic protocol](../../studies/painter_distribution_revision_v1/PROTOCOL.md)
- [Reference and human-validation plan](../../studies/painter_distribution_revision_v1/VALIDATION_PLAN.md)
- [Literature comparison](../../studies/painter_distribution_revision_v1/LITERATURE_MATRIX.md)
- [Manuscript review and responses](REVIEW.md)

Human judgments, independent reference/capture replication and learned-feature
validation have not been performed. The paper reports a finite-feature case
study, not perceptual validation or a model leaderboard.

## Reproduce the paper

From the repository root:

```bash
uv sync --locked --extra analysis --extra dev --inexact
uv run --locked python papers/painter_distribution_revision_v1/make_figures.py --check
```

To regenerate the manuscript-only figures, omit `--check`. This writes only the
three PDFs under this manuscript's `figures/` directory. Temporary PNG previews
can be requested with `--preview-dir tmp/pdfs/paper-rewrite-20260907`.

From this manuscript directory:

```bash
mkdir -p ../../tmp/paper-build-rewrite
tectonic --outdir ../../tmp/paper-build-rewrite paper.tex
cp ../../tmp/paper-build-rewrite/paper.pdf paper.pdf
pdfinfo paper.pdf
mkdir -p ../../tmp/pdfs/paper-rewrite-20260907
pdftoppm -r 100 -png paper.pdf ../../tmp/pdfs/paper-rewrite-20260907/page
```

Inspect the rendered pages after editing. The build uses Tectonic, the local
bibliography and the three manuscript figure PDFs.

## Reproduce the underlying analyses

From the repository root:

```bash
uv run --locked python -m latent_art_bench.painter_distribution_revision_v1.analysis check
uv run --locked python -m latent_art_bench.painter_distribution_revision_v1.report_publication check
uv run --locked ruff check .
uv run --locked pytest -q -m 'not live'
uv run --locked latent-art-bench verify-evidence
```

The two revision commands verify the numerical results and all 44 published
report files separately from the historical evidence audit. These checks use
retained vectors and metadata without provider calls or image access. Raw image
bytes would be required for re-extraction; service regeneration is not bitwise
reproduction. Do not rerun terminal collectors or report publication commands.
Scientific source/input commit `f7666ae`, numeric freeze `c505512`, renderer
commit `1d635a5` and their receipts remain the record of the completed analysis.
