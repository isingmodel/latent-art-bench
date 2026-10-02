# TMLR review: methods (statistics, claims vs. evidence, reproducibility)

**Submission:** "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation" (anonymous)
**PDF read:** `reports/tmlr_review_v1/round_05/input/manuscript.pdf`, SHA-256 `764356d845744d7adc994600113628525cce6f0569eff8c7927439c6a1ba5316` (30 pages, main text and Appendices A–H read in full; figures and tables checked as rendered)

## Summary of the submission

Six closed text-to-image configurations (four OpenAI GPT Image variants, Nano Banana 2, FLUX.2 Max) render 14 authored outdoor scenes under six clauses: no painting instruction, a generic oil-painting instruction, and "in the style of" Monet, Sisley, Pissarro or Cézanne. Each cell has two separately requested repeats, giving 1,008 images. The paper averages the four named conditions and splits what the names add beyond the generic clause into a shared change c and between-name differences e_a. Squared sizes are estimated from cross-repeat inner products, which removes the positive noise bias. There are four contributions:

1. **Shared fraction with benchmarks.** In 31 hand-designed colour/spatial/texture features, N/(N+B) is 66.7–88.4%. It is compared with a "faithful imitator" (named means equal the reference painter means, 84.8–95.2%) and an "exact-differences" generator (observed shared change, reference differences, 57.6–84.2%).
2. **An exact identity for proximity gain** (Eq. 4). For any score that is linear in the image embedding, the named-minus-generic proximity gain equals a name-agnostic shared term plus Hβ/4. In CLIP and CSD the shared term supplies 54.2–83.8% of the gain, and differences in gain between configurations track it (r = 0.96, 0.95).
3. **Agreement metrics for specificity.** The metrics are β (aligned amplitude), Q, the alignment ratio β/√Q and a repeat-corrected error D, where D = 1 corresponds to making no painter distinctions. They come with a prespecified 21-endpoint inferential family (six β, 15 pairwise ΔD; paired-scene Student intervals; Bonferroni). The verdicts differ by representation.
4. **Readouts disagree.** Proximity, agreement and recognition favour different configurations. A label-free translation can change recognition without changing any painter difference.

The paper states that only the 21-endpoint family was prespecified and that everything else is descriptive and retrospective. A hash-bound replay script regenerates all tables and checks the registered prose numbers.

## Strengths

- **The central decomposition is correct and useful.** Eq. (1)–(2), the exchangeable-null value of 1/4, Eq. (4)/(8) (exact because Σ_a r_a = Σ_a d_a = 0 and the score is linear), the D = 1 − 2β + Q identity, D = D_agg + V_scene, and the finite-sample bias of H (¾ Σ tr(Σ_a)/n_a) are all correct. I checked the algebra and reproduced it numerically: the identity residuals are about 1e-16. The point that proximity gain is structurally dominated by a name-agnostic term whenever the shared movement exceeds H/4 is simple and actionable. It is worth putting in front of people who use CSD/CLIP proximity as a style-fidelity score.
- **Well-chosen benchmarks.** The exact-differences benchmark N/(N+H) removes the generated-vs-photographed domain gap from the comparison and makes the "a large shared fraction is expected even for good imitation" argument sound.
- **Sound noise handling.** Cross-repeat products are unbiased under independent repeats. The paper shows the direction of the bias under shared repeat error, derives the ρ thresholds at which conclusions flip, and gives a coverage simulation that includes the failure case (0.04% coverage under configuration-level shared state). This is an unusually honest treatment of a hard-to-test assumption.
- **Transparent inferential status.** The prespecified 21-endpoint family is kept separate from the post-hoc analyses. The protocol files (`studies/painter_specificity_v1/PROTOCOL.md`, `v2/PROTOCOL.md`, `DECISION.md`, `TERMINATION.md`) match the paper's account: the aborted first attempt, the 16→14 scene reduction before any outcome, Bonferroni over 21, and paired-scene t with n−1 df.
- **Calibration against genuine paintings and a separability check.** The paper shows that the 31 features separate Monet and Sisley poorly (39.6% and 30.6% nearest-mean accuracy) and declines to rank specificity overall. That is the right call.
- **Exceptional reproducibility of the reported numbers.** `build_assets.py --check` passes (26 generated files, 163 claims). I independently recomputed essentially every primary table from the raw per-image features and embeddings (see "Verified numbers") and found no numerical discrepancy.

