# Reference-calibrated selective attribution v1

Written 2026-09-21 before computing any new selective-attribution outcomes.
This is a retrospective extension of the already inspected four-painter cohort.
Earlier baseline confusions, mean-translation outcomes and scientific reviews
were known when this question was chosen. A new frozen analysis does not turn
these observations into an untouched or independent confirmation.

## Question, fixed scope and information budget

Can ambiguity calibrated using historical artworks identify generated
prompt-name attributions that should be withheld? The practical action is to
issue the existing top-1 reference-prototype attribution or abstain. This is a
standard selective-classification diagnostic, not a new algorithm. It does not
estimate perceptual fidelity or physical authorship.

Retain the complete 1,008 generated images: six requested configurations, 14
scenes, two repeats and six clauses (free, generic oil painting, Monet, Sisley,
Pissarro, Cezanne). Every configuration has 112 named images and 28 images in
each control arm. No generated painter label is used to fit the gate. Known
named/control arm membership is used for evaluation and to define the margin
comparator's query pool, but never to select a favorable outcome subset.

Use the fixed CLIP and CSD retained unit embeddings and the exact already
recorded reference memberships and audited-region replacements. Retain all
eight encoder x view x prototype-panel settings:

- Encoders: CLIP and the released native CSD checkpoint.
- Views: original and audited_region. A region replaces its corresponding
  original only where a previously declared region exists; all other originals
  remain. Generated images receive no region substitution.
- Prototype panels: primary (649 works) and development (221 works). Calibrate
  on the *other* partition in the same view. The primary painter counts are
  297/106/141/105; development counts are 101/36/48/36. Audited replacements are
  41/23/13/13 and 17/7/11/6, respectively, in the frozen artist order.

**Primary setting: CSD / original / primary prototypes, with development
calibration.** All seven other settings are sensitivities, never substitutes
for an unfavorable primary result. All six configurations and all four artists
remain in each setting. The existing 2,009-row embedding archives comprise
1,878 originals and 131 region replacements; do not re-extract pixels or load
weights. An incomplete or inconsistent census stops the analysis, not a model
or artist deletion. No paid calls, downloads or new images are involved.

## Numerical rule, fixed alpha and ties

Artist order is Monet, Sisley, Pissarro, Cezanne, using the established machine
IDs. For each artist a, form the raw mean of the prototype-panel unit vectors,
then normalize that mean to unit direction u_a. Zero or nonfinite prototype
means are errors. Keep these prototypes fixed across all configurations and
all scene-deletion summaries.

For an image x and candidate a define

    score_a(x) = dot(x, u_a)
    s_a(x) = max_{b != a} score_b(x) - score_a(x).

For calibration works with recorded artist a, sort their s_a values. Fix
alpha = 0.10 with no search. Set k_a = ceil(9(n_a + 1)/10), calculated with
integer arithmetic, and q_a to the k_a-th smallest value (one-indexed). Do not
interpolate quantiles. If k_a > n_a, q_a is positive infinity; its JSON value
is null with an explicit infinite-threshold flag. An empty calibration class
is an error rather than an infinite threshold.

For a generated query form C(x) = {a: s_a(x) <= q_a}; equality is included.
The baseline top-1 prediction is the maximum score, resolving exact ties by
the first frozen artist index. Accept this unchanged prediction **only if
C(x) consists of that one predicted artist**. Otherwise abstain. Preserve
empty sets, multiple-label sets and singletons disagreeing with top-1 as
separate abstention reasons. Record score ties and all candidate membership.

The use of this calibration quantile does **not** establish a conformal
coverage guarantee for generated images. Historical and generated images are
not established as exchangeable; the calibration labels concern historical
artists while generated evaluation concerns recorded prompt clauses. This
experiment tests transfer of a diagnostic under that task/domain change.

## Coverage-matched margin comparator

The ordinary margin is the largest prototype score minus the second largest.
Within each configuration's 112 named queries, let K be the number accepted by
the reference gate. The comparator accepts exactly K queries with the largest
ordinary margins, breaking ties by ascending frozen observation ID. Predictions
are still the unchanged top-1. Report the cutoff value, boundary observation ID,
number tied at the cutoff and number of those ties included.

This comparator is transductive: its cutoff uses the current named-query
margin distribution and the reference gate's K, but not the true artist
correspondence or observed errors. It is a descriptive equal-coverage benchmark,
not a deployment rule learned solely from historical works.

