# Reviewer 3 — substantive revision, round 1

## Metadata and review boundary

- **Paper:** *Painter Naming and the Distributional Gap Between Generated Images and Original Paintings*.
- **Authors/affiliations:** Anonymous authors; affiliations not given.
- **Year/status:** 2026 working manuscript; no selected venue or editorial decision.
- **Domain/type:** Empirical computational evaluation of text-to-image services and digital painting distributions.
- **Reviewer:** Fresh maintainer-run LLM subagent, with no previous implementation involvement. This is neither independent human peer review nor institutional review.
- **Emphasis:** Novelty, conceptual contribution, research narrative and nearest primary literature.
- **Reviewed source SHA-256:** `4abff8f0b31110746eb6ab4a6de5cdc9992847fa0f0383c3ebb06d3abcbb5535`.
- **Reviewed PDF SHA-256:** `dd7cca03dcd18a999b348577f65b28979d594654c577ec73037d8aa8456891bc`.
- **Procedure:** Read `docs/STATUS.md`, then `docs/ARTIFACTS.md`, then inspected Git status. Read all 1,665 source lines, all appendices, bibliography, and rendered all 32 PDF pages. Visually inspected every page, including Figures 1–8. Applied the supplied DeerFlow skill and unchanged `docs/reviews/20260909_academic_review/RUBRIC.md`. Did not open previous review reports or individual scores; mandatory status exposed historical aggregate information, which was not used as a scoring target.
- **Checks:** Verified the two manuscript hashes. Ran `uv run --locked pytest -q tests/painter_distribution_study_v1/test_inference.py tests/painter_responsiveness_v2/test_diagnostics.py -m 'not live'`: **15 passed**. Read the public reproduction report and inspected the released-input schema for retained-vector feasibility. Did not rerun the full public package or independently authenticate image acquisition. This review changes presentation documentation only; no frozen scientific input or public archive was changed.

## Executive assessment

This is a strong, unusually transparent finite-panel computational study. Its clearest contribution is a controlled painter-name intervention with fixed scene wording, explicit randomization inference, several services, and a separate temporal FLUX collection. The manuscript preserves the four-painter exploration, adverse sensitivities, unresolved palette interactions and delivery differences. Public numerical reproduction is a substantial practical asset.

The contribution is useful but remains materially short of exceptional. The paper combines many sound observations without testing a sufficiently specific explanation of their relationship. The message that proximity, diversity and conditional organization must be examined separately is already well established; particularly close conditional-evaluation and prompt-complexity papers are absent from the bibliography. The present results extend that literature to controlled painter naming, but do not yet establish a new general evaluation principle. The geometric proposal below could add evidence within the current constraints. Merely introducing new terminology, another summary diagram or more assertive prose would not do so.

**Overall assessment:** A useful empirical contribution warranting substantive revision for stronger significance and narrative. No selected venue is assumed. **Contribution level:** Moderate. **Confidence:** High on claim/evidence correspondence and narrative, moderate on exhaustive novelty and numerical implementation: this was a full-paper review plus targeted checks, not an independent end-to-end study reproduction.

## Principal claims and evidence

