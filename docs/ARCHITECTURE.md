# Architecture map

LatentArtBench is a small Python package built around one active study,
`painter_feature_generation_v1`. The package implements the R0 metadata-census stage only: it can
freeze, validate, execute, and publish source censuses, and it cannot download images, extract
features, or generate. This page describes the code as it exists; it is not authorization to run
the active study before its freezes.

Earlier exploratory namespaces were removed rather than kept as inactive code. What remains is
either hash-bound by a census freeze or directly supports one.

## Entry points

- The installed command is `latent-art-bench = latent_art_bench.cli:app`.
- `cli.py` is a thin Typer application that registers each census collector as a pass-through
  subcommand. It adds no behaviour of its own; every argument is parsed by the collector module.
- `scripts/collect_pfg_v1_*.py` are the equivalent standalone adapters. These scripts are
  hash-bound frozen inputs of the freezes that authorized their censuses, so they are evidence
  and must not be edited.

## Shared package layers

Module paths in this table are relative to `src/latent_art_bench/`.

| Area | Main modules | Responsibility |
|---|---|---|
| Deterministic I/O | `io.py` | Canonical JSON/JSONL, hashing, and atomic writes |
| Contracts | `config.py`, `schemas.py` | Shared configuration and validated record shapes |
| Census collectors | `painter_feature_generation_v1/` | Fail-closed source-route censuses |

`io.py`, `config.py`, and `schemas.py` are hash-bound frozen inputs of every census freeze. They
must stay byte-identical; a change to any of them invalidates the evidence chain of every census
already executed. The same applies to `pyproject.toml`, `uv.lock`, `.gitignore`,
`src/latent_art_bench/__init__.py`, and `tests/conftest.py`.

`canonical_json` from `io.py` is the only shared dependency the collectors import. Everything else
a collector needs — transport, screening, retention, publication — lives inside its own module, so
one route can never silently change another's behaviour.

## The active study

The sole active research plan is `studies/painter_feature_generation_v1/PROTOCOL.md`, protocol 2.0.
The workflow is deliberately small and sequential:

1. `R0` exhausts the frozen metadata source registry and records candidates without image download
   or admission.
2. `R1` resolves authority, rights, physical-work identity, capture ancestry, and image quality and
   acquires lawful raw bytes under a separate authorization.
3. `R2` double-codes masked eligibility derivatives, seals reliability/adjudication, reserves
   independent-capture works, and assigns every new eligible work to development, qualification, or
   confirmation by the frozen hash rule.
4. `M0` qualifies color, spatial/orientation, and digital-texture measurements on development and
   auxiliary data only, then freezes scaling, margins, and whole-decision simulations.
5. `G0` freezes one exact model, common-content prompt census, paired seeds, request order, repetition
   count, and analysis.
6. `G1` records every generation attempt and output while confirmation feature data remain unopened.
7. `C0` opens the confirmation reference once and runs the frozen analysis.

The earlier equal 360-work quota, three-way real split, 24-template frame, and entropy-projection
machinery are retired. R0 forms an exhaustive authority/discovery/media union, reconciles it to
physical works, and keeps actual unequal painter counts. At least three broad scene groups must be
supported by all painters. Each retained confirmation group receives equal target mass and each work
within group is uniform. Generation remains NO-GO unless each painter clears the role-specific
screening floors (10 development, 10 qualification, and 20 confirmation works per retained group;
confirmation ESS 100) and the actual design passes registered whole-decision simulation; these are
not target-count stopping rules.

## Census collectors

`src/latent_art_bench/painter_feature_generation_v1/` implements the R0 census stage. Each route
is a separate fail-closed collector with its own config, freeze, neutral review, authorization,
one-shot lock, hash-chained event ledger, content-addressed raw-response store, and atomic
publication. A route that fails terminates the census; the retry is always a new module and census
ID bound to the predecessor's terminal evidence, never an in-place repair.

| Module | Route | State |
|---|---|---|
| `federated_census.py` | fixed-seed Wikidata/Commons attrition audit, plus the shared census primitives the other collectors reuse | complete (165/165 requests) |
| `broad_wikidata.py` | broad exact-creator no-`P186` discovery census | terminal on provider HTTP 502 |
| `broad_wikidata_retry.py` | same census under a new ID after that terminal run | complete (4/4 requests) |
| `broad_media_followup.py` | entity/media metadata follow-up over the broad frame | terminal on an unrecognized plural `errors:[maxlag]` envelope |
| `broad_media_followup_r2.py` | same follow-up under a new ID | complete (182/182 requests) |
| `aic_metadata.py` | Art Institute of Chicago route census | terminal on a string `classification_id` |
| `aic_metadata_r2.py` | same route under a new ID | complete (4/4 requests) |

Each module has a thin `scripts/collect_pfg_v1_*.py` CLI adapter with `prepare` and `execute`
subcommands and a matching test module under `tests/painter_feature_generation_v1/`. Every collector
writes exact request intents, raw response hashes, terminal receipts, and a non-admission candidate
manifest. None can download images, decide authority/content, create a physical-work population,
extract features, or run generation. The remaining named routes — Europeana, NGA, Cleveland, Yale,
Getty, Minneapolis, Paris Musées, and POP/Joconde — have no collector yet.

The terminal collectors are kept, not deleted. Each is a frozen input of the freeze that authorized
its run and of the successor freeze that binds its terminal evidence; removing one would make its
census unverifiable.

## Data flow and gates

Within R0 a single route runs:

1. `prepare` reads the versioned config, emits exact request intents, and writes a freeze binding
   every frozen input by path and sha256;
2. an independent reviewer inspects the sealed freeze and records a decision with empty blocking
   findings;
3. an authorization seal binds the freeze and the review by path and sha256;
4. `execute --seal <path> --seal-sha256 <hash>` takes the one-shot lock, issues the frozen requests,
   stores every raw response in the content-addressed store, and appends a hash-chained event per
   step;
5. publication is atomic — the candidate manifest and execution receipt appear together or not at
   all.

Any transport failure, non-200, redirect, URL drift, `Retry-After`, schema/pagination/identity
violation, oversize response, or content-address drift terminates the census. There is no
within-census retry. Every later stage depends on an explicit earlier closure: a transport success
is not protocol eligibility, and a completed census is not an admitted corpus.

## Storage boundaries

- `configs/` — tracked study inputs; every file is a frozen input of some freeze.
- `data/manifests/` — tracked compact request intents, event ledgers, freezes, reviews,
  authorizations, candidate manifests, and execution receipts.
- `research_workspace/` — ignored raw responses, one-shot locks, and future image bytes, all under
  one boundary.
- `reports/` — tracked compact findings and evidence.
- `artifacts/` — ignored local research bytes retained outside git.

Large runtime state lives beneath one ignored workspace root; tracked study definitions and compact
evidence stay together in one versioned namespace.

## Extension seams

New work belongs in a new versioned namespace, not in an edit to a sealed one. When adding a source
route:

- copy the collector shape rather than generalizing across routes prematurely — the isolation is
  what keeps one route's failure from contaminating another's evidence;
- keep the config, freeze, review, authorization, ledger, and publication paths disjoint from every
  existing census;
- add the matching test module and adapter script in the same change; and
- never reuse a census ID, and never repair a terminal census in place.
