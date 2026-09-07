# Agent handover

Read [STATUS.md](STATUS.md), then [ARTIFACTS.md](ARTIFACTS.md), and inspect
`git status --short --branch` before acting. Follow [AGENTS.md](../AGENTS.md).
This handover is mutable orientation, not a protocol or execution authorization.

## Where to work

The current deliverable is the English manuscript in [paper/](../paper/README.md).
It has been rewritten from a blank TeX source around the scientific question,
design, results and interpretation. Keep operational histories, budgets and
recruitment planning outside its scientific prose. Earlier manuscripts are in Git
history; do not restore duplicate manuscript folders.

The numerical evidence comes from the completed
[controlled study](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md)
and [computational revision](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md).
Use [ANALYSES.md](ANALYSES.md) to locate analysis, full-report plotting and manuscript
figure commands. Use [ARCHITECTURE.md](ARCHITECTURE.md) to trace code dependencies.
There is no unfinished collector or analysis job to resume.

## Research constraints

- Preserve the original eight conditional randomization tests. Subsequent fixed
  diagnostics are post-result and descriptive; a new analysis needs an explicitly
  versioned scope, not changes to published numbers.
- Keep proximity, aggregate variation, within-brief variation and perceptual
  interpretation distinct. All paid outputs are square, all references nonsquare,
  and capture provenance is unresolved. Classifier separability is not established
  as painter-style distance.
- Human/reference validation and learned-feature analysis have not been performed.
  The frozen [validation plan](../studies/painter_distribution_revision_v1/VALIDATION_PLAN.md)
  is planning evidence, not completed validation or recruitment authorization.
- Reviews so far are maintainer-run LLM subagent reviews with coordinator checks.
  Do not describe them as independent human or institutional peer review.

## Evidence boundaries

The controlled and revision namespaces are terminal. Never retry, top up, reorder
or rewrite a closed run. Preserve failed requests and refusal bodies alongside
successful outputs. Corrections require a successor namespace with explicit input
bindings. Existing stage gates still govern image access and generation; cleanup
or manuscript edits do not open them.

Verification is commit-bound. The revision records source/input commit `f7666ae`,
numeric freeze `c505512`, and report-renderer commit `1d635a5`. Preserve all bound
protocols, review documents, validation/literature plans, source, inputs and report
receipts. Do not refresh evidence hashes or extend acknowledgement files to hide
a mismatch. Mutable orientation documents and editable manuscript prose have a
different role from sealed scientific evidence.

Ignored files can be unique evidence. Do not use `git clean -xfd` or recursively
delete `data/`, `research_workspace/` or `artifacts/`. Check exact paths against
[ARTIFACTS.md](ARTIFACTS.md); Git history does not preserve ignored raw bytes.

## Working preferences and checks

The user wants English reasoning and documents, substantive skeptical review,
and infrequent progress updates. The paid study ceiling was $75; recorded
conservative spending is in [STATUS.md](STATUS.md). Further generation must address
a specific research uncertainty. If transport is separately authorized, use
staggered parallel calls, bounded technical retries, and stop to diagnose clustered
failures. Never expose `.env` or API keys in output.

After changes, run the smallest relevant offline checks. Python behavior changes
also require `make check`; evidence-bound changes require `make evidence` and the
appropriate replay checks. Use `make analysis` and `make plots` for the current
numerical/report evidence, and the [paper guide](../paper/README.md) for PDF builds
and visual inspection. Tests marked `live` require explicit authorization.

Update [STATUS.md](STATUS.md) when operational state changes and [INDEX.md](INDEX.md)
when canonical documents change. Keep each guide focused; link historical reports
and protocols instead of appending another copy of their timeline.
