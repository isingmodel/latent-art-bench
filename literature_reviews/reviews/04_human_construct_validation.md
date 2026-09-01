# Human construct validation for a painter-associated feature

Review depth: 18 primary empirical or methodological sources spanning style perception,
experimental aesthetics, psychometrics, paired/triplet judgments, measurement invariance, and
crossed-participant/stimulus uncertainty

Question: how can human evidence establish that a qualified image representation measures a
painter-associated visual signature across works, rather than subject matter, period, source,
technical quality, familiarity, liking, or an evaluator group's preferred vocabulary?

## 1. Conclusion

There is no human gold-standard label for “the amount of painter” in an image. Construct validity
must accumulate through a network of preregistered evidence. For this project, the central evidence
is not whether people like an image or can name an artist. It is whether blinded observers perceive
a recurring manner across held physical works by the target painter, distinguish it from matched
non-target painters when content and reproduction cues conflict, and produce relations that a
qualified computational representation predicts without merely predicting content, source, image
quality, or liking.

The human study should be built in two stages:

1. **Instrument calibration on real works.** Establish painter specificity, within-painter
   variability, reproduction stability, convergent evidence, discriminant evidence, and evaluator-
   group scope using held real works never used to select or tune the features.
2. **Application to generated images.** Only after calibration, apply the frozen instrument to
   blinded, paired generated outputs. Estimate painter resemblance and content preservation
   separately, with prompts, seeds, output images, and raters represented in the uncertainty.

Experts and nonexperts are both informative but answer different population questions. Neither
group should be silently pooled and neither should be treated as truth by title alone. Pair and
triplet choices reduce dependence on verbal scales, but they do not make content, familiarity,
display, or stimulus sampling disappear.

## 2. Construct map and claim boundaries

The intended construct is:

> **Painter-associated visual signature:** a recurring, perceptible organization of color and
> spatial structure that is shared across multiple held physical works by a specified painter,
> allowing legitimate within-painter variation and remaining distinguishable from matched painters
> after source, content/genre, medium/support, date, and reproduction are controlled.

This is not synonymous with painter identity, authenticity, historical intent, technical skill,
beauty, preference, generic “art style,” period, school, or literal material hand. A study may find
a continuous painter-associated resemblance without supporting categorical attribution.

### 2.1 Nomological predictions

Before data collection, the protocol should commit to the following directional predictions:

- held works by the same target painter are judged more similar in **manner of depiction** than
  matched target-versus-non-target works;
- that advantage survives different-source and content-matched trials and does not reverse in
  source-cue-conflict trials;
- independent reproductions of one physical work elicit equivalent painter-manner relations within
  a prespecified margin;
- a qualified computational painter-distance matrix converges with a human painter-manner distance
  matrix on held works and independent reproductions;
- painter-manner judgments discriminate from subject/content similarity, reproduction quality,
  source recognition, familiarity, liking, and generic aesthetic quality; and
- any claimed common human construct is sufficiently invariant across prespecified evaluator and
  presentation groups; otherwise the result is reported as group- or display-specific.

Within-painter variability is part of the construct. The target is not “all target works look the
same.” It is that the distribution has reproducible structure and useful separation from declared
hard neighbors over a stated domain.

## 3. What Pilot 2 did not validate

Pilot 2 supplied no human construct evidence because its generated primary cells were incomplete
and its planned primary comparisons were not run. The real-work atlas showed source balanced
accuracy 0.8125, while painter cross-source transfer was chance or weak (NGA-to-AIC 0.25;
AIC-to-NGA 0.375). A source-stratified permutation result did not establish that people perceive
the A-vector as painter manner.

The prospective human study must therefore not start by asking whether generated images “look like
Monet” in an unconstrained survey. Such a task can reward water lilies, pastel colors, a familiar
composition, a museum's reproduction palette, or name priming. It must first demonstrate on real
works that the instrument recognizes the target across works and sources when shortcuts are placed
in opposition.

## 4. Source-verified evidence and disposition

### 4.1 Direct evidence about perceived style and art reproductions

