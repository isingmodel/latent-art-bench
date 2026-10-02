# TMLR review: "Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation"

Reviewer role: empirical (evaluation of text-to-image generative models)
PDF read: `manuscript.pdf`, SHA-256 `7da8263c19eeb6ec1b3dc1c6292306712a7e5297e99f95009649c66c80299310` (all 25 pages, main text and appendices A–H)

## 1. Summary of the submission

The paper asks what "proximity gain" measures when a text-to-image model is prompted with an artist's name. Proximity gain is how much closer the named outputs move to the artist's reference works. Six commercial configurations (GPT Image 1, GPT Image 2, GPT Image 2.5 Flare and Sunburst, Nano Banana 2, FLUX.2 Max) rendered 14 authored outdoor scenes under six clauses: artist-free, a generic "oil painting" instruction, and that instruction "in the style of" Monet, Sisley, Pissarro or Cézanne. Each cell has two separate requests, 1,008 images in total. The images are measured with 31 hand-crafted colour, spatial and texture features (the prespecified representation) and with CLIP ViT-L/14 and CSD embeddings. They are compared with 649 Wikimedia reproductions of the four painters.

The method splits the named-minus-generic change into a component shared by all four names and between-name differences. Squared sizes are estimated from cross-repeat products, which removes the noise bias. Two benchmarks built from the reference means sit alongside the split: a "faithful imitator" and an "exact-differences" generator.

The main findings:
1. 66.7–88.4% of the squared change the names add is shared. A faithful imitator would show 84.8–95.2% and an exact-differences generator 57.6–84.2%, so a large shared fraction alone does not indicate weak specificity.
2. In CLIP and CSD, an exact identity (Eq. 4) splits the prototype proximity gain into a shared term and a painter-specific term, H·β/4. The shared term supplies 73.2–83.8% (CLIP) and 54.2–79.7% (CSD) of the gain, close to the faithful-imitator values.
3. Specificity is assessed through the aligned amplitude β and the error D against the reference painter differences. All six β are above 0. In the 31 features, three configurations have D > 1, meaning they are worse than making no painter distinctions.
4. Proximity, recognition and D rank the configurations differently.
5. The shared fraction varies by feature family.

The authors are careful to state which analyses were prespecified: the family of 21 comparisons, i.e. six values of β and 15 pairwise differences in D. Everything else is labelled retrospective.

## 2. Strengths

- **Clean, useful design and estimator.** The generic-painting control is the right comparator for isolating what the *name* adds. The split into shared and between-name parts is exact, and the unbiased squared-size estimator from cross-repeat products is well founded; the paper links it correctly to cross-validated RSA distances. Eq. 4 is a simple but genuinely useful observation: any linear prototype score splits into a name-independent term plus H·β/4. It shows directly why proximity gain cannot by itself certify painter specificity when the painters are related.
- **Benchmarks against the right counterfactuals.** The faithful-imitator and exact-differences benchmarks (Sec. 4.2, Tables 1–2, Fig. 3) stop a large shared fraction from being misread as "no specificity". The paper states plainly that the faithful benchmark includes the gap between generated images and photographed paintings.
- **Unusually transparent inference.** The prespecified family is clearly separated from the retrospective analyses (Sec. 4.5). The intervals are explicitly scoped to the 14 authored scenes and the finite reference panels. Coverage is checked by simulation, including a failure scenario (App. C). The sensitivity to repeat dependence is quantified, down to the ρ at which orderings reverse (App. A). I checked the protocol (`studies/painter_specificity_v2/PROTOCOL.md`, v1 scientific specification) against Sec. 4.5, and the description is accurate. The v2 reduction from 16 to 14 scenes was fixed before any feature outcome.
- **Extensive robustness.** The paper checks within-scene versus pooled aggregation, both baselines, feature families, two alternative weightings and leave-one-feature-out. It also varies the reference target: content-matched classes, audited crops and the development panel. The finite-sample H correction, a genuine-painting calibration of D, scene-deletion and joint scene/reference resampling are included. The SD-Turbo cohort is correctly described as a retrospective check rather than a replication.
- **Internal numerical consistency.** I recomputed D = 1 − 2β + Q for every row of Table 3, the shared, exact and faithful fractions from Table 10 and the addendum values, and the recognition deltas in Table 20. I also checked the −2.8 to +6.5 point range of Table 2 (unrounded 77.56 − 71.03 = 6.54) and the "11 of 12" Cézanne statement from Table 19. All agree. The released analysis outputs reproduce the reported embedding readouts.
- **Figure 2** is an honest, pre-selected panel. It makes the quantitative pattern visible: the Cézanne outputs separate, while Monet, Sisley and Pissarro look alike.

