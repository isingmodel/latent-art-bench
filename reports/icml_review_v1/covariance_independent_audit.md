# Independent implementation/result audit: repeat covariance sensitivity

**Verdict: PASS for implementation and numerical accounting.** No numerical or conceptual defect was found under the declared fixed common-trace-ratio model. This is implementation QA, not a scientific review score, an estimated dependence model, or an endorsement of a plausible correlation range.

Completed: 2026-09-18T16:15:42.931390+00:00.

## Independent reconstruction

The audit reads the canonical full-frame feature arrays with `painter_specificity_measurement_v1.workflow.load(square=False)` and computes its own artist centering, reference energy, scene statistics, scenario curves and crossing formulas using NumPy and scalar dot products. It does not import the new covariance module or use its statistic, sensitivity or crossing helpers; the absence of that module is checked at runtime. No image acquisition, feature re-extraction, parameter fitting, search, selection or alternative grid was performed.

The complete `(6, 14, 2, 6, 31)` generated array and historical reference counts `[297, 106, 141, 105]` were verified. Historical means are centered equally over painters. The independently reconstructed reference energy is `H = 5.915007479821035`. Only the four named arms enter the centered repeat statistics.

For each configuration/scene, the audit independently computes `D_s = sum_a dot(d_s1a-r_a, d_s2a-r_a)/H` and `q_s = sum_a ||d_s1a-d_s2a||²/(2H)`. Every model average D is checked against the retained primary result, every scene D against its retained primary value, and q against the earlier review-v2 direct result.

## Verification coverage

- All **56 frozen binding hashes** match before and after the audit. The result-to-input-binding hash matches and the result file is unchanged during verification.
- All **84 scene D values and 84 scene q values**, six reference energies and six D/q averages match independent raw-array calculations and the retained canonical results.
- All **30 model grid points** match for exactly `rho = [0, .10, .25, .50, .75]`: alpha, implied bias, adjusted D and negative-value flags.
- All **15 canonical pairs and 75 pair-grid points** match: model order, unrounded Delta D/Delta q, implied bias difference and adjusted difference.
- All **15 crossing classifications** match an independent calculation. Every positive root is checked by equal adjusted point values and opposite signs on either side; absent crossings retain null threshold fields.
- There are **3 positive interior crossings**, **12 pairs with no positive interior crossing**, no initial/all-rho ties, and no crossing above the displayed grid.
- All **8 negative model-grid values** are retained, with matching flags. No estimate was clipped or treated as an impossible physical squared error.
- 441 numerical assertions passed; maximum absolute discrepancy is 1.78e-15, below the declared `atol=rtol=1e-12`. Identity, membership, sign, count and hash assertions also passed. No audit check failed.

## All configuration point curves

Unrounded numbers are retained in the JSON audit receipt; this display rounds to six decimals. Negative entries are scenario-adjusted estimates.

| Configuration | Original D | q | rho=.10 | rho=.25 | rho=.50 | rho=.75 |
|---|---:|---:|---:|---:|---:|---:|
| GPT Image 1 | 1.572416 | 2.023823 | 1.347547 | 0.897808 | -0.451407 | -4.499053 |
| GPT Image 2 | 1.225931 | 0.959822 | 1.119284 | 0.905990 | 0.266108 | -1.653536 |
| GPT Image 2.5 Flare | 1.737719 | 0.423596 | 1.690653 | 1.596520 | 1.314123 | 0.466931 |
| GPT Image 2.5 Sunburst | 1.641417 | 0.582533 | 1.576691 | 1.447240 | 1.058884 | -0.106181 |
| Nano Banana 2 | 1.109451 | 2.595883 | 0.821020 | 0.244157 | -1.486432 | -6.678198 |
| FLUX.2 Max | 0.800928 | 1.674010 | 0.614927 | 0.242925 | -0.873082 | -4.221101 |

## All paired curves and crossings

Differences are first minus second. Thresholds concern only the unrounded plug-in point order. The same hypothetical trace ratio applies to every configuration.

