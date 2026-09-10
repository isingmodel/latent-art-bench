# Results audit 1: painter naming geometry

Date: 10 September 2026. Run: `pngv1-20260910`.

This is a maintainer-run LLM audit. After completing my baseline manuscript review, I implemented the successor's `variance.py` and its tests. I am therefore not an implementation-independent reviewer. The arithmetic checks below were written separately, without importing any functions from `painter_naming_geometry_v1`; that computational separation does not establish independence of the investigator. No new manuscript scores are assigned here.

## Scope and outcome

I read the complete successor `REPORT.md`, the frozen protocol, the result JSON and its input inventory. I checked all 60 original sensitivity cells and all 18 temporal-transfer cells, rather than selecting only favorable primary results. Source and numerical evidence remained unchanged. The only new artifact from this audit is this document.

**Outcome:** no numerical or fold-leakage defect was found. A direct implementation made **15,546 numerical comparisons**, with maximum absolute difference **1.4210854715202004e-14** against the stored results. Another **660 aggregation checks** verified the reported mean energies, occupancy and residuals. The largest energy-mean difference there was **8.881784197001252e-16**. Comparisons used `atol=rtol=1e-10`; the actual discrepancies were much smaller.

The important qualifications concern interpretation and heterogeneity. All 60 original average named-minus-shift/scale residuals are negative, but 70 of their 240 individual fold residuals are positive. Pure shift beats actual naming in both primary temporal comparisons, but that result reverses for Monet under one scene deletion and all three 256-pixel views. Positive corrected conditional residuals are noisy estimates of mean mismatch, not significance tests or proof against a population model.

## Evidence identities and checks

- Source commit: `459c6a88a10a209ba22619dc38d616588da8817c`.
- Freeze commit supplied by the coordinator: `8facfa3`.
- Freeze SHA256: `54b265f2777f79822057492babb3a26ac491797ec3e45eef35f17315b85a4b5b`.
- Input-inventory SHA256: `eeb3890268a85885f372bdb494e29ab558c271749667fb7e264a7e30881733de`.
- Analysis SHA256: `f50be0f772a3bff8f4bc66ddc20f3e19b5c13736fd6cced632d80224e2203324`.
- Report SHA256: `31a30614e52a74434e3477f2a193e787640dbac83205c687d68d2bd6478c8cfc`.

All 14 freeze-bound files matched their local hashes and their bytes at the recorded source commit, obtained with `git show`. All three receipt-bound outputs matched their hashes; the receipt's freeze hash also matched. The numerical inventory contains 864 original detailed images and 72 later naming images; no new images were acquired or measured. Sixty-five focused variance/geometry tests passed in 0.72 seconds. This review did not rerun the full suite; the coordinator owns final repository-wide verification.

## Independent calculation method

The audit used only JSON reads, NumPy and the recorded vectors. In particular, it did not call the frozen map, variance, residual, energy, fold or orchestration functions.

1. Pairwise Euclidean distances were formed by explicit broadcasting and square-rooted sums of squared coordinate differences. Weighted energy used direct cross-domain and within-domain sums.
2. Map traces were recomputed as one half of the weighted sum of pairwise squared distances. Weighted means and the square root of the named/free trace ratio then defined the maps.
3. Four folds were reconstructed independently from sorted scene IDs within class. Every stored train/test membership and held-scene weight was checked. All three repeats of every held scene were excluded from that fold's fit.
4. For variance, within-scene sample-covariance trace was recovered from pairwise repeat distances: `sum_(r,s) ||y_r-y_s||² / [2R(R−1)]`. Between-scene trace was obtained from weighted pairwise scene-mean distances. These quantities independently give the repeat-noise trace and finite-repeat correction.
5. Conditional residuals were computed by summing every off-diagonal repeat inner product `e_br' e_bs`, divided by `R(R−1)`, then applying scene weights. This avoids the subtraction-based implementation under audit. Every corresponding weighted scene contribution was also checked.
6. All 144 primary original scene deletions were recomputed with the original four-fold assignment, fresh training fits and the specified within-class renormalization. All 48 primary temporal deletions were recomputed with the original full-cohort map fixed.
7. All 18 temporal maps were independently recovered from the original 72 observations per arm; no later observation entered their fit. Every temporal energy term was compared. The absence of an R=1 residual correction was checked.
8. All original fold occupancy values were independently recomputed from the complete reference anchors and their third-other-neighbor radii. This audit does not reinterpret these as matched-real coverage or probability-mass recovery.

