# Research paper

## ICML review draft

[icml.tex](icml.tex) builds a separate anonymous English manuscript using the
unaltered official ICML 2026 style. Its main body is 8 pages; references and
the complete methodological appendix follow in the same PDF. This is a format
target for a future submission, not a claim of submission to the past 2026
conference. ICML 2027 instructions must be checked when published.

```bash
make paper-icml           # Build output/pdf/latent_art_bench_icml.pdf
make icml-format-check   # Check the existing build, page limit and font embedding
make icml-evidence-check # Replay the versioned scientific additions from retained vectors
make icml-artifact-check # Verify the local 1,878-image inventory and attribution records
```

The main text is in `icml_main.tex`; `icml_appendix.tex` preserves the supporting
analyses and `icml_reproducibility.tex` records exact gateway configurations,
the UTC collection timeline and replay boundaries. `icml_diagnostics_v3.tex`
adds direct incremental naming and influence diagnostics, while
`icml_learned_appendix.tex` documents the same-image CLIP/CSD audit.
`make_icml_learned_tables.py` generates its main comparison and complete
source-view/reference-target appendix tables, with exact replay through
`make icml-evidence-check`. `icml_transfer_appendix.tex` and the tables produced
by `make_icml_transfer_tables.py` report the subsequent retrospective held-scene
prompt-name task, including its adverse results and supervised context rule.
`icml_extended_results.tex` preserves magnitude and source-correction tables
moved out of the main text. `icml_covariance_appendix.tex` and the generated
`icml_covariance_results.tex` report fixed cross-repeat covariance scenarios
for all six primary-D curves and all 15 point-order comparisons; the scenarios
do not estimate actual covariance or repair uncertainty intervals. Additional
ICML-only citations are in `icml_references.bib`; the original bibliography is
preserved. Main-text tables and figures
count toward the eight-page check. The layout checker verifies every page's US
Letter size, embedded fonts, references and the official style-file hashes;
rendered-page inspection remains a separate step.

The [ICLR-style review record](../reports/icml_review_v1/README.md) uses independent
scientific recommendations on a fixed scale. It is separate from the historical
editorial assessments below. Round 04 has overall recommendations 6, 6, 4
(mean 5.333333333333333) on the exact 8-main-page, 60-total-page PDF. The
[review report](../reports/icml_review_v1/review_report_2026-09-21.md) preserves
all reviews and lists remaining scientific limits and editorial corrections in
that scored version. Prior round-03 recommendations remain 4, 4, 4. The
[portable numerical artifact](../reports/icml_review_v1/numeric_bundle_v1/README.md)
replays 16 fixed checks from an extracted copy and preserves that reviewed PDF.
It does not include exact pixels or replace independent empirical validation.
Original English and Korean sources are preserved.

The latest revision adds `icml_cross_cohort_appendix.tex` and its generated
results for the retained 2,000-image SD-Turbo collection, plus
`icml_selective_appendix.tex`, complete generated selective tables and the
primary painter-coverage heatmap. Both retrospective studies were frozen and
independently audited before their new outcomes; they add no newly collected
images. Their exact execution/replay commands, including external input and
audit digests, are documented in `icml_reproducibility.tex`. The legacy
`icml-evidence-check` target above covers its original analyses; additionally
check the new bound tables with:

```bash
uv run --locked python paper/make_icml_cross_cohort_tables.py --check
uv run --locked python paper/make_icml_selective_tables.py --check
```

The frozen review snapshot lives in `reports/icml_review_v1/round_04/input/`.
Rebuilding after any manuscript change produces a different artifact that must
not inherit this exact-PDF review claim automatically.

## Full-length English manuscript

[paper.tex](paper.tex) is the canonical English source and [paper.pdf](paper.pdf)
is the revised 23-page paper, **Artist-Name Responses beyond a Shared Painting
Effect in Text-to-Image Generation**. All four painters and the declared
six-model comparisons remain. The added diagnostics distinguish response
magnitude, artist-pair alignment and agreement with the measured reference target.

The additions are explicitly post-result and preserve the original numerical
records. [Initial diagnostics](../reports/painter_specificity_review_v1/REPORT.md)
are supplemented by [noise and stability checks](../reports/painter_specificity_review_v2/REPORT.md)
and an [assistant audit of all 870 reference/development sources](../reports/painter_reference_quality_v1/REPORT.md).
Source correction retains FLUX's lowest error point estimate but removes its
adjusted separation from Sunburst. No human evaluation was added; feature
agreement is not presented as validated artistic fidelity.

