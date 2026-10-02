# TMLR review — methods reviewer (statistics, claim–evidence, number verification, reproducibility)

**Submission:** "What Does an Artist Name Add? Separating Shared and Painter-Specific Responses in Text-to-Image Generation" (anonymous, 20 pages including appendices)

**PDF read:** `manuscript.pdf`, SHA-256 `33c87a6f609b2c791b0ba6c5101d4af64fc9b05e155b9bb448c65a5a6a90b5c8`

---

## 1. Summary of the submission

The paper asks how much of the effect of adding an artist name to a text-to-image prompt is common to every name in a prompt set, and how much differs between names. The design fixes 14 authored landscape scene descriptions. Each is crossed with six style clauses (none; "Render as an oil painting."; oil painting in the style of Monet, Sisley, Pissarro or Cézanne), six commercial configurations (GPT Image 1, GPT Image 2, GPT Image 2.5 Flare and Sunburst, Nano Banana 2, FLUX.2 Max) and two independent repeats, for 1,008 images. Images are measured in 31 hand-designed color/spatial/texture features, standardized by a separate 221-work development panel, and compared with 649 reference reproductions.

The main technical device is elementary but well executed:

- **Decomposition.** The four named-minus-baseline shifts are split into their mean (shared component) and the departures from it (between-name component B). Squared sizes are estimated with cross-repeat inner products so that sampling noise does not bias them upward (Eqs. 1–2, Appendix C). A generic-oil-painting baseline isolates what the name adds beyond the painting instruction (N).
- **Agreement with reference painter differences.** The between-name component is compared with reference painter contrasts through an aligned amplitude β, a relative size Q and a repeat-corrected error D = 1 − 2β + Q (Eq. 3). There is a prespecified family of 21 Bonferroni-adjusted paired-scene intervals.
- **Learned embeddings.** In CLIP and CSD, gain in cosine similarity to the prompted painter's prototype is split exactly into a shared term and H·β/4 (Eq. 4). Nearest-prototype recognition is reported as a separate readout.
- **Retrospective check.** A 2,000-image SD-Turbo collection with matched seeds is analysed with a block U-statistic.

The paper reports four findings:
1. 66.7–88.4% of what a name adds beyond the generic instruction is shared.
2. The same holds in CLIP/CSD (73.2–83.8% and 54.2–79.7% of prototype gain).
3. Proximity, agreement and recognition rank the configurations differently.
4. In SD-Turbo the pattern holds overall but not in texture.

It recommends that artist-style evaluations include a generic-style control and report the decomposition next to any proximity score.

## 2. Strengths

- **Numerical accuracy and reproducibility are exemplary.** `build_assets.py --check` passes ("ok: 12 generated files and 78 claims"), and every prose number is bound to a hash-recorded analysis output. More importantly, I recomputed the main tables from the raw retained measurements (`measurements.jsonl`, `reference_windows.jsonl`, the frozen scaler) and from the raw CLIP/CSD embedding archives, using my own code rather than the project's. Every value I checked matches to the printed precision (Section 10).
- **The estimators are correct and well explained.** I checked the following algebraically and numerically:
  - the cross-repeat noise correction;
  - the identities C = G + N + I, D = 1 − 2β + Q and D = D_agg + V_scene (Eq. 6);
  - the exact prototype-gain split (Eq. 4 / Eq. 7), which holds to 1e-10 in my recomputation;
  - the held-out rescaling c = max(0, β/Q);
  - the translation rule's invariance of β, Q and D.

  The block U-statistic for the seed-matched SD-Turbo design (Appendix G) is the right estimator for that dependence structure.
