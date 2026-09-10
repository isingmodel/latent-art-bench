# Reviewer 3 — interpretation of the geometry successor

10 September 2026. Maintainer-run LLM assessment of `pngv1-20260910`, before the revised whole-paper review. I previously supplied literature, structure and analysis suggestions, but did not implement the successor. I have now read its protocol, report, receipt and selected complete numerical fields; I have not read or changed its source. No aspect scores are assigned here.

The inspected report SHA-256 is `31a30614e52a74434e3477f2a193e787640dbac83205c687d68d2bd6478c8cfc`; the bound analysis SHA-256 is `f50be0f772a3bff8f4bc66ddc20f3e19b5c13736fd6cced632d80224e2203324`. Both match the receipt, which records source commit `459c6a88a10a209ba22619dc38d616588da8817c`. The read-only targeted command `uv run --locked pytest -q tests/painter_naming_geometry_v1/test_geometry.py tests/painter_naming_geometry_v1/test_variance.py -m 'not live'` passed **65 tests**. This is not an independent full replay or certification of the scientific model assumptions.

## Assessment of the central contribution

**Yes: the new evidence supplies a coherent empirical contribution, provided it is framed as a comparison of specified predictors and evaluation targets.** It moves beyond showing that several metrics disagree. It asks how much the measured naming change can be anticipated using generated training scenes, then evaluates the fixed predictors on other scene groups and a later collection.

The strongest current synthesis is not simply “translation transfers and radius does not.” It is that **a benchmark which better predicts the named conditional means can perform worse against the historical references**, and that the ordering among actual naming and these simple benchmarks changes across evaluation settings. This gives an evaluator an operational reason to distinguish predicting the intervention's output from improving proximity to the reference panel.

This remains an empirical extension of established conditional-evaluation ideas, not a newly discovered mathematical principle. Its significance depends on the bounded result, transparent splits, adverse cases and reproducibility, rather than the number of feature views or a mechanistic narrative.

## What the present results establish

### 1. Actual naming outperforms the specified shift/scale benchmark on held-scene mean energy

All six primary residual means are negative, ranging from −.359 to −.026; all 60 original view/pipeline cells have the same mean direction. This is useful stability across measured views, but neither 60 independent replications nor a significance test.

Fold heterogeneity must remain visible: NB2/Monet and NB2/Cézanne each have two positive residual folds; only FLUX/Monet favors actual naming in all four primary folds. The OAuth/Cézanne deletion range crosses zero. “Naming beats the benchmark on held-out scenes” therefore needs **on average across the four fixed folds**. The 18-query fold energies cannot be substituted into the original 72-query primary contrasts or used to compute a percentage explained.

Translation is also a serious baseline. Actual naming has lower held-scene mean energy than translation in five cells, while OAuth/Cézanne translation performs better than actual naming (2.122 versus 2.189). The shift/scale benchmark is not necessarily the strongest of the fixed maps.

### 2. Prediction of named scene means and reference proximity favor different maps

These are new, concrete comparisons already present in the bound results:

| Primary cell | Corrected conditional-mean residual: shift → shift/scale | Reference energy: shift → shift/scale |
| --- | ---: | ---: |
| NB2 / Monet | 3.772 → 2.545 | 4.127 → 4.118 |
| NB2 / Cézanne | 6.908 → 2.794 | 3.277 → 3.412 |
| FLUX / Monet | 8.799 → 3.286 | 1.899 → 1.962 |
| FLUX / Cézanne | 4.243 → 2.063 | 1.219 → 1.246 |
| OAuth / Monet | 5.254 → 2.546 | 2.794 → 2.868 |
| OAuth / Cézanne | 8.354 → 6.224 | 2.122 → 2.216 |

Lower is better in each column, but they measure different targets and have different units. Adding scale lowers the corrected conditional-mean prediction residual in all six cells; it raises reference energy in five. The fitted moment benchmark therefore captures part of the named scene-mean configuration without necessarily producing a closer reference distribution.

Positive residual estimates do not prove that every global location/scale model is wrong. The correction removes test-repeat noise under its assumptions; it does not remove training-parameter estimation error. Furthermore, the scalar is fitted from **total observed traces**, not optimized for conditional-mean prediction. Residuals establish limitations of this specified fitted predictor. They do not identify a scene-specific internal mechanism, an optimal predictor or an irreducible component of naming.

### 3. An old translation is sufficient to surpass actual naming on later reference energy

On the later FLUX images, translation fitted to the original cohort lowers energy from 2.266 to 1.470 for Monet and from 1.772 to .736 for Cézanne. Actual named values are 1.571 and .820. This demonstrates successful transfer of a **reference-proximity improvement** on these templates: the old vector displacement remains useful on the later free images.

It does not establish that translation accurately predicts the later named distribution or later naming-effect vector. Surpassing actual naming on the reference score is a different target from reproducing actual naming. “A transferred translation benchmark achieves lower reference energy than actual naming” is precise; “the naming mechanism is transferable translation” is not.

