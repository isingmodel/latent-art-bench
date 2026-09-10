# Reviewer 2 — second substantive manuscript review

Date: 2026-09-10. This review uses the unchanged three-aspect
[rubric](../20260909_academic_review/RUBRIC.md) and the user-requested DeerFlow
academic-paper-review skill. Scores assess the manuscript identified below,
without assuming that ongoing release work has finished.

## Metadata, role and review scope

- **Title:** *Painter Naming and the Distributional Gap Between Generated Images
  and Original Paintings*.
- **Authors/status:** Anonymous authors; empirical computational manuscript;
  no publication venue specified.
- **Domain:** Generated-image evaluation and computational analysis of painting
  reproductions.
- **TeX SHA256:** `8973d78ceb7d4f81a05010e118454eabc210ecdaa4885ad85eec1e3e41cff0e5`.
- **PDF SHA256:** `ca291f0e0b04ebfa740240d697be89bbe78cfdaecae5b47b61f06acb636d3b9b`.
- **Read:** All 1,871 TeX lines, including all appendices; all 36 PDF pages
  inspected for layout, and all nine figures inspected individually at full-page
  scale. The corresponding figure pages are 6, 9, 13, 15, 17, 18, 19, 26 and 28.

I am a maintainer-run LLM reviewer. After my baseline review, I implemented the
geometry primitives and the centering successor's pure analysis, protocol and
synthetic tests. I subsequently audited their results using separately written
arithmetic. This is not institutionally independent peer review, and I am no
longer independent of the implementation. That involvement is material to the
reviewer's confidence and possible bias, not a reason to increase scores.

I did not consult the other reviewers' Round 2 assessments. Mandatory status
contains earlier aggregate scores. The baseline comparison below uses my own
previous assessment. No paper or frozen evidence was edited during this review.

## Executive assessment

The revision is substantially stronger scientifically. It now tests a concrete
explanation rather than relying mainly on coexistence of lower energy and lower
spread. Generated-only moment maps are evaluated on complete held-out scenes,
then applied unchanged to later outputs. The resulting disagreement is useful:
actual naming beats the shift/scale benchmark, but a transferred translation
alone can be closer to the reference panel than actual naming. The centering
successor addresses a real ambiguity in that comparison, and conditional-mean
prediction shows that better prediction of named outputs and better reference
proximity can favor different maps.

The narrow computational claims are supported, and I found no numerical defect
in the audited additions. Their significance remains that of a strong, specific
empirical study rather than a new general principle of generative behavior.
The paintings' capture histories, requested versus realized content, selected
reference/scene panels and hand-designed metric still limit the scientific
interpretation. There are also two practical reporting improvements: explain
the cross/self-distance tradeoff behind the centered-scaling result, and provide
an actual public replay locator for the central new analyses. Adding another
collection of robustness tables would not resolve the main limitations.

## Claims and evidence

