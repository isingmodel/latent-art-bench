# TMLR review: empirical reviewer (round 01)

**Submission:** "Proximity Is Not Specificity: What Painter Names Add in Text-to-Image Generation" (anonymous)
**PDF read:** `reports/tmlr_review_v2/round_01/input/manuscript.pdf` (38 pages, all main text and appendices, with figures and tables viewed as rendered)
**PDF SHA-256:** `af4eea64c0750637d2695ce49f017ca8c45357d476eead26aed361e48fa3ecef`
**Role:** empirical reviewer, from text-to-image evaluation

---

## 1. Summary of the submission

The paper asks what artist-style "proximity" measures. Proximity here means the similarity of images generated with a painter's name to that painter's works, and its gain over a generic painting prompt. Six commercial configurations (GPT Image 1, GPT Image 2, GPT Image 2.5 Flare and Sunburst, Nano Banana 2, FLUX.2 Max) rendered 14 authored outdoor scenes under six clauses: no clause, "Render as an oil painting", and the same clause "in the style of" Monet, Sisley, Pissarro or Cézanne. Each cell was requested twice, giving 1,008 images. What the four names add beyond the generic clause is split into a change shared by all four names (N) and between-name differences (B). Squared sizes are estimated from cross-repeat products so that sampling noise does not bias them upward. Two benchmarks come from 649 reference reproductions:
- a **faithful imitator**, whose named means land on the reference means;
- an **exact-differences** generator, which keeps the observed shared change but has the reference differences.

The paper reports these results:

1. **Shared fraction, first collection.** In 31 hand-crafted features, 66.7–88.4% of the squared change is shared. A faithful imitator would share 84.8–95.2%, and an exact-differences generator 57.6–84.2% (§5.1, Table 1).
2. **Second collection.** A second collection had prespecified tests H1 and H2 and 1,680 requests. It covers a "century group" of four distant painters (van Ruisdael, Canaletto, van Gogh, Kirchner) and four Hudson River School painters. Shared fraction is 17.7–29.5% for the century group against 89.4–98.6% for the Hudson River School (H1: −72.7 points, 95% interval [−76.5, −62.6]). Across the 28 painter pairs, name distance rises with reference distance (H2: Spearman 0.85, exact p < 0.001; CLIP 0.86, CSD 0.92) (§5.2, Tables 2 and 31, Fig. 4).
3. **Proximity identity (Eq. 4).** For any score linear in the image embedding, an exact identity splits the named-minus-generic proximity gain into a name-agnostic shared term and a painter-specific term Hβ/4. For the Impressionists the shared term supplies 54.2–83.8% of the CLIP/CSD gain, close to the faithful values. Across the six configurations it correlates 0.96 (CLIP) and 0.95 (CSD) with the gain (§5.3, Tables 3 and 4).
4. **Specificity metrics.** Specificity should be read from the between-name differences: the aligned amplitude β, the relative size Q, the alignment ratio β/√Q, and the error D with its along/off-pattern split. All six configurations have β > 0 under the prespecified simultaneous intervals. GPT Image 2 has the best alignment ratio, a metric defined post hoc. Only 2 of the 15 prespecified pairwise D comparisons are resolved (§5.4, Tables 5, 6 and 14).
5. **Readouts disagree.** Proximity follows the shared change, recognition tracks the alignment ratio (Spearman 0.94/0.89), and D favors small differences (§5.5).

The supplement contains the per-image features and embeddings, the pre-collection protocols and analysis plans, and a script that regenerates the tables and checks the quoted numbers. The generated images are not included.

## 2. Strengths

- **Useful, correctly scoped question.** Proximity-based style scores (CSD prototype similarity, Somepalli et al. 2024) are widely used. The point that their gain is mostly a shared, name-agnostic movement for related painters is useful to evaluators, and the exact identity (Eq. 4) makes it concrete. The paper correctly notes that rank-, max- and threshold-based readouts such as the top-10 similarity of Verma et al. 2025 are outside the identity's scope. I checked this against the cited paper.
- **Benchmarks rather than raw percentages.** The faithful and exact-differences benchmarks are the right move. A large shared fraction alone says nothing about specificity, and the paper shows this quantitatively (Table 1, Fig. 3). The exact-differences benchmark removes the generated-versus-photographed domain gap from the comparison.
- **Careful estimation.**
  - The cross-repeat estimators are sound.
  - The noise-model assumption is stated, and its consequences are quantified as the ρ thresholds in Appendix A and Table 24.
  - Reference-resampling intervals are reported alongside scene intervals.
  - Genuine-painting controls are drawn with distinct works.
  - The reference spread H is corrected for finite-sample bias, which matters especially for the small Hudson River panels.
