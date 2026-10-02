# TMLR action-editor assessment: "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation"

Role: action editor (desk screen, then clarity, structure, length, figures/tables, format)
PDF read: `reports/tmlr_review_v1/round_04/input/manuscript.pdf`, 29 pages, every page inspected as rendered.
PDF SHA-256: `caa3b4299154a8926e29f7a7dee8d5c81784ff77477597931a0aab8d4d5ec617` (`shasum -a 256`; matches `input/inputs.sha256`).

---

## 1. Desk-rejection decision

**Not desk-rejected; send to review.**

- **Scope.** In scope. It is about evaluation methodology for text-to-image generation: what similarity-based artist-style metrics measure, with an estimator from representational similarity analysis. TMLR has reviewers for evaluation and generative models.
- **Format.** No violations found (Section 11). The official style files are unmodified according to their recorded hashes, the submission is anonymous, table captions sit above tables and figure captions below figures, and broader-impact and reproducibility statements are included.
- **Quality / likelihood of meeting the criteria.** The manuscript is careful and internally consistent. I recomputed about 40 numbers from the tables and checked the main identities (Eq. 4/8, Eq. 6, the exchangeable null, the finite-sample bias of H). Only one statement disagrees with its own table (see the factual error below).
- **Machine-generated / low care.** Low risk. The text is specific, dense and numerically checked, and it discloses AI assistance. Some stylistic tics could still draw a closer look under TMLR's LLM policy (see weakness W7): the same caveat repeated four times, and about a dozen "X, not Y" constructions. Neither is a reason to desk-reject.

## 2. Summary

The paper asks what "proximity" metrics measure when the prompted painters are stylistically related. These metrics are the similarity of artist-prompted images to the artist's works, or the gain in that similarity from adding the name.

**Data.** Six API text-to-image configurations generated 1,008 images: four GPT Image variants, Nano Banana 2 and FLUX.2 Max. The design crosses 14 fixed scenes with six clauses (none, generic oil painting, and "in the style of" Monet, Sisley, Pissarro or Cézanne), with two repeats each.

**Decomposition.** Relative to the generic clause, what the names add is split into a shared change common to all four names and between-name differences. Squared sizes are estimated from cross-repeat inner products, which removes noise bias. The observed values are compared with two benchmarks built from reference reproductions:
- a "faithful imitator", whose named means sit exactly on each painter's reference mean;
- an "exact-differences" generator, which keeps the observed shared change but reproduces the reference differences exactly.

**Findings.**
- **Shared change is large, as expected.** In 31 hand-crafted features, 66.7–88.4% of the squared change is shared. This is expected even under faithful imitation (84.8–95.2%) or exact differences (57.6–84.2%).
- **Proximity gain is mostly the shared term.** In CLIP and CSD, an exact identity (Eq. 4) splits proximity gain into a name-independent term and a painter-specific term, Hβ/4. The first supplies 54.2–83.8% of the gain.
- **Specificity readout.** Specificity is read from agreement of the between-name differences with the reference differences, using an aligned amplitude β, a relative size Q and an error D (1 means "no distinctions").
  - All configurations align in aggregate.
  - D verdicts depend on the representation: three configurations have D > 1 in the 31 features, none has a CSD point estimate above 1, and CLIP favors a different configuration.
- **Readouts disagree.** Proximity, recognition and agreement favor different configurations.
- **Checks.** An SD-Turbo collection serves as a retrospective check. A prespecified 21-test family, many sensitivity analyses and a hash-verified replay are included.

## 3. Strengths

