# TMLR review: "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation"

Role: empirical reviewer (evaluation of text-to-image generative models)
PDF read: `reports/tmlr_review_v1/round_02/input/manuscript.pdf`, SHA-256 `2837299e02bca86a872f392d19e4e5a74ee72944be0c79441b89eea7deb446d6` (all 23 pages, main text and appendices, rendered and as text)

## Summary of the submission

The paper asks what an artist name adds to a text-to-image prompt, beyond a generic "oil painting" instruction, when the prompt set contains related painters. Fourteen fixed outdoor scene descriptions were rendered under six clauses: no clause, "Render as an oil painting.", and the same clause "in the style of" Monet, Sisley, Pissarro or Cézanne. There were two independent requests per cell and six closed-service configurations: GPT Image 1, GPT Image 2, GPT Image 2.5 Flare and Sunburst, Nano Banana 2 and FLUX.2 Max, for 1,008 images in total. Images are described by 31 hand-crafted color, spatial and texture statistics (the prespecified primary representation) and by CLIP ViT-L/14 and CSD embeddings. They are compared with 649 Wikimedia reproductions of the four painters.

The named-minus-generic change is split into a component shared by all four names (N) and between-name differences (B). Squared sizes are estimated without noise bias using cross-repeat products, as in crossnobis/RSA. The split is benchmarked against an exchangeable null (25%) and a "faithful imitator" whose named means sit on the painters' reference means. In the embeddings, the gain in cosine similarity to the prompted painter's prototype is decomposed exactly into a shared term and a painter-specific term, Hβ/4 (Eq. 4).

Main findings:
- 66.7–88.4% of the added squared change is shared, against 84.8–95.2% for the faithful imitator.
- The shared term supplies 73–84% (CLIP) and 54–80% (CSD) of the proximity gain, close to the faithful values.
- Between-name differences align with reference painter differences in aggregate (β > 0 for all six configurations), but unevenly across pairs.
- Proximity, agreement (error D) and recognition pick different "best" configurations.
- A separate SD-Turbo collection shows a similar overall pattern.

The paper separates its prespecified inference (6 aligned amplitudes plus 15 pairwise D differences) from retrospective descriptive analyses, and ships hash-bound outputs with a replay script.

Contributions as claimed:
1. A controlled design with a generic-style control and repeat-corrected estimators.
2. Benchmarks (null and faithful imitator) that make the shared fraction interpretable.
3. An exact decomposition of prototype-proximity gain.
4. Evaluation recommendations.

## Strengths

- **Clean and useful design.** Fixed scenes crossed with a generic-style control isolate what the name adds. The generic control is the right baseline, and one that most artist-imitation studies lack. Su et al. (2025) use a same-seed no-name comparison but no generic-style arm.
- **Sound estimators.** Cross-repeat products remove the positive noise bias of squared norms, and negative estimates are retained honestly. I checked the algebra of Eqs. 1–8, including:
  - the exchangeable-null 1/4, via N + B = Σ‖h_a‖²;
  - the centroid-proximity identity (Eq. 6);
  - D = 1 − 2β + Q;
  - the D_agg/V_scene split;
  - the 3/4 Σ tr(Σ_a)/n_a bias of H.
  All are correct.
- **Simple and communicable decomposition.** Eq. 4 has direct practical value for anyone who scores generated images against artist prototypes, for example the CSD "general style similarity" score in Somepalli et al. (2024) or prototype similarity in Su et al. (2025).
- **Numbers reproduce.** From the retained vectors I recomputed:
  - N/H, B/H and N/(N+B) for all six configurations;
  - the faithful fraction (N*/H = 19.6, 8.3, 5.6, 6.6, 12.3, 9.5);
  - β, Q and D (Table 3);
  - the Monet–Sisley pair β (Table 14).
  All match the manuscript to the reported precision.
- **Unusually transparent inference.** The paper separates prespecified from retrospective analyses, discloses that some benchmark values were first computed during internal review, and states what its intervals do and do not cover. The simulation shows that coverage collapses when a configuration-level state is shared across scenes and repeats. It also includes a repeat-dependence sensitivity (ρ at which orderings flip), genuine-painting controls for D, reference resampling, class-matched targets, feature reweighting, leave-one-feature-out, source cropping, and a finite-sample correction of H.
- **Good scoping language in most places.** Examples: "labels denote requested configurations, not verified checkpoints"; "not perceived resemblance"; "cannot separate movement toward these painters from a generic effect of any artist name".

