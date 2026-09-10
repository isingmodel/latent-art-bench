# Literature positioning and article structure

Prepared 10 September 2026 by Reviewer 3, a maintainer-run LLM subagent. This is editorial and methodological advice written without reading the successor implementation or results. No manuscript, scientific source, protocol or archive is edited here. Future reviews should disclose this advisory contribution; it does not constitute implementation involvement, independent human review or evidence for any proposed outcome.

## Three primary sources: accurate positioning

### Zhang et al., arXiv:2510.19557v1

The arXiv record dates v1 to **22 October 2025** and v2 to 21 February 2026. Use 2025 and an explicit v1 identifier for the requested source; the experimental HTML's displayed August 2026 date is not its version date. Read the v1 abstract/record and HTML Sections 1–4, including benchmark construction and reference-based results. The PDF endpoint failed during this follow-up, but the primary HTML was available.

Its manipulation is prompt complexity, including description detail and concept specificity. It constructs comparable real/synthetic groups and studies diversity, consistency and distribution shift. This is close context for the present result, but is neither a painter-name intervention nor evidence for that intervention's mechanism. [Version record](https://arxiv.org/abs/2510.19557v1), [primary full text](https://arxiv.org/html/2510.19557v1).

**Concise manuscript wording:**

> Zhang et al. (2025) find that increasing prompt complexity can reduce conditional diversity while improving reference-based distribution measures. We hold scene wording fixed and add a painter clause, then test how far simple feature transformations predict the resulting distributional changes.

### Benny et al., IJCV 2021