- **Prespecification is honest.** The 21-comparison family, the Bonferroni t_{13,1−0.05/42} intervals and the distinction between prespecified and retrospective analyses (Section 4.4) match `studies/painter_specificity_v1/PROTOCOL.md` and `.../v2/PROTOCOL.md`. The 16→14 scene reduction was decided before outcomes (v2 DECISION.md) and is disclosed.
- **Limitations are candid.** The paper states repeat dependence and its crossing points (ρ = 0.251, 0.246), closed-service checkpoints, the AI-only source audit, CSD being built on CLIP, and the SD-Turbo collection sharing the references. The simulation in Appendix C that shows coverage collapsing under shared state (0.04%) is the kind of adverse evidence authors often omit.
- **Sensitivity analyses are broad.** They cover the central-square window, class-matched targets, equal-family and covariance weighting, source-corrected crops with and without a refit scaler, and scene deletion. I confirmed FLUX.2 Max keeps the lowest D under all 14 single-scene deletions.
- **The message is relevant.** It shows that a proximity score mixes a name-independent shift with name-specific differences, which is useful for anyone designing artist-style, mimicry or erasure evaluations.

## 3. Weaknesses (with locations)

### W1. The headline shared fractions have no benchmark, and the paper says none can be computed (Abstract; Section 1 bullets, p. 2; Section 5.1, pp. 6–7; Section 5.3, p. 8; Section 6, p. 10)

The paper presents "66.7–88.4% shared" and "the shared change is 1.4–5.3 times the entire spread of the reference means" as its lead finding. Section 6 (p. 10) then says: "Our data cannot say how large that appropriate part is, because it would require the same decomposition for real paintings against a generic reference, which does not exist."

That statement is too strong. The between-name component B is judged against the reference contrasts r_a (B vs H, β, Q, D). The same reference target implies what a generator that exactly matched the reference means would produce: B = H and N = 4‖μ̄ − ḡ_generic‖². I computed this from the retained vectors (cross-repeat, scene-averaged, as in Table 1).

**31 features.** The perfect-agreement shared change is N/H = 5.6–19.6 per configuration, against observed 1.4–5.3. The corresponding perfect-agreement shared share N/(N+H) is 84.8–95.2%, higher than every observed share (66.7–88.4%). Per configuration, observed vs. perfect-agreement shares are:

| Configuration | Observed | Perfect agreement |
|---|---|---|
| GPT Image 1 | 71.3% | 95.2% |
| GPT Image 2 | 70.9% | 89.3% |
| Flare | 71.1% | 84.8% |
| Sunburst | 66.7% | 86.9% |
| Nano Banana 2 | 69.1% | 92.5% |
| FLUX.2 Max | 88.4% | 90.4% |

The observed shared shift points toward the reference centroid: the cosine with (μ̄ − generic) is 0.58–0.86. Only 33–76% of N lies along that direction, and naming reduces the squared distance to the centroid in every configuration, from 1.40–4.91 H (generic) to 0.64–1.89 H (named).

**CLIP/CSD (Eq. 4).** Suppose a generator's named means equal the reference prototypes. Its shared part of the prototype gain, (μ̄ − g_g)ᵀμ̄ / [(μ̄ − g_g)ᵀμ̄ + H/4], would be:

| Configuration | CLIP, perfect agreement | CLIP, observed | CSD, perfect agreement | CSD, observed |
|---|---|---|---|---|
| GPT Image 1 | 71.3% | 74.5% | 70.4% | 72.7% |
| GPT Image 2 | 76.0% | 73.2% | 48.3% | 54.2% |
| Flare | 77.1% | 78.8% | 62.7% | 65.0% |
| Sunburst | 77.6% | 77.7% | 65.4% | 67.4% |
| Nano Banana 2 | 82.9% | 83.8% | 75.7% | 79.7% |
| FLUX.2 Max | 80.7% | 81.7% | 71.0% | 77.6% |

So the headline embedding fractions (73.2–83.8% and 54.2–79.7%) are within a few points of what exact agreement with the reference prototypes would give. They are set mainly by how far the generic-clause images sit from the four-painter centroid, not by what generators fail to do.