## Weaknesses

### W1. The headline claim is stated more generally, and more strongly, than the evidence (Abstract lines 1–4, Introduction bullet 2, Section 5.2, Section 6 "Recommendations")

The abstract opens: "We show that, *for related painters*, this proximity gain mostly measures a change shared by every name … and that this *would remain true* for a generator that reproduced each painter exactly." There are two problems.

(a) The evidence is one set of four painters, one clause template and 14 authored scenes. The faithful-imitator result is essentially a geometric consequence of N*/H being large (5.6–19.6), that is, the generic outputs being far from the painters' centroid relative to the painters' spread. The generalisable statement is conditional: whenever N* ≫ H, most of any faithful movement is shared. That condition should be stated rather than "for related painters". Whether it holds for other related groups, templates or domain gaps is not tested.

(b) In CSD, the faithful imitator's shared part of the proximity gain is 48.3% for GPT Image 2 (Table 2), which is below one half. The observed value is 54.2%, with a scene-deletion range of 52.4–55.6% in the supplementary output. So "mostly … would remain true for a faithful imitator" is contradicted by one of the paper's own numbers, and "mostly" is borderline for the observed CSD value. The abstract gives the 48.3–75.7% range but its lead sentence does not reflect it.

### W2. The observed-vs-faithful comparison mixes two different causes, and invites a misreading (Section 5.1, Figure 3 caption, Abstract)

The paper stresses that the observed shared fraction is "below the faithful value in every configuration and representation". The faithful value, however, assumes the full generic-to-centroid distance is covered (λ = 1), while the configurations cover 24.8–64.6% of it. The gap therefore combines:
- under-coverage of t;
- the size of the between-name differences (B/H = 0.61–2.12).

These have opposite meanings for specificity.

A benchmark that holds the observed shared movement fixed and gives reference-sized between-name differences, N/(N+H), makes this visible. I recomputed it from the retained vectors: 84.0, 83.3, 83.3, 79.9, 57.6 and 84.2% (in Table 1 order).
- For the four GPT configurations, the observed fraction is below this benchmark because B > H (oversized differences).
- For Nano Banana 2, the observed 69.1% is *above* this benchmark (B/H = 0.61). It is below the faithful 92.5% only because λ = 24.8%.

A reader who takes "below faithful" to mean "more painter-specific than a faithful imitator" would be wrong for Nano Banana 2 and misled for the GPT configurations. The paper never makes that inference explicitly, but the abstract's juxtaposition of the two ranges invites it. This benchmark also sidesteps the problem that t includes the gap between photographed paintings and generated images and the content-mix gap. The paper acknowledges that gap (Section 4.2, Limitations), but at present it is built into the headline benchmark.

### W3. Pair-level and cross-representation claims have no uncertainty, and the primary representation's ability to tell these painters apart is not reported (Section 5.3 paragraph 3, Figure 4, Table 14, Abstract "unevenly across painter pairs and representations")

- **No intervals.** Pair-level aligned amplitudes and errors (Figure 4; the Monet–Sisley columns of Table 14) are reported without intervals. From the retained vectors, the unadjusted scene standard errors of the Monet–Sisley β are 0.04–0.13. Reference resampling adds roughly ±0.12 (SD) in the projection of the Monet–Sisley reference contrast. Some pair statements look robust (Sunburst −0.249, SE ≈ 0.06), others do not (Nano Banana 2 −0.044, SE ≈ 0.13), and the paper gives the reader no way to tell which is which.
- **No discriminability check for the 31 features.** The paper checks that CLIP and CSD prototypes classify the 221 development works (79.8% / 79.6% macro), but runs no such check for the 31 features. I ran the analogous check: nearest reference mean in the standardized 31 features on the same 221 development works. It gives **49.8% macro accuracy** (Monet 39.6%, Sisley 30.6%, Pissarro 54.2%, Cézanne 75.0%; chance 25%). Leave-one-out on the 649 reference works gives 53.5%.
- **Small pair distances.** The Monet–Sisley and Sisley–Pissarro reference distances are only 0.33H and 0.28H, against 0.89–1.06H for the Cézanne pairs. The paper notes that the first component carries 66% of H and that omitting Cézanne removes most of β.
- **Consequence.** The primary representation separates Monet from Sisley at the work level barely above chance. The contrast with the embeddings ("the weak Monet–Sisley response in the 31 features therefore does not transfer to the embeddings") may therefore say more about the representations than about the generators, and "uneven across representations" should not be read as a property of the generators without this calibration.

