# Second Review Report

## Recommendation

**Current recommendation: Borderline / Weak Reject for a strong main-track ML/CV venue. Weak Accept for a specialized generative-model evaluation, computational aesthetics, or workshop venue.**

**Score: approximately 5/10 to 6/10 depending on venue.**

This is a substantial improvement over the previous version. Several concerns that previously looked like missing analyses are now directly addressed. I would no longer criticize the paper for conflating artist-response magnitude with fidelity, treating the aggregate slope as evidence that all four artists are recovered, or failing to examine whether the model ranking is driven by response calibration. Those issues are now handled unusually explicitly.

My remaining objection is more fundamental:

**The paper has become quite convincing about what its metric measures, but the metric itself is not sufficiently validated as a measure of artist-specific visual recovery.**

Importantly, the revised manuscript now says essentially the same thing. That intellectual restraint helps considerably. The question for acceptance is therefore whether a careful demonstration of this narrower evaluation phenomenon is itself a sufficient contribution.

---

# 1. What changed relative to the previous version

The revision directly addressed most of my earlier concrete requests.

| Previous concern                                                   | Revision                                                                              | Assessment                      |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------- | ------------------------------- |
| Aggregate \(\beta\) might be driven by only one artist distinction | Six artist-pair diagnostics, singular components, artist omission, label permutations | **Substantially resolved**      |
| \(D\) confounds direction and response magnitude                   | \(Q\), normalized alignment, and held-scene scalar calibration                        | **Substantially resolved**      |
| Scene variation can be mistaken for error                          | \(D_{\rm aggregate}+V_{\rm scene}\) decomposition                                     | **Resolved conceptually**       |
| Content mixture in references                                      | Class-specific targets + genuine-reference controls                                   | **Improved, not resolved**      |
| Equal feature weighting arbitrary                                  | Equal-family and covariance-weighted sensitivity                                      | **Improved**                    |
| Common fraction might be an artifact of global averaging           | Within-scene common/specific decomposition                                            | **Resolved for that objection** |
| Uncertainty procedure insufficiently checked                       | Synthetic coverage simulations including assumption violations                        | **Improved substantially**      |
| No qualitative inspection                                          | Deterministically selected generated/reference examples                               | **Improved**                    |
| Full reproducibility unavailable                                   | Still unavailable at image-measurement level                                          | **Not resolved**                |
| No perceptual/art-historical validation                            | Still absent                                                                          | **Not resolved**                |

The revision is therefore not cosmetic.

---

# 2. The strongest improvement: the paper now exposes rather than hides the fragility of the aggregate result

This is probably the most scientifically valuable addition.

The earlier manuscript established that all six models have positive aggregate reference-aligned slopes. A skeptical reader could reasonably ask whether this was really “four-artist recovery,” or whether one large contrast drove the result.

The new analysis answers that question—and the answer is revealing.

The three nonzero reference components explain approximately

$$
66.3\%,\quad 20.6\%,\quad 13.0\%
$$

of the reference centroid variation. Every model responds more strongly to the dominant component than to the other two. Even more importantly, leaving Cézanne out changes FLUX's slope from

$$
0.470 \rightarrow 0.096,
$$

and GPT Image 2 from

$$
0.999 \rightarrow 0.651.
$$

Several Monet–Sisley slopes are almost zero or negative:

* GPT Image 1: 0.074
* Flare: −0.011
* Sunburst: −0.249
* Nano Banana 2: −0.044
* FLUX: 0.129
* GPT Image 2: 0.402

This materially changes the interpretation.

The strongest defensible statement is no longer:

> Current models reproduce the relative differences among these four painters.

It is closer to:

> Current models exhibit a statistically detectable aggregate alignment with the reference artist configuration, but this alignment is highly uneven across artist distinctions and is partly dominated by the strongest reference contrast.

That is much more precise.

I regard the inclusion of these results as a major strength.

There is also an excellent label-permutation diagnostic. The correct assignment gives the minimum error for GPT Image 1, GPT Image 2, and FLUX, but only the second-best error for Flare, Sunburst, and Nano Banana 2; for those models, swapping Monet and Sisley improves the point estimate.

That is exactly the kind of adversarial check this paper needed.

---

# 3. The response-calibration analysis substantially changes the meaning of the model ranking

This addition is also important.

The revised paper makes explicit the identity

$$
D = 1 - 2\beta + Q,
$$

where \(Q\) measures corrected generated contrast magnitude. This cleanly shows that \(D\) depends jointly on alignment and response strength.

The new table is particularly informative:

