# Project handover — 2026-10-01

Read [STATUS.md](STATUS.md) first: it holds the current findings, manuscript
states and the decisions waiting for the user. This page explains where to
work, how to check it, and what must not change. Inspect
`git status --short --branch` before editing; `main` is the only branch and
should stay that way unless the user says otherwise.

## Standing instructions

- Write documentation and the English manuscripts in English. The Korean translation of the TMLR manuscript (`paper/tmlr_ko/`) was
  made by an AI assistant at the user's request and follows the English sources; it was
  deleted and translated anew on 2026-10-04 (terms in `paper/tmlr_ko/GLOSSARY.md`).
- Keep all four painters in the main scientific scope. The second collection's two further
  groups (`painter_specificity_v3`) extend it; they do not replace it.
- Do not add human evaluation. The lead manuscript is the anonymous TMLR
  submission in `paper/tmlr/`; TMLR has no page limit, but keep the main text
  near 12 pages. The full-length paper and its Korean translation were deleted on
  2026-10-04 at the user's request; Git history keeps them (last in `a55a2b4`).
- Paid generation: $112.293676 was recorded before 2026-10-03; the user then approved the
  second collection (ceiling $200, raised to $220 during collection), which charged $72.93
  (about $185.22 in total; its accounting closes at $195.22 with two unreleased $5 holds).
  Both collectors are terminal. No further paid or live request is authorized; the $350
  family-control proposal is not approved. Routine tests exclude the `live` marker.
- On 2026-10-01 the user retargeted the paper from ICML to TMLR, retired the
  ICML draft and asked for subagent reviews with revision until the rubric in
  [reports/tmlr_review_v1](../reports/tmlr_review_v1/README.md) passes. Do not
  start a collection without a new instruction.
- On 2026-10-03 the user asked for a new review round of the revision for the second
  collection. It is recorded in [reports/tmlr_review_v2](../reports/tmlr_review_v2/README.md)
  (own rubric; rounds only at the user's request). Round 1 did not pass; its
  [triage](../reports/tmlr_review_v2/round_01/triage.md) lists the confirmed errors. On
  2026-10-04 the user approved the revision ("gogo"): diagnostics v7 (plan committed before it
  ran) and the text changes in the [revision record](../reports/tmlr_review_v2/round_01/revision.md).
  The revised manuscript is unreviewed; run a round 2 only when the user asks.

## Where things are

| Component | Entry point |
| --- | --- |
| Six-model design and numerics | [painter_specificity_v2](../src/latent_art_bench/painter_specificity_v2/), [protocol](../studies/painter_specificity_v2/PROTOCOL.md) |
| Second collection (two further painter groups) | [painter_specificity_v3](../src/latent_art_bench/painter_specificity_v3/), [references](../studies/painter_specificity_v3/REFERENCES.md), [protocol](../studies/painter_specificity_v3/PROTOCOL.md), records in `data/manifests/painter_specificity_v3/` |
| Corrected reference reader and four replay views | [workflow.py](../src/latent_art_bench/painter_specificity_measurement_v1/workflow.py), [correction](../studies/painter_specificity_measurement_v1/CORRECTION.md) |
| Post-result diagnostics and source quality | `painter_specificity_review_v1.py`, `_v2.py`, `painter_reference_quality_v1.py` in [src/latent_art_bench/](../src/latent_art_bench/) |
| Retrospective analyses | Seven modules, plans and reports listed in the [analysis catalog](ANALYSES.md#retrospective-analyses) |
| Prospective family controls (uncollected) | [package](../src/latent_art_bench/painter_family_controls_v1/), [plan](../studies/painter_family_controls_v1/PLAN.md), [preparation record](../reports/painter_family_controls_v1/README.md) |
| Manuscript sources and builds | [Paper guide](../paper/README.md) |
| Full-length editorial reviews | [Record](../reports/paper_editorial_review_v1/README.md), audited by [audit_paper_reviews.py](../scripts/audit_paper_reviews.py) |
| TMLR reviews | [First record](../reports/tmlr_review_v1/README.md), [second series](../reports/tmlr_review_v2/README.md) |
| ICML scientific reviews (retired draft) | [Record](../reports/icml_review_v1/README.md), including the draft's exact sources in `round_04/input/`; pixel-inventory check in [scripts/](../scripts/) |

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
make retrospective-check      # Direct naming, timing, learned, transfer, covariance
make extensions-check         # SD-Turbo and selective attribution; needs local pixels
make tmlr-check               # TMLR tables, figure, quoted numbers and style hashes
make editorial-check          # Portable editorial-review record; no model calls
```

`make specificity-audit`, `make example-images-check`, `make review-images-check`,
`make reference-quality-images-check` and `make artifact-check` also need the
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
- `paper/replay_palette.py` and `paper/figures/palette_blocks.pdf` must stay at
  these paths: hash-bound routine tests read them.
- The full-length manuscripts that the editorial
  [final snapshot](../reports/paper_editorial_review_v1/final_update/FINAL_SNAPSHOT.json)
  records were deleted from `paper/archive/` on 2026-10-04; their bytes remain in Git
  history. The retired ICML draft's sources are
  frozen copies in `reports/icml_review_v1/round_04/input/`. Records under
  `reports/` still name the removed presentation builders and tables; Git history
  and `generative_art_diff_archive/2026-10-01/` hold them. Never edit the frozen
  copies under `reports/`.

The root `README.md` also matches a hash in the numerical bundle's
`discovery*.json`, which lists what the already-built archive copied. The archive
keeps its own copy and no check reads the live file, so editing the README
breaks nothing; a new bundle would need a new discovery record in any case.
`LICENSE` is different: earlier release export manifests bind it.

Local-only material (`research_workspace/`, `artifacts/`, `output/` and bound
files under `tmp/`) is described in [ARTIFACTS.md](ARTIFACTS.md). Do not run
broad cleanup commands.

## Continuing a manuscript

**TMLR submission.** `make paper-tmlr` checks the generated assets and every
quoted number, then builds `output/pdf/latent_art_bench_tmlr.pdf`. Numbers in the
prose must match `paper/tmlr/claims.json`, which `build_assets.py` recomputes from
the analyses. After editing, render and inspect every page. Review scores apply
only to the PDF hash they record.

**Korean translation of the TMLR manuscript.** `make paper-tmlr-ko` builds
`output/pdf/latent_art_bench_tmlr_korean.pdf` from `paper/tmlr_ko/`. After editing the
English text, edit the same passage in Korean; `make tmlr-ko-check` fails when a
number differs between the two languages or a Korean table is out of date
(`make tmlr-ko-assets` regenerates the tables).

**Retired ICML draft.** Its exact sources, the reviewed PDF and the four open
corrections are in [reports/icml_review_v1](../reports/icml_review_v1/README.md);
the TMLR manuscript applies the substance of those corrections.

**Full-length paper and Korean translation.** Deleted on 2026-10-04 at the user's
request, together with the `paper-archive` target; Git history keeps them (last in
`a55a2b4`). Their presentation builders were retired earlier, so a new revision
would start from the TMLR manuscript instead.

For a scientific correction, define a separate versioned result with explicit
inputs and compare it with the preserved original. A frozen result is not a
reason to leave a demonstrated measurement problem uninvestigated.