### W4. "Texture is the least shared feature family" is not supported per configuration (Introduction bullet 5, title of Section 5.5, Abstract "but not in texture features")

In Table 6, texture is the least-shared family only for GPT Image 1 (48.6), Flare (60.1), FLUX.2 Max (76.5) and SD-Turbo (36.6):
- for GPT Image 2 and Sunburst, spatial is lower (59.6, 61.5);
- for Nano Banana 2, texture is the *most* shared family (79.8, against 56.8 for color).

The statement holds only as a comparison of ranges (the lowest minimum and maximum) or of means across configurations (≈68 vs 71.5 spatial vs 74 color, a small margin). The SD-Turbo "not in texture" statement is fine as written.

### W5. The error D, the prespecified primary endpoint, is hard to interpret on the scale the paper uses (Section 4.3, Section 5.3, Introduction bullet 3)

D is anchored at 0 (exact) and 1 (no distinctions), and the text emphasises that "only FLUX.2 Max's error falls clearly below that of a generator making no painter distinctions". The paper's own genuine-painting controls (Appendix D) show that genuine works scored the same way average 0.234 (pooled; 95% range −0.76 to 1.38) and 0.753 (within content classes). The supplementary output also contains a class-target control, mean 0.731 with range −0.25 to 1.95, which the paper does not report.

These controls also contain half-sample target noise, so they are not direct analogues. Even so, they show three things:
- a content-faithful set of genuine paintings would score far from 0;
- the per-scene D is very noisy at 14 scenes;
- FLUX.2 Max's 0.801 lies inside the genuine-painting ranges.

Because D = 1 − 2β + Q, it rewards small differences. A generator with β = 0.47 and Q = 0.74 beats one with β = 1.00 and Q = 2.22. The paper says this (Sections 5.3–5.4 and Table 13), which I appreciate. But the D-based ranking statements in the Introduction and Section 5.4 still read as if D ≈ 1 were a meaningful "no specificity" line. D is also scored against a pooled target that mixes style with subject mix: Monet's collection is 64% water scenes. The class-target sensitivity (Table 15) moves D by up to 0.2.

### W6. Interpretation of the shared change (Section 6, "What the shared change is")

The Discussion opens by asserting that "the first is movement toward the four painters' common appearance". The evidence is a positive cosine with t, the direction from the generic mean to the reference centroid. But t also contains whatever separates photographed nineteenth-century oil paintings from clean generated images: varnish tone, canvas texture, capture and compression. Any painterly or old-master cue would move along it. The paper concedes two sentences later that a generic artist-name effect cannot be excluded. The opening sentence should be hedged to match.

The cleanest evidence would come from:
- a fictitious or unknown artist name;
- a group clause ("Impressionist");
- a stylistically distant painter set.

The authors already name some of these. I list this as optional strengthening, not a condition, because the title claim (proximity gain is dominated by the shared term) does not depend on what the shared term is.

### W7. Positioning is accurate, but "a common readout is proximity" is thinly documented (Section 1 paragraph 1, Section 2)

I checked every related-work description I could, and each is accurate (see "Literature checked"). The introduction, however, does not name a specific published analysis that uses named-minus-unnamed proximity *gain* as evidence of artist-specific imitation. The closest documented uses are:
- raw prototype similarity: the CSD "GSS" score in Somepalli et al. (2024), and prototype similarity in Su et al. (2025);
- closed-set recognition: Casper et al., Moayeri et al., Su et al.

