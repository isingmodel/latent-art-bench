# Research paper

[paper.tex](paper.tex) is the canonical English source and [paper.pdf](paper.pdf)
is the revised 22-page paper, **Artist-Name Responses beyond a Shared Painting
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
make specificity-check   # Replay the four declared numerical views
make review-check        # Replay both versions of post-result diagnostics
make reference-quality-check  # Replay source-region/scaler/label sensitivity
make reference-quality-images-check  # Verify all raw hashes and 131 crop features
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
the compact repository. The panel commands do not acquire images or extract features; the separate
reference-quality image check re-extracts crop features from retained pixels.

## Source organization

- `paper.tex` and `specificity_results.tex`: manuscript and results.
- `specificity_review_appendix.tex`: added diagnostic methods and image inspection.
- `make_specificity_figures.py` and `make_specificity_tables.py`: primary-result
  presentation; their generated files are included by the paper.
- `make_review_figures.py`: added tables, artist-pair plot and optional image panels.
- [Initial diagnostics](../src/latent_art_bench/painter_specificity_review_v1.py),
  [follow-up checks](../src/latent_art_bench/painter_specificity_review_v2.py) and
  [source-quality sensitivity](../src/latent_art_bench/painter_reference_quality_v1.py):
  separately bound analyses with exact replay.
- `references.bib`: bibliography. Earlier figure builders remain available for
  supporting evidence; the [analysis catalog](../docs/ANALYSES.md) maps their inputs.

Build intermediates and page previews belong under `tmp/paper/`. Historical
analysis records and source images remain intact.
