# TMLR action-editor screen and review: "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation"

- Role: editor (desk screen, then clarity, structure, length, figures and tables, format)
- PDF read: `reports/tmlr_review_v1/round_02/input/manuscript.pdf`, 23 pages, all pages inspected as rendered
- PDF SHA-256: `2837299e02bca86a872f392d19e4e5a74ee72944be0c79441b89eea7deb446d6`
- Sources consulted: `paper/tmlr/main.tex`, `appendix.tex`, `generated/tab_learned.tex`, `STYLE_PROVENANCE.json`, `figures/PROVENANCE.json`, `build_assets.py` and `make_supplement.py` (read only to check the reproducibility claims), and the public TMLR author guide (jmlr.org/tmlr/author-guide.html)

## 1. Desk-rejection decision

**Do not desk reject.** Reasons:

- **Scope.** The paper is about evaluation methodology for text-to-image generation: how to read artist-name effects and proximity or recognition metrics. That is squarely within TMLR's scope.
- **Format.** The paper is built with the TMLR style in anonymous mode. The style-file hashes match the recorded upstream commit. Captions sit correctly: tables above, figures below. The appendices follow the references, and a broader impact statement is included. No violations found (Section 11).
- **Anonymization.** No names, affiliations, acknowledgments, grants or identifying URLs appear. The PDF has no Author metadata.
- **Quality and care.** The numbers are internally consistent. I checked more than 20 algebraic identities and table-to-text correspondences (Section 11), and all of them held. Limitations and the preregistered/post hoc status are disclosed with unusual candour, and AI assistance is disclosed. The prose has recognizable stylistic tics (see W-C4). Still, it reads as carefully checked work, not as low-care machine output.

## 2. Summary

The paper argues that "proximity gain" is not a measure of painter specificity. Proximity gain is the increase in similarity between images generated "in the style of X" and X's works. The design renders 14 fixed scene descriptions under six clauses: no painting instruction, a generic oil-painting instruction, and the same instruction naming Monet, Sisley, Pissarro or Cézanne. Six commercial API configurations each produce two repeats per cell, 1,008 images in total. The change that the names add beyond the generic clause is split into two parts: a component shared by all four names, and between-name deviations. Squared sizes are estimated with cross-repeat products, so they are free of noise bias. Two benchmarks frame the results: an exchangeable null (25% shared) and a "faithful imitator" whose named means sit exactly on each painter's reference mean.

Main findings:

- In 31 hand-crafted features, 66.7–88.4% of the added squared change is shared, against 84.8–95.2% for the faithful imitator.
- In CLIP and CSD, the shared term supplies 73.2–83.8% and 54.2–79.7% of the prototype-proximity gain, close to the faithful values.
- The between-name differences align with the reference painter differences in aggregate (β = 0.44–1.00), but unevenly across pairs. Monet–Sisley alignment is near zero or negative in the features for five configurations.
- Proximity, agreement error D and recognition pick different "best" configurations.
- A retrospective SD-Turbo collection of 2,000 images is 64% shared overall and 37% shared in texture.

The paper recommends reporting between-name comparisons and a faithful-imitation benchmark alongside any proximity score.

## 3. Strengths

1. **The core idea is simple and useful.** Figure 1 and Eq. 4 show that prototype-proximity gain splits exactly into a label-invariant shared term and a painter-specific term, Hβ/4. This is a clean, reusable argument that people evaluating style mimicry, erasure and protection can apply directly.
2. **The generic-style control and the faithful-imitator benchmark** turn an otherwise uninterpretable "X% shared" into a comparison with what perfect imitation would produce. This is the paper's most valuable methodological move.
3. **Noise-unbiased squared magnitudes.** The cross-repeat, cross-validated-distance estimators are appropriate and correctly derived. The appendix identities (Eqs. 5–8) check out.
4. **Candid statistical status.** The paper separates the prespecified family (six β values and 15 pairwise D differences, Bonferroni-adjusted paired-scene intervals, reference resampling) from the post hoc analyses, and says which is which (Section 4.5). Limitations are specific (Section 7).
5. **Internal numerical consistency is excellent.** Every range quoted in the abstract, intro and results that I checked matches the tables. The derived quantities obey their stated identities (Section 11).
6. **Format and structure.** About 11.5 pages of main text, a clear introduction with signposted findings, and an estimand glossary (Table 9) that helps with the heavy notation.