1. **Clear, useful identity.** Eq. 4 (derived in Eq. 8) shows that prototype-based proximity gain is exactly a name-independent term plus Hβ/4. I verified it. It is simple, exact and directly relevant to how CSD-style scores are used. The remark after Eq. 4 is actionable: the shared term dominates whenever it exceeds a quarter of the painter spread.
2. **Well-designed benchmarks.** The faithful and exact-differences benchmarks keep the paper from over-reading a large shared fraction. Without them, "66.7–88.4% shared" could be misread as "names do not differentiate". Section 5.1 explicitly heads this off ("Being below the faithful value therefore does not mean being more specific").
3. **Careful estimation.** Cross-repeat products remove noise bias. D decomposes into D_agg + V_scene (verified against Table 15), and D(κ) = 1 − 2κβ + κ²Q gives a principled scale analysis. Genuine-painting controls with distinct works calibrate D.
4. **Transparency about prespecification.** Section 4.5 and Appendix A separate the prespecified family from later analyses, and say which analyses were planned after other results were known.
5. **Internal consistency.** Every cross-check I ran agreed:
   - N/(N+B) and N/(N+H) from Table 1 columns;
   - D = 1 − 2β + Q (Table 3);
   - Nfree = G + N + I (Table 11);
   - D_held ≈ 1 − β²/Q (Table 15);
   - recognition deltas against Table 24;
   - H_emb·β/4 against gain × (1 − share) in Tables 2, 4 and 5 (for example, H_CSD ≈ 0.325 comes out the same from every row).
6. **Honest scope statements.** Limitations cover the representations used, the missing human evaluation, unverifiable closed-service checkpoints, and repeat dependence, including the ρ at which orderings flip.

## 4. Weaknesses (with locations)

### W1. The headline "proximity gain mostly measures the shared change" rests on a decomposition of the level, not of the variation that drives rankings (Abstract; Sec. 1 bullet 2; Sec. 5.2; Sec. 5.4)

The abstract concludes: "Proximity gain therefore mostly measures movement that all the names share." Section 5.4 attributes the different ranking to this: "Proximity ranks differently because, by Equation 4, its dominant term carries no information about which name was used."

The evidence shown is the shared term's share of each configuration's gain level (Table 2). That a metric "measures" something is a claim about what drives its differences between the things being compared. If the shared term were roughly constant across configurations, proximity gain would rank by specificity even though the shared term dominates its level.

The paper's own tables settle this but it is never stated. The painter-specific term Hβ/4 equals gain × (1 − share):
- **CLIP.** Nano Banana 2 has the largest gain (0.112) but only the fifth-largest painter-specific term (≈0.018, essentially tied with GPT Image 1), well behind GPT Image 2 (≈0.027).
- **CSD.** GPT Image 2 has the smallest gain (0.166) but the largest painter-specific term (≈0.076, β = 0.936).
- **Spread across configurations.** The shared term varies more than the painter-specific term (CLIP ≈0.054–0.094 vs ≈0.015–0.027; CSD ≈0.090–0.168 vs ≈0.043–0.076).

These comparisons are the most direct evidence for the title. They should be reported: absolute shared and painter-specific terms in Table 5, plus the rank agreement between gain and β. The attribution in Section 5.4 should then rest on them rather than on the share of the level.

### W2. Factual misstatement about the genuine-painting controls (Sec. 5.3, p. 10)

"In the embeddings no genuine split has an error above 0.53, whereas in the 31 features 5.1–9.1% of genuine splits exceed 1."

Table 16 gives 95% ranges whose largest upper bound is 0.532 (CLIP, class sampling, pooled target). A 95% range implies that about 2.5% of splits lie above its upper bound, so the sentence contradicts the table. In `paper/tmlr/build_assets.py` the quoted value is computed as the maximum of the 95% upper bounds, and the check actually enforced there is that no embedding split exceeds 1. Suggested wording: "In the embeddings no genuine split has an error above 1 (95% ranges end at or below 0.53) …".

### W3. Abstract/intro wording on CSD is stronger than the evidence (Abstract; Sec. 1 bullet 3; Sec. 1 bullet 2)

- **"none does" / "all six below".**
  - Abstract: "in the 31 features three configurations err more than a generator that makes no painter distinctions, in CSD none does".
  - Intro: "In CSD all six errors are below that level".
  - The 31-feature statement is backed by intervals that exclude 1. The CSD statement is a point-estimate statement. Nano Banana 2's CSD error is 0.999 [0.876, 1.128], below 1 in 51.3% of joint resamples, and Sunburst's interval [0.866, 1.024] also contains 1.
  - Section 5.3 states this precisely ("four scene intervals lie entirely below 1"). The intro bullet should use the same standard.
