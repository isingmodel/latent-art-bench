# Chromatic-distance and seamlessness implementation

## Frozen source definition

The source is Lee et al. (2018), [“Heterogeneity in chromatic distance in images and characterization of massive painting data set”](https://doi.org/10.1371/journal.pone.0204430).

For an sRGB image, the implementation converts every pixel to CIE 1976 L\*a\*b\* under the D65 white point. It then computes Euclidean CIELab distance (Delta E 1976) for every horizontal and vertical adjacent-pixel pair. Diagonal and wraparound pairs are excluded. For an image of width `W` and height `H`, the distance sample therefore has

```text
H * (W - 1) + (H - 1) * W
```

values.

Let `d_bar` be the arithmetic mean of those distances and `sigma_d` their population standard deviation (`ddof=0`). The paper's scale-free distribution uses `d / d_bar`. Its seamlessness statistic is

```text
S = (sigma_d / d_bar - 1) / (sigma_d / d_bar + 1)
  = (sigma_d - d_bar) / (sigma_d + d_bar).
```

Thus a delta-like distribution approaches `-1`, an exponential distribution approaches `0`, and an increasingly heavy-tailed distribution approaches `1`.

## Project decisions

- The color conversion is implemented directly from the standard sRGB transfer curve, D65 sRGB-to-XYZ matrix, and CIELab transform so dependency changes cannot silently alter it.
- The fixed-length distribution vector is a probability histogram of `d / d_bar`. Its frozen lower edges are stored in `configs/pilot_0/pilot.yaml`; the final bin includes all values above the last finite edge.
- Exact zero-distance images make the paper's ratio `0/0`. The project defines this limiting delta case as `S = -1`, coefficient of variation `0`, and an all-zero normalized-distance sample, while marking the feature row `degenerate`.
- Image resolution remains part of the preprocessing condition. Mean normalization and seamlessness are tested for stability; they are not assumed to remove every digitization effect.

The implementation is in `src/latent_art_bench/features/chromatic.py`. Synthetic tests cover solid fields, known sRGB-to-CIELab values, adjacency counts, scale invariance, and the source's delta/exponential/heavy-tail reference behavior. Real-art reproduction and held-out validity remain mandatory before the qualification card can pass.
