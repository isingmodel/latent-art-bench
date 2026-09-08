# Computational painter responsiveness v2

Issued 2026-09-08, before any v2 image-generation request. This is a new study
namespace, responding to the user's explicit instruction: “without human reference
rating, do it more.” The earlier v1 study, its human prerequisites and its terminal
D0/R0/H0 records remain unchanged. The new scope changes the scientific claim:
**test a deployed image service's measured response to prompt instructions**, without
claiming human-perceived resemblance, a perceptually meaningful effect or validated
coverage of an artist's oeuvre.

## Question and alternatives

Does adding a painter-name clause attenuate a requested muted-to-vivid color
change compared with adding a generic painting-style clause? The primary outcome
is `chroma_median`, in the unchanged primary512 development-IQR scale. The narrow
estimand concerns six specified scenes, two specified color instructions and the
currently available OAuth `gpt-image-2` service alias. It is not an immutable model
snapshot, an identified training mechanism, or an estimate for arbitrary prompts.

A negative interaction is one possible result. Positive interactions, inconclusive
intervals and failed controls are equally reportable. Useful stylistic consistency,
ordinary instruction competition, baseline shifts, nonlinear saturation and
service rendering/metadata differences remain alternatives. An automated check
on earlier data tests whether contraction actually reduces scene distinguishability.
Human judgments are not replaced by LLM-generated ratings.

## Stages and authority

This successor follows Protocol 2.1's prospective separation of scope, source
verification, collection and measured outcomes. The latest user instruction
explicitly removes human-reference ratings as a prerequisite for this narrower
computational claim. No unchanged earlier freeze is made to appear qualified.

1. Commit the protocol, configuration, transport, numerical procedures, renderers
   and relevant tests. Freeze exact source/input hashes, request order and local
   OAuth proxy source/process identity from a clean committed tree.
2. Publish retained-data retrieval diagnostics and a prospective precision
   sensitivity simulation. These use exposed vectors; they cannot be confirmatory
   evidence for a newly discovered mechanism.
3. Execute the frozen 192-slot inventory through the verified loopback OAuth route.
   The user has already authorized bounded parallel image generation. There are
   **no OpenRouter calls or new OpenRouter charges** in this collection.
4. After terminal collection, measure every available output under the three
   existing pipelines, retain unavailable slots and compute the fixed analysis.
   Report all results regardless of sign, statistical significance or usefulness.

The exact 70 original references are the previously exposed controlled-study
panel. Use their already measured vectors only. No new paintings, independent
captures, learned evaluator or external holdout are acquired. Generated response
bytes and transient extraction files stay under the new ignored workspace.

## Fixed design and collection

There are six scenes, two in each broad content class, and four style clauses:
artist-free, generic traditional landscape painting, Monet and Cézanne. Cross each
with muted/vivid color instructions and four repetitions: **192 images**. Scenes,
clauses and the rendering payload are fully specified in `study.json`. Both painters
share the same free and generic outputs. Their effects are not statistically
independent just because they have different names.

The 24 scene/repetition blocks are randomized; all eight style/polarity cells are
randomized jointly inside each block. Complete the current block's in-flight calls
before starting another block. There are at most two in-flight requests, with at
least five seconds between starts. No scheduling at night, automatic continuation,
provider fallback or alteration of a failed prompt is permitted.

The endpoint is the locally source-verified OAuth service at
`http://127.0.0.1:10532/v1/images/generations`. Request `gpt-image-2`, one image,
1024×1024, medium quality, PNG and an opaque background. The prior service often
reported low quality despite medium being requested. Preserve actual reported
fields, container dimensions and transport timing; do not adjust for, discard or
regenerate an image because those post-request properties differ from the request.
Any supported, decodable, opaque output with both dimensions at least 512 is
eligible for measurement; geometry differences are part of the delivered service
outcome. A decoding/normalization failure remains a missing endpoint.

Each slot permits at most one identical-payload technical retry, six retries in
total. Only fully received HTTP 429/500/502/503/504 technical errors qualify;
refusals, uncertain delivery and malformed success bodies do not. Stop dispatch
on uncertain delivery, malformed success, an output below the minimum dimensions,
an authentication/quota/contract status (401/402/404 or non-refusal 403), or three
failures among the latest eight completed attempts. Unsupported/excessive retry
delays, insufficient reserved disk space, or changed source/proxy identity also stop
dispatch. Drain in-flight requests. Record every attempt and all 192 final slot statuses.
A stopped or interrupted collection is closed; a successor must use new identities
and paths, never rewrite or resume this run. This route has no incremental
OpenRouter accounting; subscription usage is not asserted to be economically free.

