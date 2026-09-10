# Geometry successor results audit — Reviewer 2

Date: 10 September 2026. This is a maintainer-run LLM audit, not independent human peer review. After completing my baseline manuscript review, I implemented the pure geometry primitives and their synthetic tests in `painter_naming_geometry_v1`. I subsequently advised on input validation and protocol wording. This implementation involvement limits reviewer independence and must remain disclosed. The verification calculations below were written separately from those primitives, without importing the study's fitting, energy or occupancy functions. No manuscript score is assigned here.

## Scope and identities

I audited the completed `pngv1-20260910` successor, its fixed protocol, assembled numerical inventory, source, complete results and report. The source commit is `459c6a88a10a209ba22619dc38d616588da8817c`; its freeze was committed at `8facfa3`.

- Freeze SHA-256: `54b265f2777f79822057492babb3a26ac491797ec3e45eef35f17315b85a4b5b`.
- Analysis SHA-256: `f50be0f772a3bff8f4bc66ddc20f3e19b5c13736fd6cced632d80224e2203324`.
- Report SHA-256: `31a30614e52a74434e3477f2a193e787640dbac83205c687d68d2bd6478c8cfc`.

This is a results/interpretation audit of a new versioned study. No frozen source, protocol, vectors, results or receipt was edited. No new images, pixel reads, extraction, transport or scientific hypothesis tests were performed. The ongoing manuscript revision and any further successor remain separate from these terminal results.

## Assessment

The numerical implementation and retained inventory support the reported shift/scale comparisons. Actual named outputs have lower average held-scene energy than the fitted shift/scale benchmark in all 60 original views, and lower later-cohort energy than the unchanged original shift/scale map in all 18 transfer views. This is a coherent result across the specified metrics and processing variants.

The stronger interpretation that naming requires more than any simple location/scale account is unsupported. In the later cohort, the unchanged **translation-only** map gives lower primary energy than actual naming for both painters and does so in 15 of 18 views. Moreover, the shift/scale map increases ball occupancy beyond actual naming in the primary later comparison while having worse energy. This gives a useful empirical example of metric disagreement, rather than a universal ordering of coverage.

The transfer failure of the old shift/scale map cannot yet be attributed specifically to its scalar. Its center is the old free mean, so it also changes the later cloud mean differently from the translation-only map. The next centering diagnostic must isolate this distinction before the manuscript identifies radius calibration as the reason for the result.

## Independently checked computation and inventory

I used separate NumPy calculations to reconstruct each training mean, population trace, positive isotropic scalar, evaluation cloud, pairwise Euclidean distance matrix, weighted energy component, third-neighbor radius and ball hit. I checked all 240 original folds and all 18 later comparisons, with their four evaluated clouds.

| Check | Result |
| --- | --- |
| Generated-only fitted moment maps | 258 checked |
| Weighted energy decompositions | 1,032 checked |
| Fixed-anchor occupancies, radii, hit vectors and hit counts | 1,032 checked |
| Largest absolute floating-point difference from saved results | `1.4210854715202004e-14` |
| Scene memberships, class allocations, query counts, hit vectors and hit counts | Exact agreement |
| Original fold aggregation | Four separately evaluated fold energies and occupancies averaged equally; no pooled transformed clouds |
| Canonical exact replay | Passed: 60 original cells and 18 transfer cells |
| Focused namespace tests rerun by this reviewer | 75 passed in 0.74 seconds |

The independently written calculations use broadcasting and explicit weighted sums rather than the study's `cdist`/matrix-multiplication functions. The small differences are consistent with arithmetic evaluation order. This verifies the arithmetic against a separate calculation; it does not validate the representation's perceptual meaning.

