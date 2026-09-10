# Agent handover — substantive geometry and paper revision

Read [STATUS.md](STATUS.md), then [ARTIFACTS.md](ARTIFACTS.md), inspect
`git status --short --branch`, and follow [AGENTS.md](../AGENTS.md). This document
is mutable orientation, not permission to reopen a terminal research stage.
The canonical English source is [paper/paper.tex](../paper/paper.tex); the
[paper guide](../paper/README.md) owns building and visual inspection.

## Current scope

The active user goal requests three skeptical reviews using the linked academic
review skill, substantive paper/analysis revisions and an unchanged nine-score
average above 9. Fresh baseline is 8.2333/10. Round 2 reviews currently assess
the 34-page, nine-figure manuscript (TeX `8973d78c…`, PDF `ca291f0e…`).
Do not alter recorded reviewer scores or claim completion before the actual
mean exceeds the target. All reviewers are maintainer-run LLMs; Reviewers 1/2
helped implement the new statistical primitives after their baseline reviews,
and Reviewer 3 supplied literature/structure advice.

Two new terminal retained-vector analyses now supplement the preceding work:

| Namespace / run | Source / freeze | Main result and boundary |
| --- | --- | --- |
| `painter_naming_geometry_v1` / `pngv1-20260910` | `459c6a8` / `8facfa3` | Four-fold whole-scene maps, fixed original-map temporal transfer, noise-corrected variance and conditional-mean residuals. Actual naming beats shift/scale in all six primary fold means, but not all folds; pure shift beats actual in both later primary FLUX comparisons, with documented sensitivity exceptions. |
| `painter_naming_centering_v1` / `pncv1-20260910` | `c390eef` / `45e3ce9` | Evaluation-free centering isolates the old scalar at the same weighted mean. It worsens energy in all 60 original fold means and 18 later views. It is a post-result cohort adaptation, not unchanged pointwise transfer. |

Both use the existing 31 coordinates/subsets and generated vectors. No new
images, feature extraction, API requests or spending occurred. Both have exact
numerical replay; the centering runner also verifies the full predecessor result.
Do not apply the independent-repeat conditional correction to the new centered
map: its evaluation-free mean induces dependence across residual repetitions.
All original/replication primary tests and the four-painter analysis remain
unchanged. Use `make geometry-check` for these two new namespaces.

The preceding user request covered implementation of the measurement-validation, replication and
public-reproducibility requirements identified by the previous three LLM reviews,
followed by a substantive paper update. The no-human-rating preference and $75
cumulative OpenRouter ceiling remain in effect. The work uses three new namespaces
and does not alter earlier studies or qualify canonical Protocol 2.1's broader
reproduction gates. Current operational state is in [STATUS.md](STATUS.md).

| Namespace | Purpose and boundary |
| --- | --- |
| `painter_measurement_validation_v1` | Ten controlled transformations of all 70 Study 1 references plus common-square extraction for all 1,006 generated images. Same extractor/scaler. Computational response characterization, not perceptual or independent-capture validation. |
| `painter_naming_replication_v1` | A separate 264-slot collection: 72 FLUX naming and 192 OAuth palette outputs. Original templates and exposed references; new four-endpoint inference. Same maintainer, without independent investigators or verified backend-state independence. |
| `paper_reproducibility_v1` | Compact core/extension exports, unchanged scientific computation, direct report bridges and a history-free public archive. Numeric replay is separate from absent raw-media verification. |

The measurement source/freeze/results commits are `f3bc9b6`, `f2ab8de` and
`994d247`. The replication source/freeze commits are `88cd185` and `2de6bc4`.
All source/input bindings were committed before the corresponding new measurement or
generation stage. Completed run outputs are create-once and cannot be refreshed.

