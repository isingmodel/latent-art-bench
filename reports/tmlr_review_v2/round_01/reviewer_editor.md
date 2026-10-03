# TMLR action-editor assessment, round 01

**Submission:** "Proximity Is Not Specificity: What Painter Names Add in Text-to-Image Generation" (anonymous)
**Role:** editor (desk screen, clarity, structure, length, figures/tables, format)
**PDF read:** `reports/tmlr_review_v2/round_01/input/manuscript.pdf`, 38 pages, all pages inspected as rendered (main text pp. 1–16, references pp. 17–18, appendices A–I pp. 19–38)
**PDF SHA-256:** `af4eea64c0750637d2695ce49f017ca8c45357d476eead26aed361e48fa3ecef`

---

## 1. Desk-rejection decision

**Not desk-rejected. The submission goes to review.**

- **Scope.** The paper is about how to evaluate text-to-image generators, specifically what artist-name proximity and recognition readouts measure. That is in scope for TMLR (generative models, evaluation methodology).
- **Format.** It uses the official, unmodified TMLR style in anonymous mode. Table captions sit above tables and figure captions below figures. A broader impact statement is present. Details are in §10.
- **Anonymity.** I found no identifying metadata or text. One phrase about "rounds of review" should be fixed (minor change m1).
- **Quality.** The paper is technically careful. The decomposition identities check out (I verified Eqs. 1, 2, 4/8, 5, 6, 7, the exchangeable-null value of 1/4 and the finite-sample bias of H). About 100 numbers spot-checked between the text, tables and abstract agree. Prespecified and post hoc analyses are separated explicitly.
- **Machine-generation screen.** The paper does not read as low-care machine-generated text. The prose is idiosyncratic and very compressed rather than generic or padded, and almost every sentence carries a specific number or definition. AI assistance for code, audits and editing is disclosed (p. 16), which matches TMLR's LLM policy. The writing problem is the opposite of padding: in places it is so dense that it is hard to follow (§4, W5).

## 2. Summary

The paper asks what artist-style proximity measures. Six commercial text-to-image configurations (four OpenAI GPT Image routes, two of them undocumented "2.5 Flare/Sunburst" variants, plus Nano Banana 2 and FLUX.2 Max) rendered 14 authored scenes under six clauses, twice each (1,008 images): no instruction, a generic oil-painting instruction, and "in the style of" Monet, Sisley, Pissarro or Cézanne.

**The split.** What the names add beyond the generic clause is split into:
- a **shared change** c, the mean over the four names;
- **between-name differences** e_a.

Squared sizes are estimated without noise bias by taking products across the two repeats.

**Benchmarks.** Two reference points come from 649 public-domain reproductions:
- a **faithful imitator**, which lands exactly on each painter's reference mean;
- an **exact-differences** generator, which keeps the observed shared change but reproduces the reference differences exactly.

**Main findings**
- **First collection.** In 31 interpretable features the shared fraction is 66.7–88.4%. A faithful imitator would show 84.8–95.2%.
- **Second collection** (prespecified H1/H2, 1,680 requests), with two further groups: four painters from four centuries and four Hudson River School painters.
  - Shared fraction: 17.7–29.5% for the century group, 89.4–98.6% for the Hudson River School.
  - Across the 28 pairs, name distances rise with reference distances (Spearman 0.85/0.86/0.92).
- **Proximity identity.** For CLIP and CSD an exact identity (Eq. 4) splits the gain in linear proximity into a shared term and a painter-specific term Hβ/4. For related painters the shared term supplies most of the gain and tracks the differences between configurations.
- **Specificity readouts.** Specificity is then read from the aligned amplitude β, relative size Q, alignment ratio β/√Q and error D.
  - Readout rankings disagree across representations.
  - Only 2 of 15 prespecified pairwise D comparisons are resolved.
- **Output.** The paper ends with concrete reporting recommendations for artist-style evaluation.

## 3. Strengths

