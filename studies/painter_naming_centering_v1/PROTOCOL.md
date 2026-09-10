# Painter naming evaluation centering — post-result diagnostic, version 1

## Origin, question and boundary

This protocol is written after observing the complete `pngv1-20260910` results
from `painter_naming_geometry_v1`. In those results, the original translation
map outperforms the original shift/scale map in all 18 later-cohort views.
Maintainer-run LLM Reviewer 3 identified a further algebraic distinction: the
original shift/scale map changes the evaluation mean when evaluation-free and
training-free means differ. Therefore its underperformance cannot be attributed
to its scalar alone. This successor fixes a centering comparison before its
execution on research observations. It is post-result, not an unexposed test.

Reviewer 2 implements this successor after implementing the predecessor's
geometry primitives and auditing its results. Other maintainers/reviewers are
also LLM agents operated by the same maintainer. This is not independent human
or institutional review. Future reviews must disclose implementation assistance.

No predecessor source, protocol, output, vector or ledger changes. This namespace
authorizes only numerical computation from the existing compact inputs and fitted
maps after the new source/protocol/tests are committed and bound by the runner.
It authorizes no image reads, extraction, new views, new reference selection,
generation, acquisition, transport, scalar tuning or spending. No computation
of this successor on research vectors occurs before that source/input binding.

## Fixed inputs and complete grid

The runner binds the unchanged input and analysis JSON objects of
`data/manifests/painter_naming_geometry_v1/pngv1-20260910/`, together with their
predecessor receipt/freeze and the new source/test/protocol files. The root
orchestrator supplies the create-once freeze, output and replay workflow.

Use every one of the predecessor's 60 original cells and 18 later FLUX cells.
Original cells retain the three original pipelines crossed with all31, no_lbp8
and nontexture19, plus common-square/all31, on all six service/painter cells.
Later cells retain the three original pipelines and three views for two painters.
The original reference panels, development-only scalers, coordinate subsets,
content masses, 24 scenes, pairing and repetitions remain unchanged. There is
no later common-square view. Old and new cohorts are never pooled.

Retain the four original whole-scene folds exactly: six held-out scenes, two per
class, with 18 outputs per condition; fit records come from the other 18 scenes.
Later evaluation retains its 24 scenes with one output per arm, and the map fitted
to all 72 original FLUX outputs per arm. Use the predecessor's exact stored maps,
not a refit selected to improve the new result.

## Evaluation-centered scalar comparison

Let m_F, m_N and a be the predecessor training-free mean, training-named mean
and positive isotropic scalar, with delta=m_N−m_F. Let m_E be the weighted mean
of the current evaluation-free cloud, using the same reference-content weights
as its energy calculation. Its identities and weights are already fixed.

The predecessor maps remain:

```
T1(y) = y + delta
T2(y) = m_N + a (y - m_F).
```

Add exactly one diagnostic map:

```
T2c(y) = m_E + delta + a (y - m_E).
```

T2c uses no evaluation-named or reference features to set its parameters. It uses
the same training delta and a without optimization. However, evaluation-free
centering is a cohort-dependent adaptation: T2c is not the same untouched
pointwise map as T2 transferred to a later collection. State that distinction
whenever reporting transfer. All maps act on features and need not produce
attainable images.

Algebraic identities provide explicit computational checks:

- T2c and T1 have the same evaluation mean, m_E+delta.
- T2c and T2 have the same centered shape and pairwise distances: both are
  isotropic rescalings of the identical evaluation-free cloud by a.
- mean(T2)−mean(T1)=(a−1)(m_E−m_F).
- T2c−T2 is a constant translation for every query.

Record the evaluation-free mean, training displacement/scalar, all three mapped
means and their differences. Verify the mean and within-distance identities to
1e-10 absolute/relative tolerance; this only handles floating arithmetic, not a
scientific equivalence margin. Zero/nonfinite training scales/traces remain
invalid under the predecessor contract. Evaluation-free weights must be finite,
strictly positive and normalized; vectors and mapped values must be finite.

## Evaluation, comparisons and uncertainty

Evaluate T2c with the predecessor's weighted V-energy and complete decomposition:
twice the cross-reference mean distance, reference self-distance and generated
self-distance. Keep T0/T1/T2/actual-named values unchanged for direct comparison.
The new descriptive contrasts are:

1. E(actual named)−E(T2c): actual naming versus the additional benchmark.
2. E(T2c)−E(T1): scaling around a shared evaluation mean.
3. E(T2)−E(T2c): the old-origin mean displacement at identical centered shape.

The latter two sum to E(T2)−E(T1). This is an algebraic decomposition along this
specified diagnostic path, not a unique causal attribution. A different path
can yield different components. Do not report fractions explained, tune a,
or interpret these comparisons as internal model mechanisms.

Compute each original fold's energy separately and average all four equally.
Do not pool clouds with different fitted maps or centering means. This remains
an 18-query held-scene score, not the original 72-query energy statistic. Later
scores use 24 queries. No new scene-deletion or sampling grid is added.

Evaluate fixed-reference k=3 ball occupancy with the same complete anchors,
radii and equal-class query identities/counts as the predecessor: 18 per
original fold, 24 per later cohort. The centering mean uses energy weights,
while occupancy remains an unweighted ball-hit statistic. Preserve this
distinction. There is no new real/real calibration or claim that ball occupancy
measures reference probability-mass matching.

For original folds only, retain the predecessor's conditional residual values
unchanged for T0/T1/T2. Do not compute a corrected conditional residual for T2c:
its centering mean depends on all evaluation-free repeats and introduces
dependence among residual errors, so the predecessor correction's independence
assumption is insufficient. No conditional residual is reported for the R=1
later cohort.

All 60 original and 18 transfer views are retained regardless of sign. Folds and
views are dependent, and no confidence intervals, p-values, equivalence test,
new hypothesis family or selected significance threshold are introduced.

## Falsification and interpretation

If the evaluation-centered scalar has lower energy than T2, the old-origin
translation contributes to T2's poorer proximity along this fixed comparison
path. If T2c remains worse than T1, the unchanged scalar itself worsens energy
when both share the evaluation mean. Either ordering can reverse across cells;
all outcomes are reported. Actual naming can remain better or worse than either
benchmark. Equal or nearby energies do not establish distribution equality.

Even clean algebraic separation of origin and scalar does not separate unknown
capture effects, content changes, feature-metric weighting or model mechanisms.
The result concerns finite-panel feature geometry. It does not validate painterly
style, physical brushwork, independent reproduction or new-scene transfer.

## Numerical bridge, tests and publication

The pure `compute(inputs, predecessor)` function constructs the complete new
grid, then recomputes the entire unchanged v1 analysis and requires exact
JSON-native equality to the supplied predecessor result before returning.
This includes all predecessor fitted maps, memberships, metrics and previously
specified deletion diagnostics. A mismatch aborts; old hashes/results are never
refreshed. The new result retains old metrics for comparison and records the
successful bridge separately from scientific findings.

Synthetic offline tests cover the mean-offset identity, unchanged centered
distances, known shift/scalar cases, finite inputs, positive weights, cases where
centering helps or harms a known feature distribution, full-grid aggregation,
unchanged old outputs, reference/named independence of the added centering,
and rejection of changed predecessor outcomes. They read no retained vectors
or pixels. A separate runner must commit/bind the source and inputs, preserve
the resulting output/receipt, and verify replay before manuscript integration.
