# Round 1 scored review — statistical and experimental validity

Reviewer: maintainer-run LLM subagent, acting as an internal skeptical reviewer. This is not independent human peer review or institutional validation. I did not consult other reviewers or earlier editorial conclusions.

Baseline commit supplied for review: `f0fe89a`.
Reviewed manuscript: `paper/paper.tex`, SHA-256 `a86ab853dddedcbf45c8d944aef3a4bc9871f022e583b2a7830c69ddfba25a17`.
Review date: 2026-09-09. Line numbers below refer to that TeX snapshot.

## Scores

The eight aspects have equal weight. Anchors: 5 = substantial unresolved defects; 7 = sound but substantial revision needed; 8 = strong with limited revisions; 9 = publication-ready as a carefully scoped empirical paper; 10 = exceptional.

| Aspect | Score / 10 | Assessment |
| --- | ---: | --- |
| 1. Research question and contribution | 8.0 | Clear questions and useful empirical distinctions; the new empirical contribution should be separated more explicitly from elementary properties of variance and retrieval. |
| 2. Study design and controls | 7.5 | Prospective paired/factorial designs and shared controls are good. One generic sentence, six fixed scenes and a selected digital reference panel leave substantial control and construct limitations. |
| 3. Statistical validity | 8.0 | Correct finite-reference randomization formulation and shared-control interaction covariance. Small-repeat approximate inference is honestly scoped, but its effective precision and calibration evidence are too difficult to assess from the paper. |
| 4. Evidence and robustness | 7.5 | Extensive retained-data sensitivities expose contrary results. They reuse the same images and cannot address reference-capture validity, semantic measurement validity or new-scene/service replication. |
| 5. Interpretation and claim calibration | 8.5 | Strong separation of computational features, perception, population inference and mechanisms. Some main claims still broaden the single generic clause or promote a realized retrieval difference beyond what its descriptive status establishes. |
| 6. Literature and positioning | 7.5 | Relevant art, generative-evaluation and compositional-benchmark connections. The exact incremental contribution and intended audience remain less clear than the methods. |
| 7. Reproducibility and transparency | 8.5 | Exceptional retention detail for an internal project; clear limitations on redistributed raw media. The prespecification summary contains a concrete mismatch, and the public replay/access boundary needs a more usable statement. |
| 8. Structure, writing and figures | 8.0 | Coherent, readable manuscript and legible plots. Main plots conceal useful repeat/scene heterogeneity, and the long cautionary exposition competes with a concise statement of the positive contribution. |

**Arithmetic mean: 63.5 / 8 = 7.9375 / 10.**

This is a sound, carefully qualified computational case study. I found no arithmetic or inferential implementation defect that overturns either study's reported primary result. It is not yet publication-ready under the stated rubric. A stronger draft is possible from existing evidence; prose changes alone cannot turn the current design into broad evidence about painter style, generic language, perception or service transfer.

## What I checked

- Read `docs/STATUS.md`, then `docs/ARTIFACTS.md`; initial working tree was clean on `research/pfg-v2-paper`, ahead 80 commits. This is an editorial review of completed versioned studies, not active-census or shared-primitive work.
- Read the whole TeX, bibliography, current manuscript README, relevant Study 1 protocol/main/inference contracts, Study 2 protocol, published primary and retrieval reports, the inference implementation, and retained primary/simulation tables. I did not audit every cited external article's full text, so the literature assessment concerns positioning rather than an exhaustive novelty search.
- Inspected existing rendered PDF pages 1, 6–11 and 14, including all four main-result figures. No clipping or illegible result labels appeared on those pages. The full TeX, including the PCA and classifier appendix, was reviewed; this is not a claim of fresh visual inspection of every PDF page.
- Ran the smallest relevant offline tests: `uv run --locked pytest -q tests/painter_distribution_study_v1/test_inference.py tests/painter_responsiveness_v1/test_design_inference.py`: **18 passed**.
- Independently reconstructed Study 2 block contrasts from `generated_chroma.csv`: standard errors 0.1208410 and 0.1233420, Welch degrees of freedom 15.24594 and 9.91481, matching the published calculations. I made no scientific source, protocol or frozen-evidence changes, and launched no collection or feature extraction. The full suite/evidence audit was unnecessary for this review-only artifact.

## Major findings and revision requests