- **Unusually transparent about what was prespecified.** I compared §4.5 against `studies/painter_specificity_v1/PROTOCOL.md`, `studies/painter_specificity_v2/PROTOCOL.md` and `studies/painter_specificity_v3/PROTOCOL.md`. The descriptions match:
  - The 21-comparison family, the D-only ranking and the 12-complete-scene rule are reported faithfully.
  - Post hoc metrics (alignment ratio, D_held) are labeled as such.
  - H1/H2 were fixed before collection, together with recorded predictions (`refs-20261002/predictions.json`, Table 30).
  - The reported test statistics match `reports/painter_specificity_v3/analysis.json` exactly (H1 −0.7270 [−0.7653, −0.6259]; H2 0.849, p = 0.00027).
- **Real out-of-sample test.** The second collection was designed after the first results to test the paper's own explanation, and its outcome was committed to "whichever way they fall". H1 and H2 hold in all three representations.
- **Thorough sensitivity and robustness work.** This covers single-scene deletion, square windows, content-class targets, feature reweighting, AI-audited source crops (disclosed as not human-verified), drift between collections (Table 34) and a linear request-time drift check.
- **Good limitations section.** Closed services, possible prompt rewriting, repeat dependence, the familiarity confound and the lack of human evaluation are all stated.

## 3. Weaknesses

### W1. The second collection does not isolate closeness, and the paper's own data show closeness is not sufficient (Abstract; §1 bullet 2; §5.2; §6; Tables 2, 30–33; Fig. 4)

**What the paper claims.** The abstract says the closeness explanation is "confirm[ed]" by the second collection. The second finding is titled "The shared fraction tracks how close the painters are". Section 5.2 ends with "The Impressionists lie between the two groups."

**The confounds.** H1 compares two groups that differ in at least three ways:
- reference spread (5.6× in the features);
- name familiarity, which the paper acknowledges in §1, §6 and §7;
- the subject-matter composition of the reference collections (Table 29). For example, 120 of 157 Canaletto works are water scenes against 25 of 255 van Gogh works. The Hudson River painters' differences may lie largely in subject choice (Western mountains, tropical and Arctic scenes, allegory, forest interiors), which a fixed-scene design cannot elicit.

**Counter-evidence within the paper.** The data contain a near-matched comparison that the text does not draw out.

| | Impressionists | Hudson River School |
|---|---|---|
| Reference spread H, primary features (raw / noise-corrected) | 5.92 / 5.52 | 6.24 / 4.21 |
| Faithful benchmark | 84.8–95.2% | 89.4–97.0% |
| Observed shared fraction | 66.7–88.4% | 89.4–98.6% |
| β | 0.44–1.00 | −0.01–0.20 |
| CLIP recognition | 41–69% | 29–50% |

At comparable closeness in the paper's primary representation, then, the generators separate the familiar Impressionists far more than the Hudson River painters. In the features, the Impressionists lie "between the two groups" in the outcome but not in closeness. The ordering by closeness holds only in the embeddings, where the Hudson River spread is 2–3× smaller.

**H2 broken down by pair type.** I recomputed the pair-level H2 data from `reports/painter_specificity_v3/analysis.json` (`reference_pairs`, `name_pairs_by_configuration`). The dose-response is carried by the century pairs and the cross-group pairs; within the Hudson River School it is essentially absent in the primary representation. Mean per-configuration Spearman by pair type:

| Pair type | Features | CLIP | CSD |
|---|---|---|---|
| Within century (6 pairs) | 0.78 | 0.73 | 0.88 |
| Cross-group (16 pairs) | 0.74 | 0.76 | 0.85 |
| Within Hudson (6 pairs) | 0.09 | 0.49 | 0.27 |

The within-century result is good evidence that name differences track reference differences among painters the generators render distinctly. It is not evidence that closeness alone sets the shared fraction.

**The Hudson result is not "good imitation".** For the Hudson River School the shared fraction exceeds even the faithful benchmark for two configurations, and β ≈ 0. The high fraction there reflects a failure to differentiate, not the mechanism the abstract says is "confirmed", namely that a large shared fraction is "expected even of good imitation when the painters are close".

