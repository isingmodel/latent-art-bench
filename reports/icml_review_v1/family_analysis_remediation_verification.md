# Independent remediation verification: family analysis

19 September 2026. Constructed-array verification only. The initial
`family_analysis_independent_audit.md` remains unchanged. No real outcome
arrays, images or fitted historical parameters were read. No implementation,
tests, proposal, frozen artifact or manuscript was edited by this verifier.

**Latest status:** the second remediation snapshot below corrects the
first-snapshot failures. Its 53 tests pass, and 2,751 decisive independent
high-precision membership checks found no remaining substantive numerical
failure in the audited array-analysis scope. The first-snapshot findings are
retained as a record of the verification sequence.

## First remediation snapshot

| File | SHA-256 |
|---|---|
| `src/latent_art_bench/painter_family_controls_v1/analysis.py` | `b544e1b3ae1ce87319b299057038bf2ba0ecc3af0f88b5d2281452b6f6cd3de6` |
| `tests/painter_family_controls_v1/test_analysis.py` | `82be555defafcd6337ae575adaab544997f50185d2adc138cda529506f0087f8` |
| Preserved initial independent audit | `919762ddd4be2e354edde38f76012ebeabd87fda91ea4b543a14dbf9c706cc93` |

**The original defects are corrected, but this snapshot still has a blocking
secondary-Fieller numerical failure near a zero denominator mean.** The
forty-seven analysis tests pass; adversarial cases below reveal behavior not
covered by that suite. Primary `N`/`T` inference is not affected by this failure.

## Corrected findings verified

1. **Original near-proportional Fieller reproducer:**
   `y = arange(1.,9.)/100`,
   `x = 0.3*y + 1e-10*tile([-1.,1.],4)` now returns the bounded interval
   `[0.2999999975070004, 0.3000000019955172]`, matching the independent
   high-precision oracle. Positive and negative slopes are covered by the
   expanded tests. Joint scaling by `1e-300`, `1e-200`, `1`, and `1e150`
   preserved the result within floating-point rounding in additional probes.
2. **Cancelled-contrast missingness:** both whole-vector NaN and explicit
   boolean-mask versions of the initial missing-generic reproducer return
   `C_F = 0`, `N-F = 0.75`, and `F-S = 0`. `N` and `T` stay unavailable and
   primary intervals stay empty. The incomplete primary census is preserved.
3. **Reference energy:** identity reference prototypes now report explicit
   sum energy `3.0` and painter-mean energy `0.75`, with the historical sum
   convention documented in the report schema.
4. **Axis identities:** primary output includes the protocol model and scene
   orders; transport fit includes the model order; reversing that order is
   rejected by transport evaluation. These labels document the contract but
   do not independently authenticate the provenance of an unlabelled array.
5. **Degenerate Fieller checks:** zero/zero returns all real; one/zero is empty;
   positive and negative deterministic ratios return singletons; symmetric
   zero-mean denominator with nonzero constant numerator is disconnected;
   exact proportional zero-mean pairs and orthogonal zero-mean pairs return
   all real. These returned records serialize with strict JSON.

## Remaining failure A — Huge centering origin breaks weak-denominator sets

The replacement solver always chooses the ratio of means as its origin when
the denominator mean is nonzero. If the denominator mean is tiny because its
positive and negative observations cancel, this creates a huge origin.
Computing roots in that coordinate and shifting them back loses the finite
endpoints, even though the input observations are of ordinary size.

Minimal reproducer:

```python
import numpy as np
from latent_art_bench.painter_family_controls_v1.analysis import fieller_confidence_set

x = np.ones(8)
y = np.tile([-1., 1.], 4) + 1e-10
print(fieller_confidence_set(x, y)["confidence_set"])
```

Observed: `all_real`, intervals `[[None, None]]`.
Expected: a disconnected set approximately
`(-infinity, -1.1188886816] union [1.1188886814, infinity)`.
The result cannot contain zero: at ratio zero the residual is the constant
one, so its mean is one and its estimated standard error is zero.

Other offsets in the same construction:

| Offset added to denominator | Observed behavior |
|---|---|
| `0` | Correct disconnected endpoints near +/-1.1188886815 |
| `1e-6` | Endpoints already inaccurate by about 1e-5 |
| `1e-8` | Endpoints near +/-1.110223 rather than +/-1.118889 |
| `1e-10` | Incorrect all-real set |
| `1e-12` | Incorrect disconnected endpoints near +/-19164.888 |
| `1e-14` | Incorrect disconnected endpoints near +/-1499753.3 |

A suitable correction must avoid the huge-origin expansion when the
denominator is compatible with zero. An adaptive origin, retaining residual
centering where it protects narrow bounded sets and using well-scaled
unshifted coefficients for weak denominators, is one possible approach.
Regression checks must include membership away from the endpoints (not only
topology) and both signs of the near-zero denominator mean.

## Remaining failure B — Common scaling does not protect unequal magnitudes

This is a more extreme numerical case than failure A. The denominator
observations are individually tiny, rather than cancelling to a tiny mean:

```python
x = np.arange(1., 9.) / 100
y = np.full(8, 1e-170)
r = fieller_confidence_set(x, y)
```

Observed: `all_real`.
Expected: bounded interval approximately
`[2.4521753277158835e168, 6.547824672284116e168]`.
The denominator is a known positive constant with zero estimated variance,
so this is just the numerator's ordinary Student interval divided by that
constant. Its point estimate and both boundaries fit in a finite double.

The common scaling protects small **joint** magnitudes but still lets the
scaled denominator square underflow when numerator and denominator scales
differ sufficiently. On this host, `np.longdouble` has the same 15-decimal-digit
precision as `float`, and supplies no wider exponent protection.
Independent numerator/denominator scaling and a corresponding ratio-coordinate
conversion would address this case.

