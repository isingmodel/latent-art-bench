# Offline family-control analysis implementation

Implemented against `prospective_controls_v2.md`, as superseded by
`prospective_controls_v3.md` and its methods audit. This is constructed-array
qualification only. No historical or prospective outcome array was analyzed,
no old-cohort parameters were fitted, and no collection, download, manuscript
edit, or scientific score was produced.

## Array contract and reporting

`src/latent_art_bench/painter_family_controls_v1/analysis.py` exposes:

- `window_components(generated, reference_means, observed=None)`: fixed axes
  `(6 models, 8 windows, 12 scenes, 8 arms, D features)` and raw `(4,D)` reference
  means. Arm order is free, generic, style-frame, family, Monet, Sisley, Pissarro,
  Cezanne. Generated observations must have unit norm within `1e-4`; raw reference
  means may have norm below one and are never normalized for gain calculations.
- `analyze_primary(generated, reference_means, window_times, ...)`: CSD only,
  equal scenes/windows, fixed twelve-endpoint two-sided 95% Bonferroni Student
  intervals with seven degrees of freedom. All eight complete windows of the
  generic, family, and four named arms are required per model. Another model's
  missing data never reduces multiplicity. Missing free/style cells remain
  explicit secondary omissions. No incomplete-window or incomplete-model
  subset mean is substituted for the registered primary estimand.
- `fieller_confidence_set(numerator, denominator)`: all eight paired component
  values, their covariance, and the ratio of component means. Raw signed ratios
  are distinct from positive-denominator shares. Bounded, singleton,
  disconnected, half-line, all-real, and empty sets remain explicit; null set
  bounds encode the indicated infinities. Fractions are not clipped. Exact
  proportional observations are solved without rounding a double root into an
  empty set. No secondary ratio acquires a familywise claim.
- `fit_transport_parameters(old_named, reference_means, encoder=...)`: detached,
  serializable parameters fitted only from a complete `(6,14,2,4,D)` old named
  cohort. It records array hashes, raw reference means, normalized reference
  prototypes, old generated means/prototypes, and the fixed scale-one translation.
- `evaluate_transport(new_named, frozen_parameters, window_times, ...)`: baseline,
  translated, and supervised-generated decisions on the fixed `(6,8,12,4,D)`
  new named census. It accepts no fit/tuning option. Reports retain every score,
  signed truth margin, exact tie, prediction, paired correction/harm, per-window
  confusion and recall, and equal-window aggregate. Missing queries suppress
  the corresponding fixed-panel accuracy and any incomplete eight-window
  aggregate; observed-only counts are identified explicitly. Raw encoder queries
  must be unit vectors. A translated query may become exactly zero: its scores
  and ties remain recorded, with a zero flag and first-painter tie resolution.

All component outputs retain `N`, `F`, `S`, `L`, `C_G`, `C_F`, `F-S`, `N-F`,
`T`, free-baseline gains, six pairwise aligned responses, reference contrast
energy, and the decomposition identities. Complete component series include
eight values and leave-one-window influence. Timing records are supplied by the
caller; this module does not infer or invent actual starts/completions. It also
reports the specified correlation multipliers as assumed sensitivities, not
estimated corrections. No new cross-session squared-error statistic is present.

Missing cells use whole-vector NaN or an explicit boolean observation mask.
Partial-NaN observations and nonunit observed vectors are rejected; explicitly
unobserved cells do not enter any calculation. No input is silently normalized,
imputed, selected, or reweighted.

## Constructed qualification

`tests/painter_family_controls_v1/test_analysis.py`: **34 passing cases**, with
Ruff passing for both new Python files. Tests use only constructed vectors and
cover exact absolute gains/identities, raw reference energy, shared-control
covariance, the fixed twelve-endpoint correction, strict zero boundaries,
unequal/negative gains, incomplete censuses, influence, correlation assumptions,
the erroneous precision from treating repeated scenes as independent windows,
paired Fieller targets and all confidence-set topologies, zero/negative/near-zero
denominators, exact proportional degeneracy, fixed old-only fitting, harmful
translation, ties/translated-zero queries, frozen-parameter persistence, and
incomplete recognition reporting.

Validation command:

```sh
.venv/bin/pytest -q tests/painter_family_controls_v1/test_analysis.py
.venv/bin/ruff check src/latent_art_bench/painter_family_controls_v1/analysis.py tests/painter_family_controls_v1/test_analysis.py
```

These checks establish constructed-case behavior, not service independence,
perceptual fidelity, an empirical result, or permission to execute the proposal.