**What would close the gap.** No new data is needed:
- narrow the wording, for example "is much lower for a group of distant, widely known painters than for a related, less widely known group";
- report the matched-spread comparison and the within-group H2 breakdown;
- state that closeness, familiarity and reference subject composition cannot be separated here.

A design that could separate them, for example a related group of very famous painters with H matched to the Hudson River School, or fictitious and group-name arms, would be a welcome addition but is not required for a narrowed claim.

### W2. "Reproduced in the right direction and near their size" overstates the century-group result by the paper's own metrics (Abstract; §1 bullet 2; §5.2; Table 32)

The paper's recommendation (§6) is to report direction and size separately: β, Q, the alignment ratio and D with its split. Applied to the century group in the primary features (Table 32 and `analysis.json`):
- **Direction:** β = 0.84–1.29 and alignment ratio 0.70–0.80. This is supported.
- **Size:** B/H = 1.33–2.56 and Q = 1.41–3.13. The between-name differences are up to 1.6× the reference differences in norm, with large off-pattern parts. For GPT Image 1, 1.44 of its D = 1.58 lies off the pattern.
- **Error D:** 0.73–1.58. The 95% interval includes 1 ("no distinctions") for five of the six configurations; only FLUX.2 Max, at [0.60, 0.85], is resolved below 1.

"Near their size" is true only for the amplitude along the reference pattern. The abstract and §5.2 should say so and report the oversized off-pattern differences and the D results. Otherwise the paper applies its own recommended readout selectively, emphasizing β and alignment ratio for the century group but D for the Impressionists.

### W3. Prespecified readouts of the second collection are not reported, and one of them qualifies a headline generalization (§1 bullet 5; §5.5; §5.3; Appendix H)

`studies/painter_tmlr_diagnostics_v6/PLAN.md`, fixed before measurement, specifies four items. The paper reports two of them: the shared-fraction intervals and four-way recognition. It omits the other two.

**Unreported item 1: Spearman between alignment ratio and recognition, within each group.** From `reports/painter_tmlr_diagnostics_v6/analysis.json`:

| Group | CLIP | CSD |
|---|---|---|
| Century | 0.29 | 0.64 |
| Hudson River | 0.94 | 0.66 |

The headline statement "recognition rises with the alignment ratio (Spearman 0.94 in CLIP, 0.89 in CSD)" (§1, §5.5) holds for the Impressionists only. For the distant group in CLIP the relation is weak.

**Unreported item 2: proximity-gain correlations with each term, within each group, plus eight-way recognition.** Across configurations, the gain correlates with its shared term at:

| Group | CLIP | CSD |
|---|---|---|
| Century | 0.97 | 0.83 |
| Hudson River | 0.99 | 1.00 |

So, for the distant painters too, the shared term drives the differences between configurations even though it supplies only 6.5–49% of the level of the gain. This actually strengthens the paper's thesis, but the abstract restricts the claim to "related painters". Eight-way recognition (century CLIP 62.5–78.1%, CSD 64.6–87.5%) is also unreported.

Given how much weight the paper places on prespecification, all planned readouts should appear, at least in an appendix table, and the generalizations in §1 and §5.5 should be scoped to the group they were computed on.

### W4. Prediction sentence mixes recorded predictions with post-collection values (§5.2, p. 9)

The sentence reads: "The predictions recorded before collection anticipated the ordering: from the new generic outputs, a faithful imitator would show 45.0–75.4% … and 89.4–97.0%."

- The recorded predictions (Table 30; v3 PROTOCOL) are 47.0–73.3% and 90.1–96.9%, computed from September's generic outputs.
- The quoted ranges are recomputed after collection from the October generic arms.

Predictions recorded before collection cannot have used the new generic outputs. Quote the recorded values, and give the recomputed ones separately.

### W5. One sensitivity check is vacuous by construction (Table 31; Appendix H)

Appendix H states that "H1 and H2 hold … in the central square window". H1 is identical (−72.7 [−76.5, −62.6]) in both rows of Table 31 because:
- the shared fraction depends only on the generated images;
- the generated images are square, so their central square is the whole image.

Presenting this as a robustness result for H1 is misleading. Say that only H2 and the benchmarks can change under the window.

### W6. Representation independence (§3 Measurements; §7; Appendix E)

The evidence rests on three representations:
- the 31 features, which separate genuine Monet and Sisley works poorly (49.8% macro accuracy);
- CLIP;
- CSD, which is built on the CLIP backbone and trained with these painters among its style tags. The paper notes both issues.