| Claim | Evidence and location | Assessment |
| --- | --- | --- |
| Generated/reference distributions differ across all four painters. | Section 4, Figure 1, Tables 2–3 and Appendix B: 24 lower-spread groups, grouped discrimination and matched-size energy baselines. | Strong for these digital collections; not a stylistic or independent-capture separation. Sisley/Pissarro remain substantively represented. |
| Naming improves controlled primary proximity and both FLUX directions recur later. | Sections 5.3 and 5.6; Tables 4 and 16: six negative original contrasts, four adjusted rejections, two later adjusted rejections. | Strong conditional evidence under the allocation/no-interference assumptions. The temporal design reuses templates and references and changes sample counts. |
| Actual named outputs outperform a generated-only shift/scale benchmark on original held-out scenes. | Sections 6.1–6.2, Figure 3A, Table 17: all six primary mean residuals and all 60 specified cell means are negative. | Strong finite-panel numerical finding. Only FLUX/Monet favors naming in all four primary folds; neither the means nor deletion ranges reject all location/scale accounts. |
| Translation alone is closer than actual naming in the later primary FLUX cohort. | Section 6.3 and Figure 3B: energies 1.470 versus 1.571 for Monet; .736 versus .820 for Cézanne. | Supported; ordering holds in 15/18 views, with all three resolution256/Monet views reversing. It is a feature-space counterexample, not an attainable image intervention. |
| The retained scalar worsens reference energy when mean differences are removed. | Section 6.4, Table 7: T2c shares T1's evaluation mean and T2's centered distances; all 60 original cell means and 18 later scores worsen versus T1. | Supported by direct arithmetic. T2c is evaluation-cohort adaptation, not an unchanged transferred map. The original statement concerns fold means, not every fold. |
| Conditional prediction and reference proximity can favor different maps. | Section 7.2, Table 9 and Appendix J: adding scale lowers corrected conditional-mean residuals in all six primary cells but raises reference energy in five. | The most useful added synthesis. Conditional residuals rely on stable independent repeat errors and concern squared mean mismatch, not complete conditional distributions. |
| Contraction does not determine scene distinguishability. | Section 7, Figures 4–5, Table 8: corrected between-scene contraction, two retrieval gains and four declines; positive global similarities preserve retrieval. | Strong descriptive distinction. Retrieval is not content adherence, and scalar signal/noise is not a full description of centroid geometry. |
| Coverage and energy need not rank the same clouds alike. | Section 6.5: later T2 occupies .605/.750 of fixed reference balls versus actual naming's .526/.719 despite worse energy. | Supported. Fixed anchors and equal query counts make the comparison meaningful; no probability-mass matching or matched-real calibration follows. |
| Palette-name attenuation beyond a generic clause is unresolved. | Section 8, Figure 6, Appendices E and I: two original and two later intervals include zero. | Supported. The generic control itself changes chroma response; two extreme palette levels cannot identify a gain mechanism. |
| Processing probes delimit what the feature metric measures. | Section 9, Figure 7, Appendices G–H: full cross-family matrix, one-coordinate blur concentration and unchanged square-view contrast signs. | Useful computational validation, not identification of capture effects or perceptual validity. |
| The findings are computationally reproducible from released measurements. | Availability statement and Appendix K; predecessor public package, local successor compact inputs and exact replay. | Established for the preceding public package; the new central analyses still need their specific public location and command. Pixel re-extraction remains outside the release. |

## Strengths

**S1. The revision adds a discriminating scientific comparison.** Sections 6
and 7.2 turn an association between proximity and spread into a testable
benchmark comparison. In particular, the fact that adding scale helps prediction
of actual named scene means while generally harming reference proximity makes
the distinction between two targets concrete. This earns contribution credit;
the number of views, output files or verification checks does not by itself.

**S2. The added benchmarks have a disciplined information boundary.** Map
parameters use generated training observations, without optimizing reference
energy. Entire scenes are excluded from fitting; the four fold energies are
averaged instead of pooling differently transformed clouds. Original-map
transfer and evaluation-centered adaptation are explicitly distinguished. The
centering analysis removes a genuine mean/spread confounding in the old-origin
comparison while keeping the original results intact.

**S3. The manuscript now handles finite-repeat geometry correctly.** Equation 8
removes the estimated noise in three-repeat scene means under stated assumptions.
Appendix J gives the cross-repeat identity for conditional mismatch, permits
within-repeat free/named dependence, retains negative values and avoids treating
overlapping fits as independent estimates. Omitting this correction for T2c is
correct because its evaluation mean couples repeat errors. These changes improve
the measurement argument, not merely the wording.

**S4. Contradictory outcomes remain visible.** The retained Sisley result,
OAuth exceptions, fold reversals, resolution256/Monet transfer reversal,
nonselective challenge responses and unresolved palette endpoints all constrain
the interpretation. Figure 3's fold points make the weakness of an exclusively
mean-based account visible. The paper consistently avoids converting correlated
sensitivity counts into independent replication or non-rejection into equivalence.

**S5. The evidence is unusually traceable for a service-based image study.**
The new input mappings and scalers agree with the preserved source vectors;
protocols precede their successor computations; direct numerical audits agree
with the published outputs. This strongly supports the reproducibility of the
defined computations, while the text correctly leaves absent pixels and backend
authentication outside that claim.

## Weaknesses and residual limitations

**W1. The feature-space target remains incompletely validated for the painting
question. Major residual scientific limitation, not an undisclosed numerical
defect.** The Euclidean metric contains correlated, processing-sensitive
coordinates and substantial texture contribution. The shared-mean scalar
penalty is valid in that geometry, but neither it nor common-square consistency
determines whether the relevant difference is painting variation, capture
variation or generated content. Sections 5.5, 9 and 10 acknowledge this well;
candor does not remove the limitation. An independent recapture comparison of
the same works would address a particular confound. More transformations of the
same photographs cannot identify their original capture contribution.