- **"close to what a faithful imitator would show" (abstract; Sec. 1).**
  - In CSD the observed share exceeds the faithful share in all six configurations, by about +2.0 to +6.6 points (from the rounded table values).
  - Two scene intervals exclude the faithful value: Nano Banana 2 [78.5, 80.8] vs 75.7 and FLUX.2 Max [73.7, 80.3] vs 71.0.
  - The difference is disclosed in Sec. 5.2 ("−2.8 to +6.5 percentage points"). The abstract should say "close to, and in CSD slightly above".

### W4. D mixes direction with magnitude, and the abstract headline reflects magnitude (Abstract; Sec. 5.3; Table 15)

The three configurations with D > 1 in the 31 features (GPT Image 1, Flare, Sunburst) have well-aligned but oversized differences: Q = 2.28–2.45, alignment ratio β/√Q = 0.51–0.60. The authors suggest this may partly reflect "a difference in scale between clean generated images and photographed paintings".

After a single held-out rescaling, GPT Image 2 has the lowest error (0.554) and FLUX.2 Max drops to fourth (0.714). So "err more than a generator that makes no painter distinctions" is partly a statement about feature-scale mismatch with the reference domain. It is not only about how accurately painters are distinguished.

This is all disclosed in Section 5.3, but only D appears in the abstract and intro. The scale-free alignment ratio should appear next to D in Tables 3 and 4, and the abstract/intro should say the D > 1 cases arise from oversized differences.

### W5. The primary representation is weak for the specificity question, and the genuine-control comparison is framed only by means (Sec. 3; Sec. 5.3; Table 16)

- **Weak separation.** The prespecified 31 features classify development works at 49.8% macro accuracy (Monet 39.6%, Sisley 30.6%).
- **Genuine errors overlap generated ones.** Genuine-painting splits in these features have 95% ranges reaching 1.16–1.36. Those ranges contain the D values of FLUX.2 Max (0.801), Nano Banana 2 (1.109) and GPT Image 2 (1.226).
- **The framing uses means only.** "Every configuration's error is far above these means in every representation" is true of means. Readers may still take it as a statement about distributions.

Part of the reason is that the pseudo-repeats in the genuine control are different works, which add much more variance than generation repeats do (Appendix D explains the means). The paper should say this explicitly and state which comparison is meaningful. The authors appropriately decline to rank specificity overall. Even so, the 31-feature verdicts get abstract space that their validity does not quite support.

### W6. Content confound in embedding agreement is not checked with content-matched targets (Sec. 5.3; Table 20; Appendix E)

- **The confound.** The reference collections differ strongly in subject mix. For example, 191/297 Monet works are water scenes against 31/105 for Cézanne. CLIP is content-sensitive, and the paper notes that "the embeddings may respond to content".
- **What is checked now.** Content-matched (class) targets are reported only for the 31 features (Table 20).
- **Why it matters.** A scene-controlled generator should not reproduce subject-driven reference differences, so for embeddings D = 0 is not the ideal even in principle.
- **Request.** Report β and D in CLIP and CSD against content-matched targets.

### W7. Density, length and repetition impede reading (throughout; main content about 13.3 pages)

The paper is understandable, but it asks a lot of the reader.

**Load.** Section 4 introduces about 15 named quantities (N, B, H, N*, t, λ, cos(c,t), β, Q, D, D_agg, V_scene, D_held, G, I, N_free). Several Results paragraphs contain more than 10 numbers each (Sec. 5.3 paragraph 2; Sec. 5.6).

