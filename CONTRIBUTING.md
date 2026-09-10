# Contributing

LatentArtBench compares generated-image feature distributions with digital
reproductions of paintings. Start with the [current status](docs/STATUS.md),
[analysis map](docs/ANALYSES.md) and [architecture](docs/ARCHITECTURE.md).

The current phase is paper correction. Use the [handover](docs/AGENT_HANDOVER.md)
for completed work and boundaries, and [paper/README.md](paper/README.md) as the
canonical build and visual-check guide.

## Where changes belong

- `paper/` contains the canonical English manuscript, bibliography and presentation
  figures. Older manuscripts are available in Git history.
- Each analysis has its own package under `src/latent_art_bench/`, corresponding
  tests, study methods, compact manifests and published reports. The analysis
  map identifies computation and plotting entry points separately.
- Mutable documentation explains current use. Completed protocols, source
  implementations and evidence bundles remain at their recorded paths.

Use English for documentation, comments and review discussions. Keep changes
focused and explain the problem, resulting behavior and relevant validation.
No issue or approval is needed for routine reversible documentation improvements.

## Scientific changes

A change to features, preprocessing, prompts, reference selection, weighting or
inference needs a stated scientific rationale and validation appropriate to the
claim. Start a new versioned analysis when the existing one contains sealed
results. Do not edit terminal collectors, frozen methods or published outputs to
make old evidence match a new result. Shared primitives can change only when
contracts remain clear and their historical versions remain verifiable.

Retain failures and negative results. Distinguish prospective tests from
post-result diagnostics and finite-image findings from perceptual or population
claims. Internal LLM reviews are not independent human peer review.
The restored four-painter analysis is current descriptive paper evidence, separate
from the later two-painter controlled experiments. Preserve its post-result,
two-retry and requested-alias qualifications; do not pool these cohorts or revive
the original incomplete prompt study's unavailable primary inference.

## Checks and data

```bash
make paper           # Render manuscript figures and build the PDF
make figures-check   # Check the nine manuscript figures without rewriting them
make check           # Ruff and the current analysis/integrity test suite
make check-all       # Ruff and all retained offline regression tests
make evidence        # Commit-bound historical evidence audit
make four-painter-analysis  # Replay exploration, Stage A controls and retry presentation
make analysis        # Replay Study 1 controlled and revision numeric results
make plots           # Replay Study 1 report bundles and check manuscript figures
make computational-responsiveness  # Replay Study 2, retrieval and quantile correction
```

Run the checks relevant to the change. [Test scope](tests/README.md) distinguishes
the 808-case routine suite from retained historical coverage. Shared Python or
test-runner changes require `make check-all`; current analysis changes require
`make check` and any affected historical modules. Paper changes require compilation and visual page inspection;
documentation changes require working links. Keep live tests explicitly marked
`live` and run them only with user authorization.

Never commit secrets or unlicensed artwork. Preserve ignored image responses,
model weights, source checkouts and bound temporary files. Git history does not
back up those bytes. See [artifact retention](docs/ARTIFACTS.md) before deleting
or moving research files. Never refresh evidence hashes or expand the two
historical acknowledgements to conceal a new mismatch.