**W2. Generalization of the new benchmark ordering is unresolved. Major residual
scope limitation.** The scientifically central maps were proposed after the
earlier and later results were visible. Cross-fitting limits within-scene
fitting leakage, but does not reverse that proposal history. Both collections
use the same 24 scene templates; only two painters have controlled comparisons;
the later FLUX arm has one output per scene. This supports finite-panel
diagnostics, not a stable ordering over new scene panels, capture sources or
service dates. No additional p-value on the current views would solve this.

**W3. The transformation family is deliberately restricted. Moderate residual
scope limitation.** T1/T2/T2c provide interpretable reference points, not a
comprehensive account of conditional image distributions. They cannot rotate
scene geometry or capture scene-specific changes, and the scalar matches
observed total traces rather than being chosen to minimize either prediction
error or reference discrepancy. The positive corrected residuals cannot reject
every global model, and transformed vectors need not be realizable images.
The manuscript largely states these limits correctly. Broader scientific
claims would require a prospectively chosen comparison class and new evaluation
data, not a more favorable scalar selected using the present references.

**W4. The centered-scaling result lacks its most explanatory energy decomposition.
Fixable reporting weakness.** Section 6.4 says that the scalar worsens proximity
at a common mean, but the result is more informative: cross-reference distance
actually improves while generated self-distance falls by more. For the later
primary Monet cell, T2c−T1 changes `cross_twice` by −1.781498 and
`generated_within` by −2.372607, yielding +.591110 energy. Cézanne gives
−1.208982 and −1.463305, yielding +.254324. These already retained numbers
would explain why a more centrally concentrated cloud scores worse and connect
the new result to Equation 1. A brief paragraph is sufficient; another figure
or analysis family is unnecessary.

**W5. Public replay of the central additions is not yet concretely available
from the reviewed manuscript. Fixable release/reporting weakness.** The text
accurately states that the old archive does not contain the new analyses, but
“accompany this revision” supplies neither a public asset locator nor a new
reproduction command. Appendix K documents the earlier eight-figure package,
while the current paper has nine figures and two subsequent namespaces. This
does not invalidate the local calculations. It prevents crediting the complete
current paper with the predecessor's already verified public replay status.
Complete the additive release and identify its exact scope and command; do not
replace the earlier immutable archive.

**W6. The scientific narrative is improved but still carries considerable
reporting load. Minor presentation limitation.** The 36-page manuscript retains
two palette experiments, several reference/control designs and multiple metric
scales. Figure 3 and Table 9 clarify the core claim, but a reader must still
track several distinct energy baselines. Page 34 contains only the final short
paragraph of Appendix J, with the reproduction section deferred to page 35.
There is no clipping or unreadable figure, but the nearly empty page and some
repeated cautions can be tightened without changing scope or dropping painters.

## Methodology and numerical verification

The assessment focuses on the defined finite-panel computations. I inspected
the complete moment-map, centering and variance source and the protocol
contracts. The associated audits are [RESULTS_AUDIT_2.md](RESULTS_AUDIT_2.md) and
[CENTERING_RESULTS_AUDIT_2.md](CENTERING_RESULTS_AUDIT_2.md).

The centering audit directly reconstructed 258 fitted/evaluated clouds and all
1,290 energy and occupancy records without importing the study arithmetic.
Maximum discrepancy was below `9e-15`; memberships, hit counts and radii matched
exactly. It verified all 22 bound files against their hashes and recorded source
commit, as well as predecessor values retained unchanged. The successor's exact
replay command also passed. That replay alone would have been insufficient to
validate a shared implementation error.

For Table 9 specifically, I separately computed the 48 primary T1/T2 fold
residuals using explicit distinct-repeat inner products. They reproduce the
reported conditional values to `3.56e-15`. This verifies the estimator's
implementation and table transfer, not the independence assumptions of the
real service errors. The full repository suite was being handled by the root;
I did not run a competing full suite or assume its pending outcome.

Two small specification improvements remain. Section 6.1 should say explicitly
that delete-one-scene recalculation is reported for the primary all31/512 cells,
whereas the full sensitivity grid retains every fold but does not contain a new
deletion grid. Section 6.4 should call the 60 original results **fold means**;
the same mean direction holds in 232/240 individual folds, not all of them.
Neither clarification requires recomputation.

## Literature positioning

