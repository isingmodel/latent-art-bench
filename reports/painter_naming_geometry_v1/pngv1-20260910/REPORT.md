# Global moment account of painter naming

Post-result, fixed-panel descriptive analysis. No new images, tests or intervals.
Negative residual energy favors actual named outputs; positive favors the fitted benchmark. Near zero is not equivalence. Fold energies are not the original 72-query energies. All folds and deletion sensitivities are retained in analysis.json.

## Held-scene primary metric

| Service / painter | Free | Shift | Shift/scale | Named | Named−shift/scale | Four fold residuals | Delete-one range |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| NB2 / Monet | 4.872039 | 4.127115 | 4.118207 | 3.759370 | -0.358837 | 0.2396, -0.7567, -1.5591, 0.6409 | [-0.559144, -0.180429] |
| NB2 / Cézanne | 5.148301 | 3.276539 | 3.411656 | 3.192150 | -0.219507 | 0.2619, -0.9713, -0.4463, 0.2777 | [-0.375651, -0.138349] |
| FLUX / Monet | 2.627100 | 1.899303 | 1.961784 | 1.649921 | -0.311862 | -0.2257, -0.6571, -0.0957, -0.2690 | [-0.641650, -0.079851] |
| FLUX / Cézanne | 2.143972 | 1.219304 | 1.246285 | 1.054765 | -0.191520 | -0.3655, -0.2826, 0.0746, -0.1925 | [-0.274740, -0.142175] |
| OAuth / Monet | 3.185042 | 2.793911 | 2.868001 | 2.738701 | -0.129299 | -0.3913, -0.3113, -0.0526, 0.2380 | [-0.246532, -0.043243] |
| OAuth / Cézanne | 2.312155 | 2.121558 | 2.215722 | 2.189301 | -0.026421 | -0.1818, -0.1995, -0.3698, 0.6454 | [-0.121696, 0.055520] |

## Original-map transfer to later FLUX

| Painter | Free | Shift | Shift/scale | Named | Named−shift/scale | Delete-one range |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Monet | 2.265630 | 1.470401 | 1.900722 | 1.570522 | -0.330200 | [-0.430323, -0.222457] |
| Cézanne | 1.772275 | 0.736045 | 0.992087 | 0.820251 | -0.171835 | [-0.219638, -0.136015] |

## Repeat-corrected conditional geometry

B* is corrected fixed-scene variance; N* is unbiased repeat-noise trace. These estimates require independent, stable repeat errors. Negative estimates are retained. Ratios below are named/free; residual means are absolute IQR² units.

| Cell | Weighting | B* ratio | N* ratio | (B*/N*) ratio | Corrected held-scene residual, shift/scale |
| --- | --- | ---: | ---: | ---: | ---: |
| NB2 / Monet | reference_content | 0.677314 | 0.749157 | 0.904101 | 2.544769 |
| NB2 / Monet | equal_scene | 0.719015 | 0.814568 | 0.882694 | not evaluated |
| NB2 / Cézanne | reference_content | 0.316293 | 0.785999 | 0.402409 | 2.794303 |
| NB2 / Cézanne | equal_scene | 0.360379 | 0.755123 | 0.477246 | not evaluated |
| FLUX / Monet | reference_content | 0.341689 | 0.308776 | 1.106592 | 3.285979 |
| FLUX / Monet | equal_scene | 0.332533 | 0.354951 | 0.936843 | not evaluated |
| FLUX / Cézanne | reference_content | 0.443331 | 0.488603 | 0.907344 | 2.063341 |
| FLUX / Cézanne | equal_scene | 0.447541 | 0.534960 | 0.836587 | not evaluated |
| OAuth / Monet | reference_content | 0.487502 | 0.869789 | 0.560483 | 2.546337 |
| OAuth / Monet | equal_scene | 0.491716 | 0.838003 | 0.586771 | not evaluated |
| OAuth / Cézanne | reference_content | 0.543718 | 1.139095 | 0.477325 | 6.223637 |
| OAuth / Cézanne | equal_scene | 0.514448 | 0.979599 | 0.525162 | not evaluated |

## Fixed-reference ball occupancy

