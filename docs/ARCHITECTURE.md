# Architecture map

LatentArtBench is a Python package with shared measurement primitives and three accumulated
pilot-specific workflow layers. The scientific workflows are deliberately fail-closed, but
their historical growth has concentrated too many responsibilities in a few modules. This
page describes the code as it exists; it is not authorization to resume a closed pilot.

## Entry points

- The installed command is `latent-art-bench = latent_art_bench.cli:app`.
- `python -m latent_art_bench` invokes the same Typer application.
- The root CLI contains historical Pilot 0/1 commands and mounts the `pilot2` and `pilot3`
  subcommand groups.
- Root-command defaults still point at `configs/pilot_0/pilot.yaml`; this is legacy behavior,
  not the current project stage.

## Shared package layers

| Area | Main modules | Responsibility |
|---|---|---|
| Deterministic I/O | `io.py`, `provenance.py`, `manifests.py` | Canonical JSON/JSONL, hashing, atomic writes, and provenance |
| Contracts | `config.py`, `schemas.py`, `evaluation/contracts.py` | Shared configuration and validated record shapes |
| Corpus | `data/corpus.py`, `data/museums.py` | Museum metadata, selection, acquisition, and leakage checks |
| Preprocessing | `preprocessing/` | Deterministic common image views and synthetic fixtures |
| Features | `features/` | Chromatic and learned-formal extraction pipelines |
| Evaluation | `evaluation/` | Distances, real-only qualification, frozen transforms, and analysis cells |
| Generation | `generation/` | Image-request records, output validation, and attestation |
| Reporting | `reporting/` | Compact pilot reports |

The reusable core is real, but it is not yet a clean independent library. Several shared
modules retain Pilot 0/1 assumptions, and Pilot 3 imports Pilot 2 preprocessing, learned-formal,
schema, and transport helpers.

## Versioned workflow layers

### Pilot 2

`src/latent_art_bench/pilot2/` is a mostly self-contained historical requested-label study.
It owns its config, schemas, corpus projection, qualification, transport, generation,
analysis, and reporting. Its durable 320-attempt recovery receipts and compact result evidence
are intentionally committed.

### Pilot 3

`src/latent_art_bench/pilot3/` is the latest and largest workflow:

| Module | Role |
|---|---|
| `planning.py`, `corpus.py`, `design.py` | Offline planning and Freeze-A1 corpus/design evidence |
| `phasea.py` | Development acquisition, normalization, A-vectors, repeat probes, fitting, and external validation |
| `preprocessing.py` | Pilot 3 metadata-free PNG normalization contract |
| `met_r2.py` | Isolated official-Met successor protocol; now closed on its first metadata failure |
| `design_freeze.py`, `normalization_scope.py` | Later-phase memberships and gates |
| `transport.py` | OAuth runtime and requested-label qualification |
| `generation.py` | Frozen schedule, durable request/attempt ledgers, output validation, recovery, and generation completion |
| `analysis.py`, `execution.py` | Analysis, generated-output measurement, cross-phase orchestration, and verification |
| `cli.py` | Pilot 3 command adapters |

The largest maintenance hotspots are `phasea.py`, `generation.py`, and `execution.py`. A
software reboot should split these by responsibility only after preserving the historical
implementation at its current commit or tag.

## Data flow and gates

The intended scientific flow is:

1. versioned config and compact manifests;
2. append-only request/acquisition evidence and content-addressed local bytes;
3. deterministic normalization;
4. feature extraction;
5. real-only qualification and frozen transforms;
6. sealed external validation;
7. generation-transport qualification;
8. frozen generation, measurement, analysis, and reporting.

Every later step depends on an explicit earlier closure. A transport success is not the same
as protocol eligibility, and an executed study is not the same as a supported hypothesis.
Pilot 3 stopped while completing the development-acquisition cohort: all AIC acquisition and
normalization finished, but the Met R2 path closed before the Met half could be acquired. No
full-cohort feature extraction or later gate is open.

## Storage boundaries

Historical storage spans five roots:

- `configs/` — tracked study inputs;
- `data/` — ignored media plus selectively tracked manifests;
- `artifacts/` — ignored local CAS/vector/model state plus selectively tracked receipts;
- `outputs/` — ignored generated images and run outputs; and
- `reports/` — tracked compact findings and evidence.

This overlap is a compatibility constraint, not a recommended design. New work should put all
large runtime state beneath one ignored workspace root and keep tracked study definitions and
compact evidence together in one versioned namespace.

## Safe reboot seams

A software-first reboot can initially preserve behavior while extracting:

- deterministic JSON/JSONL and hashing utilities;
- content-addressed storage and portable path handling;
- normalization as a standalone contract;
- learned-formal extraction behind a pilot-neutral interface; and
- append-only request journals independent of a particular transport.

Do not start by moving historical files or deleting pilot code. Paths and implementation
hashes are part of the evidence. Create a new namespace, add characterization tests around the
shared seam, and retire old entry points only after the historical commit remains accessible.
