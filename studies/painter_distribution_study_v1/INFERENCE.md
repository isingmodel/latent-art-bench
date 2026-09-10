# Conditional prompt inference and qualification — 2026-09-06

This contract is prospective for new research generation. No new research image
or fresh reference fidelity vector has been measured. Technical pilot outcomes
are excluded. It defines a limited inferential claim suited to the actual design,
not a promise of population confidence intervals from a small collection.

## Estimands and assignment

The main comparison target is the finite visually eligible reference panel,
with weights fixed before feature measurement. Absolute original/generated
energy discrepancy, spread, coverage and grouped detection scores are descriptive.
Report sample-matched disjoint original baselines, content sensitivities and
leave-window/leave-brief summaries; label their ranges as sensitivities rather
than population confidence intervals. No painter-oeuvre equivalence claim follows.

The **eight inferential endpoints** are all-31 energy changes from artist-free to
named generation for each of three routes and two painters (six), and from generic
named to detailed named prompting on OAuth for the two painters (two). Negative
changes mean smaller finite-reference energy discrepancy. The same reference,
content support and pair weights must enter both conditions in a contrast.
Feature-family and cross-model contrasts remain secondary descriptive results.
Never select an inferential endpoint after inspecting its effect or significance.

For each route × painter × brief × repetition, randomly assign the two conditions
to their request positions. OAuth has three conditions; uniformly permute all
three, and condition on the third condition's position when comparing a pair.
Assignment units are independently randomized prospectively. Interleave routes
and distribute each brief's three repetitions among distinct collection windows.
At least eight windows span multiple days. No assumption of eight independent
backend sessions is inferred from this schedule.

The randomization null is **no prompt effect on both availability and measured
features in any assignment position, with no interference**. It is not merely
equal expected energy distances. Arbitrary fixed reference values, scene
heterogeneity, window drift and endpoint dependence are allowed under that sharp
null and the actual random assignment. Service carryover or treatment-dependent
request duration may challenge no-interference; report that limit explicitly.
The tests do not isolate aesthetic, semantic or purely stylistic mechanisms.

## Weighted statistic and failures

Let each retained matched pair have probability weight b_i and each fixed
reference work have probability weight a_j. Write A/B for the two conditions,
C(v)=sum_j a_j ||v-x_j|| and
T(v)=sum_i b_i (||v-A_i||+||v-B_i||). The contribution is

```
c_i = b_i [2(C(B_i)-C(A_i)) - (T(B_i)-T(A_i))].
```

The sum is exactly V-energy(B,reference) minus V-energy(A,reference), including
within-generated terms. Complementary pair swaps give `sign @ c` exactly.
The implementation is checked against direct weighted energy under all swaps
of a small unequal-weight example; no centroid approximation is used.

Use complete measured pairs only in the inferential contrast, preserving every
excluded pair and its disposition. Renormalize to the fixed content weights on
common support; if a required class is absent, or fewer than 12 distinct briefs
or 24 pairs survive, mark that endpoint unavailable and retain p=1 in the eight-
test multiplicity family. All-available descriptive distributions remain separate.
This common-pair procedure concerns the joint availability/features null. It does
not establish a feature-only effect in a population with differential failures.
Each randomized request position is a slot. Under the user's subsequent retry
instruction, the main contract may assign a fixed, bounded technical retry policy
to that slot before collection. Analyze its first valid returned image and retain
the initial-only result as a sensitivity. A retry uses a distinct request identity
and disjoint response path linked to its failed predecessor. Never retry a valid
image, choose among successes, impute an image or extend sampling after inspecting
an effect. The assignment null applies to the entire fixed slot policy, including
availability; the retry policy does not establish independent service responses.

Use 99,999 independent Monte Carlo sign draws per endpoint, fixed endpoint seeds
declared in the final design, a two-sided absolute statistic and the conservative
`(1 + exceedances)/(1 + draws)` p-value. Include numerical ties conservatively.
Apply Holm adjustment to the fixed family of eight p-values, alpha=0.05. Preserve
both raw and adjusted values, contribution vectors and exact pair membership.
Do not attach these tests to the earlier retrospective refusal replacements.

## Prospective qualification

Commit this method, implementation and tests before preparing the qualification
freeze; commit that freeze before computing the synthetic checks. Use distinct
fixed development and validation seeds 2026090601 and 2026090701, without tuning.
Each phase has 10,000 trials in each of 24 valid-null cells: 24/48/72 pairs,
constant/content-weighted/window-drifting/rare-large contribution magnitudes,
and independent or shared endpoint assignment signs. These represent the planned
24 briefs × three repetitions and smaller common-pair supports after attrition.
Window weights use the eight-window layout. Reference size/values are conditioned
on, so this qualification does not estimate uncertainty from sampling an oeuvre.

Integer contribution magnitudes permit an exact finite Rademacher tail by
convolution. Conditional Monte Carlo exceedances are sampled from their exact
Binomial(99,999, exact-tail) law; this is an efficiency identity, not a normal
approximation. The shared-endpoint construction probes multiplicity dependence.
Holm allows arbitrary dependence when each marginal p-value is valid.

Every valid-null cell in both phases must have Wilson 95% Monte Carlo upper bound
at most 0.065 for family-wise rejection. Failure withholds the inferential label;
the planned descriptive study can still proceed. No threshold or seed is changed
to obtain a pass. Synthetic checks do not prove the live service assumptions.

Also report illustrative power for coefficient-sign probabilities .55, .65 and
.75 at 72 pairs. These are hypothetical contribution-space alternatives, not an
image-space effect size or evidence that 72 images have adequate power for the
scientific hypothesis. Include an intentionally invalid assignment construction
that synchronizes signs within windows but analyzes individual pairs; it illustrates
why collection windows and nominal image counts cannot substitute for the actual
randomization design. That invalid cell is not part of the pass criterion.

No image-level bootstrap interval or calibrated absolute distribution-equality
test is claimed by this qualification. Human construct validation and population
coverage remain separate research questions.
