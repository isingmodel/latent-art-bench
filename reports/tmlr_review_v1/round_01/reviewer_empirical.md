# TMLR review: "What Does an Artist Name Add? Separating Shared and Painter-Specific Responses in Text-to-Image Generation"

Reviewer role: empirical (evaluation of text-to-image generative models)
PDF read: `manuscript.pdf`, SHA-256 `33c87a6f609b2c791b0ba6c5101d4af64fc9b05e155b9bb448c65a5a6a90b5c8` (all 20 pages: main text, references, Appendices A–H)

## 1. Summary of the submission

The paper asks how much of the effect of an artist name in a text-to-image prompt is specific to that artist. Each of 14 fixed outdoor scene descriptions is rendered with six style clauses: none, "Render as an oil painting.", and "... in the style of" Monet, Sisley, Pissarro or Cézanne. The renders come from six commercial configurations (four OpenAI GPT Image variants, Nano Banana 2 and FLUX.2 Max), with two separate requests per cell, for 1,008 images. The response to a name is split into a component shared by all four names (the change in their mean) and a between-name component (departures from that mean). Squared sizes are estimated with cross-repeat inner products, which remove the positive bias that sampling noise adds to squared norms. The between-name differences are compared with the differences among the four painters' reference means (649 Wikimedia reproductions) using an aligned amplitude β and an error D. The same split is applied to CLIP and CSD embeddings, where an exact identity (Eq. 4) divides the "proximity gain" to the prompted painter's prototype into a shared term and a painter-specific term. A retrospective SD-Turbo collection (2,000 images) is used as a further check.

Main reported findings:
- Beyond the generic oil-painting clause, 66.7–88.4% of the squared change a name adds is shared (31 features). The shared change N is 1.4–5.3 H, where H is the spread of the reference painter means; the between-name change B is 0.6–2.1 H.
- All six β intervals lie above zero. No configuration's D is shown to be below 1, the value for "no painter distinctions".
- The shared term supplies 73–84% (CLIP) and 54–80% (CSD) of the prototype-similarity gain.
- Proximity, agreement (D) and nearest-prototype recognition rank the configurations differently.
- In SD-Turbo the shared share is 64.2% overall and 36.6% for texture features.

The paper recommends that artist-style evaluations add a generic-style control and report the decomposition alongside proximity.

Contributions: (i) a controlled design with a generic-style control; (ii) repeat-corrected estimators for the shared and between-name components and for agreement with reference differences; (iii) an exact decomposition of embedding proximity gain; (iv) an empirical demonstration across six current commercial configurations and two encoders.

## 2. Strengths

1. **Clean intervention design.** Only the style clause varies; scene text, suffix and request settings are fixed. The request order was randomized and hashed before collection. Adding a generic "oil painting" arm is a simple, useful control that most artist-style evaluations lack.
2. **Correct and well-motivated estimators.** The cross-repeat (cross-validated distance) estimators are standard in RSA and are applied correctly. I checked the identities C = G + N + I, D = 1 − 2β + Q and D = D_agg + V_scene against the definitions. Keeping negative estimates is the right choice.
3. **Candid reporting of negative and weak results.** Examples: FLUX's D interval includes 1 (p. 8); only 2 of 15 prespecified pairwise comparisons are resolved (Table 8); a correlation of ρ ≈ 0.25 between repeats would reverse an ordering (App. A); Cézanne carries much of the aggregate β (Table 10); the SD-Turbo check is labelled retrospective and non-independent. The paper also separates prespecified from post hoc analyses (Sec. 4.4).
4. **Reproducibility.** I independently reproduced several values from `data/manifests/painter_specificity_v2/psv2-20260911/measurements.jsonl` and `reference_windows.jsonl`, using only the development-panel scale: H = 5.915, and every N/H, B/H and shared share in Table 1. I also confirmed that all 1,008 images have distinct hashes, so no repeat is a pixel-identical cached return. Table 3, Table 4 and the development-panel accuracies match `reports/painter_learned_audit_v1/analysis.json`.
5. **Useful practical points.** Eq. 4 is simple and easy for practitioners to adopt. The translation experiment (Sec. 5.4, App. F) cleanly shows that recognition responds to a shared offset that leaves every painter contrast unchanged.

