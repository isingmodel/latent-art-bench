# Controlled painter-distribution study workflow

The scientific contract is [MAIN.md](../studies/painter_distribution_study_v1/MAIN.md).
Consult [STATUS.md](STATUS.md) before executing any stage. A published terminal
receipt closes its stage permanently; validation commands read evidence without
replacing it. The $75 ceiling includes pilot charges, failures and bounded retries.

## Preparation and collection

Metadata, pilot, reference delivery, scientific design and all reference/development
measurement are complete. The unused sequential collector and three subsequent
collection censuses are permanently closed. The three components retain 504 original
slot identities: 503 selected images and one OAuth refusal, including one successful
technical retry whose original complete FLUX failure retains a $5 contingency.

The user requested the remaining generation immediately. The
[immediate collection amendment](../studies/painter_distribution_study_v1/IMMEDIATE_COLLECTION.md)
executes exactly the 504 untouched original slots in batches 4–7, consecutively.
Keep three workers, one active call per route, globally staggered starts at least
five seconds apart and a five-second pause between completed batches. Original
window IDs and planned times remain evidence; actual times define the executed span.
The $75 cap and qualified retry, uncertainty and failure-cluster rules remain.

Commit the new source, tests, contract and closed predecessor evidence before the
create-once preparation step, then commit its execution freeze before dispatch:

This preparation is complete: source `6697108`, execution freeze `d0f8170`.
Do not repeat `prepare` or start a second coordinator while the existing run is live.

```bash
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.immediate prepare
# Commit execution_freeze.json before running check or dispatching.
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.immediate check
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.immediate run
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.immediate status
```

Run only one coordinator. It completes all remaining batches without scheduled
night waits. A completed initial attempt is never sent again on resumption; a
conditional technical retry has its own child identity and source-linked evidence.
An unclassified outcome/charge or failure cluster stops dispatch for diagnosis.
Never restart any census that already has a terminal generation receipt.

## Measurement and analysis

The 70-work reference panel and all development scalers are already measured
and verified; never rerun them. Once the remaining-slot collection is complete,
bind all four terminal components into the combined collection receipt, then measure
the selected successful images. Each writing command is create-once:

```bash
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.immediate_results combine
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.immediate_results generated
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.immediate_results analysis
```

The primary scaler is unchanged. The 256-pixel and JPEG sensitivities each fit
their scaler on the same 221 historical development works, before new reference
or generated measurement. No model weights or learned encoders are needed.

Nonmutating reproducibility checks:

```bash
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.immediate_results analysis --check
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.immediate_results generated --check
```

The analysis check replays numeric results. The measurement check reopens retained
raw images and recomputes their features; it makes no provider request. The same
reference replay remains `parallel_results reference --check`. Completed development replays through
its original `measurement development --check` command. Raw image bytes are ignored local
evidence and must be archived separately from Git; see [ARTIFACTS.md](ARTIFACTS.md).

## Final comparison report

After terminal generation and verified numeric analysis, commit the measurement,
analysis and renderer inputs, then publish the report once:

```bash
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.main_report build
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.main_report check
```

The report exports full-precision tables, every PCA point, classifier membership,
paired contributions, availability, transport timing/settings and descriptive
sensitivity figures. The report check re-renders every output in temporary storage
and compares file hashes without changing the published bundle.

## Validation and writing

```bash
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
uv run --locked latent-art-bench verify-evidence
```

The [paper prototype](../papers/painter_distribution_study_v1/README.md) has separate
build instructions. Figures use measured numerical evidence, and the manuscript
must label pending collection/results rather than inventing a complete study.
