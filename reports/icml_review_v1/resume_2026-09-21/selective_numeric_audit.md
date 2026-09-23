# Selective-attribution independent numerical audit

**Status: passed. The primary joint usefulness criterion remains false.**

This audit was run after the separate pre-outcome method/code audit and real analysis. It independently reconstructed the results from the retained manifest and both raw embedding archives. It did not import the study implementation or call its computation/evaluation routines. It is not a scientific rating.

## Verification scope

- Recomputed all eight encoder/view/prototype settings and all six requested configurations, retaining 1,008 queries in every setting.
- Reconstructed original/audited reference membership, prototypes, calibration scores and exact order statistics directly from raw archive rows.
- Recomputed every query score, candidate set, top-1 prediction, abstention reason and both acceptance decisions.
- Recomputed counts, confusions, per-painter coverage/risk, free/generic control rates and inclusive ties, exactly matched margin coverage, all joint criteria, every scene deletion, and all reported influence ranges.
- Compared **435,066 values**. Maximum absolute numerical difference: **1.11e-16**; maximum relative difference: **8.35e-14**. No discrepancy exceeded rtol=1e-10 / atol=1e-12. Counts, identities, decisions, failure flags and missing values agreed exactly.

## Primary finding

The CSD/original/primary setting fails both required coverage conditions: coverage is below 50% for five configurations, and three configurations accept no examples from at least one prompted artist. All eight settings fail their joint descriptive usefulness criterion.
The equal-configuration accepted-risk reduction is **26.0304 percentage points** relative to unrestricted top-1 and **0.5259 points** relative to the coverage-matched margin comparator. The latter mean includes a negative FLUX comparison.

| Configuration | Coverage % | Gate risk % | Margin risk % | Accepted counts: Monet / Sisley / Pissarro / Cezanne |
|---|---:|---:|---:|---|
| gpt-image-1 | 26.7857 | 0.0000 | 0.0000 | 1 / 0 / 1 / 28 |
| gpt-image-2 | 33.0357 | 2.7027 | 2.7027 | 1 / 1 / 8 / 27 |
| gpt-image-2.5-flare | 24.1071 | 0.0000 | 0.0000 | 0 / 0 / 2 / 25 |
| gpt-image-2.5-sunburst | 26.7857 | 0.0000 | 0.0000 | 0 / 0 / 2 / 28 |
| google/gemini-3.1-flash-image | 45.5357 | 25.4902 | 33.3333 | 6 / 9 / 8 / 28 |
| black-forest-labs/flux.2-max | 57.1429 | 53.1250 | 48.4375 | 8 / 17 / 22 / 17 |

## Scope and replay

This is retrospective standard selective classification. Numerical agreement does not establish generated-image conformal coverage, perceptual fidelity, shared-family causality, service independence or fresh-session replication. The adverse findings remain part of the result.

The adjacent JSON binds the exact input freeze, pre-outcome audit, row manifest, both raw archives, real analysis and independent script. To replay without overwriting this completed evidence, use a new output path:

```sh
uv run --locked python reports/icml_review_v1/resume_2026-09-21/selective_numeric_replay.py --output /tmp/selective_numeric_reaudit.json
```
