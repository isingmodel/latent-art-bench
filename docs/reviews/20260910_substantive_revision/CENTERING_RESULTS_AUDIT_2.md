# Reviewer 2: direct-formula centering results audit

Date: 2026-09-10. Scope: completed `pncv1-20260910`, following
`pngv1-20260910`. This audit assigns no manuscript scores.

## Role and evidence identity

I am a maintainer-run LLM reviewer. I implemented the predecessor geometry
primitives and this successor's pure centering module, protocol and synthetic
tests. The calculation below is independently written arithmetic, but this is
not an institutionally independent review or a reviewer independent of the
implementation. No frozen file was edited and no new data were acquired.

- Source commit: `c390eef639ef8770230243bf5989ef93c84ec8d6`.
- Freeze commit reported by the root: `45e3ce9`.
- Freeze SHA256: `1c77284fbee616d20ef38d052f7c1593d82058e837f20721fdd68e95f5b67974`.
- Analysis SHA256: `d032a0058eb9fa314818d6234fbb391d0e250f5a7863535a8eb3edc500001961`.
- Report SHA256: `7cb64ae3f090e7b9c4753cd2c382aeca1c79c3c67d60587f1ef91911a366562b`.

All 22 freeze-bound files matched both their recorded SHA256 hashes and their
bytes at the source commit. Both output hashes and the receipt's freeze hash
matched. The inputs and predecessor numerical results remain unchanged.

## Direct arithmetic checks

A separate NumPy calculation read the compact input/result JSON, without
importing either study's fitting, transformation, energy, occupancy or analysis
functions. It reconstructed training moments from training vectors and class
weights, reconstructed all five evaluation clouds directly from the formulas,
and computed Euclidean distance matrices by broadcast subtraction and vector
norms. It checked the following complete grid, rather than selecting the
primary rows:

- 60 original cells, each with four disjoint whole-scene test folds, plus 18
  later-cohort cells: **258** evaluated clouds and unchanged fitted maps.
- **1,290** energy decompositions and **1,290** occupancy records, covering
  identity, translation, old-origin scaling, evaluation-centered scaling and
  actual named outputs.
- **1,032** predecessor energy/occupancy record pairs retained exactly.
- Exact scene memberships, class masses, reference radii, per-anchor hit
  booleans and hit counts. Each original fold has six scenes, two per class,
  with 18 queries per arm; each later cell has 24 queries per arm. All four
  original test folds cover each of the 24 scenes exactly once.
- Original arithmetic means of fold energies, occupancy and new contrasts;
  clouds with different fold-specific maps were not pooled.

The largest absolute numerical discrepancy was `8.88e-15` in a contrast;
energy-term discrepancies were at most `7.99e-15`. Occupancy, radii and weights
matched exactly. Directly reconstructed training moments differed by at most
`7.11e-15`. These are floating arithmetic differences, not scientific margins.

Across all 258 clouds, T2c and T1 have the same weighted mean, T2c and T2 have
the same pairwise distances, and their difference is the constant translation
`−(a−1)(m_E−m_F)`. The largest mean-identity discrepancy was `6.66e-16`, and
the largest pairwise-distance discrepancy was `3.55e-15`. Generated within
distance is unchanged between T2 and T2c to `8.88e-16`. All stored scales are
positive contractions: original-fold range `.508203–.960652`; later-cohort
range `.555145–.678537`.

T2c has no corrected conditional residual. Original T0/T1/T2 conditional values
are copied unchanged; later results contain no conditional residual. This is
appropriate because the evaluation-free mean induces dependence among T2c
residual errors across repetitions.

## Findings that survive the full grid

Here positive energy differences mean worse proximity to the fixed references.

| Contrast | Original cell means | Later cells | Difference range |
| --- | --- | --- | --- |
| T2c minus T1 | Positive in 60/60 | Positive in 18/18 | Original `.045000–.528676`; later `.180580–.591110` |
| T2 minus T2c | Negative in 60/60 | Negative in 15/18 | Original `−.487912–−.050805`; later `−.210315–+.008433` |
| Actual named minus T2c | Negative in 60/60 | Negative in 18/18 | Original `−.809908–−.092613`; later `−.634244–−.128997` |

The original statements concern four-fold averages. They must not be rewritten
as claims about every fold: T2c minus T1 is positive in 232/240 folds and
negative in eight; T2 minus T2c is negative in 206/240 folds and positive in 34.
The three later cells where centering improves on old T2 are all Cézanne:
primary/all31, resolution256/all31 and resolution256/no_lbp8.

