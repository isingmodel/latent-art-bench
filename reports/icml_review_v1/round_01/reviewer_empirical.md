# Independent empirical review — round 01

**Inspected PDF SHA-256:** `4ee2a3004226bbcd0151ca310265efad851b69e431d1e05895701b8f918a3e85`

**Recommendation: 4 / 10 — marginally below acceptance.**  
**Soundness:** 3/4 · **Presentation:** 3/4 · **Contribution:** 2/4 · **Confidence:** 4/5

## Summary

The paper audits six requested image-generation configurations using 14 fixed scenes, six prompt arms, two repeats, and 31 hand-engineered digital-image measurements. It compares centered generated painter means with centered means of 649 reproductions of four painters. Independent-repeat cross-products separate expected systematic discrepancy from repeat noise. The main observations are a dominant common named-prompt shift, positive aggregate reference alignment alongside appreciable mismatch, uneven painter-pair agreement, and changed point-estimate orderings after scene averaging or scalar calibration. The paper carefully limits its target to the finite digital collection.

## Strengths

- **S1.** The factorial common-scene design, generic-painting control, complete 1,008-output census, separate development scaling, and equal painter weighting support a clean conditional comparison. The repeated-output estimator addresses a real problem: output variability should not automatically count as systematic painter-contrast error. (Sections 3-4; Appendices A-B.)
- **S2.** The distinction between aligned response and total mismatch is concrete and empirically illustrated: GPT Image 2 has beta approximately 1 but D=1.226, whereas FLUX has beta=.470 and D=.801. Pairwise diagnostics and the omission of Cezanne expose information hidden by an aggregate response. This is a useful evaluation lesson even without a novel estimator. (Sections 5.1 and 5.3; Tables 1 and 9; Figure 2.)
- **S3.** The manuscript reports uncertainty limits and contrary evidence unusually carefully: only two of 15 original paired comparisons resolve, none establishes D<1, crop correction changes resolved comparisons, calibration is a feature-space counterfactual, overlapping folds are not independent replications, and a prospective supporting intervention contradicts an earlier ordering. The genuine-painting controls and reference/metric sensitivities are valuable. (Sections 4.3-5.5; Appendices C and F.)
- **S4.** Numerical reproducibility is strong. In this review all four primary replay variants, both retrospective diagnostic replays, reference-quality replay, and all 38 focused tests passed. The inspected estimator implementation agrees with the stated centering and cross-product equations. These checks support the retained-vector computation, not the correctness of pixel extraction or hidden service identity. (Reproducibility; Appendix I; Inspected scientific implementation.)

## Weaknesses

### W1: Contribution and construct relevance

**Locations:** Sections 3.1, 3.3, 4.2, and 6.1; Appendix C.1, Tables 6-7.

The precise finite-panel claim is credible, but its scientific importance is still limited. The target combines painter, subject, reproduction, and feature-weighting effects; every scene is asked to match the same pooled historical contrast. The paper acknowledges that genuine scene-dependent painter behavior can increase its error. The real-painting controls show substantial target mismatch even for authentic held-out works, and do not establish which differences matter for an evaluation user. Thus the current evidence establishes conditional behavior in one low-dimensional digital target, rather than a validated capability ordering or a demonstrated evaluation failure that transfers beyond it. This is principally a contribution limitation, not a charge that the finite-panel calculations are invalid. A second independent target or an external validation of the practical relevance of the measured distinctions would add more than further caveats.

### W2: Empirical precision and stability

**Locations:** Section 4.3; Sections 5.2-5.4; Figure 2 and Table 3; Appendix C.4.

Several of the most interesting claims are descriptive point estimates with little direct uncertainty characterization. In particular, weak/reversed Monet-Sisley alignment and the calibrated ordering have only two requests per cell and 14 fixed briefs behind them. The manuscript responsibly avoids significance claims, but the strength of these findings remains uncertain; source correction already changes several pair signs. The synthetic coverage experiments are useful conditional checks, yet cannot diagnose actual cross-request dependence, and their shared-state scenario demonstrates the potential severity. Existing-data influence and resampling summaries would help assess fragility; reliable fresh-request uncertainty and transfer require another appropriately designed collection.

### W3: Control interpretation

**Locations:** Abstract; Section 5.2; Table 2; Appendix B.

The headline 82.5-95.7% common fraction uses artist-free images as its baseline and therefore includes the large generic-painting change. This is disclosed, but it weakens the specificity of the most prominent empirical finding. The existing generic arm can directly quantify the common component of named-minus-generic change. My exploratory calculation from retained vectors gives 71.3%, 70.9%, 71.1%, 66.7%, 69.1%, and 88.4% in table model order. These values support a more informative statement about common additional naming effects. They should be independently verified, accompanied by appropriate stability summaries, and labeled retrospective; they are not new confirmatory findings.

### W4: Reproducibility

**Locations:** Reproducibility; Appendices G and I.1-I.3.

The compact artifact cannot yet independently reproduce the image measurements because the full exact-pixel cohort has no dedicated public archive or verified recovery route. This matters especially here: crop and scaling decisions change resolved comparisons, and all source corrections and visual classes are AI-coded without human verification. Requested configurations are documented rather than checkpoint-attested, which is an acceptable service-audit scope but limits model-specific attribution. Numerical replay is not a substitute for inspectable original pixels.

