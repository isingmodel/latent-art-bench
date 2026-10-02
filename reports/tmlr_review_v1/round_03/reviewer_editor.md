# TMLR action-editor screen and review: "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation"

- Role: editor (desk-rejection screen, then review)
- PDF read: `reports/tmlr_review_v1/round_03/input/manuscript.pdf`, 25 pages, all pages inspected as rendered
- PDF SHA-256: `7da8263c19eeb6ec1b3dc1c6292306712a7e5297e99f95009649c66c80299310`
- Criterion 1 (claims and evidence): **partially**
- Criterion 2 (audience and clarity): **yes**
- Desk-rejection risk: **low**
- Recommendation: **minor revision**
- Confidence: **4/5**

---

## 1. Desk-rejection decision

**Not desk-rejected. The paper goes to review.**

- **Scope.** The paper is about how artist-style prompting in text-to-image models is evaluated, which is in scope for TMLR as ML evaluation methodology. Likely readers include people working on evaluation of generative models, style mimicry and protection, and concept erasure.
- **Format.** The official TMLR template is used in anonymous-submission mode. The page header reads "Under review as submission to TMLR", and the author block reads "Anonymous authors / Paper under double-blind review". Table captions sit above tables and figure captions below figures. A broader impact statement and a reproducibility statement are included. I found no violations (details in Section 10).
- **Anonymity.** No author names, acknowledgments, identifying URLs or PDF author metadata. The SD-Turbo collection is described as coming from "an earlier, unpublished distance analysis by the same project", which does not identify anyone.
- **Quality and care.** The manuscript does not read as low-care machine-generated text. The prose is compressed but specific. Caveats are concrete (for example, the collection history and the list of analyses added after collection), not boilerplate. I spot-checked more than 40 numbers across the text, tables and appendix identities (Section 11), and all but trivial rounding differences agree. AI assistance for code, the reference-source audit and editing is disclosed. The main risk is density, not padding.

---

## 2. Summary of the submission

The paper asks what the usual "proximity gain" readout for artist-name prompting measures. This readout is the increase in similarity between named generations and an artist's reference works.

**Design.**
- Six closed-service configurations: four OpenAI GPT Image variants, Nano Banana 2 and FLUX.2 Max.
- 14 authored outdoor scenes, each rendered under six prompt clauses: no painting instruction, a generic oil-painting instruction, and the same instruction "in the style of" Monet, Sisley, Pissarro or Cézanne.
- Two separate requests per cell, 1,008 images in total.

**Method.**
- The named-minus-generic change is split into a component shared by all four names and between-name differences (Eq. 1–2).
- Squared sizes are estimated with cross-repeat inner products, so sampling noise adds no positive bias.
- The observed split is compared with two benchmarks computed from 649 reference reproductions:
  - a *faithful imitator*, whose named means land on the painters' reference means;
  - an *exact-differences* generator, which keeps the observed shared change but reproduces the reference differences between painters.
- In CLIP and CSD embeddings, an exact identity (Eq. 4) splits proximity gain into a name-independent shared term and a painter-specific term, Hβ/4.
- Specificity is scored with an aligned amplitude β, a relative squared size Q and an error D = 1 − 2β + Q. D = 1 corresponds to making no painter distinctions.

**Findings.**
- In the 31 interpretable features, 66.7–88.4% of the change the names add is shared. The benchmarks give 84.8–95.2% (faithful) and 57.6–84.2% (exact differences), so a high shared fraction is expected even under good imitation.
- In the embeddings, the shared term supplies 54.2–83.8% of proximity gain, within −2.8 to +6.5 points of a faithful imitator.
- Every configuration's between-name differences point in the reference direction in aggregate. However, three GPT configurations have D > 1 in the 31 features.
- Proximity, recognition and agreement rank the configurations differently.
- An earlier SD-Turbo collection serves as a retrospective check.
- Status of the analyses: only a 21-comparison family was prespecified. The paper openly labels the headline analyses as retrospective.

---

## 3. Strengths

