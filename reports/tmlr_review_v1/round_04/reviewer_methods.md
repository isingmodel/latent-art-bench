# TMLR review (methods): "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation"

Reviewer role: methods (statistics and estimators, whether the evidence supports each claim, whether reported numbers match the analysis outputs, reproducibility).

PDF read: `reports/tmlr_review_v1/round_04/input/manuscript.pdf`, 29 pages, SHA-256 `caa3b4299154a8926e29f7a7dee8d5c81784ff77477597931a0aab8d4d5ec617`.

## Summary of the submission

The paper asks what artist-style "proximity" measures when the prompted painters are closely related. Six commercial text-to-image configurations render 14 authored outdoor scenes under six clauses, twice each (1,008 images). The clauses are no painting instruction, a generic "oil painting" instruction, and that instruction "in the style of" Monet, Sisley, Pissarro or Cézanne. Images are measured in 31 hand-crafted colour, spatial and texture features (the prespecified primary representation) and in CLIP and CSD embeddings.

Averaging over the four names splits what they add beyond the generic clause into two parts: a shared change (N), and between-name differences (B). Squared sizes are estimated from products across the two repeats, which removes noise bias. The paper compares these with two benchmarks built from 649 reference reproductions: a "faithful imitator" and an "exact-differences" generator. In the embeddings, an exact linear identity (Eq. 4) splits the named-minus-generic gain in similarity to the painter's prototype into two terms: one that is invariant to how the names are assigned, and a painter-specific term Hβ/4.

Specificity is then read from agreement between generated and reference between-name differences. The paper reports an aligned amplitude β and a repeat-corrected error D, where D = 1 corresponds to making no painter distinctions. These are calibrated against genuine paintings sampled the same way. The inferential family fixed before collection covers only the six β values and the 15 pairwise differences in D (31 features, Bonferroni over 21). Everything else is retrospective, each piece under a written plan, and the paper discloses this.

**Main claims.**
1. 66.7–88.4% of the squared change the names add is shared. A faithful imitator would share even more (84.8–95.2%), and even exact painter differences would leave 57.6–84.2% shared.
2. In CLIP and CSD, the name-invariant term supplies 54.2–83.8% of the proximity gain, close to the faithful-imitation share.
3. Every configuration's between-name differences align with the reference differences in aggregate (β > 0). Their accuracy (D) depends on the representation: three configurations have D > 1 in the 31 features, none has D > 1 in CSD, and the 31 features separate genuine Monet and Sisley works poorly.
4. Proximity, recognition and agreement favour different configurations.
5. Texture features are less shared than colour features on average.

## Strengths

- **The central argument is an exact identity, and it is correct.** Eq. 4 (and Eq. 8) follows from Σ_a r_a = Σ_a d_a = 0. I recomputed it from the released embeddings for all 12 configuration–encoder pairs: shared plus painter-specific equals the gain to within 10⁻¹⁶. The thesis ("proximity gain is dominated by a name-invariant term for related painters") does not depend on any cross-repeat noise model, because the proximity decomposition is linear in the means. This makes the headline result robust to the main untestable assumption behind the other analyses (independent repeats).
- **The estimators are appropriate and correctly derived.** They include cross-repeat (cross-validated) inner products, the exchangeable-null value of 1/4, D = 1 − 2β + Q, D = D_agg + V_scene, the centroid-proximity split (Eq. 6), and the finite-sample bias of H, (3/4)Σ tr(Σ_a)/n_a. I checked each derivation and reproduced each numerically (see "Verification" below).
- **The numbers are exact.** From raw per-image features, I reproduced every point estimate I checked: Tables 1, 2, 3, 4, 5, 11, 12, 13, 14, 15 and 25, the Bonferroni-6 interval, and the development-panel accuracies. Bootstrap quantities agree within Monte Carlo error. `build_assets.py --check` passes (26 generated files, 141 registered claims).
- **The paper is candid about prespecification and multiplicity.** Section 4.5 separates the prespecified family from the retrospective analyses. The supplementary plans record which outcomes were known when each analysis was defined, and they match the protocol (`studies/painter_specificity_v2/PROTOCOL.md`, `studies/painter_specificity_v1/PROTOCOL.md`). Intervals are presented as describing 14 fixed authored scenes, not a scene population.
- **The benchmarks make the shared fraction interpretable.** Without them, a "66–88% shared" number would be read as a failure of specificity. The exact-differences benchmark removes the photo-versus-generated domain gap, which the faithful benchmark cannot.
- **Many sensitivity analyses, reported even when they cut against the paper.** These include feature families, reweightings, leave-one-feature-out, scene deletion, square windows, content-matched targets, source crops, a genuine-painting calibration (corrected to distinct works), repeat-correlation sensitivity, and a held-out rescaling that reverses the 31-feature ordering. The Monet–Sisley weakness of the 31 features is stated prominently.

