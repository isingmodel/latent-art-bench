# Painter Distribution Revision v1: fixed post-result diagnostic scope

Issued 2026-09-07 after the completed controlled results and skeptical review.
This is an explicitly post-result methodological revision, not a retrospective
preregistration or replacement of any earlier study. The user authorized the
revision, the updated English paper, and additional OpenRouter data if needed.
The new namespace is `painter_distribution_revision_v1`; initial run ID is
`pdrv1-numeric-20260907`.

## Objective and claim

Determine how the observed painter-name changes in finite feature distributions
depend on measurement weighting, prompt variation, reference support and detection
controls. Retain the original eight sharp-null prompt tests unchanged. Every new
analysis in this scope is descriptive: no additional confirmatory p-value family,
population-equivalence threshold, or claim of perceptual style validation is
introduced. The first revised paper targets the computational case-study claim
that the available evidence can support. Original sampling, source/capture, human
and immutable-model limitations remain explicit when not experimentally resolved.

This scope implements the review's retained-data package and operationalizes the
remaining validation choices. It does not silently claim that planning a human
study or sampling frame completes that validation.

## Inputs and boundary

Read the unchanged 210 reference vectors (70 works × three pipelines), 3,018
generated vectors (1,006 images × three pipelines), the same 221 development
works in each pipeline, their development-only scalers, original exact requests,
reference annotations and delivery metadata, terminal generation event metadata,
and published numeric analysis. Input paths, source and tests are bound by SHA-256
and a recorded Git commit before computing the new full diagnostic package.

No raw image or full generated response is opened, no features are re-extracted,
and no external image acquisition, human recruitment or generation POST occurs
in this numeric scope. Historical original/development exposure remains labeled.
The Python entry point is `python -m
latent_art_bench.painter_distribution_revision_v1.analysis` with `prepare`,
`verify`, `build`, and `check` commands. `prepare` requires exact committed clean
bound inputs; commit the resulting freeze before `build`. Output is create-once.
An interrupted/failed stage is diagnosed; a terminal publication is never topped
up or rewritten. Scientific corrections require a separately recorded successor.

## Fixed metric diagnostics

Use all three existing pipelines: primary512, resolution256 and jpeg90_512.
Keep four predeclared measurement views, without an open-ended search:

1. Original 31 scaled coordinates, unchanged.
2. Nonredundant 28: omit deltaE slope (index 10), wavelet slope (23) and wavelet
   curvature (24), which summarize other included coordinates.
3. Family-balanced 31: multiply the 11 color, eight spatial and twelve texture
   coordinates by 1/sqrt(11), 1/sqrt(8), and 1/sqrt(12), respectively. This gives
   equal coordinate-count family weight in squared distance, not equal observed
   variance or calibrated style weight.
4. No-texture 19: retain the unchanged color and spatial coordinates.

For all 14 cells, use the original painter-reference class masses and compute
energy, total trace and IQR summaries. Show the separate cross-domain and both
within-domain distance terms. Compute the six named/free energy changes on common
brief/repetition pairs and the same weights; these are new descriptive views.
Preserve the original generic/detailed results in the revised paper and record
their missingness; do not promote selected new views to primary tests.

Decompose generated trace exactly into within-brief, between-brief within content
class, and between-content-class components. Decompose original trace into
within/between content class, without inventing original brief labels. Show
coordinate and family contributions to trace. Use population-weight denominators
for these finite empirical decompositions, not claims of unbiased variance
components based on three repetitions.

Show development equal-painter-weighted coordinate correlations and a bounded
primary-scaler sensitivity omitting each development painter in turn. Fit any
alternative scales using development only and never choose the scale based on
evaluation results. Report invalid scales explicitly rather than adjusting them
until a desired result appears.

For primary512/original31, show leave-one-reference-work and feasible
leave-one-holding-collection-group analyses, retaining the original class masses when
support permits. A group is the exact recorded set of collection IDs (including
combined sets or unknown), not each overlapping membership. A collection ID is a source proxy, not a verified
photographic workflow. Report unavailable source/class support. Delete each
content class separately and renormalize the remaining target masses as an
explicitly different target. Influence ranges are not confidence intervals.

## Specificity, placebo and timing