1. **A useful, testable conceptual point.** Equation 4 is an exact identity: the shared term cannot depend on which name produced which image. This turns the intuition "related painters make proximity uninformative about specificity" into something that can be measured. The recommendation (Section 6) follows directly from it: report exact-differences and faithful benchmarks next to proximity. It needs only a generic-style control and the reference means.
2. **The benchmarks block the obvious misreading.** Without them, a 70–88% shared fraction would look like weak specificity. With them, the paper shows this is the expected regime whenever painters are close to each other relative to their distance from the generic outputs (Table 1; Nano Banana 2 is worked through in Section 5.1).
3. **Careful estimation and many checks.**
   - Cross-repeat unbiased products (Appendix C).
   - Scene and reference-work resampling, with joint resampling for D < 1 (Table 3).
   - Genuine-painting controls (Appendix D).
   - Within-scene and artist-free variants (Table 10).
   - Feature-family, weighting, leave-one-feature-out, crop and content-matched sensitivity checks (Tables 6, 16, 17).
   - A finite-sample bias correction for H.
   - A simulation of interval coverage under several error models.
4. **Transparent about what was prespecified and what came later.** Section 4.5 separates the prespecified 21-comparison family from analyses added afterwards. It discloses the aborted first collection and the scene-panel reduction from 16 to 14, and states that the added analyses were run "on images whose other results were known". It also states that the service labels denote requested configurations, not verified checkpoints. This is better practice than the field norm.
5. **Internally consistent numbers.** For example:
   - D = 1 − 2β + Q holds for all six rows of Table 3.
   - N_free = G + N + I holds for Table 10.
   - The exact-differences fractions in Table 1 equal N/(N + 1) from Table 10.
   - The "along generic" column of Table 1 equals cos(c, g)² from Table 11.
   - The ranges and means in Table 20 match Section 5.4.
6. **The reader learns something.** Rankings by proximity, recognition and agreement genuinely diverge (Tables 4–5). Recognition can be moved by a label-free shared translation that leaves every painter difference unchanged (Table 20: +0.9 to +26.8 points in CSD). Both results are concrete warnings for people who evaluate style mimicry and style erasure.
7. **Limitations are specific.** Section 7 names the concrete consequences, for example "under an assumed common correlation of 0.251 the Nano Banana 2 and FLUX.2 Max error estimates would swap order".

---

## 4. Weaknesses (with locations)

**W1. The headline specificity claims come from a representation that barely separates the painters, and the abstract does not say which representation they come from.**
- Abstract: "every configuration responds in the right direction in aggregate, but three have larger errors than a generator that makes no painter distinctions".
- Section 1, bullet 3: "Three have errors above those of a generator that makes no painter distinctions, and only FLUX.2 Max is below that level in 94.2% of joint scene and reference resamples."
- Both statements hold in the 31 features only. Section 5.3 and Appendix D report that these features classify genuine development works at 49.8% macro accuracy (Monet 39.6%, Sisley 30.6%). The embeddings reach 79.8% (CLIP) and 79.6% (CSD).
- In Table 4, the embedding D values tell a different story. In CLIP, five of six point estimates exceed 1 (0.847, 1.061, 1.057, 1.136, 1.078, 1.058). In CSD, none do (0.714–0.999).
- The embedding D values have no intervals in the main text, although Section 6 itself recommends reporting "β (direction and size), Q and D with scene and reference intervals".
- The D > 1 verdict for GPT Image 1, Flare and Sunburst comes with β = 0.77–0.94 and Q = 2.22–2.45 (Tables 3 and 13). Their differences are over-sized and only partly aligned (alignment ratio 0.51–0.60). They are not absent.
- Q > 1 may partly reflect a scale mismatch between clean generated images and photographed, aged paintings. The rescaling result (D_held; GPT Image 2 best at 0.554) points the same way. The main text never states this possibility.

**W2. D is compared with genuine paintings without a spread for the relevant control.**
- Section 5.3: "FLUX.2 Max's 0.801 is close to the content-sampled genuine level; the other configurations are not."
- Only means are given for the content-sampled control (0.753 against the pooled target, 0.731 against content-matched targets).
- The pooled control's central 95% range is [−0.758, 1.380] (Appendix D). That range is wide enough that D ≈ 1.1 (Nano Banana 2) or 1.2 (GPT Image 2) may lie inside what genuine paintings score under this design.
- As written, the sentence is a claim without the evidence needed to support it.

