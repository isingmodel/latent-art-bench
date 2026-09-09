# Academic review — round 2, reviewer 2

## Manuscript and review metadata

- **Title:** Painter Naming and the Distributional Gap Between Generated Images and Original Paintings
- **Authors:** Anonymous authors; no affiliations specified.
- **Status and domain:** Local empirical computational-art manuscript, 2026. No target venue has been supplied.
- **Review date:** 10 September 2026, Korea Standard Time.
- **Source reviewed:** Complete `paper/paper.tex`, all 1,385 lines, including every appendix; bibliography also reread.
- **Source SHA-256:** `83deb0b17af76c82d6a9899edaee9359a128ef0c31832746771fd87acda5539d`.
- **PDF reviewed:** 25-page `paper/paper.pdf`; SHA-256 `d4f731b6487a932543b943f93b5cbb95b47126cff581f3bd5f8785c0f9f2ac4c`.
- **Visual inspection:** Current rendered pages 9–16, plus pages 22–23 containing the new block-level presentation.
- **Reviewer identity:** Maintainer-run LLM subagent, emphasizing contribution, significance and nearest literature. This is not independent human or institutional peer review. I also supplied a bounded, unscored check of the coverage and literature corrections between rounds.
- **Rubric:** The unchanged three-aspect `RUBRIC.md`. I did not consult other reviewers' reports or the coordinator's aggregate review.

## Executive assessment

The revised paper is a stronger presentation of the same bounded empirical study. The main improvement is substantive reporting of an existing result: at the focal matched-neighborhood scale, naming improves coverage in five service–painter comparisons and ties in one, even while spread contracts and coverage remains below the real-query baseline. This makes the relationship between proximity, coverage and spread much more informative than the previous presentation of residual deficits alone. The revised comparison with Deliège also locates the empirical increment accurately.

The new compact replay is a real improvement in local reproducibility. I ran `make palette-check`: it reproduced both primary Study 2 estimates, intervals and adjusted p-values from the retained chroma table and request schedule, and reproduced the new descriptive block summaries. The block display exposes variation previously hidden behind six scene means. These additions do not constitute new independent observations, validate the service-error assumptions, or establish the artistic meaning of the features.

My overall assessment remains **a solid empirical contribution of moderate significance**, with strong reporting and important remaining scientific limits. There is no remaining major numerical or claim-reporting defect identified by this review. The material limits are primarily measurement/capture validity, narrow scope, Study 2 precision, and public access. Those cannot be removed through another prose revision. Minor layout corrections remain feasible before handoff; the build guide was synchronized and checked before this review was finalized.

## Main claims and current support

| Claim | Evidence in the revised paper | Assessment |
|---|---|---|
| The four-painter generated collections have lower feature spread and detectable differences from their references. | §4, Tables 2–3 and Appendix B; all 24 cells retained, trace ratios .206–.376 and RBF balanced accuracy .940–.983. | **Strong descriptive support for the recorded image domains.** This remains separate from a validated stylistic distinction or a controlled naming effect. |
| Naming improves primary reference proximity in the controlled study. | §5.3, Figure 2 and Table 4; six negative energy changes, four adjusted rejections within the fixed eight-test family. | **Strong for the stated conditional prompt intervention.** The OAuth comparisons remain unresolved; reference/prompt selection and service conditions constrain transfer. |
| Naming improves joint relative painter alignment. | §5.4 and Table 5; negative joint interaction changes under all 36 prescribed service/view/pipeline combinations. | **Moderate descriptive evidence.** It is a joint statistic, without a dedicated uncertainty analysis; NB2/Monet's individual cross-painter preference remains explicit. |
| Naming can improve matched reference coverage while reducing spread, without reaching the real-query baseline. | New Table 6 and revised §5.4; five increases and one tie at k=3, with all six named medians below the real medians. Appendix D.1 retains k=1/3/5 sensitivity. | **Strong finite-panel descriptive support.** The new table matches the retained values and meaningfully improves the joint-change account. It is not evidence of a universal coverage effect or distribution matching. |
| Contraction need not imply less repeat variability or worse scene retrieval. | §§5.5–5.6 and Figures 3–4; OAuth/Cézanne within-scene ratio 1.139; FLUX/Monet retrieval 44.4%→59.7% while between-scene spread contracts. | **Strong descriptive counterexamples.** They do not measure semantic adherence or performance on new scenes. |
| Additional named-clause chroma-response effects remain unresolved relative to the generic clause. | §6.3, Figure 5 and Appendix E; estimates −.284 and −.018 with simultaneous intervals including zero. | **Supported under the approximate fixed-scene error model.** The revised presentation does not turn non-rejection into equivalence. |
| The six negative Monet scene means conceal block-level variation. | New Appendix E.1 and Figure 7: 17 of 24 Monet block contrasts are negative; the garden contributes 25.7% of its estimated interaction variance. | **Verified descriptive summary of retained outcomes.** The display exposes heterogeneity without demonstrating repeat independence, temporal stability, or a new significance result. |
| The tested generic style clause attenuates measured chroma response relative to the artist-free arm. | §6.3: secondary contrast −.853, nominal interval [−1.136,−.570]. | **Moderate secondary support for that wording and delivered service.** This does not establish a generic-language population effect or identify why Study 1 contracts. |

