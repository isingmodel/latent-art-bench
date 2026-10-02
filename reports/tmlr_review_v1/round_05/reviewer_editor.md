# Action-editor assessment: "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation"

- **Role:** action editor (desk screen, clarity, structure, length, figures/tables, TMLR format)
- **PDF read:** `reports/tmlr_review_v1/round_05/input/manuscript.pdf`, 30 pages. I read every page as rendered, plus the text extraction.
- **PDF SHA-256:** `764356d845744d7adc994600113628525cce6f0569eff8c7927439c6a1ba5316`

## 1. Desk-rejection decision

**Not desk rejected. The paper goes to review.**

- *Scope:* The paper is about evaluation methodology for text-to-image generative models: how to read artist-style proximity, recognition and specificity readouts. This is in scope for TMLR.
- *Format:* It uses the official TMLR style in submission mode. The files `tmlr.sty`, `tmlr.bst` and `fancyhdr.sty` match the SHA-256 hashes recorded in `STYLE_PROVENANCE.json` (upstream commit 7bf90ef, `modified: false`), and the `tmlr.sty` header matches the official macros. The author block is anonymous. All 25 table captions sit above their tables and all 4 figure captions sit below their figures. A Broader Impact Statement is included. Details are in §11.
- *Quality and completeness:* The paper is complete and internally checked. The estimators are defined, the pre-registration status is disclosed, and the supplement is described. I found one text–table inconsistency (§6).
- *Machine-generated, low-care screen:* The paper does not read as generic or padded LLM output. The prose is compressed and very precise, not filler. AI assistance is disclosed (code, reference audits, editing). There are a few stylistic signs of automated number-checking, such as "(computed before rounding)" appearing twice and the "registered sentence context" wording in App. H, but they point to care rather than carelessness.

## 2. Summary

The paper asks what proximity-based artist-style metrics measure when the prompted painters are related (Monet, Sisley, Pissarro, Cézanne). The design:

- 6 API text-to-image configurations, four of them GPT Image variants.
- 14 authored scenes.
- 6 clauses: none, generic "oil painting", and one per painter.
- 2 separately requested repeats per cell, for 1,008 images.

The change that the names add beyond the generic clause is split into two parts: a component shared by all four names (N) and between-name differences (B). Squared sizes are estimated without noise bias using cross-repeat products. Two benchmarks built from 649 public-domain reproductions calibrate the split:

- a *faithful imitator*, whose named means land on the painters' reference means;
- an *exact-differences* generator, which keeps the observed shared change but reproduces the reference differences.

Main findings:

1. In 31 hand-crafted features the shared fraction is 66.7–88.4%. That is below the faithful benchmark (84.8–95.2%) and near the exact-differences benchmark (57.6–84.2%). A large shared fraction is therefore expected even of good imitation.
2. For any proximity score that is linear in the image embedding, an exact identity (Eq. 4) splits the named-minus-generic gain into a name-agnostic shared term and a painter-specific term Hβ/4. In CLIP and CSD the shared term supplies 54–84% of the gain, close to the faithful imitator's share, and it drives the differences in gain between configurations.
3. Specificity, read as agreement β, Q and D between generated and reference between-name differences, is directionally right for every configuration. Its accuracy depends on the representation. The 31 features separate genuine Monet and Sisley works poorly and give several D > 1 verdicts. CSD resolves four configurations below D = 1.
4. Proximity, agreement and recognition favor different configurations.

The paper closes with concrete reporting recommendations.

## 3. Strengths

- **A clear, generalizable diagnostic.** The shared versus between-name split, the two benchmarks, and the exact identity for linear proximity scores (Eq. 4, App. E Eq. 8) are simple and correct; I checked the algebra. The condition "the shared term dominates an exact-differences generator's gain whenever it exceeds H/4" (§4.4) gives practitioners a rule that transfers to other painter sets.
- **Careful estimation.** Cross-repeat products remove the noise bias. Reference-resampling and scene-resampling intervals are reported separately. A prespecified 21-endpoint family with Bonferroni adjustment is clearly separated from post-hoc descriptive analyses (§4.5).
- **Honest scoping.** The paper states candidly what the design cannot identify: a generic artist-name effect, unverified checkpoints, repeat dependence, the domain gap between generated images and photographed reproductions, and AI-only audits. It gives quantitative sensitivity values for the most fragile orderings, such as the ρ at which an ordering flips (App. A).
- **Internal consistency.** I spot-checked about 60 numbers against the tables and all matched except the one item in §6. Examples:
  - D = 1 − 2β + Q for all six rows of Table 4.
  - β/√Q, Q = B/H + V_scene, and N/(N+H) in Table 1.
  - The 6 resolved nominal and 8 resolved bootstrap pairwise differences in Table 13.
  - "11 of 12" for the Cézanne shares in Table 23.
  - The shift-rule recognition changes in Table 24 (−5.4 to +12.5, +0.9 to +26.8).
  - The corrected-H scaling.
  - The CLIP correlation 0.96, which I recompute as 0.958 from Table 3.
