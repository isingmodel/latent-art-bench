# Resolution of the prospective 31-feature secondary

19 September 2026. **Precollection methods amendment and constructed-array
implementation; no scientific outcomes, old-data fits, acquisitions, downloads,
review rescore or manuscript changes.** This report preserves
[v2](prospective_controls_v2.md), [v3](prospective_controls_v3.md), the
[independent methods audit](prospective_controls_method_audit.md), and every
historical analysis. It supplies the specification for a new v4 addendum.

## Decision and adequacy

Retain the allocation of six configurations, four painters, 12 scenes, eight
arms and eight windows: **4,608 assigned images**. Retain the original fixed
31 measurements, historical development-only scaler, primary CSD endpoints and
primary decision rule. Explicitly replace the unresolved v2 31-feature
cross-repeat secondary with **descriptive energies of realized, scene-averaged
feature vectors within each window**. Average these scalar energies over all
eight windows when complete. Do not calculate prospective common/specific
energy fractions, confidence intervals, noise corrections or cross-window D.

This is an adequate precollection resolution **for the stated descriptive
secondary**, provided the replacement is declared, independently checked and
bound before any new outcome. It is a changed secondary estimand, not another
estimator of the historical cross-repeat quantity. V3 alone did not settle this:
it removed cross-session squared-error diagnostics but left v2's remaining
31-feature squared-change specification unresolved, as the implementation PLAN
correctly records. Neither the formulas nor constructed tests supply the
unavailable noise-corrected target, authenticate feature provenance, complete
the study freeze or authorize collection.

## 1. Fixed coordinates and order of operations

For one configuration, let `x[w,s,j]` be the observed 31-vector for window `w`,
scene `s` and prompt arm `j`, already transformed coordinatewise as
`(raw - retained_development_center) / retained_development_IQR`.

- There are exactly eight windows, 12 scenes, and arms `free`, `generic`,
  `style_frame`, `shared_family`, Monet, Sisley, Pissarro and Cezanne in the
  protocol's retained order.
- Keep all 31 coordinates and their existing order: 11 color, eight spatial
  and 12 texture measurements. Use the retained 512-short-side historical
  measurement routine and already declared reference/region sensitivities;
  no new crop, unit-vector normalization, coordinate selection or scaler fit.
- The scaler path is
  `data/manifests/painter_feature_generation_v2/pfg2-method-20260905/scaler.json`.
  Bind its existing bytes and the measurement implementation through the
  extraction manifest. The array function cannot establish those identities
  merely from dimension 31 or numerical values.
- Compute each arm's equal-scene vector `y[w,j] = sum_s x[w,s,j] / 12` first.
  Next compute each window's energies below. Finally average scalar energies
  over the eight windows. Averaging individual scene energies, or averaging
  windows before squaring, changes the quantity and is not a substitute.
- Energies sum across all 31 coordinates and four painters in historical
  standardized squared units. There is no division by 31 or reference contrast
  energy `H`. These energies need no new reference prototype or fit.

Each prespecified preprocessing sensitivity must retain its own bound identity
and separately labeled output; it cannot be selected after seeing results.

## 2. Exact within-window realized decomposition

Suppress the configuration and window indices. For the four named arm means,
write `n = (1/4) sum_a y[a]` and `d[a] = y[a] - n`. For each common comparator
`b` in `{free, generic, style_frame, shared_family}`, define:

```
c[b] = n - y[b]
C[b] = 4 ||c[b]||²
S    = sum_a ||d[a]||²
Q[b] = sum_a ||y[a] - y[b]||²

Q[b] = C[b] + S
S    = (1/4) sum_{a<a'} ||y[a] - y[a']||²
```

Report `C[b]`, the common energy; `S`, the energy of departures of named means
from their four-name mean; and `Q[b]`, the total energy relative to that
comparator. All are nonnegative realized quantities, up to numerical error.
Retain direct evaluations and identity residuals; do not clip values to hide
failed arithmetic. Report `S` once per configuration/window. It is unchanged
by a common comparator **by algebra**; four identical copies are not four
pieces of evidence.

Here “specific” means departure among these four realized named means. It does
not mean correct painter discrimination, alignment with historical references,
perceptual fidelity, or noise-free individuality. A shared noisy comparator
contributes to `C[b]` and cancels from `S`. Individual named-arm noise can
contribute to both components.

### Comparator paths and signed interactions

For a path from comparator `b` through comparator `c` to the mean named arm,
define:

```
u = y[c] - y[b]
v = n - y[c]
n - y[b] = u + v

B[b,c] = 4 ||u||²
I[b,c] = 8 <u,v>
C[b] = B[b,c] + C[c] + I[b,c]
Q[b] - Q[c] = C[b] - C[c] = B[b,c] + I[b,c]
```

Freeze and report these four paths:

| Start `b` | Intermediate `c` | Purpose |
|---|---|---|
| `free` | `generic` | Generic-painting shift and remaining named shift |
| `generic` | `style_frame` | Exact wording-comparator shift |
| `style_frame` | `shared_family` | Family phrase relative to the wording comparator |
| `generic` | `shared_family` | Family phrase relative to generic painting |

Retain all three 31-vectors per window, their energies, signed interaction,
signed total-energy change, and vector/scalar identity residuals. `B[b,c]`
requires only those two comparator arms and remains available without named
images. `I[b,c]` and `Q[b]-Q[c]` can be negative. In particular, the family
baseline can increase total energy. Do not add squared path segments while
omitting the interaction. This is a vector identity, not causal mediation or
a factorial interaction estimate. Multiplying a single comparator shift by
four matches the painter-sum convention; it does not create four observations.

## 3. What one observation per cell does not identify

Write each scene-averaged vector as `y[w,j] = theta[w,j] + e[w,j]`, where
`theta[w,j]` is its expectation under that window's request law and
`E[e[w,j]] = 0`. This is notation for a possible repeated-request expectation,
not a claim that window-specific expectations or error covariance can be
estimated here. It allows changing means and arbitrary cross-scene/arm
dependence. Let `theta_bar` and `e_bar` be the four-name averages within a
window. Conditional-mean signal energies would be

```
C_theta[b] = 4 ||theta_bar - theta[b]||²
S_theta    = sum_a ||theta[a] - theta_bar||²
Q_theta[b] = sum_a ||theta[a] - theta[b]||².
```

The realized energies have expectations

```
E C[b] = C_theta[b] + 4 E ||e_bar - e[b]||²
E S    = S_theta + sum_a E ||e[a] - e_bar||²
E Q[b] = Q_theta[b] + sum_a E ||e[a] - e[b]||².
```

The additional terms include full covariance of the scene averages; they are
not marginal single-image variances divided by 12 unless extra assumptions
hold. For example,

```
4 E ||e_bar-e[b]||²
  = 4 { tr Var(e_bar) + tr Var(e[b]) - 2 tr Cov(e_bar,e[b]) }

sum_a E ||e[a]-e_bar||²
  = sum_a tr Var(e[a]) - 4 tr Var(e_bar).
```

If the four named scene-mean errors are mutually independent with equal
covariance trace `v_N` and independent of a comparator of trace `v_b`, the
extra contributions simplify to `v_N + 4 v_b` for common energy, `3 v_N` for
specific energy, and `4 v_N + 4 v_b` for total energy. These assumptions are
not adopted as a correction. The finite-enumeration test with five independent
`+1/-1` errors has zero conditional-mean signal but expected realized energies
`(C,S,Q) = (5,3,8)`.

With unrestricted cell/window means and unknown request-error laws, one draw
per cell provides no generally unbiased estimator of the squared conditional
mean or its noise correction. Even in one dimension, an estimator unbiased for
`theta²` under every point-mass law must satisfy `g(x)=x²`; under an equally
weighted `+1/-1` law it then has expectation one when `theta²=0`. Other cells
do not resolve this without assumptions relating their means or error laws.
Variation across the 12 authored scenes is not repeat noise for a fixed scene.

### Why crossing windows does not repair this

Let `z[w] = theta[w] + e[w]` stand for any common displacement or stacked
centered named vector, and write
`V_theta = (1/8) sum_w ||theta[w]-theta_bar||²`. Even with zero cross-window
error covariance, the equally weighted off-diagonal product targets

```
(1/(8*7)) sum_{w!=v} <theta[w],theta[v]>
  = ||theta_bar||² - V_theta/7,
```

whereas the mean window squared signal is `||theta_bar||² + V_theta`.
Nonzero cross-window error covariance adds another unidentified term.
Eight noiseless scalar means alternating `+1,-1` therefore give average
within-window square one, square of their overall mean zero, and off-window
product `-1/7`. The corresponding common energies multiply these by four.
This counterexample requires no noise at all. It is why v3's removed
cross-session diagnostic must not return as a corrected secondary energy.

## 4. Window aggregation, missingness and reporting

For each scalar endpoint `R`, the new descriptive summary is
`R_realized = (1/8) sum_w R[w]`, with every per-window value shown. It describes
the retained realized requests on this fixed panel and schedule. If an
expectation is discussed, it concerns the corresponding noise-inclusive
expected realized statistic, not `C_theta`, `S_theta` or `Q_theta`.

