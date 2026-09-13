# Architecture

LatentArtBench separates versioned scientific computation from manuscript
presentation. The current experiment compares six image models with four
painters using 31 interpretable features. Earlier experiments provide separate
controls and supporting evidence; their observations are not pooled into the
current model comparison.

## Current data flow

```text
studies/ + configs/                 fixed scientific design and settings
data/manifests/                     retained vectors, requests, hashes, receipts
    |
    +-- painter_specificity_measurement_v1/workflow.py
    |     corrected reader: 649 reference works + 1,008 generated images
    |     painter_specificity_v2/analysis.py: primary comparisons
    |     four views: full/square x pooled/content-weighted references
    |
    +-- painter_specificity_review_v1.py
          post-result scene, calibration, artist-pair and reference diagnostics
    |
    v
saved numerical results             original results remain unchanged
    |
paper/make_specificity_*.py          primary figures and tables
paper/make_review_figures.py         diagnostic tables and example panels
    |
paper/paper.tex -> paper/paper.pdf
```

Scaling uses 221 separate development works. The historical feature definitions
remain in [features.py](../src/latent_art_bench/painter_feature_generation_v2/features.py).
The [analysis catalog](ANALYSES.md) lists the exact entry points for current and
supporting numerical checks and renderers.

## Storage and responsibilities

| Location | Responsibility |
| --- | --- |
| [src/latent_art_bench/](../src/latent_art_bench/) | Scientific calculation, data readers, historical collection implementations |
| [studies/](../studies/), [configs/](../configs/) | Protocols, fixed plans and configuration |
| [data/manifests/](../data/manifests/) | Compact measurements, assignments, provenance and result bindings |
| [reports/](../reports/README.md) | Numerical outputs, complete report tables/plots and release receipts |
| [paper/](../paper/README.md) | Editable manuscript and presentation from retained results |
| [tests/](../tests/README.md) | Offline scientific and integrity checks |
| `research_workspace/` | Ignored raw artwork, generated images and transport records |

Normal figure builds use committed numerical inputs; example panels reuse
committed PDFs. Explicit image-panel replay and raw-byte audits additionally
read the ignored archive. Numerical replay makes no generation requests.

Older modules remain because later analyses import their measurement,
randomization and provenance primitives, and completed studies bind their source
paths and bytes. Collection code is retained to document execution; it is not
called by Makefile replay targets. Changing a numerical method requires a new
result version when its existing output is sealed. See
[CONTRIBUTING.md](../CONTRIBUTING.md) and [ARTIFACTS.md](ARTIFACTS.md).
