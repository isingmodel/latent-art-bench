# Project handover — 2026-09-23

Read [STATUS.md](STATUS.md) first: it holds the current findings, manuscript
states and the decisions waiting for the user. This page explains where to
work, how to check it, and what must not change. Inspect
`git status --short --branch` before editing; `main` is the only branch and
should stay that way unless the user says otherwise.

## Standing instructions

- Write documentation and the English manuscripts in English. The Korean
  translation is the user's work; preserve it.
- Keep all four painters in the main scientific scope.
- Do not add human evaluation. The full-length paper has no length limit; the
  ICML draft keeps eight main pages.
- Paid generation stays strictly below the $120 ceiling ($112.293676 recorded).
  The $350 family-control proposal is not approved. Collectors are terminal, and
  no live request may be made without explicit authorization; routine tests
  exclude the `live` marker.
- Work stopped at the ICML review target on 2026-09-21. Do not start a new review
  round, collection or manuscript revision without a new instruction.

## Where things are

| Component | Entry point |
| --- | --- |
| Six-model design and numerics | [painter_specificity_v2](../src/latent_art_bench/painter_specificity_v2/), [protocol](../studies/painter_specificity_v2/PROTOCOL.md) |
| Corrected reference reader and four replay views | [workflow.py](../src/latent_art_bench/painter_specificity_measurement_v1/workflow.py), [correction](../studies/painter_specificity_measurement_v1/CORRECTION.md) |
| Post-result diagnostics and source quality | `painter_specificity_review_v1.py`, `_v2.py`, `painter_reference_quality_v1.py` in [src/latent_art_bench/](../src/latent_art_bench/) |
| ICML-era retrospective analyses | Seven modules, plans and reports listed in the [analysis catalog](ANALYSES.md#icml-era-retrospective-analyses) |
| Prospective family controls (uncollected) | [package](../src/latent_art_bench/painter_family_controls_v1/), [plan](../studies/painter_family_controls_v1/PLAN.md), [preparation record](../reports/painter_family_controls_v1/README.md) |
| Manuscript sources and builders | [Paper guide](../paper/README.md) |
| Full-length editorial reviews | [Record](../reports/paper_editorial_review_v1/README.md), audited by [audit_paper_reviews.py](../scripts/audit_paper_reviews.py) |
| ICML scientific reviews | [Record](../reports/icml_review_v1/README.md); format and pixel checks in [scripts/](../scripts/) |

## Checks

Run from the repository root with the recorded Python 3.13.11 runtime and `uv`.
PDF builds need Tectonic. No target generates images.

```bash
make check                    # Ruff and the routine offline test suite
make evidence                 # Commit-bound audit of historical freezes and ledgers
make specificity-check        # Four primary numerical views
make review-check             # Post-result diagnostics and their tables
make reference-quality-check  # Source-region, scaler and label sensitivity
make figures-check            # Full-length figures and tables, without rewriting
make icml-evidence-check      # Direct naming, timing, learned, transfer, covariance
make icml-extensions-check    # SD-Turbo and selective attribution; needs local pixels
make icml-format-check        # ICML format of the build in tmp/paper/icml-build
make editorial-check          # Portable editorial-review record; no model calls
```

`make specificity-audit`, `make example-images-check`, `make review-images-check`,
`make reference-quality-images-check` and `make icml-artifact-check` also need the
retained local pixels and responses. A documentation-only change needs link checks,
not a test run. [Test scope](../tests/README.md) explains `make check` versus
`make check-all`.

## What must not change

Completed analyses bind files by path and SHA-256. Before editing or moving a
file outside the navigation documents, test whether it is bound:

```bash
git grep -l "$(shasum -a 256 path/to/file | cut -d' ' -f1)"
git grep -l "path/to/file"
```

Files that look editable but are bound:

- `pyproject.toml`, `uv.lock`, `pytest.ini` and `pytest-paper.ini`. Newer routine
  suites go in the Makefile's `ROUTINE_EXTRA` list, not in `pytest-paper.ini`.
- `docs/RESEARCH_IDEA_20260908.md`, `docs/reviews/20260907_methodology/` and
  `critics/assessment_v1/check_claims.py`.
- Protocols, plans, configurations, manifests, analysis JSON, reports and their
  source/tests under `studies/`, `configs/`, `data/manifests/`, `reports/`,
  `src/` and `tests/`. Corrections go in a new versioned namespace.
- Python scripts under `reports/` are frozen audit records. `make check` excludes
  them from lint rather than reformatting them.
- `paper/paper.tex`, its figures and `paper/paper.pdf` are bound by the editorial
  [final snapshot](../reports/paper_editorial_review_v1/final_update/FINAL_SNAPSHOT.json);
  `paper/icml*.tex`, the style files and the included figures are bound by the
  round-04 [inputs](../reports/icml_review_v1/round_04/inputs.json); the
  `paper/make_icml_*.py` builders by its
  [evidence manifest](../reports/icml_review_v1/round_04/evidence_manifest.json)
  and the numerical bundle's `discovery*.json` records. A new revision may edit
  them, but the result is a new unscored artifact. Never edit the frozen copies
  under `reports/`.

The root `README.md` also matches a hash in the numerical bundle's
`discovery*.json`, which lists what the already-built archive copied. The archive
keeps its own copy and no check reads the live file, so editing the README
breaks nothing; a new bundle would need a new discovery record in any case.
`LICENSE` is different: earlier release export manifests bind it.

Local-only material (`research_workspace/`, `artifacts/`, `output/` and bound
files under `tmp/`) is described in [ARTIFACTS.md](ARTIFACTS.md). Do not run
broad cleanup commands.

## Continuing a manuscript

**ICML draft.** `make paper-icml` rebuilds `output/pdf/latent_art_bench_icml.pdf`
and runs the format check. The reviewed PDF is also preserved locally at
`reports/icml_review_v1/round_04/input/manuscript.pdf`. The four corrections in
the [round-04 report](../reports/icml_review_v1/review_report_2026-09-21.md) are
the documented starting point for a revision. After editing, render and inspect
every page; the round-04 scores do not transfer to the new PDF.

**Full-length paper.** `make paper` rebuilds figures and `paper/paper.pdf`;
`make figures-check` verifies them without rewriting. Normal builds reuse the
committed example-image PDFs. Earlier editorial scores do not carry forward.

For a scientific correction, define a separate versioned result with explicit
inputs and compare it with the preserved original. A frozen result is not a
reason to leave a demonstrated measurement problem uninvestigated.