- **Useful figures.** Figure 1 sets up the geometry before any notation. Figure 3 is the paper's best exhibit: observed values against both benchmarks across three representations, with shape and color both encoding the series, and a caption explaining why the left panel differs from the embedding panels. Figure 2 shows the "shared change" at a glance; for example, GPT Image 1's Monet, Sisley and Pissarro panels are nearly identical while its Cézanne panel is not.
- **Actionable recommendations** (§6), each tied to a specific result.

## 4. Weaknesses (with locations)

**W1. Density impedes reading in the abstract and §5.3, though the main message survives.**

The abstract is about 310 words and contains several sentences that are hard to parse on first reading:
- "whereas in CSD four configurations are resolved as closer to the reference differences than making no distinctions" (p. 1).
- "The first supplies most of the gain, close to what a faithful imitator would show, and differences in gain between configurations follow it" (p. 1). This is ambiguous: close in *share*, not in magnitude.
- "Proximity, agreement and recognition favor different configurations" (p. 1). "Agreement" has not been defined at this point.

§5.3 (pp. 9–11) packs the following into about 1.5 pages: β, Q, the alignment ratio and D; five interval types (simultaneous Student, nominal Student, percentile bootstrap, reference bootstrap, joint resamples); Bonferroni-over-six; ρ-dependence; per-pair Cézanne results; representation dependence; genuine-painting calibration; aggregation; and rescaling. One example sentence: "The comparisons with 1 assume independent repeats. With a Bonferroni adjustment over the six configurations (also descriptive), GPT Image 1's interval for D, [0.935, 2.210], includes 1, and its error would fall below 1 if the two repeats shared a fraction 0.22 of their noise power, against 0.64 for Flare and 0.52 for Sunburst (Appendix A)" (p. 10).

**W2. The genuine-painting paragraph has no takeaway (p. 11).** It opens with "Genuine paintings calibrate these values" and then qualifies the comparison twice: "The comparison favors the genuine works…" and "Genuine splits also vary widely in the 31 features, whose central 95% ranges end at 1.16–1.36 and so contain several generated errors". The reader is left unsure whether the control makes the generated D values look good, bad, or uninformative in the 31 features. The 31-feature genuine range, [−0.886, 1.159] for the pooled design (Table 15), is very wide, and this deserves one explicit concluding sentence.

**W3. Interval types differ between adjacent tables.** Table 4 gives simultaneous Student intervals for β, unadjusted Student intervals for D, and reference percentiles. Table 5 gives percentile bootstrap intervals. Readers comparing Tables 4 and 5 are comparing different kinds of interval.

**W4. The main text depends heavily on the appendix.** It cites about 17 appendix tables (Tables 8–23). Several claims in §5 can only be checked by flipping to the appendix, e.g. "11 of the 12 pairs, as low as 34.6% (Appendix Table 23)" and "Appendix Table 16 and Figure 4".

**W5. Some sentences are unclear or have a missing antecedent.**
- p. 1: "raw proximity adds the generic outputs' own similarity, which does not depend on the name either." The word "either" has no antecedent yet, because the shared term has not been introduced.
- p. 2, bullet 3: "In CSD four configurations have errors resolved below that level and none above it." "That level" refers back three clauses to "a generator making no painter distinctions".
- p. 4, §3: "The 31 features were prespecified for their interpretability. The embeddings were added afterwards; embedding metrics can respond to image content (…), and CSD was trained with these painters among its style tags." This puts three unrelated caveats in one sentence.
- p. 6, §4.2: "This value includes the distance between generated images and photographed paintings, so it serves as a reference point." The "so" does not follow, and "reference point" is vague. Say what the benchmark is and is not: an upper reference for the shared fraction that includes the domain gap.
- p. 7, §4.3: "Because even genuine paintings do not reach D = 0 when sampled this way". "This way" is not yet defined.
- p. 12, §5.4: "the configuration with the largest CSD gain is best in at most 33.6% of resamples". GPT Image 1 and FLUX.2 Max are tied at 0.217, so name both.
- pp. 8 and 12: the parenthetical "(computed before rounding)" appears twice and reads as tooling residue. A single global note would do.

