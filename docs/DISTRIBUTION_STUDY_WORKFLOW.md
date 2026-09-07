# Controlled painter-distribution study workflow

The scientific contract is [MAIN.md](../studies/painter_distribution_study_v1/MAIN.md).
Consult [STATUS.md](STATUS.md) before executing any stage. A published terminal
receipt closes its stage permanently; validation commands read evidence without
replacing it. The $75 ceiling includes pilot charges, failures and bounded retries.

## Completed collection

All collection censuses are permanently terminal. The fixed 1,008-slot inventory
contains 1,006 selected images, two OAuth moderation refusals and one successful
bounded FLUX technical retry. Including the 18-image pilot, there were 1,027
physical attempts (589 paid). Reported charges are $40.6819185; a retained $5
failed-call contingency gives conservative accounting of $45.6819185.

The user-requested immediate successor completed untouched batches 4–7 on
September 7, 00:29:19–02:01:37 UTC, with peak concurrency three, one active call
per route and starts at least 5.043739 seconds apart. The original 33-hour schedule
was not executed in full. All four components retain their ledgers and terminal
receipts. Their combined fixed-slot view preserves the original failures and sole
bound retry; never restart a collector or regenerate an existing slot.

The scientific contract, execution amendments and immutable input freezes remain
in the study namespace. Current status is readable without making provider calls:

```bash
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.immediate status
```

## Measurement and analysis

The 70-work reference panel, all development scalers and 1,006 selected generated
images are measured. Generated measurement contains 3,018 successful vectors and
no duplicate raw hashes. Measurement writing commands are permanently terminal.
The original analysis publisher failed before creating a file because NumPy
Boolean decision flags are not native JSON values. Its scientific calculation is
unchanged. The [publication correction](../studies/painter_distribution_study_v1/ANALYSIS_PUBLICATION.md)
binds a new adapter and completed inputs, converts only those flags with exact
value equality, and writes analysis in `pdsv1-analysis-20260907`.

Analysis publication is complete (source/inputs `200b21b`, freeze `4e70d29`).
The following was its create-once publication command; use `check` below for reproduction:

```bash
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.analysis_publication build
```

The primary scaler is unchanged. The 256-pixel and JPEG sensitivities each fit
their scaler on the same 221 historical development works, before new reference
or generated measurement. No model weights or learned encoders are needed.

Nonmutating reproducibility checks:

```bash
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.analysis_publication check
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.immediate_results generated --check
```

The analysis check replays numeric results. The measurement check reopens retained
raw images and recomputes their features; it makes no provider request. The same
reference replay remains `parallel_results reference --check`. Completed development replays through
its original `measurement development --check` command. Raw image bytes are ignored local
evidence and must be archived separately from Git; see [ARTIFACTS.md](ARTIFACTS.md).

## Final comparison report

The completed report binds renderer and numeric inputs at `383228c`. All 22 output
files reproduce byte-for-byte. Publication was create-once; do not run `build` again:

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
reports the actual completed study and explicitly retains all interpretation limits.