I separately checked 280 assembled reference vectors and 3,456 original generated vectors against their raw retained numerical coordinates and the original fixed development scalers. These include the common-square numerical coordinates. The arrays agree exactly after applying the documented center and scale. Released and successor scalers exactly equal the sealed original scaler objects. Centers/scales are finite, 31-dimensional, and all scale entries are positive. The complete 1,076 square baseline `(stage, image_id)` identities are unique and match the original primary inventory, with painter identity agreement. Every bound file's bytes match both its freeze digest and its recorded source commit.

The later input loader preserves the same original scaler, checks measured FLUX rows, exact repetition IDs, and equality of original/later scene and class identities. Both painter comparisons reuse the same later free allocation. Full-space and reduced-coordinate views subset the already standardized coordinates; they do not fit a new evaluator to favorable outcomes. Common-square views exist only for the original cohort, as specified.

## Results that the manuscript should retain

### Original held-scene comparisons

The primary named-minus-shift/scale means are −.358837 and −.219507 for NB2, −.311862 and −.191520 for FLUX, and −.129299 and −.026421 for OAuth, in Monet/Cézanne order. All 60 specified view/pipeline means have this negative sign, ranging from −.397936 to −.017941.

This is a statement about means across four fixed folds, not every held-out subset. Primary NB2/Monet and NB2/Cézanne each have two positive fold residuals; FLUX/Cézanne and both OAuth cells each have one. FLUX/Monet is the only primary cell with all four residuals negative. The delete-one-scene ranges retain a negative mean except OAuth/Cézanne, whose range is [−.121696, .055520]. Neither the count of negative views nor these dependent deletions is a new significance test.

Translation-only is already a stronger benchmark in some original cells. Across 60 original views, actual naming beats translation in 51 and loses in nine. The exceptions are OAuth cells; the primary OAuth/Cézanne mean favors translation by .067743. The revised narrative must preserve this exception rather than collapsing translation and shift/scale into one uniformly defeated benchmark family.

### Later transfer distinguishes translation from the original shift/scale map

| Painter, primary512/all31 | Free energy | Translation energy | Shift/scale energy | Actual named energy | Named minus translation | Named minus shift/scale |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Monet | 2.265630 | 1.470401 | 1.900722 | 1.570522 | +.100121 | −.330200 |
| Cézanne | 1.772275 | .736045 | .992087 | .820251 | +.084206 | −.171835 |

The original translation improves over the later free cloud in **all 18 views**. It beats actual naming in **15/18**: all nine Cézanne views and six Monet views. For Monet, all three `resolution256` views instead favor actual naming, with named-minus-translation residuals −.123106, −.145598 and −.095162 for all31, no_lbp8 and nontexture19. Thus the primary translation ordering survives removal of LBP8 and texture at 512 pixels, but is not invariant to lower resolution for Monet.

The primary translation advantage survives 23/24 later-scene deletions for Monet and 24/24 for Cézanne. Monet's range [−.026011, .215322] includes a reversal; Cézanne's [.036282, .126721] remains positive. In contrast, both primary named-minus-shift/scale deletion ranges remain entirely negative. These are finite-panel stability descriptions.

Shift/scale has worse energy than translation in every one of the 18 transfer views. It still improves over the untransformed free cloud in 15/18 views, while actual naming improves over free in all 18. A safe inference is that the old estimated mean displacement remains useful for reference proximity in these retained views. This is not evidence that the full displacement vector or a latent generation mechanism is temporally stable.

### Fixed-reference occupancy gives an empirical caution, not a universal ranking

The primary later shift/scale map occupies 23/38 Monet reference balls (.605263), compared with 20/38 (.526316) for actual naming. For Cézanne the counts are 24/32 (.750000) and 23/32 (.718750). Nevertheless, shift/scale energy is worse for both. This is a concrete illustration that more occupied reference balls need not imply lower energy or better matching of reference probability mass.

The ordering is not representation-robust: actual-minus-shift/scale occupancy has ten negative values, five positive values and three ties across the 18 transfer views. Actual-minus-translation occupancy has ten positive values, six negative values and two ties. Cite the complete view record and use the primary comparison as the illustrated example. Do not state that contraction necessarily increases occupancy or that naming invariably occupies fewer neighborhoods than a simple map.