**W6. Content classes do not map cleanly between scenes and references.** Scenes use the classes water, built, land and mixed (§3, Table 6). References use water, built place, route, and open or wooded land (App. A). The content-matched targets use "water, built and land". The paper never says how "route" works are treated.

**W7. Length.** The main content runs from p. 1 to p. 13, with the Broader Impact Statement continuing to p. 14. The TMLR author guide warns that "papers that are unusually long (not counting any Appendices) are likely to result in reviewing delays". The OpenReview form separates regular submissions (≤12 pages of main content) from long ones. Either declare this a long submission or trim about one page. Candidates to move to the appendix: the SD-Turbo sentences in §5.5, "Other checks", and the ρ discussion in §5.3.

**W8. Appendix layout.** `\FloatBarrier` leaves large blank areas on pp. 23, 25, 26 and 28. This is cosmetic.

**W9. Supplement reproducibility for the pixel level.** The generated images are not in the supplement (§7, Reproducibility statement), and readers see only one scene (Fig. 2). TMLR allows 100 MB of supplement. Downsampled per-configuration contact sheets (14 scenes × 6 clauses, first repeat) would fit easily, and so might 512-px copies, which is the resolution at which the 31 features are computed. An anonymized external link would also work.

## 5. Claim–evidence gaps (criterion 1 detail)

| Claim (location) | Evidence | Gap | What would close it |
|---|---|---|---|
| Most of what names add is shared, expected even under faithful imitation (Abstract; §5.1) | Table 1, Fig. 3; both benchmarks; scene intervals | None material. The 25% exchangeable null is a weak comparator ("far above the 25%", p. 7). | De-emphasize the null and lead with the benchmarks. |
| Proximity gain mostly measures the shared term; differences between configurations follow it (Abstract; bullet 2; §5.2) | Exact identity (Eq. 4); Tables 2–3; r = 0.96 (CLIP) and 0.95 (CSD); "11 times" variance ratio | The correlations use n = 6 configurations and have no uncertainty (Fisher 95% intervals are roughly [0.6, 0.995]). The CLIP correlation cited in bullet 2 does not appear in §5.2. The "11 times" ratio gives ≈9.8 from the rounded Table 3 values, and the CSD ratio (≈6) is not stated. | Report both correlations and both variance ratios in §5.2 with scene-resampling intervals, and state that n = 6. |
| "Aligned but oversized" differences in the 31 features (Abstract; §5.3) | Table 4: β = 0.77–0.94 with Q = 2.2–2.45; Table 14 | "Oversized" is measured in reference units. The paper itself notes that "Part of the excess size may reflect a difference in scale between clean generated images and photographed paintings" (p. 11). The features also separate Monet and Sisley poorly (49.8% macro accuracy). | Add a scale calibration, e.g. Q after normalizing generated and reference differences by their own within-group dispersion, or qualify the wording as "oversized in reference units". |
| "Content does not explain the difference" between representations (§5.3) | Table 5 content-matched columns; Table 19 | **The robustness sentence is inaccurate as written** (see §6). The substantive conclusion still holds: the lowest-error configuration and the verdicts relative to 1 are unchanged. | Correct the sentence and report the 11-scene pooled baseline. |
| Readouts favor different configurations (§5.4) | Table 20 with scene-resample frequencies | Adequate. | — |
| Interpretation of the shared change as movement toward these painters (§6) | cos(c, t) = 0.57–0.86 (Table 11) | The paper acknowledges that the design cannot separate this from a generic artist-name effect. | A fictitious-name, distant-painter or "Impressionist" clause (168–504 more images). Optional; the core claims do not depend on it. |
| Pairwise orderings and the D vs 1 verdicts | Tables 4 and 13 | These are conditional on independent repeats; ρ ≈ 0.25 flips NB2 vs FLUX.2 Max, and ρ = 0.22 moves GPT Image 1 below 1. This is disclosed. | A third repeat collected at a separate time for a subset, to probe shared-state dependence. |

