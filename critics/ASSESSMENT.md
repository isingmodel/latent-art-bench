# Assessment of the three reviews

Reviewed on 2026-09-13 against `d12f726`. The manuscript, scientific source,
protocols and tests do not differ from the `cc764fe` version identified by
Reviews 1 and 2. This assessment does not revise the manuscript or frozen
scientific results. The additional calculations below are exploratory checks
for adjudicating the reviews.

**Overall judgment: most of the criticisms make sense. There is little outright
nonsense, but there are important differences between demonstrated defects,
limitations of scope, optional extensions, and overstatements. Review 2 is the
most technically specific and best matched to the paper's current claims.
Review 1 is largely sound but asks for a stronger research contribution.
Review 3 has useful scientific suggestions, alongside several exaggerated or
already-addressed points.**

## What this project actually tests

LatentArtBench compares generated images with documented digital painting
reproductions in 31 color, spatial and texture coordinates. The current
experiment crosses six recorded generator configurations, 14 authored scenes,
six clauses and two repeated requests: 1,008 images. Four named clauses concern
Monet, Sisley, Pissarro and Cézanne; the other two are artist-free and generic
oil-painting controls. There are 649 reference works and a separate 221-work
development panel for scaling.

The paper asks whether changing painter names produces differences aligned with
the reference collection, after subtracting the response common to the four
names. The slope beta measures projection onto the reference configuration.
The error D measures scene-wise disagreement with that fixed, pooled target,
using independent repeats to remove additive sampling-noise bias. It is not
claimed to measure perceptual artistic fidelity. Earlier naming, palette and
fixed-map studies supply separate supporting evidence; their images are not
pooled into the main comparison.

The main findings survive numerical replay: all six aggregate slopes have
positive simultaneous intervals; FLUX has the lowest primary error estimate
and adjusted advantages over Flare and Sunburst; the other 13 pairwise
comparisons are unresolved. No model is established to beat D = 1. Artist-pair,
scene-variation and calibration diagnostics show why those findings do not
establish a general artistic ranking.

## Decisions on the substantive criticisms