For control queries, apply the resulting **numeric cutoff inclusively**,
margin >= cutoff, and record the number of equality ties. The ID tie rule is
used only to achieve exact named-pool coverage, not to split control ties. If
K=0, both comparator named and control acceptances are zero and no numeric
cutoff is defined. If K=112, the cutoff is the smallest named margin, which
still need not accept every control. Controls do not set the cutoff.

## Fixed hypothesis, endpoints and joint usefulness criterion

Hypothesis: the reference-calibrated gate concentrates generated prompt-name
errors in its abstained set enough to lower attribution error while preserving
useful named-image coverage, beyond ordinary margin filtering.

For every setting/configuration retain all observation IDs, scores,
nonconformity values, set memberships, top-1 predictions and both gates. Report:

- Accepted counts and coverage overall and for every prompted artist.
- Total, accepted and abstained correct/incorrect counts and confusion matrices.
- Unrestricted, accepted and abstained error rates against prompt-name labels.
- Separate frequencies of each abstention reason and exact top-score ties.
- Baseline-minus-gate accepted-risk reduction and margin-minus-gate
  accepted-risk reduction; positive values favor the reference gate.
- Separate gate and comparator named-attribution rates for the artist-free and
  generic-oil control arms, including per-predicted-artist counts and ties.

Risk with zero denominator is **undefined (JSON null)**, never zero. An
equal-configuration mean is undefined if any of its six values is undefined;
do not silently average a subset. Preserve the undefined configuration and
failure reason. Overall risk is image-weighted within a configuration;
cross-configuration means weight each of the six configurations equally.
Painter-specific coverage/risk is always shown to expose selective class loss.

The primary setting meets the **joint descriptive usefulness criterion** only
if all of the following hold:

1. Gate named-image coverage is at least 50% in **each** configuration.
2. At least one observation from **each** prompted artist is accepted in each
   configuration.
3. The equal-configuration mean baseline-minus-gate accepted-risk reduction is
   strictly positive.
4. The equal-configuration mean coverage-matched-margin-minus-gate accepted-risk
   reduction is strictly positive.

Missing/undefined required means make criteria 3/4 false, with an explicit
missing-mean failure. List every failed criterion. Apply the same bookkeeping
to sensitivities, but they cannot replace the primary verdict. These thresholds
are operational decisions fixed before this new analysis, not p-value cutoffs.
Retain every adverse configuration even when a mean improves. No new scoring
or scientific-review outcome is promised.

Control acceptance means an attribution was issued although none of the four
names was explicitly requested. It is **not** an error against a human style
judgment and does not prove the image lacks resemblance to a named artist.
Do not silently turn abstention into a fifth validated visual-style label.

## Scene-deletion influence and limitations

Delete each of the 14 complete scenes in turn, retaining both repeats and all
six arms in the remaining scenes. Keep reference prototypes, calibration and
per-image reference gate decisions fixed. Recompute the margin comparator on
the remaining named queries to match that deletion's K. Report the deletion
endpoints, equal-configuration reductions, joint criteria, and complete ranges.
A range is undefined if any deletion value is undefined; report missing counts.
These are finite-design influence summaries, not confidence intervals or
independent tests. No p-values or claims about unseen prompts/sessions appear.

A successful result would support a bounded decision aid on this fixed cohort.
A negative result must remain negative; do not tune alpha, replace the score,
choose favorable artists/representations, or launch alternative gates to erase
it. Neither outcome resolves shared-family causality, service dependence,
perceptual validity, encoder training overlap or the lack of fresh observations.

## Verification, freeze and execution boundary

Pure constructed tests must cover quantile rank/equality, all abstention
reasons, ties, harmful and helpful selective outcomes, exact margin coverage,
control cutoff semantics, painter loss, zero acceptance and undefined means,
scene deletion, source membership/crops, invalid/missing vectors and identities,
input tampering and create-once outputs. Do not read real arrays from tests.

Before real execution, freeze this plan, implementation, tests, interpreter/
NumPy versions, the retained row manifest, both archives, extraction receipts
and the full historical binding chain. The hash-only freeze must never load
embedding arrays or calculate new selective outcomes. Require an externally
recorded SHA-256 of the freeze when loading, and validate bytes before parsing.
Real execution requires a subsequent independent method/code audit and an
explicit execute-real flag. Its external audit JSON must report passed, bind
the exact frozen-input digest and the exact plan/implementation/every constructed
test, and match a separately supplied audit digest. Keep the audit external to
the pre-audit freeze to avoid a circular hash. Execution and replay require
the recorded Python and NumPy versions exactly. Output creation is exclusive;
replay verifies the same complete report. Preserve earlier freezes if pre-outcome
audit amendments are needed. Never rewrite any earlier scientific analysis or
manuscript.