1. **A clean, useful identity.** Eq. 4 shows that the named-minus-generic gain in any proximity score that is linear in the image embedding equals a shared term plus Hβ/K. This is exact, simple and directly usable by anyone who reports CSD or CLIP prototype similarity. Its practical consequence is stated explicitly (p. 7): the shared term dominates whenever it exceeds H/4.
2. **Benchmarks that make the main number interpretable.** Without the faithful and exact-differences benchmarks, "66.7–88.4% shared" would be uninterpretable. With them, readers can see that a high shared fraction is expected for related painters (Table 1, Figure 3).
3. **A prespecified second collection that tests the central reading** (H1, H2; §4.5, Appendix H). It includes recorded predictions (Table 30) and an exact permutation test. Both tests pass in all three representations (Table 31).
4. **Transparent inference status.** §4.5 says plainly which comparisons were prespecified, which were defined after collection, and which plans were written with outcomes partly known. The abstract ends with "Beyond the prespecified tests, the analyses are descriptive."
5. **Strong internal consistency.** Abstract ranges, in-text ranges and table entries match throughout. Identities such as D = 1 − 2β + Q, D = D_agg + V_scene and the proximity sums reproduce from the printed tables to rounding.
6. **Limitations are named.** These include the familiarity confound, repeat dependence (with the break-even repeat correlations quantified, Table 24), the weak painter separation of the 31 features, and the absence of human validation.
7. **Actionable recommendations** (p. 15) for evaluators.

## 4. Weaknesses (with locations)

### W1. The second collection is credited to closeness more strongly than its own benchmarks allow (abstract p. 1; Intro bullet 2 p. 2; §5.2 heading and text pp. 9–11) — *claims/evidence*

The abstract says the high shared fraction "is expected even of good imitation when the painters are close to one another relative to their distance from the generic outputs, and a second collection whose tests were fixed in advance confirms it". §5.2 is titled "The shared fraction tracks how close the painters are."

The paper's own faithful benchmark is the closeness-only prediction: it depends only on H relative to the distance to the paintings. Averaging Table 2 over configurations, it accounts for well under half of the observed group differences:

| Contrast | Observed difference (points) | Faithful-benchmark difference (points) |
|---|---|---|
| Century − Hudson River | −72.7 | about −30.9 (62.7 vs 93.6) |
| Impressionists − Hudson River | about −21.4 (72.9 vs 94.4) | about −3.7 (89.9 vs 93.6) |
| Century − Impressionists | about −51.3 | about −27.2 |

The rest comes from what the generators do with the names:
- The century group's names produce differences larger than the reference differences (Q = 1.41–3.13, Table 32). This pushes the observed fraction 25–45 points below its faithful value.
- The Hudson River names barely differ (β ≈ 0), so the observed fraction meets or exceeds its faithful value.

That generator-side component is exactly the part confounded with name familiarity, which the paper itself acknowledges (p. 2 last paragraph, p. 15, p. 16). In short, H1 confirms the direction predicted by closeness. It does not show that closeness explains the size of the shared fraction. The abstract's "confirms it" and the §5.2 heading attribute the effect to closeness alone.

What would close the gap:
- In Table 2, report the faithful-predicted and exact-differences (N/(N+H)) contrasts next to the observed H1 contrast.
- Say in the text how much of the 72.7 points closeness accounts for.
- Reword the abstract, bullet 2 and the §5.2 heading. For example: the shared fraction depends on both how close the painters are and how strongly the generator separates the names; the second collection confirms the predicted ordering.

### W2. "Near their size" overstates the century-group agreement (abstract p. 1; Intro bullet 2 p. 2; §5.2 p. 11) — *claims/evidence*

The abstract says "the generators reproduce the distant painters' differences in the right direction and near their size". §5.2 says they "match the reference differences in direction and roughly in size: β is 0.840–1.292".

β is only the amplitude along the reference pattern. The same table (Table 32) shows:
- Q = 2.22–3.13 for five of six configurations. The scene-wise generated differences are 1.5–1.8 times the reference size in norm.
- The prespecified error D is 0.94–1.58 for five of six configurations. Only FLUX.2 Max is resolved below 1 (0.73 [0.60, 0.85]).

By the paper's own prespecified error, then, most configurations do no better on the century group's 31-feature differences than making no distinctions at all. The embeddings are better (Table 33, D 0.61–1.04).

Fix: the abstract and §5.2 should say "in the right direction, with amplitude near 1 along the reference pattern but with large off-pattern differences", and should give D next to β.

### W3. The primary data are not available for verification (p. 16, p. 38) — *claims/evidence and reproducibility*

The paper says: "The generated images are not part of the anonymous supplement, so features cannot yet be re-extracted from pixels by others."

Two of the six configurations are undocumented, and the authors cannot guarantee their availability (p. 4): "we have no further documentation of how they differ and cannot guarantee that they remain available." The other services are closed and versionless. The 2,686 generated images are therefore the only durable primary evidence. The replay check in Appendix I explicitly stops at the retained feature vectors.