## 3. Weaknesses (with locations)

### W1. The headline share and "N is 1.4–5.3 × H" have no benchmark, and the supplied data suggest a faithful imitator would show an even larger share (Abstract; Intro bullet 1, p. 2; Sec. 5.1, pp. 6–7; Discussion, p. 10)

The abstract and Section 5.1 say the shared change "is 1.4–5.3 times as large as the entire spread of the four painters' reference means". Readers will take this to mean the shared movement is excessive. But H measures how far the painters are from each other. It is the natural yardstick for B, not for N. The relevant yardstick for N is how far the generic output is from the painters' common appearance.

The supplied data allow this comparison, although the Discussion says "Our data cannot say how large that appropriate part is". I used the retained 31-feature vectors and the paper's cross-repeat convention, with μ̄ as the reference centroid and z̄_g as the scene-averaged generic output. The quantity 4⟨μ̄ − z̄_g,1, μ̄ − z̄_g,2⟩/H is the shared change needed to put the named-output centroid on the reference centroid. Its values are:
- GPT Image 1: 19.6
- GPT Image 2: 8.3
- Flare: 5.6
- Sunburst: 6.6
- Nano Banana 2: 12.3
- FLUX.2 Max: 9.5

In every configuration this exceeds the observed N (5.3, 5.0, 5.0, 4.0, 1.4, 5.3). The observed shared change points toward μ̄: the cosine between n and μ̄ − z̄_g is 0.57–0.86. It closes part of the gap; for example, FLUX goes from 9.5 to 2.6 and GPT Image 1 from 19.6 to 7.6, in the same units.

Now consider a generator whose named outputs reproduced the four reference painter means exactly (B = H), measured against the same generic baselines. Its shared share would be 85–95%, higher than the observed 66.7–88.4%. Even a generator that kept its observed N but reproduced the painter differences exactly would show 58–84%.

Part of the μ̄ − z̄_g distance is a domain gap between generated images and photographed paintings, so these benchmarks are approximate. Still, they show that the size of the shared share mainly reflects (a) how close the four painters are to each other and (b) how far generic outputs sit from them. It is not by itself evidence that generators under-produce painter-specific change. The paper does say "a large shared component is therefore not by itself a failure" (p. 2). However, the headline numbers carry no reference point, and the recommendation to "report this decomposition next to any proximity score" leaves readers without a way to interpret the result.

**What would close the gap:** add benchmark shares computed from existing data, for example (i) the reference-centroid oracle above, and (ii) a held-out "ideal output" built from the 221-work development panel. Report the direction and distance reduction of the shared change toward μ̄ in the 31 features, not only in embeddings. Then reframe the abstract, bullet 1 and the Discussion.

### W2. What the shared component is, and how far the finding generalizes (Title; Abstract; Intro bullets; Sec. 5.3, p. 8; Discussion, p. 10; Limitations, p. 10)

The design cannot tell apart three sources of the shared component:
- a family resemblance specific to these four Impressionist-adjacent painters;
- a generic "any artist name" effect, such as more stylization or more painterliness;
- an intensification of the painting instruction.

The Discussion's statement that "the shared change moves images toward the four painters' common appearance" rests on a positive projection onto μ̄ in raw cosine geometry. In anisotropic embeddings such as CLIP's, much of μ̄ is a global "photographed painting" direction, so almost any painterly change would project positively on it.

The data show a painterliness component in some configurations. I computed the fraction of N that lies along the generic-instruction shift g (cross-repeat): about 0 for GPT Image 1/2, 0.2 for Sunburst and Nano Banana 2, and 0.4 for FLUX.2 Max. This fits the large positive cross terms I in Table 1. The paper reports I but does not interpret it.