| Model         | \(D_{\rm aggregate}\) | \(V_{\rm scene}\) | \(Q\) | \(\beta/\sqrt Q\) | held-scene calibrated \(D\) |
| ------------- | --------------------: | ----------------: | ----: | ----------------: | --------------------------: |
| GPT Image 1   |                 1.239 |              .333 | 2.449 |              .600 |                        .645 |
| GPT Image 2   |                 1.044 |              .182 | 2.223 |          **.670** |                    **.554** |
| Flare         |                 1.483 |              .255 | 2.281 |              .511 |                        .741 |
| Sunburst      |                 1.337 |              .305 | 2.289 |              .545 |                        .706 |
| Nano Banana 2 |              **.723** |              .387 |  .994 |              .444 |                        .832 |
| FLUX          |                  .761 |          **.040** |  .741 |              .546 |                        .714 |

This produces two important results.

First, Nano Banana has lower aggregate mismatch than FLUX but much larger scene variation. FLUX wins on the original scene-conditional endpoint because it behaves more consistently across scenes.

Second, once only a scalar response magnitude is estimated on the other 13 scenes and evaluated on the held-out scene, **GPT Image 2 obtains the lowest point estimate, not FLUX**.

This validates one of the core objections from my previous review: the uncalibrated \(D\) ranking is partly a calibration ranking.

The paper handles this correctly. It does not replace the preregistered endpoint after observing the result and does not claim that rescaled feature vectors correspond to realizable images.

My recommendation would now be to make this even more central.

The paper is more interesting as:

> “Different reasonable decompositions of artist-name response produce different model orderings.”

than as:

> “FLUX performs better than two GPT Image variants.”

The former is a general evaluation insight. The latter is contingent and comparatively fragile.

---

# 4. The largest unresolved problem remains construct validity

This is still the main reason I would hesitate to accept the paper in a strong main track.

The paper wants to evaluate whether artist names produce differences corresponding to historical painters. But the reference target is constructed from uncontrolled digital reproductions.

The revised manuscript now provides direct evidence that this is not an abstract concern.

The deterministic reference examples reveal:

* calibration strips retained in at least the displayed Sisley reproduction;
* calibration strips retained in the displayed Pissarro reproduction;
* a Cézanne street scene categorized as “water-organized” by the title-derived classifier;
* no painting-region mask in the primary measurement pipeline.

This is simultaneously a strength of the revision and a serious problem for the underlying measurement.

The authors deserve credit for showing these examples rather than silently correcting them after seeing the results. But the consequence is unavoidable:

**some portion of the reference artist geometry may describe digitization practices, borders, institutional capture conventions, or metadata artifacts rather than painter characteristics.**

The manuscript now states this clearly.

However, acknowledgement does not validate the endpoint.

If Sisley files systematically contain different borders, calibration targets, sharpening, resolution histories, or color pipelines than Monet files, the model is being evaluated partly on whether its generated images reproduce those acquisition artifacts.

No amount of statistical correction to \(D\) solves that.

---

# 5. The genuine-painting controls are useful, but they actually weaken absolute interpretation

The new real/reference controls are a good idea.

Using disjoint reference halves, the reported median corrected errors are approximately:

* pooled sampling: **0.233**
* class-stratified sampling against pooled target: **0.721**
* class-stratified sampling against class-specific target: **0.702**

with very broad central ranges, for example approximately

$$
[-0.758, 1.380]
$$

for the pooled condition.

These experiments demonstrate two things.

First, the metric can indeed assign low error to genuine artworks when content is favorable.

Second—and more importantly—the apparent “ground-truth” geometry itself is unstable under finite reference sampling and content stratification.

This makes statements such as

$$
D=0.801
$$

difficult to interpret absolutely.

Is .801 bad?

The revised paper correctly concludes that the current experiment cannot answer that question.

This is a major improvement over the previous version.

But there is a subtle issue with using these controls as validation: the target in each simulation is estimated from only a half-reference sample, whereas the generated models are compared against the full 649-image target. Thus part of the genuine-control spread comes from target estimation error that the model evaluations do not experience. The manuscript acknowledges that training-target estimation contributes to the spread and explicitly avoids treating the distributions as direct tests.

That is statistically responsible.

It also means these controls are better described as **reference-stability diagnostics** than as a calibrated real-art benchmark.

---

# 6. Content confounding is better characterized but not solved

The class-specific analysis is useful.

The paper reports that reference class-specific artist configurations differ from the pooled target by average squared distance

$$
0.438H.
$$

That is not small.

This directly confirms my earlier concern that subject composition contributes materially to the artist geometry.

