# Prospective painter family controls: implementation draft

## Status and authoritative design

This is an **uncollected, unscheduled, unauthorized prospective study**. It is
separate from every completed collector and analysis. Nothing in an offline
simulation changes the approved cumulative ceiling of strictly below $120 or
the retained historical accounting of $112.293676. There is no live transport.

The complete design is the [v2 proposal](../../reports/icml_review_v1/prospective_controls_v2.md),
as superseded by the [v3 corrections](../../reports/icml_review_v1/prospective_controls_v3.md).
Preserve both documents and the [independent methods audit](../../reports/icml_review_v1/prospective_controls_method_audit.md).
The source of exact scenes, suffixes, payload descriptions, axis labels and
within-window assignment order is
`src/latent_art_bench/painter_family_controls_v1/protocol.py`.
Historical payload descriptions do not establish current service availability.

The allocation remains six configurations, all four painters, 12 authored
outdoor scenes, eight arms and eight windows: **4,608 assigned images**. Arms
are free, generic painting, generic style framing, the name-free historical
family phrase, and Monet, Sisley, Pissarro and Cezanne. Each window contains
576 globally interleaved assignments. Relative starts are 0, 8, 24, 32, 48, 56,
72 and 80 hours, with four hours for dispatch per window. Two windows per day
are not eight independently sampled days. No absolute start is frozen.

## Analysis contract

The primary array has axes `(configuration, window, scene, arm, feature)` with
prefix `(6,8,12,8)`. Model, painter, scene and arm order must be bound to the
assignment and feature manifests; an array's shape alone does not authenticate
its membership. Use fixed unit encoder outputs and raw, unnormalized painter
reference means. Never silently renormalize, impute, replace a scene, pool old
and new outcomes, or change equal scene/window/painter weights.

For each configuration and window, average the 12 fixed scenes. The CSD primary
endpoints are `N`, named-minus-generic diagonal prototype gain, and
`T = F - 0.5 N`, where `F` is the name-free family-minus-generic gain. Keep the
family at 12 endpoints even when another configuration is incomplete. Use the
prespecified two-sided 95% Bonferroni Student intervals with seven degrees of
freedom, conditional on independent, suitably behaved window summaries. A
positive lower bound for both N and T satisfies the declared operational
criterion; positive N and a negative upper bound for T contradict that
criterion. Boundaries touching zero are unresolved.

All eight windows must contain the complete primary arms for a configuration
to receive a primary decision. Failures in free/framing arms remain secondary
missingness. Report the full missing census, every window value, times,
leave-one-window influence and assumed correlation sensitivities. Available
secondary contrasts use only their actual required arms: missing generic does
not erase `C_F`, `N-F` or `F-S`, in which it cancels algebraically.

Ratios are ratios of eight paired window averages, not means of window ratios.
Fieller sets retain paired covariance, negative/zero denominators, disconnected
or unbounded sets, and adverse values. Stable inversion must cover nearly
proportional observations and weak denominators; neither numeric clipping nor
a narrow-set tolerance is permitted. These secondary sets carry no additional
familywise claim. Report reference contrast energy as both the historical
sum `H = sum_a ||mu_a - mu_bar||^2` and its painter mean `H/4`, explicitly named.

The name-free prompt tests an operational comparator as a whole. It does not
identify causal mediation within the named prompts or establish perceptual
fidelity. The cross-session squared-error comparison was removed by v3.

## Old-to-new recognition control

Use the fixed primary 649-image full-frame reference target and both fixed
encoders. Fit one scale-one translation and four generated prototypes per
configuration from **all old 14 scenes, two repeats and four names** only.
Prepare and bind these parameters before any new outcome is observed. Their
preparation is not a complete study freeze or evidence of prospective success.

Apply the frozen baseline, translated and supervised-generated rules to every
new named query, with no new-query fitting or parameter selection. Retain
scores, exact ties, truth-minus-best-other margins, paired corrections/harms,
per-painter confusions/recall, and incomplete panels. Original encoder queries
must be unit vectors. A translated zero query is retained with its zero scores,
explicit flag and first-painter tie resolution. Missing cells never turn into
zero queries. Source hashes and parameter identity require a bound artifact
loader in addition to the pure array functions.

## Collection and offline qualification

`collector.py` is an offline state machine; construction denies starts unless
explicitly simulating finite in-memory fixtures. No authentication, HTTP,
image-URL retrieval or production scheduler exists. It must preserve exact
requests/order/windows, durable accounting, exclusive ownership, original image
bytes, bounded gzip responses, technical failure evidence and terminal census.
Unknown costs retain $5 reservations and pause; they never imply zero cost.
Five-second starts, at most three active attempts, within-window retries,
20/60-second delays, two retries per slot and 96 total remain fixed.

The new namespace's tests and independent audit reports establish only the
constructed behaviors they actually exercise. The full-grid qualification
script uses a synthetic clock, solid-color PNGs, mock $0.01 charges and mock
100 GiB capacity. Its $350 policy is strictly a fixture parameter. Retained
qualification ledgers are labeled simulation; they must never be imported as
study observations. The script removes only its own temporary fixture files.

## Work still required before a complete freeze

- Resolve the pending resource decision: proposed cumulative ceiling $350 and
  an actual writable destination with at least 40 GiB free. The proposal is not
  approval, and the present local volume is below the unchanged 5 GiB floor.
- Verify current routes and prices; a material route/configuration change
  requires a new precollection decision, not a silently mixed cohort.
- Finish independent remediation checks, archive exact qualification evidence,
  and bind future live transport/scheduler behavior to this offline contract.
- Bind extraction manifests, checkpoints, preprocessing, row-to-axis assembly,
  all reference views and existing development-panel sensitivities. The array
  analysis code alone is not a complete extraction/reporting pipeline.
- Resolve the remaining 31-feature secondary specification before collection:
  v2's cross-repeat squared-change quantities cannot silently become ordinary
  within-window squared changes. Those have different noise contributions, and
  cross-window changing means present the same difficulty identified in v3.
  No replacement estimand or corresponding result is claimed here.
- Freeze absolute UTC windows, approved financial/storage settings, exact
  assignments, analysis/test/runtime hashes and old transport artifacts before
  the first new request; measure features only after terminal closure.

The prospective evidence does not yet exist. No reviewer rescore, ICML
acceptance claim, public exact-pixel release, or achievement of the requested
mean above 8.2 follows from this implementation draft.
