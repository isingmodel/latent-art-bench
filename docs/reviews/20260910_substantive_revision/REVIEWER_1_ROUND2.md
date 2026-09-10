# Reviewer 1, round 2: revised manuscript assessment

Date: 10 September 2026. This is a maintainer-run LLM assessment, not independent human peer review, institutional review or an editorial decision. Unlike my fresh round-1 assessment, this review follows my implementation of the new variance and cross-repeat residual primitives and their tests, plus the local addendum packager and its tests. I also audited the geometry orchestration and results. That involvement is a limitation of reviewer independence, not evidence of scientific validity. I did not consult the other reviewers' round-2 reports or scores. The required status document contains historical aggregate scores.

## Manuscript and procedure

- **Title:** Painter Naming and the Distributional Gap Between Generated Images and Original Paintings.
- **Authors:** Anonymous authors; affiliations and venue unspecified.
- **Type/domain:** Empirical computational evaluation of painter-name prompting and digital image distributions, 2026.
- **TeX:** `paper/paper.tex`, SHA256 `8973d78ceb7d4f81a05010e118454eabc210ecdaa4885ad85eec1e3e41cff0e5`.
- **PDF:** `paper/paper.pdf`, 36 pages and nine figures, SHA256 `ca291f0e0b04ebfa740240d697be89bbe78cfdaecae5b47b61f06acb636d3b9b`.
- **Rubric:** The unchanged three aspects and anchors in `docs/reviews/20260909_academic_review/RUBRIC.md`, adapting the requested [DeerFlow academic-paper-review skill](https://github.com/bytedance/deer-flow/blob/main/skills/public/academic-paper-review/SKILL.md).

I read all 1,871 TeX lines, including every appendix and the bibliography, inspected all 36 PDF pages in contact sheets, and inspected all nine figure pages individually. The paper hashes remained unchanged at the end of reading. I read both new protocols and the centering report, inspected the new result JSON files, and checked their connection to the manuscript. My earlier direct-formula audit of the complete geometry results remains recorded separately in `RESULTS_AUDIT_1.md`; it is not a substitute for this full manuscript review.

For this round, an additional independent calculation used NumPy array distances and explicit off-diagonal repeat products, without importing the scientific namespace functions. It checked the primary centering maps, energy values, weighted-mean identities and T1/T2 conditional residuals: 178 comparisons, maximum absolute difference `1.0658141036401503e-14`. All 60 original mean centered-minus-shift contrasts are positive, ranging from .045000 to .528676; all 18 later contrasts are positive, ranging from .180580 to .591110. I verified the two new freezes and their transitive bound files against local hashes and recorded source commits while implementing the packager. This establishes numerical consistency, not acquisition authenticity or statistical assumptions.

This assessment introduces no new image acquisition, extraction, scientific result or frozen-source change. The root orchestrator is running the integrated offline suite; I did not duplicate it. The local packager has passed 54 targeted safety tests and Ruff, but I do not count an unpublished addendum or a planned public replay as completed public access.

## Executive assessment

The revision has gained substantive scientific content. It now uses the repeated-prompt design to compare two explicit prediction targets: reproducing the named conditional scene means and approaching the reference painting panel. Adding the fitted scalar improves the corrected first target in all six primary cells, while worsening the second in five. The later cohort provides a further concrete result: an unchanged translation produces smaller reference energy than actual naming for both painters in the primary view. The evaluation-centered successor removes a real ambiguity about whether the old map's mean offset, rather than its scaling, explains its poorer proximity. These are useful empirical findings rather than additional sensitivity tables alone.

The work remains a strong, materially limited empirical application. Its general message—that favorable marginal distribution scores do not determine conditional organization—is established in generative evaluation. Its new evidence is the observed behavior of simple predictors under this painter-name intervention. The finite, selected panels, feature weighting, uncertain capture domains and limited repetitions still constrain what the observed rankings establish. The manuscript generally respects those constraints. I found no remaining mathematical defect that requires withdrawing a reported new result.

I support publication as a scoped empirical contribution after completing the new artifact access and minor presentation corrections. I do not regard the current paper as exceptional with only minor scientific limitations. Neither more precise scope wording nor another code audit would by itself remove those limitations.

## Fixed aspect scores

| Aspect | Round 2 / 10 | Change from my round 1 | Justification |
| --- | ---: | ---: | --- |
| Scientific rigor | **8.7** | **+0.6**, from 8.1 | The observed between-scene trace is now separated from repeat noise under explicit assumptions. Whole-scene fits, unchanged temporal maps, the centering algebra and the conditional-residual comparison address specific previously unresolved interpretations. Negative estimates and unfavorable folds remain visible. The remaining dependence/precision and measurement limitations are substantive, especially for the new diagnostic rankings. |
| Contribution and significance | **8.4** | **+0.7**, from 7.7 | The different outcomes for conditional prediction and reference proximity are an informative empirical result, and the centered comparison resolves an actual alternative explanation. This goes beyond cataloguing contraction. The underlying principle and tools are established, and neither a general new evaluation theory nor a validated account of how painter naming reorganizes images is established. |
| Clarity and reproducibility | **8.8** | **Unchanged**, from 8.8 | The central question is more coherent and the weighting/finite-repeat distinctions are clearer. Historical public numerical reproduction remains a concrete strength. These gains are offset by incomplete reader-facing identification/access for the new central analyses, an appendix that still documents only predecessor replay, and some avoidable length/layout problems. The unpublished addendum earns no prospective access credit. |

Arithmetic reviewer mean: **8.6333/10**. The scores use the same rubric, not a venue assumption, amount-of-work reward or desired aggregate.

## Claim/evidence map

| Claim | Evidence | Assessment |
| --- | --- | --- |
| The four named exploratory collections differ from their references and have lower spread | Section 4, Figure 1, Tables 2–3 and Appendix B; all 24 groups and matched-size baselines retained | **Strong for observed digital domains.** Content, capture and request-route differences remain possible sources. The exploratory result is not equivalent to the controlled naming effect. |
| Naming reduces primary reference energy, with four adjusted rejections | Section 5.3, Table 4 and Appendix C; complete eight-test family and exact complementary-pair identity | **Strong conditional evidence for the four NB2/FLUX comparisons.** The two OAuth directions remain unresolved; assignment inference assumes no relevant interference. |
| Both FLUX directions recur in the later collection | Section 5.6 and Appendix I; two rejections in a separate four-endpoint family | **Strong for directional recurrence on these templates.** The shared free arm, changed sample count and one later repeat prevent a clean temporal effect estimate or later noise decomposition. |
| Actual named outputs beat fitted T2 on held scenes | Section 6.2, Figure 3A and Appendix J; six primary averages and all 60 specified means negative | **Strong descriptive evidence for the specified predictor.** Only FLUX/Monet has all four primary folds negative; OAuth/Cézanne crosses zero after one scene deletion. This is not rejection of all location/scale models. |
| An unchanged translation can score better than actual naming in the later cohort | Section 6.3, Figure 3B; energies 1.470 versus 1.571 and .736 versus .820 | **A valid finite-panel counterexample.** It holds in 15/18 views, with three Monet 256-pixel reversals; neither an attainable image intervention nor representation-invariant superiority is shown. |
| The fitted scalar worsens proximity when evaluation means are held equal | Section 6.4, Equation 7 and Table 7; all 60 original and 18 later cell means positive | **Strong for this specified geometric comparison.** T2c changes only scale relative to T1 at the same weighted mean; it is evaluation-cohort adaptation, not unchanged pointwise transfer. The algebra is correctly separated from a causal attribution. |
| Corrected scene variance contracts, while retrieval need not decline | Section 7, Table 8 and Figure 5 | **Supported as finite-repeat estimates plus observed retrieval.** FLUX/Monet's equal-scene corrected signal/noise ratio falls to .937 despite better retrieval. Scalar traces cannot identify the orientation, local margins or conditional distribution producing that gain. |
| Predicting named scene means and approaching paintings favor different maps | Section 7.2, Table 9 and Appendix J; T2 lowers Q relative to T1 in all six rows and raises energy in five | **The strongest new empirical insight.** Q estimates conditional-mean mismatch under repeat assumptions; its ordering is descriptive and has no calibrated precision statement. No corrected T2c Q is claimed, appropriately. |
| Painter-specific palette attenuation beyond the generic clause is unresolved | Section 8 and Appendices E/F/I; both original and both later intervals include zero | **Supported.** The negative secondary generic contrasts do not establish a painter-specific mechanism, and two palette extremes do not identify gain versus saturation. |
| Computational response checks and public code delimit measurement interpretation | Section 9, availability section and Appendices H/K | **Strong for tested processing behavior and historical numerical replay.** Public pixel re-extraction and capture authentication are absent; the new addendum is still local at review time. |

## Specific strengths

1. **The new analysis changes the question being answered.** Table 9 makes the target distinction concrete rather than treating lower energy, trace and better conditional prediction as interchangeable. For FLUX/Monet, T2 reduces Q from 8.799 to 3.286 while increasing reference energy from 1.899 to 1.962. This is a useful audit pattern for conditional generation, even without a claim to a new metric.

2. **Center and scale are separated correctly.** Section 6.3 recognizes that T2 applied to a shifted evaluation cohort changes its mean relative to T1. Section 6.4 then compares T2c at T1's mean, preserving T2's centered distances. For later Monet, scaling at that common mean worsens energy by .591110, while the old-origin offset reduces that penalty by .160789. The opposite direction of this offset rules out the tempting explanation that old anchoring alone caused the bad scalar result.

3. **The finite-repeat correction is proportionate to the available evidence.** Equations 8 and 14–15 remove expected diagonal repeat noise, retain negative estimates and distinguish fixed scene means from random-scene sampling. The appendix reports the naive values as well as their corrected counterparts. It does not convert six positive means or 23 positive folds into a significance test. Excluding T2c from this correction is essential: its evaluation mean would induce cross-repeat dependence.

4. **Whole-scene evaluation and temporal transfer have meaningful boundaries.** Every original held fold excludes all repetitions of its six scenes from fitting. Actual and transformed clouds are scored at the same sample count. The later maps are fitted once on the original collection, and later scene deletions do not refit them. Fixed-fold deletion weighting is explicitly distinguished from a globally reweighted remaining-scene estimator.

5. **Unfavorable outcomes remain scientifically visible.** The paper retains OAuth non-rejections, original fold reversals, the OAuth/Cézanne deletion reversal, all three later Monet resolution reversals, unresolved palette effects and nonselective processing responses. These details materially constrain the interpretation of the more favorable aggregate patterns.

## Remaining substantive weaknesses

### W1. Metric and capture dependence still limit the meaning of the central proximity target

The target is explicit and legitimate, but the 31-coordinate Euclidean geometry gives correlated digital-texture coordinates substantial influence, and the references remain photographs or reproductions with unknown capture histories. The new nontexture and no-LBP sensitivities show that the principal map ordering is not solely an LBP artifact; they do not establish that the reference energy is a validated measure of painterly distribution. A translated feature cloud can score well without corresponding to attainable paintings or preserving requested objects. This affects the significance of the proximity comparison even though the mathematics is sound.

**Action:** Keep the finite digital target prominent. A stronger art-specific claim would require a distinct validation study, such as independent captures of the same reference works or a separately justified semantic/perceptual target. Human ratings are not required for the current algebraic/computational claim; they should not be added merely to make the paper appear complete.

### W2. Diagnostic orderings still have limited realized-service uncertainty characterization

Three repeats permit the stated unbiased corrections under stable independent errors, but do not demonstrate those assumptions or give a reliable empirical error law. Overlapping folds, reused processing views and scene-deletion ranges do not quantify the chance that a map ranking or a corrected ratio would reverse under fresh draws from the same prompts. The corrected residuals are noisy enough to include a negative primary fold. The current wording is mostly appropriate; the remaining weakness is evidential precision, not a missing generic error bar.

**Action:** Preserve the distinction between estimated conditional targets and observed scores. If stronger ordering claims are desired, specify a fixed-scene repeat-generation estimand and collect independent repeats under a separately frozen design. Do not bootstrap scenes and label the interval fixed-scene uncertainty; do not treat four folds as independent units. An R=2 leave-one-repeat display could be a sensitivity diagnostic, but it would not close this inferential gap and is not required to repair the present claims.

### W3. The contribution is a bounded empirical demonstration, with limited generalization or mechanism

The general distinction between marginal proximity and conditional organization predates this paper. The new predictor comparisons reveal which simple feature-space accounts succeed in these collections, but do not explain which scene relations or content changes produce the residual mismatch. The temporal study reuses the same templates and reference panels after a short interval, and the additional centering diagnostic was selected after seeing the first map results. Its complete grid and explicit post-result label are good practice, but do not make it an unexposed validation.

**Action:** Present the observed T1/T2/Q comparison as the contribution, as the introduction now largely does. A future externally specified scene panel would provide a more discriminating test than further variants on these 24 scenes. Per-scene contributions already exported could support a small descriptive illustration of where mismatch lies, but more such displays would not establish a mechanism or automatically make the contribution exceptional. No new retained-data computation is required to correct a detected mathematical defect in the current paper.

### W4. The revised central analyses do not yet have the paper's historical public-access standard

The availability text says that the subsequent analysis is separately versioned as “the moment-map diagnostic,” without giving its actual namespace or run ID. Appendix K still explains only `tools/paper_release.py`, which does not replay Sections 6–7's new analyses. The local files, freezes and prospective packaging workflow exist, but the preceding immutable archive explicitly lacks them. A reader following the present public link cannot reproduce the new central result from that link alone.

**Action:** Complete the additive release, verify it in a fresh environment, and cite its exact asset and checksum. Name `painter_naming_geometry_v1` / `pngv1-20260910` and `painter_naming_centering_v1` / `pncv1-20260910`, with both module verification commands and the predecessor dependency. Clearly state which paper sections each archive reruns. Preserve the preceding public assets. This is a concrete release/documentation task, not a need for new scientific data.

## Literature positioning

The updated literature discussion substantially improves the manuscript's positioning. I read the following primary sources during this round, rather than relying on search snippets:

- [Benny et al., Evaluation Metrics for Conditional Image Generation](https://link.springer.com/article/10.1007/s11263-020-01424-w), particularly Sections 1 and 3. Their conditional metrics distinguish within-class distributions from organization of class means, and show why a marginal score can overlook conditional disagreement. That principle is not new here. The manuscript's distinctive contribution is the controlled naming intervention and two-target predictor evidence, not discovery of the distinction itself.
- [Zhang et al., The Intricate Dance of Prompt Complexity, Quality, Diversity, and Consistency in T2I Models, v1](https://arxiv.org/html/2510.19557v1), particularly Sections 3–4. Their conditional prompt-complexity framework already observes different movements in diversity and reference-based measures. Holding scene text fixed while adding a painter clause is a meaningful different intervention. The current comparison is fair; it should remain an empirical extension rather than an assertion that fidelity/diversity tension itself is novel.
- [Khayatkhoei and AbdAlmageed, Emergent Asymmetry of Precision and Recall](https://proceedings.mlr.press/v202/khayatkhoei23a/khayatkhoei23a.pdf), abstract, motivating geometry and metric definitions. Their high-dimensional k-nearest-neighbor asymmetry motivates caution but is not a theorem about this paper's specific occupancy values. The manuscript appropriately says it motivates a comparison, and uses observed energy/occupancy disagreement rather than claiming to have demonstrated their asymptotic phenomenon in 31 coordinates.
- [Diedrichsen and Kriegeskorte, Representational models](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005508), especially the cross-validated distance section. Independent-partition inner products are an established way to remove positive noise bias in squared distances. A brief methodological citation near Appendix J would acknowledge that lineage. The present Q is Euclidean and unwhitened; it should not be described as a Mahalanobis/crossnobis estimator without those extra operations.

The painting-specific primary-source comparisons examined in round 1 remain relevant. I did not re-authenticate every older paper or every artwork source in this round. There is no material literature-positioning omission that requires changing the scientific result.

## Presentation and remaining author-facing clarifications

1. **Repair page 34's nearly empty layout.** It contains only the last short paragraph of Appendix J. Review the long `samepage` grouping/float barriers before Appendix K; this is a presentation change and should not touch frozen reports.
2. **Make the new predictor targets easier to scan.** Table 9 is the central scientific comparison. In its first main-text mention, state explicitly that Q is an estimated squared conditional-mean error and energy is an empirical marginal discrepancy; “lower-is-better” alone does not explain their different units or why one has noise correction. The caption and appendix already contain the ingredients.
3. **Clarify public addendum identity and commands.** This is the highest-priority reader-facing issue above. Appendix K can give one concise second command block and an exact namespace/run mapping rather than further prose about versioning.
4. **Increase Figure 3's legend/label size if feasible.** The plot is interpretable at page scale, but the two-panel legend and service labels are smaller than in the other main figures. I found no clipped data, missing figures, unreadable equation boxes or broken citation markers in the inspected PDF.

## Prioritized revision plan and confidence

| Priority | Work | Type | What it resolves |
| --- | --- | --- | --- |
| 1 | Publish and freshly verify the additive numerical archive; supply exact artifact/module/run references in the paper | Release plus writing | Actual reader access to the revised central analyses |
| 2 | Repair page 34, improve Figure 3 labels, and sharpen the first explanation of Table 9 | Writing/layout | Avoidable effort in reading an already long manuscript |
| 3 | Maintain all post-result, repeat-independence and fixed-panel qualifications when condensing the paper | Writing, no new results | Prevents stronger claims from emerging during presentation cleanup |
| 4 | If broader inference is a future objective, freeze new scenes and a fixed repeat-generation target before collection; address independent reference capture separately | New scientific study, optional for current scope | Generalization and capture explanations that retained-vector replay cannot settle |

**Confidence:** High in the finite-statistic and map implementation assessment because of explicit formula checks and complete manuscript reading; moderate in broader artistic interpretation and novelty magnitude; no claim of acquisition authentication. Implementation involvement limits review independence. The remaining substantive constraints are not automatically solved by repeated review, publication of another archive, or adding more sensitivity counts.
