# TMLR review: "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation"

Reviewer role: empirical (evaluation of text-to-image generative models)
PDF read: `reports/tmlr_review_v1/round_06/input/manuscript.pdf`, 32 pages, all of it, including the appendices.
SHA-256 of the PDF: `4ae5600ec39d49e52f30a105432d92b809d117d71d0c3e8627ccd6405209a242`

## 1. Summary of the submission

The paper asks what "proximity" measures, meaning the similarity between images generated with an artist's name and that artist's works, when the prompted painters are closely related. The setup has six commercial image configurations (four OpenAI GPT Image variants, Nano Banana 2 and FLUX.2 Max). Each renders 14 authored outdoor scenes under six clauses: no painting instruction, a generic oil-painting instruction, and the generic instruction plus "in the style of" Monet, Sisley, Pissarro or Cézanne. Each cell is requested twice, giving 1,008 images. The images are measured in 31 hand-crafted color, spatial and texture features (the prespecified primary representation) and in CLIP ViT-L/14 and CSD ViT-L embeddings. A 649-work reference collection supplies each painter's mean.

The method has three parts:

1. **Shared and between-name split.** Relative to the generic clause, the four named means split into a shared change c and between-name differences e_a. Squared sizes N and B are estimated from cross-repeat products, which removes the bias sampling noise adds to a squared size. Two benchmarks come from the reference collection: a *faithful imitator* (named means equal the reference means) and an *exact-differences* generator (observed shared change plus the reference differences r_a).
2. **An exact identity for proximity gain (Eq. 4).** Any gain that is linear in the embedding equals a name-independent shared term (ḡ − g_g)ᵀμ̄ plus a painter-specific term Hβ/4.
3. **Agreement readouts.** Agreement between the between-name differences and the reference differences is scored by an aligned amplitude β, a relative size Q, an "alignment ratio" β/√Q and a repeat-corrected error D. D = 1 corresponds to making no painter distinctions.

The main findings are:

- In the 31 features, 66.7–88.4% of what the names add is shared. A faithful imitator would show 84.8–95.2%, and exact differences would still leave 57.6–84.2%.
- The shared term supplies 54–84% of the embedding proximity gain and accounts for most of its variation across configurations (r = 0.96 in CLIP, 0.95 in CSD).
- All configurations have β > 0. GPT Image 2 has the highest alignment ratio in all three representations.
- D ranks the configurations differently in each representation.
- Recognition co-varies with the alignment ratio.

The authors are explicit that only 21 comparisons in the features were prespecified and that everything else is descriptive and retrospective.

## 2. Contributions as I read them

1. A simple and useful decomposition, with an exact identity (Eq. 4 and Appendix E), that separates the name-independent and painter-specific parts of any linear prototype-similarity gain. It comes with benchmarks that tell readers how large the shared part would be even for faithful imitation.
2. A controlled design with a generic-style control and two independent repeats per cell. The cross-repeat estimators make squared magnitudes unbiased under independent repeats.
3. An empirical demonstration on six current commercial configurations and three representations. On the same images, proximity gain, recognition and a reference-difference error disagree, and the disagreement is explained by what each readout weighs.
4. A candid account of sensitivity: repeat dependence, reference sources, content-matched targets, feature weightings, a genuine-painting control, and a reproducibility harness that ties every quoted number to hash-bound analysis outputs.

## 3. Strengths