Closed-set recognition already conditions on between-name information, although the paper's shift analysis (Section 5.4, Appendix F) shows that it still responds to shared offsets, which is a nice point. Some related work is missing:
- change-direction readouts such as CLIP directional similarity (Gal et al., 2022, StyleGAN-NADA; used in InstructPix2Pix), which are close in spirit to β;
- Su et al.'s own observation that recent generators (SD3.5, FLUX.1-dev) often respond weakly to artist names, which is consistent with FLUX.2 Max's weak between-name differences here;
- recent work on artist names triggering generic "canonical shortcuts" (Xing et al., 2026, arXiv:2608.06751), which relates directly to the shared component.

### W8. Smaller transparency and reporting points

- **Protocol history not disclosed.** The supplied protocols show that the first collection attempt (1,152 planned images, 16 scenes) was terminated before feature extraction. The reason was that an upstream route returned an image for an invalid model identifier. The design was then reduced to 14 scenes before outcomes were seen. Neither fact is in the manuscript. Both are relevant to the prespecification narrative in Section 4.5 and to the "requested configurations" caveat.
- **Bootstrap status unclear.** Section 4.5 lists "the scene bootstrap" among the post-hoc additions. The v1 protocol did prespecify a paired scene bootstrap (5,000 draws) for the pairwise D differences, and it was computed in the primary analysis output. The Table 5 readout bootstrap is the post-hoc one. The text should distinguish the two.
- **Missing deletion ranges for Table 2.** Scene-deletion ranges exist for the Table 2 shares but are not reported. They are narrow and would reassure the reader, especially for the 54.2% CSD value.
- **Aggregation dependence.** The headline range depends on aggregation: 52.8–93.6% within scenes, and 82.5–95.7% against the artist-free baseline. Section 5.1 or the abstract should flag this. Nano Banana 2 moves from 69.1% to 52.8%.
- **Generated images not released.** The reason given is archive size. For an evaluation paper whose conclusions rest on features of these images, an external archive (e.g., Zenodo) at camera-ready would let others re-extract features and test other representations.

## Requested changes

### Critical (required for acceptance). All can be met by editing and by computations on the retained data. No new generation is required.

1. **Scope and correct the headline claim (W1).** In the abstract and introduction:
   - replace "for related painters" with the tested scope (four related painters, one template, 14 scenes);
   - state the geometric condition under which a faithful imitator's change is mostly shared (N* ≫ H);
   - qualify "would remain true for a generator that reproduced each painter exactly", since the CSD faithful share for GPT Image 2 is 48.3% and the observed share is 54.2%.

   Alternatively, add a stylistically distant painter set to support a general statement, though that is not required if the claim is narrowed.
2. **Make the faithful benchmark interpretable (W2).**
   - Report, next to N*/(N*+H), a benchmark that holds the observed shared movement fixed, such as N/(N+H), or an equivalent decomposition of the observed-vs-faithful gap into coverage (λ, N/N*) and between-name size (B/H).
   - Say explicitly that a below-faithful shared fraction does not by itself mean more painter-specific behaviour (Nano Banana 2 is the counterexample).
   - Revise the Figure 3 caption and the abstract accordingly.
3. **Support or narrow the pair- and representation-level claims (W3).**
   - Add scene and reference-resampling intervals for the pair β and pair D values (Figure 4; the Monet–Sisley columns of Table 14, all three representations).
   - Report the 31-feature discriminability of genuine works on the development panel, alongside the 79.8/79.6% embedding check. My recomputation gives about 50% macro accuracy, with Monet at 40% and Sisley at 31%.
   - Qualify "unevenly across painter pairs and representations" and the "does not transfer to the embeddings" sentence in light of both.
4. **Correct the texture claim (W4).** Rephrase Introduction bullet 5, the Section 5.5 title and the corresponding abstract clause so they match Table 6. Texture is least shared in 3 of 6 main configurations and in SD-Turbo; it is the most shared family for Nano Banana 2.

### Minor

