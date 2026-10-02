# Action editor assessment: "What Does an Artist Name Add? Separating Shared and Painter-Specific Responses in Text-to-Image Generation"

- Role: action editor (desk screen, then clarity, structure, length, figures/tables, TMLR format compliance)
- PDF read: `reports/tmlr_review_v1/round_01/input/manuscript.pdf`, 20 pages (main text pp. 1–11, references pp. 11–13, appendices A–H pp. 14–20). I read every rendered page, including all figures and tables, and cross-checked the text extraction.
- PDF SHA-256: `33c87a6f609b2c791b0ba6c5101d4af64fc9b05e155b9bb448c65a5a6a90b5c8`

## 1. Desk-rejection decision

**Not desk-rejected. The paper goes to review.**

- **Scope.** The paper is on evaluation methodology for text-to-image generation (artist-style prompting, proximity and recognition readouts). It is in scope for TMLR.
- **Format.** The style files are the official, unmodified ones, the submission is anonymized, captions are placed correctly, and a broader impact statement is included (see Section 11). The only format issue I found is cosmetic.
- **Quality.** The paper is a controlled measurement study with pre-specified primary inference and an explicit split between confirmatory and descriptive analyses. I recomputed about 40 reported quantities from the tables and they are internally consistent:
  - C/(C+B) and N/(N+B) for all six configurations (Table 1).
  - D = 1 − 2β + Q (Table 2).
  - D = D_agg + V_scene and β/√Q (Table 9).
  - The pairwise differences in Table 8.
  - All recognition deltas in Section 5.4 and Table 12, including the +2.7/+10.0 and +16.1/+25.0 means and "corrects 39 and harms 9".
  - The SD-Turbo shares in Table 5.
- **Machine-generated, low-care screen.** Not triggered. The prose is dense and sometimes aphoristic ("Size is not direction.", §4.2), but it is specific, internally consistent and not padded. I found no generic filler paragraphs. Two sentences in the paper overreach (see W2 and W5), but that is a claims issue, not a care issue.

## 2. Summary

The paper argues that the usual readout for artist-style prompting, the gain in proximity to an artist's works, mixes two things:
- a change shared by every artist name in the prompt set;
- between-name differences, which alone can encode what distinguishes one painter from another.

**Design.** 14 fixed scene descriptions × 6 clauses (no painting instruction; "Render as an oil painting."; the same clause "in the style of" Monet, Sisley, Pissarro or Cézanne) × 2 repeats × 6 commercial configurations = 1,008 images.

**Method.**
- The four named-minus-baseline changes are split into their mean (shared) and the deviations from it (between-name).
- Squared sizes are estimated with cross-repeat inner products, which remove noise bias.
- The between-name part is compared with the contrasts among the four painters' reference means using an aligned amplitude β and an error D.
- In CLIP and CSD, an exact identity (Eq. 4) splits the prototype proximity gain into a shared term and a painter-specific term, Hβ/4.

**Main results.**
- Beyond the generic clause, 66.7–88.4% of the squared change is shared (31 features).
- β is above zero in all six configurations (pre-specified simultaneous intervals).
- The shared term supplies 73.2–83.8% (CLIP) and 54.2–79.7% (CSD) of the proximity gain.
- Proximity, agreement and recognition rank the configurations differently.
- A retrospective SD-Turbo collection is majority-shared overall but not in texture features.

**Recommendation to the field.** Include a generic-style control and report the decomposition next to proximity.

## 3. Strengths

- **S1. A clean, useful question.** The paper asks how much of a "style" effect would be produced by any name in the prompt set. It answers with a design (a generic-style control plus multiple names) that others can copy cheaply. The recommendation in §6 follows directly from the identity in Eq. 4. The accounting in Eq. 4 is exact and the paper checks it (App. E).
- **S2. Careful estimation.**
  - Cross-repeat products remove noise bias, and the paper correctly notes that estimates can be negative and keeps them.
  - The primary family of 21 comparisons was fixed before collection, with Bonferroni-adjusted paired-scene intervals.
  - A simulation checks coverage and shows that coverage collapses under shared model state (App. C). That result is used honestly to motivate a limitation.