Frochte (2026), cited by the paper, reports that shared-tradition failures replicate across CLIP, SigLIP and DINOv2. A non-CLIP representation (for example DINOv2, or Gram-matrix style statistics) would test whether the embedding agreement reflects the shared backbone, and it needs only the retained images. This is not required for the claims as currently scoped.

### W7. Repeat dependence: existing data could address it (§7; Appendix A; Table 34)

The paper repeatedly says that two repeats "cannot rule out shared state". Yet the October collection re-requested the identical no-clause and generic prompts three weeks later, and the protocol itself calls this a "third repeat". In Table 34, the noise-free September–October distances scale with September's repeat noise and average about zero (−0.61 to 0.48 in the features; mean ≈ −0.02). Under a session-level shared component this would be biased positive. A brief analysis using this to bound session-level dependence would strengthen the inference behind the pairwise D comparisons and the "D vs 1" statements. It would not address prompt-deterministic dependence (caching), which should remain a stated limitation.

### W8. Instability of the shared-fraction ratio (Table 2, FLUX.2 Max row)

The Bonferroni-adjusted interval for FLUX.2 Max's century-minus-Hudson difference is [−198.2, +90.2] percentage points. The per-group intervals from the v6 output are century [−2.8, 27.9]% and Hudson [50.1, 105.8]%. The ratio N/(N+B) is ill-conditioned when N+B is small in resamples. For the second collection, also report N/H and B/H with intervals, which the pooled test hides, or use a bounded or log-ratio parameterization for per-configuration summaries.

### W9. Documentation of the generator configurations (§3 Generators; Appendix A)

The paper says "we have no further documentation of how [Flare and Sunburst] differ". Public descriptions exist:
- an OpenAI release on 8 September 2026, with OpenRouter IDs dated `-20260908`;
- these position Flare as the fast default and Sunburst as precision- and editing-oriented, at GPT Image 2 token rates.

Cite these sources, and note that collection (10 September) ran two days after release. This affects reproducibility and interpretation, not the conclusions.

### W10. Presentation density (§1, §4.3, §5.4)

The core message is clear: proximity gain is mostly shared, benchmarks are needed, and specificity should be read from between-name differences. But the density obscures it:
- Section 4.3 defines β, Q, the alignment ratio, D, D_agg, V_scene and D_held in one paragraph.
- Section 5.4 tracks the six configurations through all of them in three representations.
- The intro bullets carry about 40 numbers.

Much of the first-collection model comparison by D, which is mostly unresolved (2 of 15 comparisons), could move to the appendix. That would make room for the second-collection analysis requested in W1–W3. This is editorial.

### W11. Smaller presentation and consistency issues

- **Table 32 caption.** It labels the feature-space "shared gain" as "Eq. 4, here in the features". The code (`painter_tmlr_diagnostics_v1.decomposition`) computes the squared-distance identity of Eq. 6, not the linear identity of Eq. 4. The "–" entry for GPT Image 1 / Hudson is unexplained; it appears to be a non-positive gain.
- **Table 4 bold rule.** The caption says bold marks the largest value in each column, but the "shared" columns are not bolded.
- **§3 eligibility description.** It lists single creator, outdoor title and size, but Table 29 and `REFERENCES.md` show the same gate sequence (oil on canvas, collection, open licence) applied "as for the four-painter panel".
- **Table 31 label.** It calls H2 a "Mantel" test without a citation (Mantel 1967).
- **Repeat-dependence threshold.** The §7 phrase "errors above 1 could fall below it (at a repeat correlation of 0.22 for GPT Image 1 …)" is also stated in §5.4 and Appendix A. It is consistent, just repeated three times.

### W12. Data availability (Reproducibility statement)

The 2,686 generated images, which are the primary data, are not released, so features cannot be re-extracted. The authors should commit to depositing the images, for example through an anonymized link during review and a permanent archive on acceptance. The services' terms appear to permit this for outputs.

## 4. Requested changes

### Critical (all can be met with existing data and outputs)

1. **(W1) Narrow and qualify the closeness claim.**
   - Reword the abstract ("confirms it"), the §1 bullet title, the §5.2 title and the §6 discussion so that the second collection is described as showing a much lower shared fraction for a distant, widely known group than for a related, less widely known group, consistent with but not isolating closeness.
   - Report the matched-spread comparison of Impressionists and Hudson River School in the primary features (similar H and faithful benchmark, very different shared fraction, β and recognition).
   - Report the within-group and cross-group breakdown of H2.
   - State that the Hudson River School's high fraction reflects a lack of differentiation (β ≈ 0, fraction above the faithful benchmark for two configurations) rather than good imitation of close painters.
   - Name reference subject composition as a further confound alongside familiarity.
