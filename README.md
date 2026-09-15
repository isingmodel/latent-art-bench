# LatentArtBench

**Does painter-name prompting recover differences between painters, or mainly
produce a shared painting-like appearance?**

This project compares generated images with digital reproductions of paintings
by Monet, Sisley, Pissarro and Cézanne using 31 interpretable color, spatial and
texture features. The current experiment separates common appearance from
reference-aligned painter variation and compares six image models on the same
scenes. It measures agreement with digital reference contrasts; perceptual style
and internal model mechanisms remain unvalidated.

Read the [current paper](paper/paper.pdf), then use the
[paper guide](paper/README.md) for sources, figures and build instructions.

The [prospective protocol](studies/painter_specificity_v2/PROTOCOL.md) fixes
**1,008 images**, 14 common scenes, six clauses and two repeated requests per
cell. Models are GPT Image 1, GPT Image 2, GPT Image 2.5 Flare, GPT Image 2.5
Sunburst, Nano Banana 2 and FLUX.2 Max. All 1,008 images were collected and
measured. The [results](reports/painter_specificity_v2/psv2-20260911/REPORT.md)
show positive reference-aligned responses in every model, but response strength
does not track pooled-reference agreement. FLUX has the lowest estimated
uncalibrated geometry error; its original adjusted advantage over Sunburst does not survive
[source-region correction](reports/painter_reference_quality_v1/REPORT.md), while
the Flare comparison remains separated. No model is established to beat
the no-contrast benchmark before calibration. Retrospective
[diagnostics](reports/painter_specificity_review_v1/REPORT.md) and
[follow-up checks](reports/painter_specificity_review_v2/REPORT.md) examine
artist pairs, shared responses and calibration; GPT Image 2 has the lowest
held-out calibrated error estimate. An assistant audit covers all 870
reference/development sources. The [novelty assessment](studies/painter_specificity_v1/NOVELTY.md)
identifies close prior work and the contribution being tested.

- [Current status](docs/STATUS.md): findings, limitations and revision state.
- [Handover](docs/AGENT_HANDOVER.md): implementation entry points and maintenance.
- [Analysis catalog](docs/ANALYSES.md): computation, plotting and replay commands.
- [Results index](reports/README.md): current reports and supporting evidence.
- [Editorial review record](reports/paper_editorial_review_v1/README.md): assessments tied to specific manuscript versions.
- [Artifact retention](docs/ARTIFACTS.md): immutable evidence and unique local bytes.

Earlier studies retain four-painter distributional differences, controlled
named/free comparisons, generic-clause and palette interventions, and prospective
fixed-map transfer. Their [versioned public releases](https://github.com/isingmodel/latent-art-bench/releases)
remain unchanged. The paper integrates the six-model results, all four
painters, generic/palette controls and the contrary fixed-map transfer result.
Its new compact experiment has not yet been archived as a public release.

## Reproduce

Use the recorded **Python 3.13.11** runtime and `uv` for current evidence replay.
The package metadata's broader Python floor does not qualify every frozen study
on older interpreters. From the repository root:

```bash
uv sync --locked --extra analysis --extra dev --inexact
make specificity-check
make review-check
make reference-quality-check
make paper
```

These commands make no generation requests. `make figures-check` verifies
presentation without rewriting it. See [the analysis catalog](docs/ANALYSES.md)
for supporting experiments and [the paper guide](paper/README.md) for compilation
and visual checks. Run targeted checks for the work being changed;
[test scope](tests/README.md) explains the broader suites.

No API key or learned-model weights are needed for current analysis replay.
Re-extracting features would require retained raw image bytes; a Git checkout does
not include those images. The intervention replay also verifies retained raw-response
hashes, so it requires the local response archive without re-extracting features.

## Repository map

| Location | Purpose |
| --- | --- |
| [paper/](paper/README.md) | The current manuscript, bibliography, figures and figure builder |
| [src/latent_art_bench/](src/latent_art_bench/) | Versioned analysis code and shared measurement primitives |
| [tests/](tests/README.md) | Current analysis/integrity checks and retained historical coverage |
| [reports/](reports/README.md) | Numerical results, complete tables, report plots and release receipts |
| [studies/](studies/) | Protocols, fixed study plans and methodological boundaries |
| [data/manifests/](data/manifests/) | Compact measured vectors, request records, hashes and receipts |
| [docs/](docs/INDEX.md) | Current guidance and navigation to retained historical evidence |

`paper/paper.tex` is the canonical English manuscript; earlier manuscript versions
are available in Git history. Historical scientific protocols, source, results and raw
local evidence remain necessary for reproducibility. Read the
[artifact policy](docs/ARTIFACTS.md) before deleting research files.

For the current state, read [STATUS.md](docs/STATUS.md). For implementation work,
read [the handover](docs/AGENT_HANDOVER.md),
[architecture](docs/ARCHITECTURE.md) and [contributing guidance](CONTRIBUTING.md).
The [documentation index](docs/INDEX.md) links current guidance. Retired reviews
and duplicate summaries remain in Git history; the current editorial assessment
record is linked above. Code is distributed under [the repository license](LICENSE);
full-resolution raw artwork is not redistributed by this repository; the paper
includes four reduced reference examples with recorded public-domain metadata.