The occupancy design itself is implemented correctly: all reference works remain anchors, each radius excludes its own anchor, boundary hits count, and all compared conditions use identical slots/query counts. Each original fold has 18 equal-class queries; the later cohort has 24. Energy uses the reference-content weights whereas occupancy counts those equal-class queries without probability weighting. The new occupancy values are not comparable numerically to the older disjoint-anchor/matched-real figure, and they have no new real/real calibration.

## Central interpretive caveat: anchor movement and radius are entangled in T2

Let `m_F` be the original training-free mean, `m_N` the training-named mean, `delta = m_N - m_F`, `m_E` the evaluation-free mean and `a` the original fitted scalar. The two maps are

```
T1(y) = y + delta
T2(y) = m_N + a (y - m_F).
```

Their evaluation means differ by

```
mean(T2) - mean(T1) = (a - 1) (m_E - m_F).
```

Their centered radii also differ. Therefore the worse energy of T2 relative to T1 is not a clean estimate of the effect of shrinking around a common evaluation mean. The caveat applies to held-out original folds as well as the later cohort, since either evaluation-free mean can differ from its fitted training mean.

The saved primary energy components confirm how the net ordering is formed, without identifying its cause. In later Monet, adding the original T2 operation relative to translation decreases twice the cross-reference distance by 1.942287 but decreases the subtracted within-generated distance by 2.372607, producing an energy increase of .430320. The corresponding Cézanne changes are −1.207264 and −1.463305, producing +.256042. These exact terms explain the arithmetic of the energy change, not whether its cause is the radius, shifted mean or their interaction.

Similarly, actual named outputs have a larger cross-reference term than T2 in both primary later comparisons, but also a sufficiently larger within-generated term to achieve lower energy. That is compatible with excessive concentration by T2, but it is not identification of concentration as the sole explanation. Reference geometry, shifted means and covariance organization can all affect the cross term.

A further post-result successor could compare an evaluation-centered map

```
T2c(y) = m_E + delta + a (y - m_E),
```

using the same training displacement/scalar and only the evaluation-free mean. T2c and T1 have the same evaluation mean; T2c and T2 have the same centered shape and radius, differing only by translation. These two comparisons isolate the algebraic interventions more cleanly. This audit does not execute T2c on the research vectors or report any result for it. Its design must be fixed and source-bound before such computation, and it remains explicitly motivated by already observed v1 results rather than a new unexposed test.

## Recommended manuscript wording and reporting

- Say that actual naming improves on the **specific original moment-matched shift/scale benchmark**, including on the retained later FLUX collection. Do not say that it defeats all simple global maps or that the scalar has been causally isolated.
- Give translation-only equal visual and narrative prominence in the transfer result. Its success changes the scientific conclusion; it is not a minor robustness exception.
- Describe the primary occupancy/energy disagreement as an observed counterexample. Retain the sensitivity reversals and the distinct query/anchor design.
- Identify the cross-fitted energy as a four-fold, 18-query score. Its generated self-distance term omits between-fold comparisons, so it is not an additive decomposition of the original full 72-query energy contrast.
- Keep dependent folds and prescribed deletion ranges descriptive. The frozen protocol correctly explains the local reweighting after deleting a scene and why this is not global equal weighting over the remaining scenes.
- Interpret positive corrected conditional-mean residuals under their repeat-error assumptions; their signs alone are not tests, and they cannot establish equality or inequality of complete conditional distributions. The separate variance primitive audit should address those assumptions in detail.

The present v1 numerical result is sound for its declared diagnostic scope. The required correction is interpretive: separate the specific benchmark result from the broader location/scale claim, and separate the old-origin anchor from scalar calibration. No frozen result needs replacement to make those distinctions.
