# Fixed-map offline precision qualification protocol

2026-09-10. Namespace `painter_map_validation_v1`; qualification identifier
`pmvqv1-20260910`. **Prospective qualification contract, fixed before the formal
simulation; no collection gate is open.** [DESIGN.md](DESIGN.md) defines the new
question and its relationship to permanently closed cohorts. This document
specifies one interval candidate and its allocation decision, not a choice among
methods after examining qualification output. No formal qualification has been
run while preparing this protocol. Tiny artificial unit/oracle checks qualify
arithmetic only. Maintainer-run LLM agents advise, implement and review this work;
they are not independent human investigators. The implementing reviewer also
contributed earlier variance/analysis and public-replay code.

## Inputs, panel proxies and unchanged maps

Only these historical numerical inputs may supply the proxy:

| Relative path | SHA256 |
| --- | --- |
| `data/manifests/painter_naming_geometry_v1/pngv1-20260910/inputs.json` | `eeb3890268a85885f372bdb494e29ab558c271749667fb7e264a7e30881733de` |
| `data/manifests/painter_naming_geometry_v1/pngv1-20260910/analysis.json` | `f50be0f772a3bff8f4bc66ddc20f3e19b5c13736fd6cced632d80224e2203324` |

Take original `primary512 / flux_2_max / paul_cezanne`, the unchanged 32-work
primary512 Cézanne reference with equal 1/32 reference weights, and the bound
primary512 221-development-work scaler. Input vectors are already in that
scaler's coordinates; do not scale them again. The single matching transfer
`fitted` record supplies the full-original-cohort free/named means and scalar
`a=0.6785365094757265`. Set T1(f)=f+muN−muF and
T2(f)=muN+a(f−muF). No map, scaler, reference objective or feature weight is refit.
The stored original generated vectors, not the later evaluation vectors or
any clause/new-scene outcomes, supply the following proxy construction.

The explicit class order is **water, built, land**, with masses
q=(3,11,18)/32. The twelve proxy scene IDs, in order, are water01–04,
built01–04, land01–04. Their free means average the three old repeats. These
are deterministic historical mean proxies, not the new authored briefs and not
independent, noiseless estimates of service means. Each scene weight is q_c/4;
the finite-R collection has R paired free/named repeats with weight w_j/R.
Candidate R=4,6,8 gives 96,144,192 outputs. New scenes are fixed, not sampled from
a scene population; scene resampling is prohibited in this qualification.

Estimate each arm's 31×31 noise covariance from **all 24 original scenes**:

    Sigma_arm = sum_j (q_class(j)/8) S_arm,j,
    S_arm,j = sum_r (Y_jr−Ybar_j)(Y_jr−Ybar_j)' / (3−1).

This preserves historical within-arm feature covariance, not only marginal
variances. It remains an uncertain R=3 historical proxy; it does not identify
future service noise or preserve its joint F/N dependence. The symmetric PSD
square root uses `numpy.linalg.eigh`; negative eigenvalues below
−1e−12 max(1,max|eigenvalue|) fail. Only smaller floating-point negative values
are set to zero for this covariance square root. This is not truncation of Q,
B*, an effect estimate or an inferential variance.

## Twenty-seven exact finite-support laws

Three shapes × three named-mean positions × three noise regimes are all
specified below. Each scene/repeat independently selects one of 64 *joint* F/N
support points uniformly; within a pair the same support index selects both
arms. Shared codebook values across scenes do not create dependent draws.

For shape index sh=0,1,2 initialize NumPy `default_rng(SeedSequence([2026091061,
sh]))`. Draw a 64×62 matrix, splitting columns into U,V of width31:

1. standard normal;
2. independent t with 5 degrees of freedom, multiplied by sqrt(3/5);
3. exp(Z), with Z standard normal.

For **each block separately**, subtract its column means and symmetrically
whiten its population covariance C=Z'Z/64: Z C^(−1/2). Fail if the smallest
eigenvalue is <=1e−12 max(1,largest). Whitening defines the finite support; these
are Gaussian-shaped, t5-shaped and lognormal-shaped laws, **not continuous
Gaussian/t/lognormal laws**. In particular their tails are bounded by the
committed support. Do not substitute a new codebook if one is inconvenient.

| Regime | SD multiplier m | Nominal F/N mixing rho | Scene SD factors h |
| --- | ---: | ---: | --- |
| baseline | 1 | 0 | all1 |
| high_positive | 2 | .75 | water .5, built1, land2, normalized below |
| low_negative | .5 | −.5 | same normalized factors |

