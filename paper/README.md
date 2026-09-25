# Manuscripts

All three manuscripts share the title **Artist-Name Responses beyond a Shared
Painting Effect in Text-to-Image Generation**.

| Manuscript | Root file | Output | State |
| --- | --- | --- | --- |
| ICML-format draft | [icml.tex](icml.tex) | `output/pdf/latent_art_bench_icml.pdf` (local, not in Git) | Most recent. 8 main pages, 60 total, anonymous. Sources are identical to the round-04 reviewed input. |
| Full-length paper | [paper.tex](paper.tex) | [paper.pdf](paper.pdf) (committed) | 23 pages, final editorial update of 2026-09-15. Does not include the ICML-era retrospective analyses. |
| Korean translation | [latent_art_bench_korean.tex](latent_art_bench_korean.tex) | `output/pdf/latent_art_bench_korean.pdf` (local) | 26-page translation of the full-length paper at commit `f9e3935`; the user's work, preserved as written. |

The ICML draft uses the unaltered official ICML 2026 style as a provisional
format target. It is not a claim of submission to the past 2026 conference;
check the ICML 2027 instructions when they are published. Because the draft is
anonymous, do not commit its PDF to the public repository.

## Build and check

Run from the repository root with the recorded Python 3.13.11 environment.
Tectonic is the only TeX engine needed; it runs BibTeX and reruns automatically.

```bash
# ICML draft
make paper-icml             # Compile into tmp/paper/icml-build, format-check, copy to output/pdf/
make icml-format-check      # Page limit, US Letter size, embedded fonts, official style hashes
make icml-format-check ICML_BUILD=tmp/paper/icml-resume-build   # The round-04 reviewed build
make icml-evidence-check    # Direct naming, timing, learned, transfer and covariance analyses and tables
make icml-extensions-check  # SD-Turbo and selective-attribution analyses and tables; needs local pixels
make icml-artifact-check    # Local 1,878-image inventory and attribution records

# Full-length paper
make paper                  # Rebuild figures/tables and compile paper/paper.pdf
make figures-check          # Verify figures/tables without rewriting them
make example-images-check   # Optional: verify the 40 example-image sources and panels

# Korean translation (XeTeX through Tectonic, with kotex)
mkdir -p tmp/paper/korean-build && cd paper && tectonic --outdir ../tmp/paper/korean-build latent_art_bench_korean.tex
```

`make paper-icml` overwrites `output/pdf/latent_art_bench_icml.pdf`; the reviewed
copy is also preserved at `reports/icml_review_v1/round_04/input/manuscript.pdf`.
Until the next `make paper-icml`, the default build folder `tmp/paper/icml-build`
holds an older round-03 build, so a plain `make icml-format-check` fails on its
missing new labels; pass the reviewed build folder as shown above.
Rebuilt PDFs differ byte-for-byte from earlier builds, so recorded PDF hashes and
review scores apply only to the preserved files. After a substantive edit, render
and inspect every page; the format checker does not replace visual inspection.

Normal builds reuse the committed example-image PDFs. `make example-images`
rebuilds them from retained source pixels; the [presentation manifest](example_selection.json)
records the selection rule, work titles, public-domain metadata, crop boxes,
source hashes and all 36 exact prompts. `make review-images-check` verifies the
preserved preceding full-frame panels. Neither command acquires images or
extracts scientific features.

## ICML draft sources

| File | Role |
| --- | --- |
| `icml.tex` | Title, abstract, reproducibility and impact statements, appendix order |
| `icml_main.tex` | Eight-page main text |
| `icml_appendix.tex` | Features, estimators, post-result diagnostics, image provenance, model/painter summaries and supporting interventions |
| `icml_primary_context.tex` | Detailed primary comparisons, with the artist-pair figure |
| `icml_diagnostics_v3.tex`, `icml_extended_results.tex` | Direct naming diagnostics; magnitude and source-correction tables moved from the main text |
| `icml_learned_appendix.tex` | Same-image CLIP/CSD audit |
| `icml_transfer_appendix.tex`, `icml_covariance_appendix.tex` | Held-scene prompt-name task; fixed covariance scenarios |
| `icml_cross_cohort_appendix.tex`, `icml_selective_appendix.tex` | SD-Turbo collection; reference-calibrated abstention |
| `icml_reproducibility.tex` | Gateway configurations, collection timeline and exact replay commands |
| `icml_references.bib` | ICML-only citations, added to `references.bib` |
| `icml2026.sty`, `icml2026.bst`, `icml_style/PROVENANCE.json` | Official style files, hash-checked by `scripts/check_icml_format.py` |

Generated files: edit the builder, not the output.

| Builder | Writes |
| --- | --- |
| `make_icml_learned_tables.py` | `icml_learned_table.tex`, `icml_learned_results.tex` |
| `make_icml_learned_calibration_tables.py` | `icml_learned_calibration.tex` |
| `make_icml_transfer_tables.py` | `icml_transfer_table.tex`, `icml_transfer_results.tex` |
| `make_icml_covariance_tables.py` | `icml_covariance_results.tex` |
| `make_icml_cross_cohort_tables.py` | `icml_cross_cohort_results.tex` |
| `make_icml_selective_tables.py` | `icml_selective_table.tex`, `icml_selective_results.tex` |
| `make_icml_selective_figure.py` | `figures/icml_selective_coverage.pdf` |

## Full-length paper sources

| File | Role |
| --- | --- |
| `paper.tex` | Manuscript |
| `specificity_results.tex` | Results section |
| `specificity_estimator_details.tex` | Score identities and methods |
| `specificity_review_appendix.tex` | Diagnostic methods and image provenance |
| `references.bib` | Bibliography, shared with the ICML draft |

| Builder | Writes |
| --- | --- |
| `make_specificity_figures.py` | Six-model comparison, diagnostics, geometry and distribution figures |
| `make_specificity_tables.py` | `specificity_model_table.tex`, `specificity_shared_table.tex`, `specificity_supplement_tables.tex` |
| `make_review_figures.py` | Artist-pair figure, `specificity_review_table.tex`, `specificity_source_comparison.tex`, the alignment/component/review supplements and preserved image panels |
| `make_example_figures.py` | `specificity_original_generated.pdf`, `specificity_control_examples.pdf` |

`make_figures.py`, `replay_palette.py`, `make_validation_figure.py` and
`make_geometry_figure.py` rebuild figures from earlier manuscript versions.
Eighteen of the 24 committed figures are no longer included by either manuscript;
they remain because review provenance and release receipts bind their bytes. The
[analysis catalog](../docs/ANALYSES.md#manuscript-presentation) maps every
builder to its inputs.

## Review records

Scores are internal language-model assessments of exact PDF snapshots, not
human evaluation or scientific acceptance, and never transfer to a rebuilt PDF.

| Record | Manuscript | Outcome |
| --- | --- | --- |
| [ICML scientific review](../reports/icml_review_v1/README.md) | ICML draft | Rounds 1–3: 4, 4, 4. Round 4: **6, 6, 4** (mean 5.33) on the current sources, with four corrections listed in the [round-04 report](../reports/icml_review_v1/review_report_2026-09-21.md) |
| [Editorial review](../reports/paper_editorial_review_v1/README.md) | Full-length paper | Round 33 met the original goal (three fresh reviewers, mean 9.29; 99 reviews over 33 rounds); later paired external reviews scored 8.06–8.94; the [final update](../reports/paper_editorial_review_v1/final_update/README.md) is unscored |

Build intermediates and page previews belong under `tmp/paper/`. Keep the frozen
reviewed snapshots there and under `reports/`; see
[artifact retention](../docs/ARTIFACTS.md).
