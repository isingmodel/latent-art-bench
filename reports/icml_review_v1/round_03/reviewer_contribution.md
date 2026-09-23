# Independent contribution review - round 03

*AI review simulation using the fixed local ICLR-style rubric; not an official conference decision.*

**Manuscript:** Artist-Name Responses beyond a Shared Painting Effect in Text-to-Image Generation
**Inspected PDF SHA-256:** `bbcc12901427538ed0938cdea510f848a0999d0edd08b4bc707c5b6fb8051472`
**Reading scope:** complete frozen PDF, pp. 1-46 (eight main pages, references, Appendices A-O).

## Summary

The paper audits 1,008 images from six requested generator configurations using four painter names, artist-free and generic-oil controls, 14 fixed scenes, and two repeats. It compares 31 hand-designed features and CLIP/CSD embeddings against finite historical reproduction panels. Artist-centered contrasts separate an aligned response from total mismatch; most named-minus-control movement and learned prototype gain is common across the selected painters. A retrospective leave-scene-out mean translation changes prompt-name accuracy without changing centered contrasts, while supervised generated centroids perform better. The supported contribution is an unusually explicit same-image accounting of these distinct evaluation quantities, rather than a new algorithm or a validated painter-fidelity metric.

## Strengths

1. **Sections 3-5, pp. 2-7; Appendices B, I, L, M.** The crossed prompt design and generic-oil control make the measured intervention interpretable. Reporting common and labeled components in the same representation avoids attributing every improvement in own-painter proximity to artist differentiation. The absolute components in Table 20 are particularly useful.
2. **Sections 4.2-4.3, pp. 3-4; Appendices B, C, O.** The cross-repeat estimator and its conditional target are carefully specified. Artist dependence induced by centering is handled at the repeat-block level; negative estimates are retained. The paper acknowledges fixed-scene heterogeneity, unverified service independence, and that the covariance scenarios do not repair interval coverage.
3. **Sections 5.6-5.7, pp. 6-8; Tables 3-4; Appendices L-M.** The representation reversal for Monet-Sisley is reported candidly. The decision experiment has a known nonperceptual criterion, excludes both repeats of the held scene, reports harmful corrections, and gives the stronger supervised comparator with its larger information budget. These are real empirical observations, not merely algebraic identities.
4. **Appendices L-N, pp. 25-44; bound scientific records.** Provenance and numerical accounting are strong. All 23 directly bound evidence files match the frozen manifest. My separate calculation from the row manifest and retained embeddings reproduces Table 3's common-gain fractions and every original-primary B/T/G accuracy in Table 4. No arithmetic error was found in these headline results.

## Weaknesses

### W1. significance; requires new evidence for a stronger contribution

**Location:** Contribution statement, pp. 1-2; Sections 5.6-5.7 and Conclusion, pp. 6-8.

The demonstrated advance remains a narrow evaluation case study. Common-versus-centered decomposition, sensitivity of cosine decisions to class intercepts, and the difference between real-reference recognition and generated-domain separability are established distinctions. The measured magnitudes and the CSD decision gains add value, but the study does not yet establish a reusable diagnosis that predicts when a practical evaluation conclusion is unreliable or when mean translation should help. On the original primary target CLIP has two declines, one tie and three gains; the CSD all-positive pattern becomes a decline and a tie for two configurations after source cropping (Table 25). These adverse results are appropriately disclosed, but they leave a practitioner with a reporting recommendation rather than a validated evaluation procedure. A new algorithm is unnecessary; an independently reproduced, consequential empirical finding would suffice. More bookkeeping or narrower wording alone would not address this limitation.

### W2. scope and interpretation; new evidence needed

**Location:** Sections 3.1-3.2, p. 2; 5.2, pp. 4-5; 6.1, p. 8; Appendices L.4 and M.1.

The majority-common result is conditioned on four closely related painters and on a generic oil-painting baseline. A common movement toward their shared tradition can be a legitimate stylistic response. Its large fraction does not by itself diagnose failed naming, and the fraction changes with the artist set and baseline. The manuscript largely avoids that overclaim, but it also provides no matched shared-tradition control or second artist group establishing what the large percentage teaches beyond this chosen panel. The transfer task additionally assumes a known balanced pool from the same generator and fixed candidate set. It does not show whether its benefits survive a new collection session or a changed prompt template. These limits constrain significance, even though the finite-panel numerical claims remain sound.

### W3. empirical support; not an identified arithmetic error

**Location:** Section 4.3, p. 4; Sections 5.5-5.6, pp. 5-7; Appendices C.4, N.5, O, pp. 15, 44-46.

