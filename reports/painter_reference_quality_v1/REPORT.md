# Reference-quality sensitivity

This retrospective assistant visual audit covers all **649 reference and 221 development reproductions**. It is not a human artist-resemblance study or an independently validated content annotation. The [plan](../../studies/painter_reference_quality_v1/PLAN.md) was recorded before this audit and corrected-vector analysis, after the original findings and reviews were known. No model scores were used to choose crops or labels. Original images, vectors, scaler and primary inferential family remain unchanged.

The numerical consequence is material: FLUX remains the lowest primary-error point estimate after source-region correction, but the Sunburst-minus-FLUX adjusted interval includes zero. The Flare contrast remains separated. GPT Image 2 retains the lowest calibrated point estimate. Corrections qualify the model comparisons while preserving the broader distinction between alignment, magnitude and collection-relative agreement.

## Audit coverage

Every image was inspected in numbered contact sheets; suspicious regions were enlarged and proposed crops were visually checked. Conservative rectangles remove clear external strips, frames or margins while preserving signatures and unfinished support edges. Oblique and nonrectangular frames can leave residual slivers, and uncertain boundaries remain unchanged. Root spot-checks included the two known calibration strips and large frame removals from each painter. These judgments do not standardize illumination, color, sharpening or capture source.

| Painter | Panel | Works | Cropped | Calibration strips | Frame flags | Uncertain boundaries retained | Revised class labels | Unclear content retained |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude_monet | reference | 297 | 41 | 1 | 25 | 14 | 85 | 23 |
| claude_monet | development | 101 | 17 | 0 | 9 | 5 | 0 | 0 |
| alfred_sisley | reference | 106 | 23 | 4 | 14 | 9 | 32 | 3 |
| alfred_sisley | development | 36 | 7 | 0 | 4 | 3 | 0 | 0 |
| camille_pissarro | reference | 141 | 13 | 2 | 6 | 6 | 72 | 10 |
| camille_pissarro | development | 48 | 11 | 2 | 2 | 1 | 0 | 0 |
| paul_cezanne | reference | 105 | 13 | 1 | 9 | 3 | 41 | 6 |
| paul_cezanne | development | 36 | 6 | 0 | 5 | 2 | 0 | 0 |

In total, **90 reference and 41 development images** were cropped. Ten images contain calibration strips (eight reference, two development). **43 uncertain regions** were left unchanged; uncertainty flags must not be counted as 43 confirmed contaminants. Removed areas range from 1.8% to 66.3% for the cropped images, including large photographic frames.

Visual reference classes were assigned before comparison with the original title-derived classes. There are **230 confident visual/title disagreements**; **42 mixed or unclear cases** retain their original labels. These are alternative coarse assistant assignments, not 230 independently verified factual metadata errors. The known Cézanne street image demonstrates an obvious water-class mismatch; other disagreements can depend on which element organizes a mixed composition. Development classes do not affect scaling.

## Separate region and scaler effects

| Model | Original beta | Original D | Regions, original scaler D | Regions, refitted scaler beta | Regions, refitted scaler D | Regions, refitted scaler calibrated D |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 1 | 0.938 | 1.572 | 1.561 | 0.851 | 1.631 | 0.693 |
| GPT Image 2 | 0.999 | 1.226 | 1.171 | 0.962 | 1.259 | 0.579 |
| GPT Image 2.5 Flare | 0.772 | 1.738 | 1.680 | 0.727 | 1.737 | 0.760 |
| GPT Image 2.5 Sunburst | 0.824 | 1.641 | 1.536 | 0.795 | 1.577 | 0.711 |
| Nano Banana 2 | 0.442 | 1.109 | 1.076 | 0.426 | 1.121 | 0.846 |
| FLUX.2 Max | 0.470 | 0.801 | 0.832 | 0.422 | 0.872 | 0.762 |

Original reference magnitude H is 5.915007; region correction gives 6.297649 with original scaling and 6.299393 with refitted development scaling. Under original scaling, the corrected target cosine with the original is 0.989684, and normalized squared displacement is 0.022303. Development scale ratios range from 0.776 to 1.071. All generated measurements are unchanged; they are transformed consistently into the revised coordinates.

Each view uses its own normalizer. Changes in D under refitted scaling include a changed metric; their magnitudes are not directly interchangeable artistic units. Original data passed through the new implementation reproduce the original summaries exactly.

## All model contrasts after regions and refitted scaling

The same paired-scene Student/Bonferroni-21 calculation is displayed for sensitivity only, without redefining the primary family or promoting new retrospective rejections. In particular, the new GPT Image 1–FLUX interval is not a new confirmatory finding. The original Sunburst result is no longer separated under either correction view.

