# Proposed cross-repeat covariance sensitivity

**Status: methodology design only, 2026-09-19.** No new sensitivity values,
crossing thresholds, simulations, or scientific scores were computed for this
document. Existing outcomes and review diagnostics were already known; any
implementation would be a retrospective descriptive analysis, not a
preregistration. Preserve all existing data, estimators, results, and manuscripts.

## Verdict and narrow question

**Proceed only with a compact primary-D point-estimate sensitivity if adopted.**
It can answer a distinct question: *under a declared common trace-correlation
assumption, how large would positive cross-repeat covariance have to be to
reverse each observed model-pair point ordering?* Existing simulations show
failure under one shared-state law and coverage under several independent-error
laws; they do not provide these data-scaled breakpoints. The timing diagnostic
tests predictability from a common linear drift, not covariance.

This cannot estimate actual covariance, bound the actual dependence, repair
interval coverage, or establish which model ordering is correct. Do not call
the resulting thresholds a robustness guarantee, and do not convert them into
new significance claims. **Do not execute a shared-fraction extension in this
version:** its extra assumptions and additional unknown covariance components
would substantially weaken the clarity of this small diagnostic.

## 1. What the repeat difference estimates

For one model, stack the four artist-centered named vectors as
\(d_{sk}=\theta_s+e_{sk}\), with the existing \(S=14\), fixed reference vector
\(r\), and \(H=\|r\|^2>0\). Assume identical conditional means across the two
repeat labels, zero-mean errors, and finite second moments. Dependence among
artists/features within a repeat is allowed; centering is already included in
\(e\). Define model-level, equally scene-weighted quantities

\[
 V=\frac{1}{SH}\sum_s\frac{E\|e_{s1}\|^2+E\|e_{s2}\|^2}{2},\qquad
 C=\frac{1}{SH}\sum_s E\langle e_{s1},e_{s2}\rangle.
\]

Here \(C\) is a covariance trace divided by \(H\), not the full covariance
matrix. The canonical estimator and the existing direct difference statistic
satisfy

\[
 E\widehat D=D_*+C,\qquad
 D_*=\frac{1}{SH}\sum_s\|\theta_s-r\|^2,
\]
\[
 \widehat q=\frac{1}{2SH}\sum_s\|d_{s1}-d_{s2}\|^2,
 \qquad q:=E\widehat q=V-C.
\]

These identities do not require equal marginal repeat covariances, independent
scenes, Gaussian noise, or zero cross-artist covariance. Those assumptions would
matter for precision. The existing review-v2 `direct` noise-power statistic is
exactly \(\widehat q\); it estimates marginal noise power only when \(C=0\).
Do not use its independent-artist approximation.

If repeat means change, \(E\widehat q\) also includes their squared difference
divided by \(2H\), and the primary cross-product no longer targets the stated
stable-mean squared error. This sensitivity does not address that violation.

## 2. Declared sensitivity parameter

For \(V>0\), define the **trace correlation** \(\rho=C/V\). This is an
aggregate noise-energy ratio, not an estimated Pearson correlation between
observed images. Positive semidefiniteness implies \(-1\leq\rho\leq1\).
For \(\rho<1\),

\[
 C=\alpha(\rho)q,\qquad
 \alpha(\rho)=\frac{\rho}{1-\rho},\qquad
 \widehat D(\rho)=\widehat D-\alpha(\rho)\widehat q.
\]

For a *fixed, correct assumed* \(\rho\), the final expression has expectation
\(D_*\), despite noise in \(\widehat q\). In this exercise it is a scenario
curve, not an empirically justified corrected estimate. Its uncertainty differs
from the original estimator's uncertainty, so neither shifting old intervals
nor treating \(\widehat q\) as known is justified.

Apply the same hypothetical \(\rho\) to all six configurations. This assumes
equal **trace correlations**, while allowing covariance biases
\(C_m=\alpha q_m\) to differ with noise scale. Equal normalized covariance
bias \(C_m=C\) is a different assumption: it shifts every D equally and leaves
all model-pair differences unchanged. Arbitrary model-specific correlations
are not examined by a common-\(\rho\) curve.