The inferential results depend on stable, independent request errors that two repeats in one collection cannot assess. The covariance appendix gives useful assumption-indexed point crossings, but neither estimates actual dependence nor bounds bias in the headline scene-averaged shared fractions. The linear drift check also cannot do this. Moreover, pooled historical contrasts mix content and capture differences, and learned versus hand-feature comparison changes preprocessing together with representation. These caveats are stated correctly. Their cumulative consequence is that the strongest broadly relevant findings are descriptive and representation/target specific, while the only confirmatory model-error comparisons are few and partly source-sensitive. I do not interpret the adverse synthetic coverage scenario as evidence that the actual service was dependent.

### W4. literature positioning; editorial correction plus substantive differentiation

**Location:** Related Work, p. 2; Sections 5.6-5.7, pp. 6-8.

The treatment of prior work is incomplete at the point where the practical contribution is claimed. [Su et al.](https://arxiv.org/html/2507.18633v1) already distinguish prompted-artist recognition from real-art style recognition and study generator-specific benefits from generated training data. More directly, [Frochte (2026), *When Style Similarity Scores Fail*](https://arxiv.org/html/2605.09030v2), diagnoses raw CSD score failures, shared-tradition confusions, and readout corrections. That preprint explicitly excludes closed-set discrimination, so it does not duplicate this paper's translation experiment. Nevertheless, the paper should explain its distinct empirical lesson relative to that work; a generic warning about raw similarity is no longer an adequate novelty statement.

### W5. reproducibility; artifact completion

**Location:** Reproducibility, p. 8; Appendices L.4 and N.3-N.6, pp. 27, 43-45.

Exact-pixel access is incomplete outside the local workspace. The retained vectors enable strong numerical replay but cannot independently check source selection, the AI-coded crops, image measurements, or encoder preprocessing. This matters especially for a measurement paper whose conclusions change with representation and some source corrections. The local inventory and attribution metadata are useful preparation, not a completed public artifact.

### W6. presentation; editing

**Location:** Abstract and Sections 4-5, pp. 1-7; Appendices I-O, pp. 23-46.

The main text is careful but crowded with multiple targets, baselines, calibrations and caveats. The named-minus-generic common component and the generated-to-reference translation are different quantities; the paper states this, yet placing them under one contribution makes the practical through-line easy to miss. A compact claim/evidence/limitation table and a shorter appendix hierarchy would make the scientific message easier to assess. This is an editing issue, unlike W1-W3.

## Questions

1. What specific evaluation decision should a practitioner change after seeing the common/labeled decomposition, beyond reporting another descriptive statistic? Which observed result establishes that benefit?
2. How much of the large common naming component is shared-tradition agreement, and what evidence would distinguish that interpretation from an evaluation nuisance?
3. Is the intended use of mean translation limited to a known balanced four-name pool from the same generator? Which independent held-out setting would test the usefulness of this rule under that declared use?
4. How does the proposed evaluation lesson differ from Su et al.'s generated-versus-real recognition distinction and Frochte's diagnostic/readout study?
5. Can the authors supply an anonymous exact-pixel artifact or verified recovery mechanism with the per-file source metadata needed for independent extraction?

## Revision priorities

1. **new evidence.** Choose one consequential, nonperceptual claim and test it prospectively on untouched observations. For example, freeze the current reference prototypes and mean-translation protocol, collect an independently interleaved session with held-out scene wording, and report all six configurations, both encoders and adverse decisions. A new algorithm or a human study is not required for prompt-name recovery.
2. **new evidence.** If majority-common movement remains the central empirical claim, add a control that separates shared-tradition resemblance from generic painting, or replicate the decomposition on a separately selected artist group. Define in advance what result would support the claimed evaluation lesson.
3. **literature and presentation.** Position the paper against the raw-CSD diagnostic literature and the existing generated-domain recognition findings. Organize the main contribution around the supported distinction between proximity gain, reference decisions and generated separability; keep the two different common components explicit.
4. **artifact.** Complete exact-pixel access, anonymous replay instructions, and attribution packaging. Preserve the existing hashes and all unfavorable results.

These are priorities for a stronger submission, not credit for work already done. Human evaluation is necessary only for a perceptual-fidelity claim; the present prompt-name task has a known label criterion.

## Ethics

No evidenced issue warrants a separate ethics escalation. The paper discloses AI-assisted source coding and incomplete attribution/release packaging; the latter should be completed for the artifact. I do not infer a license violation from the available records.

## Scores and recommendation

| Dimension | Score |
|---|---:|
| Overall | **4 - marginally below acceptance** |
| Soundness | 3/4 |
| Presentation | 3/4 |
| Contribution | 2/4 |
| Confidence | 4/5 |

I recommend 4 (marginally below acceptance). The manuscript is largely sound for its carefully conditioned, descriptive claims, and the same-image decomposition plus adverse-outcome reporting is worthwhile. However, the contribution is not yet sufficiently consequential relative to established prototype evaluation, domain-sensitive recognition, and recent CSD-diagnostic work. The added decision experiment strengthens the paper, but remains a retrospective four-class, single-collection demonstration with mixed transfer effects and no independent validation of a reusable evaluation lesson. This recommendation is not based on the absence of a new algorithm or on demanding perceptual claims the paper does not make. The evidence gaps require new observations or a stronger operational demonstration; editorial narrowing and successful replay alone would not close them.

**Confidence limits:** Read the full frozen manuscript and pertinent primary literature; inspected bound plans, source definitions and records; independently reproduced the main learned gain and classification summaries. I did not re-extract all pixels, rerun encoders, authenticate served models or perform a human perceptual assessment.

## Evidence inspected

- `reports/icml_review_v1/rubric.md`: Read the fixed rubric.
- `reports/icml_review_v1/round_03/input/manuscript.pdf`: Complete 46-page frozen manuscript, including eight main pages, references and Appendices A-O. Read complete manuscript.txt; visually checked render contact sheets for all pages and enlarged Figures 2 and 5.
- `reports/icml_review_v1/round_03/evidence_manifest.json`: Verified SHA-256 for all 23 directly listed records; all match. Hash verification does not imply substantive reading of every bound report.
- `studies/painter_learned_audit_v1/PLAN.md`: Read complete plan.
- `studies/painter_prototype_transfer_v1/PLAN.md`: Read complete plan, including information budgets and chronology.
- `studies/painter_repeat_covariance_v1/PLAN.md`: Read complete plan and assumptions.
- `reports/painter_learned_audit_v1/inputs.json`: Inspected metadata and row identities; used all rows in an independent original-view calculation.
- `reports/painter_learned_audit_v1/analysis.json`: Inspected original-view analysis structure, recognition context and shared-change summaries; verified bound analysis/extraction code hashes.
- `reports/painter_learned_audit_v1/embeddings_clip.npz`: Verified against the transfer input binding; independently recomputed original-primary prototype common gains and B/T/G accuracies for all six configurations.
- `reports/painter_learned_audit_v1/embeddings_csd.npz`: Verified against the transfer input binding; independently recomputed original-primary prototype common gains and B/T/G accuracies for all six configurations.
- `reports/painter_prototype_transfer_v1/inputs.json`: Inspected frozen rules/splits and verified relevant code/embedding bindings.
- `reports/painter_prototype_transfer_v1/analysis.json`: Inspected axes, retained result structure and scope; direct computation reproduced the main table.
- `src/latent_art_bench/painter_prototype_transfer_v1.py`: Read evaluator, score summarization, paired accounting and row assembly (first 270 lines); source matches frozen binding.
- `src/latent_art_bench/painter_learned_analysis_v1.py`: Inspected relevant prototype/common-gain definitions by targeted source search; source matches frozen binding.
- `reports/painter_repeat_covariance_v1/inputs.json`: Inspected binding/environment metadata.
- `reports/painter_repeat_covariance_v1/analysis.json`: Inspected all model D/q arrays and pair-crossing structure; recomputed all grid formulas and interior crossings with zero residual from retained D/q values.
- `reports/icml_review_v1/artifact_inventory.json`: Inspected census, byte total and explicit local-only availability metadata.
- `reports/icml_review_v1/artifact_attribution.json`: Inspected record census, license categories and local-only availability metadata.

### Primary literature

- [Somepalli et al., Investigating Style Similarity in Diffusion Models (ECCV 2024)](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/08294.pdf): Primary-paper indexed text for the GSS prototype definition and content-constrained evaluation; ECVA paper page.
- [Su et al., Identifying Prompted Artist Names from Generated Images (2025), v1](https://arxiv.org/html/2507.18633v1): Primary HTML, especially Sections 3.1-3.5, 4.1-4.2 and 5.1-5.3.
- [Frochte, When Style Similarity Scores Fail: Diagnosing Raw CSD Cosine in Artist-Style Evaluation (2026), v2](https://arxiv.org/html/2605.09030v2): Primary abstract/history and HTML Sections 1-4 and 5-7; scope exclusion of closed-set discrimination. Submitted May 9, revised July 5, 2026.

The CSD prototype definition and content-constrained evaluation were checked against the [original ECCV paper](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/08294.pdf). The manuscript correctly attributes those ingredients; the novelty assessment concerns its empirical diagnostic findings.

No older review, other reviewer output, historical editorial rating, desired score, or parent-context discussion was read or used. No conferring occurred.