2. **(W2) Report size and error for the century group alongside direction.**
   - Qualify "near their size" in the abstract, §1 and §5.2 as applying to the amplitude along the reference pattern.
   - Report B/H (1.33–2.56), Q (1.41–3.13) and D (0.73–1.58, with the interval including 1 for five of six configurations in the features) together with β.
3. **(W3) Report all readouts prespecified in the v6 plan.**
   - These are eight-way recognition, the per-group Spearman between alignment ratio and recognition (century CLIP 0.29, CSD 0.64), and the per-group correlations of proximity gain with the shared and painter-specific terms.
   - Scope the §1/§5.5 statement "recognition rises with the alignment ratio (0.94/0.89)" to the Impressionists.
   - Revisit the "for related painters" restriction on "drives the differences between configurations" in light of the century-group correlation of 0.97 (CLIP).

### Minor

1. **(W4)** Correct the §5.2 sentence on predictions: quote the recorded values (47.0–73.3%, 90.1–96.9%) and give the post-collection recomputation separately.
2. **(W5)** Remove or relabel "H1 holds in the central square window"; it is identical by construction.
3. **(W7)** Use the October re-collection of the identical no-clause and generic prompts (Table 34) to bound session-level repeat dependence, or explain why it cannot.
4. **(W8)** For the second collection, report N/H and B/H with intervals per configuration and comment on the ill-conditioning of N/(N+B) (FLUX.2 Max).
5. **(W6)** Optionally add a non-CLIP representation (DINOv2 or Gram statistics) as a check on the CLIP–CSD agreement, or state more explicitly that the embedding agreement is not independent evidence.
6. **(W1 extension)** Optionally add a fictitious-name and a group-name ("Impressionist") arm, which the paper itself identifies as the decisive control (§6). This is cheap at the reported costs.
7. **(W9)** Cite the public descriptions of GPT Image 2.5 Flare and Sunburst and the release date relative to collection.
8. **(W11)** Fix the Table 32 caption (Eq. 6, not Eq. 4) and explain the "–" entry. Apply the Table 4 bold rule consistently. Make the §3 eligibility description complete. Cite Mantel (1967).
9. **(W10)** Reduce density: shorten the intro bullets, split §4.3 into a definitions list or table, and move the unresolved first-collection D model comparisons to the appendix.
10. **(W12)** Commit to releasing the generated images.
11. **Positioning.** Connect the paper's related-painter argument to Frochte's (2026) "shared-tradition" failures on the reference side. Consider citing ArtFID (Wright & Ommer 2022) as a prior style-evaluation metric, and fine-art style and artist classification work (e.g., Karayev et al. 2014; Saleh & Elgammal 2016) when arguing about representation separability.

## 5. Criterion 1: claims and evidence

**Answer: partially.**

**Supported as worded:**
- the shared/between-name decomposition and its numbers (§5.1);
- the benchmark comparisons;
- the exact proximity identity and the shares it yields for the Impressionists and the Hudson River School (§5.3);
- the prespecified findings that all six β are positive, that only 2 of 15 pairwise D comparisons are resolved, and that H1 and H2 are statistically supported;
- the descriptive readout comparisons, which are clearly labeled as post hoc where applicable.

The estimation is careful, and the numbers I checked against the retained outputs match.

**Gaps:**
1. **Closeness as the explanatory variable (W1).** It is attributed beyond what a two-group contrast confounded with familiarity and subject composition can support. The paper's own Impressionist–Hudson comparison at similar spread contradicts closeness as a sufficient explanation, and H2 is not reproduced within the related group in the primary representation.
2. **The century group's size (W2).** The claim that it is reproduced "near [its] size" is selective with respect to the paper's own recommended readouts.
3. **Unreported planned readouts (W3).** Prespecified readouts are missing, and one of them weakens a stated generalization.
4. **Mislabelled predictions (W4).** One sentence presents post-collection values as pre-collection predictions.

All four can be closed by narrowing wording and reporting outputs that already exist. No new experiments are required for the claims as narrowed.

## 6. Criterion 2: audience and clarity

**Answer: yes.**

Researchers who evaluate style imitation, artist recognition, concept erasure or unlearning, and T2I evaluation methodology in general would be interested. The concrete recommendations in §6 (generic-style control, benchmarks, separating direction from size) are actionable. The figures (1, 3, 4) communicate the main ideas well.

