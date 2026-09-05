# Painter Prompt Supplement v1 — available-output feature distances

Protocol ID: `painter-prompt-supplement/1.0`. Specified on 2026-09-05 **after the first
service refusal and before the registered measurement of new generated images**. This is an
explicitly post-registration analysis supplement, not the original prospective primary analysis.
It authorizes no image request, retry, replacement, feature extraction or reference access.

## 1. Reason, scope and preservation

The approved source run is `pps1-gpt-prompts-20260905`: 1,920 registered requests, two requested
OAuth aliases, three prompt methods, four named painters plus an artist-free control, 16 scenes
and four repetitions. Its 416th request (zero-based sequence 415, Camille Pissarro, `by_name`,
`gpt-image-1`, block 0, scene L3) received HTTP 400 with `moderation_blocked`. The retained response
is an input-moderation refusal, not an image-decoding error. It is retained in its original slot.

The original protocol requires a completely measured grid for primary inference. Its source,
freeze, ledgers, measurement and report remain unchanged; its primary result is unavailable
when any slot lacks a measurement. The supplement does not repair that result or describe its
own tests as preregistered. Its purpose is still to compare generated-image features with the
original painters' measured paintings while documenting missingness honestly.

No additional images are requested. No numerical feature result from the new run is used to
choose an endpoint, reference, feature, weight, seed, threshold or reporting subset. The same
universal rules apply to every condition, family and transition. A supplement freeze must be
committed before the source measurement ledger exists. It binds the observed generation-ledger
prefix, source freeze, this contract, config, qualification and implementation. The prefix
documents known operational outcomes; absence of a registered measurement ledger does not
establish institutional blinding or prove that every possible out-of-band access was prevented.

## 2. Fixed representation and complete reporting inventory

Use the 649 exposed confirmation paintings and the unchanged scaler fitted to 221 new-development
paintings. Reuse the same 512-short-side normalization and all 31 color, spatial/orientation and
digital-texture coordinates already produced by the source measurement stage. Read only its
terminal numeric records. Never remeasure an image or insert historical generated outputs.

Retain all 1,920 request dispositions, 30 cell availability rows, 480 template availability rows,
360 generated-condition/reference-painter/family distance cells, 72 named target distances,
744 coordinate diagnostics, 48 adjacent paired contrasts, 72 descriptive secondary contrasts,
all planned pair-support and chronological-contribution rows, and 48 order diagnostics.
Unavailable cells/endpoints retain their identities and explicit reasons. Nothing is removed
because of a large distance, unusual feature, unfavorable contrast, duplicate or p-value.

The aliases are requested service labels with no attested model snapshots. The paintings are
fixed measured digital surrogates in the exposed outdoor-place frame, not complete oeuvres.
Service geometry/quality/profile differences, source limitations and exact/perceptual copy
screens remain reported. A perceptual screen is not a finding of copying or its absence.

## 3. All-available descriptive distributions

Within each alias/method/condition, let `m_t` be the number of measured outputs for scene `t`.
If every one of the 16 scenes has `m_t >= 1`, each successful output has weight
`w_i = 1/(16*m_t)`. Each scene therefore retains weight 1/16, even when completion counts differ.
If any scene has no measured output, retain the entire cell as unavailable. Do not renormalize
over fewer scenes, invent missing features or copy another repetition's output.

For a uniform reference of `N` paintings and generated weights summing to one, use weighted
finite V-energy

`D(Y,R) = 2 sum_i w_i mean_r d(Y_i,R_r) - sum_ij w_i w_j d(Y_i,Y_j) - mean_rs d(R_r,R_s)`.

Distances use Euclidean norms within each original scaled feature family. They describe the
actually successful outputs with explicit scene weights; they do not identify the feature
distribution of failed requests or a population that would always return an image.

Coordinate medians and IQRs use weighted empirical inverse-CDF quantiles for **both** generated
and reference distributions, with uniform reference weights. This differs from the earlier
linear-interpolation coordinate quantiles. Declare that distinction; do not attribute numerical
differences caused by the quantile convention to image generation. All 31 coordinates remain.
For quantile accumulation, use integer reference masses of one and generated masses `12/m_t`;
these are proportional to the same weights and avoid floating-point cumulative boundary shifts.

The 48 named-minus-control adjacent differences-in-differences and 24 overall
`style_aspects - by_name` comparisons use these all-available distributions. They are descriptive,
with no confidence intervals, causal labels or significance tests.

## 4. Paired support and exploratory joint-null tests

For each alias/painter/adjacent-method comparison, pair the original requests by scene and
repetition. A pair is eligible only when both slots have terminal measured features. For each
scene, count eligible pairs `m_t`. Every scene must have at least one pair; otherwise retain all
three family endpoints as unavailable. Eligible pairs use `w_i = 1/(16*m_t)` for both methods.
Retain every planned pair in the support table, including missing slots and successful counterpart
images not used in this particular paired contrast. They still enter their own all-available cell.