**Caveat.** The reference centroid mixes subject matter and reproduction conditions with style, so this benchmark is conditional on the reference target. That is exactly the conditioning the paper already accepts for H, β and D. A content-matched version is possible with the class targets already used in Table 11.

As written, a reader will take "most of what a name adds is shared" and "N is several times H" as evidence that names mostly add a generic effect. The paper's own data show that a large shared fraction is expected even under perfect agreement. This does not refute the paper's central methodological point: proximity gain cannot separate the two components. It does change how the headline numbers should be read, and it removes the claim that the appropriate size is unknowable.

### W2. The real-painting control for D was computed but not reported (Section 5.2, p. 8; Table 2)

`reports/painter_specificity_review_v1/analysis.json` (`real_controls`) contains a real-painting control that the paper does not mention. Held-out halves of the reference paintings are arranged into the same 14-scene × 2-repeat design and scored against the other half. The results are:

| Arrangement | Mean D | 95% range over 1,000 splits | P(D ≥ 1) |
|---|---|---|---|
| Content-pooled | 0.234 | [−0.758, 1.38] | — |
| Class-matched real paintings vs. pooled target | 0.753 | [−0.554, 2.40] | ≈ 0.35 |
| Class-matched real paintings vs. class target | 0.731 | [−0.248, 1.946] | ≈ 0.29 |

This matters for two statements:

- **"so no configuration is shown to beat a generator that makes no painter distinctions at all" (p. 8).** Under this design, even the painters' own content-matched paintings would often not be shown to beat D = 1. The statement is literally true but gives little information. The control implies a practical floor of roughly 0.7 for content-matched D against the pooled target, not 0.
- **"D = 0 for exact agreement" (Section 4.2).** FLUX.2 Max's D = 0.801 is close to the real-painting value. The paper also does not state that three configurations have nominal 95% intervals entirely above 1: GPT Image 1 [1.129, 2.016], Flare [1.477, 1.999] and Sunburst [1.312, 1.971]. Their between-name differences are, on this metric, worse than no distinctions, driven by Q ≈ 2.2–2.4. That is relevant to the "differences point the right way but do not match" message.

### W3. The rank-reversal finding (third headline claim) has no uncertainty (Abstract; Section 1 bullet 3; Section 5.4, pp. 8–9; Table 4)

Table 4's proximity, recognition and D values in CLIP/CSD are reported without intervals, and the abstract states that the readouts "therefore rank the configurations differently." I ran a paired scene bootstrap (2,000 resamples of the 14 scenes; unadjusted).

**Robust:**
- GPT Image 2 is the most recognizable in CLIP (P(best) = 0.98). Its CLIP recognition exceeds Nano Banana 2's by +17.0 pp [8.9, 25.9], and it is never the largest-gain configuration.
- FLUX.2 Max is less recognizable than Flare, Sunburst and Nano Banana 2 in both encoders:
  - CLIP: Flare +18.8 pp [8.0, 31.2]; Nano Banana 2 +10.7 [4.5, 17.0].
  - CSD: Flare +23.2 [14.3, 33.9]; Nano Banana 2 +11.6 [5.4, 18.8].
- FLUX's lower 31-feature D than Flare and Sunburst is resolved in the prespecified family. The FLUX-vs-Flare/Sunburst reversal is therefore well supported.

**Not resolved:**
- Nano Banana 2's CLIP gain lead over GPT Image 2: 0.013 [−0.002, 0.033].
- The largest CSD proximity gain: P(best) is 0.26 / 0.27 / 0.34 / 0.13 for GPT Image 1, Sunburst, FLUX and Nano Banana 2. GPT Image 1 and FLUX both print 0.217, and only one is bold.
- FLUX's lowest CSD D: vs. GPT Image 1 −0.022 [−0.136, 0.096]; P(best) = 0.49.
- FLUX's lowest 31-feature D vs. Nano Banana 2: the prespecified interval [−0.847, 1.464].

The qualitative claim likely survives. As stated, though, it rests on point estimates and names specific orderings ("the configuration with the largest proximity gain", "the lowest error") that are not resolved.

