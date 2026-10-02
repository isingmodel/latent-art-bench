# TMLR review (methods): "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation"

Role: methods (statistics, claim–evidence fit, number provenance, reproducibility)
PDF read: `reports/tmlr_review_v1/round_03/input/manuscript.pdf`, 25 pages
PDF SHA-256: `7da8263c19eeb6ec1b3dc1c6292306712a7e5297e99f95009649c66c80299310`

## Summary of the submission

The paper asks what the usual artist-style "proximity gain" measures when the prompted painters are related. Six commercial text-to-image configurations (four OpenAI GPT Image variants, Nano Banana 2 and FLUX.2 Max) rendered 14 authored outdoor scenes under six clauses (artist-free, generic "oil painting", and each of Monet, Sisley, Pissarro and Cézanne), with two repeats per cell (1,008 images). Images are measured in 31 hand-crafted color, spatial and texture features (the prespecified primary representation), and in CLIP ViT-L/14 and CSD embeddings. The reference targets are 649 Wikimedia reproductions, and a separate 221-work panel sets the feature scaling.

Contributions:
1. A split of what the names add, relative to the generic clause, into a shared change `c` and between-name differences `e_a`. Squared sizes are estimated with cross-repeat products (N, B), and the split comes with two interpretable benchmarks: a *faithful imitator* (N*/(N*+H)) and an *exact-differences* generator (N/(N+H)).
2. An exact identity (Eq. 4 and 8) that splits embedding proximity gain into a label-independent shared term and a painter-specific term H·β/4.
3. Agreement scores for the between-name differences: aligned amplitude β, squared size Q, and error D = 1 − 2β + Q. These come with a prespecified 21-comparison inferential family, reference resampling and genuine-painting controls.
4. The empirical findings:
   - 66.7–88.4% of the named change is shared, against 84.8–95.2% for a faithful imitator and 57.6–84.2% with exact differences.
   - In embeddings, the shared term supplies 73.2–83.8% (CLIP) and 54.2–79.7% (CSD) of the proximity gain, close to faithful-imitator values.
   - All six β are positive. In the 31 features, three configurations have D above 1, and FLUX.2 Max has the lowest D.
   - Proximity, recognition and agreement favor different configurations.
   - The shared fraction varies by feature family.

The paper is explicit that everything beyond the prespecified family is post hoc on known images. It is also explicit that the intervals describe the 14 authored scenes and the finite reference panels.

## Strengths

- **A useful, correct decomposition.** Equation 4 is exact. I recomputed it from the retained CLIP and CSD embeddings and it holds to <3·10⁻¹⁶ for all 12 configuration–encoder pairs. It makes a clear, general point: when the shared movement toward related painters exceeds a quarter of their spread (H/4), proximity gain is dominated by a term that ignores which name produced which image. The exact-differences benchmark is a good device because it separates that point from the domain gap between renders and photographed paintings.
- **Sound estimators with clear assumptions.** Cross-repeat products remove the additive noise bias of squared sizes. Negative estimates are kept. The finite-sample bias of H is derived correctly (the (3/4)Σ tr Σ_a/n_a factor checks), and the effect of repeat dependence is analysed explicitly (crossing correlations; simulation coverage under violated assumptions).
- **Conservative, transparent inference.** The protocol fixed 6 β and 15 pairwise D differences with Bonferroni t intervals, and the paper reports that only 2 of 15 pairwise differences are resolved. Post hoc plans record which values were already known. Section 4.5 is unusually candid about the status of each analysis.
- **Broad sensitivity analysis.** It covers content-matched targets, cropped reference sources with and without scaler refit, family and covariance weightings, square windows, single-scene and single-feature deletion, scene and reference resampling, joint resampling, and an SD-Turbo cross-check.
- **Excellent number provenance.** Every table and figure is generated from hash-bound analysis outputs, and `build_assets.py --check` passes ("ok: 21 generated files and 106 claims"). Every number I recomputed from the retained vectors with my own code matched the manuscript (list below).
- **Candid limitations.** The limitations section is honest (related painters only, unverifiable closed checkpoints, no human evaluation, weak Monet–Sisley separability of the 31 features).

