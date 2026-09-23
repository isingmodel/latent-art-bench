# Independent scientific review: contribution and communication

## Review identification and scope

- Manuscript: *Artist-Name Responses beyond a Shared Painting Effect in Text-to-Image Generation*.
- Round: 01; reviewer role: contribution, related work, and communication to a broad ML audience.
- PDF inspected: `reports/icml_review_v1/round_01/input/manuscript.pdf`, all 23 pages, including Appendices A–I.
- PDF SHA-256: `4ee2a3004226bbcd0151ca310265efad851b69e431d1e05895701b8f918a3e85`.
- Also read the frozen `icml.tex`, `icml_main.tex`, `icml_appendix.tex`, `icml_reproducibility.tex`, and bibliography. Visually inspected rendered pages 1–3, 6–7, and 21. I did not inspect other reviews, historical editorial reports, critics, or goal/status documents. I did not rerun the numerical pipeline or independently authenticate service identities.
- This is a local ICLR-style review simulation, not an official conference decision.

## Summary

The paper evaluates six requested image-generation configurations on four related painters, 14 outdoor scenes, two repeats, and artist-free, generic-painting, and named-painter prompts. It compares 31 standardized image measurements with a finite collection of 649 reproductions. Centering across painter names removes a common additive response; a projection coefficient measures reference-aligned amplitude, and a cross-repeat inner product estimates squared error of scene-conditional mean contrasts. The empirical results distinguish a large common prompt response from labeled painter agreement, show uneven pairwise alignment, and demonstrate different orderings after scene averaging or scalar calibration. Reference-region correction also changes which model differences exclude zero.

This is a thoughtful empirical audit, rather than a new estimator or image-generation method. Its main merit is making several commonly conflated evaluation questions explicit. The supported conclusions remain conditional on one small painter panel, one feature representation, one prompt template, and a reference target that mixes painting properties with subject and reproduction differences. My concern is the significance established by the evidence, rather than a requirement for algorithmic novelty.

## Strengths

1. **A clear and useful distinction.** Sections 1 and 4 separate a name response, reference-aligned amplitude, and total labeled mismatch. The lightness example and the no-contrast/exact/doubled examples explain this well. A positive projection is correctly not treated as success on every painter pair.
2. **Careful experimental and statistical accounting.** The crossed scene design, separate generic-painting arm, independent-repeat rationale, development-only scaling, and scene-paired comparisons make the experiment interpretable. The paper does not inflate the sample size by treating features or images as independent scenes. It consistently labels retrospective analyses as such.
3. **Candid reporting of limitations and contrary evidence.** The text acknowledges content mismatch, source artifacts, service-identity uncertainty, approximate inference, and incomplete pixel access. It preserves a contrary prospective transfer result in Appendix F rather than presenting historical behavior as universal. Table 4 shows the consequences of source correction rather than only its reassuring aspects.
4. **The empirical pattern is more informative than a single leaderboard.** FLUX's low uncalibrated error, GPT Image 2's stronger directional agreement, and their changed order after rescaling illustrate different properties of this measured response. Figure 1 and the pair matrix make these claims inspectable. I do not count the number of sensitivity analyses as an independent contribution, but they improve confidence in the limited conclusions.

## Weaknesses and locations

### W1. The added scientific value over existing evaluation practice is plausible but not demonstrated directly

**Locations:** Section 2, pp. 1–2; Sections 5.3–5.4, pp. 5–7; Appendix C.2, p. 14. **Type:** evidence and contribution.