## 3. Weaknesses

### W1. The verdict "worse than making no painter distinctions" depends on the representation, and the abstract states it without qualification (abstract p. 1; intro bullet 3, p. 2; Sec. 5.3, p. 9; Discussion, p. 12)

The abstract says "three have larger errors than a generator that makes no painter distinctions". Intro bullet 3 adds that "only FLUX.2 Max is below that level in 94.2%". Both statements hold only in the 31 features. The same readout D, computed in the embeddings the paper also reports, gives a different picture. Table 4 already shows it, but the text never draws the consequence:

- **GPT Image 1** is among the worst in the 31 features: D = 1.572, and D < 1 in only 0.7% of joint resamples. Yet it has the *lowest* CLIP error (0.847, best in 99.3% of scene resamples, Table 5) and a CSD error of 0.735.
- In **CSD**, all six point estimates are below 1 (0.714–0.999).

I recomputed scene-bootstrap intervals from the released embeddings (`reports/painter_learned_audit_v1/embeddings_*.npz`), using the paper's definitions, 5,000 resamples of the 14 scenes and scene-wise D against the primary prototypes. The authors should verify these numbers:

- **CLIP:** GPT Image 1 0.847 [0.759, 0.934], D < 1 in 100% of resamples; Sunburst 1.136 [1.058, 1.215], D < 1 in 0%. GPT Image 2, Flare, Nano Banana 2 and FLUX.2 Max all have intervals straddling 1.
- **CSD:** GPT Image 1 0.735 [0.646, 0.828], GPT Image 2 0.741 [0.668, 0.823], Flare 0.819 [0.778, 0.861] and FLUX.2 Max 0.714 [0.623, 0.802] are below 1 in 100% of resamples. Sunburst is below 1 in about 91% and Nano Banana 2 in about 51%.

So two of the three configurations labelled "worse than no distinctions" (GPT Image 1 and Flare) are clearly *better* than no distinctions in CSD, and GPT Image 1 is also better in CLIP. FLUX.2 Max's advantage is likewise specific to the features: in CLIP it sits at about 1.06, straddling 1. As written, the headline specificity result reads as a property of the generators. The evidence supports it only as a property of the generators *measured in the 31 features*.

### W2. The prespecified representation is the weakest at telling the painters apart, and the paper does not confront this for the aggregate results (Sec. 3 p. 4; Sec. 5.3 p. 9; App. D p. 20)

Nearest-mean classification of the genuine development works reaches 49.8% macro accuracy in the 31 features (Monet 39.6%, Sisley 30.6%), against 79.8% in CLIP and 79.6% in CSD. The paper uses this fact to discount the weak Monet–Sisley response in the features, but not to qualify the aggregate D verdicts or the FLUX.2 Max ranking, which rest on the same representation.

I understand the reason for the ordering: the features were prespecified and the embeddings were added retrospectively, and there are real counter-concerns. CSD was trained with these painters among its style tags, the embeddings may respond to content, and the two encoders are related. The paper needs to put this tension on the table rather than leave the reader to reconstruct it from Tables 4, 5 and 15. The recommendation to "read specificity from the between-name differences" (Discussion) is also incomplete without a condition: first check that the representation separates the painters' genuine works, and calibrate D against genuine paintings *in that representation*.

### W3. The genuine-painting calibration of D is reported only as a mean, and only in the 31 features (Sec. 5.3 p. 9; App. D p. 20)

The main text compares FLUX.2 Max's 0.801 with the content-sampled genuine means (0.753 and 0.731) and says "the other configurations are not" close. The released control draws (`reports/painter_specificity_review_v1/analysis.json`) show how wide that distribution is:

