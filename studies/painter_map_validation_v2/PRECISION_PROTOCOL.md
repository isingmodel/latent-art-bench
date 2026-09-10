# One R10 offline precision qualification after retained v1 failure

2026-09-10. Namespace `painter_map_validation_v2`; create-once qualification
identifier `pmvqv2-20260910`. **No formal R10 assessment or new image outcome has
been examined when fixing this protocol.** Only artificial arithmetic and
orchestration fixtures may run before review and a clean source commit.
[DECISION.md](DECISION.md) records why this is a disclosed, simulation-informed
pre-data redesign of the same question, rather than an outcome-blind design or a
claim that v1 succeeded. The implementing/reviewing agents are maintainer-run
LLMs with earlier variance/analysis/export involvement, not independent human
investigators. No collector, generation, feature extraction or live gate exists
in this qualification implementation.

## Retained predecessor and only change

The entire failed v1 record remains unchanged:

| Relative file under `studies/painter_map_validation_v1/pmvqv1-20260910/` | SHA256 |
| --- | --- |
| `RUN.json` | `944a8ea098b55d8ccb12c66f8b55dd55582456b080e0c77139f8100f4d0589e8` |
| `precision.json` | `ca5da6798dfc4c6056de6250320d85d1c17dffe1a0d274788d3ac8091557598a` |
| `PRECISION.md` | `c65ec527fd67289baefa7f52207a85778b84e818015546f703c589994c703555` |

Its recorded source is `eb70ab8c30019b4b283366c170f8bdaf1405a023`; its failed
result was committed at `9e3fd1a`. Verify all three exact artifact hashes, their
shared provenance, all twelve original source/input bindings against the old
source commit and current bytes, and the unchanged failed allocation decision.
No v1 simulation, output writer, exporter, protocol or source is altered or
rerun by this assessment.

The sole new candidate is **R=10**, twelve fixed scenes × two arms × ten paired
repeats, or **240 outputs** if eventually authorized. There are no R4/R6/R8
recomputations and no R12 or alternative candidate in this version. The candidate
was chosen after the v1 simulations and their narrow baseline Q precision
failure were known. The v1 failure and all reasons remain visible; the new
candidate is not presented as an allocation already permitted by v1.

## Exactly reused numerical contract

Incorporate the unchanged
[v1 precision protocol](../painter_map_validation_v1/PRECISION_PROTOCOL.md)
for every definition below except its three-candidate allocation and its
version/output provenance. Reuse the immutable v1 numerical functions directly,
without changing globals, monkeypatching parameters, refitting maps or copying
an alternative numerical implementation:

* The two pinned geometry numerical inputs, 32 equal-weight Cézanne references,
  unchanged 221-work primary512 scaler, full-original-FLUX Cézanne T1/T2 map,
  and all 31 coordinates. The stored scalar remains `.6785365094757265`.
* Historical mean proxies water01–04, built01–04, land01–04; explicit class order
  water/built/land with q=(3,11,18)/32 and scene weights q_c/4. These historical
  means are not the new authored scene briefs or noiseless service truths.
* Each arm's full weighted within-scene 31 × 31 covariance from all 24 original
  scenes/three repeats, including its fixed numerical PSD-root rule.
* All27 laws: three 64-point joint-support shapes × named mean at T1/midpoint/T2
  × baseline/high_positive/low_negative noise. Keep exact centering, block and
  mixed-eta covariance whitening, nominal coupling coefficients, stress
  multipliers and normalized class heteroscedasticity. They remain bounded
  discrete shaped laws and constructed coupling, not continuous distributions
  or an empirically validated joint service law.
* Support seeds `SeedSequence([2026091061,shape_index])`, fixed dimension 31 per
  arm and 64 joint support points. Reconstructed supports are independent of R;
  their exact hashes should match the corresponding v1 cell on matching
  numerical arithmetic. Do not change a codebook following a result.
* The full weighted empirical V-energy contrast E(T2F)−E(T1F) and untruncated
  distinct-repeat residual contrast Q(T2)−Q(T1). No map-label permutation,
  scene bootstrap, new endpoint, p-value family or interval fallback is added.