- **The central claim is well posed and well supported.** Eq. 4 is exact. I re-derived it, and it also holds with unit-normalized prototypes. The exact-differences benchmark (Table 2) shows that for these painters the shared term would dominate the gain even with perfect between-name differences. The claim "proximity gain mostly measures the shared change" is therefore demonstrated, not merely asserted.
- **The benchmarks are appropriate.** Without the faithful and exact-differences references, a large shared fraction would be uninterpretable. The paper states plainly (p. 8) that a lower shared fraction does not mean more specificity.
- **Statistical hygiene is careful.** Cross-repeat products avoid noise inflation. Paired-scene intervals are used, and a simulation check of simultaneous coverage appears in Appendix C. The paper distinguishes scene resampling from reference resampling and discloses the prespecified family, and which analyses were added later and what was known when, in §4.5 and the plans under `studies/painter_tmlr_diagnostics_v1–v5`. It also reports how fragile the D > 1 verdicts are to repeat correlation (Appendix A, Table 23).
- **The paper is honest about the weak primary representation.** The 31 features separate genuine Monet and Sisley works poorly (49.8% macro accuracy; Sisley 30.6%, §3, Appendix D). The paper states this and declines to rank configurations by D across representations.
- **Internal consistency is high.** I recomputed many derived quantities from the printed tables, and every one matched:
  - D = 1 − 2β + Q in Tables 4 and 5.
  - N/(N+B) and N/(N+H) in Table 1.
  - N_free = G + N + I in Table 9.
  - The Spearman values 0.60–0.77 and −0.14 to 0.66 in §5.3, and 0.94 and 0.89 in §5.4.
  - The ρ thresholds 0.22, 0.246, 0.251, 0.30–0.32 and 0.64 in Appendix A.
  - The "11 of 12" Cézanne statement in Table 25.
  - The bootstrap and Student resolution counts (6 and 8 of 15) in Table 13.
  - The −2.8 to +6.5 point differences in §5.2 (6.53 unrounded for FLUX.2 Max in CSD).

  I also recomputed β, Q and D in CLIP and CSD from the released embeddings (`reports/painter_learned_audit_v1/embeddings_*.npz`), and they reproduce Table 5.
- **Related work is described accurately** in every case I checked (Section 9 below).

## 4. Weaknesses (with locations)

**W1. The alignment ratio is described as "direction regardless of size", but it also penalizes scene-to-scene variation** (§4.3, p. 6; Table 4 caption, p. 10; Table 5 caption; §5.3 "Direction"; abstract).
- Q is averaged per scene, and the paper itself shows Q = B/H + V_scene (§4.3, Eq. 7).
- β/√Q is therefore invariant only to one global rescaling. A generator whose between-name differences point exactly along the reference pattern in every scene, but with a different amplitude in each scene, gets a ratio below 1.
- The caption's "1 for a scaled copy of the reference pattern" holds only when the scale is constant across scenes.
- This matters because the headline "GPT Image 2 aligns best in all three representations" rests on this readout.
- I checked whether the conclusion survives the scene-averaged cosine β/√(B/H), which removes V_scene. GPT Image 2 is still highest:
  - features: 0.70 vs ≤ 0.64;
  - CLIP: 0.71 vs ≤ 0.66;
  - CSD: 0.78 vs ≤ 0.72.
- So this is a description and definition problem, not a problem with the result.

**W2. The explanation of recognition is technically incorrect as worded** (§5.4, p. 12: "Recognition tracks the alignment ratio ... both reward differences in the right direction, whatever their size"; intro bullet 4).
- Nearest-prototype recognition of individual images depends on the size of the between-name differences relative to the within-condition spread of the images. It also depends on the shared offset.
- The paper's own Appendix F and Table 26 show that one name-independent translation changes recognition by up to +26.8 points in CSD.
- The rank correlations (six configurations; one transposition in CLIP, two in CSD) are descriptive. Recognition correlates almost as well with β itself (Spearman about 0.77 in CLIP and 0.71 in CSD by my computation from Tables 3 and 5). The data therefore cannot single out "direction regardless of size" as the shared driver.
- The sentence "The disagreements follow from what each readout weighs" is a plausible interpretation, not a demonstrated mechanism.