| Genuine-painting control (31 features) | 95% range | Draws with D > 1 |
|---|---|---|
| Content-sampled, content-matched target | [−0.25, 1.95] | 29% |
| Content-sampled, pooled target | [−0.55, 2.40] | 35% |
| Pooled sampling (the only range the paper gives) | [−0.76, 1.38] | 9% |

These ranges mostly reflect work-to-work variability and noise in estimating the target, so they are not directly comparable with the scene intervals. The more important point is the expected level. In the 31 features, a genuine painter sampled like the design is expected at about 0.75, only about 0.25 below the no-distinction value of 1. The metric therefore has little room to separate "specific" from "non-specific" in this representation. That should be said.

No genuine calibration is given for CLIP or CSD. A quick split-half control I ran on the released embeddings, with pooled sampling like the paper's first control, gives means of about 0.14 (CLIP) and 0.12 (CSD). That is far below every generated value, but the content-sampled analogue is needed before any "close to genuine" statement can be made across representations.

### W4. How the paper positions "proximity" against common practice (abstract first sentence; Intro p. 1)

The abstract says artist-style prompting is "commonly assessed by how much closer images generated with an artist's name move to that artist's works", i.e. by a gain. The work cited as the canonical example, CSD's General Style Similarity (Somepalli et al., 2024), is a *raw* similarity to the prototype with no no-name baseline; I checked the paper. Su et al. (2025) compare with the no-name image from the same seed. The paper's gain relative to a generic painting clause is a cleaner variant introduced here, not the common practice. The conclusion likely transfers a fortiori, because raw proximity adds the generic outputs' own similarity, which is also name-independent. The text should say so explicitly and, ideally, report the raw-proximity analogue of Table 2.

### W5. Wording of the first finding (Sec. 5.1 heading, p. 7; intro bullet 1)

"Most of what the names add is shared, as it would be for a faithful imitator" can be read as "the fraction matches a faithful imitator". It does not: the observed fraction is below the faithful one in 100% of scene resamples for five of six configurations (Table 1). What the evidence supports is "a majority is shared, and a majority would also be shared for a faithful imitator".

Relatedly, the faithful benchmark's shared fraction is driven by ‖t‖. Its size (N*/H = 5.6–19.6) is dominated by the gap between generated images and photographed paintings and by content differences. The observed-versus-exact comparison reduces to B versus H. The first finding would be easier to read if N/H and B/H (Table 10) were shown in the main text next to the fractions.

### W6. "Mostly" is borderline for one configuration (Sec. 5.2, Table 2, p. 8)

For GPT Image 2 in CSD, the shared share is 54.2% with scene interval [47.4, 59.3], which includes values below 50%. The abstract's "proximity gain therefore mostly measures movement that all the names share" should carry that exception or be stated per representation.

### W7. The feature-family finding is weak and should not be headlined (intro bullet 5; Sec. 5.5, Table 6, p. 11)

"Texture is the least shared family on average" rests on means of 68.2% [61.9, 70.7] for texture and 71.5% [57.3, 80.1] for spatial features. The intervals overlap heavily, and the family ordering differs across configurations: texture is least shared for only three of six. Report a paired interval for the texture-minus-spatial difference, or demote this from the list of contributions.

### W8. Readout differences are partly representation differences (intro bullet 4; Sec. 5.4, p. 10)

The intro bullet contrasts CLIP proximity, CLIP recognition and 31-feature D, which mixes readouts with representations. Table 5 contains a clean within-representation demonstration. In CLIP, proximity favours Nano Banana 2 (85.8% of resamples), recognition favours GPT Image 2 (98.7%) and D favours GPT Image 1 (99.3%). Leading with that contrast would make the "different readouts" claim stronger and would not conflate it with W1.

### W9. Minor internal inconsistency (App. D, "Scene aggregation and rescaling", p. 21, versus Sec. 5.3, p. 9)

The appendix says GPT Image 2's differences are "about twice the reference size". Section 5.3 correctly says 1.49 times in norm (Q = 2.223 is the *squared* size). The optimal shrink factor of about 0.45 = β/Q is consistent with the squared reading. Say "about twice in squared size".

### W10. Reproducibility of the pixel-level claims (Reproducibility statement; Limitations)

The 1,008 generated images are not released, so the 31 features and the embeddings cannot be re-extracted independently. The replay only checks that the numbers follow from the retained vectors. For a study of closed services, whose outputs cannot be regenerated, releasing the images (they are small: 1,008 × 1024²) is the single most valuable reproducibility step.