### W4. Prespecified secondary analyses are not reported (Section 4.4, p. 6; Appendix C)

The protocol (`studies/painter_specificity_v1/PROTOCOL.md`, adopted unchanged by v2) prespecifies several analyses. They were run, and the results exist in `data/manifests/painter_specificity_v2/psv2-20260911/analysis.json`, but they are absent from the paper:

- **Stratified reference-work resampling (1,000 draws)** as sensitivity to the finite reference panel. The paper instead says "Intervals condition on the reference panels." The ranges are not small:
  - D: GPT Image 2 [0.976, 1.507]; Nano Banana 2 [0.961, 1.266]; FLUX.2 Max [0.693, 0.945].
  - β: Nano Banana 2 [0.342, 0.499]; FLUX.2 Max [0.369, 0.509].

  The β conclusion survives: all resampling lower bounds are above 0. It is unknown whether the two resolved pairwise contrasts survive.
- **Per-family estimates (color, spatial, texture, without texture).** The paper reports family-level shares only for SD-Turbo and then contrasts SD-Turbo's texture result with the overall pattern (Abstract; Section 5.5). In the main collection, the generic-baseline share in texture is 48.6% for GPT Image 1 (below a majority) and 60.1–79.8% for the others. Spatial shares range 59.6–95.1%. So "not in texture" is not specific to SD-Turbo, and the main-collection family breakdown is needed to interpret Section 5.5.
- **Paired scene bootstrap (5,000 draws)**, all leave-one-scene estimates, and the V-energy/trace-ratio diagnostics.

These do not all need to be in the main text. A paper that relies on prespecification should still say which prespecified analyses were run and where their results are, and report at least the reference-resampling and family results.

### W5. Plug-in H is biased upward by finite reference sampling (Section 4.1; Section 5.2)

Generated-image magnitudes are carefully repeat-corrected, but H = Σ‖r̂_a‖² is a plug-in over reference means from 105–297 works per painter. From the per-painter covariances of the standardized reference vectors, E[Ĥ] − H ≈ 0.40 (≈ 6.7% of 5.915). That biases β, Q, N/H and B/H downward by about 7%. For example, "GPT Image 2 matches the reference amplitude almost exactly, β = 0.999" corresponds to β ≈ 1.07 with a bias-corrected H. Both are within the interval, so this is a precision issue, not a reversal. A split-half cross-product estimate of H is easy and consistent with the paper's own logic, and the `pooled_real` control above is effectively that split.

### W6. Deletion ranges look like intervals but understate uncertainty (Table 1; Table 5; Section 5.1)

Table 1's "deletion range" brackets (e.g. [70.4, 72.3]) sit next to point estimates and will be read as intervals. The scene-jackknife standard errors of the generic-baseline shares are 1.9–4.4 pp, so approximate 95% intervals are ±4–9 pp, roughly 2–4 times the printed ranges. Section 4.4 and Appendix G correctly say these are sensitivity, not uncertainty. A table caption or a jackknife/bootstrap SE would prevent misreading.

### W7. Configuration identity and provenance (Section 3 "Generators"; Appendix A)

The predecessor attempt's records (`studies/painter_specificity_v1/TERMINATION.md`, v2 `DECISION.md`) show the gateway returned HTTP 200 and an image for an invalid model identifier. The paper says labels are "requested configurations rather than verified checkpoints" but omits this negative-control result, and does not say whether the v2 routes were negative-controlled.

I checked distinguishability. For every pair of configurations the noise-corrected squared difference of cell means is clearly positive. The closest pair, Flare vs Sunburst, gives t ≈ 6.7 in the 31 features and t ≈ 11.5 in CLIP (paired over scenes). This largely allays the concern that two labels are the same model. The paper should report this check and the earlier negative control.

### W8. Wording that goes beyond the evidence (minor)

