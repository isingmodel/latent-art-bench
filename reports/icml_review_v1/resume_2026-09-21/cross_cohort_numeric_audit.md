# Retrospective cross-cohort numerical audit

Status: **passed**.

This is a separate computational replay of retained, previously analyzed SD-Turbo images. It is not independent scientific validation or prospective replication. The same four painters and exposed historical target remain in use. No p-values or confidence intervals are calculated.

## Verification

- Frozen input SHA-256: `94413b3ee5bd689f60df35e7a8135f79eb929fd9dbee36bd450b47df4db0e693`.
- Frozen analysis SHA-256: `9488dfafa5779b8b065cc756804e67ad64c2841a5c62c2f9b0105f8fef13973e`.
- All 47 frozen source bindings match.
- Original image file hashes match for 2,000 SD-Turbo outputs, 649 historical works, and 1,008 main-experiment images. Main/SD-Turbo hash overlap is zero.
- Reconstructed the complete 25-block × 16-scene × 5-arm × 31-coordinate array from raw retained rows. Verified exact cells, names, normalization, painter membership, fixed 221-work scaler, prompt insertion, and 400 paired HMAC seeds.
- Recomputed all four families, pooled and within-scene summaries, all 16 scene records, six painter pairs per family, all 25 block deletions (K=24), and all 56 sensitivity ranges. Pair records and scene records were also recomputed within every deletion.
- Each cross-block statistic directly multiplies every ordered distinct-block pair. The production analysis module is not imported. Historical raw means use compensated scalar sums before fixed standardization.
- Compared 22,553 numeric leaves and 7,488 categorical/null leaves; no mismatches. Maximum absolute numeric difference: 1.85e-13; tolerance: abs=1e-10, rel=1e-11.

## Full-cohort results

| Family | Pooled C/N | Pooled T | Scene C/N | Scene T | beta | Pooled D | Scene D |
|---|---:|---:|---:|---:|---:|---:|---:|
| all31 | 0.641844577 | 5.397488432 | 0.723666793 | 17.922120982 | 0.617532640 | 0.916968523 | 1.636632297 |
| color | 0.575098931 | 0.719060728 | 0.666478579 | 2.438316939 | 0.632180399 | 0.692255148 | 0.884251602 |
| spatial | 0.848511492 | 6.137171459 | 0.812022874 | 15.710149602 | 0.310210442 | 1.269964973 | 3.538554959 |
| texture | 0.365771519 | -1.458743755 | 0.485042797 | -0.226345560 | 0.804926610 | 0.894718918 | 1.091230392 |

The all-coordinate descriptive common-majority condition (N > 0 and T > 0) holds, as do color and spatial sensitivities. **Texture fails that condition in both pooled and within-scene summaries**, and its T stays negative in all 25 deletions. All denominators are positive in these retained results. Positive alignment and smaller error do not establish artistic fidelity; a common response is not thereby unwanted or non-stylistic.

The generic control already requests oil painting. The exact named prompt inserts ` by [painter]` after `An oil painting on canvas`. All five arms share each scene/block seed. SD-Turbo revision `b261bac6fd2cf515557d5d0707481eafa0485ec2` uses fp16/MPS, 512×512, one denoising step, guidance zero, and null negative prompt. Prior energy-distance, coordinate, qualification, and copy diagnostics exposed the cohort. Stable independent block errors remain an assumption; this replay does not establish them or validate closed-service independence.

The companion JSON retains every recomputed numeric record, comparison counts, maximum identity residuals, source bindings, and provenance checks. Original-image SHA-256 checks hash file bytes; this audit does not re-extract features or decode images.

## Replay

Run from the repository root (ordinary replay is read-only):

```sh
.venv/bin/python reports/icml_review_v1/resume_2026-09-21/cross_cohort_numeric_audit.py
```

The original invocation used `--write` to create this JSON/Markdown pair once; existing audit artifacts are never overwritten.
