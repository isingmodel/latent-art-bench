# TMLR review — methods reviewer

**Submission:** "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation" (anonymous)
**PDF read:** `reports/tmlr_review_v1/round_06/input/manuscript.pdf`, SHA-256 `4ae5600ec39d49e52f30a105432d92b809d117d71d0c3e8627ccd6405209a242` (32 pages, main text and all appendices read; figures and tables checked as rendered)

## Summary of the submission

The paper asks what artist-style "proximity" measures when the prompted painters are related. It does this with a controlled prompt design: 14 fixed outdoor scenes × 6 clauses (none, generic "oil painting", and the generic clause plus "in the style of" Monet, Sisley, Pissarro or Cézanne) × 2 separately requested repeats, for 6 commercial text-to-image configurations (1,008 images). Images are measured in 31 interpretable colour, spatial and texture features (primary, prespecified) and in CLIP ViT-L/14 and CSD embeddings (added later). Reference targets are 649 Wikimedia reproductions of the four painters.

Methodological contributions:
1. **A split of what the names add beyond the generic clause.** The change divides into a shared change (N) and between-name differences (B). Squared sizes are estimated from cross-repeat products, which removes the noise bias. Two reference benchmarks go with it: a faithful imitator, N\*/(N\*+H), and an exact-differences generator, N/(N+H).
2. **An exact identity (Eq. 4) for any proximity gain linear in the image embedding.** It splits the gain into a label-permutation-invariant shared term (ḡ−g_g)ᵀμ̄ and a painter-specific term Hβ/4.
3. **Agreement readouts for the between-name differences.** These are the aligned amplitude β, the relative size Q, the alignment ratio β/√Q and the error D = 1 − 2β + Q. D is split along and off the reference pattern, into D_agg + V_scene, and after a held-out rescaling (D_held).

Main empirical findings:
- **Shared fraction.** It is 66.7–88.4% in the features, below a faithful imitator's 84.8–95.2%. Even exact painter differences would leave 57.6–84.2% shared.
- **Proximity gain.** The shared term supplies 54.2–83.8% of it in the embeddings and tracks the gain across configurations (r = 0.96 CLIP, 0.95 CSD).
- **Direction of the differences.** All configurations align positively, and GPT Image 2 has the highest alignment ratio in all three representations.
- **Error D.** It ranks the configurations differently in each representation.
- **Recognition.** It tracks the alignment ratio.

A 21-comparison family (six β, 15 pairwise D differences) was fixed before collection. Everything else is declared descriptive and retrospective.

## Strengths

1. **The central argument is correct and useful.** Eq. 4 is an exact identity (I re-derived it and reproduced every Table 2/3 entry from the raw embeddings). The exact-differences benchmark neatly removes the generated-vs-photographed domain gap from the comparison. Evaluators who report CSD/CLIP prototype similarity, or gains in it, should see this.
2. **Estimators are sound and clearly specified.**
   - The cross-repeat products are the standard unbiased (crossnobis-style) squared-norm estimator.
   - The exchangeable-null value 1/4, the finite-sample bias of H, (3/4)Σ tr(Σ_a)/n_a, the identity D = 1 − 2β + Q, the exact along/off-pattern split and D = D_agg + V_scene all check out algebraically.
   - The genuine-painting control is designed correctly: with distinct works drawn without replacement from a random half, the pseudo-repeat cross-products are unbiased for the true painter mean, so its expectation is the target noise alone, as the paper states.
3. **Numbers are exactly reproducible from the raw data.**
   - Starting from the per-image features, scaler and reference features, I independently reproduced every point estimate in Tables 1, 4, 11, 12, 13 and 14.
   - Starting from the raw embeddings, I reproduced Tables 2, 3 and 5.
   - The resampled Table 1 interval and "obs.<faithful" share also reproduce exactly with the registered seed (details below).
   - `build_assets.py --check` passes (29 generated files, 180 registered claims).
4. **Unusually candid about inference and design threats.**
   - Repeat dependence is quantified as ρ thresholds at which verdicts flip, and I verified them.
   - Scene-level intervals are explicitly limited to the 14 authored scenes.
   - The paper discloses the weak Monet–Sisley separability of the features, CSD's training on these painters' tags, the AI-performed audits, the aborted first collection, and the with-replacement flaw in an earlier genuine-painting control.
