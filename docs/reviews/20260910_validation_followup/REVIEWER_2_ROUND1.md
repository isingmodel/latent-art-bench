# Reviewer 2 — validation follow-up, round 1

## Manuscript and review metadata

- **Title:** Painter Naming and the Distributional Gap Between Generated Images and Original Paintings.
- **Authors/status:** Anonymous authors; 2026 working empirical computational manuscript. No target venue is assumed.
- **Source reviewed:** `paper/paper.tex`, all 1,635 lines including all appendices; SHA-256 `be91c40bc9434d4b4f5659d7e5de1741e56302f19d3f7a90bc31475916e3a25b`.
- **PDF reviewed:** 30 pages; SHA-256 `df0ed7517857c7c27aef6e997d38fce0a5daef0577744318bcda61cec82b0d1b`. Both hashes remained unchanged through the reading and visual inspection.
- **Visual inspection:** All eight figures on pages 6, 9, 11, 12, 15, 17, 25 and 27; the complete new follow-up/discussion/access pages 15–20 and final appendices/references on pages 28–30. The bibliography and current local build guide were also read.
- **Rubric:** The unchanged three 1–10 aspects in `docs/reviews/20260909_academic_review/RUBRIC.md`, adapting the retrieved academic-paper-review skill. Methodology dimensions below are qualitative, not additional numerical scores.
- **Reviewer relationship:** Maintainer-run LLM subagent, not independent human or institutional peer review. I implemented the compact-release adapter and exports, performed its replay checks, and previously supplied bounded manuscript correction checks. This involvement gives direct knowledge of the computation but limits independence. I did not read the other reviewers' current scored reviews or the coordinator's aggregate. I consulted only my own earlier assessment when explaining score changes.
- **Access at this assessment:** The new versioned release and hosted Ubuntu/anonymous-download verification are pending. The manuscript's present-tense public-access statements are anticipatory working-draft text and receive no credit as completed public access.

## Assessment

This is a strong, carefully delimited empirical study of prompt effects in a specified image-feature space. The most informative result is the combination of improved reference proximity, incomplete coverage and lower spread under naming, together with heterogeneous scene retrieval. The new FLUX collection supplies actual fresh-output evidence for both naming directions. The image challenges likewise add measurements: they show both response to controlled operations and substantial processing sensitivity, rather than merely promising validation.

The increment is useful but remains an empirical application of established distributional ideas. It does not establish a new metric, a perceptual style scale or an explanation of the generated/reference gap. The fresh collection reuses the same templates and reference panels, and both palette collections remain imprecise about additional named-clause effects. Computational reproducibility has advanced materially: a clean, allowlisted artifact now executes the original numerical functions and connects them to the displayed results. Publication and cross-platform execution still need to happen, and the release intentionally stops short of public feature re-extraction.

## Claims and evidence

