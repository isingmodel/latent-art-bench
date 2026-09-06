# Controlled painter-distribution study workflow

The scientific contract is [MAIN.md](../studies/painter_distribution_study_v1/MAIN.md).
Consult [STATUS.md](STATUS.md) before executing any stage. A published terminal
receipt closes its stage permanently; validation commands read evidence without
replacing it. The $75 ceiling includes pilot charges, failures and bounded retries.

## Preparation and collection

The metadata and technical pilot stages are complete and must not be rerun.
For the not-yet-created main design, commit all code, tests, contracts, annotation
and qualification inputs, prepare the freeze, then commit its four inventory/
freeze files before dispatch. Preparation is create-once:

```bash
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.study prepare
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.study check
```

Collection uses the committed earliest UTC window times and actual provider calls.
It spends credit. The `.env` key stays private. Run one collector only:

```bash
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.collection run --watch
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.collection status
```

Without `--watch`, the collector executes currently due slots and returns while
waiting for a later window. It does not close the run merely because a window is
not due. A completed initial attempt is never sent again on resumption. The
prospective conditional retry has its own child census ID and source-linked
evidence. An unknown outcome/charge or a failure cluster stops further dispatch;
inspect the cause before a separately frozen successor, never alter a receipt.

## Measurement and analysis

After the main freeze is committed, process development and references. Generated
measurement requires a terminal collection receipt. All three stages retain their
failures and source hashes. Each command writes once:

```bash
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.measurement development
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.measurement reference
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.measurement generated
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.analysis build
```

The primary scaler is unchanged. The 256-pixel and JPEG sensitivities each fit
their scaler on the same 221 historical development works, before new reference
or generated measurement. No model weights or learned encoders are needed.

Nonmutating reproducibility checks:

```bash
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.analysis check
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.measurement generated --check
```

The analysis check replays numeric results. The measurement check reopens retained
raw images and recomputes their features; it makes no provider request. The same
flag works for development/reference stages. Raw image bytes are ignored local
evidence and must be archived separately from Git; see [ARTIFACTS.md](ARTIFACTS.md).

## Validation and writing

```bash
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
uv run --locked latent-art-bench verify-evidence
```

The [paper prototype](../papers/painter_distribution_study_v1/README.md) has separate
build instructions. Figures use measured numerical evidence, and the manuscript
must label pending collection/results rather than inventing a complete study.