**Sentences that are hard to follow:**
- Sec. 2, end of first paragraph: "Artist-free comparisons and closed-set recognition, which already uses between-name information, are therefore established." It is not clear what "therefore established" refers to.
- Sec. 4, opening: "How much of the proximity gain is common? The shared term of Equation 4 (Section 4.4)." This is a fragment that points forward to an equation not yet defined.
- Sec. 4.1: "against the artist-free baseline the shared component is Nfree = G + N + I, with G the squared generic-minus-free shift and I a signed cross term". Three symbols appear in the main text for a side result; they belong in the appendix.
- Sec. 5.3: "Their differences are not missing but too large for their alignment". This is cryptic; say "well aligned but about 1.5 times too large in norm".
- Sec. 5.5: "The only minority value among the six configurations is GPT Image 1's texture fraction, 48.6%." "Minority value" means "below 50%"; say so.
- Sec. 5.5: "Resamples in which a denominator was not positive were dropped (32 of 5,000 for the spatial and 4 for the texture mean, 35 for the paired differences)." This is bookkeeping for the appendix.
- Figure 2 caption: "the panel labels Flare and Sunburst by their full names, GPT Image 2.5 Flare and Sunburst." Use the same labels in figure and text instead of explaining the mismatch.
- Abstract: "Every configuration responds in the reference direction in aggregate, but how accurately depends on the representation: in the 31 features three configurations err more than a generator that makes no painter distinctions, in CSD none does, and the 31 features separate genuine Monet and Sisley works poorly." This packs three different kinds of statement into one list.

**Over-hedging and repetition.**
- The retrospective-analysis caveat appears four times:
  - Abstract: "Apart from a prespecified family of tests, the analyses are descriptive and retrospective."
  - Sec. 1: "apart from the prespecified tests the analyses are retrospective".
  - Sec. 4.5: "We attach no significance claims to these analyses."
  - Sec. 7: "Apart from the prespecified family, the analyses are retrospective analyses of images whose other results were known".
- The "X, not Y" construction appears about a dozen times, for example:
  - "a reference point, not an attainable target" (4.2);
  - "requested configurations, not verified checkpoints" (3);
  - "not a perceptual judgment" (4.3);
  - "not confidence for new scenes" (Table 6);
  - "a retrospective check, not an independent replication" (5.5);
  - "differences between prompt conditions, not their causes" (6);
  - "not artists in general" (7);
  - "not independent confirmation" (E);
  - "sensitivity, not uncertainty" (G);
  - "rather than a floor" (D);
  - "feature vectors, not images" (Table 15).

  Each is accurate. Together they read as formulaic and make the text feel defensive. Consolidating them into Limitations would shorten the paper.

**Length.** Main content before references is about 13.3 pages. Under the reviewer guide this puts the paper on the 4-week track. The SD-Turbo paragraph, the feature-family denominators, the N_free split and most of Sec. 5.6 could move to the appendix without loss.

### W8. Figure 3 shows the observed-versus-faithful relation reversing between panels without explanation (p. 8)

- In the left panel (squared change, 31 features), the observed fraction is below the faithful value.
- In the CLIP/CSD panels (share of gain), it is at or above the faithful value.

The reason is different in the two cases. The squared-change fraction includes all between-name energy (B, inflated by off-pattern differences). The gain share includes only the aligned part (Hβ/4 with β < 1). Table 22 confirms that the embedding squared-change fraction is below faithful, as in the left panel. One sentence in the caption or in Sec. 5.2 would prevent confusion.

### W9. Smaller issues

- **Exchangeable null unused.** It is defined in Sec. 4.2 and Table 10 but never used in Results. Use it or drop it.
- **Hat notation.** β̂ and D̂ in Eqs. 3–4 become β and D elsewhere.
- **Rounding precision.** Table 1 shows "84" in the obs.<faithful column where the text says 84.1%. Sec. 5.4's "−5.4" cannot be recovered from Table 24's rounded entries (60.7 − 55.4 = 5.3); add "computed before rounding" as in Sec. 5.2.
- **Ad hoc adjustment.** Sec. 5.3 applies a Bonferroni adjustment over six configurations that is not part of the prespecified family. Label it descriptive.
- **"Widely read".** Sec. 1 supports "is widely read as style fidelity" with a single citation (Frochte, 2026). Add citations or soften.
- **Feature-families bullet.** The intro's fifth bullet is only loosely tied to the thesis and is not consistent across configurations or with SD-Turbo. Motivate it or demote it.
- **Layout.** Large blank regions on pp. 10, 25, 27, 28 and 29 come from `[t]` floats and `\FloatBarrier`. This is cosmetic.
- **Images not released.** The generated images are withheld "because of the archive's size limit". Downsampled images, or anonymized external hosting, would allow features to be re-extracted.

## 5. Requested changes

**Critical (must change for acceptance)**