The Limitations section acknowledges that out-group painters and a family phrase were not run. Even so, the title and abstract state "What does an artist name add?" and "Most of what a painter name adds is shared" without saying that the four painters form one related group.

**What would close the gap:** at minimum, restrict the headline claims to four related painters and remove or qualify "toward the four painters' common appearance". Cheaper supporting evidence needs no new generation: project the shared change onto μ̄ − μ_out, where μ_out is a prototype built from reference images of non-Impressionist painters. Stronger evidence would come from the family-phrase and distant-painter arms the authors describe.

### W3. The claim that readouts "rank the configurations differently" has no uncertainty (Abstract; Intro bullet 3, p. 2; Sec. 5.4, pp. 8–9; Table 4)

This is one of the four headline findings, but it rests only on point estimates:
- **Recognition.** Each value uses 112 images, so the binomial 95% half-width is about ±8–9 points.
- **CLIP proximity.** The three highest gains are 0.112, 0.101 and 0.100.
- **CSD proximity.** Four configurations fall within 0.210–0.217. GPT Image 1 (0.21672) and FLUX.2 Max (0.21666) are tied at the reported precision, yet only GPT Image 1 is bold.
- **31-feature D.** FLUX's "lowest error" is resolved against only 2 of 5 configurations, and its interval includes the no-distinction value.

So the example "the configuration with the lowest error ... has the least recognizable names" pairs a D ordering that is mostly unresolved with a recognition difference that is partly unresolved (FLUX vs Nano Banana 2: 41.1 vs 51.8).

The mechanism the paper gives is algebraically sound: proximity is dominated by a label-free term, recognition rewards separability, and D penalizes exaggeration. The empirical claim that the rankings differ is a separate claim, and it has not been established.

**What would close the gap:** a joint scene-cluster bootstrap (or scene-deletion ranges) for proximity gain, recognition and D, reporting rank correlations or the probability of each named reversal. Otherwise, reword the claim as "point estimates order the configurations differently, and the decomposition shows why this can happen".

### W4. The prespecified reference-panel uncertainty is not reported, and H is not bias-corrected (Sec. 4.4, p. 6; Table 2; Sec. 5.6)

The protocol (`studies/painter_specificity_v2/PROTOCOL.md`) lists "reference resampling", and the retained analysis contains the results (`data/manifests/.../analysis.json`, `reference_resampling`). For β, reference-panel uncertainty is often larger than scene uncertainty:
- Flare: reference-resampling interval [0.568, 0.878], against a nominal scene interval of [0.719, 0.824].
- FLUX.2 Max D: reference-resampling interval [0.693, 0.945].

The paper says only that intervals "condition on the reference panels". The conclusions survive (the lowest reference-resampling bound on β is 0.34), but a prespecified analysis should be reported.

In addition, the paper removes noise bias from generated squared norms but not from H. Using within-painter variances, I estimate the finite-sample upward bias of H at about 0.40 of 5.92, or roughly 7%. Uncorrected, this bias pushes β down and pushes up the D value of a perfect imitator. The effect is small, but it runs against the paper's emphasis on unbiased squared magnitudes.

### W5. Feature-family and weighting sensitivity of the headline share is not reported for the main collection (Table 1; Sec. 5.5 heading; Intro bullet 4)

Table 11 varies the weighting for D only. Table 5 breaks SD-Turbo down by feature family, but the main collection gets no such breakdown. From the retained vectors, the main-collection shares by family (named-minus-generic) are:
- **Texture:** 48.6% (GPT Image 1), 73.8%, 60.1%, 70.3%, 79.8% and 76.5%.
- **Spatial:** as high as 95.1% for FLUX.
- **Color:** 56.8–83.8%.

FLUX's maximal share comes mostly from two spatial-orientation features: quadrant JSD and orientation entropy supply 27% and 24% of its N. The overall share is reassuringly stable, with a leave-one-feature-out range of 64.8–89.6% and 66.1–89.8% under equal-family weighting. These results should be in the paper, both to support the headline and to put the SD-Turbo texture exception (bullet 4, Sec. 5.5) in context. In the main collection texture is mostly majority-shared, the exception being GPT Image 1.