TMLR's 100 MB supplement limit is a reason to host the images elsewhere, not a reason to omit them. Options:
- an anonymized external link now (OSF, Zenodo or figshare with anonymous view);
- or, at minimum, a firm commitment in the paper to release all images, for example the 512-pixel resized versions that were actually measured, on acceptance.

### W4. Two further claim/evidence details

- **Feature-space proximity for the century group** (Table 32, p. 36, not discussed in the main text). In the 31-feature centroid proximity (Eq. 6), the shared term supplies 73.0–100.7% of the gain for five of six configurations in the century group (31.5% for FLUX.2 Max). That is far above the 6.5–49.0% quoted for the embeddings (p. 11: "Proximity follows suit"). The main-text sentence is correctly limited to "embedding proximity gain". However, the paper should say that a squared-distance proximity, which penalizes oversized between-name differences through −¼Σ‖e_a‖², still reads as mostly shared for the distant painters. Otherwise readers will over-generalize "for distant painters proximity is mostly specific."
- **The headline generic-baseline split was defined after collection** (p. 8: "Everything else, including the generic-baseline split, the benchmarks, …, was added afterwards"). The prespecified artist-free split gives 82.5–95.7% (Table 10). The post hoc choice is the conservative one for the paper's claim, so this is not a problem of substance. But §5.1 should say in one sentence that the prespecified baseline gives a higher shared fraction. At present a reader has to put §4.5, §5.1 and Appendix D together.

### W5. Density impedes reading in specific places — *clarity*

The paper's overall message is clear: the title, Figure 1, the results subsection headings and the recommendations all communicate it. Several passages, however, are compressed to the point where a TMLR reader outside this niche will struggle.

- **Abstract (285 words, p. 1).** It carries about ten numerical ranges and three technical constructs before the reader has any definitions. Trimming it to about 200 words, with two or three numbers, would help. The sentence "In those embeddings, an exact identity splits any proximity gain that is linear in the image embedding into a term that ignores which name was used and a painter-specific term; for related painters the first supplies most of the gain and drives the differences between configurations" is precise but heavy. "Drives" is causal language for a six-point correlation.
- **Intro bullet 4 (p. 2)** is the hardest passage in the paper: "Descriptively, in the 31 features, which separate genuine Monet and Sisley works poorly, Flare and Sunburst err more than a generator making no painter distinctions, mostly through differences off the reference pattern (GPT Image 1 too, but not after a multiplicity adjustment); in CSD four configurations are resolved below that level and none above it (Section 5.4)." This uses D, its off-pattern split, multiplicity status, resolution and representation dependence, none of which has been defined yet. The contributions list should give the finding ("the error D ranks configurations differently in each representation and resolves only 2 of 15 prespecified comparisons") and move the detail to §5.4.
- **§4.3 (p. 7)** introduces β, Q, β/√Q, D, the along- and off-pattern split, D_held, D_agg, V_scene and the scene-averaged alignment β/√(B/H) in one paragraph: "Rescaling the differences optimally would leave D = 1 − β²/Q; D_held applies such a rescaling fitted on the other scenes and therefore closely follows the alignment ratio. Every scene is compared with the same pooled target, so D also penalizes differences that vary across scenes: D = D_agg + V_scene, where D_agg scores the scene-averaged differences and Q = B/H + V_scene; the scene-averaged alignment is β/√(B/H)." D_agg, V_scene and the scene-averaged alignment are each used only once or twice in the main text. Moving them to Appendix C would leave §4.3 with β, Q, β/√Q and D, and a small diagram analogous to Figure 1 (reference pattern versus generated differences, along/off) would help considerably.
- **§5.2 (p. 11), two hard-to-parse sentences.** "Small panels do not explain this: correcting the Hudson River School's spread for panel size lowers it from 6.24 to 4.21, so an imitator of the corrected means would still show β near 0.68 against the observed pattern." It is unclear which "observed pattern" (the uncorrected reference pattern) and why 0.68 (= 4.21/6.24). "The Impressionists lie between the two groups." It is unclear on which quantity: shared fraction, β, recognition, or all of them.
- **Discussion (p. 15).** "our design still cannot tell movement toward a group from a generic effect that any artist name would have; a fictitious name or a clause naming the group ("Impressionist") would." The elliptical "would" should be expanded: "adding a fictitious-name or group-name clause would separate these."
- **§4.5 (p. 8).** "its scene fixed-effects regression reproduces the pairwise differences, and a projection of the means (Appendix Figure 6) replaces its reference PCA display of full distributions." This is a protocol deviation phrased so obliquely that it reads as description. Say plainly that the prespecified PCA display of full distributions was replaced by a projection of means, and why.
- **Results prose (§5.4, pp. 12–14)** often puts four to six numbers per sentence that already appear in Tables 5, 6 and 15. Keeping one or two numbers per claim and pointing to the tables would cut about a page and make the argument visible.

