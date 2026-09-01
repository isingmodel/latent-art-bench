# Contributing

LatentArtBench is preparing for a project reboot after the Pilot 3 Met R2 cohort closed.
Contributions are welcome when they simplify the reusable implementation, improve
methodological clarity, reproducibility, corpus governance, or implementation fidelity. Read
the [current status](docs/STATUS.md) before proposing work.

## Before contributing

Please open an issue describing:

- the research or engineering problem;
- the source paper, dataset, or benchmark module affected;
- whether the proposal changes a confirmed decision;
- expected effects on reproducibility, rights, or comparability.

## Contribution principles

- Write documentation, code comments, issue titles, and pull-request descriptions in English.
- Do not add artwork files unless their redistribution rights have been verified and documented.
- Do not commit API keys, credentials, cookies, proprietary model outputs that cannot be redistributed, or private dataset URLs.
- Preserve source metadata and provenance; do not overwrite historical labels silently.
- Add tests for feature implementations and preprocessing changes.
- Report failed replications and negative results.
- Keep source-faithful and harmonized methods distinct.
- Avoid benchmark changes made after observing final model rankings unless they are released as a new benchmark version.
- Keep the initial study within the scope frozen in the roadmap. Optional feature or extension work must not become an undeclared prerequisite for the MVP.

## Research-method changes

A change to a metric, prompt distribution, corpus split, target ontology, evaluator, or score must include:

1. a rationale;
2. affected source methods;
3. validation evidence;
4. backward-compatibility implications;
5. a versioning proposal.

## Pull requests

Pull requests should be focused and include a concise validation summary. Documentation-only contributions should verify internal links and references. Code contributions should include tests and a reproducible command or notebook.

The standard offline checks are:

```bash
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
```

Do not use `pilot2 verify` or `pilot3 verify` as general current-branch health checks; their
known hash-bound failures are recorded in [the status page](docs/STATUS.md). The standard test
suite must not make live museum, browser, proxy, or image-generation requests. Any intentionally
maintained legacy live transport test must use the `live` marker and run only with explicit
user authorization.

Historical protocols, reports, and append-only ledgers should stay at their existing paths.
New scientific work must use a new versioned study namespace rather than altering a closed
pilot.

## Conduct

Contributors should discuss disagreements in terms of evidence, scope, and reproducibility. Art-historical labels and canons are contested constructs; their use should remain attributed, transparent, and open to revision.
