# TMLR review: methods (statistics, claim–evidence fit, numerical accuracy, reproducibility)

Submission: "Proximity Is Not Specificity: What Painter Names Add in Text-to-Image Generation" (anonymous)

PDF read (all 38 pages, main text and appendices): `reports/tmlr_review_v2/round_01/input/manuscript.pdf`
SHA-256: `af4eea64c0750637d2695ce49f017ca8c45357d476eead26aed361e48fa3ecef`

## Summary

The paper asks what artist-name "proximity" (similarity of generated images to an artist's works, or how much that similarity rises when the name is added) actually measures. Six commercial text-to-image configurations, four of them OpenAI GPT Image variants, rendered 14 authored outdoor scenes without a painting instruction, with a generic oil-painting instruction, and "in the style of" Monet, Sisley, Pissarro or Cézanne, with two independent requests per cell (1,008 images). What the names add beyond the generic clause is split into a shared change common to the four names (N) and between-name differences (B). Squared sizes use cross-repeat inner products, so they are unbiased under independent repeat noise. Two benchmarks built from reference collections of digitised paintings give context: a faithful imitator and an exact-differences generator. Agreement of the between-name differences with the painters' reference differences is scored by the aligned amplitude β, the relative size Q, the alignment ratio β/√Q (defined after collection) and a repeat-corrected error D = 1 − 2β + Q (prespecified). An exact identity (Eq. 4) splits any proximity gain that is linear in the embedding into a name-independent shared term and a painter-specific term Hβ/4. A second, preregistered collection (1,680 requests) adds a far-apart "century" group and a related Hudson River School group. It tests H1 (the century group's shared fraction is lower) and H2 (across 28 painter pairs, name distances rise with reference distances; exact permutation Mantel test).

Main contributions:
1. A decomposition of the name effect into shared and between-name parts, with noise-corrected estimators and two interpretable benchmarks.
2. An exact identity showing that, for related painters, prototype-proximity gain is mostly a name-independent term.
3. A direction-versus-size reading of specificity (β, Q, β/√Q, D, and the split of D along and off the reference pattern), with genuine-painting controls.
4. A preregistered second collection supporting the claim that the shared fraction depends on how close the painters are.

## Strengths

- **Numerical integrity is excellent.** `build_assets.py --check` passes (37 generated files, 225 registered claims). I reproduced every number I tried exactly from the raw per-image features and embeddings, using my own code rather than the authors' estimator functions (see "Verified numbers"). Every number I checked matches its analysis output.
- **The estimators are sound and correctly derived.** I checked by hand: D = 1 − 2β + Q; the exchangeable-null value of 1/4; the finite-panel bias of H, (3/4)Σ tr(Σ_a)/n_a, with the centroid adding one third of that to N*; Eq. 6; and Eq. 4. Eq. 4 also holds to 1e-12 on the data.
- **Preregistration of the second collection is real and verifiable.** `psv3-r1/freeze.json` binds `PROTOCOL.md` (fb85328b…) and the analysis code (897f8727…), and both match the shipped files. The freeze (01:16:15 UTC) precedes the first request (01:16:24 UTC). The readout plan (v6) is dated during the collection and before measurement (measurement receipt 07:11 UTC). The two refusals, the 12-scene complete panel, the amendments and the ceiling increase are reported accurately.
- **The paper is transparent about which analyses were added after collection.** Section 4.5 is unusually explicit about what was prespecified, what was added afterwards and what was known at each stage. Inference is honest about scope: intervals describe 14 authored scenes and fixed panels.
- **Failure modes are well probed.** Sensitivity to repeat dependence (the ρ at which conclusions flip), the D = D_agg + V_scene split, the genuine-painting controls with distinct works, feature reweighting, reference sources and content-matched targets are all examined. Readouts that disagree (proximity, recognition, D) are reported rather than hidden.
- **The core identity (Eq. 4) is simple, correct and useful to evaluators.** Any linear prototype-proximity gain contains a term that cannot depend on which name produced which image.

## Weaknesses

W1. **The closeness claim is stated more strongly than two groups allow** (Abstract ll. 24–26 "a second collection … confirms it"; Section 5.2 title; Section 6 "The second collection supports this reading").
- H1 compares one distant group with one close group. Closeness is confounded with how familiar the names are (the authors say so in Sections 1, 6 and 7, but not in the abstract). The scene-resampling interval cannot address a group-level confound.
- The paper's own data show that closeness does not determine the observed fraction. In the primary representation, the Impressionists and the Hudson River School are about equally close: H is 5.92 against 6.24 (Table 30), and the preregistered faithful benchmarks are 84.8–95.2% against 90.1–96.9%. Yet the observed shared fractions differ by 23–28 points in five of six configurations (Table 2).
- For GPT Image 1, the preregistered faithful prediction is higher for the Impressionists (95.2% against 90.5%; `refs-20261002/predictions.json`), but the observed fraction is far lower (71.3% against 95.7%).
- The Hudson River School's high fraction comes with β ≈ 0 (Table 32). It is a failure to differentiate the names, not the "good imitation" scenario that the abstract says the second collection confirms. Whether good imitation would be mostly shared is shown analytically by the faithful benchmark, not by the experiment.
- The evidence therefore supports a narrower statement: the observed shared fraction reflects both closeness and how strongly a generator differentiates the names.
- H2 is somewhat stronger evidence, and it holds beyond the group block. My recomputation of the mean Spearman correlation over configurations gives 0.78 within the century group's 6 pairs, 0.74 over the 16 cross-group pairs, 0.77 over the 22 non-Hudson pairs and 0.09 within the Hudson River School's 6 pairs. The paper does not report this breakdown.

W2. **Century-group reproduction is described through the readouts that favour it** (Abstract ll. 33–35 "in the right direction and near their size"; Intro bullet 2; Section 5.2 "roughly in size").
- β is the amplitude along the reference pattern only. The total size of the century group's between-name differences is Q = 1.41–3.13 (1.2–1.8 times the reference norm), with B/H = 1.33–2.56.
- The prespecified error D for the century group is 0.73–1.58, with only FLUX.2 Max's interval entirely below 1 (Table 32). That is about the same range as the Impressionists' 0.80–1.74.
- The abstract's ordering ("distant painters … near their size, the Impressionists' in part, the Hudson River painters' barely") therefore holds for β, the alignment ratio and D_held, but not for D. D is the paper's own prespecified error, and the paper's central recommendation is to report direction and size separately.
- Section 5.2 never mentions the century group's D.

W3. **H1's bootstrap handling differs from the stated rule and is not reported** (Section 4.5; Table 2; Appendix C, last sentence; Appendix H).
- Appendix C says that scene-bootstrap draws with a non-positive denominator are dropped and counted. The frozen H1 code (`painter_specificity_v3/analysis.py`, `closeness_test`) keeps them.
- With the protocol seed (20261003), 90 of the 5,000 draws give FLUX.2 Max a non-positive N + B for the Hudson River School. For the same configuration, 150 century-group draws and 237 Hudson draws give fractions outside [0, 1].
- This is what produces FLUX.2 Max's adjusted interval of [−198.2, +90.2] points in Table 2. The pooled H1 conclusion is unaffected (my rerun gives [−76.6, −61.8] against the reported [−76.5, −62.6]), but the count should be reported and the rule stated consistently.

W4. **Coverage of the ratio statistics is not checked.**
- The percentile intervals for ratio statistics (N/(N+B), shared-gain shares, the H1 difference, the alignment ratio) come from resampling 12–14 authored scenes.
- The coverage simulation in Appendix C covers only the Student intervals for β and D. Percentile intervals for ratios with 12–14 clusters can under-cover, and some of these ratios have unstable denominators (W3).

W5. **The alignment ratio may not be comparable across painter groups** (Section 5.2: "above that of every configuration for the Impressionists").
- β/√Q is scale-free within a group. Across groups, though, the spread H differs by a factor of 5.6, so repeat noise, scene variation and off-pattern name effects of fixed absolute size enter Q with different weights.
- This comparison should be labelled descriptive, with that caveat.

W6. **The headline 66.7–88.4% split was added after collection.**
- The split against the generic baseline (the abstract's 66.7–88.4%) was added after collection. The protocol prespecified the split against the artist-free baseline (82.5–95.7%; `painter_specificity_v1/PROTOCOL.md`, "Explanatory diagnostics").
- Section 4.5 discloses this, but Section 5.1 and Table 1 present the generic-baseline split without the flag.

W7. **The supplement has documentation inconsistencies.**
- The hash-bound `studies/painter_specificity_v3/PROTOCOL.md` still opens with "Version 1.0 **draft** … Not frozen". A reader of the supplement who does not inspect `freeze.json` will doubt the preregistration.
- The protocol's prose definition of H2 does not mention the panel-size correction of reference distances. The frozen code applies it as the primary statistic, and the paper describes it as prespecified. Correct in substance, but the text and code should agree, or the paper should say that the correction was fixed in code.

W8. **Clarity and length.**
- The main text runs to about 16 pages, which makes this a long submission under TMLR guidance.
- Section 4.3 defines β, Q, β/√Q, D, D_held, D_agg and V_scene in one paragraph. The introduction's bullets are very dense with numbers.
- Some passages read as accumulated responses to earlier reviews, for example the history of the with-replacement genuine-painting control in Table 16 and Appendix D. These can move to the appendix.
- In Table 32, the "–" for the Hudson River School's GPT Image 1 shared gain is not explained.

W9. **Pixel-level reproduction is not yet possible.** The generated images are not in the supplement, so features cannot be re-extracted from pixels. This is disclosed. The table and claim replay is otherwise complete.

## Requested changes

**Critical (must change for acceptance; all are text edits and need no new data):**

1. **Calibrate the closeness claim (W1).**
   - In the abstract, replace "confirms it" with wording such as "is consistent with this", and name the closeness–familiarity confound there.
   - In Section 5.2, add the Impressionist–Hudson comparison at matched closeness: H and the faithful benchmarks are similar, yet observed fractions differ by 23–28 points in five of six configurations. State plainly that closeness predicts the faithful benchmark, not the observed fraction, which also depends on how much a generator differentiates the names.
   - Retitle Section 5.2 or qualify it, for example "The shared fraction falls when the painters are far apart".
   - Report H2 within subsets of pairs (within the century group, across groups, within the Hudson River School), so readers can see that the dose-response is not only the group contrast.
2. **Make the century-group size claim consistent with the paper's own framework (W2).**
   - In the abstract, introduction and Section 5.2, say "in the right direction with aligned amplitude near the reference (β 0.84–1.29), but with total differences 1.2–1.8 times the reference norm (Q 1.41–3.13)".
   - Report the century group's D (0.73–1.58; only FLUX.2 Max's interval is below 1), and say that by D the century group is reproduced about as well as the Impressionists, while by β, the alignment ratio and D_held it is reproduced better.

**Minor:**

3. Report how many H1 bootstrap draws had non-positive denominators, or fractions outside [0, 1], per configuration and group (90 Hudson draws with N + B ≤ 0 for FLUX.2 Max). Reconcile Appendix C's "dropped and counted" rule with the frozen H1 code. Explain FLUX.2 Max's [−198.2, +90.2] in the caption of Table 2 (W3).
4. Add a coverage check (simulation or jackknife/BCa comparison) for the percentile intervals of the ratio statistics with 12–14 scenes, or state that their coverage is unverified (W4).
5. Label the cross-group comparison of alignment ratios as descriptive and note its dependence on group-specific H (W5).
6. In Section 5.1 and the caption of Table 1, flag the generic-baseline split as added after collection, and give the prespecified artist-free value (82.5–95.7%) beside it (W6).
7. In the supplement, add a note that `freeze.json` binds `PROTOCOL.md` despite the file's "draft / Not frozen" header. State that the H2 panel-size correction was fixed in the frozen analysis code rather than in the protocol prose (W7).
8. Optional, using existing data: a descriptive check of whether the shared change is group-specific rather than a generic "any artist name" effect. For example, compare the cosine between the two new groups' noise-corrected shared changes with the cosine between their targets t. My quick computation gives −0.17 to 0.65 for the shared changes against 0.66–0.95 for the targets. This would partly address the limitation stated in Section 6 without a fictitious-name arm, interpreted with care.
9. Shorten the main text toward TMLR's regular length. Split the definitions in Section 4.3 into a short list. Move the history of the with-replacement control and some sensitivity detail to the appendices. Explain the "–" entry in Table 32. Figure 3's caption says "dotted line"; the line is dashed (W8).
10. Commit to releasing the generated images, or a hashed external archive of them, on de-anonymisation, so that features can be re-extracted from pixels (W9).

## Criterion 1: claims and evidence — **partially**

- **Fully supported:**
  - the decomposition and its estimates (Table 1);
  - the benchmarks;
  - the exact identity (Eq. 4) and the shared-term shares (Table 3);
  - the cross-configuration variance attribution;
  - the positive direction of every configuration's between-name differences;
  - the prespecified pairwise results (2 of 15 resolved);
  - the descriptive readout disagreements;
  - the H1 and H2 test outcomes as tests.
- **Calibration and limitations are generally good.** Post hoc status is flagged, the intervals are scoped to the authored scenes, and repeat dependence is examined.
- **Two headline statements go beyond the evidence as worded** (W1, W2):
  - The second collection is said to "confirm" the closeness explanation, although the familiarity confound is unaddressed and the Impressionist–Hudson contrast at matched closeness shows the observed fraction is not determined by closeness.
  - The distant painters' differences are said to be reproduced "near their size", although the paper's own prespecified error D says the total size is 1.2–1.8 times the reference norm.
- Both gaps close by narrowing the wording. No new experiments are needed.

## Criterion 2: audience and clarity — **yes**

Researchers who evaluate style imitation, mimicry protection and concept erasure, and who use CSD or CLIP proximity as a style-fidelity score, will find the identity and the benchmarks directly useful. The main message comes through clearly in the title, abstract, Figure 1, Figure 3, Figure 4 and Section 6. The text is dense and long, and Section 4.3 is hard going, but it is precise; these are presentation improvements rather than barriers (minor item 9).

## Desk-rejection screen — risk **low**

- In scope for TMLR (ML evaluation methodology).
- Correct TMLR style, anonymous, with broader impact and reproducibility statements. Use of AI assistants is disclosed.
- The writing is dense but specific and internally consistent, and every number is backed by retained analysis outputs. It does not read as low-care machine-generated text.
- The main length (about 16 pages) makes it a long submission, which is not grounds for desk rejection.

## Recommendation: **minor revision**

The statistical work is careful and the numbers are fully reproducible. The required changes are edits to the claim wording (critical items 1–2) plus reporting details. With those edits, every claim would be supported as worded.

## Confidence: 4 / 5

I checked the estimators algebraically and recomputed the main tables and both prespecified tests independently. I did not re-extract features from pixels (the images are not supplied), and I did not re-run all resampling analyses.

## Verified numbers and how

I recomputed everything with my own scripts (in my scratchpad, not the repository). They load the raw per-image features (`psv2-20260911/measurements.jsonl`, `psv3-r1/measurements.jsonl`), the reference features (`pfg2-method-20260905/confirmation_features.jsonl`, `refs-20261002/features.jsonl`), the scaler, and the CLIP/CSD embeddings (`reports/painter_learned_audit_v1`, `psv3-r1/embeddings_*.npz`). The estimators are written from the paper's equations, not imported from the authors' code.

**Replay check**
1. `uv run --locked python paper/tmlr/build_assets.py --check` prints "ok: 37 generated files and 225 claims".

**First collection, 31 features**
2. H = 5.915 (Table 10).
3. Table 1, all six rows, exact match. Shared fraction 71.3/70.9/71.1/66.7/69.1/88.4%; N/H 5.26/4.98/4.99/3.97/1.36/5.34; B/H 2.12/2.04/2.03/1.98/0.61/0.70; faithful 95.2/89.3/84.8/86.9/92.5/90.4%; exact differences 84.0/83.3/83.3/79.9/57.6/84.2%.
4. Table 12, exact match: cos(c, t) 0.85/0.66/0.57/0.72/0.75/0.86; λ 44.1/50.7/54.3/55.6/24.8/64.6%.
5. Table 5, exact match: β 0.938/0.999/0.772/0.824/0.442/0.470; Q 2.449/2.223/2.281/2.289/0.994/0.741; β/√Q 0.600/0.670/0.511/0.545/0.444/0.546; D 1.572/1.226/1.738/1.641/1.109/0.801. The identity D = 1 − 2β + Q holds per configuration.
6. Prespecified simultaneous intervals, using t(13, 1 − 0.05/42) on per-scene values: β for GPT Image 1 [0.709, 1.168] and FLUX.2 Max [0.239, 0.701]. Pairwise D differences: Flare − FLUX.2 Max 0.937 [0.256, 1.618]; Sunburst − FLUX.2 Max 0.840 [0.058, 1.623]; GPT Image 1 − FLUX.2 Max 0.771 [−0.037, 1.580]. So 2 of 15 are resolved.
7. GPT Image 1's D with Bonferroni over six configurations is [0.935, 2.210]; the nominal interval is [1.129, 2.016].
8. FLUX.2 Max's shared-fraction scene interval and obs. < faithful share, from my own 5,000-draw bootstrap with a different seed: [77.1, 94.2] and 85.6%, against the reported [76.8, 94.2] and 84.1%. Consistent within Monte Carlo error.

**First collection, CLIP and CSD**
9. Tables 3, 4 and 6, exact match: gains, shared terms, painter-specific terms Hβ/4, shared shares, recognition, β, Q, β/√Q and D. Values checked include CLIP 74.5/73.2/78.8/77.7/83.8/81.7% and CSD 72.7/54.2/65.0/67.4/79.7/77.6%; recognition CLIP 60.7/68.8/59.8/58.9/51.8/41.1% and CSD 72.3/75.9/62.5/61.6/50.9/39.3%.
10. Eq. 4 holds to 1e-12.
11. corr(gain, shared) is 0.96 (CLIP) and 0.95 (CSD). corr(gain, painter-specific) in CSD is −0.65. The variance ratio is 10.8 (reported as 11) in CLIP and 5.8 in CSD. Spearman(recognition, alignment ratio) is 0.94 and 0.89.

**Second collection**
12. Missing cells: GPT Image 1 / scene 8 / Bierstadt and Sunburst / scene 5 / Durand, leaving 12 complete scenes.
13. Table 2 per-group fractions (century 29.5/18.5/18.9/23.6/21.6/17.7%; Hudson 95.7/98.6/93.8/93.5/95.1/89.4%) and the October faithful values, exact match.
14. H1 pooled difference −72.7 points, exact match. My own bootstrap gives [−76.6, −61.8]; the reported interval is [−76.5, −62.6].
15. H2 mean Spearman 0.849, per configuration 0.77–0.92; uncorrected 0.84. The exact p from the analysis output is 0.00027 (11/40,320); CLIP 0.86 (p = 0.00037); CSD 0.92 (p = 0.00055).
16. Within-subset H2, not in the paper: 0.78 (century, 6 pairs), 0.74 (cross-group, 16 pairs), 0.09 (Hudson, 6 pairs).
17. Table 32 β, Q, β/√Q and D for both groups, exact match (for example, century D 1.58/0.94/0.99/1.12/1.13/0.73).
18. Panel-size-corrected Hudson H is 4.21/6.24 = 0.676 of the uncorrected value, matching "β near 0.68".
19. FLUX.2 Max H1 draws with N + B ≤ 0: 90 of 5,000 (Hudson), using the protocol seed.
20. New charges: $72.93 = $195.22 accounted − $112.29 baseline − $10 of unreleased holds.

**Provenance**
21. The hashes of `PROTOCOL.md` and `analysis.py` match `freeze.json`. Timestamps: freeze 01:16:15 UTC, first request 01:16:24 UTC, measurement 07:11 UTC (2026-10-03). The preregistered predictions (Table 30) match `predictions.json`.

**Algebra (checked by hand)**
22. D = 1 − 2β + Q; the exchangeable-null ratio of 1/4; E[Ĥ] − H = (3/4)Σ tr(Σ_a)/n_a, with the centroid contributing a third of that to N*; Eq. 6; Eq. 4 and Eq. 8.