### W6. Presentation and table issues

- **"After … the first rounds of review"** (p. 4: "we added two groups after the results above and the first rounds of review"; Appendix H p. 34: "After the four-painter results and the first rounds of review"). TMLR reviewers will read this as a reference to a prior review process they cannot see, possibly a rejected TMLR submission, which TMLR requires to be declared and linked. If the reviews were internal, say "after analysing the first collection". If it was a prior venue, follow TMLR's resubmission policy.
- **Table 2 (p. 9).** The FLUX.2 Max interval [−198.2, +90.2] is striking and is explained only in Appendix H ("both of its fractions are unstable under resampling"). Add a note to the caption: the ratio is unstable when the resampled denominator approaches zero.
- **Table 32 (p. 36).** The "–" in "shared gain" for Hudson River / GPT Image 1 is not explained.
- **Table 31 / Appendix H (p. 34).** The text says "H1 and H2 hold in every representation, in the central square window …". H1 is identical in the full and central-square rows (−72.7 [−76.5, −62.6]) because the shared fraction does not use the references. Say that it is unchanged by construction rather than presenting it as a robustness result.
- **Figure 4 / H2 definition.** The protocol and the Table 31 caption define H2 as the Spearman correlation "averaged over configurations", meaning the mean of six per-configuration correlations. Figure 4 plots configuration-averaged distances with ρ in the panel title. State which statistic the titles show, so that readers do not recompute ρ from the plotted points and get a different value.
- **Third-person framing of the "Two further painter groups" paragraph (p. 4).** It belongs under Design but reads as project history. It would be cleaner to present the design as two collections from the start of §3 and keep the history in Appendix H.
- **Float placement in the appendix** leaves pages 30, 35, 36 and 37 about half empty. This is cosmetic.

### W7. Data and service provenance (acknowledged, but worth tightening)

- **Undocumented services.** Two of the six configurations are services whose identity the authors cannot document (p. 4, Appendix A). The paper rightly speaks of "configurations". The phrase "Six commercial text-to-image configurations" in the abstract should say "four of them OpenAI routes, two undocumented", so that readers do not take this as six independent models.
- **AI audits not checked by a human.** "a visual audit by AI assistants, not checked by a human, disagreed with the title-derived class for 230 of 870 works" (p. 4), and the crops of 131 works "were not verified by a human" (p. 15). These enter only sensitivity analyses, not the primary ones, so the impact is limited. A human check of a random sample (say 50 works) would cost little and remove the caveat.
- **Missing positive control.** The paper says "None of these readouts has been validated … against a positive control with known painter differences" (p. 15). The held-out genuine-painting control (Table 16) is a partial positive control for D. The sentence should acknowledge it and say what is missing: a generator with known painter differences, for example a per-painter fine-tuned model or retrieval of held-out works passed through the same pipeline.

## 5. Requested changes

### Critical (must change for acceptance)

- **C1 (W1).** Recalibrate the second-collection claim.
  - Add the faithful-predicted and exact-differences contrasts for H1 to Table 2 (closeness accounts for about −31 of the observed −72.7 points; Impressionists versus Hudson River: about −4 predicted against about −21 observed).
  - Say in §5.2 that the rest reflects how strongly generators separate the names, which is confounded with familiarity.
  - Reword "confirms it" (abstract), Intro bullet 2 and the §5.2 heading accordingly.
- **C2 (W2).** Replace "near their size" (abstract) and "roughly in size" (p. 11) for the century group with a statement that gives Q (1.41–3.13) and D (0.73–1.58 in the features; only FLUX.2 Max resolved below 1). The agreement is in direction and in amplitude along the pattern, with large off-pattern differences.
- **C3 (W3).** Make the generated images available: an anonymized external link now, or at least a stated commitment to release them, including the 512-pixel versions that were measured, on acceptance. Two of the six configurations may no longer exist, so the images are the only primary evidence.

### Minor