## Response to the round 1 findings

| Prior finding | Status in round 2 | Consequence for assessment |
|---|---|---|
| W1: Weak bridge from fixed digital features to painter resemblance; unresolved capture and representation effects. | **Unchanged scientifically.** The expanded feature specification clarifies exactly what was measured but adds no validation. | Retained as a substantive limit on interpretation and significance. Clearer reporting does not eliminate it. |
| W2: Empirical novelty was less clear than the broad, established distributional lesson. | **Reporting concern resolved.** The introduction identifies a controlled empirical characterization, and §2 now correctly distinguishes Deliège's expert-knowledge reference ranges from explicit image panels. Coverage is attributed at its definition. | The paper is positioned more fairly. Its underlying originality remains moderate rather than becoming a new evaluation principle. |
| W3: The displayed coverage comparison omitted the artist-free arm. | **Resolved.** Table 6 includes artist-free, named and held-out real values, and the abstract/discussion specify the median comparison. | The published empirical account now includes an informative joint consequence of naming. This supports a modest contribution-score increase, not a claim of new independent evidence. |
| W4: Limited controlled scope and unresolved Study 2 precision/transfer. | **Unchanged scientifically.** Figure 7 makes block variation inspectable but does not enlarge the sample, add services or generic phrasings, or verify repeat-error assumptions. | Remains a substantive limitation, not an unresolved prose task. |
| W5: External reproducibility unavailable at the cited snapshot. | **Partly improved operationally; external access unresolved.** A compact numerical replay now runs without raw images/responses, and the manuscript distinguishes current build files from the earlier scientific snapshot. | Genuine local reproducibility gain. It does not publish the snapshot or provide external pixel access. |

My optional suggestion to show per-painter own/cross margins has not been adopted. I do not treat that as a blocking omission: the joint estimand is correctly defined, the NB2/Monet exception is explicit, and the complete matrices remain in the retained evidence.

## Specific strengths

### S1. The controlled naming question is supported by the experimental design

Section 5 preserves fixed scene text, matched prompt positions, randomized order and the complete prespecified inferential family. That design makes the measured naming contrast interpretable within its stated scope. It remains the paper's main advance over uncontrolled generated/reference comparisons.

### S2. The revised coverage result makes the joint behavior substantially clearer

Table 6 shows more than a remaining gap: the generated distribution can contract while occupying more of the reference neighborhoods. Together with the energy-term decomposition and scene retrieval, this demonstrates why a single variance reduction is an inadequate description of the observed change. The table's class/count matching and the retained real-query baseline make this comparison useful rather than merely visual.

### S3. The palette experiment has a relevant active control and now exposes its repeat variation

The generic arm addresses an ambiguity in a named/free contrast. Appendix E.1 and Figure 7 then show all block interactions underlying the estimates. In particular, 17 negative Monet blocks alongside six negative scene means prevents readers from confusing average sign consistency with uniform behavior across repetitions. The complete display is useful without being promoted into a new test.

### S4. A compact calculation path now supports direct local verification

`paper/replay_palette.py` reads three hash-checked compact inputs, validates their request identities and completeness, calls the unchanged inference routine, and compares its output with the saved results. The documented `make palette-check` command succeeded during this review. This materially improves the ability to check the primary palette calculations without requiring the separate raw-response archive.

### S5. Methods and positioning are easier to assess

The exact exploratory controls, development-painter counts and expanded feature specification reduce ambiguity about the comparison being made. Section 2 correctly distinguishes expert-derived historical style ranges, a fixed digital reference panel and image-to-image contextual transformations. These improvements help readers evaluate the contribution without implying that computational measurements supersede expert judgments. The synchronized build guide now identifies the seven figures, three compact replay inputs, required environment and separate access levels.

## Remaining weaknesses and limitations

### W1. Measurement and capture ambiguity still limit artistic significance

