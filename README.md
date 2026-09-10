# LatentArtBench

LatentArtBench compares the feature distributions of generated images with digital
reproductions of artists' paintings. It measures color, spatial structure and
texture with **31 interpretable features**. The current research asks how adding a
painter's name changes proximity to the reference distribution and variation
among generated images.

The paper now includes **held-scene moment maps, temporal transfer and a
center-controlled comparison**, with [public numerical replay](https://github.com/isingmodel/latent-art-bench/releases/tag/ppgv1-20260910).
The 288-slot prospective clause validation stopped after 211 images; both
primary comparisons are unavailable. One separately frozen, final 96-output
Cezanne/generic comparison is complete: energy falls from 2.166 to .970
(paired randomization p=.00001), with named/generic trace ratio .552.
The result uses 24 new fixed scenes; it supplies no new-scene map validation.
Neither clause cohort is pooled with another, and both added zero paid cost. The
[handover](docs/AGENT_HANDOVER.md) records completed work, current boundaries and
the correction workflow; [STATUS.md](docs/STATUS.md) records integration and checks.

The [local English draft](paper/paper.pdf) is now 39 pages and remains unpublished.
The latest [published paper](https://github.com/isingmodel/latent-art-bench/releases/tag/pcrv1-20260910)
is the 36-page clause-release version. See the [source and build guide](paper/README.md)
and [analysis catalog](docs/ANALYSES.md).
The paper begins with a **four-painter distributional analysis**: 649 references
(297 Monet, 106 Sisley, 141 Pissarro and 105 Cézanne), 1,536 painter-conditioned
outputs across three prompt methods, and 384 artist-free controls. This descriptive
evidence is separate from Study 1's **1,006 images from three generation routes**
and 70 Monet/Cézanne references, and Study 2's **192-image color experiment**.
The development panel contains 221 works.

The separate fixed-map v1 proposal stopped before collection: all 81 proxy coverage
checks passed, but each allocation failed the conditional-residual precision gate.
Its [public planning release](https://github.com/isingmodel/latent-art-bench/releases/tag/pmrv1-20260910)
replays all 81 cells and contains no new images. One prospective R10 redesign
passed qualification and completed its [240-output FLUX/Cezanne comparison](reports/painter_map_validation_v2/pmv2-20260910/REPORT.md)
on twelve new fixed scenes. Translation/scaling improves both reference energy
(deltaE −.390187) and corrected conditional-mean prediction (deltaQ −5.046510),
with both approximate simultaneous intervals below zero. The earlier opposing
ordering does not transfer. The observed Q half-width exceeds the proxy planning
criterion, so passed qualification should not be read as achieved precision.
Collection and measurement are permanently complete; do not restart either.

New reported charges are $16.80; conservative project accounting is **$67.5219185**
against the $75 ceiling. All 240 outputs returned without failure/retry. The
[terminal audit](docs/reviews/20260910_substantive_revision/MAP_VALIDATION_TERMINAL_AUDIT_2.md)
passes response, source and measured-vector provenance plus exact numerical replay.
The [public numerical archive](reports/paper_map_validation_reproducibility_v2/pmv2r-20260910/REPORT.md)
passes exact fresh local and anonymous replay with 75 tests each. A single
[Ubuntu attempt](reports/paper_map_validation_reproducibility_v2/pmv2r-20260910/HOSTED_REPORT.md)
fails the qualification comparison before observed replay; its tests and
inventory checks pass. A [separate diagnostic](reports/paper_map_portability_diagnostic_v1/pmpdv1-20260910/REPORT.md)
localizes its own failure to support hashes and records floating differences below
4e-15, with the displayed results unchanged. An additive portable route is in
development; cross-platform replay under that route remains unverified. The fixed
round-4 score mean is **8.9333** after three full reviews of the 39-page
version under the unchanged rubric. The target remains unmet. See
[STATUS.md](docs/STATUS.md) for current manuscript integration and verification.

The [four-painter exploration](reports/painter_distribution_exploration_v1/REPORT.md)
shows overlap in two-dimensional projections alongside reduced generated spread
and strong held-scene discrimination in all four painters. It is a post-result
analysis of the completed retry grid: two later successes are identified, and
the requested `gpt-image-1` / `gpt-image-2` aliases do not establish distinct
underlying model identities. The original incomplete study's primary inference
remains unavailable. Restoring these results does not turn them into new
confirmatory evidence.

Painter naming reduces the primary feature discrepancy on both paid routes and
reduces aggregate variation relative to artist-free controls. Variation within a
scene description does not always decrease, and one proximity comparison reverses
when texture is removed at a different measurement resolution. These are bounded
computational findings: human style validation is unperformed, reference capture
provenance is unresolved, and image geometry differs between domains.

The [computational follow-up report](reports/painter_responsiveness_v2/REPORT.md)
adds a completed **192-image intervention without human ratings**. The tested
generic painting clause reduces response to muted/vivid color instructions in a
secondary comparison; additional
Monet/Cézanne effects remain unresolved in the two primary comparisons. Retained-data
scene retrieval improves for FLUX/Monet despite strong feature contraction, showing
that contraction does not necessarily imply lost scene distinguishability.
The report links the new distributions to the original digital paintings and
documents the limits of these explanations. See [implementation](studies/painter_responsiveness_v2/README.md)
and [current status](docs/STATUS.md); `make computational-responsiveness` replays the
published results offline. The earlier [v1 diagnostic](reports/painter_responsiveness_v1/prv1-diagnostic-20260908/REPORT.md)
and its unperformed human-validation scope remain preserved.

The [measurement challenge](reports/painter_measurement_validation_v1/pmvv1-20260910/REPORT.md)
adds ten controlled image conditions on the 70 references and common-square
measurements of all 1,006 Study 1 outputs. The specified transformations exceed
the selected processing comparison on average, while revealing substantial
texture sensitivity to resampling and overlapping feature-family responses.
All eight naming/description contrast directions and the original four adjusted
rejections persist under the common square. This is computational measurement
characterization, without human style or independent-capture validation.
The [fresh 264-image temporal follow-up](reports/painter_naming_replication_v1/pnrv1-20260910/REPORT.md)
reproduces both FLUX naming directions (adjusted p=.00006/.00004); the two palette
interactions remain unresolved. All outputs returned without retries, at a new
reported OpenRouter cost of $5.04. The same maintainer collected this cohort; it
is not independent-investigator replication. The [public numerical release](https://github.com/isingmodel/latent-art-bench/releases/tag/pprv1-20260910)
passes 98 exact checks after anonymous download and 98 checks under its documented
Ubuntu portability contract. Its corrected `paper-r1.pdf`, the earlier geometry
paper, both numerical archives and the explicit erratum remain preserved; the
latest published manuscript is in the separate clause release. See the
[verification report](reports/paper_reproducibility_v1/pprv1-20260910/REPORT.md) and
[STATUS.md](docs/STATUS.md) for access, scope and accounting.

## Reproduce

Use the recorded **Python 3.13.11** runtime and `uv` for current evidence replay.
The package metadata's broader Python floor does not qualify every frozen study
on older interpreters. From the repository root:

```bash
uv sync --locked --extra analysis --extra dev --inexact
make four-painter-analysis
make analysis
make plots
make computational-responsiveness
make validation-check
make replication-check
make geometry-check
make check
make evidence
```

`make four-painter-analysis` replays the four-painter exploration, Stage A controls
and retry presentation. `make analysis` and `make plots` cover Study 1 and its
computational revision;
`make computational-responsiveness` covers Study 2, retained-data retrieval and
the quantile correction. These targets make no generation requests.
`make figures-check` checks the nine manuscript figures without rewriting
them. `make figures` rebuilds the nine
manuscript figures; `make paper` builds the PDF with Tectonic. See
[the analysis catalog](docs/ANALYSES.md) for individual commands, inputs and outputs,
and [the paper guide](paper/README.md) for rendering and visual checks.

No API key or learned-model weights are needed for current analysis replay.
Re-extracting features would require retained raw image bytes; a Git checkout does
not include those images. The intervention replay also verifies retained raw-response
hashes, so it requires the local response archive without re-extracting features.

## Repository map

| Location | Purpose |
| --- | --- |
| [paper/](paper/README.md) | The current manuscript, bibliography, figures and figure builder |
| [src/latent_art_bench/](src/latent_art_bench/) | Versioned analysis code and shared measurement primitives |
| [tests/](tests/) | Offline contract and numerical tests |
| [reports/](reports/) | Published numerical results, complete tables and report plots |
| [studies/](studies/) | Protocols, fixed study plans and methodological boundaries |
| [data/manifests/](data/manifests/) | Compact measured vectors, request records, hashes and receipts |
| [docs/](docs/INDEX.md) | Current guidance and navigation to retained historical evidence |

`paper/paper.tex` is the canonical English manuscript; earlier manuscript versions
are available in Git history. Historical scientific protocols, source, results and raw
local evidence remain necessary for reproducibility. Read the
[artifact policy](docs/ARTIFACTS.md) before deleting research files.

For the current state, read [STATUS.md](docs/STATUS.md). For implementation work,
read [AGENTS.md](AGENTS.md), [the handover](docs/AGENT_HANDOVER.md),
[architecture](docs/ARCHITECTURE.md) and [contributing guidance](CONTRIBUTING.md).
The [documentation index](docs/INDEX.md) links earlier studies without duplicating
their history here. Code is distributed under [the repository license](LICENSE);
raw artwork is not redistributed by this repository.