No finite upper bound on positive \(C\) follows from repeat differences alone
under this second-moment model: with \(q>0\), \(\rho\uparrow1\) sends
\(C\) to infinity. An additive random state shared by both repeats cancels
exactly from their difference. If \(q=0\), an arbitrarily variable shared
state at \(\rho=1\) is still possible. Observed \(\widehat q=0\) is not
evidence of zero latent covariance. Negative trace covariance is mathematically
possible; the proposed positive grid deliberately addresses shared-state-like
dependence, and is not a complete dependence analysis.

The expectation must also be defined consistently: a state regarded as random
over repeated collection sessions belongs to the error law above. Conditioning
on its one realized value instead changes the conditional mean target. One
collection cannot separate these interpretations empirically.

## 3. Exact proposed computation, to freeze before execution

1. Use only the canonical full-frame retained panel: six configurations, all
   14 scenes, two repeats, four named arms, and 31 existing standardized
   coordinates. Load through
   `painter_specificity_measurement_v1.workflow.load(square=False)`, preserving
   the corrected 649-work reference membership and existing scaler. Require the
   complete finite `(6, 14, 2, 6, 31)` array; fail rather than change membership.
2. Compute \(r,H,d\), per-scene \(\widehat D_{ms}\), and
   \(\widehat q_{ms}=\|d_{ms1}-d_{ms2}\|^2/(2H)\) using the canonical
   centering and geometry definitions. Retain all scene values. Require replay
   agreement with frozen primary D and with the existing review-v2 direct
   difference statistic at declared numerical tolerance (`atol=rtol=1e-12`).
3. Retain every model at the fixed grid
   \(\rho\in\{0,0.10,0.25,0.50,0.75\}\). Report its original D,
   \(\widehat q\), implied normalized bias
   \(\alpha\widehat q\), and adjusted D. Use unrounded float64 inputs.
   Retain negative adjusted estimates with a flag and the same warning as for
   ordinary negative cross-product estimates; do not clip, drop a scenario, or
   interpret negative values as physical squared-error truths. An implausible
   point correction is not a formal rejection of the assumed correlation.
4. Retain all 15 model pairs in the canonical order. With
   \(\Delta_D=\widehat D_a-\widehat D_b\) and
   \(\Delta_q=\widehat q_a-\widehat q_b\), report
   \(\Delta_D(\rho)=\Delta_D-\alpha(\rho)\Delta_q\) at every grid
   value. An interior positive-correlation crossing exists exactly when
   \(\Delta_q\ne0\) and \(\alpha_*:=\Delta_D/\Delta_q>0\):

   \[
     \rho_*=\frac{\alpha_*}{1+\alpha_*}
            =\frac{\Delta_D}{\Delta_D+\Delta_q}\in(0,1).
   \]

   Report this analytic point-order threshold even when it exceeds the displayed
   grid, and the corresponding two implied covariance biases. Classify all
   other pairs: no positive interior crossing; initial tie that separates for
   positive rho; or tied for all rho. If \(\Delta_q=0\), a nonzero original
   gap never changes under the common-rho scenario. Use full-precision zero/sign
   comparisons, and retain raw differences so rounding does not create ties.
   These are thresholds of the plug-in curves, not uncertainty bounds on the
   crossing or thresholds for a resolved statistical comparison.
5. Add no confidence intervals, p-values, coverage calculations, significance
   labels, data-chosen grids, selected-pair reporting, new metrics, learned
   representations, crops, reference adjustments, or recalibrated scores.
   Beta is linear and remains unbiased under the stated mean-zero covariance
   model, but its sampling variance and interval validity are not certified by
   this exercise; do not extend the sensitivity claims to it.
6. If adopted, put implementation, tests, plan, and create-once outputs in a new
   versioned namespace (suggestion: `painter_repeat_covariance_v1`). Bind the
   frozen primary/review-v2 results, canonical estimator/reader sources, raw
   compact inputs, reference/scaler, recursively named input freezes, new plan,
   source/tests, and locked runtime with SHA-256. `check` must replay numerical
   and report outputs exactly. Do not mutate the frozen scientific sources.