### 1. Make the exact positive contribution and its units of generalization unmistakable

The introduction (67–91), retrieval result (482–496) and conclusion (644–654) mix an analytical fact with an empirical finding. Uniform positive rescaling leaves nearest-centroid assignments unchanged; the manuscript correctly explains this at 295–298. The useful empirical finding is that the particular retained FLUX/Monet collection exhibits contraction and higher held-repetition accuracy, while other cells move in the opposite direction. The phrase “direct counterexample” at 488–489 should explicitly mean a **realized finite-feature diagnostic counterexample**. With 72 overlapping cross-validation queries and centroids reusing observations, it is not an independently replicated estimate that naming improves expected retrieval. The current descriptive caveats help, but the strongest sentence needs the same precision.

Likewise, “generic painting language” at 509, 596–600 and 648 generalizes beyond the one tested sentence, despite the good limitation at 307–308. Use “the tested generic clause” consistently in result and conclusion claims. A significant comparison with that clause establishes neither an effect of generic language as a class nor a mechanism of instruction competition.

**Repair:** editorial. State the empirical contribution as a controlled finite-service case study showing dissociations among four measured outcomes. Distinguish the mathematical reason contraction alone is insufficient from the observed examples. Retain all opposing cells. New independent scene/service collections would be required to promote the retrieval improvement to a replicated effect; multiple generic clauses would be required for a generic-language claim.

### 2. Bring the actual support and fragility of Study 2's approximate intervals into the paper

The formulas at 732–750 and implementation are correct under the stated model. Excluding between-scene mean heterogeneity is appropriate for the explicitly fixed-scene target; treating shared controls as independent would be wrong, and the code avoids that error. Bonferroni intervals and Holm tests are not contradictory procedures here. The concern is empirical support for the approximation, not an algebraic mistake.

Four interaction draws per scene estimate each scene variance. The effective degrees of freedom are only **15.25 for Monet and 9.91 for Cézanne** (`experiment/primary.csv`), substantially more informative than an apparent sample size of 192 images. Approximately 44.5% of the Cézanne variance estimate comes from `land_fields` and 29.0% from `water_river` in an independent reconstruction. A mean-only left panel in Figure 4 makes this heterogeneity invisible. Also, Monet's interval permits an additional reduction of about 0.585 IQR units, roughly 22% of the generic point response: “unresolved” should not be read as evidence that only negligible attenuation remains plausible. No perceptual threshold is available.

The retained prospective simulation is omitted from the manuscript. Its three independent-noise scenarios give simultaneous coverage 0.9596–0.9670 and global-null family rejection 0.0330–0.0404 (`diagnostics/simulation.csv`, 5,000 trials per scenario). This supports numerical behavior under those proxy scenarios; it does not validate serial independence, unobserved tails or live-service stability. The Study 2 collection occupied approximately 49.46 minutes according to retained monotonic transport starts and latencies. Neither a long image count nor randomized order establishes independent service errors.

These are the existing global-null rows worth surfacing; brackets are 95% Wilson **Monte Carlo** intervals, not experimental confidence intervals:

| Prospective noise scenario | Null-family rejection | Simultaneous coverage |
| --- | --- | --- |
| Historical empirical proxy | .0382 [.03323, .04388] | .9618 [.95612, .96677] |
| Generic-noise multiplier 1.5 | .0330 [.02840, .03832] | .9670 [.96168, .97160] |
| Heteroskedastic normal | .0404 [.03529, .04622] | .9596 [.95378, .96471] |

The last scenario scales the six template standard deviations from 0.7 to 1.8, muted/vivid deviations by 0.8/1.4, generic deviations by 1.5 and Cézanne deviations by 1.25 (`painter_responsiveness_v1/inference.py`, `simulate_design`). This is deliberate variance heterogeneity, not serial-dependence calibration. Historical within-prompt residuals have their means removed and receive the finite-repeat variance correction; generic noise is an **unvalidated artist-free proxy**, and the implementation samples independent errors with complete availability. `studies/painter_responsiveness_v2/PROTOCOL.md:149–156` prospectively specifies 5,000 trials, global/partial nulls and hypothetical 0.25/0.5/1-IQR interactions, explicitly without a human-margin or power-threshold gate. Across the retained partial-null rows, null-family rejection ranges from .0336 to .0428. Do not describe these as validation of the realized service's independence, tail behavior, future power or interval coverage.