## Weaknesses

### W1. The "aligned but oversized" characterization conflicts with the paper's own prespecified diagnostic (Abstract p.1; Intro bullet 3 p.2; §5.3 p.9; §6 "Recommendations" p.13)

The abstract says several configurations "make aligned but oversized differences". §5.3 says "Their differences are well aligned but oversized: β = 0.772–0.938 with Q = 2.28–2.45, an alignment ratio of 0.511–0.600".

The v1 protocol ("Explanatory diagnostics") prespecified an exact split of D into an aligned-amplitude error and an orthogonal (off-pattern) error, "to distinguish weak/strong aligned responses from painter differences in the wrong direction". That split is in the retained primary output (`data/manifests/painter_specificity_v2/psv2-20260911/analysis.json`, fields `amplitude_error` and `off_axis_error`) but is not reported. It shows:

| Configuration | D | amplitude error | orthogonal error | orthogonal share of D |
|---|---|---|---|---|
| GPT Image 1 | 1.572 | 0.029 | 1.543 | 98% |
| GPT Image 2 | 1.226 | −0.003 | 1.229 | ≈100% |
| Flare | 1.738 | 0.054 | 1.683 | 97% |
| Sunburst | 1.641 | 0.044 | 1.598 | 97% |
| Nano Banana 2 | 1.109 | 0.317 | 0.793 | 72% |
| FLUX.2 Max | 0.801 | 0.304 | 0.497 | 62% |

For the three configurations with D > 1, the component along the reference pattern is already about the right size (β ≈ 0.77–0.94). Essentially all of the error is off-pattern. An alignment ratio of 0.51–0.60 is a noise-corrected cosine: 64–74% of the (scene-wise) squared size lies outside the reference pattern. Calling this "well aligned" overstates it.

The comparative reading the paper intends is defensible: these configurations have a cosine similar to FLUX.2 Max's 0.546 but a larger total size, and D < 1 requires ‖d‖ < 2·cos·‖r‖. However, a reader will take "aligned but oversized" to mean "the right pattern, exaggerated", and the data do not show that.

The Recommendations sentence "the alignment ratio shows whether they are misdirected or merely too large" makes this worse. By that criterion, all six configurations (ratios 0.44–0.67) are substantially misdirected and none is "merely too large".

This is an editing fix, not new evidence: reword the characterization and report the prespecified split.

### W2. Small inaccuracies and unverifiable statements in the results prose

- **Figure 3 caption (p.9)** says observed shares lie below the faithful ones in the features "but not in the embeddings". This is false for GPT Image 2 in CLIP (observed 73.2 vs faithful 76.0, Table 2), which §5.2's own "−2.8" acknowledges.
- **§5.3 (p.11)** says that under content-matched targets "the embedding errors change by at most 0.037 and keep their order". This is true only relative to the pooled target on the same 11 scenes (`painter_tmlr_diagnostics_v4`, `pooled_d` vs `class_d`), and that column is not in Table 5. Table 5 juxtaposes the 14-scene primary D with the 11-scene class D. Between those columns the changes reach 0.064 (CLIP Sunburst 1.136 → 1.200; CLIP GPT Image 1 0.847 → 0.904), and two adjacent orderings swap: GPT Image 1/GPT Image 2 in CSD (0.735 < 0.741 becomes 0.767 > 0.759) and Flare/FLUX.2 Max in CLIP (1.057 < 1.058 becomes 1.074 > 1.023). A reader checking the text against Table 5 will think the text is wrong. The replay script also checks only that the minimum is unchanged, not the full order.
- **Intro bullet 3 (p.2)**, "FLUX.2 Max has the lowest error in the features", is a point estimate. Under the prespecified rule ("rank models only on D and label differences unresolved if the simultaneous interval contains zero"), FLUX.2 Max is resolved only against Flare and Sunburst. §5.3 says so, but the introduction does not.
- **Appendix A (p.18)** says "so under this model the dependence is below about 0.3". This follows from the point estimates of D. With D's sampling error the statement is not a bound. It should read "the point estimates imply".