The original shift/scale map instead has later energies 1.901 and .992, both above actual naming. The contrast between maps is interesting, but does not yet isolate a failure of radial calibration, for the algebraic reason below.

### 4. Reference-ball occupancy and energy disagree

The later shift/scale occupancies (.605 and .750) exceed actual named occupancies (.526 and .719), even though actual naming has lower energy. This illustrates differing geometric criteria, not which criterion gives the “correct” artistic answer. This successor uses complete anchors and different query counts from the original matched-real coverage analysis, without its real/real calibration. Keep the label **fixed-reference ball occupancy** and do not numerically merge the two constructions.

### 5. Corrected variance does not explain retrieval through a single scalar ratio

Corrected between-scene variation contracts in every primary cell under both weightings. FLUX/Monet nevertheless gains in equal-scene retrieval while its corresponding corrected between/noise ratio declines to .937 of the free value. The reference-content ratio of 1.107 answers a different weighting question and cannot be used to explain the equal-scene retrieval gain.

This is a useful refined counterexample: not only total spread, but also this aggregate corrected signal/noise ratio, is insufficient to predict nearest-centroid retrieval. It leaves directional covariance and relative scene arrangement unresolved. Describe the pattern as finite-design evidence; the correction assumes stable independent repeat errors, and the fresh one-repeat FLUX cohort cannot supply its own repeat-noise correction.

## The single highest-value unresolved question

**Does the later shift/scale benchmark underperform because the old scalar contracts the later free cloud poorly, or because scaling around the old center changes its mean differently from translation?**

Let `m_old` be the original free mean, `n_old` the original named mean, `m_new` the later free mean, `delta = n_old − m_old`, and `a` the old fitted scale. The frozen maps are

```text
T1(y) = y + delta
T2(y) = n_old + a (y − m_old)

mean_new(T2) − mean_new(T1) = (a − 1)(m_new − m_old).
```

Thus a comparison of T1 and T2 changes **both** scale and output mean whenever the free mean moves across collections. The same issue can occur between a training fold and its held-out fold. “Cohort-dependent radial calibration” is currently a possible account, not an isolated explanation.

A separate post-result successor can evaluate

```text
T2c(y) = m_eval + delta + a (y − m_eval),
```

where `m_eval` is the weighted mean of the evaluation **free** cloud. This holds T1's output mean fixed and changes only scalar spread. It uses no evaluation named outcomes or reference objective to fit parameters. Because it adapts to an observed evaluation cohort, it is a cohort-level normalization benchmark, distinct from the original unchanged map transfer. The original frozen T2 result must remain.

The planned disjoint centering successor directly addresses this question. Preserve its fixed map and all existing views; do not select scales or centers by observed reference performance. No new images, live access, extractor changes or confirmatory test family are needed.

Possible outcomes all add information:

- If recentering recovers most of T2's loss relative to T1, old-center anchoring was a substantial part of its failure; a radial explanation alone is inadequate.
- If recentering leaves the loss largely intact, the old scalar itself performs poorly relative to translation at the same output mean in this comparison. This still does not prove temporal drift, because collection counts and free-arm sampling changed.
- If outcomes differ by painter, pipeline or held-scene versus later setting, the useful conclusion is the scope of this normalization's transfer. Retain that heterogeneity instead of choosing a universal label.

No further major analysis is needed before writing and reviewing the coherent revised paper once this question is answered. Cross-condition scene transfer remains an interesting future diagnostic, but adding it now would broaden rather than complete the present explanation.

## Recommended article emphasis

1. Preserve the four-painter descriptive comparison as context and expose the follow-up selection; do not imply controlled results for Sisley/Pissarro.
2. Establish the original controlled naming effect and later directional recurrence before interpreting its geometry.
3. Present the fixed identity/shift/shift-scale benchmark, held-scene averages and fold heterogeneity, then the later transfer and the separately identified centering analysis.
4. Pair the two columns above: better prediction of named conditional means and better reference proximity are different outcomes. Follow with the corrected variance/retrieval counterexample.
5. Keep measurement challenges and both unresolved palette cohorts as boundary evidence. They qualify interpretation; neither supplies the missing cause of naming contraction.

A defensible current abstract sentence is:

> Fixed maps fitted on other scenes reduced the discrepancy between free and named scene means, but their ranking depended on the evaluation target. Actual naming had lower mean reference energy than the shift/scale benchmark in all six original comparisons, whereas an original-cohort translation achieved lower reference energy than actual naming in both later FLUX comparisons.

The eventual abstract should incorporate the **actual** centering result in place of speculation about radial calibration. It should avoid “explained fraction,” “residual style,” “universal contraction mechanism,” and any statement that the fitted-map residual rejects the entire family of global feature transformations.

These findings can improve the paper's contribution and coherence. They do not predetermine a score, and they do not replace the required full-manuscript assessment under the unchanged rubric.
