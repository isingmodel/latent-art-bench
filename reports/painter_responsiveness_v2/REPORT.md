# Painter instructions, feature responsiveness and the original-painting gap

Computational follow-up, 8 September 2026. This report combines a newly completed
192-image experiment with a retained-data falsification analysis. No human ratings
or learned features were used.

The findings weaken a simple explanation that painter naming makes generated
paintings different by uniformly suppressing their responsiveness. Feature-space
contraction can coexist with **better scene retrieval**. In the new experiment,
a generic traditional-painting clause already reduces the response to color
instructions in a secondary contrast; additional attenuation from naming Monet or Cézanne is **unresolved
in the two prespecified primary comparisons**. The data suggest studying the
interaction of prompt wording, color level and distribution shape more closely.
They do not establish the internal cause of the original/generated discrepancy.

## Questions and design

The [earlier controlled study](../painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md)
found that painter naming can move generated feature distributions closer to the
retained digital paintings while reducing their variation. The
[computational revision](../painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md)
showed that between-scene and within-scene variation behave differently. This
follow-up tests two implications of a proposed responsiveness explanation:

1. Does reduced between-scene variation also mean poorer scene distinguishability?
2. Does a named painter reduce response to an explicit color instruction beyond
   what an ordinary painting-style clause does?

For the first question, each held-out generated image was assigned to the nearest
scene centroid computed from the other two repetitions. We retained all 24 scene
labels, also tested eight candidates within the same broad scene class, and used
five fixed feature views under three processing pipelines. These are descriptive
analyses of exposed data, without new significance tests.

For the second question, the fixed experiment crossed six landscape scenes, four
style arms, two color instructions and four repetitions: **192 images, all
successfully collected and measured**. All prompts requested an oil painting on
canvas. The four arms added no style clause, a generic traditional-landscape
clause, a Monet clause, or a Cézanne clause. Each requested either a muted,
low-chroma palette or a vivid, high-chroma palette. The generic and artist-free
outputs were shared controls. The local OAuth `gpt-image-2` name identifies the
deployed service route, not attested immutable model weights.
Returned geometry and reported quality varied despite fixed requested settings;
the estimand includes this delivered-service behavior.

The primary coordinate is median pixel CIELAB chroma, scaled using the previously
fixed development center and IQR. One reported unit is **7.34764 chroma units**;
the scale was not fitted to the new images. Let d(a) be the equal-scene average of
the vivid-minus-muted response in arm a. The two primary contrasts are
κ(Monet) = d(Monet) − d(generic) and κ(Cézanne) = d(Cézanne) − d(generic).
The [frozen protocol](../../studies/painter_responsiveness_v2/PROTOCOL.md)
specifies the six-scene estimand, paired repeat-block calculation, shared-control
covariance, approximate Welch–Satterthwaite inference, Bonferroni simultaneous
intervals and Holm adjustment for these two contrasts. Inference is conditional
on these scenes and service stability assumptions; it does not generalize to a
population of new scenes.

## Contraction does not necessarily destroy scene distinguishability

The primary 31-feature, 24-candidate retrieval results are:

| Route / painter | Artist-free accuracy | Named accuracy | Change, percentage points | Named/free between-scene variance |
| --- | ---: | ---: | ---: | ---: |
| Nano Banana 2 / Monet | 58.3% | 56.9% | −1.4 | 0.731 |
| Nano Banana 2 / Cézanne | 66.7% | 41.7% | −25.0 | 0.402 |
| FLUX / Monet | 44.4% | 59.7% | +15.3 | 0.336 |
| FLUX / Cézanne | 50.0% | 54.2% | +4.2 | 0.461 |
| OAuth / Monet | 79.2% | 70.8% | −8.3 | 0.515 |
| OAuth / Cézanne | 83.3% | 69.4% | −13.9 | 0.544 |

Each accuracy uses 72 held-repetition queries. FLUX/Monet is the clearest
counterexample: between-scene variation decreases by approximately 66.4%, yet
retrieval improves. Its positive retrieval difference persists across all three
pipelines and with candidates restricted to the same broad class. The
Nano Banana 2/Cézanne and OAuth/Cézanne declines persist across the five feature
views and three pipelines in both candidate settings. Thus there is evidence of
route- and painter-dependent changes in distinguishability, rather than a
universal loss caused by contraction. The Nano Banana 2/Monet primary difference
is only one correct query out of 72.

