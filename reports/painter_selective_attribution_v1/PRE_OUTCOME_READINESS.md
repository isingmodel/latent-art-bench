# Selective-attribution pre-outcome readiness

Recorded 2026-09-21. This record precedes independent final audit and any new
empirical selective-attribution outputs.

- Plan: `studies/painter_selective_attribution_v1/PLAN.md`.
- Implementation: `src/latent_art_bench/painter_selective_attribution_v1.py`.
- Constructed tests: `tests/painter_selective_attribution_v1/`.
- Hash-only freeze: `reports/painter_selective_attribution_v1/inputs.json`.
- Freeze SHA-256:
  `f9d6b94e19d8004463f7b0524dd72865e22c18b0786cf48387cb9257e0528826`.

The last constructed suite passed 55 tests in 0.50 seconds. Ruff passed after a
line-wrap-only correction. The suite includes quantile ranks, all four gate
outcomes, harmful/selective examples, exact margin matching and control ties,
undefined risks and incomplete means, source/crop membership, archive and audit
tampering, exact runtime-version checks, create-once outputs, and full eight-
setting/six-configuration orchestration on constructed one-hot vectors. No
retained empirical vectors are read by those tests. The freeze hashes raw files
but does not load embedding arrays or compute new selective outcomes.

Real execution requires the independent audit JSON, its separately recorded
SHA-256, this freeze identity and `--execute-real`. The audit must bind this
exact plan, implementation and every constructed test. The audit remains
external to the pre-audit freeze to avoid circular hashes.

```sh
uv run --locked python -m latent_art_bench.painter_selective_attribution_v1 analyze \
  --execute-real \
  --input-sha256 f9d6b94e19d8004463f7b0524dd72865e22c18b0786cf48387cb9257e0528826 \
  --audit-file PATH_TO_PASSED_AUDIT_JSON \
  --audit-sha256 EXTERNALLY_RECORDED_AUDIT_SHA256
```

After execution, replace `analyze` with `check` for complete deterministic
result/report replay. No real result was computed while preparing this record.
The independent reviewer must inspect and sign the final bytes before the
execution boundary is crossed. The analysis is a retrospective application of
standard selective classification, with no conformal coverage guarantee for
generated images, no fresh observations and no scientific score claim.
