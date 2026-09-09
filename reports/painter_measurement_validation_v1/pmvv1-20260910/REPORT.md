# Computational measurement validation

This successor measures ten fixed conditions on all 70 previously exposed reference works and a common central square on all 1,006 retained Study 1 generated images. There are 1,706 unique feature vectors; the 70 reference-square vectors are reused. No new images were collected and no human ratings were obtained.

The unchanged full-view eight-endpoint inference replays exactly. Square-window results are post-result sensitivities and preserve the original pairing, missingness, weights, randomization seeds and Holm family. They do not replace the original primary results.

## Known-change versus processing challenges

Positive differences indicate that the fixed known change displaced the specified feature family more than the per-work maximum of JPEG 95 and resampling. Neither processing operation is assumed perceptually irrelevant. Intervals are descriptive whole-work bootstrap summaries conditional on the exposed panel, with nominal 98.3333% per comparison (Bonferroni-three adjustment); population coverage is unqualified.

| Family | Equal-painter mean difference | Descriptive interval |
| --- | ---: | --- |
| color | 0.157829 | [0.138636, 0.177929] |
| spatial | 0.304921 | [0.238989, 0.373173] |
| texture | 3.944537 | [3.679809, 4.186611] |

![All-family displacement matrix](challenge_matrix.png)

The matrix retains cross-family responses: tile boundaries can change neighboring-color measurements despite exact preservation of the pixel multiset. Chroma contraction partially tests its own measurement definition; signed chroma responses and gamut clipping are retained per work. No all-feature monotonicity requirement or perceptual pass margin is imposed.

## Common central field of view

![Eight geometry contrasts](geometry_contrasts.png)

The central square is cropped after the unchanged 512-pixel short-side normalization, without a second normalization or anisotropic warp. Cropping changes visible content and does not isolate photographic capture. The square-condition p-values are sensitivity outputs, not new confirmation.

All 31 feature coordinates, normalization/window metadata, work-level processing contrasts, signed chroma responses, and per-image geometry shifts are in the bound feature/analysis records. The scaler is unchanged. These results cannot establish painter-style, physical-brushwork or independent-capture equivalence.

| Source | Painter | Images | Retained area: min / median / max |
| --- | --- | ---: | --- |
| FLUX | Monet | 144 | 100.0% / 100.0% / 100.0% |
| FLUX | Cézanne | 144 | 100.0% / 100.0% / 100.0% |
| Nano Banana 2 | Monet | 144 | 100.0% / 100.0% / 100.0% |
| Nano Banana 2 | Cézanne | 144 | 100.0% / 100.0% / 100.0% |
| OAuth | Monet | 216 | 75.2% / 80.0% / 100.0% |
| OAuth | Cézanne | 214 | 79.3% / 80.0% / 100.0% |
| Reference | Monet | 38 | 49.5% / 75.0% / 95.7% |
| Reference | Cézanne | 32 | 52.5% / 78.8% / 86.8% |