The original paper retains all four painters: Monet, Sisley, Pissarro and Cézanne.
The exploration uses 649 references, 1,536 named images and 384 artist-free controls.
Study 1 separately uses 1,006 generated images and 70 Monet/Cézanne references;
Study 2 uses a separate 192-image primary palette run. The 221-work development
scaler is unchanged. The 49-image earlier palette cohort remains ancillary; two
late exploratory retries do not restore the original incomplete-grid primary.
Never pool these cohorts to change an inferential result or denominator.

## Analysis and paper entry points

[ANALYSES.md](ANALYSES.md) maps every study's inputs, numerical computation and
plotting code. [ARCHITECTURE.md](ARCHITECTURE.md) describes shared primitives and
storage. Main offline commands:

```bash
make four-painter-analysis
make analysis
make palette-check
make validation-check
make replication-check
make geometry-check
make figures-check
make paper
```

`make replication-check` requires its terminal measurement receipt. These targets
do not generate images. The complete older response-bound replay is
`make computational-responsiveness`; it needs retained private responses.
Eight preceding manuscript figures come from `paper/make_figures.py` (six),
`paper/replay_palette.py` (one) and `paper/make_validation_figure.py` (one).
The last uses the frozen measurement renderer. The ninth figure is generated by
`painter_naming_geometry_v1/report.py` and copied from its immutable report by
`make figures`; `make figures-check` compares the manuscript copy. The original frozen geometry
report calls its last two comparisons “named − generic”; their scientific
meaning is detailed minus short-scene **named** prompts. The current manuscript
and review table label them correctly without overwriting the retained figure.

The [measurement review](reviews/20260910_validation_followup/RESULTS_REVIEW.md)
records the full matrix and its limits: large texture sensitivity to resampling,
overlap among feature-family responses, and different crop fractions across
references and services. Square sensitivities preserve the eight signs/four
rejections, but no square-domain classifier was recomputed. Derivative vectors
are repeated measurements of the same works, not additional independent samples.

Temporal naming uses 24 outputs per arm and shared free controls, whereas the
original FLUX comparison used 72 per painter/arm. Changed counts and dependence
preclude treating old/new V-energy magnitude differences as an isolated time
effect. Preserve the new four-test Holm family and 98.75% marginal palette
intervals. Negative unresolved and significant directional replication are
separate conclusions. Missing measurements or a duration violation withhold
specified primary inference; later outputs cannot repair that grid.

## Public release

The project remote is <https://github.com/isingmodel/latent-art-bench>.
The published tag is `pprv1-20260910` on sanitized branch
`codex/paper-reproducibility-v1` (commit `2592dfb`), with `pprv1-20260910.tar.gz`.
The [release verification report](../reports/paper_reproducibility_v1/pprv1-20260910/REPORT.md)
records 98 exact local/anonymous checks and 98 portable hosted checks. The source
builder is `tools/paper_release.py`; its
[guide](../studies/paper_reproducibility_v1/README.md) specifies export/build/check.

The builder copies an explicit allowlist and requires copied original inputs to
match the final local source commit. Do not push the full local history as a
shortcut. The manifest distinguishes original input-export provenance, final
local build commit and the different public history-free commit. A build-time
prepared status does not prove publication. The actual archive hash, anonymous-download replay and hosted CI are recorded
separately in `PUBLICATION_VERIFICATION.json` beside the report.

The preceding paper remains in additive `paper-r1.pdf` / `paper-r1.tex`
assets; the current substantive manuscript differs from those published files. An explicit erratum corrects the blanket exact-p-value statement after
the portable Welch comparison amendment, plus one verb agreement. Preserve the
original released archive and paper asset; do not silently replace either.
The standalone palette replay remains exact; the portable release adapter passes
its reviewed comparison callback and records that check with the palette figure.

Exports contain fixed vectors, scalers, memberships, seeds, request identities,
recorded source URLs/licenses and numeric reports. They exclude raw pixels,
responses, local credentials, model weights, literature full text and user drafts.
Code/numerical licensing grants no rights to absent artwork. Python audit-hook
guards record observed network/process/file attempts during replay; they are not
an operating-system security sandbox. The actual reproduced scope is recorded
in `COVERAGE.json`, rather than inferred from the presence of report files.