## 6. Factual errors / internal inconsistencies

1. **§5.3, p. 11:** "against title-derived content-class targets on the 11 non-mixed scenes, the embedding errors change by at most 0.037 and keep their order". This does not match Table 5, which pairs the 14-scene D with the content-matched D.
   - The changes reach **0.064**: CLIP Sunburst goes 1.136 → 1.200, CLIP GPT Image 1 goes 0.847 → 0.904, and CSD GPT Image 1 goes 0.735 → 0.767.
   - The full order is **not** kept. In CLIP, Flare and FLUX.2 Max go from 1.057/1.058 to 1.074/1.023. In CSD, GPT Image 1 and GPT Image 2 go from 0.735/0.741 to 0.767/0.759.
   - The source (`build_assets.py`) computes 0.037 against an 11-scene *pooled-target* D that no table reports. Its guard asserts only that the lowest-error configuration is unchanged.
   - Fix: either add the 11-scene pooled-target D to Table 5 and say "the lowest-error configuration is unchanged (GPT Image 1 in CLIP, FLUX.2 Max in CSD)", or quote the change relative to the reported 14-scene values.

No other numerical inconsistencies were found in the spot checks.

## 7. Requested changes

**Critical (must change for acceptance)**

- **C1.** Correct the content-matched robustness sentence in §5.3 (p. 11) as described in §6. Either report the 11-scene pooled-target embedding D the sentence relies on, or restate the claim so it is true of Table 5. Also check that the Introduction's "content-matched reference targets change none of these orderings" (p. 2) refers only to the orderings that are in fact preserved: the argmin configurations and the verdicts relative to 1.

**Minor**

- **M1.** Shorten and simplify the abstract (about 310 words now). Define "agreement". Rephrase "resolved as closer to the reference differences than making no distinctions" and "close to what a faithful imitator would show" (say "a share close to…").
- **M2.** Restructure §5.3 into labelled paragraphs: (a) direction and size in the features, (b) representation dependence, (c) genuine-painting calibration, (d) aggregation and rescaling. Give each one a one-sentence takeaway, especially (c) (see W2). Move the Bonferroni-over-six and ρ side analyses to App. A, keeping one sentence in the main text.
- **M3.** State in one place (e.g. §4.5) which interval each table uses, or harmonize Tables 4 and 5.
- **M4.** In §5.2, report both cross-configuration correlations and both variance ratios with scene-resampling intervals, and note n = 6. Make sure the "11 times" ratio is stated with its basis; it is ≈9.8 from the rounded Table 3.
- **M5.** Qualify "oversized" as "larger than the reference differences in reference units" or add a scale-calibrated Q (see §5 table).
- **M6.** Fix the sentence-level issues in W5 and remove the repeated "(computed before rounding)" parentheticals in favor of one global note.
- **M7.** Say how reference works labelled "route" enter the content-matched targets (W6).
- **M8.** Mention in §5.3 that Sunburst's Monet–Sisley amplitude in the features is significantly *negative* (Table 17: −0.249 [−0.369, −0.140]). It is the one resolved misdirection and bears on the word "aligned".
- **M9.** Declare a long submission on OpenReview or trim the main content to 12 pages (W7).
- **M10.** Add downsampled contact sheets of all generated images, or an anonymized link, to the supplement (W9).
- **M11.** Optional but valuable: a generic-name control (fictitious name, distant painters, or an "Impressionist" clause) and a time-separated third repeat for a subset.
- **M12.** Optional: a human spot-check of a random sample of the AI-only reference audits (230/870 content-label disagreements; 131 crops), reported in App. D.
- **M13.** Tighten the appendix float placement (pp. 23, 25, 26, 28).
- **M14.** Make the bibliography consistent: initials versus full names (Kim 2014, Kim 2026, Lee 2020, Sigaki 2018), inconsistent URL/DOI inclusion, and the Casper et al. venue format.
- **M15.** Supplement housekeeping: `paper/tmlr/figures/PROVENANCE.json` calls `example_selection.json` the selection manifest "for Figure 1", but the image panel is Figure 2 in this manuscript. Align this before packaging, since the Reproducibility statement points readers to the manifest.
- **M16.** De-emphasize the 25% exchangeable null in §5.1 (p. 7) in favor of the two benchmarks.