### W3. Uncertainty summaries for post-hoc embedding results (Table 5, §5.3, Abstract)

The embedding D intervals are percentile scene-bootstrap intervals with S = 14, which tend to be narrow. They are also not the Student intervals used for the prespecified family. I recomputed paired-scene Student intervals for embedding D. The conclusions do not change: for CSD, GPT Image 1 [0.629, 0.842], GPT Image 2 [0.652, 0.830], Flare [0.771, 0.867] and FLUX.2 Max [0.609, 0.818] stay below 1, and CLIP Sunburst [1.047, 1.225] stays above 1. They remain below 1 even with a Bonferroni-over-12 half-width. The authors should say this, because the abstract's "resolved" language rests on these intervals.

There is also a useful asymmetry the paper does not state. Positive repeat dependence and reference-target noise both bias D upward. The D < 1 conclusions (CSD) are therefore conservative under both, while the D > 1 conclusions (features; CLIP Sunburst) are the vulnerable ones. The ρ sensitivity is given only for the features.

### W4. Correlation evidence for "differences in gain follow the shared term" (§5.2 p.8–9; Intro bullet 2)

The correlation is computed over n = 6 configurations and is partly mechanical, because total = shared + specific. The variance ratio is the more informative statistic. It is reported for CLIP (≈11; I get 10.8) but not for CSD, where I get ≈5.8, and where the shared and specific terms are negatively correlated. The qualitative claim holds, but the CSD variance ratio should be reported, and the part-whole caveat noted.

### W5. Prespecified diagnostics omitted without comment (§4.5)

Besides the amplitude/orthogonal split (W1), the v1 protocol prespecified these diagnostics, which the paper does not report or mention:

- generated-vs-reference energy distances and trace ratios per model and artist ("a model may recover artist contrasts yet fail to recover within-artist diversity");
- the scene fixed-effects regression;
- a reference-only PCA display.

§4.5 lists what the protocol "also prescribed" but does not say that these were dropped. Complete reporting of a prespecified plan, or an explicit list of what was omitted and why, is expected.

### W6. Configuration identity (§3 "Generators" p.4; Appendix A p.17)

The first attempt was stopped because a gateway route accepted an invented model identifier. The paper does not say whether the same negative control (an invalid identifier) was run on the explicit `provider.only=[openai]` route used for the main collection. The pilot records show no such probe. The medium-quality cost difference (GPT Image 2 $0.0528 vs Flare/Sunburst $0.0133 per image) and some distinct feature signatures (e.g. share of N along the generic shift 6.6% vs 22.0%; Monet–Sisley β −0.011 vs −0.249) are weak evidence that Flare and Sunburst are distinct backends. The paper already labels these as requested configurations, but it should report whether the explicit route rejects invalid identifiers, and what evidence distinguishes Flare from Sunburst.

### W7. Limitations that are acknowledged and appropriately scoped (no action needed beyond wording)

- The scope is four related painters, one template, 14 authored scenes, two repeats taken minutes apart within the same scene block, closed services, and four of six configurations from one vendor.
- There is no any-name control (a fictitious name or "Impressionist"), so the shared change cannot be attributed to the painters.
- The 31-feature representation fails the paper's own first recommendation for Monet vs Sisley.
- The AI-assistant audits (content labels, which disagree with the title labels on 230 of 870 works, and crops) have no human verification. They enter only sensitivity analyses. A small human-checked random sample would strengthen those analyses cheaply.