**W3. The premise is thinly documented, and the score analysed differs from the one used in practice.**
- Abstract, first sentence: "Artist-style prompting is commonly assessed by how much closer images generated with an artist's name move to that artist's works."
- Section 1: "a score that is widely read as style fidelity (Frochte, 2026)".
- Only Somepalli et al. (2024) and Frochte (2026) are cited for proximity as common practice. Section 2 itself concedes that "artist-free comparisons and closed-set recognition, which already uses between-name information, are therefore established."
- The title argues against a practice, so that practice should be shown to exist in the form analysed. That means published evaluations that read named-image proximity, or its gain over a baseline, as evidence of style fidelity or mimicry.
- Section 4.4 calls the readout "the mean gain in cosine similarity to the prompted painter's prototype". Because μ_a is unnormalized, g_aᵀμ_a is the mean image-to-reference cosine (as Appendix E says correctly), not a cosine to the prototype.
- CSD-style practice, and the paper's own recognition readout, use normalized prototypes.
- The identity still holds for normalized prototypes because the score stays linear in the image embedding. But the reported shares are for the unnormalized form, and the main text does not say so.

**W4. Some secondary claims go beyond the intervals shown.**
- Section 1, bullet 5, and Section 5.5: "Texture is the least shared family on average across configurations". Texture is 68.2% [61.9, 70.7], but spatial is 71.5% [57.3, 80.1] (Table 6). Texture is resolved against color, not against spatial.
- Abstract, "Proximity gain therefore mostly measures movement that all the names share", and the Section 5.2 heading. GPT Image 2 in CSD has 54.2% [47.4, 59.3] (Table 2), an interval that includes 50%. The claim holds for 11 of 12 configuration–encoder pairs by lower bound, and the text should say so.

**W5. Repeat independence carries the inference and is not tested.**
- Appendix C reports simulated simultaneous coverage of 96.0–99.7% under benign error models. It falls to 0.04% when "a configuration-specific state shared by all scenes and both repeats" exists.
- Appendix A shows that ρ = 0.251 reverses the Nano Banana 2 / FLUX.2 Max ordering, and ρ = 0.246 reverses GPT Image 1 / GPT Image 2.
- The authors cannot identify ρ with two repeats and say so. However, they have request timestamps: the order was randomized, and collection ran 15:34–18:21 UTC. A drift diagnostic from existing data is therefore possible, and a small delayed third repeat would bound ρ.

**W6. Design limits on interpreting the shared change.** These are acknowledged in Sections 1, 6 and 7 and are not grounds for rejection.
- The design cannot separate movement toward these painters from a generic artist-name effect.
- There is one clause template.
- Four of six configurations are OpenAI variants.
- Section 6 already names the missing controls: a fictitious name, distant painters, or "Impressionist" as a group name. Adding one would strengthen the "What the shared change is" paragraph considerably. I list it as optional.

**W7. Density and a few hard-to-follow sentences.** The paper is precise, but the abstract contains about eleven numeric ranges and uses the benchmark terms before a reader can know them. Specific sentences:
- Abstract: "This alone does not indicate weak specificity: keeping each configuration's shared change and giving it exactly the painters' reference differences would still leave 57.6–84.2% shared, and moving the generic outputs exactly onto the painters' reference means would leave 84.8–95.2%." This is hard to parse on first reading. The reason, painters close to each other relative to their distance from the generic outputs, appears only in Figure 1 and Section 5.1.
- Abstract: "Proximity, agreement and recognition favor different configurations, several of them stably under scene resampling." It is unclear whether "several" refers to orderings or to configurations.
- Section 1, bullet 3: "only FLUX.2 Max is below that level in 94.2% of joint scene and reference resamples". "Only" misattaches.
- Section 5.1: "so in those two configurations a name partly acts as a stronger painting instruction; the two components overlap and do not add." It is unclear which two components are meant and why they would "add".
- Section 5.3: "shrinking each configuration's differences by one scalar fitted on the other 13 scenes gives GPT Image 2 the lowest held-out error, 0.554 against 0.714". The comparator (FLUX.2 Max) is not named. GPT Image 1 (0.645) and Sunburst (0.706) are also below 0.714 (Table 13), so a reader may wrongly infer FLUX.2 Max is second.
- Section 5.4: "For proximity, the difference follows from Equation 4". It is unclear which difference is meant.
- Appendix F: "Across the four combinations of source view and reference target". "Source view" is never defined.
- Appendix F: "The translation changes each class score by the constant t⊤₋ₛu_a and cancels exactly under centering across painters". The class-score shift differs across classes, which is exactly why recognition changes. What is invariant is the centered contrasts d_sak.
- Labels: the configurations are called "Flare" and "Sunburst" in the text and tables but "GPT Image 2.5 Flare/Sunburst" in Figure 2. The paper never says what these gateway variants are (preview or stealth endpoints?) or whether they can still be requested.

