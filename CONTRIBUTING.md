# Contributing

LatentArtBench compares generated-image features with digital reproductions of
paintings. Start with [current status](docs/STATUS.md), then the
[handover](docs/AGENT_HANDOVER.md) and the [analysis catalog](docs/ANALYSES.md).
Work paused on 2026-09-21 after the ICML draft met the user's review target;
new scientific work or manuscript revision needs a new instruction.

## Where changes belong

- `paper/`: the ICML draft, the full-length paper, the Korean translation and
  their presentation builders. [paper/README.md](paper/README.md) owns the builds.
- Versioned packages in `src/latent_art_bench/`: scientific computation, with
  corresponding tests, study plans, manifests and result directories.
- `docs/` and the README files: current navigation. Keep them short and link to
  records instead of restating them.
- `reports/` and `studies/`: dated records. Add new files under a new version;
  do not rewrite existing ones.
- Git history: superseded navigation text and duplicate summaries that are not
  scientific dependencies.

Use English for documentation and the English manuscripts. Keep all four
painters in scope. Explain the resulting behavior and validation; routine
reversible documentation improvements need no additional approval.

## Scientific changes

Changes to features, preprocessing, prompts, references, weighting or inference
need a scientific rationale and validation appropriate to the claim. For a
completed, bound analysis, create a new versioned result and compare it with the
preserved original. Keep failures and negative findings. Distinguish prospective
tests from post-result diagnostics, and numerical agreement from artistic
fidelity or independent replication.

Historical source paths, tests, configuration files and reports can be evidence
dependencies. Test a file's bindings before moving or deleting it (see the
[handover](docs/AGENT_HANDOVER.md#what-must-not-change)). Do not change terminal
outputs, ledger entries or stored hashes to make a check pass.

## Checks and data

Run checks appropriate to the change:

- Documentation: working links and preserved dependencies.
- Manuscript: the relevant build, presentation replay and page-by-page visual inspection.
- Current analysis: targeted tests, `make check` and affected numerical replays.
- Shared primitives or historical workflows: `make check-all` and the relevant
  evidence/replay checks.

`pytest-paper.ini` is hash-bound, so a new routine test suite is added to
`ROUTINE_EXTRA` in the Makefile. [Test scope](tests/README.md) explains routine
versus historical coverage. Live tests require explicit authorization; Makefile
targets make no generation requests. Passing software checks does not establish
scientific validity.

Preserve secrets, local user work, ignored image/response archives, weights and
bound temporary files. Do not commit unlicensed artwork or the anonymous ICML
PDF. See [artifact retention](docs/ARTIFACTS.md); ignore status is not
permission to delete a file.
