# Academic review — round 1, reviewer 1

## Metadata and review scope

- **Title:** Painter Naming and the Distributional Gap Between Generated Images and Original Paintings.
- **Authors:** Anonymous authors; affiliations are not supplied.
- **Status / venue:** Local manuscript draft; no publication venue selected or assumed.
- **Year:** 2026; reviewed 9 September 2026.
- **Domain / type:** Computational art and text-to-image evaluation; empirical computational study.
- **Manuscript:** `paper/paper.tex`, all 1,275 lines, including every appendix and the bibliography; 23-page `paper/paper.pdf`.
- **Manuscript SHA-256:** `8466d0374936f884371b3acfcb73db8a7311f8a10bd16a0689ade4284cdd0b90`.
- **Working-tree commit:** `1fcbcc5860aff18549e72095526e4baed4b82128`; manuscript scientific snapshot cited in the paper: `28a9eb6`.
- **Reviewer role:** Maintainer-run LLM subagent, emphasizing statistical design and measurement validity. This is not independent human or institutional peer review.
- **Rubric:** The three fixed 1–10 criteria in `RUBRIC.md`. No older scored review or another reviewer's assessment was consulted. Scores mentioned incidentally in mandatory status/build documentation were not used as a benchmark.

I read the entire source in consecutive, untruncated segments. I inspected all six rendered figures on PDF pages 5, 9, 10, 11, 14 and 20, and verified that the rendered-page text matches the current PDF. I examined the primary Study 1 report and inference contract, the computational revision report, the Study 2 and recovery protocols, and retained Study 2 image-level chroma and primary-result tables. I independently recalculated both Study 2 interactions, standard errors, Welch degrees of freedom, simultaneous intervals and raw p-values from the retained chroma rows; they agree to numerical precision. The relevant offline tests passed: **19 tests** in `test_inference.py` and `test_prv2_analysis.py`.

This is a scientific review with targeted computational checks, not a complete audit of all historical freezes or every original pixel. I did not regenerate images, remeasure features, alter evidence, or inspect the user-owned Korean drafts.

## Executive assessment

This is a sound, useful empirical paper about a carefully delimited computational question. Its strongest contribution is the controlled prompt design: changes in painter-reference proximity are considered alongside generated spread, relative painter alignment, matched-reference coverage and scene retrieval. Study 1 provides persuasive evidence of a prompt-assignment effect in four service/painter comparisons in the specified feature geometry. The variance decomposition and FLUX/Monet retrieval example demonstrate that contraction is an incomplete description of the observed response. Study 2 supplies an informative control comparison, although its two primary painter-minus-generic interactions remain imprecise.

The main limitations are substantive rather than numerical. The feature geometry has not been validated as a measure of artistic resemblance, the reference/generation domains differ in capture and delivered geometry, and the small selected painter panels cannot establish much about other references or painters. These limitations do not invalidate the finite-image calculations, but they constrain their scientific interpretation and utility. Study 2's uncertainty additionally depends on stable independent repeat-block errors across one short collection, with only four repetitions per scene. The paper describes these boundaries correctly; describing them does not supply the missing validation or replication. Public numerical and pixel-level reproduction also remains incomplete because the archival snapshot and raw-media access are pending.

My assessment is **a solid empirical contribution with remaining substantive limits**, rather than a new general principle or validated explanation of painter imitation. I found no blocking arithmetic error or clear contradiction between the primary claims and the retained results. The most useful next revision would improve the inspectability of the uncertainty and feature definitions; a substantially stronger scientific claim requires new validation or replication, not additional caveats.

## Contributions and claim/evidence map

