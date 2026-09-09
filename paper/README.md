# Research paper

The canonical English manuscript is [paper.tex](paper.tex), compiled to
[paper.pdf](paper.pdf), with [references.bib](references.bib). It restores the
four-painter distributional analysis to the main text, followed by the separate
two-painter controlled distribution study, scene-retrieval diagnostics and
controlled color-response experiment. The current draft is 24 pages with six
vector figures.
Earlier drafts and the superseded paper are retained only in Git history.
The [four-painter restoration record](../docs/reviews/20260909_four_painter_restoration.md)
documents the omission history, restored evidence, two maintainer-run LLM reviews,
table checks, replay of 62 report files and manuscript QA.
The [scored manuscript reviews and responses](../docs/reviews/20260909_scored_review/REVIEW.md)
record three maintainer-run LLM assessments of the **prior 19-page revision**
under a fixed eight-aspect rubric. Its final average was **8.5417/10** (initially
7.8125), with no blocking manuscript finding. These scores do not apply to the
restored four-painter draft and are not external peer acceptance.
The [earlier integration review](../docs/reviews/20260908_manuscript.md) remains
historical. The current paper gives each study its own methods and results,
promotes joint painter alignment and matched-reference occupancy, and shows all
six scene-specific color interactions alongside the pooled intervals.

This is the build guide for the current paper-correction phase. Edit the English
source, bibliography and presentation figures here; trace claims to the saved
evidence listed below. The [handover](../docs/AGENT_HANDOVER.md) records completed
work and scientific boundaries. The dated reviews describe their identified revision;
their scores are not a gate for routine corrections. Preserve untracked user drafts.

## Build and check

From the repository root, after `uv sync --locked --extra analysis --extra dev`:

```bash
make paper          # Render figures and compile paper/paper.pdf with Tectonic
make figures-check  # Check manuscript figures without rewriting them
```

`make_figures.py` verifies the hashes of eight published inputs: seven CSVs and
the exploration's `projections.json`. It extracts saved endpoints and PCA
coordinates without fitting projections or
computing new statistics. Its only permanent outputs are the six PDFs in `figures/`.
The four-painter figure displays 649 unique originals and 1,536 painter-conditioned
outputs using the saved all-31-feature balanced-joint coordinates. Each painter
shares a basis and axis limits across its three prompt methods; equal aspect and
all outliers are retained, with the two later retry points marked. The color-response figure
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

The four-painter exploration uses 649 painting reproductions: 297 Monet,
106 Sisley, 141 Pissarro and 105 Cézanne. Its completed retry grid contains
1,536 painter-conditioned outputs (three prompt methods × two requested aliases
× four painters × 64 outputs) and 384 artist-free controls. The exploration,
Stage A diagnostics and retry contrasts are descriptive post-result analyses.
Two later successes remain identified, the original incomplete-grid primary
inference remains unavailable, and the requested `gpt-image-1` / `gpt-image-2`
aliases do not establish distinct underlying model identities.

Study 1 separately uses 1,006 generated images across three services; Study 2 uses
192 images from one service. These later studies share a 70-work Monet/Cézanne
reference panel and a development scaler fitted on 221 works. Their controlled
results are not pooled with the earlier four-painter cohort. The 49-image
incomplete color-experiment predecessor remains ancillary and is not pooled
into either primary cohort. The eight original
conditional randomization tests, post-result diagnostics and two new model-based
interaction tests remain distinct. Human judgments, independent capture
replication and learned-feature validation are unperformed.

- [Four-painter exploration methods](../studies/painter_distribution_exploration_v1/METHODS.md)
- [Four-painter distributions and complete tables](../reports/painter_distribution_exploration_v1/REPORT.md)
- [Stage A diagnostic controls](../reports/painter_distribution_study_v1/pdsv1-diagnostics-20260906/REPORT.md)
- [Descriptive retry contrasts](../reports/painter_prompt_retry_v1/ppr1-two-refusals-20260906-r2/REPORT.md)
- [Controlled study methods](../studies/painter_distribution_study_v1/MAIN.md)
- [Controlled report and complete tables](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md)
- [Diagnostic methods](../studies/painter_distribution_revision_v1/PROTOCOL.md)
- [Diagnostic report and complete tables](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md)
- [Computational follow-up synthesis](../reports/painter_responsiveness_v2/REPORT.md)
- [Color experiment and inference](../studies/painter_responsiveness_v2/PROTOCOL.md)
- [Primary color-response results](../reports/painter_responsiveness_v2/prv2-oauth-recovery-20260908/experiment/REPORT.md)
- [Exact-weight quantile corrigendum](../reports/painter_responsiveness_quantiles_v1/prqv1-20260908/REPORT.md)
- [Analysis and plotting source map](../docs/ANALYSES.md)

`make four-painter-analysis` replays the exploration, Stage A diagnostics and
retry presentation, verifying 35 + 18 + 9 published files. `make analysis`
replays the later controlled study and revision.
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