5. Put the genuine-painting D distribution next to Table 3 (pooled, class vs pooled target, and class vs class target, the last of which is in the output but not the paper). Explain that these controls include half-sample target noise. Tone down the "no-distinction" framing of D in the Introduction and Section 5.3 (W5).
6. Hedge the first sentence of Section 6 ("movement toward the four painters' common appearance"). Note that t also carries reproduction and old-painting properties. List a fictitious-name, group-clause ("Impressionist") or distant-painter control as the test (W6).
7. Positioning (W7):
   - name concrete uses of prototype-proximity readouts (CSD GSS; Su et al.);
   - note that closed-set recognition already uses between-name information;
   - add change-direction readouts (CLIP directional similarity);
   - mention Su et al.'s weak-name-effect observation for recent models;
   - consider citing Xing et al. (2026).
8. Disclose the terminated first collection (unverifiable model routing) and the 16→14 scene reduction made before outcomes, in Section 4.5 or Appendix A. Distinguish the prespecified pairwise-D bootstrap from the post-hoc readout bootstrap of Table 5, and consider reporting the prespecified bootstrap and nominal intervals for Table 12.
9. Add scene-deletion ranges to Table 2.
10. Flag in Section 5.1 (or the abstract) that the shared fraction depends on aggregation: 52.8–93.6% within scenes, 82.5–95.7% against the artist-free baseline.
11. Add a figure for the title claim itself: stacked shared vs painter-specific proximity gain, observed vs faithful, per configuration and encoder. Currently this appears only in Table 2, while Figure 3 shows squared-change fractions instead.
12. Readability:
    - move a compact version of the notation table (Table 9) into the main text;
    - reduce the number of numeric ranges in the abstract (about 15 at present);
    - rewrite a few dense sentences, e.g. the last sentence of Section 5.1 paragraph 3 ("…whose between-name differences move the named means away from the painters' individual reference means on balance").
13. De-emphasise the exchangeable null ("far above the exchangeable null of 25%"). Given the faithful benchmark, rejecting it carries little information.
14. In the Recommendations, add content matching of the reference target: Table 15 shows D shifting by up to 0.2 under class-matched targets.
15. Release the generated images through an external archive at camera-ready, or explain why this is impossible.

## Criterion 1: Are the claims supported by accurate and convincing evidence?

**Partially.**

The core within-study results are accurate and well supported. I reproduced the main quantities from the retained vectors. Those results are:
- the shared component dominates both the named-minus-generic change and prototype-proximity gain, in three representations and six configurations;
- β > 0 for all configurations under the prespecified intervals;
- proximity, error and recognition rank configurations differently.

The inference is honest and carefully labelled. Four gaps prevent a "yes":
- the lead claim is generalised beyond one painter set, and its faithful-imitator half is contradicted by one reported CSD value (W1);
- the central benchmark comparison conflates under-coverage with between-name size, so it can be misread (W2);
- pair-level and cross-representation statements lack uncertainty and a discriminability calibration of the primary representation (W3);
- the texture claim does not hold per configuration (W4).

Each gap closes with a narrower claim or with analyses on existing data. None needs new images.

## Criterion 2: Would some of TMLR's audience be interested, and is the paper clear?

**Yes.**

Researchers on artist-style imitation, style protection and unlearning, copyright-oriented auditing, and generative evaluation methodology will find the generic-control design, the Eq. 4 decomposition and the recommendations directly useful. The writing is precise, the limitations are stated plainly, and Figure 1 conveys the idea well.

The paper is dense: many estimands (N, B, H, β, Q, D, D_agg, V_scene, D_held, λ, G, I) and a number-heavy abstract. Parts of Sections 5.3–5.4 take several readings. These are editing issues (items 11–12) and do not prevent a careful reader from following the argument.

## Desk-rejection screen

**Risk: low.**

- **Scope.** The paper is within TMLR's scope: evaluation methodology for generative models.
- **Format.** It uses the TMLR template and is anonymised. The main text ends on page 12 and the appendices are well organised.
- **Quality.** The results are internally consistent, reproducible from the supplied outputs, and the paper discloses its analysis history and its use of AI assistance.
- **Machine-generated appearance.** The prose is polished and very compressed. It does not read as low-care machine-generated text: claims are specific, hedged and checkable.

## Recommendation

**Minor revision.** The substantive evidence is sound. The required changes are mostly corrections of scope and wording plus small analyses on the retained data. If the authors choose to keep a general "for related painters" claim instead of narrowing it, a second, stylistically distant painter set would be needed, and I would then regard the revision as major.

