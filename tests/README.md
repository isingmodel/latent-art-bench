# Test scope

`make check` runs three steps:

1. Ruff on the repository. Scripts under `reports/` are frozen audit records and
   are excluded.
2. The routine suite selected by [pytest-paper.ini](../pytest-paper.ini).
3. The newer routine suites in the Makefile's `ROUTINE_EXTRA` list
   (SD-Turbo cross-cohort, selective attribution, the TMLR diagnostics v1–v6 and the
   second collection, `painter_specificity_v3`: reference gates and lexicon, payload identity
   with the first collection, the collector with a mocked transport, and the analysis on
   constructed data).

Together they cover the 31-feature calculations, four-painter comparisons,
weighting and randomization, missing observations, palette response, geometry,
arithmetic oracles, evidence integrity, the main public replay contracts, the
six-model analysis and diagnostics, every retrospective analysis and the offline
family-control collector. No live calls are made.

```sh
make check                         # Routine analysis and integrity checks
make check-all                     # All retained offline regression tests
uv run --locked pytest -q tests/painter_map_validation_v2/test_analysis_oracle.py
```

`pytest-paper.ini`, `pytest.ini` and `pyproject.toml` are hash-bound by completed
analyses, so their bytes stay unchanged. Add a new routine test directory to
`ROUTINE_EXTRA` in the Makefile instead. A plain `pytest` uses `pytest.ini` and
discovers every retained test. Both Make targets exclude tests marked `live`.

Two historical mocked-collector modules (`painter_naming_replication_v1` and
`painter_map_validation_v2/test_operations.py`) keep the production 5 GiB storage
reserve and read the host's real free space. With less free disk they fail
before dispatch; this is an environment condition, documented in the
[2026-09-19 environment audit](../reports/icml_review_v1/validation_environment_audit.md).

## Why the routine suite is a selection

The former 1,970-case suite mixed current analysis with closed acquisition,
generation, preparation, human-rating and packaging workflows. The routine
selection omits those historical cases; they remain in `make check-all`. This
narrows routine regression coverage; it does not claim equivalent coverage of
every old implementation.

Eight unbound test files for obsolete operational paths (the early generic
metadata collector, old acquisition and delivery transports, preliminary
generation grids, service probes and OAuth transport) and two report-formatting
tests were retired; they are recoverable from Git at `b5a6348`. Frozen
predecessor tests were not deleted merely because they repeat successor tests.

## Choosing checks

Run the relevant test module while editing. Use `make check` for changes to
current analysis and `make check-all` for shared primitives, test-runner changes
or historical workflows. Run `make evidence` after changes that could affect an
evidence binding. Manuscript edits need compilation and visual inspection;
documentation edits need working links, not a Python run. Test totals describe
software checks, not scientific validation.

## Verification history

| Date | Routine suite | Full offline suite | Notes |
| --- | --- | --- | --- |
| 2026-09-10 | 808 passed | 1,929 passed | Evidence audit 2,902 checks |
| 2026-09-11 | 823 passed | 1,944 passed | Six-model implementation |
| 2026-09-13 | 848 passed | Not rerun | Source-quality audit; 870 source hashes, 131 crops re-extracted |
| 2026-09-19 | 881 passed, 10 failed | Not rerun | Failures from the storage reserve; a scoped fixture verified all 85 affected cases |
| 2026-09-23 | 1,251 + 110 passed | 2,482 passed (536 s) | Evidence audit 2,902 checks, 0 failed; Ruff passes with the record-script exclusion |
| 2026-09-25 | 1,251 + 110 passed | Not rerun | Evidence audit 2,902 checks, 0 failed; at 4.1 GiB free the same 10 storage-reserve cases failed, and passed after space was freed |
| 2026-10-01 | 1,251 + 134 passed | Not rerun | After the TMLR round-3 revision; `evidence`, `retrospective-check` (diagnostics v1–v3) and `tmlr-check` pass |
| 2026-10-01 | 1,251 + 136 passed | Not rerun | After the TMLR round-4 revision (diagnostics v4 added); all offline check targets pass |
| 2026-10-01 | 1,251 + 141 passed | Not rerun | After the TMLR round-5 revision (diagnostics v5 added); all offline check targets pass |
| 2026-10-01 | 1,251 + 141 passed | Not rerun | After the final post-round-6 TMLR revision; all offline check targets pass |
| 2026-10-03 | 1,251 + 174 passed | Not rerun | After the second collection and the paper revision; `retrospective-check` (including the v3 analysis and diagnostics v6), `tmlr-check` (37 generated files, 225 claims) and `tmlr-ko-check` pass; supplement 100 files, 69.5 MiB, no identifier found |
| 2026-10-04 | 1,251 + 178 passed | Not rerun | After the revision for TMLR review v2 round 1 (diagnostics v7 added); `retrospective-check` (including diagnostics v7), `tmlr-check` (39 generated files, 259 claims) and `tmlr-ko-check` (34 Korean tables) pass; the anonymous supplement (104 files, 69.6 MiB) passes its identifier scan |
| 2026-10-04 | 1,251 + 178 passed | Not rerun | After the Korean translation was deleted and made anew; `tmlr-check` (39 generated files, 259 claims) and `tmlr-ko-check` (34 Korean tables, numbers of the Korean text) pass; the Korean PDF builds (41 pages) |