## Measurement, estimation and interpretation

Reuse the exact 31-feature extractor and previously fixed development scalers for
primary512, resolution256 and JPEG90/512. No scaler is fitted to the new outputs.
For cross-processing chroma comparisons, use the *same primary512* center and IQR.
Keep native per-pipeline scaled full vectors for the other descriptive coordinates.

Let d(a) be the vivid-minus-muted response for arm a. The two primary interactions
are kappa(Monet)=d(Monet)−d(generic) and kappa(Cézanne)=d(Cézanne)−d(generic), averaged
equally across the six fixed scenes. Estimate four paired block contrasts per
scene, then their equal-scene average. Retain the shared-control covariance.
Use the existing template-stratified variance, Welch–Satterthwaite t approximation,
Bonferroni simultaneous two-endpoint intervals and Holm adjustment at alpha 0.05.
These are approximate model-based finite-template inferences, not exact tests of
a weak null under the randomized order. They assume independent repeat-block errors
and adequate stability over the collection; order randomization does not prove
those assumptions. The original two-endpoint family is fixed before outcomes.

Report free and generic manipulation checks against **zero**, with their nominal
intervals, and all arm/polarity means. No perceptual meaningful-effect threshold is
invented. A primary interval wholly below zero supports a smaller positive measured
response only when both control responses have nominal lower bounds above zero
and the named response estimate is positive. Otherwise report the negative
interaction with its failed-control, zero-response or response-reversal qualifier.
An interval wholly above zero indicates a larger named response, qualified by
control status; one including zero is inconclusive. A failed control does not remove a scene
or hide the interaction. Named-minus-free and generic-minus-free contrasts diagnose
ordinary instruction competition. Two levels cannot distinguish a gain change
from nonlinear saturation or a shifted response curve.

Any missing primary measurement withholds primary inference for the allocated
192-slot grid. Complete-block survivors remain explicitly selected descriptions.
Processing sensitivity and all 31 coordinate interactions are descriptive; they
create no additional confirmatory test family. Every unavailable status and every
contrary result stays in the numerical report.

## Link to original paintings

Describe each condition's measured chroma relative to the exact original reference
panel, including empirical 10th–90th percentile ranges, one-dimensional Wasserstein
distance and range coverage. Preserve exact work IDs and show both the observed
painter mixture and equal broad-class weighting. Broad content annotations were
made by a single maintainer-run LLM; they are not independent fine-content matches.
These are comparisons with an exposed collection of digital reproductions, not
unseen validation, population tolerance intervals or human fidelity scores.

## Retained-data falsification and precision sensitivity

Using only the previous controlled dataset, perform leave-one-repetition-out scene
retrieval. For each held-out repetition, construct each scene centroid from the
other two repetitions and classify the held-out image among 24 scene centroids,
separately for named/free conditions. Reuse frozen feature scales and examine all
three pipelines and five fixed views: original31, color11, spatial8, texture12 and
no-texture19. Also restrict candidates to the eight scenes in the same broad class.
Report exact predictions, deterministic lexical tie handling, tie-aware accuracy,
midranks and own/nearest-other distances. Every fixed scene and query remains.
These are descriptive comparisons without new p-values or a population-of-scenes
claim. Uniform contraction need not reduce retrieval; unchanged or improved
retrieval weakens an interpretation of contraction as lost scene information.

Simulate the 192-image design from centered historical OAuth residuals, with the
finite-repeat variance correction. Generic-clause noise is an unvalidated free-arm
proxy. Use the fixed seed and 5,000 trials per scenario/effect setting; include
empirical noise, enlarged generic noise and heterogeneous noise, with global and
partial nulls. The hypothetical 0.25/0.5/1 IQR interactions are sensitivity values,
not meaningful human effects. Disclose Monte Carlo uncertainty. There is no
human-margin or power-threshold gate: this is a bounded, estimation-focused
computational experiment, and wide intervals are a valid outcome.

## Publication and reproducibility

Publish one report with scientific results, complete tables and comparison plots;
keep operational receipts separate. Recompute measured-vector analyses and plot
bytes offline without reopening generation. Preserve all frozen stages and raw
research bytes. Reviews of this implementation are maintainer-run LLM subagent
reviews with coordinator checks, not institutionally independent validation.
