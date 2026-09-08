# Round 2 scored review — statistical and experimental validity

Reviewer: maintainer-run LLM subagent conducting an internal skeptical review. This is not independent human peer review or institutional validation. I did not read the other reviewers' reports or coordinate scores.

Baseline Git commit remains `f0fe89a9179377b0a91630b775bcf7163853e66b`; this review evaluates the revised working-tree manuscript, not the manuscript committed at that baseline.

- TeX SHA-256: `2d28cec5b0bf7e62cb8e76338b4c3b52809c63c0ab6e8bb9aba4dced9a931a52`
- PDF SHA-256: `48bb8772bd0bf8da48c621de1610ce8e7a29690c5aeeb9b6e330c803daf87666`
- Review date: 2026-09-09. All manuscript line references below use this TeX snapshot.

## Scores

Identical equal-weight rubric and anchors: 5 = substantial unresolved defects; 7 = sound but substantial revision needed; 8 = strong with limited revisions; 9 = publication-ready as a carefully scoped empirical paper; 10 = exceptional.

| Aspect | Score / 10 | Assessment of the revised whole paper |
| --- | ---: | --- |
| 1. Research question and contribution | 8.5 | The controlled conjunction of proximity, joint alignment, matched-reference occupancy and repeated-prompt behavior is now explicit. This is a useful empirical contribution, though deliberately narrow rather than a new general evaluation principle. |
| 2. Study design and controls | 8.5 | The full controls now visible in the paper materially strengthen the design: identical artist-free payloads, own/cross-painter contrasts at equal class masses, disjoint real-query controls, and shared free/generic factorial controls. A single generic clause, selected panels and one short Study 2 service run still limit the scientific reach. |
| 3. Statistical validity | 9.0 | Primary inference is correctly formulated and calibrated to the stated target. Effective df, shared-control covariance, proxy simulation scope, multiplicity and unresolved effect sizes are now assessable. No result-changing statistical or numerical defect found. |
| 4. Evidence and robustness | 8.5 | Matched real-query occupancy with k sensitivity and energy-term accounting add concrete evidence beyond general caveats. Contrary alignments, processing reversals and retrieval declines are visible. Independent capture/representation and scene/service replication remain absent. |
| 5. Interpretation and claim calibration | 9.0 | The manuscript now consistently distinguishes realized retrieval, a particular generic clause, model-based interaction uncertainty, joint rather than six individual painter matches, and computational rather than perceptual conclusions. |
| 6. Literature and positioning | 8.5 | Direct distributional-style precedent and the added contrast with corpus-level studies make the incremental contribution substantially clearer. Positioning is sound for a scoped computational paper; it is not an exhaustive review of style evaluation. |
| 7. Reproducibility and transparency | 8.5 | The prospective/descriptive/post-result map is corrected and local-versus-public access is honest. External archival release and reviewer access to the necessary artifacts are still pending, so this aspect is not yet fully publication-ready. |
| 8. Structure, writing and figures | 8.5 | Study-specific methods/results and the revised interaction figure are easier to follow. The evidence hierarchy and appendix placement work. Some duplicated panel/collection prose and two small terminology issues remain. |

**Arithmetic mean: 69.0 / 8 = 8.625 / 10.**

The revised scientific argument is suitable for a narrowly scoped empirical submission after limited copyediting and release preparation. I do **not** recommend another primary analysis, more significance tests or new collection merely to improve a score. The changes in design/evidence scores reflect controls and comparisons now actually presented, not an increased count of limitation statements. Scores below 9 do not mean that broadening the scientific question is required for this manuscript.

## Review and verification scope

I read `docs/STATUS.md`, then `docs/ARTIFACTS.md`, inspected Git status, verified both manuscript hashes and read the complete revised TeX and bibliography. The working tree contained the coordinator's manuscript, figure and bibliography edits; I preserved them. This remains editorial work on completed versioned studies.

I checked the newly foregrounded quantities against the retained revision tables and implementation: `metric_cells.csv`, `specificity_matrices.csv`, `specificity_interactions.csv`, `heldout_real_controls.csv`, and the held-out coverage construction in `painter_distribution_revision_v1/diagnostics.py`. I retained the previous review's checks of Study 1's swap identity and Study 2's block estimator and independently reran the smallest relevant tests: **18 passed in 0.71 seconds**. I did not rerun the full suite or evidence audit, edit scientific sources, extract features or collect images.

Using the PDF-review workflow, I inspected the existing round-2 rendered pages 3, 6, 7, 9, 10, 11, 15 and 16. These include the design map, primary result table/figure, alignment result, retrieval figure, interaction methods and revised figure, calibration table and coverage table. I found no clipping or omitted scene estimates on these pages. This was targeted visual inspection, not a claim of inspecting all 20 pages afresh.

