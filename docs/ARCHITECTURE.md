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
- `cli.py` is a thin Typer application that registers each census collector and each evidence or
  R0 artifact tool as a pass-through subcommand. It adds no behaviour of its own; every argument
  is parsed by the target module.
- `scripts/collect_pfg_v1_*.py` are the equivalent standalone adapters. These scripts are
  hash-bound frozen inputs of the freezes that authorized their censuses, so they are evidence
  and must not be edited. `scripts/verify_pfg_v1_evidence.py`,
  `scripts/render_pfg_v1_prompt_library.py`, `scripts/render_pfg_v1_content_lexicon.py`,
  `scripts/build_pfg_v1_exposure_denylist.py`, and `scripts/prescreen_pfg_v1_scene_support.py`
  are the adapters for the tools below; `scripts/collect_pfg_v1_cleveland_metadata.py` is the
  adapter for the Cleveland route.

## Shared package layers

Module paths in this table are relative to `src/latent_art_bench/`.

| Area | Main modules | Responsibility |
|---|---|---|
| Deterministic I/O | `io.py` | Canonical JSON/JSONL, hashing, and atomic writes |
| Evidence audit | `evidence.py` | Commit-bound verification of freezes, ledgers, and receipts; all git reads go through one `git cat-file --batch` per step |
| Retired contracts | `config.py`, `schemas.py` | Pilot-era pydantic contracts with no runtime consumer; retained only because the R0 freezes bind them |
| Census collectors | `painter_feature_generation_v1/` | Fail-closed source-route censuses |
| R0 artifact tools | `painter_feature_generation_v1/prompt_library.py`, `content_lexicon.py`, `exposure_denylist.py`, `scene_prescreen.py` | Deterministic, offline renderers of the §11.1 prompt library, the §7.4 content lexicon, the §8 exposure denylist, and the non-binding corpus pre-screen |

`panel.py` is the single source of the four-painter roster; `artifact_cli.py` is the shared
`--root/--check` command line of the R0 artifact renderers.

`io.py`, `config.py`, `schemas.py`, `pyproject.toml`, `uv.lock`, `.gitignore`,
`src/latent_art_bench/__init__.py`, and `tests/conftest.py` are bound by every census freeze.
Verification is commit-bound, so editing one of them no longer invalidates earlier evidence; the
terminal collectors and their frozen inputs are still left unmodified as policy.
`tests/conftest.py` carries an unused pilot-era fixture that points at a config which no longer
exists; it is kept only because the freezes bind it.

The collectors import `canonical_json` and `hash_file` from `io.py`. The AIC and broad-media
collectors additionally reuse private primitives from `federated_census.py` (event ledger, atomic
writes, response store, metadata parsing), and `broad_wikidata_retry.py` reuses
`broad_wikidata.py`. Route isolation is therefore a policy of separate configs, freezes, IDs, and
paths, not of zero shared code.

## The active study

The sole active research plan is `studies/painter_feature_generation_v1/PROTOCOL_2.1.md`,
protocol 2.1; `PROTOCOL.md` is the frozen 2.0 text that authorized the completed censuses. The
workflow is deliberately small and sequential:

1. `R0` exhausts the frozen metadata source registry and records candidates without image download
   or admission.
2. `R1` resolves authority, rights, physical-work identity, capture ancestry, and image quality and
   acquires lawful raw bytes under a separate authorization.
3. `R2` applies the frozen content lexicon to authority metadata (no human coding, no pixels),
   reserves independent-capture works, applies the exposure denylist, and assigns every new
   eligible work to development, qualification, or confirmation by the frozen hash rule.
4. `M0` qualifies color, spatial/orientation, and digital-texture measurements on development and
   auxiliary data only, then freezes scaling, margins, and whole-decision simulations.
5. `G0` freezes one exact model, the 16-template prompt census, paired seeds, request order,
   repetition count, the adherence classifier, and analysis.
6. `G1` records every generation attempt and output while confirmation feature data remain unopened.
7. `C0` opens the confirmation reference once and runs the frozen analysis.