- **S3. Candour about the analysis status.** §4.4 says clearly which analyses were pre-specified and which were added after other results were known. §7 and App. A state the repeat-independence assumption and give the correlation at which the Nano Banana 2–FLUX.2 Max ordering reverses (ρ = 0.251).
- **S4. Informative secondary analyses.**
  - The D = D_agg + V_scene split and held-out rescaling (Table 9) explain why the rankings move.
  - Omitting each painter (Table 10) shows that Cézanne carries much of the aggregate β. This is a useful caution that authors of recognition benchmarks should see.
  - The translation experiment (§5.4, Table 12) shows that recognition can move by up to 26.8 pp while every painter contrast stays unchanged. This is a small but useful result for evaluation practice.
- **S5. Figure 1** is a good qualitative figure. It shows the two controls next to the four names for all six configurations, with a pre-fixed selection rule, and it makes the "shared" phenomenon visible (e.g., FLUX.2 Max's four named outputs look alike).
- **S6. Length and structure.**
  - The main text is about 10.5 pages.
  - Section titles state the findings.
  - Appendices are well targeted: A provenance, B features, C estimators, D robustness, E embeddings, F recognition, G SD-Turbo, H replay.

## 4. Weaknesses (with locations)

**W1. The "shared share" has no reference value, so readers cannot tell whether 66.7–88.4% is surprising (Abstract; §1 bullet 1; §5.1; §6).**
- Two reference points are missing.
- **(a) An exchangeable null.** If the four names produced unrelated changes of equal expected size with no common component, E[N]/(E[N]+E[B]) = 1/4. The share is therefore not measured against 0%, and this is never stated.
- **(b) The faithful-imitation value.** This is the share a generator would show if it moved generic images exactly to each painter's reference mean. In the 31 features this is 4‖μ̄ − z̄_g‖² / (4‖μ̄ − z̄_g‖² + H). In an embedding it is (μ̄ − g_g)ᵀμ̄ / ((μ̄ − g_g)ᵀμ̄ + H/4), obtained by substituting g_a = μ_a in Eq. 4.
- §6 says: "Our data cannot say how large that appropriate part is, because it would require the same decomposition for real paintings against a generic reference, which does not exist here."
- A first-order version of that benchmark can in fact be computed from quantities the paper already has (μ_a, the generic-clause means, H). There is a caveat: part of μ̄ − z̄_g is a gap between the reproduction domain and the generated-image domain. That caveat should be stated, not used as a reason to omit the number.
- For four closely related painters, H is small by construction. A faithful imitator could therefore also show a large shared fraction. If so, the headline says more about the prompt set than about the generators.
- As written, the abstract and the §1 bullet "Most of what a painter name adds is shared" invite the reading that the generators fall short on specificity. The paper itself disclaims that reading (§1: "A large shared component is therefore not by itself a failure"), but it gives the reader no number to judge by.

**W2. The direction of the shared change is established only in embeddings, yet §6 generalizes it (§6, "What the shared change is").**
- §6 says: "The shared change moves images toward the four painters' common appearance: in both embeddings it increases similarity to the average reference prototype … What the data do show is that the shared change is several times larger than the entire spread among the four painters, and that it dominates proximity gain in every configuration and representation we examined."
- Proximity gain is computed only in CLIP and CSD (Tables 3–4), not in the 31 features. In the features, only the size of c is reported, never its direction relative to μ̄ − z̄_g. The shared change could partly overshoot the reference centroid or be orthogonal to it (for example, a generic "painterly" texture shift).
- "Dominates" is also strong for GPT Image 2 in CSD, where the shared part is 54.2%.

**W3. The main collection's shared fraction is reported only for the pooled 31-feature metric, although the paper's own SD-Turbo check shows strong dependence on feature family (§5.1, §5.5, §5.6, Table 11).**
- In SD-Turbo, the shares are:

  | Feature family | Shared share |
  |---|---|
  | Spatial | 84.9% |
  | Color | 57.5% |
  | Texture | 36.6% |

- The pooled figure there (64.2%) is therefore partly determined by the equal weighting of 31 coordinates.
- For the six commercial configurations, which carry the paper's headline, no family breakdown is given.
- Table 11 reports D under equal-family and covariance weighting, but not N/(N+B) or N/H.
- §5.6 says: "The shared/between-name split uses only generated images and the fixed feature scaling, so choices about the reference collection cannot change it." This is true of the reference collection. It is not true of the weighting, and N/H does depend on the reference target through H.
- The CLIP/CSD shares (68.8–82.3%) partly reassure, but those encoders are related to each other (App. E) and do not substitute for the family breakdown.

**W4. The ranking-reversal claim (Abstract; §1 bullet 3; §5.4, Table 4) rests on point estimates without uncertainty.**
- §4.4 says the descriptive analyses are reported "with scene- or block-deletion ranges". Table 3, Table 4 and the embedding shares in §5.3 have none.
- Some reversals may be within noise:
  - The CLIP proximity gains are 0.100 (GPT Image 2) and 0.112 (Nano Banana 2).
  - Recognition uses 112 images per configuration. The binomial standard error alone is about 4.4–4.7 pp before scene clustering, so 60.7% vs 68.8% (GPT Image 1 vs GPT Image 2) is not clearly separated.
- The companion claim that "the configuration with the lowest error against the reference painter differences in the 31 features has the least recognizable names" uses FLUX.2 Max's lowest D. That D is not resolved from Nano Banana 2, GPT Image 1 or GPT Image 2 (Table 8), and its own interval includes the no-distinction value 1 (§5.2).
- Some reversals are clearly robust. FLUX.2 Max's recognition of 39.3–41.1% against 68.8–75.9% for GPT Image 2 is one. The paper should say which reversals are robust.

**W5. The headline magnitude is a squared ratio, but it is phrased as if it were a linear one (Abstract; §1; §5.1; §6).**
- The abstract says: "the shared change is 1.4–5.3 times as large as the entire spread of the four painters' reference means."
- N and H are sums of squared norms. Most readers will read "times as large" linearly.
- In linear terms, the shared shift per image is √(N/H) ≈ 1.2–2.3 times the root-mean-square distance of a painter mean from the four-painter mean. The between-name part is √(B/H) ≈ 0.8–1.5.
- The squared framing roughly doubles the rhetorical contrast. §6's "several times larger than the entire spread" inherits the same problem.

**W6. §5.3 overinterprets the embedding check.**
- §5.3 says: "The decomposition is not an artifact of the hand-designed features." The decomposition is an algebraic identity. What is being checked is the finding that the change is majority-shared.
- §5.3 also says: "The weak or reversed Monet–Sisley response in the 31 features is therefore a property of that representation, not evidence that the generators cannot distinguish these painters."
- Positive Monet–Sisley alignment in CLIP and CSD is compatible with other explanations. The encoders may pick up semantic or content cues correlated with the painter name rather than style. CSD was also trained with these painters' names as style tags (§7, App. E).
- "Therefore" should become a weaker statement: the 31-feature result does not transfer to the embeddings.

**W7. "These reversals follow from the decomposition." (§5.4).** Eq. 4 is an identity for proximity only. The link to recognition (argmax over prototypes) is an interpretation, not a consequence of the identity. The sentence should say so.

**W8. Terminology and notation make the paper harder to read than necessary.**
- **Unstable names for the same object.** "Between-name", "name-specific" and "painter-specific" are used interchangeably:
  - title: "Painter-Specific Responses";
  - §4.1: "between-name changes";
  - abstract: "Name-specific differences".
  - By the paper's own logic, between-name differences are painter-specific only to the extent that they match r_a.
- **"Shared share".** The phrase is awkward (Table 1 header, §5.5). "Shared fraction" would read better.
- **Similar names.** β is the "aligned amplitude", but β/√Q is labelled "Alignment" (Table 9).
- **Undefined term.** "Uncalibrated error point estimate" in §5.6 is not defined. It means "not rescaled".
- **Overloaded symbols.**
  - B is the between-name component (Table 1) and also the reference-prototype rule (Table 12).
  - G is the generic shift (Table 1) and also the generated-prototype rule (Table 12).
  - C is the shared component against the artist-free baseline and also Cézanne (Fig. 3).
  - b is the baseline index and also the scale factor in "(b − 1)²" (§4.2).
  - Eq. 2 uses the word "shared" as a symbol.
- **Hard-to-follow sentences.** For a general ML reader these are dense:
  - §4.4: "Intervals condition on the reference panels, the scaling and the 14 authored scenes, and they include fixed scene heterogeneity."
  - §5.2: "Each is a legitimate target; they answer different questions." This sentence does not say which questions.
  - §3: "31 coordinates chosen to change independently." The features are correlated; the paper itself reports a covariance weighting.
- **No schematic.** There is no diagram of the geometry: the generic mean, the four named means, c, e_a and the reference contrasts r_a. Figure 2 repeats the N and B columns of Table 1 and adds little. A two-dimensional schematic would do more for readers outside the evaluation subcommunity.

**W9. Reproducibility and provenance gaps (App. A, §5.6, Reproducibility statement).**
- **Unclear configurations.** It is not explained what "GPT Image 2.5 Flare" and "Sunburst" are (public product names, codenames, or preview variants), and the gateway is not named. Naming a commercial gateway does not de-anonymize the authors.
- **Protocol not available.** The pre-collection protocol that fixed the 21 comparisons is described as hashed, but it is not stated to be in the supplement.
- **Unverified AI audit.** §5.6 says: "AI assistants audited all 870 reference and development reproductions and cropped peripheral artifacts … from 131 of them, without human verification." The tool and procedure are not described. A human check of 131 crops is cheap.
- **Images not released.** The generated images are not released: "Generated images are not included in the supplementary archive because of its size limit." Features therefore cannot be re-extracted from pixels (App. H says so). An anonymized download link would close this.
- **Unclear prior study.** The SD-Turbo collection comes from "an earlier study" / "an earlier distance analysis". Say whether this is published. If it is, cite it in the third person; if not, say it is unpublished.
- **Missing attribution.** Figure 1 reproduces four reference paintings. The broader impact statement (p. 11) says some reference records are CC BY/BY-SA, but the displayed images carry no source or licence line.

**W10. Scope versus title.**
- The findings are for four related painters and one clause template (§7).
- The title "What Does an Artist Name Add?" and the abstract's unqualified "66.7–88.4% of the change that a painter name adds" read more generally than the evidence supports.
- The limitation is stated honestly in §7, but only there.

## 5. Requested changes

### Critical (must change for acceptance)

1. **C1. Give the shared fraction reference values.**
   - State the exchangeable null of 25% (no common component).
   - Report the faithful-imitation shared fraction implied by moving the generic-clause mean to each reference mean: in the 31 features, 4‖μ̄ − z̄_g‖²/(4‖μ̄ − z̄_g‖² + H) per configuration; in CLIP and CSD, the same quantity for Eq. 4 with g_a = μ_a.
   - State the domain-gap caveat.
   - Then revise the Abstract, §1 and §6 so that 66.7–88.4% (and 73.2–83.8% / 54.2–79.7% of proximity gain) is read against these values.
   - If the authors think this benchmark is invalid, they must argue it explicitly, rather than saying it "does not exist here".
2. **C2. Establish the direction of the shared change in the 31 features, or restrict the claim.**
   - Report cos(c, μ̄ − z̄_g).
   - Report the component of c along μ̄ − z̄_g against its orthogonal remainder.
   - Report whether the distance to μ̄ falls from the generic to the named condition.
   - Either compute proximity gain in the features (for example, a Euclidean or negative-squared-distance analogue of Eq. 4) or rewrite §6's "dominates proximity gain in every configuration and representation we examined" to name only CLIP and CSD.
   - Replace "dominates" where the shared part is about 54% (GPT Image 2, CSD).
3. **C3. Report how the main collection's shared fraction depends on representation choices.**
   - For all six configurations, give N/(N+B), N/H and B/H by feature family (color, spatial, texture). The SD-Turbo result in §5.5 makes this breakdown necessary.
   - Give the same under the equal-family and covariance weightings already used in Table 11.
   - Give N/H under the content-matched (class) reference target.
   - Correct §5.6's statement that choices cannot change the split: it holds for the reference collection but not for the weighting or the H normalizer.
4. **C4. Add uncertainty to the descriptive readouts, and qualify the ranking-reversal claim to match.**
   - Give scene-deletion ranges, or scene-cluster bootstrap intervals, for proximity gain, recognition and the embedding shares in Tables 3–4. §4.4 promises this.
   - State which ranking reversals are robust.
   - Rephrase the abstract and §1 bullet 3 so that FLUX.2 Max's lowest D is not presented as a resolved ordering. Only 2 of 15 pairwise D differences are resolved, and FLUX.2 Max's own interval includes 1.
5. **C5. State the headline magnitude as a squared ratio, or convert it to a linear one.**
   - In the Abstract, §1, §5.1 and §6, either say "in squared magnitude" or report the linear equivalents: shared shift about 1.2–2.3 times, and between-name about 0.8–1.5 times, the RMS painter deviation.
   - Rephrase "several times larger than the entire spread" (§6) to match.

### Minor

1. **M1.** Soften §5.3: replace "The decomposition is not an artifact of the hand-designed features" with a statement about the majority-shared finding. Replace "therefore a property of that representation" with "does not transfer to the embeddings", and note the content/semantic and CSD-training-tag alternatives.
2. **M2.** §5.4: present "These reversals follow from the decomposition" as an interpretation for recognition. Eq. 4 covers only proximity.
3. **M3. Terminology and notation.**
   - Use one term (e.g., "between-name") consistently, and reserve "painter-specific" for the aligned part.
   - Replace "shared share" with "shared fraction".
   - Rename either β ("aligned amplitude") or β/√Q ("Alignment") so the two are not confused.
   - Define or drop "uncalibrated" (§5.6).
   - De-overload B, G, C and b (Tables 1 and 12, Fig. 3, §4.2).
   - Give Eq. 2's "shared" a symbol.
4. **M4. Add a schematic of the geometry.** Show the generic mean, the named means, c, e_a and r_a. Either drop Figure 2 or merge it into Table 1, since it repeats Table 1's N and B columns. Figure 2 also labels configurations "Flare" and "Sunburst" where the tables use "GPT Image 2.5 Flare/Sunburst".
5. **M5.** Move β/√Q from Table 9 into Table 2. It separates direction from magnitude, which is the distinction §5.2 is making. Say in the caption that D > 1 can occur for correctly directed but over-amplified responses (e.g., GPT Image 2).
6. **M6.** Rewrite for a general ML reader:
   - §4.4, "Intervals condition on the reference panels, the scaling and the 14 authored scenes, and they include fixed scene heterogeneity";
   - §5.2, "Each is a legitimate target; they answer different questions" (name the questions);
   - §3, "31 coordinates chosen to change independently".
7. **M7.** Abstract: "estimators that use independent repeated generations to remove sampling noise from squared magnitudes". The estimators remove the noise-induced bias, not the noise, and independence is assumed, not established (§7). Rephrase; §1 has the same wording.
8. **M8.** Abstract and §1: say that name-specific differences are aligned "in aggregate". In 5 of 6 configurations, Monet–Sisley alignment in the features is between −0.249 and 0.129 (§5.2).
9. **M9.** Signal in the abstract, or at the start of §5, that the generic-baseline decomposition, the embedding analyses and the recognition analyses are post hoc descriptive analyses. Put the hashed pre-collection protocol in the supplement.
10. **M10.** App. A: explain what "GPT Image 2.5 Flare/Sunburst" are and name the gateway. Also name the third ordering that reverses for ρ < 1: the text says "three point orderings reverse" but names only two.
11. **M11.** §5.6/App. D: name the AI tool and procedure used for the reference audit. Verify the 131 crops by hand, or say why not.
12. **M12.** Provide the 1,008 generated images through an anonymized link, subject to provider terms, so features can be re-extracted from pixels.
13. **M13.** §3/App. D: report the subject composition of the reference panels (landscape vs. other genres), and whether the primary r_a and H are restricted to landscapes. The generated scenes are all outdoor landscapes, and the conclusions about Cézanne (Table 10) depend on r_a.
14. **M14.** §1/App. G: clarify the status of the "earlier study" behind the SD-Turbo collection. If it is published, cite it in the third person.
15. **M15.** Figure 1: add source and licence attribution for the four reference reproductions.
16. **M16.** §1: add a source for "Artist names are among the most widely used style controls" (for example, prompt-log analyses such as DiffusionDB). Fix BibTeX capitalization: Verma et al., "? estimating" should be "? Estimating"; Deliège et al., "? on" should be "? On".
17. **M17.** §5.1: report the generic-baseline within-scene shares alongside the artist-free within-scene shares (88.6–97.2%).
18. **M18.** Table 4: GPT Image 1 and FLUX.2 Max both show 0.217 CSD proximity but only one is bold. Show more digits or bold both.
19. **M19.** Table spacing is cosmetic: the last caption line abuts the top rule in Tables 1, 6, 8, 11 and 12. Add a small skip below table captions, which does not modify tmlr.sty.
20. **M20. Optional but strengthening.** Scope the title or subtitle to the four-painter study, or run the distant-painter or "Impressionist"-clause control proposed in §7. That would directly test whether the shared fraction tracks painter similarity.
21. **M21.** The references cite "Commons:GLAM … Accessed 11 September 2026", while §3 says both panels "were assembled before this experiment" (collection on 10 September) and the SD-Turbo set (5 September) reused them. Clarify that the access date refers to the cited page, not to when the panel was assembled.

## 6. TMLR criterion 1: claims and evidence

**Answer: partially.**

**Supported:**
- the existence of a large common component in the named-minus-generic change (Table 1, with scene-deletion ranges);
- β > 0 in all six configurations (pre-specified simultaneous intervals);
- the exactness of the proximity split in embeddings (Eq. 4 and App. E);
- the translation result, where recognition changes while every contrast is held fixed;
- the confirmatory/descriptive boundary, which is honestly drawn.

**Not yet adequately supported:**
- **(i) Interpretation of the headline fraction.** There is no null or faithful-imitation reference (C1).
- **(ii) The §6 claims about direction and proximity in "every … representation".** Proximity was not examined in the 31 features (C2).
- **(iii) Robustness of the main-collection share to feature family and weighting.** The paper's own SD-Turbo check shows it is not robust in that collection (C3).
- **(iv) The ranking-reversal headline.** It is not accompanied by uncertainty (C4).
- **(v) The abstract's magnitude comparison.** It is a squared ratio read as a linear one (C5).

All five can be closed with analyses on data the authors already hold. No new image collection is needed.

## 7. TMLR criterion 2: audience and clarity

**Answer: yes.**

**Audience.** Researchers who evaluate style imitation, work on artist-style protection and erasure, or build recognition benchmarks such as those of Su et al. and Moayeri et al. would be interested. The practical message is concrete and cheap to adopt: add a generic-style control, report the shared/between-name split next to proximity, and treat recognition separately.

**What readers learn.** The introduction's finding bullets, section titles that state findings, and the Limitations section make this clear.

**Where clarity falls short.** It is local and fixable:
- symbol overloading and unstable terminology (W8);
- a few dense sentences (M6);
- no schematic of the geometry (M4);
- the squared-versus-linear phrasing (C5).

None of these prevents a careful reader from understanding the paper.

## 8. Desk-rejection risk

**Low.**
- The paper is in scope and format-compliant.
- The quality is well above the desk-rejection bar.
- The writing is specific and internally consistent, not generic.
- The only format blemish is caption-to-rule spacing.

## 9. Recommendation

**Major revision.** The core design and estimators are sound. The paper is clearly within TMLR's criteria for interest. However, the interpretation of the headline number (C1), one overreaching Discussion claim (C2), missing representation-sensitivity results for the main collection (C3) and missing uncertainty for a headline comparison (C4) must be fixed before the claims match the evidence. None requires new data collection.

## 10. Confidence

**4 of 5.** I checked the algebra and many reported numbers against each other. I did not have the feature vectors, so I could not recompute C1–C3 myself or verify the external citations beyond plausibility.

## 11. Format checks performed

- Computed the PDF SHA-256 with `shasum -a 256` (value above).
- Style files:
  - `paper/tmlr/tmlr.sty`, `tmlr.bst` and `fancyhdr.sty` have SHA-256 hashes identical to those in `STYLE_PROVENANCE.json`, which declares the JmlrOrg/tmlr-style-file commit 7bf90efe with `modified: false`.
  - I did not re-fetch upstream (no network allowed). The `tmlr.sty` header and logic match the official file ("Adapted by Hugo Larochelle and Fabian Pedregosa … Last edited, January 2021 by Chris J. Maddison").
- `main.tex` loads `\usepackage{tmlr}` with no `[accepted]`/`[preprint]` option. The running header "Under review as submission to TMLR" appears on all 20 pages.
- Anonymization:
  - The title block reads "Anonymous authors / Paper under double-blind review".
  - There is no acknowledgments section.
  - PDF metadata has no author or title fields (Creator: LaTeX with hyperref; Producer: xdvipdfmx).
  - A byte scan of the PDF for user names and local paths was negative.
  - `paper/tmlr` sources contain no identifying paths or emails.
  - Cited art-analytics works are referenced in the third person.
- No layout overrides in the preamble or body: no geometry, `\vspace` hacks, margin changes or font-size changes other than `\small` inside tables. Letter paper, 612×792 pt.
- All fonts are embedded (Type 1C Latin Modern and CID TrueType DejaVu in the figures). No Type 3 fonts.
- Table captions are above the table for all 12 tables (Tables 1–12).
- Figure captions are below the figure for all 3 figures.
- A broader impact statement is present (p. 11). It covers misreading as a service ranking and legal questions, public-domain painters, reference licences and the absence of human participants. A reproducibility statement is also present.
- Length: main text pp. 1–11 (about 10.5 pages, within the 12-page regular-submission guideline), references pp. 11–13, appendices A–H pp. 14–20 in the same PDF.
- No unresolved references (`??`) in the text extraction. The bibliography uses tmlr.bst natbib author–year.
- Figure legibility:
  - Figure 1 thumbnails are embedded at about 309 ppi.
  - Figure 2 and Figure 3 labels are legible at print size.
  - Figure 2's configuration labels ("Flare", "Sunburst") are inconsistent with the table labels.
- Cosmetic: the last caption line nearly touches the table's top rule in Tables 1, 6, 8, 11 and 12. This is standard LaTeX `\belowcaptionskip = 0` with captions placed above tables.