## 8. Criterion answers

**Criterion 1 (claims and evidence): yes.**
The paper's central claims are directly supported:
- The shared change dominates and is expected even under faithful imitation (Table 1, Fig. 3).
- Proximity gain is mostly the name-agnostic term, by an exact identity plus Tables 2 and 3.
- Specificity readouts are directionally right but representation-dependent (Tables 4 and 5, 15–17).
- Readouts disagree (Table 20).

The claims are scoped to four related painters, one template, 14 authored scenes and these API configurations, and the retrospective status of most analyses is disclosed. The gaps in §5 are secondary: n = 6 correlations without intervals, unit-dependence of "oversized", and the untestable repeat-independence assumption. One robustness sentence is inaccurate (C1), but correcting it does not change the conclusion it supports.

**Criterion 2 (audience and clarity): yes.**
Researchers evaluating style imitation, style protection or erasure, and generative-model metrics in general will find the decomposition, the benchmarks and the H/4 condition directly usable. The title, Figure 1, the four intro bullets, Figure 3 and the §6 recommendations tell a reader what was found and what to do differently.

The prose is precise but over-compressed. The abstract and §5.3 need the edits in M1–M3 and M6, and the paper sits at the lower edge of comfortable readability. Even so, a careful reader can follow the argument, and the density slows understanding rather than blocking it.

## 9. Desk-rejection risk

**Low.** The paper is in scope, anonymous, complete and format-compliant. The only format-adjacent item is the long-submission declaration (M9).

## 10. Recommendation and confidence

- **Recommendation:** minor revision
- **Confidence:** 4/5. I verified the algebra and cross-checked many numbers. I did not re-run the analyses, and I could not verify the style files against upstream GitHub (the rules allowed no network access for that); I checked them against the recorded provenance hashes only.

## 11. Format checks performed

1. SHA-256 of `tmlr.sty` (816214ff…0002), `tmlr.bst` (306fd454…5206) and `fancyhdr.sty` (3d292254…6e6d) match `STYLE_PROVENANCE.json` (JmlrOrg/tmlr-style-file @ 7bf90ef, `modified: false`). The `tmlr.sty` header ("Adapted by Hugo Larochelle and Fabian Pedregosa…; Last edited, January 2021 by Chris J. Maddison") matches the official file. I did not compare against upstream over the network.
2. `\usepackage{tmlr}` has no `[accepted]` or `[preprint]` option. The running header reads "Under review as submission to TMLR" on every page, and the author block reads "Anonymous authors / Paper under double-blind review".
3. `main.tex` has no geometry, margin, line-spacing or font overrides; the only packages are amsmath, amssymb, booktabs, graphicx, hyperref, url and placeins. `\small` and `\vspace{2pt}` appear only inside two appendix tables (Tables 7 and 8), which is acceptable.
4. The page size is US Letter (612 × 792 pt). Fonts are Latin Modern (loaded by tmlr.sty) plus DejaVu Sans inside the matplotlib figures, all embedded.
5. PDF metadata: Creator "LaTeX with hyperref", Producer xdvipdfmx, no Author/Title/Subject fields, CreationDate normalized to D:20260101000000Z. No identity or time-zone leak.
6. A text search for author names, emails, GitHub URLs, acknowledgments and "our previous work" phrasing found nothing. Self-references are non-identifying ("an earlier, unpublished distance analysis by the same project").
7. Caption placement: all 25 table captions are above their tables and all 4 figure captions (Figs. 1–3 in the main text, Fig. 4 in App. D) are below their figures.
8. A Broader Impact Statement is present (pp. 13–14). It covers misreading as a service ranking or as legal evidence and the dual use of optimizing imitation of living artists, with a mitigation stated. A Reproducibility statement is present, with AI-assistance disclosure.
9. Length: 30 pages. Main content pp. 1–13 (BIS to p. 14), references pp. 14–16, appendices A–H pp. 17–30. This exceeds 12 pages of main content; see M9.
10. References use natbib author-year via tmlr.bst. Cross-references and hyperlinks resolve, with no "??" anywhere.
11. Figures are legible at print size. Figure 3 encodes its series by both shape and color. The Figure 2 image panel reproduces public-domain reference works, with rights stated in the BIS.
12. I checked TMLR's public author guide and editorial policies for the rules on length, anonymity, broader impact, LLM use and desk rejection.
