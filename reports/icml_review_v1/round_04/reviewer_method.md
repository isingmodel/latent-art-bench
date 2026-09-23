# Independent scientific review: methods and statistical soundness

**This is an AI scientific review simulation, not an official conference review or decision.**

**Overall: 6 — marginally above acceptance.** Soundness: 3/4; presentation: 3/4; contribution: 3/4; confidence: 4/5.

## Summary

The paper audits artist-name responses in a balanced 1,008-image experiment spanning six requested configurations, four painters, 14 scenes, two repeats, and artist-free/generic-painting controls. It distinguishes common naming movement, agreement with centered historical painter contrasts, prompted-name recognition, and selective recognition. Analyses use 31 standardized image measurements and CLIP/CSD embeddings. A separate, previously analyzed 2,000-image SD-Turbo collection extends the common/centered decomposition using 25 matched-seed blocks. The supported contribution is an empirical evaluation case study: proximity gain can be mostly common, representation and aggregation choices alter conclusions, mean translation changes decisions without changing centered contrasts, and low selective error can conceal missing painters. It does not establish perceptual painter fidelity or a general model ranking.

## Strengths

- **S1.** The statistical targets are unusually explicit. The cross-repeat error estimator, common/centered decomposition, scene-wise versus pooled targets, and covariance sensitivity are algebraically coherent. The matched-seed extension correctly keeps correlated arms within blocks and uses distinct blocks for cross-products. Negative estimates and nonpositive-denominator conventions are handled transparently. (Sections 3–4; Appendices B, C.3–C.4, O, Q.2).

- **S2.** The empirical findings are substantive as a diagnostic package. Common naming change is 66.7–88.4% in the main hand-feature metric, while the independent-pixel SD-Turbo collection exposes a texture exception (36.6%). Learned representations reverse the weak hand-feature Monet–Sisley story. The paper keeps adverse translation results, the very small matched-coverage advantage of abstention, and missing painter conditions rather than presenting only favorable aggregates. (Sections 5.1–5.9; Tables 2–5, 14, 16, 21, 39, 43–58).

- **S3.** The paper distinguishes prespecified inference from retrospective diagnostics, separates information budgets for reference, translated, and supervised generated prototypes, and does not attach fictitious independent-fold or conformal guarantees. The finite historical target, shared encoder ancestry, training-overlap uncertainty, and unverified served checkpoint identities are stated clearly. (Sections 4.3, 5.8–5.9, 6.1; Appendices I, L–R).

- **S4.** The retained numerical evidence is strong. I verified all 44 evidence-manifest hashes and independently reconstructed the six primary hand-feature summaries, the learned prototype-gain decompositions, all original-primary transfer accuracies, all eight SD-Turbo family/aggregation summaries, and all 8,064 selective decisions. The calculations agree with the reported results. This supports implementation correctness conditional on retained measurements. (Reproducibility statement; Appendices L.2, N, Q, R).

- **S5.** Related work appropriately acknowledges that prompted-name recognition, raw style-similarity concerns, domain adjustment, and selective classification are established. The authors identify measured evaluation behavior rather than elementary geometry as the contribution. (Section 2; Section 1, contribution statement).

## Weaknesses and questions

### W1: major limitation of inference

**Location:** Section 4.3, lines 174–186; Section 5.2; Appendices N.5 and O.3.

The central main-collection common-change percentages and repeat-corrected errors concern conditional mean responses only under unverified error assumptions. There are two outputs per cell from one collection, and scene identity is confounded with contiguous collection time. The covariance analysis is useful but applies to D under assumed trace correlations; it explicitly cannot correct or bound the headline common fractions. The 0.251 Nano Banana 2–FLUX point-order crossing illustrates sensitivity rather than measuring dependence. The local SD-Turbo seed design does not identify closed-service dependence. The text is candid, so this is not an undisclosed statistical error, but it limits how much stochastic evidence the main headline provides.

**Revision scope:** New independently interleaved collections would be needed to establish repeat/session robustness. Existing-data dependence scenarios could clarify sensitivity but cannot identify actual covariance.

**Question:** Which headline conclusions are intended as descriptions of the retained vectors, and which concern expected fresh-request responses? Can these two evidential levels be separated more prominently in the results summary?

### W2: major limitation of contribution breadth

**Location:** Sections 3.1–3.3, 5.3, 6.1; Appendices L.4 and Q.