## Weaknesses (with locations)

**W1. A factual misstatement in the genuine-painting calibration (p. 10, Section 5.3, paragraph "Genuine paintings calibrate these values").** The text says "In the embeddings no genuine split has an error above 0.53". The recorded outputs (`reports/painter_tmlr_diagnostics_v3/analysis.json`, `genuine_controls_distinct`) support only two statements:
- no genuine split in either embedding exceeds 1 (`above_one = 0` in all six embedding controls);
- the largest 97.5th percentile is 0.5315 (CLIP, class sampling, pooled target).

By definition, therefore, about 2.5% of those splits exceed 0.53. The registered claim `genuine_emb_upper` is derived in `build_assets.py` (≈ line 1743) as the maximum of the 95%-range upper bounds. The check script confirms the number, but not that the number is the quantity the sentence describes. The substantive point (embedding genuine splits never exceed 1, unlike 5.1–9.1% of 31-feature splits) is correct.

**W2. The headline "three configurations err more than a generator that makes no painter distinctions" (abstract p. 1; introduction bullet 3, p. 2; Discussion p. 13) is stated without the qualifications the paper's own analyses supply.**
- (a) **It depends on independent repeats.** From `reports/painter_repeat_covariance_v1/analysis.json`, GPT Image 1's D (1.572) falls below 1 once the repeats share about 22% of their noise power; at ρ = 0.25 its adjusted D is 0.898. Flare and Sunburst stay above 1 up to ρ ≈ 0.64 and ≈ 0.52. The Limitations section (p. 13) mentions only the Nano Banana 2 / FLUX.2 Max order swap at ρ = 0.251, not that a D > 1 verdict flips.
- (b) **For GPT Image 1 it is not resolved under multiplicity adjustment.** The Bonferroni-over-six interval the paper reports, [0.935, 2.210] (p. 10), includes 1.
- (c) **It is driven by magnitude, not direction.** Q = 2.28–2.45 against alignment ratios β/√Q of 0.511–0.600. GPT Image 1 (0.600) is better aligned in direction than FLUX.2 Max (0.546). The paper itself suggests that part of the excess size may be a scale difference between clean generated images and photographed paintings (p. 10).
- The companion statement "in CSD none does" rests on Nano Banana 2 at D = 0.999, scene interval [0.876, 1.128], below 1 in 51.3% of joint resamples. That is indistinguishable from 1.

The body text in Section 5.3 is careful. The abstract and introduction turn a descriptive point-estimate contrast into a categorical one.

**W3. The abstract's reasoning for the exact-differences benchmark mixes two benchmarks (p. 1, sentence beginning "That is expected even of good imitation").** The premise ("the four painters are close to one another relative to their distance from the generic outputs") is about ‖t‖² and supports the faithful benchmark. That distance includes the photo-versus-generated gap and content mismatch, as p. 6 acknowledges. The exact-differences result N/(N+H) instead depends on the observed N, which includes shared movement away from the reference direction (corrected cos(c, t) = 0.57–0.86). If only the component of the shared change along t is kept (cos²·N), the exact-differences fraction becomes 62–80% for five configurations and 43% for Nano Banana 2 (my computation). The claim as stated in Section 5.1 (p. 7) is accurate. The abstract's causal "so" is not.

**W4. Proximity is analysed as a level, not as a comparison across models (Section 5.2, p. 9).** The evaluation practice the paper criticises uses proximity to compare models, so the more relevant quantity is how much of the between-configuration variation in gain comes from the shared term. The data answer this and support the paper:
- across the six configurations, gain correlates 0.96 (CLIP) and 0.95 (CSD) with the shared term;
- in CSD, gain correlates −0.65 with the painter-specific term.

The paper does not report this, and it would strengthen Section 5.2 considerably.

**W5. The scope of Eq. 4 is broader in the title and abstract than in the evidence.** The identity holds for scores linear in the image embedding: mean cosine to the works, or to a (normalised) prototype. The paper says so on p. 7. The introduction, however, cites work whose proximity readouts are not necessarily linear: retrieval, top-k, thresholded imitation decisions. The claim "proximity gain therefore mostly measures movement that all the names share" is established only for the linear class.

