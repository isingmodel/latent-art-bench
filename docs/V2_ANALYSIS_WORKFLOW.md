# V2 empirical analysis workflow

This is operational guidance, not a new protocol. The immediate deliverable is a Markdown
analysis report, not a manuscript. The authority is Protocol 1.0 with amendments 1.1–1.3;
[current status](STATUS.md) distinguishes terminal stages from running work.

## Existing runs

| Evidence | Namespace | Purpose |
| --- | --- | --- |
| Frame | `pfg2-frame-20260905` | 1,193 identities with prospective roles |
| SD-Turbo | `pfg2-sd-turbo-20260905` | Complete 25-block / 2,000-image baseline |
| OAuth pilot | `pfg2-oauth-pilot-20260905` | One full 80-image grid per requested alias |
| Corrected rendering acquisition | `pfg2-renderings-r2-20260905` | Disjoint acquisition of the whole fixed frame |
| Calibration | `pfg2-calibration-20260905` | Known synthetic populations; 100 trials per scenario |

Terminal runs never resume. Do not regenerate, top up, splice earlier successes, refresh hashes,
or overwrite results. Keep all ignored raw bytes and credentials outside tracked artifacts.
The proxy performs ordinary Codex OAuth credential handling; research clients never print or
copy tokens. No public paid-API fallback is part of this study.

## Gates

1. Complete real acquisition and commit its full terminal ledger, manifest and receipt.
2. Commit the exact tested method code and calibration. `prepare-method` binds these, the frame,
   acquisition, protocols, lockfile and both prospective generation freezes at the recording commit.
3. Measure development, freeze its equal-painter new-development scaler, then measure qualification.
   Historical development is measured for diagnostics but never fitted into the scaler. Invalid
   development IQR blocks subsequent measurement; no coordinate is silently dropped.
4. Commit development, qualification, scaling, and **both** generation terminal outputs. The first
   confirmation/generated measurement publishes the one-time common confirmation opening. Each
   subsequent raw read has an access event. A failed grid gets availability reporting, not fidelity
   results from its successful prefix.
5. Measure confirmation and each complete generated grid. Compute the SD-Turbo repeated-block
   analysis and the common finite descriptive comparisons.
6. Measure all primary-success images uncropped and uniformly 1% cropped at 496 pixels. Both
   branches use the uncropped-496 new-development scaler. Preserve full paired accounting.
7. Commit numeric results and the report renderer, then render the report and audit all evidence.

One OS lock serializes measurement stages. Three frozen worker threads perform the image
calculations, while the main writer preserves registered record order. Interrupted nonterminal
measurement can continue from already recorded rows with unchanged inputs; a terminal stage
cannot run again. No image-generation request is rerolled by measurement resumption.

## Commands

The examples use `NEW_METHOD_ID` to avoid inviting an in-place retry of sealed evidence.
Run only the next authorized stage, and commit the exact required inputs before each freeze.

```bash
uv run --locked --extra analysis --extra learned latent-art-bench paper-study -- --help
uv run --locked --extra analysis --extra learned latent-art-bench paper-study prepare-method \
  --method-id NEW_METHOD_ID --frame-id pfg2-frame-20260905 \
  --acquisition-id pfg2-renderings-r2-20260905 \
  --experiment-id pfg2-sd-turbo-20260905 --experiment-id pfg2-oauth-pilot-20260905 \
  --calibration-id pfg2-calibration-20260905
uv run --locked --extra analysis --extra learned latent-art-bench paper-study measure \
  --method-id NEW_METHOD_ID --stage development
uv run --locked --extra analysis --extra learned latent-art-bench paper-study measure \
  --method-id NEW_METHOD_ID --stage qualification
```

After the confirmation gate, use `measure --stage confirmation`, then `measure --stage generated
--experiment-id EXPERIMENT_ID` for each complete grid. `analyze --method-id NEW_METHOD_ID
--experiment-id pfg2-sd-turbo-20260905` computes the repeated analysis. `empirical`, `robustness`
and `report` each require `--method-id NEW_METHOD_ID`. The report refuses to omit the registered
SD-Turbo repeated analysis when its complete comparison is available.

The `paper-study` command name is retained for compatibility; it does not request a manuscript.
The extra `--` forwards help to the detailed stage parser instead of the outer CLI wrapper.

```bash
uv run --locked --extra analysis --extra learned ruff check .
uv run --locked --extra analysis --extra learned pytest -q -m "not live"
uv run --locked --extra analysis --extra learned latent-art-bench verify-evidence
uv run --locked --extra analysis --extra learned latent-art-bench paper-study audit
```

The standard suite is offline. Preserve both extras while generation is running, so environment
synchronization does not remove its dependencies. The audits are read-only and verify retained
bytes as well as compact hashes. V1's two historical acknowledgements are unchanged.

## Interpretation

The report separates finite V-statistic descriptions from SD-Turbo's generator U-estimator.
It does not rank models with unequal sample sizes or treat requested OAuth aliases as verified
weight snapshots. The synthetic shift scenario attained 86% joint nondegenerate-endpoint coverage;
nominal 95% intervals are therefore exploratory, not validated error guarantees. Crops are dependent
captures. Independent-capture calibration and justified equivalence margins remain absent, so no
positive reproduction claim is licensed by a favorable contrast or a nonsignificant difference.
