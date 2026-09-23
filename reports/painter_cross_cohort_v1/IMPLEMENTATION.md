# SD-Turbo retrospective audit: implementation qualification

Status: constructed qualification passed; independent final code audit and input
freeze are pending. No new empirical decomposition has been computed.

## Scope

The new `painter_cross_cohort_v1.py` module implements the separate retained
2,000-image SD-Turbo study defined in
`studies/painter_cross_cohort_v1/PLAN.md`. It preserves matched seeds across arms
and treats repeat blocks as the sampling unit for the stated expectation
calculations. It adds no calls, downloads, image extraction, or changes to prior
study records.

Outputs cover pooled and within-scene common/centered/total naming change,
common-majority contrasts and signed ratios, reference alignment and error, all
six painter pairs, all four fixed coordinate views, and every delete-one-block
result. Undefined denominators retain reasons; finite sensitivity ranges are
not confidence intervals. No p-values are produced.

## Completed qualification

- `uv run --locked pytest -c pytest-paper.ini -q tests/painter_cross_cohort_v1`:
  **55 passed**.
- Ruff checks on the new implementation and its tests: passed.
- Constructed tests include explicit ordered-pair U-statistic oracles, the
  two-repeat formula, paired-arm nuisance cancellation, common-only and
  contrast-only cases, negative finite estimates, fractions outside [0,1],
  zero reference/pair denominators, scene averaging order, family-specific
  denominators, all six pair identities and all 25 deletion records.
- Synthetic metadata tests reject missing, duplicate, foreign, failed and
  inconsistent cells, changed normalization and invalid features. Gate tests
  cover code-audit bindings, explicit execution, external frozen-input hashes,
  create-once writes and constructed result serialization/replay/tampering.
- A read-only `validate_census()` run passed: all 2,000 generated pixel hashes,
  649 reference original pixel hashes, exact reference membership, complete
  cell census, literal prompts, 400 matched scene/block seeds, fixed scaler
  and normalization contracts, non-overlap with the main 1,008 image hashes,
  and 41 retained source/metadata bindings.

The validation reads existing feature rows to check their schema and finite
values, but does not aggregate empirical features or calculate any new outcome.
The metadata run created no study freeze or result files.

## Execution boundary

`freeze --audit-report PATH` requires a passing independent audit JSON whose
`bindings` cover the exact plan, implementation and every constructed test.
Freeze creates `inputs.json` once and prints its SHA-256. It calculates no
empirical outcome.

`analyze` and `check` require both `--execute-real` and
`--inputs-sha256 EXPECTED_DIGEST`. They verify the audit, frozen inputs, runtime,
full census and pixels before empirical calculations. Analysis and report files
are create-once; check recomputes their numeric and report content.

This software qualification is not evidence of a scientific result, a new
generation cohort, independent reference validation, or a higher review score.