The fixed-fold deletion target is correctly different from a globally reweighted remaining-scene mixture: the affected fold has five scenes, other folds retain six, and each fold still has one quarter of the outer weight. The protocol declares this as conditional stability. No deletion range is a confidence interval.

## Held-scene proximity and sign stability

Negative residuals favor actual naming. Values below use the primary 31-coordinate pipeline.

| Cell | Named minus shift/scale | Negative / positive folds | Delete-one range | Negative / positive deletions |
| --- | ---: | ---: | --- | ---: |
| NB2 / Monet | −.358837 | 2 / 2 | [−.559144, −.180429] | 24 / 0 |
| NB2 / Cézanne | −.219507 | 2 / 2 | [−.375651, −.138349] | 24 / 0 |
| FLUX / Monet | −.311862 | 4 / 0 | [−.641650, −.079851] | 24 / 0 |
| FLUX / Cézanne | −.191520 | 3 / 1 | [−.274740, −.142175] | 24 / 0 |
| OAuth / Monet | −.129299 | 3 / 1 | [−.246532, −.043243] | 24 / 0 |
| OAuth / Cézanne | −.026421 | 3 / 1 | [−.121696, +.055520] | 23 / 1 |

There are 17 negative and seven positive primary fold residuals. The positive OAuth/Cézanne deletion is `built01`. Across the entire original sensitivity grid, all 60 mean residuals favor actual naming, with 170 negative and 70 positive individual folds. These correlated direction counts are descriptive; the evidence does not support replacing them with a test of 60 or 240 independent observations.

The simpler translation-only comparison deserves equal visibility. It favors actual naming in five of six primary original cells, but OAuth/Cézanne has named-minus-shift **+.067743**. Across the 60 original cells, 51 translation-only residuals favor naming. Thus “actual naming improves beyond both global benchmarks everywhere” would be false, even though the shift/scale mean comparison is uniformly negative.

## Temporal pure shift versus shift/scale

| Painter | Pure shift energy | Shift/scale energy | Actual named energy | Named minus shift | Named minus shift/scale |
| --- | ---: | ---: | ---: | ---: | ---: |
| Monet | 1.470401 | 1.900722 | 1.570522 | +.100121 | −.330200 |
| Cézanne | .736045 | .992087 | .820251 | +.084206 | −.171835 |

All 24 primary temporal deletions preserve the negative named-minus-shift/scale result for each painter. Their ranges are [−.430323, −.222457] for Monet and [−.219638, −.136015] for Cézanne.

The pure-shift result is less uniform. Monet's named-minus-shift range is **[−.026011, +.215322]**; omitting `water05` makes actual naming closer, while the other 23 deletions favor pure shift. Cézanne's range is **[+.036282, +.126721]**, favoring pure shift in every deletion. Across the 18 transfer views, 15 favor pure shift over actual naming. The three exceptions are all Monet at 256 pixels: −.123106 with all 31 coordinates, −.145598 without LBP8, and −.095162 without texture.

The energy terms give a concrete arithmetic account of the primary temporal result. Adding the fitted contraction to the pure shift decreases the doubled reference-to-generated distance by **1.942287** for Monet and **1.207264** for Cézanne. It also decreases the within-generated mean distance by **2.372607** and **1.463305**. Since within-generated distance is subtracted in energy, the latter change more than offsets the former, increasing energy by **.430320** and **.256042**. The fitted contraction therefore worsens this measured proximity relative to translation alone.

The original fitted scales are **.575142** and **.678537**. For scale context, directly computed later empirical named/free trace square roots are **.682548** and **.857657**. The retained old map contracts more than the later empirical naming transformation in this scalar sense. These are observed moment ratios, not latent gains or a test of temporal drift; the original and later allocations differ and the later scene means have one observation each.

## Conditional residual magnitude and repeat correction

