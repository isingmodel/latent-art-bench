# Research proposal: painter-conditioned distribution fidelity under content and capture controls

**Date:** 2026-09-06. **Status:** proposal for a new versioned study; not a frozen protocol or
an executed experiment. **Resources:** approximately $100 of OpenRouter credit, inexpensive
existing OAuth access, and the local computer. All research documents will be in English.

## Recommendation

Investigate whether the reduced feature spread and original/generated separation persist when
the compared sets have similar subject matter and digital-reproduction conditions. Add two
current image-model families to test the scope of that finding. Use one targeted prompt
intervention to ask how much of the gap is attributable to the prompt library.

The proposed central question is:

> Within a declared outdoor-painting reference frame, how closely do painter-conditioned
> generators reproduce the location, spread and coverage of original-painting features, and
> how do these results change with content matching, capture controls and prompt specificity?

This supports a focused empirical paper. A possible working title is **“Recognizable Style,
Restricted Distributions? A Controlled Study of Generated and Original Paintings.”** The question
mark matters: recognizability and restricted distributions must both be tested, and restriction
may weaken after better controls. Publication venue and Kim's involvement remain undecided.

The preferred design has **1,008 research generation attempts plus 18 technical pilot attempts**,
with one image requested per attempt. Only **588 attempts** use OpenRouter. Estimated image-output
charges are about **$40.34**, before ancillary charges. Keep a conservative initial operating
envelope of **$75**, leaving **$25 uncommitted**. These are proposed ceilings, not instructions to
spend the credit now. The work completed for this proposal used no paid generation calls.

## Decision: which axis to expand

**Make model-family breadth the main expansion of the generation experiment.** Improving content
coverage and reference/capture controls comes first in execution because it makes that expansion
interpretable. Do not increase every dimension of the factorial.

| Axis | Decision for this round | Evidence and purpose |
| --- | --- | --- |
| Generation models | Add two paid families; retain one OAuth route | The recent large experiment compares two service aliases without attested distinct model snapshots. New families address whether its finding extends beyond that service; the older SD-Turbo study alone does not supply a contemporaneous matched comparison. |
| Painters | Add none; focus new generation on Monet and Cézanne | Separation already occurs across all four existing painter cases. More painters would improve artist generality but leave content/capture and model-identity explanations unresolved, while multiplying reference and generation costs. |
| Prompt content | Increase structured coverage to 24 briefs per painter, matched to reference content strata | Repeating the same 16 generic scenes cannot reveal whether the reference's broader subject/composition mixture caused the apparent contraction. Distinct supported content is more useful here than extra paraphrases. |
| Prompt wording | Reduce the main experiment to named/artist-free; add one generic/detailed contrast on OAuth | By-name was closest in 19/24 earlier cells, and explicit style instruction was farther in 24/24. These observed directions justify a focused follow-up, while giving no assurance that the same ordering holds for new models. |
| Repetitions | Three per brief, distributed across collection windows | Repetition is needed to inspect within-brief variation, but more repeats of a restricted library cannot resolve missing content coverage. Three is a budget/design choice to qualify, not a demonstrated sufficient sample size. |
| Original reference evidence | Improve distinct-work and capture coverage within the two selected painters | Uncertainty about the comparison target currently limits interpretation more than a shortage of generated images alone. |
| Feature representations | Keep 31 primary; defer learned features to a small optional pilot | Changing the measurement representation now would create another major dimension before the existing feature gap is explained. |

This is a judgment about information gained per unit of budget and curation effort, not an
estimated numerical ranking of research value. **The intended contribution is an explanation
and a test across model families, not a larger collection of separated scatter plots.**

Narrowing the painter and prompt sets is acceptable for a two-painter case study when selection
is disclosed, the new outcomes have not guided that selection, and inference stays within the
registered conditions. It does not support claims about all painters, all prompts, or each
model's best achievable style fidelity. Preserve the earlier broad analyses as development
evidence rather than excluding the less favorable methods from the research record.

After this round, broaden painters only if the next question is whether the controlled result
extends across artistic traditions. Select contrasting traditions and feasible reference sources
before measuring their gaps; do not choose the painters expected to produce the largest separation.
If models instead differ strongly, the next expansion should be a targeted model-by-prompt
interaction study. If content or capture controls explain most of the gap, prioritize that
explanation and report it before considering any further expansion. These decisions depend on
effect patterns and uncertainty, not on whether a preferred hypothesis reaches significance.

## What the completed analyses establish