| Claim | Evidence location | Assessment |
| --- | --- | --- |
| Generated collections differ from the four painters' reference distributions and have lower measured spread. | Section 4; Figure 1; Tables 2–3; Appendix B. All 24 trace ratios .206–.376, with high full-space classification accuracy and matched-size reference baselines. | **Strong descriptive support** for the recorded feature distributions. Content/capture confounding and non-attested aliases prevent stylistic or model-internal attribution. |
| Adding a name improves primary energy proximity. | Section 5.3; Figure 2; Table 4; Appendix C. Six negative estimates; four Holm rejections. | **Strong conditional evidence** for the NB2/FLUX cases under the assigned-position sharp null and no-interference assumption. OAuth estimates remain unresolved. |
| Names provide relative painter alignment beyond common generic movement. | Section 5.4; Table 5; Appendix D.2. Three negative changes in the equal-class interaction, stable across 36 views. | **Moderate descriptive support.** It is joint alignment, not individual correct-painter preference; NB2/Monet remains closer to Cézanne in the cited comparison. Sparse strata and absent uncertainty matter. |
| Contraction can accompany increased reference coverage and either direction of scene retrieval. | Sections 5.4–5.6; Figures 3–4; Table 6. FLUX/Monet retrieval improves while between-scene trace falls; OAuth/Cézanne within-scene spread rises despite total contraction. | **Strong finite-set counterexamples** to interpreting total trace as conditional distinguishability. Their broader methodological motivation is established in conditional-generation literature. |
| The palette design does not resolve additional named-clause attenuation beyond the generic clause. | Section 6; Figure 5; Appendix E. Both primary intervals include zero. | **Supported unresolved conclusion.** Six scenes and four repeats limit precision; one generic wording does not isolate artist identity from every linguistic difference. |
| Measurement responses are computationally characterized, and square windows preserve the naming pattern. | Section 7.1–7.2; Figure 6; Appendix G. Three positive paired challenge comparisons and the same four original rejection decisions after cropping. | **Strong computational support**, with substantial cross-family responses and processing sensitivity. No perceptual construct validation or capture equivalence follows. |
| The FLUX naming direction recurs in fresh outputs. | Sections 7.3–7.4; Table 7. Two negative contrasts with fresh-family adjusted p-values below .0001. | **Strong directional replication** on the same fixed scene/reference design. The free-arm spread changes, and shared controls/sample counts differ, so this is not general temporal stability. |
| Statistical analyses and figures are publicly reproducible from retained measurements. | Availability statement; Appendix H; `reports/paper_reproducibility_v1/pprv1-20260910/REPORT.md`. | **Strong documented numerical-reproduction support.** The corrected r1 and portability distinctions are clear. Pixels and acquisition authentication remain outside the package. |

## Concrete strengths

### S1. The intervention is sharper than an imitation benchmark

Section 5.1 holds the detailed scene text fixed while adding the painter clause, and Section 5.2 describes the exact inferential family. This supports a concrete service-output question that a comparison of unrelated generated and historical collections cannot answer. The temporal FLUX result strengthens this specific contribution without pooling cohorts.

### S2. The paper retains observations that resist a simple favorable story

Section 4 reports that named medians are lower than free medians only for Sisley; Section 5.4 reports the NB2/Monet cross-painter preference; Section 5.7 reports a no-texture proximity reversal; Section 7.4 reports changed free-arm spread. These disclosures materially improve claim calibration. Retaining Sisley and Pissarro also makes the follow-up selection and its generalization limit visible.

### S3. Repeated scenes make conditional variation observable

The decomposition and held-repetition retrieval in Sections 5.5–5.6 are more informative than another PCA picture. OAuth/Cézanne demonstrates that total contraction can conceal increased repeat variability; FLUX/Monet demonstrates that lower between-scene spread can coexist with better retrieval. The caption and methods correctly avoid treating overlapping retrieval queries as independent Bernoulli observations.

### S4. Measurement challenges reveal actual weaknesses of the representation

Figure 6 includes cross-family responses, not only expected positive checks. The 83.9% LBP contribution to squared blur response, the resampling displacement and the tile response in the color family are useful evidence about what the feature names do and do not mean. Common-square sensitivity adds a concrete test while preserving its crop/content limitation.

### S5. Reproduction has become a usable contribution

The public package exposes numerical inputs, prompts, scalers, memberships and original analysis functions. Appendix H distinguishes continuous floating-point comparisons from exact discrete results and platform-dependent figure bytes. This makes the finite-panel calculations accessible to other evaluators even though image re-extraction is unavailable.

## Substantive weaknesses and residual limits

### W1. The nearest methodological literature is incomplete

Section 2 cites fidelity/diversity/coverage work, but not the closer literature connecting condition structure and prompt specificity to distribution-level evaluation. Benny et al. formalize why unconditional metrics can conceal within-/between-class mismatch. Zhang et al. directly study prompt complexity alongside conditional diversity, consistency, distribution shift and coverage. These sources constrain how much novelty can be assigned to the paper's concluding evaluation lesson. Their existence does not invalidate the painter-name intervention, which is a different manipulation. The revision needs a precise comparison of estimands and resulting insight, not simply two added citations.