- **m1.** Remove or explain "after … the first rounds of review" (p. 4, Appendix H). If this is a resubmission of a rejected TMLR paper, link the earlier submission as TMLR requires.
- **m2.** Shorten the abstract to about 200 words with at most three numerical results.
- **m3.** Rewrite Intro bullet 4 as a one-sentence finding and move the detail to §5.4.
- **m4.** Slim §4.3 to β, Q, β/√Q and D (move D_agg, V_scene, D_held and the scene-averaged alignment to Appendix C), and add a schematic of along- versus off-pattern differences.
- **m5.** Rewrite the "β near 0.68 against the observed pattern" sentence and "The Impressionists lie between the two groups" (p. 11) so the quantity is named.
- **m6.** In §5.3 or §5.2, mention that in the 31-feature squared-distance proximity (Eq. 6, Table 32) the shared term still supplies 73.0–100.7% of the century group's gain in five of six configurations, and explain the difference from the linear embedding readout.
- **m7.** In §5.1, note in one sentence that the prespecified artist-free split gives 82.5–95.7% and that the generic baseline adopted after collection is the conservative choice.
- **m8.** Explain the FLUX.2 Max interval in the Table 2 caption, and the "–" entry in Table 32.
- **m9.** State in the Figure 4 caption which Spearman statistic the panel titles report (the mean of the per-configuration correlations, or the correlation of the averaged distances), consistent with the H2 definition.
- **m10.** Say that H1 is unchanged by construction in the central-square row of Table 31, rather than listing it as a robustness result.
- **m11.** In §4.5, state the PCA-display deviation explicitly as a deviation from the protocol.
- **m12.** Expand the elliptical "a fictitious name or a clause naming the group ("Impressionist") would" (p. 15).
- **m13.** Optional but helpful for the familiarity confound: report H2 with group membership partialled out (or stratified into within- and across-group pairs), and correlate a simple familiarity proxy (for example Wikidata sitelinks or Commons file counts) with β across the twelve painters.
- **m14.** Say in the abstract that four of the six configurations are OpenAI routes and two are undocumented variants.
- **m15.** Acknowledge in the Recommendations paragraph that the genuine-painting control (Table 16) is a partial positive control, and name the missing generator-side positive control.
- **m16.** Have a human check a random sample of the AI-audited content classes and crops, or state why this is unnecessary.
- **m17.** Cut repeated numbers from §5.4 prose that already appear in Tables 5, 6 and 15. The main text currently runs about 15 pages; see the length note in §10.
- **m18.** Fix the appendix float placement (the half-empty pages 30 and 35–37).

## 6. Criterion 1: Are the claims supported by accurate and convincing evidence?

**Answer: partially.**

What is supported:
- **The core first-collection claims.** The identity (Eq. 4) is exact and correct. The shared fractions, benchmarks, proximity shares and readout disagreements are measured with appropriate noise correction and resampling, and they are reported consistently.
- **The prespecified tests.** H1 and H2 pass as specified.
- **The descriptive status of everything else.** It is stated honestly.

What is not yet supported as written:
- **Closeness credited for the whole group gap** (C1). The abstract and §5.2 credit the second-collection result to closeness. The paper's own faithful benchmarks show that closeness explains well under half of the group differences, and the rest is confounded with familiarity.
- **"Near their size"** (C2). The abstract's description of the century group is contradicted by the paper's own Q and D.
- **Verifiability** (C3). The pixel-level evidence cannot be checked by others.

None of these gaps needs new experiments. C1 and C2 can be closed with numbers the paper already has; C3 needs a data release.

## 7. Criterion 2: Would some of TMLR's audience be interested, and are the findings communicated clearly?

**Answer: yes.**

**Who would be interested.** Researchers who evaluate style imitation, mimicry protection, concept erasure or unlearning with CSD or CLIP prototype similarity, or with artist recognition. For them the identity and the benchmarks change how a commonly reported number should be read. The recommendations (p. 15) say concretely what to report instead.

**What a reader learns.** The main findings come through in the abstract, Figure 1, the results headings, Figure 3 and Table 2:
- for related painters, proximity gain mostly measures a group-level shift;
- that shift is expected even of faithful imitation;
- readouts that weigh the size of differences rank generators differently.

**Clarity.** The density problems in W5 (abstract, Intro bullet 4, §4.3, two sentences on p. 11) are real and listed as minor changes. They slow the reader but do not prevent the findings from being understood.

## 8. Desk-rejection risk

