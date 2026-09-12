# Research paper

[paper.tex](paper.tex) is the canonical English source and [paper.pdf](paper.pdf)
is the revised 23-page paper, **Artist-Name Responses beyond a Shared Painting
Effect in Text-to-Image Generation**. All four painters and the declared
six-model comparisons remain. The added diagnostics distinguish response
magnitude, artist-pair alignment and agreement with the measured reference target.

The additions are explicitly post-result. Their [recorded scope](../studies/painter_specificity_review_v1/PLAN.md)
and [numerical record](../reports/painter_specificity_review_v1/analysis.json)
are separate from the unchanged primary analysis. Image examples expose reference
calibration strips and a title-class mismatch; the revision documents these
limitations rather than treating feature agreement as validated artistic fidelity.

## Build and verification

Run from the repository root with the recorded Python 3.13.11 environment:

```bash
make paper               # Rebuild numerical figures/tables and compile the PDF
make figures-check       # Verify figure/table replay
make specificity-check   # Replay the four declared numerical views
make review-check        # Replay the separate post-result diagnostics
uv run --locked pytest -q tests/painter_specificity_review_v1
```

The build reuses the committed example-panel PDFs. To verify or reproduce those
panels from the retained source images:

```bash
make review-images-check
uv run --locked python paper/make_review_figures.py --images
```

The [inspection manifest](../reports/painter_specificity_review_v1/inspection.json)
records the 36 generated and four reference examples, exact prompts, source
identifiers, rights metadata and byte hashes. Full-resolution sources are outside
the compact repository. These commands do not acquire images or extract features.

## Source organization

- `paper.tex` and `specificity_results.tex`: manuscript and results.
- `specificity_review_appendix.tex`: added diagnostic methods and image inspection.
- `make_specificity_figures.py` and `make_specificity_tables.py`: primary-result
  presentation; their generated files are included by the paper.
- `make_review_figures.py`: added tables, artist-pair plot and optional image panels.
- [Diagnostic implementation](../src/latent_art_bench/painter_specificity_review_v1.py):
  retained-vector analyses and exact replay of the saved source/input bindings.
- `references.bib`: bibliography. Earlier figure builders remain available for
  supporting evidence; the [analysis catalog](../docs/ANALYSES.md) maps their inputs.

Build intermediates and page previews belong under `tmp/paper/`. Historical
analysis records and source images remain intact.
