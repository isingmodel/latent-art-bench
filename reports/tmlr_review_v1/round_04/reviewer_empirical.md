# TMLR review: "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation"

**Reviewer role:** empirical (evaluation of text-to-image generative models)
**PDF read:** `reports/tmlr_review_v1/round_04/input/manuscript.pdf`, 29 pages, SHA-256 `caa3b4299154a8926e29f7a7dee8d5c81784ff77477597931a0aab8d4d5ec617`
**Supplement consulted:** `paper/tmlr/` (main.tex, appendix.tex, claims.json, build_assets.py), the analysis outputs in its `INPUTS` (in particular `reports/painter_tmlr_diagnostics_v1/v2/v3/analysis.json`, `reports/painter_learned_audit_v1/analysis.json`), the protocols and plans under `studies/painter_specificity_v1/`, `_v2/`, `painter_tmlr_diagnostics_v1–v3/`, `painter_request_timing_v1/`, `painter_reference_quality_v1/PLAN.md`, and `src/latent_art_bench/painter_specificity_v1/analysis.py`.

---

## 1. Summary of the submission

The paper asks what "proximity" (similarity of named generations to an artist's reference works, or its gain over a baseline) measures when the prompted artists are stylistically related. Six API text-to-image configurations (four GPT Image variants, Nano Banana 2, FLUX.2 Max) render 14 authored outdoor scenes under six clauses (no painting instruction, a generic oil-painting clause, and the same clause "in the style of" Monet, Sisley, Pissarro or Cézanne), with two independent requests per cell (1,008 images). Images are described by 31 prespecified colour, spatial and texture features and, post hoc, by CLIP ViT-L/14 and CSD embeddings. The reference target is 649 Wikimedia reproductions of outdoor paintings.

The method splits the named-minus-generic change into a component shared by all four names (N) and between-name departures (B). Squared sizes use cross-repeat products to remove noise bias. Two benchmarks make the split interpretable: a faithful imitator whose named means equal the reference means, and an exact-differences generator that keeps the observed shared change but reproduces the reference between-painter differences. In the embeddings, an exact identity (Eq. 4) splits the mean named-minus-generic prototype-similarity gain into a name-independent term and a painter-specific term Hβ/4. Specificity is read from the aligned amplitude β, the relative size Q and the repeat-corrected error D = 1 − 2β + Q (1 = no painter distinctions), with a prespecified 21-comparison inferential family in the 31 features.

Main findings: (i) 66.7–88.4% of the squared change is shared, below the faithful values (84.8–95.2%), and even exact differences would leave 57.6–84.2% shared; (ii) the name-independent term supplies 73–84% (CLIP) and 54–80% (CSD) of the proximity gain, close to faithful-imitation values; (iii) all configurations have β > 0, but D verdicts differ by representation: three configurations have D > 1 in the features, none has a point estimate above 1 in CSD, and GPT Image 1 is lowest in CLIP; (iv) proximity, recognition and D favour different configurations; (v) texture features are less shared than colour features. An earlier 2,000-image SD-Turbo collection gives a retrospective check.

## 2. Contributions as I see them

1. A clean, reusable decomposition of what artist names add, relative to a generic-style control. It comes with two benchmarks that stop the naive reading "a large shared fraction means a lack of specificity". This is the paper's most useful conceptual move.
2. An exact identity showing that, for related painters, the averaged prototype-similarity gain is dominated by a name-independent term. This holds even for a faithful imitator, so proximity gain is structurally uninformative about between-painter specificity in this regime.
3. A noise-corrected agreement analysis (β, Q, D) with genuine-painting calibration, per-pair breakdowns and an extensive sensitivity battery.
4. Evidence that common readouts (proximity gain, closed-set recognition, reference agreement) rank the same outputs differently, plus concrete reporting recommendations.

## 3. Strengths

- **Well-chosen control.** The generic clause "Render as an oil painting." is identical to the named clause minus the name, so the named-minus-generic contrast isolates what the names add. Concept ablation's generic-painting anchor is correctly noted as related (p. 3).
- **Honest benchmarking of the headline quantity.** The paper does not stop at "most of the change is shared". It shows that faithful imitation would share even more (Table 1, Fig. 3) and that B/H, not the shared fraction, carries the specificity-relevant information (p. 7–8).
- **Correct, verifiable estimators.** I checked Eq. 4 and Eq. 8 algebraically; the identity is exact. D = 1 − 2β + Q follows from the definitions. The cross-repeat estimators in `painter_specificity_v1/analysis.py::geometry` and `shared_diagnostics` match Eqs. 1–3. The appendix derivations of the exchangeable null, the baseline cross term and the finite-sample bias of H are correct.
- **Unusually transparent about inferential status.** Section 4.5 separates the prespecified family from post hoc analyses. The plans in `studies/painter_tmlr_diagnostics_v1–v3/PLAN.md` record which values were already known when each analysis was defined, including values computed by earlier reviewers. I checked that the prespecified family (six β, 15 pairwise D differences, Bonferroni over 21, paired-scene t intervals) matches `studies/painter_specificity_v1/PROTOCOL.md` and `_v2/PROTOCOL.md`.
- **Extensive sensitivity analysis:** single-scene deletion, square windows, content-matched targets, two alternative weightings, leave-one-feature-out, cropped sources, refitted scaling, H bias correction, repeat-dependence thresholds (ρ at which orderings flip), a timing-drift check, and simulated coverage under several error models (App. C).
- **Genuine-painting calibration.** The distinct-works control, with the earlier with-replacement version kept and its bias explained (App. D, Table 16), is a good practice.
- **Reproducibility of the numbers.** Every table is generated from hash-bound outputs, and prose numbers are checked against their sources (App. H). I spot-checked about 30 numbers (Tables 1–6, 14, 17, 18, 21, 23, 24; Section 5.2–5.5 prose), and all matched the supplement except the one noted under W7.

## 4. Weaknesses

**W1. Headline agreement claims are stated without the fragility the paper itself documents** (Abstract; Section 1, third bullet; Section 5.3).
- *Scale.* The features claim that "three configurations err more than a generator that makes no painter distinctions" rests on Q > 2β: the differences are too large, not misdirected (β/√Q = 0.51–0.60). One held-out scalar shrinkage makes every configuration's error fall below 1 and puts GPT Image 2 (0.554), GPT Image 1 (0.645) and Sunburst (0.706) below FLUX.2 Max (0.714) (Table 15). The paper names a plausible alternative explanation, a scale mismatch between clean generations and photographed paintings (p. 10), but does not test it. The Abstract and Introduction do not mention this reversal.
- *Multiplicity.* With Bonferroni over six configurations, GPT Image 1's interval includes 1 (p. 10). The unqualified "three" is therefore descriptive at the point-estimate level only.
- *What drives FLUX.2 Max's low error.* FLUX.2 Max, singled out in the Introduction as "the only configuration whose error is below that level in most joint … resamples (94.2%)", gets its aggregate D < 1 mostly from the Cézanne contrast. Its second-component amplitude is 0.021 and β falls to 0.096 when Cézanne is omitted (Table 17). Its pair amplitudes among the Impressionists are 0.13 (M–S), 0.02 (M–P) and 0.17 (S–P), with pair errors of 1.16 and 1.51 for M–S and M–P (Fig. 4). It also has the least recognisable names (41.1% / 39.3%, Table 5).

This is exactly the kind of aggregate-hides-structure point the paper makes about proximity. It should be visible where FLUX.2 Max is highlighted, not only in the appendix.

**W2. "In CSD none does" (Abstract) overstates the evidence.** Nano Banana 2's CSD error is 0.999 [0.876, 1.128] with D < 1 in 51.3% of joint resamples, and Sunburst's is 0.944 [0.866, 1.024] (Table 4). Section 5.3 states this correctly ("four scene intervals lie entirely below 1"). The Abstract's contrast between "three err more" (features) and "none does" (CSD) compares an interval-supported statement with a point-estimate one.

**W3. The feature-family finding is reported without the benchmarks the paper says are necessary** (Section 1, fifth bullet; Section 5.5; Table 7).
The paper's central argument is that a shared fraction cannot be read without its faithful and exact-differences values ("Being below the faithful value therefore does not mean being more specific", p. 8; Recommendation 2, p. 13). Yet Table 7 and the fifth contribution report raw per-family fractions for the main collection. The per-family benchmarks are already computed in `reports/painter_tmlr_diagnostics_v1/analysis.json` (`hand31[*].families`). They change the reading:
- GPT Image 1's texture fraction of 48.6%, "the only minority value", comes from over-sized texture differences (B/H = 3.11), not from specificity. Its exact-differences texture value is 74.6%.
- Averaged over the six configurations, the exact-differences benchmark is itself 3.1 points lower for texture than for colour (74.7% vs 77.8%). About half of the observed −6.1-point texture–colour gap would therefore occur even with exact painter differences.
- The faithful benchmark goes the other way (texture 89.4% vs colour 87.2%).

As written, readers are invited to read "texture is less shared" as "texture carries more painter-specific signal", the misreading the paper warns against. The SD-Turbo family table (Table 25) already reports these benchmarks, so the main collection is inconsistent.

**W4. The embedding agreement analysis uses content-unmatched targets** (Section 5.3, Table 4).
The reference collections differ strongly in subject (Monet 191/297 water scenes vs Cézanne 31/105, p. 4), and CLIP in particular encodes subject. The reference differences r_a in CLIP and CSD therefore include subject-mix differences that fixed-scene generations cannot reproduce by design. The paper shows that content-matched targets change the orderings in the features (Table 20; Recommendation 3), but it does not apply them in the embeddings. The representation-dependence claim (Section 1, third bullet) is worded descriptively and remains true. However, the offered explanation ("the embeddings may respond to content or naming cues") is untested, even though the class labels and embeddings needed to test it already exist.

**W5. Positioning: the "proximity gain" is attributed to Su et al. (2025), who do not compute it** (p. 1).
The Introduction says "comparing with the image generated without the name turns it into a gain (Su et al., 2025)". Su et al.'s Table 1(a) reports two things:
- CLIP similarity between each named image and the name-removed image from the same seed (how much the name changes the image);
- the similarity of named images to the real-artist prototype.

It does not report a named-minus-unnamed gain in prototype similarity. The Related-work description on p. 2 is accurate; the Introduction's is not. The paper's critique still applies, even more strongly, to raw proximity (Section 4.4 notes this), so the fix is wording. As written, though, a reader will think the paper's central target quantity is an established readout with a specific source.

**W6. An unconditional statement in the Discussion is false as worded** (p. 13, Recommendation 2).
"a shared term larger than a quarter of the painter spread will dominate proximity whatever the model does." The painter-specific term is Hβ/4, which exceeds H/4 whenever β > 1. A model that exaggerates the reference pattern along its own direction therefore escapes this bound. This is possible here: GPT Image 2's corrected β is 1.071 in the features (Table 13). Section 4.4 states the condition correctly ("of an exact-differences generator"); the Discussion drops it.

**W7. A calibration statement is misreported** (p. 10).
"In the embeddings no genuine split has an error above 0.53." `build_assets.py` (line 1743) computes 0.53 as the maximum of the upper ends of the central 95% ranges (`np.quantile(v, [0.025, 0.975])` in `painter_tmlr_diagnostics_v3.py`, line 93). In the CLIP class-sampling / pooled-target control, about 25 of 1,000 splits therefore exceed 0.53 by construction. What the output supports is that no genuine split exceeds 1 (`above_one = 0.0` for all six embedding controls), or that 97.5% of splits lie below 0.53.

**W8. The share-of-gain framing does not directly measure what evaluation practice uses proximity for** (Sections 5.2, 5.4).
Table 2 reports a ratio within each configuration. Evaluators use proximity to compare models or to apply thresholds, so the relevant question is what drives differences in gain across configurations. The supplement answers it, and the answer supports the paper:
- In CLIP, the across-configuration variance of the shared term is about 11 times that of the painter-specific term (1.48×10⁻⁴ vs 1.37×10⁻⁵; my computation from `diagnostics_v1` `learned.clip[*].readouts`).
- In CSD, the two terms are negatively correlated across configurations (GPT Image 2 has the smallest shared term and the largest specific term). This explains why the CSD-gain ranking is unstable (33.6%, Table 6).

Section 5.4's sentence "Proximity ranks differently because … its dominant term carries no information about which name was used" would be much stronger with this shown explicitly.

**W9. Reproducibility of the generation side is limited.**
- The 1,008 generated images are not released (p. 14, Reproducibility statement), so features cannot be re-extracted.
- Two of the six configurations (Flare, Sunburst) are undocumented gateway endpoints that "may not remain available" (p. 4).
- All six are closed services whose checkpoints cannot be verified.

The paper states all of this, and its claims concern the requested configurations. However, the practical recommendations would be more credible if at least the images were archived. A reduced-resolution set would fit TMLR's 100 MB supplement limit, and the full set could be released on de-anonymisation.

**W10. Minor clarity and disclosure points.**
- The "visual audit" that disagrees with the title-derived class for 230 of 870 works (p. 4; App. D) was an AI-assistant labelling (`studies/painter_reference_quality_v1/PLAN.md`), like the crop audit. Section 3 does not say so.
- The prose is very number-dense. Sections 5.3 and 5.4 read as long sequences of values and would benefit from moving secondary numbers into tables.
- Figure 2 shows one scene only. A low-resolution contact sheet of all 14 scenes in the appendix would help readers judge the qualitative claims, for example Nano Banana 2's small shared change and FLUX.2 Max's muted differences.

**Limitations that are acknowledged and need no new evidence for the claims as worded:**
- The shared-change direction toward the reference centroid (cos 0.57–0.86) cannot be separated from a generic artist-name or "painterliness/old-photograph" effect without an unrelated-painter, fictitious-name or "Impressionist" clause (p. 13).
- The 31 features separate genuine Monet and Sisley poorly (p. 4).
- Repeat independence cannot be tested with two repeats (p. 13, App. A).
- There is no human evaluation (p. 13).

The claims are appropriately scoped to these conditions.

## 5. Requested changes

### Critical (must change for acceptance; all are editing or reporting of already-computed values)

1. **Calibrate the headline agreement claims in the Abstract and Introduction (W1, W2).**
   - State that the features' D > 1 verdicts reflect over-sized differences (Q > 2β), that they reverse under a single held-out rescaling (Table 15), and that only two survive a Bonferroni adjustment over configurations.
   - Where FLUX.2 Max is singled out, say that its aggregate D < 1 rests mainly on the Cézanne contrast, with near-zero differentiation among the three Impressionists.
   - Replace "in CSD none does" with an interval-based statement (e.g., "in CSD four are resolved below 1 and none is above it").
2. **Report the per-family faithful and exact-differences benchmarks for the main collection (W3)**, e.g., as extra columns or rows in Table 7 (they are already in `diagnostics_v1`). Then either reinterpret the texture–colour contrast relative to its benchmark or narrow the fifth contribution bullet to a purely descriptive statement with the benchmark caveat.
3. **Correct three factual misstatements:**
   - (a) the attribution of the proximity gain to Su et al. (2025) on p. 1 (W5);
   - (b) "whatever the model does" on p. 13, which should be conditioned on β ≤ 1 (W6);
   - (c) "no genuine split has an error above 0.53" on p. 10 (W7).

### Minor

4. Add a content-matched (title- or visual-class) target for the CLIP and CSD agreement scores on the 11 non-mixed scenes, analogous to Table 20, to test whether the representation-dependence of D reflects the representations or subject-mix differences in r_a (W4).
5. Add the across-configuration decomposition of proximity-gain differences into shared and painter-specific terms (W8), e.g., a two-column addition to Table 5 or a sentence in Section 5.4.
6. Commit to releasing the generated images, even at reduced resolution within the supplement limit, and add an appendix contact sheet of all 14 scenes (W9, W10).
7. State in Section 3 that the visual content labels, like the crops, were assigned by AI assistants and not verified by a human (W10).
8. In Section 5.3, add one sentence noting that the genuine-painting controls' expected value is essentially the target's sampling noise, since pseudo-scenes have no fixed content. The paper derives this in App. D; bringing it forward makes clear that the distance between generated and genuine errors partly reflects the fixed-content design.
9. Reduce numeric density in Sections 5.3–5.4, moving secondary values (Bonferroni-over-six intervals, per-pair counts, bootstrap resolution counts) into tables.
10. In the Discussion's first paragraph, the claim that the shared change "increases similarity to their average prototype in both embeddings" could note that the same would be expected of any movement toward "painting-like" images. The paper already says this later in the paragraph, so this is only ordering.

## 6. Criterion 1: are the claims supported by accurate and convincing evidence?

**Partially.** The core claims are well supported, and the supplementary outputs reproduce the reported values:
- most of what the names add is shared, and a faithful imitator or exact-differences generator would also leave most of it shared (Section 5.1);
- proximity gain in CLIP and CSD is dominated by a name-independent term, close to the faithful-imitation share (Section 5.2);
- every configuration has a positive aligned amplitude (Section 5.3, prespecified);
- proximity, recognition and agreement favour different configurations (Section 5.4).

Several statements are worded beyond the evidence:
- the Abstract's "in CSD none does" (W2);
- the unqualified features verdict and the FLUX.2 Max highlight (W1);
- the feature-family contribution, presented without the benchmarks the paper's own framework requires (W3);
- three factual misstatements: the Su et al. attribution, "whatever the model does", and the 0.53 calibration bound (W5–W7).

Each gap is closed by narrowing the wording or by reporting values already in the supplement; none requires new data.

## 7. Criterion 2: would some of TMLR's audience be interested, and is the paper clear?

**Yes.** Researchers who evaluate style imitation, build style-similarity metrics (CSD-style scoring, imitation-threshold studies, style-erasure benchmarks) or report artist-recognition benchmarks will find the decomposition and the Eq. 4 identity directly useful. The recommendations (Section 6) are concrete and cheap to adopt: a generic-style control and the reference means suffice.

The paper is precise and well organised: a schematic (Fig. 1), a symbol table (Table 10), clearly labelled prespecified vs post hoc analyses, and explicit reference values for every estimand. The main clarity cost is numeric density in Sections 5.3–5.5, which makes the argument harder to follow than it needs to be. This is an editing issue, not a barrier to understanding.

## 8. Desk-rejection screen

**Risk: low.**
- The paper is in scope (evaluation methodology for generative models).
- It uses the TMLR template, is anonymised and includes a broader-impact statement.
- The main text is about 13 pages. TMLR imposes no page limit, and the length is justified by the content.
- It is carefully constructed: numbers are cross-checked by script, and the estimators are derived and tested.
- The prose is dense and terse but not generic or padded. AI assistance (code, source audit, editing) is disclosed.

I see no signs of low-care machine generation.

## 9. Recommendation

**Minor revision.** The empirical design is sound for the scoped claims, and the analyses are thorough and reproducible from the released vectors. The required changes are recalibration of a few headline sentences, correction of three factual misstatements, and reporting of per-family benchmarks that already exist.

**Confidence: 4/5.** I verified the algebra, the core estimator code, the prespecified family against the protocols, about 30 reported numbers against the supplementary outputs, and the descriptions of the key related works. I did not re-extract features from pixels (the images are not available) or rerun the pipeline.

## 10. Literature checked

- Su et al. (2025), arXiv:2507.18633: 110 artists, content-controlled name substitution and same-seed name-removed images confirmed. Table 1(a) reports named-vs-unnamed CLIP similarity and named-to-prototype similarity, but no named-minus-unnamed proximity gain (see W5).
- Somepalli et al. (2024), CSD, arXiv:2404.01292: confirmed that generated images are scored by dot product with an averaged artist prototype (GSS).
- Frochte (2026), arXiv:2605.09030v2: confirmed the negative discrimination gaps for 23 of 91 artists with raw CSD cosine, the phrase "widely read as … style-fidelity score", and a T2I section with prompted Flux generations and pairwise CSD discrimination.
- Xing et al. (2026), arXiv:2608.06751: confirmed "canonical shortcuts, such as recurring motifs, generic palettes".
- Moayeri et al. (ICLR 2025), arXiv:2404.08030: confirmed 372 artists, with about 20% at risk.
- Casper et al. (2023), arXiv:2307.04028: confirmed 70 artists, CLIP zero-shot, 81.0% average accuracy.
- Verma et al. (TMLR 2025), imitation thresholds: confirmed the art-style domain and similarity-based imitation measurement.
- Fu et al. (2025), arXiv:2508.01408: confirmed VLM attribution and detection of AI-generated paintings.
- Kim et al. (2026) PNAS: the arXiv version (2503.13531) and a 2026 event listing with the cited title were found; volume and page details not verified.
- Deliège et al. (2025), J. Imaging: existence confirmed (supplementary-material record); content not verified.
- TMLR author guide: no page limit; 100 MB supplement limit.

No closely competing prior work that decomposes artist-name effects into shared and between-name parts against a generic-style control turned up in my searches. Readers may also want to see work showing that embedding-based metrics are sensitive to content, such as Kynkäänniemi et al. (2023) on ImageNet classes in FID. I suggest it but do not require it.

## 11. PDF hash

`shasum -a 256 manuscript.pdf` → `caa3b4299154a8926e29f7a7dee8d5c81784ff77477597931a0aab8d4d5ec617`
