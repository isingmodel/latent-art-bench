# Response to independent skeptical review

PR: [#1](https://github.com/isingmodel/latent-art-bench/pull/1)

First-pass review: [GitHub comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5488634370)

Response status: revisions implemented locally; closure requires fresh reviewer inspection of the
updated PR

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
| P1-1 joint common support | Added claim-specific common-support and shared-workflow sets, connected incidence, at least two painters per exchangeability cell, hard work floors subordinate to simulation, fixed weights, joint source-by-content transfer, and fail/narrow rules. | `MEASUREMENT_PROTOCOL.md`; `VALIDATION_PROTOCOL.md`; `ANALYSIS_AND_CLAIMS.md` | Implemented; pending reviewer verification |
| P1-2 conditioned estimands | Defined a standardized real painter distribution over frozen common support and source-workflow weights, permitted exact matched alternatives, prohibited extrapolation, and specified that generated images receive no museum-source value. | `VALIDATION_PROTOCOL.md`; `ANALYSIS_AND_CLAIMS.md` | Implemented; pending reviewer verification |
| P1-3 multiplicity | Replaced family-local qualification with an experiment-wide omnibus hierarchy and closed-testing or jointly calibrated max-statistic requirement covering families, coordinates, scales, encoders, painters, neighbors, transfer, and human endpoints; the external set reuses the same tree. | `ANALYSIS_AND_CLAIMS.md`; `METHOD_DECISIONS.md` | Implemented; pending reviewer verification |
| P1-4 generator criteria | Added absolute real-real-calibrated target agreement, paired movement, worst and lower-tail hard-neighbor specificity, precision/density, recall/coverage, contraction, content coherence, availability, and a conjunctive success rule. | `ANALYSIS_AND_CLAIMS.md`; `VALIDATION_PROTOCOL.md`; `SYNTHESIS.md`; `RESEARCH_REPORT.md` | Implemented; pending reviewer verification |
| P1-5 citation integrity | Rebuilt every disputed matrix row from the primary source, expanded the DOI-keyed consistency audit, corrected additional mislabeled rows found by that audit, and aligned the digitization reviews. | `EVIDENCE_MATRIX.csv`; `BIBLIOGRAPHY.md`; reviews 01 and 03 | Implemented by citation audit; pending final QA and reviewer verification |
| P1-6 Kim replication language | Replaced exact-replication promises with source-faithful, versioned compatibility reconstruction; declared repaired A an adaptation and C provisional until its complete artifact contract is recovered. | `SYNTHESIS.md`; review 02; `METHOD_DECISIONS.md`; study README; `RESEARCH_REPORT.md` | Implemented; pending reviewer verification |
| P1-7 reproduction identification | Required a work × provider × capture × derivative × processing incidence matrix, design-rank audit, repeated works across provider pairs, multiple works per pair, repeated derivatives, crossed processing branches, and collapse of non-identifiable effects. | `MEASUREMENT_PROTOCOL.md`; `RESEARCH_REPORT.md` | Implemented; pending reviewer verification |
| P2-1 Pilot 2 terminology | Confined the result to pooled artist-label predictability within the fixed Pilot 2 atlas and stated that no transferable painter feature or generated-output effect was established. | `SYNTHESIS.md`; review 02; `RESEARCH_REPORT.md` | Implemented; pending reviewer verification |
| P2-2 same-work retrieval | Made retrieval diagnostic and moved the gate to paired-capture equivalence of painter margins and profile location/spread. | `VALIDATION_PROTOCOL.md`; `RESEARCH_REPORT.md` | Implemented; pending reviewer verification |
| P2-3 human cue controls | Added attribution/source/condition blinding, frozen signature/text masking, post-judgment recognition, unfamiliar-work primary inference, recognized/unmasked sensitivities, and independent final raters/works. | `VALIDATION_PROTOCOL.md`; `RESEARCH_REPORT.md` | Implemented; pending reviewer verification |
| P2-4 external source independence | Required an unopened institution/capture workflow and full derivative disjointness for `qualified_core`; other-axis-only confirmation is domain-limited. | `VALIDATION_PROTOCOL.md`; `RESEARCH_REPORT.md` | Implemented; pending reviewer verification |
| P2-5 missingness | Added frozen frame denominators, hard cell minima, completion rules, differential-selection modeling, MNAR pattern-mixture/bound/tipping analyses, and terminal domain-limiting/failure rules. | `ANALYSIS_AND_CLAIMS.md`; `METHOD_DECISIONS.md`; `RESEARCH_REPORT.md` | Implemented; pending reviewer verification |
| P2-6 shared controls | Defined the whole content-cell × model/version × path × seed bundle as the future resampling cluster and required joint resampling of shared real references; independent controls must be painter-indexed. | `ANALYSIS_AND_CLAIMS.md`; `METHOD_DECISIONS.md`; `RESEARCH_REPORT.md` | Implemented; pending reviewer verification |
| P2-7 source-level selection | Required outer source-workflow nested selection of coordinates, scales, encoders, tolerances, dimensions, and metric hyperparameters; otherwise the claim is limited to seen sources. | `VALIDATION_PROTOCOL.md`; `METHOD_DECISIONS.md`; `RESEARCH_REPORT.md` | Implemented; pending reviewer verification |
| P2-8 design readiness | Relabeled the package as a non-executable, non-preregistered prospective design framework and enumerated the separate execution-freeze artifact required before operations. | study README; all protocols; `SYNTHESIS.md`; `RESEARCH_REPORT.md` | Implemented; pending reviewer verification |
| P2-9 retrospective search | Relabeled the search and stopping process as retrospective, disclosed absent saved result/screening manifests and unstable result totals, and avoided invented denominators. | `SEARCH_PROTOCOL.md`; `SEARCH_LOG.md`; `SYNTHESIS.md`; `RESEARCH_REPORT.md` | Implemented by citation audit; pending final QA and reviewer verification |
| P2-10 null is not invariance | Reworded Redies/Groß to absence of a statistically significant aggregate group difference and explicitly noted the lack of equivalence and work-level repeatability tests. | reviews 01 and 03; evidence matrix | Implemented; pending reviewer verification |

## 3. Changed claim boundary

The revision makes the following hierarchy explicit:

1. a file-level coordinate may describe only declared digital bytes and preprocessing;
2. a reproduction-associated coordinate must pass controlled perturbation and identifiable
   paired-capture tests;
3. a painter-associated coordinate must additionally pass common-support painter specificity,
   joint source-by-content transfer, nuisance baselines, experiment-wide multiplicity, human
   construct validation, and unopened-workflow external confirmation; and
4. a future generated-output claim must additionally pass conjunctive absolute agreement,
   hard-neighbor specificity, target-support, coverage, content coherence, and availability rules.

Failure lowers the disposition. Nothing in the revised PR qualifies an actual painter coordinate,
opens a historical holdout, or authorizes generation.

## 4. Verification required before closure

The following evidence is required before this response can be marked closed:

- all matrix rows parse and every source ID remains unique;
- DOI/title/method identities reconcile across matrix, bibliography, and reviews;
- local Markdown links resolve;
- prohibited overclaim phrases are absent;
- `git diff --check`, Ruff, and the full offline test suite pass;
- the revised commit is pushed to PR #1; and
- the same skeptical reviewer inspects the revised diff and explicitly reports whether each P1 and
  P2 finding is closed, narrowed, or still open.

The final verification record and re-review verdict will be appended after those steps; they are
not predeclared successful.