## Build and verification

Run from the repository root with the recorded Python 3.13.11 environment:

```bash
make paper               # Rebuild numerical figures/tables and compile the PDF
make figures-check       # Verify figure/table replay
make editorial-check     # Audit archived review hashes and score arithmetic
make specificity-check   # Replay the four declared numerical views
make review-check        # Replay both versions of post-result diagnostics
make reference-quality-check  # Replay source-region/scaler/label sensitivity
make reference-quality-images-check  # Verify all raw hashes and 131 crop features
```

The main-text comparison places four original painting reproductions above the
24 named-painter outputs from all six models, with the 12 artist-free/generic
controls in the same model rows. All conditions use the same first scene and repeat. All 36
generated examples come from the completed experiment; no new images were generated.

Normal builds reuse the committed example PDFs. With retained source pixels:

```bash
make example-images        # Rebuild the current comparison and control panels
make example-images-check  # Verify all 40 source hashes and exact panel replay
```

The [presentation manifest](example_selection.json) records the selection rule,
original work titles, public-domain metadata, crop boxes, source hashes and all
36 exact prompts. References are selected by work ID from the completed audit's
water class; they are comparison examples, not generator inputs or matched scenes.
Full-resolution sources remain outside the compact repository.

The preceding full-frame example panels and their
[inspection manifest](../reports/painter_specificity_review_v1/inspection.json)
remain preserved; `make review-images-check` verifies that historical presentation.
Neither panel command acquires images or extracts scientific features.

## Source organization

- `paper.tex` and `specificity_results.tex`: manuscript and results.
- `specificity_estimator_details.tex`: additional score identities and methods.
- `specificity_review_appendix.tex`: diagnostic methods and image provenance.
- `specificity_alignment_supplement.tex`: squared magnitude and directional alignment.
- `specificity_component_supplement.tex`: reference-component and artist-omission
  results, placed after their definitions.
- `specificity_shared_table.tex`: scene-averaged shared and painter-specific
  shares of repeat-corrected squared change, plus retrospective shared/generic
  directional agreement and squared-size ratios, from retained analysis records.
- `specificity_source_comparison.tex`: original versus source-corrected model
  differences and adjusted intervals from the frozen analysis records.
- `make_specificity_figures.py` and `make_specificity_tables.py`: primary-result
  presentation; their generated files are included by the paper.
- `make_review_figures.py`: diagnostic tables, artist-pair plot and preserved old panels.
- `make_example_figures.py`: current original/generated comparison and control panels.
- [Initial diagnostics](../src/latent_art_bench/painter_specificity_review_v1.py),
  [follow-up checks](../src/latent_art_bench/painter_specificity_review_v2.py) and
  [source-quality sensitivity](../src/latent_art_bench/painter_reference_quality_v1.py):
  separately bound analyses with exact replay.
- `references.bib`: bibliography. Earlier figure builders remain available for
  supporting evidence; the [analysis catalog](../docs/ANALYSES.md) maps their inputs.

Build intermediates and page previews belong under `tmp/paper/`. Historical
analysis records and source images remain intact.

The [editorial review record](../reports/paper_editorial_review_v1/README.md)
contains the fixed reader-experience rubric and independent review rounds.

The original editorial stopping criterion was met in round 33, with three fresh
reviewers' mean of 9.2916666667/10. That evaluated snapshot is preserved unchanged.
The subsequent [revision and paired-review record](../reports/paper_editorial_review_v1/paired_review_03/README.md)
distinguishes the original independent reviews `_01`, cancelled requests `_02`,
and fresh `_03` reviews of a first revision (Claude 8.0625; Astra xhigh 8.8125).
Those reviews informed a second revision, assessed in the
[evaluation-only round `_04`](../reports/paper_editorial_review_v1/paired_review_04/README.md):
Claude Opus 5 **8.0625**, Astra xhigh **8.8125**, mean **8.4375**.
These are internal AI editorial assessments, not human evaluation or scientific acceptance.

The canonical manuscript now includes the user's
[final update](../reports/paper_editorial_review_v1/final_update/README.md)
after `_04`. It clarifies the three error criteria, identifies calibration's
measured contrasts, tabulates shared/generic comparisons and improves source
and model-provenance pointers. The user lifted the manuscript length limit;
the abstract remains 151 words. No new independent score is assigned to this
last revision. Earlier reviewed snapshots and raw assessments remain intact.
The [archive guide](../reports/paper_editorial_review_v1/ARCHIVE.md) explains
portable verification and local execution evidence.
