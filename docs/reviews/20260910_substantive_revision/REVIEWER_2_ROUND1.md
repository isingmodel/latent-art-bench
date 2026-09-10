# Reviewer 2 — substantive academic review, round 1

Date: 10 September 2026. This is a fresh **maintainer-run LLM subagent review**, not independent human peer review or institutional review. I had no implementation involvement in the manuscript or analyses reviewed. I read the mandatory status/artifact documents, the user-requested [DeerFlow academic-paper-review skill](https://github.com/bytedance/deer-flow/blob/main/skills/public/academic-paper-review/SKILL.md), and the [fixed rubric](../20260909_academic_review/RUBRIC.md). I did not inspect previous review reports or scores beyond the unavoidable information in `docs/STATUS.md`. Feasibility of the proposed successor diagnostic was discussed with the coordinating agent; the scores below assess only the unchanged baseline manuscript.

## Manuscript and review scope

- **Title:** *Painter Naming and the Distributional Gap Between Generated Images and Original Paintings*.
- **Authors:** Anonymous authors; no affiliations supplied.
- **Status/year:** Empirical computational manuscript, 2026; no target venue specified.
- **Domain:** Generative-image evaluation and quantitative analysis of painting reproductions.
- **Source SHA-256:** `4abff8f0b31110746eb6ab4a6de5cdc9992847fa0f0383c3ebb06d3abcbb5535`.
- **PDF SHA-256:** `dd7cca03dcd18a999b348577f65b28979d594654c577ec73037d8aa8456891bc`.
- **Reading:** Entire 1,665-line source, including all appendices; all eight figures inspected in the rendered 32-page PDF, on pages 6, 10, 12, 13, 15, 18, 26 and 28. Both manuscript hashes were checked again after reading.
- **Emphasis:** Measurement validity, content and image-processing confounding, distribution geometry, and scientifically useful additions available from retained 31-feature vectors.

This task is a new review record of closed studies, not active-census work. No scientific source, feature record, protocol, ledger, pixel collection or frozen output was changed. No generation, extraction, acquisition or human rating was performed. The four-painter exploration is an essential part of the evidence and should remain in the paper.

## Executive assessment

The paper provides strong evidence for its narrowest central result: adding a painter name changes measured proximity in the selected prompt/service/reference designs, with convincing negative FLUX contrasts in a separate temporal collection. The public numerical release, exact pairing logic, transparent missingness accounting, and separation of primary inference from later diagnostics make this an unusually inspectable empirical application. Its treatment of the unresolved palette results is careful and appropriate.

The principal remaining opportunity is substantive rather than editorial. The paper shows changes in proximity, trace, neighborhoods and retrieval, but does not test whether a simple translation and global rescaling of the artist-free cloud captures most of the observed distributional behavior. Consequently, the reader learns that the clouds differ, but relatively little about which aspects of their geometry change beyond location and radius. Moreover, the reported coexistence of contraction and increased neighborhood coverage has a concrete geometric alternative explanation in the primary literature. A constrained, cross-fitted location/scale benchmark, followed by transfer of the original FLUX map to the retained fresh cohort, would address this question directly. It would not identify a generation mechanism or validate painterly style.

I recommend substantive revision centered on that comparison. I found no fatal numerical or implementation defect in the inspected components. More robustness tables, another round of wording qualification, or more precision for the palette experiment would not resolve the main scientific limitation.

## Independent scores under the fixed rubric

| Aspect | Score / 10 | Justification |
| --- | ---: | --- |
| Scientific rigor | **8.2** | Strong conditional intervention design, correct weighted energy/swap implementation, preserved primary families, useful processing challenge and fresh FLUX directional recurrence. The geometry and capture/content alternatives materially constrain the scientific interpretation of the remaining gap. Computational response checks do not establish a validated construct, and the organization of contraction is not tested against a simple location/scale account. These are substantive limitations even for the finite-panel question. |
| Contribution and significance | **7.8** | A useful and distinctive repeated-prompt application with four-painter context, relative alignment, explicit service outcomes, and temporal evidence. It goes beyond static domain classification. However, proximity versus distribution matching is established evaluation logic; the paper mainly applies several existing summaries without yet extracting a sharper structural finding about the generated distributions. The separate unresolved palette interaction does not explain the naming result. |
| Clarity and reproducibility | **9.0** | Definitions, estimands, cohort boundaries, figures, assumptions and negative results are clear. The public release covers the statistical computations and figures, and the corrected portability contract is explicit. The remaining limitations are the long accumulation of analyses, a directly relevant missing coverage citation, and lack of public pixel re-extraction. The latter is clearly disclosed, so the numerical reproducibility claim is well scoped. |

**Reviewer mean: 8.3333 / 10.** No credit is assigned for unperformed future analyses or for achieving a desired aggregate. Overall contribution level: strong specialist empirical application, with a moderate substantive advance. Overall recommendation: substantive revision; this is not a prediction of acceptance at an unspecified venue. Confidence: high for the finite-vector methods and interpretation, moderate for broader art-historical significance and literature completeness.

## Principal claim/evidence map

| Claim | Evidence and location | Assessment |
| --- | --- | --- |
| All four exploratory painters exhibit lower generated trace and strong domain separation. | Section 4, Figure 1, Tables 2–3, Appendix B; 24 cells, trace ratios .206–.376 and RBF balanced accuracy .940–.983. | **Strong descriptive support** for those recorded feature collections. Scene/work holdout and matched-size original/original comparisons are useful. Content/capture differences remain plausible explanations; this is not validated stylistic discrimination. |
| Naming improves primary reference proximity in the controlled study. | Section 5.3, Figure 2, Table 4; six negative contrasts, four Holm rejections in eight tests. Appendix C gives the exact swap identity. | **Strong for the four rejecting conditional comparisons**, weaker for the two OAuth directions. Correctly does not establish oeuvre-level matching or an effect at fixed rendering settings. |
| Naming changes joint own/cross-painter alignment. | Section 5.4, Table 5 and Appendix D.2; equal class masses and negative changes on all three services. | **Moderate descriptive support.** Within-distribution energy terms cancel, so the contrast is a relative cross-distance interaction. It does not establish that every individual named collection favors its own painter, as NB2/Monet illustrates. |
| Naming often increases coverage while contracting the generated cloud. | Section 5.4, Table 6, Appendix D.1; same anchors and matched real/generated query counts. | **Strong as an empirical neighborhood calculation; limited structural interpretation.** Contraction toward the interior of reference neighborhoods can itself increase this metric. Matched real controls address sample size but do not isolate this geometric effect. |
| Lower trace does not determine scene distinguishability. | Sections 5.5–5.6, Figures 3–4; OAuth/Cézanne within-scene variation increases despite lower total trace, and FLUX/Monet retrieval improves. | **Strong as a finite-set counterexample.** The three-repeat empirical decomposition and overlapping retrieval training sets do not estimate a population of scenes. The manuscript states this correctly. |
| The extractor responds more to the selected image changes than to selected processing challenges. | Sections 7.1–7.2, Figure 6; paired means .158/.305/3.945, exact PNG invariance and dose responses. | **Strong computational support, limited construct validation.** Chroma change partly checks its own definition; family responses overlap and the blur response is dominated by one LBP coordinate. Unknown capture pipelines are not bounded by JPEG95/resample384. |
| The primary naming pattern persists under a common square window. | Section 7.2 and Appendix G; all eight signs and the same four Holm decisions persist. | **Strong window sensitivity result.** Cropping removes different content from reference and generated images and does not revalidate the full-view classifiers. |
| FLUX naming directions recur in newly generated images. | Sections 7.3–7.4, Table 7; 24 shared-control pairs per painter, effects −.695/−.952 and Holm .00006/.00004. | **Strong directional recurrence for these templates and references.** One retained output per scene cannot repeat the within-scene analysis, and two short-period collections do not estimate a service-date population. |
| Additional named-clause palette attenuation remains unresolved. | Section 6 and Table 7; both original and fresh named-minus-generic intervals include zero. | **Strongly supported statement of uncertainty.** The generic contrast is informative but secondary. Neither non-rejection nor interval overlap establishes equivalence or temporal stability. |
| The statistical results and figures are publicly reproducible from retained measurements. | Availability section, Appendix H, public release report and explicit r1 erratum. | **Strong numerical-reproduction support.** Inspection confirmed the scope of the local/hosted/anonymous receipts; this reviewer did not independently download and rerun the full package. Pixels, delivery authentication and re-extraction remain outside the public claim. |

## Strengths

### S1. The intervention is better identified than an unpaired imitation comparison

Section 5 holds scene text fixed and randomizes condition positions within the service/painter/scene/repetition design. All successful outputs are retained. The energy difference includes within-generated distances rather than replacing a distribution question with a mean-vector distance. Inspection of `paired_contributions` and the corresponding tests supports the Appendix C identity. This supplies a defensible prompt-assignment result even though content and rendering can mediate it.

### S2. The manuscript preserves contradictory and unresolved evidence

The four-painter exploratory named/free ordering differs from the controlled results; NB2/Monet reverses under one no-texture view; OAuth/Cézanne contracts while its within-scene trace grows; and neither palette collection resolves the additional named-clause effect. These findings are visible in the main text. Their preservation prevents an artificially universal naming narrative and makes the four-painter context scientifically useful.

### S3. The diagnostic baselines address real finite-sample problems

Matched-size original/original energy, disjoint real-query coverage, held-scene classification, fixed development scaling and content-weighted comparisons are sensible controls. They address unequal counts, repeated prompt leakage and coarse mixture differences. Their scope is carefully delimited, especially the difference between holding collections and actual capture workflows.

### S4. Processing challenges reveal weaknesses instead of being used only as a pass badge

Figure 6 retains the whole cross-family matrix. The text identifies resampling sensitivity, blur responses in spatial features, tile-boundary responses in color features and the 83.9% single-coordinate contribution to the blur texture response. This is scientifically better than reporting only three favorable change-minus-processing means. The common-square reanalysis also preserves the original inference rather than replacing the primary view.

### S5. Public numerical reproducibility is unusually complete

The code, locked environment, retained vectors, exact memberships, reported outputs and figure builders are released together. The r1 amendment explicitly distinguishes portable floating comparison from exact identities and decisions. That materially improves external inspection of a long, versioned empirical project; it is not merely an access disclaimer.

## Major weaknesses and residual limitations

### W1. The paper lacks a simple structural benchmark for the naming effect

Sections 5.3–5.6 establish lower energy, contraction, relative alignment and heterogeneous retrieval. None determines whether naming does more than translate and uniformly contract the artist-free distribution. Such a transformation can reduce cross-reference distances, increase neighborhood occupancy and leave scene retrieval unchanged. A change in retrieval rejects exact uniform transformation of the observed vectors, but does not show that the residual change is reference-aligned or important to the proximity result.

This is an opportunity to answer the paper's own distribution question, not a request for a different study. Compare the named cloud to a held-scene location/scale benchmark, and determine whether the remaining geometry improves or worsens reference proximity. Report the actual outcome even if the simple benchmark performs as well or better. The present paper's observation that contraction does not mechanically reduce energy is correct; it is not a substitute for this empirical comparison.

### W2. Coverage improvement is vulnerable to the precise geometric alternative at issue

Naeem coverage counts reference balls with at least one generated hit; it is not a probability-mass matching criterion. With only 15 or 18 anchors in 31 coordinates and k=3, balls can cover substantial interior regions. Appendix D.1's k=5 saturation is one visible symptom, but the issue is not restricted to k=5.

[Khayatkhoei and AbdAlmageed (2023), Section 4](https://proceedings.mlr.press/v202/khayatkhoei23a/khayatkhoei23a.pdf) explicitly identifies Naeem coverage as their complementary recall and demonstrates inward/outward asymmetry in higher dimensions. This does not prove that this particular dataset suffers the demonstrated pathology. It does show why contraction plus higher coverage cannot alone establish improved representation of reference variation. Include the relevant literature and evaluate the same coverage statistic on the simple location/scale benchmark using identical anchors and query selections. If benchmark coverage improves similarly, the manuscript should interpret increased occupancy as consistent with geometric centralization, without implying recovered distribution structure.

### W3. Measurement calibration is numerical response characterization, with unresolved gap attribution

The fixed metric assigns Euclidean weight to IQR-standardized coordinates with considerable redundancy, substantial texture trace, and mixed spatial/color content. The 28-coordinate view removes three derived summaries but does not decorrelate the remaining measurements. A positive challenge contrast does not validate an equal perceptual scale, painter specificity or independent-capture stability. In particular, reference captures have unknown blur, sharpening, reproduction and color workflows; the chosen processing doses cannot bound those unknown differences.

The paper acknowledges these limitations, which prevents overclaiming but does not remove their scientific cost. I do not require human ratings to pursue the stated computational question. A useful current addition is to locate any residual distributional change in a small number of development-fixed directions, rather than attaching a painterly interpretation to total texture displacement. Truly identifying capture effects would require a new independently captured/matched reproduction study, outside the retained-vector analysis.

### W4. The palette branch does not advance an explanation of the main distribution gap

The two endpoint levels measure global median chroma responsiveness under deliberate extremes. They cannot distinguish response gain, an operating-range shift or saturation, and the single generic phrase cannot isolate identity from all wording differences. The manuscript correctly says so. The findings are useful as a negative control on a simple story about naming, but they occupy considerable narrative space without explaining the contraction in Study 1. Further repeats of the same palette design would principally reduce uncertainty, not solve that explanatory problem. Keep both outcomes and the generic control, but prioritize the geometry comparison as the substantive revision.

### W5. The four-painter breadth and temporal recurrence do not establish broad transfer

Sisley and Pissarro have only exploratory evidence, while the fresh confirmatory naming collection covers FLUX and the same 24 scene templates for the two selected painters. This is a real, accurately reported limit, not a reason to omit the other painters. A revised paper should preserve their full descriptive results while avoiding a single pooled narrative of a universal naming advantage. Further generalization requires a separate prospectively sampled scene/service design; no rearrangement of existing tables supplies it.

## Prioritized substantive revisions using retained data

### R1. Test a location/scale account of naming in a successor namespace

**Scientific question:** Does actual naming improve reference proximity beyond a simple global transformation fitted to artist-free and named feature distributions, and does that relation transfer to the retained fresh FLUX cohort?

Freeze the analysis contract before executing it, in a disjoint successor namespace. The data are already exposed, so this remains a prospectively specified *post-result diagnostic*, not newly unexposed confirmation. Use the existing scaler, original 31-feature primary metric, content targets, complete detailed-condition observations and fixed scene identities. Do not refit the metric or choose transformations to optimize reference energy.

For a training subset of whole scenes, compute weighted free/named means `mu_F`, `mu_N` and traces `V_F`, `V_N`. Define two nested, transparent benchmarks:

```
T_shift(y)       = y + mu_N - mu_F
T_shift_scale(y) = mu_N + sqrt(V_N / V_F) * (y - mu_F)
```

Guard zero/nonfinite trace explicitly. These are transformations of retained feature vectors, not image interventions, feasible edits or evidence about a model's internal mechanism.

Fix four folds of six whole scenes, two per broad class. Fit each map on the other 18 scenes and evaluate it on the held-out free outputs, alongside the actual held-out named outputs. Compute energy to the same fixed references with unchanged class masses. Keep each fold's result separate before aggregating equally across the class-balanced folds; pooling differently fitted transformed clouds would add variation from fold-specific parameter estimates.

The principal descriptive contrast should be the **absolute residual energy difference**

```
E(reference, actual named held-out)
  - E(reference, transformed free held-out).
```

A negative value says the actual named output is closer than this fitted benchmark; a positive value says the benchmark is closer. A value near zero does not establish distribution equivalence. Report untransformed free, shifted free, shifted/scaled free and actual named energy, rather than a fraction or percentage "explained." Such percentages are especially unstable in the small OAuth contrasts and are not additive causal decompositions.

**Falsification criteria:** A stable residual favoring actual named outputs across held-scene folds would contradict a sufficient *proximity* account based on this global location/scale map. A reversed or negligible residual would fail to support extra reference-proximity benefit beyond that benchmark, even if named and benchmark distributions remain distinguishable. Transfer failure in the retained fresh cohort would limit the structural account to the original collection. None of these outcomes proves or disproves perceptual style imitation.

Fit one map per original FLUX painter comparison using all original scenes, then apply it unchanged to the fresh shared artist-free outputs. Compare with the fresh named outputs using that cohort's own counts and weights. This is an especially valuable held-collection test of the simple account. Do not pool old and new cohorts or interpret changed estimates as an isolated date effect.

**Uncertainty:** Overlapping training folds are not four independent observations. Ordinary sign flips of actual versus transformed outcomes are not the original exact randomization test, since the map is estimated from treatment data. A full randomization calculation would have to refit every map for every assignment and would test the sharp no-naming-effect null, not the composite location/scale account. Report all folds and leave-one-scene sensitivity as descriptive stability. If a whole-scene bootstrap is used, refit the complete procedure and label it a sensitivity over the fixed scene panel, without claiming validated scene-population coverage. No new threshold should be tuned to make the account succeed or fail.

### R2. Use coverage to distinguish centralization from occupied reference variation

Evaluate the existing matched-anchor coverage statistic for the benchmark and actual named distributions with exactly shared anchor/query identities and query counts. With cross-fitting, query-count support must be explicit: a held-out fold has only six generated examples per class, so the original Monet allocation of ten water queries cannot simply be reused within that fold. Either define a smaller feasible common allocation prospectively or evaluate the original fixed map in the complete fresh cohort; never silently change class proportions or merge different maps to create apparent support.

The useful finding is whether observed coverage gains exceed, match or fall below those created by the simple benchmark. Add one compact reference-centered display or curve illustrating that comparison. Do not add a large grid of new k values. A centroid-only limiting benchmark can be informative as a clearly labeled geometric stress test, but should not be selected after seeing the result.

### R3. Characterize residual shape only if it changes the interpretation

If R1 leaves a material residual, use a small, prospectively fixed set of directions fitted only to the 221-work development panel to display signed mean shifts, centered directional variance and central/tail quantiles for references, free, benchmark and named outputs. Report retained and omitted variation. This would distinguish an anisotropic redistribution from a simple radius change and identify which measured coordinates underlie it.

Avoid unregularized 31-dimensional whitening by the 32/38-work reference covariances, or a high-capacity affine map with hundreds of free parameters. Those would be unstable and could manufacture apparent alignment in this sample. Any reduced dimension or regularization must be fixed independently of favorable outcome differences. A Gaussian covariance-distance decomposition may summarize moments but cannot establish matching of non-Gaussian distributions; it should not replace energy or become an unlabeled FID-like artistic score.

### R4. Rebuild the scientific narrative around the result obtained

Keep all four painters, original inference and both palette outcomes. In the main text, make the structural diagnostic answer explicit: either the naming effect is substantially captured by cloud relocation/rescaling in the measured space, or named outputs exhibit additional reference-relevant structure that transfers to the second collection. Both are useful findings. Move repeated sensitivity detail to the appendix where possible. Do not append the successor as another loosely connected validation section while leaving the central contribution unchanged.

## Work requiring a new scientific study

These are future studies, not prerequisites to run the retained-vector revisions and not authorized live actions in this review:

1. **Capture attribution:** independently captured reproductions of the same physical works, with recorded processing, to estimate variation due to capture separately from work identity. Current common-square and JPEG/resampling probes cannot substitute for this.
2. **Painter/scene transfer:** new prospectively defined scenes and controlled collections for all four painters, without selecting outcomes from this exploration. Preserve the existing four-painter evidence rather than overwriting it.
3. **Palette mechanism:** intermediate instruction levels and several generic phrasings to separate shifts, slope changes and saturation. More repeats at the current two levels alone would not identify those alternatives.

Human ratings are not required for the present computational extension. Without them, the resulting conclusions should continue to concern digital image measurements rather than validated perceptual stylistic equivalence.

## Literature positioning and retrieval limits

- [Naeem et al. (2020)](https://proceedings.mlr.press/v119/naeem20a/naeem20a.pdf), particularly Sections 2–4, provides the actual neighborhood-coverage construction and its sample-count/k dependence. This supports the paper's complementary metrics and matched-size controls, but also shows that the general lesson of separating fidelity and diversity is prior work. The novelty must come from what the intervention reveals about these painting distributions.
- [Parmar et al., accessible arXiv v1](https://arxiv.org/html/2104.11222v1), Sections 3–4, gives a concrete account of resizing, compression and measurement-pipeline effects. I inspected this accessible version and the official CVPR abstract; the final CVPR PDF fetch failed. Its results motivate the current processing challenges but do not validate these 31 features or calibrate unknown painting captures.
- [Khayatkhoei and AbdAlmageed (2023)](https://proceedings.mlr.press/v202/khayatkhoei23a/khayatkhoei23a.pdf), especially Section 4 and Figure 3, supplies the directly relevant coverage/contraction alternative discussed in W2. I inspected the definitions and motivating results, not every appendix proof. Applicability to the present feature cloud must be measured, not asserted from dimensionality alone.
- [Deliège et al. (2025)](https://doi.org/10.3390/jimaging11120429), Sections 2.1 and 2.2.3, uses 300 Midjourney images and expert historical ranges rather than presenting the raters with a fixed selected historical corpus. The manuscript's distinction is accurate. Live PMC/MDPI opening encountered access errors; the relevant primary-paper passages were read from the retained local PDF extraction, including the explicit description of the historical-reference procedure. This makes the present fixed-panel repeated-prompt design useful without implying that numerical features replace expert constructs.

This was a targeted primary-source search, not a comprehensive systematic review. I did not infer the correctness of every cited 2025–2026 study from bibliography entries or search snippets.

## Author questions and minor issues

1. Is the desired scientific interpretation that naming changes only proximity/spread, or that it reorganizes variation in a reference-aligned way? The proposed benchmark would distinguish those claims without changing the data.
2. After the benchmark comparison, which single residual feature direction or distributional property best explains the remaining difference? An answer supported by held-scene and held-collection evaluation would be more informative than another list of direction counts.
3. Is the reported increase in coverage greater than a simple translation/shrinkage map creates with the same anchors? If not, the coverage result should remain an occupancy observation rather than evidence of recovered reference variation.

The figures inspected are legible, retain outliers and clearly distinguish primary versus descriptive quantities. I found no clipping or consequential rendering defect. Figure 6's labels and text appropriately prevent reading its common numerical scale as equal perceptual importance. The main minor literature issue is the missing 2023 coverage qualification. The writing could be shorter, particularly where several sensitivity counts repeat the same limitation, but wording alone would not materially raise the scientific scores.

## Verification and limits of this review

Inspected code includes the fixed feature extractor, weighted energy terms, empirical variance decomposition, paired energy contributions, matched-real coverage construction, retained-vector loader, and measurement-challenge summarization. Retained generated rows include the necessary 31-vector, scene, repetition, content class, condition, service and image identity fields for the proposed successor. I also inspected the existing diagnostic report, measurement protocol/report, public reproduction report and r1 erratum.

The smallest relevant offline check was:

```
uv run --locked pytest -q tests/painter_distribution_revision_v1/test_metrics.py tests/painter_measurement_validation_v1/test_statistics.py tests/painter_distribution_study_v1/test_inference.py -m 'not live'
```

Result: **19 passed in 1.39 seconds**. This review changes no Python behavior or freeze-bound evidence, so I did not rerun the full suite or evidence audit. I did not re-extract pixels, independently authenticate service responses, inspect every source painting, independently reproduce all 98 public-package checks, or execute any proposed new diagnostic. Public replay and raw-integrity outcomes are reported from the inspected receipts, not represented as newly verified by this reviewer. Review recommendations are separate from baseline evidence and baseline scores.