The publisher's version of record is **2 March 2021**, volume 129, pages 1712–1731. Read the introduction, conditional metric definitions, Section 3.2 and Theorem 2. The paper develops conditional IS/FID measures, separating within-class distributions and class-mean distributions; it proves an upper-bound relationship to unconditional FID. Its theorem is about its defined metrics, not this paper's energy statistic or finite-repeat variance correction. [Publisher full text](https://link.springer.com/article/10.1007/s11263-020-01424-w).

**Concise manuscript wording:**

> Conditional-generation evaluation already distinguishes within-condition variation from the organization of condition means (Benny et al., 2021). Our repeated scenes permit a finite-design analysis of these quantities under painter naming; a fitted feature-space baseline tests whether changes beyond location and scale remain on held-out scenes.

### Khayatkhoei and AbdAlmageed, ICML 2023

Read Sections 2–5 and Equations (6)–(8) of the PMLR paper. Section 4 explicitly identifies its `cRecall` with Naeem et al.'s **Coverage**; the relevance is direct. Its high-dimensional support examples and feature-scaling experiments show inward/outward asymmetry. The asymptotic hypersphere analysis does not establish that the same distortion occurs in this finite, correlated 31-coordinate painting representation. [PMLR record](https://proceedings.mlr.press/v202/khayatkhoei23a.html), [primary paper](https://proceedings.mlr.press/v202/khayatkhoei23a/khayatkhoei23a.pdf).

**Concise manuscript wording:**

> Neighborhood coverage can respond asymmetrically to inward and outward changes in high-dimensional distributions (Khayatkhoei and AbdAlmageed, 2023). We therefore interpret coverage through matched real-query and fitted-transformation comparisons, rather than as a calibrated fraction of a painter's distribution recovered.

Do not cite this paper as a proof that the observed coverage gains are artifacts, that all nearest-neighbor metrics fail, or that switching to its symmetric metrics would solve the present measurement problem.

## BibTeX ready for editorial integration

Keys are suggestions; these entries do not modify the bibliography. Title case protection is included where useful. The second author's capitalization follows the ICML paper itself.

```bibtex
@misc{zhang2025promptcomplexity,
  author = {Zhang, Xiaofeng and Courville, Aaron and Drozdzal, Michal
            and Romero-Soriano, Adriana},
  title = {The Intricate Dance of Prompt Complexity, Quality, Diversity,
           and Consistency in {T2I} Models},
  year = {2025},
  howpublished = {arXiv:2510.19557, version 1},
  note = {Preprint},
  url = {https://arxiv.org/abs/2510.19557v1}
}

@article{benny2021conditional,
  author = {Benny, Yaniv and Galanti, Tomer and Benaim, Sagie and Wolf, Lior},
  title = {Evaluation Metrics for Conditional Image Generation},
  journal = {International Journal of Computer Vision},
  volume = {129},
  pages = {1712--1731},
  year = {2021},
  doi = {10.1007/s11263-020-01424-w},
  url = {https://link.springer.com/article/10.1007/s11263-020-01424-w}
}

@inproceedings{khayatkhoei2023asymmetry,
  author = {Khayatkhoei, Mahyar and AbdAlmageed, Wael},
  title = {Emergent Asymmetry of Precision and Recall for Measuring
           Fidelity and Diversity of Generative Models in High Dimensions},
  booktitle = {Proceedings of the 40th International Conference on Machine Learning},
  series = {Proceedings of Machine Learning Research},
  volume = {202},
  pages = {16326--16343},
  year = {2023},
  publisher = {PMLR},
  url = {https://proceedings.mlr.press/v202/khayatkhoei23a.html}
}
```

## A coherent article argument

**Central question:** What additional evidence is needed before interpreting a painter-name proximity gain as improvement in the organization of a generated collection?

**Contribution statement, conditional on completed analysis:** The paper combines a controlled painter-clause intervention with an evaluation benchmark fitted on separate scenes, checks its transfer to a later collection, and uses repeated outputs to distinguish variability among outputs from variability among scene means. The novelty lies in what this benchmark actually predicts and fails to predict in these measured collections. Location/scale maps, variance decomposition, held-out evaluation and the need for conditional metrics are established ideas.

The revised abstract should make four moves: define the measured question; state the controlled naming result and temporal recurrence; report the actual held-scene/transfer and conditional-variance result; end with the scope boundary and unresolved palette finding. Name all four painters once. Do not list every derivative count or every processing check in the abstract.

### Suggested main-text order

| Section | Question and material | Presentation priority |
| --- | --- | --- |
| 1. Introduction | Why a name-induced proximity gain is insufficient, and what a held-scene benchmark can test. | State the new diagnostic question early, before enumerating studies. Give two or three concrete contributions after results are known. |
| 2. Related work | Painting-distribution studies; conditional evaluation; prompt specificity; neighborhood geometry. | Compare estimands using the three sources above. Keep existing distinctions from Deliège and Asperti. |
| 3. Cohorts, measurements and evidence hierarchy | Shared features/scalers; four-painter exploration; original and temporal controlled cohorts; primary versus successor analyses. | One cohort table; one account of service-output estimands. Define energy, weighting and the primary randomization family once. Briefly identify processing challenges and the square-window sensitivity. |
| 4. Four-painter context and controlled naming result | All four painters' original/generated gaps; naming effect on separate Monet/Cézanne references; temporal recurrence. | Retain the four-row PCA figure and compact complete-painter summary. Put original and fresh FLUX naming estimates together. Preserve the exploratory named/free reversal and explain differing contrasts. |
| 5. Can simple feature transformations predict naming? | Exact map family and fitting objective; scene-group splits; held-scene evaluation; untouched cross-collection transfer; discrepancy/coverage relative to actual naming. | This becomes the main new result, with one coherent figure. Present every service/painter and the predefined failure cases. Distinguish predicted reference proximity from predicting the named distribution itself. |
| 6. What changes in conditional organization? | Observed decomposition; finite-repeat correction; corrected between-scene and within-scene summaries; held-repetition retrieval. | Keep these together so readers can evaluate whether map agreement leaves conditional structure unexplained. Show original and corrected estimates compactly. A scalar moment map and a diagonal map have different retrieval invariances. |
| 7. Boundary checks: measurement and palette response | Main cross-family/resampling behavior; common-square naming pattern; both original/fresh named-minus-generic palette results. | These are interpretation boundaries, not mechanisms inferred from the preceding result. One palette table or paired figure must retain both unresolved painters in both cohorts. Report secondary generic effects as secondary. |
| 8. Discussion and conclusion | Which diagnostic claims were supported; what the baseline misses; where interpretation ends. | Organize by findings, not acquisition chronology. Distinguish metric movement, conditional organization and perceptual resemblance. End with a narrow empirical conclusion. |
| Availability and appendices | Public release scope, successor access, exact protocols and full diagnostics. | State which release reproduces which manuscript results; an unchanged old release cannot be described as containing new analyses. |

Section 7 need not merge unlike estimands statistically. It groups two short boundary discussions editorially. If its combined title feels artificial, retain two short subsections or separate compact sections; neither needs its own repeated design/limitation narrative.

### What can move to appendices without erasing evidence

- Keep all four painters, their counts, PCA and main spread/discrepancy summaries in the body. Move classifier specifications and complete 24-cell entries to their existing appendix.
- Keep the full original primary family in a table, but move pair-swap derivation and detailed collection logistics to the methods appendix.
- Preserve the new corrected variance derivation and assumptions, together with the old exact finite-set identity. Do not overwrite the original decomposition or relabel it as erroneous; they target different quantities.
- Keep the main cross-family challenge finding and full matrix accessible. Shift detailed transform parameters, clipping and per-coordinate attribution to the appendix if shortening the body.
- Combine temporal design details into the cohort/methods description; the main naming and palette results should each appear beside their earlier counterpart.
- Move complete palette block displays, simulation settings and the ancillary 49-image history to the appendix while retaining the exclusion decision and the actual two-cohort intervals in the body.
- Consolidate repeated statements about fixed references, no human judgment, pipeline reuse and service identity into explicit shared scope paragraphs. Repeat a limitation only where it changes interpretation of a specific result.

## Corrected conditional variance: what the narrative must preserve

This is a conceptual check, not inspection of the implementation. For scene weights `w_b` summing to one, `R` independent repetitions within each fixed scene, scene sample means `bar_y_b`, and unbiased within-scene sample trace `s_b²`, define

```text
B_observed = sum_b w_b ||bar_y_b - sum_c w_c bar_y_c||²
W_unbiased = sum_b w_b s_b²
B_corrected = B_observed - sum_b w_b (1 - w_b) s_b² / R
```

Under independent repetitions and independent scene-mean errors, the subtraction removes the expected contribution of estimated-mean noise to the weighted between-scene quantity. The population-form observed within-scene trace uses denominator `R`, so it equals `(R - 1)/R` times `W_unbiased`; it must not be substituted silently into the correction. Unequal repeat counts require their own terms.

The corrected estimate can be negative and unstable with few repeats. Preserve negative values; they indicate finite-sample estimation behavior, not negative population variance. A changed sign in a ratio with a near-zero corrected denominator requires a stable reporting alternative, not clipping. The correction assumes error independence; random order does not establish it. It targets variability across the **fixed scene means**, not a population of new scene prompts. One fresh FLUX output per scene cannot estimate its own within-scene noise or supply the same correction without an additional assumption.

For interpretation, show whether conclusions actually change after correction. An unchanged conclusion is a useful robustness qualification; the algebra alone is not a new evaluation principle.

## Further retained-data work that could add significance

The first priority is a complete, honest result for the already proposed held-scene and temporal benchmark. More analyses should be added only if a specific unresolved interpretation remains. These suggestions are outcome-independent and do not authorize expanding the frozen protocol.

### 1. Distinguish common painting movement from painter-specific calibration

If the primary benchmark has separate maps for Monet and Cézanne, compare them with a common map fitted to both names under equal scene/class weights. Keep the reference panels out of fitting. Evaluate both maps on the same held-out generated samples and inspect joint own/cross-painter alignment, as well as proximity. This asks whether a predictor that knows painter identity adds useful structure beyond a single generic relocation of the generated cloud. It connects the strongest naming question to the existing joint alignment diagnostic, rather than adding another unrelated metric.

A common map succeeding on proximity but failing on painter alignment would delimit what proximity alone captures. A painter-specific map adding no held-out benefit would also be scientifically useful. Different parameter counts and training sample sizes need transparent reporting. Neither result identifies the service's internal mechanism. This comparison is optional if it duplicates a pre-existing map specification or the existing benchmark cannot estimate it stably.

### 2. Test conditional geometry with cross-condition scene transfer

Within-condition retrieval can improve even when a scene is represented by a different configuration of features. Fit the transformation using training scenes, then compare actual named queries with transformed free centroids for held-out scene candidates. Compare with untransformed free centroids and ordinary named-centroid retrieval under the same candidate set. Repetitions used to build centroids must be disjoint from query repetitions; fitting may not use the held-out scenes. Where possible, include normalized distances or margins so a one-query accuracy change is not the only signal.

This can establish whether the simple map transfers scene identity across naming conditions, which energy and within-condition retrieval do not establish. Both successful and unsuccessful transfer are informative. Do not concatenate differently fitted folds and reinterpret them as a single coherent feature geometry. The later FLUX collection has no within-scene repetitions, so its role would require a separately defined cross-collection centroid comparison.

### 3. Use the four-painter corpus as a descriptive scope check only if needed

A fixed version of the benchmark can be applied to the 16-scene exploratory designs without acquiring images. Keep all four painters and all three prompt/control constructions; retain the two later retries and their original status. This would test whether the diagnostic is usable beyond the two follow-up painters, while differences among controls remain part of the comparison. It would be a post-result application to previously exposed evidence, not confirmation on new painters or reinstatement of the failed original full-grid inference.

This is lower priority than the two analyses above. Extending a table from two to four painter labels is not itself a conceptual advance. Its value would be revealing a limitation or a scope boundary of the fixed diagnostic.

### Work that would mainly increase volume

- More pipelines, map families, alternative distances or random seeds without a prior interpretive question.
- An in-sample fit that optimizes directly against the target references.
- A visual demonstration that global scale preserves retrieval, or that shuffling scene labels leaves marginal distributions unchanged. These are useful correctness checks, but their logic is already established.
- A pooled old/new analysis that gains precision by discarding the changed collection design.
- Replacing an unresolved palette interaction with a more favorable secondary contrast.

The scientific advance must be judged from the completed evidence: does the benchmark give an evaluator a reliable, bounded answer that the original scalar comparisons could not? No predicted score increase is assigned to this outline, to additional citations, or to the number of new analyses.
