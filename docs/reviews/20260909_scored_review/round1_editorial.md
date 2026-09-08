# Round 1 — whole-paper editorial and positioning review

Date: 2026-09-09. Reviewer: a maintainer-run LLM subagent. This is not independent human or institutional peer review. I did not consult other reviewers' findings or earlier editorial conclusions.

Reviewed baseline: `f0fe89a9179377b0a91630b775bcf7163853e66b` (`f0fe89a`).

- `paper/paper.tex` SHA-256: `a86ab853dddedcbf45c8d944aef3a4bc9871f022e583b2a7830c69ddfba25a17`
- `paper/paper.pdf` SHA-256: `ac4ef841add2f672b939d69d13e881fbc2e99368f1e5dd8dab9768b4fa547742`

Scope: the entire TeX manuscript, bibliography, manuscript README, and all 16 PDF pages. I read `docs/STATUS.md`, then `docs/ARTIFACTS.md`, and inspected the initially clean Git status. This is mutable manuscript-review work, not shared-primitive, active-census, or newly versioned scientific-study work. I also checked selected primary literature and ran `uv run --locked python paper/make_figures.py --check`: all five figures reproduced. No collection, measurement, scientific-source editing, evidence rewriting, or new analysis was performed. The review is not a fresh full numerical or evidence audit.

## Scores

All aspects have equal weight; half-points are allowed. The anchors are 5 = substantial unresolved defects, 7 = sound but substantial revision needed, 8 = strong with limited revisions, 9 = publication-ready as a carefully scoped empirical paper, and 10 = exceptional.

| Aspect | Score / 10 | Assessment |
|---|---:|---|
| 1. Research question and contribution | 7.5 | A coherent empirical question and useful counterexamples, but the distinctive advance over existing distributional style evaluation is insufficiently specified. |
| 2. Study design and controls | 7.5 | Repeated common scenes, randomized order, a generic clause, and complete replacement cohort are substantive strengths. One generic sentence, selected reference panels, and uncontrolled delivered rendering settings limit what the intervention isolates. |
| 3. Statistical validity | 8.0 | The finite-design randomization target, test families, and fixed-scene model-based interactions are unusually explicit. Four repeats per scene and unvalidated repeat-error assumptions leave real uncertainty; I found no obvious statistical contradiction in the presented formulas. |
| 4. Evidence and robustness | 8.0 | Multiple processing and feature views, reference perturbations, and all-cell reporting support the computational claims. Reused data and shared reproduction issues prevent treating these as external validation. |
| 5. Interpretation and claim calibration | 8.5 | The paper correctly rejects equivalence readings, semantic-adherence claims, and identified internal mechanisms. The meaning of the unresolved interaction intervals could be developed more quantitatively. |
| 6. Literature and positioning | 6.5 | Relevant literature is mostly described accurately, but a directly overlapping published study of historical/generated stylistic distributions is omitted. This affects the originality argument, not merely bibliography completeness. |
| 7. Reproducibility and transparency | 8.0 | Exact formulas, retained numeric inputs, provenance distinctions, and successful figure replay are strong. The standalone PDF lacks a resolvable repository/version locator and collection dates; raw-archive access remains a practical limitation. |
| 8. Structure, writing and figures | 8.0 | Clean, readable, consistent vector graphics and restrained prose. A long methodological runway and repeated negative conclusions obscure the paper's empirical contribution and the relationship among its analyses. |

Arithmetic mean: `(7.5 + 7.5 + 8 + 8 + 8.5 + 6.5 + 8 + 8) / 8 = 7.75 / 10`.

Editorial recommendation: substantial but focused revision. A defensible computational empirical paper is present. Its strongest contribution is a controlled set of observed dissociations under painter prompting, not a new general distinction between fidelity and diversity or an established account of artistic style. The scores do not reward the amount of implementation effort or the mere presence of caveats.

## Major findings

### E1. The nearest conceptual comparator is missing

Evidence: `paper/paper.tex:93–125`, especially the individual-image versus distribution-level contrast at lines 103–110 and the resulting contribution at 85–91.

