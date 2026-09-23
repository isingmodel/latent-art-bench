# Precollection resolution of the31-feature secondary

19 September 2026. **Explicit design amendment; no new observations, full
freeze, live authorization or manuscript-result change.** This document
supersedes the unresolved31-feature secondary specification in
[v2](prospective_controls_v2.md), [v3](prospective_controls_v3.md), and the
[implementation draft](../../studies/painter_family_controls_v1/PLAN.md).
Those earlier documents remain unchanged. The detailed derivation, assumptions
and constructed counterexamples are preserved in the
[methods resolution](prospective_controls_secondary_method_resolution.md).

## Unchanged primary and allocation

Retain six configurations, all four painters,12 fixed scenes,eight arms,eight
windows and4,608 assigned images. Retain fixed CSD original-primary references,
the12 simultaneous N/T endpoints, seven degrees of freedom, strict majority
criterion and missingness rules. No representation or subset will be selected
after outcomes. The proposed $350 cumulative ceiling and40GiB destination are
still unapproved; no acquisition is authorized here.

## Adopted descriptive secondary

Use the historical31 coordinates and their frozen development-only center/IQR
scaler, original full-frame normalization at512 pixels on the short side, and
no new fitting or crop. For each configuration/window, average all12 scenes
within each arm **before** evaluating energies. Let `y_a` be the four named
means, `n=mean_a y_a`, and `y_b` one of free, generic, style-frame or family:

```
C_b = 4 ||n-y_b||²
S   = sum_a ||y_a-n||²
Q_b = sum_a ||y_a-y_b||² = C_b + S.
```

These are energies of the realized requests and include request noise. They
are not estimators of the historical noise-corrected conditional-mean energies.
Report all four comparator results and S once. Average scalar energies over
all eight windows only when their required cells are complete; otherwise retain
the per-window values and explicit missingness. Preserve the fixed coordinate
and painter-sum units; do not divide by31 or reference energy.

For free→generic, generic→style-frame, style-frame→family and generic→family,
set `u=y_c-y_b` and `v=n-y_c`. Retain the signed interaction and exact identities:

```
B_bc = 4 ||u||²; I_bc = 8 <u,v>
C_b = B_bc + C_c + I_bc
Q_b-Q_c = B_bc + I_bc.
```

Report all vectors, direct energies and identity residuals. Negative interaction
or energy differences remain negative. Comparator-only B uses only its two
arms; missing named cells do not erase it. A missing irrelevant comparator does
not erase another baseline's energy. No imputation or complete-case reweighting.

Do not report new common/specific energy fractions, Fieller intervals, corrected
D, cross-window energy products as noise corrections, or primary significance
claims from this31-feature secondary. The learned cosine-gain ratios in v2/v3
remain separate. With arbitrary changing window means and one draw per cell,
the proposed data do not identify the generally unbiased conditional-mean
squared-energy target. Cross-window products do not repair that limitation.

## Reference sensitivities and reporting grid

Use both previously fixed encoders and four retained targets:
primary/development × original/audited-region. Audited-region means replace
only the previously declared cropped reference rows; all other rows retain
their originals. The primary is only CSD/primary-original. The other seven
encoder/target combinations remain secondary, with no new primary decision or
familywise claim. Generated queries retain their original full-frame encoder
processing in every target comparison. The old-to-new recognition control
still uses only the original primary target and frozen old-only parameters.

All source membership, checkpoint/preprocessing, scaler and runtime identities
must be bound before actual analysis. Artifact hashes prove identity, not that
declared features were produced by an encoder: an execution receipt and replay
remain required. Offline fixtures must retain their simulation labels and can
never enter the prospective observations. The completed tests and reference
parameter candidates are preparation, not a new empirical study or review score.
