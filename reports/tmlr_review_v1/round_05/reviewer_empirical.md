# TMLR review: "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation"

Reviewer role: empirical (evaluation of text-to-image generative models)

PDF read (SHA-256): `764356d845744d7adc994600113628525cce6f0569eff8c7927439c6a1ba5316`

I read the whole PDF (30 pages, main text and Appendices A–H), with figures and tables as rendered. I also read the pre-collection protocols (`studies/painter_specificity_v1/PROTOCOL.md`, `studies/painter_specificity_v2/PROTOCOL.md`, `DECISION.md`, `TERMINATION.md`), the claim registry and build script in `paper/tmlr/`, and the released per-image CLIP/CSD embeddings (`reports/painter_learned_audit_v1/`). I recomputed some of the numbers from those embeddings myself (see "Verification" below).

## 1. Summary of the submission

The paper asks what similarity-based ("proximity") evaluations of artist-style prompting measure when the prompted artists are stylistically related. Six commercial text-to-image configurations (GPT Image 1, GPT Image 2, two "GPT Image 2.5" variants called Flare and Sunburst, Nano Banana 2, FLUX.2 Max) each render 14 authored outdoor scenes under six clauses: no painting instruction, a generic oil-painting instruction, and the same instruction "in the style of" Monet, Sisley, Pissarro or Cézanne. Each cell has two separately requested repeats, for 1,008 images. Each image is represented by 31 hand-crafted colour, spatial and texture features (the prespecified primary representation) and by CLIP ViT-L/14 and CSD embeddings (added after collection).

The core move splits what the four names add beyond the generic clause into two parts: a change shared by all four names, and between-name differences (deviations from the four-name average). Squared sizes are estimated without noise bias by taking products across the two repeats. Two reference-based benchmarks are used for comparison: a "faithful imitator" whose named means land on each painter's reference mean, and an "exact-differences" generator that keeps the observed shared change but reproduces the reference painter differences exactly. For embeddings, an exact identity (Eq. 4 / Eq. 8) writes the named-minus-generic proximity gain as the sum of a name-independent shared term and a painter-specific term, Hβ/4. Specificity is then operationalised as agreement between the generated between-name differences and the reference painter differences. The aligned amplitude β, relative size Q, alignment ratio β/√Q and a repeat-corrected error D measure that agreement; D is 1 for a generator that makes no painter distinctions.

Main findings:
- In the 31 features, 66.7–88.4% of the squared change the names add is shared. A faithful imitator would share 84.8–95.2% and an exact-differences generator 57.6–84.2% (Table 1).
- In CLIP and CSD the shared term supplies 54.2–83.8% of the proximity gain, close to the faithful-imitation values. Differences in gain between configurations track the shared term (r = 0.96 and 0.95 across the six configurations; Tables 2–3).
- All configurations have positive aligned amplitudes. In the features, three GPT configurations have D > 1 through oversized but aligned differences, and FLUX.2 Max has the lowest D. In CSD, four configurations have D resolved below 1. In CLIP, GPT Image 1 has the lowest D (Tables 4–5).
- Proximity, D and nearest-prototype recognition favour different configurations (Table 3, Table 20).

The confirmatory family (six β and fifteen pairwise D differences in the features) was fixed before collection. All other analyses are labelled post hoc and descriptive.

## 2. Strengths