The earlier equal 360-work quota, three-way real split, 24-template frame, entropy-projection
machinery, and (since 2.1) scene-group stratification and human coding are retired. R0 forms an
exhaustive authority/discovery/media union, reconciles it to physical works, and keeps actual
unequal painter counts. The real target is uniform over metadata-declared outdoor-place works.
Generation remains NO-GO unless each painter clears the screening floors (10 development, 10
qualification, and 100 confirmation works; the 60/12 auxiliary panel; workflow crossing) and the
actual design passes registered whole-decision simulation; these are not target-count stopping
rules.

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
| `census_engine.py` + `cleveland_metadata.py` | Cleveland Museum of Art route on the shared engine | config written; not prepared, reviewed, frozen, or executed |

Each module has a thin `scripts/collect_pfg_v1_*.py` CLI adapter with `prepare` and `execute`
subcommands and a matching test module under `tests/painter_feature_generation_v1/`. Every collector
writes exact request intents, raw response hashes, terminal receipts, and a non-admission candidate
manifest. None can download images, decide authority/content, create a physical-work population,
extract features, or run generation. The remaining named routes — Europeana, NGA, Cleveland, Yale,
Getty, Minneapolis, Paris Musées, and POP/Joconde — have no collector yet.

The terminal collectors are kept, not deleted. Each is a frozen input of the freeze that authorized
its run and of the successor freeze that binds its terminal evidence; removing one would make its
census unverifiable.

Three of the four routes terminated on their first run because the frozen parser rejected a valid
provider representation (a `languagefallback` term, a plural `errors` envelope, a string
`classification_id`), and each retry cost a ~1,300-line module copy. A future route should validate
only the fields its screen actually uses and retain everything else raw, so that an unfamiliar
representation is recorded rather than fatal.

## Evidence and R0 artifact tools

| Module | Command | Output |
|---|---|---|
| `evidence.py` | `latent-art-bench verify-evidence` | commit-bound audit of every freeze, event ledger, and execution receipt; exit 1 on any unacknowledged mismatch |
| `prompt_library.py` | `latent-art-bench prompt-library [--check]` | `data/manifests/painter_feature_generation_v1/prompt_library.json`, the exact §11.1 artifact |
| `content_lexicon.py` | `latent-art-bench content-lexicon [--check]` | `content_lexicon.json`, the §7.4 eligibility lexicon, plus the `classify` rule R2 will apply |
| `exposure_denylist.py` | `latent-art-bench exposure-denylist [--check]` | `exposure_denylist.jsonl` and its receipt, rebuilt from pinned git blobs |
| `scene_prescreen.py` | `latent-art-bench scene-prescreen` | non-binding corpus pre-screen JSON and Korean summary against the 2.1 floors |

None of these tools makes a network request or opens an image.

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

## Shared census engine

`painter_feature_generation_v1/census_engine.py` holds the machinery every collector copied:
config validation, exact intents, a commit-bound freeze, review and authorization seals, the
one-shot lock, the hash-chained ledger, the content-addressed response store, and atomic
publication. A route supplies a `RouteContract` with its endpoint, config validation, intent
builder, response parser/screen, duplicate key, sort key, and receipt summary;
`cleveland_metadata.py` is the reference consumer at about 300 lines.

The engine differs from the copied collectors in three deliberate ways: `prepare` writes the
freeze itself, records `recorded_git_commit`, and refuses to run when a tracked frozen input is
dirty against HEAD; the review seal must state `reviewer_kind` (`human` or `llm_subagent`); and a
route parser is expected to validate only the fields its screen uses and to retain everything
else raw, so an unfamiliar provider representation is recorded rather than fatal.

The seven existing collectors are not migrated. They are hash-bound evidence of what ran.

## Extension seams

New work belongs in a new versioned namespace, not in an edit to a sealed one. When adding a source
route:

- build it on `census_engine.RouteContract` rather than copying a collector; the isolation that
  matters is separate configs, census IDs, freezes, and paths, not duplicated transport code;
- keep the config, freeze, review, authorization, ledger, and publication paths disjoint from every
  existing census;
- add the matching test module and adapter script in the same change, because the freeze binds
  both;
- commit the config and code before `prepare`, and commit the intents and freeze immediately
  after, so `recorded_git_commit` verifies; and
- never reuse a census ID, and never repair a terminal census in place.
