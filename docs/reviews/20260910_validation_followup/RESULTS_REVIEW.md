# Measurement results review — 10 September 2026

Run: `painter_measurement_validation_v1/pmvv1-20260910`. This is a
maintainer-run LLM assessment by reviewer 1, who designed and implemented this
measurement successor. Separate numerical reconstruction provides a useful
implementation cross-check; it is not neutral external validation. This review
reads the frozen protocol/source and compact completed outputs, without reopening
raw pixels or reading new replication outcomes.

## Disposition and verification

The study supplies genuine new computational evidence: controlled transformations
of all 70 retained reference works and a complete common-square sensitivity of
the 1,006 Study 1 generated images. It supplies no new reference sample, independent
captures, human judgments or perceptual equivalence test. No numerical defect was
found in the inspected outputs.

The receipt records 1,076 verified raw images, 1,706 vectors and zero generation
calls. I checked all 108 frozen input hashes and both output hashes, the feature
ledger chain and complete condition identities. Independent calculations from the
saved vectors reproduced all 30 equal-painter family means and the three paired
bootstrap summaries within 2e-14. Direct weighted-distance matrix calculations
reproduced all eight square energy estimates within 2e-13, with unchanged image
pair identities, weights and missing-pair records. PNG array hashes and all
31-vector values match the baseline exactly for all 70 works. The coordinator's
full numeric replay separately checks the unchanged randomization results;
this review did not duplicate that entire replay.

## Principal computational findings

Displacement is RMS change in the unchanged development-IQR units. The comparator
is the **within-work, within-family maximum** of JPEG 95 and resampling 512→384→512,
not the larger of their aggregate means. Estimates average the Monet and Cézanne
means equally. Intervals resample whole works within painter, preserving the three
paired responses together, with 9,999 draws and seed 2026091002.

| Known change / family | Difference from processing maximum | Nominal 98.3333% interval | Positive works |
| --- | ---: | --- | ---: |
| Chroma ×0.8 / color | 0.157829 | [0.138636, 0.177929] | 69/70 |
| Tile permutation / spatial | 0.304921 | [0.238989, 0.373173] | 67/70 |
| Blur σ=1 / texture | 3.944537 | [3.679809, 4.186611] | 70/70 |

All three fixed known changes exceed their selected processing comparator on
average for both painters. The descriptive bootstrap ranges are wholly positive.
These conditional, exposed-panel intervals use a Bonferroni-three convention;
they do not establish calibrated population coverage, a perceptual pass margin,
universal per-image ordering or artist-style validity.

The full equal-painter mean matrix is essential context:

| Condition | Color | Spatial | Texture |
| --- | ---: | ---: | ---: |
| Baseline and PNG, each | 0 | 0 | 0 |
| JPEG 95 | 0.021979 | 0.026756 | 0.102472 |
| JPEG 75 | 0.027870 | 0.056906 | 0.410243 |
| Resample 384 | 0.061607 | 0.119012 | 1.098994 |
| Chroma ×0.8 | 0.220112 | 0.0000257 | 0.0001646 |
| Chroma ×0.6 | 0.490507 | 0.0000369 | 0.0002401 |
| Blur σ=1 | 0.338423 | 1.059093 | 5.043531 |
| Blur σ=2 | 0.630659 | 4.694227 | 9.391558 |
| Tile permutation | 0.283369 | 0.424258 | 0.164938 |

Processing sensitivity is substantive: resampling causes a mean texture shift
of 1.099 IQR-RMS units, and JPEG 75 causes approximately four times the JPEG 95
texture displacement. JPEG 75 exceeds JPEG 95 in 43/70 color, 63/70 spatial and
68/70 texture responses; this is not universal monotonicity. The favorable
principal comparisons cannot justify calling encoding or resampling irrelevant.

The families are also not isolated constructs. Blur σ=1 moves the spatial family
more than tile permutation, and tile permutation moves the color family more than
Chroma ×0.8. The tile operation preserves the RGB pixel multiset by construction;
the seven marginal-color summaries agree within 2.4e-15, while neighboring-color
distance features legitimately change. Chroma contraction is nearly isolated
from luminance-derived spatial/texture coordinates in this particular operation.

A post-result coordinate diagnostic, computed for this review, finds that
`lbp_entropy_8` accounts for 83.85% of the sum of equal-painter mean squared texture
coordinate displacements under Blur σ=1; corresponding shares are 49.35% under
resampling and 93.19% under Blur σ=2. Its unchanged development IQR is 0.00885458.
This explains much of the large texture RMS. It is not evidence that all twelve
texture coordinates respond comparably, and it supplies no reason to retune the
frozen metric after seeing results.

## Dose and identity checks

Stronger chroma contraction increases color-family displacement in every work:
Chroma ×0.6 minus ×0.8 mean differences are 0.284092 for Monet and 0.256697 for
Cézanne. Blur σ=2 minus σ=1 texture differences are 4.286237 and 4.409817,
also positive in every work. These are family-level dose responses, not a claim
that every coordinate is monotone.