**W8. Some evidence is cited but not shown.**
- Section 5.6 cites "(Appendix Table 17)" for single-scene deletion and square measurement windows. Table 17 has neither.
- The crop-induced changes to resolved pairwise comparisons (Section 5.6) are not tabulated.
- The "at most 1.6 points" change under audited regions or the development-panel target (Section 5.2) is not tabulated.
- The 230-of-870 disagreement between title-derived and visual content labels (Appendix D) is not reflected where the main text reports title-derived content counts ("191 of 297 Monet works are water scenes", Section 3).

**W9. Minor presentation defects in figures and tables.**
- Figure 3: the rightmost x-tick label of the CSD panel ("100%") is clipped at the figure edge.
- Figure 4: the pair-error colorbar starts at 0, but one cell is −0.05 (Nano Banana 2, S–P).
- Appendix E, "Extraction" paragraph: very loose line justification caused by the long `\texttt` identifiers.
- Table 1 packs three kinds of quantities into ten columns (observed values, benchmarks, direction). The "direction" block could move to the appendix.

**W10. The primary data are not available.** Section 7 says "The generated images are not yet public, so features cannot be re-extracted from pixels by others." The services are closed and may drift, so the images are the only primary evidence.

---

## 5. Requested changes

### Critical (must change for acceptance)

1. **(critical) Scope the agreement claims to their representation and explain what drives them (W1).**
   - In the abstract and the Section 1 bullet, say that "three have larger errors than a generator that makes no painter distinctions" is a 31-feature result.
   - Report the CLIP and CSD D values with scene intervals, and ideally reference intervals, in the main text (Table 4 or a companion table).
   - State that the D > 1 verdicts come from differences that are over-sized (Q ≈ 2.2–2.4) and only partly aligned (β/√Q ≈ 0.5–0.6), not from missing responses.
   - Name the generated-versus-photographed scale mismatch as a possible contributor, with the D_held result as the relevant evidence.
   - Put the 31-feature separability limit (49.8% macro accuracy; Sisley 30.6%) next to the headline D claims, not only in Section 5.3.
2. **(critical) Support or remove the comparison with genuine paintings in Section 5.3 (W2).**
   - Report the central range of the content-sampled genuine control, against both the pooled and the content-matched targets.
   - Preferably also report where each configuration's D falls within that distribution.
   - Then rephrase "FLUX.2 Max's 0.801 is close to the content-sampled genuine level; the other configurations are not" to match what the spread shows.
3. **(critical) Document the premise the title argues against (W3).**
   - Cite concrete published evaluations that read proximity to an artist's works, or its gain over a baseline, as evidence of style fidelity, mimicry or erasure success. Alternatively, narrow the opening sentence and Section 1 paragraph 1 to what the cited literature shows.
   - Say explicitly how the analysed score (mean image-to-reference cosine, unnormalized prototype) relates to the scores used in that literature (normalized-prototype cosine; absolute similarity rather than gain).

### Minor

