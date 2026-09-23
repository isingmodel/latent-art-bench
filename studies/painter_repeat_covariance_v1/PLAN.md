# Primary-D cross-repeat covariance sensitivity v1

Version 1, 2026-09-19. This is a **retrospective descriptive analysis**, not a
preregistration. Primary results, review-v2 noise estimates and the earlier
simulations were known before this plan. No new covariance sensitivity outcomes
or crossing thresholds have been computed at the time of this implementation
plan. Freeze this plan, implementation and synthetic tests before executing
the real sensitivity. Preserve every existing scientific source and result.

## Question and estimand

Under a declared common trace-correlation assumption, how much positive
cross-repeat covariance would reverse each observed primary-D point ordering?
This supplies data-scaled breakpoints that the existing coverage simulations
and linear timing diagnostic do not give. It does not estimate actual service
covariance, identify the correct ordering, or repair confidence intervals.

For one model, stack the four artist-centered named measurements as
\(d_{sk}=\theta_s+e_{sk}\), with fixed reference \(r\),
\(H=\|r\|^2\), and \(S=14\). Assume stable conditional means over repeat
labels, mean-zero errors, and finite second moments. Define

\[
 V=\frac{1}{SH}\sum_s\frac{E\|e_{s1}\|^2+E\|e_{s2}\|^2}{2},\quad
 C=\frac{1}{SH}\sum_s E\langle e_{s1},e_{s2}\rangle,\quad
 D_*=\frac{1}{SH}\sum_s\|\theta_s-r\|^2.
\]

The canonical estimator and difference statistic satisfy

\[
 E\widehat D=D_*+C,\qquad
 \widehat q=\frac{1}{2SH}\sum_s\|d_{s1}-d_{s2}\|^2,\qquad
 E\widehat q=V-C=:q.
\]

Within-repeat feature/artist covariance, unequal repeat variances and
cross-scene dependence are allowed for these expectation identities. No
independent-artist approximation is used. Precision would require additional
assumptions. Changing repeat means violates this estimand and adds mean drift
to the difference statistic; this sensitivity does not correct that violation.

For \(V>0\), posit the aggregate trace correlation \(\rho=C/V\), not an
estimated Pearson correlation between images. For \(\rho<1\),

\[
 \alpha(\rho)=\frac{\rho}{1-\rho},\qquad C=\alpha q,\qquad
 \widehat D(\rho)=\widehat D-\alpha\widehat q.
\]

The assumed trace correlation is the same across all six configurations;
implied covariance bias can differ because q differs. Equal normalized
covariance bias is a different assumption and preserves all pair differences.
Arbitrary model-specific correlations are not examined. For a correct fixed
rho the adjustment is unbiased in expectation, but rho is unidentified here,
so outputs are scenario point estimates without uncertainty claims.

## Fixed data and outputs

1. Load only the full-frame canonical panel through
   `painter_specificity_measurement_v1.workflow.load(square=False)`. Require
   complete finite shape `(6, 14, 2, 6, 31)` and the unchanged corrected
   649-work reference counts `(297, 106, 141, 105)`, scaler and artist order.
   No scene, artist, coordinate, crop, reference or model selection is allowed.
2. Compute per-scene D and q from the four named arms with canonical centering
   and H. Retain all 84 values of each statistic. Verify scene D against
   canonical `geometry` and frozen primary results, verify mean D against its
   frozen primary value, and verify mean q against both the review-v2 direct
   function and frozen review-v2 `direct` result. Use float64 and
   `atol=rtol=1e-12`; fail on any disagreement or membership change.
3. Use exactly `rho = [0, .1, .25, .5, .75]`. Retain all six configurations and
   all five grid values, reporting original D, q, rho, alpha, implied normalized
   covariance bias and adjusted D. Flag and retain negative adjustments without
   clipping, interpreting them as physical negative squared errors, or claiming
   they formally reject a rho value.
4. Retain all 15 pairs in canonical model order. Report unrounded
   \(\Delta_D=D_a-D_b\), \(\Delta_q=q_a-q_b\), and every grid difference
   \(\Delta_D-\alpha\Delta_q\). When \(\Delta_q\ne0\) and
   \(\Delta_D/\Delta_q>0\), retain the analytic interior point-order crossing

   \[
   \alpha_* = \Delta_D/\Delta_q,\qquad
   \rho_* = \Delta_D/(\Delta_D+\Delta_q)\in(0,1),
   \]

   with both implied covariance biases, including crossings above the grid.
   Otherwise classify no positive interior crossing, an initial tie separating
   at positive rho, or a tie for all rho. Exact-zero/sign comparisons use
   unrounded float64 values, not rounded report cells. Fail rather than silently
   round an interior crossing to 0 or 1 if it exceeds float64 representation.
5. No confidence intervals, p-values, simulations, new significance claims,
   selected-pair summaries, additional grids, learned features, shared-fraction
   sensitivity, or primary-score edits are allowed. Do not shift old intervals.
   Linear beta retains its expectation under the covariance model but its
   variance and interval validity are not validated by this diagnostic.

## Interpretation limits

Two repeats do not estimate covariance: a random state shared by both repeats
vanishes from their difference. Within this second-moment model, q alone gives
no finite upper bound on positive covariance as rho approaches 1. Even zero
q permits arbitrary shared-state variance at rho=1. Negative covariance is
possible; the positive grid is a declared shared-state-like sensitivity rather
than an exhaustive dependence analysis or plausible-range estimate.

A state treated as random over new collection sessions enters the error law;
conditioning on its one realized value changes the conditional mean target.
One collection cannot distinguish these interpretations. Uncertainty in q and
its association with D is not quantified. Crossings are not statistical
significance thresholds or confidence bounds on the true ordering.

No named/shared-fraction outcomes are computed. Their common component also
contains baseline noise, and both common/specific scene-averaged components
depend on cross-scene covariance. Primary q does not identify those quantities;
scene-local versus session-wide shared noise can change the aggregate bias
by a factor S while leaving per-scene difference moments unchanged.

## Synthetic verification and provenance

Before real execution, use synthetic/analytic examples for unequal-variance
covariance identities, centering/reference normalization, repeat swapping,
common covariance versus common correlation, all crossing/tie cases, retention
of negative adjustments, and invalid inputs. Separately test exclusive output
creation and replay gates using temporary files or mocked data; synthetic tests
must not load real measurement vectors or compute real sensitivity outcomes.

Use only this new namespace. `freeze` verifies inherited bindings and hashes
the plan, source/tests, canonical primary and review-v2 results, raw compact
measurements, references/scaler, canonical reader/estimator, recursively named
input freezes, and runtime declarations into create-once `inputs.json`. It
computes no new sensitivity outcomes. `analyze` and `check` additionally require
`--execute-real` after method review. Input bindings are verified before and
after computation. `analyze` refuses existing results; `check` must reproduce
both JSON and Markdown exactly. Never replace an existing freeze or result.

```sh
uv run --locked pytest -q tests/painter_repeat_covariance_v1
uv run --locked python -m latent_art_bench.painter_repeat_covariance_v1 freeze
uv run --locked python -m latent_art_bench.painter_repeat_covariance_v1 analyze --execute-real
uv run --locked python -m latent_art_bench.painter_repeat_covariance_v1 check --execute-real
```