The claims are worded within this scope. One exception is §6 (p.12), "as movement toward any painting-like image would", which is an untested conjecture and should be flagged as one.

### W8. Clarity

The paper is precise but very dense.

- The abstract (~290 words) packs six numeric findings and several defined terms.
- "Resolved" is used throughout to mean "interval excludes the value". It should be defined once, and it should be made clear which uses are inside the prespecified family and which are not.
- The main-text Monet–Sisley summary ("scene intervals that include zero in four configurations", p.11) omits that Sunburst's interval is entirely negative (−0.249 [−0.369, −0.140], Table 17). That is a resolved wrong-direction pair contrast under scene resampling, although the reference interval [−0.443, 0.122] includes zero. It is relevant to "every configuration responds in the reference direction in aggregate".
- The Reproducibility statement says the code "checks every number quoted in the text". Appendix H more accurately says "each registered number". The two should be aligned.

## Requested changes

**Critical (must change for acceptance; all are editing changes, no new data required)**

1. **(W1)** Replace "aligned but oversized" in the Abstract, Intro bullet 3 and §5.3 ("well aligned but oversized") with wording that reflects the prespecified decomposition. For example: "their projection on the reference pattern is close to the reference size (β = 0.77–0.94), but they carry large off-pattern differences (alignment ratio 0.51–0.60), so their total size exceeds what their alignment warrants". Report the prespecified aligned-amplitude and orthogonal error split for all six configurations (Table 4 or 14). Revise the Recommendations sentence, because by the paper's own criterion none of the six configurations is "merely too large".

**Minor**

1. **(W2)** Correct the Figure 3 caption: in CLIP, GPT Image 2's observed share is below its faithful value.
2. **(W2)** Add the 11-scene pooled-target D to Table 5, or state explicitly in §5.3 that "change by at most 0.037 and keep their order" is relative to the pooled target on the same 11 scenes. Note that relative to the 14-scene primary column the changes reach 0.064 and two adjacent pairs swap.
3. **(W2)** In Intro bullet 3, qualify "FLUX.2 Max has the lowest error in the features" as a point estimate that is resolved only against Flare and Sunburst in the prespecified family.
4. **(W2)** In Appendix A, change "the dependence is below about 0.3" to a statement about point estimates.
5. **(W3)** Report paired-scene Student intervals (or state that they agree) for embedding D and β, alongside the percentile intervals. State the asymmetry: positive repeat dependence and target noise inflate D, so D < 1 conclusions are conservative and D > 1 conclusions are the vulnerable ones. Extend the ρ sensitivity to the CLIP D > 1 result, or note that it is missing.
6. **(W4)** Report the CSD variance ratio of the shared to the painter-specific term (≈5.8). Note that n = 6 and that total = shared + specific, so the correlation is partly mechanical.
7. **(W5)** List the prespecified diagnostics that are not reported (energy distances and trace ratios, the scene fixed-effects regression, the reference PCA), or report them in the appendix.
8. **(W6)** State whether the explicit OpenAI route was checked with an invalid identifier, and summarize the evidence that the Flare and Sunburst requests reached distinct backends.
9. **(W7)** Flag §6's "as movement toward any painting-like image would" as conjecture. Consider a human spot-check of a random sample of the AI-assistant content labels and crops.
10. **(W8)** Define "resolved" once, and mark which "resolved" statements are inside the prespecified family. Mention Sunburst's negative Monet–Sisley alignment in the main text. Align the Reproducibility statement ("every number") with Appendix H ("each registered number"). Consider shortening the abstract.

## Criterion 1: Are the claims supported by accurate and convincing evidence? **partially**

Every number I checked is accurate and follows from the retained measurements. The algebraic claims (Eq. 1–8, the D identities, the H-bias correction) are correct. These headline claims are supported as worded:

- the shared fraction is large and expected even for good imitation;
- proximity gain is mostly the shared term, and cross-configuration differences in gain track it;
- aggregate β > 0 for all six configurations;
- representation dependence of the agreement verdicts;
- CSD D < 1 for four configurations (robust to Student and Bonferroni intervals and conservative under repeat dependence);
- different readouts favour different configurations.

The paper is also careful about the prespecified vs. post-hoc status. The gap is the characterization of the D > 1 configurations as "(well) aligned but oversized" in the abstract, introduction and §5.3. The paper's own prespecified amplitude/orthogonal split shows that 97–100% of their error is off-pattern and their along-pattern amplitude is near the reference, so that wording needs narrowing (critical change 1). The Figure 3 caption misstatement and the Table 5 / "keep their order" mismatch are smaller accuracy issues. All of these are fixable by editing and need no new experiments.

## Criterion 2: Would some of TMLR's audience be interested, and is it clear? **yes**

Researchers evaluating style mimicry, style protection/erasure, and CSD/CLIP-based style metrics will find the proximity identity and the benchmark logic directly useful, and the recommendations are concrete. The writing is precise, the notation is summarized (Table 8), and each result is traceable to a table. The density of the abstract and results prose is a readability cost, not a barrier.

## Desk-rejection screen: **low**

The paper is in scope (evaluation methodology for generative models). It uses the TMLR template, is anonymized, and has a complete broader-impact statement. It is written with evident care: consistent notation, correct algebra, and numbers that replay exactly. It does not read as low-care machine-generated text, and AI assistance is disclosed. The only concern is density.

## Recommendation: **minor revision**

The methods are sound, the numbers are reproducible, and the claims are appropriately scoped. The one required change is an interpretive rewording backed by an already-computed prespecified diagnostic, plus several small accuracy and clarity fixes.

## Confidence: **4 / 5**

I re-derived the estimators and independently recomputed the primary tables from the raw features and embeddings. My confidence is not 5 because the scene/reference resampling outputs were checked only by approximate re-simulation with different seeds, and the image-level feature extraction was not re-run from pixels (the images are not in the supplement).

## Numbers verified and how

All checks were read-only. Scripts were placed in the session scratchpad.

- **PDF SHA-256:** `764356d845744d7adc994600113628525cce6f0569eff8c7927439c6a1ba5316` (`shasum -a 256`).
- **`uv run --locked python paper/tmlr/build_assets.py --check`:** "ok: 26 generated files and 163 claims".
- **Independent recomputation from raw 31-feature vectors.** Sources: `measurements.jsonl` joined to `requests.jsonl`, standardized with `scaler.json`; references are the 649 measured rows of `confirmation_features.jsonl`. The estimators are my own implementation of Eqs. 1–3 and 5–7.
  - H = 5.915; finite-sample H bias = 6.7%.
  - Table 1, all six rows exactly: fractions 71.3/70.9/71.1/66.7/69.1/88.4; N/H; B/H; faithful 95.2/89.3/84.8/86.9/92.5/90.4; exact 84.0/83.3/83.3/79.9/57.6/84.2.
  - Table 11 exactly (cos(c,t) 0.85…0.86; λ 44.1…64.6; along-generic 0.1…52.8).
  - Table 9 exactly (G, N, I, N_free; vs-free 82.5–95.7; within-scene 52.8–93.6).
  - Table 4: β, Q, D, β/√Q, and D = 1 − 2β + Q exactly; β simultaneous intervals (e.g. FLUX.2 Max [0.239, 0.701]); D Student intervals (e.g. GPT Image 1 [1.129, 2.016]); Bonferroni-over-6 for GPT Image 1 [0.935, 2.210].
  - Table 13: all 15 ΔD with simultaneous and nominal intervals exactly. 2 of 15 are resolved simultaneously (Flare–FLUX.2 Max, Sunburst–FLUX.2 Max) and 6 of 15 nominally.
  - Table 14: D_agg, D_held (0.645/0.554/0.741/0.706/0.832/0.714) and the fitted-scalar ranges exactly.
  - Table 12: repeat noise/H (2.02 … 1.67) and centroid proximity gain split (17.490 = 17.844 − 0.354, etc.) exactly.
  - Development nearest-mean macro accuracy 49.8% (Monet 39.6%, Sisley 30.6%).