1. **(minor)** Rewrite the abstract so it states the argument in words before giving numbers, and keep only the ranges the argument needs. For example: "Even a generator that reproduced the painters' reference differences exactly would leave most of the change shared, because the four painters are close to one another relative to their distance from the generic outputs." Resolve "several of them stably under scene resampling".
2. **(minor)** Rephrase Section 1 bullet 3 ("only FLUX.2 Max is below that level in 94.2% …") so that "only" attaches correctly.
3. **(minor)** Qualify the texture claim (Section 1 bullet 5, Section 5.5) as a point-estimate ordering that is not resolved against spatial features, or drop it from the contribution list.
4. **(minor)** Qualify "mostly" for proximity. In 11 of 12 configuration–encoder pairs the scene lower bound exceeds 50%; GPT Image 2 in CSD is at 54.2% [47.4, 59.3].
5. **(minor)** In the main text, report the proximity-share decomposition with normalized prototypes as well. It remains exact because the score is linear in the image embedding. Also correct "cosine similarity to the prompted painter's prototype" (Section 4.4, the Table 4 caption and the abstract wording) to "mean cosine similarity to the painter's reference works", or equivalent.
6. **(minor)** Section 5.1: explain or remove "the two components overlap and do not add".
7. **(minor)** Section 5.3, last sentence: name the comparator for 0.554 and note that GPT Image 1 (0.645) and Sunburst (0.706) are also below FLUX.2 Max's 0.714 after rescaling.
8. **(minor)** Appendix D, "Scene aggregation and rescaling": change "GPT Image 2's differences are about twice the reference size" to "about twice in squared size (1.49 times in norm)", consistent with Section 5.3.
9. **(minor)** Section 4.2: add "mean zero" to the exchangeable-null condition, as in Appendix C. Without it, the 25% value does not follow.
10. **(minor)** Tabulate, or point to named supplementary files for, every quantitative claim not shown in a table:
    - single-scene deletion and square windows (Section 5.6; not in Table 17 as cited);
    - crop-induced changes in resolved pairwise differences;
    - the "at most 1.6 points" share change (Section 5.2);
    - the SD-Turbo within-scene values.
11. **(minor)** Appendix F: define "source view", and correct the sentence on the translation's effect on class scores (see W7).
12. **(minor)** Explain what the "Flare" and "Sunburst" configurations are as listed by the gateway, and whether they remain available. Use the same labels in Figure 2 and the tables.
13. **(minor)** Add a drift and repeat-dependence diagnostic from the existing request timestamps, or collect a small delayed third repeat on a subset of cells to bound ρ. At minimum, report how far apart in time the two repeats of each cell were requested.
14. **(minor)** Where the main text reports title-derived content counts and uses content-matched targets, note the 230-of-870 disagreement between title-derived and visual content labels.
15. **(minor)** Abstract "+6.5": the rounded Table 2 values give +6.6 for FLUX.2 Max in CSD (77.6 − 71.0). State that ranges are computed from unrounded values, or align the numbers.
16. **(minor)** Fix the clipped "100%" tick in Figure 3 (CSD panel), extend the Figure 4 error colorbar to cover −0.05, and allow line breaks in the Appendix E `\texttt` identifiers.
17. **(minor)** Commit to releasing the 1,008 generated images (and the SD-Turbo images), for example through an anonymized external host during review and a permanent archive at camera-ready. Remove the reliance on "not yet public".
18. **(minor)** Broader impact: add one sentence on dual use. Metrics that score whether a model reproduces an artist's *distinguishing* traits could also be used to optimize imitation of living artists. Mention a mitigation, such as reporting the metrics only for public-domain painters or pairing them with erasure evaluations.
19. **(optional)** A small additional arm with a fictitious name, a stylistically distant painter, or the group term "Impressionist" would let the "What the shared change is" paragraph (Section 6) say what the shared change is, rather than only what it is not.

---

## 6. Criterion 1: Are the claims supported by accurate and convincing evidence? **Partially.**

**Supported.**
- The central claims are supported by accurate, internally consistent evidence:
  - most of what the names add is shared, as a faithful imitator would also show (Table 1, Figure 3);
  - proximity gain is dominated by a name-independent term (Eq. 4, Table 2);
  - readouts rank configurations differently (Tables 4–5).
- The benchmarks are the right controls for these claims. The exact identities check out (Eq. 4/8, Eq. 5, Eq. 6, Eq. 7, the finite-sample bias of H).
- The prespecified status and the retrospective status of each analysis are stated honestly.

**Gaps and what would close them.**