### Meaningful verification before real execution

Use small synthetic or analytic examples to verify the expectation identity
with unequal marginal variances and nonzero cross-repeat covariance;
artist-centering and reference normalization; invariance to swapping repeat
labels; the difference between common covariance and common correlation;
positive, absent, and tied crossing cases; and preservation of negative
adjustments. A two-component construction with independent mean-zero shared
\(u_s\) and repeat-specific \(\epsilon_{sk}\),
\(e_{sk}=u_s+\epsilon_{sk}\), gives
\(q=E\|\epsilon\|^2/H\) and \(C=E\|u\|^2/H\), an immediate analytic
check. No Monte Carlo coverage sweep is needed for this point-sensitivity task.

## 4. Why shared/naming fractions need a separate design

For either free or generic baseline \(b\), define
\(u_{sk}^{(b)}=2(\text{mean named}_{sk}-z_{skb})\) and
\(v_{sk}=d_{sk}\). The published scene-averaged components are
\(\widehat A_b=\langle\bar u_1^{(b)},\bar u_2^{(b)}\rangle\) and
\(\widehat B=\langle\bar v_1,\bar v_2\rangle\), with fraction
\(\widehat A_b/(\widehat A_b+\widehat B)\). Their covariance biases are

\[
 C_A=S^{-2}\sum_{s,t}E\langle e^u_{s1},e^u_{t2}\rangle,
 \qquad C_B=S^{-2}\sum_{s,t}E\langle e^v_{s1},e^v_{t2}\rangle.
\]

Primary \(\widehat q\) addresses only the centered named component and
same-scene pairs. It does not identify baseline/common noise, either bias above,
or their difference. The majority-common boundary is
\((A-B)-(C_A-C_B)=0\) for a positive adjusted total, so a single primary-D
rho cannot answer it. Here the boundary uses the observed component values as
plug-in moments; it is not an identified boundary for the true fraction.

Even a specified within-scene covariance trace gives different aggregate bias
if shared states are independent across scenes (division by S) versus common
to all scenes (no division by S). These mechanisms can have identical marginal
repeat-difference moments. One can form
\(\|\bar u_1-\bar u_2\|^2/2\) and its v counterpart, whose expectations
are aggregate variance minus aggregate covariance without scene independence,
but each comes from only one aggregate repeat pair and still loses any state
shared by both repeats. Separate assumed aggregate correlations would be
needed, and the resulting ratio is not unbiased or necessarily bounded.

Thus this extension is algebraically possible but does not inherit the primary
sensitivity's assumptions or add empirical identification. Defer it rather than
imply that two repeats estimate service-state uncertainty. Existing direct-naming
fractions, signed components, and scene-deletion ranges retain their stated
descriptive interpretation.

## Inspected sources

- Canonical numerical target:
  `src/latent_art_bench/painter_specificity_v1/analysis.py` (`geometry`, `centered`),
  `src/latent_art_bench/painter_specificity_v2/analysis.py`, and
  `studies/painter_specificity_v2/PROTOCOL.md`.
- Canonical reference reader:
  `studies/painter_specificity_measurement_v1/CORRECTION.md` and its workflow.
- Existing noise/statistical stress checks:
  `studies/painter_specificity_review_v1/PLAN.md`, review-v2 `PLAN.md`,
  `painter_specificity_review_v1.py`, review-v2 `centered_noise_power`, and
  `reports/painter_specificity_review_v2/REPORT.md`.
- Shared/naming decomposition: review-v3 `PLAN.md` and
  `painter_specificity_review_v3.py` (`shared_decomposition`).
- Manuscript: `paper/icml_main.tex` Section 4;
  `paper/icml_appendix.tex` estimator, score-detail and synthetic-coverage
  sections; `paper/icml_diagnostics_v3.tex`.
- Timing scope: `studies/painter_request_timing_v1/PLAN.md` and its report.