The paper correctly acknowledges that content-controlled artist substitutions, cross-model comparisons, and style descriptors already exist. Su et al. study both artist-free/named image similarity and real-artist prototypes, while Somepalli et al. evaluate learned style similarity. The present centered, labeled comparison asks a different question, but the manuscript does not compare the conclusions of these approaches on its own images. Thus the reader sees that quantities can disagree, but not a concrete failure of a commonly used evaluation that this audit usefully diagnoses. [Su et al.](https://arxiv.org/html/2507.18633v1), [Somepalli et al.](https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/8294_ECCV_2024_paper.php).

Some results are expected properties of squared distance: amplitude need not equal agreement, averaging removes a scene-variation term, and scalar shrinkage can reduce mismatch. The empirical instances are worthwhile; however, changing a point ordering through a feature-space rescaling is insufficient by itself to establish a broadly important evaluation result. There is no need to invent a new algorithm, but the paper needs a sharper demonstration of what consequential misconception its measurements resolve.

### W2. The finite reference target makes the central comparison difficult to interpret beyond this collection

**Locations:** Sections 3.1, 4.2 and 6.1, pp. 2, 4, 7–8; Appendix C.1, pp. 13–14. **Type:** evidence and scope.

The authors are explicit that the same pooled painter contrast is the target in every scene. This is mathematically legitimate, but it penalizes legitimate scene-dependent differences as well as mismatches. Appendix C.1 quantifies the problem: class-specific reference means depart from the pooled target by .438H, and the class-stratified genuine-painting controls have exact-held-out-mean scores spanning .544–.993 against the pooled target. These are substantial values relative to the no-distinction benchmark of one. The control is useful and does not invalidate the estimator, but it shows why a low or high score has limited interpretation without a better characterized target.

The class-target and source-crop checks do not resolve that issue: the classes are coarse, 230 title assignments change under the AI visual audit, and no human verification is reported. A narrowly defined finite-target study can be sound, yet the current evidence does not show how much of the identified painter pattern is reproducible across independently assembled or source-controlled reference material.

### W3. The most interesting substantive finding remains descriptive and concentrated in one painter panel

**Locations:** Abstract; Section 5.3 and Figure 2, pp. 5–6; Section 5.5, p. 7; Appendix C.2/Table 9, p. 14. **Type:** evidence.

Weak Monet–Sisley alignment is potentially the most useful empirical observation. However, pairwise estimates have no uncertainty intervals or independent confirmation. Some signs change after source correction. There is therefore evidence of a pattern in this dataset, rather than evidence that five services systematically fail to express this distinction. The paper usually makes that distinction, but the finding carries much of the contribution.

The four-painter configuration is also dominated by a strong direction: the first reference component accounts for 66.3% of centroid variation, and omitting Cézanne reduces FLUX's aggregate response from .470 to .096. This is not a reason to dismiss the close-painter question; it is a reason to validate the selected pair-level hypothesis prospectively, with enough repeats to characterize it. More deletions of the same observations would not substitute for that evidence.

### W4. The headline shared fraction conflates the painting instruction with the additional naming effect

**Locations:** Abstract; Section 5.2/Table 2, pp. 5–6; Appendix B, p. 12. **Type:** additional analysis and communication.

The 82.5–95.7% figure is accurately defined as artist-free-to-named change, including the oil-painting clause. Its interpretation is consequently narrower than a statement about how much *adding a painter name* does. The generic arm is a strong design feature. A direct common-versus-between-name decomposition of **named-minus-generic** change would expose the incremental naming effect more clearly. The reported cosine and magnitude ratio describe related quantities but require readers to reconstruct that comparison. This can be addressed largely with retained data; it is not a request to collect a new generic control.

### W5. Accessibility and reproducibility need a clearer path from numbers to images

**Locations:** Section 3.3, p. 2; Appendix A/Table 5, p. 11; Appendix H/Figure 5, p. 21; Reproducibility and Appendix I.3, pp. 8 and 22. **Type:** editing and artifact availability.

The prose is generally strong, but the actual feature-family inventory is relegated to Appendix A, even though feature choice defines the scientific object. Bringing its short table into the main text and showing one coordinate-level explanation of the Monet–Sisley result would help a broad ML reader. The geometric plot is also useful enough to introduce earlier. Appendix H's reference to the pair analysis “below” is stale.

Numerical replay from feature vectors is valuable. Nevertheless, the lack of a public exact-pixel archive or verified recovery route prevents an independent reader from re-extracting features, checking source corrections, or applying an alternative representation to the same cohort. That specifically weakens the utility of an evaluation contribution; it is more consequential than an ordinary missing implementation detail.

## Questions for the authors

1. On the same generated images, do existing artist-prototype or style-similarity evaluations give a materially misleading conclusion that the centered contrasts diagnose? What concrete conclusion changes, and what evidence adjudicates the difference?
2. How stable are the Monet–Sisley contrast direction and magnitude under independent reference splits and additional requests? Can a prospective test distinguish weak alignment from the uncertainty of two-repeat estimates?
3. What are the shared and between-name fractions for named-minus-generic change, with uncertainty or clearly stated descriptive status?
4. Can the retained generated pixels and the exact reference recovery/crop information be distributed in an anonymous artifact, so that alternative feature extraction is possible?

## Scores

| Field | Score | Rationale |
|---|---:|---|
| Soundness | 3 / 4 | The estimator and limited conditional claims are coherent; uncertainty and target-validity limitations are disclosed. I have not independently replayed the computation. |
| Presentation | 3 / 4 | Clear explanations and disciplined claims; the feature inventory and concrete empirical interpretation should be more prominent. |
| Contribution | 2 / 4 | A useful, careful case study, but its incremental practical value and repeatable pair-level finding are not yet sufficiently established. |
| Overall recommendation | **4 / 10 — marginally below acceptance** | The work is close in rigor and communication, but the empirical contribution currently falls short in demonstrated significance. |
| Confidence | 4 / 5 | I read the complete manuscript and relevant primary work; confidence is lower concerning pixel-level execution and service provenance, which I did not independently audit. |

The overall recommendation uses the fixed **0/2/4/6/8/10** scale. It is not an arithmetic average of the three subscores.

## Ethics concerns

I found no evidenced concern requiring a separate ethics review. The historical-artist scope, recorded public-domain metadata, and disclosure of AI assistance are appropriate. The unvalidated AI source audit is an evidentiary limitation, not by itself an ethics violation. Scores should continue to be described as measurements of the documented collection, rather than rankings of artistic authenticity or legal permissibility.

## Concrete revision priorities and what would change my decision

1. **Establish a consequential evaluation result.** Use the retained cohort to compare the proposed diagnosis with a relevant existing prototype/style measure. Identify a specific misleading aggregate conclusion and explain its resolution using controlled evidence. Learned features need not be treated as ground truth, and a human study is not mandatory for the current finite-feature claim.
2. **Confirm the central empirical distinction.** Freeze a targeted follow-up of the close-painter result with additional independently requested repeats/new scenes, and characterize the reference contrast using independently assembled or carefully source-controlled material. Specify a meaningful weak-alignment region rather than inferring weakness only from point estimates near zero. A clear confirmation—or a informative failure that explains the boundary of the effect—would materially strengthen the paper.
3. **Use existing data to isolate incremental naming and improve interpretation.** Add the named-minus-generic decomposition, pair-level uncertainty appropriate to its stated target, and a small feature-level explanation. Move essential feature information into the main text. These improve the current paper but, alone, would not change my recommendation.
4. **Make the evaluation reusable.** Provide an anonymous, exact-pixel artifact or a verified recovery procedure, including source corrections and full prompts. Preserve the current candid provenance statements.

I would move toward **6** if the paper demonstrated the added evaluative value in priority 1 and provided convincing independent evidence for the central result in priority 2, with adequate artifact access. This is a focused route, not a demand for every possible robustness experiment. Copyediting, further deletions/reweightings of the same sample, or stronger wording would not change the decision. A substantially broader, reusable and independently replicated result would be needed for **8**.