**W6. The genuine-painting calibration is not directly comparable with the generated D (p. 10; Appendix D, pp. 20–21).** With pooled sampling, the two "pseudo-repeats" of a pseudo-scene are independent random works, so there is no shared scene content. The expected D is then target noise alone (≈ 0.125, as p. 21 derives). Generated D, by contrast, includes the scene-by-name variation V_scene = 0.04–0.39. The sentence "Every configuration's error is far above these means in every representation" is true, but part of the gap is this design difference. The class-sampling rows partly address it. A comparison with D_agg, or an explicit statement, would make the calibration fair.

**W7. D_held is bounded by construction (p. 10; Table 15, p. 23).** min_κ D(κ) = 1 − β²/Q ≤ 1, so "shrinking … lowers every held-out error" is expected. The held-out D values reproduce 1 − (β/√Q)² almost exactly: 0.645 vs 0.640 for GPT Image 1, 0.554 vs 0.551 for GPT Image 2, 0.714 vs 0.702 for FLUX.2 Max. The informative content is the alignment-ratio ranking, which the paper should say explicitly.

**W8. Minor estimator and reporting issues.**
- **Percentile reference-resampling intervals for β sit off-centre.** Each resample re-estimates H with the same ≈ 6.7% upward bias, so point estimates lie near the upper ends of their intervals (FLUX.2 Max 0.470 in [0.369, 0.509]; GPT Image 1 0.938 in [0.767, 0.989]; Table 3).
- **Ties in the best-configuration frequencies (Table 6) go to whichever configuration is listed first** (`np.argmax` in `painter_tmlr_diagnostics_v1.py`). In CSD recognition, ties occur in about 6% of scene resamples and are credited to GPT Image 1, so part of its 19.6% is ties.
- **Table 4 does not show the embedding β intervals** that the text cites ("all with scene intervals above zero", p. 9).
- **Interval types are mixed:** Student intervals for D in Table 3, percentile bootstrap in Table 4.
- **B/H (Table 1) and Q (Table 3) look like two different "sizes" of the same differences.** Q = B/H + V_scene would reconcile them for the reader.

**W9. Content confound in the embedding targets (Sections 3 and 5.3).** CLIP and CSD respond to content, and the reference collections differ in subject mix: 191/297 Monet works are water scenes against 31/105 for Cézanne. The 31-feature D is re-scored against content-matched targets (Table 20); the embedding D is not.

**W10. Clarity.** Section 5.3 in particular strings many numbers together per sentence, and the reader must keep about ten related symbols in mind (Table 10). The core message is clear from the title, Figure 1, Eq. 4 and Figure 3, but the specificity results are hard to follow.

## Requested changes

### Critical (must change for acceptance; both are wording changes, no new experiments)

1. **Correct the statement "In the embeddings no genuine split has an error above 0.53" (p. 10).** For example: "no genuine split in either embedding exceeds 1, and 97.5% fall below 0.53". Also correct the claim-registry derivation in `build_assets.py` so that the registered number matches the sentence.
2. **Qualify the D-versus-1 headline in the abstract, introduction bullet 3 and the Discussion recommendation.** Say that:
   - it is a point-estimate/unadjusted statement conditional on independent repeats;
   - GPT Image 1's verdict does not survive the Bonferroni-over-six interval ([0.935, 2.210]) and reverses if the repeats share ≳ 22% of their noise;
   - the excess comes from oversized rather than misdirected differences (Q ≈ 2.2–2.4).

   Also soften "in CSD none does", since Nano Banana 2 sits at D = 0.999 [0.876, 1.128]. A narrower formulation such as "Flare and Sunburst robustly, and GPT Image 1 at the unadjusted level" would be supported as worded.

### Minor

1. **Report the between-configuration decomposition of proximity gain (W4):** correlation or variance share of the gain with the shared and painter-specific terms across configurations. This directly supports the claim that proximity rankings track the name-invariant term.
2. **State in the abstract or Section 4.4 that Eq. 4 covers scores linear in the embedding,** and note that nonlinear proximity readouts (top-k retrieval, max-similarity, thresholds) are not covered (W5).
3. **Rephrase the abstract's justification of the exact-differences result (W3),** or report the fraction that keeps only the on-target component of the shared change.
4. **Qualify the texture-versus-colour bullet (p. 2, p. 12).** The difference is an average over six configurations driven by GPT Image 1 and Flare; it is reversed for Sunburst and Nano Banana 2 and essentially tied for GPT Image 2 (Table 7).
5. **Note that D_held ≈ 1 − (β/√Q)² ≤ 1 by construction (W7),** and add Q = B/H + V_scene to Table 10 or Section 4.3.
6. **Make the genuine-painting comparison like-for-like (W6).** Compare D_agg with the pooled controls, or state explicitly that pooled pseudo-scenes carry no scene effect.
7. **Report the implied admissible range of ρ.** Adjusted D becomes negative for Nano Banana 2 and FLUX.2 Max at ρ ≈ 0.30–0.32 (from the repeat-covariance output), which gives a rough upper bound. Optionally, collect a small third repeat on a different day for a subset of cells, to bound between-session dependence.
8. **Use bias-corrected (basic or BCa) reference-resampling intervals for β,** or correct Ĥ within resamples; alternatively, note the off-centre percentile intervals (W8).
9. **State the tie rule in Table 6,** or split ties (W8).
10. **Add the embedding β scene intervals to Table 4,** or cite where they are.
11. **Report embedding D against content-matched reference targets,** as Table 20 does for the 31 features (W9).
12. **Streamline Section 5.3:** move secondary numbers into tables and add a one-paragraph reading guide for D, D_agg, V_scene, D_held, Q and β/√Q.
13. **Commit to releasing the 1,008 generated images after de-anonymisation.** The Flare and Sunburst endpoints may disappear, and the paper's own Appendix H notes that features cannot be re-extracted from pixels without the images.