**W3. The headline D > 1 verdict is stated more firmly in the introduction than the evidence allows** (p. 2, bullet 3: "GPT Image 1, Flare and Sunburst err more than a generator making no painter distinctions").
- Comparisons with 1 lie outside the prespecified family and use unadjusted intervals.
- With a Bonferroni adjustment over six configurations, GPT Image 1's interval [0.935, 2.210] includes 1.
- GPT Image 1's verdict reverses at a repeat correlation of only ρ = 0.22. Two repeats cannot identify ρ (§5.3, Appendix A).
- The body of the paper qualifies all of this. The introduction does not.

**W4. The headline configuration result is post hoc, and the prespecified primary outcome is hard to find.**
- The v1/v2 protocol fixed D in the 31 features as the ranking criterion ("Rank models only on D"; `studies/painter_specificity_v1/PROTOCOL.md`).
- Within that family, only 2 of 15 pairwise differences are resolved (Flare and Sunburst worse than FLUX.2 Max).
- The alignment ratio, Q and D_held were defined afterwards (`studies/painter_tmlr_diagnostics_v5/PLAN.md` lists them as already recorded in a post-result audit).
- The abstract and introduction lead with the post hoc alignment-ratio ranking and do not state the prespecified primary outcome.
- §4.5 does disclose that "everything else" was added afterwards. The status of each headline number should still be visible where it is stated.

**W5. In the embeddings, the faithful benchmark confounds movement with dispersion, and the Figure 3 caption explains only part of the gap** (Figure 3 caption, p. 9; Table 2; Appendix E).
- The faithful imitator sets each named mean embedding to the mean of the *unit* reference embeddings.
- The norm of such a mean reflects the collection's diversity:
  - CSD reference centroid ‖μ̄‖ ≈ 0.66, and per-painter reference means ≈ 0.72;
  - named-condition means of the generated images ≈ 0.85–0.91.

  I computed these from the released embeddings. They agree with the trace ratios of 0.25–0.88 in Table 20.
- As a result, the observed shared term can exceed the faithful one. For GPT Image 2 in CSD, (ḡ − g_g)ᵀμ̄ ≈ 0.090 against (μ̄ − g_g)ᵀμ̄ ≈ 0.076. In the other CSD cases the ratio is 0.66–0.94, and in CLIP 0.47–0.66.
- The caption attributes "observed at or above faithful" to Hβ/4 < H/4 alone. Part of it is that generated images are more concentrated than reference works.
- This does not affect the exact-differences benchmark or the main claim. It does mean "faithful imitator" is less of a ceiling in embeddings than in features. It also means the shared term partly reflects how concentrated the named outputs are.
- Reporting λ, the analogue of Table 11, in the embeddings and the mean-embedding norms would make this clear.

**W6. D in the embeddings is not decomposed by aggregation, although the paper recommends doing so** (§5.3, Table 5; the Discussion recommends stating "whether errors are scored per scene or after averaging").
- From the released embeddings I obtain D_agg of 0.59–0.80 in CLIP for all six configurations, with V_scene 0.26–0.45.
- In CSD, D_agg is 0.56–0.82, with V_scene 0.10–0.19.
- So every CLIP D above 1, including Sunburst's "resolved above 1", comes from scene-to-scene variation of the differences, not from the scene-averaged pattern.
- Table 14 gives this split for the features. The same split belongs in Table 5 or 23, and it changes how the CLIP verdict should be read.

**W7. Scope and generality of the recommendations** (§6, "Recommendations").
- The empirical magnitude of the shared term relative to H is shown for one group of four related painters, one clause template and 14 scenes. The paper says so (§7).
- The rule "a shared term larger than a quarter of the painter spread will dominate" is specific to K = 4. For K painters the painter-specific term is Hβ/K.
- Most benchmarks in the literature use tens to hundreds of artists: 70 in Casper et al., 110 in Su et al., 372 in Moayeri et al. Stating the general form, and what it implies for unrelated painter sets, would make the recommendations usable beyond this case study.
- No new experiment is needed for the claims as scoped.