| Review location | Decision | Reason and appropriate response |
| --- | --- | --- |
| R1 §3.2; R2 §4; R3 §§4, 16 | **Accept: highest priority.** | Calibration strips and a wrong content label occur in the actual reference panel. Quantify prevalence and the effect of objectively defined corrections. Include the development panel because its IQRs determine metric weights. Preserve original results alongside the correction. |
| R2 §5 | **Accept the technical issue; limit its consequence.** | The shared artist-free estimate creates a positive covariance term in the generic/common dot product. The suggested cross-repeat diagnostic is appropriate. Recalculation below preserves the positive alignment pattern; it does not reveal failure of primary D. |
| R1 §3.1; R2 §3; R3 §§1, 3 | **Accept the limitation; reject treating it as an invalid estimator.** | D penalizes legitimate scene dependence when the target is pooled. The paper explicitly defines this quantity and gives the decomposition and counterexample. R2 correctly treats the interpretive objection as resolved. R1's request to justify its scientific priority is a reasonable contribution-level challenge, not an algebraic correction. |
| R1 §3.3; R2 §6; R3 §3 | **Accept.** | Calibration changes the evaluation question. Training-set improvement follows from optimizing a quadratic; transfer to omitted scenes is the empirical finding. Neither raw nor calibrated ordering establishes artistic superiority. |
| R2 §§6–7; R3 §16, minor revision 3 | **Accept: useful, bounded analysis.** | Report stability of calibration and separate reference split variation from sparse pseudo-output noise. Existing vectors suffice for descriptive checks. Overlapping leave-one-out folds are not independent replications. |
| R1 §3.4; R2 §2; R3 §§2, 8 | **Accept uneven measured artist coverage.** | Monet–Sisley alignment is weak in several configurations, and Cézanne omission sharply reduces FLUX's slope. Do not infer a learned art-historical hierarchy or perceptual inability from four painters and unvalidated reference coordinates. |
| R2 §2, final qualification | **Accept.** | Negative pair slope and lower error after swapping that pair are algebraically connected. They are not independent corroborating experiments. |
| R1 §3.5; R2 §8; R3 §9 | **Accept assumptions and limited inference; reject presumed failure.** | Fourteen scene summaries and two repeats limit coverage assessment and external inference. The scene-based variance identity and simulations are legitimate. Shared-state simulation failure is not evidence that the actual requests were dependent. |
| R2 §8 | **Accept: simulation coverage is too narrow to represent all observed noise.** | The quoted noise-power estimates reproduce. The homoskedastic simulation uses 0.5, whereas estimated centered repeat-noise powers range from 0.436 to 2.666. Noise/covariance sweeps would extend the stress test; the mismatch alone does not invalidate existing intervals. |
| R1 §3.6; R2 §7; R3 §5 | **Accept lack of absolute calibration; qualify claims of instability.** | The control distributions mix changes in reference targets, content and two-work sampling noise. Our decomposition below shows that their broad spread should not be attributed mainly to instability of the underlying target geometry. |
| R1 §§3.7, 5; R2 §11; R3 §§7, 16 | **Accept external validation as an extension; do not make humans an unconditional requirement.** | Human resemblance judgments or an independent style representation could support an artistic interpretation. The current paper expressly declines that interpretation. R2 makes this distinction most clearly; R1 also explicitly says a human study is not mandatory for every finite feature-space audit. |
| R1 §3.8; R2 §10; R3 §12 | **Accept.** | Public vectors reproduce calculations, but cannot independently verify painting-region handling or extract another representation. Supply exact permissible image inputs or a demonstrated recovery route and a dedicated versioned release. Local availability of raw bytes does not resolve public reproducibility. |
| R1 §3.8 | **Accept provenance documentation; reject assuming labels are false.** | A historical interface accepted an invented identifier. The current experiment uses repaired explicit routes and carefully labels request configurations. There is no evidence here establishing that current model identities are wrong. |
| All reviews on novelty | **Accept limited novelty; reject a dataset-size dismissal.** | Artist-name substitutions, recognition, style descriptors and independent-partition distances have precedents. The controlled combination and concrete empirical disagreements are the contribution. A 110-artist recognition benchmark does not automatically answer this four-painter contrast question. |
| R2 §10; R3 §§13–16 | **Partly accept editorial emphasis; some requests are already implemented.** | Artist-pair results already have a main-results subsection and Figure 2, and historical cohorts are already in the appendix. Further emphasis or compression is editorial work, not a missing analysis. |
| All venue verdicts; R3 numerical scores | **Treat as judgment, not evidence.** | “Weak reject,” “weak accept,” and 4.5/10 or 8/10 are not calibrated forecasts of publication. They convey reviewer priorities, not experimentally established defects or readiness. |

## Additional checks performed for this assessment

**The cosine criticism is real, but does not overturn the common-direction
result.** In `shared_diagnostics`, both repeat-averaged differences subtract
the same free-arm estimate. Under independent arm errors,
E[g_hat dot c_hat] = g dot c + tr(Sigma_free). This justifies checking the
statistic; it does not determine the direction or magnitude of the cosine
ratio's bias, because the norms are noisy too.

I calculated the review's symmetric cross-repeat numerator and cross-repeat
squared norms, preserving the original global scene averaging:

| Configuration | Reported plug-in cosine | Cross-repeat alignment ratio |
| --- | ---: | ---: |
| GPT Image 1 | 0.693 | 0.689 |
| GPT Image 2 | 0.769 | 0.774 |
| GPT Image 2.5 Flare | 0.765 | 0.766 |
| GPT Image 2.5 Sunburst | 0.832 | 0.837 |
| Nano Banana 2 | 0.857 | 0.930 |
| FLUX.2 Max | 0.888 | 0.916 |

Both estimated norm squares are positive for every model. Every ratio remains
positive under each single-scene deletion. These are descriptive checks,
not new confidence intervals. The corrected ratio is not itself an unbiased
cosine and need not always lie in [-1, 1]. Accept R2's request to report it;
reject any stronger interpretation that the existing common response was
shown to be an artifact. R2 itself carefully avoids that claim. Primary D
does not use the free or generic arm, so this shared-control problem cannot
contaminate it through that route.