### W11. Clarity and density

- The abstract packs eight numeric ranges into one paragraph and is hard to parse on a first read.
- "Corrected cosine" and the Table 1 columns "covered" (λ) and "along generic" (which equals cos²(c, g)) are defined only implicitly in the main text.
- The paper introduces about 14 symbols (N, B, H, N*, λ, β, Q, D, D_agg, V_scene, D_held, …). A short "what each number answers" guide in Sec. 4, like Table 9 but in the main text, would help readers from outside RSA.

None of this rises to a clarity failure. The writing is precise and careful.

### W12. Status of the headline claims (Sec. 4.5)

The title claim and findings 1, 2, 4 and 5 all come from retrospective analyses. The generic-baseline split was introduced after the artist-free split, which was the prespecified diagnostic, was known. The paper discloses this fully, and the claims are descriptive or algebraic, so I do not ask for changes beyond keeping the current disclosure prominent. I note it because the prespecified tests (β > 0 and the pairwise D differences) support only a small part of the narrative.

## 4. Requested changes

**Critical**

1. **Qualify the D-based specificity verdicts by representation and report them across representations.**
   - Everywhere the paper says configurations are worse than, or better than, making no painter distinctions (abstract, intro bullet 3, Sec. 5.3, Discussion), state that this holds in the 31 features.
   - Add D, Q and β for CLIP and CSD, with scene (and reference) intervals and the share of resamples with D < 1, next to Table 3. All of this can be computed from the retained embeddings.
   - State explicitly that GPT Image 1 reverses from worst to best between the features and CLIP, and that all six CSD estimates are below 1.
   - This is an editing change plus computation on retained data; no new images are needed.
2. **Confront the validity of the representations for painter specificity.**
   - Introduce the genuine-work separability numbers (49.8% versus about 80%) where the representations are defined (Sec. 3 / Sec. 4.3), not only in Sec. 5.3.
   - Compute the genuine-painting D calibration (pooled and content-sampled) in CLIP and CSD, and report dispersion (for example, P(D > 1)) as well as means.
   - Explain what the paper concludes, and does not conclude, about the specificity of each configuration given that the prespecified representation is the least discriminative.
   - Extend recommendation 1 in the Discussion: check that the representation separates the painters' genuine works, and calibrate D in that representation.

**Minor**

