# LatentArtBench

**Does painter-name prompting recover differences between painters, or mainly
produce a shared painting-like appearance?**

This project compares generated images with digital reproductions of paintings
by Monet, Sisley, Pissarro and Cézanne using 31 interpretable color, spatial and
texture features. The current experiment separates common appearance from
reference-aligned painter variation and compares six image models on the same
scenes. It evaluates digital feature recovery, without claiming perceptual
style validation or an identified internal model mechanism.

The [prospective protocol](studies/painter_specificity_v2/PROTOCOL.md) fixes
**1,008 images**, 14 common scenes, six clauses and two repeated requests per
cell. Models are GPT Image 1, GPT Image 2, GPT Image 2.5 Flare, GPT Image 2.5
Sunburst, Nano Banana 2 and FLUX.2 Max. Collection is running; new scientific
results are pending. The [novelty assessment](studies/painter_specificity_v1/NOVELTY.md)
identifies close prior work and the limited contribution being tested.

- [Current status](docs/STATUS.md): active collection, accounting and boundaries.
- [Handover](docs/AGENT_HANDOVER.md): source freezes and continuation instructions.
- [Analysis catalog](docs/ANALYSES.md): computation, plots and replay commands.
- [Manuscript source](paper/paper.tex) and [build guide](paper/README.md).
- [Artifact retention](docs/ARTIFACTS.md): immutable evidence and unique local bytes.

Earlier studies retain four-painter distributional differences, controlled
named/free comparisons, generic-clause and palette interventions, and prospective
fixed-map transfer. Their [versioned public releases](https://github.com/isingmodel/latent-art-bench/releases)
remain unchanged. The current manuscript rewrite is in progress; the existing
PDF is the prior completed 39-page version until the new experiment is analyzed.

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
| [tests/](tests/README.md) | 822 routine analysis/integrity cases; historical checks via `make check-all` |
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