The new literature framing is appropriate. [Benny et al. (2021), Sections 1
and 3](https://link.springer.com/article/10.1007/s11263-020-01424-w), already
distinguish unconditional, within-class and between-class evaluation. Their
counterexamples prevent treating the broad distinction between marginal
proximity and conditional structure as a new principle. The present paper's
increment is a repeated painter-clause intervention and the observed behavior
of fixed generated-only maps against two evaluation targets.

[Zhang et al., version 1, Sections 3–4](https://arxiv.org/html/2510.19557v1)
already show that prompt complexity can reduce conditional diversity while
improving reference-based distribution measures. Here the unchanged scene text,
painter-clause contrast and original-map temporal application ask a different,
narrower question. I read the specified version's methods and results; an
OpenReview PDF retrieval failed, so I do not base a claim on differences in its
later conference version.

[Khayatkhoei and AbdAlmageed (2023), Sections 4–5](https://proceedings.mlr.press/v202/khayatkhoei23a/khayatkhoei23a.pdf)
explicitly identify Naeem coverage as complement recall and demonstrate inward
versus outward asymmetry, including feature-space scaling experiments. This
supports the caution about occupancy, but their high-dimensional examples do
not by themselves establish that pathology in these 31 coordinates. The
manuscript now gets that distinction right. Its own verified map/occupancy
disagreement supplies the relevant local evidence.

These primary sources substantiate the narrower empirical positioning. I did
not perform a new exhaustive literature search or claim that no one has used
similar mean/scale diagnostics elsewhere. The art-imitation comparisons read
in the baseline review remain relevant; none licenses a perceptual validation
claim for the current coordinates.

## Prioritized revisions and next studies

**Retained evidence and manuscript work:**

1. Add the short cross/self-distance explanation in W4, and retain the
   specified-path qualification for center versus scale.
2. Complete and verify the additive public package for both new namespaces and
   the ninth figure. Put its concrete locator, command and pixel-access boundary
   in the availability statement and Appendix K. Pending work receives no
   advance reproducibility credit.
3. Specify the primary-only deletion scope and original-fold-mean qualifier.
   Tighten the Appendix J/K page break if convenient. These are local reporting
   changes, not reasons to reopen frozen numerical results.

**New scientific studies, outside the currently authorized retained-data work:**

1. Fix the present maps and evaluation rules before sampling new scene panels
   with repeated outputs. The discriminating outcomes are whether T1's advantage
   over actual naming and the T2c−T1 penalty preserve their sign and magnitude
   on those panels. A reversal would falsify generalization of the current
   ordering, while mixed outcomes would bound its scene dependence.
2. Measure independent digital captures of the same reference works, keeping
   work identity fixed. Compare within-work capture displacement with the
   relevant generated/reference terms. If capture changes reverse the benchmark
   ordering, the current geometry cannot sustain a capture-stable interpretation.
3. If the palette mechanism remains a goal, prospectively specify intermediate
   palette levels and multiple generic clauses. Nonlinear response or a
   control-dependent slope would distinguish the present saturation/operating-
   point alternatives. More repeats at only the current two extremes cannot.

No human-rating study is requested here, and no new extraction, generation or
acquisition was performed for this review.

## Scores and recommendation

| Fixed aspect | Round 2 | My baseline | Explanation |
| --- | ---: | ---: | --- |
| Scientific rigor | **8.8/10** | 8.2 | Whole-scene fitting, exact energy comparisons, finite-repeat correction and the centering control materially strengthen claim/evidence correspondence. Representation/capture validity and post-result fixed-panel generalization remain substantive limitations. |
| Contribution and significance | **8.6/10** | 7.8 | The named-prediction versus reference-proximity disagreement and unchanged-map transfer supply substantive new empirical insight. It remains an application-specific finding built from established conditional-evaluation and distribution-geometry ideas, without a validated generative or perceptual explanation. |
| Clarity and reproducibility | **9.0/10** | 9.0 | The narrative and mathematical distinctions improve, and the new numerical evidence is auditable. Those gains are offset at this snapshot by the incomplete public replay locator for the central additions and remaining presentation load. No increase is awarded for documentation volume or promised publication. |

**Per-reviewer mean: 8.8000/10.** Every change above reflects substantive
evidence or the actual reviewed state, not a desired aggregate score.

**Recommendation:** A strong empirical computational paper suitable for
publication after the focused reporting and additive-release work above. The
remaining scientific limitations bound its significance rather than invalidate
its carefully stated finite-panel findings. No numerical must-fix defect was
found in the audited additions.

**Confidence:** High for the new algebra, data mapping and reported numerical
comparisons; moderate for measurement interpretation and generalization. The
review did not authenticate remote backend states, inspect new raw pixels,
validate realized content, repeat feature extraction or independently execute
the pending public add-on. Implementation assistance and common maintainer
operation preclude presenting this as independent external validation.