**Low.** The paper is in scope, uses the official TMLR format and is properly anonymized. Its quality is clearly above the desk bar. The residual risk comes from:
- length and density: about 15 pages of main content, 34 tables;
- the "rounds of review" phrasing, which an AE may query against TMLR's resubmission policy.

## 9. Recommendation and confidence

- **Recommendation: minor revision.** The critical changes are recalibrations of claims and one release of data. They need no new experiments.
- **Confidence: 4/5.** I checked the mathematics and the internal numerical consistency closely. I did not re-run the analyses or inspect the supplementary archive.

## 10. Format checks performed

1. **Style files.** SHA-256 of `paper/tmlr/tmlr.sty`, `tmlr.bst` and `fancyhdr.sty` match `STYLE_PROVENANCE.json` (JmlrOrg/tmlr-style-file commit 7bf90ef, `"modified": false`). I did not re-download the upstream files to compare; network use was limited to the TMLR author guide and editorial policies.
2. **Preamble.** `main.tex` loads `\usepackage{tmlr}` with no option (anonymous mode). It loads only amsmath, amssymb, booktabs, graphicx, hyperref, url and placeins. There is no geometry, spacing, font or margin override. `\small` and `\tabcolsep` are used inside tables only.
3. **Running header** "Under review as submission to TMLR" appears on every page. US Letter (612×792 pt), 10 pt, TMLR title block and sans-serif headings render correctly.
4. **Anonymization.**
   - The author block reads "Anonymous authors / Paper under double-blind review".
   - PDF metadata contain no Author or Title field (Creator "LaTeX with hyperref", Producer xdvipdfmx, CreationDate neutralized).
   - No author name, email or local path appears in the PDF bytes.
   - There is no acknowledgments section and no GitHub or Hugging Face link that identifies the authors.
   - The embedded figure PDFs carry only Matplotlib metadata.
   - The phrase "first rounds of review" (p. 4, p. 34) is flagged as m1.
5. **Captions.** All 34 table captions are above their tables and all 6 figure captions below their figures. Counted from the text extraction: 40 caption lines.
6. **Cross-references.** No unresolved "??" references in the extraction.
7. **Broader impact statement.** Present (unnumbered, before the references, p. 16). It addresses misreading as a quality ranking or as evidence on attribution and legal questions, potential misuse for optimizing imitation of living artists, licensing of the reproductions (public domain, CC0, CC BY/BY-SA), and the absence of living artists or human participants.
8. **Other statements.** A reproducibility statement and an LLM-use disclosure are present (p. 16), consistent with TMLR's LLM policy.
9. **Length.**
   - Main content runs about 15 pages (pp. 1–16, including the statements), references 2 pages, appendices 20 pages.
   - TMLR sets no page limit, but says length "should be justified by its content". On OpenReview a submission with more than 12 pages of main content should be entered as a long submission.
   - Shortening the main text toward 12 pages (W5, m17) would also help clarity.
10. **References.** The tmlr.bst author-year style is used consistently. Recent (2026) arXiv and journal entries carry identifiers.
11. **Supplement.** TMLR allows 100 MB as PDF or ZIP. The generated images are excluded for size reasons; see C3.
12. **Figure legibility.** Figures 3–6 are legible at 100%. The axis fonts of Figure 4 are small but readable. Figure 2's painting reproductions are labelled with title and source.

## 11. Numerical consistency checks performed (no errors found)

I recomputed the following from the printed tables:
- N/(N+B) and N/(N+H) for all rows of Table 1;
- D = 1 − 2β + Q and β/√Q for every row of Tables 5 and 6;
- along + off = D and D_agg + V_scene = D in Table 15;
- shared + painter-specific = total in Table 4;
- the H1 mean of −72.7 from Table 2;
- all abstract and introduction ranges against Tables 1–6, 32 and 33;
- the six-point Spearman values (0.94, 0.89, 0.60–0.77, −0.14 to 0.66) from the Table 4 ranks;
- recognition shift ranges (−5.4 to +12.5 and +0.9 to +26.8) from Table 27, in multiples of 1/112;
- the Cézanne "11 of 12" claim from Table 26;
- the counts 649, 221, 870, 788, 1,008, 1,680, 104, 26 and 40,320.

Small last-digit differences (for example +6.5 versus +6.6 from rounded Table 3 values) are explained by the stated use of unrounded values.

## 12. Factual errors

None found. The items in W1 and W2 are over-statements relative to the paper's own evidence, not factual errors.