## Factual errors

- **p. 10:** "In the embeddings no genuine split has an error above 0.53." The recorded data give a maximum 97.5th percentile of 0.5315 (CLIP, class sampling, pooled target). About 2.5% of those splits therefore exceed 0.53. Only "no split exceeds 1" is supported.

No other factual errors were found among the roughly 70 numbers I checked.

## Criterion 1: claims and evidence: **partially**

The core claims are supported by accurate, reproducible evidence. These are: the shared fraction and its benchmarks; the exact proximity decomposition and its faithful and exact-differences benchmarks; positive aggregate alignment in all representations; disagreement among readouts; and the weak Monet–Sisley separation of the 31 features. Every point estimate I recomputed from raw per-image features and embeddings matched to the printed precision.

Two gaps remain, and both can be closed by editing rather than new evidence:
- one sentence is factually wrong (W1);
- the most categorical specificity verdict in the abstract and introduction (W2) omits its dependence on repeat independence and, for GPT Image 1, on the absence of a multiplicity adjustment. The paper's own supplementary analyses show both.

With these corrected, together with the smaller wording issues W3 and minor change 4, I would answer "yes".

## Criterion 2: audience and clarity: **yes**

The paper is relevant to TMLR readers who work on generative-model evaluation, style mimicry, protection and erasure, and representation-based metrics. The recommendations in Section 6 are actionable and need only a generic-style control and reference means. The main finding is communicated clearly through the title, Figure 1, Eq. 4 and Figure 3. The specificity section is dense and would benefit from streamlining (minor change 12), but this does not prevent an expert reader from following the argument.

## Desk-rejection screen: risk **low**

- **Scope:** in scope for TMLR.
- **Format:** TMLR template, anonymous.
- **Quality:** careful and internally consistent.
- **Machine generation:** AI assistance is disclosed, and the text does not read as low-care machine output. Every number I checked traces to a hash-bound analysis output.
- **Residual risk:** the main text runs to about 13–14 pages with a 15-page appendix of 25 tables, and it is very dense. That could irritate an action editor, but it is not grounds for desk rejection.

## Recommendation

**Minor revision.**

## Confidence

**4 / 5.** I independently recomputed the estimators from the raw features and embeddings, checked the derivations, and read the protocol and plans. I am less expert on the art-historical choices of painters and reference collections.

## Numbers verified and how

All recomputations use my own scripts reading the raw inputs:
- `data/manifests/painter_specificity_v2/psv2-20260911/measurements.jsonl` and `requests.jsonl`;
- `data/manifests/painter_feature_generation_v2/pfg2-method-20260905/{confirmation_features.jsonl, scaler.json}` (development median/IQR scaling; 649 measured reference works);
- `experiments/pfg2-sd-turbo-20260905/generated_features.jsonl`;
- `reports/painter_learned_audit_v1/{inputs.json, embeddings_clip.npz, embeddings_csd.npz}`;
- `data/manifests/painter_specificity_v2/psv2-20260911/attempts.jsonl`.

I did not reuse the paper's code for these, except to read the recorded genuine-control and repeat-covariance outputs.

