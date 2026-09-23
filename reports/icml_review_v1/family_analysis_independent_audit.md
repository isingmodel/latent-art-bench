# Independent audit of the offline family-control analysis

19 September 2026. **Constructed-array mathematical/code audit only.** No actual
historical or prospective outcome array was read, no old-cohort parameters were
fitted, and no image, model, paid request or manuscript was changed. This is not
a scientific result, improvement claim, review rating or collection approval.

## Scope and result

Inspected `prospective_controls_v2.md`, its superseding
`prospective_controls_v3.md`, the methods audit,
`family_analysis_implementation.md`, the new analysis module and its tests.
Read the historical learned-analysis and transport **source code only** to
check conventions. Ran the 34 existing analysis tests, all passing, and the
additional constructed probes below. No implementation or test file was edited.

**Two reproducible defects need correction before qualification:** near-
proportional Fieller inputs can produce an empty confidence set, and algebraic
generic-arm cancellation is not respected in secondary missingness. There is
also an unlabeled change in reference-energy convention. The primary endpoint
formulas and twelve-endpoint multiplicity calculation passed the inspected
checks; the Fieller defect affects secondary ratios, not the linear primary
decision.

Snapshot audited:

| File | SHA-256 |
|---|---|
| `prospective_controls_v2.md` | `979d2eb6f12c3ce52b332874125afa424f0f9c4f5b3682078577f70dfe2ba485` |
| `prospective_controls_v3.md` | `e984da446e9e4f1f8e4bda1afa18ef200775aca67641f1d016d63a332b9dc040` |
| `src/latent_art_bench/painter_family_controls_v1/analysis.py` | `5a20297d07501d29ae955c0bcdb7b85616496971a5f2146c52bb7982f5ae6efd` |
| `tests/painter_family_controls_v1/test_analysis.py` | `062007424cee81e587cb27f7726ddcd9981b42fcdcf00c8227d10bd500701613` |

Later corrections should be verified separately rather than rewriting this
snapshot's findings as if the original implementation passed.

## Finding 1 — Fieller cancellation can create an impossible empty set

Location: `fieller_confidence_set` and `_quadratic_confidence_set` in
`src/latent_art_bench/painter_family_controls_v1/analysis.py`.

The expanded coefficients are computed in double precision before the
discriminant is evaluated. For nearly proportional paired values, the
discriminant is the subtraction of almost equal quantities. Roundoff can make
it negative even though the confidence set is a narrow bounded interval. The
special case for **exactly** proportional values does not protect nearby
inputs. Casting already rounded coefficients to `longdouble` does not recover
the lost information; its precision is also platform dependent.

Minimal reproducer, using only valid small finite values:

```python
import numpy as np
from latent_art_bench.painter_family_controls_v1.analysis import fieller_confidence_set

y = np.arange(1., 9.) / 100
x = 0.3 * y + 1e-10 * np.tile([-1., 1.], 4)
r = fieller_confidence_set(x, y)
print(r["raw_signed_ratio"])
print(r["confidence_set"])
```

Observed: raw ratio `0.3`, confidence-set kind `empty`, intervals `[]`.
Independent 80-digit Decimal arithmetic, starting from the exact input floats
and the same Student critical value, gives the bounded interval
approximately **[0.2999999975070004, 0.3000000019955172]**.

This has a direct invariant check: when the denominator mean is nonzero, the
ratio of means must satisfy the inverted Fieller inequality. At that ratio the
mean residual is zero and its estimated variance is nonnegative. Returning an
empty set is therefore a numerical error, not a defensible degenerate case.
Changing the multiplier to `-0.3` in this probe also produces a spurious
singleton that excludes the ratio of means.

Recommended correction: form a numerically stable inversion, such as shifting
the variable to the ratio of means and computing the residual variance and
covariance from the original paired observations. Cover near-proportional
values, not only exact proportionality. Check point-estimate inclusion,
topology, boundaries, and sensible behavior under joint rescaling. Do not merely
clamp every negative discriminant to zero: that would collapse valid narrow
intervals and conceal the loss of precision.

## Finding 2 — Missing generic observations erase available secondary contrasts

Location: `window_components`, definitions of `C_F`, `N-F`, and `F-S`.

The code obtains these terms by subtracting quantities that each use generic
observations. Generic cancels exactly in all three estimands:

```text
C_F = dot(mean_a(g_a) - g_F, mean_a(mu_a))
N-F = mean_a dot(g_a, mu_a) - dot(g_F, mean_a(mu_a))
F-S = dot(g_F - g_S, mean_a(mu_a))
```

With a missing generic cell, the current arithmetic propagates NaN to all
three, even when every observation needed for their direct definitions is
present. This does not justify restoring primary inference: `N` and `T` still
require generic and must remain unavailable. It does mean the secondary
family-baseline quantities and family-versus-wording comparison unnecessarily
lose a complete fixed-panel result.

Reproducer:

