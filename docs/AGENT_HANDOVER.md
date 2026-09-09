# Agent handover — paper-correction phase

Read [STATUS.md](STATUS.md), then [ARTIFACTS.md](ARTIFACTS.md), inspect
`git status --short --branch`, and follow [AGENTS.md](../AGENTS.md). This is mutable
orientation, not a protocol or authorization to reopen research stages.

The current phase is **paper correction**, with four-artist coverage restored on
`codex/restore-four-artist-analysis`. Before this correction, local `main` was fast-forwarded from
`bdd57e9` to `ecc2c2b`, incorporating `research/pfg-v2-paper` without rewriting
history. No remote push was performed. No image collection or measurement process
is active, and there is no pending acquisition task.

The integration cleanup (`ecc2c2b`) clarified the code/plotting map and the distinct
Study 1 and Study 2 replay commands, added `make figures-check`, consolidated
current status and made this document the correction handover. Scientific packages
and evidence remain at their recorded paths. The English TeX/PDF and user-owned
Korean files were not changed during that integration. The current correction
updates the English manuscript; the Korean files remain preserved.
See [STATUS.md](STATUS.md) for verification
checks and [paper/README.md](../paper/README.md) for the canonical editing workflow.

## Current deliverable

The sole maintained English manuscript is
[paper/paper.tex](../paper/paper.tex), titled **Painter Naming and the
Distributional Gap Between Generated Images and Original Paintings**, with a
[24-page PDF](../paper/paper.pdf) and six vector figures. See the
[paper guide](../paper/README.md) for its bibliography, scientific inputs, build
instructions and access status. Earlier drafts remain in Git history.

The current correction restores Sisley and Pissarro to a main-text four-painter
analysis, including all-method scatter panels, classifier/spread summaries,
matched-size reference baselines and all 24 alias/method cells. It uses only
retained numeric evidence. See the
[restoration review](reviews/20260909_four_painter_restoration.md) for why coverage
was lost, the two skeptical reviews and validation. New collection had focused
on Monet/Cézanne for service breadth and reference curation within the budget;
the plan explicitly retained all four painters in earlier diagnostics. The
omission occurred in later writing, not because Sisley/Pissarro lacked data.

The prior substantive manuscript revision is commit `dd314ee`. It gives each controlled study its
own methods and results, clarifies the contribution and evidence hierarchy,
promotes existing painter-alignment and matched-reference controls, and shows the
six scene-specific color interactions. It did not change scientific results.
The [three-reviewer record](reviews/20260909_scored_review/REVIEW.md) preserves the
fixed rubric, findings and responses: the equal-weight mean rose from **7.8125 to
8.5417/10**, with final reviewer means of 8.625, 8.500 and 8.500 and no unresolved
blocking manuscript finding. These are maintainer-run LLM subagent assessments,
not independent human peer review or a prediction of publication acceptance.
Those scores apply to the prior 19-page version, not the restored draft.

`paper/paper_ko.tex` and the ignored `paper/paper_ko.pdf` are user-owned work.
Preserve them during integration and English-paper correction; do not stage or
modify them as part of repository cleanup.

## Completed scientific work

| Evidence | Completed scope and interpretation |
| --- | --- |
| [Four-painter distributions](../reports/painter_distribution_exploration_v1/REPORT.md) | 649 references (Monet 297, Sisley 106, Pissarro 141, Cézanne 105), 1,536 painter-conditioned images and 384 artist-free controls. Main-text coverage restored without pooling into either controlled study. Both aliases and all three prompt methods remain descriptive; the two later retries do not restore the original randomized primary. |
| [Controlled distribution study](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md) | 1,006 generated images across three services, 70 Monet/Cézanne references and a scaler fixed on 221 development works. Naming lowers primary energy discrepancy in all six service/painter comparisons; four reject after adjustment. Preserve the original eight-test family. |
| [Computational revision](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md) | Feature-view, variance, reference/scaler, painter-alignment, coverage and cross-service diagnostics. The manuscript uses these saved results without introducing new tests. |
| [Scene retrieval and color responsiveness](../reports/painter_responsiveness_v2/REPORT.md) | Retained-data retrieval improves in two service/painter cells and declines in four despite contraction. The separate prospective experiment completed 192 images across six scenes, four style arms, two palettes and four repeats. Both primary named-minus-generic interactions remain unresolved; the secondary generic-minus-free color response decreases. |
| [Exact-weight quantile correction](../reports/painter_responsiveness_quantiles_v1/prqv1-20260908/REPORT.md) | Corrects descriptive weighted medians and their displays in a successor namespace. Primary inference, means, Wasserstein distances and range occupancy are unchanged. Use the corrected displays while preserving the original bundles. |