**W8. Possible content injection by the names is not examined** (§3 "Measurements"; Appendix E "Scope").
- CLIP is content-sensitive, and the paper cites Kynkäänniemi et al. for this.
- The content-matched targets address the reference collections' subject mix. They do not address whether a name adds or removes scene content in the generated images (for example, water lilies, boats or a mountain in the manner of Mont Sainte-Victoire).
- Such content could count as on-pattern or off-pattern difference in CLIP.
- A light check would suffice: a captioner or CLIP text probes on named versus generic images, or a short visual audit of one or two scenes. So would a sentence acknowledging the issue.

**W9. The Results sections are hard to read** (§5.3–5.5, pp. 10–13).
- Nearly every sentence carries several numbers, intervals and cross-references. The reader must track N, B, H, N*, λ, β, Q, β/√Q, D, D_agg, V_scene, D_held, κ and ρ, and three kinds of interval.
- The introduction and Figures 1 and 3 communicate the core message well. §5.3–5.5 read like an audit log.
- Moving most sensitivity numbers to the appendix would make the paper far more accessible to TMLR's broad audience. This includes the source-audit ρ values, the individual pair errors and the texture-only exception. A compact table of each headline claim with its status (prespecified or post hoc, interval type, conditional on independent repeats) would help.

**W10. Reproducibility of the pixels** (Reproducibility statement; §7).
- The generated images are not in the supplement.
- They come from closed services that may change or disappear. The paper notes that Flare and Sunburst may not remain available.
- So the 31-feature and embedding extraction cannot be re-run by others.
- The hash-checked replay harness (Appendix H) is excellent for the analysis layer. The images themselves are the primary data and should be deposited, for example in an archival data repository at camera-ready time.
- Only one scene is shown qualitatively (Figure 2). A contact sheet of a few scenes for all four names, per configuration, would let readers see what "off-pattern" differences look like.

**W11. Minor presentation and accuracy points.**
- p. 2, bullet 2: "(less for Cézanne alone)" is ambiguous. It means the shared share is lower for Cézanne's gain (Table 25).
- §5.3: "Content does not explain the difference" is broader than the evidence. The evidence is that title-derived content-class targets on 11 scenes change embedding errors by at most 0.037.
- §4.4: "cosine similarity to a prototype normalized to unit length, as in CSD's prototype scoring". The CSD paper describes a dot product with the averaged prototype and does not say it is normalized. Cite the released code if that is the source, or say "a normalized variant".
- §1: Verma et al. (2025) score imitation as the average similarity to each generated image's top-10 most similar training images. That is a nonlinear readout outside Eq. 4's scope. "The same kind of similarity" is loose, and should point to the scope statement in §4.4.
- Related work could link the trace ratios (named outputs 25–88% as varied as the references) to "stereotyped" imitation and dispersion in Deliège et al. (2025) and to Xing et al. (2026). It could also note that concept-erasure evaluations already use between-artist readouts, such as effects on non-target artists.
- The PDF metadata CreationDate carries a KST time zone. This is a small anonymity hint; strip it (for example, build with TZ=UTC).
- Percentile bootstrap intervals over 14 scenes for ratio statistics, such as Table 1's shared fraction, may undercover. Say so, or use the Student or BCa intervals already used elsewhere.

## 5. Requested changes

### Critical (must change for acceptance; all are text-level and need no new data)