### W6. Reference collection: selection criteria, subject mix and data quality (Sec. 3, p. 3; Sec. 5.6, p. 10; App. D)

Section 3 gives counts and sources but no inclusion criteria: which subjects, which periods, and how works were chosen from Commons. The reference-quality output suggests all 649 works are outdoor scenes. It also shows a strongly unequal subject mix: 191 of 297 Monet works are water scenes, against 31 of 105 for Cézanne. So the reference contrasts r_a partly encode subject choice. The content-matched target (Table 11) addresses this in part.

Two further issues are not mentioned:
- The same audit found 230 confident disagreements between title-derived and visual content classes, and the content-matched target uses the title-derived classes.
- The crops applied to 131 images were made by "AI assistants ... without human verification". Checking even a sample by hand would cost little.

### W7. Status of the evidence is unclear in the abstract (Abstract; Sec. 4.4)

The headline numbers are all post hoc descriptive analyses, defined after other results on the same images were known: the generic-baseline share, the embedding shares and recognition. The prespecified endpoints (β and pairwise D) play a secondary role in the narrative. Section 4.4 is transparent about this, but the abstract gives no hint of it.

### W8. Diversity of configurations and repeat independence (Sec. 3; App. A; Sec. 7)

- Four of the six configurations are OpenAI GPT Image variants, which limits how far "every configuration" generalizes.
- Independence of repeats cannot be tested. The simulation in App. C shows coverage collapses to 0.04% under shared state. Reporting per-configuration repeat disagreement (the noise-to-signal ratio) and discussing server-side prompt rewriting would help readers judge the risk.
- The generated images are not released, so features cannot be re-extracted.

### W9. Related-work accuracy and coverage (Sec. 2, pp. 2–3)

Some descriptions are inaccurate (listed under factual errors below).

The positioning also omits that Su et al. (2025) already compare each image with "the image generated with the same seed and prompt, except that the artist's name is removed" (their Sec. 3.5), and include prompts without artist names in a detection task. The genuinely new element here is the *generic-style* control and the shared/between-name split, and the paper should say so explicitly.

Missing directly relevant work:
- Casper et al. (2023), who measure CLIP zero-shot recognition of 70 artists in Stable Diffusion imitations; this is the recognition readout the paper critiques.
- Kumari et al. (ICCV 2023, Ablating Concepts), who map artist styles to a generic "painting" anchor; this is conceptually close to the generic control.
- A source for the opening claim that artist names are "among the most widely used style controls", for example DiffusionDB (Wang et al., 2023).

### W10. Clarity (throughout)

The writing is careful but dense. About a dozen estimands are used: C, G, N, I, B, H, β, Q, D, D_agg, V_scene, D_held, plus the embedding counterparts. A short table of estimands with their "ideal" values would help. Other clarity points:
- "Uncalibrated error" in Sec. 5.6 is not defined in the main text.
- "Monet–Sisley β" is defined only in a table caption.
- The bolding in Table 4 hides ties.

## 4. Requested changes

**Critical**
1. **Benchmark the shared share and N/H.** Report reference-based benchmarks computed from existing data: the share a faithful imitator would show against the same generic baselines (from the reference means and/or the held-out development panel), and the direction and distance reduction of the shared change toward the reference centroid in the 31 features. Reframe the abstract, Intro bullet 1, Sec. 5.1 and the Discussion so readers do not take "N ≫ H" as a sign of excess shared response. Correct the Discussion statement that the data "cannot say" anything about the appropriate shared part.
2. **Support or narrow the ranking claim.** Either provide uncertainty for the claim that proximity, recognition and agreement rank configurations differently (a joint scene-cluster bootstrap or deletion ranges for all three readouts, including rank correlations or the probability of each named reversal), or restate it as a point-estimate observation plus the algebraic explanation. Apply this to the Abstract, Intro bullet 3, Sec. 5.4 and Table 4 (include recognition confidence intervals and fix the tie in bolding).
3. **Scope the claims and address the main alternative explanation.** State in the title/abstract/bullets that the painters form one related group and that the results concern these four names. Qualify "moves images toward the four painters' common appearance". Either add an out-group analysis (projection of the shared change onto μ̄ − μ_out, where μ_out comes from non-Impressionist reference images; no generation needed) or state explicitly that a generic artist-name or painterliness effect cannot be excluded. Also interpret the cross term I, which for FLUX shows that the name shift partly continues the generic painting shift.

