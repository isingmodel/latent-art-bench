# LatentArtBench

**Does painter-name prompting recover differences between painters, or mainly
produce a shared painting-like appearance?**

This project compares generated images with digital reproductions of paintings
by Monet, Sisley, Pissarro and Cézanne using 31 interpretable color, spatial and
texture features, with CLIP and CSD representations as a same-image check. It
separates the appearance common to all painter names from reference-aligned
painter variation. It measures agreement with digital reference contrasts;
perceptual style and internal model mechanisms remain unvalidated.

## Current state

The primary [prospective experiment](studies/painter_specificity_v2/PROTOCOL.md)
has **1,008 images**: six image models × 14 scenes × six prompt clauses × two
repeats. The models are GPT Image 1, GPT Image 2, GPT Image 2.5 Flare,
GPT Image 2.5 Sunburst, Nano Banana 2 and FLUX.2 Max.

- Every model shows a positive reference-aligned response, but response strength
  does not track agreement with the pooled reference.
- Most of the change added by a painter name, beyond a generic painting request,
  is common to all four names: 66.7–88.4% in the 31 features.
- FLUX.2 Max has the lowest uncalibrated error estimate; GPT Image 2 has the
  lowest held-out calibrated error. No model is shown to beat the no-contrast
  benchmark before calibration.
- A separate 2,000-image SD-Turbo collection also shows majority-common change
  overall, but not in texture features.

[docs/STATUS.md](docs/STATUS.md) has the full findings, the retrospective
analyses added for the ICML draft, open decisions and limits.

## Manuscripts

| Manuscript | Source | Scope |
| --- | --- | --- |
| ICML-format draft | [paper/icml.tex](paper/icml.tex) | Most recent: primary results plus all retrospective extensions; its PDF is built locally with `make paper-icml` |
| Full-length paper | [paper/paper.tex](paper/paper.tex), [PDF](paper/paper.pdf) | 23-page version of 2026-09-15, without the ICML-era extensions |
| Korean translation | [paper/latent_art_bench_korean.tex](paper/latent_art_bench_korean.tex) | Translation of the full-length paper |

The [paper guide](paper/README.md) explains sources, figures and builds.

## Reproduce

Use the recorded **Python 3.13.11** runtime and `uv`. The package metadata's
broader Python floor does not qualify every frozen study on older interpreters.

```bash
uv sync --locked --extra analysis --extra dev --inexact
make specificity-check      # Primary numerical results
make review-check           # Post-result diagnostics
make reference-quality-check
make icml-evidence-check    # ICML-era retrospective analyses
make figures-check          # Figures and tables, without rewriting
make check                  # Ruff and the routine test suite
```

These commands make no generation requests and need no API key or model weights.
A Git checkout contains compact measurements, not image pixels; commands that
re-extract features or verify pixel hashes need the retained local archive.
The [analysis catalog](docs/ANALYSES.md) lists every replay command.

## Repository map

| Location | Purpose |
| --- | --- |
| [paper/](paper/README.md) | Manuscripts, bibliographies, figures and presentation builders |
| [src/latent_art_bench/](src/latent_art_bench/) | Versioned analysis code and shared measurement primitives |
| [studies/](studies/) | Protocols, fixed plans and methodological boundaries |
| [data/manifests/](data/manifests/) | Compact measured vectors, request records, hashes and receipts |
| [reports/](reports/README.md) | Numerical results, report plots, release receipts and review records |
| [tests/](tests/README.md) | Offline analysis and integrity checks |
| [scripts/](scripts/), [tools/](tools/) | Record audits, ICML checks, historical collectors and release adapters |
| [configs/](configs/README.md) | Executed study configurations |
| [docs/](docs/README.md) | Status, handover, analysis catalog and retention policy |
| [critics/](critics/ASSESSMENT.md), [literature_reviews/](literature_reviews/README.md) | 2026-09-13 external reviews; original literature base |

Historical protocols, source, results and local raw evidence are needed for
reproducibility and are bound by path and hash. Read the
[artifact policy](docs/ARTIFACTS.md) and [contributing guide](CONTRIBUTING.md)
before moving or deleting research files.

Earlier studies have [versioned public releases](https://github.com/isingmodel/latent-art-bench/releases);
the six-model experiment has not been released yet. Code is distributed under
[the repository license](LICENSE). Full-resolution artwork is not redistributed;
the paper includes four reduced reference examples with recorded public-domain
metadata.