Deliège, Marlot, Van Droogenbroeck, and Dondero (2025), *How Good Is the Machine at the Imitation Game? On Stylistic Characteristics of AI-Generated Images*, already compares historical and generated corpora through expert-rated relative shifts, dispersion, and overlap. It uses three experts, Midjourney v6, five movements, and ten painters. Its corpus-level ratings are a direct predecessor to the motivation here. Source: [publisher DOI](https://doi.org/10.3390/jimaging11120429), [author institutional record](https://orbi.uliege.be/handle/2268/338186), and the [primary article text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12734345/).

The present paper's distinctive contribution is the randomized addition of a painter clause to repeated fixed scene prompts, followed by within/between decomposition, held-repetition retrieval, and a controlled chroma interaction. That comparison should be explicit. A new citation alone will not resolve the issue: revise the introduction's contribution paragraph and related-work synthesis so that readers see what the intervention design establishes beyond an original/generated dispersion comparison.

Repair: editorial and literature synthesis. No new data are needed to state this narrower and more informative contribution. Do not imply that earlier work evaluated only individual images.

### E2. The relation between the two studies needs a stronger positive argument

Evidence: questions at lines 67–73, study overview at 75–91, post-result status at 254–259, palette methods at 300–357, and discussion at 586–613.

The current chain is largely a sequence of cautions: contraction does not imply poorer retrieval; artist-free attenuation does not establish painter specificity; range overlap does not establish density matching. These are correct, but the reader must reconstruct the positive empirical contribution. Study 2 changes scenes, treatment arms, and outcome and uses only one service. It is an additional controlled test of one measurable response, rather than a causal explanation of the Study 1 contraction. The manuscript acknowledges this piecemeal but never presents the inferential map compactly.

Repair: introduce a short design/estimand table or equivalent connected paragraph distinguishing (a) Study 1's eight confirmatory energy comparisons, (b) its post-result descriptive contraction/retrieval diagnostics, and (c) Study 2's two primary chroma interactions and secondary generic-control contrast. Give each its actual unit, comparison, and conclusion. State explicitly that Study 2 tests an additional observable implication and does not mediate or explain the historical covariance change. Then make the discussion develop what the observed dissociations teach an evaluator, instead of repeating all the exclusions.

This is an editorial repair. A causal explanation connecting the cohorts would require a newly designed experiment; the present paper need not make that claim to be worthwhile.

### E3. The paper is not yet self-contained enough for publication use

Evidence: service descriptions at lines 155–169 and 314–324; data availability at 656–666; the design and feature details split across pages 3–6 and 12–13.

The computational record is detailed, but the PDF itself gives no repository URL or archival identifier, commit/version reference for its accompanying package, or calendar dates for either deployed-service collection. A reader encountering only the PDF cannot resolve “the accompanying repository,” and deployment timing matters when model identifiers do not attest immutable weights. The code README is useful once one has already found the repository.

Repair: add verified collection dates and a concise release locator that resolves to the exact manuscript data/code version, including precise access status for the raw response archive. Distinguish numerical reproduction from image-level remeasurement. If public archival release has not occurred, describe that status accurately rather than implying independent access already exists. A compact design table would also make the 1,006-image total transparent: 864 detailed-condition images plus 142 short-scene images, while Study 2 uses a separate 192-image cohort.

The writing changes need no new scientific data. Making an unavailable raw archive externally accessible is a release/access decision, not something an editorial rewrite can claim to accomplish.

## Important scientific limits that prose cannot remove

These limits matter to the scores even though the manuscript largely discloses them. They are not requests to reopen terminal studies.

- **Construct validation:** lines 129–142, 177–186, 468–480, and 615–633 establish a selected digital panel, coarse LLM content coding, texture-sensitive geometry, and no independent perceptual validation. The paper can support a study of measured image statistics. A claim about artistic fidelity, stereotype prevalence across an oeuvre, or perceptual scene adherence would need independent reference and/or human validation.
- **Treatment specificity:** lines 303–308 and 318–322 show that only one generic sentence is tested and that returned quality differs by arm. The total delivered-service estimand is legitimate. A semantic painter-name effect at fixed rendering settings, or a claim about generic painting language as a class, would require further control phrasings and service-setting control in a new prospective study.
- **Precision and transfer:** lines 341–357, 521–549, and 732–750 leave the two primary interactions unresolved under approximate inference with four repeats per fixed scene. The paper should not gain certainty by emphasizing Monet's six negative scene means or JPEG's threshold crossing. More independent data would be needed to resolve small interactions or estimate transfer to new scenes/services.

None of these broader questions is required for a carefully scoped finite-service computational paper. Explicitly declining them is necessary, but does not itself add positive evidence.

## Minor findings and presentation repairs

1. **Make interval magnitude interpretable.** Lines 521–526 correctly say “unresolved,” but readers need more than a binary test outcome. The Monet interval still permits roughly 0.6 development-IQR units of additional attenuation; the Cézanne interval allows effects in both directions of roughly 0.3 units. Explain these magnitudes against the observed generic response of 2.636, explicitly as descriptive scale context and without introducing an equivalence threshold or ratio confidence interval. This clarifies the empirical uncertainty without adding data.
2. **Avoid promoting a secondary result through headings alone.** Section 4.5 is titled “Generic painting language also reduces color response” (line 509), while its prespecified primary question is named-minus-generic interaction. The text properly identifies the generic comparison as secondary. A heading such as “Color responses and named-minus-generic interactions” would better preserve that hierarchy while retaining the observed generic effect.
3. **Precisely describe AI-Pastiche's evaluations.** Lines 104–105 describe “human authenticity and prompt-adherence surveys.” The published article distinguishes a public authenticity survey from prompt-adherence evaluation by the research team and additional volunteers. Use that distinction, rather than implying identical sampling and evaluation procedures. Primary source: [Asperti et al. (2025)](https://www.mdpi.com/2504-2289/9/9/231), DOI `10.3390/bdcc9090231`.
4. **Retain the existing accurate comparisons.** The description of AI-WikiArt's caption-conditioned generation and attribution task is supported by its [primary methods](https://arxiv.org/html/2508.01408v1), section 3.2. The broader separation of fidelity/diversity is already established in [Naeem et al. (2020)](https://proceedings.mlr.press/v119/naeem20a.html); describe the present work as an application with additional controlled readouts, not discovery of that distinction.
5. **Visual inspection passed, hierarchy can improve.** All 16 pages are legible, with no clipped text, overlapping objects, broken equations, or unreadable figure labels. The first figure arrives on page 7. Figure 3 is positioned after the next subsection has begun on page 9, and Figure 4 follows the next subsection's prose on page 10. Prefer keeping each figure with the result it supports. The current blue/orange condition mapping, explicit reference lines, and caption identification of descriptive versus interval estimates are good.
6. **Shorten repetition selectively.** The abstract, introduction, results, discussion, and conclusion repeatedly restate that contraction is not retrieval loss and that non-rejection is not equivalence. Keep the boundary where a result is introduced and synthesize it once in discussion. Use the recovered space for the empirical contribution and the comparison to the omitted literature. Do not remove inferential-family or service-response qualifications merely to shorten the text.

## Minimum defensible revision path

1. Reposition the contribution against the direct corpus-level style comparator and established fidelity/diversity evaluation.
2. Add a compact design/estimand map with fixed scenes, cohorts, inferential status, and the distinct conclusions each analysis supports.
3. Rewrite the discussion around the observed dissociations, explicitly bounding Study 2's relationship to Study 1.
4. Clarify the size of the unresolved interactions and preserve the primary/secondary hierarchy in headings and summary.
5. Supply verified collection dates, a resolvable code/data release locator, and accurate raw-archive access/reproduction boundaries.
6. Rebuild and inspect every page after text/float changes; repeat the existing figure check if figure sources change.

This path can produce a substantially stronger paper without changing frozen results or gathering images. New human ratings, new reference acquisitions, new generic phrases, intermediate palettes, or additional services would strengthen different scientific claims, but are separate successor-study decisions. I would re-review the actual revised text and rendering using the same eight-aspect rubric; this review does not promise a target score after specified edits.