**Review 3 overstates what the wide genuine-painting control ranges establish.**
I reproduced all 1,000 original control draws exactly. For each unchanged split,
I also calculated the conditional expected score from the held-out pool's exact
means, keeping that split's training target and normalizer. This integrates
out the additional randomness of sampling two pseudo-outputs.

| Real control | Original central 95% range | Range of conditional expected scores |
| --- | ---: | ---: |
| Pooled works, pooled target | [-0.758, 1.380] | [0.135, 0.428] |
| Class-stratified works, pooled target | [-0.554, 2.400] | [0.544, 0.993] |
| Class-stratified works, class target | [-0.248, 1.946] | [0.517, 0.954] |

For the pooled control, the standard deviation falls from 0.561 to 0.076;
the residual sampling noise has SD 0.556. Substantial finite-pool disagreement
remains: the expected-score median is 0.236 for pooled controls and 0.706 for
class-specific controls. But much of the spectacular width is sparse sampling
noise. R3 §5's stronger attribution to unstable “ground-truth” geometry is
insufficiently discriminating. R2 §7's proposed separation is the better
diagnosis. These calculations still do not create an absolute artistic benchmark
or a direct test against the generated models.

**The calibrated ordering is not driven by just one scene in this panel.**
GPT Image 2 has lower calibrated error than FLUX in 12 of 14 held-out scene
scores. Their mean difference is -0.160. Deleting each scene in turn and
refitting the entire calibration procedure on the remaining panel gives
differences from -0.189 to -0.137. This addresses the narrow concern about
single-scene leverage. It does not establish superiority on unseen scenes,
an independent reference collection, or human judgments. It also does not
treat the 14 overlapping folds as independent binomial trials.

**R2's noise-power arithmetic checks out.** Using the published definition of
within-scene repeat variance and H = 5.915007, the estimated centered
single-repeat noise powers are 1.896, 0.969, 0.436, 0.535, 2.666 and 1.570
in the model order above. These assume independent errors across artist arms.
They support broader simulation scenarios, not a conclusion that the actual
simultaneous intervals fail. R3's blanket advice to do no more statistical
diagnostics is therefore too strong; R2 identifies specific inexpensive gaps.

## Points to push back on precisely

1. **Human validation is necessary for a claim of perceptual fidelity, not
   for every claim about measured image statistics.** Do not claim that a
   disclaimer makes all validation irrelevant: the actual calibration strips
   still require investigation. But do not let an optional broader scientific
   objective replace the paper's stated objective without making that choice
   explicit. R3's stronger acceptance requirement is a venue/contribution
   preference, not proof that the present calculation is meaningless.

2. **Different point orderings do not refute each other.** Raw D, aggregate D
   and calibrated D answer different questions. The uncalibrated endpoint
   legitimately includes amplitude. A shrinkage-adjusted score is not
   automatically the correct artistic metric. No observed reversal establishes
   a statistically significant rank reversal between GPT Image 2 and FLUX.

3. **Do not infer perceptual Monet–Sisley failure or an art-historical mechanism.**
   R3's hierarchy hypothesis is sensible as future work, as that reviewer partly
   acknowledges. The current results show weak alignment along measured pair
   differences, not inability of humans to distinguish the images, nor how the
   model internally organizes artists. Likewise, R3 §15's “wins” and “essentially
   fail” wording is stronger than the descriptive evidence warrants.

4. **Do not treat 0.438H as an identified causal content contribution.** The
   class-specific means differ from the pooled means, but the quantity includes
   finite-sample estimation, erroneous labels and potentially different capture
   sources. R3 §6's “directly confirms” formulation is too strong if interpreted
   as isolating subject composition. Its example of eight Monet route works
   also does not describe the 11-scene conditional comparison: that comparison
   uses water, built and land, and excludes the route class.

5. **Separate image defects from labeling defects.** Calibration strips can
   directly affect primary features and pooled D. The known water-class mistake
   affects class-based targets and their interpretation; the primary pooled
   target does not use those class labels. Neither two displayed strips nor
   one wrong label estimates collection-wide prevalence or establishes that
   the FLUX comparisons will reverse after correction.