The Q estimand stays the difference in weighted squared conditional scene-mean
mismatch. **The E sampling estimand changes with R**. Let A be the exact twice
reference-distance contrast and D_jk the independent uniform support-pair
free/free distance from v1. With c=1−a,

    theta_E,10 = A + c [sum_jk w_j w_k D_jk − sum_j w_j² D_jj/10].

Thus it is the expected finite-R10 empirical V contrast, not the old finite-R8
contrast or an unbiased population-mixture energy. Q truth and its exact
sampling-variance audit use the unchanged formulas evaluated at R10. No nested
Monte Carlo estimates replace the finite-support truths.

## One interval, one 27-cell qualification

Use the unchanged paired, scene-stratified leave-one-repeat jackknife. Each
deleted scene has nine remaining pairs; only that scene's repeat weights and Q
denominator change. Use

    V_J(T) = sum_j 9/10 sum_r(T_-jr − mean_s T_-js)²,
    interval(T) = T ± t_(9,.9875) sqrt(V_J(T)).

This is the same approximate Bonferroni marginal construction; R10 does not make
it an exact service-coverage theorem. Nonpositive/nonfinite variances or
nonfinite points make the two-component family unavailable, counted as a
coverage miss with infinite half-widths. Keep negative point estimates and every
trial. Reuse the unchanged finite/nonfinite aggregate-diagnostic handling.

For each of 27 cells, run exactly 10,000 trials. Initialize
`default_rng(SeedSequence([2026091062,shape_index,mean_index,regime_index,10]))`.
R is already an explicit seed component;10 was absent from the v1 grid. Draw
12 × 10 joint support indices per trial in the same order and use the same 128-trial
batching. There is no empirical tuning/calibration of a critical value and no
alternative seed tried following failure.

Retain the one-sided Clopper–Pearson lower-bound tail **.05/81**, although this
version has only 27 cells, and require every coverage lower bound to be >=.94.
The passing count is still 9476/10000. Do not claim combined 95% Monte Carlo
coverage across the old 81 and new 27 checks, or use v1's passing coverage as a
substitute for any new check. The shared selected proxy laws and adaptive
cross-version planning remain disclosed.

Require all 27 coverage criteria, and **each of nine baseline cells** to have
median half-width E<=.25 and Q<=1.0. Full lengths are .5 and2. Report all stress
half-widths; they are not precision gates. These fixed planning tolerances were
informed by the scale of existing results; they are not meaningful-effect or
equivalence margins, and they provide no detection or actual-service precision
guarantee. None changes after qualification. Pass selects only R10/240 outputs
for possible later operational qualification. Fail stops this single additional
assessment: no R12, new proxy, method, threshold, seed or additional version to
obtain admissibility in the current revision. No generated outcome may cause
an extension, refill or replacement.

## Source binding and create-once execution

Bind this decision/protocol, v2 source/init/test, all twelve v1 source/input
bindings (including dependencies and package initialization), and all three
failed v1 outputs: twenty files in total. Before formal execution, working and
staged bytes must match a clean recorded source commit. Preserve the original
predecessor commit and exact artifact hashes in the v2 RUN/result records;
these record provenance, not independent authentication of absent pixels.

After parent review and commit, the sole formal entry point is:

    uv run --locked python -m latent_art_bench.painter_map_validation_v2.precision

It creates `studies/painter_map_validation_v2/pmvqv2-20260910/` once, writes a
RUN.json with bindings/runtime/predecessor before computing, then writes
precision.json and PRECISION.md. It rechecks current source, HEAD/index and
predecessor bindings after computation. Existing or interrupted output
directories are preserved and cannot be overwritten. Formal execution is the
parent's action; implementation tests must not sample historical R10 laws.

A pass is only evidence about the stated discrete historical proxy laws under
independent stationary repeats with fixed inputs. Proxy-estimation uncertainty,
new-scene generality, service drift, carryover, capture and perception remain
unqualified. An eventual live study still needs a separate source-tested,
prospectively frozen collection/measurement/analysis contract and actual budget
and credit gates. This module supplies no such permission or transport.
