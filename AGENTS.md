# Agent guide

## Project principles

1. Do not leave redundant or stale artifacts in the codebase.
2. If a plan fails, find the cause and retry the same goal; do not quietly substitute a
   different goal.
3. Keep the project simple. Extra machinery is not evidence of progress.

## Start of every task

1. Read `docs/STATUS.md`, then `docs/ARTIFACTS.md`.
2. Inspect `git status --short --branch`; preserve user changes and ignored research bytes.
3. Identify whether the requested work is shared-primitive work, active-census work, or a
   newly versioned study.
4. Run the smallest relevant offline tests. Before handoff, run Ruff and the full suite when
   the change can affect Python behavior.

```bash
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
```

## Evidence and protocol boundaries

- Do not rewrite, reorder, truncate, move, or regenerate frozen protocols, hash-bound
  evidence, or append-only ledgers for cosmetic cleanup.
- A terminal census is closed permanently. Do not retry it in place or introduce a fallback;
  a retry is always a new census ID with disjoint paths, bound to the predecessor's terminal
  evidence.
- External-holdout access, image acquisition, feature extraction, generation transport, and
  image generation are closed unless Protocol 2.0's stage gates explicitly authorize them.
- The one expected freeze-verification failure is documented in `docs/STATUS.md`. Do not make
  it pass by refreshing old evidence hashes.
- Raw artwork, full-resolution generated images, model weights, and source checkouts are
  ignored but may be unique local evidence. Never use `git clean -xfd` or broad recursive
  deletion under `artifacts/`, `data/`, or `research_workspace/`.

## Study conventions

- Prefer a new versioned namespace over mutating a namespace that already holds sealed evidence.
- Reuse shared primitives only when their contracts remain clear and tested.
- Keep mutable status separate from immutable evidence.
- Store large runtime bytes under one ignored workspace boundary and commit only compact,
  redistributable manifests and reports.
- Record portable relative paths; do not add new `/Users/fred` paths.
- Keep the standard suite offline. Any live transport test must use the registered `live`
  marker and must never run without explicit user authorization.

Update `docs/STATUS.md` when operational state changes. Update `docs/INDEX.md` when adding or
retiring a canonical document.
