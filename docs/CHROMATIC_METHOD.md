# Chromatic-distance and seamlessness implementation

## Source definition

The primary source is Lee et al. (2018), [“Heterogeneity in chromatic distance in images and characterization of massive painting data set”](https://doi.org/10.1371/journal.pone.0204430); the complete version of record is also available on the [PLOS article page](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0204430).

For an sRGB image, the project converts every pixel to CIE 1976 L\*a\*b\* under D65 and computes Euclidean CIELab distance (Delta E 1976) for every horizontal and vertical adjacent-pixel pair. Diagonal and wraparound pairs are excluded. For width `W` and height `H`, the sample contains

```text
H * (W - 1) + (H - 1) * W
```

distances. Let `d_bar` be their arithmetic mean and `sigma_d` their population standard deviation (`ddof=0`). The paper's scale-free distribution rescales distance by `d_bar`; its seamlessness statistic is

```text
S = (sigma_d / d_bar - 1) / (sigma_d / d_bar + 1)
  = (sigma_d - d_bar) / (sigma_d + d_bar).
```

A delta-like distribution approaches `-1`, an exponential distribution approaches `0`, and an increasingly heavy-tailed distribution approaches `1`.

The paper reports resolution dependence for the raw distance distribution and collapse of the **full mean-rescaled distributions** across the 500, 1000, 1500, 2000, 2500, and 3000 pixel versions shown in Figure 1. That distributional collapse is a defining empirical behavior of the source method. Computing the scalar `S` correctly is necessary, but it cannot establish the collapse: many different distributions have the same mean and coefficient of variation and therefore the same `S`.

Lee et al. also excluded partial images of larger originals, non-rectangular frames, seriously damaged images, photographs, and other inputs outside their painting domain. The paper does not define ICC handling, a JPEG quality/subsampling condition, a cross-reproduction equivalence margin, or invariance to arbitrary acquisition pipelines. Project tests of those properties are explicit extensions and must not be attributed to Lee et al.

## Versioned project decisions

Shared implementation decisions are:

- direct conversion through the standard sRGB transfer curve, D65 sRGB-to-XYZ matrix, and CIELab transform so dependency changes cannot silently change color conversion;
- exact zero-distance images are the limiting delta case `S = -1`, coefficient of variation `0`, and an all-zero normalized-distance sample, marked `degenerate`;
- resolution, resampling, color management, compression, and reproduction identity remain named acquisition conditions rather than assumed-away nuisances.

`pilot_0` feature version `lee2018-deltae76-seamlessness-v1` used an 11-bin histogram of `d / d_bar` as its multivariate feature and retained `S` as a scalar. Its frozen bin edges remain in `configs/pilot_0/pilot.yaml` for historical reproduction.

`pilot_1` feature version `lee2018-seamlessness-s-v2` makes scalar `S` the sole primary vector. The histogram and quantiles remain provenance diagnostics, not extra coordinates that can change the primary qualification. The v2 evaluator additionally:

- normalizes EXIF orientation and ICC content to sRGB before measurement;
- derives native-to-500, native-to-400, and native-to-256 lossless branches independently rather than cascading resizes;
- derives matched-input lossless and JPEG treatments from the same normalized 1024-pixel parent before canonicalizing each to 500;
- verifies exact repeated lossless pixels and containers;
- groups multiple alternate captures into one median distance per physical work;
- fits a fresh standardizer inside each leave-source-out fold;
- uses 2,000 artist-stratified bootstrap draws and requires the 95% upper confidence bound, not only the point ratio, to clear the frozen margin.

## Formula checks are not source-behavior recovery

The v2 synthetic tests recover the intended analytic behavior of the scalar formula:

| Check | Value |
|---|---:|
| Delta seamlessness | `-1.0` |
| Exponential seamlessness | `-0.00024142878088992257` |
| Heavy-tail seamlessness | `0.9386634042914666` |
| Absolute scale-invariance error | `8.326672684688674e-17` |

These checks validate the statistic and implementation contract. They neither reproduce the paper's full 179,853-image historical analysis nor test the full shape of the normalized adjacent-distance distribution.

## Adapted full-distribution diagnostic

For every `pilot_1` primary image, v2 compares the empirical CDF of every mean-rescaled adjacent-pixel distance, `d / d_bar`, between the independently derived 500 and 400 pixel branches and between the 500 and 256 pixel branches. The two-sample Kolmogorov-Smirnov distance must be at most `0.05` for **both** comparisons for an image to pass. This threshold is a frozen project equivalence margin; Lee et al. did not report a numerical K-S criterion.

The raw adapted diagnostic produced 216 defined pair comparisons. Of 108 primary images, 91 passed both comparisons and 17 missed the margin on at least one branch. The median K-S distance was `0.0185638889`, and the maximum was `0.1031922796`.

This result does not recover the paper behavior, even though most images pass the adapted diagnostic:

- the project evaluated 500/400/256 pixels, not Figure 1's 500-3000 pixel branch set;
- 0/108 primary files natively support the 3000 pixel maximum without upsampling;
- 0/108 primary files have a clear border review, and the current manifest has no explicit partial-capture or serious-damage review fields;
- the frozen aggregation rule requires every eligible image and every resolution comparison to pass, while 17 images missed at least one adapted comparison; and
- the margin was frozen before the first full-distribution evaluation, but after this corpus had already been collected, so it is not prospective to corpus collection.

The evidence therefore records `paper_resolution_collapse_status: ineligible` and `source_behavior_recovered: false`. Scalar `S`, analytic delta/exponential/heavy-tail checks, or stable scalar values at selected sizes cannot override that result.

## Pilot_0 outcome remains failed

The historical real-only run evaluated 108 canonical works and 11 alternate images. Exact preprocessing was deterministic for 119/119 inputs, and 256-pixel drift was `0.4936563346` of the within-artist median. Q85 JPEG drift was `0.6927977711`, exceeding the frozen `0.5` margin. The `pilot_0` measurement card therefore remains `fail`; later protocol work does not alter it. Full evidence is in `reports/pilot_0/evidence/chromatic_qualification.json`.

## Pilot_1 outcome: fail

The v2 run evaluated 108 primary works, 97 matched-input codec-eligible works, and 11 alternate images grouped into 7 independent works. The frozen real split contains 76 training and 32 held-out works.

| Diagnostic | Point ratio or score | 95% interval | Result |
|---|---:|---:|---|
| Lossless repeat determinism | 119/119 | exact | supported |
| Adapted full-distribution collapse | 91/108 images | K-S `D <= 0.05` for both pairs | **unsupported overall** |
| Lee input-domain review | 0/108 border-cleared | partial/damage reviews absent | **ineligible** |
| Native support for Figure 1 through 3000 px | 0/108 | exact | **ineligible** |
| Direct native 400 vs 500 | `0.0819375820` | `[0.0580938772, 0.1279254608]` | supported |
| Direct native 256 vs 500 | `0.2604446675` | `[0.1718565735, 0.3900617693]` | supported |
| Matched 1024 Q95 4:4:4 vs lossless | `0.0558064356` | `[0.0414253939, 0.0804704261]` | supported secondary sensitivity |
| Matched 1024 Q85 4:2:0 vs lossless | `0.4325558376` | `[0.2634302557, 0.6231027032]` | **unsupported** |
| Grouped same-work reproduction | `0.5882766278` | `[0.2433774343, 1.8285907947]` | **unsupported** |
| Held-out artist balanced accuracy | `0.3506944444` | not estimated | clears `0.35` narrowly |
| Held-out source balanced accuracy | `0.2416666667` | not estimated | below `0.55` |
| Nested leave-source-out artist balanced accuracy | `0.3369674185` | not estimated | pooled threshold clears, but not every source fold clears |

The v2 card is `fail`. The exact lossless-processing and direct-resolution results remain useful engineering diagnostics, and Q95 4:4:4 remains a secondary sensitivity result. They do not create a scientific conditional pass when the defining source behavior was not recovered. Q85 4:2:0 and reproduction stability also failed because their 95% upper bounds exceed `0.5` and `1.0`, respectively.

No claim extends to arbitrary JPEG recompression, unrepresented digitization pipelines, upsampling, physical artworks, broad source invariance, or Lee et al.'s reported resolution collapse. Per-source artist performance varied materially and not every held-source fold cleared the frozen minimum, so the pooled score is a limited construct diagnostic rather than artist recognition.

The complete current result is [the `pilot_1` chromatic qualification evidence](../reports/pilot_1/evidence/chromatic_qualification.json). Its protocol is `lee2018-chromatic-qualification-v3`; the evidence carries the protocol, feature-config, result, probe, and distribution hashes needed to audit the decision.

## Proper next test

A scientific `pilot_2` must be prospective and use new or still-sealed real data. Before extraction, it should record border, partial-capture, damage, and painting-medium eligibility; obtain native files supporting the preregistered resolution set without upsampling; and freeze a full-distribution comparison and all-record aggregation rule. If 3000 pixel sources are not obtainable, the study should define a new adapted multiscale protocol and stop calling it a replication of Lee et al.'s Figure 1 result. The scalar formula tests should remain unit tests, not a substitute for the empirical distribution test.

Implementation details live in `src/latent_art_bench/features/chromatic.py` and `src/latent_art_bench/evaluation/chromatic_v2.py`; unit tests cover color conversion, adjacency, analytic distribution cases, branch provenance, nested fitting, grouped alternates, and confidence-bound gating.