### W2. The results identify coexistence and counterexamples, but not what predicts the coexistence

Sections 5.3–5.6 establish that proximity, spread, coverage and retrieval can move differently. The paper explains the energy subtraction correctly and states uniform-scale retrieval invariance. However, it does not quantify how much of the observed naming change is consistent with a single global relocation/contraction of a cloud, and how much requires changes in relative scene organization. The remaining conceptual contribution is therefore a set of instructive examples rather than a tested diagnostic account. A small, held-out geometric baseline is feasible from the released vectors; see the proposal below.

### W3. The measurement challenge and the principal naming result remain partly disconnected

Section 7 establishes response to selected transformations, including nonselective and processing-dependent behavior. Section 5 uses the same representation to quantify naming. Their coexistence does not reveal which aspects of the observed naming improvement are stable geometric changes and which rely on processing-sensitive coordinates. The existing 19-coordinate and pipeline sensitivities are useful, but summary counts conceal the practical extent of agreement. A compact side-by-side display of the main effect and any new baseline residual in the primary and no-texture views would be more informative than additional challenge significance statements. This would still be a feature-space result, without claiming a style mechanism.

### W4. The palette experiment is scientifically separate but narratively expensive

Sections 6–7 devote considerable space to two unresolved artist-specific interactions. They are valid results; non-rejection should not be penalized as failure. Their role is nevertheless narrower than the manuscript's cumulative story suggests: the different scenes and service, explicit extremes, one generic clause and global chroma endpoint cannot explain Study 1 contraction. The manuscript acknowledges this correctly. It should make the palette design a distinct boundary test of control wording, with the two full cohorts kept visible in one integrated result table. More pages and nominal secondary findings do not strengthen a unified mechanism that was not tested.

### W5. Several meaningful limitations cannot be solved editorially

The finite reference panel is selected, capture workflows are unknown, broad classes include uncertain LLM annotations, painter choice follows exploration, and the public package excludes pixels. These are acceptable boundaries for the stated computational question, but they limit interpretive utility. Neither perfect numerical replay nor a stronger caveat converts a low-level distribution gap into validated artistic resemblance. I do not require human ratings, new extraction or new painters for this revision; these limits simply remain in the rigor/significance assessment.

## Literature positioning and retrieval audit