Texture accounts for nearly half of the primary reference trace; some coordinates are correlated; one NB2/Monet proximity direction reverses in the no-texture/resolution sensitivity (§5.7). The paid-service/reference geometry difference and unknown historical capture processes remain (§7.2 and Appendix D.4). These issues do not invalidate a finite feature-space intervention, but they constrain what the measured gap says about painter resemblance. Expanded descriptor definitions improve reproducibility, not construct validity. Independent judgments and a capture design with appropriate common support would require new research.

### W2. The contribution remains an informative application rather than a broad new principle

The controlled combination of proximity, coverage, scene decomposition and retrieval is useful. However, existing literature already distinguishes central tendency, dispersion, coverage and perceptual similarity. The new coverage table strengthens the paper's empirical account, but neither it nor the clearer novelty statement establishes a general law, a validated explanation, or a new metric. The significance score remains below the strongest empirical papers because practical interpretation beyond the specified feature geometry and prompts remains limited.

### W3. Study 2's scope and precision remain constrained

Six fixed scenes, four repetitions, a single generic phrase, one service and one short collection cannot establish a general additional painter-name effect. The intervals still permit practically nontrivial possibilities, without a validated relevance threshold. The block display reveals variation and concentration of estimated variance but cannot establish independence or stability. More repetitions alone would not solve wording, measurement or transfer questions. This limitation is accurately stated and still has practical consequences.

### W4. Local replay is stronger than external reproducibility

The compact path removes the raw-response dependency for checking Study 2's primary calculations. The scientific snapshot and current manuscript/build revision nevertheless remain unreleased, and pixel access is not arranged. An external reader cannot yet reproduce the complete advertised scientific workflow. Publication of compact records would address one access layer; remeasurement would still require a separate media arrangement. Accurate access wording should not be treated as equivalent to access itself.

## Qualitative methodology assessment

| Criterion | Current assessment |
|---|---|
| Design validity | Strong for the finite fixed-scene Study 1 prompt contrast. Study 2 has a useful active wording control but supports only its specified phrase comparison. |
| Statistical reasoning | Primary estimands and multiplicity families remain coherent and unchanged. The new block display and variance shares are appropriately descriptive. Small-sample and service-error assumptions remain material. |
| Measurements | The expanded inventory and operational details are valuable. Development fitting uses separate works by the same painters. Perceptual validity, capture comparability and sensitivity to feature geometry remain unresolved. |
| Reference comparisons | Matched real coverage and equal-class joint alignment are useful controls. New Table 6 resolves a substantive reporting omission. The sparse reference strata and selected panels remain important limits. |
| Reproducibility | Improved by a successful compact-data replay and clearer separation of source/build revisions. The primary measurements themselves are not independently reverified by that replay, and public release is pending. |
| Computational scope | Adequate for this bounded question. Mutable service identities and transfer across scenes/capture conditions matter more than computational scalability. A much larger benchmark is not a prerequisite for reporting these finite-panel results. |

## Scores and explanation of changes

| Aspect | Round 1 | Round 2 | Explanation |
|---|---:|---:|---|
| Scientific rigor | 8.0 | **8.0** | The central design, sample, measurements, estimators and assumptions are unchanged. The new display and successful replay improve inspectability, but do not provide new independent validation or repair capture and service-error uncertainty. No additional rigor points are awarded for clearer caveats. |
| Contribution and significance | 7.3 | **7.5** | The paper now develops an existing but previously omitted joint result: matched coverage improves in five cells despite contraction, while remaining below the real baseline. This makes the reported empirical contribution more informative. The increase is modest because the evidence comes from the same retained sample and the underlying methods and broader evaluation lesson remain established. Merely correcting attribution would not justify an increase. |
| Clarity and reproducibility | 8.0 | **8.4** | The full coverage contrast, block display, exact exploratory controls, expanded feature details and actual compact replay substantially improve assessability and local reproduction. The replay was executed successfully rather than inferred from prose, and the guide now documents the current workflow. Pending public access and minor float interruptions remain limits. |

**Round 2 reviewer mean: 7.9667/10**, compared with **7.7667/10** in round 1. The mean increased by 0.2000. The fixed criteria and equal weights were not changed.

**Contribution level:** Moderate, with a useful controlled empirical finding.

**Confidence:** High in the manuscript-level assessment, corrected literature comparison and coverage reporting; moderate in general literature completeness and empirical validity beyond the reported measurements. No venue-specific acceptance recommendation is implied.

## Literature basis and access limits

This reassessment uses the targeted primary-source search and reads performed for round 1; no new systematic literature search is claimed. The nearest-work assessment has not changed because the underlying study has not changed.