The [distribution report](../reports/painter_distribution_exploration_v1/REPORT.md) provides
strong motivation: all-31 generated/original total-variance ratios of 0.206–0.376, and grouped
out-of-fold balanced accuracies of 0.913–0.976 for the linear classifier and 0.940–0.983 for RBF.
The first two PCs retain only 42.9–47.8% of balanced variance, so visible overlap and strong
full-space discrimination are compatible. These remain exploratory finite-dataset findings.

The [completed prompt comparison](../reports/painter_prompt_retry_v1/ppr1-two-refusals-20260906-r2/REPORT.md)
also justifies reducing the prompt factorial: by-name was closest in 19/24 family-level cells;
explicit style instruction did not improve its distance in any of the 24 comparisons. This is a
disclosed development-stage reason to choose a baseline, not a universal claim that short prompts
are best. The new study must preserve all earlier methods/results and test its choices on new data.

Four alternative explanations remain material:

| Explanation | Why the current evidence does not resolve it | Discriminating next step |
| --- | --- | --- |
| Prompt/content restriction | Sixteen generic scene templates do not represent the full variation of the original collections | Match content strata and compare generic versus detailed prompts contemporaneously |
| Digital-reproduction effects | Originals and generated PNGs have different capture, compression, profile and geometry histories | Same-work capture pairs, source-held-out checks and symmetric processing sensitivities |
| Generic generated-image signatures | A detector can recognize synthetic images without measuring the requested painter's style | Artist-free controls, cross-painter/generator transfer and wrong-painter reference comparisons |
| Painter-associated distribution mismatch | The generator may reproduce selected cues while missing other variation | Test remaining mismatch and coverage after the preceding controls; assess human resemblance separately |

We should explicitly correct an over-interpretation of the current variance result: a smaller
spread across a fixed prompt library does **not** by itself demonstrate intrinsic model collapse
or lower artistic diversity. Nor does a 97% discriminator establish poor aesthetic quality.

## Position relative to the literature