1. **Describe the alignment ratio accurately (W1).** β/√Q is invariant to one global rescaling. It is lowered by off-pattern differences *and* by scene-to-scene variation of the differences (Q = B/H + V_scene). Fix the wording in §4.3, the captions of Tables 4 and 5, §5.3 and the abstract. Also report the scene-averaged cosine β/√(B/H) next to it. By my computation GPT Image 2 remains highest in all three representations, so the headline survives.
2. **Correct the explanation of recognition (W2).** Remove "whatever their size". Recognition depends on the size of the differences relative to image-level spread and on shared offsets, as Appendix F itself shows. Present the Spearman values (n = 6) as descriptive co-variation, not as evidence that recognition and the alignment ratio "reward" the same thing. Soften "The disagreements follow from what each readout weighs" to an interpretation.
3. **Bring the qualifications of the D > 1 verdicts into the introduction (W3), and mark post hoc status where results are stated (W4).** In the introduction bullet, the D > 1 verdicts for GPT Image 1, Flare and Sunburst in the features, and for Sunburst in CLIP, need three qualifications:
   - they use unadjusted intervals;
   - they are conditional on independent repeats;
   - GPT Image 1's verdict does not survive a Bonferroni adjustment over six configurations or ρ ≥ 0.22.

   State the prespecified primary outcome in the introduction (2 of 15 pairwise D differences resolved in the features), and state that the alignment ratio and D_held were defined after the D results were known.

### Minor

4. Report λ (or the ratio of the observed to the faithful shared term) and the mean-embedding norms for CLIP and CSD. Revise the Figure 3 caption to say that in embeddings the faithful imitator carries the reference collection's dispersion, and that generated outputs are more concentrated (W5).
5. Add D_agg and V_scene for the embeddings to Table 5 or 23, and note that every CLIP D above 1 comes from scene-to-scene variation (W6).
6. Give the K-painter form of Eq. 4 and of the "quarter of the spread" rule, and say how the recommendations apply to many-artist benchmarks (W7).
7. Acknowledge, or briefly check, name-induced content changes in the generated images, especially for CLIP (W8).
8. Streamline §5.3–5.5 and move secondary sensitivity numbers to the appendix. Consider a one-table summary of headline claims with status and interval type (W9).
9. Commit to depositing the 1,008 generated images, and add a small qualitative contact sheet in the appendix (W10).
10. Wording fixes: "(less for Cézanne alone)"; "Content does not explain the difference"; the CSD prototype-normalization attribution; the Verma et al. description (W11).
11. Add the related-work links to stereotyped or concentrated imitation (Deliège et al.; Xing et al.) and to erasure-specificity readouts (W11).
12. Strip the time zone from the PDF metadata (W11).
13. Note the limited small-sample coverage of percentile bootstrap intervals over 14 scenes, or use the Student intervals already used elsewhere for per-scene statistics (W11).

## 6. TMLR criteria

**Criterion 1 (claims and evidence): partially.**
- The central claims are supported by accurate and convincing evidence:
  - most of what the names add is shared, and this is expected even under faithful imitation;
  - proximity gain is mostly the name-independent term of an exact identity and accounts for most between-configuration differences in gain;
  - every configuration's between-name differences align positively with the reference pattern in aggregate;
  - D orders configurations differently across representations.
- Several statements are worded beyond their evidence:
  - the alignment ratio is described as direction-only, when it also penalizes scene inconsistency (W1);
  - recognition is said to reward direction "whatever their size", which is incorrect and contradicted by Appendix F (W2);
  - the unconditional introductory D > 1 verdicts (W3);
  - "Content does not explain the difference" (W11).
- All of these can be closed by rewording plus small additions computable from the released vectors. None requires new experiments. I verified that the GPT Image 2 alignment result survives the corrected cosine.

**Criterion 2 (audience and clarity): yes.**
- Evaluators of artist-style imitation, and the copyright, protection and erasure communities who use CSD and CLIP prototype scores, will find the decomposition and benchmarks directly useful.
- The core message is communicated clearly in the abstract, the introduction bullets and Figures 1 and 3.
- The Results sections are very dense (W9). This hurts readability but does not prevent the findings from being understood.

## 7. Desk-rejection screen

**Risk: low.**
- The paper is in scope, uses the TMLR format and is anonymized. The only leak is a minor time-zone hint in the PDF metadata.
- The prose is careful and specific rather than generic.
- AI assistance is disclosed, and the analysis trail is unusually thorough.
- Nothing suggests low-care machine generation.

