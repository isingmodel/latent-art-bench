# Independent skeptical research review

Review target: [PR #1](https://github.com/isingmodel/latent-art-bench/pull/1)

Review passes:

| Pass | Exact committed range | Verdict | Public record |
|---|---|---|---|
| 1 | `612d09e4..c70589fc` | **request changes** | [comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5488634370) |
| 2 | `c70589fc..e93a8ece` | **request changes** | [comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5488825142) |
| 3 | `e93a8ece..f3497b7d` | **request changes** | [comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489036477) |
| 4 | `f3497b7d..9561a99f` | **approve** | [comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489144824) |
| 5 | `9561a99f..17ed93db` | **request changes** | [comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489200986) |

Review status: five passes recorded. The fourth **approved** the prospective design framework at
`9561a99f`; the fifth found one P2 inconsistency introduced by incomplete propagation of the P3
clarification. That generated-output rule is aligned in the final revision, whose exact-head
closure verdict is recorded externally on the PR to avoid a recursive metadata commit.

Reviewer role: independent skeptical researcher subagent; the reviewer made no project edits

## 1. Review mandate

The reviewer was asked to treat the pull request as a proposed scientific measurement framework,
not as a documentation or software-style exercise. The audit covered:

- construct definition and consistency with Pilot 2's painter-feature aim;
- identification under source, content, medium, phase, and reproduction confounding;
- sampling units, dependence, missingness, multiplicity, and claim language;
- Kim A/C artifact identity and reproducibility;
- citation fidelity against primary sources;
- internal consistency among the synthesis, evidence matrix, protocols, and report; and
- whether the proposed gates could actually prevent a nuisance shortcut from being qualified.

The reviewer inspected the frozen Pilot 2 protocol, analysis, qualification, and report; all 18
new files in the initial PR; Kim's released source at revision `7da12358`; and the primary sources
needed to audit disputed method summaries. The consolidated public request-changes verdict is
preserved in the
[GitHub review comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5488634370);
this document preserves the reviewer's fuller ranked memo, including issues that the public comment
grouped together.

## 2. Severity convention

- **P0:** invalidates or makes the project unsafe to proceed in any form.
- **P1:** could falsely qualify a painter feature or makes a central claim non-identifiable or
  non-reproducible; must be corrected before approval.
- **P2:** materially weakens validity, transparency, or the permitted claim; must be corrected or
  explicitly accepted as a narrower limitation.
- **P3:** nonblocking improvement.

The reviewer found no P0 issue, seven P1 blockers, and ten P2 findings.

## 3. P1 blockers

### P1-1 — no joint common-support invariant

The initial corpus rule required each painter to span multiple sources and content strata only
marginally. Painter could still be aliased with a source × content × medium × date combination,
and a proposed permutation block could contain only one painter. Separate leave-source and
leave-content tests do not identify a joint painter effect.

Required correction: publish a connected painter-by-joint-nuisance incidence table; freeze hard
cell minima, at least two painters in every exchangeability cell, shared-support weights, and a
joint source-by-content transfer task; narrow or fail the claim when overlap is absent.

### P1-2 — estimands discarded the construct's conditioning variables

The construct was written as a conditional distribution, but the real-specificity and future
generator equations used an unqualified painter distribution. Its value could therefore change
with the convenience mixture of sources, subjects, media, or phases. Generated images also have no
museum-source value.

Required correction: define a standardized painter distribution on frozen joint common support or
use exact matched conditional contrasts; state the target weights, source/capture treatment,
finite-reference uncertainty, and behavior outside support. Do not impute museum source to a
generated image.

### P1-3 — multiplicity did not cover winner selection

The initial policy controlled error within each family while permitting any of many families,
coordinates, scales, encoders, painters, neighbors, and human endpoints to qualify. Thus the
project-level claim that at least one painter feature exists had no experiment-wide error control.

Required correction: freeze a primary omnibus or hierarchical closed-testing family covering
every selection stage and preserve the same tree for sealed external confirmation.

### P1-4 — generator success could omit absolute fit and target support

Relative named-versus-control movement could be favorable while returned outputs remained far
from the target, failed the closest hard neighbor, or occupied a narrow off-target region. The
high-level report required stronger outcomes than the canonical estimand file did.

Required correction: bind future success to absolute target discrepancy/equivalence,
worst-neighbor and lower-tail specificity, precision and density, recall and coverage, content
coherence, and availability robustness. Preserve relative movement as a prompt-effect estimand,
not a substitute for fidelity.

### P1-5 — evidence-matrix method summaries were unreliable

Several matrix rows materially misdescribed the cited method or corpus. The review specifically
identified PF001, PF006, PF013, PF020, and PF041; a subsequent full audit also had to check the
remaining DOI-keyed rows. The thematic prose was often more accurate than the table, creating an
internally inconsistent evidence package.

Required correction: rebuild affected rows from primary methods and cross-check DOI/title/method
identity among the evidence matrix, bibliography, and review tables.

### P1-6 — “exact A and C replication” contradicted the artifact audit

The initial report correctly documented that Kim A is not executable unchanged and that the
released artifacts omit checkpoint, dependency, fixture, and stochastic-realization information,
yet later promised exact replication. Kim C likewise lacks a complete executable artifact
contract.

Required correction: permit only a source-faithful, versioned compatibility reconstruction. Any
repaired A implementation is an adaptation; C remains provisional until its full artifact contract
is recovered and verified.

### P1-7 — the reproduction variance model was not identified by the design

The observation equation separated provider, capture, delivery, and processing effects, but the
sampling prose allowed all captures to be nested uniquely within providers and all derivatives
within captures. Those components cannot be separated from such a design.

Required correction: require a prospective provider/capture incidence matrix and design-rank
audit, repeated works bridging provider pairs, multiple works per pair, repeated derivatives per
capture, and processing branches crossed over reproductions. Collapse inseparable terms and lower
the claim ceiling when the design is rank deficient.

## 4. P2 findings

### P2-1 — Pilot 2 terminology exceeded its evidence

Pilot 2's pooled held balanced accuracy of 0.50 was called painter-associated even though the
framework itself required source transfer and Pilot 2's opposite-source accuracies were 0.25 and
0.375. Its generated-output primary tests were not run.

Required correction: call the result only pooled artist-label predictability within the fixed
Pilot 2 atlas. State that Pilot 2 established neither a transferable painter feature nor a
generated-output effect. Do not call two-class source balanced accuracy stronger or easier than
four-class painter balanced accuracy; report high source predictability together with failed
opposite-source painter transfer without ranking unlike tasks.

### P2-2 — same-work retrieval could select semantics

Exact-work retrieval can reward subject, iconography, or a work-specific defect. Conversely, an
aggregate painter coordinate need not retrieve the exact work to be stable across captures.

Required correction: keep retrieval diagnostic; gate on paired-capture equivalence of painter
margins and profile statistics.

### P2-3 — the human gate omitted binding cue controls

The supporting review recommended blinding and recognition controls, but the gate-defining file
did not require them. Familiar canonical works, signatures, attribution labels, or museum
interfaces could validate recognition or stereotype instead of painterly manner.

Required correction: blind attribution, source, and experimental condition; freeze signature/text
masking; measure familiarity after the primary judgment; use unfamiliar works as primary; report
recognized and unmasked sensitivities; keep final works and raters independent of tuning.

### P2-4 — external confirmation could preserve the source shortcut

Changing any one domain axis allowed new content from the same institutional capture workflow to
count as external confirmation.

Required correction: require an unopened institution/capture workflow and derivative-family
disjointness for `qualified_core`. A change on another axis alone supports only a domain-limited
claim.

### P2-5 — complete-case selection could create an easier corpus

Rights, metadata, profile, resolution, acquisition, and preprocessing exclusions can vary by
painter and source. The initial policy required a missingness summary but did not prevent a
selectively observed subset from qualifying.

Required correction: freeze denominators, cell minima, and completion rules; diagnose differential
selection; run registered missing-not-at-random bounds or tipping analyses; narrow, fail, or leave
unexecuted a claim that is not robust.

### P2-6 — shared-control dependence was underspecified

Pilot 2 reused one painter-free control across several painter contrasts. Painter-wise resampling
would copy that control into nominally independent units and understate uncertainty.

Required correction: resample the entire content × model/version × request-path × seed bundle that
contains the shared control and all named targets; jointly resample shared real references. If
controls are independent, index and freeze them as painter-specific controls.

### P2-7 — leave-source method-selection leakage remained possible

A coordinate could be chosen after inspecting development works from every source and only then be
refit inside a leave-source fold. Refitting does not undo source-informed selection.

Required correction: nest coordinate and hyperparameter selection at the outer source-workflow
level, or limit the claim explicitly to already-seen source domains.

### P2-8 — the framework was not yet executable

Corpus minima, estimators, simulations, SESOIs, thresholds, and terminal actions were deferred.
That is legitimate at a design stage, but “prospectively testable,” “preregistered,” or
“executable” overstated readiness.

Required correction: call the artifact a prospective design framework and require a separate,
reviewed execution-freeze artifact before any acquisition, extraction, external access, or
generation.

### P2-9 — the literature-search audit trail was retrospective

The search protocol and log first appeared together, stable result totals were unavailable for
some interfaces, and no saved result/screening manifests existed. The stopping rule therefore
could not be demonstrated as prespecified. The protocol also promised a rich extraction record for
every retained source, but the 11-column matrix and thematic tables did not instantiate 138 such
evidence cards.

Required correction: describe the work as a broad, retrospectively documented critical review and
retrospective stopping decision. Do not claim preregistration, exhaustive systematic coverage, or
a prospective saturation rule. Describe the detailed extraction schema as a future requirement and
disclose the current per-source evidence-card omission.

### P2-10 — a null group result was paraphrased as invariance

The digitization review described Redies and Groß as showing reproduction-route independence.
Their study reported no statistically significant aggregate group difference; it did not perform
an equivalence test or establish work-level repeatability.

Required correction: state the narrower result and do not infer invariance from failure to reject a
group difference.

## 5. Strengths retained by the reviewer

The request-changes recommendation did not negate several strong aspects of the initial work:

- Pilot 2's numerical reconstruction was accurate.
- The 315 successful outputs, five refusals, incomplete grid, and “primary tests not run” result
  were handled correctly.
- Most Kim A/C limitations were candid and technically accurate.
- CSD's released-checkpoint discrepancy was acknowledged.
- The physical work was treated as the real-image inferential unit.
- The report separated historical empirical evidence from prospective design.
- The package did not claim that any candidate was already qualified.
- Bibliographic title/DOI metadata were broadly sound; the principal citation failures were method
  summaries and consequences in specific evidence-matrix rows.

## 6. First-pass verdict

The scientific direction was defensible, but the initial PR could still qualify a nuisance mixture
as a painter feature and could overstate reproducibility. The reviewer therefore requested changes
and required a fresh review of the revised PR before approval. Closure is recorded in
`RESPONSE_TO_REVIEW.md`. The exact reviewed objects and public verdict remain preserved in Git
history and the linked GitHub comment; this living consolidation is amended to retain findings
that later passes showed had been incompletely transcribed.

## 7. Second-pass re-review

The same reviewer inspected revised head `e93a8ece83a14924cafcd6bfe5a1d92640c36c48` and posted a
second [request-changes comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5488825142).
The re-review closed the experiment-wide multiplicity, identified reproduction design, disputed
citation summaries, Kim artifact language, retrieval, human controls, external workflow,
missingness, shared-control, source-selection, readiness, and Redies/Groß findings. It found the
following residual issues.

### Remaining P1-R1 — hard-neighbor panel support was only pairwise-capable

The general common-support notation allowed a different contrast set for every target-neighbor
pair, while the specificity rule then took a minimum and lower quantile over the full neighbor
panel. Those pairwise margins could represent different contents, sources, and even different
target distributions.

Required correction: define one frozen set containing the target and every hard neighbor; use its
single support and weights for every panel margin and generated criterion. If only pairwise support
exists, prohibit a panel minimum, lower quantile, omnibus specificity decision, or canonical
fidelity claim.

### Remaining P1-R2 — generator-success rules contradicted the canonical rule

The analysis file made content coherence and availability binding and treated precision, density,
recall, and coverage as plural requirements. The synthesis and report instead made coherence and
availability secondary and used “or” between support metrics.

Required correction: use one rule everywhere. Absolute agreement, panel-wide hard-neighbor
specificity, precision **and** density, recall **and** coverage, content coherence, and availability
robustness are all binding. Contraction and paired prompt movement are mandatory nongating outcomes.

### Partial P2-R1 — cross-task balanced-accuracy ranking

The revision still called source performance stronger or substantially better than painter
performance. Because the tasks have different class counts and baselines, their raw balanced
accuracies are not directly ranked.

Required correction: state high source predictability together with failed opposite-source painter
transfer, and explicitly decline the cross-task raw-accuracy ranking.

### Partial P2-R2 — extraction-schema promise

The retrospective search correction still said every source received a rich corpus, preprocessing,
fitting, validation, uncertainty, and artifact record. No such 138-record evidence-card artifact
existed.

Required correction: identify the 11 fields actually present, label the rich schema a future
requirement, and disclose the current omission.

### Residual P2-R3 — observation-model hierarchy notation

The prose required a provider-to-capture-to-delivery hierarchy, but the displayed observation
model indexed only work, reproduction, source, and processing.

Required correction: either display provider, capture, delivery derivative, and processing
explicitly or label the equation as collapsed. Retain the rule that unidentified components must
be combined and the claim ceiling lowered.

The second-pass reviewer also required this review artifact and the response to record the
cross-task and extraction-schema objections instead of overstating closure. No project file was
edited by the reviewer. Ruff, all 490 offline tests, CSV identity joins, and changed local links
passed during that review. A third pass is required after these corrections.

## 8. Third-pass re-review

The same reviewer inspected exact head `f3497b7d0d376b1a581b2701dec74892fe6af6b7` and posted a
third [request-changes comment](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489036477).
The re-review verified closure at the design-framework level of the original and second-pass
findings concerning standardized conditioned estimands, the four authoritative documents'
panel-wide generator rule, cross-task balanced-accuracy language, extraction-schema disclosure,
reproduction hierarchy and collapse rule, Kim artifact language, retrieval, human cue controls,
external-workflow independence, missingness, shared controls, source-level selection, review
status, retrospective search, and null-versus-invariance wording. It nevertheless found two
remaining P1 false-positive paths and three P2 integrity defects elsewhere in the package.

### Remaining P1-T1 — a thematic review retained an alternate success rule

Review 05 still used unstandardized target/neighbor references, permitted a worst **or**
lower-quantile hard-neighbor decision, omitted content coherence from its adopted outcomes, and did
not distinguish the six binding outcome families from contraction and prompt movement. That stale
summary contradicted the canonical analysis, validation, synthesis, and report.

Required correction: use one immutable target-plus-all-hard-neighbors support and weight system;
prohibit aggregating pairwise-only supports; require simultaneous passage of both the panel-worst
and lower-tail rules; and state the same six binding plus two mandatory nongating outcome families.

### Remaining P1-T2 — real painter qualification required hard-neighbor sign only

Validation Gate 4 could qualify a coordinate when each hard-neighbor point estimate merely retained
a positive sign, even if the closest margin was arbitrarily small or uncertain.

Required correction: at every required transfer endpoint, require a simultaneous lower confidence
bound above the frozen positive SESOI for every hard-neighbor margin, or equivalently for the
jointly calibrated panel-worst margin. Treat sign retention as diagnostic only.

### Remaining P2-T1 — confirmatory FDR ambiguity

Review 05 listed a false-discovery procedure as a possible confirmatory tool, contradicting the
analysis policy's strong experiment-wide FWER rule.

Required correction: reserve FDR for labeled exploratory coordinates that cannot qualify a method
or support any project-level, external-confirmation, or generated-success claim.

### Remaining P2-T2 — H9 could be read as standalone generative success

The human-validation H9 gate paired a prompt-movement effect with the failure disposition “no
generative painter-feature success claim.” It could therefore be read as authorizing success
without absolute agreement, both panel-wide specificity rules, four support metrics, content
coherence, and availability.

Required correction: label H9 as human prompt-movement evidence for G2 only and state explicitly
that it cannot establish canonical painter fidelity or rescue any failed binding conjunct.

### Remaining P2-T3 — two matrix author labels were wrong

PF023 attributed DOI `10.1016/j.sigpro.2012.09.025` to “Taeb et al.” instead of Qi, Taeb, and
Hughes. PF029 reversed the author order for DOI `10.3389/fnins.2017.00593`, whose authors are
Redies and Brachmann. The identifiers, method summaries, and dispositions were otherwise correct.

Required correction: reconcile both short citations with the audited bibliography and correct the
same Qi/Taeb order in the thematic interpretable-feature review.

The third-pass reviewer also requested this pass-by-pass range table because the previous single
range did not describe the living review artifact. The reviewer audited committed objects only,
made no project edits, and required another exact-head review after correction.

## 9. Fourth-pass approval

The same reviewer inspected exact head `9561a99f741e04216279d34183993f25985ac289` and posted an
[approve verdict](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489144824).
No P0, P1, or P2 finding remained. The reviewer verified that:

- review 05 uses one immutable target-plus-all-hard-neighbor support and weight system, prohibits
  pairwise aggregation, requires both specificity rules, and states the six binding plus two
  mandatory nongating outcome families;
- Validation Gate 4 requires simultaneous lower bounds above frozen positive SESOIs for every
  hard neighbor at every required transfer endpoint, while sign alone is diagnostic;
- strong experiment-wide FWER governs qualification, winner selection, external confirmation,
  and generated-success claims, while FDR is exploratory-only;
- H9 supports only G2 human prompt-movement evidence and cannot establish painter fidelity;
- PF023 and PF029 author identities reconcile across primary metadata, bibliography, matrix, and
  thematic review; and
- the review, response, and report preserve the three request-changes rounds without predeclaring
  closure.

The approval is strictly at the prospective design-framework level. It qualifies no coordinate,
establishes no empirical painter feature, and authorizes no acquisition, extraction, holdout
access, transport, or generation.

### Nonblocking P3 clarification incorporated after approval

The reviewer noted that calling a panel-worst rule “equivalent” to per-neighbor SESOI tests is
ambiguous when neighbors have different SESOIs. Validation protocol 1.4 and report 1.4 therefore
define the adjusted panel statistic explicitly:

\[
T_{a,e}^{panel}=\min_{h\in H_a}\{M_{a,h,e}-\delta_{a,h,e}\},
\]

with simultaneous uncertainty and a required lower bound above zero. Review 05 applies the same
subtract-before-aggregation rule to both the generated panel-worst and lower-tail statistics. This
is a clarification of the already approved fail-closed per-neighbor rule, not a relaxed criterion.

The reviewer's committed-object QA passed diff integrity, the 138-by-11 evidence matrix and source
identity checks, DOI joins, local Markdown links, and Ruff. In an isolated exact-commit checkout,
the suite reported 487 passed and one skipped; two failures required an intentionally uncommitted
historical Lee PDF and were unrelated to the documentation-only revision. In the evidence-bearing
workspace, where that preserved historical byte exists, the full offline suite passed all 490
tests. The final closure-only commit requires one narrow exact-head confirmation recorded on the
PR; adding that later URL here would itself create a new unreviewed commit.

## 10. Fifth-pass exact-head correction

The reviewer inspected exact head `17ed93db2f5b5f3282a4cd2af9cc8756c9648690` and posted a
[request-changes verdict](https://github.com/isingmodel/latent-art-bench/pull/1#issuecomment-5489200986).
The real Gate 4 adjusted-SESOI rule, provenance, QA record, and every earlier P0-P2 closure remained
sound. One P2 inconsistency remained in generated-output specificity:

- review 05 correctly bound
  \(T_a^{worst}=\min_h\{S_{a,h}-\delta_{a,h}\}\) and
  \(T_a^{tail}=Q_\tau\{S_{a,h,q}-\delta_{a,h,q}\}\);
- canonical Analysis G3 still bound raw minima and quantiles against aggregate SESOIs; and
- heterogeneous thresholds make those operations non-equivalent.

Required correction: Analysis G3 must define the adjusted worst and tail statistics, require both
simultaneous lower bounds above zero, and leave raw minima/quantiles descriptive only. The
validation freeze, synthesis, method ledger, and report must use that same rule.

Analysis protocol 1.3 now supplies the authoritative adjusted formulas. Validation protocol 1.5,
the synthesis, method-decision ledger 1.3, and report 1.5 reproduce the same decision. The final
exact-head verdict is intentionally kept in the public PR record rather than added here after the
fact.