6. **A frozen analysis can be supplemented.** Preserve the original evidence,
   but add an objectively specified retrospective correction. Correcting
   non-painting regions while retaining works is useful; simply excluding all
   flagged works can change artist/content/source composition and needs its
   own sensitivity interpretation. For development-panel defects, distinguish
   changes to reference means from changes to feature scaling.

7. **Suggested sample sizes are illustrations, not justified requirements.**
   “100–200 pairs” and “8–10 repeats” need precision and sampling calculations.
   Human ratings should match the statistic's unit of analysis and account
   for repeated raters, images and scenes. Hundreds of judgments do not create
   hundreds of independent observations of six model-level scores.

## Recommended response

Accept a versioned reference-quality audit and its impact analysis first.
Document objective region/label rules, apply them without optimizing model
results, cover both reference and development panels, and compare original and
corrected beta, D, artist-pair findings and calibration. Improve access to the
exact image inputs alongside this work.

Accept the bounded statistical requests: report cross-repeat generic/common
alignment; distinguish split variation from two-work control noise; show
calibration stability; and broaden the simulation stress range if relying on
it to support interval behavior. This assessment provides preliminary checks,
not a replacement for versioned manuscript analyses.

Keep uneven measured artist coverage and the separation of response strength
from target agreement central. The paper already presents both. Avoid promoting
post-result observations into prespecified hypotheses or replacing one
leaderboard with another.

Choose human or learned-style validation if the intended contribution includes
perceptual artist resemblance. It would strengthen the work considerably, but
is a separate research decision. Do not add generators, features or diagnostic
tables solely to satisfy all three lists. Do not treat their numerical review
scores as publication-readiness evidence.

## Evidence and verification

Read the complete canonical LaTeX manuscript and included results/appendix,
all three reviews, protocols, architecture, current status, core estimator,
measurement reader and diagnostic implementation. Inspected PDF pages 18–19
visually; the two calibration strips and the Cézanne street depiction are
visible. No full 649-image audit, new generation, feature re-extraction or human
evaluation was performed.

`make specificity-check review-check` passed: all four primary/target/window
views and the post-result diagnostics replayed exactly, and the review
presentation verified. The targeted estimator, diagnostic and measurement
tests passed: **17 tests**. Software replay checks consistency, not artistic
validity.

The additional checks are retained in
[assessment_v1/check_claims.py](assessment_v1/check_claims.py) and
[assessment_v1/checks.json](assessment_v1/checks.json), with source commit and
hashes. Run from the repository root:

```bash
uv run --locked python critics/assessment_v1/check_claims.py
```

Key local evidence:

- [Manuscript](../paper/paper.tex): scope, estimands, limitations and availability.
- [Results](../paper/specificity_results.tex): artist pairs already in the main text.
- [Diagnostic appendix](../paper/specificity_review_appendix.tex): controls and assumptions.
- [Primary geometry and shared diagnostics](../src/latent_art_bench/painter_specificity_v1/analysis.py).
- [Post-result implementation](../src/latent_art_bench/painter_specificity_review_v1.py).

External precedents checked against primary sources:

- Su et al.'s [prompted-artist recognition paper](https://arxiv.org/html/2507.18633v1)
  does report 1.95 million images, 110 artists and shared-content artist-name
  substitutions. It studies prompted-artist identification, and distinguishes
  that task from recognizing styles in real artwork.
- Somepalli et al.'s [style-descriptor paper](https://arxiv.org/abs/2404.01292)
  establishes learned style descriptors, retrieval and attribution as prior work.
- Diedrichsen and Kriegeskorte's [representational-analysis paper](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1005508)
  explicitly discusses independent-partition inner products for unbiased distance
  estimation and distinctions between representational structure and scale.
- Parmar et al.'s [image-processing evaluation paper](https://arxiv.org/abs/2104.11222)
  supports processing sensitivity as a general concern; it does not quantify
  calibration-strip effects in this project's collection.

These sources support the reviews' limited-novelty assessment, not an assertion
that this exact experiment has already been done or that its contribution is zero.
