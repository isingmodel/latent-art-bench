# Current status — 2026-09-09

The project is in the **paper-correction phase**. Research collection, measurement
and analysis are complete; no collector is active. Local `main` was fast-forwarded
from `bdd57e9` to `ecc2c2b`, incorporating `research/pfg-v2-paper` and preserving
every commit referenced by scientific evidence. No remote push was performed.

Use the [handover](AGENT_HANDOVER.md) for completed work and correction boundaries,
the [paper guide](../paper/README.md) for editing/building, and the
[analysis catalog](ANALYSES.md) for computation and plotting entry points.
Current guidance is mutable; [ARTIFACTS.md](ARTIFACTS.md) governs retained evidence.

Integration cleanup clarified Study 1 versus Study 2 replay commands, added
`make figures-check`, consolidated current status and rewrote the handover.
Frozen code, protocols and evidence retain their recorded paths; the approved
English manuscript and both user-owned Korean files are byte-unchanged.

## Manuscript and correction baseline

The canonical English manuscript is [paper/paper.tex](../paper/paper.tex):
**Painter Naming and the Distributional Gap Between Generated Images and
Original Paintings**, with a [19-page PDF](../paper/paper.pdf) and five vector
figures. Substantive revision `dd314ee` gives each study its own methods and
results, promotes painter alignment and matched-reference coverage, clarifies the
evidence hierarchy, and shows all six scene-specific color interactions.

The [scored review record](reviews/20260909_scored_review/REVIEW.md) preserves the
three reviewers' findings and responses. Its equal-weight mean increased from
**7.8125 to 8.5417/10**; final reviewer means are 8.625, 8.500 and 8.500, with no
unresolved blocking manuscript finding. These are maintainer-run LLM assessments,
not external peer-review scores. They describe that revision, rather than serving
as a gate for subsequent corrections.

The local Korean manuscript source and PDF are user-owned work and remain
outside this cleanup. Public archival release of the scientific snapshot
`28a9eb6` and external raw-media access remain pending; a local merge does not
establish either.

## Completed evidence

| Component | State and interpretation |
| --- | --- |
| [Study 1 controlled analysis](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md) | 1,006 generated images across three services, 70 Monet/Cézanne references and 221 development works. Preserve the original eight conditional randomization tests. Naming lowers primary energy discrepancy in all six service/painter cells; four reject after adjustment. |
| [Study 1 computational revision](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md) | Feature-view, variance, reference/scaler, painter-alignment, coverage and cross-service diagnostics. Aggregate contraction does not establish perceptual similarity or a causal mechanism. |
| [Retained-data retrieval](../reports/painter_responsiveness_v2/prv2-oauth-20260908/diagnostics/REPORT.md) | Retrieval improves in two cells and declines in four despite between-scene contraction. FLUX/Monet improves from 44.4% to 59.7%. These fixed-feature descriptions are not new significance tests or human scene-adherence scores. |
| [Study 2 color experiment](../reports/painter_responsiveness_v2/prv2-oauth-recovery-20260908/experiment/REPORT.md) | Sole primary run `prv2-oauth-recovery-20260908` completed 192/192 images: six fixed scenes, four style arms, two palettes and four repeats, with shared free/generic controls. Both primary named-minus-generic interactions remain unresolved. |
| [Exact-weight quantile corrigendum](../reports/painter_responsiveness_quantiles_v1/prqv1-20260908/REPORT.md) | Corrects 51 primary and 15 ancillary descriptive medians. Primary inference, means, Wasserstein distances, 10th/90th percentile endpoints and range occupancy are unchanged. Original bundles remain preserved. |
| [Earlier responsiveness v1](../reports/painter_responsiveness_v1/prv1-diagnostic-20260908/REPORT.md) | D0 diagnostic complete; human reference tasks have zero responses and the FLUX preflight is closed. Its human/reference prerequisites were not retroactively waived or fulfilled. |

Study 2's Monet interaction is −0.284 (simultaneous family interval
[−0.585, 0.016], Holm p=0.0649); Cézanne is −0.018 ([−0.343, 0.308],
p=0.8886). The tested generic-minus-free contrast is secondary: −0.853
(nominal 95% interval [−1.136, −0.570]). A JPEG sensitivity threshold crossing
does not replace the prespecified result. The
[scientific synthesis](../reports/painter_responsiveness_v2/REPORT.md) connects
these results to the original/generated distributions and their limits.

## Collection boundary and accounting

The 49-image predecessor is ancillary and never pooled into primary inference.
Its one complete HTTP 503 and 142 never-started slots remain recorded. The
[prospective recovery protocol](../studies/painter_responsiveness_recovery_v1/PROTOCOL.md)
created a disjoint replacement and qualified only that exact error form for
bounded retries. Across both terminal collections there were 242 attempts,
241 unique images and zero actual retries. See the
[implementation guide](../studies/painter_responsiveness_v2/README.md) for the
source/process bindings and recorded commits.

All 192 primary outputs were nonsquare despite a square request; 174 reported
low quality and 18 medium despite a fixed medium request. These fields remain
unfiltered. Findings concern the complete delivered-service response.

No OpenRouter requests or charges were incurred in this follow-up or manuscript
revision. Prior conservative accounting remains **$45.6819185 within the $75
ceiling**; OAuth subscription usage has no assigned monetary value.

Terminal collections cannot be resumed or refilled. Frozen sources, tests,
protocols, configurations and evidence stay at their recorded paths. Human
ratings, independent capture replication and learned-feature validation remain
unperformed. Paper correction does not reopen image acquisition or extraction.

## Verification

Integration validation passed on local `main` at `ecc2c2b`:

- Ruff and **1,135 offline tests** (117.82 seconds).
- Historical evidence audit: **2,902 checks, zero failures**, retaining only the
  two existing acknowledgements.
- All five manuscript figures reproduce byte for byte with `make figures-check`.
- All 293 local documentation links and both checked anchors resolve;
  `git diff --check` passes.
- Hashes confirm that the English TeX/PDF and both user-owned Korean files are
  unchanged from the start of integration.

The manuscript was not rebuilt during cleanup. Its last substantive revision
had all 19 pages visually inspected and no TeX warnings. The
[computational review](reviews/20260908_computational_responsiveness/REVIEW.md)
records numerical/report replay and visual checks of the experiment displays.

The historical evidence audit does not register responsiveness v2.
`make computational-responsiveness` separately
verifies the retrieval, primary replacement, ancillary predecessor and quantile
correction: **74 report files** plus numerical calculations and input/output
hashes, using the retained response archive. That full replay passed before the
manuscript revision; no scientific inputs or implementations changed in cleanup.

`make analysis` and `make plots` cover Study 1 and its revision.
`make figures-check` checks only the five editable manuscript figures.
All replay targets are offline; the [paper guide](../paper/README.md) specifies
the build and page-inspection workflow for the next correction.
