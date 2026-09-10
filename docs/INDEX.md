# Documentation index

## Current guidance

| Document | Purpose |
| --- | --- |
| [Project README](../README.md) | Research question, current result and quickstart |
| [Current status](STATUS.md) | Completed work, limitations and latest verification |
| [Agent handover](AGENT_HANDOVER.md) | Completed work, paper-correction workflow and working constraints |
| [Analysis catalog](ANALYSES.md) | Numerical, report-plot and manuscript-figure commands |
| [Architecture](ARCHITECTURE.md) | Code and data dependencies |
| [Artifact policy](ARTIFACTS.md) | What must be retained and what is disposable |
| [Contributing](../CONTRIBUTING.md) | Development and verification workflow |
| [Agent rules](../AGENTS.md) | Repository-wide research and editing boundaries |

## Current paper and scientific record

| Material | Link |
| --- | --- |
| New validation and replication follow-up | [Measurement challenge protocol](../studies/painter_measurement_validation_v1/PROTOCOL.md) tests fixed computational image changes and common-square sensitivity; [naming/palette successor protocol](../studies/painter_naming_replication_v1/PROTOCOL.md) specifies a separate bounded collection. See [current status](STATUS.md) for gates and actual execution. |
| Public numerical reproduction | [Published release and verification](../reports/paper_reproducibility_v1/pprv1-20260910/REPORT.md), [implementation guide](../studies/paper_reproducibility_v1/README.md); an allowlisted package with explicit numerical replay coverage, separate from raw-media access and independent research replication. |
| English manuscript | [PDF](../paper/paper.pdf), [source/build guide](../paper/README.md), [validation follow-up reviews and responses](reviews/20260910_validation_followup/REVIEW.md), [preceding academic reviews](reviews/20260909_academic_review/REVIEW.md), [four-painter restoration](reviews/20260909_four_painter_restoration.md); [scored reviews of the prior 19-page revision](reviews/20260909_scored_review/REVIEW.md), [earlier integration review](reviews/20260908_manuscript.md) |
| Four-painter descriptive distributions | [Exploration report](../reports/painter_distribution_exploration_v1/REPORT.md), [methods](../studies/painter_distribution_exploration_v1/METHODS.md); 649 references and 1,536 painter-conditioned outputs across Monet, Sisley, Pissarro and Cézanne |
| Four-painter descriptive controls | [Stage A report](../reports/painter_distribution_study_v1/pdsv1-diagnostics-20260906/REPORT.md), [diagnostic scope](../studies/painter_distribution_study_v1/DIAGNOSTICS.md), [retry-contrast presentation](../reports/painter_prompt_retry_v1/ppr1-two-refusals-20260906-r2/REPORT.md); completed grid additionally includes 384 artist-free controls |
| Controlled results | [Full report](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md) |
| Controlled design | [Protocol](../studies/painter_distribution_study_v1/PROTOCOL.md), [main design](../studies/painter_distribution_study_v1/MAIN.md), [inference](../studies/painter_distribution_study_v1/INFERENCE.md) |
| Computational revision | [Full report](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md), [fixed diagnostic protocol](../studies/painter_distribution_revision_v1/PROTOCOL.md) |
| Methodology assessment | [Skeptical review and revision plan](reviews/20260907_methodology/REVIEW_AND_REVISION_PLAN.md) |
| Further validation | [Reference/human study plan](../studies/painter_distribution_revision_v1/VALIDATION_PLAN.md), [literature comparison](../studies/painter_distribution_revision_v1/LITERATURE_MATRIX.md) |
| Technical retry correction | [Prospective exact-503 recovery protocol](../studies/painter_responsiveness_recovery_v1/PROTOCOL.md); unchanged v2 scientific design, disjoint replacement run |
| Computational responsiveness v2 | [Scientific synthesis](../reports/painter_responsiveness_v2/REPORT.md), [192-image primary experiment](../reports/painter_responsiveness_v2/prv2-oauth-recovery-20260908/experiment/REPORT.md), [retrieval results](../reports/painter_responsiveness_v2/prv2-oauth-20260908/diagnostics/REPORT.md), [protocol and implementation](../studies/painter_responsiveness_v2/README.md), [review record](reviews/20260908_computational_responsiveness/REVIEW.md) |
| Descriptive quantile corrigendum | [Corrected displays and affected-record tables](../reports/painter_responsiveness_quantiles_v1/prqv1-20260908/REPORT.md), [exact-weight protocol](../studies/painter_responsiveness_quantiles_v1/PROTOCOL.md); medians corrected, primary inference and range occupancy unchanged |
| Responsiveness implementation v1 | [Protocol and continuation guide](../studies/painter_responsiveness_v1/README.md), [capture feasibility](../studies/painter_responsiveness_v1/CAPTURE_FEASIBILITY.md) |
| Historical research proposal | [Why generated paintings differ: mechanism report and proposal](RESEARCH_IDEA_20260908.md), with primary-paper readings and eight numerical/metadata case studies; later execution is recorded in current status |