- **Deliège et al. (2025):** I read materials, the expert-rating protocol and RRMap construction, discussion and conclusion through Europe PMC full-text XML after PMC and publisher-page access failures. The revised paragraph accurately distinguishes 300 Midjourney v6 images from historical reference ranges elicited using the experts' knowledge; experts could consult resources, but were not supplied a fixed historical-image panel. [Primary article](https://doi.org/10.3390/jimaging11120429); [accessed full-text XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12734345/fullTextXML).
- **Kim et al. (2026):** I read the relevant published representation and contextual-generation sections in the retained `tmp/pdfs/kim2026/published.txt`. Its autoencoder/CLIP comparison and image-to-image historical-context experiment remain fairly distinguished from the present text-only naming intervention. [Published article](https://doi.org/10.1073/pnas.2517969123).
- **Asperti (2026):** I read the accessible primary preprint's relevant experimental-setting, inversion and limitations material. Its analysis of CLIP separation and low-salience perturbations is related background, not a validation of this manuscript's 31-coordinate representation. [Version 1](https://arxiv.org/html/2608.25609v1).
- **Naeem et al. (2020):** The coverage construction is now credited at its use. Its real-neighborhood definition is adapted here with matched generated and disjoint real queries; that application does not make coverage a new metric. [Primary paper, §3.2–3.3 and Eq. 5](https://proceedings.mlr.press/v119/naeem20a/naeem20a.pdf).
- **Parmar et al. (2022):** The official abstract/proceedings record was accessible, but the full PDF fetch was denied. I rely only on its stated relevance of resizing/compression, not a detailed evaluation of its experiments. [Official proceedings record](https://openaccess.thecvf.com/content/CVPR2022/html/Parmar_On_Aliased_Resizing_and_Surprising_Subtleties_in_GAN_Evaluation_CVPR_2022_paper.html).

## Verification and review boundaries

I reread every source line and the bibliography, checked the new coverage table against the retained values in the preceding unscored check, inspected the current layout on pages 9–16 and 22–23, read the compact replay implementation, and executed `make palette-check`. The output reproduced:

- Monet: estimate −0.284367715, simultaneous interval [−0.584714607, 0.015979177], Holm p=0.064857047.
- Cézanne: estimate −0.017720927, simultaneous interval [−0.343056397, 0.307614543], Holm p=0.888636789.
- The reported 17/24 negative Monet blocks, 25.7% Monet garden variance share and 44.5% Cézanne fields variance share.

The coordinator separately reports Ruff, 1,149 offline tests and the historical evidence audit of 2,902 checks with zero failures passing. I did not independently rerun those checks. No new pixel extraction, raw-response audit, image generation or human assessment was performed by this reviewer. The previous round's 19 targeted tests remain a record of that round, not a substitute for the current validation.

## Residual feasible corrections

1. **Repair the two float interruptions.** The Study 2 sensitivity paragraph stops at “basis for” on page 14 and continues after Figure 5 on page 15. The collection-history paragraph on page 22 similarly stops after “a replacement collection using” and resumes after Figure 7 on page 23. Keep these short paragraphs together or move their figures to avoid interrupting the sentences.
2. **Optional layout polish:** §7.2 starts at the bottom of page 15 with only two opening lines before continuing on page 16. Starting that subsection together would improve reading. Pages 9–16 otherwise show no clipping, overlaps, or unreadable table/figure labels; the new block figure is legible.

The initially stale `paper/README.md` was corrected during the review. I inspected the revised guide; it now documents 25 pages, seven figures, `palette-check`, its three exact input paths and the limits of numerical replay. That finding is resolved.

These are localized handoff corrections. I find no need for another broad manuscript rewrite or for adding more post-result tests.

## Requirements for stronger scientific or reproducibility claims

1. **Public release:** Publish the scientific snapshot and current compact replay/build revision with a verified external checkout path. Separately describe what media can be accessed for remeasurement.
2. **Measurement validation:** If the target expands from digital-image features to painter resemblance, obtain independent judgments and appropriately comparable reference/capture evidence in a new study. A second encoder alone is not ground truth.
3. **Transfer and response specificity:** For broader naming-specific responsiveness claims, use a new prespecified design with multiple generic phrasings and additional scenes/services; add intermediate palette levels only if response shape becomes the target.

These are routes to additional evidence, not demands to reopen closed cohorts. Further review rounds without scientific or access changes would not remove these residual limitations.

## Remaining question for the authors

What exact release package will be externally available with the final paper: the compact vectors and numerical replay, the raw-response integrity archive, the source pixels, or a documented subset of those layers? The final availability statement should be checked against the released package rather than the local workspace.
