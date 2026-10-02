# TMLR action-editor screen and review

**Submission:** "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation" (anonymous)
**Role:** action editor (desk screen, clarity, structure, length, figures/tables, format)
**PDF read:** `reports/tmlr_review_v1/round_06/input/manuscript.pdf`, 32 pages. I read all of it as rendered (pp. 1–32), cross-checked it against the text extraction, and read the LaTeX sources in `paper/tmlr/`.
**PDF SHA-256:** `4ae5600ec39d49e52f30a105432d92b809d117d71d0c3e8627ccd6405209a242`

---

## 1. Desk-rejection decision

**Not desk-rejected.** The paper can go out for review once the supplementary-material issue in C1 is fixed. That fix has to happen before the paper is uploaded.

- **Scope:** in scope. The paper evaluates text-to-image generative models and analyzes metrics used in style-imitation research (CSD, CLIP, recognition).
- **Format:** the PDF complies (checks in §10). The official style is used in anonymous mode, table captions sit above tables and figure captions below figures, and a broader impact statement is included.
- **Anonymity of the PDF:** clean. The author block is anonymous, there are no acknowledgments, and the PDF metadata carries only Creator/Producer. A scan of every decompressed content stream found no identifying strings; the only hit for "fred" is "Alfred Sisley".
- **Anonymity of the supplementary material: not clean as the sources stand.** `paper/tmlr/make_supplement.py` packs every file under `paper/tmlr/` into the archive (`HERE.rglob("*")`, lines 79–88), and that includes the script itself. Line 47 of the script is a regex that spells out the author's GitHub handle, first name, email domain and email local part (`isingmodel|…|kibum|kakao|neuralnetwork@|github\.com/isingmodel`). Lines 101–102 then exempt the script from its own identifier scan. TMLR requires the supplement to be anonymized ("Like submissions, supplementary material must be anonymized"), so uploading the archive as built would break double-blind review and could trigger a desk rejection. The scan also skips `.pdf`, `.npz` and `.gz` members; I checked the figure PDFs under `paper/tmlr/` and their metadata are clean.
- **Quality / machine generation:** the paper does not read as low-care machine-generated text. I checked about 60 numbers in the text against the tables and against each other: Table 1 fractions against N/H and B/H, D = 1 − 2β + Q, D = D_agg + V_scene, the split of D into along- and off-pattern parts, the Spearman values, the recognition deltas, the counts of resolved pairwise contrasts, the reference counts, and the effect of the H-bias correction. **I found no discrepancies.** AI use is disclosed. The risk in the prose is over-compression, not padding (see W2).

## 2. Summary

