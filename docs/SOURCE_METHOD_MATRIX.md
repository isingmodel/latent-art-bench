# Source-Method and Resolution Matrix

## Purpose

Historical-painting datasets and generated-image outputs do not necessarily share the same acquisition process or native resolution. This matrix records how the source studies actually treated image size and identifies the benchmark rule that follows from each method.

The central conclusion is that generated outputs at 512 or 1024 pixels are not automatically too small for this research. Several source methods deliberately reduce images to 400, 500, 512, or 224 pixels. The more important threats are inconsistent observation scale, resampling, aspect-ratio distortion, color management, compression, and heterogeneous digital reproduction.

## Method matrix

| Source method | Corpus and source-image scale | Analysis preprocessing | Resolution assessment | LatentArtBench rule |
|---|---|---|---|---|
| Kim, Son, and Jeong (2014) | 8,798 Web Gallery of Art paintings; more than 94% were reported as larger than 700 × 700 pixels | Color-space statistics used digitized RGB values; brightness roughness used pixel-distance correlations; the local image-entropy analysis resized images to 500 × 500 with Lanczos | Color and roughness measurements can reflect digitization and spatial scale; the paper explicitly notes color-distortion limitations | Reproduce each observable with its source preprocessing. Express spatial distance relative to canvas size in the harmonized track and test a common-resolution pyramid |
| Lee et al. (2018), chromatic distance | 179,853 paintings from multiple web archives; the great majority of images in the principal sources had a long side of at least 500 pixels | Adjacent-pixel CIELab distances define the raw distribution; rescaling by its mean collapses the tested image-size-dependent distributions; seamlessness is derived from a scale-invariant distribution descriptor | Raw adjacent-pixel distance is resolution-dependent, while the normalized distribution was shown to collapse across tested sizes | Retain the source-normalized distribution and seamlessness. Verify collapse on the benchmark corpus and test sensitivity to color conversion, compression, and resampling |
| Seo et al. (2018), color interaction | Three sample paintings; scale is represented through recursive partition depth | Information-theoretic partitioning into quasi-homogeneous regions, regional hue extraction, and comparison with color-harmony templates | Raw partition count and average pixel area do not provide a fully normalized cross-image scale | Replicate the three examples first. For extension, report source partition counts and a harmonized scale based on normalized region area or an equivalent relative measure |
| Sigaki, Perc, and Ribeiro (2018) | 137,364 WikiArt images; typical dimensions were on the order of 900 × 900 pixels with wide variation | RGB channels were averaged to grayscale; two-by-two ordinal patterns produced permutation entropy and statistical complexity | Dataset-level associations with image dimensions were small, but cross-sectional correlation does not replace same-image downsampling tests | Use the original two-by-two construction as the source track and add same-image multiresolution validation before individual-work inference |
| Lee et al. (2020), landscape composition | 14,912 landscape paintings from WikiArt and the Web Gallery of Art | Borders and unsuitable backgrounds were removed; aspect ratio was preserved; the long side was set to 400 pixels; the principal analysis used a painting-specific three-bit RGB representation | The method was reported as minimally affected by image size, and robustness checks used alternative color depth and grayscale representations | Treat long-side 400 pixels with preserved aspect ratio and the source color quantization as the replication baseline. Do not force the method onto non-landscape primary targets |
| Kim, Lee, and Lee (2025) | 149,780 user-generated works; reported mean width and height were approximately 1,012 and 954 pixels | RGB values were averaged to grayscale for two-by-two ordinal patterns; ResNet-18 used its 224 × 224 model input; SIFT retained original image dimensions | Entropy-complexity uses extremely local patterns; ResNet standardizes input size; SIFT remains sensitive to image condition and fine-detail loss | Validate entropy-complexity at multiple scales, use model-native preprocessing for ResNet, and treat SIFT as a secondary condition-sensitive module |
| Tarozo et al. (2025) | The 137,364-work WikiArt corpus used in the earlier entropy-complexity study | Two-by-two ordinal patterns explicitly include ties, yielding a 75-dimensional distribution grouped into 11 interpretable types | A direct downsampling example showed broad stability but changes in tied and fine-detail patterns; the paper identifies heterogeneous resolution and single-scale analysis as limitations | Use the 75-dimensional pattern distribution as a diagnostic extension and require multiscale sensitivity reporting for work-level claims |
| Kim et al. (2026), formal and contextual vectors | 72,447 curated works after size and extreme-aspect-ratio filtering | The formal A-vector pipeline uses a Stable Diffusion 2.0 autoencoder and 512 × 512 images; the contextual C-vector uses a CLIP-family representation. The public code indicates that the two paths do not share identical image-loading and resizing code | Input standardization is model-defined, but forced square resizing can alter composition. Differences between the paper description and executable preprocessing must be versioned | Reproduce the released implementation at a fixed commit. Keep source-faithful A- and C-vector paths distinct, and add independent evaluators plus an aspect-preserving harmonized control |

## Two-track policy

### Source-faithful track

Each method follows the original paper, supplement, and released code as closely as possible. This track asks whether the reported scientific behavior can be functionally reproduced and whether generated images can be inserted into the original measurement system.

### Harmonized multiscale track

Real and generated images pass through the same versioned color, border, aspect-ratio, resampling, and compression workflow. Features are evaluated at supported common scales, using only downsampling in the primary analysis. Features that remain scale-sensitive are represented by response curves or restricted to matched-resolution inference.

## Interpretation rules

1. A difference that appears only in native-file comparison but disappears under harmonized processing is classified as an acquisition or preprocessing effect.
2. A difference that survives the source-faithful and harmonized tracks is stronger evidence of a model-related gap.
3. A generated image is not penalized for lacking detail that the source method deliberately removes before analysis.
4. Upsampling cannot restore absent detail and is not used to claim resolution equivalence.
5. Forced square inputs are acceptable for reproducing a model-defined embedding, but they do not replace aspect-preserving composition analysis.
6. Digital-reproduction variation establishes a feature-specific noise floor below which artistic interpretation is unresolved.

## Primary sources

- [Large-Scale Quantitative Analysis of Painting Arts](https://doi.org/10.1038/srep07370)
- [Heterogeneity in chromatic distance in images and characterization of massive painting data set](https://doi.org/10.1371/journal.pone.0204430)
- [Information-Theoretic Analysis of Color Interaction in Artistic Paintings](https://doi.org/10.3938/NPSM.68.693)
- [History of art paintings through the lens of entropy and complexity](https://doi.org/10.1073/pnas.1800083115)
- [Dissecting landscape art history with information theory](https://doi.org/10.1073/pnas.2011927117)
- [Investigating the diversity and stylization of contemporary user generated visual arts in the complexity entropy plane](https://doi.org/10.1038/s41598-025-04448-9)
- [Two-by-two ordinal patterns in art paintings](https://doi.org/10.1093/pnasnexus/pgaf092)
- [Context-aware multimodal AI navigates hidden pathways in five centuries of art evolution](https://doi.org/10.1073/pnas.2517969123)