## 4. Weaknesses

### A. Claims versus evidence

**W-A1. The first claim of the abstract is contradicted by Table 2** (p. 1, abstract; p. 8, Table 2).
- The abstract says: "this proximity gain mostly measures a change shared by every name in the prompt set, and that this would remain true for a generator that reproduced each painter exactly."
- Table 2 gives a faithful CSD value of **48.3%** for GPT Image 2. So a faithful imitator starting from those generic outputs would get *less than half* of its CSD proximity gain from the shared term. The abstract itself quotes "48.3–75.7%" two sentences later.
- The observed CSD value for GPT Image 2, 54.2%, is also only marginally a majority, and it has no interval.
- "Mostly … would remain true" therefore holds in 11 of the 12 configuration × encoder cells, not in all of them.

**W-A2. "Only a few points higher" / "within a few points" is inaccurate as stated** (p. 2, intro bullet 2; p. 8, §5.2).
- §5.2 says: "A faithful imitator would obtain 71.3–82.9% and 48.3–75.7% of its gain from the same term, so the observed shares are only a few points higher."
- From Table 2, observed minus faithful is −2.8 to +3.2 points in CLIP and +2.0 to +6.6 points in CSD.
- GPT Image 2 in CLIP is *lower* than faithful (73.2 vs 76.0).
- FLUX.2 Max in CSD is 6.6 points higher (77.6 vs 71.0).
- No interval is given for any of these differences.

**W-A3. The headline "Texture is the least shared feature family" does not hold per configuration** (p. 2, intro bullet 5; p. 10, §5.5 heading and text; p. 11, Table 6).
- Per Table 6, texture is the least-shared family only for GPT Image 1, Flare and FLUX.2 Max.
- For GPT Image 2 (spatial 59.6) and Sunburst (spatial 61.5), spatial is least shared.
- For Nano Banana 2, color is least shared (56.8), and texture is the *most* shared family (79.8). Texture is also the most shared family for Sunburst (70.3).
- The claim rests on comparing range endpoints across configurations ("48.6–79.8%"). Averaged over configurations the ordering is texture 68.2% < spatial 71.5% < color 74.3%, a gap of about 3 points with no uncertainty attached.
- The claim is well supported only for the SD-Turbo collection (36.6%, with a block-deletion range of 36.2–36.9%).