**Repair:** mostly editorial/presentation using retained results. Add effective df/SE and a compact calibration summary with Monte Carlo uncertainty and its assumptions; explain that the interval still admits a nontrivial measured attenuation. Show existing scene estimates or repeat-level observations alongside arm means. Report the realized service collection duration. A new, separately versioned retained-data sensitivity to influential blocks or temporal dependence could be useful, but should remain post-result and must not replace the primary test or tune the conclusion. Stronger empirical validation of repeated-generation coverage requires new replication; no reanalysis can prove independence from this single run.

### 3. Correct the prespecification map and give the reader a complete evidence hierarchy

Lines 254–258 describe detection/coverage diagnostics collectively as post-result. However, `studies/painter_distribution_study_v1/MAIN.md:126–135` prospectively requires reference coverage and grouped original/generated detection, while lines 136–141 also require PCA and painter-reference comparisons. Later revisions and cross-service diagnostics can be post-result without retroactively making the original descriptive analyses post-result. This does not inflate a primary p-value, but it is a real transparency mismatch in a paper whose credibility rests partly on prospective separation.

The manuscript also says primary endpoints were specified before evaluation-feature measurement (254–255), while the main contract states it was issued before research generation. Give the actual stronger chronology where supported. Distinguish selection of painters after earlier exploration from specification of the later tests; those are different stages.

**Repair:** editorial, checked against freezes/contracts. A compact table or paragraph should identify Study 1's eight primary tests, prospectively specified descriptive analyses, later retained-data diagnostics, Study 2's two primary tests, and secondary nominal comparisons. Do not alter frozen protocols or rebrand all secondary results as confirmatory.

## Minor findings

1. **Explain inferential versus descriptive spread more locally.** The abstract says aggregate variation decreases consistently (33–34), and the main result gives 72/72 sensitivity directions (459–466). Add an immediate finite-set/descriptive qualifier so 72 reused views are not mistaken for 72 independent corroborations. The later warning at 620–621 is correct but remote.
2. **Clarify what 31-feature proximity contributes beyond palette/rendering effects.** The manuscript appropriately reports texture dominance and a no-texture reversal (458–480), and delivery fields remain part of the estimand (625–633). Tighten the novelty paragraph around this restricted geometry. A claim about painter-style fidelity would require construct validation and better reference/capture controls, not a larger number of pipelines.
3. **Make the evidence-access boundary actionable.** Lines 656–666 disclose that full integrity replay needs separately retained response bytes. Include a persistent repository/archive identifier when publication is prepared, and distinguish commands that any reader can run from redistributed vectors from commands requiring the private/local archive. Figure reproduction alone is not independent verification of extraction. This is a publication/access issue, not evidence that retained numbers are incorrect.
4. **Do not oversell “all six scene estimates negative.”** At 524–525 this is useful heterogeneity description, but those scene estimates share a service run and do not supply a prespecified sign test. The present manuscript does not calculate such a test; keep it that way. A scene-level display is more informative than the sign count alone.
5. **Improve positioning without adding an indiscriminate literature list.** Related work (93–125) gives appropriate categories. Add a precise sentence explaining what existing fidelity/diversity and attribute-response evaluations do not answer about the named/free/generic experimental comparisons. The analytical distinction between spread and classification is familiar; the novelty lies in the controlled empirical conjunction and scope, not discovery of that distinction itself.

## Smallest scientifically defensible revision path

1. Fix the prespecification chronology and consistently name the tested clause, fixed scenes, measured features and realized retrieval diagnostic.
2. Add a concise Study 2 uncertainty/precision paragraph or table from retained df, SE and simulation records; expose scene or repeat heterogeneity in Figure 4 or an appendix. Keep the primary intervals and p-values unchanged.
3. State the positive contribution earlier and reduce repeated broad cautionary phrasing by attaching each essential limitation directly to the corresponding claim. Improve the public replay instructions without claiming unavailable raw-data validation.
4. Rebuild and inspect the manuscript. No new scientific collection is necessary to produce a stronger, defensible scoped manuscript.

The revised text can become substantially clearer and more reviewable. Scores for design and evidence should not rise merely because limitations are acknowledged more often: broader claims would still need new controls, independent reference/perceptual validation, and prospective replication in a new namespace.