[Kim et al. (2026)](https://pmc.ncbi.nlm.nih.gov/articles/PMC13416963/) connects learned image
representations to art-historical structure and uses contextual guidance in image-to-image
experiments. Our proposed contribution is a conditional generated-to-original distribution
study. A future comparison of contextual recognition and interpretable feature mismatch would
connect the projects, but is not an exact replication of Kim's A/C vectors.

[Asperti (2026), a preprint already in our bibliography](https://arxiv.org/html/2608.25609v1),
is particularly close: it studies human/generated painting separation in CLIP, examines
preprocessing and multiscale explanations, and demonstrates sensitivity to perturbations of low
visual salience. Therefore, “the scatter plots separate” is insufficient as the paper's central
novelty. Our candidate contribution is the **painter-conditional, content-matched distribution
comparison and controlled prompt intervention**, with independent capture and human checks.
This is a positioning argument, not a verified claim of being the first such study.

[Frochte (2026), also a preprint](https://arxiv.org/abs/2605.09030), cautions against treating raw
style-embedding cosine as a calibrated fidelity score. Adding an encoder will not automatically
solve construct validity. [Naeem et al. (2020)](https://proceedings.mlr.press/v119/naeem20a.html)
motivates distinguishing fidelity from coverage, while
[Parmar et al. (2022)](https://arxiv.org/abs/2104.11222) motivates explicit control of resizing
and compression. Their metrics and findings do not establish calibrated thresholds for this corpus.

## Stage A: explain the existing result before buying images

Use all four existing painters for this diagnostic stage. Keep it explicitly exploratory and
retain the original 31-coordinate scaler and all published endpoints.

1. **Original-versus-original baselines.** Make reproducible, disjoint splits of physical works
   within painter; match group sizes where possible. Repeat the distance, variance and
   classification procedures under randomized pseudo-domain labels. This measures instability
   arising from finite samples and real heterogeneity. These resamples are not independent new
   studies and do not define an artistic-equivalence margin.
2. **Artist-free comparison.** Extend the latest scatter/separability and spread analysis to
   the 384 existing artist-free images. Compare named versus artist-free distributions against
   the same reference. Similar discrimination for both suggests that the detector is capturing
   general domain differences; it does not prove there is no artist-specific signal.
3. **Robust spread.** Complement covariance trace with coordinate IQR ratios and a fixed
   robust spread summary. Inspect existing family-only results and PCA loadings to locate the
   difference. Keep every coordinate and original result; do not select a favorable feature subset.
4. **Content accounting.** Annotate originals and a balanced generated subset using a short
   rubric for depicted objects, viewpoint and composition. Compare their content mixtures and
   perform a fixed reweighting sensitivity over supported strata. Exclude palette, brushwork
   and measured texture from the matching rubric: matching those would erase the target signal.
5. **Transfer diagnostics.** Train a domain classifier on one painter and evaluate on another;
   later evaluate it on the new generators. Use group-disjoint original works and prompt families.
   Strong transfer would motivate investigating generic generator/capture signatures.

**Output:** one explanation report that states which parts of the gap survive these checks.
**Estimated effort:** 1–3 working days plus annotation; no generation credit required.
If these checks materially weaken the apparent contraction, that is a substantive answer to the
same research question. Do not compensate by searching for a stronger-looking projection.

## Stage B: build a small, controlled reference panel

Focus the paid experiment on **Monet and Cézanne**, while retaining Sisley and Pissarro in Stage A.
They provide different existing feature patterns and a manageable comparison. This selection is
informed by already observed results and must be disclosed. Conclusions will concern these two
case studies, not painters in general. If their common content support is inadequate, revise the
selection on reference-feasibility grounds before new generation, not after inspecting new outcomes.

The target panel is **48 previously unmeasured, distinct physical works per painter**, 96 total,
distributed across **12 shared content strata**, with four originals per painter/stratum. Aim for
at least two documented reproduction workflows per painter, crossed with both painters and as
many content strata as possible. Museum or website names alone do not establish capture workflows.

First enumerate an eligible source frame and deduplicate it against all historical exposures;
then select within strata by a fixed randomized rule. Do not collect until an appealing quota
is reached. One mirrored file, crop or alternate encoding never counts as a new physical work.
Retain the outdoor-painting domain and document attribution, medium, rights, borders, image
geometry and capture provenance. A matched subset is a conditional target, not the complete oeuvre.

Develop the content rubric and **two distinct content briefs per stratum** using exposed
development works and curatorial descriptions. This gives 24 briefs per painter. Use the same
briefs for all routes and name/no-name conditions; prefer identical briefs across painters where
the common support permits. Briefs describe subjects and composition, not desired color or texture
statistics, famous painting titles, or feature-target values. Do not feed original images to the
generation models: that would introduce a separate image-to-image task.

The new reference images may be inspected for eligibility/content by annotators, but they should
not be used to optimize prompts, features, classifiers or thresholds. Freeze the rubric, prompts,
sampling and analysis before extracting their evaluation features. Document this restricted
content exposure; do not call the images completely unseen in every sense.

Create a separate auxiliary panel targeting **12 same-work capture pairs per painter**. Prefer
existing exposed works with a genuinely distinct photographic/digitization event, giving 24 pairs
overall without consuming the fresh reference panel. Record evidence of capture independence.
If only alternate encodings or mirrors are available, label them as processing sensitivities and
do not claim independent-capture validation.

Apply identical, prespecified downsampling/re-encoding branches to originals and generations,
for example the original 512-short-side pipeline, a 256-short-side branch and a common JPEG branch.
All versions of a work stay in the same validation fold. Changes across branches demonstrate
measurement sensitivity; blurring away the difference is not proof that it was merely an artifact.
Do not histogram-match away color or otherwise normalize away the painter features being studied.

**Feasibility checkpoint:** 12 well-supported strata and 48 fresh works per painter are targets,
not established availability. If they fail, change the reference design before spending. Reusing
exposed works remains a valid exploratory study, but cannot be presented as fresh confirmation.

## Stage C: two new model families and one targeted prompt intervention

### Model selection

Recommended additions, checked against public listings on 2026-09-06:

| Route | Role | Planning price for image output | Selection rationale |
| --- | --- | --- | --- |
| `google/gemini-3.1-flash-image` — Nano Banana 2 | Paid comparator | Approximately $0.0672 per 1K square image | Current Google image family at a cost compatible with repeated sampling |
| `black-forest-labs/flux.2-max` | Paid comparator | $0.07 for the first generated megapixel | A second model family, using BFL's upper-tier offering |
| Existing OAuth `gpt-image-2` service alias | Low-cost prompt experiment and service comparator | Almost free to the user; not an audited public API price | Reuse access while retaining its model-identity and rendering limitations |

Google documents 1,120 image-output tokens at $60/million for 1K output, and the OpenRouter
listing shows that image-token rate. BFL's OpenRouter listing specifies first-megapixel pricing.
These are planning estimates, not an all-inclusive quote for every returned geometry.
[Google pricing](https://ai.google.dev/gemini-api/docs/pricing),
[OpenRouter Nano Banana 2](https://openrouter.ai/google/gemini-3.1-flash-image),
[OpenRouter FLUX.2 Max](https://openrouter.ai/black-forest-labs/flux.2-max/pricing).

Call these **current high-capability comparators**, not a verified ranking of the best painter
imitators. A full leaderboard survey is outside this proposal. Do not select models by whichever
gives the largest gap in a pilot. Nano Banana Pro is a possible replacement before registration,
but its standard 1K image-output estimate is roughly twice Nano Banana 2's; a third paid model
adds less value initially than better reference controls.

Use one explicit model ID and a pinned provider when available. Record model/provider identifiers,
settings, response metadata, timestamps and actual billing. A provider/model name is still not
proof of immutable weights. The existing two OAuth aliases must not be counted as two independently
verified models. If OAuth still ignores geometry/quality, report that route separately from any
comparison requiring a matched rendering contract.

### Prompt conditions

| Condition | Definition | Routes | Scientific purpose |
| --- | --- | --- | --- |
| N: detailed content + painter name | Fixed content brief with the original by-name syntax | All three | Main painter-conditioned distribution |
| F: detailed content, artist-free | Identical brief and medium wording with the painter attribution removed | All three | Incremental effect of naming the painter |
| G: generic content + painter name | A contemporaneous broad-scene version corresponding to each detailed brief | OAuth only | Effect of prompt specificity/content restriction while preserving painter attribution |

The core does not repeat all three historical style-wording methods. The generic-versus-detailed
contrast addresses a more specific explanation for the contraction. It is a combined intervention
on content specificity and wording, not a clean estimate of text length or one linguistic token.
Keep generic scene-family weights matched to the detailed set. Repeated generic strings are one
prompt family for validation; never split identical strings between classifier training and testing.

Generate **three repetitions of each of 24 briefs**, giving **72 images per painter/condition/route**.
The planned research counts are:

| Allocation | Calculation | Attempts |
| --- | --- | ---: |
| Nano Banana 2 core | 2 painters × 24 briefs × 3 repetitions × 2 conditions | 288 |
| FLUX.2 Max core | Same design | 288 |
| OAuth core | Same design | 288 |
| OAuth generic-prompt condition | 2 painters × 24 briefs × 3 repetitions | 144 |
| Research total | | **1,008** |
| Technical pilot, excluded from research endpoints | 6 fixed calls per route | **18** |
| Total proposed request cap | One requested image per attempt | **1,026** |

Use at least eight scheduled collection windows across several days, with routes and conditions
interleaved. Assign the three repetitions of a brief to distinct windows and balance condition
counts. Eight windows do not establish independent backend states, and three repetitions do not
become eight independent replicates. Preserve the schedule for dependence analysis.

Match requested aspect ratios/resolution using a common supported contract, and verify actual
outputs. Maintain original aspect ratios in measurement and report any remaining aspect mismatch.
Pin the contract using the technical pilot, based on operation, identity, cost and geometry rather
than favorable feature outcomes. No silent route fallback, selective regeneration or best-of-N.
Refusals and measurement failures count toward the attempt cap and are outcomes to report; a later
retry requires a separately recorded follow-up and never repairs a terminal run in place.

The [OpenRouter image documentation](https://openrouter.ai/docs/guides/overview/multimodal/image-generation)
describes per-endpoint capabilities, provider pinning, granular billing and response costs. Before
execution, verify these for the chosen endpoint and bound the complete request cost. Public web
listings were inspected here; no authenticated endpoint qualification was performed.

### Budget

| Item | Calculation | Estimated image-output charge |
| --- | --- | ---: |
| Nano Banana 2, including six pilot attempts | 294 × $0.0672 | $19.76 |
| FLUX.2 Max, including six pilot attempts | 294 × $0.07 | $20.58 |
| OpenRouter image-output subtotal | 588 paid attempts | **$40.34** |
| Conservative operating envelope | Includes text/thinking, geometry rounding and billing uncertainty | **Up to $75** |
| Uncommitted reserve | Not automatically allocated to more calls/models | **$25** |
| Total available credit | | **$100** |

At an all-inclusive ceiling of $0.12 per paid attempt, 588 attempts would cost $70.56. That ceiling
must be justified from actual endpoint billing and bounded request settings before launch; an
image-output quote alone does not establish it. Track incurred and reserved costs for in-flight
requests. If the qualified envelope exceeds $75, revise the design before launch rather than
truncate selected conditions after observing results. The reserve is not permission to reroll.

The $100 is an API budget. Volunteer/annotator time, possible participant compensation, paid
image licensing and equipment are not included. Do not assume those resources are free or secured.

## Stage D: analysis and a small human validation

### Primary scientific outputs

Retain the 31 interpretable features as the main representation, with separate color, spatial
and digital-texture reporting. Reuse the frozen development scaler for the primary analysis;
any alternative preprocessing requires a separately fitted development-only sensitivity scaler.

Report three distinct properties:

1. **Distribution discrepancy:** energy distance against the content-standardized reference,
   plus named-minus-artist-free contrasts and comparisons to the other painter's matched reference.
2. **Spread and coverage:** log total-variance ratios, robust coordinate spread, and an explicitly
   secondary density/coverage diagnostic qualified on real-versus-real samples of comparable size.
   Do not label a variance ratio of one as equivalence; different shapes can have equal variance.
3. **Separability:** fixed full-space classifiers, common PCA views, and transfer across sources
   and generators. For the new paid models, frozen existing-data domain classifiers provide a
   transfer test; within-route grouped cross-validation is a separate supplementary analysis.

Standardize original and generated sets to the same 12 content-stratum weights. Three outputs
per exact brief permit an exploratory between-brief/within-brief variance decomposition, but
the within-brief estimates will be noisy. This directly asks whether coverage is constrained by
the selected scenes, by repeated outputs within scenes, or both.

Show the original content-mixture comparison alongside the standardized comparison. They answer
different questions: the former describes the collected sets, while the latter compares features
under a shared declared content mixture. Neither estimates fidelity to a painter's entire oeuvre.
Distinguish **distribution difference**, **reduced spread**, and **painter specificity** as separate
hypotheses: a persistent difference need not be a contraction, and a generic domain signature
need not respond to the requested painter. Avoid treating evidence for one as proof of all three.

Keep the all-31 result as a descriptive overview rather than quietly replacing the three-family
contract with a new composite score. Predeclare the confirmatory family, if justified, around the
two paid routes × two painters × three families. If both distance and log-spread are tested, that
is 24 endpoints. Use Holm adjustment across that family only if the underlying tests qualify;
adjustment cannot repair invalid image-level independence assumptions. Name/control, prompting
and human associations require separate, clearly labeled secondary families rather than
uncorrected additional primary claims.

### Statistical design required before generation

The counts above establish affordability, **not statistical power**. Stage A should support a
simulation study for the actual reference sizes, strata, repeated briefs, collection windows,
source effects and plausible missingness. Use a range of effects smaller than the exploratory
gap, rather than assuming the observed 95% discrimination will reproduce.

Freeze the estimand and uncertainty procedure before measuring the new reference/generated set.
Resampling must retain the work/brief/window hierarchy and shared-reference covariance; every
fitted analysis step must be repeated inside resampling or fixed on development data. Never treat
all images, pairwise distances, CV folds, crops or repeated ratings as independent observations.
Generic prompts that repeat across briefs require grouping at their common parent template.

With 24 briefs and only eight collection windows, interval coverage may be unreliable. Only call
intervals calibrated if the prespecified simulation checks support that statement under their
declared assumptions. Otherwise report effect sizes and sensitivity honestly and defer the
stronger confirmatory claim. Do not add repetitions opportunistically until a result is significant.
For route/prompt comparisons, preserve paired content and collection-window assignments.

Separate availability from measured-image fit. Prespecify how incomplete content strata affect
the target, and report all attempted images and refusals. Adherent-only or available-case analyses
cannot silently substitute for the intended generated population. No prospective analysis changes
the status of the earlier incomplete primary or the later two-image retry.

### Human validation

Propose a small pilot of **12 participants × 32 trials = 384 judgments**. A balanced panel can
contain 96 generated stimuli (eight per painter × route × N/F cell) and 32 original controls,
with three ratings per stimulus. Divide the original controls between target-painter and
other-painter works; keep all test works out of the displayed reference boards.

Ask separately about stylistic resemblance to a reference board and adherence to the content
brief. Hide generation source and prompt condition, randomize display order, and use disjoint
reference-board works balanced across capture sources. Sample stimuli by a fixed rule, not the
most convincing or most separated examples. Record art expertise and rater agreement.

This tests whether the measured differences correspond to perceived resemblance. It does not
turn 384 ratings into 384 independent people, or individual-image ratings into validation of
set-level diversity. Treat the small convenience sample as exploratory; analyze image/rater
dependence. If participant recruitment or compensation is unavailable, defer this component and
omit claims about human perception rather than substituting an LLM judge.

## Learned representations: optional next round, with a local feasibility pilot

There is no need to train an encoder. The local machine was checked during proposal preparation:
**Apple M1, 16 GiB RAM, PyTorch MPS available, CUDA unavailable**. Small frozen-encoder inference
is plausible on this hardware, although throughput and operator compatibility have not been tested.

First benchmark 32 exposed development images with a small OpenCLIP model, such as ViT-B/32,
using the prescribed preprocessing and checkpoint. Start with small batches and use CPU if MPS
operations are unsupported; record throughput, peak memory and numerical agreement. Do not rent
a GPU before this check. The [OpenCLIP implementation](https://github.com/mlfoundations/open_clip)
supports pretrained image encoding. A contrasting visual-only option is
[DINOv2 ViT-S/14](https://github.com/facebookresearch/dinov2), whose released small backbone has
21 million parameters. Neither representation is a pure style measurement.

If feasible, encode each existing/new image once, cache vectors and hashes, and repeat the fixed
analysis in each representation separately. For scale, 5,000 float32 vectors of dimension 512
occupy about 10.2 MB; weights and inference activations require additional memory. This is a
storage calculation, not a runtime benchmark.

The most useful question would be whether painter resemblance/association improves in a
contextual representation while interpretable distribution mismatch or limited coverage remains.
That is a testable bridge to Kim's work. Exact A/C reproduction should wait for a clear checkpoint,
preprocessing and stochastic-latent contract, ideally informed by discussion with Kim. A different
encoder or repaired local pipeline must be labeled an adaptation. Keep this entire component
secondary and optional; it should not delay the content/capture study.

## What each possible outcome would mean

| Outcome | Defensible interpretation | Next action |
| --- | --- | --- |
| Gap shrinks markedly after content matching | The original comparison partly reflected different content mixtures | Report the design sensitivity; retain remaining conditional effects |
| Gap changes markedly with capture/source controls | Some measured separation depends on digital reproduction | Narrow the claim and improve capture qualification |
| Gap persists across two new model families and controlled references | Evidence for a broader conditional feature mismatch in these painter cases | Quantify effect size, coverage and uncertainty; avoid universal claims |
| Detailed prompts improve coverage over generic prompts | Prompt design contributes to the observed restriction on this OAuth route | Test this specific intervention on a paid route in a later allocation |
| Naming improves painter specificity but substantial mismatch remains | Painter-associated cues and distribution fidelity are distinct | Make that distinction the empirical contribution |
| Humans report resemblance despite a robust measured gap | Perceived resemblance and the chosen feature measures capture different properties | Investigate representation dependence; do not declare either evaluator correct by default |
| The new gap is small or uncertain | The exploratory finding may not generalize under the new conditions | Report that result; do not widen the model/prompt search to recover it |

## Execution order and material to bring to Kim

1. Complete Stage A and the reference-feasibility audit.
2. Specify the new source/capture frame, content rubric and analysis, including simulation checks.
3. Run the bounded technical pilot, finalize endpoint/geometry/cost contracts, then freeze the
   research design in a new namespace before its generation and evaluation-feature extraction.
4. Collect the planned research outputs across the scheduled windows and close the evidence.
5. Run the frozen analysis and, if feasible, the human pilot. Add learned features only under
   their own declared supplementary contract.
6. Prepare a short paper outline, five main figures and a limitation table for discussion with Kim.

The five figures should cover the design/content frame; matched distribution geometry and spread;
capture/source sensitivities; name/control and generic/detailed prompt effects; and human or
representation agreement if that component is completed. Supply the complete tables and manifests
as supplementary material. Ask Kim about construct interpretation, the closest literature,
reference/capture adequacy and a suitable venue. Do not assume endorsement, coauthorship or access
to unpublished artifacts, and do not contact anyone as part of this proposal task.

A planning estimate is **two to four weeks of work after reference access and annotation support
are available**; source discovery or participant recruitment may extend calendar time. The next
concrete task should be Stage A and the reference-feasibility audit, followed by an executable
protocol. More prompt variants, a larger model roster and learned-feature training are deferred.

The existing reports, freezes, ledgers and unique image bytes remain unchanged. No new generation,
acquisition, feature extraction or human study has been executed for this proposal.