## New addendum packaging

`tools/paper_geometry_release.py` builds a local history-free addendum containing
only both new namespaces, their transitive frozen numerical inputs, and the
English paper with nine approved figure PDFs. It never publishes. Final mode
requires every copied file to be clean at HEAD and bound inputs to agree with
their recorded source commits. `--draft` skips only Git checks for local QA.
Never replace the old public archive or push the full local history.

The first draft was extracted into a clean directory and both analyses replayed
exactly with a fresh Python 3.13.11 environment. Its optional combined pytest
command initially collided on duplicate `test_analysis.py` basenames; the
packager README now specifies `--import-mode=importlib`, and all 95 scientific
tests pass with that flag. Use a new create-once output directory after changes.
Package inventory verification runs before dependency installation, because a
new `.venv` is intentionally outside the sealed payload inventory. Final public
publication and current review outcome belong in STATUS and the release receipt.

## Verification and preservation

Before handoff after Python changes, run:

```bash
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
uv run --locked latent-art-bench verify-evidence
make validation-check
make replication-check
make geometry-check
make figures-check
git diff --check
```

`pytest.ini` uses importlib collection plus two legacy helper-import paths so
versioned studies can reuse test filenames. The old `pyproject.toml` is a frozen
input and remains unchanged. Historical evidence verification does not cover all
new namespaces, so their own numerical/response checks are also necessary.
Do not repeat extraction merely to verify a paper edit. Build the PDF and render
all pages for final visual QA, following the paper guide.

Never rewrite, move or delete frozen protocols, sources, tests, reports, ledgers
or hash-bound inputs. Never refresh hashes or extend the two historical evidence
acknowledgements. Ignored `research_workspace/`, `artifacts/` and `tmp/pdfs/` may
contain unique evidence. No broad recursive cleanup or `git clean -xfd`.
A terminal census or collector remains permanently closed.

`paper/paper_ko.tex` and ignored `paper/paper_ko.pdf` are user-owned. Do not modify,
stage or publish either. Historical integration and reviews are linked in
[INDEX.md](INDEX.md); their scores describe their own manuscript hashes.
The [preceding review record](reviews/20260910_validation_followup/REVIEW.md) gives
a nine-score mean of 8.4111/10 for r1. The active substantive cycle has separate
reports under `docs/reviews/20260910_substantive_revision/`; its baseline is
8.2333/10 and its latest completed round must be read before reporting a score. Every
review here is maintainer-run LLM work, not independent human peer review
or a prediction of publication acceptance. Current paper claims must follow the
actual results, including unresolved or contrary findings.


## Active prospective clause validation

Current user goal remains active: honest unchanged nine-score mean >9. Latest
complete round is **8.6889**; no later score is assigned. Geometry/centering are
sealed and publicly reproduced at `ppgv1-20260910`, source `5485e36`, public
commit `7923049`, SHA256 `4a26b9c3…ce5a9b30`. Their 34-page paper is published;
never replace the archived manuscript or numerical bytes.

`painter_clause_validation_v1` is a newly versioned study under qualification.
It specifies 288 OAuth outputs, 24 new fixed scenes x3 repeats x4 clauses, no
paid calls. R1 wrote precision/source/tests (committed `6dd1e80`, qualified
synthetic results), R2 wrote collection/workflow/tests, R3 wrote protocol/scenes
and reviews root analysis. Root owns common/analysis/CLI/tests. Reviews disclose
these roles. Identity failure after a non-identity stop is being checked for
terminal replay; all must-fix findings must close before source/qualification
commit, preparation, freeze commit and explicit live collection. No new scene
images have been generated or measured. Preserve the fixed historical OAuth
maps and the pair-specific primary completeness rules.