The sole primary color run is `prv2-oauth-recovery-20260908` (192/192 images).
Its 49-image predecessor remains ancillary and is never pooled into primary
inference. The [prospective recovery protocol](../studies/painter_responsiveness_recovery_v1/PROTOCOL.md)
and [v2 implementation guide](../studies/painter_responsiveness_v2/README.md) retain
the transport correction, allocation and provenance. No OpenRouter charges were
incurred in this follow-up. [STATUS.md](STATUS.md) summarizes accounting and links
the detailed collection record.

The user removed human ratings as a prerequisite for the computational v2 scope.
This did not retrospectively satisfy or waive the earlier
[v1 human/reference qualification](../studies/painter_responsiveness_v1/README.md).
Its human validation remains unperformed; the completed diagnostic and closed
preflight records remain preserved.

## Correction workflow and scientific boundary

Edit manuscript prose, bibliography, presentation figures and current navigation
documents as needed. Use [ANALYSES.md](ANALYSES.md) to find the exact saved numerical
source for a claim and [ARCHITECTURE.md](ARCHITECTURE.md) to trace implementation.
The [follow-up synthesis](../reports/painter_responsiveness_v2/REPORT.md) is editable
writing; its linked per-run reports and numerical bundles are immutable evidence.
Keep revisions substantive and keep one canonical document for each purpose.

Do not move or rewrite frozen protocols, configurations, sources, tests, manifests,
reports, append-only ledgers or bound review records. A scientific or implementation
correction requires a successor scope with explicit input bindings. A terminal
collection cannot be resumed, refilled or combined with later successes to alter
its disposition. Paper correction does not reopen image access, generation or
feature extraction. Preserve the separate test families and distinguish prospective
analyses from post-result diagnostics.

Verification resolves the recorded Git commits and local research bytes. Never
refresh a hash or extend the two historical evidence acknowledgements to conceal
a mismatch. Ignored artwork, response archives, weights and source checkouts can
be unique evidence. Follow [ARTIFACTS.md](ARTIFACTS.md); never use `git clean -xfd`
or broad recursive deletion of research directories.

## Verification and reproduction

Run commands from the repository root, with the locked environment installed using
`uv sync --locked --extra analysis --extra dev`. For a manuscript correction, use
the build and page-rendering instructions in [paper/README.md](../paper/README.md):

```bash
make paper
make figures-check
git diff --check
```

Inspect every rendered PDF page and resolve compilation or layout defects. Figure
rebuilding reads committed numeric tables; it does not compute new scientific
results. After Python behavior changes, run Ruff and the full offline suite:

```bash
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
```

For scientific integrity and retained-data replay, use the distinct checks below.
They are offline and do not acquire images or extract features:

```bash
uv run --locked latent-art-bench verify-evidence
make analysis
make plots
make four-painter-analysis
make computational-responsiveness
```

`make analysis` and `make plots` cover Study 1 and its revision. The historical
evidence audit does not register responsiveness v2; its separate
replay is required for that scope. Full integrity-checked replay needs the retained
raw-response archive, while image-level remeasurement additionally needs retained
pixels and is outside paper correction. Fresh integration validation on local
`main` at `ecc2c2b` passed Ruff, 1,135 offline tests and 2,902 historical audit
checks; all five manuscript figures reproduce byte for byte. The earlier
computational replay passed all 74 report files, and the last substantive paper
revision had all 19 PDF pages visually checked. See [STATUS.md](STATUS.md) for
the precise check record. These checks do not automatically validate later
edits. The restoration reran Ruff, all 1,135 offline tests and the historical
audit; its three dedicated replay commands reproduced all 62 report files.
Current manuscript/figure checks are in the restoration review. Tests marked
`live` require explicit authorization.

## Limits and next-agent priorities

Keep conclusions within the 31-feature representation, selected references and
delivered services. Capture provenance and perceptual validity remain unresolved;
human ratings, independent capture replication and learned-feature validation have
not been performed. Retrieval is distinguishability, not semantic adherence.
Study 2 uses one service, six fixed scenes and one generic clause; its unresolved
interactions do not establish equivalence. Returned geometry and quality differ
from requested settings, so the estimates do not isolate a backend mechanism or
style effect at matched rendering settings.

Public archival release and external raw-media access remain pending; see the
[paper access statement](../paper/README.md#release-and-access-status). A merge
into `main` does not establish either. Do not promise public reproducibility beyond
the artifacts actually redistributed.

The user prefers English reasoning and documents, skeptical review and infrequent
progress updates. Address requested paper corrections against existing evidence;
do not launch more experiments simply to improve the manuscript. Update
[STATUS.md](STATUS.md) for operational changes and [INDEX.md](INDEX.md) for changed
canonical documents. Preserve user work and never expose `.env` or API keys.