The paper is dense: many estimands, a number-heavy introduction, and §4.3 and §5.4 are hard going. Streamlining would help (minor change 9), but the main findings are communicated and the symbols are tabulated (Table 9).

## 7. Desk-rejection screen

**Risk: low.**

- **Scope:** on-topic for TMLR (evaluation of generative models).
- **Format:** anonymous TMLR format, with broader-impact and reproducibility statements.
- **Quality:** the methods are sound and the analysis is careful.
- **Machine-generated prose:** the prose is terse and AI-assisted, which is disclosed, but it is precise and internally consistent apart from the issues noted. It does not read as low-care machine generation.
- **Length:** 16 pages of main text, 2 of references and 20 of appendices. This is long but not a format violation.

## 8. Recommendation

**Minor revision.** The empirical core is sound and transparently reported. The required changes concern how the new second-collection evidence is interpreted and reported (W1–W3), plus a few corrections. All can be addressed from the existing outputs without new data. If the authors chose to keep the closeness attribution as worded, I would move to major revision.

**Confidence: 4/5.** I am confident about the empirical and statistical assessment. I did not re-extract features from pixels (the images are not available), and I did not verify every table entry.

## 9. Literature checked (web)

| Work | What I verified |
|---|---|
| Somepalli et al. 2024 (CSD, ECCV) | Artist prototypes are averaged CSD embeddings and the GSS score is the dot product with the prototype. Accurately described. |
| Verma et al. 2025 (TMLR, imitation thresholds) | Uses the Somepalli et al. art-style embedding; the imitation score is the cosine to the top-10 most similar training images. Accurately described, and correctly placed outside the scope of Eq. 4. |
| Frochte 2026 (arXiv 2605.09030v2) | Real; 91 artists. Says raw CSD cosine is "widely read" as a style-fidelity score. Includes T2I and LoRA stress tests. Shared-tradition failures replicate across CLIP, SigLIP and DINOv2. Accurately described; relevant to W6. |
| Su et al. 2025 (arXiv 2507.18633) | 110 artists, content-controlled name substitution, same-seed no-name comparison. Accurately described. |
| Casper et al. 2023 | 70 artists, Stable Diffusion, CLIP zero-shot identification about 81%. Accurately described. |
| Moayeri et al. 2025 (ICLR, ArtSavant) | 20% of 372 artists at risk. Accurately described. |
| Xing et al. 2026 (arXiv 2608.06751) | Canonical shortcuts: motifs, generic palettes, period signatures. Accurately described. |
| Deliège et al. 2025 (J. Imaging) | Three expert raters, Midjourney v6, ten painters. Accurately described. |
| Asperti et al. 2025 (AI-Pastiche) | User surveys on authenticity and prompt adherence. Accurately described. |
| Fu et al. 2025 (arXiv 2508.01408) | VLM artist attribution and AI-image detection. Accurately described. |
| Kim et al. 2026 (PNAS; arXiv 2503.13531) | Content matches; PNAS volume and issue not independently verified. |
| GPT Image 2.5 Flare/Sunburst public documentation | OpenRouter model pages dated 20260908 and third-party summaries of the OpenAI release of 8 Sep 2026. Contradicts "no further documentation" (W9). |
| ArtFID (Wright & Ommer 2022); Mantel (1967); Karayev et al. 2014; Saleh & Elgammal 2016 | Suggested additions; not cited. |

## 10. Checks run on the supplementary material (read-only)

- **Protocols:** `studies/painter_specificity_v1/PROTOCOL.md`, `studies/painter_specificity_v2/PROTOCOL.md` and `studies/painter_specificity_v3/PROTOCOL.md` checked against §4.5 and Appendix H. Consistent.
- **H1/H2 values:** checked in `reports/painter_specificity_v3/analysis.json` and `REPORT.md`. The values, per-configuration differences and Bonferroni intervals match Tables 2 and 31.
- **v6 plan against outputs:** `studies/painter_tmlr_diagnostics_v6/PLAN.md` checked against `reports/painter_tmlr_diagnostics_v6/analysis.json`. Items 3 and 4 and eight-way recognition are unreported (W3).
- **H2 pair-type breakdown:** recomputed from the retained pair distances (W1).
- **Feature-space gain:** confirmed that the "shared gain" in Table 32 uses the squared-distance identity (Eq. 6) in `painter_tmlr_diagnostics_v1.decomposition`.