## Weaknesses

**W1. The genuine-painting control is inflated by an implementation detail that contradicts its description, and a main-text claim rests on it.** (Section 5.3, p. 9, second paragraph; Appendix D "Genuine-painting controls", p. 20; Section 6 "Recommendations", p. 12.)
- *What the paper says.* The control "supplies two works per painter for each of 14 pseudo-scenes".
- *What the code does.* The implementation (`painter_specificity_review_v1.real_controls`) draws the two pseudo-repeats with `rng.integers(...)`, that is, with replacement from each held-out half. The same painting can therefore fill both "repeats". A cross-repeat product of a work with itself is a squared norm, so these draws reintroduce exactly the within-painter variance that the cross-repeat design is meant to remove. The effect is largest for the content-class draws, where held-out class groups are as small as 8 works (Sisley, land), so duplicates are common.
- *Reproduction.* Running the paper's own function reproduces 0.234 / 0.753 / 0.731 exactly (pooled; class sampling with pooled target; class sampling with class targets).
- *With the draws corrected.* Changing only the pair draws to two distinct works gives means of **0.111 / 0.252 / 0.373**. Sampling without replacement from a finite set is unbiased for the population-level cross product. Sampling with replacement adds tr Σ/n_held.
- *Target noise.* The genuine controls also use targets estimated from the smaller half of each collection, or of each content class (4–48 works per class and painter). The generated images are scored against the full-collection target. So even the corrected control carries more target noise than the generated D.
- *Consequence.* The sentence "FLUX.2 Max's 0.801 is close to the content-sampled genuine level; the other configurations are not" is not supported. With distinct works, FLUX.2 Max is well above the genuine level. The recommendation to "compare D with genuine paintings sampled the same way" is sound in principle, but the control used here does not implement it.
- *Fixability.* This is a small reanalysis of retained data, not new evidence.

**W2. The headline "three configurations have larger errors than a generator that makes no painter distinctions" is specific to one representation, and part of it is fragile.** (Abstract; Section 1, bullet 3; Section 5.3.)
- *It holds only in the 31 features.* The paper's own Table 4 shows the picture changes in the embeddings:
  - In CLIP, five of six point estimates of D exceed 1. GPT Image 1, one of the "three", has the lowest CLIP D (0.847) and is best in 99.3% of scene resamples.
  - In CSD, all six are below 1 (0.714–0.999).
  - The abstract states the finding without the qualifier "in the 31 features". Its later clause, "agreement varies across … representations", does not make clear that this ranking inverts.
- *It is outside the prespecified family.* The protocol (`studies/painter_specificity_v2/PROTOCOL.md`) designates absolute D intervals as "descriptive nominal 95% summaries, not additional claims covered by that 21-comparison family". The paper labels them "unadjusted" in the Table 3 caption but uses them for a headline claim.
- *GPT Image 1's exceedance is fragile.* I recomputed the t intervals. With even a 6-way Bonferroni adjustment, GPT Image 1's interval is [0.935, 2.210] and includes 1. Flare [1.363, 2.113] and Sunburst [1.167, 2.116] remain above 1. The joint resampling (D < 1 in 0.7% of draws for GPT Image 1) supports the descriptive statement, but without multiplicity control.
- *Evidence of the 31 features themselves.* The 31 features classify genuine development works at only 49.8% macro accuracy (Monet 39.6%, Sisley 30.6%). A feature-specific D ordering should therefore not be stated as a general finding.