| Principal claim | Evidence and location | Strength and boundary |
| --- | --- | --- |
| Generated and reference collections differ across all four exploratory painters. | Section 4; Figure 1; Tables 2–3 and Appendix B. All 24 trace ratios are .206–.376; RBF balanced accuracy is .940–.983; matched-size energy exceeds original/original medians. | **Strong descriptive support** for the recorded digital collections. This does not isolate painter style or establish transfer to other capture sources or sessions. |
| Adding a painter clause improves primary reference proximity. | Section 5.3; Figure 2; Table 4; Appendix C. All six primary changes are negative, with four Holm-adjusted sharp-null rejections. Primary report values agree. | **Strong conditional evidence** for four comparisons; the other two provide negative point estimates without adjusted rejection. The null concerns the delivered service outcome, including availability, under no interference. |
| Naming improves relative painter alignment while leaving reference coverage gaps. | Section 5.4; Equation 4; Table 5; Appendix D.1–D.2. Joint named-minus-free alignment is negative on all three services; matched real coverage exceeds named coverage at k=3. | **Moderate descriptive support.** Equal-class weighting addresses mixture differences, but sparse strata, no dedicated alignment uncertainty and k-dependent coverage limit interpretation. It is a joint contrast, not individual painter recognition. |
| Aggregate contraction does not determine variation among repetitions or scene distinguishability. | Sections 5.5–5.6; Figures 3–4. OAuth/Cézanne within-scene ratio is 1.139 despite total contraction; FLUX/Monet retrieval rises from 44.4% to 59.7%. | **Strong finite-set counterexamples.** They refute a deterministic reading of contraction. They do not estimate retrieval improvement on new scenes or establish semantic adherence. |
| Additional named-clause chroma-response effects relative to a generic clause remain unresolved. | Section 6.3; Figure 5; Appendix E. Estimates −.284 and −.018; both simultaneous intervals include zero. Independent recomputation agrees. | **Well-supported statistical description**, conditional on the repeat-error model. Neither effect is established as absent or practically negligible. |
| Generic wording also attenuates the vivid-minus-muted response relative to artist-free wording. | Section 6.3; retained `generic_minus_free.csv`; nominal interval [−1.136, −.570]. | **Moderate secondary evidence** for this particular sentence and collection. It does not identify a general mechanism of instruction competition. |

## Specific strengths

### S1. The primary intervention and statistic are aligned

Section 5 holds scene descriptions fixed while changing the painter clause and retains randomized condition positions, paired memberships and all eight prespecified tests. The Appendix C swap statistic includes the within-generated energy terms; it is not a test on distances to a reference centroid masquerading as a distribution test. The inference contract and passing targeted tests support that implementation. This makes the main intervention substantially more interpretable than an unmatched comparison between two prompt corpora.

### S2. Controls address several otherwise ambiguous distribution summaries

The matched-size original/original comparisons in Section 4 address the V-statistic's nonzero finite-sample baseline. The equal-class own/cross-painter double contrast in Section 5.4 distinguishes relative painter alignment from a common shift toward both panels. The held-out real queries in Appendix D.1 provide a considerably better coverage comparator than treating one as a universal target. These are substantive improvements to the comparisons, not merely careful wording.

### S3. Repetitions reveal scientifically useful heterogeneity

Figures 3–4 and Sections 5.5–5.6 exploit the repeated-scene design to show that total spread, within-scene variability and retrieval need not move together. The OAuth/Cézanne and FLUX/Monet examples are concrete and informative. The retrieval procedure excludes the held-out output from every centroid, and the within-class diagnostic prevents success from depending solely on the three broad content classes.

### S4. Study 2 uses an appropriate control and retains shared-control uncertainty

The generic arm improves the question relative to comparing named and artist-free prompts alone. Appendix E retains the covariance arising from shared generic draws and uses a fixed two-endpoint family. The delivered 192-image grid is complete, and the earlier 49-image run is not pooled into it. The primary estimates and uncertainty calculations reproduce directly from image-level chroma values. These design and computational properties warrant credit independently of the non-significant outcome.

## Weaknesses and residual limitations

### W1. The measurement geometry remains useful but unvalidated, and domain differences are substantial

**Location:** Sections 3, 5.7, 7.2; Appendix D.3–D.4.

Median/IQR scaling provides a stable coordinate system, but it does not establish why a Euclidean unit in each feature should have equal scientific importance. Texture supplies almost half of reference trace and includes correlated multiscale summaries. The NB2/Monet reversal without texture shows that this choice can affect the direction of proximity, not just its magnitude. In addition, square NB2/FLUX outputs and nonsquare references, unresolved reference capture, and condition-associated OAuth delivery fields make the domain gap partly uninterpretable as an artistic difference. A square-only rule is not proof that the feature classifier uses shape, but it demonstrates how little artistic analysis domain classification itself requires.

This is not an objection to measuring digital images. It limits what is learned from the measured gap and how useful that gap is beyond this representation. Existing sensitivities reduce concern about a single preprocessing accident but cannot validate the construct. A stronger account needs independently selected or adjudicated references with capture/geometry common support, and a separate evaluation of whether the measurements track judgments or other relevant visual properties. Those are new research requirements; retroactive filtering on delivered quality would not solve them.

### W2. Study 2's small-sample error model has limited empirical support

**Location:** Sections 6.1–6.3; Appendix E; Figure 5.

Four repetitions per scene estimate each scene's interaction variance. The simulation checks three independent proxy-noise scenarios, not the dependence or tail behavior of the actual delivered service. One 49.5-minute collection cannot assess between-session stability. This matters particularly because Monet's primary upper interval endpoint is .016 and processing variants cross the rejection boundary. The result is correctly unresolved, but its interval should not be treated as strongly validated repeated-service coverage.