| Pair | Delta q | rho=0 | rho=.10 | rho=.25 | rho=.50 | rho=.75 | Interior crossing rho |
|---|---:|---:|---:|---:|---:|---:|---|
| GPT Image 1 minus GPT Image 2 | 1.064001 | 0.346485 | 0.228263 | -0.008182 | -0.717515 | -2.845517 | 0.245649519 |
| GPT Image 1 minus GPT Image 2.5 Flare | 1.600227 | -0.165303 | -0.343106 | -0.698712 | -1.765530 | -4.965984 | None |
| GPT Image 1 minus GPT Image 2.5 Sunburst | 1.441290 | -0.069001 | -0.229144 | -0.549431 | -1.510291 | -4.392872 | None |
| GPT Image 1 minus Nano Banana 2 | -0.572060 | 0.462965 | 0.526527 | 0.653652 | 1.035025 | 2.179145 | None |
| GPT Image 1 minus FLUX.2 Max | 0.349813 | 0.771488 | 0.732620 | 0.654883 | 0.421675 | -0.277952 | 0.688029220 |
| GPT Image 2 minus GPT Image 2.5 Flare | 0.536227 | -0.511788 | -0.571369 | -0.690530 | -1.048015 | -2.120468 | None |
| GPT Image 2 minus GPT Image 2.5 Sunburst | 0.377290 | -0.415486 | -0.457407 | -0.541249 | -0.792776 | -1.547355 | None |
| GPT Image 2 minus Nano Banana 2 | -1.636061 | 0.116480 | 0.298264 | 0.661834 | 1.752541 | 5.024662 | None |
| GPT Image 2 minus FLUX.2 Max | -0.714187 | 0.425003 | 0.504357 | 0.663065 | 1.139190 | 2.567565 | None |
| GPT Image 2.5 Flare minus GPT Image 2.5 Sunburst | -0.158937 | 0.096302 | 0.113962 | 0.149281 | 0.255239 | 0.573113 | None |
| GPT Image 2.5 Flare minus Nano Banana 2 | -2.172287 | 0.628268 | 0.869633 | 1.352364 | 2.800555 | 7.145129 | None |
| GPT Image 2.5 Flare minus FLUX.2 Max | -1.250414 | 0.936791 | 1.075726 | 1.353596 | 2.187205 | 4.688033 | None |
| GPT Image 2.5 Sunburst minus Nano Banana 2 | -2.013350 | 0.531966 | 0.755672 | 1.203083 | 2.545316 | 6.572017 | None |
| GPT Image 2.5 Sunburst minus FLUX.2 Max | -1.091477 | 0.840489 | 0.961764 | 1.204315 | 1.931966 | 4.114920 | None |
| Nano Banana 2 minus FLUX.2 Max | 0.921873 | 0.308523 | 0.206092 | 0.001232 | -0.613350 | -2.457097 | 0.250750773 |

## Mathematical interpretation checked

With stable conditional repeat means and mean-zero errors, the two identities are `E[Dhat] = D_* + c` and `E[qhat] = v − c`, with v the average normalized marginal error energy and c the normalized cross-repeat covariance trace. The observed repeat difference does **not** estimate marginal variance without the zero-covariance assumption. The trace ratio `rho = c/v` is a second-moment scenario parameter, not an estimated Pearson correlation of image vectors.

Under a fixed assumed ratio, `alpha = rho/(1−rho)` and the point adjustment is `Dhat − alpha*qhat`. Equal rho permits unequal biases when q differs. Equal covariance bias instead shifts every model equally and leaves all pair differences unchanged. The independent root calculation is `alpha_* = Delta D/Delta q`, with `rho_* = alpha_*/(1+alpha_*)` only when alpha is positive; every sign and tie case is retained.

The adjustment does not repair uncertainty intervals, estimate actual session covariance, prove statistical superiority, identify the correct ranking, or validate a correlation range. The near-.25 crossings are point-curve properties, not confidence bounds or tests. Two-repeat differences do not bound a shared random component that cancels from their difference. Mean drift, arbitrary model-specific ratios, cross-scene covariance and uncertainty in D/q remain outside these curves.

No correction of shared naming fractions or their intervals follows from primary q. Linear aligned response retains its expectation under the stated mean-zero covariance model; this does not validate its precision or interval coverage. All of these distinctions are preserved by the audited plan and outputs.

## Reproduction and exact receipts

Independent code: [covariance_independent_audit.py](covariance_independent_audit.py). Full receipt, all scene statistics, model implied biases and pair curves: [covariance_independent_audit.json](covariance_independent_audit.json).

```sh
uv run --locked python reports/icml_review_v1/covariance_independent_audit.py
```

Result SHA-256: `e5031ccad955b289b0d8dec110e8ee6b2ec39b43dfd8a6f2e150cc1dea1ce0c9`.

Input binding SHA-256: `43a44d769700b1a8fd0122d9a4e4d8e34726c121313641d892aa85b843bf2346`.

Report SHA-256: `7ebb75099602bd091e61c2c1b51cd4b1fa6f68fc6f5e51d8e33a4fe86f8d58a9`.

Independent script SHA-256: `bb3fbf5f8bfe140e273fa6d6a4dc159bab1f66fba008236d8a060020445c163b`.
