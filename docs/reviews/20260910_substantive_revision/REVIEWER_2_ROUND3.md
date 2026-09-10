# Reviewer 2 — third substantive manuscript review

Date: 2026-09-10. This is a create-once assessment under the unchanged
[three-aspect rubric](../20260909_academic_review/RUBRIC.md), using the requested
[DeerFlow academic-paper-review skill](https://github.com/bytedance/deer-flow/blob/main/skills/public/academic-paper-review/SKILL.md).
The local skill was read in full. Its recorded SHA256 is
`a0285baaeacc916bf45751c06db37745b195ddd4ec30e271ec1472f6cd48e8aa`.

## Metadata and reviewer involvement

- **Title:** *Painter Naming and the Distributional Gap Between Generated Images
  and Original Paintings*.
- **Authors/status:** Anonymous authors; empirical computational manuscript;
  no publication venue specified.
- **Domain:** Generated-image evaluation and computational study of digital
  painting reproductions.
- **Committed manuscript:** `28b7d28ae630f7fe601eb77f63194376587eba48`.
- **TeX SHA256:** `5853d7283c5a3d737288d232a481a05e3dd170273934486ea0df169be906d9ce`.
- **PDF SHA256:** `873c78aca8b9f9d469ea8ae4c0f819c3202a5705d912146111815b77634fe52f`.
- **Bibliography SHA256:** `7b2d0dcb8ec858009ac2401903cc63572c42610fef1972e622419afd83e70808`.
- **Snapshot:** [ROUND3_SNAPSHOT.json](ROUND3_SNAPSHOT.json); all listed manuscript,
  bibliography and nine figure hashes were independently checked against it.
- **Reading:** Complete TeX, all appendices and bibliography. I freshly rendered
  all 35 PDF pages and inspected every page in contact sheets, then inspected all
  nine figure pages individually: 6, 9, 13, 15, 17, 18, 19, 27 and 28. Pages 12,
  16, 34 and 35 received additional full-page inspection for tables, formulas,
  commands and references. No clipping, missing figure, unresolved citation or
  unreadable table was found. Local review renders are under
  `tmp/paper/reviewer2-round3-20260910/`.

I am a maintainer-run LLM reviewer. I implemented the geometry primitives and
the centering successor's pure analysis, protocol and synthetic tests, and later
implemented both painter-clause collectors/workflows and their transport tests.
I also audited their terminal evidence and reviewed numerical release tooling.
This is an involved implementer's separately conducted review, not independent
human, institutional or external-investigator peer review. My implementation
knowledge improves verification access but creates a material potential bias.

I did not read the other reviewers' Round 3 reports or scores. I read my own
Round 2 assessment to explain the score changes. Mandatory status and earlier
coordination expose prior results and the requested aggregate goal; neither is
a scoring criterion. No manuscript, scientific source, protocol, observation,
old review or result was changed during this review.

## Executive assessment

The paper now supports a strong and specific empirical conclusion: in these
fixed digital collections, painter naming can improve painting-reference energy
while contracting generated variation, but reference proximity, prediction of
named scene means and scene distinguishability are different evaluation targets.
The generated-only map comparisons provide the most substantive explanation of
why these targets should be reported separately. The new prospective Cézanne
comparison adds evidence against one generic-painting-clause control on new
scenes; it does not validate the map explanation on those scenes.

The reporting and practical numerical reproducibility are materially stronger
than at Round 2. The scale/energy mechanism is explained through the actual
cross-distance and within-generated terms, fold heterogeneity is visible, and
the central new analyses now have working public archives. The failed original
clause cohort remains unavailable, including Monet, rather than being rescued
by partial data or pooled with its successor. I found no new correctness or
public-access blocker.

The contribution remains an empirical result about a selected representation,
reference corpus and set of service deliveries. It does not identify a perceptual
style mechanism, independent-capture equivalence, or a generally predictive
transformation of new scenes. Those are substantive limits even though the
manuscript now states them accurately. They limit rigor and significance more
than they limit the quality of its reporting.

## Claim–evidence map

| Principal claim | Evidence location | Assessment and boundary |
| --- | --- | --- |
| Generated and original distributions differ across the four painters. | Section 4; Figure 1; Tables 2–3; Appendix B. All 24 generated cells have lower trace than their reference panels, with strong grouped discrimination. | Supported for the retained digital collections. Four-painter coverage is substantive, including the contrary Sisley energy ordering. Neither classifier separation nor PCA proves stylistic or capture-independent separation. |
| Naming improves primary controlled feature proximity. | Sections 5.3–5.6; Figure 2; Tables 4–6 and Appendix I. Six original named-minus-free energy contrasts are negative; four reject after the eight-test adjustment; both later FLUX contrasts reject in their separately fixed family. | Supported under the stated conditional randomization/no-interference assumptions. The later collection reuses scenes and references and changes repeat counts, so it is not a pure time-effect experiment. |
| The new Cézanne clause beats a generic painting clause on new fixed scenes. | Section 5.7; Table 7; Appendix A.3; separately frozen `pcsv1-20260910`. All 96 outputs complete 48 pairs. Primary energy is 2.165789 versus .970369, difference −1.195419, with the specified Monte Carlo p=.00001 at alpha .025. | Strong evidence for this two-clause delivered-service comparison. Three pipelines preserve the direction. The p-value is the simulation resolution floor, not zero probability, and is not a test merely of equal energy. One generic phrase, one painter, unequal reported quality and a fixed authored panel bound the inference. |
| The failed original clause cohort supplies no recovered primary conclusion. | Section 5.7; Appendix A.3; original terminal/measurement records and public adapter. The 288-slot cohort returns 211 images and fails its global collection contract. | Correctly withheld for both original endpoints; internal Holm-one values are bookkeeping. The separate 96-output cohort neither restores Monet nor permits pooling or filling missing original cells. |
| Actual naming beats the fitted shift/scale benchmark on held scenes. | Sections 6.1–6.2; Figure 3A; Appendix J. All six primary means and all 60 specified cell means favor actual naming. | Supported finite-panel result. Four folds are scored separately. Only FLUX/Monet favors actual naming in every primary fold; OAuth/Cézanne deletion means cross zero. This does not reject every possible location/scale model. |
| A transferred translation can be closer to paintings than actual naming. | Section 6.3; Figure 3B. Later FLUX translation energies 1.470/.736 are below actual naming's 1.571/.820. | Supported for both primary painter panels, with 15/18 view agreement and the stated resolution256/Monet reversals. A feature-space diagnostic is not an attainable image intervention. |
| The retained scale can worsen energy even when evaluated at the same mean. | Section 6.4; Table 8. Evaluation-centered scale has penalties .591110/.254324 against translation in the later primary cells; all 60 original means and 18 transfer scores have this sign. | Supported by the earlier direct-formula audit. The new explanation is correct: twice-cross-distance decreases by 1.781/1.209, while within-generated distance decreases by 2.373/1.463 and is subtracted. This is a specified path decomposition, not an optimal scalar or unique causal attribution. |
| Better named-scene mean prediction need not improve painting-reference energy. | Section 7.2; Table 10; Appendix J. Adding scale lowers corrected residuals in all six primary means and raises energy in five. At fold level the counts are 22/24 and 16/24, jointly 15/24. | The clearest substantive synthesis. I independently verified these fold counts from the sealed precomputed values before this review. The cross-repeat correction requires the stated error assumptions and does not remove fitted-parameter uncertainty. It is correctly omitted for evaluation-centered T2c. |
| Contraction need not lower scene retrieval. | Sections 7.1–7.3; Figures 4–5; Table 9. Corrected variance separates fixed-scene means from repeat noise; retrieval gains occur in two cells and declines in four. | Supported descriptive distinction. Retrieval compares relative centroid geometry, is invariant to a shared positive similarity, and is not semantic adherence. Reused centroids and queries are not independent Bernoulli trials. |
| Occupancy and energy can rank the same clouds differently. | Section 6.5. Later shift/scale occupies .605/.750 of reference balls, above actual naming's .526/.719 despite worse energy. | Supported with fixed anchors and equal query counts. This is explicitly distinct from the matched-real baseline in Section 5.4 and is not evidence of matched probability mass or a general high-dimensional pathology. |
| Additional named-clause attenuation of palette response is unresolved. | Section 8; Figures 6 and 9; Appendices E, F and I. Original and later named-minus-generic intervals span zero; shared controls enter the covariance calculation. | Correct. Repeat blocks determine precision, approximate interval assumptions are explicit, and two palette extremes cannot identify response gain. No equivalence conclusion follows. |
| Processing probes delimit the measurement. | Section 9; Figure 7; Appendices G–H. All-reference transformations show cross-family sensitivity, substantial blur dependence and preserved original primary signs in the common-square view. | Useful computational calibration. It neither validates perceptual importance nor identifies the share of the original/generated gap due to real capture histories. |
| The reported computations are publicly replayable from compact measurements. | Availability statement; Appendix K; the three published versioned archives and clause reproduction report. | Established for the stated numerical scope. Public replay does not authenticate absent image bytes, repeat feature extraction or independently verify a remote model checkpoint. The three archives have separate coverage and commands. |

## Specific strengths

**S1. The main scientific comparison is informative rather than circular.**
The map fit uses generated training moments without optimizing against painting
features. Whole scenes are held out, maps are not pooled across folds, and
unchanged transfer is distinguished from evaluation-mean adaptation. This makes
the disagreement between predicting named outputs and approaching a reference
panel an interpretable empirical finding.

**S2. The prospective addition has a meaningful control and preserves failure.**
The Cézanne/generic comparison addresses the ambiguity that any conventional
painting instruction could explain a named-versus-free contrast. Its scenes,
allocation, threshold and single-replacement boundary were fixed before its
outcomes. The entire original cohort and its failed contract remain visible.
The new evidence earns credit for answering that narrow question, not for
restoring unavailable endpoints or supplying unperformed map validation.

**S3. Numerical geometry is now explained at the appropriate level.**
The revised cross/self-distance account makes the centered-scaling result
understandable. Table 10 reports both target-specific scores and the heterogeneous
fold signs. Finite-repeat correction, unequal content weights, equal-scene
retrieval, observation-level versus scene-level variation, and the limitations
of occupancy are distinguished rather than collapsed into a single diversity
claim.

**S4. Counterexamples remain in the scientific argument.**
Sisley, OAuth non-rejections, fold reversals, the translation-only transfer
advantage, the resolution256 exception, increased OAuth/Cézanne within-scene
variation and unresolved palette effects all constrain the interpretation.
The paper does not count correlated sensitivity cells as independent evidence
or treat a null result as equivalence.

**S5. Public reproducibility is now demonstrated, with a realistic boundary.**
This reviewer performed the fresh local extraction, pre-install standard-library
verification, locked Python 3.13.11 installation, unchanged public numerical
check and exact four-path optional test command for the actual clause archive.
That run passed 152 tests with eight explicit maintainer-only skips; all 85
payload files were unchanged afterward. Both original unavailable outcomes and
the complete successor result replay exactly. This closes a practical access
gap; it is stronger evidence than a promise to release code.

## Weaknesses and residual limits

**W1 — Substantive measurement/generalization limit: the chosen metric remains
part of the result.** The development scaler is work-disjoint but comes from
the same artists. The 31 coordinates are correlated, and the strongest texture
response is concentrated in a blur-sensitive LBP coordinate. Capture source,
surface texture, framing and requested rather than verified content can affect
both energy and trace. Common-square views, transformations and coordinate
omissions delimit sensitivity; they do not identify which measured differences
represent painting style rather than the digital acquisition process. This is
not a newly discovered implementation defect, but it limits how much the
generated-versus-painting result explains beyond these reproductions.

**W2 — Substantive validation limit: the central map account remains post-result
and narrowly tested.** The original whole-scene evaluation is useful, but the
diagnostic family was selected after Study 1 and later FLUX results were known.
The transfer cohort reuses the original scene briefs and has one repeat. The
new C/G cohort has neither a free arm nor enough of the specified comparison
structure to validate T1/T2 or conditional residual predictions. Moreover,
translation plus one scalar cannot represent rotation, anisotropic changes or
scene-specific transformations. The manuscript correctly avoids rejecting all
such accounts, but its mechanism-level reach remains limited.

**W3 — Substantive scope limit: the new generic-clause result is one attained
service contrast.** Forty-eight pairs improve the evidence for the fixed
Cézanne comparison; they do not sample a population of artists, generic phrases
or scene descriptions. Sixteen generic outputs versus six Cézanne outputs have
reported medium quality, with low quality otherwise, and all are nonsquare
despite identical square requests. These delivered differences belong in the
effect, but prevent isolating a pure semantic naming mechanism. Loss of the
original cohort also leaves no contemporaneous Monet/generic answer and no
prospective map answer. The current text does not falsely claim either.

**W4 — Residual assumption limit: computation cannot establish repeat-error or
service-state assumptions.** The conditional sharp-null tests require their
specified allocation/no-interference or joint-invariance conditions. The
corrected variances, cross-repeat inner products and palette intervals require
additional repeat-error assumptions. Transport identity and source checks do
not observe the full remote backend state. Random order and proxy calibration
do not prove independent stable errors. The manuscript now says this correctly,
but it remains a practical limitation of the scientific inference.

**W5 — Minor reporting burden: several comparison scales require sustained
attention.** Full-cohort V-energy, averages of fold-specific V-energies,
content-weighted and equal-scene traces, matched-real coverage and all-reference
occupancy are individually defined correctly. Their coexistence makes a
35-page paper demanding to read, particularly around Sections 5–7. The prose
and captions are substantially improved, but a short consolidated guide to the
different targets and query counts would help readers avoid comparisons the
authors themselves do not make. This is a usability improvement, not a numerical
correction or a request for another robustness grid.

## Targeted primary literature assessment

I read relevant primary-source method and result sections, not just search
snippets. This was a targeted check of the nearest claims, not a systematic
literature review or complete replication of the cited papers.

- [Su et al., *Identifying Prompted Artist Names from Generated Images*, v1](https://arxiv.org/html/2507.18633v1):
  Sections 3–4 include held-out prompts and artist names, same-seed named/free
  image comparisons and real-artist CLIP prototypes. The present related-work
  discussion now appropriately disclaims priority for those controls and
  generalization settings. Its distinct value is the finite distributional and
  repeated-scene geometry analysis, rather than artist identification alone.
- [Benny et al., *Evaluation Metrics for Conditional Image Generation*](https://link.springer.com/article/10.1007/s11263-020-01424-w):
  Section 3 separates within-class and class-mean comparisons and explains why
  unconditional agreement can hide conditional mismatch. This limits the
  novelty of the broad principle. The manuscript's contribution is the empirical
  target disagreement in this painting setting and its generated-only benchmark,
  not discovery of conditional evaluation.
- [Zhang et al., *The Intricate Dance of Prompt Complexity, Quality, Diversity,
  and Consistency in T2I Models*, v1](https://arxiv.org/html/2510.19557v1):
  Sections 3–4 construct matched prompt/reference comparisons and report that
  prompt detail can improve reference-based scores while changing diversity.
  The present paper fairly treats coexistence of proximity and contraction as
  insufficient novelty on its own.
- [Khayatkhoei and AbdAlmageed, *Emergent Asymmetry of Precision and Recall*](https://proceedings.mlr.press/v202/khayatkhoei23a/khayatkhoei23a.pdf):
  The support-approximation argument and Sections 3–4 concern defined geometric
  assumptions and asymptotic behavior. They motivate caution about interpreting
  nearest-neighbor support estimates; they do not establish that this paper's
  31-feature occupancy result is that pathology. The manuscript now preserves
  that distinction.
- [Diedrichsen and Kriegeskorte, *Representational Models*](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005508):
  The independent-partition inner-product argument supports removal of diagonal
  noise bias under its assumptions. It does not justify using the same
  correction after evaluation-mean adaptation has coupled errors. The paper's
  deliberate omission of corrected T2c residuals is appropriate.

## Access and provenance verification

All three paper-linked public release pages resolved during this review:
[original numerical package](https://github.com/isingmodel/latent-art-bench/releases/tag/pprv1-20260910),
[geometry addendum](https://github.com/isingmodel/latent-art-bench/releases/tag/ppgv1-20260910)
and [clause addendum](https://github.com/isingmodel/latent-art-bench/releases/tag/pcrv1-20260910).
GitHub's dynamically loaded asset panels were not exposed by the page-text tool;
actual archive access is established separately by the download receipts.

The actual clause archive has 1,500,356 bytes and SHA256
`6038da2daed74e6ed4b509464dc6f1a4dae386e644d265235de982db4bf23e40`.
My completed [local replay record](../../../reports/paper_clause_reproducibility_v1/pcrv1-20260910/LOCAL_REPLAY.md)
documents the fresh run described above. The separate
[anonymous-download record](../../../reports/paper_clause_reproducibility_v1/pcrv1-20260910/ANONYMOUS_REPLAY.json)
was produced by the coordinating maintainer-run agent, and I inspected it and the
[reproduction report](../../../reports/paper_clause_reproducibility_v1/pcrv1-20260910/REPORT.md).
It reports another exact replay and 152 passes/eight skips after an unauthenticated
download. These two runs used the same macOS arm64 host; I assign no cross-platform
or independent-investigator replication credit to them. The earlier archive's
separate Linux result is not a Linux result for the new addendum.

The clause exporter was independently reviewed within this maintainer team for
source closure, compact-input lineage, terminal binding inventory, unavailable
outcomes, sanitized allowlisting and cached-module isolation. The public check
uses unchanged numerical analyses and does not import the collection workflow.
My preceding [successor terminal audit](CLAUSE_SUCCESSOR_TERMINAL_AUDIT_2.md)
checked all 96 retained response hashes, 167 source bindings, timing/accounting,
identity gates, all 288 measurement rows and the exact four measurement-output
bindings without re-extracting images. Reviewer 1's separately written
[arithmetic audit](CLAUSE_SUCCESSOR_RESULTS_AUDIT_1.md), also with implementation
involvement disclosed, agrees on the primary contrast, 48 contributions and
Monte Carlo decision. Those are complementary checks, not independent studies.

No full test suite, generation or image extraction was repeated for this
manuscript-only review. Prior completed checks are identified as such. The
public packages support computation from measured vectors, not authentication
of absent pixels, legal reassessment of every artwork source or reconstruction
of an upstream checkpoint.

## Scores, changes and confidence

| Fixed aspect | Round 2 | Round 3 | Rationale |
| --- | ---: | ---: | --- |
| Scientific rigor | 8.8 | **8.9** | The complete prospective C/G contrast adds an informative control on new fixed scenes, with honest global withholding of the failed predecessor. The result is bounded by delivery and reference/metric assumptions, and the central map claims still lack prospective new-scene validation. The small increase is for the new evidence, not protocol volume or candor alone. |
| Contribution and significance | 8.6 | **8.8** | The new comparison strengthens the empirical naming result beyond artist-free prompting, while the integrated cross/self-distance explanation and conditional-versus-reference target comparison make the practical lesson clearer. It remains a strong empirical application of established evaluation ideas; neither a general naming mechanism nor a broadly validated predictor has been established. |
| Clarity and reproducibility | 9.0 | **9.4** | Working public replay for the central additions, verified unavailable-outcome preservation, exact commands, explicit deployment/runtime scope, readable figures and the improved energy/fold explanation resolve the main Round 2 reporting/access gaps. The remaining problems are minor navigation burden and the deliberately limited vector-only reproduction scope, not a missing numerical release. |

**Confidence:** High for the manuscript's numerical/reporting correspondence and
the actual public clause replay; moderately high for the statistical assessment;
moderate for claims of wider scientific novelty and measurement generalization.
These are fixed independent aspect judgments. No aggregate target, hypothetical
future experiment, additional file count or unperformed external replication
receives credit.

## Prioritized actions

1. **Retained evidence, optional minor revision:** Add a compact reader guide
   near Sections 5–7 identifying each target, its weighting and its query unit:
   original full-cohort energy, mean fold energy, matched-real coverage,
   all-reference occupancy, and conditional-mean residual/retrieval. Reuse the
   existing definitions and counts; do not introduce a new analysis or baseline.
   No result-changing correction is required by this review.
2. **Retained evidence, interpretation discipline:** Preserve the explicit
   distinctions already present when shortening the paper or writing publicity:
   the new C/G result does not restore Monet, validate the maps, isolate semantic
   style from delivery, establish equivalence or authenticate raw images. The
   related-work delimitations and fold reversals should survive condensation.
3. **New scientific study, highest value for the map claim:** If future work is
   undertaken, freeze the existing maps and competing target orderings before a
   genuinely new scene panel with free and named repeats. Evaluate prediction
   of named conditional means and reference energy separately, with a specified
   decision rule. Failure to reproduce their disagreement should count against
   its generality. The current C/G cohort cannot be repurposed for this test.
4. **New scientific study, highest value for measurement interpretation:** A
   separately gated same-work independent-capture calibration or independent
   institutional reference panel would address a different uncertainty than
   more processing derivatives. Specify capture provenance and matched-work
   comparisons before access. A capture-associated displacement comparable to
   the claimed naming effect would weaken a style-level interpretation. This
   is future work, not a reason to reopen terminal cohorts or acquire bytes
   under the existing freezes.

The current paper is ready for a bounded empirical presentation with these
limits intact. I do not recommend another retained-data sweep or additional
collection merely to increase review scores.