| Claim | Manuscript/evidence location | Assessment |
| --- | --- | --- |
| The four-painter generated collections have lower spread and are distinguishable from references. | Section 4; `tab:four-painter`, `tab:four-cells`, `fig:four-painter`; recomputed exploration and Stage A outputs. | **Strong for recorded image domains.** All 24 trace ratios and grouped classifier results replay. Matched-size real/real comparisons address count effects. Capture and content differences prevent a stylistic interpretation of discrimination. |
| Painter naming lowers primary discrepancy in all six controlled cells, with four adjusted rejections. | Section 5.3; `tab:contrasts`; original eight-endpoint analysis. | **Strong conditional evidence.** The paired statistic, finite assignment null, plus-one Monte Carlo calculation and fixed Holm family are explicit. The claim does not extend to every representation or all services' significance. |
| Naming improves relative alignment and usually coverage while contracting spread. | Sections 5.4–5.5; `tab:alignment`, `tab:coverage-main`, `fig:variation`; revision outputs. | **Strong descriptive evidence.** The artist-free and held-out-real baselines are present. Coverage depends on k, and joint alignment permits an individual cross-painter preference. These qualifications materially delimit the finding. |
| Contraction does not determine scene distinguishability. | Section 5.6; `fig:retrieval`; retained split/query identities and predictions. | **Strong finite-design demonstration.** Two changes are positive and four negative; the uniform-rescaling argument explains why trace alone cannot determine retrieval. There is no claim of semantic adherence or independent Bernoulli trials. |
| Extra painter-name attenuation beyond generic painting language remains unresolved. | Section 6; `fig:response`; Section 7.4 and `tab:replication`; both separate palette analyses. | **Strong support for unresolved estimates, not for a null effect.** The shared-control covariance and distinct family intervals replay. Both collections allow material negative and positive interactions. |
| The representation responds to known operations, and the primary naming pattern persists in common windows. | Sections 7.1–7.2; `fig:challenges`, `tab:geometry`; 1,706-vector measurement extension. | **Strong computational evidence with limited validation reach.** Three challenge-minus-processing means and all eight window contrasts replay. Full cross-family responses and the post-result 83.9% LBP8 share expose measurement concentration rather than establish selective constructs. |
| The naming directions recur in new FLUX outputs. | Sections 7.3–7.4; `tab:replication`; 264-request/792-measurement extension. | **Strong for the specified directional criterion.** Both negative estimates reject in the new four-test family. One new session with 24 reused scenes and shared free outputs does not estimate between-date variability or test independent investigators. |
| The release reproduces numerical analyses and all figures without the private archive. | Data availability; Appendix H; draft artifact and verification receipt below. | **Strong local computational support; public access pending.** All 98 checks pass in the fresh extracted artifact. Metadata-only acquisition/audit statements are distinguished from recomputed inference. Pixels and transport authentication are outside this check. |

## Specific strengths

1. **The controls support the actual naming question.** Study 1 changes a defined clause while retaining scene text, pairs by allocation, and evaluates discrepancy against a fixed panel. The generic clause in Study 2 reveals why named/free attenuation alone would not identify an additional painter-name response. The separate exploratory ordering is reported even though it differs from the controlled result.
2. **The statistical targets are unusually explicit.** The complete original eight-test family, new four-test family, shared-control covariance, missingness and duration restrictions are stated. Sign-randomization inference is distinguished from approximate palette intervals. The new result is not pooled with the old cohort or presented as evidence that their magnitudes are equal.
3. **The measurement follow-up is informative even where it challenges interpretation.** It includes every cross-family response, actual resampling displacement, the source of the dominant blur response, and all eight common-window contrasts. The NB2/FLUX explanation correctly locates their crop-induced changes in the references because those generated images were already square.
4. **Fresh outputs supply evidence beyond replay.** The new 72 FLUX and 192 OAuth images are measured only after the terminal collection. All four outcomes are reported, including unresolved palette results, and no exact duplicates were found in the recorded post-result integrity audit. This adds temporal evidence without claiming backend-state independence.
5. **The numerical release has an executable, narrow contract.** Vectors, fixed scalers, labels, memberships, seeds, expected outputs and unchanged scientific functions are included; the original prompt inventories and design documents are inspectable. Direct report bridges and PDF checks connect computation to manuscript displays. Source provenance, numerical licensing and absent artwork rights are distinguished.

## Genuine weaknesses and residual limitations

### W1 — Measurement validity remains narrower than the motivating artistic comparison

The controlled challenges establish response properties of these coordinates, not independent evidence that their geometry measures painterly resemblance. Nearly half the reference trace is texture; 83.9% of the mean squared texture blur displacement comes from one LBP coordinate. Tile rearrangement affects the color family more than the selected chroma contraction, and blur affects the spatial family more than tile rearrangement. Alongside the no-texture NB2/Monet reversal, these results leave practical interpretation representation-dependent. Common windows help assess shape dependence but change content and do not repair unknown capture workflows or validate the original classifiers. The manuscript correctly limits these claims; the scientific limitation nevertheless remains.

### W2 — The replication scope is one additional finite-template service collection

New images are valuable, but the FLUX design has only one new output per arm per existing scene, uses shared controls, and reuses exposed references. It does not replicate the original within-scene variance decomposition. The palette follow-up uses the same six scenes and one additional short service window. There is no estimate across service dates, independent research team or capture process. This limits transfer and prevents treating old/new effect-size differences as isolated temporal change. More independent collections or new scenes would address different parts of this limitation; another replay would not.

