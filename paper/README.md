# Research paper

The single current manuscript is [paper.tex](paper.tex), compiled to
[paper.pdf](paper.pdf), with [references.bib](references.bib). It is the complete
11-page rewrite on painter naming, reference proximity and generated variation.
Earlier drafts and the superseded paper are retained only in Git history.
The [manuscript review and responses](../docs/reviews/20260907_manuscript.md)
record the internal LLM reviews and subsequent corrections.

## Build and check

From the repository root, after `uv sync --locked --extra analysis --extra dev`:

```bash
make figures   # Render three vector figures from saved numeric tables
make paper     # Render figures and compile paper/paper.pdf with Tectonic
make plots     # Byte-check both report bundles and the manuscript figures
```

`make_figures.py` verifies the hashes of its three published CSV inputs. It
extracts saved endpoints and PCA coordinates without fitting projections or
computing new statistics. Its only outputs are the three PDFs in `figures/`.
For temporary PNG previews:

```bash
uv run --locked python paper/make_figures.py --preview-dir tmp/paper/preview
```

Build files go to `tmp/paper/build/`. Render and inspect every PDF page after
manuscript edits, for example:

```bash
mkdir -p tmp/paper/pages
pdftoppm -r 100 -png paper/paper.pdf tmp/paper/pages/page
```

## Scientific inputs

The paper uses 1,006 generated images, 70 painting reproductions and a scaler
fitted on 221 development works. Eight original conditional randomization tests
remain distinct from the subsequent descriptive diagnostics. Human judgments,
independent capture replication and learned-feature validation are unperformed.

- [Controlled study methods](../studies/painter_distribution_study_v1/MAIN.md)
- [Controlled report and complete tables](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md)
- [Diagnostic methods](../studies/painter_distribution_revision_v1/PROTOCOL.md)
- [Diagnostic report and complete tables](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md)
- [Analysis and plotting source map](../docs/ANALYSES.md)

`make analysis` replays both numerical analyses. These commands use retained
vectors and metadata; they do not regenerate images or restart terminal studies.
