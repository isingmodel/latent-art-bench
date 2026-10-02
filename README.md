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
analyses, open decisions and limits.

## Manuscripts

| Manuscript | Source | Scope |
| --- | --- | --- |
| TMLR submission (lead) | [paper/tmlr/main.tex](paper/tmlr/main.tex) | Anonymous TMLR-format manuscript: the shared/between-name decomposition, learned embeddings, readout disagreement and the SD-Turbo check; its PDF is built locally with `make paper-tmlr` |
| Korean translation of the TMLR manuscript | [paper/tmlr_ko/main.tex](paper/tmlr_ko/main.tex) | Same content, tables and figures as the TMLR manuscript; built locally with `make paper-tmlr-ko` |
| Full-length paper (frozen) | [paper/archive/full_length_2026-09-15/paper.tex](paper/archive/full_length_2026-09-15/paper.tex), [PDF](paper/archive/full_length_2026-09-15/paper.pdf) | 23-page version of 2026-09-15, without the later retrospective analyses |
| Korean translation (frozen) | [paper/archive/full_length_2026-09-15/latent_art_bench_korean.tex](paper/archive/full_length_2026-09-15/latent_art_bench_korean.tex) | Translation of the full-length paper |

The [paper guide](paper/README.md) explains the layout and builds.

## Reproduce

Use the recorded **Python 3.13.11** runtime and `uv`. The package metadata's
broader Python floor does not qualify every frozen study on older interpreters.

```bash
uv sync --locked --extra analysis --extra dev --inexact
make install-hooks         # Reject staged files over GitHub's 100 MiB limit
make restore-analysis      # Extract and checksum-verify the frozen transfer result
make specificity-check      # Primary numerical results
make review-check           # Post-result diagnostics
make reference-quality-check
make retrospective-check    # Retrospective analyses (direct naming, timing, learned, transfer, covariance)
make tmlr-check             # TMLR tables, figure and every number quoted in its text
make figures-check          # Retained palette figure against its replay
make check                  # Ruff and the routine test suite
```

These commands make no generation requests and need no API key or model weights.
The frozen transfer result is stored as a lossless `analysis.json.gz` archive.
`make restore-analysis` restores its original path and bytes without changing
any scientific hashes; `make retrospective-check` and `make tmlr-check` run this step automatically.
Run it before invoking the transfer Python scripts or numerical bundle tools directly.
A Git checkout contains compact measurements, not image pixels; commands that
re-extract features or verify pixel hashes need the retained local archive.
The [analysis catalog](docs/ANALYSES.md) lists every replay command.

## Repository map

| Location | Purpose |
| --- | --- |
| [paper/](paper/README.md) | TMLR manuscript with its asset builder, and the frozen earlier manuscripts |
| [src/latent_art_bench/](src/latent_art_bench/) | Versioned analysis code and shared measurement primitives |
| [studies/](studies/) | Protocols, fixed plans and methodological boundaries |
| [data/manifests/](data/manifests/) | Compact measured vectors, request records, hashes and receipts |
| [reports/](reports/README.md) | Numerical results, report plots, release receipts and review records |
| [tests/](tests/README.md) | Offline analysis and integrity checks |
| [scripts/](scripts/), [tools/](tools/) | Record audits, artifact checks, historical collectors and release adapters |
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
