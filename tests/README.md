# Test scope

Use `make check` for the current paper's analysis and data-integrity tests. It
runs Ruff and the **822-case routine suite** selected by
[pytest-paper.ini](../pytest-paper.ini). Tests cover the 31-feature calculations,
four-painter comparisons, weighting and randomization, missing observations,
palette response, geometry, arithmetic oracles, evidence integrity and the main
and current public replay contracts. The latest collection safeguards remain
covered with artificial inputs; no live calls are made.

The artist-specificity extension adds 14 cases: eight numerical checks for
centering, repeat correction, paired intervals and regression; three route and
accounting checks; two reference-mixture checks; and one reference-membership
check. They protect the new scientific and collection contracts. No plotting or
document-formatting tests were added.

```sh
make check                         # Routine analysis and integrity checks
make check-all                     # All retained offline regression tests
uv run --locked pytest -q tests/painter_map_validation_v2/test_analysis_oracle.py
```

The routine suite is an explicit selection. Add a new current analysis test
file to `pytest-paper.ini` when introducing it. A plain `pytest` still uses the
original `pytest.ini` and discovers all retained tests. That file, `pyproject.toml`
and many historical tests are bound to published evidence, so their bytes and
paths remain unchanged. Both Make targets exclude tests marked `live`.

## What was reduced

The former 1,970-case suite mixed current analysis with closed acquisition,
generation, preparation, human-rating and packaging workflows. Those histories
are useful for reproducing old software states, but they do not all belong in
routine paper development. The routine selection omits **1,121 retained historical
cases**. This reduces the scope of routine regression coverage; it does not claim
equivalent coverage of every old implementation.

Another **41 cases were removed from the working tree**, leaving 1,929 at that
retirement. With the subsequent 14 specificity cases, `make check-all` contains
1,943 retained cases. Eight retired unbound files covered obsolete operational paths:

- `painter_feature_generation_v1/test_collect.py`: the early generic metadata collector.
- `painter_feature_generation_v2/test_acquisition.py`, `test_renderings.py` and
  `test_renderings_r2.py`: old acquisition and delivery transports.
- `painter_feature_generation_v2/test_generation.py`, `test_model_assessment.py`,
  `test_assessment_diagnostics.py` and `test_oauth_generate.py`: preliminary
  generation grids, service probes and OAuth transport.

Two report-formatting tests were also removed from
`painter_feature_generation_v2/test_report.py`; numerical report and missing-analysis
checks remain. This is retirement of coverage for closed paths and low-impact
formatting, not a claim that different collectors behave identically. These
unbound tests remain recoverable from Git at `b5a6348`. No implementation,
numerical fixture, protocol, ledger, result or published archive was changed.

Frozen predecessor tests were not deleted or rewritten merely because they
repeat successor test bodies. In particular, historical collector, qualification,
human-rating preparation and older release-adapter suites remain available in
`make check-all`. Different adapters still require their own integrity checks
when they change. The routine suite retains result-level refusal, missingness
and retry-identity checks even where the old collection executor is omitted.

## Choosing checks

Run the relevant test module while editing. Use `make check` for changes to the
current analysis. Use `make check-all` for shared Python primitives, test-runner
changes or work on a historical workflow. Run `make evidence` after changes that
could affect an evidence binding. Paper-only edits require compilation and
visual inspection; documentation-only edits need working links, not a full
Python run. Test totals describe software checks, not scientific validation.

Verification on 2026-09-10: `make check` passes all 808 routine cases; the
explicit full suite passes all 1,929 retained cases. Ruff and the 2,902-check
evidence audit pass. No test cases were merged into loops to lower the count,
and no scientific values or comparison thresholds were changed.

Verification on 2026-09-11 after the specificity implementation: the full
offline suite passes all 1,943 cases, including the 822 routine cases, in
476.14 seconds. Ruff passes. The earlier audit's 2,902 checks cover historical
evidence; the new experiment has its own four numerical replays and raw-byte
audit. Passing software tests does not establish measurement or scientific validity.
