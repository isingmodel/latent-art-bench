# LatentArtBench

LatentArtBench is a research codebase for testing whether generated images reproduce
measurable distributions associated with artists, rather than only recognizable visual
prototypes. It combines deterministic preprocessing, hand-designed and learned image
features, real-only qualification gates, provenance checks, and frozen study workflows.

> **Reboot status (2026-09-01):** the Pilot 3 official-Met R2 cohort closed at its first
> metadata request. That request returned HTTP 403 and the prospective R2 protocol forbids
> retry or fallback after a terminal protocol failure. As a reboot governance decision, this
> baseline freezes Pilots 0–3 as history and requires further work to use a new versioned
> namespace. See [current status](docs/STATUS.md) before changing code or running a workflow.

## Current disposition

| Study | Disposition | Canonical record |
|---|---|---|
| Pilot 0 | Historical qualification attempt; failed | [Pilot 0 report](reports/pilot_0/REPORT.md) |
| Pilot 1 | Engineering traversal complete; scientific gate closed | [Pilot 1 report](reports/pilot_1/REPORT.md) |
| Pilot 2 | Execution complete; primary tests not run because both requested-label feature-pair grids were incomplete; decision `REDESIGN` | [Pilot 2 report](reports/pilot_2/REPORT.md) |
| Pilot 3 | Freeze A1 complete; 20 AIC development works acquired; Met R2 cohort closed on HTTP 403 before Met image acquisition | [Reboot status](docs/STATUS.md) |
| Painter Features v1 | Standalone method protocol complete; execution freeze not created; no empirical operation authorized | [Canonical measurement protocol](studies/painter_features_v1/MEASUREMENT_PROTOCOL.md) |

No Pilot 3 development A-vectors, repeat probes, external-holdout access, image-generation
transport qualification, or analytic generation exist.

## Start here

Read these in order:

1. [Current status and reboot boundary](docs/STATUS.md)
2. [Canonical Painter Features v1 measurement protocol](studies/painter_features_v1/MEASUREMENT_PROTOCOL.md)
3. [Architecture map](docs/ARCHITECTURE.md)
4. [Documentation index](docs/INDEX.md)
5. [Artifact retention policy](docs/ARTIFACTS.md)
6. [Agent guidance](AGENTS.md)

The canonical Painter Features v1 protocol is the active research plan. The older
[research proposal](docs/RESEARCH_PROPOSAL.md), frozen protocols, and historical result files are
background or evidence snapshots, not alternative current plans.

## Development setup

The project declares Python 3.9 or newer and requires `uv`; install `uv` with your platform's
package manager or its official installer before setup. The complete learned feature stack is
large. This reboot baseline was validated with CPython 3.13.11 on macOS arm64.

```bash
uv sync --locked --extra dev --extra learned
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
```

At the reboot baseline, Ruff passes and the offline suite contains 490 passing tests. The
standard command excludes the registered `live` marker. Tests use fixtures and injected
transports; they do not authorize live image, museum, browser, or API requests.

The historical `pilot2 verify` and planning-era `pilot3 verify` commands are not general
repository health checks on current `main`. Both correctly reject current implementation
drift from their older hash-bound closures. Do not regenerate a frozen bundle merely to make
one of those commands green.

## Repository map

| Path | Role |
|---|---|
| `src/latent_art_bench/` | Shared library, root CLI, and versioned pilot implementations |
| `tests/` | Unit, integration, and pilot-specific offline tests |
| `configs/` | Versioned study inputs; see [config index](configs/README.md) |
| `studies/` | Versioned reboot studies; each active study names one canonical plan |
| `docs/` | Mutable indexes/status plus frozen protocols and method references |
| `reports/` | Compact study results and committed evidence |
| `data/manifests/` | Compact tracked manifests; each record retains its own rights boundary |
| `artifacts/` | Mixed historical receipts and ignored local research bytes |
| `outputs/` | Ignored generated media and run outputs |
| `scripts/` | Narrow legacy import/render/metadata utilities |

The command-line entry points are:

```bash
uv run --locked latent-art-bench --help
uv run --locked latent-art-bench pilot2 --help
uv run --locked latent-art-bench pilot3 --help
```

The root command group still exposes historical Pilot 0/1 commands. Their presence does not
make them the active workflow.

## Artifact model

Git tracks source, tests, configuration, compact evidence, durable Pilot 2 attempt receipts,
and downsampled Pilot 2 visual-QC sheets. It intentionally ignores copyrighted artwork,
generated full-resolution images, model weights, source checkouts, derived images, feature
vectors, caches, and runtime locks.

Some ignored files are unique local evidence required by historical offline verification.
Never run broad cleanup commands such as `git clean -xfd`, and never recursively remove
`artifacts/`, `data/`, or `outputs/`. Follow the [artifact retention policy](docs/ARTIFACTS.md).

## Reboot rule

Treat Pilots 0–3 as immutable study history. A reboot may reuse well-tested shared primitives,
but it should define a new namespace, a small explicit objective, repository-relative
provenance, and a clean separation between tracked evidence and ignored workspace bytes.
Network access, external-holdout access, and generation remain closed unless a new prospective
protocol explicitly authorizes them. For the active reboot, use only the
[Painter Features v1 measurement protocol](studies/painter_features_v1/MEASUREMENT_PROTOCOL.md);
its [`old/` archive](studies/painter_features_v1/old/) is noncanonical.

## License

Code and documentation are released under the [MIT License](LICENSE). Artwork, model weights,
generated outputs, museum metadata, and third-party source material retain their own rights
and are not relicensed by this repository.