- **"The weak or reversed Monet–Sisley response in the 31 features is therefore a property of that representation, not evidence that the generators cannot distinguish these painters" (Section 5.3, p. 8).** What is shown is that the two representations disagree on this pair with the same references. "Of that representation" should be "of the 31-feature representation of these references"; the "therefore" is stronger than a single-pair contrast between related representations supports.
- **"it dominates proximity gain in every configuration and representation we examined" (Section 6, p. 10).** CSD GPT Image 2 is 54.2%, and W1 shows these fractions are close to the perfect-agreement values.
- **"so the prompted names are more separable within each generator's own outputs than with respect to the historical references" (Section 5.4, p. 9).** The G rule is a supervised in-distribution classifier; B is a zero-shot cross-domain rule. The comparison is expected, and the "so" implies more than it shows.
- **Squared units.** "1.4–5.3 times as large as the entire spread" (Abstract) is in squared units (1.2–2.3 in linear units). Say "squared" in the abstract.

### W9. Factual error in Appendix A (pp. 14–15)

"If both repeats of every cell shared an error component with a common fraction ρ of the noise power, the estimated error of each configuration would be biased **downward** by an amount proportional to its observed repeat disagreement."

A positive shared error component makes E⟨d₁ − r, d₂ − r⟩ = ‖θ − r‖² + ρ·tr Σ. The cross-repeat D is biased **upward**, and the correction lowers it. The repeat-covariance analysis (`painter_repeat_covariance_v1`) does exactly this: adjusted D = D − ρq/(1−ρ). The numbers (crossings at 0.251 and 0.246) are right; the sentence states the direction backwards.

### W10. Clarity (minor)

The notation load is high: G, N, I, C, B, H, β, Q, D, D_agg, V_scene, plus "shared", "shared share", "shared part of gain" and "shared share of change". Table 3's two "shared" columns are easy to confuse. "Shared share" is awkward; "shared fraction" would read better. Eq. (2) uses the word "shared" as a variable before C/N are introduced. The abstract does not say which findings are prespecified. The lead generic-baseline split was added after collection (Section 4.4), which should be visible where the number first appears.

## 4. Requested changes

**Critical (must change for acceptance; none requires new data collection)**

1. **Add reference-based benchmarks for the headline quantities, and reframe the abstract, Section 1 bullets and Section 6 accordingly.**
   - (a) Report, per configuration and representation, the perfect-agreement shared component 4‖μ̄ − ḡ_generic‖²/H, the corresponding shared share, and the perfect-agreement shared part of prototype gain. Add a content-matched version using the Table 11 class targets.
   - (b) Split N into its component along (μ̄ − generic) and the orthogonal remainder.
   - (c) Report the real-painting D control already in `painter_specificity_review_v1/analysis.json` next to Table 2.
   - (d) Delete or qualify "Our data cannot say how large that appropriate part is."

   My recomputation shows the observed shared fractions are at or below perfect-agreement values (31 features: 66.7–88.4% observed vs 84.8–95.2%; CLIP/CSD prototype gain within a few points of the perfect-agreement values). The abstract should not present the shared fraction as though a large value indicated a generator deficiency.
2. **Attach uncertainty to the rank-reversal claims (Table 4, Section 5.4, Abstract, Section 1 bullet 3)**, e.g. paired scene-bootstrap intervals for between-configuration differences in proximity gain, recognition and D in each representation. Restate the claim around the reversals that are resolved. FLUX.2 Max vs Flare/Sunburst is well supported: lower prespecified D and 18–23 pp lower recognition in both encoders. Drop or qualify unresolved orderings: CLIP largest gain, CSD largest gain, CSD lowest D.
3. **Report the prespecified secondary analyses, or list them with pointers.** At minimum:
   - reference-resampling ranges for β, D and the 15 pairwise differences, stating whether the two resolved contrasts survive;
   - main-collection per-family shares, β and D.

   Revise Section 5.5 and the abstract's "but not in texture features" in light of the main-collection texture results (GPT Image 1: 48.6% shared).