Same complete reference anchors and k=3 for all maps. Equal-class query counts are 18 within a held-scene fold and 24 in the later cohort. This differs from the predecessor matched-real coverage design and has no real/real calibration.

| Cohort / cell | Free | Shift | Shift/scale | Named |
| --- | ---: | ---: | ---: | ---: |
| original / NB2 / Monet | 0.177632 | 0.250000 | 0.282895 | 0.361842 |
| original / NB2 / Cézanne | 0.085938 | 0.218750 | 0.265625 | 0.226562 |
| original / FLUX / Monet | 0.355263 | 0.342105 | 0.473684 | 0.559211 |
| original / FLUX / Cézanne | 0.312500 | 0.468750 | 0.617188 | 0.601562 |
| original / OAuth / Monet | 0.355263 | 0.355263 | 0.427632 | 0.315789 |
| original / OAuth / Cézanne | 0.242188 | 0.320312 | 0.343750 | 0.406250 |
| transfer / FLUX / Monet | 0.473684 | 0.552632 | 0.605263 | 0.526316 |
| transfer / FLUX / Cézanne | 0.375000 | 0.625000 | 0.750000 | 0.718750 |

## Complete metric and processing sensitivity

No direction count is a hypothesis test. No views are selected for success.

| Cohort | Pipeline | View | Service | Painter | Named−shift/scale |
| --- | --- | --- | --- | --- | ---: |
| original | common_square | all31 | NB2 | Monet | -0.357785 |
| original | common_square | all31 | NB2 | Cézanne | -0.216930 |
| original | common_square | all31 | FLUX | Monet | -0.313167 |
| original | common_square | all31 | FLUX | Cézanne | -0.186085 |
| original | common_square | all31 | OAuth | Monet | -0.163233 |
| original | common_square | all31 | OAuth | Cézanne | -0.025778 |
| original | jpeg90_512 | all31 | NB2 | Monet | -0.372154 |
| original | jpeg90_512 | all31 | NB2 | Cézanne | -0.270446 |
| original | jpeg90_512 | all31 | FLUX | Monet | -0.313397 |
| original | jpeg90_512 | all31 | FLUX | Cézanne | -0.208633 |
| original | jpeg90_512 | all31 | OAuth | Monet | -0.129852 |
| original | jpeg90_512 | all31 | OAuth | Cézanne | -0.017941 |
| original | jpeg90_512 | no_lbp8 | NB2 | Monet | -0.365582 |
| original | jpeg90_512 | no_lbp8 | NB2 | Cézanne | -0.214067 |
| original | jpeg90_512 | no_lbp8 | FLUX | Monet | -0.322384 |
| original | jpeg90_512 | no_lbp8 | FLUX | Cézanne | -0.206309 |
| original | jpeg90_512 | no_lbp8 | OAuth | Monet | -0.138342 |
| original | jpeg90_512 | no_lbp8 | OAuth | Cézanne | -0.025179 |
| original | jpeg90_512 | nontexture19 | NB2 | Monet | -0.256668 |
| original | jpeg90_512 | nontexture19 | NB2 | Cézanne | -0.157857 |
| original | jpeg90_512 | nontexture19 | FLUX | Monet | -0.312871 |
| original | jpeg90_512 | nontexture19 | FLUX | Cézanne | -0.166752 |
| original | jpeg90_512 | nontexture19 | OAuth | Monet | -0.103569 |
| original | jpeg90_512 | nontexture19 | OAuth | Cézanne | -0.070035 |
| original | primary512 | all31 | NB2 | Monet | -0.358837 |
| original | primary512 | all31 | NB2 | Cézanne | -0.219507 |
| original | primary512 | all31 | FLUX | Monet | -0.311862 |
| original | primary512 | all31 | FLUX | Cézanne | -0.191520 |
| original | primary512 | all31 | OAuth | Monet | -0.129299 |
| original | primary512 | all31 | OAuth | Cézanne | -0.026421 |
| original | primary512 | no_lbp8 | NB2 | Monet | -0.358284 |
| original | primary512 | no_lbp8 | NB2 | Cézanne | -0.209038 |
| original | primary512 | no_lbp8 | FLUX | Monet | -0.327687 |
| original | primary512 | no_lbp8 | FLUX | Cézanne | -0.194600 |
| original | primary512 | no_lbp8 | OAuth | Monet | -0.135542 |
| original | primary512 | no_lbp8 | OAuth | Cézanne | -0.032861 |
| original | primary512 | nontexture19 | NB2 | Monet | -0.248416 |
| original | primary512 | nontexture19 | NB2 | Cézanne | -0.148760 |
| original | primary512 | nontexture19 | FLUX | Monet | -0.321996 |
| original | primary512 | nontexture19 | FLUX | Cézanne | -0.157072 |
| original | primary512 | nontexture19 | OAuth | Monet | -0.100599 |
| original | primary512 | nontexture19 | OAuth | Cézanne | -0.078621 |
| original | resolution256 | all31 | NB2 | Monet | -0.397936 |
| original | resolution256 | all31 | NB2 | Cézanne | -0.292836 |
| original | resolution256 | all31 | FLUX | Monet | -0.239619 |
| original | resolution256 | all31 | FLUX | Cézanne | -0.209685 |
| original | resolution256 | all31 | OAuth | Monet | -0.085156 |
| original | resolution256 | all31 | OAuth | Cézanne | -0.077023 |
| original | resolution256 | no_lbp8 | NB2 | Monet | -0.373769 |
| original | resolution256 | no_lbp8 | NB2 | Cézanne | -0.206976 |
| original | resolution256 | no_lbp8 | FLUX | Monet | -0.224174 |
| original | resolution256 | no_lbp8 | FLUX | Cézanne | -0.210890 |
| original | resolution256 | no_lbp8 | OAuth | Monet | -0.087113 |
| original | resolution256 | no_lbp8 | OAuth | Cézanne | -0.081131 |
| original | resolution256 | nontexture19 | NB2 | Monet | -0.244453 |
| original | resolution256 | nontexture19 | NB2 | Cézanne | -0.156523 |
| original | resolution256 | nontexture19 | FLUX | Monet | -0.232156 |
| original | resolution256 | nontexture19 | FLUX | Cézanne | -0.200745 |
| original | resolution256 | nontexture19 | OAuth | Monet | -0.073978 |
| original | resolution256 | nontexture19 | OAuth | Cézanne | -0.088815 |
| transfer | jpeg90_512 | all31 | FLUX | Monet | -0.330653 |
| transfer | jpeg90_512 | all31 | FLUX | Cézanne | -0.215535 |
| transfer | jpeg90_512 | no_lbp8 | FLUX | Monet | -0.343897 |
| transfer | jpeg90_512 | no_lbp8 | FLUX | Cézanne | -0.228339 |
| transfer | jpeg90_512 | nontexture19 | FLUX | Monet | -0.258227 |
| transfer | jpeg90_512 | nontexture19 | FLUX | Cézanne | -0.170848 |
| transfer | primary512 | all31 | FLUX | Monet | -0.330200 |
| transfer | primary512 | all31 | FLUX | Cézanne | -0.171835 |
| transfer | primary512 | no_lbp8 | FLUX | Monet | -0.332770 |
| transfer | primary512 | no_lbp8 | FLUX | Cézanne | -0.178505 |
| transfer | primary512 | nontexture19 | FLUX | Monet | -0.244561 |
| transfer | primary512 | nontexture19 | FLUX | Cézanne | -0.120819 |
| transfer | resolution256 | all31 | FLUX | Monet | -0.423929 |
| transfer | resolution256 | all31 | FLUX | Cézanne | -0.207705 |
| transfer | resolution256 | no_lbp8 | FLUX | Monet | -0.423880 |
| transfer | resolution256 | no_lbp8 | FLUX | Cézanne | -0.217244 |
| transfer | resolution256 | nontexture19 | FLUX | Monet | -0.303074 |
| transfer | resolution256 | nontexture19 | FLUX | Cézanne | -0.182988 |

## Interpretation boundary

A map predicts measured proximity, not feasible image edits or internal model mechanisms. Its scalar is fitted from total observed traces, not a latent gain. Conditional residual correction concerns means, not full conditional distributions. The later cohort reuses templates and investigators. Capture differences, artistic judgment and new-scene generalization are not resolved by this analysis.