| Model A minus model B | Difference | Adjusted interval |
| --- | ---: | --- |
| GPT Image 1 − GPT Image 2 | 0.372 | [-0.352, 1.096] |
| GPT Image 1 − GPT Image 2.5 Flare | -0.106 | [-0.818, 0.606] |
| GPT Image 1 − GPT Image 2.5 Sunburst | 0.053 | [-0.905, 1.011] |
| GPT Image 1 − Nano Banana 2 | 0.510 | [-0.439, 1.459] |
| GPT Image 1 − FLUX.2 Max | 0.758 | [0.026, 1.491] |
| GPT Image 2 − GPT Image 2.5 Flare | -0.478 | [-1.144, 0.188] |
| GPT Image 2 − GPT Image 2.5 Sunburst | -0.319 | [-1.063, 0.425] |
| GPT Image 2 − Nano Banana 2 | 0.138 | [-0.964, 1.240] |
| GPT Image 2 − FLUX.2 Max | 0.386 | [-0.136, 0.908] |
| GPT Image 2.5 Flare − GPT Image 2.5 Sunburst | 0.159 | [-0.208, 0.527] |
| GPT Image 2.5 Flare − Nano Banana 2 | 0.616 | [-0.292, 1.523] |
| GPT Image 2.5 Flare − FLUX.2 Max | 0.864 | [0.193, 1.535] |
| GPT Image 2.5 Sunburst − Nano Banana 2 | 0.456 | [-0.527, 1.440] |
| GPT Image 2.5 Sunburst − FLUX.2 Max | 0.705 | [-0.026, 1.436] |
| Nano Banana 2 − FLUX.2 Max | 0.249 | [-0.917, 1.414] |

## Artist-pair alignment with regions and refitted scaling

| Model | Monet–Sisley | Monet–Pissarro | Monet–Cézanne | Sisley–Pissarro | Sisley–Cézanne | Pissarro–Cézanne |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 1 | -0.053 | 0.365 | 0.938 | 0.661 | 0.813 | 1.356 |
| GPT Image 2 | 0.457 | 0.641 | 0.848 | 0.998 | 1.209 | 1.142 |
| GPT Image 2.5 Flare | 0.019 | 0.263 | 0.606 | 0.434 | 1.143 | 0.983 |
| GPT Image 2.5 Sunburst | -0.146 | 0.386 | 0.644 | 0.821 | 1.121 | 1.122 |
| Nano Banana 2 | -0.060 | 0.431 | 0.289 | 0.415 | 0.600 | 0.561 |
| FLUX.2 Max | 0.019 | -0.026 | 0.586 | 0.193 | 0.491 | 0.588 |

Pair slopes remain descriptive; sign changes near zero show why a label-swap diagnostic must not be treated as an established perceptual failure. All six aggregate slope intervals remain above zero in both source-correction views. FLUX nominal absolute D intervals still include the no-contrast benchmark of one.

## Content-label sensitivity on the same 11 briefs

| Model | Original/title | Original/visual | Regions/title | Regions + refit/title | Regions + refit/visual |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPT Image 1 | 1.366 | 1.398 | 1.370 | 1.416 | 1.448 |
| GPT Image 2 | 1.130 | 1.191 | 1.084 | 1.147 | 1.212 |
| GPT Image 2.5 Flare | 1.539 | 1.519 | 1.507 | 1.550 | 1.516 |
| GPT Image 2.5 Sunburst | 1.525 | 1.560 | 1.418 | 1.448 | 1.505 |
| Nano Banana 2 | 0.948 | 1.011 | 0.917 | 0.958 | 1.020 |
| FLUX.2 Max | 0.786 | 0.815 | 0.800 | 0.819 | 0.845 |

The unchanged 11 water/built/land scenes isolate label changes from scene-subset changes. Targets remain coarse, unmatched historical compositions and each has its own H. Original/title → original/visual isolates labeling with unchanged pixels; regions+refit/title → regions+refit/visual isolates labeling with corrected inputs. FLUX has the lowest point estimate in every column. All counts, target magnitudes and model summaries are in the numerical record.

## Evidence and replay

- [Monet audit](audit_monet.json) and [other painters](audit_others.json): all 870 source identities, raw hashes, crop coordinates, flags, visual labels, reasons and inspection-sheet references.
- [Region measurements](measurements.json): original-vector reuse for unchanged works, new normalized-pixel hashes and 31 features for crops.
- [Complete analysis](analysis.json): inputs, corrected scaler, prevalence, all pair contrasts, all calibration folds and all target variants.
- [Implementation](../../src/latent_art_bench/painter_reference_quality_v1.py): create-once measurement/result writers and exact replay.

```bash
make reference-quality-check
make reference-quality-images-check  # Requires retained raw pixels; re-extracts 131 crops
uv run --locked pytest -q tests/painter_reference_quality_v1
```

The image check verifies all 870 raw hashes and exact crop-feature replay. The numerical check needs compact vectors and manifests, not pixels. Public exact-pixel access is still incomplete; local inspection and replay do not constitute a public archive or independent acquisition. No original file is overwritten by these commands.