### W3 — Palette precision and service-error assumptions remain material

Twenty-four repeat blocks across six fixed scenes do not resolve the added named-clause interaction. The fresh intervals extend from approximately −.475 to .158 for Monet and −.263 to .336 for Cézanne. Reported quality varies substantially by arm, and the service may have time-dependent responses. Retaining those delivered outcomes is appropriate for the service-response estimand, but it prevents a fixed-rendering interpretation. Proxy calibration, recorded spacing and request-order randomization do not establish independent, stable repeat errors. The present paper reports this properly; no equivalence claim or retrospective minimum-effect threshold should be added.

### W4 — Public reproduction is still a pending external action, and numerical replay has a boundary

The current draft says the package is provided publicly, while the assessed artifact is an unpublished draft. This is a release-completion requirement, not a discovered numerical failure. A final commit-bound artifact, anonymous download and hosted Ubuntu run must precede retaining that wording in the released paper. Even after those checks, public readers can recompute statistics from vectors but cannot verify extraction from the absent original/generated pixels. The supplied source URL/license catalog does not guarantee retrieval of identical bytes. That distinction is appropriate, but means this is not end-to-end public image-level reproduction.

### W5 — The advance is substantive but incremental

The combination of prompt-controlled proximity, coverage, decomposition, retrieval and palette response is more useful than a corpus-level separation result. Fresh naming outputs and actual measurement probes further strengthen it. However, location, spread, coverage and perceptual judgment were already distinct concepts in the nearest literature. The paper offers no new estimator or validated mechanism and has limited practical interpretation outside the selected features and prompts. This constrains significance even when every reported computation is correct; extra administrative detail would not change it.

### W6 — Minor presentation defects remain

The figures themselves are readable and unclipped. Several floats interrupt prose: Figure 5 separates the mixture paragraph across pages 14–15; Figure 6 interrupts the opening replication-design paragraph across pages 16–17; Table 7 interrupts the opening Discussion paragraph across pages 18–19; Figure 7 interrupts the cross-service paragraph across pages 24–25; Table 13 splits the reproduction list across pages 28–29 and appears after Appendix H has begun. The final page contains only four references. These are feasible layout repairs, not statistical weaknesses. The current build guide is synchronized with eight figures; it is not a stale-guide defect.

## Qualitative methodology assessment

| Dimension | Assessment |
| --- | --- |
| Soundness | No new numerical inconsistency found. Pairing, weights, scope gates and family definitions survive the public adapter. Energy proximity and spread are correctly distinguished, and the paired identity includes within-generated distances. |
| Experimental design | Strong for assigned prompt effects in the finite frame. Coarse LLM content labels, post-exploration painter selection, delivered geometry/quality and one new session constrain interpretation and transfer. |
| Statistical reasoning | Fixed families and conditional inference are careful. Palette covariance accounts for shared controls but still relies on repeat-error assumptions. Challenge intervals are correctly described as exposed-panel resampling summaries. |
| Measurement | The new computations materially characterize responsiveness and window sensitivity; they also demonstrate nonselectivity and processing dependence. Perceptual or independent-capture validation remains absent. |
| Reproducibility | The locally verified package provides a complete numerical route for the manuscript's result families, with recorded-only acquisition coverage. Public download and hosted execution are not yet observed, and feature extraction requires private pixels. |
| Novelty and utility | A useful controlled empirical combination, strengthened by fresh observations and reusable numerical materials. Established evaluation ideas are applied rather than newly discovered. |
| Computational scale | The compact draft is about 11.85 MB and completes the full numerical/display replay in 53.32 seconds on the tested machine. This supports practical reuse of the finite data; it is not a benchmark of image extraction, transport or arbitrary larger corpora. |

## Primary-literature context and access