**Minor**

4. Fix the direction of the repeat-dependence bias in Appendix A (W9).
5. Estimate H without finite-reference bias (split-half cross product), or report the ≈7% plug-in bias and its effect on β, Q, N/H and B/H. Temper "matches the reference amplitude almost exactly."
6. Replace or supplement scene-deletion ranges with jackknife/bootstrap SEs for the shares (Tables 1, 3, 5), or relabel the bracket column so it is not read as an interval.
7. State in Section 5.2 that three configurations have nominal D intervals entirely above 1.
8. Disclose the predecessor invalid-model-ID negative control, state whether the v2 routes were negative-controlled, and add the configuration-distinguishability check.
9. Temper the wording flagged in W8, and say "squared" in the abstract's H comparison.
10. Mark prespecified vs retrospective results in the abstract/introduction bullets.
11. Table 4: GPT Image 1 and FLUX.2 Max both print 0.217 in CSD proximity (0.21672 vs 0.21666) and only one is bold. Bold both or print more digits.
12. Simplify terminology ("shared fraction"), and make Table 3's two "shared" column groups visually distinct.
13. Consider releasing the 512-pixel normalized images (or hashes plus a retrieval path) so the feature extraction, not just the post-extraction analysis, can be replayed. Appendix H correctly states the current limit.

## 5. Criterion 1 — Claims and evidence: **partially**

Every reported number I checked is accurate and reproducible from the retained measurements. The prespecified claims are supported: all six β simultaneous intervals are above zero, and two pairwise D contrasts are resolved. The descriptive magnitudes are also supported. The gaps are interpretive and inferential:

- The lead finding and Section 6 omit a benchmark that the paper's own reference target provides. That benchmark shows the observed shared fractions are no higher than perfect agreement would produce (W1).
- A computed real-painting control that changes how D should be read is omitted (W2).
- The rank-reversal claim has no uncertainty (W3).
- Prespecified sensitivity analyses bearing on the reference conditioning and on the texture contrast are not reported (W4).

All of these can be closed with the retained data and narrower wording.

## 6. Criterion 2 — Audience and clarity: **yes**

The question matters to people who evaluate style prompting, mimicry, protection or erasure, and the recommendation to add a generic-style control is actionable. The writing is precise and compact, and every quantity is defined. It is dense (W10), and some wording needs tempering (W8), but a TMLR reader can follow the argument and check it.

## 7. Desk-rejection risk: **low**

It is in scope for TMLR (evaluation methodology for generative models). It uses the TMLR template with unmodified style files per the check script, is anonymized, and includes broader-impact and reproducibility statements. The prose is terse but careful, internally consistent and backed by a verifiable replay pipeline. It does not read as low-care machine-generated text. The AI-assisted source audit is disclosed.

## 8. Recommendation: **major revision**

The core methodological contribution is sound and the numbers are accurate. However, the headline interpretation needs rework: the missing benchmark, the omitted real-painting control and the ranking claims without uncertainty, together with the prespecified analyses to report. That goes beyond minor edits, although it needs no new experiments. I expect a revised version to be acceptable.

## 9. Confidence: **4 / 5**

I reproduced the central tables independently from raw retained vectors. I did not re-extract features from pixels (images are not supplied), did not inspect the SD-Turbo feature file (outside the permitted paths; checked Table 5 for internal consistency only), and did not verify the related-work characterizations against the cited papers.

## 10. Numbers verified and how

All recomputations used my own scripts (numpy/scipy) reading raw retained files. I did not import project analysis code. The 31-feature standardization used the freeze-bound scaler (`scaler.json`, SHA-256 `71f51123…97b9`, matching the freeze binding).