5. **Sensitivity coverage is broad.** It includes scene deletion, square windows, content-matched targets, alternative weightings, cropped sources, corrected H, the development panel as target, and normalized prototypes.

## Weaknesses (with locations)

**W1. The abstract's headline ranking departs from the protocol's ranking rule, and the paper does not say so.** (Abstract; §1 bullet 3; §4.5, p. 7; §5.3 "Direction", p. 10)
- The pre-collection protocol (`studies/painter_specificity_v1/PROTOCOL.md`, retained unchanged by v2) says: *"Rank models only on D … No universal quality winner follows from a single feature target."*
- The abstract and introduction instead lead with a ranking by the alignment ratio β/√Q ("GPT Image 2 aligns best in all three representations"). That readout was introduced after collection, once the D rankings had turned out to differ across representations.
- §4.5 says the later analyses were "each fixed before its outcomes were computed but on images whose other results were known". For this headline, the protection is nominal.
  - β/√Q is a deterministic function of β and Q, which were already reported.
  - `studies/painter_tmlr_diagnostics_v5/PLAN.md` records that the alignment ratios had already been recorded, and that the 99.7%/100% "best" shares and the Spearman 0.94/0.89 had been computed (by earlier reviewers) before that plan "fixed" them.
- The claim itself is descriptively accurate (I reproduced it), but readers need to know that it replaces the protocol's ranking criterion and was chosen with its outcome known.
- **This is an editing fix, not a request for new evidence.**

**W2. Factual error: sign of the drift diagnostic.** (Appendix A, "Repeat dependence", p. 18)
- The text reads: "predicts those differences worse than no drift in every configuration (−3.4 to −0.7% change in squared prediction error relative to zero)".
- The source (`reports/painter_request_timing_v1/REPORT.md`) defines *predictive gain* = (MSE_zero − MSE_held)/MSE_zero, with values −3.38% to −0.72%.
- So the held-out squared error was 0.7–3.4% *higher* than zero prediction. As worded, the parenthetical says the error fell, which contradicts the sentence it supports.
- The claim registry (`claims.json`, key `drift_gain`) checks the string, not its meaning, so the replay check cannot catch this.

**W3. The alignment ratio is described as "direction only / regardless of size", but it also counts scene-to-scene variation as misalignment.** (§4.3; Table 4 caption; Table 8; §5.4)
- Because Q = B/H + V_scene, a generator whose differences equal κ·r_a on average but vary by scene has β/√Q < 1. The ratio is invariant to scale, but not purely a measure of pooled direction.
- I computed the scene-averaged version β/√(B/H):

  | Representation | GPT Image 1 | GPT Image 2 | Flare | Sunburst | Nano Banana 2 | FLUX.2 Max |
  |---|---|---|---|---|---|---|
  | 31 features | 0.645 | 0.699 | 0.542 | 0.585 | 0.568 | 0.561 |
  | CLIP | 0.658 | 0.711 | 0.619 | 0.656 | 0.584 | 0.534 |
  | CSD | 0.715 | 0.782 | 0.705 | 0.708 | 0.562 | 0.664 |

- GPT Image 2 stays best everywhere, and the Spearman correlations with recognition are unchanged (0.94, 0.89). So the headline survives.
- Nano Banana 2, however, moves from last to third in the features, where V_scene is 39% of its Q. The mechanism offered in §5.4 ("readouts disagree where they weigh size differently") is right about scale, but the "direction" wording should acknowledge the scene-consistency component.

**W4. D_held is presented as corroboration but is nearly the same statistic as the alignment ratio.** (§5.3 "Direction", p. 10: "it also has the lowest error after a held-out rescaling in each")
- The paper itself notes that optimal rescaling gives D = 1 − β²/Q. The recomputed D_held values are within 0.03 of 1 − (β/√Q)²; for example, GPT Image 2 gives 0.551 against 0.554.
- D_held therefore guards against overfitting κ but is not independent evidence.

**W5. The unqualified "D > 1" claim for GPT Image 1 in the introduction.** (§1 bullet 3)
- The introduction lists GPT Image 1 with Flare and Sunburst as erring "more than a generator making no painter distinctions".
- §5.3 correctly qualifies this: the claim rests on an unadjusted interval, the Bonferroni-over-six interval [0.935, 2.210] includes 1, and it would reverse at a repeat correlation of 0.22. The introduction should carry the same qualification, or restrict the statement to Flare and Sunburst, whose Bonferroni-over-six intervals exclude 1.