```python
import numpy as np
from latent_art_bench.painter_family_controls_v1.analysis import analyze_primary

refs = np.eye(4)
data = np.broadcast_to(refs[0], (6, 8, 12, 8, 4)).copy()
data[..., 4:8, :] = refs
data[..., 3, :] = refs[1]
data[..., 2, :] = refs[2]
times = [{"start": str(i), "completion": str(i)} for i in range(8)]
data[0, 0, 0, 1] = np.nan  # generic only
model = analyze_primary(data, refs, times)["models"][0]
for key in ("C_F", "N-F", "F-S"):
    print(key, model["components"][key]["equal_window_mean"])
```

Observed: all three means are `None`. Their directly identifiable full-panel
values are respectively **0, 0.75, and 0**. `L` remains 0.75, as expected.

Recommended correction: calculate each cancelled contrast from its actual
arms, preserving the original generic-required masks for primary inference.
Test both whole-vector NaN and explicit-mask missingness, and verify the
decomposition identities on complete data.

## Finding 3 — Reference-energy convention differs by a factor of four

The new module reports
`reference_contrast_energy = mean_a ||mu_a - mean(mu)||^2`.
The retained `painter_learned_analysis_v1.py` uses
`reference_energy = sum_a ||mu_a - mean(mu)||^2` (the historical `H`).

For `refs = np.eye(4)`, the new value is **0.75**, whereas historical `H` is
**3.0**. Both are valid conventions, and the mean convention is compatible with
the new equal-painter gain formulas. The issue is comparability and an
insufficiently explicit name, not incorrect primary inference. The proposal
asks for reference contrast energy without declaring this convention change.

Recommended correction: return explicitly named sum and mean energies and
document `H_sum = 4 * H_mean`, or retain the historical sum convention with an
explicit conversion. Pairwise energy uses the unaveraged squared difference
and is unaffected.

## Transport contract checks and remaining integration boundary

The old-only fit uses precisely `(6,14,2,4,D)`, equal old scene/repeat/painter
weights, raw reference means for translation, normalized prototypes for
recognition, and translation scale one. The evaluator does not refit on new
queries. Constructed identity, harmful-translation, exact-tie, translated-zero,
confusion, correction/harm and incomplete-census cases passed. It retains
linear translated scores rather than silently normalizing them. The supplied
parameter mapping remained unchanged after evaluation.

The evaluator **trusts** the parameter mapping beyond its schema, painter
order, scale, shapes, finiteness and prototype norms. It does not establish that
the arrays, encoder/source view, configuration order or hashes match a frozen
artifact. For example, after fitting identity synthetic arrays, replacing
`parameters["translation"][0]` with `[0,5,0,0]` and both source hashes with
`"not-a-sha256"` is accepted; translated accuracy becomes 0.25 and the invalid
hash is echoed. This is an integration boundary, not evidence of new-query
fitting by the current function. A precollection loader must authenticate the
complete frozen artifact, bind explicit configuration/encoder/source identities,
and avoid relying on the word `frozen` or the presence of hash fields as proof.
Internal parameter-consistency validation would additionally catch accidental
mapping corruption. No actual frozen transport artifact was created or tested
in this audit.

Likewise, `window_times` checks eight supplied entries rather than validating
the actual schedule. The eventual protocol adapter must supply archived timing
records and exact row/axis identities. Those integration checks cannot be
established by these constructed arrays.

## Checks that passed and interpretation limits

- The primary components use raw, unnormalized reference means and fixed
  equal scene/painter/window weights. `N = C_G + L` and `N-F = C_F + L` hold
  on complete constructed data.
- The two-sided critical value is `t.ppf(1 - .05 / 24, 7)`, giving a half-width
  of about 1.4758 observed between-window SDs. Missingness in another
  configuration does not shrink the family of twelve endpoints.
- The strict decision boundaries require positive simultaneous lower bounds
  for both `N` and `T`, or positive `N` with strictly negative `T` upper bound
  for the opposite declared result. Zero-touching boundaries remain unresolved.
- Shared generic-arm covariance is retained in `T`; scenes are not substituted
  for the eight inference windows. Correlation multipliers equal the specified
  assumption-indexed formula and are labeled accordingly.
- Primary incomplete censuses receive no full-panel interval or decision.
  Missing free/style arms do not remove primary inference; incomplete
  recognition windows are not silently reweighted into a subset accuracy.
- Ordinary paired Fieller calculations target ratios of window means, retain
  signed denominators, and do not clip shares to [0,1]. The numerical defect
  above remains despite the passing ordinary/topology tests.
- No removed cross-session squared-error statistic is present.

The Student and Fieller procedures remain the proposal's conditional
approximations. Synthetic correctness does not demonstrate independence of
service states, perceptual validity, source authenticity or prospective
transport performance.

Validation executed:

```sh
.venv/bin/pytest -q tests/painter_family_controls_v1/test_analysis.py
# 34 passed in 0.88s on the audited snapshot.
```

The findings above were communicated before implementation changes so that
corrections can be regression-checked independently. All pre-existing files,
including proposals and frozen artifacts, were preserved by this auditor.