1. **The design choice is simple and useful.** A generic-style control plus several related names turns an ambiguous proximity score into two interpretable parts. The decomposition in Eq. 4 is exact, and it shows directly why proximity gain is dominated by movement shared across names when the painter spread H is small relative to the shared movement. The rule "the shared term dominates whenever it exceeds H/4 and β ≤ 1" (Sections 4.4 and 6) is a practical, checkable criterion that other evaluators can apply.
2. **The benchmarks head off the naive reading.** The paper does not claim that a large shared fraction shows a failure of specificity. The faithful and exact-differences benchmarks make clear that such a fraction is expected even of good imitation (Section 5.1, Figure 3). The paper also separates the part of the faithful benchmark that comes from the gap between generated images and photographs, which is honest.
3. **The statistics are careful and the paper is transparent.** Cross-repeat products remove noise bias, and scene resampling and reference resampling are reported separately. The prespecified Bonferroni family is kept distinct from descriptive results, and the collection history is disclosed, including a terminated first attempt and an outcome-blind reduction from 16 to 14 scenes. The protocols I read match the description in Section 4.5 and Appendix A. The sensitivity analysis on repeat dependence (Appendix A: the value of ρ at which each conclusion flips) is a good practice for closed services that give no seed control.
4. **Many robustness checks.** These include single-scene deletion, square windows, content-class targets, feature reweighting, audited crops, the finite-sample bias of H, genuine-painting controls using distinct works, an independent SD-Turbo collection, and per-painter and per-pair breakdowns. The paper reports unfavourable results (for example, GPT Image 1's D > 1 does not survive Bonferroni or ρ = 0.22).
5. **Computational integrity.** I recomputed the CLIP/CSD proximity gains, shared terms and shares (Tables 2 and 3) and every CLIP/CSD β and D in Table 5 from the released embeddings. All match to the reported precision.

## 3. Weaknesses

**W1. The claims that agreement depends on the representation and that readouts disagree rest on the size-sensitive error D. The paper's own direction-only measure gives a consistent picture that is not reported for the embeddings.** (Abstract; Section 1, bullets 3–4; Section 5.3 title and p. 11; Section 5.4; Tables 3, 5, 20.)

D = 1 − 2β + Q penalises both misdirection and miscalibrated amplitude. The paper defines the alignment ratio β/√Q and the held-out rescaled error D_held, and recommends reporting them (Section 6). It reports them only for the 31 features (Table 4, Table 14), where GPT Image 2 has both the highest alignment ratio (0.670) and the lowest D_held (0.554).

The supplement (`reports/painter_learned_audit_v1/analysis.json`, `calibration.held_out_d`) already contains D_held for the embeddings, and my recomputation from the released embeddings agrees:

- CLIP D_held: GPT Image 2 0.631, GPT Image 1 0.694, Sunburst 0.705, Flare 0.735, Nano Banana 2 0.759, FLUX.2 Max 0.796.
- CSD D_held: GPT Image 2 0.458, Flare 0.547, Sunburst 0.556, GPT Image 1 0.557, FLUX.2 Max 0.610, Nano Banana 2 0.739.
- Alignment ratios (CLIP / CSD): GPT Image 2 0.609 / 0.737 is highest in both, and highest in 99.7% / 100% of my 5,000 paired scene resamples.

So GPT Image 2 has the best direction-only agreement in all three representations. The rank correlation of alignment ratios across representations is 0.60–0.77, against −0.14 to 0.66 for D. Alignment ratio also tracks reference-prototype recognition closely (Spearman 0.94 in CLIP, 0.89 in CSD), and GPT Image 2 has the best recognition in both encoders (Table 20).

The disagreements the paper emphasises, between representations and between "agreement" and recognition, therefore arise mostly from the amplitude of the between-name differences. The paper itself suggests this amplitude "may reflect a difference in scale between clean generated images and photographed paintings" (p. 11). The statements as worded are literally true of D. However, readers will take "how accurately depends on the representation", "we do not rank the configurations' specificity overall" and "Proximity, agreement and recognition favor different configurations" to mean that specificity readouts are mutually inconsistent. That impression is not borne out by the direction-only readout, which the paper recommends but omits for the embeddings. This matters for the paper's methodological advice, which is its main contribution to evaluators.

**W2. There is no external validation of the specificity readout.** Specificity is defined as agreement with differences between reference means in a chosen representation (Section 4.3, p. 7), and the paper explicitly excludes perceptual claims (Section 7). That is acceptable as scoping. However, the recommendations in Section 6 invite evaluators to adopt β, Q and D as specificity metrics. The only calibration is genuine held-out paintings, which the paper concedes favours genuine works and does not bound what a generator could achieve (Appendix D). Two cheap additions would help readers judge how much weight to put on D versus the alignment ratio:
- a positive control with known painter-specific differences, such as reference works themselves passed through a generator's image-to-image path, or images rendered with a known exaggeration factor;
- a small expert or perceptual check of whether named outputs are distinguishable.

I do not make this a condition for acceptance, because the paper states the limitation. It should be acknowledged next to the recommendations.

**W3. The primary (prespecified) representation is poorly suited to the question.** The 31 features classify genuine development works at 49.8% macro accuracy, with Monet 39.6% and Sisley 30.6% (Section 3, p. 4). Genuine-painting splits exceed D = 1 in 5.1–9.1% of cases (p. 11). The confirmatory family is therefore evaluated in a representation that barely resolves two of the four painters. The more discriminative representations (CLIP and CSD, about 80%) are post hoc, as are their intervals, which are unadjusted percentile scene-bootstrap intervals over 14 clusters. The paper is candid about this (Sections 3, 5.3 and 7). The practical consequence is that the confirmatory results, such as "Flare and Sunburst have higher error than FLUX.2 Max", concern a readout the paper itself tells readers not to rely on without first checking separability.

**W4. Scope.** There is one set of four related painters, one clause template, 14 authored scenes, two repeats, and four of six configurations are OpenAI variants. The design cannot separate movement toward these painters from a generic effect of naming any artist (Section 6). The abstract and limitations scope the claims appropriately. The title states a general thesis, but that thesis is supported by the identity rather than by the magnitudes. The SD-Turbo check reuses the same painters and references.

**W5. Reporting and clarity issues (editing, not evidence).**
- *Section 5.3, p. 11 and Table 5.* The statement that content-matched targets "change [errors] by at most 0.037 and keep their order" compares against the 11-scene pooled-target D. Table 5 does not show that value. A reader comparing Table 5's "Error D" (14 scenes) with "Content-matched D" sees changes of up to 0.064 (Sunburst, CLIP: 1.136 to 1.200). The reader also sees two order swaps: CSD GPT Image 1/GPT Image 2 (0.735 < 0.741 becomes 0.767 > 0.759), and CLIP Flare/FLUX.2 Max. The 11-scene pooled values exist in `reports/painter_tmlr_diagnostics_v4/analysis.json` (`pooled_d`), and against them the sentence is correct. They should be shown.
- *Table 5 omits Q and β/√Q* for the embeddings, although Section 6 recommends reporting them (see W1).
- *Figure 3 (p. 9)* puts a squared-change share (left) and a proximity-gain share (middle, right) on one axis labelled "Shared part of the change added by the names". The caption explains the difference, but the embedding squared-change shares (Table 22) are the like-for-like comparison and could be shown.
- *Correlations with n = 6.* The CLIP correlation of 0.96 is stated in the introduction but not in Section 5.2, which gives only the rank identity and the variance ratio. Neither correlation carries an uncertainty statement. My leave-one-configuration-out ranges are 0.91–0.99 (CLIP) and 0.84–0.98 (CSD), so the claim is robust, but n = 6 should be stated.
- *Per-painter heterogeneity.* "Proximity gain mostly measures the shared change" is an average over four painters. For Cézanne the shared part is as low as 34.6% (GPT Image 2, CSD; Table 23). This appears in Section 5.2 but not in the abstract or introduction.
- *Speculative wording in the Discussion (p. 12).* The phrase "as movement toward any painting-like image would" is not tested, and the generic clause already requests an oil painting. Soften it or tie it to the proposed fictitious-name or "Impressionist" control.
- *Density.* The abstract (about 250 words) and Sections 5.3–5.5 pack many numbers into each sentence, with repeated "(computed before rounding)" qualifiers. Moving secondary numbers to tables would help readers outside this subfield. A figure that projects each configuration's four named means onto the reference-difference subspace would make β, Q and "aligned but oversized" immediately visible. The first two components carry 86.9% of H (Table 16), and the v1 protocol already lists such a PCA display.
- *Examples shown.* Only one scene is shown (Figure 2), and the generated images are not in the supplement (p. 13). For a paper about visual painter distinctions, a contact sheet of several more scenes, and a commitment to release all 1,008 images on acceptance, would substantially help readers.

**W6. Model identity for the undocumented variants.** Flare and Sunburst are undocumented catalogue entries accessed through a gateway whose earlier route accepted an invented model identifier (Appendix A; `TERMINATION.md`). The paper labels them only as requested configurations, which is appropriate. It does not report whether the explicit provider routes used for the main collection reject an invalid identifier. From the released embeddings I checked that Flare and Sunburst are distinguishable: cross-configuration distances exceed within-configuration repeat distances in 92% (CLIP) and 100% (CSD) of scene × clause cells. So they are not the same output distribution. Reporting this, and a one-request negative control, would close the question cheaply.

**W7. Inference details.** The coverage simulation (Appendix C) addresses the Student intervals in the features. Most embedding results use percentile scene-bootstrap intervals over 14 clusters, which tend to under-cover. The margins for the headline embedding claims are large, for example CSD upper bounds of 0.80–0.86 against 1, so I do not expect conclusions to change. The repeat-dependence (ρ) sensitivity is also reported only for the features. Among the embedding verdicts, Sunburst's CLIP D > 1 [1.058, 1.213] is the only one close to the boundary.

**W8. Minor asymmetry in the embedding pipeline.** Generated images are square, so the 224 × 224 centre crop sees nearly the whole image. Non-square reference reproductions lose their periphery. The square-window sensitivity exists for the features (Table 19) but not for the embeddings. Table 21's "crop" variant concerns the audited painting regions, not square windows.

## 4. Requested changes

### Critical

1. **Report direction-only agreement for the embeddings and qualify the representation-dependence and readout-disagreement claims.** Add Q, β/√Q and D_held (already in the supplement) to Table 5 for CLIP and CSD. Add the alignment ratio or D_held as a row in Tables 3 and 20, with scene-resampling stability. Then revise the abstract ("how accurately depends on the representation"; "Proximity, agreement and recognition favor different configurations"), the Section 1 bullets 3–4, the Section 5.3 title and text ("we do not rank ... overall"), Section 5.4 and Section 6. The revised text should state that:
   - direction-only agreement ranks GPT Image 2 highest in all three representations;
   - direction-only agreement tracks reference-prototype recognition;
   - the representational and readout disagreements concern the size of the between-name differences;
   - that size may partly reflect the generated-versus-photographed scale difference the paper already suggests.

   Alternatively, justify explicitly why amplitude miscalibration should count against specificity, and present D and the alignment ratio side by side as two different questions. No new data are needed.

### Minor

1. Show the 11-scene pooled-target D for CLIP and CSD in Table 5, or state explicitly that the "at most 0.037 ... keep their order" comparison is against that unreported baseline. Against the displayed 14-scene column, shifts reach 0.064 and two orders swap.
2. Correct the citation on p. 3: Naeem et al. (2020) propose unconditional fidelity and diversity metrics (density and coverage), not conditional metrics that separate within-condition variation from relations among condition means. Benny et al. (2021) fits that sentence; Naeem et al. does not.
3. State n = 6 for the correlations of 0.96 and 0.95, and add a leave-one-out range or interval. Give the CLIP correlation in Section 5.2, not only in the introduction.
4. Mention in the abstract or introduction that shared-term dominance is a four-painter average and is weakest for Cézanne (as low as 34.6%; Table 23).
5. In the introduction bullet "FLUX.2 Max has the lowest error in the features", note that within the prespecified family FLUX.2 Max is resolved only against Flare and Sunburst (Table 13). Say "unadjusted" wherever "resolved" refers to intervals outside the family (for example, the CSD D < 1 statements).
6. Soften "as movement toward any painting-like image would" (Section 6, p. 12) or link it to the proposed control conditions.
7. Report a negative-control request (an invalid model identifier on the explicit OpenAI provider route) and a simple check that Flare and Sunburst outputs are distinguishable, to support treating them as distinct configurations (W6).
8. Commit to public release of the 1,008 generated images on acceptance, for example as a data deposit with lossless compression. Add an appendix contact sheet showing several more scenes under all six clauses.
9. Extend the ρ repeat-dependence sensitivity to the embedding D-versus-1 statements, notably Sunburst in CLIP. State that percentile scene-bootstrap intervals over 14 clusters may under-cover, or extend the Appendix C simulation to them.
10. Revise Figure 3 so that like-for-like quantities share an axis, for example by adding the Table 22 squared-change shares for the embeddings.
11. Add a projection figure of the generated named means and the reference means in the reference-difference subspace for each configuration, to make β, Q and "aligned but oversized" visible.
12. Either add an embedding square-window check comparable to Table 19's "square" column, or note the crop asymmetry between square generated images and non-square references (W8).
13. Reduce numerical density in the abstract and Sections 5.3–5.5 by moving secondary figures to tables and consolidating the repeated "(computed before rounding)" qualifiers.
14. Next to the Section 6 recommendations, acknowledge that β, Q and D have not been validated against perceptual or expert judgement or against a positive control with known painter differences (W2). Optionally, add such a control.
15. Remove the rhetorical weight on the 25% exchangeable null (Section 5.1). It is far from any plausible alternative and adds little beside the two reference benchmarks.

## 5. Criterion 1: Are the claims supported by accurate and convincing evidence?

**Answer: partially.**

Most claims are supported as worded, and the numbers are accurate: I reproduced the embedding decompositions and agreement statistics from the released data. The following are well supported:
- the shared-fraction results and their benchmarks (Table 1, Figure 3);
- the proximity-gain decomposition and its closeness to the faithful benchmark (Table 2);
- the claim that between-configuration gain differences follow the shared term (Table 3; robust to leaving out any configuration);
- positive aligned amplitudes for all configurations (Tables 4–5);
- the per-representation D verdicts, with the prespecified/descriptive distinction honestly drawn.

The gap is in the headline interpretive claims that agreement "depends on the representation" and that "proximity, agreement and recognition favor different configurations". These hold for the size-sensitive error D, but the paper's own direction-only measure (alignment ratio, held-out rescaled D) is reported only for the features. That measure gives a consistent answer across all three representations (GPT Image 2 highest) and tracks recognition (Spearman 0.94 and 0.89). The results for it are already in the supplement. Reporting them and narrowing the claims to the amplitude-sensitive readout would close the gap without new evidence (critical change 1).

Other gaps are either editing issues (the Table 5 content-matched baseline and the Naeem et al. citation) or disclosed limitations: no perceptual validation, a poorly separating primary representation, and scope.

## 6. Criterion 2: Would some of TMLR's audience be interested, and is the paper clear?

**Answer: yes.**

Researchers evaluating style imitation, style removal or erasure, and copyright-related measurement in text-to-image models are a clear audience. The decomposition, the H/4 criterion, and the warning that proximity gains are dominated by name-independent movement are directly usable. The main message is stated clearly in the title, abstract, contribution bullets and Figure 1. Estimators are precisely defined, with a symbol table (Table 8), and every table is traceable to released outputs.

Clarity could still improve. The abstract and results sections are very dense with numbers, and the paper has only one qualitative figure. A geometric figure of the between-name differences and the minor editing fixes above (W5) would make the paper easier to follow for non-specialists. These are presentation improvements, not barriers to understanding.

## 7. Desk-rejection risk

**Low.** The submission is in scope (evaluation methodology for generative models), uses the TMLR template, is anonymised, and includes broader-impact and reproducibility statements. The quality of analysis and care in reporting are high. The prose is dense and highly compressed, and AI assistance for code, audits and editing is disclosed. However, the text is specific, internally consistent and checked against released data. It does not read as low-care machine-generated content.

## 8. Recommendation

**Minor revision.** The empirical core is sound, reproducible from the released outputs, and honestly scoped. The one critical change, reporting direction-only agreement for the embeddings and qualifying two headline interpretive claims, uses analyses that already exist in the supplement. The remaining changes are editing, a few cheap checks, and data release.

## 9. Confidence

**4 / 5.** I read the full paper and the protocols, and I recomputed key embedding results from the released data. I did not re-extract the 31 hand-crafted features from pixels (the images are not released), and I did not re-run the feature-space analyses.

## 10. Verification performed (read-only, from released data)

- Recomputed the CLIP/CSD named-minus-generic proximity gain, shared term and shared share for all six configurations from `reports/painter_learned_audit_v1/embeddings_{clip,csd}.npz`. The results match Tables 2–3 exactly, for example CSD GPT Image 2 at 0.166 / 0.090 / 54.2%.
- Recomputed CLIP/CSD β and D for all configurations. The results match Table 5 exactly.
- Computed Q, β/√Q and held-out rescaled D for the embeddings. The D_held values match the supplement's `calibration.held_out_d`. The alignment ratio of GPT Image 2 is highest in 99.7% (CLIP) and 100% (CSD) of 5,000 paired scene resamples.
- Verified the correlations 0.96 / 0.95 / −0.65 and the variance ratio of 11 from Table 3, and computed leave-one-configuration-out ranges (CLIP 0.91–0.99; CSD 0.84–0.98).
- Checked the internal consistency of Table 1 (N/(N+B), N/(N+H), and λ against cos(c,t) and the faithful fraction), Table 9 (N_free = G + N + I; cos(c,g) from I), Table 4 (D = 1 − 2β + Q; β/√Q), Table 13 (resolved counts 2 / 6 / 8) and Table 24 (the mean changes). All are consistent.
- Traced the "at most 0.037" content-matched statement to `pooled_d` versus `class_d` in `reports/painter_tmlr_diagnostics_v4/analysis.json`. It is correct against that 11-scene baseline, which the paper does not display.
- Checked that Flare and Sunburst outputs are distinguishable: cross-configuration distances exceed within-configuration repeat distances in 92% (CLIP) and 100% (CSD) of cells.
- Confirmed that the protocols (`painter_specificity_v1/PROTOCOL.md`, `painter_specificity_v2/PROTOCOL.md`, `DECISION.md`) match the paper's account of the prespecified family, the 16-to-14 scene reduction and the terminated first attempt.

## 11. Literature checked

- Somepalli et al. (2024), CSD. Checked that generated images are scored by dot-product similarity to an averaged artist prototype, with 0.5/0.8 interpretive thresholds. The paper describes this accurately.
- Verma et al. (2025, TMLR), imitation thresholds. The imitation score is the average CSD cosine to the top-10 most similar training images, with no baseline subtraction. The paper's description is accurate, and this is the kind of max/rank-type readout the paper places outside the scope of its identity.
- Frochte (2026, arXiv:2605.09030v2). Raw CSD cosine is described as "widely read as an absolute, calibrated style-fidelity score". The paper finds negative discrimination gaps for 23 of 91 artists pairwise and 15 of 91 pooled, and evaluates Flux generations. The paper's description is accurate.
- Su et al. (2025, arXiv:2507.18633), prompted-artist identification with 110 artists, content held fixed across substituted names, and comparison with same-seed images without the artist name. Accurate.
- Moayeri et al. (ICLR 2025), ArtSavant: 20% of 372 artists appear at risk. Accurate.
- Casper et al. (2023): 70 artists, CLIP zero-shot identification, 81% average accuracy. Accurate.
- Deliège et al. (2025, J. Imaging): three art-history and semiotics experts, Midjourney v6, ten painters. Accurate.
- Asperti et al. (2025, BDCC), AI-Pastiche. Accurate.
- Xing et al. (2026, arXiv:2608.06751), Atelier: artist names act through canonical shortcuts. Accurate.
- Kim, Lee, You and Yun (2026, PNAS 123(30)). Exists as cited.
- Benny et al. (2021, IJCV), conditional IS/FID with a between/within-class relationship. The citation fits.
- Naeem et al. (2020, ICML), density and coverage, which are unconditional metrics. Mis-cited as a conditional metric (p. 3).
- Dinu et al. (2026, arXiv:2607.20127), "Back to Back with a Copy", on the stylistic similarity of AI pastiches to twelve contemporary artists using embedding cosine distances. Not cited; it is optional, related work on proximity-based pastiche evaluation.