1. **Support "proximity gain mostly measures the shared change" with the between-configuration decomposition (W1).**
   - Report the absolute shared and painter-specific terms per configuration and encoder (e.g., add them to Table 5).
   - State how the gain ranking compares with the painter-specific term (equivalently β): e.g., Nano Banana 2 is first by CLIP gain but fifth by its painter-specific term, and GPT Image 2 is last by CSD gain but first by painter-specific term.
   - Rest the Section 5.4 attribution on this rather than on the share of the level.
2. **Correct the misstatement "no genuine split has an error above 0.53" (Sec. 5.3, p. 10; W2).** It contradicts the 95% ranges in Table 16. State that no embedding split exceeds 1 and that the 95% ranges end at or below 0.53.
3. **Use the same evidence standard for CSD statements in the abstract and intro as for the 31-feature statements (W3).**
   - Replace "In CSD all six errors are below that level" with a statement that gives the four intervals entirely below 1, and note Nano Banana 2 (0.999; 51.3%).
   - Qualify "close to what a faithful imitator would show" to say the CSD shares are slightly above faithful in all six configurations.

**Minor**

1. Put the scale-free alignment ratio β/√Q (or D_held) next to D in Tables 3–4. Say in the abstract/intro that the three 31-feature D > 1 cases come from oversized, aligned differences (Q = 2.28–2.45), which may reflect a difference in scale between generated images and photographed paintings (W4).
2. Reframe the genuine-control comparison (W5):
   - say that 31-feature genuine 95% ranges contain several generated D values;
   - explain why genuine-split variance is larger;
   - say which comparison is informative.
3. Report CLIP/CSD β and D against content-matched reference targets (W6).
4. Add one sentence explaining why observed is below faithful in the left panel of Figure 3 but at or above faithful in the embedding panels (W8).
5. Bring the main content to 12 pages or fewer. Move the SD-Turbo paragraph, the N_free split, the feature-family bookkeeping and most of Sec. 5.6 to the appendix (W7).
6. Rewrite the unclear sentences quoted in W7: Sec. 2 "therefore established"; the Sec. 4 opening fragment; Sec. 5.3 "not missing but too large for their alignment"; Sec. 5.5 "only minority value"; the Figure 2 caption; the three-part abstract sentence.
7. State the retrospective/prespecified caveat once in the abstract and once in Sec. 4.5, and cut the other repetitions. Vary or consolidate the repeated "X, not Y" constructions (W7).
8. Use the exchangeable null (1/4) in Results or remove it from Sec. 4.2 and Table 10.
9. Keep hat notation consistent for β̂ and D̂.
10. Show Table 1's obs.<faithful to one decimal. Note "computed before rounding" for the Sec. 5.4 recognition deltas.
11. Label the six-configuration Bonferroni adjustment in Sec. 5.3 as descriptive (outside the prespecified family).
12. Add support for "widely read as style fidelity" or soften it.
13. Motivate or demote the feature-family bullet in the intro.
14. Reduce blank space on pp. 10 and 25–29.
15. Provide downsampled generated images, or anonymized hosting, so features can be re-extracted.
16. Use consistent configuration labels in Figure 2 and the text.

## 6. Criterion 1: claims and evidence — **partially**

**What is supported.**
- The core technical claims: the identity, the benchmarks, the observed shared fractions and gain shares, and the representation-dependence of agreement.
- The numbers are internally consistent (Strength 5).
- Scope and inferential status are stated carefully.

**Gaps that currently keep this from "yes":**
- (a) The central "mostly measures" conclusion is argued from a decomposition of the level, while the ranking evidence that would establish it is never presented. It is computable from the paper's own tables (W1).
- (b) One statement contradicts its table (W2).
- (c) The CSD wording in the abstract/intro uses a looser evidence standard than the 31-feature wording (W3).

All three can be fixed with existing results. None requires new data. Secondary gaps are:
- the magnitude-driven interpretation of D > 1 (W4);
- the means-only genuine-control framing (W5);
- the content confound in embedding agreement (W6).

**What would close them:** critical changes 1–3, plus minor changes 1–3.

## 7. Criterion 2: audience and clarity — **yes**