1. **Benny, Galanti, Benaim and Wolf (2021), *Evaluation Metrics for Conditional Image Generation*.** Read the publisher's full-text introduction and Sections 3.1–3.3, including the conditional-FID decomposition. The prior paper separates within-class distribution mismatch from class-mean mismatch and explains how unconditional scores can hide both. The present manuscript's repeated-scene treatment is a useful empirical application of this concern, with different metrics and no matched per-scene historical target. [Publisher full text](https://link.springer.com/article/10.1007/s11263-020-01424-w).

2. **Zhang, Courville, Drozdzal and Romero-Soriano, *The Intricate Dance of Prompt Complexity, Quality, Diversity, and Consistency in T2I Models*, arXiv:2510.19557v1.** Read the primary author manuscript's introduction, synthetic motivation, benchmark construction, and Sections 4.1–4.4. Its experiments connect more specific prompts with lower conditional diversity and smaller synthetic/real shift, while tracking consistency and coverage. This is a close omitted comparison. Its prompt-complexity manipulation and image-caption matching differ from adding a painter name to fixed scenes; neither experiment identifies the other's effect. The HTML identifies a v1 preprint and also displays an August 2026 date, so citation metadata should be checked before adding it. [Author manuscript](https://arxiv.org/html/2510.19557v1).

3. **Naeem et al. (2020), *Reliable Fidelity and Diversity Metrics for Generative Models*.** Read the PMLR paper, especially the evaluation pipeline and density/coverage construction. The manuscript appropriately adopts reference-neighborhood coverage and discusses its scale dependence. The general need to distinguish fidelity and diversity is prior methodology rather than a new result here. [Primary paper](https://proceedings.mlr.press/v119/naeem20a/naeem20a.pdf).

4. **Deliège et al. (2025), *How Good Is the Machine at the Imitation Game?*** Read the institution-hosted PDF's materials and rating protocol, including Sections 2.1 and 2.2.3–2.2.4. This confirms that the historical target was experts' knowledge, not a presented fixed original-image corpus. The current manuscript fairly distinguishes its explicit reference panels and repeated-scene intervention. PMC/publisher retrieval initially failed; the university repository PDF was downloaded and text-read successfully. [Institution-hosted paper](https://orbi.uliege.be/bitstream/2268/338186/1/jimaging-11-00429.pdf).

5. **Asperti (2026), *On the Separation of Human and AI-Generated Images in CLIP Embedding Space*.** Read the author manuscript's experimental setting and robustness/descriptor sections. Its investigation of embedding separation and spatially distributed image statistics differs from prompt assignment. It supports caution about interpreting computational separation, rather than providing a reason to substitute learned features for this paper's stated target. [Author manuscript](https://arxiv.org/html/2608.25609v1).

This is a targeted search, not an exhaustive priority determination. I relied on retrieved primary text, not solely search snippets. The paper's artistic comparison is better positioned than its broader conditional-evaluation contribution.

## Highest-value feasible next analysis

**Question:** Does naming's measured proximity improvement mostly follow from a prompt-independent global change in feature location and scale, or does it require substantial reorganization of the scene-conditioned clouds?

Use a new versioned, explicitly post-result vector-analysis namespace. The released Study 1 inputs contain 31-coordinate measurements, development scalers, scene IDs, conditions, repetitions and service routes; the temporal extension retains the fresh vectors. No pixels or live operations are needed.

1. Fix a deliberately small baseline family before running it: identity, translation only, and positive isotropic scaling plus translation, `T(y) = mu_N + a (y - mu_F)`. Estimate `mu_F`, `mu_N` and `a` only from generated training scenes, without optimizing energy against the reference panel. State whether `a` matches training spread or minimizes training prediction loss; use one primary fitting rule and retain its failure cases. Do not select among many flexible maps for favorable outcomes.
2. Hold out complete scene identities with their repetitions. Apply the fitted map to the held-out free vectors; compare these baseline vectors with the actual held-out named vectors and the same fixed references. Match counts, content weights and memberships exactly. Report actual-minus-baseline energy, the remaining named-versus-baseline discrepancy, and coverage using the existing anchor construction where sample sizes permit it. Include training/held-out errors so a poor baseline is not misinterpreted as evidence of sophisticated generation behavior.
3. For FLUX, fit on the original collection and apply the unchanged mapping to the fresh free outputs. Compare with actual fresh named outputs, separately by painter. The target collection is new, but it has already been exposed during prior work: call this a post-result cross-collection check, not new prospective validation or unseen-scene generalization. Keep the two original/temporal primary families untouched.
4. Quantify conditional geometry with the existing repeated Study 1 images. A single positive isotropic map preserves nearest-centroid assignments when the same map is applied to queries and all centroids. Use this as the explicit baseline. If using several fitted folds, evaluate each fold under its single map; do not concatenate vectors transformed by different maps and then claim global retrieval invariance. Report actual differences in held-repetition retrieval or normalized scene-pair geometry, keeping training overlap and only three repeats visible.
5. Repeat the small fixed analysis in the primary and no-texture views, with already-retained pipelines as sensitivity checks. Do not turn every cell into a new confirmatory hypothesis or count correlated sensitivities as replications. A full 31-by-31 fitted affine map is unnecessary and too flexible for this question.

**What would constitute added evidence:** Out-of-training-scene and cross-collection estimates showing whether a simple scene-independent map captures the proximity gain while leaving measurable conditional reorganization unexplained. If it does, that yields a practical evaluation insight: proximity improvement can be predicted by global feature calibration even when condition structure differs. If it fails, the amount and location of the failure delimit that interpretation. Either result can be informative, provided the baseline is specified before calculation and all cases are retained.

**What would not constitute added evidence:** Restating the variance identity; generating a synthetic cartoon where contraction preserves retrieval; renaming existing metrics as a framework; fitting a flexible map on all observed named images and reporting its in-sample agreement; or describing transformed feature vectors as possible generated artworks. The baseline is a diagnostic mathematical intervention, not a transport mechanism of the image service.

This analysis cannot repair capture confounding or establish perceptual similarity. It can still strengthen the paper's stated computational contribution substantially without changing the frozen studies, public archive, four-painter scope or no-human/no-live constraints.

## Prioritized revisions

1. **Substantive, retained vectors:** Specify and execute the small held-out baseline above, or another comparably falsifiable analysis of the relation among proximity, contraction and conditional organization. Publish its inputs/memberships and all results as a successor artifact; do not mutate historical evidence.
2. **Literature and argument:** Integrate Benny et al. and Zhang et al. into the contribution comparison. State what is inherited evaluation logic and what the controlled painter-name intervention newly establishes.
3. **Narrative:** Center the paper on the controlled naming result, its temporal recurrence and the geometric diagnostic. Preserve the four-painter section as the broader descriptive context and selection record. Present the palette result as a separate control-wording boundary, with both unresolved cohorts together.
4. **Clarity using existing numbers:** Add a compact estimand/evidence comparison that distinguishes reference proximity, painter alignment, conditional geometry and palette response. Consolidate repeated caveats rather than enlarging the manuscript. This is valuable writing work but should not by itself raise the contribution score.
5. **Future study only:** Independent capture validation, different scene populations or perceptual measurements could expand external interpretation. They are outside the authorized revision and are not prerequisites for completing items 1–4.

## Genuine questions for the authors

1. Is the intended reusable contribution primarily the randomized painter-clause intervention, or a diagnostic for deciding when lower distance misrepresents conditional diversity? The current title favors the former while the cumulative discussion sometimes favors the latter.
2. Which low-complexity, reference-independent baseline would the authors consider sufficient to explain the naming gain, and what held-out failure would count against that explanation?
3. What practical decision should a reader change after seeing the unresolved palette interactions, beyond using the tested generic clause as a control? Clarifying this would justify its position in the main narrative.

## Minor presentation issues

- Figures 1–8 are readable and captions are materially accurate; no visible clipping or missing text was found. Some pages have substantial whitespace, but this is not a scientific defect and does not justify invasive layout edits.
- The abstract is dense with cohorts and counts. A shorter result hierarchy would make the main controlled finding easier to retain.
- Table 7 commendably lists all fresh primary endpoints. A similarly integrated original/fresh palette figure would reduce the reader's need to reconcile interval levels across distant sections.
- No new artwork montage or human ratings are requested. Those would introduce a different evaluative target and are not needed for the proposed analysis.

## Fixed-rubric scores

| Aspect | Score / 10 | Justification |
| --- | ---: | --- |
| Scientific rigor | **8.4** | Strong finite-panel intervention, clear conditional inference, retained failures, genuine temporal evidence, informative measurement sensitivity and good claim calibration. Remaining measurement/capture ambiguity, selected references, descriptive alignment/geometry, and palette service-error assumptions are substantive rather than cosmetic. |
| Contribution and significance | **7.4** | Useful controlled painter-name evidence and an unusually reusable numerical package. The central general lesson overlaps with close omitted literature, and the manuscript has not yet tested a sufficiently specific account connecting its multiple empirical findings. |
| Clarity and reproducibility | **8.7** | Precise definitions, transparent evidence hierarchy, readable figures and verified public numerical assets. The long sequence of studies still fragments the research narrative; public feature re-extraction is unavailable. |

**Arithmetic mean: 8.1667/10.** These scores assess the stated empirical computational paper under the unchanged rubric. No score is increased to meet a target. The proposed analysis is an opportunity, not a promised score improvement; its actual evidence and the resulting claims would require a fresh assessment.