**W3. The "texture is the least shared family" contribution is not stable under the paper's own resampling standard.** (Section 1, bullet 5; Section 5.5; Table 6.)
- *Overlapping intervals.* The family means are 74.3 (color), 71.5 (spatial) and 68.2 (texture). The spatial interval [57.3, 80.1] contains the whole texture interval [61.9, 70.7].
- *Paired bootstrap.* I ran a paired scene bootstrap (5,000 draws) of the six-configuration means. Texture minus spatial is −2.9 points, 95% interval [−14.1, +10.2], with texture below spatial in only about 68% of resamples. Texture minus color is −6.3 [−13.6, −2.1], below in about 99.6%.
- *Inconsistency.* Section 5.4 calls orderings that hold in 33.6% and 47.2% of resamples "not stable", so a 68% ordering should not be a headline finding.
- *Per-configuration orderings.* The per-configuration orderings also differ: texture is least shared in only 3 of 6 configurations.
- *What is supported.* Texture is less shared than color on average. The only minority values are in texture (GPT Image 1 at 48.6%, which is itself not shown to be below 50%, and SD-Turbo).

**W4. One overgeneralization in Section 5.2** (p. 8–9, last sentence). "Proximity gain is thus dominated by movement that does not depend on which name was used, for these generators and for a faithful imitator alike."
- For GPT Image 2 in CSD, the faithful-imitator share is 48.3%, and the observed share is 54.2% with interval [47.4, 59.3].
- Per painter, Cézanne's shared share is 34.6–64.0% in CSD (Table 19).
- The average statement holds; "alike" needs "in 11 of 12 configuration–encoder pairs, and not for Cézanne individually".

**W5. Prespecified reporting is incomplete for the pairwise comparisons** (Section 4.5; Table 12). The v1 protocol, inherited by v2, required nominal 95% intervals alongside the simultaneous ones, plus paired-scene bootstrap sensitivity (5,000 draws). Section 4.5 says the bootstrap was prescribed, but its results are not reported. From the primary analysis output:
- Bootstrap intervals exclude zero for 8 of 15 pairs.
- Nominal t intervals exclude zero for 6 of 15.
- Simultaneous intervals exclude zero for 2 of 15.

The simultaneous rule is the correct decision rule, and I do not dispute "only two are resolved". The prescribed sensitivities should still appear, labelled unadjusted, so readers can see the whole prespecified output.

**W6. Smaller issues** (details in the minor changes below):
- The Table 11 caption omits a factor ½.
- An Appendix D phrase conflicts with the main text on norm versus squared size.
- The exchangeable-null wording is imprecise.
- Bootstrap draws with non-positive denominators are dropped silently (32 spatial and 4 texture draws of 5,000).
- The H bias correction is applied to β only, not to D or the benchmarks.
- Table 4 gives no intervals for the embedding D values.
- The effect of repeat dependence on N and B is not stated (only D is discussed).
- The generated images are not released, so features cannot be re-extracted.

**Limitations that need new evidence and are acknowledged.**
- Repeat dependence cannot be tested with two repeats.
- Four related painters and one template limit generality.
- The design cannot separate an "any artist name" effect from movement toward these painters.

The paper states all three and scopes its claims accordingly. I do not ask for new experiments on these points.

## Requested changes

**Critical**

1. **Correct and re-report the genuine-painting control (W1).**
   - Draw two *distinct* works per painter per pseudo-scene. Alternatively, keep the current scheme but describe it accurately and explain why the duplicate term belongs in the benchmark; I do not think it does.
   - Report the effect of the larger target noise in the half-collection and class-specific targets relative to the full-collection target. The analytic (3/4)Σ tr Σ_a/n_a term already derived in Appendix C would serve.
   - Then revise or remove "FLUX.2 Max's 0.801 is close to the content-sampled genuine level; the other configurations are not" (Section 5.3), and update Appendix D and the corresponding recommendation in Section 6.
   - For reference, my rerun with distinct works gives means of 0.111 (pooled), 0.252 (class draws, pooled target) and 0.373 (class draws, class targets).
