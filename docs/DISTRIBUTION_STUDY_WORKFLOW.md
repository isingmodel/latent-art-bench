# Controlled painter-distribution study workflow

The scientific contract is [MAIN.md](../studies/painter_distribution_study_v1/MAIN.md).
Consult [STATUS.md](STATUS.md) before executing any stage. A published terminal
receipt closes its stage permanently; validation commands read evidence without
replacing it. The $75 ceiling includes pilot charges, failures and bounded retries.

## Preparation and collection

Metadata, pilot, reference delivery, scientific design and all reference/development
measurement are complete. The unused sequential collector and two parallel censuses
are permanently terminal. The latter retain 100 original slot outcomes: 98 images,
one OAuth moderation refusal and one complete FLUX 502 failure with no reported cost.

The [bounded recovery](../studies/painter_distribution_study_v1/TRANSIENT_RECOVERY.md)
executes 908 unattempted original slots and one authorized technical retry of the
FLUX failure. It preserves the refused slot, all successes and the missing reported
cost, retaining a $5 contingency against the spending ceiling. Commit its new
source, tests, contract and predecessor evidence before preparing its create-once
freeze, then commit the freeze before dispatch:

This preparation is complete for the active recovery: source `94c602e`, execution
freeze `fb21593`. The preparation command below is a record of the completed step;
do not prepare the same freeze again.

```bash
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.recovery prepare
# Commit execution_freeze.json before running check or dispatching.
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.recovery check
```

Collection uses three workers, one active call per model route, and globally
staggered starts at least five seconds apart. Eight prospective UTC windows retain
separation across days. Calls spend credit; the `.env` key stays private. Run one
coordinator only:

```bash
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.recovery run --watch
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.recovery status
```

Without `--watch`, the collector executes currently due slots and returns while
waiting for a later window. It does not close the run merely because a window is
not due. A completed initial attempt is never sent again on resumption. The
prospective conditional retry has its own child census ID and source-linked
evidence. An unclassified unknown outcome/charge or a failure cluster stops further dispatch;
inspect the cause before a separately frozen successor, never alter a receipt.

## Measurement and analysis

The 70-work reference panel and all development scalers are already measured
and verified; never rerun them. Once the remaining-slot collection is complete,
bind all three terminal components into the combined collection receipt, then measure
the selected successful images. Each writing command is create-once:

```bash
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.recovery_results combine
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.recovery_results generated
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.recovery_results analysis
```

The primary scaler is unchanged. The 256-pixel and JPEG sensitivities each fit
their scaler on the same 221 historical development works, before new reference
or generated measurement. No model weights or learned encoders are needed.

Nonmutating reproducibility checks:

```bash
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.recovery_results analysis --check
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.recovery_results generated --check
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
