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
   the change can affect Python behavior, and the evidence audit when the change touches
   `data/manifests/`, `research_workspace/`, or any freeze-bound file.

```bash
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
uv run --locked latent-art-bench verify-evidence
```

## Evidence and protocol boundaries

- Do not rewrite, reorder, truncate, move, or regenerate frozen protocols, hash-bound
  evidence, or append-only ledgers for cosmetic cleanup.
- A terminal census is closed permanently. Do not retry it in place or introduce a fallback;
  a retry is always a new census ID with disjoint paths, bound to the predecessor's terminal
  evidence.
- External-holdout access, image acquisition, feature extraction, generation transport, and
  image generation are closed unless Protocol 2.1's stage gates explicitly authorize them.
- `studies/painter_feature_generation_v1/PROTOCOL_2.1.md` is canonical. `PROTOCOL.md` is the
  frozen Protocol 2.0 text bound by every completed census freeze; never edit it.
- Evidence verification is commit-bound. The two bound inputs that can never re-verify are
  recorded in `data/manifests/painter_feature_generation_v1/evidence_acknowledgements.json`; do
  not extend that file to hide a new mismatch, and never refresh an evidence hash. New freezes
  record `recorded_git_commit` and are prepared from a tree whose bound inputs are clean.
- Every "neutral independent review" so far was an LLM review subagent run by the maintainer.
  Say so wherever a report describes a review; do not describe it as institutionally independent.
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