2. **Qualify the D > 1 headline (W2).** In the abstract, Section 1 bullet 3 and Section 5.3:
   - Say it holds "in the 31 features".
   - Say that D-vs-1 is a descriptive comparison outside the prespecified 21-comparison family.
   - Report that the ordering changes in the embeddings (CLIP: five of six above 1, with GPT Image 1 lowest; CSD: none above 1).
   - Note that GPT Image 1's exceedance does not survive a multiplicity adjustment, while Flare's and Sunburst's do.
3. **Narrow the feature-family contribution (W3).**
   - Add paired scene-bootstrap intervals for the family differences (texture−spatial, texture−color, spatial−color).
   - Reword Section 1 bullet 5 and Section 5.5 to what is supported: texture is less shared than color; the texture/spatial ordering is not resolved; the family ordering differs by configuration.

**Minor**

1. Section 5.2, last sentence: qualify "for a faithful imitator alike". The faithful CSD share for GPT Image 2 is 48.3%, and Cézanne's per-painter shares are as low as 34.6% (W4).
2. Table 11 caption: "Repeat noise" is *half* the squared difference between repeats' centered contrasts, relative to H. This follows the diagnostics-v1 plan, Addendum A, and my recomputation reproduces the printed values only with the ½.
3. Appendix D, "Scene aggregation and rescaling": "GPT Image 2's differences are about twice the reference size" should read "about twice in squared size (1.49 times in norm)", consistent with Section 5.3.
4. Appendix C, "Exchangeable null": the result is E[N]/(E[N]+E[B]) = 1/4, a ratio of expectations, not "the expected shared fraction".
5. Report the protocol-prescribed nominal and paired-bootstrap intervals for the 15 pairwise D differences, labelled unadjusted (W5).
6. Section 5.6: separate the cropped-only and refit statements. With cropped regions and the original scaler, only Flare–FLUX.2 Max is resolved. After refitting, GPT Image 1–FLUX.2 Max and Flare–FLUX.2 Max are resolved.
7. State how scene-bootstrap draws with non-positive denominators were handled (family means: 32 spatial and 4 texture draws of 5,000 unavailable).
8. State the normalization of the proximity prototype. Equation 4 uses the unnormalized mean (the mean of reference cosines), while recognition uses unit prototypes. Add one line showing that the normalized-prototype variant gives nearly the same shares; in my check they changed by at most 0.5 points in all 12 pairs.
9. Note that the finite-sample correction of H also changes Q, D, B/H and both benchmarks, not only β, and report the corrected D, or at least the direction of the change.
10. Give scene intervals, or at least the stability frequencies already computed, for the CLIP and CSD D values in Table 4, since these reorder the configurations relative to the 31 features.
11. Section 7 and Appendix A: note that a shared repeat component would also inflate N and B, and hence the shared fraction, not only D.
12. Section 1, bullet 3: rephrase "only FLUX.2 Max is below that level in 94.2% of joint … resamples" as "FLUX.2 Max is the only configuration whose D is below 1 in most joint resamples (94.2%; next, Nano Banana 2 at 33.4%)".
13. Appendix C, "Intervals": the sentence "they describe these 14 scenes rather than fresh requests" is confusing. A between-scene standard error is conservative for fixed scenes. The reason the intervals do not generalize is that the scenes are authored, not sampled.
14. Commit to releasing the generated images, subject to service terms, with the camera-ready version, so the features can be re-extracted from pixels.
15. Clarity: the prose packs many ranges into single sentences, especially in the abstract, Section 5.1 and Section 5.3. Moving some ranges to tables, and adding a one-paragraph reading guide (which quantity answers which question), would help non-specialist readers.
16. Appendix H: the claim check verifies that each registered literal appears somewhere in the text, not in its sentence. Anchoring claims to their context would make the replay guarantee stronger, and a few caption numbers, such as the Table 14 shares, are literals in the build script rather than computed values. I verified the Table 14 shares independently.

## Criterion 1: claims and evidence

