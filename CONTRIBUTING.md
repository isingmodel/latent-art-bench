# Contributing

LatentArtBench compares generated-image feature distributions with digital
reproductions of paintings. Start with the [current status](docs/STATUS.md),
[analysis map](docs/ANALYSES.md) and [architecture](docs/ARCHITECTURE.md).

## Where changes belong

- `paper/` contains the single current manuscript, bibliography and presentation
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

## Checks and data

```bash
make check       # Ruff and the full offline test suite
make evidence    # Commit-bound historical evidence audit
make analysis    # Replay the paper's two numerical analyses
make plots       # Replay their report figures/tables and check paper figures
make paper       # Render manuscript figures and build the PDF
```

Run the checks relevant to the change. Python changes require Ruff and the full
offline suite. Paper changes require compilation and visual page inspection;
documentation changes require working links. Keep live tests explicitly marked
`live` and run them only with user authorization.

Never commit secrets or unlicensed artwork. Preserve ignored image responses,
model weights, source checkouts and bound temporary files. Git history does not
back up those bytes. See [artifact retention](docs/ARTIFACTS.md) before deleting
or moving research files. Never refresh evidence hashes or expand the two
historical acknowledgements to conceal a new mismatch.
