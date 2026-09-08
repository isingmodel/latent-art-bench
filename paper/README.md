# Research paper

The single current manuscript is [paper.tex](paper.tex), compiled to
[paper.pdf](paper.pdf), with [references.bib](references.bib). It integrates the original distribution study, scene-retrieval diagnostics and
the completed controlled color-response experiment into one research paper.
Earlier drafts and the superseded paper are retained only in Git history.
The [manuscript review and responses](../docs/reviews/20260908_manuscript.md)
record the internal LLM reviews and subsequent corrections.

## Build and check

From the repository root, after `uv sync --locked --extra analysis --extra dev`:

```bash
make figures   # Render five vector figures from saved numeric tables
make paper     # Render figures and compile paper/paper.pdf with Tectonic
make plots     # Byte-check both report bundles and the manuscript figures
```

`make_figures.py` verifies the hashes of six published CSV inputs. It
extracts saved endpoints and PCA coordinates without fitting projections or
computing new statistics. Its only outputs are the five PDFs in `figures/`.
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

Study 1 uses 1,006 generated images across three services; Study 2 uses 192 new
images from one service. The 70 painting reproductions and development scaler
fitted on 221 works are shared. The 49-image incomplete predecessor remains
ancillary and is not pooled into either primary cohort. The eight original
conditional randomization tests, post-result diagnostics and two new model-based
interaction tests remain distinct. Human judgments, independent capture
replication and learned-feature validation are unperformed.

- [Controlled study methods](../studies/painter_distribution_study_v1/MAIN.md)
- [Controlled report and complete tables](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md)
- [Diagnostic methods](../studies/painter_distribution_revision_v1/PROTOCOL.md)
- [Diagnostic report and complete tables](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md)
- [Computational follow-up synthesis](../reports/painter_responsiveness_v2/REPORT.md)
- [Color experiment and inference](../studies/painter_responsiveness_v2/PROTOCOL.md)
- [Primary color-response results](../reports/painter_responsiveness_v2/prv2-oauth-recovery-20260908/experiment/REPORT.md)
- [Exact-weight quantile corrigendum](../reports/painter_responsiveness_quantiles_v1/prqv1-20260908/REPORT.md)
- [Analysis and plotting source map](../docs/ANALYSES.md)

`make analysis` replays the original controlled study and revision.
`make computational-responsiveness` replays the subsequent computational studies
and quantile correction. These commands use retained
vectors and metadata; full integrity-checked computational replay also requires
the separately retained raw response archive. Figure rebuilding uses only the
committed numeric tables. None of these commands regenerates images or restarts
terminal studies.