**Audience.** Researchers who evaluate artist-style imitation, style protection/erasure (Glaze, concept ablation, UnlearnCanvas) and CSD-style metrics would care about this. So would anyone reporting "style similarity" gains.

**Clarity.** The abstract, the intro bullets, Figure 1 and the Section 6 recommendations say clearly:
- what was found: the shared term dominates proximity even for faithful imitation, and specificity must be read from between-name differences;
- why it matters: proximity-based comparisons can reward movement common to all names;
- what readers can do: report the benchmarks, β/Q/D with genuine controls, and ranking stability.

**Caveat.** The Results are very dense and longer than necessary (W7). Streamlining would widen the readership, but the density does not stop a motivated reader from following the argument.

## 8. Desk-rejection risk — **low**

The paper is in scope and complies with the format. The quality is high and the care is evident. The stylistic repetition noted in W7 is the only thing likely to draw a closer look under the LLM-generated-content policy, and the substance would survive that look.

## 9. Recommendation — **minor revision**

The three critical changes are small edits that use existing results. They are needed so that the headline claims match the evidence as presented.

## 10. Confidence — **4 / 5**

I read every page. I verified the main identities and cross-checked about 40 reported numbers against the tables. I also consulted the LaTeX sources, `claims.json` and `build_assets.py` for the one discrepancy found. I did not re-run analyses or inspect the supplementary archive.

## 11. Format checks performed

1. **Style files.** `tmlr.sty`, `tmlr.bst` and `fancyhdr.sty` in `paper/tmlr/` have SHA-256 hashes that match `STYLE_PROVENANCE.json`, which records JmlrOrg/tmlr-style-file commit 7bf90ef with `modified: false`. The `tmlr.sty` header matches the official file (Larochelle/Pedregosa, last edited Jan 2021 by Maddison). I did not diff against upstream because network access was limited to the author guidelines.
2. **Preamble.** `main.tex` uses `\documentclass[10pt]{article}` and `\usepackage{tmlr}` with no option (anonymous submission mode), plus the template's `\month`/`\year`/`\openreview` placeholders. There are no geometry, spacing or font-size overrides in the preamble. `\small`/`\footnotesize` are used only inside some tables.
3. **Rendered page.** The header reads "Under review as submission to TMLR", the byline reads "Anonymous authors / Paper under double-blind review", and the paper is US letter, 29 pages.
4. **Anonymization.**
   - No names, affiliations, acknowledgments, funding or identifying URLs appear.
   - The PDF metadata has no Author or Title fields (Creator "LaTeX with hyperref", Producer xdvipdfmx).
   - The creation date is normalized.
   - The project refers to itself only in the third person ("the same project").
   - The supplement is described as anonymous, but I did not inspect it.
5. **Caption placement.** All 25 table captions are above their tables and all 4 figure captions are below their figures, verified visually on every page.
6. **Statements.** A broader impact statement is present (p. 14) and appropriate: it covers misuse for imitating living artists, misreading as a service ranking, and public-domain/CC status of references. A reproducibility statement is present and includes an AI-assistance disclosure.
7. **Length.** Main content before references is about 13.3 pages, over the 12-page threshold, so the paper goes to the 4-week review track under the TMLR reviewer guide. This is not a violation.
8. **References.** Author-year via `tmlr.bst`. All in-text citations resolve to bibliography entries, and there are no undefined references ("??") in the text.
9. **Figures.** Figures 1, 3 and 4 are vector graphics and legible. Figure 2 is a raster panel of thumbnails, adequate for orientation. The Figure 2 images are public-domain or generated.
10. **Math.** I checked Eq. 4/8 (the proximity identity), Eq. 6 (centroid proximity), the exchangeable-null ratio of 1/4, the finite-sample bias of H ((3/4)Σ tr Σ_a/n_a), D = 1 − 2β + Q and D = D_agg + V_scene.

## Factual errors found

- Sec. 5.3, p. 10: "In the embeddings no genuine split has an error above 0.53". Table 16 reports 95% ranges with upper bounds up to 0.532, which implies that some splits exceed 0.53. The source computes this value as the maximum of the 95% upper bounds, not the maximum over splits. The supportable statement is that no embedding split exceeds 1.