![Scene retrieval with and without painter names](prv2-oauth-20260908/diagnostics/plots/retrieval_accuracy.png)

Nearest-centroid retrieval measures geometry in the chosen feature space. It does
not establish correct objects, composition or semantic adherence. Neither the
retrieval gains nor aggregate variance ratios identify their internal cause.
All 450 comparisons, split identities and 25,920 predictions are retained in the
[diagnostic bundle](prv2-oauth-20260908/diagnostics/REPORT.md).

## Generic painting language already changes color responsiveness

All four arms respond positively to vivid versus muted instructions:

| Arm | Muted mean | Vivid mean | Response d(a) | Nominal 95% interval for d(a) |
| --- | ---: | ---: | ---: | --- |
| Artist-free | −0.137 | 3.351 | 3.489 | [3.361, 3.616] |
| Generic painting | 0.085 | 2.720 | 2.636 | [2.443, 2.828] |
| Monet | −0.643 | 1.709 | 2.351 | [2.179, 2.523] |
| Cézanne | −0.234 | 2.384 | 2.618 | [2.462, 2.773] |

Values are fixed development-IQR units; each arm/polarity mean uses 24 images.
The generic-minus-free response contrast is **−0.853**, with nominal interval
[−1.136, −0.570], a 24.5% reduction relative to the artist-free point estimate.
Monet-minus-free is −1.137 and Cézanne-minus-free is −0.871. These secondary
contrasts show why an artist-free comparison alone cannot isolate a
painter-specific attenuation effect. They are not additional primary tests.

![Color response by instruction and style arm](prv2-oauth-recovery-20260908/experiment/plots/arm_chroma.png)

The two primary comparisons are:

| Painter minus generic | κ estimate | Simultaneous 95% family interval | Holm-adjusted p |
| --- | ---: | --- | ---: |
| Monet | −0.284 | [−0.585, 0.016] | 0.0649 |
| Cézanne | −0.018 | [−0.343, 0.308] | 0.8886 |

Neither primary comparison establishes the direction after the prespecified
adjustment. Monet's point estimates are negative in all six scenes, but its
family interval includes zero. Cézanne's scene estimates have mixed signs and
its average is near zero. These results do not establish equivalence or prove
the absence of a smaller effect.

Processing sensitivity gives Monet estimates of −0.301 at resolution 256 and
−0.308 after JPEG90 processing, compared with −0.284 in the primary pipeline.
The JPEG interval narrowly excludes zero (upper endpoint −0.004), while the
resolution-256 interval includes it (upper endpoint 0.003). This fragile boundary
crossing does not replace the primary result. Cézanne remains unresolved under
both sensitivity pipelines. All 31 coordinate responses are exported as
descriptive estimates, without selecting new primary endpoints after inspection.

The means suggest a separate question about **color level**. Relative to the
generic arm, Monet lowers chroma under both muted and vivid instructions;
Cézanne does so too, while retaining almost the same vivid-minus-muted contrast.
A level shift and a response reduction are distinct effects. Two instruction
levels cannot distinguish a changed response gain from a shifted operating range
or nonlinear saturation.

## Connection to distributions of original paintings

The same 70 previously exposed digital references provide a descriptive chroma
comparison: 38 Monet and 32 Cézanne works. We compare empirical distributions,
not only their means. The following uses the empirical reference mixture and
the experiment's deliberately equal mixture of muted and vivid outputs.
Generated values in each row come from that painter's named arm.

| Painter | Reference mean | Generated mixture mean | Generated outputs inside reference central 80% range | References inside generated central 80% range | Wasserstein-1 distance |
| --- | ---: | ---: | ---: | ---: | ---: |
| Monet | 0.369 | 0.533 | 37.5% | 89.5% | 0.620 |
| Cézanne | 0.812 | 1.075 | 16.7% | 93.8% | 0.716 |

The comparatively close means and broad generated ranges obscure unequal mass
allocation. Many references fall inside the generated range, while most generated
outputs fall outside the reference's central range. Equal broad-class reference
weighting changes the distances to 0.603 and 0.759, respectively; all memberships
and weights are retained in the full tables.