FLUX remains the lowest point estimate when the 11 unambiguously designated water/built/land generated briefs are compared with corresponding class-specific targets. That is reassuring for the specific model ordering.

But the content classes remain extremely coarse and metadata-derived.

The counts are also highly imbalanced—for example, only eight Monet works fall in the route class, while 191 fall in the water class.

Most importantly, a water painting by Monet and a water painting by Cézanne are not thereby composition-matched.

They may differ systematically in:

* horizon placement,
* fraction of water,
* architecture,
* vegetation,
* season,
* viewpoint,
* number of figures,
* time period,
* canvas dimensions,
* crop,
* painting medium and support,
* digitization source.

Therefore, the paper still cannot cleanly estimate

$$
\text{artist effect independent of depicted content}.
$$

The revised manuscript no longer pretends otherwise. That saves the claim, but it also narrows it.

---

# 7. The absence of human or independent perceptual validation is now the clearest missing experiment

At this stage I think this is the single highest-value experiment remaining.

The current literature already contains artist-prompt identification at far larger scale. Su et al. evaluate 1.95 million generated images over 110 artists and multiple T2I systems, including content-controlled substitutions.

Other work explicitly evaluates artistic replication using human judgments and aesthetic/style assessments.

The revised paper's novelty therefore does not come from showing that artist names leave distinguishable signatures.

It comes from showing that:

1. detectability,
2. reference alignment,
3. response strength,
4. scene invariance,
5. distributional proximity,

can disagree.

That is interesting.

But the paper still lacks evidence connecting its 31-dimensional disagreement to what competent observers call painter resemblance.

A relatively modest human study could transform the paper.

For example:

* 100–200 generated image pairs;
* blinded artist-identification or pairwise resemblance judgment;
* include both historical references and generated outputs;
* measure whether \(D\), pairwise \(\beta\), or the calibrated metric predicts human confusion;
* separately score scene adherence.

This need not become the primary metric.

It would provide **construct validation**.

Without it, the authors can show that the coordinates are mathematically well behaved but not that they measure the intended artistic phenomenon.

---

# 8. The artist-pair results raise a deeper conceptual question that deserves more emphasis

The new pairwise analysis is sufficiently important that I would move some of it from “diagnostics” into the core narrative.

Consider the Monet–Sisley result again.

For five of six systems, the slope is between roughly −0.25 and +0.13.

That suggests that much of the aggregate positive alignment is not “fine artist discrimination” at all.

Rather, the model may capture a broad axis such as:

$$
\text{Cézanne-like} \leftrightarrow \text{high-Impressionist-like},
$$

while struggling with distinctions among more closely related Impressionists.

This is potentially a stronger scientific result than the original ranking.

The fact that Cézanne omission collapses FLUX from .470 to .096 is especially informative.

I would explicitly formulate the hypothesis:

> Artist-name conditioning may recover coarse art-historical clusters before recovering within-cluster painter identity.

That hypothesis is supported only suggestively by four artists here, but it gives the findings a broader conceptual trajectory.

It would also motivate a natural next experiment involving hierarchical painter sets:

* very different movements,
* same movement,
* close contemporaries,
* artist periods,
* possibly teacher/student relationships.

That would be a more interesting continuation than simply adding more models.

---

# 9. The statistical treatment is now considerably stronger

I was skeptical of making too much inferentially from 14 scenes and two repeats.

The paper now explicitly simulates the exact six-model, 14-scene, two-repeat, 21-endpoint setting.

Under the three scenarios maintaining cross-repeat independence, family coverage is reported as:

* Gaussian: **95.96%**
* heavy-tailed/heteroskedastic: **97.42%**
* fixed artist-by-scene interaction: **99.68%**

Under a shared-state violation, coverage collapses to approximately:

$$
0.04\%.
$$

This is a very good diagnostic because it does not merely demonstrate favorable simulations. It deliberately constructs a failure mode and shows catastrophic failure.

My assessment therefore changes from:

> “The interval procedure is under-justified.”

to:

> “The interval procedure is internally reasonable conditional on repeat independence, but that assumption is empirically weakly identified with two repeats.”

That is a much narrower concern.

The remaining issue cannot be solved through further simulation. You need empirical evidence about repeat dependence.

A relatively small follow-up with, say, 8–10 repeats for a subset of models/scenes, temporally blocked across collection periods, would provide more useful information than another theoretical robustness check.

---

# 10. The shared-effect claim is now appropriately bounded

The revision adds two useful clarifications.

First, the common component remains enormous when computed scene-wise before global averaging:

$$
88.6\%-97.2\%.
$$

