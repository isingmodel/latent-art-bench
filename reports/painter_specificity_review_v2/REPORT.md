# Review clarification diagnostics

This is a **post-result descriptive extension**, using the retained measurement
vectors and the original review diagnostics. It adds no primary endpoints,
generation, feature extraction or human evaluation. The target remains the
specified reference collection in the declared 31-feature space.

The [plan](../../studies/painter_specificity_review_v2/PLAN.md) records the scope;
the [complete numerical record](analysis.json) binds sources, inputs and tests
with SHA-256. It contains every deletion, every calibration fit, all 1,000
observed and conditional expected control scores, and every simulated endpoint's
coverage. Run `.venv/bin/python -m latent_art_bench.painter_specificity_review_v2 check`
for exact offline replay. Its create-once writer refuses to replace results.

## Generic/common alignment

Let `gk` and `ck` be the generic-minus-free and mean-named-minus-free contrasts,
respectively, averaged across scenes separately for repeat `k`. The new ratio is
`((g0·c1 + g1·c0)/2) / sqrt((g0·g1)(c0·c1))`. It removes the same-repeat shared-control
term from the numerator and corrects both squared norms with cross-repeat
products. The ratio itself is not unbiased, bounded, or a confidence interval;
it is unavailable when either squared-norm estimate is nonpositive. Independence
between repeat errors is still an assumption. Primary D does not use this ratio.

| Model | Original plug-in cosine | Cross-repeat ratio | Single-scene deletion range |
| --- | ---: | ---: | --- |
| GPT Image 1 | .693 | .689 | [.612, .743] |
| GPT Image 2 | .769 | .774 | [.752, .790] |
| GPT Image 2.5 Flare | .765 | .766 | [.737, .784] |
| GPT Image 2.5 Sunburst | .832 | .837 | [.824, .848] |
| Nano Banana 2 | .857 | .930 | [.877, .972] |
| FLUX.2 Max | .888 | .916 | [.899, .968] |

All 84 deletion ratios are available and positive. This supports positive
generic/common alignment within the retained panel under the same repeat
assumption; the direction is not an artifact of the original plug-in numerator.
The correction need not lower a ratio because it also changes the denominator.

## Calibrated ordering and reference controls

GPT Image 2 minus FLUX.2 Max held-scene calibrated D is **−.15991**. GPT Image 2
has lower error in **12 of 14** held-scene scores. After each single-scene deletion,
refitting the entire calibration procedure gives differences **[−.18850, −.13728]**.
These are point-estimate sensitivity checks. The 14 folds overlap and cannot
support a binomial test or be treated as 14 independent studies. Every inner
scalar uses the other 12 scenes after an outer deletion. Calibrated vectors are
counterfactual and need not correspond to realizable images.

The original sampled real-control scores replay **exactly**, for all three
controls and all 1,000 stratified disjoint half-splits. Conditional on each split,
independently drawn repeats have expected cross-product error equal to the
squared error between the held-pool mean contrast and the training target. This
integrates out two-work sampling while preserving reference split variability.

| Control | Original sampled central 95% range | Conditional expected median | Conditional expected central 95% range |
| --- | --- | ---: | --- |
| Pooled real, pooled target | [−.758, 1.380] | .236 | [.135, .428] |
| Class real, pooled target | [−.554, 2.400] | .731 | [.544, .993] |
| Class real, class target | [−.248, 1.946] | .706 | [.517, .954] |

Much of the original width therefore reflects sparse sampling rather than
variation between reference splits alone. Residual reference disagreement
remains. The narrower ranges are **not** uncertainty intervals for the generated
model scores, population confidence intervals, or artistic thresholds. They do
not remove collection content imbalance, source artifacts or target-estimation
error. Sampled D can be negative; these conditional squared mean errors cannot.

## Noise magnitude and correlated-noise simulation

Observed per-repeat noise power relative to H is estimated directly as
`mean_s ||center(x_s0,named − x_s1,named)||² / (2H)`. The assessment's approximation
instead uses `0.75` times the sum of marginal artist traces, assuming no
cross-artist error covariance. Both estimates are retained for transparency.

| Model | Direct centered estimate | Independent-artist approximation |
| --- | ---: | ---: |
| GPT Image 1 | 2.024 | 1.896 |
| GPT Image 2 | .960 | .969 |
| GPT Image 2.5 Flare | .424 | .436 |
| GPT Image 2.5 Sunburst | .583 | .535 |
| Nano Banana 2 | 2.596 | 2.666 |
| FLUX.2 Max | 1.674 | 1.570 |

The new simulation retains the original fixed model means and the exact family
of six slopes plus 15 paired D differences, using `t(13, 1−.05/(2×21)) = 3.76017`.
Noise is Gaussian and independent across scenes, models and repeats. Isotropic
noise has trace equal to the specified power in the 93-dimensional centered
space. Correlated noise has rank three, lies along the three reference SVD
components, and allocates power .66343/.20643/.13014 to those orthogonal axes.
These weights describe the reference centroid contrast, which has at most three
nonzero singular components because four artist means were centered; they are
not a discovered representation inside the generators.

| Centered noise power | Isotropic family coverage | Reference-aligned rank-three coverage |
| ---: | ---: | ---: |
| .5 | 95.40% | 96.32% |
| 1.5 | 95.06% | 96.80% |
| 3.0 | 95.66% | 96.34% |

Each cell uses 5,000 repetitions. Monte Carlo standard errors are .25–.31
percentage points, and the largest absolute model-level mean D bias is .0165.
The observed average noise powers agree with the specified powers within .03%.
The grid covers the observed magnitudes, although .5 is slightly above the
smallest observed estimate, .424. It is not fitted to API errors and does not
verify independence. The original heavy-tail, fixed-interaction and shared-state
simulation results remain separately preserved; in particular, the original
shared-state failure still applies.

## Compact manuscript replacements

These sentences can replace existing discussion rather than add a section:

> A symmetric cross-repeat generic/common alignment ratio is .689–.930 and remains
> positive under every single-scene deletion, supporting the common direction
> after correcting the shared-control moments.
>
> GPT Image 2's calibrated error is lower than FLUX's on 12/14 held scenes and after
> every scene deletion with full refitting (difference −.189 to −.137), a
> descriptive stability check rather than a new ranking test.
>
> Integrating out two-work sampling narrows the pooled real-control central 95%
> range from [−.758, 1.380] to [.135, .428], so sparse sampling explains much of its
> width while collection disagreement remains.

For the existing simulation sentence, a compact replacement is:

> Across noise powers .5, 1.5 and 3 with isotropic or reference-aligned rank-three
> Gaussian errors, 5,000 repetitions per case gave 95.06–96.80% coverage for the
> 21-interval family; these independent-error models do not establish API
> independence, whose violation caused the original shared-state failure.

The full report should remain a repository supplement; no new manuscript table
is needed. The reference-quality audit is a separate diagnostic with its own
scope and outputs.

## Verification

Ten new tests pass. They check the cross-moment correction analytically under
shared-control noise; exchangeability of repeat order and unavailable/unbounded
ratios; exact finite-pool expectations by exhaustive enumeration; target
normalization; original real-control RNG replay; full inner refitting after
scene deletion; artist-centering of noise power; covariance trace/rank/alignment;
the exact 21-endpoint construction; and noise power and independent-repeat bias.
The source and tests pass Ruff. The full diagnostic `check` requires numerical
equality with the saved result, including original calibration and all sampled
real controls.
