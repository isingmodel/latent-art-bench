# Prospective fixed-map comparison on new scene briefs

2026-09-10. Namespace `painter_map_validation_v2`; collection run
`pmv2-20260910`. **Prospective scientific contract, conditional on the single
R=10 offline qualification and a separate technical freeze. No collection or
new feature extraction is authorized by this document.** Maintainer-run LLM
agents designed the study, authored/reviewed its scene briefs, and contribute
analysis, implementation and manuscript advice. They are not independent human
or institutional investigators.

## Question and relationship to prior evidence

On twelve new fixed scene briefs, do the unchanged historical FLUX/Cezanne
translation and translation/scaling maps favor different orderings under
painting-reference energy and corrected prediction error for named scene means?
The historical expectation is higher energy but lower conditional-mean error
after scaling. Contrary orderings, agreement between the targets, uncertainty
and collection failure are equally reportable outcomes.

[DECISION.md](DECISION.md) records why this is a disclosed pre-data redesign.
V1 permanently stopped after every 96/144/192-output allocation failed its fixed
conditional-residual precision criterion. Its complete qualification remains at
`studies/painter_map_validation_v1/pmvqv1-20260910/`; no v1 result, source or
stopping decision changes. R=10 was chosen after those simulations but before
any new map-validation image outcome. The question, painter/service choice and
design are informed by historical outcomes, not independently selected. This is
the sole additional allocation assessment for this question in the current
revision, as fixed in DECISION.md. A failed qualification ends it.

## Fixed panel, prompting and measurement

[scenes.json](scenes.json) contains twelve authored briefs: four each of water,
built and land, with IDs `pmv2_water01` through `pmv2_land04`. Their bodies and
class labels are copied unchanged from the reviewed scene draft; only IDs and
inventory metadata change. The panel contains new scene specifications relative
to the earlier inventories, not a probability sample or a guarantee of semantic
out-of-distribution content or absence from model training. Classes describe
requested content, not independently verified image adherence.

Each scene has ten paired repetitions of artist-free F (`artist_free`) and
named N (`named`): **120 pairs, 120 images per arm, 240 outputs total**. The exact
Study 1 prompt scaffold is retained, with `{detailed}` replaced literally by
the brief body:

```text
F: Create an oil painting on canvas. Scene: {detailed} Render only the painting area, without a surrounding frame, signature, letters or watermark.
N: Create an oil painting on canvas. In the style of Paul Cezanne. Scene: {detailed} Render only the painting area, without a surrounding frame, signature, letters or watermark.
```

No reference image, generic painting clause, palette instruction or new rendering
seed is supplied. The historical OpenRouter route is
`black-forest-labs/flux.2-max`, restricted to `black-forest-labs/us-3`, with
`allow_fallbacks=false`, `n=1`, `aspect_ratio="1:1"` and `output_format="png"`.
No size, resolution or seed field is added. This identifies a requested service,
not independently attested weights. Randomized F/N positions and globally
interleaved scene/repeat pair order are fixed before collection; the technical
contract specifies their construction and dispatch.

Use only the existing `primary512` normalization, all 31 features, unchanged
221-work development scaler, and 32 retained Cezanne references. References have
weight 1/32. Class masses in water/built/land order are q=(3,11,18)/32; scene j
in class c has weight w_j=q_c/4, and each of its ten images has weight q_c/40.
No reweighting based on delivered content or results is allowed.

The original generated-only full-FLUX Cezanne fit supplies

```text
T1(f) = f + muN - muF
T2(f) = muN + a (f - muF),  a = 0.6785365094757265.
```

The authoritative historical inputs and full-fit record are respectively
`data/manifests/painter_naming_geometry_v1/pngv1-20260910/inputs.json`
(SHA256 `eeb3890268a85885f372bdb494e29ab558c271749667fb7e264a7e30881733de`)
and its `analysis.json`
(SHA256 `f50be0f772a3bff8f4bc66ddc20f3e19b5c13736fd6cced632d80224e2203324`).
Use the unique primary512/FLUX/Cezanne full-cohort transfer fit, not averaged
fold maps. Bound inputs must identify the exact scaler, feature order, reference
vectors and map parameters. Already standardized vectors are not scaled twice.
No map refit, new evaluation centering or reference-objective optimization occurs.

## Two primary targets

For reference X and a transformed free cloud Y, compute the full weighted
empirical V-energy, including self diagonals:

