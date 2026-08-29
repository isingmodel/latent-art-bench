# Contributing

LatentArtBench is currently in the research-design and validation stage. Contributions are welcome when they improve methodological clarity, reproducibility, corpus governance, or implementation fidelity.

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

## Conduct

Contributors should discuss disagreements in terms of evidence, scope, and reproducibility. Art-historical labels and canons are contested constructs; their use should remain attributed, transparent, and open to revision.