- **Derivation check (ρ thresholds, Appendix A).** Shared error fraction ρ inflates D by ρ/(1−ρ)·(repeat noise). Solving from Table 4 D and Table 12 noise gives GPT Image 1 0.221, Flare 0.637, Sunburst 0.525, the NB2/FLUX.2 Max crossing ≈0.25, and zero crossings 0.30/0.32. All match the text.
- **Independent recomputation from `reports/painter_learned_audit_v1/embeddings_{clip,csd}.npz`** (row map from `inputs.json`):
  - Table 2, all 12 observed/faithful/exact shares exactly.
  - Table 3 gain/shared/specific/recognition/D exactly.
  - Table 5 β and D point estimates exactly.
  - Eq. 4 residual about 1e-16.
  - corr(gain, shared) = 0.96 (CLIP), 0.95 (CSD); corr(gain, specific) = −0.65 (CSD).
  - CLIP variance ratio 10.8 (the paper's "11"); the CLIP gain ranking is identical to the shared-term ranking.
  - Nano Banana 2 is fifth in the CLIP painter-specific term (0.01816 vs GPT Image 1 0.01827).
  - Student intervals for embedding D (reported in W3).
- **Approximate re-simulation with different seeds:**
  - joint scene+reference D < 1: 0.6/9.6/0.0/0.1/33.1/94.2 vs paper 0.7/9.9/0.0/0.1/33.4/94.2;
  - reference-resampling β intervals close to Table 4 (e.g. FLUX.2 Max [0.372, 0.514] vs [0.369, 0.509]);
  - genuine-painting control (pooled, distinct works): mean 0.112 and range [−0.868, 1.129] vs 0.125 and [−0.886, 1.159];
  - Table 20 "most often best": CLIP gain Nano Banana 2 86.4 vs 85.8; CLIP D GPT Image 1 99.4 vs 99.3; CLIP recognition GPT Image 2 98.8 vs 98.7; CSD recognition 80.4 vs 80.4; CSD D FLUX.2 Max 47.6 vs 47.2; CSD gain 33.5 vs 33.6;
  - FLUX.2 Max recognition below Nano Banana 2 in 99.9% of resamples in both encoders.
- **From retained analysis JSONs:**
  - SD-Turbo shared fraction 64.2%, β 0.618, D_agg 0.917, D 1.637 (`painter_cross_cohort_v1`);
  - drift predictive gains −3.4 to −0.7% and maximum repeat gap 19.98 min (`painter_request_timing_v1`);
  - content-matched max |class − pooled(11 scenes)| = 0.037 with order preserved, but see W2 for the comparison against Table 5's primary column;
  - prespecified amplitude/orthogonal error split (`psv2-20260911/analysis.json`), W1.
- **Arithmetic and table cross-checks:**
  - reference counts 297 + 106 + 141 + 105 = 649, and the content-lexicon counts sum per painter;
  - development panel 101 + 36 + 48 + 36 = 221;
  - 6 × 14 × 6 × 2 = 1,008 images; 112 named images per configuration;
  - recognition shift changes −5.4 to +12.5 (CLIP) and +0.9 to +26.8 (CSD), with means +2.7 and +10.0;
  - "11 of 12" scene intervals above 50% and "Cézanne least shared in 11 of 12" (Table 23; the exception is Nano Banana 2 in CSD);
  - unit-prototype shares change by at most 0.5 points and source/target variants by at most 1.6 points (Table 21);
  - H-corrected β 0.474–1.071 and FLUX.2 Max D 0.787.
