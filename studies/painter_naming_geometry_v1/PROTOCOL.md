# Painter naming geometry — post-result diagnostic, version 1

## Question and status

Does the observed improvement in proximity to the fixed painting panel require
more than a global location/scale change of artist-free feature vectors? Does
the same map transfer to the later FLUX collection, and does it preserve the
conditional organization of the fixed scenes?

This is a new, offline analysis of previously exposed observations, motivated by
three maintainer-run LLM reviews on 10 September 2026. It is **post-result and
descriptive**, not an unexposed confirmatory experiment. Reviewer 1 had already
calculated equal-scene corrected-variance ratios before this protocol; those
calculations are disclosed in its round-1 report. None of the maps below had
been evaluated on the research observations when this protocol was written.
The original studies, all four-painter exploration results and primary tests
remain unchanged. This protocol authorizes no image access, feature extraction,
external-holdout access, generation transport or spending.

## Fixed inputs and representation

Use only the public numerical release's original Study 1 vectors/scalers and
later naming vectors, plus the sealed common-square measurement vectors. The
complete detailed naming comparisons are six service/painter cells, each with
24 scenes and three free/named repeat pairs (864 original images). The later
FLUX collection has 24 scenes, one shared free output and two named outputs per
scene (72 images). The original Monet/Cézanne reference panel remains 38/32
works; the scaler remains fitted on 221 development works. No outcomes are
removed or selected. Scene and image identifiers are retained in the input
inventory. All source files and inputs must be clean and commit-bound before
the create-once analysis output is written.

Primary presentation uses the 31-coordinate primary512 metric. Prespecified
descriptive sensitivities cross the three existing pipelines with all31,
no_lbp8 (remove coordinate 25, the dominant blur-response coordinate identified
in the predecessor measurement study), and nontexture19 (coordinates 0–18).
Also analyze all31 on the existing common-square original vectors using the
unchanged primary512 scaler. No new square vectors are extracted for the later
cohort. Report all views without choosing a favorable metric. Reference works
have equal weight. Generated scene mass equals the original reference content
proportions, divided equally among scenes within each class and then repeats.

## Global moment benchmarks and held-scene evaluation

For weighted training clouds F and N, estimate means mu_F, mu_N and population
traces V_F, V_N. Define identity T0(y)=y, translation T1(y)=y+mu_N−mu_F, and
translation/scale T2(y)=mu_N+sqrt(V_N/V_F)(y−mu_F). Require finite positive
training traces. These maps use generated training observations only: no
reference objective, learned metric, affine rotation or outcome-selected fit.
The scalar is an algorithmic moment match, not a noise-corrected latent gain.
Transformed coordinates need not correspond to any realizable image.

Sort the eight scene IDs within each of the three classes. Assign zero-based
position modulo four to folds 0–3: each fold holds out six whole scenes, two per
class. Fit on the other 18 scenes (54 vectors/condition); evaluate on the 18
held-out vectors/condition. Calculate each fold separately and average its
energy values equally. Never pool clouds produced by different fitted maps.
This 18-query fold score omits between-fold generated self-distances and has
a different finite-sample baseline from the original full 72-query energy.
Compare actual and benchmark on this same fold scale; the residual is not an
additive decomposition of the original full-cloud naming contrast.

Report all four clouds' weighted V-energy to the same reference panel, with
the attraction and generated within-distance terms. The principal descriptive
residual is E(reference,N_test)−E(reference,T2(F_test)); also report T1 residuals
and the observed N−F contrast. Negative residual means actual naming is closer
than this benchmark, positive means the benchmark is closer. A near-zero
residual does not establish equivalence. Do not report a percentage explained.

For occupancy, form one ball around every reference work, with radius its third
nearest other reference. Use the same anchors/radii and exactly the same query
identities for each map; actual named queries use their paired slots. Held-out
queries are 18 equal-class vectors, later queries are 24 equal-class vectors.
This unweighted occupancy diagnostic has different anchor/query support from
the predecessor matched-real coverage display and has no real/real calibration.
It measures ball hits, not recovered reference probability mass.

Recompute the entire four-fold procedure after deleting each scene in turn,
renormalizing scene weights within each fold and each of the three classes.
Fold IDs and equal fold aggregation stay fixed. Consequently a surviving scene
in a depleted fold/class receives more effective mass than same-class scenes
in other folds; this is a specified deletion sensitivity, not a globally equal
weight mean over the remaining scenes. Retain all 24 residuals,
not a confidence interval. Overlapping training folds are dependent; no t test,
ordinary sign-flip test of fitted residuals, population interval, equivalence
margin or selected significance threshold is introduced.

## Later-cohort transfer

Fit one T1/T2 map per painter on all 72 original FLUX observations per arm.
Apply it unchanged to the later 24 free outputs and compare with the later
24 named outputs using the original panel/scaler and identical cohort weights.
Report absolute energies, map parameters and occupancy, with leave-one-later-
scene stability while keeping the original map fixed. This tests temporal
transfer on already exposed observations of the same templates; it is not
independent-investigator or new-scene validation. Do not pool cohorts or refit
to improve the later results. R=1 precludes repeat-noise correction there.

## Conditional geometry and finite-repeat correction

Let z_br be a feature vector for scene b and repeat r, R=3, with fixed positive
scene masses w_b summing to one. Report observed B=sum w_b||mean_b−mean||²,
W=sum w_b R^−1 sum_r||z_br−mean_b||², and V=B+W. Let S_b be the unbiased
within-scene covariance. Under zero-mean repeat errors independent across
repeats and scenes, report N*=sum w_b tr(S_b) and
B*=B−sum w_b(1−w_b)tr(S_b)/R. Keep negative corrected values. These assumptions
are not guaranteed by randomized request order. Report named/free ratios and
B*/N* under both reference-content and equal-scene weights, with zero
denominators explicitly unavailable. The two weightings answer different
questions. They are not pooled.

For each held-out scene define e_br=N_br−T(F_br), with T fitted only on other
scenes. Estimate conditional-mean mismatch by
sum_b w_b sum_(r!=s) e_br' e_bs / [R(R−1)]. This subtracts the positive finite-
repeat contribution from the naive squared mean residual. Conditional on the
training fit and zero-mean errors independent across repeats and scenes, it
estimates weighted squared conditional-mean mismatch; within-repeat pairing
dependence is allowed. Retain negative estimates and per-scene contributions;
do not use their signs as significance tests. This diagnostic concerns scene
means, not equality of complete conditional distributions. Synthetic known-
map and independent heteroscedastic-noise tests check the implementation.

Uniform translation and positive isotropic scaling preserve nearest-centroid
scene retrieval when applied consistently to all queries and candidate
centroids. Thus this benchmark cannot explain a change in the existing
retrieval score. Relate the corrected variance and conditional residuals to
the predecessor retrieval results without adding a new retrieval test family.

## Reproduction and interpretation

Publish a compact vector inventory, protocol/source bindings, complete results,
all fold/deletion diagnostics, and a deterministic figure/report in this new
namespace. Replay must verify bindings and all numerical outputs. Frozen
predecessors and the existing public release remain untouched. Any future
method change requires a separately documented successor, not refreshed hashes.

The result can support or challenge a simple *measured proximity account*.
It cannot identify internal model training mechanisms, physical brushwork,
perceptual style, or undocumented photographic processing. Lack of extra
proximity benefit does not imply distribution equality; a residual does not
show that naming has learned artist-specific features. The same maintainer
operates all three LLM reviewers; two reviewers assist with the statistical
implementation after their baseline reviews, which must be disclosed on
re-review. Scores remain governed by the unchanged nine-score rubric.