- **Deliège et al. (2025):** I read the publisher PDF's materials, expert-rating protocol, RRMap construction, limitations and conclusion. Three experts characterize historical production from knowledge and may consult resources; they are not given a fixed historical-image panel. The generated sample is 300 Midjourney v6 images. The manuscript's distinction is accurate. The present paper's increment is the explicit image panel and repeated text-only intervention, not first recognition of distributional shift or dispersion. PMC challenged access, the MDPI page returned HTTP 429, and the ORBi PDF timed out in the web reader; direct retrieval from the institutional repository succeeded. [Primary institutional copy](https://orbi.uliege.be/handle/2268/338186); [publisher DOI](https://doi.org/10.3390/jimaging11120429).
- **Kim et al. (2026):** I read the retained published text's abstract, contextual generation, discussion and generation methods. Its autoencoder/CLIP comparison and source-image-conditioned experiment with century keywords differ from the paper's naming contrast; the generation keyword filtering removes artist names and movement/period labels. This is fairly described in Related Work. Current assessment uses the already retained published article, not a claim of freshly retrieving the challenged PMC page or reading its large supplementary PDF. [Published article](https://doi.org/10.1073/pnas.2517969123).
- **Asperti (2026):** I read the arXiv v1 HTML introduction/methods and discussion, limitations and conclusion. Its CLIP separation, multiscale/scattering probes and inversion results support the distinction between computational displacement and visual judgment. They do not supply perceptual validation for this paper's 31 coordinates. The manuscript labels it a preprint and makes an appropriately limited comparison. [Primary preprint HTML](https://arxiv.org/html/2608.25609v1).
- **Naeem et al. (2020):** I read the official paper's evaluation setup, coverage definition and analytic/hyperparameter discussion. The present anchor-ball fraction is an application of that coverage construction; matching real/generated query counts and reporting k sensitivity are meaningful finite-panel adaptations. Neither the metric nor the need to separate fidelity and diversity is new here. [Official PMLR paper](https://proceedings.mlr.press/v119/naeem20a/naeem20a.pdf).

These were targeted primary-source checks, not an exhaustive literature survey. No manuscript text was sent to an external research service. The newly retrieved Deliège PDF has SHA-256 `2e962254060981cdcc58c4c0d5524e64bd882795227c05e8ced8d2b557c7e37e`; the unchanged retained Kim text has SHA-256 `511887c90d38170411a8a099bb4db34e487b9b0398bda9d6c60f93ab69662fac`.

## Verification actually performed

I exported the terminal replication extension into three new create-once files, preserving prior core/measurement exports. I screened its compact metadata and inspected the integrity audit's schema, identities and counts; the audit itself is included as recorded metadata rather than represented as publicly recomputed. The release contains all 264 requests, 792 unique request/pipeline outcomes with 31 measured coordinates, and 528 attempt/terminal metadata events. Missing reported delivery fields remain null.

The unpublished `tmp/paper-release/replication-draft-01.tar.gz` has SHA-256 `0a1a3a29b8144b91107132fe544af814fd538c56c668e13921305205af1f0c7f`, 11,846,104 bytes and 299 manifest-listed files. In its disjoint extracted directory I installed locked dependencies into a fresh environment with no inherited provider credentials, then ran `tools/paper_release.py check --release-id pprv1-20260910 --isolated --output .replayed-results`.

All **98 checks passed**: 12 exact numerical objects, 62 exact computed display files, 16 exact reports and all eight exact PDF files. The 83.9% post-result LBP diagnostic also reproduced `.838534929880718` using original IQR `.008854580480121665`. All four new endpoints matched exactly: naming estimates −.6951079233141104/−.9520240321048407 with Holm .00006/.00004; palette estimates −.15864789317217737/+.036740796803838294 with Holm .34884384852731126/.7268407457182556. The primary family is four with alpha .05 and the actual duration gate true. A separate counterfactual call to the unchanged scope function correctly withholds all four endpoints when that gate is false.

Environment: Python 3.13.11, macOS 26.6.2 arm64, NumPy 2.5.2, SciPy 1.18.1, scikit-image 0.26.0, Pillow 11.3.0 and matplotlib 3.11.1. PyWavelets distribution metadata is 1.9.0 while its module reports 1.8.0; both conventions are retained, rather than interpreting this as drift. Elapsed replay time was 53.3227 seconds. The Python audit-hook guard observed zero network and subprocess attempts; it blocked one optional `SystemVersion.plist` read. It is not an OS sandbox or hostile-code containment boundary.

The create-once receipt is `tmp/paper-release/replication-draft-01/reports/paper_reproducibility_v1/pprv1-20260910/verification.json`, SHA-256 `7dc4172050a1078bb189177c7b727eb27c79b6c73fdcd55b15651be5c75124db`. Release tests passed **19/19**, relevant Ruff checks passed, and the historical evidence audit passed **2,902 checks with zero failures** after the export. The coordinator separately reported the full offline suite's 1,228 passing tests; I did not duplicate that full run in this review. The historical audit does not itself register the new namespaces. I did not rerun raw pixel extraction or verify public access.

## Scores and changes from my preceding assessment

| Fixed aspect | Earlier round 2 | This assessment | Reason |
| --- | ---: | ---: | --- |
| Scientific rigor | 8.0 | **8.4** | Actual controlled image measurements and a complete fresh generation cohort strengthen the evidence. The cross-family matrix and unchanged crop inference establish concrete response/sensitivity properties; both FLUX effects recur under a prospectively fixed new family. The increase is for these new observations, not candid wording or replay alone. Representation/capture validity and service-error assumptions remain substantive limits. |
| Contribution and significance | 7.5 | **7.9** | The original joint empirical result is now supported by fresh naming outputs and a measured account of processing sensitivity, making it more informative and reusable. The contribution still applies known distributional concepts to a narrow prompt/reference frame, without a perceptual scale or mechanism. It is stronger than the preceding version but not an exceptional general advance. |
| Clarity and reproducibility | 8.4 | **8.7** | The integrated evidence hierarchy, all four new endpoints, complete response matrix, exact prompt inventory and successful whole-paper compact replay materially improve inspectability and reuse. No public-access points are awarded before actual release/download/Ubuntu verification. Image-level extraction remains unavailable publicly, and the float interruptions still warrant repair. |

**Reviewer mean: 8.3333/10**, compared with 7.9667 in my preceding round 2. The fixed criteria and equal weights are unchanged. Scores are not targeted to a requested aggregate. Successful publication would warrant reassessing the access component, not automatically increasing scientific rigor or novelty.

## Prioritized actions and genuine questions

**Feasible from the present manuscript, retained evidence and prepared release:**

1. Complete the final commit-bound build, publication, anonymous download and actual hosted Ubuntu replay. Retain the artifact hash, environment, command and result receipt. Investigate any platform mismatch under the already fixed tolerance; do not silently relax it. Until this is done, public-access wording is prospective.
2. Repair the listed float interruptions, especially placing the common-square table within Appendix G before Appendix H begins. Recheck the complete final PDF for clipping and awkward splits. Preserve current numerical values and scope.
3. Keep the main contrast table and discussion explicit that only fresh FLUX naming meets the stated directional criterion. The present wording is sound: neither unresolved palette result is evidence of equivalence, and changed FLUX sample size/shared controls prevent an isolated time-effect estimate.

**Questions for final release/interpretation:**

- Does the anonymously downloaded, hash-identified artifact pass the same complete numerical route on the actual Ubuntu runner, including exact scientific decisions and p-values? This is presently an unanswered access/portability question, not a suspected failure.
- Which scientifically material source pixels can eventually be made accessible under their actual rights, if any? If none can be released, numerical reproduction remains a valuable but explicit endpoint; the paper should continue to distinguish it from re-extraction.
- For any future extension, is the priority generalization to new scenes/dates or validation against independently captured paintings? These answer different residual questions and should not be combined into an undifferentiated request for more samples.

**Requires a new study or additional rights-cleared release:** independent-capture or perceptual validation; new scenes, repeated collection dates or another investigator; a sufficiently precise palette design with an independently justified relevance scale; and public source-pixel extraction. None is manufactured as a mandatory rewrite of this finite-panel paper, and none is achieved by more prose or another identical replay.

**Confidence:** High in the numerical and manuscript-coverage assessment because the full source was read, all figures inspected and the compact artifact executed. Moderate in broad artistic significance and external validity. Independence is limited by my release implementation role and the maintainer-run LLM review setting; no human expert validation or editorial acceptance is implied.