```text
E(X,Y) = 2 sum_i,l p_i b_l ||x_i-y_l||_2
         - sum_i,k p_i p_k ||x_i-x_k||_2
         - sum_l,m b_l b_m ||y_l-y_m||_2.
deltaE = E(X,T2(F)) - E(X,T1(F)).
```

Its sampling target is the **expected empirical finite-R=10 contrast** under
repeated collection on the fixed panel, conditional on the old maps, scaler and
references. It is not unbiased population-mixture energy. Changing R from v1's
candidates changes this energy target; hypothetical v1 targets are not pooled
with the new result.

For k=1,2, let e_k,jr=N_jr-Tk(F_jr). With R=10, compute

```text
Qk = sum_j w_j sum_(r != s) e_k,jr' e_k,js / [R(R-1)]
   = sum_j w_j (||mean_r e_k,jr||_2^2 - trace(S_k,j)/R),
deltaQ = Q2 - Q1,
```

where S_k,j is the unbiased sample covariance of the ten residuals. Under stable
zero-mean errors independent across repeats and scenes, Qk estimates weighted
squared conditional-mean mismatch. F/N dependence within a paired repetition is
allowed. Preserve negative Q and deltaQ without truncation. The correction
removes repeat noise, not historical map-estimation uncertainty. Energy uses
unsquared standardized distance; Q uses squared standardized coordinates. Both
are lower-is-better but have different targets and units.

## Prespecified uncertainty and interpretation

For each endpoint T, delete paired draw (j,r), preserving every scene and scene
weight. The affected scene's nine observations each receive q_c/36; its Q
denominator is 9x8. Other scenes retain q_c/40 and 10x9. Recompute the complete
endpoint for every deletion. For the ten deletions in scene j, let Tbar_-j be
their mean. The sole interval procedure is

```text
VJ(T) = sum_j (9/10) sum_r (T_-jr - Tbar_-j)^2,
interval(T) = T +/- t_(9,.9875) sqrt(VJ(T)).
```

The two Bonferroni marginal intervals aim at simultaneous 95% coverage; neither
the t critical value nor passing historical-proxy qualification proves actual
coverage. No scene resampling, map-label permutation, additional p-value,
equivalence test or alternative interval is used. A nonfinite point or
nonpositive/nonfinite variance withholds **both intervals**; finite full-grid
point values may still be reported descriptively, with unavailable quantities
explicitly marked.

An energy interval wholly above zero and a Q interval wholly below zero support
the historical opposing ordering under the stated sampling assumptions. Report
other resolved sign patterns as observed; an interval containing zero leaves
the joint direction unresolved. Opposite point-estimate signs alone do not
establish that joint conclusion. Randomized request order does not establish
independent stationary service errors. No painter-population, new-scene
population, perceptual-style, capture-validity or internal-mechanism claim follows.

## Completeness, reporting and remaining authorization

Both contrasts, their component scores and intervals require all **240 allocated
primary vectors**, with finite features and the separately frozen collection,
identity and timing eligibility conditions fulfilled. Otherwise the full-grid
scientific summaries are unavailable: no complete-case estimate, dropped scene,
changed weight, pooling or replacement. Retain every assigned slot's outcome
and delivered-image metadata. The interval-only exception above does not relax
collection or measurement completeness.

Report a two-endpoint table with point estimates, interval availability/bounds,
and the 120-pair/12-scene counts. E(X,T1F), E(X,T2F), Q1 and Q2 are point-value
interpretation aids only, with no extra tests or component intervals. Do not add
actual-name energy tests, retrieval, coverage, variance-ratio analyses, feature
or processing sweeps, scalar searches, or selectively chosen plots. Retain the
complete numerical results and pair/scene weights. All four painters remain in
the manuscript's earlier exploration; this experiment concerns only FLUX/Cezanne.

Before any collection, bind a passing R=10 qualification and the reviewed exact
scene/assignment inventory, source, measurement and analysis implementation.
The separate technical contract must fix payload and identity checks, paid-budget
reservations within the unchanged ceiling, concurrency and timing, permitted
technical retries, missingness, and terminal failure handling. No private credit
balance is part of this scientific protocol. Qualification alone opens no live
activity. Incomplete collection, contrary ordering or wide intervals trigger
neither more repetitions nor another cohort; earlier clause and capture studies
remain terminal and contribute no observations to this new comparison.
