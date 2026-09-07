# Current status — 2026-09-08

The computational revision and English manuscript are complete. The canonical
manuscript is [paper/paper.pdf](../paper/paper.pdf), with one TeX source and three
vector figures in [paper/](../paper/README.md). Earlier manuscript versions remain
in Git history; terminal scientific evidence stays at its original paths.
There is no active collector or scheduled continuation.

## Completed evidence

| Item | Current state |
| --- | --- |
| Controlled study | 1,006 generated images, 70 Monet/Cézanne references, 221 development works; [report](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md) |
| Computational revision | 103 bound inputs; four feature views, variation decomposition, reference/scaler sensitivity, painter interactions, coverage and cross-route diagnostics; [report](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md) |
| English manuscript | 11 pages, three figures, two tables; [build guide](../paper/README.md) |
| Review | Skeptical methodology and manuscript reviews by maintainer-run LLM subagents, followed by coordinator checks; [methodology review](reviews/20260907_methodology/REVIEW_AND_REVISION_PLAN.md) and [manuscript responses](reviews/20260907_manuscript.md) |

The original eight conditional randomization tests are preserved. All additional
revision diagnostics are post-result and descriptive; they introduce no new
confirmatory test family. The revision report contains six figures and 31 tables.
The manuscript figure builder uses saved, hash-checked values and PCA coordinates.

## Scientific interpretation

- Painter naming lowers the primary energy discrepancy on both paid routes for
  both painters. All 72 fixed-view named/free total-variance ratios are below one.
- Aggregate contraction does not imply contraction within a scene description:
  primary OAuth Cézanne has within-brief ratio **1.139**, despite total ratio **0.651**.
- Nano Banana 2 Monet is sensitive to the feature view: its primary named/reference
  variance ratio becomes **1.101** without texture, and its 256-pixel/no-texture
  energy contrast reverses to **+0.4159**. The other paid comparisons retain their
  energy directions across the fixed views and pipelines.
- Cross-route fixed-threshold balanced accuracy falls under naming in all 12
  directed route/painter comparisons for both kernels. Mean within-fold AUC can
  increase; this is not a uniform loss of discrimination.
- Coverage depends on reference sampling and neighborhood size. All 576 paid
  outputs are square and all 70 references nonsquare; every reference capture
  workflow remains unresolved. Absolute domain separability is not validated as
  a measure of painter style.

These findings support a finite-feature case study. They do not establish human
perceived resemblance, perceived variation, or general model superiority.

## Remaining research

The [mechanism-focused research report](RESEARCH_IDEA_20260908.md) combines 12
primary-paper readings with eight numerical and metadata case studies. It proposes
testing visual responsiveness under painter naming, with capture and reference
validation, before adding model breadth. Its optional 192-image shared-control
design is a planning cap, not an executed study or a justified power target.

Human judgments, independent reference/capture replication, independent content
coding and learned-feature validation remain **unperformed**. The frozen
[validation plan](../studies/painter_distribution_revision_v1/VALIDATION_PLAN.md)
and [literature matrix](../studies/painter_distribution_revision_v1/LITERATURE_MATRIX.md)
record the next research options. More generated images alone cannot resolve the
current capture and construct limitations.

No images or generation spending were added for the revision or manuscript rewrite.
Conservative recorded study accounting is **$45.6819185 of the $75 ceiling**;
this is historical accounting, not a fresh API balance. The controlled collection
is terminal, including its two refusals and successful technical retry.

## Verification

Verified on **2026-09-08** after repository cleanup: `make check` passes Ruff
and **886 offline tests** (95.90 seconds). `make analysis` reproduces both the
controlled and revision numerical results. `make plots` reproduces all **22
controlled report files**, **44 revision report files**, and the three manuscript
figure PDFs byte-for-byte. `make paper` builds the 11-page PDF; every page was
visually checked. The historical evidence audit passes **2,902 checks with zero
failures**, retaining only its two documented historical acknowledgements.

## Repository cleanup

The revised manuscript is the only paper in the working tree, under `paper/`.
Four duplicated workflow guides and three unused CLI-alias scripts were retired;
their replay instructions are consolidated in the analysis catalog and Makefile.
The current guides were rewritten instead of appending more historical status.
Exactly 342 inspected build/preview files (91.7 MiB) were removed, with no retained
scientific references to their paths. Frozen source, protocols, reports, local
image data, literature and bound temporary records remain unchanged. Earlier
manuscripts and retired documentation are available in Git history.

Use [the analysis catalog](ANALYSES.md) for current replay commands and
[the artifact policy](ARTIFACTS.md) for retention rules. This is mutable operational
status; protocols and terminal receipts are the authoritative scientific record.