The extensive sensitivity inventory still shares four related painters and the same historical comparison target. There is no shared-family clause, and the hand-feature units and learned representations are not externally validated measures of painter fidelity. A common response may be an appropriate response to the painters’ shared tradition. The paper correctly restricts its conclusions, but those restrictions leave a relatively narrow evaluation case study. The separate SD-Turbo collection improves the evidence by changing pixels, wording and generation mechanism, yet does not establish that the common-majority phenomenon or the proposed reporting practice materially changes evaluation across artist groups.

**Revision scope:** Broader claims require new evidence, such as applying the frozen audit to a distinct painter group or an existing larger prompted-artist benchmark. A shared-family control would be needed specifically to interpret common change beyond shared tradition; human fidelity judgments are not necessary for the paper’s current algebraic/descriptive claims.

**Question:** What concrete evaluation decision, beyond the already-known inadequacy of uncalibrated similarity or recognition as fidelity, is supported across settings by these measurements?

### W3: moderate limitation of selective-result interpretation

**Location:** Section 5.9; Appendix R.2; Tables 43–46.

The abstention counterexample is useful, but the joint usefulness verdict depends on one nominal level and an author-chosen 50% coverage threshold. CLIP/original/primary fails because one configuration accepts 55/112 rather than the 56/112 boundary. CSD’s missing Monet/Sisley conditions are a much stronger qualitative failure. The 26.0-point primary mean error reduction shrinks to 0.53 points at matched coverage, with four configuration ties and opposing effects for Nano Banana 2 and FLUX. These continuous results deserve more emphasis than the common fail label. The manuscript already avoids claiming that abstention generally fails; no such general failure is established.

**Revision scope:** Primarily presentation and scope. An exploratory risk–coverage display could add context from retained scores, but it must remain separate from the fixed primary operating point and cannot count as prospective validation.

**Question:** Can the headline distinguish severe painter loss from a one-query threshold miss, and show how little evidence the average matched-coverage advantage supplies about any individual configuration?

### W4: moderate reproducibility limitation

**Location:** Reproducibility statement; Appendices L.4 and N.3–N.7.

Independent numerical replay is substantially more complete than independent image measurement. The exact 1,878 original pixels, totaling about 4.36 GB, remain outside the compact repository, and a public exact-pixel recovery route is incomplete. This prevents a reader from fully checking feature extraction, source boundaries, prompt adherence, or another representation from the released numerical artifact alone. The AI-coded source audit also lacks human verification. No future archive or validation should be credited as completed.

**Revision scope:** Artifact release and documentation can address pixel access; validating source judgments requires additional checking of images.

**Question:** Can an anonymous, hash-preserving pixel bundle or verified recovery mechanism be supplied with per-file licenses and credits before publication?

### W5: minor editing/presentation issue

**Location:** Table 2 caption, page 5; Section 7; Appendices M and R.

Table 2 says that the artist-free baseline includes the painting clause, although the artist-free arm does not; the intended statement is that the named-minus-artist-free change includes that clause. The main text is dense, and the exhaustive appendices would be easier to use with a compact map from each claim to its target, evidence status and table. The conclusion also contains “an coverage-matched comparator.” The rendered figures I inspected are readable and do not show a major layout failure.

**Revision scope:** Editing only; these fixes do not supply new evidence.

## Prior-work context

