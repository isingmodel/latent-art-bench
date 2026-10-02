# TMLR review: methods (statistics, claims and evidence, reproducibility)

**Submission:** "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation" (anonymous)
**PDF read:** `reports/tmlr_review_v1/round_02/input/manuscript.pdf`, 23 pages, SHA-256 `2837299e02bca86a872f392d19e4e5a74ee72944be0c79441b89eea7deb446d6`
**Recommendation:** minor revision. **Confidence:** 4/5

---

## 1. Summary of the submission

The paper asks what adding an artist name to a text-to-image prompt contributes beyond a generic painting instruction. It also asks whether the usual "proximity gain" readout (named images become more similar to the artist's works) measures painter specificity. The design renders 14 authored outdoor scenes under six clauses: artist-free, a generic "Render as an oil painting.", and the same clause "in the style of" Monet, Sisley, Pissarro or Cézanne. There are two independent repeats per cell, across six commercial configurations (four OpenAI GPT Image variants, Nano Banana 2 and FLUX.2 Max), for 1,008 images. Images are measured with 31 hand-crafted color, spatial and texture features, and with CLIP ViT-L/14 and CSD embeddings.

The methodological core is simple and correct:

* The four named-minus-generic shifts are split into a shared component c (their mean) and between-name departures e_a. Squared sizes N = 4⟨c₁,c₂⟩ and B = Σ⟨e_a1,e_a2⟩ come from cross-repeat products, the cross-validated distance of RSA, so they are unbiased for the squared means under independent repeat noise.
* The shared fraction N/(N+B) is compared with an exchangeable null (25%) and a "faithful imitator" value N*/(N*+H). The faithful value is what one would observe if each named mean sat exactly on the painter's reference mean, starting from the observed generic outputs.
* In an embedding, the mean named-minus-generic gain in similarity to the prompted painter's prototype decomposes exactly into a name-independent term (ḡ−g_g)ᵀμ̄ plus Hβ/4 (Eq. 4). β is the aligned amplitude of the between-name differences along the reference painter differences.
* Agreement with the reference differences is scored with β and a repeat-corrected error D = 1 − 2β + Q. Six β values and 15 pairwise D differences form a prespecified family with Bonferroni paired-scene t intervals, and the protocol also prescribed reference-work resampling.

Main findings:

* 66.7–88.4% of the named change is shared in the 31 features, against 84.8–95.2% for the faithful imitator.
* The shared term supplies 73.2–83.8% (CLIP) and 54.2–79.7% (CSD) of the proximity gain, against faithful values of 71.3–82.9% and 48.3–75.7%.
* All six β are positive (0.44–1.00), with uneven painter-pair structure.
* Proximity, recognition and D pick different "best" configurations.
* Only 2 of the 15 prespecified D contrasts are resolved.
* A retrospective SD-Turbo collection (2,000 images) is majority-shared overall but not in texture.

The paper recommends reporting between-name comparisons and a faithful-imitation reference next to any proximity score.

**Contributions as I see them:**

1. A clean, exactly additive decomposition that separates the name-independent part of proximity gain from the painter-specific part, with noise-corrected magnitudes.
2. Explicit reference points for interpreting shared fractions.
3. A careful, prespecified comparison of six configurations with honest reporting of how little is statistically resolved.
4. An unusually complete evidence trail: hash-bound analysis outputs and a script that regenerates every table and figure and checks every quoted number.

## 2. Strengths

* **The estimators are correct, and the paper reports the numbers it computed.** I recomputed the main quantities from the raw retained vectors, independently of the authors' analysis modules (Section 9). All of them match to the printed precision: H, N, B, G, I, N_free, shared fractions, faithful fractions, cos(c,t), λ, β, Q, D, D_agg, the centroid-proximity split, all 15 simultaneous intervals, the β simultaneous intervals, FLUX.2 Max's nominal D interval, the reference-resampling intervals, and the CLIP/CSD proximity, recognition, D and Monet–Sisley values. `build_assets.py --check` passes (16 generated files, 102 registered claims), and every registered claim literal appears in the frozen PDF text.
* **The algebra is right.** I re-derived Eq. 4/8 (exact under Σr_a = Σd_a = 0), Eq. 6 (centroid-proximity split), Eq. 7 (D = D_agg + V_scene), the finite-sample bias of H ((3/4)Σ tr Σ_a/n_a), and the identity D = 1 − 2β + Q. The printed tables satisfy these identities internally. For example, Q − B/H = V_scene holds for every configuration, and N*/H = (N/H)·cos²/λ² reproduces the faithful column of Table 1.
* **Inferential status is labelled honestly.** Section 4.5 states which analyses were prespecified and that everything else is retrospective. It also discloses that some benchmark values were first computed during internal review. This matches the v1/v2 protocols and the diagnostics plan I inspected.
* **Negative and inconvenient results are reported.** Only 2/15 contrasts are resolved. The orderings change under aggregation and rescaling (Table 13). The repeat-dependence sensitivity reverses NB2/FLUX at ρ = 0.251. The simulation shows 0.04% coverage under a configuration-level shared state.
* **The sensitivity program is thoughtful.** It covers content-matched targets, square windows, AI-audited crops with and without refitting the scaler, alternative weightings, leave-one-feature-out, a finite-sample H correction and a genuine-painting control for D.
* **The scope statements are appropriate.** Labels denote requested configurations, not verified checkpoints. There is no human perception claim, and the paper says the intervention identifies prompt-condition differences, not causes.

## 3. Weaknesses (with locations)

**W1. The headline "texture is the least shared family" is not true per configuration** (Intro bullet 5, p. 2; §5.5 heading and text, p. 10; Table 6, p. 11). By Table 6:

| Configuration | Least shared family | Note |
| --- | --- | --- |
| GPT Image 1, Flare, FLUX.2 Max | texture | as claimed |
| GPT Image 2 | spatial (59.6%) | texture is 73.8% |
| Sunburst | spatial (61.5%) | texture is 70.3% |
| Nano Banana 2 | color (56.8%) | texture is the most shared family, at 79.8% |

The statement holds only for the ranges' minima and maxima, for the six-configuration mean (texture about 68.2% against about 71.5% spatial and 74.3% color), and for SD-Turbo. This is an editing fix, but it is currently a factual overstatement in a headline bullet.

**W2. The headline shared fractions carry no uncertainty statement adequate to the comparisons drawn** (Table 1 and §5.1, p. 7; Figure 3 caption, p. 8).

* **The deletion ranges understate uncertainty.** The only spread shown is the range over 14 leave-one-scene-out estimates. Such ranges are about √(n−1) times narrower than a jackknife standard error would imply. They are presented as robustness ("deleting any one scene keeps it within 65.9–90.2%"). I computed jackknife SEs of 1.9–4.4 points, and paired scene-bootstrap 95% percentile intervals of, for example:
  * FLUX.2 Max: 77.6–94.2% (deletion range 86.1–90.2%)
  * Nano Banana 2: 51.3–75.5% (deletion range 66.8–70.9%)
* **FLUX.2 Max's "below faithful" is not established.** For FLUX.2 Max in the 31 features, the observed shared fraction (88.4%) is only 2.0 points below the faithful value (90.4%). In my scene bootstrap, faithful − observed was ≤ 0 in 14.8% of resamples (95% interval −0.020 to 0.082). The statements "more than every configuration" (§5.1) and "The observed fraction is below the faithful value in every configuration and representation" (Figure 3) are therefore not established for FLUX.2 Max. The larger conclusions (≫25%, and faithful ≫ observed for the other five) are unaffected.

**W3. The faithful-imitation benchmark confounds painter geometry with the reproduction/generation domain gap, and the abstract's generalization rests on it** (Abstract lines 2–4, p. 1; §4.2, p. 6; Table 2, p. 8; §7 Scope).

* **Why it confounds.** The faithful fraction N*/(N*+H) is large because the generic outputs are far from photographed paintings (N*/H ≈ 5.5–19.5). That distance includes capture, varnish, aspect ratio and resolution differences and content mismatch, not only style. The paper acknowledges this ("a reference point, not an attainable target"). Even so, the abstract states as a finding that proximity gain would be mostly shared "for a generator that reproduced each painter exactly."
* **One of 12 cells contradicts it.** In CSD for GPT Image 2, the faithful proximity share is 48.3%, a minority, so the claim fails there as worded.
* **A domain-gap-free benchmark exists and helps the authors.** Keep each configuration's observed shared term and replace its between-name differences by the exact reference differences. The shared share of proximity gain is then S_obs/(S_obs + H/4). I computed it from the retained embeddings: 60.6–73.0% (CLIP) and 52.5–67.4% (CSD), all above 50%. In the 31 features, N/(N+H) is 57.6–84.2%. This benchmark supports the paper's claim more robustly than the faithful one. It should be reported, and the general condition stated: the shared term dominates iff the observed (or imitated) centroid movement exceeds H/4.

**W4. "Movement toward the four painters' common appearance" is not identified** (§5.1 last sentences of paragraph 1; §6 "What the shared change is", p. 11). A positive cosine between c and t = μ̄ − z̄_g is expected for any shift from generated images toward photographed oil paintings in general. For NB2 and FLUX, 53–55% of N lies along the painting-instruction direction g. The t and g components are also not additive, so presenting them as "two things" that contribute is loose. The paper concedes in the same paragraph that the design cannot separate painter-directed from generic-artist effects. The first sentence should be worded as "toward the centroid of these reproductions", not "toward the four painters' common appearance". A reference centroid of unrelated painters, or a non-Impressionist name clause, would be needed to claim more.

**W5. Omitted prespecified sensitivity analyses: some prespecified family-level results are not reported** (§5.6, p. 11; Appendix D, Table 15).

* **What the protocol required.** The v1 protocol (inherited by v2) prespecified β and D "separately by color (11), spatial structure (8), texture (12), and without texture (19)" as descriptive sensitivity analyses. These results exist in `data/manifests/painter_specificity_v2/psv2-20260911/analysis.json` ("sensitivities") but do not appear in the paper.
* **Why the omission matters.** §5.6 lists every sensitivity under which FLUX.2 Max keeps the lowest D. In the prespecified texture family it does not: Nano Banana 2 has 0.886 against FLUX.2 Max's 0.906. FLUX.2 Max is lowest in color, spatial and without-texture. The omission is small in consequence but reads as selective reporting of sensitivity analyses, so the four family rows should be added to Table 15.

**W6. Painter-pair and cross-representation statements carry no uncertainty** (§5.3 paragraph 3, p. 9; Figure 4; Table 14).

* **What is claimed.** The claims include that "Monet–Sisley alignment ranges from −0.249 to 0.129 in five configurations" in the 31 features, and that the pattern "does not transfer to the embeddings".
* **How uncertain the pair values are.** My scene-bootstrap and within-painter reference-resampling intervals for the 31-feature Monet–Sisley β are wide. For example:
  * Sunburst: −0.249, scene [−0.36, −0.14], reference [−0.45, 0.21]
  * FLUX.2 Max: 0.129, scene [−0.07, 0.34], reference [−0.01, 0.22]
  * GPT Image 2: 0.402, scene [0.24, 0.57], reference [0.15, 0.65]
* **What to change.** The qualitative "uneven" conclusion probably survives, but pair-level and cross-representation contrasts need intervals, or a statement that they are point descriptions.

**W7. Precision of the proximity readout's definition** (§4.4, Tables 2 and 4, Appendix E). The main text calls the readout "gain in cosine similarity to the prompted painter's prototype". The computed quantity is the mean image-to-reference cosine, because μ_a is the unnormalized mean of unit embeddings, while recognition uses the normalized u_a. This is immaterial numerically. I recomputed with normalized prototypes, and the shared shares moved by at most 0.5 points (CLIP 73.4–83.9%, CSD 54.7–79.6%). It should still be stated precisely, and the identity's validity for any linear score noted. Relatedly, §5.2 says "the observed shares are only a few points higher" than faithful. For GPT Image 2 in CLIP the observed value is lower (73.2 against 76.0), and the CSD gaps reach 6.6 points.

**W8. Scope of the abstract's first sentence** (p. 1). "We show that, for related painters, …" generalizes from one quartet of painters, one clause template and 14 authored scenes. §7 scopes this correctly; the abstract should match it ("for four related Impressionist-era painters").

**W9. Minor methodological clarity issues.**

* §4.5 and Appendix C say the intervals "describe these 14 scenes rather than fresh requests" and "include differences between scenes". It would be clearer to say that for the fixed-panel estimand they are conservative (they include scene × configuration heterogeneity). They are not justified for a scene population, because the scenes were authored rather than sampled.
* Neither the scene interval nor the reference-resampling interval for D combines both sources of variation. The intro claim "only when the reference works are resampled" is correctly worded, but a two-way (scene × reference) bootstrap would settle the FLUX.2 Max-below-1 statement.
* The v2 reduction from 16 to 14 scenes, made for cost before any outcome, and the terminated v1 attempt are not mentioned. One sentence would complete the preregistration narrative.
* The 0.04%-coverage scenario (a configuration-level state shared by all requests) deserves one interpretive sentence. It concerns generalization over time or service state, not the fixed-collection estimand.
* Table 11's centroid-proximity units (squared standardized units, not /H) are not stated.

**W10. Reproducibility gap at the pixel level** (§7, Reproducibility statement). Features, embeddings, request records and analysis outputs are supplied, and replay is exact. The 1,008 generated images are withheld "because of the archive's size limit", so feature extraction cannot be audited. Two of the six configurations are codename-like variants that may not stay available. Releasing the images through an anonymous external host, or at least committing to release on acceptance, would close this.

## 4. Requested changes

**Critical (must change for acceptance; all can be done with retained data and text edits):**

1. **Correct the texture claim.** Rewrite the Intro bullet 5 and the §5.5 heading and text. Texture is the least shared family in 3 of 6 configurations (GPT Image 1, Flare, FLUX.2 Max) and in SD-Turbo. Spatial is lowest for GPT Image 2 and Sunburst, and texture is the most shared family for Nano Banana 2.
2. **Replace deletion ranges as the only spread for the headline fractions.** Add scene-bootstrap (or jackknife) intervals for the observed shared fractions, the faithful fractions and their difference, in Table 1/Figure 3 and Table 2. Qualify "a faithful imitator would share more" and the Figure 3 caption for FLUX.2 Max in the 31 features: in my paired bootstrap the difference is unresolved (about 15% of resamples reverse it). State explicitly that deletion ranges are sensitivity, not uncertainty.
3. **Narrow the abstract's claim that proximity gain would be mostly shared for an exact imitator.** Note the CSD GPT Image 2 faithful value of 48.3%. Add the domain-gap-free benchmark (observed shared term + exact reference differences: S_obs/(S_obs+H/4) in the embeddings and N/(N+H) in the features), and state the general condition under which the shared term dominates.
4. **Report the prespecified family-level β and D sensitivity (color, spatial, texture, without texture).** Revise the §5.6 list of analyses under which FLUX.2 Max keeps the lowest D to note that it does not in texture (NB2 0.886 against FLUX.2 Max 0.906).
5. **Reword the unidentified interpretation.** Replace "movement toward the four painters' common appearance" (§6) and similar phrasing with "movement toward the centroid of these reproductions", which is what the data identify. Match the abstract's first sentence to the four-painter, single-template scope.

**Minor:**

1. Define the proximity readout precisely (mean image-to-reference cosine with unnormalized μ_a) and distinguish it from the normalized prototypes used for recognition. Note that the Eq. 4 identity holds for any linear score, and that normalized prototypes give essentially the same shares.
2. Fix §5.2 "only a few points higher": the observed–faithful gaps are −2.8 to +6.6 points.
3. Add intervals, or an explicit "point description" label, to the painter-pair β/D (Figure 4, Table 14) and to the 31-feature against embedding Monet–Sisley contrast.
4. Consider a two-way (scene × reference) bootstrap for D relative to 1, and a combined interval for the FLUX.2 Max D.
5. Clarify the interval estimand wording (fixed panel against scene population). Add one sentence interpreting the 0.04% shared-state coverage.
6. Mention the pre-outcome 16→14 scene reduction and the terminated v1 attempt in §4.5 or Appendix A.
7. §6: note that the "toward centroid" and "along generic" components overlap (cos² shares of N are not additive).
8. State the units of the centroid-proximity gain in Table 11.
9. Report per-painter (not only name-averaged) proximity splits in an appendix. Single-artist evaluations, the common practice the paper addresses, face additional cross terms that cancel only in the average.
10. Release the generated images (anonymized host) or commit to release, so features can be re-extracted.
11. When correcting H for its 6.7% finite-sample bias, report the implied Q and D alongside the rescaled β.
12. Consider trimming the density of numbers in running text (§5.3–5.4). The findings are clear, but the prose is heavy for readers outside the subarea.

## 5. TMLR criterion 1: claims and evidence

**Answer: partially.**

**What holds.** The reported numbers are accurate and reproducible; I found no discrepancy between printed values and underlying outputs. The core methodological claim is exactly supported by Eq. 4 and the observed shares (54–84% of proximity gain is name-independent in every configuration and encoder). Proximity gain alone therefore cannot establish painter specificity, and the prespecified results (all β > 0; only Flare/Sunburst > FLUX.2 Max resolved in D) are correctly stated.

**Where the claims go beyond the evidence.**

* The texture headline is false as a per-configuration statement (W1).
* "A faithful imitator would share more" is not established for FLUX.2 Max in the 31 features, because the only uncertainty shown (deletion ranges) understates scene variability (W2).
* The abstract's "would remain true for a generator that reproduced each painter exactly" rests on a benchmark that includes the domain gap and fails in one of 12 cells (W3). A domain-gap-free benchmark I computed from the retained data supports a suitably worded version.
* "Toward the four painters' common appearance" is not identified by the design (W4).
* Prespecified family sensitivity results were omitted, including one where the reported "FLUX.2 Max keeps the lowest D" fails (W5).

All five can be closed by narrowing the text and adding analyses on the existing data. None requires new images.

## 6. TMLR criterion 2: audience and clarity

**Answer: yes.**

**Audience.** Researchers evaluating style imitation, style protection or erasure, and text-to-image conditioning will find the decomposition and the "report a reference point next to proximity" recommendation useful. The approach transfers to any evaluation that averages a linear similarity over a set of related prompts.

**Clarity.** The paper is organized logically, and Figure 1 and Table 9 give readers a way into the notation. Estimators and inferential status are stated precisely. The prose is dense with numbers and the readouts are many, but the main findings are communicated clearly. The clarity issues (W7, W9) are local.

## 7. Desk-rejection screen

**Risk: low.**

* **Scope and format.** It is in scope (ML evaluation methodology for generative models). It uses the TMLR template, is anonymized, and includes broader-impact and reproducibility statements.
* **Quality.** Quality is high. The analysis replays exactly, and the text reflects care: explicit prespecification status and honest reporting of unresolved contrasts.
* **Machine-generated appearance.** AI assistance is disclosed. The writing is terse and numerically dense in a way an action editor might notice, but it does not read as low-care machine output, and every number I checked is correct.

## 8. Recommendation and confidence

**Minor revision. Confidence 4/5.** The science is sound and unusually well documented. The requested changes are corrections and narrowing of several headline statements, plus a few analyses computable from the retained vectors (uncertainty for the shared fractions, a domain-gap-free benchmark, the omitted prespecified family sensitivities). If the texture claim, the FLUX.2 Max faithful comparison and the abstract's generalization were left as written, I would consider the claims–evidence criterion unmet.

## 9. Numbers verified, and how

**Checks:**

* `uv run --locked python paper/tmlr/build_assets.py --check` returned `ok: 16 generated files and 102 claims`: input hashes verified, generated tables and figures byte-identical, and registered claims equal their computed values.
* I compared `--print-claims` output (103 computed claims) against the PDF text extraction. Every literal occurs in the frozen PDF; the only apparent misses were a line-broken range (0.474–1.071) and one value (repeat noise 0.42–2.60) that appears in Table 11 rather than prose.

**Independent recomputation.** My own script (scratchpad `recompute.py`) did not use the authors' analysis modules. It read `measurements.jsonl` + `requests.jsonl` (1,008 measured), `confirmation_features.jsonl` (649 measured: 297/106/141/105) and `scaler.json`, applied the (x − center)/scale transform, and reproduced:

* H = 5.915; H finite-sample bias 6.7% (0.0675).
* Table 1, all six rows: shared fraction (71.3, 70.9, 71.1, 66.7, 69.1, 88.4), leave-one-scene ranges, faithful (95.2, 89.3, 84.8, 86.9, 92.5, 90.4), cos(c,t) (0.85, 0.66, 0.57, 0.72, 0.75, 0.86), λ, along-generic share (0.1, 0.9, 6.6, 22.0, 55.5, 52.8) and B/H.
* Table 10: G, N, I, N_free, B /H and the vs.-free, vs.-generic and within-scene shares.
* Table 11: centroid gain total, shared and between for all six (e.g., GPT Image 1 17.490 = 17.844 − 0.354).
* Table 3: β, Q, D for all six and the β simultaneous intervals, with t_{13,1−0.05/42} = 3.760. FLUX.2 Max nominal D interval [0.586, 1.016].
* Table 12: all 15 D differences and simultaneous intervals, with the two resolved pairs (Flare and Sunburst against FLUX.2 Max).
* Table 13: D_agg.
* The identity D = 1 − 2β + Q to 1e-9.
* Reference-resampling intervals: my own 1,000-draw within-painter bootstrap gave FLUX.2 Max D [0.695, 0.944] and β [0.369, 0.510], against the reported [0.693, 0.945] and [0.369, 0.509]. The other five agree within Monte Carlo error.
* FLUX.2 Max has the lowest D in all 14 leave-one-scene deletions.
* Text quantities: B root-mean-square ratio 0.78–1.45, N root-mean-square ratio 1.17–2.31, and the corrected-H β range 0.474–1.071.

**Embeddings.** A second script (`embed.py`) read `embeddings_{clip,csd}.npz` + `inputs.json` and reproduced:

* Table 2, all 24 cells (e.g., CLIP shared part of gain 74.5/73.2/78.8/77.7/83.8/81.7 with faithful 71.3/76.0/77.1/77.6/82.9/80.7; CSD 72.7/54.2/65.0/67.4/79.7/77.6 with faithful 70.4/48.3/62.7/65.4/75.7/71.0).
* Table 4 proximity gains, recognition macro accuracies and CLIP/CSD D.
* Table 14 CLIP/CSD Monet–Sisley β.
* Development-panel recognition of 79.8% (CLIP) and 79.6% (CSD).

**Derivations checked by hand from printed tables:**

* N*/H = (N/H)·cos²(c,t)/λ² reproduces the Table 1 faithful column (e.g., GPT Image 1: 5.26·0.85²/0.441² = 19.5, giving 95.1%).
* Q − B/H = V_scene for all six rows.
* The between-name centroid term equals H(β/2 − B/(4H)) (GPT Image 2 −0.06, FLUX.2 Max +0.35).
* Along-generic share = cos²(c,g).
* The Table 16 mean translation gains (+2.7 CLIP, +10.0 CSD), and FLUX.2 Max CSD +30/112 = +26.8 points.

**Additional analyses I ran (they support W2, W3, W6 and W7):**

* Scene-bootstrap 95% intervals and jackknife SEs for the shared fractions.
* Faithful − observed for FLUX.2 Max in the 31 features: reversed in 14.8% of scene resamples, interval [−0.020, 0.082].
* The domain-gap-free benchmark: CLIP 60.6–73.0%, CSD 52.5–67.4%, 31 features 57.6–84.2%.
* Monet–Sisley pair intervals.
* Normalized-prototype proximity shares, within 0.5 points of the reported ones.
* Embedding H finite-sample bias: 3.6% (CLIP) and 3.2% (CSD).

**Not independently recomputed:** SD-Turbo collection statistics, source-correction (crop and refit) values, recognition-transfer table beyond arithmetic checks, repeat-covariance crossings, and simulation coverages. These were verified only through `build_assets.py --check` against their hash-bound outputs.