1. **`uv run --locked python paper/tmlr/build_assets.py --check`** → "ok: 12 generated files and 78 claims" (inputs hash-verified; prose claims equal source outputs).
2. **H = 5.915** — from the 649 reference vectors (297/106/141/105) in `reference_windows.jsonl` after standardization.
3. **Table 1, all six rows** — G, N, I, B (/H), shares vs free and vs generic, and 14-scene deletion ranges, recomputed from `measurements.jsonl` + `requests.jsonl`. Examples: GPT Image 1 5.04 / 5.26 / −0.29 / 2.12, 82.5%, 71.3%, [70.4, 72.3]; FLUX.2 Max 3.78 / 5.34 / 6.53 / 0.70, 95.7%, 88.4%, [86.1, 90.2]. Identity C = G + N + I holds.
4. **Within-scene artist-free shares 88.6–97.2%** (Section 5.1).
5. **Table 2, all six rows** — β, Bonferroni simultaneous intervals with t_{13,1−0.05/42}, Q, D, D_agg. Example: GPT Image 2 0.999 [0.893, 1.104], 2.223, 1.226, 1.044. D = 1 − 2β + Q checked.
6. **FLUX.2 Max unadjusted D interval [0.586, 1.016]** (t_{13,0.975}).
7. **Table 8** — all 15 pairwise D differences and simultaneous intervals; only Flare–FLUX [0.256, 1.618] and Sunburst–FLUX [0.058, 1.623] exclude 0.
8. **Table 9** — V_scene, β/√Q, fitted-scalar ranges and held-out D (GPT Image 2 0.554, FLUX.2 Max 0.714), with a leave-one-scene refit of c = max(0, β/Q).
9. **Monet–Sisley β in the 31 features** −0.249 to 0.129 (five configurations) and 0.402 (GPT Image 2). **Omit-Cézanne β** 0.096 (FLUX) and 0.651 (GPT Image 2).
10. **Tables 3 and 4** — recomputed from `embeddings_clip.npz` / `embeddings_csd.npz` using the row manifest in `inputs.json`: prototype gains, shared part of gain (73.2–83.8% CLIP; 54.2–79.7% CSD), N/(N+B) in embeddings (76.1–82.3%; 68.8–77.4%), recognition (e.g. GPT Image 2 68.8% / 75.9%, FLUX.2 Max 41.1% / 39.3%), D in each encoder (GPT Image 1 CLIP 0.847, FLUX CSD 0.714), and Monet–Sisley β (0.299–0.532; 0.323–0.587). Eq. 4 identity verified to 1e-10.
11. **Development-panel recognition** 79.8% (CLIP) and 79.6% (CSD).
12. **Table 12, all 12 rows** — held-scene B/T/G recognition. Mean changes +2.7 / +16.1 (CLIP) and +10.0 / +25.0 (CSD). FLUX CSD translation "corrects 39 and harms 9."
13. **FLUX.2 Max keeps the lowest D under each of the 14 single-scene deletions** (Section 5.6).
14. **Table 5 (SD-Turbo)** — internal consistency against `painter_cross_cohort_v1/analysis.json`: share = C/(C+L) in all four families; family H values (2.126 + 1.498 + 2.291) sum to 5.915; β 0.618, D 0.917, scene-wise D 1.637. Raw SD-Turbo features were not recomputed.
15. **Reference singular-value shares 66.3 / 20.6 / 13.0%** (Table 10 caption), and **simulation coverages 96.0 / 97.4 / 99.7 / 0.04%** — read from `painter_specificity_review_v1/analysis.json`.
16. **Repeat-covariance direction** — from `painter_repeat_covariance_v1/analysis.json` and its source: adjusted D = D − ρq/(1−ρ), establishing the W9 error.
17. **Additional computations supporting the requested changes (not in the paper):**
    - perfect-agreement shared shares and prototype-gain fractions (W1);
    - real-painting D controls (W2);
    - scene-bootstrap reversal intervals (W3);
    - main-collection family shares (W4);
    - H plug-in bias ≈ 0.40 (W5);
    - jackknife SEs 1.9–4.4 pp (W6);
    - configuration distinguishability (W7).
