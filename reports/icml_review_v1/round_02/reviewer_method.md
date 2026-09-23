# Independent scientific review: statistical soundness and estimands

**Overall: 4/10 — marginally below acceptance. Confidence: 4/5.**

Local AI review simulation, not a conference decision. This review concerns only the frozen 31-page manuscript, including all appendices.

**PDF SHA-256:** `ad4377767c0d442617b9a6dff49eb1231e1c359072daf3e317ba87c20f206e14`

## Summary

The paper audits 1,008 images from six requested text-to-image configurations on 14 fixed scenes, six prompt conditions and two repeats, against 649 digital reproductions of four related painters. It separates shared prompt movement from centered, labeled painter contrasts, measures alignment and cross-repeat squared error, and compares the same images in 31 hand-designed coordinates, CLIP and a released CSD checkpoint. The main observations are majority-common naming change and prototype gain, representation-dependent Monet–Sisley alignment, and disagreement among proximity, recognition and error rankings.

## Strengths

1. **Sections 4.1–4.3; Appendix B and C.2.** The estimands are unusually explicit. Centering removes only a shared additive shift; beta measures one stacked reference direction; D measures total contrast error; scene averaging and scene-wise error are distinguished. The cross-repeat estimator is correct under the stated zero cross-repeat covariance assumption, including dependence induced by centering within each repeat. Negative estimates are handled honestly.
2. **Sections 3.2, 4.3 and 5.1; Tables 1 and 11.** The balanced common-scene design, generic-painting control, equal artist weighting, separate development scaling and declared 21-endpoint family are sensible. The manuscript correctly avoids treating features or images as independent scene replicates and does not claim that any configuration is established to outperform the no-distinction benchmark.
3. **Section 5.6; Appendix J; Tables 5, 17 and 18.** The same-image learned audit is a useful empirical addition. It directly shows that the weak hand-feature Monet–Sisley result is not representation-independent, and it distinguishes prototype-similarity gain from recognition. The exact common/labeled decomposition gives a concrete way to interrogate a proximity metric.
4. **Sections 5.4–5.5; Appendices C, F, I and K.** The paper retains inconvenient results: model order changes under calibration, one adjusted comparison disappears after source correction, a historical transfer pattern fails prospectively, and a timing diagnostic cannot establish independence. Source corrections, alternative reference panels and metric weightings are documented rather than silently substituted.
5. **Appendices J–K and inspected artifacts.** The computational audit trail is strong for numerical replay. The frozen PDF hash and all nine evidence-manifest hashes matched; the learned-vector, direct-naming and request-timing replay commands passed. Inspected core analysis code agrees with the displayed estimator and prototype-gain equations.

## Weaknesses

### W1. Evidence / contribution (major)

**Location:** Introduction contribution paragraph; Sections 5.6–7; Appendix J.3–J.4.

The empirical importance remains insufficiently established. The difference between proximity, recognition and squared contrast error is partly built into their definitions: Eq. 11 separates a global mean direction from label contrasts, and Eq. 7 penalizes magnitude as well as alignment. Observing different orders is useful, but does not by itself show which assessment is misleading for a specified downstream evaluation task. The majority-common fractions are conditional on four closely related artists and the chosen control, while the two learned representations share a CLIP backbone. No independently checked outcome, controlled benchmark with an externally specified success criterion, or independent artist/prompt panel establishes how consequential these effects are beyond this finite case study. I do not require a new algorithm or necessarily a human study; a convincing empirical demonstration of the evaluation consequence would suffice. The current caveats correctly bound the claims but cannot supply that missing importance.

### W2. Evidence / uncertainty (major)

**Location:** Sections 4.3, 5.2–5.6; Tables 2–5; Appendix C.4 and K.5.

The strongest headline findings are point estimates with influence checks, whereas the simultaneous intervals address a different, earlier family of endpoints. Single-scene deletion is not uncertainty for the common fractions, pair-alignment signs or ranking reversals under fresh requests. In particular, CSD common gain reaches only 54.2% for GPT Image 2, and its three lowest scene errors are close (.714, .735 and .741). These are legitimate descriptive values, but their stability under output sampling is not established. The fixed-scene Student variance includes fixed scene heterogeneity and has only approximate coverage with 14 summaries; two repeats do not establish the needed repeat/block independence. The common-state coverage failure in Appendix C.4 and the explicitly limited linear timing check in K.5 make this an evidential limitation, not a cosmetic one. I found no algebraic error in the reported procedure, and the paper appropriately labels these comparisons descriptive. Nevertheless, they should carry less weight as scientific findings until uncertainty is quantified for these endpoints or the collection is replicated.

### W3. Evidence / estimand relevance (major)

**Location:** Sections 3.1, 4.2 and 5.4–5.5; Appendix C.1 and C.5.

D has a coherent finite-vector target, but its relevance to painter distinctions is weakly calibrated. A pooled historical contrast is imposed on every scene even though actual paintings have different subject mixtures; the paper itself measures class-target departure of .438H. Consequently, a model can be penalized for a real artist-by-content interaction and rewarded for a small, nearly invariant response. Table 3 demonstrates precisely that scene variation changes the model ordering. The title-class sensitivity, AI-only source audit and random split genuine-painting controls do not determine whether that penalty is desirable: the controls have wide two-draw ranges, and exact held-out class-control errors remain appreciable. This does not invalidate D as the defined audit quantity, but it limits what the error-ranking component adds scientifically. A better anchored controlled target or explicit evaluation task is needed to elevate the ranking beyond a property of this reference construction.

### W4. Artifact / reproducibility (moderate)

**Location:** Reproducibility paragraph; Appendix G and K.1–K.6.