**Answer: partially.**
- *What is supported.* The central, abstract-level claims are supported by accurate numbers, all of which I reproduced from the retained vectors:
  - Most of what the names add is shared, and a faithful or exact-differences generator would also leave most of it shared.
  - Proximity gain in CLIP and CSD is dominated by the shared term, close to faithful-imitator values.
  - All β are positive.
  - Different readouts favor different configurations, several stably under scene resampling.
- *Three gaps.*
  - (i) A main-text comparison with genuine paintings rests on a control whose implementation contradicts its description, and which changes materially when corrected (W1).
  - (ii) The "three configurations worse than no distinctions" headline is stated without the representation qualifier it needs, and one of the three is not robust to multiplicity (W2).
  - (iii) The feature-family ordering listed as a contribution is not stable under scene resampling (W3).
- *How to close them.* All three can be closed with narrower wording plus a small reanalysis of retained data. None requires new images.

## Criterion 2: audience and clarity

**Answer: yes.**
- *Audience.* The paper addresses a practical evaluation question: how to read artist-style proximity, recognition and CSD scores. That question matters to researchers working on text-to-image evaluation, style mimicry, protection and unlearning, and they will find the decomposition and benchmarks directly usable.
- *Clarity.* The method is precisely defined (Equations 1–8, Table 9, the Figure 1 schematic). Results are organized by question, and limitations are clearly stated. The prose is very dense with numbers, and a few sentences are hard to parse (see the minor changes). These are editing issues, not failures to communicate the findings.

## Desk-rejection screen

**Risk: low.**
- *Scope and format.* The paper is in scope (evaluation methodology for generative models). It uses the TMLR template with an anonymized header, and I found no identifying information in the PDF text or metadata.
- *Quality.* The work is careful, internally consistent and reproducible. AI assistance is disclosed, and the text does not read as low-care machine output: claims are scoped, and the analysis status is tracked.

## Recommendation

**Minor revision.** The core contribution is sound and fully reproducible. The three critical items are claim–evidence corrections that use existing data: fix the genuine-painting control and its interpretive sentence, qualify the D > 1 headline, and narrow the family-ordering claim.

**Confidence: 4/5.** I verified the estimators, most main-text numbers and several derivations independently. My remaining uncertainty concerns how the authors will choose to re-specify the genuine-painting control's target noise.

## Numbers verified and how

1. **Build replay.** I ran `uv run --locked python paper/tmlr/build_assets.py --check`, which verifies input hashes, byte-identical tables and figures, and the claim registry. Output: "ok: 21 generated files and 106 claims".
2. **Table 1 and Table 10, own code.** From the retained 31-feature vectors, loaded with the paper's loader and analysed with my own estimators, I recomputed:
   - H = 5.915;
   - N/H, B/H, G/H and I/H for all six configurations (Table 10);
   - the shared fraction against the generic baseline, 66.7–88.4%, and against the free baseline, 82.5–95.7%;
   - the faithful benchmark, 84.8–95.2%, and the exact-differences benchmark, 57.6–84.2% (NB2 57.6%);
   - cos(c,t) 0.57–0.86, λ 24.8–64.6%, and the share along the generic shift, 0.1–55.5%.

   All match.