**Confidence: 4/5.** I read the full paper and appendices, checked the derivations, recomputed the key quantities from the retained vectors, and checked the protocols and the related literature. I did not re-extract features from pixels.

## Independent checks performed (read-only, from retained vectors and outputs)

- Recomputed N/H, B/H, N/(N+B), N*/H, faithful fraction, β, Q and D for all six configurations. All match Tables 1, 3 and 10.
- Recomputed the Monet–Sisley pair β (matches Table 14) and its unadjusted scene SEs (0.04–0.13).
- Computed N/(N+H): 84.0, 83.3, 83.3, 79.9, 57.6 and 84.2% (W2).
- Computed pairwise reference distances relative to H: M–S 0.33, M–P 0.41, S–P 0.28, M–C 1.03, S–C 0.89, P–C 1.06.
- Computed 31-feature nearest-reference-mean accuracy on the 221 development works: 49.8% macro (M 39.6, S 30.6, P 54.2, C 75.0). Leave-one-out on the reference panel: 53.5%.
- Read scene-deletion ranges for the Table 2 shares from the diagnostics output (CSD GPT Image 2: 52.4–55.6%) and the class-target genuine control (mean 0.731, range −0.25 to 1.95) from the review output.
- Checked the v1/v2 protocols and the post-result plan against the manuscript's account of what was prespecified (W8).

## Literature checked

- Su et al., 2025, "Identifying Prompted Artist Names from Generated Images" (arXiv:2507.18633). 110 artists; content-controlled name substitution; same-seed no-name CLIP comparison; prototype similarity. The manuscript describes it accurately. It also reports weak artist-name effects in recent generators, which the manuscript does not cite.
- Somepalli et al., ECCV 2024, CSD. Artist prototypes and the GSS score; described accurately.
- Casper et al., 2023 (arXiv:2307.04028). 70 artists, zero-shot CLIP classification, about 81% average accuracy; accurate.
- Moayeri et al., ICLR 2025, ArtSavant. About 20% of 372 artists at risk; accurate.
- Frochte, 2026 (arXiv:2605.09030v2). Raw CSD cosine fails for part of a 91-artist corpus; also prompts FLUX.1-dev for 15 artists; accurate.
- Verma et al., TMLR 2025, imitation thresholds; accurate.
- Deliège et al., J. Imaging 2025. Expert ratings, Midjourney v6; accurate.
- Asperti et al., BDCC 2025, AI-Pastiche; accurate.
- Fu et al., 2025 (arXiv:2508.01408). VLM attribution and AI-painting detection; accurate.
- Kim et al., PNAS 2026 (doi:10.1073/pnas.2517969123). Historical change in CLIP space; accurate.
- Xing et al., 2026, "Beyond Starry Night" / Atelier (arXiv:2608.06751). Artist names trigger canonical shortcuts; relevant and not cited.
- Gal et al., 2022, StyleGAN-NADA (directional CLIP similarity), and Brooks et al., 2023, InstructPix2Pix. Change-direction readouts; not cited (from my own knowledge, not web-checked).
- OpenRouter and gateway listings for GPT Image 2.5 Flare/Sunburst (released 8 September 2026, five quality levels). Consistent with the manuscript's configuration description.
- Hönig et al. (ICLR 2025), Gandikota et al. (ICCV 2023), Kumari et al. (ICCV 2023), Diedrichsen & Kriegeskorte (2017), Benny et al. (2021), Naeem et al. (2020), Parmar et al. (2022). Descriptions consistent with my knowledge of these papers.

## Factual errors found

1. Introduction bullet 5, Section 5.5 title, Abstract: "Texture is the least shared feature family" is contradicted per configuration by Table 6. For GPT Image 2 and Sunburst spatial is lower; for Nano Banana 2 texture is the most shared family.
2. Abstract, sentence 2: "this would remain true for a generator that reproduced each painter exactly" (proximity gain *mostly* shared) is contradicted by the CSD faithful value of 48.3% for GPT Image 2 (Table 2).

PDF SHA-256: `2837299e02bca86a872f392d19e4e5a74ee72944be0c79441b89eea7deb446d6`