For the new literature connection, the primary [Deliège et al. article](https://pmc.ncbi.nlm.nih.gov/articles/PMC12734345/) supports the stated comparison through three experts, five movements, ten painters, and relative shift/dispersion/overlap. That precedent makes the manuscript's experimental contrast clearer; it should not be described as absent from earlier work. The revised text appropriately does not do so.

## Substantive resolution of Round 1 issues

1. **Contribution and generalization are now explicit.** Lines 65–90 and 637–673 identify the empirical conjunction rather than claiming discovery of the general variance/retrieval distinction. Lines 316–320 explain overlapping training sets and the invariance to translation and positive rescaling. Lines 484–486 restrict the FLUX/Monet counterexample to the realized feature comparison. Lines 589–590 and 656–664 consistently identify the tested generic sentence and deny mediation between the studies. These repair the earlier claim-calibration concern.

2. **Study 2 uncertainty is now visible and scientifically interpretable.** Lines 597–603 report the effective df/SE and explain the size of effects still admitted by Monet's interval. The scene estimates in Figure 4 expose the difference between Monet's consistently negative scene means and Cézanne's mixed signs without converting the points into a new sign test. Appendix C reports the correct covariance/df formulas, approximate coverage, independent proxy noise and Monte Carlo intervals. These changes make the model-based inference defensible for the fixed-scene target; they do not pretend that dispatch randomization validates independence. The nonsignificant result is not evidence of equivalence, and the revised paper says so clearly.

3. **The evidence hierarchy is corrected.** The design table and lines 270–276 distinguish prospective descriptive analyses from the later alignment double contrast, matched-real coverage, decomposition, retrieval and cross-service diagnostics. The earlier incorrect blanket classification of detection/coverage as post-result is removed. The stronger pre-generation timing is now accurately distinguished from earlier painter selection after exploration.

4. **The distributional gap now has a substantive finite-panel comparator.** The retained matched-real occupancy analysis uses the same anchors, identical query class counts, disjoint real queries and common radii. The k=1/3/5 sensitivity exposes saturation rather than presenting one threshold as a universal answer. This does not identify the source of the gap, but it is a meaningful descriptive reference comparison beyond observing that two continuous empirical distributions differ.

## Numerical and inferential findings

- **No actual numerical error found in the checked revised claims.** The FLUX/Monet energy terms at 377–383 match the saved values: cross term 15.8313785 to 12.4212084 and generated-within term 6.9057794 to 4.1202559. Their signs are interpreted correctly: lower within-generated distance, being subtracted, opposes the measured energy decrease. This avoids a mechanistic misreading of energy/spread dependence.
- The NB2/Monet equal-class energies at 393–394 match `specificity_matrices.csv`: 3.68716595 to its own panel and 3.48839325 to Cézanne. The exception matters and is correctly retained beside the joint alignment result.
- Every named median in the k=1/3/5 coverage table matches `heldout_real_controls.csv`, including FLUX/Cézanne saturation at 1.000. The disjoint split sizes and class counts in 908–915 agree with `heldout_design` and `heldout_coverage`. The text correctly avoids interpreting the repeated split ranges as population confidence intervals.
- The primary interaction estimates, intervals, Holm values, df and SE remain consistent with the previously independently reconstructed block calculation. Bonferroni family intervals and Holm tests are distinct valid choices; they need not use identical rejection boundaries. Shared controls are retained in the covariance. Fixed-scene mean heterogeneity is correctly excluded from the repeated-generation variance target.
- The prospective simulation table matches the retained global-null rows and Wilson Monte Carlo intervals. Neither those simulations nor the tests validate the live service's error assumptions, and the manuscript explicitly preserves that boundary.

## Remaining actionable issues

These are limited revisions; none requires altering the primary results.

1. **Describe simulation heterogeneity as multipliers, not absolute standard deviations.** At 867–869, “varied scene standard deviations from .7 to 1.8” can imply absolute chroma-IQR standard deviations. The implementation multiplies arm-specific baseline noise by scene factors ranging from .7 to 1.8, then applies the polarity and arm factors. Change this to “used scene standard-deviation multipliers from .7 to 1.8.” This is a precision-of-methods issue, not a defect in Table 5's numbers.

2. **Use “approximate” in the abstract's Study 2 interval label.** Lines 40–42 give “simultaneous 95% intervals” without the adjective supplied correctly in methods and the figure caption. “Approximate simultaneous 95% intervals” preserves the important inferential qualification for abstract-only readers.

3. **Resolve external artifact access before claiming a publication-ready reproducible package.** Lines 712–725 and Appendix F correctly disclose the pending release and unavailable raw-media access. That disclosure fixes overstatement; it does not give a reviewer the local snapshot. The release path should provide a persistent numeric/code snapshot and a tested way to recompute the numerical findings from the supplied vectors. If raw responses remain inaccessible, keep a distinct statement that transport-integrity checks and image remeasurement are not externally reproducible. This is release preparation, not a request to change frozen evidence, publish private material without authorization, or collect more data.

4. **Optional compression.** Appendix A repeats much of the panel and collection account already in 164–191 nearly verbatim. Retain the extra delivery, missingness and prompt details there, but a brief cross-reference can replace duplicated general panel prose. This would improve the 20-page document without reducing scientific transparency.

## Remaining scientific limits and necessary path

The single generic sentence is an active wording comparator, and the six fixed scenes are the target of the current interaction estimate. I am not treating absent human ratings as an automatic defect for those explicitly computational endpoints. Similarly, descriptive alignment and neighborhood occupancy need not be promoted into extra hypothesis tests to become useful evidence.

What remains unavailable is stronger validation of the measured gap as an artistic/style phenomenon, separation from fine content or capture/rendering differences, and transfer of the interaction to new wording, scenes or services. Those would need new controls or data in a prospective successor namespace. More caveats, another encoding, a post-result significance test or a larger number of reused-view summaries would not supply that evidence.

The smallest defensible path is therefore: make the two terminology edits, prepare a reviewable external numeric/code snapshot when publication is authorized, optionally compress duplicated prose, and inspect the final PDF. No result-changing statistical blocker was identified in this round, and no new scientific collection is required for the present scoped paper.