| Source | Method and evidence | Assumptions and limitations | Prospective disposition |
|---|---|---|---|
| [Zhao et al. 2023, *Zooming in on style: Exploring style perception using details of paintings*](https://doi.org/10.1167/jov.23.6.2) | Forty-eight apple details from 42 oil paintings were judged in similarity triplets by 415 online participants; landmark MDS recovered a structured three-dimensional perceptual space. A second experiment with 224 participants related it to texture/brushstroke coarseness, smoothness, hue, chroma, and other attributes. | One recurring motif, mostly Western paintings, online display, and overwhelmingly North American participation; crop-level style omits composition. | Strongest design precedent for content-controlled, vocabulary-light triplets. Use several recurring motifs and whole-work/crop branches; do not assume one style space is painter-specific or culturally invariant. |
| [Boger & Firestone 2025, *The psychophysics of style*](https://doi.org/10.1038/s41562-025-02249-8) | Ten preregistered experiments with naturalistic and synthetic stimuli found style tuning, discounting, and extrapolation; grayscale/luminance and image-similarity controls showed that observers can partly parse manner from represented content. | Synthetic transformations and online tasks simplify art-historical painter variation; perceptual style is broader than painter signature. | Justifies cue-conflict and transfer tests, not a single “style” score. Include grayscale or color-controlled sensitivity only as diagnostics because color may be genuine painter information. |
| [Reymond et al. 2020, *Aesthetic Evaluation of Digitally Reproduced Art Images*](https://doi.org/10.3389/fpsyg.2020.615575) | Seventy-five art-expert participants and 72 less-experienced participants viewed 16 Impressionist/Expressionist reproductions with original-like versus increased saturation at 100 ms and unrestricted durations. Saturation had small liking effects but affected specific reactions differently by expertise; experts revised judgments more with time. | Quasi-experimental expert groups; liking/emotion rather than painter recognition; online/device conditions and 16 works limit scope. | Predefine expertise strata and viewing regime. Measure reproduction surface effects separately from painter manner; liking cannot substitute for construct validity. |
| [Nascimento et al. 2017, *The colors of paintings and viewers' preferences*](https://doi.org/10.1016/j.visres.2016.11.006) | Fifty naive observers adjusted rotations of the three-dimensional color gamut for ten paintings; preferred orientations were close to the original but varied by painting. | Preference, not painter specificity; ten works and one manipulation family. | Color relations are perceptually consequential, but “preferred” is not “painter-like.” Keep painter-manner and liking questions in separate trials. |
| [Locher, Smith & Smith 1999, *Original paintings versus slide and computer reproductions: A comparison of viewer responses*](https://doi.org/10.2190/R1WN-TAF2-376D-EFUH) | Museum visitors evaluated nine works as originals, projected slides, or computer images on physical/structural, content, and aesthetic dimensions; some pictorial relations survived presentation format. | Nine works, older display technology, and different viewing contexts; perceptual sameness is not metric invariance. | Include reproduction as an experimental facet. Do not infer that current web files are interchangeable merely because viewers can adapt to a medium. |
| [Iigaya et al. 2021, *Aesthetic preference for art can be predicted from a mixture of low- and high-level visual features*](https://doi.org/10.1038/s41562-021-01124-6) | Large laboratory and online rating datasets showed that both image statistics and annotated higher-level properties contributed to individual aesthetic preference. | The endpoint is liking; feature annotations and model selection can share stimulus structure. | Use liking and generic aesthetic quality as discriminant variables. A coordinate that predicts liking may still fail painter-manner validation. |

### 4.2 Human evaluation of style-transfer systems

| Source | Method and evidence | Assumptions and limitations | Prospective disposition |
|---|---|---|---|
| [Yeh et al. 2020, *Improving Style Transfer with Calibrated Metrics*](https://doi.org/10.1109/WACV45572.2020.9093351) | Separate Effectiveness and Coherence statistics were calibrated with human pairwise preferences; methods occupied a trade-off frontier, and much variability was attributable to the style stimulus. | Neural style transfer and method-level comparison; one reference style image is not a painter distribution. | Separate painter resemblance from content preservation. Sample many reference works and estimate reference-work variability instead of selecting flattering examples. |
| [Wright & Ommer 2022, *ArtFID: Quantitative Evaluation of Neural Style Transfer*](https://doi.org/10.1007/978-3-031-16788-1_34) | Thirteen style-transfer methods were compared in 31,200 crowdsourced pairwise tasks; each comparison received five votes and method rankings were modeled from head-to-head outcomes. ArtFID combined art-domain style and content terms. | Primarily ranks methods, not individual target-painter fidelity; majority votes do not address crossed rater/stimulus uncertainty, and metric assumptions remain. | Useful pairwise interface precedent. Retain image-level, prompt-level, work-level, and rater-level data; never replace uncertainty with majority winners or a single method rank. |

### 4.3 Construct validity and measurement invariance

| Source | Methodological contribution | Limitation | Prospective disposition |
|---|---|---|---|
| [Cronbach & Meehl 1955, *Construct validity in psychological tests*](https://doi.org/10.1037/h0040957) | A construct without a definitive criterion is validated through explicit theory and a nomological network of predicted relations. | General psychometric framework, not an art protocol. | Define the painter construct and falsifiers before choosing outcomes; no single accuracy, correlation, or expert opinion can “prove” it. |
| [Campbell & Fiske 1959, *Convergent and discriminant validation by the multitrait-multimethod matrix*](https://doi.org/10.1037/h0046016) | Same-trait relations measured by different methods should exceed different-trait relations, including those sharing a method. | Classical correlation matrix assumes suitable, sufficiently reliable scores. | Cross painter-manner, content, color, quality, and liking traits with triplet, pair, rating, computational, and reproduction methods. Test method effects explicitly. |
| [Messick 1995, *Validity of psychological assessment*](https://doi.org/10.1037/0003-066X.50.9.741) | Validity concerns the interpretation and use of scores and integrates content, substantive, structural, generalizability, external, and consequential evidence. | Broad assessment argument; does not prescribe one estimator. | Validate the exact claim and decision. A representation may be valid for ranking reproduction similarity and invalid for claiming painter hand or evaluating generations. |
| [Flake, Pek & Hehman 2017, *Construct validation in social and personality research*](https://doi.org/10.1177/1948550617693063) | Empirical audit and recommendations distinguish substantive, structural, and external phases; reliability alone was often misused as sufficient validation. | Focuses on questionnaire-based behavioral research. | Maintain a construct-to-item/task table, evaluate task structure, then seek external convergence/discrimination. Do not report agreement alone as validity. |
| [Meredith 1993, *Measurement invariance, factor analysis and factorial invariance*](https://doi.org/10.1007/BF02294825) | Formalizes levels of factorial invariance needed before interpreting observed group-score differences as latent differences rather than measurement change. | Developed for latent-variable/item models; forced choices need different group-comparison models. | Test item/trait-rating invariance across expertise/language/display. For pair/triplet tasks, use group-specific choice models and test group-by-stimulus relations instead of claiming CFA solves all invariance. |
| [Specker et al. 2020, *The Vienna Art Interest and Art Knowledge Questionnaire*](https://doi.org/10.1037/aca0000205) | Developed and validated separable measures of art interest and knowledge rather than relying only on self-described expertise. | General art interest/knowledge is not painter-specific attribution expertise. | Record formal role/training and a validated knowledge/interest measure; analyze painter-specific familiarity separately. Do not create expert status from one score. |

### 4.4 Paired-choice models and crossed uncertainty

| Source | Methodological contribution | Limitation | Prospective disposition |
|---|---|---|---|
| [Bradley & Terry 1952, *Rank analysis of incomplete block designs: I. The method of paired comparisons*](https://doi.org/10.2307/2334029) | Provides a probabilistic model for paired wins from latent item strengths and supports incomplete comparison designs. | Basic model assumes a particular log-odds structure and independent outcomes absent extensions. | Use a hierarchical extension with rater, work/image, prompt, and seed effects; diagnose transitivity and position effects. Do not analyze win percentages as independent binomial trials. |
| [Judd, Westfall & Kenny 2012, *Treating stimuli as a random factor in social psychology*](https://doi.org/10.1037/a0028347) | Demonstrates that inference that ignores sampled stimuli can be anti-conservative and recommends crossed participant/stimulus mixed models. | Examples are social-cognitive experiments, not art triplets. | Physical works and generated images are sampling units/factors. Model both participants and stimuli; extra votes on the same few works do not establish across-work generalization. |
| [Owen & Eckles 2012, *Bootstrapping data arrays of arbitrary order*](https://doi.org/10.1214/12-AOAS547) | Product reweighting across crossed factors gives a practical, typically mildly conservative variance estimator for large multiway data arrays. | Targets means and crossed random-effects structures; no exact bootstrap exists for every crossed design. | Use a multiway bootstrap as a robustness check over raters, physical works, prompts, and outputs, aligned with the actual estimand. |
| [Winkler et al. 2015, *Multi-level block permutation*](https://doi.org/10.1016/j.neuroimage.2015.05.092) | Develops restricted permutation for repeated and multilevel designs using exchangeability blocks. | Validity depends on the null and exchangeability structure; blocking cannot manufacture a crossed design. | Permute painter/condition labels only within prespecified work/source/content blocks allowed by the randomization. Never shuffle crops, votes, or files as if independent. |

## 5. Prospective human instrument

### 5.1 Stimulus frame

Calibrate the instrument using a held real-work panel that played no role in feature selection,
threshold selection, descriptor pruning, or exemplar choice. Each target painter is paired with
several historically and visually plausible non-target painters. Painter-source cells are crossed
or explicitly matched, and the panel includes declared strata for content/genre, medium/support,
date, tonal range, and whole-work versus recurring-motif crop.

Each physical work receives one primary reproduction and, for a balanced reliability panel, an
independent reproduction. All files are processed under the qualified digitization protocol.
Familiar canonical works are not banned silently: familiarity is measured, and a preregistered
sensitivity analysis excludes recognized works. Attribution labels, filenames, institutional marks,
captions, frames, and interfaces that reveal source are removed or masked by a frozen rule.

### 5.2 Task family A: vocabulary-light triplets

The primary calibration task uses an anchor (A) and candidates (B) and (C):

> Which candidate is closer to the anchor in the **manner of depiction**—how it is rendered—rather
> than what object or scene is shown?

The interface provides short, neutral practice examples but no painter names and no list of
supposed painter traits. Critical triplets include:

- same-painter versus matched non-target candidates with content matched;
- different-source target candidate versus same-source non-target candidate;
- same-painter candidates from different content/medium/date strata where supported;
- independent reproductions of the same physical work in counterbalanced positions; and
- negative-control triplets where content similarity and painter identity intentionally disagree.

A complementary unconstrained similarity-triplet block asks only which pair is most similar in
manner and supports a human representational distance matrix, following Zhao et al. It should use
several motifs and whole works; otherwise the construct is “style of painted apples,” not the
target painter across works.

### 5.3 Task family B: focused pairs

Pairs are easier to scale and are the primary form for later generated-image comparisons. Each
generated pair shares the prompt, seed or seed-allocation rule, model/version, aspect ratio, and
postprocessing. Evaluators are blinded to which output came from the named versus painter-free
condition. Separate randomized blocks ask:

1. which image is more consistent with the supplied **multi-work target-painter reference panel**;
2. which better preserves the requested subject/content;
3. which has fewer visible technical defects; and
4. which is preferred, as an explicitly secondary discriminant outcome.

Never combine those questions into “which is better?” Yeh et al. show why style effectiveness and
content coherence can trade off, while Reymond and Iigaya et al. show that surface appearance and
liking can move differently from the intended construct.

The reference panel is sampled from multiple held works under a frozen rotation scheme. Repeating
the evaluation across reference panels estimates reference uncertainty; selecting one iconic work
turns painter fidelity into exemplar matching.

### 5.4 Task family C: interpretable trait ratings

Ratings are secondary and explain the choice space; they do not define painter validity. Candidate
traits map directly to qualified feature families, for example local color-transition strength,
palette organization, edge/orientation structure, coarse-versus-fine mark organization,
self-similarity, and spatial organization. Separate items measure subject/content similarity,
familiarity, reproduction quality, perceived source consistency, liking, and generic aesthetic
quality.

Every item has a definition, response anchors, and a construct role (`convergent`, `discriminant`,
or `diagnostic`) frozen before collection. Avoid “brushstroke width,” “pigment,” or “impasto” for
ordinary web RGB unless a physical-scale/topographic modality supports those terms.

## 6. Experts and nonexperts

### 6.1 Recruitment and characterization

Recruit two preregistered strata rather than a self-selected pooled crowd:

- **domain experts:** roles and minimum experience relevant to close visual comparison—such as art
  historians, conservators, curators, or practicing painters—with painter/period familiarity
  measured separately; and
- **general observers:** participants without the expert inclusion criteria, sampled for the
  intended public-facing use.

Record role, years of relevant education/practice, visual status, color-vision screening, art
interest/knowledge, language/culture, painter familiarity, and device/display conditions. Specker
et al.'s VAIAK can characterize general interest and knowledge but does not replace domain criteria.

The primary expert analysis is not automatically superior. Reymond et al. found expertise-related
differences and time-dependent revision, illustrating that group behavior depends on the task.
Report each stratum first, then a preregistered pooled model with group interactions.

### 6.2 Administration quality

Use a controlled, color-managed viewing setting for the primary color-sensitive validation where
feasible. If online collection is necessary, define minimum display size, browser/profile handling,
ambient-light instructions, a visual-acuity/color-screening procedure, and an explicitly narrower
claim. Randomize left/right position and trial order; insert repeated trials to estimate within-
rater consistency; record response time without using speed as a truth criterion.

Attention checks test whether a participant followed the task, not whether they agreed with the
research hypothesis. Exclusion rules and the handling of ties/“cannot tell” responses are
preregistered. A forced choice when observers genuinely cannot discriminate inflates apparent
precision; allow and model an indifference response or use a prespecified confidence response where
the chosen model supports it.

## 7. Convergent and discriminant evidence

### 7.1 Multitrait-multimethod design

The minimum matrix crosses several traits and methods:

| Trait | Human methods | Nonhuman/technical methods | Expected relation |
|---|---|---|---|
| Painter-associated manner | content-matched triplet; target-reference pair; defined trait ratings | qualified transparent feature distance; held-work target model | convergence across method and reproduction |
| Subject/content | explicit content pair/triplet; semantic labels | frozen semantic embedding or metadata match used only as nuisance comparator | weak after content matching; should not explain painter result |
| Color appearance | color-organization ratings | qualified CIELAB/distribution features | selective convergence, stable across managed reproductions |
| Reproduction/source quality | defect/source-consistency ratings | source classifier; resolution/codec/profile metadata | may converge internally but must be discriminant from painter manner |
| Liking/aesthetic quality | preference and liking ratings | optional preference baseline | not required to converge with painter manner |

The primary convergent estimand is the association between the human painter-manner distance matrix
and the qualified computational painter-distance matrix on held works. It is computed within
content/medium/date common support, with source and semantic/content distance controlled, and is
repeated on the independent-reproduction panel. Both effect size and uncertainty are reported.

A large raw correlation is insufficient if both matrices encode chronology, brightness, motif, or
provider. Conversely, imperfect convergence is expected because the computational profile is
deliberately transparent and human style perception is multidimensional. The preregistered claim
must specify how much convergence is practically meaningful.

### 7.2 Discriminant and cue-conflict tests

Painter evidence should survive all applicable tests:

- same subject, different painter;
- different subject, same painter;
- same provider, different painter versus different provider, same painter;
- matched medium/date with different painter;
- independent reproduction of the same work;
- grayscale or controlled-color diagnostic branches where color shortcut is suspected;
- border/frame present versus qualified mask; and
- familiar/canonical versus unfamiliar held works.

Grayscale is not the “truer” style condition because color can be constitutive of painter manner.
It is a diagnostic interaction. A coordinate or judgment that disappears in grayscale may be valid
color-based evidence if it also passes reproduction and content controls.

## 8. Measurement invariance

Measurement invariance asks whether the task relates observed responses to the same latent
interpretation across groups and conditions. It is not established by a nonsignificant group mean
difference.

### 8.1 Prespecified facets

Test or scope claims across:

- expert versus general observer;
- relevant language/cultural groups, if more than one is claimed;
- controlled display versus allowed online device classes;
- whole work versus recurring-motif crop;
- primary versus independent reproduction;
- source/provider;
- content/genre, medium/support, and supported date bands; and
- real-work calibration versus generated-image application.

### 8.2 Appropriate tests by response type

For multi-item ordinal trait ratings, fit a prespecified multi-group ordinal latent-variable model
where sample size supports it. Examine configural structure, loading discrimination, and response
thresholds before comparing latent means. If invariance fails, report partial or group-specific
measurement only when that possibility and its decision rule were preregistered; do not free
parameters until the desired conclusion appears.

For pair/triplet choices, rating-scale invariance is not the issue. Fit group-specific hierarchical
Bradley–Terry/Thurstone-style or multinomial choice models and estimate interactions among evaluator
group, target painter, stimulus stratum, and reproduction. Compare group-specific human distance
matrices, hard-neighbor ordering, and cue-conflict effects. A common construct requires stable
direction and practically equivalent target contrasts, not identical response rates.

If experts and general observers agree on painter ordering but use different cues, the shared score
may be usable with a qualified interpretation. If they reverse target-versus-neighbor judgments,
pooling is invalid; the project has two audience-specific constructs.

## 9. Uncertainty and dependence

### 9.1 Sampling units

The hierarchy for real-work calibration contains evaluator, physical work, reproduction nested
within work, and trial/comparison. A pair or triplet crosses several works, so observations are not
purely nested. The generated application adds prompt/content stratum, seed, output image, reference
panel, and possibly model run. Repeated ratings and crops remain within these units.

The confirmatory choice model should include, as supported by design:

- fixed effects for condition, target painter, evaluator stratum, source/content/medium/date strata,
  presentation order, and prespecified interactions;
- crossed random effects for evaluator and physical work or output image;
- comparison/pair or anchor effects when the same combinations recur; and
- prompt and seed allocation effects for generated evaluations.

Painter may be treated as fixed when the study asks about named, purposively chosen painters. The
works are still sampled evidence for each painter and must contribute to uncertainty.

### 9.2 Resampling and randomization

Use model-based intervals plus a robustness analysis that reweights/resamples crossed evaluator,
work, prompt, and output factors. Do not bootstrap individual clicks. For randomization tests,
labels may move only within the exchangeability blocks authorized by the design—typically at the
physical-work or matched-pair level, not among files or ratings.

Report estimates and intervals for:

- target-versus-each-matched-neighbor choice probability or latent contrast;
- within-painter versus between-painter human distance distributions;
- source-cue-conflict and content-cue-conflict effects;
- expert/general-observer differences and equivalence contrasts;
- independent-reproduction differences;
- human–computational convergence after nuisance control; and
- generated named-versus-painter-free effects separately for painter resemblance, content,
  defects, and liking.

Five votes on one image do not equal five images. Power and precision must be simulated from the
planned crossed model using pilot-independent variance ranges. Increase the number and coverage of
physical works before purchasing many redundant ratings of the same few exemplars.

## 10. Preregistration and decision gates

Freeze the construct definition, corpus, exclusions, comparison graph, task wording, reference-panel
rotation, evaluator strata, primary outcomes, nuisance controls, smallest effects of interest,
equivalence margins, model, multiplicity family, and missing/indifference handling before opening
the held real-work labels or generated condition results.

| Gate | Passing evidence | Failure disposition |
|---|---|---|
| H0 — construct content | task and items map to painter manner; painter names and hypothesized cues are not leaked; experts review wording before outcomes | revise instrument prospectively |
| H1 — stimulus validity | held physical works, hard matched painters, work-level splits, source/content/medium/date common support, and independent reproductions | no confirmatory human painter claim |
| H2 — response quality | prespecified completion/vision criteria; interpretable repeat consistency; no material position/interface artifact | repair administration and recollect prospectively |
| H3 — real-work painter specificity | same-painter advantage against each relevant hard neighbor on held works, with uncertainty and no single-work dominance | reject or narrow the painter construct |
| H4 — cue discrimination | target advantage survives content and source cue-conflict, medium/date controls where supported, and familiarity sensitivity | label the detected shortcut; do not call it painter manner |
| H5 — reproduction reliability | materially equivalent painter relations across independent digitizations | restrict claim to the tested file/source |
| H6 — convergence | qualified computational and human painter-manner relations agree on held work after nuisance control and replicate by reproduction | retain computation as image descriptor, not validated painter measure |
| H7 — discriminant evidence | painter-manner measure is not reducible to content, quality, liking, or source | split/redefine the construct or reject it |
| H8 — evaluator/presentation invariance | target conclusions are stable within prespecified margins across claimed groups/conditions | publish group-specific scope; do not pool |
| H9 — generated prompt-movement evidence | frozen real-work instrument shows a named-versus-painter-free painter-resemblance effect while content, defects, and missingness remain acceptable | no human prompt-movement claim |

Passing H9 supports only the human component of the analysis policy's G2 prompt-movement
estimand. It does not prove authorship, authenticity, cultural value, that the generator recreated
a physical painter's hand, or canonical painter fidelity. Under the declared prompts, models,
reference domain, reproductions, evaluator populations, and decision margins, it permits only the
narrow statement that named prompting shifted outputs toward a human- and measurement-qualified
painter-associated visual distribution. A canonical painter-fidelity claim remains prohibited
unless absolute fit, both panel-wide hard-neighbor rules, precision and density, recall and
coverage, content coherence, and availability all pass their binding criteria; H9 cannot rescue
any failed conjunct.

## 11. Weak leads and rejected shortcuts

| Lead or practice | Disposition | Reason |
|---|---|---|
| Unblinded “Does this look like [painter]?” rating | `rejected_primary` | name, iconic subject, and expectation cues are inseparable |
| Liking, beauty, emotion, auction price, or generic quality | `discriminant_or_secondary` | Iigaya, Nascimento, and Reymond show these are real responses but not painter specificity |
| One iconic reference image | `rejected` | estimates exemplar matching and suppresses within-painter variability |
| Majority vote as ground truth | `rejected` | discards rater/stimulus uncertainty and minority/group structure |
| Expert opinion alone | `insufficient` | expertise changes processing but does not create a criterion; qualification and invariance remain necessary |
| Nonexpert crowd alone | `scope_limited` | supports only that sampled population and device regime |
| High interrater agreement | `reliability_not_validity` | observers can agree on source, content, saturation, or stereotypes |
| Human–feature correlation on feature-selection works | `circular` | the same stimuli selected the measure and assessed convergence |
| Randomly shuffled clicks or crops in inference | `prohibited` | violates physical-work, stimulus, and evaluator dependence |
| Method-level ArtFID/user rank | `background_only` for painter validity | does not establish target-painter specificity or image-level coverage |
| Grayscale as universal deconfounding | `diagnostic_only` | removes possible legitimate painter color information along with reproduction cues |
| Pooling experts and nonexperts after a nonsignificant interaction | `rejected` | absence of conventional significance is not evidence of practical invariance |
| More ratings on the same few works | `precision_only_within_stimuli` | cannot repair limited across-work support |

The result should be reported as a validity argument, including failures and scope restrictions, not
as a single human score. That standard directly addresses Pilot 2's central lesson: detectable
structure is easy to find; demonstrating that it is specifically, reproducibly, and perceptibly
associated with a painter across works is the scientific task.