The earlier validation documents are frozen planning artifacts. The computational v2 successor removes human ratings as a prerequisite for its
narrower service-response claim. The earlier v1 human-validation scope remains
unchanged. See current status for executed stages. Reviews are maintainer-run LLM reviews. The current paper is the only
manuscript directory; earlier writing is retained in Git history.
The earlier scored review's 8.5417 average applies to the prior 19-page manuscript;
the current academic review uses a different, fixed three-aspect rubric and
records its own manuscript hashes and scores. The restored analyses are post-result descriptive
evidence: two later retries and unresolved requested-alias identities retain their
original qualifications, and the incomplete prompt study's primary inference is
not reinstated. Their source bundles remain terminal.

## Earlier evidence

These are historical study outputs, not instructions to resume collection. Their
full ledgers, protocols and committed dependencies remain at their existing paths.

| Study | Entry points |
| --- | --- |
| Two-refusal retry follow-up | [Original descriptive report](../reports/painter_prompt_retry_v1/ppr1-two-refusals-20260906/REPORT.md), [protocol](../studies/painter_prompt_retry_v1/PROTOCOL.md); the current presentation is linked above |
| Prompt-study missingness supplement | [Report](../reports/painter_prompt_supplement_v1/ppss1-missingness-20260905/REPORT.md), [protocol](../studies/painter_prompt_supplement_v1/PROTOCOL.md) |
| Original repeated prompt study | [Report](../reports/painter_prompt_study_v1/pps1-gpt-prompts-20260905/REPORT.md), [protocol](../studies/painter_prompt_study_v1/PROTOCOL.md) |
| Existing-data feature distances | [Report](../reports/painter_feature_distance_v1/REPORT.md) |
| Feature-generation v2 | [Empirical report](../reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS.md), [protocol](../studies/painter_feature_generation_v2/PROTOCOL.md) |
| Feature-generation v1 feasibility | [Study guide](../studies/painter_feature_generation_v1/README.md), [canonical Protocol 2.1](../studies/painter_feature_generation_v1/PROTOCOL_2.1.md), [terminal determination](../reports/painter_feature_generation_v1/R1_DETERMINATION_KO.md) |
| Earlier literature work | [Literature index](../literature_reviews/README.md), [synthesis](../literature_reviews/SYNTHESIS.md), [method decisions](../literature_reviews/METHOD_DECISIONS.md) |

Historical protocols and reports can be hash-bound dependencies. Their presence
does not make them current operating instructions. The analysis catalog replaces
the retired operational workflow guides; consult current status before acting on
an older stage description.

- [Post-result painter-naming geometry protocol](../studies/painter_naming_geometry_v1/PROTOCOL.md): held-scene global moment benchmark, temporal transfer and repeat correction.

- [Evaluation-centering successor](../studies/painter_naming_centering_v1/PROTOCOL.md): separates mean anchoring from the fitted scalar using retained evaluation-free vectors.

- [Prospective actual-clause validation](../studies/painter_clause_validation_v1/PROTOCOL.md):
  terminal new-scene OAuth experiment; both original primary comparisons unavailable.
- [Clause allocation and simulation qualification](../studies/painter_clause_validation_v1/PRECISION.md).
- [Public geometry addendum verification](../reports/paper_geometry_reproducibility_v1/ppgv1-20260910/REPORT.md).

- [Clause numerical-release guide](../studies/paper_clause_reproducibility_v1/README.md):
  terminal export and standalone public replay for the two separate clause cohorts.
- [Clause exporter review](reviews/20260910_substantive_revision/CLAUSE_RELEASE_REVIEW.md):
  bounded synthetic qualification and remaining real-release checks.

- [Single Cezanne/generic successor](../studies/painter_clause_successor_v1/PROTOCOL.md):
  completed 96-output comparison with a fixed .025 primary threshold.
- [Availability-triggered decision](../studies/painter_clause_successor_v1/DESIGN_DECISION.md):
  fixed before predecessor feature extraction; no pooling or further replacement.

- [Stopped clause transport audit](reviews/20260910_substantive_revision/CLAUSE_TERMINAL_AUDIT_2.md):
  exact terminal accounting and unavailable inference for the original 288-slot run.

- [Stopped clause measurement audit](reviews/20260910_substantive_revision/CLAUSE_MEASUREMENT_AUDIT_2.md):
  all 864 rows, exact scaler/provenance checks and preserved unavailable endpoints.
- [Combined clause release review](reviews/20260910_substantive_revision/CLAUSE_COMBINED_RELEASE_REVIEW.md):
  separate replay/provenance for both cohorts, synthetic final-stage verification.
- [Successor terminal and measurement audit](reviews/20260910_substantive_revision/CLAUSE_SUCCESSOR_TERMINAL_AUDIT_2.md):
  all 96 response hashes, 288 vectors, source/receipt bindings and exact report replay.
- [Successor independent arithmetic audit](reviews/20260910_substantive_revision/CLAUSE_SUCCESSOR_RESULTS_AUDIT_1.md):
  separate energy, trace and 99,999-draw calculation with implementation involvement disclosed.
- [Public clause addendum verification](../reports/paper_clause_reproducibility_v1/pcrv1-20260910/REPORT.md):
  history-free publication and exact fresh local/anonymous replay of both separate cohorts.