**W-A4. The generalization from one painter set is unsupported** (p. 1, abstract "for related painters"; title).
- The magnitude of the faithful-imitator fraction depends on ‖t‖²/H, the generic-to-reference distance relative to the painter spread.
- ‖t‖² includes the gap between rendered images and photographed canvases, which the paper acknowledges (§4.2, §7).
- With one painter set, the paper cannot show how much of "proximity is mostly shared" comes from painter relatedness and how much from this domain gap.
- Either scope the claim to "these four related painters", or add evidence that separates the two. Options: a second painter set (the paper's own suggestion in §6 of distant painters, or an "Impressionist" group clause), or a faithful benchmark computed from a broader landscape-painting baseline.

**W-A5. The post hoc headline comparisons have no uncertainty** (p. 7, Table 1; p. 8, Figure 3 and Table 2).
- Figure 3's caption asserts: "The observed fraction is below the faithful value in every configuration and representation."
- For FLUX.2 Max in the features, the observed value is 88.4 against a faithful value of 90.4. The observed value's own single-scene-deletion range reaches 90.2. The faithful value also depends on reference sampling and on H, which carries a 6.7% upward bias.
- These are the paper's central comparisons, yet only deletion ranges on the observed side are reported.
- Scene-bootstrap and reference-resampling intervals for *observed minus faithful* (Tables 1 and 2) can be computed from existing data and are needed before "below in every configuration" or "close to" can be asserted.

**W-A6. The agreement error D is under-interpreted, so the paper's own recommendation is not operational** (p. 9, §5.3 and Table 3; p. 12, §6 "Recommendations").
- Table 3's reference-resampling intervals for D lie *entirely above 1* for GPT Image 1 [1.260, 1.892], Flare [1.407, 2.032] and Sunburst [1.318, 1.925]. By this readout, these three configurations do *worse* than a generator that ignores the painter names, even though they have β = 0.77–0.94 and some of the best recognition. The text never says this. The intro reports only that "Only FLUX.2 Max's error falls clearly below" 1.
- The genuine-painting control gives D = 0.753 for real paintings drawn within content classes (p. 9; App. D). That is close to FLUX.2 Max's 0.801, and the paper does not relate the two. As a result, a reader cannot tell what counts as a good D.
- §6 says "report the between-name comparison … This is the readout of specificity". But the paper shows that β, D, D_agg, D_held (in effect β/√Q) and per-pair values rank the configurations differently. The recommendation should say which statistic(s) to report, and how to read D > 1 alongside β ≈ 1.

**W-A7. Internal inconsistencies:**
- **Development panel.** p. 4, §3 says the development panel "sets the feature scaling and is never compared with generated images". p. 8, §5.2 says "Using the audited source regions or the development panel as the reference target changes the shared part of the gain by at most 1.6 percentage points". App. F (p. 22) refers to "four combinations of source view and reference target".
- **Size of GPT Image 2's differences.** p. 9 says "its differences are more than twice the reference size, Q = 2.223", and App. D (p. 19) says "GPT Image 2's differences are about twice the reference size". Q is a *squared*-size ratio, so in norm the differences are about 1.49× the reference. §5.1 draws this distinction correctly ("in squared size … or 0.78–1.45 times in root-mean-square terms").
- **Reproducibility claims.** App. H (p. 23) and the Reproducibility statement (p. 12) say "a check script … regenerates every table and figure byte for byte" and "code that regenerates each table and figure". However, `figures/PROVENANCE.json` records Figures 2 and 4 as static, hash-checked copies whose builders were retired, and Figure 1 is a schematic ("positions are illustrative, not data") that App. H nonetheless calls "generated from those result files".
- **Independence of repeats.** p. 2 asserts "Two independent generations per condition", while p. 12 concedes "Two repeats cannot establish that repeated requests are independent."

**W-A8. The practice being critiqued is thinly documented** (p. 1).
- The abstract opens: "Artist-style prompting is often evaluated by how much closer images generated with an artist's name move to that artist's works."
- The only citation for proximity-type scoring is Somepalli et al. (2024). Most of the related work cited uses *recognition* or classification (Casper; Su; Moayeri), which the paper treats as a separate readout.
- To show that the critique targets real practice, name specific published evaluations that report artist-similarity or proximity (for example CLIP/CSD similarity to artist works in erasure, ablation or mimicry evaluations) and state which quantity each reports.

**W-A9. Some quoted sensitivity numbers are not shown in any table** (p. 8, p. 9, p. 11):
- "at most 1.6 percentage points" (development/audited target, §5.2)
- "Its unadjusted scene interval [0.586, 1.016]" (§5.3)
- "all six aligned amplitudes remain above zero, the Sunburst–FLUX.2 Max difference is no longer resolved, and the GPT Image 1–FLUX.2 Max difference becomes resolved" (§5.6)
- "below Nano Banana 2 in 99.9% of resamples" (§5.4)

These are checkable only through the supplement.

**W-A10. The inference caveat about a shared state is unexplained** (p. 18, App. C "Intervals").
- The text says: "whereas a configuration-specific state shared by all scenes and both repeats reduced it to 0.04%."
- Coverage collapsing to 0.04% is a striking disclosure for closed services queried within a single 3-hour window. The reader is not told the estimand, the size of the simulated state, or why the main text should not worry about it. If the state counts as part of "the configuration", say so. If not, the prespecified intervals need that caveat in the main text.

**W-A11. The SD-Turbo check lacks the paper's central benchmark** (p. 11, §5.5). The 64.2% shared fraction is reported without its faithful-imitator value, so it cannot be read the way the paper asks readers to read every other shared fraction.

### B. Audience and clarity

**W-B1. Sentences that are ambiguous or hard to parse** (quoted):
- p. 1, abstract: "Proximity, agreement with the reference differences and recognition of the prompted name identify different best configurations, several of them stably under scene resampling."
- p. 3, §2: "Our results concern prompting of pretrained services, but they suggest asking of any such readout how much of the measured effect every artist name would produce."
- p. 2, §2: "Artist-free comparisons are therefore established." ("therefore" does not follow from the preceding sentence.)
- p. 7, §4.5: "Some benchmark values were first computed during internal review of an earlier draft; the analysis plan records this." Readers do not know which values, what "internal review" means, or where the plan is. The supplement script includes the protocols and plan, but the paper never says so.
- p. 9, §5.3: "Zero error is not attainable either." (The antecedent of "either" is unclear.)
- p. 9, §5.3: "The weak Monet–Sisley response in the 31 features therefore does not transfer to the embeddings; the embeddings may also respond to content or naming cues correlated with each painter, and CSD was trained with these painters among its style tags." ("therefore" introduces an observation, not an inference, and the clause mixes finding and caveat.)
- p. 10, §5.4: "These differences have a common explanation, which follows from Equation 4 for proximity and is an interpretation for the other two readouts."
- p. 11, §5.6: "The shared fraction uses only generated images and the fixed feature scaling, so it does not depend on the reference collection, although its benchmarks and B/H do." (The scaling comes from the development paintings, so "does not depend on the reference collection" needs the panel distinction spelled out.)
- p. 16, App. A: "The Commons page cited for the source records (Wikimedia Commons, 2026) was consulted when the manuscript was written; the panels were assembled before the experiment." (The citation is the Commons:GLAM project page, which is not a record of these works' sources.)

**W-B2. Number density impedes reading in §5.3–5.4** (pp. 9–10).
- §5.3 packs about 35 numeric values into four paragraphs, and §5.4 about 30 into three. Many of them repeat table entries.
- The reader has to track the meanings of β, Q, D, D_agg, D_held, κ, V_scene, the reference and scene intervals, and the pairwise results at the same time.
- Moving secondary values to tables and stating one takeaway per paragraph would improve readability without losing content.

**W-B3. Caveat phrasing is repetitive and may draw machine-text scrutiny.** The "X, not Y" construction recurs at least eleven times:
- "a reference point, not an attainable target" (p. 6)
- "requested configurations, not verified checkpoints" (p. 4)
- "to compare response components, not to define style" (p. 3)
- "digital measurements of reproductions, not perceived resemblance" (p. 2)
- "a retrospective check, not an independent replication" (p. 11)
- "dependence on the authored scenes, not confidence for new scenes" (p. 10)
- "differences between prompt conditions, not their causes" (p. 11)
- "these painters and configurations, not artists in general" (p. 12)
- "sensitivity, not uncertainty" (p. 22)
- "related representations, not independent confirmation" (p. 21)
- "these 14 scenes rather than fresh requests" (p. 18)

Each caveat is legitimate. Together, their uniform cadence and the process-level disclosures read as defensive, and they are the kind of pattern TMLR's screening for machine-generated text notices. Consolidating them into the Scope/Limitations paragraphs would help.

**W-B4. The audience case is fine but under-argued.** The paper would interest researchers in style-mimicry evaluation, concept erasure/unlearning, artist protection and generative-model metrics. It would reach them better if §6 showed concretely how the shared/between-name split changes the reading of one published evaluation type, for example an erasure evaluation in which erasing "Monet" also lowers similarity to Sisley.

### C. Figures and tables

- **Table 2 (p. 8).** The last "faithful" (CSD) column is visibly stretched, because the spanning header is wider than its four columns. Cosmetic, but it looks unfinished.
- **Naming is inconsistent across figures.** Figure 3 uses "Flare"/"Sunburst", Figure 4 uses "2.5 Flare"/"2.5 Sunburst", and the tables use "GPT Image 2.5 Flare"/"GPT Image 2.5 Sunburst".
- **Table 7 placement (p. 15).** Table 7 floats above the "A Prompts, requests and provenance" heading, directly after the references.
- **Figure 3 (p. 8).** For FLUX.2 Max in the 31 features, the filled and open markers overlap, so the one case where the gap matters most cannot be read. A difference plot (observed minus faithful, with intervals) would carry the paper's central comparison better.
- **Table 3 (p. 9).** The D column lacks the scene interval that the text quotes ([0.586, 1.016] for FLUX.2 Max). Adding an unadjusted scene interval, or D − 1, per configuration would support the intro's claim directly.
- **Figure 2 (p. 5).** Clear and informative. The reference thumbnails are small but legible.
- **Figure 4 (p. 18).** Readable. Its colorbar annotations ("no alignment", "reference strength", "no distinction") are helpful.

### D. Length and structure

The main text runs about 11.5 pages (pp. 1–12), followed by 11 pages of appendices. That is reasonable under TMLR's guidance that length should be justified by content. The order (design → estimators → benchmarks → results → sensitivity → discussion → limitations) is logical. Sections 4.3–4.4 could say earlier which statistic is the paper's preferred specificity readout (see W-A6).

## 5. Requested changes

### Critical (must change for acceptance)

1. **C1 — Align the headline claims with the tables.**
   - Revise the abstract's "this would remain true for a generator that reproduced each painter exactly". Either scope it to 11 of 12 cells or restate it (the faithful CSD value is 48.3% for GPT Image 2).
   - Replace "only a few points higher" / "within a few points" with the actual deltas (CLIP −2.8 to +3.2; CSD +2.0 to +6.6), noting that GPT Image 2 in CLIP is below faithful.
   - Scope "for related painters" to "for these four related painters", unless a second painter set is added.
2. **C2 — Restate or remove the texture headline** (intro bullet 5, §5.5 heading). Report per-configuration orderings: texture is least shared in 3 of 6 configurations and most shared for Nano Banana 2 and Sunburst. Give the cross-configuration mean with uncertainty (scene bootstrap or deletion) if the claim is kept. Keep the SD-Turbo texture result, which is well supported.
3. **C3 — Add uncertainty to the observed-versus-faithful comparisons.** Provide scene-bootstrap and reference-resampling intervals for (observed − faithful) in Table 1 and in both halves of Table 2, and qualify Figure 3's "below the faithful value in every configuration and representation" accordingly, especially for FLUX.2 Max (88.4 vs 90.4).
4. **C4 — Make the specificity readout operational and interpret D.**
   - State in §5.3 that under reference resampling, GPT Image 1, Flare and Sunburst have D intervals entirely above the no-distinction value of 1.
   - Relate the observed D values to the genuine-painting controls (0.234 pooled; 0.753 within content classes, against FLUX.2 Max's 0.801).
   - In §6, say which between-name statistics a practitioner should report (for example β and β/√Q for direction and size, D or D_agg for overall agreement, and per-pair β) and how to read disagreements among them.
5. **C5 — Fix the internal inconsistencies:**
   - the development panel "never compared with generated images" (§3) against its use as a reference target (§5.2, App. F);
   - "twice the reference size" for Q (§5.3, App. D), which should say "in squared size";
   - the "regenerates every table and figure" claims (App. H, Reproducibility statement), given that Figures 2 and 4 are static hash-checked copies and Figure 1 is a schematic;
   - "independent generations" (intro) against the concession in Limitations.
6. **C6 — Ground the practice being critiqued.** Support "Artist-style prompting is often evaluated by how much closer …" with specific published evaluations that report proximity or similarity-to-artist scores, and state which quantity each uses.
7. **C7 — Clarity edit.** Rewrite the sentences quoted in W-B1. Explain the App. C coverage-collapse scenario (estimand, size of the simulated state, relevance to closed services) in one or two sentences, and flag it in §4.5 or §7 if it bears on the prespecified intervals. Reduce the number density of §5.3–5.4 by moving secondary values to tables (W-B2).

### Minor

1. Report in tables the sensitivity numbers now quoted only in the text (W-A9): the 1.6 pp development/audited-target change, the unadjusted scene interval of D, the cropped-source β and pairwise results, and the 99.9% recognition resampling.
2. Add the faithful-imitator benchmark for the SD-Turbo collection, or explain why it is not computed.
3. Consider a domain-gap control for the faithful benchmark: for example, a baseline at the centroid of a broader landscape-painting corpus. This would separate "related painters" from "rendered versus photographed painting". It would also partly address W-A4.
4. State in §4.5 and in the Reproducibility statement that the pre-collection protocols and the post hoc analysis plan are in the supplement, and say what "internal review of an earlier draft" refers to.
5. Consolidate the repeated "X, not Y" caveats (W-B3) into the Scope and Limitations paragraphs.
6. Use consistent configuration names in Figures 3 and 4 and in all tables.
7. Fix the Table 2 column spacing, for example by setting explicit column widths or splitting the spanning header.
8. Place Table 7 after the Appendix A heading.
9. Consider replacing or supplementing Figure 3 with an observed-minus-faithful difference plot with intervals.
10. Replace or explain the Commons:GLAM citation as the source for the reference records. Cite the Wikidata query or the dataset release instead.
11. Say whether `gpt-image-2.5-flare`/`-sunburst` are preview or stealth endpoints that may disappear, since this affects replicability.
12. Release the generated images through an anonymized host, or include downsampled JPEGs within the 100 MB supplement, so that others can re-extract features. The paper currently notes "features cannot yet be re-extracted from pixels by others".
13. Optionally extend related work to data-attribution and replication studies (for example, work evaluating data attribution for text-to-image models, and replication/"digital forgery" analyses), and to erasure papers that evaluate artist removal with CLIP similarity.
14. Trim the abstract, which carries about ten numeric ranges. Keep the two or three that define the contribution.
15. Anonymity hygiene: the PDF CreationDate carries a local timezone (KST). Strip it, or normalize it to UTC, before submission. This is negligible risk but costs nothing to fix.

## 6. Criterion 1 — claims and evidence: **partially**

The core methodological claims are correct and supported: the exact decomposition of prototype-proximity gain (Eq. 4), a shared component above the exchangeable null, positive aggregate alignment with prespecified intervals, and readouts that disagree. The derivations are right, and the tables obey every identity I checked. Several headline statements go beyond the evidence:

- the faithful-imitator clause in the abstract, contradicted by 48.3% (W-A1);
- "a few points higher" (W-A2);
- the texture headline (W-A3);
- the general "for related painters" claim from one painter set (W-A4);
- observed-below-faithful asserted without intervals (W-A5).

Beyond these, the paper's own specificity readout D is left uninterpreted where it matters (W-A6), and there are internal inconsistencies (W-A7). All of this can be closed with rewording and with analyses on the existing data (C1–C6). No new data collection is required, unless the authors want to keep the general claim, in which case a second painter set would be needed.

## 7. Criterion 2 — audience and clarity: **partially**

Some of TMLR's audience would clearly be interested: researchers in generative-model evaluation, style-mimicry and erasure benchmarks, and artist protection. The abstract, introduction and Figure 1 state what was found and why it matters. The communication problems are local but real:

- ambiguous sentences (W-B1);
- very high number density in §5.3–5.4 (W-B2);
- a recommendation section that does not say which statistic to report (W-A6);
- repetitive defensive caveats (W-B3).

These make the results harder to use than they need to be. They do not obscure the main message, and an editing pass (C7) should be enough.

## 8. Desk-rejection risk: **low**

The paper is in scope and compliant with the format and anonymity requirements, and its care is evident from its internal consistency. The residual risk comes from the uniform, caveat-heavy prose style (W-B3) under TMLR's scrutiny of machine-generated text. The disclosed AI use and the verified consistency argue against a low-care reading.

## 9. Recommendation: **minor revision**

The contribution is sound and relevant, and the required changes are bounded: claim scoping, intervals computed from existing data, interpretation of D, consistency fixes and a clarity edit. If the authors choose to keep general "related painters" claims instead of scoping them, the revision becomes major, because it would need a second painter set.

## 10. Confidence: **4 / 5**

I read every page and checked the numbers extensively. I did not rerun the analyses, inspect the supplement archive or diff the style files against upstream.

## 11. Format and consistency checks performed

1. **Style files.** The SHA-256 hashes of `tmlr.sty`, `tmlr.bst` and `fancyhdr.sty` match `STYLE_PROVENANCE.json` (JmlrOrg/tmlr-style-file, commit 7bf90ef, `"modified": false`). The `tmlr.sty` header matches the official file ("Adapted by Hugo Larochelle and Fabian Pedregosa … Last edited, January 2021 by Chris J. Maddison"). I did not download upstream to diff the bytes. `main.tex` loads `\usepackage{tmlr}` with no option, which is anonymous submission mode.
2. **Rendered header and author block.** The header reads "Under review as submission to TMLR", and the author block reads "Anonymous authors / Paper under double-blind review". Pass.
3. **Page and fonts.** Page size is US letter (612×792 pt). Fonts are Latin Modern, as loaded by `tmlr.sty`, plus DejaVu Sans inside the matplotlib figures, all embedded. Pass.
4. **Anonymization.** The text contains no names, affiliations, acknowledgments, grants or identifying URLs. The PDF Info has no Author field (Creator "LaTeX with hyperref", Producer xdvipdfmx), and the figure PDFs record only the Matplotlib creator. A byte search of the PDF streams for local paths, user or e-mail identifiers found nothing (the only hit was "Alfred"). The CreationDate carries a KST timezone (minor). `make_supplement.py` filters identifying strings; I checked the script, not the archive. Pass.
5. **Caption placement.** Table captions are above their tables for all of Tables 1–16. Pass. Figure captions are below their figures for all of Figures 1–4. Pass.
6. **Required statements.** A broader impact statement is present (p. 12), which is appropriate given the style-imitation and commercial-ranking misuse risks. The reproducibility statement and AI-use disclosure are present. Pass.
7. **Length and appendices.** The main text runs about 11.5 pages. The references are on pp. 12–14, and the appendices come after the references (pp. 15–23), as the TMLR author guide allows. Pass.
8. **References and citations.** Cross-references resolve, with no "??". Citations use author-year via `tmlr.bst`. The reference list is complete for every in-text citation. Pass.
9. **Numerical identities verified.**
   - D = 1 − 2β + Q for all six configurations (Table 3).
   - N_free = G + N + I, and every shared fraction in Table 10 recomputed from its components.
   - "Along generic shift" = cos²(c, g), and I = 2·cos(c, g)·√(GN), using Tables 1, 10 and 11.
   - Centroid proximity total = shared + between-name (Table 11).
   - D = D_agg + V_scene and β/√Q (Table 13).
   - β with corrected H = β/0.933 (Table 11 and §5.6).
   - All 15 pairwise differences in Table 12.
   - Recognition shift and generated-prototype changes and means (Table 16 against §5.4).
   - The fitted scalar ≈ β/Q (Table 13).
   - Figure 4 Monet–Sisley values against Table 14.
   - Every range quoted in the abstract and introduction against Tables 1, 2, 3, 5 and 6.
   - Inconsistencies found: W-A1, W-A2, W-A3, W-A7.
10. **Reproducibility claims against provenance.** Figures 2 and 4 are static, hash-checked copies (`figures/PROVENANCE.json`), and Figure 1 is a schematic. The statements in App. H and the Reproducibility statement overstate what is regenerated (W-A7).