Thus the retained scalar worsens the reference energy even when it is applied
around the same evaluation mean as translation. The old-origin offset is not a
general explanation for T2's failure against T1: on average it improves T2's
energy in every original cell and in 15/18 later cells. This comparison is a
specified path through feature-space counterfactuals, not a unique causal
decomposition or a statement about the image model's mechanism.

## Exact later primary energy decomposition

The identity is `E = cross_twice − reference_within − generated_within`.
The reference term is fixed within each painter. All values below were
recalculated directly, then checked against the frozen record.

| Painter and map | Cross twice | Generated within | Energy |
| --- | ---: | ---: | ---: |
| Monet T1 | 13.990671551 | 5.584465349 | 1.470401427 |
| Monet T2 | 12.048384447 | 3.211857878 | 1.900721793 |
| Monet T2c | 12.209173676 | 3.211857878 | 2.061511022 |
| Monet actual named | 12.463502155 | 3.957175123 | 1.570522257 |
| Cézanne T1 | 10.697303671 | 4.552011132 | .736045122 |
| Cézanne T2 | 9.490039820 | 3.088705745 | .992086659 |
| Cézanne T2c | 9.488321962 | 3.088705745 | .990368801 |
| Cézanne actual named | 10.208444905 | 3.978946043 | .820251446 |

Reference within distance is `6.935804776` for Monet and `5.409247416` for
Cézanne. At the shared mean, adding the retained scalar changes the terms as
follows:

| T2c minus T1 | Change in cross twice | Change in generated within | Change in energy |
| --- | ---: | ---: | ---: |
| Monet | −1.781497875 | −2.372607470 | +.591109595 |
| Cézanne | −1.208981709 | −1.463305388 | +.254323678 |

Scaling improves average cross-reference distance, but decreases query
self-distance by more. Since energy subtracts query self-distance, the net
energy rises. Calling this merely a failure to approach the references would
miss the main result. Conversely, using only cross distance would reward this
contraction while concealing the distributional penalty.

T2 minus T2c changes only cross distance: `−.160789229` for Monet and
`+.001717859` for Cézanne, with zero change in generated within distance. The
Cézanne advantage from recentering is small descriptively and does not have an
equivalence or significance interpretation. It does not remove the `.254324`
shared-mean scalar penalty.

## Occupancy interpretation

The direct audit confirms all query counts, complete reference anchors, k=3
radii, memberships and coverage fractions. T2c raises occupancy relative to T1
in **52/60** original cell means and **12/18** later cells, even though it
worsens energy in all 78 cells. Original occupancy falls in five cells and ties
in three; later it falls in four and ties in two. This is direct evidence in
the retained feature space that higher ball occupancy need not mean lower
distributional energy.

Later primary occupancy is:

| Painter | T1 | T2 | T2c | Actual named |
| --- | ---: | ---: | ---: | ---: |
| Monet | 21/38 | 23/38 | 21/38 | 20/38 |
| Cézanne | 20/32 | 24/32 | 22/32 | 23/32 |

No real/real calibration was added. This fixed-anchor, 18/24-query statistic
cannot inherit the calibration or sample-count interpretation of the older
matched-real figure. Energy uses reference-content weights, whereas occupancy
counts unweighted query hits; that distinction remains essential.

## Limits and manuscript recommendations

1. State the shared-mean scalar penalty and the cross/self-distance tradeoff
   directly. Retain the original-fold averaging qualifier and all sensitivity
   views; do not turn consistent signs across dependent views into replication
   counts or hypothesis tests.
2. Say that old-origin effects generally *offset* part of the scalar penalty
   on this path. Do not say that recentering rescues the old scale or that
   drift of the original mean explains its overall failure.
3. Explain that T2c uses the evaluation-free cohort and is cohort adaptation,
   whereas T1/T2 are unchanged pointwise maps transferred from the original
   collection. No evaluation-named or reference feature is used to fit T2c.
4. Keep energy and occupancy interpretations separate. Improved occupancy and
   cross distance coexist with worse energy here. None establishes human
   painterly style, image attainability or reference probability-mass matching.

This is a post-result retained-vector diagnostic with no scalar tuning, new
views, newly sampled scenes, tests or intervals. It does not separate capture
artifacts, content changes, representation weighting or temporal service
changes. I did not reopen images or repeat extraction, and I did not assign
new scientific scores as part of this audit.