3. Reword the Sec. 5.1 heading and intro bullet 1 so they do not suggest the observed fraction matches the faithful imitator. Show N/H and B/H in the main text.
4. Clarify that common practice uses raw prototype similarity (for example, CSD's GSS), not gain relative to a generic clause. Explain why the conclusion transfers, and ideally give the raw-proximity analogue of Table 2.
5. Qualify "mostly" for GPT Image 2 in CSD (54.2% [47.4, 59.3]).
6. Give a paired interval for the texture-versus-spatial difference in the shared fraction, or remove the family ordering from the contributions list.
7. Lead the "different readouts" finding with the within-CLIP contrast (proximity: Nano Banana 2; recognition: GPT Image 2; D: GPT Image 1).
8. Fix "about twice the reference size" in App. D (twice in squared size; 1.49 times in norm).
9. Define "corrected cosine", λ and "along generic" (cos²) in the main text or in the Table 1 caption.
10. Simplify the abstract: fewer ranges, and keep the representation qualifiers.
11. Release the generated images, or commit to releasing them on acceptance, so the features can be re-extracted from pixels.
12. In Limitations, state that "specificity" is operationalised as agreement with differences between reference means in a chosen representation, and that no perceptual validation exists. The claims as worded do not require a human study, but readers will read "specificity" perceptually.

## 5. TMLR criteria

**Criterion 1 (claims and evidence): partially.**

Supported as worded:
- The decomposition and its benchmarks (Tables 1–2, 10).
- The claim that a large shared fraction alone does not indicate weak specificity.
- The claim that the shared term dominates prototype proximity gain in both embeddings. There is one borderline case (GPT Image 2 in CSD), and the claim follows largely from Eq. 4 given H.
- That every configuration has β > 0 (prespecified, in all three representations).
- That readouts rank configurations differently, within CLIP alone and stably under scene resampling.

The ranking claims are appropriately hedged, and the prespecified-versus-retrospective status is accurate.

Not supported as worded: the abstract-level claim that "three have larger errors than a generator that makes no painter distinctions" holds only in the 31 features. Those features are the least able to separate the painters' genuine works, and the verdict reverses for GPT Image 1 (and for Flare in CSD) in the embeddings the paper itself reports. The "texture is the least shared family" bullet is weakly supported.

Both gaps close by narrowing the wording and reporting cross-representation D with intervals and genuine-painting calibrations. These can be computed from the retained data.

**Criterion 2 (audience and clarity): yes.**

Researchers evaluating text-to-image style control, style mimicry, attribution and copyright auditing, and style-similarity metrics such as CSD will find the decomposition and Eq. 4 directly useful. The recommendations are actionable, and the paper connects to the recent work that questions raw CSD scores (Frochte, 2026). The paper is dense in notation and numbers but precise, well organised and honest about scope. The fixes in W11 are editorial.

## 6. Desk-rejection risk: low

The paper is in scope (evaluation methodology for generative models), follows the TMLR format, is anonymised, and includes Broader Impact and Reproducibility statements. It does not read as low-care machine-generated text. The prose is specific, the numbers are internally consistent, and AI assistance is disclosed. The only risk is how dense it is to read.

## 7. Recommendation: minor revision

The core contribution is sound, carefully executed and useful. The main problem is the representation-dependent specificity verdict, which is a framing and reporting problem. It can be fixed with wording changes and analyses on data the authors already hold. No new generation or human study is required for the claims once they are narrowed.

## 8. Confidence: 4 / 5

I read the full PDF, checked the key identities and several tables numerically, read the protocols and post-result plans, and recomputed embedding-space D intervals and a genuine control from the released embeddings. I did not re-extract features from pixels, which is impossible because the images are not released, and I did not audit the reference collection.

## 9. Literature checked

- Somepalli et al. 2024 (CSD, ECCV): GSS is raw prototype similarity with no no-name baseline. The paper's description of CSD prototype scoring is accurate; the "commonly assessed by gain" framing is not quite (W4).
- Frochte 2026 (arXiv 2605.09030v2): raw CSD cosine gives negative discrimination gaps for 23 of 91 artists, and Section 8 evaluates prompted FLUX generations. Described accurately.
- Su et al. 2025 (arXiv 2507.18633): 110 artists, same content prompt with substituted names, and CLIP similarity to the no-name image from the same seed. Described accurately.
- Moayeri et al. 2025 (ICLR, ArtSavant): 20% of 372 artists at risk. Accurate.
- Casper et al. 2023 (arXiv 2307.04028): 70 artists, CLIP zero-shot, 81% average accuracy. Accurate.
- Xing et al. 2026 (arXiv 2608.06751, Atelier/ArtIntentBench): canonical shortcuts such as generic palettes and recurring motifs. Accurate.
- Asperti et al. 2025 (BDCC 9(9):231, AI-Pastiche): accurate.
- Fu et al. 2025 (arXiv 2508.01408): VLM artist attribution and AI-versus-human detection. Accurate.
- Deliège et al. 2025 (J. Imaging): existence confirmed.
- Kim et al. 2026 (PNAS): the arXiv version is titled "Context-aware Multimodal AI *Reveals* Hidden Pathways…". I could not access the PNAS page to confirm the volume and title; not flagged as an error.
- Hönig et al. 2025 (ICLR), Kumari et al. 2023, Gandikota et al. 2023, Zhang et al. 2024 (UnlearnCanvas) and Verma et al. 2025 (TMLR): consistent with the descriptions.
- GPT Image 2.5 Flare and Sunburst: confirmed as OpenAI models released on about 8–9 September 2026 and listed on OpenRouter, so "four of them OpenAI GPT Image variants" is accurate.
- Possibly worth citing: HEIM (Lee et al., NeurIPS 2023 D&B), which evaluates art styles with human raters, as context for the missing perceptual validation. This is optional.

## 10. Factual errors

- App. D, p. 21: "GPT Image 2's differences are about twice the reference size". They are about twice in *squared* size and 1.49 times in norm, as Sec. 5.3 correctly states.