**W6. Some wording is broader than the evidence.**
- (a) §5.3, p. 11: "Content does not explain the difference". The evidence is that title-derived content-class targets on 11 scenes change embedding D by ≤ 0.037. The sentence should say that.
- (b) §5.4 and §1: the Spearman values 0.94/0.89/0.60–0.77 are over six configurations, where one adjacent swap moves ρ by 0.057. State n = 6 in the text, or give resampling intervals.
- (c) Appendix A: "Two observations argue that the six requested configurations reached different generators." Cost differences and between-configuration distances show that the output distributions differ, not that the checkpoints differ (the same model served with different settings would pass). §3's "labels denote the requested configurations" is the right register.
- (d) §6: "a shared term larger than a quarter of the painter spread will dominate the proximity gain unless the model exaggerates the reference differences (β > 1)". The exact condition is β < 4S/H. With S > H/4, β ≤ 1 is sufficient for dominance, but β > 1 is not sufficient to overturn it.

**W7. Minor reporting and reproducibility gaps.**
- (a) `confirmation_features.jsonl` has 653 eligible works, of which 4 failed extraction (2 Monet, 1 Pissarro, 1 Cézanne); the 649 is after this exclusion. It is not mentioned in §3 or Appendix A.
- (b) The generated images are not in the supplement (disclosed), so the features cannot be re-extracted. The authors should commit to depositing them upon de-anonymisation.
- (c) Table 3 recognition accuracies (112 images each) have no uncertainty. Table 21 gives only "best" shares, while the text compares, for example, 68.8% with 60.7%.

**W8. Clarity.** The paper is correct but very dense.
- §§5.3–5.5 put five to ten numbers in many sentences and use about 12 estimands (N, B, H, N\*, λ, β, Q, β/√Q, D, D_agg, V_scene, D_held).
- Table 8 and the §4 roadmap help. Moving secondary ranges into tables, and stating early that the comparison with the exact-differences benchmark reduces to B/H versus 1, would help readers.
- This is not a barrier for the intended audience.

## Requested changes

**Critical** (both are editing-only; no new experiments are needed)
1. **Disclose the protocol's ranking rule and the status of the direction-only headline.**
   - Where: §4.5, and briefly in the abstract/§1.
   - State that the pre-collection protocol designated D as the only ranking criterion.
   - State that the alignment-ratio ranking featured in the abstract was adopted after collection, when D's rankings proved representation-dependent.
   - State that its values (and the resampled "best" shares and recognition correlations) were known before the plan that fixed them.
   - Replace "each fixed before its outcomes were computed" with wording that does not imply protection for these quantities.
2. **Correct the sign error in Appendix A's drift diagnostic.**
   - Write either "+0.7 to +3.4% change in squared prediction error" or "predictive gain of −3.4 to −0.7%".
   - Update the `drift_gain` registry entry to match.

**Minor**
1. Define the alignment ratio as the alignment of the *scene-wise* differences with the pooled pattern. Note that it treats scene-specific variation as misalignment. Report the scene-averaged β/√(B/H) alongside it; in these data it leaves the headline unchanged.
2. In §5.3, say that D_held ≈ 1 − (β/√Q)², so its agreement with the alignment ratio is expected rather than independent confirmation.
3. In §1 bullet 3, qualify GPT Image 1's D > 1 as §5.3 does (unadjusted; Bonferroni-over-six interval includes 1; ρ = 0.22).
4. Narrow "Content does not explain the difference" to title-derived content-class targets.
5. Give n = 6 wherever the Spearman correlations appear (§1, §5.3, §5.4), and preferably resampling intervals.
6. In Appendix A, temper "reached different generators" to "produced distinguishable outputs".
7. Rephrase the §6 condition "unless … (β > 1)" as β < 4S/H, or say that β ≤ 1 suffices.
8. Report the 4 eligible reference works that failed feature extraction.
9. Add scene-resampling or binomial intervals to the recognition accuracies in Table 3.
10. Commit to depositing the 1,008 generated images, so that features can be re-extracted from pixels.
11. Reduce number density in §§5.3–5.5; move secondary ranges to the appendix tables that already hold them.
12. (Supplement) Have the claim registry record the sign or units of each registered value, so that the replay check can catch errors like W2.