Under common one-third content masses, compare each named collection with both
painters and report cross/within distance terms. Add a painter-prompt ×
reference-painter double contrast: it cancels reference-only and generated-only
within terms. Include the separately collected artist-free outputs under the two
nominal painter labels, verifying exact payload identity for all matched requests.
Neither a two-way minimum nor the double contrast is human painter recognition.

Preserve every original assignment position and actual start/completion timestamp.
Report group start spans and crossings between collector components. For all
eight original endpoint definitions, calculate descriptive estimates using all
selected images; omitting technical-retry groups alone (initial-only sensitivity);
omitting component-crossing groups; omitting groups with start
span over 120 seconds; and omitting boundary plus technical-retry groups. These
post-result deletions do not repair no-interference or become new tests. Retain
all refusal/retry and reported-quality dispositions. Assigned windows are not
independent sessions, and no arbitrary clustered sign permutation is substituted
for the original within-group assignment.

## Coverage and detector controls

Primary512/original31 only. Fix k to 1, 3 and 5; retain per-reference radii and
hits, including cross-class neighborhood composition. For 100 fixed-seed draws,
compare uniform generated sampling and class-stratified sampling at the full
reference count and half that count. The full allocation matches reference class
counts; half-size counts use deterministic largest-remainder apportionment.
All-available support is separate from probability-weighted distributions.

Construct 100 disjoint original-anchor/original-query positive-control draws,
paired with generated queries at the same per-class counts and identical anchor
radii. An altered anchor panel defines an altered neighborhood statistic: do not
compare it to the original k=3 score as though it were the same target. Where a
required radius or class support is unavailable, report that outcome rather than
silently changing k. These controls are not equivalence margins.

Report geometry, profile, delivered and parent dimensions, file-format metadata,
border flags, and source-proxy availability. The square/non-square metadata rule
is an explicit nuisance baseline, not proof that the existing feature classifier
uses shape. Descriptor associations are within domain/painter where defined;
they are neither causal adjustment nor a solution to absent common support.

Use fixed inherited linear/RBF kernels and ridge, six whole-brief folds, and
disjoint original works to test directed cross-route transfer for shared named
and artist-free conditions. Preserve memberships, per-fold counts/errors/AUC,
and pooled fixed-threshold balanced accuracy. Different fitted score margins do
not automatically share a calibration. No test-outcome tuning occurs. Verified
capture-workflow holdout is unavailable if provenance remains unresolved; a
holding-collection split must not be advertised as capture validation.

Fixed diagnostic seed: 2026090719, with stable named substreams; no seed shopping.
All specified variants, unavailable cases and contradictory directions are kept.
Tests use synthetic values and remain offline. Full results are checked against
the preserved primary energy/trace table and eight original all-selected contrasts.

## New-data decision and remaining validation

Generation is conditional on identifying a question existing outputs and better
references cannot resolve. Approximately $29.32 remains under the original $75
ceiling after conservative accounting of $45.6819185. This scope spends none.
A justified additional generation experiment would require a separate exact
request/assignment/rendering contract, source and budget freeze, before its first
POST; bounded staggered parallel calls and technical retries must preserve the
user's existing preferences. No terminal census can be reused.

The reference feasibility and human/representation plans are specified in
`VALIDATION_PLAN.md`. Any new work frame and sample size must follow source/content/
geometry support and a declared precision/power target. Distinct captures are not
additional physical works. Human judgments require actual consenting participants,
appropriate institutional review and a prespecified stimulus/rater design. An LLM
review is not human validation. Learned measurements require a separate scope and
remain optional for this interpretable-feature paper.

## Reporting and preservation

Commit compact JSON, tables and numerical figures under this namespace, retaining
portable paths and exact source/input identities. Figure generation may be written
after the diagnostic freeze only if it cannot modify the frozen calculations;
bind its code and input analysis in its own report receipt. Reproduce every
published numerical value and figure from the retained numeric records.

Write a revised English paper in a new paper directory and update canonical
navigation. Preserve the previous paper and reports as historical versions. The
new paper must distinguish original prospective findings, post-result diagnostics,
and unperformed validation. Review throughout is maintainer-run LLM review, not
institutionally independent assessment. Report numerical, raw-image and service-
regeneration reproducibility as different promises.