Compute separate before/after weighted distances on this identical paired support. Their
difference is the paired contrast. It generally differs from subtracting all-available distances,
which use different supports and weights. Display the paired distances and support counts
alongside each contrast; never mix the two estimands.

Conditional on the source design's third-method positions, exchange the two tested methods
within each eligible scene/repetition pair. The null is the **joint sharp absence of any method
effect on measured feature outcomes AND availability**, with no interference between requests,
or a justified joint invariance under the complete allowed swap group. Under this null, slot
outcomes and availability are fixed under counterfactual assignment, so the eligibility mask
and scene weights are unchanged after each permissible swap. Merely relabeling observed rows
symmetrically is not sufficient justification when counterfactual availability can change.

Prompt-dependent moderation can violate the availability component. Consequently, rejection
cannot be attributed specifically to a change in feature distance rather than availability.
These tests do not recover a population feature effect, an always-successful principal stratum,
or the images that were never returned. A failure to reject does not establish equal styles,
equal feature distributions or no availability effect. Conditional inference also requires the
source randomization and no-interference assumptions; metadata cannot prove them.

For paired `A_i,B_i`, define `r(X)=mean_r d(X,R_r)` and
`s(X)=sum_j w_j[d(X,A_j)+d(X,B_j)]`. Then

`c_i = 2*w_i*(r(B_i)-r(A_i)) - w_i*(s(B_i)-s(A_i))`.

The observed weighted contrast equals `sum_i c_i`; every permitted swap changes only the
corresponding coefficient sign because the weighted pooled distribution stays fixed. Verify
this against direct weighted energy recomputation and counterfactual triplet allocations.

Use the unchanged source randomization engine: exact enumeration at up to 16 eligible pairs,
otherwise 99,999 uniform seeded sign vectors plus the observed assignment. Count ties
conservatively, using `(1+extreme)/(1+draws)` for Monte Carlo tests. Retain the original fixed
permutation seed with canonical endpoint derivation; never search or rerun seeds for significance.

Keep all 48 adjacent endpoints in one Holm family at alpha 0.05. An unavailable endpoint
contributes 1 solely to the adjustment calculation; report its raw and adjusted test as
unavailable, with an explicit `holm_input` placeholder. No test family is reduced after missingness.
There are no confidence intervals or equivalence claims. The tests remain exploratory even if
their mathematical and software qualification passes; qualification does not restore preregistration.

## 5. Qualification before supplemental inference

Publish a separate immutable qualification against clean committed code. Required checks include
unequal-weight brute-force energy/swap identities, uniform-weight reduction, ties/zeros, and an
exhaustive triplet-allocation oracle with filtering and scene reweighting performed **after**
each counterfactual allocation. Enumerate conditional third-slot strata and check the full
null p-value distribution, including unavailable templates.

Synthetic full-family checks cover complete support, a fixed missing slot, strongly unequal
scene completion, and a wholly unavailable template, with independent and shared-family endpoint
dependence. Development seed is 20260910 and unseen validation seed is 20260911, each with
2,000 trials per prescribed valid-null cell. Every valid development and validation cell must have a Wilson 95%
upper bound on family-wise rejection at most 0.065. Keep a method-dependent-availability stress
case with unchanged feature potential outcomes to show the danger of a feature-only interpretation.
Do not tune failed cases or hide them. The validation module fixes the complete case inventory
before any synthetic result is published.

Exact weighted-sign convolution and Binomial Monte Carlo exceedance sampling may accelerate
these contribution-space constructions. They are not simulations of image generation or proof
of remote-service assumptions; actual engine and assignment-level checks remain separate.
Supplemental p-values require a passing qualification. No inspection of this run's new generated-image
feature measurements precedes the qualification and supplement freeze.

The random-transform justification follows [Hemerik and Goeman](https://pmc.ncbi.nlm.nih.gov/articles/PMC6405018/).
The counterfactual missingness distinction is discussed by
[Heng, Zhang and Feng](https://pmc.ncbi.nlm.nih.gov/articles/PMC12380393/).
The weighted coefficient derivation and this specific conditioning argument are study-specific
extensions, not claims that those sources validated this image service or this sample count.

## 6. Reproducibility and reporting

Verify the original terminal numeric analysis and report before building this supplement.
Bind all consumed features, dispositions, source references, frozen config, qualification and
implementation by relative path and SHA-256 at the recorded commit. Build a separate report
under `reports/painter_prompt_supplement_v1/`; publish no replacement of the original report.

Export full-precision numeric tables and deterministic PNG/SVG comparison plots. Replay the
complete supplemental numerical analysis and all report bytes from retained numeric evidence,
without contacting the provider, reading image bytes or changing a study ledger. The final
evidence audit must distinguish original primary availability from supplemental conclusions.
Reviews are maintainer-run LLM subagent reviews, not institutionally independent review.