## Criterion 1 — Claims and evidence: **yes**

- Every central claim is supported by accurate evidence:
  - the shared fraction and its benchmarks;
  - the exact proximity identity and its shares;
  - the shared term driving between-configuration gain differences (stated as descriptive);
  - positive alignment for all configurations;
  - GPT Image 2's best direction-only agreement;
  - D's representation-dependent rankings;
  - the recognition–alignment association.
- I reproduced these numbers from the raw per-image features and embeddings, not only from the analysis JSONs.
- Claims are appropriately scoped: four related painters, one template, 14 authored scenes, no perceptual validation, and inference conditional on independent repeats.
- The gaps I found are all correctable by editing, and none changes a conclusion: the undisclosed protocol ranking rule (W1), a sign error in a peripheral diagnostic (W2), and several wording overreaches (W3–W6).

## Criterion 2 — Audience and clarity: **yes**

- The work concerns how artist-style imitation is evaluated in text-to-image models. That is directly relevant to TMLR readers working on generative-model evaluation, style mimicry, and protection or erasure benchmarks.
- The central distinction (shared change vs between-name differences; proximity vs specificity) is clearly motivated by Figure 1 and Eq. 4.
- The benchmarks make the results interpretable. The recommendations in §6 are actionable.
- The density noted in W8 is a readability cost, not a failure to communicate.

## Desk-rejection risk: **none**

The submission is on-topic, uses the TMLR template, and is anonymised. The main text is about 13.5 pages, so it would go in the long-submission track, which is not a rejection ground. It is written with evident care and internal consistency; it does not read as low-care machine-generated text. AI assistance is disclosed.

## Recommendation: **minor revision**

## Confidence: **4 / 5**

I independently reproduced the core estimators and many secondary quantities from raw data. I did not re-run every sensitivity analysis (cropped sources, SD-Turbo, content-matched embedding targets, joint scene × reference resampling).

## Numbers verified and how

All recomputations use my own scripts, written from the definitions in §4 and Appendix C. Inputs were read directly from:
- `data/manifests/painter_specificity_v2/psv2-20260911/{requests,measurements}.jsonl`;
- `data/manifests/painter_feature_generation_v2/pfg2-method-20260905/{scaler.json,confirmation_features.jsonl,development_features.jsonl}`;
- `reports/painter_learned_audit_v1/{inputs.json,embeddings_clip.npz,embeddings_csd.npz}`.

My scripts did not use the project's analysis code.

1. **Replay check.** `uv run --locked python paper/tmlr/build_assets.py --check` returns "ok: 29 generated files and 180 claims".
2. **Reference and development counts.** Reference: 297/106/141/105 = 649 measured, plus 4 failed (not reported). Development: 221 (101/36/48/36).
3. **Generated images.** 1,008 measured images, all 1024×1024, with 1,008 distinct hashes.
4. **Reference spread.** H = 5.915 in the 31 features. Its finite-sample bias, (3/4)Σ tr(S_a)/n_a, is 6.75% of H (paper: 6.7%).
5. **Table 1, all six rows exact.** Shared fraction 71.3/70.9/71.1/66.7/69.1/88.4%; N/H; B/H; faithful 95.2/89.3/84.8/86.9/92.5/90.4%; exact-differences 84.0/83.3/83.3/79.9/57.6/84.2%.
6. **Table 1 resampling for FLUX.2 Max.** Scene-bootstrap interval [76.8, 94.2] and obs.<faithful 84.1%, reproduced exactly with the registered seed 20261002. Other seeds give 85.2–85.5%. The other five configurations are at 100% below faithful.
7. **Table 4 point estimates.** β, Q, β/√Q and D exactly, with D = 1 − 2β + Q verified numerically.
8. **Table 4 and Table 23 intervals.**
   - β simultaneous intervals (t₁₃ at 1 − 0.05/42), e.g. GPT Image 1 [0.709, 1.168].
   - Nominal β intervals, e.g. [0.806, 1.070].
   - Nominal D intervals, e.g. GPT Image 1 [1.129, 2.016].
   - GPT Image 1's Bonferroni-over-six D interval [0.935, 2.210].