A direct retained-data calculation shows that the `land_fields` scene contributes **44.5% of Cézanne's estimated interaction variance**; the largest Monet share is **25.7%**, from `land_garden`. This concentration is not an error, nor evidence of dependence. It makes the limited variance information concrete. A compact view of all 24 block contrasts per painter, with actual collection order and scene labels, would let readers inspect influential blocks and gross instability. Such diagnostics cannot certify independence and should not replace the prespecified intervals. Independent collection periods and additional repetitions would provide stronger evidence.

### W3. The contribution's reach is limited by selected painters, scenes and control wording

**Location:** Sections 4, 5.1, 6.1 and 7.1.

Monet and Cézanne were selected after exploration; the controlled study does not test the naming effect for Sisley or Pissarro. The exploratory named/free ordering differs from Study 1, with only Sisley showing a lower pooled named median. That difference is not a contradiction because the cohorts and prompts differ, but it prevents a simple general statement that painter naming improves proximity. The generic comparison in Study 2 consists of one sentence, so it cannot distinguish artist identity from other differences in language. Finally, two palette endpoints and new scenes do not explain the contraction observed under Study 1's ordinary prompts.

The present finite-panel findings are useful as a case study. Their broader significance would grow through a prospectively selected replication across new painters/scenes and several generic phrasings. That would be a new study; presenting the same sensitivity grid more favorably cannot provide it.

### W4. Numerical transparency is strong locally, but public reproducibility is unfinished

**Location:** Data and code availability; Appendix G; `paper/README.md`.

The local repository exposes compact vectors, memberships, reports and executable tests, but the cited scientific snapshot is not yet archivally released. Full integrity-checked replay also requires a separately retained response archive; raw-media access has not been arranged. Thus an outside reader cannot currently perform the reviewer's local checks or remeasure the images from the promised release alone. That is a practical reproducibility limitation, not a criticism of retaining private bytes.

An immutable public release of the redistributable snapshot, together with a tested compact-data analysis workflow and an explicit access process for any restricted inputs, would materially improve this aspect. Documentation alone does not substitute for the release. The paper should distinguish a runnable numerical analysis from response-integrity verification and pixel remeasurement in its deliverables.

### W5. The feature inventory is too abbreviated for implementation without the repository

**Location:** Section 3 and Appendix A.1.

The table names descriptor families but omits defining parameters such as wavelet family, local-binary-pattern scales and hue/chromaticity thresholds. These choices can materially change the scientific measurement and therefore deserve a compact methods supplement or an exact link to an immutable extraction specification. The frozen Protocol 2.1 contains concrete definitions, including the stationary `db2` transform and hue bins, so this is feasible from existing materials without changing any measurement. It is a reporting limitation, not evidence that the implementation is unspecified locally.

## Qualitative methodological assessment

| Criterion | Assessment |
| --- | --- |
| Soundness | The energy statistic, paired-swap identity, variance decomposition, held-repetition retrieval and Study 2 stratified variance formulas are coherent. Checked values agree with the reports. No arithmetic defect identified. |
| Experimental design | Strong control of prompt contrasts within the finite inventories. Weak support for capture/source comparability and limited independent service replication; painter selection and control wording restrict transfer. |
| Statistical reasoning | Good correspondence between the sharp null and Study 1 randomization. Multiplicity families and shared controls are handled appropriately. Study 2's approximate small-sample inference is the main remaining inferential limitation. |
| Measurement validity | Features are interpretable and preprocessing is explicit, but their joint metric and relevance to artistic resemblance are unvalidated. Sensitivity results partly support robustness and also reveal a meaningful exception. |
| Reproducibility | Excellent local traceability and successful targeted reproduction, with substantial current barriers for external numerical and pixel-level reproduction. |
| Scalability | The computations are modest at these sizes; pairwise energy and kernel operations grow quadratically. Scalability is not a central claim or a material shortcoming for the studied collections. |

## Targeted primary-source literature context

I searched for the nearest stylistic corpus comparison and for generative-distribution and preprocessing evaluation methods. The following sources were actually read, beyond search snippets:

- **Naeem et al. (2020), Sections 1–3:** Their coverage definition is the fraction of reference neighborhoods containing generated samples, and their analysis explicitly treats sample count and neighborhood size. The present paper applies this established idea with content-matched held-out real controls; it should receive credit for its application, not for originating the fidelity/diversity distinction. [Primary paper, PMLR](https://proceedings.mlr.press/v119/naeem20a/naeem20a.pdf).
- **Deliège et al. (2025), materials, rating protocol and discussion:** They use 300 Midjourney images from 15 short movement/painter prompts and expert assessments of stylistic location, dispersion and overlap. Historical production is rated from expert knowledge, rather than from a fixed individually measured reference panel. This makes the current paper's repeated fixed-scene intervention and observable reference vectors a useful methodological difference; it does not make corpus-level distributional comparison itself novel. [Article text, Europe PMC full-text service](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12734345/fullTextXML).
- **Parmar et al., arXiv v1 (2021), Sections 3–4:** Resizing and compression alter evaluation scores, including changes with little apparent visual effect. The current processing checks are therefore well motivated, but common re-encoding cannot reconstruct or remove unknown earlier capture operations. I read the v1 text; I did not verify every change in the final CVPR version. [Primary preprint](https://arxiv.org/html/2104.11222v1).
- **Asperti (2026), Sections 3–4:** The preprint probes CLIP separation using image inversion and interpretable statistics, including examples where image perturbations strongly change feature position while appearing visually similar. This reinforces the need to keep feature effects distinct from perceptual effects. It addresses an explanatory representation question that the current service-level intervention does not resolve. [Primary preprint, version 1](https://arxiv.org/html/2608.25609v1).

Retrieval limits: the PMC browser page returned a verification page, and two publisher/PDF fetches failed. Deliège's methods and discussion were subsequently retrieved as full-text XML from Europe PMC. These sources support a **moderate, useful empirical contribution**; I found no basis to claim a new universal fidelity/diversity principle or an identified generation mechanism.

## Questions for the authors

1. Which specific art-science or measurement rationale selected the relative weighting of these 31 coordinates, and can the immutable feature specification and its pre-experiment freeze be made directly accessible from the methods?
2. Do the retained block contrasts or service timestamps show an influential short period that explains much of Study 2's variance? An explicit descriptive display would help; a non-significant serial-correlation test with this sample would not establish independence.
3. What exact release will allow an external researcher to rerun numerical estimates from standardized vectors without possessing the private response archive, and which checks will remain unavailable at that level?
4. Is the intended practical use principally a reproducible case study of these delivered services, or a proposed evaluation workflow for other painter panels? The latter would need a prospective transfer study to establish usefulness beyond this example.

## Scores under the fixed rubric

| Aspect | Score / 10 | Explanation |
| --- | ---: | --- |
| Scientific rigor | **7.8** | Strong finite-panel prompt design and correct checked calculations, with meaningful matched controls and relevant sensitivity analyses. The unvalidated measurement geometry, reference/domain comparability and limited support for Study 2 repeat-error assumptions remain substantive. Accurate limitation statements do not remove these constraints. |
| Contribution and significance | **7.2** | A useful empirical extension from corpus comparison to repeated controlled prompting, with informative heterogeneous variance/retrieval results and a generic control. The statistical tools and broad proximity/diversity distinction are established; transfer, practical perceptual relevance and an explanatory mechanism remain unestablished. |
| Clarity and reproducibility | **8.0** | Coherent study sequence, clear definitions and readable figures, complete primary families and unusually traceable local evidence. Abbreviated feature definitions and unfinished external release prevent an exceptional reproducibility score. |

**Reviewer mean: 7.6667 / 10.**

**Confidence:** High for the reading, calculations checked and assessment of the stated finite-panel estimands; moderate for novelty across all computational-art literature and for unobserved backend dependence. **Contribution level:** Moderate. **Overall recommendation:** Suitable for serious empirical-paper development with targeted revisions and a concrete public release; no venue-specific acceptance prediction is made.

## Ranked actions

| Priority | Action | Feasible scope and expected benefit |
| --- | --- | --- |
| 1 | Complete an immutable release of compact scientific inputs and test an external numerical-replay path. | **Release using existing evidence.** Makes independent checking possible; does not require new images. Keep private archive verification and pixel remeasurement as separate access levels. |
| 2 | Supply exact feature definitions and parameter choices in an accessible immutable methods supplement. | **Existing evidence / manuscript revision.** Addresses W5 and helps others evaluate the metric; copy the already frozen definitions without changing them. |
| 3 | Show all Study 2 block interactions with scene and collection-order labels, and report how variance is distributed across scenes. | **Existing retained data, explicitly new descriptive diagnostic if computed.** Makes W2 inspectable without changing the primary family, selecting blocks, or claiming that diagnostics validate independence. Preserve frozen evidence. |
| 4 | Validate the measurements against independently selected/adjudicated references and appropriate capture/geometry controls. | **New research.** Addresses the most important measurement limitation. An additional learned representation alone would be complementary evidence, not ground truth. |
| 5 | Replicate across separate service collections and prospectively selected scenes/painters; include multiple generic phrasings if painter identity is the target. | **New research.** Addresses inferential stability and transfer. Extra palette levels are needed only if response slope or saturation becomes a claim. |

The present paper does not need new images merely to retain its narrow descriptive conclusions. However, the larger gains in rigor and significance would require new evidence, rather than further editorial qualification of the same results.