Median-chroma ratios range from 0.7999999999999904 to 0.8000015318204199 for the
0.8 dose, and 0.5999999999999978 to 0.6000018565364256 for the 0.6 dose. At least
one clipped pixel occurs in 18 and 17 works respectively; the largest clipped
pixel fraction is 0.00251007 (0.2510%) for either dose. Thus the signed chroma
check behaves as specified, with small recorded gamut effects. Because this
coordinate directly measures the quantity transformed, it is a calibration of
the computation rather than independent validation of painter recognition.

## Common-square naming sensitivity

All eight estimates remain negative and exactly the same four endpoints reject
under the unchanged Holm family of eight. The first six compare detailed-scene
named with artist-free; the final two compare detailed-scene named with
short-scene named. Both conditions in those final comparisons name the painter.
The stored `generic_named` identifier denotes a shorter scene description in
Study 1, not the generic-style arm used in Study 2.

| Service / painter / comparator | Full-view estimate | Square estimate | Full-view Holm p | Square Holm p |
| --- | ---: | ---: | ---: | ---: |
| Nano Banana / Monet / free | −0.846229 | −0.812671 | 0.00310 | 0.00430 |
| Nano Banana / Cézanne / free | −1.817577 | −1.796933 | 0.00008 | 0.00008 |
| FLUX / Monet / free | −0.624647 | −0.531743 | 0.00008 | 0.00008 |
| FLUX / Cézanne / free | −0.895593 | −0.906167 | 0.00008 | 0.00008 |
| OAuth / Monet / free | −0.233883 | −0.244420 | 0.19308 | 0.17259 |
| OAuth / Cézanne / free | −0.056055 | −0.109987 | 1.00000 | 0.62136 |
| OAuth / Monet / short-scene named | −0.037471 | −0.043214 | 1.00000 | 0.74574 |
| OAuth / Cézanne / short-scene named | −0.272342 | −0.278710 | 0.09280 | 0.10312 |

Pair counts remain 72 except the final comparison, which retains 70. The largest
absolute estimate change is 0.092904 for FLUX/Monet. These results show persistence
under this exact central-window operation, not fresh confirmation.

All FLUX and Nano Banana generated images were already square and have exactly
zero feature displacement: their changed estimates arise solely from the changed
reference views. The reference retained-area min/median/max are
49.47%/74.96%/95.70% for Monet and 52.51%/78.83%/86.78% for Cézanne. OAuth retained
areas are 75.18%/80.00%/100% and 79.26%/80.00%/100%, respectively. The operation
equalizes raster shape but removes unequal amounts of composition. It cannot
separate aspect ratio, visible subject matter, capture workflow or artistic style.

Presentation caveat: the now-frozen report figure labels the final comparisons
`named − generic`, an ambiguous shorthand that can be mistaken for the Study 2
generic-style contrast. The scientific input and numeric contrast are correct;
the manuscript should spell out **detailed-scene named minus short-scene named**
in its own table/caption. Preserve the frozen figure and record the clarification
rather than overwriting its source or output.

## Implications for the manuscript

The paper can claim that the fixed feature families respond more strongly, on
average, to these selected known changes than to the selected processing
comparison, with ordered stronger-dose responses on the exposed reference panel.
It can also claim that the original controlled naming pattern persists when all
images are measured through a common central square. It should retain the full
matrix, processing sensitivity, unequal cropping and conditional interval scope.
Calling the study a computational calibration/challenge is justified; calling it
perceptual, independent-capture or general painter-style validation is not.

No frozen-output correction is requested. Generalization beyond these images and
operations still requires new evidence, not more sensitivity labels. The separate
temporal replication and public numerical release answer different questions and
must be reported on their own results and access status.

## Exact reviewed identities

Source commit: `f3bc9b61cc142c79a90c521696fad5bcc578f990`.

```text
e739d0e415d21ae8df0d07a0a48ada513ceb9eeaebbaf6e997e50d832329a924  studies/painter_measurement_validation_v1/PROTOCOL.md
41d740512975e53a6ce030fad3cdb17222d793ee5eed0bab4f7fae280949ad06  src/latent_art_bench/painter_measurement_validation_v1/statistics.py
74037960ef2ef68ba44948e9c7d063311fcec193939f63d7d613f5adf3ffb13a  src/latent_art_bench/painter_measurement_validation_v1/transforms.py
4e800704b9e421f9a775d98a81d15ee03e7e9e0022cbdaf6cf4c9fda330a99a0  src/latent_art_bench/painter_measurement_validation_v1/pipeline.py
75cbaff834eb9428efcaddcd40662f4b5dcb19e137f9befcf366df2a82a303e7  data/manifests/painter_measurement_validation_v1/pmvv1-20260910/freeze.json
71d911bc5344fc5ab532e9ef4625f5eadd5e86284266b054fb01bfe5e4393f88  data/manifests/painter_measurement_validation_v1/pmvv1-20260910/analysis.json
bee5f002765dbf5f4ad43031ca46c76be5ca2d836c4e5b477d8ff9f1d5afe697  data/manifests/painter_measurement_validation_v1/pmvv1-20260910/features.jsonl
6ab4f647af5680fd36c749e01694a0c066d584b047e99fc51da73880af268fed  data/manifests/painter_measurement_validation_v1/pmvv1-20260910/run_receipt.json
```
