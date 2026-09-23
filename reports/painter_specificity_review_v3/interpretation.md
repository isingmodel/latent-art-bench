# Interpretation note

The full-frame and central-square generated feature arrays are **exactly equal**
(maximum absolute coordinate difference 0): all generated images are square.
Accordingly, identical shared fractions and common/specific terms across these
views are an expected identity, **not independent robustness evidence**. The
square-window Monet-Sisley alignment changes because its reference direction
changes; it uses each view's own reference vectors with the original scaler.

Across all configurations, direct named-minus-generic shared fractions are
66.6756–88.3905%; all single-scene-deletion fractions remain 65.9125–90.2042%.
These are descriptive estimates and deletion sensitivities, not confidence
intervals, equivalence findings, or service-independent replications.

The full-frame generic/additional-naming cross term is negative for GPT Image 1
(-1.7269) and positive for the other configurations (6.2420–38.6191).
The algebraic interaction explains why generic and extra-naming squared
magnitudes do not add to the common named-minus-free magnitude by themselves.

Full-frame Monet-Sisley pair beta is most positive for GPT Image 2 (0.4018;
scene-deletion range 0.3591–0.4447). Sunburst remains negatively aligned under
all deletions (-0.2494; -0.2794 to -0.2140), whereas Flare and Nano Banana 2
cross zero under deletion. The reference-window sensitivity also changes
Flare's point-estimate sign (-0.0105 full-frame; 0.0116 square). These sign
changes are sensitivity observations, not hypothesis tests.

## Verification

- 14 analytical tests passed.
- Ruff passed for the new implementation and tests.
- Exact numerical and Markdown replay passed.
- Maximum absolute full-panel scalar identity residual: 1.07e-14.
- Existing scientific source and result paths were not modified.

This note is interpretive and does not alter the immutable analysis/report.
Their SHA-256 values are:

- `analysis.json`: `79fa5ca28900e852c072e2a52d35f3cb400ee053935d857729b4ad4aa3bc542c`
- `report.md`: `4a4b589854325d32b232abc5e627026274797a4c0c3287f34ee4d41f27a824f9`
