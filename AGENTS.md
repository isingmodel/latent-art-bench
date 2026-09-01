# Agent guide

## Project principles

1. Do not leave redundant or stale artifacts in the codebase.
2. If a plan fails, find the cause and retry the same goal; do not quietly substitute a
   different goal.
3. Keep the project simple. Extra machinery is not evidence of progress.

## Start of every task

1. Read `docs/STATUS.md`, then `docs/ARTIFACTS.md`.
2. Inspect `git status --short --branch`; preserve user changes and ignored research bytes.
3. Identify whether the requested work is shared-library work, historical study maintenance,
   or a newly versioned reboot study.
4. Run the smallest relevant offline tests. Before handoff, run Ruff and the full suite when
   the change can affect Python behavior.

```bash
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
```

## Evidence and protocol boundaries

- For this reboot, treat Pilots 0–3 as historical study records. Do not rewrite, reorder,
  truncate, move, or regenerate frozen protocols, hash-bound evidence, or append-only ledgers
  for cosmetic cleanup.
- The Pilot 3 Met R2 cohort is closed after a terminal HTTP 403 metadata response. Do not
  retry it or introduce a fallback.
- External-holdout access, feature extraction from an incomplete Pilot 3 cohort, generation
  transport, and image generation are closed unless a new prospective protocol explicitly
  authorizes them.
- Historical verifier failures are documented in `docs/STATUS.md`. Do not make them pass by
  refreshing old evidence hashes.
- Raw artwork, full-resolution generated images, model weights, and source checkouts are
  ignored but may be unique local evidence. Never use `git clean -xfd` or broad recursive
  deletion under `artifacts/`, `data/`, or `outputs/`.

## Reboot conventions

- Prefer a new namespace over mutating `pilot_0` through `pilot_3`.
- Reuse shared primitives only when their contracts remain clear and tested.
- Keep mutable status separate from immutable evidence.
- Store large runtime bytes under one ignored workspace boundary and commit only compact,
  redistributable manifests and reports.
- Record portable relative paths; do not add new `/Users/fred` paths.
- Keep the standard suite offline. A legacy live transport test must use the registered
  `live` marker and must never run without explicit user authorization.

Update `docs/STATUS.md` when operational state changes. Update `docs/INDEX.md` when adding or
retiring a canonical document.