The following quantities are four-fold means with reference-content weights. They sum squared differences across **31 development-IQR-standardized coordinates**. They are not 31 equally perceptually important measurements, and the sum should not be described as a single-coordinate chroma difference.

| Cell | Naive squared mean residual | Repeat-noise correction | Corrected cross-repeat residual | Correction / naive | Corrected / 31 |
| --- | ---: | ---: | ---: | ---: | ---: |
| NB2 / Monet | 6.982540 | 4.437772 | 2.544769 | 63.6% | .082089 |
| NB2 / Cézanne | 6.026300 | 3.231997 | 2.794303 | 53.6% | .090139 |
| FLUX / Monet | 5.527013 | 2.241034 | 3.285979 | 40.5% | .105999 |
| FLUX / Cézanne | 3.973314 | 1.909974 | 2.063341 | 48.1% | .066559 |
| OAuth / Monet | 4.609555 | 2.063218 | 2.546337 | 44.8% | .082140 |
| OAuth / Cézanne | 7.699644 | 1.476007 | 6.223637 | 19.2% | .200762 |

The correction removes a substantial part of the naive residual. All 60 sensitivity-cell corrected residual means remain positive, but 10 of 240 fold estimates are negative. In the six primary cells, 23 of 24 fold estimates are positive; the negative fold is NB2/Monet, whose fold range is [−.462984, 5.113138]. Negative scene contributions occur in every primary cell, with counts 5, 5, 5, 3, 1 and 1 out of 24, respectively. These negative estimates are correctly retained.

The last column is only a normalization by coordinate count to help interpret the displayed magnitude. For example, 3.285979 is a sum over 31 coordinates, corresponding to .105999 mean squared standardized difference per coordinate. Neither this conversion nor positivity supplies a significance threshold, calibrated equivalence margin or perceptual effect size. A square root of a corrected estimate would also be a nonlinear display transformation, not an unbiased RMS estimator.

Under the declared assumptions, each fold's residual estimates mismatch of conditional scene means given that fold's fitted map. Training sets overlap, so fold estimates remain dependent. Conditional independence given all fitted maps is not implied. The correction does not test full conditional-distribution equality, and positive observed estimates cannot be presented as a statistically significant rejection without new justified inference.

## Corrected variance and weighting

All stored corrected variance aggregates agreed with the independently evaluated pairwise formulas. None of the 240 corrected-between estimates across 60 cells × two arms × two weighting schemes was negative, although the implementation and tests correctly allow negatives.

The equal-scene ratios reproduce the earlier reviewer feasibility calculation. FLUX/Monet has corrected-between named/free **.332533**, repeat-noise named/free **.354951**, and relative scalar signal/noise **.936843**, while its predecessor scene retrieval improves. Under reference-content weights the relative signal/noise is instead **1.106592**. Thus the statement that scalar signal/noise decreases alongside improved retrieval requires the equal-scene weighting that matches retrieval.

Likewise, OAuth/Cézanne's repeat-noise ratio is **1.139095** under reference-content weights and **.979599** under equal scenes. These are consistent answers to different weighted questions. The manuscript should not combine the former within-scene increase with the latter retrieval weighting without explicitly identifying the change of target.

## Guidance for manuscript integration

1. State the result as improvement relative to the **specified generated-moment shift/scale benchmark**, not proof that no global location/scale map could explain proximity. This map was not optimized against the references, and pure shift is a stronger proximity benchmark in several cells.
2. Give the pure-shift temporal result and its Monet sensitivity alongside the uniform mean shift/scale direction. The termwise calculation shows how extra contraction can hurt proximity without alleging an internal generation mechanism.
3. Show naive and corrected conditional residual magnitudes together, label the 31-coordinate sum and keep negative fold/scene estimates visible in the retained record. Do not treat a positive mean as a significance result.
4. Report corrected variance with its weighting, preserving the equal-scene connection to retrieval and the different reference-content target.
5. Keep these post-result calculations separate from the original conditional randomization tests and the prospective temporal endpoints. No rewording should turn a descriptive benchmark comparison into new confirmatory evidence.

The frozen results support a useful, more specific account of the original patterns while preserving meaningful limits. This is a results audit, not a new peer-review score or a claim of independent empirical replication.