| Gap | Where | What closes it |
|---|---|---|
| Agreement claims ("three have larger errors…") presented without their representation; embedding D has no intervals; D > 1 is driven by magnitude, possibly domain scale | Abstract; §1 bullet 3; §5.3; Table 4 | Critical change 1 |
| Genuine-painting comparison lacks the spread needed to claim FLUX.2 Max is "close" and the others are "not" | §5.3 ¶2; App. D | Critical change 2 |
| The practice being critiqued is asserted with thin citation; the analysed score differs from normalized-prototype practice | Abstract s.1; §1 ¶1; §4.4 | Critical change 3; minor change 5 |
| "Texture is the least shared" is not resolved against spatial | §1 bullet 5; §5.5; Table 6 | Minor change 3 |
| "Mostly" fails by interval for GPT Image 2 in CSD | Abstract; §5.2; Table 2 | Minor change 4 |
| Pairwise orderings and intervals rest on an untestable independence assumption, with documented fragility (ρ ≈ 0.25) | §7; App. A, C | Minor change 13 (drift diagnostic or third repeat) |
| Several sensitivity claims are cited to tables that do not contain them | §5.2; §5.6 | Minor change 10 |
| Primary data (images) not available for re-extraction | §7; Reproducibility statement | Minor change 17 |

None of these undermines the paper's main thesis. The first three concern headline statements that go beyond what the paper shows, so they must be fixed.

## 7. Criterion 2: Would some of TMLR's audience be interested, and is the writing clear? **Yes.**

- **Audience.** Researchers who evaluate style mimicry, style protection (Glaze-type work), concept erasure (UnlearnCanvas-type benchmarks) and artist attribution will find the shared/between-name split and the benchmarks directly usable. Section 6 gives four concrete reporting recommendations.
- **Clarity.** The paper says what it found (section headings state the findings), why it matters (proximity gain can rise without any painter-specific content), and what readers learn (Section 6).
  - Figure 1 conveys the geometry quickly.
  - Section 4 defines every estimator before use.
  - Limitations are specific.
- **Cost of density.** The density is real (W7), but it is local: the abstract, a handful of sentences in Section 5, and two appendix sentences. A motivated reader in the target community can follow the argument. The fixes above are editorial.
- **Machine-generation screen.** I found no generic, padded or boilerplate passages. Qualifications are specific and tied to numbers. Repeated statements of the retrospective status (abstract, Section 1, Section 4.5, Table 5 caption, Section 7) are slightly redundant but justified by their content.

## 8. Structure, length, figures and tables

- **Structure.** The order is conventional and logical: introduction, related work, design, estimators (with an inference-status subsection), results with findings as headings, discussion with recommendations, limitations, then the broader impact and reproducibility statements. The appendices A–H are well partitioned.
- **Length.** Main text runs about 12 pages (pp. 1–12, with the statements spilling onto p. 13), references pp. 13–15 and appendices pp. 16–25. This is appropriate for the content; TMLR sets no page limit.
- **Figures.** Figure 1 (schematic) is effective. Figure 2 (image panel, selected by a fixed rule) is informative, though the thumbnails are small. Figure 3 carries the main result well, apart from the clipped tick. Figure 4 (pair heatmaps) is readable, apart from the colorbar range.
- **Tables.** There are 20 tables, six in the main text. The main-text tables are dense but consistently formatted with booktabs, and all captions define their columns. Table 1 could be split. Tables 4 and 5 together make a good summary of the divergence between readouts.

---

## 9. Factual errors and inconsistencies found

1. **Appendix D, "Scene aggregation and rescaling".** "GPT Image 2's differences are about twice the reference size" contradicts Section 5.3: "its differences are 1.49 times the reference size in norm (Q = 2.223)". "Twice" holds only for squared size.
2. **Section 4.4, the Table 4 caption and the abstract.** The proximity readout is described as a gain in "cosine similarity to the prompted painter's prototype". With the unnormalized μ_a used here, g_aᵀμ_a is the mean image-to-reference cosine (Appendix E: "the average image-to-reference cosine similarity"), not a cosine to the prototype.
3. **Section 5.6.** "FLUX.2 Max keeps the lowest error estimate under every single-scene deletion, square measurement windows, … (Appendix Table 17)". Table 17 reports neither single-scene deletion nor square windows. Square windows appear only for the Monet–Sisley β in Table 14.
4. **Section 4.2.** "An exchangeable null, in which the four named shifts are independent and of equal expected size, gives a shared fraction of 25%". The condition "mean zero" (stated in Appendix C) is missing, and without it the 25% value does not follow.