Independent measurement reproducibility remains incomplete. Exact pixels are outside the compact repository, no complete public archive or verified recovery route is supplied, and requested gateway configurations lack response-level model attestation. Hashes and local replay establish consistency conditional on retained artifacts, not independent regeneration or feature extraction. This is particularly material for a paper whose main contribution is an empirical audit of image measurements. The limitation is candidly disclosed; it still reduces the study’s value as a reusable benchmark.

### W5. Reporting / writing (moderate)

**Location:** Section 5.6; Table 5; Appendix J.3–J.5 and Tables 17–18.

The learned audit emphasizes common-gain percentages but does not tabulate absolute total, common and labeled gains for every configuration. It also says development-work recognition and confusion matrices are retained without displaying their calibration context in the PDF. Providing these already-computed quantities, along with each representation’s reference contrast energy, would make the size and reliability of the learned comparisons much easier to evaluate. The common-change columns repeated identically across reference panels can be consolidated to make room. This is principally a reporting improvement, unlike W1–W3.

## Questions

1. What specific evaluation decision should change after this audit, and what existing evidence establishes that the change is beneficial? Can the paper distinguish an informative empirical failure of a metric from the expected disagreement of different estimands?
2. How much fresh-request uncertainty surrounds the generic-baseline common fractions and Monet–Sisley alignments, especially the 54.2% CSD fraction? Can an uncertainty analysis target the fixed scene panel without treating authored scenes as a random population?
3. What evidence justifies penalizing scene-dependent painter contrasts around the pooled target? Can the genuine-painting controls be used to define a useful task-specific reference range without conflating target estimation error and artist-by-content structure?
4. Can the exact-pixel cohort, source metadata and measurement environment be made accessible for anonymous independent verification, and what response-level evidence is available about the served configurations?
5. Why are absolute learned gains, development-work prototype recognition and the reference energies omitted from the PDF despite being retained in the analysis?

## Revision priorities

1. **new evidence:** Anchor at least one principal conclusion to a concrete evaluation task with an independently specified success criterion, or demonstrate transfer of the common-versus-labeled effect to an independent artist/prompt panel. A controlled measurement benchmark can address this without requiring perceptual claims.
2. **uncertainty / additional sampling where needed:** Quantify fresh-request uncertainty for the headline common fractions and pair contrasts, preserving the fixed-scene estimand and the exploratory status. Separate stable disagreements from near-ties; an independent collection would also address service-state sensitivity.
3. **target validation:** Provide evidence for the practical meaning of pooled scene-wise contrast error, or center the contribution on the directly interpretable decomposition and avoid giving error minima more evaluative weight than the target supports.
4. **artifact:** Supply a reviewable exact-pixel bundle or demonstrated complete recovery route, with the retained hashes and source-license metadata.
5. **writing / existing results:** Report absolute learned gain components, reference energies and real-development recognition/confusions; use a compact main-text comparison to separate mathematical identities, descriptive observations and resolved comparisons.

## Scores and recommendation

| Dimension | Score | Rationale |
|---|---:|---|
| Soundness | 3/4 | The main algebra, cross-repeat estimator and inspected implementation are correct under explicit assumptions. The uncertainty model is approximate and target validity is limited, but these restrictions are largely stated accurately. |
| Presentation | 3/4 | Clear definitions, useful worked interpretation and legible figures/tables. The many retrospective diagnostics and repeated caveats obscure the central empirical claim, and several useful learned calibration quantities are absent from the PDF. |
| Contribution | 2/4 | A useful, carefully documented finite-case metric audit. Its broader scientific significance and practical evaluation consequence remain insufficiently established. |

I recommend 4 (marginally below acceptance). The paper is mathematically careful, transparent about its estimands and limitations, and supported by a substantial, replayable within-cohort analysis. The same-image learned comparison provides useful empirical evidence and deserves credit. My concern is chiefly contribution rather than a discovered numerical mistake: the results remain a narrowly conditioned demonstration that several established metrics answer different questions, without sufficiently establishing the importance or external validity of the resulting evaluation changes. Limited uncertainty for the headline descriptive comparisons and incomplete public measurement access further weaken the case. The paper is close enough that a concrete, well-validated evaluation consequence could change my judgment; additional caveats alone would not.

## Prior work

The paper appropriately cites prior prompted-artist recognition, CSD, conditional evaluation and cross-validated distance estimation rather than claiming those operations as new. Su et al. already distinguishes prompted-artist identification from style recognition of real artwork; this manuscript’s incremental value is the centered same-image contrast audit, whose practical importance needs stronger demonstration. See [Su et al., version 1](https://arxiv.org/html/2507.18633v1).

## Ethics

No concrete ethics violation is evidenced. The paper discloses AI-assisted source auditing, limits its claims to deceased artists and does not report human participants. Outstanding release attribution is acknowledged; I do not infer a license violation from an unreleased local inventory.

## Inspection and reproducibility

- Read PDF pages 1–31, including the eight-page main paper, references and all appendices. Visually inspected pages 5, 17, 19, 20, 23, 27 and 28.
- Verified the frozen PDF hash and all nine hashes in the round’s evidence manifest. Inspected the learned audit plan, input census, results and validation receipts; direct-naming and timing analyses; and artifact and attribution inventories.
- Inspected the core contrast/error, interval, learned-geometry, prototype and recognition code. The learned-vector, direct-naming and timing replay commands all passed.
- Large JSON artifacts were inspected through selected records, summaries and exact replay, not by manually reading every scalar. I did not re-extract all original pixels or collect new service responses.
- Numerical replay is substantially more complete than independent pixel-level measurement reproduction. I did not read other reviewers’ reports or historical scores.