Therefore the previously observed 82.5–95.7% global fraction is not simply caused by cancellation of artist-specific responses across scenes.

Second, the manuscript now explicitly notes that centering removes a common additive shift \(b\), but not a common transformation:

$$
z \mapsto Az+b.
$$

After centering, \(b\) disappears while \(Ad\) remains.

That resolves an important wording problem in the old version.

I would consider my previous concern on this point essentially addressed.

---

# 11. Feature weighting is no longer an obvious Achilles heel, but validity remains open

The new diagnostics examine:

* equal-family weighting;
* covariance weighting based on the independent development panel;
* deletion of every individual coordinate;
* no-texture analysis;
* square-window measurements.

FLUX remains the minimum primary point estimate under these sensitivity analyses and under all 31 leave-one-coordinate-out checks.

This materially strengthens the claim that the main FLUX result is not produced by one accidental coordinate or by simply having more texture dimensions.

I therefore withdraw the strong version of my previous feature-weighting objection.

However:

**robustness across several arbitrary metrics does not establish that any of them is perceptually correct.**

The revised text handles this distinction properly.

---

# 12. Reproducibility remains incomplete

The repository engineering is strong.

The project now retains:

* exact protocols,
* prompts,
* request assignments,
* scalers,
* compact measurements,
* hashes,
* post-result diagnostics,
* fixed-rule visual examples,
* replay code.

The source explicitly distinguishes confirmatory results from review-driven post-result diagnostics.

This is unusually careful.

However, the paper still states that:

* full-resolution generated images are not in the compact package;
* public replay begins from feature vectors;
* feature extraction cannot be independently reproduced from the public package;
* the newest experiment is not yet archived as an immutable release.

This remains a publication issue.

For a paper whose central scientific uncertainty concerns **whether the image measurement is valid**, releasing only the downstream vectors is especially limiting.

I would strongly recommend making permissible generated pixels available before submission or camera-ready.

---

# 13. A new problem created by the improved revision: the paper risks becoming too defensive

The revision is scientifically better, but structurally there is now a lot happening:

* primary geometry,
* generic controls,
* energy distance,
* variance,
* artist pairs,
* SVD components,
* permutations,
* artist omissions,
* global-vs-scene decomposition,
* scalar calibration,
* content targets,
* real controls,
* family weighting,
* covariance metrics,
* coordinate deletion,
* corrected energy,
* simulations,
* palette experiments,
* historical transformation maps.

This is impressive, but it risks making the manuscript feel like an accumulation of responses to every conceivable objection.

The paper's most compelling story is actually simpler:

### Question 1

Does changing the artist name produce a common painting response?

**Yes, overwhelmingly.**

### Question 2

Is there artist-specific signal beyond it?

**Yes, in aggregate.**

### Question 3

Does that imply faithful artist recovery?

**No. Pairwise distinctions are uneven, magnitude matters, scene dependence matters, and the reference itself is unstable.**

That three-stage argument is strong.

Everything else should support it.

I would move more historical cohorts and several lower-priority diagnostics into the supplement.

---

# 14. I would change the emphasis of the title and contribution slightly

The new title,

> **Artist-Name Responses beyond a Shared Painting Effect in Text-to-Image Generation**

is better than the previous wording because it avoids equating the endpoint with painter fidelity.

That is the correct direction.

I would lean into it even more.

The paper's strongest contribution is arguably an evaluation lesson:

> **Detectable artist conditioning is not equivalent to artist recovery.**

The ranking among six particular 2026 models should be secondary evidence.

This would also make the work more durable as specific commercial models change.

---

# 15. Novelty after revision

My novelty assessment has improved slightly.

Su et al. already establish artist-name recognizability at large scale using controlled prompting across multiple generators. Their benchmark contains 1.95M images and 110 artists.

Therefore, “artist names produce identifiable signatures” is not novel.

The novel part here is the decomposition:

$$
\text{name effect}
\neq
\text{reference alignment}
\neq
\text{correct amplitude}
\neq
\text{low conditional error}
\neq
\text{distribution matching}.
$$

The revised paper now demonstrates these separations empirically rather than merely defining them.

In particular:

* GPT Image 2 has near-unit aggregate amplitude but substantial residual error.
* FLUX has lower original \(D\) despite weaker amplitude.
* GPT Image 2 wins the post-hoc held-scene scalar-calibrated comparison.
* Nano Banana beats FLUX in aggregate \(D\) but loses because of scene variation.
* several models essentially fail Monet–Sisley alignment.
* the correct artist assignment is not even the lowest-error permutation for half the models.

