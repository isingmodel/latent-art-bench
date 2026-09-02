# Architecture map

LatentArtBench is a Python package with shared measurement primitives and three accumulated
pilot-specific workflow layers. The active `painter_feature_generation_v1` reboot currently has a
research protocol and compact metadata evidence, not an executable workflow layer. The historical
scientific workflows are deliberately fail-closed, but their growth concentrated too many
responsibilities in a few modules. This page describes the code as it exists; it is not
authorization to resume a closed pilot or to run the active study before its freezes.

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

### Painter Feature Generation v1

The sole active research plan is
`studies/painter_feature_generation_v1/PROTOCOL.md`. No active CLI, feature implementation,
admitted/downloaded corpus, registered generation request, generated output, or result exists;
R0a is NO-GO. Protocol 1.7 stages its future
workflow as R0a census, complete 1,440-work internal-frame acquisition, painter-level exposure-role
assignment, 12-candidate-frame/selected-24-template freeze, complete-population `q*` freeze, and
auxiliary independent-capture census; R1a measurement of the complete development population and
whole-decision simulation; R0b release of the complete qualification census without population
expansion; R1b untouched real-only qualification; G0 exact generator freeze; G1a
generation/output seal; and G1b one-time complete sealed-confirmation-census analysis. Every real
population is measured as a census; only generator-side units under a G0-frozen independence
partition are resampled for continuous-endpoint uncertainty. All 12 prompt candidates are byte-exact and hash-complete before
active content labels, and G0 can verify but not rewrite the selected frame. Deterministic seed lists
are independent template-specific IID uniform draws with replacement only for a fixed deterministic
local execution map; local inference resamples whole seed-condition vectors within template. An
opaque/remote endpoint instead uses `C` equal-size common-shock units, each with `L` complete
template×condition waves and `R=C*L`, and resamples whole units only. Rates use separately
alpha-allocated weighted-Hoeffding/ratio bounds rather than empirical-bootstrap quantiles; a full
endpoint contributes four directional events (`A` lower, `A` upper, `J` lower, `K` upper) to
`M_rate`. The same G0 partition governs both endpoint families: the rate bound uses `sum_c W_c^2`, and
plausible remote provider/batch/backend/moderation/outage/retry common shocks must share a unit.
Request IDs or timestamps alone are not independence evidence; a crossed shock, unusable balanced
unit, or partition not aligned with fixed-template resampling makes both affected rate and continuous
endpoints ineligible or inconclusive. R1a stress-tests clustered pixel/feature failures. New
implementation should live in this new
namespace and reuse a shared primitive only after its contract is characterized; it must not mutate
Pilot 0–3 behavior to make the reboot convenient.

The real frame uses four broad scene groups and five visible-property contrasts. Its complete
internal populations contain 360 works per painter (1,440 total); optional external replication
adds 96 per painter (384 total), raising the acquired and analyzed total to at least 1,824. The
separate at-least-32-work independent-capture census is outside both totals.

R0a also preserves the pre-adjudication coding receipt: three-way visual-eligibility agreement must
reach 0.90 per painter and each coder's ambiguous share must not exceed 0.10; on union-eligible and
assigned-population denominators, broad-scene and all five three-state contrasts must reach 0.85 and
each coder's season/illumination/depth indeterminate share must not exceed 0.20. Adjudication cannot
erase a failure. G1b independently double-codes every sealed-confirmation and technically analyzable
generated image, seals condition-scoped 0.85/0.20 receipts, and only then creates third-coder
consensus; a failed receipt makes the affected endpoint inconclusive. R1a uses one equal-painter
`q*`-weighted pooled-development median/IQR transform, validates full-frame unweighted-only and
assigned-population unweighted/`q*` source-share caps, the exact source-versus-complement median-
shift RMS gate, and `1/(24 m_t)` generated-quantile weights, and treats any nonstructural zero
replicate variance as inconclusive.

The active four-painter request formula is `120R`, with equal named/control `R` in every template.
The former `R=16`/1,920-request capacity is retired because it cannot clear the boundary-safe
availability gate. Even the impossible best case requires `R>=25` and at least 3,000 requests; R1a
must treat that floor as assuming one auditable independent unit per repetition and freeze the actual
larger `R` from the endpoint inventory, independence-unit audit, and whole-decision simulation before
G0. No request count is currently registered or authorized.

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

The historical Pilot 3 scientific flow was:

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