For either stress regime divide h by sqrt(sum_j w_j h_j²). Construct
eta=rho U+sqrt(1−rho²)V, then **center and fully whiten eta again**, using the
same rule. With symmetric covariance roots L_F,L_N, the supports are

    F_js = muF_j + m h_j (U_s L_F'),
    N_js = muN_j + m h_j (eta_s L_N').

Thus each arm's within-scene covariance is (m h_j)² Sigma_arm, to floating-point
precision. The coefficient rho is not the resulting exact correlation: the
finite support has incidental cross-block covariance and eta is whitened.
Baseline and stressed dependence structures are constructed proxies, not a
claim that empirical F/N joint noise has been preserved.

Mean index 0,1,2 sets muN_j to T1(muF_j), their midpoint, or T2(muF_j).
Consequently Q truth is respectively positive, zero, or negative weighted
squared separation of the mapped means. All resulting E truths are retained;
no reference/free mean is selected or altered to manufacture an energy ranking.
The grid does not cover arbitrary new-scene means, drift, carryover or tail laws.

## Statistics and exact truths

The two retained statistics are the full empirical weighted V-energy contrast
Ehat=E(X,T2F)−E(X,T1F), including its self diagonals, and

    Qhat = sum_j w_j sum_{r != s}
            [e2_jr' e2_js − e1_jr' e1_js] / [R(R−1)],
    ek_jr=N_jr−Tk(F_jr).

Do not truncate negative Q. Maps are deterministic transformations, not randomized
treatments; no map-label permutation is justified. The E sampling target is its
**finite-R expected empirical contrast**, not an unbiased population-mixture
energy. For uniform support let

    A = 2 sum_ijs p_i w_j/64
          [||x_i−T2(F_js)||−||x_i−T1(F_js)||],
    D_jk = sum_st ||F_js−F_kt|| / 64².

Support draws in D_jj are independent and may select the same support index.
With c=1−a, exact finite-sum truths are

    theta_E,R = A + c [sum_jk w_j w_k D_jk − sum_j w_j² D_jj/R],
    theta_Q = sum_j w_j [||mean(N_j)−T2(mean(F_j))||²
                         −||mean(N_j)−T1(mean(F_j))||²].

The finite-R E bias relative to mixture energy is
(a−1) sum_j w_j² D_jj/R. Evaluate these sums directly; no nested Monte Carlo
truth approximation is needed. Cached support distances are computational aids,
not altered estimands. The exact Q sampling variance is also an arithmetic audit:
for its per-scene support kernel h, zeta1=Var_s mean_t h(s,t) and
zeta2=Var_st h(s,t), giving
sum_j w_j²[4(R−2)zeta1_j+2zeta2_j]/[R(R−1)]. It does not replace the one interval
procedure below after seeing an unfavorable result.

## Single interval candidate

For each component T, delete one paired F/N repeat r within scene j. Keep every
scene and its weight. Only scene j now has R−1 observations with weight
w_j/(R−1); other scenes keep R. Recompute the full V statistic and the appropriate
per-scene distinct-repeat denominator for Q. With Tbar_-j averaging those R
deletions, use

    V_J(T) = sum_j (R−1)/R sum_r (T_-jr−Tbar_-j)²,
    interval(T) = T ± t_(R−1,.9875) sqrt(V_J(T)).

These are two Bonferroni marginal intervals aiming at simultaneous95% coverage.
The large critical value is an intentional approximation, not a theorem that
R−1 is conservative. Jackknifing U-statistics has an asymptotic foundation
([Arvesen, 1969](https://doi.org/10.1214/aoms/1177697287)); it supplies no exact
R=4 coverage guarantee. E deletion also changes its local finite-R expectation;
the jackknife is not represented as an unbiased variance estimate for E.
Malformed inputs fail validation. A numerical trial with nonfinite point or
variance, or nonpositive variance for either component, has its whole interval
family unavailable: count it as a coverage miss and both half-widths as infinity.
Do not remove such trials from denominators, replace the method, or claim zero
uncertainty. A nonfinite aggregate diagnostic is unavailable rather than a
trimmed mean of selected trials.

## Fixed simulation, criteria and decision

For each of the 27 cells and R=4,6,8 run **10,000 trials**, using
`default_rng(SeedSequence([2026091062,shape_index,mean_index,regime_index,R]))`.
Each trial draws a 12×R integer array in [0,64), in that axis order. Codebook
and trial seeds are independent. Fixed batch size128 only bounds memory;
no nested bootstrap or fitted critical value is used. Every statistic, paired
deletion and variance uses the same one prescribed implementation.

Coverage means both exact truths lie in their intervals in the same trial.
For k covered trials out of n=10000, use the one-sided Clopper–Pearson lower
bound BetaQuantile(.05/81; k,n−k+1), or0 if k=0. The .05/81 allocation controls
Monte Carlo statement error across the entire three-allocation,27-cell grid.
A coverage cell passes only if this lower bound is >=.94. At n=10000, k=9476
is the first passing integer. This is a nominal95% candidate with a fixed .94
qualification floor, not a claim that true95% coverage was proved.

An allocation passes only when:

* **all27 cells** pass the coverage criterion; and
* in **each of its nine baseline cells**, the median E half-width is <=.25
  and the median Q half-width is <=1.0 (full lengths .5 and2).

Stress half-widths are fully reported but are not precision gates. Doubled noise
is a coverage stress, not an asserted upper bound on actual service variance.
The baseline half-width tolerances are planning tolerances informed by the scale
of existing results, fixed before formal qualification and new outcomes. They
are not meaningful-effect or equivalence margins, provide no detection guarantee,
and do not establish service precision. These criteria precede any formal output. Select the smallest passing
R in4,6,8. If none passes, **stop this inferential proposal**; no method, seed,
scenario, threshold or allocation changes in response to failure. Any future
separate proposal must retain this failed qualification and its reasons.

## Provenance, execution and scope

Before formal execution, commit clean source, tests, this protocol, DESIGN,
package initializers, pyproject/uv.lock, the two numerical inputs and their old
freeze/receipt bindings. Working and staged bytes must equal the recorded HEAD.
Run `uv run --locked python -m latent_art_bench.painter_map_validation_v1.precision`
only after parent review and commit. It creates
`studies/painter_map_validation_v1/pmvqv1-20260910/` once, recording source/input
hashes and Python/NumPy/SciPy/platform in RUN.json before computation, followed
by precision.json and PRECISION.md. Existing or interrupted output directories
are never overwritten. Recheck all source bindings after computation. No source
change while running, no formal output deletion, and no silent rerun are allowed.

Passing establishes behavior only for these specified discrete historical proxy
laws, with fixed maps, scene means, noise covariances and independent stationary
draws. It does not establish those assumptions for a service, account for
estimated-proxy uncertainty, qualify human style/capture, or open any acquisition,
feature-extraction, transport or generation gate. Negative or reversed estimates
are informative, not failures to be repaired. Budget and operational permissions
remain separate from this offline qualification.