The paper appropriately does not claim a new prompted-artist recognition task. Su et al. already study this task across 110 artists and multiple generalization settings, including supervised and few-shot methods ([primary source](https://arxiv.org/abs/2507.18633v1)). Concerns about interpreting raw CSD cosine as an absolute fidelity score, and diagnostic readout corrections, are also prior work ([Frochte v2](https://arxiv.org/abs/2605.09030v2)). The current paper’s additional value lies in its controlled common/labeled decomposition and connected decision diagnostics. Its limited artist scope makes the empirical specificity of that increment important.

## Ethics

No additional substantial ethical concern is evidenced for this study of historical, nonliving painters. The manuscript appropriately avoids claims of legal authorization or authenticity. However, release preparation is incomplete: the documented inventory includes 84 CC BY/CC BY-SA files and two records lacking a separate artist-text field. Those credits and license obligations need contextual review before a public bundle is distributed.

## Concrete revision priorities

1. **clarify existing claims:** Add a concise claim-to-evidence summary identifying finite-vector descriptions, assumption-dependent mean-response estimates, retrospective decisions, and the separate SD-Turbo check. Keep common naming movement separate from generated/reference mixture offsets.

2. **new evidence for stronger generalization:** For a stronger broad contribution, run the frozen diagnostics on an additional painter group or existing larger benchmark and obtain independently interleaved repeat/session evidence for the closed-service mean-response claims. These would strengthen scope and inference; they are not work already completed.

3. **presentation using completed evidence:** Lead the abstention discussion with per-painter coverage and the continuous matched-coverage error differences. Explain the qualitatively different CSD and CLIP failure modes without treating the 50% cutoff as a scientific boundary.

4. **reproducibility deliverable:** Provide an anonymous exact-pixel archive or verified recovery route with hashes, media types, per-file licenses and credits. State separately what can be replayed from vectors and what requires pixels.

5. **editing:** Correct the Table 2 baseline wording and conclusion typo, and add navigation for the extensive supplementary tables.

## Recommendation rationale

I lean narrowly toward acceptance as a careful empirical evaluation paper. The contribution does not need to be a new algorithm: the measured coexistence of mostly common proximity gain, representation-dependent painter contrast conclusions, offset-sensitive decisions, and painter-skewed selective coverage makes a useful connected case. The separate SD-Turbo analysis supplies distinct pixels and a meaningful adverse texture result, rather than merely repeating an algebraic identity. The authors retain all six requested configurations and all four painters and are unusually clear about retrospective reuse and unsupported perceptual interpretations. My independent numerical checks found no discrepancy in the inspected calculations. I do not recommend a stronger rating because the central service mean-response quantities remain conditional on unverified dependence assumptions; the scope stays within one related painter group and reused historical target; several lessons overlap established evaluation warnings; and full independent measurement reproduction is not yet publicly supported. These are evidence and contribution limits, not reasons to erase the valid descriptive findings. Editing alone would not turn this into broad prospective validation.

## Inspection and verification

Read the complete frozen 60-page manuscript via manuscript.txt, including the eight-page main text, impact statement, references and all appendices A–R, equations, captions and complete numerical tables. Verified the PDF SHA-256. Did not read prior scientific reviews, another current reviewer report, round summaries, goal state or a user target score.

Rendered pages inspected: 1, 3, 4, 5, 6, 7, 17, 23, 48, 51, 54, 55. Inspected main methods/results, main selective-coverage heatmap, the complete one-scene image panel, reference-contrast projection, pairwise heatmaps, cross-cohort tables, and selective criteria/coverage tables.

- Reconstructed reference counts 297/106/141/105 and H=5.9150074798210355 directly from retained feature rows and development scaling.

- Recomputed all six primary beta estimates and simultaneous Student intervals, D estimates, named-minus-generic common fractions, and repeat-difference energies. Values match the manuscript. Independently obtained the Nano Banana 2–FLUX common-trace-correlation point crossing 0.25075077326387407.

- Recomputed all 12 original-primary learned prototype gains, common fractions and Monet–Sisley amplitudes from retained embeddings; the gain identity holds to numerical precision and manuscript values agree.

- Recomputed the baseline, held-scene translation and supervised generated-prototype accuracies for both encoders and all six configurations, excluding both repeats of each held scene. All 36 Table 4 accuracies agree.

- Reconstructed all eight SD-Turbo family/aggregation panels using explicit ordered cross-products over distinct blocks rather than the production summary function. Largest discrepancy from retained summaries was 1.4210854715202004e-14.

- Reconstructed historical calibration thresholds, candidate sets, top-1 labels, gate acceptances and named-image exact-coverage margin selections for all eight settings. All 8,064 image decisions agree, with zero numerical score discrepancy in this environment. The primary mean error reductions are 26.030350 and 0.525940 percentage points.

Did not re-extract all features or embeddings from source pixels, rerun image generators, validate actual service checkpoint identities, establish error independence, or human-validate painter resemblance/source crops. Hash and numerical checks establish consistency conditional on recorded artifacts.

All 44 evidence-manifest entries matched their recorded hashes. Source inspection covered the original protocol; cross-cohort and selective plans; primary geometry/interval, cross-block and calibration/selection code; raw retained feature rows and scaler; learned embedding archives and row identities; and corresponding input/result records. The JSON companion lists the exact paths. Only the two review outputs were written.

**Inspected PDF SHA-256:** `3fbf2dafd970a1d352d63af336bd6cb4c089f2332dc8df604428cb4d9e3e62ac`.
