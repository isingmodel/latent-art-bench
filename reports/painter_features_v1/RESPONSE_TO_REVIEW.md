# Response to independent skeptical review

PR: [#1](https://github.com/isingmodel/latent-art-bench/pull/1)

First-pass review: [GitHub comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5488634370)

Second-pass review: [GitHub comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5488825142)

Third-pass review: [GitHub comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489036477)

Fourth-pass review: [GitHub approval](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489144824)

Response status: fourth pass approved exact head `9561a99f`; all P1 and P2 findings are closed at
the prospective design-framework level. The one nonblocking P3 notation clarification is
incorporated in the final closure-only revision; its exact-head confirmation is recorded externally
on the PR rather than triggering another metadata-only commit.

## 1. Response policy

Every P1 and P2 finding is treated as actionable. No objection is dismissed because the current
artifact is “only documentation.” When a desired effect is not identifiable, the response narrows,
fails, or leaves the claim unexecuted; it does not substitute a more convenient estimand.

This response authorizes no empirical operation. Pilots 0-3 remain frozen, the Pilot 3 Met R2
cohort remains terminally closed, and the revision does not access artworks, model weights, sealed
external data, or generation services.

## 2. Finding-by-finding response

| Finding | Revision | Primary artifacts | Pre-re-review status |
|---|---|---|---|
| P1-1 joint common support | Added claim-specific common-support and shared-workflow sets, connected incidence, at least two painters per exchangeability cell, hard work floors subordinate to simulation, fixed weights, and joint source-by-content transfer. After the second pass, bound the target and every hard neighbor to one immutable panel-wide support; pairwise-only supports cannot yield a panel minimum, quantile, omnibus, or canonical fidelity claim. | `MEASUREMENT_PROTOCOL.md`; `VALIDATION_PROTOCOL.md`; `ANALYSIS_AND_CLAIMS.md` | Third pass verified closed in the authoritative protocols; review 05 consistency fixed below |
| P1-2 conditioned estimands | Defined a standardized real painter distribution over frozen common support and source-workflow weights, permitted exact matched alternatives, prohibited extrapolation, and specified that generated images receive no museum-source value. The same panel-wide target distribution now governs every hard-neighbor and generated criterion. | `VALIDATION_PROTOCOL.md`; `ANALYSIS_AND_CLAIMS.md` | Third pass verified closed in the authoritative protocols; review 05 consistency fixed below |
| P1-3 multiplicity | Replaced family-local qualification with an experiment-wide omnibus hierarchy and closed-testing or jointly calibrated max-statistic requirement covering families, coordinates, scales, encoders, painters, neighbors, transfer, and human endpoints; the external set reuses the same tree. | `ANALYSIS_AND_CLAIMS.md`; `METHOD_DECISIONS.md` | Third pass verified closed in the authoritative policy; review 05 FDR ambiguity fixed below |
| P1-4 generator criteria | Added absolute real-real-calibrated target agreement, paired movement, worst and lower-tail hard-neighbor specificity, precision, density, recall, coverage, contraction, content coherence, availability, and one cross-document conjunctive rule. After the second pass, precision and density, recall and coverage, coherence, and availability are explicitly all binding; contraction and movement are mandatory nongating outcomes. | `ANALYSIS_AND_CLAIMS.md`; `VALIDATION_PROTOCOL.md`; `SYNTHESIS.md`; `RESEARCH_REPORT.md` | Third pass verified the four authoritative documents; review 05 and H9 consistency fixed below |
| P1-5 citation integrity | Rebuilt every disputed matrix row from the primary source, expanded the DOI-keyed consistency audit, corrected additional mislabeled rows found by that audit, and aligned the digitization reviews. | `EVIDENCE_MATRIX.csv`; `BIBLIOGRAPHY.md`; reviews 01 and 03 | Central errors verified closed; two residual P2 author labels fixed below |
| P1-6 Kim replication language | Replaced exact-replication promises with source-faithful, versioned compatibility reconstruction; declared repaired A an adaptation and C provisional until its complete artifact contract is recovered. | `SYNTHESIS.md`; review 02; `METHOD_DECISIONS.md`; study README; `RESEARCH_REPORT.md` | Third pass verified closed |
| P1-7 reproduction identification | Required a work × provider × capture × derivative × processing incidence matrix, design-rank audit, repeated works across provider pairs, multiple works per pair, repeated derivatives, crossed processing branches, and collapse of non-identifiable effects. After the second pass, expanded the displayed model to index the provider→capture→delivery→processing hierarchy explicitly. | `MEASUREMENT_PROTOCOL.md`; `RESEARCH_REPORT.md` | Third pass verified closed |
| P2-1 Pilot 2 terminology | Confined the result to pooled artist-label predictability within the fixed Pilot 2 atlas and stated that no transferable painter feature or generated-output effect was established. After the second pass, removed raw balanced-accuracy rankings between the two-class source and four-class painter tasks. | `SYNTHESIS.md`; reviews 00, 02, and 03; `RESEARCH_REPORT.md` | Third pass verified closed |
| P2-2 same-work retrieval | Made retrieval diagnostic and moved the gate to paired-capture equivalence of painter margins and profile location/spread. | `VALIDATION_PROTOCOL.md`; `RESEARCH_REPORT.md` | Third pass verified closed |
| P2-3 human cue controls | Added attribution/source/condition blinding, frozen signature/text masking, post-judgment recognition, unfamiliar-work primary inference, recognized/unmasked sensitivities, and independent final raters/works. | `VALIDATION_PROTOCOL.md`; `RESEARCH_REPORT.md` | Third pass verified closed; H9 scope fixed below |
| P2-4 external source independence | Required an unopened institution/capture workflow and full derivative disjointness for `qualified_core`; other-axis-only confirmation is domain-limited. | `VALIDATION_PROTOCOL.md`; `RESEARCH_REPORT.md` | Third pass verified closed |
| P2-5 missingness | Added frozen frame denominators, hard cell minima, completion rules, differential-selection modeling, MNAR pattern-mixture/bound/tipping analyses, and terminal domain-limiting/failure rules. | `ANALYSIS_AND_CLAIMS.md`; `METHOD_DECISIONS.md`; `RESEARCH_REPORT.md` | Third pass verified closed |
| P2-6 shared controls | Defined the whole content-cell × model/version × path × seed bundle as the future resampling cluster and required joint resampling of shared real references; independent controls must be painter-indexed. | `ANALYSIS_AND_CLAIMS.md`; `METHOD_DECISIONS.md`; `RESEARCH_REPORT.md` | Third pass verified closed |
| P2-7 source-level selection | Required outer source-workflow nested selection of coordinates, scales, encoders, tolerances, dimensions, and metric hyperparameters; otherwise the claim is limited to seen sources. | `VALIDATION_PROTOCOL.md`; `METHOD_DECISIONS.md`; `RESEARCH_REPORT.md` | Third pass verified closed |
| P2-8 design readiness | Relabeled the package as a non-executable, non-preregistered prospective design framework and enumerated the separate execution-freeze artifact required before operations. | study README; all protocols; `SYNTHESIS.md`; `RESEARCH_REPORT.md` | Third pass verified closed by narrowing |
| P2-9 retrospective search | Relabeled the search and stopping process as retrospective, disclosed absent saved result/screening manifests and unstable result totals, and avoided invented denominators. After the second pass, identified the actual 11-column matrix, labeled the rich per-source schema a future requirement, and disclosed that 138 detailed evidence cards do not exist. | `SEARCH_PROTOCOL.md`; `SEARCH_LOG.md`; literature README; `SYNTHESIS.md`; `RESEARCH_REPORT.md` | Third pass verified closed |
| P2-10 null is not invariance | Reworded Redies/Groß to absence of a statistically significant aggregate group difference and explicitly noted the lack of equivalence and work-level repeatability tests. | reviews 01 and 03; evidence matrix | Third pass verified closed |

## 3. Third-pass residual response

| Third-pass finding | Revision | Primary artifacts | Pre-fourth-pass status |
|---|---|---|---|
| P1-T1 stale alternate panel and generator rule | Rewrote review 05 around one immutable `target + all hard neighbors` support and weights; prohibited pairwise aggregation; made both worst and lower-tail specificity rules simultaneous; and aligned the six binding plus two mandatory nongating outcomes with the canonical documents. | review 05 | Fourth pass verified closed |
| P1-T2 sign-only real hard-neighbor gate | Replaced sign retention with simultaneous lower confidence bounds above frozen positive SESOIs for every hard-neighbor margin at every required transfer endpoint. Sign alone is diagnostic. Protocol 1.4 additionally defines the adjusted panel statistic `min_h(M_h - delta_h)` for heterogeneous neighbor SESOIs. | `VALIDATION_PROTOCOL.md` 1.4 | Fourth pass verified the P1 closed; P3 notation clarified afterward |
| P2-T1 confirmatory FDR ambiguity | Restricted FDR to labeled exploratory coordinates that cannot qualify a method or support a project-level claim; all confirmatory selection and success decisions use strong experiment-wide FWER control. | review 05 | Fourth pass verified closed |
| P2-T2 H9 standalone-success ambiguity | Renamed H9 as human prompt-movement evidence for G2 only and prohibited it from establishing canonical fidelity or rescuing a failed binding conjunct. | review 04 | Fourth pass verified closed |
| P2-T3 author labels | Corrected PF023 to Qi, Taeb, and Hughes; corrected PF029 to Redies and Brachmann; and reconciled the Qi/Taeb order in review 01. | `EVIDENCE_MATRIX.csv`; review 01 | Fourth pass verified closed |
| P3 pass provenance | Replaced the single reviewed range with an exact pass table and clarified that exact objects and verdicts are preserved in Git history and linked GitHub comments. | `SKEPTICAL_REVIEW.md` | Fourth pass accepted |
| P3 heterogeneous-neighbor SESOI notation | Replaced the ambiguous “equivalent panel-worst” phrase with an explicit subtract-before-minimum statistic and applied the same rule to the generated worst and lower-tail summaries. | validation protocol 1.4; review 05; research report 1.4 | Incorporated; narrow exact-head confirmation required |

## 4. Changed claim boundary

The revision makes the following hierarchy explicit:

1. a file-level coordinate may describe only declared digital bytes and preprocessing;
2. a reproduction-associated coordinate must pass controlled perturbation and identifiable
   paired-capture tests;
3. a painter-associated coordinate must additionally pass common-support painter specificity,
   joint source-by-content transfer, nuisance baselines, experiment-wide multiplicity, human
   construct validation, and unopened-workflow external confirmation; and
4. a future generated-output claim must additionally pass conjunctive absolute agreement,
   panel-wide hard-neighbor specificity, precision, density, recall, coverage, content coherence,
   and availability rules.

Failure lowers the disposition. Nothing in the revised PR qualifies an actual painter coordinate,
opens a historical holdout, or authorizes generation.

## 5. Closure verification record

The fourth pass independently verified all P1 and P2 closures at exact head `9561a99f`. It also
rechecked the 138-by-11 matrix, all source and stable identifiers, 102 DOI joins, the 36 non-DOI
identities, local Markdown links, diff integrity, and Ruff. The approval explicitly states that it
qualifies no coordinate and authorizes no empirical operation.

Local evidence-bearing-workspace QA additionally passed all 490 offline tests. The reviewer's
isolated exact-commit checkout reported 487 passed and one skipped; its only two failures required
the intentionally uncommitted historical Lee PDF. That known historical-evidence dependency is
unrelated to this documentation-only revision and is not “fixed” by committing or replacing the
ignored evidence byte.

The final closure-only commit adds this record and the reviewer's nonblocking heterogeneous-SESOI
notation. A narrow exact-head confirmation is kept as a public PR comment rather than recursively
amending this file after every confirmation. The final user report and PR body link that external
confirmation.