For comparison, the same generic-control outputs have equal-class reference
distances of 1.071 to Monet and 0.787 to Cézanne. Naming therefore improves this
particular mixture comparison in both cases; this direction persists across the
three pipelines and both reference weightings. The data do not support a general
claim that naming makes the original chroma distribution harder to approach.
The free and generic controls shown against both painters are the same shared
generated images, not independent painter-specific control samples.

![Original and generated empirical chroma ranges](../painter_responsiveness_quantiles_v1/prqv1-20260908/prv2-oauth-recovery-20260908/plots/original_chroma_context.png)

This display uses the [exact-weight quantile corrigendum](../painter_responsiveness_quantiles_v1/prqv1-20260908/REPORT.md).
A floating-point CDF boundary error in the first publication affected some
descriptive medians, including the Monet empirical reference median. The correction
changes no primary estimates, means, Wasserstein distances, range endpoints or
range-occupancy results. Original records remain preserved.

Ranges are empirical 10th–90th percentiles, not confidence intervals. The forced
two-polarity mixture is an experimental construction, not the service's natural
output distribution. Its pattern therefore illustrates why mean or range overlap
is insufficient; it cannot by itself explain the earlier discrepancy measured
without explicit chroma-polarity manipulation.
These are one-coordinate comparisons with digital reproductions, not oeuvre
coverage or perceptual fidelity. Broad classes were assigned by a single
maintainer-run LLM; reference capture and fine-content matching remain unresolved.

## What the evidence changes

The proposed general chain—painter naming contracts feature space, therefore
scene information is lost, therefore generated paintings differ from originals—is
not supported as a universal explanation. The retrieval counterexample breaks
its first implication, and the controlled color experiment does not confirm the
two additional painter-specific attenuation effects. Ordinary painting language
and changes in color level are now concrete alternatives to investigate.

The most focused next computational question is whether several intermediate
color instructions trace different response curves under painter and generic
clauses. Multiple generic phrasings would test whether the result depends on the
single control sentence. This would distinguish level shifts, endpoint saturation
and response slopes more directly than adding more artists or indiscriminately
adding repeats. It requires a new prospective study; the current evidence remains
closed and is not extended until a favorable threshold is crossed.

A material limitation is that the service did not honor all requested rendering
fields. All 192 primary images were nonsquare RGB PNGs despite a 1024×1024 request;
174 reported low quality and 18 medium despite a fixed medium-quality request.
The medium-quality counts were 10/48, 4/48, 3/48 and 1/48 for free, generic, Monet
and Cézanne. Geometry also differed across arms. These fields were retained without
postselection or adjustment. Consequently the effects concern the deployed
service's complete response to the prompts, including any rendering changes,
rather than an isolated internal style mechanism at matched delivery settings.

## Evidence and reproduction

The sole primary collection is `prv2-oauth-recovery-20260908`. A predecessor stopped
after 49 successful outputs and one complete plain-text HTTP 503; its remaining
142 slots were never started. An exact-error transport correction and a new
collection identity using the same frozen design and dispatch order were fixed
before successful images were visually reviewed or their
scientific features extracted. The predecessor was measured only after the
replacement became terminal. Its selected outputs remain
[ancillary](prv2-oauth-20260908/experiment/REPORT.md), with primary inference withheld
and no pooling into the 192-image result. Across both runs, 242 actual attempts
produced 241 unique images. Incremental OpenRouter spending was $0.

The [primary experiment bundle](prv2-oauth-recovery-20260908/experiment/REPORT.md)
contains all 19 numeric tables and four plot pairs. Methods, computation,
collection and plotting are mapped in the [analysis catalog](../../docs/ANALYSES.md).
Run `make computational-responsiveness` to recompute retained-vector analyses and
verify report bytes, including the quantile correction. It makes no network calls or feature re-extractions, but
requires the retained local response archive for raw hash verification. Source,
protocols, ledgers and publication receipts remain commit bound.

Three maintainer-run LLM subagents reviewed statistical interpretation, transport
integrity and report rendering, with coordinator checks. These are computational
and editorial checks, not independent human or institutional validation; see the
[review record](../../docs/reviews/20260908_computational_responsiveness/REVIEW.md).