**Minor**
1. Report the prespecified reference-resampling intervals next to the scene intervals (Table 2, Sec. 4.4). Note or correct the finite-sample bias of H.
2. Add per-family shares and weighting sensitivity (equal-family, covariance, leave-one-feature-out) for the main collection. Revise bullet 4 and the Sec. 5.5 heading in light of the main-collection texture results. Report which features dominate N for FLUX.
3. State the reference-collection inclusion criteria and the subject mix per painter. Mention the title/visual class disagreements that affect the content-matched target.
4. Have a human verify at least a sample of the AI-proposed crops, and report agreement.
5. Correct the related-work descriptions (see factual errors). Acknowledge Su et al.'s artist-removed control. Cite Casper et al. 2023, Kumari et al. 2023 and a source for the prevalence of artist-name prompting.
6. Give the exact prompt strings. The Cézanne clause used "Paul Cezanne" without the diacritic (`requests.jsonl`), whereas the text implies "Paul Cézanne".
7. Say in the abstract that the headline decompositions are post hoc descriptive analyses.
8. Define "uncalibrated/calibrated" error in the main text. Add a compact table of estimands with their ideal and null values.
9. Say explicitly that four of the six configurations are OpenAI variants. Report per-configuration repeat disagreement and whether the services rewrite prompts.
10. If licensing and size allow, release the generated images (or reduced-resolution copies) after review so that features can be re-extracted.
11. State whether the 16 SD-Turbo scenes overlap in content with the 14 main-collection scenes.

## 5. TMLR criteria

**Criterion 1: Are the claims supported by accurate and convincing evidence? — partially.**
The descriptive numbers are accurate; I reproduced Table 1 and H exactly from the retained vectors. The algebraic claims (Eqs. 1–7) are correct, and the prespecified β and D results are reported with appropriate caution. The gaps between claims and evidence are:
- The headline shared share and N/H are presented without a benchmark. My computation suggests a faithful imitator would show a higher share, so their evaluative meaning is unsupported (W1).
- The claim that readouts rank configurations differently rests on unresolved point estimates (W3).
- The claims are worded generally, but the evidence covers four related painters and cannot exclude a generic artist-name or painterliness explanation (W2).

Adding benchmarks, uncertainty and narrower wording, mostly from existing data, would close these gaps.

**Criterion 2: Would some of TMLR's audience be interested, and is the paper clear? — yes.**
Researchers who evaluate style mimicry, style erasure and artist-recognition benchmarks will find the generic control and the decomposition of proximity useful. The paper is well organized and honest about its limits. The notation is dense, and a few definitions sit only in captions or appendices, but these are editing issues.

## 6. Desk-rejection risk: low

The topic is in scope, the TMLR format and anonymization are correct, and broader-impact and reproducibility statements are included. The paper is carefully argued, with internally consistent numbers that are checked against source analyses, so it does not read as low-care machine generation. Two things could draw an action editor's attention without justifying desk rejection:
- the disclosure that AI assistants curated the reference crops without human verification;
- the density of the prose.

## 7. Recommendation: major revision

The design and estimators are sound, and the core observation (proximity gain mixes a label-free shared term with painter-specific differences) is useful. However, the headline quantitative framing needs a benchmark, which on my reading of the supplied data may reverse its evaluative implication. The cross-readout ranking claim also needs uncertainty or narrowing, and the scope must be restricted to what four related painters can support. Most of these revisions use existing data. None requires new image generation unless the authors choose to add out-group arms.