9. **Table 13.** All 15 pairwise D differences with simultaneous and nominal intervals, exact; Flare−FLUX [0.256, 1.618] and Sunburst−FLUX [0.058, 1.623] are the two resolved.
10. **Table 11.** λ = 44.1/50.7/54.3/55.6/24.8/64.6% and corrected cos(c, t) = 0.85/0.66/0.57/0.72/0.75/0.86.
11. **Table 14.**
    - D_agg 1.239/1.044/1.483/1.337/0.723/0.761, giving V_scene = D − D_agg.
    - D_held (κ = max(0, β/Q) fitted on 13 scenes) 0.645/0.554/0.741/0.706/0.832/0.714.
12. **Table 12 centroid proximity.** Exact via Eq. 6 and by direct computation, e.g. GPT Image 1: 17.490 = 17.844 − 0.354.
13. **Reference components.** Singular-component shares 66.3/20.6/13.0% (Table 16 caption).
14. **Feature separability.** Nearest-reference-mean accuracy on the development panel: 49.8% macro, Monet 39.6%, Sisley 30.6%.
15. **Tables 2, 3 and 5 from raw embeddings (CLIP and CSD).** Exact: total, shared and painter-specific gain; shared %, faithful % and exact-differences %; β, Q, β/√Q and D; recognition macro accuracy (60.7, 68.8, 59.8, 58.9, 51.8, 41.1 in CLIP; 72.3, 75.9, 62.5, 61.6, 50.9, 39.3 in CSD).
16. **Correlations across configurations.** Gain vs shared term 0.960 (CLIP) and 0.949 (CSD); gain vs painter-specific term −0.646 (CSD). Variance ratio shared/specific 10.8 ("11") and 5.82. The CLIP gain ranking equals the shared-term ranking.
17. **Spearman correlations (by hand).** Recognition vs alignment ratio 0.943 (CLIP) and 0.886 (CSD). Alignment ratio across representations 0.600–0.771. D across representations −0.143 to 0.657.
18. **Table 21 "best" shares (own scene bootstrap).** Alignment ratio, 31 features: GPT Image 2 97.9% (paper 98.0%). D, 31 features: FLUX.2 Max 85.0% (paper 84.7%).
19. **ρ thresholds.** Using bias = ρ/(1−ρ)·(repeat noise) with the Table 23 noise values: GPT Image 1 0.22, GPT Image 2 0.19, Flare 0.64, Sunburst 0.52, Nano Banana 2 0.04; Nano Banana 2 and FLUX.2 Max adjusted D reach 0 at 0.30 and 0.32.
20. **Genuine-painting controls (`painter_tmlr_diagnostics_v3/analysis.json`).** Table 15 means and ranges; 5.1/9.1/6.6% of splits above 1 in the features; 0% in CLIP and CSD.
21. **Table 26 arithmetic.** Mean changes +2.7 (CLIP shift), +10.0 (CSD shift) and +16.1 (CLIP generated-prototype rule); shift ranges −5.4…+12.5 (CLIP) and +0.9…+26.8 (CSD).
22. **Tables 22 and 25.** Cézanne's share is least shared in 11 of 12 configuration–encoder pairs, minimum 34.6%; reference-setting changes ≤ 1.6 points; normalized-prototype changes ≤ 0.5 points.
23. **Configuration distinctness.** Flare vs Sunburst are farther apart than repeats in 91.7% of cells in CLIP (`painter_tmlr_diagnostics_v5`).
24. **Drift diagnostic.** Held-out predictive gains −0.86, −3.38, −2.28, −2.62, −0.72 and −1.19% (`painter_request_timing_v1`). This is where I found the W2 sign error. Per-configuration median repeat gaps are 2.9–3.3 minutes, with a maximum of 20.0 minutes.
25. **Algebra.**
    - Eq. 4, via ḡ + d_a and μ̄ + r_a with Σd_a = Σr_a = 0.
    - Exchangeable null E[N]/(E[N]+E[B]) = 1/4.
    - Finite-sample bias of H = (3/4)Σ tr(Σ_a)/n_a, with the centroid contributing one third to N\*.
    - The D split (s₁−1)(s₂−1) + ⟨o₁,o₂⟩/H.
    - Unbiasedness of the distinct-works genuine control.
    - The protocol checks: the 21-comparison family (six β, 15 D differences, Bonferroni over 21 via t at 1 − 0.05/42) matches `studies/painter_specificity_v1/PROTOCOL.md`, as retained by v2; the reduction from 16 to 14 scenes matches `studies/painter_specificity_v2/`.