The distinction from pooling windows can be checked without assumptions:

```
mean_w C[w,b]
  = 4 ||mean_w c[w,b]||² + 4 mean_w ||c[w,b]-mean_w c[w,b]||²

mean_w S[w]
  = sum_a ||mean_w d[w,a]||²
    + mean_w sum_a ||d[w,a]-mean_w d[w,a]||².
```

These observed between-window terms mix realized noise and changing means.
They cannot be renamed variance estimates for independent service states.

Availability rules are endpoint-specific and fixed:

- Each arm mean requires all 12 finite scene vectors. A missing cell is a
  whole-vector missing value or an explicit false observed-cell mask, never
  an imputed zero. Reject partial nonfinite vectors and all infinite values.
- `S` needs only the four complete named panels. `C[b]` and `Q[b]` additionally
  need `b`. A missing generic arm does not erase family-relative energies.
- `B[b,c]` needs only complete panels for `b,c`. Remaining named displacement
  and `C[c]` need the four names and `c`, even when `b` is missing. Full path
  interactions and identity residuals need the four names plus `b,c`.
- An equal-window scalar mean, descriptive sample SD and leave-one-window
  means require all eight endpoint values. Otherwise retain the eight-value
  array with explicit nulls and report that full-schedule summary unavailable;
  no available-window reweighting, scene dropping, arm substitution or backfill.
- Include all six configurations, axis labels, original caller-supplied eight
  timing records, complete arm-panel flags, and full cell-level missing census.
  Preserve actual collection times in the eventual reporting pipeline.

Report absolute energies and signed path terms only. **No fractions or Fieller
sets are defined for this new secondary.** In particular, historical
cross-repeat common fractions and prototype cosine-gain fractions cannot be
filled with `C/Q` from these realizations. The existing prespecified secondary
ratios for linear prototype gains are unchanged. No significance test,
simultaneous claim, fidelity ranking or replacement primary decision follows
from this descriptive table.

## 5. Separate implementation and constructed checks

The new module is
[`secondary_features.py`](../../src/latent_art_bench/painter_family_controls_v1/secondary_features.py),
with pure interface
`analyze_realized_features(generated, window_times, *, observed=None)`.
It accepts exactly `(6,8,12,8,31)` already standardized values and returns
strict JSON-compatible records. It does not import or modify frozen primary
analysis, load images/scalers, extract features, fit any data, or send requests.
It explicitly marks scaler/assignment provenance unauthenticated at this
array-only layer; the future bound extraction loader must establish it.

The separate constructed-array suite is
[`test_secondary_features.py`](../../tests/painter_family_controls_v1/test_secondary_features.py).
Its required checks cover:

1. Exact common/specific/total and pairwise identities with the factor four;
   signed vector-path interactions, negative total-energy changes and zero
   totals, without percentages or clipping.
2. Scene cancellation before squaring; deterministic window drift with
   nonzero mean window energy but zero energy after pooling windows.
3. The noiseless alternating-mean off-window product counterexample and an
   exact 32-point enumeration of the independent-error contributions `(5,3,8)`.
4. Multi-coordinate identities and equal-window mean/SD/deletion summaries,
   preserving every configuration and all timing/axis labels.
5. Generic cancellation, comparator-only availability with missing names,
   whole-panel completeness and unavailable eight-window summaries after one
   required scene is missing; finite masked placeholders are ignored.
6. Rejection of wrong dimensions, nonboolean/wrong masks, partial nonfinite
   vectors, infinite inputs, inconsistent observed masks, ambiguous masked
   arrays, malformed timing records and numerical overflow.

Before collection, bind the replacement prose, module, checks, feature/scaler
identity, preprocessing sensitivities and output schema into the new freeze.
This report does not claim those later binding or execution steps are complete.

Local validation: `uv run pytest -q
tests/painter_family_controls_v1/test_secondary_features.py` completed with
**12 passed**. These are constructed-array checks of the separate descriptive
implementation; they provide no prospective scientific measurements.

## Inspected methodological sources

Read the v2/v3 proposals, independent methods audit, family-control PLAN and
protocol; historical `painter_specificity_review_v3.shared_decomposition`;
`painter_specificity_v1.analysis.shared_diagnostics`; the learned-analysis
cross-component definitions; historical feature definitions, `transform`,
`study.SCALER`, `measure_one`, and corrected measurement-reader code. These
were code/protocol reads only. No historical measurement array, generated
image, reference image or new observation was analyzed in this resolution.