## 8. Confidence: 4 / 5

I read the whole PDF and checked the main estimators. I reproduced Table 1 and the benchmark computations above from the supplementary vectors and checked the embedding and recognition values. Confidence is not 5 because I could not inspect the images themselves or re-extract features, and the benchmark numbers in W1 are my own computations, not the authors'.

## 9. Literature checked

- Su, Wang, Hertzmann, Shechtman, Zhu, Zhang (2025), "Identifying prompted artist names from generated images", arXiv 2507.18633. 110 artists and content-controlled name substitution confirmed; also includes an artist-removed, same-seed comparison (Sec. 3.5) that the manuscript does not mention.
- Frochte (2026), "When style similarity scores fail: Diagnosing raw CSD cosine in artist-style evaluation", arXiv 2605.09030 (v1 May 2026, v2 July 2026). 91 artists; CSD+ with CSLS readout; top-1/top-5 recognition of prompted generations confirmed. Raw-cosine failures: 23/91 negative gaps as point estimates, but only 2/91 robust under bootstrap.
- Moayeri et al. (ICLR 2025), "Rethinking artistic copyright infringements in the era of text-to-image generative models" (ArtSavant). 372 artists; about 20% at risk. The at-risk criterion also requires generated images to be recognized, not only the artist's own works.
- Somepalli et al. (ECCV 2024), "Investigating style similarity in diffusion models" (CSD). Averaged-embedding artist prototypes and content-constrained prompts confirmed.
- Fu et al. (2025), arXiv 2508.01408v1. Studies VLM attribution and AI-image detection using WikiArt plus a generated set. I found no dataset named "AI-WikiArt" in it; that name appears in unrelated sources.
- Asperti et al. (2025), "A critical assessment of modern generative models' ability to replicate artistic styles" (AI-Pastiche), BDCC 9(9):231. Confirmed.
- Deliège et al. (2025), J. Imaging. Existence confirmed.
- Verma et al. (TMLR 2025), "How many images does it take? Estimating imitation thresholds in text-to-image models". Venue and content confirmed.
- Kim, Lee, You, Yun (PNAS 2026). arXiv 2503.13531 exists under a slightly different title ("... Reveals Hidden Pathways ..."), and the published title matches a 2026 seminar listing. Plausible.
- Casper et al. (2023), "Measuring the success of diffusion models at imitating human artists", arXiv 2307.04028. CLIP zero-shot recognition of 70 artists; relevant and not cited.
- Also considered: Kumari et al. (ICCV 2023), "Ablating concepts in text-to-image diffusion models" (generic "painting" anchor for artist styles; relevant, not cited); Wang et al. (ACL 2023), DiffusionDB (prevalence of artist names in prompts; suggested citation); Diedrichsen & Kriegeskorte (2017) for cross-validated distances (correctly cited); Glaze, Hönig et al. (ICLR 2025, which includes a user study), ESD and UnlearnCanvas (descriptions consistent with my knowledge).

## 10. Factual errors or inaccuracies found

1. p. 3: "AI-WikiArt (Fu et al., 2025)". Fu et al. (arXiv 2508.01408v1) does not appear to name its data "AI-WikiArt"; the label seems misattributed.
2. p. 2: Moayeri et al. are described as deciding at-risk status "by testing whether the artist's own works are recognizable". Their roughly 20% figure refers to artists whose distinctive style is also recognized in *generated* images.
3. Sec. 3 / Intro: the named clause is described as using each painter's full name, "Paul Cézanne". The actual prompts used "Paul Cezanne" without the diacritic (`requests.jsonl`).
4. Table 4: "Bold marks the best value in each column". In the CSD proximity column, GPT Image 1 (0.21672) and FLUX.2 Max (0.21666) are equal at the reported precision, but only one is bold.
5. p. 10 (Discussion): "Our data cannot say how large that appropriate part is". The reference centroid supplied with the paper does permit a partial benchmark (W1), so this statement is too strong.
