# Documentation

| Question | Read |
| --- | --- |
| What does the project ask, and how is it reproduced? | [Project README](../README.md) |
| What is currently true, and what is still undecided? | [Status](STATUS.md) |
| Where do I continue, and which files must not change? | [Handover](AGENT_HANDOVER.md) |
| Which code produces each result, figure and table? | [Analysis catalog](ANALYSES.md) |
| Which files are evidence, and what may be deleted? | [Artifact retention](ARTIFACTS.md) |
| How are the manuscripts organized and built? | [Paper guide](../paper/README.md) |
| Where are the numerical results and review records? | [Results index](../reports/README.md) |
| Which tests run routinely? | [Test scope](../tests/README.md) |
| How should a change be made and checked? | [Contributing](../CONTRIBUTING.md) |

Scientific protocols and fixed plans live in [studies/](../studies/); executed
study settings are described in [configs/](../configs/README.md).

## Historical documents at fixed paths

These records describe earlier decisions, not the current task. Completed
analyses bind their bytes or paths, so they stay where they are and are never
edited.

| Record | Why it is retained |
| --- | --- |
| [Mechanism proposal, 2026-09-08](RESEARCH_IDEA_20260908.md) | Hash-bound input of the responsiveness v1/v2 freezes |
| [Methodology revision plan, 2026-09-07](reviews/20260907_methodology/REVIEW_AND_REVISION_PLAN.md) | Hash-bound by the distribution-revision and measurement-validation freezes; its three source reviews sit beside it |
| [External reviews and assessment, 2026-09-13](../critics/ASSESSMENT.md) | Motivated the source-quality and diagnostic corrections; `critics/assessment_v1/check_claims.py` is bound by later analyses |
| [Literature evidence base](../literature_reviews/README.md) | Search protocol, evidence matrix and thematic reviews for the original feature protocol |

Superseded documentation is recoverable from Git; see
[retired documentation](ARTIFACTS.md#retired-documentation).