The paper asks what "proximity" (similarity of generated images to an artist's works) measures when the prompted artists are related. Six commercial text-to-image configurations each rendered 14 authored scenes under six clauses, twice each: no painting instruction, a generic oil-painting instruction, and the generic instruction "in the style of" Monet, Sisley, Pissarro or Cézanne (1,008 images). Relative to the generic clause, what the names add is split into a change shared by all four names (N) and between-name differences (B). Squared sizes are estimated from cross-repeat inner products so that sampling noise does not bias them upward. Two reference benchmarks come from 649 Wikimedia reproductions: a *faithful imitator*, whose named means equal the reference means, and an *exact-differences* generator, which keeps the observed shared change but reproduces the reference differences exactly.

Main findings:
1. In 31 hand-crafted features, 66.7–88.4% of the squared change is shared. A faithful imitator would give 84.8–95.2% and the exact-differences generator 57.6–84.2%, so a large shared fraction is expected and says little about specificity.
2. For any proximity score that is linear in the image embedding, an exact identity (Eq. 4) splits the named-minus-generic gain into a name-agnostic shared term and a painter-specific term Hβ/4. In CLIP and CSD the shared term supplies 54.2–83.8% of the gain. It also accounts for most of the between-configuration variation in gain: correlations 0.96/0.95, and the shared term's variance across configurations exceeds the painter-specific term's by a factor of 11 in CLIP and 5.8 in CSD.
3. Specificity is read from the between-name differences. All configurations align positively with the reference pattern (β > 0), and GPT Image 2 has the best direction-only alignment ratio β/√Q in all three representations. The size-penalizing error D ranks the configurations differently in each representation.
4. Recognition tracks the alignment ratio, proximity tracks the shared change, and D favors small differences.

The analyses are partly prespecified (a 21-comparison family in the features) and otherwise descriptive, with extensive sensitivity checks and a replay script.

## 3. Strengths

- **A simple, reusable conceptual result.** Eq. 4 (p. 7; derivation in App. E, p. 27) is exact and representation-agnostic. It gives practitioners a concrete reason why proximity gain in CSD-style prototype scoring cannot on its own indicate artist specificity. The "shared term > H/4" condition (p. 7) and the recommendation to report both benchmarks (p. 13) are directly actionable.
- **Careful design for a black-box setting.** The generic-style control, the artist-free baseline (App. C/D), cross-repeat estimators, and the pair of benchmarks that separate the photo-vs-generation gap from between-name structure are well chosen. Figure 1 (p. 3) and Figure 3 (p. 9) convey the core idea well.
- **Transparent inferential status.** Section 4.5 states what was prespecified, what was added afterwards, and what was known when. The authors also report adverse or weak results: the 31 features separate Monet and Sisley poorly (49.8% macro), GPT Image 1's D includes 1 under a Bonferroni correction over the six configurations, and repeat-dependence thresholds are given.
- **Internal consistency.** Numbers agree across abstract, introduction, results, tables and appendices (see §1). The replay design in App. H is unusually rigorous.
- **Honest limitations** (Section 7) and an adequate broader impact statement.

## 4. Weaknesses (with locations)

**W1. The supplementary archive would de-anonymize the authors** (`paper/tmlr/make_supplement.py`, lines 47 and 79–102). Details are in §1. This is a submission-blocking compliance issue, not a scientific one.

**W2. Density makes the specificity half of the paper hard to follow (Sections 4.3, 4.5, 5.3, 5.5).** The first finding (shared change, Eq. 4) is communicated clearly. The second finding (how to read specificity) is buried under symbols and robustness detail. The main text runs about 13.2 pages: Limitations end near the top of p. 14. It contains more than 20 forward references to appendix tables (Tables 10–25), and a reader needs about 15 symbols (N, B, H, N\*, t, λ, β, Q, β/√Q, D, D_agg, V_scene, D_held, κ, ρ) to follow Sections 4–5. Examples:
- p. 6, §4.3, one paragraph that introduces β, D, κ, Q, the along/off split, β/√Q, D_held, D_agg, V_scene and the genuine-painting control: *"Every scene is compared with the same pooled target, so D also penalizes differences that vary across scenes: D = D_agg + V_scene, where D_agg scores the scene-averaged differences and Q = B/H + V_scene. Genuine paintings do not reach D = 0 either when two works per painter stand in for the two repeats of a scene, so we also report that error for held-out reference paintings."*
- p. 7, §4.5: *"It also prescribed unadjusted intervals and a paired-scene bootstrap for the pairwise differences (Appendix Table 13), resampling of the reference works within painter, the artist-free shared/between-name split, the split of D along and off the reference pattern, and distribution diagnostics (Appendix Table 20); its scene fixed-effects regression reproduces the pairwise differences, and a projection of the means (Appendix Figure 5) replaces its reference PCA display of full distributions."* This reads as a protocol audit log, not an explanation.
- p. 11, "Genuine paintings": *"Held-out reference paintings sampled like the generated images, two distinct works per painter and pseudo-scene scored against a target from the other half of each collection, have mean errors of 0.125–0.328 in the 31 features and 0.060–0.216 in the embeddings."*
- p. 11: *"The comparisons with 1 assume independent repeats: with a Bonferroni adjustment over the six configurations, GPT Image 1's interval for D, [0.935, 2.210], includes 1, and its error would fall to 1 if the two repeats shared a fraction 0.22 of their noise power, against 0.64 for Flare and 0.52 for Sunburst (Appendix A)."*
- p. 2, introduction bullet 3, which packs three representations, two metrics, a validity caveat and a mechanism into one sentence (quoted in W3).

Section 5.3 as a whole (pp. 10–12: Direction / Size / Embeddings / Genuine paintings / Aggregation) and Section 5.5 (pp. 12–13) read as robustness logs. A reader in the T2I-evaluation audience will take away finding 1 but will struggle to say what they learned about the six configurations' specificity.

**W3. Headline verdicts rest on the weakest representation and are stated without the caveats that appear later.** The 31 features are the prespecified primary representation, but the paper shows they separate genuine works poorly: 49.8% macro, with 39.6% of Monet and 30.6% of Sisley works correct, against about 80% for CLIP/CSD (p. 4). Yet introduction bullet 3 (p. 2) says: *"in the 31 features, which separate genuine Monet and Sisley works poorly, GPT Image 1, Flare and Sunburst err more than a generator making no painter distinctions, mostly through differences off the reference pattern."* This is stated without the qualifications from p. 11:
- the intervals are unadjusted;
- GPT Image 1's interval includes 1 under a Bonferroni correction over the six configurations;
- the verdict reverses at a repeat correlation of ρ = 0.22;
- the genuine-painting control "discriminates weakly there".

The same applies to "FLUX.2 Max has the lowest error" (p. 10). The introduction should present these as conditional, or lead with the representation-agnostic results (Eq. 4, direction/alignment) and subordinate the 31-feature D ranking.

**W4. Some interpretive claims rest on six points or go beyond the check performed.**
- p. 12: *"Recognition tracks the alignment ratio (Spearman 0.94 in CLIP and 0.89 in CSD): both reward differences in the right direction, whatever their size."* These are rank correlations over six configurations, with no interval, and both quantities are computed from the same projections onto the same reference prototypes, so part of the agreement is built in. The abstract's *"GPT Image 2 aligns best in all three representations, as it is also best recognized"* reads causally because of "as".
- p. 2 and p. 10: the gain "follows" or "drives" the shared term (r = 0.96/0.95 across six configurations). The paper notes that gain = shared + specific, which makes the correlation partly mechanical. The variance-ratio statistic (11 [4.6, 29.3] and 5.8 [2.5, 13.8]) is the better evidence and should lead.
- p. 11: *"Content does not explain the difference"*. Only title-derived content-class targets on 11 scenes were tested, so "Content-class matching does not change the errors or their order" is what the evidence shows.
- p. 11: *"Since direction-only agreement is consistent across representations, the representations differ mainly in how they weigh the size of the between-name differences"*. The cross-representation Spearman for β/√Q is 0.60–0.77 over six items. The consistency is mainly that GPT Image 2 is best everywhere.

**W5. The specificity readouts are definitional and not validated.** Section 4.3 (p. 6) defines specificity as agreement with reference-mean differences in a given representation, and p. 13 states that *"None of these readouts has been validated against perceptual or expert judgments or against a positive control with known painter differences."* The abstract's *"Specificity is better read from how the differences between names match the painters' reference differences"* should say it follows from that definition. The shared change also cannot be separated from a generic any-artist-name effect (p. 13). That does not undermine the proximity claims, but it leaves the "What Four Painter Names Add" interpretation open. A fictitious-name clause, a group clause ("Impressionist"), or a distant-painter clause on the same 14 scenes would cost a few hundred API calls and would close this gap.

**W6. Reproducibility of the closed-service data.**
- The generated images are not in the supplement (p. 14), so features cannot be re-extracted.
- Two of the six configurations (`gpt-image-2.5-flare`, `gpt-image-2.5-sunburst`) are undocumented gateway variants that "cannot [be] guarantee[d to] remain available" (p. 4).

The features are computed after resizing to a 512-pixel short side and the embeddings from 224-pixel crops. Releasing the 1,008 images at 512 px, losslessly, through an anonymous link would probably fit and would make the measurements re-derivable.

**W7. Revision residue and process jargon.**
- p. 21–22, App. D, and Table 15 (p. 24): *"An earlier version of this control drew the two works with replacement … which inflated that version's means (0.234, 0.753 and 0.731, first column)."* Reporting a superseded, biased control next to the corrected one is confusing unless the with-replacement control was prespecified. If it was, say so in one clause and move the column to the supplement.
- p. 32, App. H: *"appears in its registered sentence context"*. This is internal tooling vocabulary.
- p. 4 and p. 12: the AI-assistant audits are *"not checked by a human"* and *"the crops were not verified by a human."* These only feed sensitivity analyses. Still, a human check of the 131 crops is cheap and removes an easy reviewer objection.

**W8. Figure and table presentation.**
- Figure 1 (p. 3): the label "t: to reference centroid µ̄" overlaps a generated (blue) point.
- Figure 5 (p. 26): the letter labels overlap in several panels (Flare "S SM", Nano Banana 2 "S S M").
- Table 3 (p. 9) bolds the largest proximity gain as "best". That conflicts with the paper's thesis that gain is mostly shared movement. Bold only the agreement and recognition columns, or say that bold means "largest".
- The Figure 4 D colorbar starts at 0 while one cell is −0.05. The caption explains negative values, so this is fine.

**W9. Small wording issues.**
- p. 2, bullet 2: *"(less for Cézanne alone)"* is cryptic. Say "the shared share is lowest for Cézanne-prompted images (as low as 34.6%)".
- p. 6: the faithful imitator is *"an upper reference for the shared fraction"*. It is not an upper bound: a configuration with B < H can exceed it, and one with no between-name differences scores 100%. Use "a reference point, not a bound".
- p. 4: *"Appendix Table 8 lists every symbol"*. Table 8 omits N\*, t, G, I, N_free, κ and ρ.

## 5. Requested changes

**Critical (must change for acceptance)**
- **C1 — Anonymize the supplement.** Exclude `make_supplement.py`, or move the identifier regex out of the packaged files (for example, read it from an environment variable or an untracked file). Drop the self-exemption on lines 101–102. Also scan `.pdf` members' metadata and the inside of `.gz` members. Rebuild the archive and grep the final zip for the handle, name and email before uploading.
- **C2 — Restructure Sections 4–5 for readability and bring the main text to 12 pages or fewer.** Otherwise declare a long submission and accept the slower review; TMLR warns that unusually long papers delay review. Concretely:
  - put a short symbol/"reading guide" table in the main text (a condensed Table 8 with the 5–6 quantities needed to read Section 5);
  - split §4.3 into "direction" (β, β/√Q) and "size" (Q, D and its splits) with one sentence of intuition each;
  - move the protocol-deviation detail of §4.5 to an appendix and keep one summary sentence;
  - move the repeat-dependence thresholds, the Bonferroni variants, the 11-scene content checks, the source-audit results and SD-Turbo out of Section 5 into the appendix, leaving a one-line pointer for each.
- **C3 — Align the introduction and abstract claims with their evidence.**
  - Qualify introduction bullet 3's D > 1 verdicts: unadjusted, conditional on independent repeats, and made in a representation that separates Monet/Sisley poorly. Alternatively, drop them from the bullet.
  - Replace "as it is also best recognized" with "and is also best recognized".
  - State that "Recognition tracks the alignment ratio" is a rank agreement over six configurations; add scene-resampling intervals for the two Spearman values, or rephrase it descriptively.
  - Lead the between-configuration claim with the variance ratio, not the correlation.
  - Tie "Specificity is better read from…" to the paper's operational definition.

**Minor**
- M1. Rephrase "Content does not explain the difference" (p. 11) to what was tested, and soften "direction-only agreement is consistent across representations" (p. 11).
- M2. Call the faithful imitator a reference point rather than an "upper reference" (p. 6), and state that it is not a bound.
- M3. Fix "Appendix Table 8 lists every symbol" (p. 4), or complete Table 8.
- M4. App. H (p. 32) lists Figures 1, 3 and 4 as generated but omits Figure 5 (`fig_projection.pdf`, which is generated). Make it consistent with the reproducibility statement ("all figures except … Figure 2").
- M5. Remove or justify the superseded with-replacement genuine-painting control (Table 15 first column; App. D, pp. 21–22). Replace "registered sentence context" (App. H) with plain language.
- M6. Have a human verify the 131 AI-proposed crops and a sample of the 230 content-label disagreements, and report the outcome in one sentence.
- M7. Release the generated images (for example losslessly at the 512-pixel measurement resolution) through an anonymous link, or explain why they cannot be shared.
- M8. Consider adding a fictitious-name, group ("Impressionist") or distant-painter clause on the same 14 scenes. This would separate painter-group movement from a generic artist-name effect (p. 13, "What the shared change is") at small cost.
- M9. Fix the label overlaps in Figure 1 and Figure 5. In Table 3, do not bold proximity gain as "best", or define bold as "largest".
- M10. Clarify introduction bullet 2's "(less for Cézanne alone)".
- M11. Consider adding raw proximity (not only gain) to Table 3, since practitioners usually report raw CSD scores. The paper notes that raw proximity adds g_g⊤µ̄, which is name-independent; showing it would strengthen the point.
- M12. Rewrite the appendix introductions to Tables 21–25 so each table's purpose is stated before its numbers. The appendix is 18 pages with 22 tables.

## 6. Criterion 1 — Claims and evidence: **yes**

The central claims are supported by accurate and convincing evidence:
- most of what the names add is shared, and this is expected given the benchmarks (Table 1, Figure 3);
- proximity gain in linear readouts is dominated by a name-agnostic term (the Eq. 4 identity plus Table 2, with intervals and reference sensitivities in Table 22);
- all configurations have positive aligned amplitude, with prespecified simultaneous intervals above zero (Table 4);
- GPT Image 2 has the best direction-only alignment in 98.0–100.0% of scene resamples (Table 21).

The numbers are internally consistent, and the paper scopes itself (14 authored scenes, four related painters, closed services, no perceptual validation). The gaps are wording-level and are listed in C3, M1 and M2:
- the introduction's unqualified D > 1 verdicts in the weak feature representation;
- mechanism language built on six-point rank correlations;
- "Content does not explain";
- the "upper reference" wording.

W5 (no validation of the specificity readouts and the generic-name confound) limits interpretation but is disclosed. It would be closed by a positive control (for example, a generator conditioned on the actual reference paintings, or perceptual/expert ratings on a subset) and by a fictitious-name or group-name clause.

## 7. Criterion 2 — Audience and clarity: **partially**

Audience interest is clear. Researchers who evaluate style imitation, use CSD or CLIP proximity, or build erasure and protection benchmarks would want to know that proximity gain for related artists mostly measures shared movement, and they would want the two benchmarks and the Eq. 4 identity. Finding 1 is communicated well by the abstract, introduction, Figure 1, Figure 3 and Table 2.

The second half of the contribution is hard to extract from the text as written: how to read specificity, and what the six configurations do. Sections 4.3, 4.5 and 5.3–5.5 compress many estimands, interval types and robustness caveats into long sentences (quoted in W2). The main text exceeds 12 pages, and more than 20 appendix tables are cited from the main text. This is a presentation problem that editing alone can fix (C2); no new experiments are required.

## 8. Desk-rejection risk: **low**

The risk is low for the PDF as frozen. It becomes **high** if the supplementary archive is uploaded as currently built (C1).

## 9. Recommendation: **minor revision** — Confidence: **4/5**

The science is careful and the claims are mostly calibrated. The required changes are editorial: anonymizing the supplement, restructuring for readability, and qualifying a few claims. None of them needs new data.

## 10. Format checks performed

- **Style files:** SHA-256 of `tmlr.sty`, `tmlr.bst` and `fancyhdr.sty` match `STYLE_PROVENANCE.json` (upstream commit 7bf90ef…, `"modified": false`). The `tmlr.sty` header matches the official file (Larochelle/Pedregosa, edited January 2021 by Maddison, lmodern). I did not re-download the upstream files; network access was limited to the TMLR guidelines.
- **Mode:** `\usepackage{tmlr}` without `[accepted]` or `[preprint]`. Every page carries the header "Under review as submission to TMLR", and the author block reads "Anonymous authors / Paper under double-blind review".
- **Layout:** no geometry, margin, line-spread or caption-spacing changes in `main.tex`/`appendix.tex`. The generated tables use `\small` (24 tables), `\footnotesize` (1) and reduced `\tabcolsep`. These are permitted local table formatting, not template modifications.
- **Captions:** all 27 table captions are above their tables and all 5 figure captions are below their figures (checked visually on pp. 3, 5, 8–11, 17, 19, 21–29, 31–32).
- **Statements:** the broader impact statement (p. 14) covers misuse (optimizing imitation of living artists), misreading as a service ranking or legal evidence, and licensing. A reproducibility statement is present with an AI-use disclosure. There is no acknowledgments section.
- **Citations:** natbib author-year style via `tmlr.bst`. The reference list is complete for the cited works, and DOIs or URLs are given where available.
- **PDF:** letter size (612×792 pt), 32 pages, all fonts embedded (`pdffonts`). Metadata contains only Creator and Producer (no Author or Title), with a fixed creation date.
- **Anonymity (PDF):** I scanned the raw and decompressed streams for the author's name, handle, email, `/Users/` paths and repository names. There were no hits apart from "Alfred" in painter names.
- **Anonymity (supplement):** inspected `make_supplement.py`. The identifier regex (containing the author's handle, name and email fragments) is packaged into the archive and exempted from the scan. **Violation (C1).** The figure PDFs under `paper/tmlr/` have clean metadata.
- **Length:** main text about 13.2 pages (pp. 1–14 top), plus about 0.7 page of statements, 2.5 pages of references and 16 pages of appendices. TMLR guidance says unusually long papers are likely to delay review, and the OpenReview form, as I recall it, splits regular and long submissions at 12 pages of main content.
- **Figures:** all five are legible at print size. Figure 2 is a photographic panel with a disclosed fixed selection rule. There are minor label overlaps in Figures 1 and 5.
- **Internal consistency:** about 60 numbers were cross-checked across the abstract, text, tables and appendices with no mismatches. There are two documentation inconsistencies: App. H omits Figure 5, and "Table 8 lists every symbol" is not true.

## 11. PDF SHA-256

`4ae5600ec39d49e52f30a105432d92b809d117d71d0c3e8627ccd6405209a242` (computed with `shasum -a 256`).