- `uv run --locked python paper/tmlr/build_assets.py --check` passes: "ok: 26 generated files and 141 claims".
- **H = 5.915** (Table 11) and the finite-sample bias of H = 6.7% (6.75%). Exact.
- **Table 1** for all six configurations (shared fraction, N/H, B/H, faithful, exact differences), e.g. GPT Image 1 71.3 / 5.26 / 2.12 / 95.2 / 84.0 and Nano Banana 2 69.1 / 1.36 / 0.61 / 92.5 / 57.6. Exact.
- **Table 11** (G/H, I/H) and **Table 12** (cos(c, t) 0.57–0.86, λ 24.8–64.6%). Exact.
- **Table 3** β, Q and D for all six configurations. Exact. Also exact: the prespecified simultaneous β intervals with t₁₃,₁₋₀.₀₅/₄₂ (e.g. GPT Image 1 [0.709, 1.168]) and the nominal D intervals (e.g. [1.129, 2.016]).
- **Bonferroni-over-six D interval** for GPT Image 1, [0.935, 2.210]. Exact.
- **Table 14:** all 15 D differences with simultaneous and nominal intervals; 6/15 resolved nominally and 2/15 (Flare and Sunburst vs FLUX.2 Max) simultaneously. Exact.
- **Table 15** D_agg, V_scene, D_held and fitted-scalar ranges (e.g. GPT Image 2 D_held 0.554, scalar 0.438–0.459). Exact. D_held ≈ 1 − (β/√Q)² confirmed.
- **Table 13** centroid proximity split (Eq. 6), e.g. GPT Image 1 17.490 = 17.844 − 0.354. Exact.
- **Table 2** shared, faithful and exact-differences shares in CLIP and CSD for all six configurations. Exact. Eq. 4 residual ≤ 2.2 × 10⁻¹⁶. "−2.8 to +6.5 points" confirmed (−2.80 to +6.54).
- **Table 4** β and D, **Table 5** proximity gains and recognition accuracies, and development-panel macro accuracy 79.8% (CLIP) and 79.6% (CSD). Exact.
- **Table 7** family shared fractions and six-configuration means (74.3 / 71.5 / 68.2). Exact.
- **Scene-bootstrap quantities,** my 5,000 draws with a different seed. All agree within Monte Carlo error:

  | Quantity | Paper | Mine |
  |---|---|---|
  | Nano Banana 2 shared-fraction interval | [52.0, 75.8] | [51.1, 76.0] |
  | FLUX.2 Max obs. < faithful | 84.1% | 85.6% |
  | Texture − colour interval | [−13.5, −2.0] | [−13.1, −2.0] |
  | Texture − colour below zero | 99.7% | 99.4% |
  | Texture below spatial | 65.2% | 66.2% |

- **Reference and joint resampling,** my 1,000 and 2,000 draws. Agree within Monte Carlo error:

  | Quantity | Paper | Mine |
  |---|---|---|
  | FLUX.2 Max β reference interval | [0.369, 0.509] | [0.374, 0.513] |
  | Joint D < 1, FLUX.2 Max | 94.2% | 95.2% |
  | Joint D < 1, Nano Banana 2 | 33.4% | 33.9% |

- **Table 6 CLIP stability shares,** my 3,000 draws: Nano Banana 2 largest gain 85.5% (paper 85.8%); GPT Image 2 best recognition 98.9% (98.7%); GPT Image 1 lowest D 99.0% (99.3%).
- **Table 25 (SD-Turbo):** shared, faithful and exact-differences fractions for all 31 features and each family (64.2/92.5/67.4; 57.5/79.7/56.4; 84.9/96.8/83.3; 36.6/89.8/46.5), recomputed with the cross-block U-statistic. Exact.
- **Timing:** repeat gap median 3.15 min, maximum 19.98 min; collection 15:34–18:21 UTC; 1,008 starts and 1,008 ends with no retries.
- **By table inspection:** Cézanne least shared in 11 of 12 pairs (Table 23); normalised-prototype change ≤ 0.5 points and reference-setting change ≤ 1.6 points (Table 21); Monet–Sisley intervals (Table 18).
- **Recorded outputs read directly:**
  - Genuine controls: embedding `above_one = 0`; maximum 97.5th percentile 0.5315. This contradicts the p. 10 sentence (W1).
  - Repeat covariance: GPT Image 1 adjusted D is 1.348 at ρ = 0.1 and 0.898 at ρ = 0.25 (W2).
- **Tie frequency** in CSD recognition bootstrap: 5.8% of draws, all credited to the first-listed configuration.

**Derivations checked analytically:** the exchangeable null of 1/4 (N + B = Σ_a‖h_a‖²); Eq. 4 and Eq. 8; D = 1 − 2β + Q; E[D] = (κ − 1)² under scaling; Eq. 7; the finite-sample bias (3/4)Σ tr(Σ_a)/n_a; and min_κ D(κ) = 1 − β²/Q.

PDF SHA-256 (`shasum -a 256`): `caa3b4299154a8926e29f7a7dee8d5c81784ff77477597931a0aab8d4d5ec617`