3. **Table 3, own code.** I recomputed β, Q and D for all six configurations and confirmed the identity D = 1 − 2β + Q. The nominal D intervals, e.g. GPT Image 1 [1.129, 2.016] and FLUX.2 Max [0.586, 1.016], match. So do the 21-endpoint simultaneous β intervals (t₁₃ at 1−0.05/42 = 3.760), e.g. GPT Image 1 [0.709, 1.168].
4. **Table 12, own code.** Simultaneous pairwise intervals: Flare−FLUX [0.256, 1.618], Sunburst−FLUX [0.058, 1.623], GPT Image 1−FLUX [−0.037, 1.580]. All match.
5. **Scene bootstrap, own implementation and seed.** FLUX.2 Max shared fraction [77.6, 94.2] (paper: [76.8, 94.2]). Family means: color [70.9, 77.1], spatial [57.2, 80.7], texture [61.7, 70.8] (paper: [70.9, 77.2], [57.3, 80.1], [61.9, 70.7]). Paired differences: texture−spatial [−14.1, +10.2] with P(texture < spatial) = 0.68; texture−color [−13.6, −2.1] with P = 0.996.
6. **Table 2 and Table 4, own code on the CLIP and CSD embeddings.** Recomputed values:
   - gains 0.072–0.112 (CLIP) and 0.166–0.217 (CSD);
   - shared shares 73.2–83.8% and 54.2–79.7%;
   - faithful 71.3–82.9% and 48.3–75.7%;
   - exact 60.6–73.0% and 52.5–67.4%;
   - recognition, e.g. NB2 51.8% and FLUX 41.1%/39.3%;
   - D, e.g. GPT Image 1 CLIP 0.847;
   - development recognition 79.8% (CLIP) and 79.6% (CSD).

   All match. The Equation 4 identity error is below 3·10⁻¹⁶. The normalized-prototype variant shifts shares by at most 0.5 points.
7. **Embedding β and D.** All embedding β are positive. CLIP D exceeds 1 for five of six configurations; CSD D is below 1 for all six (0.714–0.999).
8. **Repeat-correlation crossing.** Nano Banana 2 versus FLUX.2 Max crosses at ρ = 0.251. The implied biases are 0.869 and 0.560, a difference of 0.309, which equals the D gap 1.109 − 0.801. This is consistent with bias = ρ/(1−ρ) × repeat noise, where the noise uses the ½ definition. I also recomputed repeat noise/H = 0.42–2.60.
9. **Scene deletion and square windows.** FLUX.2 Max has the lowest D in all 14 single-scene deletions (range 0.754–0.852). It is also lowest with square windows (0.765; the models.csv `square_distortion` column matches).
10. **Figure 4, own code.** The painter-pair β and D matrix reproduces exactly (e.g., Sunburst M-S β −0.25, D 3.60; NB2 S-P D −0.05).
11. **Reference spread and H correction.** The singular-component shares of the reference spread are 66.3 / 20.6 / 13.0%. The H bias is 6.7%, and the corrected β range 0.474–1.071 equals β/0.933.
12. **Hand derivations.**
    - G + N + I = N_free in every row of Table 10.
    - I ≈ 2cos(c,g)√(GN), e.g. FLUX 6.56 against 6.53.
    - The Table 11 centroid split: between-name = Hβ/2 − B/4 gives −0.36 against −0.354 (GPT Image 1) and 0.355 against 0.353 (FLUX).
    - Table 13: D_agg + V_scene = D; β/√Q = 0.600 for GPT Image 1.
    - D(κ) at κ = β/Q gives 0.551 (GPT Image 2) and 0.702 (FLUX), against the held-out 0.554 and 0.714.
    - N/(N+H) from Table 10 reproduces the exact-differences column.
13. **Genuine-painting control.** The paper's `real_controls` reproduces 0.234 / 0.753 / 0.731 exactly. With the two pseudo-repeats drawn as distinct works (the same seed structure, only the pair draws changed), the means are 0.111 / 0.252 / 0.373.
14. **Protocol-prescribed pairwise bootstrap**, read from `data/manifests/painter_specificity_v2/psv2-20260911/analysis.json`: 8 of 15 intervals exclude zero; nominal t intervals exclude zero for 6 of 15; simultaneous intervals for 2 of 15. The source-correction resolved sets match the text (with the cropped-only / refit distinction noted in minor change 6).
15. **Reference audit counts.** 870 works audited, 131 cropped, 230 class changes, 43 uncertain regions. All match Section 5.6 and Appendix D.
16. **Table counts and consistency.**
    - Cézanne is least shared in 11 of 12 configuration–encoder pairs (Table 19).
    - Reference counts are 297/106/141/105 = 649, and content-class counts sum per painter.
    - The development panel has 221 works (101/36/48/36).
    - The design has 6 × 14 × 6 × 2 = 1,008 images.
