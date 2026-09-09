# LatentArtBench

LatentArtBench compares the feature distributions of generated images with digital
reproductions of artists' paintings. It measures color, spatial structure and
texture with **31 interpretable features**. The current research asks how adding a
painter's name changes proximity to the reference distribution and variation
among generated images.

The project is in the **paper-correction phase**. The
[handover](docs/AGENT_HANDOVER.md) records completed work, current boundaries and
the correction workflow; [STATUS.md](docs/STATUS.md) records integration and checks.

Read the [English paper](paper/paper.pdf), its [source and build guide](paper/README.md),
and the [complete revision report](reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md).
The paper integrates **1,006 images from three generation routes** in Study 1
and a separate **192-image color experiment** in Study 2, using 70 Monet/Cézanne
references and 221 development works.

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

## Reproduce

Use the recorded **Python 3.13.11** runtime and `uv` for current evidence replay.
The package metadata's broader Python floor does not qualify every frozen study
on older interpreters. From the repository root:

```bash
uv sync --locked --extra analysis --extra dev --inexact
make analysis
make plots
make computational-responsiveness
make check
make evidence
```

`make analysis` and `make plots` cover Study 1 and its computational revision;
`make computational-responsiveness` covers Study 2, retained-data retrieval and
the quantile correction. These targets make no generation requests.
`make figures-check` checks only the five manuscript figures without rewriting
them. `make figures` rebuilds the five
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