Taken together, these results make a persuasive case that one-dimensional evaluations of “style imitation” are inadequate.

That is a legitimate contribution.

---

# 16. Specific technical issues I would still request before acceptance

## Major revision 1 — Add external construct validation

This is now the single most important missing piece.

Either:

* human painter-resemblance judgments, or
* an independently developed style representation, preferably with known human correlation,

should be compared to the proposed diagnostics.

Human evaluation is preferable.

## Major revision 2 — Audit and cleanly quantify reference-image contamination

You have now shown concrete calibration-strip and metadata failures.

Do not silently remove them from the primary analysis.

Instead, conduct a **predefined diagnostic audit** of the 649 reference files:

* border/frame presence,
* calibration strip presence,
* grayscale charts,
* large text/labels,
* obvious metadata-content mismatch,
* museum background,
* non-painting regions.

Report prevalence by artist.

Then run a transparent sensitivity excluding objectively flagged files.

This could materially strengthen or materially alter the geometry; either outcome is informative.

## Major revision 3 — Make the coarse-vs-fine artist distinction a first-class result

The Cézanne omission and Monet–Sisley results are too important to bury.

I would make this one of the paper's primary empirical findings.

## Major revision 4 — Release enough image-level data to reproduce feature extraction

Without this, independent verification stops exactly before the most scientifically disputed step.

## Minor revision 1 — Reduce emphasis on FLUX versus GPT 2.5

Those two adjusted pairwise comparisons are statistically legitimate under the declared analysis, but the calibration analysis shows how endpoint-dependent that ranking is.

Keep them, but do not make them the centerpiece.

## Minor revision 2 — Clarify “reference component”

Because the stacked four-artist configuration has rank three, readers may confuse the dominant SVD component with a particular artist axis. Explain visually what each component corresponds to.

## Minor revision 3 — Report uncertainty around the calibrated ordering

I agree with not turning post-hoc diagnostics into a second confirmatory test.

Still, descriptive fold distributions for \(D_{\rm held}\) would help readers see whether .554 versus .714 is widespread across scenes or driven by a few folds.

---

# 17. Updated scoring

### Technical correctness: 8/10

I do not see a major mathematical defect in the core estimator. The new diagnostics are thoughtfully designed and unusually transparent about their limitations.

### Experimental design: 7/10

The controlled prompt design is strong. Fixed common scenes and independent repeated requests are appropriate. The main weakness lies in the historical reference side, not the generated side.

### Statistical methodology: 7.5/10

Good paired-scene reasoning, explicit multiplicity, cross-repeat correction, and now useful synthetic stress testing. Remaining uncertainty centers on empirically unverified repeat independence and the small number of scene clusters.

### Construct validity: 4.5/10

Still the central weakness. The revision identifies rather than solves it.

### Novelty: 6/10

The individual ingredients are not novel, but their combination and the empirical demonstration that common response, recognition, alignment, magnitude and recovery disagree is useful.

### Reproducibility: 6.5/10

Excellent numerical provenance; incomplete image-level reproducibility.

### Clarity / scientific honesty: 9/10

The new manuscript is remarkably explicit about what it cannot conclude. This is substantially better than the previous version.

---

# 18. Updated verdict

My previous assessment was roughly:

> “Interesting metric and sound estimator, but insufficiently validated to support the claimed artist-recovery interpretation.”

My revised assessment is:

> **“A technically careful and now unusually self-critical study showing that artist-name conditioning, contrast strength and reference-relative agreement are distinct phenomena. The primary numerical claims are credible as collection-relative measurements. However, the paper still lacks sufficient evidence that the collection-relative geometry corresponds to perceptually meaningful artist fidelity.”**

That is a meaningful improvement.

For a specialized venue, I would now lean **weak accept** because the evaluation lesson is useful even without solving artistic fidelity.

For a strong CV/ML main conference, I remain at **borderline / weak reject**, principally because the missing human/external validation lies directly between the metric and the phenomenon named in the research question.

The most important point is that I would **not recommend spending the next iteration on more statistical diagnostics**. You have reached diminishing returns there.

The next evidence should come from outside the existing 31-dimensional closed loop:

1. human judgments,
2. systematic reference-image audit,
3. externally validated style representation,
4. image-level reproducibility.

If those agree with the principal qualitative conclusions, I would be considerably more comfortable moving to **weak accept / accept**.

# One-sentence reviewer summary

**The revision successfully turns most earlier methodological objections into measured, transparent qualifications; the remaining bottleneck is no longer statistical technique but whether the measured reference geometry is genuinely a valid proxy for artist-specific visual fidelity.**
