# English paper prototype

The completed **14-page** venue-neutral manuscript is [paper.pdf](paper.pdf), with
editable [LaTeX source](paper.tex) and [bibliography](references.bib). It reports
actual controlled results from 1,006 generated images and 70 fresh reference works,
with historical findings as development context. Figures and numerical tables come
from the verified [controlled analysis](../../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md).

The central finding is improved proximity with contracted aggregate spread when
naming painters on the two paid routes. The manuscript includes conditional prompt
inference, grouped detection, coverage, specificity, processing and reference
exceptions, service rendering variation, costs and the publication-only Boolean
correction. Human construct validation and learned representations remain follow-ups;
no venue, collaborator participation or authorship is presumed.

Build from this directory:

```bash
tectonic --outdir ../../tmp/paper-build paper.tex
cp ../../tmp/paper-build/paper.pdf paper.pdf
```

Create the temporary output directory first if necessary. All 14 pages were rendered
and visually inspected after the final build; no TeX overflow warning remained.
The three included scientific figures contain numerical points only, not artwork pixels.
The report also exports original-only PCA and matched-reference baseline figures,
all 22 files with byte-for-byte replay. See the [workflow](../../docs/DISTRIBUTION_STUDY_WORKFLOW.md)
for numerical and raw-feature verification commands. The original frozen scientific
calculation remains unchanged, and every collection census is closed permanently.
