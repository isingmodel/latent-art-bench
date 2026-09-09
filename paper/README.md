# Research paper

The canonical English manuscript is [paper.tex](paper.tex), compiled to
[paper.pdf](paper.pdf), with [references.bib](references.bib). It integrates the original distribution study, scene-retrieval diagnostics and
the completed controlled color-response experiment into one research paper.
Earlier drafts and the superseded paper are retained only in Git history.
The [scored manuscript reviews and responses](../docs/reviews/20260909_scored_review/REVIEW.md)
record three maintainer-run LLM assessments under a fixed eight-aspect rubric.
The final average is **8.5417/10** (initially 7.8125), with no blocking manuscript
finding. These are internal assessment scores, not external peer acceptance.
The delivered manuscript is 19 pages.
The [earlier integration review](../docs/reviews/20260908_manuscript.md) remains
historical. The current paper gives each study its own methods and results,
promotes joint painter alignment and matched-reference occupancy, and shows all
six scene-specific color interactions alongside the pooled intervals.

This is the build guide for the current paper-correction phase. Edit the English
source, bibliography and presentation figures here; trace claims to the saved
evidence listed below. The [handover](../docs/AGENT_HANDOVER.md) records completed
work and scientific boundaries. The dated reviews describe the delivered revision;
their scores are not a gate for routine corrections. Preserve untracked user drafts.

## Build and check

From the repository root, after `uv sync --locked --extra analysis --extra dev`:

```bash
make paper          # Render figures and compile paper/paper.pdf with Tectonic
make figures-check  # Check manuscript figures without rewriting them
```

`make_figures.py` verifies the hashes of six published CSV inputs. It
extracts saved endpoints and PCA coordinates without fitting projections or
computing new statistics. Its only outputs are the five PDFs in `figures/`. The color-response figure
extracts the six saved scene estimates for each painter as well as the pooled
estimates and intervals; it does not calculate new interactions.
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
`make plots` byte-checks those two Study 1 report bundles and the manuscript figures.
`make computational-responsiveness` replays the subsequent computational studies
and quantile correction. These commands use retained
vectors and metadata; full integrity-checked computational replay also requires
the separately retained raw response archive. Figure rebuilding uses only the
committed numeric tables. None of these commands regenerates images or restarts
terminal studies.

## Release and access status

The project remote is <https://github.com/isingmodel/latent-art-bench>. The
scientific snapshot cited by this draft is local commit `28a9eb6`; its public
archival release is pending. The current manuscript revision does not publish
or push that snapshot. Figure rebuilding requires the redistributed numeric
tables, while full computational-follow-up replay verifies separately retained
raw-response bytes. Image-level remeasurement additionally needs retained image
pixels. Those media are not publicly redistributed, and external access has
not been arranged. The paper distinguishes these access boundaries explicitly.
