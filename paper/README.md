# Manuscripts

```
paper/
  tmlr/                          lead manuscript: anonymous TMLR submission
    main.tex, appendix.tex, references.bib
    tmlr.sty, tmlr.bst, fancyhdr.sty, STYLE_PROVENANCE.json   official, unmodified
    build_assets.py              builds generated/ and checks every quoted number
    claims.json                  numbers quoted in the prose (checked)
    generated/                   tables and the component figure (do not edit)
    figures/                     two static figures, the example-image manifest
                                 and PROVENANCE.json
  tmlr_ko/                       Korean translation of the TMLR manuscript
    main.tex, appendix.tex       Korean prose; figures and bibliography come from tmlr/
    tables_ko.json               Korean captions, headers and row labels of the tables
    GLOSSARY.md                  style rules and terms of the translation
    build_korean.py              builds generated/ from tmlr/generated and checks that
                                 the Korean text has the same numbers as the English
    generated/                   Korean tables (do not edit)
  replay_palette.py              kept here: hash-bound routine tests read these
  figures/palette_blocks.pdf     two paths directly
```

| Manuscript | Source | State |
| --- | --- | --- |
| **TMLR submission** | [tmlr/main.tex](tmlr/main.tex) | Lead manuscript. *Proximity Is Not Specificity: What Painter Names Add in Text-to-Image Generation.* Revised on 2026-10-03 for the second collection (two further painter groups) and on 2026-10-04 after review round 1 of the second series. Built locally to `output/pdf/latent_art_bench_tmlr.pdf`; review records in [reports/tmlr_review_v1](../reports/tmlr_review_v1/README.md) and [reports/tmlr_review_v2](../reports/tmlr_review_v2/README.md) |
| Korean translation of the TMLR manuscript | [tmlr_ko/main.tex](tmlr_ko/main.tex) | Translation of the current TMLR sources by an AI assistant, made anew on 2026-10-04 after the user had the earlier translation (2026-10-01) deleted; not yet reviewed by the author. Style and terms in [tmlr_ko/GLOSSARY.md](tmlr_ko/GLOSSARY.md). Same numbers, tables and figures; labels inside figures and the prompt texts stay in English. Built locally to `output/pdf/latent_art_bench_tmlr_korean.pdf` |
| Full-length paper and its Korean translation | Deleted on 2026-10-04 | The 23-page version of 2026-09-15 and the user's 26-page translation were deleted at the user's request; Git history keeps them (last in commit `a55a2b4`) |
| ICML-format draft | [reports/icml_review_v1/round_04/input/](../reports/icml_review_v1/round_04/input/) | Retired on 2026-10-01; exact sources kept only in its review record |

Keep the TMLR manuscript anonymous (`\usepackage{tmlr}`) until acceptance; use
`[preprint]` for an arXiv version and `[accepted]` for the camera-ready version.
Do not commit its PDF.

## Build and check

Run from the repository root with the recorded Python 3.13.11 environment.
Tectonic is the only TeX engine needed; it runs BibTeX and reruns automatically.

```bash
make tmlr-check     # Input hashes, generated files, quoted numbers in context, style and figure hashes
make paper-tmlr     # tmlr-check, then compile into tmp/paper/tmlr-build and copy to output/pdf/
make tmlr-assets    # Regenerate tmlr/generated/ after changing build_assets.py
make paper-tmlr-ko  # Check and compile the Korean translation into tmp/paper/tmlr-ko-build and output/pdf/
make tmlr-ko-assets # Regenerate tmlr_ko/generated/ after the English tables or tables_ko.json change
```

`build_assets.py` reads only completed analysis outputs, each checked against a
recorded SHA-256, and writes nothing in `--check` mode. When you change a number
in the prose, update `claims.json` (it must equal the recomputed value) or
`make tmlr-check` fails; add a claim for every new quoted number. After a
substantive edit, render and inspect every page.

The Korean translation follows the English sources by hand: after editing
`tmlr/main.tex` or `tmlr/appendix.tex`, edit the same passage in `tmlr_ko/`, using the terms of `tmlr_ko/GLOSSARY.md`.
`make tmlr-ko-check` then fails if a number differs between the two languages
(numbers that one language writes as a word are listed in `EXPECTED` in
`build_korean.py`) or if a Korean table is out of date. It uses the macOS fonts
Nanum Myeongjo and Apple SD Gothic Neo when present and falls back to the kotex
defaults otherwise.

## TMLR evidence

| Manuscript part | Analysis |
| --- | --- |
| Shared vs. between-name change (Table 1, Figure 2) | [direct naming](../reports/painter_specificity_review_v3/report.md); reference spread $H$ from [diagnostics](../reports/painter_specificity_review_v1/REPORT.md) |
| Agreement with reference differences (Table 2, Appendix D) | [primary analysis](../reports/painter_specificity_v2/psv2-20260911/REPORT.md), [diagnostics](../reports/painter_specificity_review_v1/REPORT.md) |
| Learned embeddings and readouts (Tables 3–4) | [learned audit](../reports/painter_learned_audit_v1/REPORT.md) |
| Held-scene recognition (Appendix F) | [transfer](../reports/painter_prototype_transfer_v1/REPORT.md) |
| SD-Turbo collection (Table 5) | [cross-cohort](../reports/painter_cross_cohort_v1/REPORT.md) |
| Sensitivities and repeat dependence (Appendices A, D) | [source quality](../reports/painter_reference_quality_v1/REPORT.md), [repeat covariance](../reports/painter_repeat_covariance_v1/REPORT.md) |
| Figure 2 (example images) | [figures/example_selection.json](tmlr/figures/example_selection.json) |

The selective-attribution (abstention) analysis is not used by the TMLR
manuscript; its record stays in
[reports/painter_selective_attribution_v1](../reports/painter_selective_attribution_v1/REPORT.md).

## What was removed on 2026-10-01

The ICML style files and draft sources, the full-length paper's presentation
builders (`make_specificity_*`, `make_review_figures`, `make_example_figures`,
`make_figures`, `make_validation_figure`, `make_geometry_figure`), the
retrospective-table builders (`make_icml_*`) with their nine generated tables,
and 18 figures that neither the TMLR manuscript nor the then-archived papers used. Numerical results are unaffected:
they live in `reports/` and are replayed by `make retrospective-check`,
`make extensions-check`, `make review-check` and the other analysis targets.
A complete copy of the previous `paper/` folder, with a SHA-256 inventory, is in
the sibling folder `generative_art_diff_archive/2026-10-01/`, and Git history
holds every tracked file. [Artifact retention](../docs/ARTIFACTS.md) records
the change and the before/after check run.

## Review records

Recommendations are internal language-model assessments of exact PDF snapshots,
not human evaluation or journal decisions, and never transfer to a rebuilt PDF.

| Record | Manuscript |
| --- | --- |
| [TMLR review](../reports/tmlr_review_v1/README.md) | TMLR submission |
| [TMLR review, second series](../reports/tmlr_review_v2/README.md) | TMLR submission after the second collection |
| [ICML scientific review](../reports/icml_review_v1/README.md) | Retired ICML draft |
| [Editorial review](../reports/paper_editorial_review_v1/README.md) | Full-length paper |