## 8. Recommendation

**Minor revision.** The paper makes a correct and useful methodological point and backs it with a careful, transparent experiment. The remaining problems are how the specificity readouts are described and interpreted, and how the status of post hoc results is flagged. All can be fixed in text, with a few additions computed from data already in the supplement.

**Confidence: 4/5.** I checked the algebra and many numbers, and reproduced the embedding agreement statistics from the released embeddings. I did not re-extract features from pixels, which are not available.

## 9. Literature checked (web)

- Somepalli et al. (ECCV 2024), CSD. Confirmed that generated images are scored by dot product with an artist prototype averaged over the artist's paintings (the "GSS" score). The paper does not state that the prototype is normalized.
- Verma et al. (TMLR 2025), imitation thresholds. The imitation score is the average cosine similarity between generated images and the top-10 most similar training images, followed by PELT change detection. That is a nonlinear readout, outside Eq. 4's scope.
- Frochte (arXiv 2605.09030v2, 2026). Confirmed the statement that raw CSD cosine is "widely read as an absolute, calibrated style-fidelity score", the 91-artist corpus with negative same-versus-different gaps for part of it, and the evaluation of prompted Flux generations.
- Su et al. (arXiv 2507.18633, 2025). Confirmed 110 artists, a fixed content prompt with substituted names, and comparison with the same-seed image without the artist's name.
- Casper et al. (2023). Confirmed 70 artists, CLIP zero-shot classification, and 81.0% average identification.
- Moayeri et al. (ICLR 2025), ArtSavant. Confirmed about 20% of 372 artists at risk.
- Xing et al. (arXiv 2608.06751, 2026). Confirmed "canonical shortcuts, such as recurring motifs, generic palettes".
- Kim et al. (PNAS 2026; arXiv 2503.13531). Confirmed; embeddings trace historical change.
- Deliège et al. (J. Imaging 2025). Confirmed expert raters on the stylistic fidelity of Midjourney images, including Monet.
- Asperti et al. (BDCC 2025), AI-Pastiche. Confirmed.
- Fu et al. (arXiv 2508.01408, 2025). Confirmed VLM tests of artist attribution and AI-image detection.
- From prior knowledge, not re-fetched: Kumari et al. (2023) use a generic "painting" anchor for styles; Hönig et al. (ICLR 2025) include a user study; Benny et al. (IJCV 2021) on conditional metrics; Diedrichsen & Kriegeskorte (2017) on cross-validated distances.

## 10. Numerical checks I ran (read-only)

- I reproduced β, Q and D for CLIP and CSD from `reports/painter_learned_audit_v1/embeddings_{clip,csd}.npz`, using the project's own loaders. They match Table 5 to three decimals.
- I computed from the same embeddings:
  - D_agg: CLIP 0.587, 0.634, 0.698, 0.683, 0.756, 0.798; CSD 0.581, 0.560, 0.695, 0.753, 0.824, 0.615 (model order as in the tables);
  - the scene-averaged cosine β/√(B/H): CLIP 0.658, 0.711, 0.619, 0.656, 0.584, 0.534; CSD 0.715, 0.782, 0.705, 0.708, 0.562, 0.664;
  - mean-embedding norms: CSD ‖μ̄‖ = 0.664; named-condition means 0.85–0.91;
  - the ratio of the observed to the faithful shared term: CLIP 0.47–0.66; CSD 0.66–1.18.
- From Table 4 and Table 9: the 31-feature scene-averaged cosine β/√(B/H) is 0.64, 0.70, 0.54, 0.59, 0.57 and 0.56.
- `reports/painter_tmlr_diagnostics_v5/analysis.json` confirms the Spearman values and the proximity correlation, variance-ratio point estimates and intervals quoted in §5.2–5.4.