Also observed: jointly scaling the original near-proportional reproducer by
`1e200` raises `OverflowError` while calculating legacy raw coefficients,
before the scaled solver runs. This lies outside the physical cosine-gain
range, so it is lower priority than failure A. The function currently accepts
arbitrary finite paired inputs without documenting this magnitude limitation.

## Verification command and remaining boundary

```sh
.venv/bin/pytest -q tests/painter_family_controls_v1/test_analysis.py
# 47 passed in 0.89s on this snapshot.
```

The root implementer was sent both remaining numerical reproducers. Artifact
authentication for old parameters is separate pending integration work; the
bare array function's trusted mapping remains acknowledged. This verification
does not establish a qualified provenance loader, service independence,
perceptual validity or any empirical improvement.

## Second remediation snapshot — final array-analysis verification

The implementer replaced the unconditional ratio origin with a ratio origin
when the denominator is strong (`A > 0`) and a paired-regression origin
otherwise. Numerator and denominator now have separate positive scales, with
an explicit conversion back to the original ratio coordinate. The redundant
overflow-prone expanded raw quadratic diagnostic was removed. This verifier
read the changes and reran the tests and independent adversarial probes.

| File | SHA-256 |
|---|---|
| `src/latent_art_bench/painter_family_controls_v1/analysis.py` | `fa8f1adf5e222cac0ac3e00c70cf015731615616b7995e56b732f514cf430e64` |
| `tests/painter_family_controls_v1/test_analysis.py` | `3cd13887870933008025e71fbc7e63815be3fd2a7820e148be7f03bf9aa88199` |
| Preserved initial independent audit | `919762ddd4be2e354edde38f76012ebeabd87fda91ea4b543a14dbf9c706cc93` |

### Former failures now pass

- `x = ones(8)`, `y = tile([-1.,1.],4) + 1e-10` now returns the correct
  disconnected set with endpoints `-1.1188886816070132` and
  `1.118888681356631`. Offset `+1e-12` gives endpoints
  `-1.118888681483074` and `1.1188886814805705`; negative offset reverses the
  appropriate asymmetry. Zero is correctly excluded.
- Constant denominator `1e-170` with numerator `arange(1.,9.)/100` returns
  the bounded interval `[2.4521753277158833e168, 6.547824672284116e168]`.
  The negative-denominator version also passes the direct-inversion checks.
- The original near-proportional case remains a narrow bounded interval
  containing its estimate, including both signs of the slope and very small
  joint scales.
- Joint scaling by `1e200` no longer prevents the confidence-set solution:
  the original near-proportional case still returns approximately
  `[0.29999999750700046, 0.30000000199551724]`. Its unscaled covariance
  cannot be represented in a finite double and serializes as null entries.
  This is an explicitly observed diagnostic precision limit, outside the
  physical cosine-gain range; it does not change that scaled interval.

### Independent direct-inversion probe

Ran **309 constructed cases** and **2,751 decisive membership comparisons**
against a 100-digit Decimal oracle, with **zero failures**. The oracle uses
the exact supplied floating-point values and the same Student critical value,
then tests the original paired residual inequality directly:

```text
d_i(r) = x_i - r*y_i
mean(d(r))^2 <= t_7(.975)^2 * sum_i(d_i(r)-mean(d(r)))^2 / (8*7)
```

It does not call either quadratic solver or reuse the implementation's
centering/scaling calculations. Candidate ratios include fixed negative, zero
and positive values, the ratio estimate when numerically modest, and points
on each side of every finite reported boundary.

Coverage of the 309 cases:

- Constant numerator with denominator mean offsets of zero and both signs of
  `1e-2`, `1e-6`, `1e-10`, `1e-12`, and `1e-14`.
- Weak denominators near proportionality, slopes `-3`, `-0.3`, `0.3`, and `3`,
  with exact multiplication or independent residual amplitudes `1e-10`,
  `1e-6`, and `0.1`.
- One hundred seeded ordinary random paired arrays with varying means and
  numerator scales (NumPy random seed `271828`).
- Strong-denominator near-proportional arrays at the four signed slopes and
  joint scales `1e-300`, `1e-200`, `1`, `1e100`, and `1e150`.
- Constant positive and negative denominators of magnitude `1e-170`.

**Numerical boundary limitation:** 46 comparisons were excluded as unresolved
at floating-point precision, principally exact multiplication pairs whose
rounded inputs leave residuals near machine precision. Specifically, writing
the oracle's left and right sides as `L` and `R`, and
`s = max(max(abs(x)), abs(r)*max(abs(y)))`, a comparison was excluded if
`abs(L-R) <= max(1e-12*max(abs(L),abs(R)), 1e-28*s^2)`.
No high-precision topology claim is made for a gap smaller than representable
boundary spacing. This exclusion is far below the original `1e-10` residual
probe and does not conceal its former empty-set error, or the former
ordinary-scale weak-denominator failure.

### Final result and remaining integration work

```sh
.venv/bin/pytest -q tests/painter_family_controls_v1/test_analysis.py
# 53 passed in 0.88s on the second snapshot.
```

The original missingness corrections, explicit sum/mean reference energies
and protocol model/scene identities remain present. No remaining substantive
array-analysis blocker was identified by this bounded audit. That statement
is limited to the inspected code, existing suite and documented constructed
probes; it is not a proof for every finite floating-point input.

The bare transport function still trusts the supplied parameter mapping.
Source membership, checkpoint/view identities, frozen artifact authentication
and actual timestamps remain the provenance loader's responsibility and are
outside this verification. No real old-cohort fit or prospective analysis was
performed by this verifier. Statistical assumptions and all empirical limits
from the initial audit remain unchanged.
