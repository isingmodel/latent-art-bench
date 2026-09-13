# Contributing

LatentArtBench compares generated-image features with digital reproductions of
paintings. Start with [current status](docs/STATUS.md), the
[analysis catalog](docs/ANALYSES.md) and [architecture](docs/ARCHITECTURE.md).
The current phase is paper correction; [paper/README.md](paper/README.md) owns
the build workflow and [the handover](docs/AGENT_HANDOVER.md) identifies where to
continue.

## Where changes belong

- `paper/`: canonical English manuscript, bibliography and presentation.
- Versioned packages in `src/latent_art_bench/`: scientific computation, with
  corresponding tests, study methods, manifests and result bundles.
- `docs/`: concise current guidance. Use the analysis catalog for code/plot
  navigation and `reports/README.md` for result navigation.
- Git history: superseded editorial drafts, review rounds and duplicate status
  summaries that are not scientific dependencies.

Use English for documentation and the canonical paper. Keep all four painters in
scope. Explain the resulting behavior and validation; routine reversible
documentation improvements need no additional approval.

## Scientific changes

Changes to features, preprocessing, prompts, references, weighting or inference
need a scientific rationale and validation appropriate to the claim. For a
completed, bound analysis, create a new versioned result and compare it with the
preserved original. Keep failures and negative findings. Distinguish prospective
tests from post-result diagnostics, and numerical agreement from artistic
fidelity or independent replication.

Historical source paths, tests and reports can be evidence dependencies.
Inspect bindings before moving or deleting them. Do not change terminal outputs,
ledger entries or stored hashes to make a check pass.

## Checks and data

Run checks appropriate to the change:

- Documentation: working links and preserved dependencies.
- Manuscript: `make paper`, presentation replay and visual inspection.
- Current analysis: targeted tests, `make check` and affected numerical replays.
- Shared primitives or historical workflows: `make check-all` and their relevant
  evidence/replay checks.

[Test scope](tests/README.md) explains routine versus historical coverage.
Live tests require explicit authorization; normal Makefile targets make no
generation requests. Passing software checks does not establish scientific
validity.

Preserve secrets, local user work, ignored image/response archives, weights and
bound temporary files. Do not commit unlicensed artwork. See
[artifact retention](docs/ARTIFACTS.md); ignore status is not permission to
delete a file.