### W5: Separating mathematical identity from empirical finding

**Locations:** Introduction; Sections 4.2 and 5.4; Table 3; Appendices B.1 and C.2.

The scene-variation penalty and the possibility that shrinking large contrasts reduces squared error follow directly from the metric. The empirical ordering reversals are useful examples, but calibration changes measured feature contrasts and supplies no image-space intervention. With one artist panel and one clause template, these examples provide limited additional evidence for general evaluation practice. The paper should emphasize the empirical quantities that are not implied by the identities, and explain the concrete decision that its recommended collection of scores would support.

## Questions

1. How stable are the common named-minus-generic fraction and the Monet-Sisley aligned response under scene deletion, reference-target variation, and scene-level resampling? Please distinguish sensitivity summaries from new confirmatory tests.
2. Which specific practical evaluation decision is supported by the finite digital target? What evidence would distinguish a meaningful painter-label mismatch from historical content or digitization differences?
3. Can the retained original images, reproduction sources, crop decisions, and exact request/response manifests be made anonymously retrievable with hash verification? What portion currently has an independently verified recovery route?
4. Are repeat index, request time, or collection blocks associated with systematic contrast shifts? A diagnostic on the existing randomized request sequence would be useful, even though two repeats cannot establish service independence.

## Concrete revision priorities

1. **Existing-data analysis:** Add the named-minus-generic common/specific decomposition with clear denominators, retain the artist-free decomposition for context, and report scene-deletion or resampling stability for both. This is the most consequential attainable improvement to the central empirical finding.
2. **Existing-data analysis and presentation:** Show per-scene contributions and influence for the painter-pair and calibrated comparisons, including how the small Monet-Sisley reference distance affects interpretation. Keep all retrospective analyses outside the original test family and distinguish fixed-panel sensitivity from sampling uncertainty.
3. **Artifact and audit work:** Provide an anonymous exact-pixel archive or demonstrably complete recovery manifest for the evaluated cohort and document the audited regions. Independently validate a useful sample of the AI source/class decisions; archive work needs no new generated images, while validation does require new human annotations.
4. **New evidence:** Conduct one targeted prospective replication of the central common-effect/painter-pair findings with frozen estimands, a fresh collection batch, more within-cell repeats, and held-out scene wording or an independently assembled painter/reference panel. This would address evidential stability and contribution more directly than adding more retrospective metrics. Perceptual/expert validation is necessary only for an expanded claim about artistic resemblance, not for the current finite-feature claim.
5. **Editing:** Make the empirical contribution explicit separately from the exact score identities, and state the evaluation decision the scores are intended to inform. Editing can improve positioning but cannot establish generalization, service independence, or perceptual relevance.

## Limits requiring new evidence

- Fresh-request uncertainty and actual service dependence cannot be established with two requests per cell in one collection.
- Transfer to new prompt wording, painter groups, or independent reference collections is untested.
- Independent accuracy of AI crop/content judgments requires new validation annotations.
- Separating reproduction effects from painting properties requires additional source evidence, such as multiple captures; perceptual artistic fidelity requires a separately validated perceptual evaluation if that claim is desired.

## Score rationale

I recommend 4 (marginally below acceptance). This is a careful, numerically reproducible conditional audit with useful counterexamples to interpreting response strength as agreement. I do not require a new algorithm or a perceptual-fidelity claim. However, much of the evaluation lesson is supplied by established identities, while the distinctive empirical findings depend on one small, partially source-confounded painter target and sparse repeated sampling. The transparent limitations appropriately narrow the claims but do not by themselves supply the significance or independent validation needed for acceptance. A more direct analysis of the existing generic control would improve the paper substantially; stronger evidential scope requires new data or annotations.

- **Soundness:** The main computations and conditional claims are sound under stated independence assumptions; small-repeat inferential uncertainty and the unvalidated target limit empirical interpretation.
- **Presentation:** Clear explanations, informative visual examples, and unusually honest scope; the many metric variants somewhat dilute the empirical message.
- **Contribution:** A useful focused audit, but limited evidence that its empirical conclusions or practical utility extend beyond the selected digital panel.
- **Confidence:** High confidence in the conditional numerical and empirical assessment after the complete manuscript, implementation inspection, and replay; hidden service identity and independent pixel extraction were not verified.

## Ethics

No additional evidenced ethics concern. The manuscript reports historical public-domain metadata, avoids living-artist or human-participant claims, discloses AI assistance, and acknowledges that measurements do not establish authorization or authenticity.

## Inspection and reproducibility checks

- `make specificity-check` — Passed all four exact numerical replay variants.
- `make review-check reference-quality-check` — Passed both diagnostic versions, associated presentation verification, and reference-quality numerical replay.
- `uv run --locked pytest -q tests/painter_specificity_v1 tests/painter_specificity_v2 tests/painter_specificity_measurement_v1 tests/painter_specificity_review_v1 tests/painter_specificity_review_v2 tests/painter_reference_quality_v1` — 38 passed in 1.40 seconds.

Read the complete frozen manuscript and appendices, its adjacent TeX sources, the primary scientific loader/estimator code, and relevant retained-vector inputs. Visually inspected all five scientific figures and principal result tables. Exact-pixel feature re-extraction and hidden checkpoint identity were not independently verified.

Prepared independently without reading other reviewers or historical editorial scores. No manuscript files were modified.