(A rounding mismatch rather than an error: the abstract's "+6.5" versus +6.6 computed from the rounded Table 2 entries for FLUX.2 Max in CSD. claims.json shows the range was computed from unrounded values.)

## 10. Format checks performed

1. **Style files.** `tmlr.sty`, `tmlr.bst` and `fancyhdr.sty` in `paper/tmlr/` hash to the SHA-256 values recorded in `STYLE_PROVENANCE.json` (upstream JmlrOrg/tmlr-style-file, commit 7bf90efe…, `"modified": false`). The `tmlr.sty` content matches the standard TMLR file (header comments, 6.5 in × 9 in text block, natbib author-year). This is self-consistent; I did not re-download upstream.
2. **Submission mode.** `\usepackage{tmlr}` is loaded without `[accepted]` or `[preprint]`, and "Under review as submission to TMLR" appears on all 25 pages.
3. **Anonymization.**
   - Author block: "Anonymous authors / Paper under double-blind review".
   - No acknowledgments.
   - No identifying URLs or repository links.
   - PDF metadata has no Author field.
   - A string scan of the PDF found no author or account identifiers.
   - Self-reference to prior work is neutral ("the same project").
4. **Caption placement.** Captions are above all 20 tables and below all 4 figures, checked on every rendered page.
5. **Required statements.** A broader impact statement is present (Section after 7) and appropriate to this topic. A reproducibility statement and an AI-use disclosure are also present.
6. **Page setup and fonts.** Paper size is US letter (612 × 792 pt). There are no Type 3 fonts. All cross-references resolve (no "??").
7. **Preamble and layout.** There are no layout overrides (geometry, global spacing or font changes). Tables use local `\small`/`\footnotesize` and `\tabcolsep`, which is acceptable.
8. **Bibliography.** References use tmlr.bst in author-year style and are complete, with DOI or URL where applicable.
9. **Length.** Main text is about 12 pages, which is not unusually long under the TMLR author guidelines (checked at jmlr.org/tmlr/author-guide.html).
10. **Rendered-figure inspection.** Figure 3 has a clipped tick label. The Figure 4 colorbar does not cover −0.05. Appendix E has loose justification.
11. **Supplementary archive.** Not inspected; it is outside the permitted inputs. The authors should make sure the "request records" in the supplement contain no account or API identifiers.

## 11. Numerical spot checks performed (all consistent unless noted)

- Table 3: D = 1 − 2β + Q for all six configurations; √2.223 = 1.49.
- Table 10: N_free = G + N + I; shared fractions N/(N + B) and N_free/(N_free + B).
- Table 1: the exact-differences column equals N/(N + 1) in units of H; the "along generic" column equals cos(c, g)² from Table 11; Nano Banana 2 has the smallest B.
- Table 11: β with corrected H = β/0.933; the range 0.474–1.071 matches Section 5.6.
- Table 2: differences from the faithful benchmark range from −2.8 to +6.6 on rounded values (+6.5 unrounded).
- Table 6: family means 74.3, 71.5 and 68.2, and the all-feature mean 72.9; the per-configuration least-shared family matches Section 5.5.
- Table 19: Cézanne is least shared in 11 of 12 configuration–encoder pairs.
- Table 20: the Shift and Gen. mean changes (+2.7, +16.1, +10.0, +25.0) and the ranges −5.4 to +12.5 and +0.9 to +26.8; the Gen. rule beats both reference rules in 12 of 12 combinations; 39 − 9 = 30 of 112 = 26.8 points.
- Table 12: exactly two intervals exclude zero (Flare and Sunburst vs FLUX.2 Max).
- Table 13: κ = β/Q ≈ 0.45 for GPT Image 2.
- Appendix C: the identities for Eq. 5, Eq. 6 (centroid proximity), Eq. 4/8, Eq. 7 and the finite-sample bias of H (3/4 Σ tr Σ_a/n_a) verified algebraically; the Bonferroni quantile t₁₃,₁₋₀.₀₅/₄₂ is consistent with 21 two-sided tests.
- The label swap "lowers the overall error, as it must when the pair alignment is negative" is verified algebraically.
