# Available image-generation services: empirical painter-feature analysis

Analysis report, not a manuscript. Recorded 2026-09-05. Method: `pfg2-method-20260905`.

## Outcome and interpretation

The fixed frame contains 1,193 works: 1,185 acquired, 1,180 successfully measured, and 649 in the finite reference. Complete measured comparisons are available for gpt-image-1, gpt-image-2, sd-turbo.

**Painter-feature reproduction is not demonstrated.** The analysis measures discrepancy and painter-name/control contrasts, not equivalence. Independent-capture calibration and justified equivalence margins remain unavailable. The coverage check prevents treating nominal 95% intervals as validated confidence guarantees.


| Requested service / baseline | Images per condition | Negative named-minus-control contrasts | Color / spatial / texture breakdown | Own target closer than all three others |
| --- | --- | --- | --- | --- |
| gpt-image-1 | 16 | 7/12 | 4/4, 1/4, 2/4 | 8/12 |
| gpt-image-2 | 16 | 7/12 | 3/4, 2/4, 2/4 | 9/12 |
| sd-turbo | 400 | 10/12 | 3/4, 4/4, 3/4 | 4/12 |

These are descriptive sign counts, not significance tests or a ranking. Each denominator is four painters × three families. Unequal generated sample sizes affect the finite V-statistic; the OAuth aliases have one repetition and unverified underlying snapshots.

Benefit over an artist-free control and painter specificity answer different questions. More favorable control contrasts may reflect a weaker artist-free baseline, not better absolute named-painter fit. Improvement over control does not mean the named painter is closer than every wrong painter, and neither property demonstrates equivalence.

## Registered experiment and observed service behavior

SD-Turbo uses checkpoint `b261bac6fd2cf515557d5d0707481eafa0485ec2`, local FP16 MPS, 512×512, one step, guidance 0, and 25 paired seed blocks. The OAuth pilot requests `gpt-image-1` and `gpt-image-2` through the dated local Codex OAuth proxy: all 16 exact templates × five conditions × one repetition per alias. It supplies no seed. No aesthetic selection, rerolls, or paid API fallback were used.


| Alias | Terminal outcomes | Decoded sizes | Reported quality | Reported model |
| --- | --- | --- | --- | --- |
| gpt-image-1 | {'generated': 80} | 19 sizes; mode 1402×1122 (29/80); landscape 80/80 | {'low': 80} | {'None': 80} |
| gpt-image-2 | {'generated': 80} | 16 sizes; mode 1402×1122 (25/80); landscape 79/80 | {'low': 80} | {'None': 80} |
| sd-turbo | {'generated': 2000} | 1 sizes; mode 512×512 (2000/2000); landscape 0/2000 | {'None': 2000} | {'None': 2000} |

OAuth requests asked for 1024×1024 / medium / PNG. Actual returned geometry and quality are retained separately; normalization does not retroactively satisfy those requested controls. `None` means no model identifier was returned, not a verified shared model. SD-Turbo has a local checkpoint contract rather than response-reported settings. Latency and every requested/returned mismatch are in the numeric result.

Preserving native aspect ratio means the square SD-Turbo canvases and the OAuth service's returned shapes are not geometry-matched. Common short-side normalization does not remove this spatial/texture confound. The earlier neutral access probe's 1254×1254 outputs are separate evidence, not the sizes of this painter grid.

For real paintings, the reported native dimensions describe the acquired Commons rendering, not necessarily the original full-resolution photograph or physical canvas.

## Corpus, attrition and measurement

The real frame is Wikidata-declared outdoor-place paintings, not institutionally verified attribution or a probability sample of a painter's oeuvre. Works retain their fixed roles after losses. Historical exposure matching placed 91 records in development-only; 14 denylist records lacked crosswalk identifiers; absence of leakage is unproved.


| Painter | Role | Frame | Acquired | Measured |
| --- | --- | --- | --- | --- |
| Monet | development | 102 | 101 | 101 |
| Monet | historical_development | 31 | 31 | 31 |
| Monet | qualification | 102 | 100 | 100 |
| Monet | confirmation | 303 | 299 | 297 |
| Sisley | development | 36 | 36 | 36 |
| Sisley | historical_development | 17 | 17 | 17 |
| Sisley | qualification | 36 | 36 | 36 |
| Sisley | confirmation | 107 | 106 | 106 |
| Pissarro | development | 48 | 48 | 48 |
| Pissarro | historical_development | 21 | 21 | 21 |
| Pissarro | qualification | 48 | 48 | 48 |
| Pissarro | confirmation | 142 | 142 | 141 |
| Cézanne | development | 36 | 36 | 36 |
| Cézanne | historical_development | 22 | 22 | 22 |
| Cézanne | qualification | 36 | 36 | 35 |
| Cézanne | confirmation | 106 | 106 | 105 |

Acquisition failures: Monet / development: {'unsupported_format': 1}; Monet / qualification: {'short_side_below_1024': 2}; Monet / confirmation: {'short_side_below_1024': 4}; Sisley / confirmation: {'unsupported_format': 1}.

Measurement failures: Monet / confirmation: {'unprofiled non-RGB color space': 2}; Pissarro / confirmation: {'unprofiled non-RGB color space': 1}; Cézanne / qualification: {'unprofiled non-RGB color space': 1}; Cézanne / confirmation: {'nonopaque alpha is not a painting area': 1}.

All real images come from the complete corrected R2 rendering run. Earlier original and first-rendering acquisitions are terminal; their partial successes were not spliced into R2. The correction recognizes Wikimedia's new thumbnail host and actual advertised thumbnail sizes; no work was added or threshold lowered. [Wikimedia host migration](https://phabricator.wikimedia.org/T434821); [Imageinfo size behavior](https://www.mediawiki.org/wiki/API:Imageinfo/en).

The shared method fully decodes, applies EXIF, converts valid ICC profiles to sRGB, flags missing profiles as assumed sRGB, preserves aspect ratio, and downsamples without upsampling to short side 512. It measures 11 color, eight spatial/orientation, and 12 digital-texture coordinates. A common equal-painter median/IQR transform is fitted only on new development. Qualification is diagnostic and does not select a method.

Development-to-qualification finite energy distances use the same 512-pixel new-development scaler. These are reference-set diagnostics, not equivalence margins; no pipeline was selected from them.


| Painter | Color | Spatial | Texture |
| --- | --- | --- | --- |
| Monet | 0.0901 | 0.0495 | 0.1588 |
| Sisley | 0.1856 | 0.1552 | 0.1586 |
| Pissarro | 0.1849 | 0.1251 | 0.0963 |
| Cézanne | 0.1571 | 0.2484 | 0.1131 |

## Complete finite comparisons

Energy distance is computed between the finite measured reference and finite generated sets, with both self terms including diagonals (V-statistic). Lower own-target distance means closer measured distributions; negative named-minus-artist-free values favor the named condition. Family distances are not comparable across different dimensions.

### gpt-image-1


| Painter | Family | Own-target distance | Named minus artist-free |
| --- | --- | --- | --- |
| Monet | color | 0.6827 | -0.7905 |
| Monet | spatial | 0.8434 | 0.5204 |
| Monet | texture | 1.5800 | 0.0999 |
| Sisley | color | 0.7927 | -0.5646 |
| Sisley | spatial | 0.8204 | 0.3470 |
| Sisley | texture | 1.1942 | -0.5989 |
| Pissarro | color | 1.1261 | -0.1921 |
| Pissarro | spatial | 0.8721 | 0.0711 |
| Pissarro | texture | 1.2708 | -0.2286 |
| Cézanne | color | 0.6905 | -0.0608 |
| Cézanne | spatial | 0.7155 | -0.1616 |
| Cézanne | texture | 2.2039 | 0.4570 |

Own-target minus each wrong-painter distance; negatives favor own-target fit.


| Named painter | Family | Monet | Sisley | Pissarro | Cézanne |
| --- | --- | --- | --- | --- | --- |
| Monet | color | — | -0.1178 | -0.1899 | -1.1950 |
| Monet | spatial | — | 0.0757 | 0.1119 | -0.7908 |
| Monet | texture | — | 0.2760 | 0.0545 | -0.9019 |
| Sisley | color | -0.0766 | — | -0.1018 | -1.4803 |
| Sisley | spatial | 0.0314 | — | -0.2475 | -0.7892 |
| Sisley | texture | -0.2891 | — | -0.2911 | -1.2791 |
| Pissarro | color | -0.5777 | -0.4575 | — | -1.3068 |
| Pissarro | spatial | -0.1483 | -0.0884 | — | -0.8107 |
| Pissarro | texture | -0.1697 | -0.0591 | — | -1.1035 |
| Cézanne | color | -0.1131 | -0.2662 | -0.3414 | — |
| Cézanne | spatial | -0.3487 | -0.5961 | -0.6468 | — |
| Cézanne | texture | 0.3399 | 0.0275 | -0.2409 | — |

### gpt-image-2


| Painter | Family | Own-target distance | Named minus artist-free |
| --- | --- | --- | --- |
| Monet | color | 0.5468 | -0.7631 |
| Monet | spatial | 0.7872 | 0.4513 |
| Monet | texture | 1.7033 | 0.2325 |
| Sisley | color | 0.7812 | -0.4401 |
| Sisley | spatial | 0.5760 | 0.0676 |
| Sisley | texture | 1.2013 | -0.5059 |
| Pissarro | color | 1.0748 | -0.0993 |
| Pissarro | spatial | 0.6400 | -0.2146 |
| Pissarro | texture | 1.4319 | -0.0048 |
| Cézanne | color | 0.7285 | 0.1072 |
| Cézanne | spatial | 0.7129 | -0.1526 |
| Cézanne | texture | 2.2831 | 0.6954 |

Own-target minus each wrong-painter distance; negatives favor own-target fit.


| Named painter | Family | Monet | Sisley | Pissarro | Cézanne |
| --- | --- | --- | --- | --- | --- |
| Monet | color | — | -0.1516 | -0.2365 | -1.2569 |
| Monet | spatial | — | 0.0308 | 0.0150 | -0.7969 |
| Monet | texture | — | 0.2091 | -0.0215 | -0.9442 |
| Sisley | color | -0.0705 | — | -0.0542 | -1.4709 |
| Sisley | spatial | -0.0110 | — | -0.2255 | -0.8127 |
| Sisley | texture | -0.2336 | — | -0.1946 | -1.3071 |
| Pissarro | color | -0.5301 | -0.4401 | — | -1.3458 |
| Pissarro | spatial | -0.0789 | -0.0548 | — | -0.7204 |
| Pissarro | texture | -0.1397 | -0.0634 | — | -1.1614 |
| Cézanne | color | -0.1266 | -0.2613 | -0.3202 | — |
| Cézanne | spatial | -0.4776 | -0.6575 | -0.5781 | — |
| Cézanne | texture | 0.4672 | 0.0945 | -0.0724 | — |

### sd-turbo


| Painter | Family | Own-target distance | Named minus artist-free |
| --- | --- | --- | --- |
| Monet | color | 0.9016 | -0.3270 |
| Monet | spatial | 0.9749 | -0.7737 |
| Monet | texture | 1.4964 | 0.1759 |
| Sisley | color | 0.8325 | -0.2751 |
| Sisley | spatial | 1.4560 | -0.8675 |
| Sisley | texture | 1.6071 | -0.4102 |
| Pissarro | color | 1.1475 | 0.0566 |
| Pissarro | spatial | 1.4440 | -1.5210 |
| Pissarro | texture | 1.6945 | -0.2412 |
| Cézanne | color | 0.5813 | -0.0553 |
| Cézanne | spatial | 1.1428 | -0.7680 |
| Cézanne | texture | 0.7053 | -0.7419 |

Own-target minus each wrong-painter distance; negatives favor own-target fit.


| Named painter | Family | Monet | Sisley | Pissarro | Cézanne |
| --- | --- | --- | --- | --- | --- |
| Monet | color | — | 0.0164 | 0.2570 | 0.0242 |
| Monet | spatial | — | -0.4295 | -0.8462 | 0.0053 |
| Monet | texture | — | -1.0015 | -0.6890 | -0.7049 |
| Sisley | color | -0.0587 | — | 0.2173 | -0.0481 |
| Sisley | spatial | 0.4384 | — | -0.4100 | 0.4345 |
| Sisley | texture | 0.5952 | — | 0.1588 | 0.2707 |
| Pissarro | color | -0.3504 | -0.2202 | — | 0.3106 |
| Pissarro | spatial | 0.6135 | 0.2493 | — | 0.8275 |
| Pissarro | texture | 0.4708 | -0.1150 | — | 0.2700 |
| Cézanne | color | -1.1753 | -1.1459 | -1.1741 | — |
| Cézanne | spatial | -0.0905 | -0.5653 | -1.0004 | — |
| Cézanne | texture | -1.0110 | -1.0324 | -1.2161 | — |

All 124 coordinate median differences and IQR ratios per available service are retained in [the primary numeric result](../../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/empirical_analysis.json); none is thresholded into a reproduction label.

## Repeated SD-Turbo uncertainty and calibration

The SD-Turbo generator estimator excludes equal repetition blocks in its generated self term; it differs from the finite tables above and may be negative. The 9,999 bootstrap resamples jointly resample whole blocks across all 60 endpoints, conditioning on the finite real reference. Intervals are nominal and exploratory, not validated tests.

Experiment `pfg2-sd-turbo-20260905`: 25 blocks; all 60 intervals are retained in its [numeric result](../../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/experiments/pfg2-sd-turbo-20260905/analysis.json). The control intervals are shown below.


| Painter | Family | U-estimator contrast | Nominal joint 95% interval |
| --- | --- | --- | --- |
| Monet | color | -0.3268 | [-0.3894, -0.2642] |
| Sisley | color | -0.2750 | [-0.3235, -0.2264] |
| Pissarro | color | 0.0570 | [-0.0077, 0.1218] |
| Cézanne | color | -0.0549 | [-0.0944, -0.0154] |
| Monet | spatial | -0.7726 | [-0.9039, -0.6413] |
| Sisley | spatial | -0.8654 | [-1.0236, -0.7071] |
| Pissarro | spatial | -1.5192 | [-1.6638, -1.3746] |
| Cézanne | spatial | -0.7670 | [-0.9125, -0.6215] |
| Monet | texture | 0.1758 | [0.0962, 0.2555] |
| Sisley | texture | -0.4101 | [-0.5140, -0.3062] |
| Pissarro | texture | -0.2410 | [-0.3182, -0.1638] |
| Cézanne | texture | -0.7415 | [-0.8209, -0.6621] |


| Synthetic scenario | Joint coverage, nondegenerate endpoints | Monte Carlo Wilson 95% interval | Zero-variance endpoint counts |
| --- | --- | --- | --- |
| null | 1.0000 | [0.9630, 1.0000] | [48] |
| shift | 0.8600 | [0.7786, 0.9147] | [0] |
| dispersion | 0.9600 | [0.9016, 0.9843] | [0] |

Calibration used 100 trials per scenario, eight possible synthetic blocks, 16 templates, 31 coordinates, 25 blocks and 999 bootstrap draws per trial. Null coverage excludes 48 zero-variance endpoints without intervals; it is not complete 60-endpoint coverage. The shift scenario's 0.86 coverage rules out presenting nominal 0.95 as demonstrated. Exact truths, bias and Monte Carlo uncertainty are retained. No active-outcome retuning was performed.

## Crop and source sensitivity

Paired crop status: `complete_paired_features`; 3,340 images per branch. Both uncropped and uniform 1% cropped images use short side 496, with the same transform fitted on uncropped-496 new development. This separates crop effects from changing the analysis scale and never upsamples SD-Turbo.

gpt-image-1: 0/12 descriptive control-contrast sign reversals.


| Painter | Family | Uncropped 496 | Cropped 496 | Change |
| --- | --- | --- | --- | --- |
| Monet | color | -0.7822 | -0.7687 | 0.0135 |
| Sisley | color | -0.5631 | -0.5701 | -0.0070 |
| Pissarro | color | -0.1861 | -0.1742 | 0.0118 |
| Cézanne | color | -0.0572 | -0.0532 | 0.0040 |
| Monet | spatial | 0.5344 | 0.5563 | 0.0219 |
| Sisley | spatial | 0.3515 | 0.3295 | -0.0220 |
| Pissarro | spatial | 0.0970 | 0.0775 | -0.0194 |
| Cézanne | spatial | -0.1628 | -0.2330 | -0.0702 |
| Monet | texture | 0.0875 | 0.0669 | -0.0206 |
| Sisley | texture | -0.6098 | -0.6652 | -0.0554 |
| Pissarro | texture | -0.2502 | -0.2794 | -0.0292 |
| Cézanne | texture | 0.4534 | 0.3436 | -0.1098 |

gpt-image-2: 0/12 descriptive control-contrast sign reversals.


| Painter | Family | Uncropped 496 | Cropped 496 | Change |
| --- | --- | --- | --- | --- |
| Monet | color | -0.7565 | -0.7434 | 0.0132 |
| Sisley | color | -0.4397 | -0.4572 | -0.0175 |
| Pissarro | color | -0.0952 | -0.0891 | 0.0061 |
| Cézanne | color | 0.1112 | 0.1140 | 0.0028 |
| Monet | spatial | 0.4739 | 0.4842 | 0.0103 |
| Sisley | spatial | 0.0817 | 0.0977 | 0.0160 |
| Pissarro | spatial | -0.1820 | -0.1863 | -0.0043 |
| Cézanne | spatial | -0.1399 | -0.1822 | -0.0423 |
| Monet | texture | 0.2289 | 0.1876 | -0.0413 |
| Sisley | texture | -0.5072 | -0.5744 | -0.0671 |
| Pissarro | texture | -0.0126 | -0.0409 | -0.0283 |
| Cézanne | texture | 0.7246 | 0.5983 | -0.1263 |

sd-turbo: 0/12 descriptive control-contrast sign reversals.


| Painter | Family | Uncropped 496 | Cropped 496 | Change |
| --- | --- | --- | --- | --- |
| Monet | color | -0.3245 | -0.3352 | -0.0107 |
| Sisley | color | -0.2752 | -0.2824 | -0.0073 |
| Pissarro | color | 0.0593 | 0.0637 | 0.0044 |
| Cézanne | color | -0.0571 | -0.0544 | 0.0027 |
| Monet | spatial | -0.7575 | -0.7821 | -0.0245 |
| Sisley | spatial | -0.8605 | -0.9108 | -0.0503 |
| Pissarro | spatial | -1.5100 | -1.5428 | -0.0328 |
| Cézanne | spatial | -0.7660 | -0.7727 | -0.0066 |
| Monet | texture | 0.1349 | 0.0831 | -0.0518 |
| Sisley | texture | -0.3936 | -0.4259 | -0.0323 |
| Pissarro | texture | -0.2504 | -0.2550 | -0.0046 |
| Cézanne | texture | -0.6482 | -0.5965 | 0.0517 |

Crop results retain all target/specificity changes and paired feature-shift summaries in [the crop result](../../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/robustness/robustness_analysis.json). Crops are dependent versions of one capture, not independent reproductions of the physical painting.


| Painter (confirmation) | Profiles | Native short side min/median/max | Aspect min/median/max | Frame content composition |
| --- | --- | --- | --- | --- |
| Monet | {'embedded_to_srgb': 83, 'missing_assumed_srgb': 214} | [1024.0, 2012.0, 3831.0] | [0.601, 1.253, 3.11] | {'built_place_organized': 68, 'open_or_wooded_land': 33, 'route_organized': 8, 'water_organized': 194} |
| Sisley | {'embedded_to_srgb': 48, 'missing_assumed_srgb': 58} | [1024.0, 2020.0, 3539.0] | [0.75, 1.311, 1.649] | {'built_place_organized': 29, 'open_or_wooded_land': 17, 'route_organized': 9, 'water_organized': 52} |
| Pissarro | {'embedded_to_srgb': 68, 'missing_assumed_srgb': 73} | [1024.0, 2288.0, 3239.0] | [0.735, 1.229, 1.685] | {'built_place_organized': 77, 'open_or_wooded_land': 25, 'route_organized': 12, 'water_organized': 28} |
| Cézanne | {'embedded_to_srgb': 36, 'missing_assumed_srgb': 69} | [1024.0, 1920.0, 3244.0] | [0.35, 1.225, 1.559] | {'built_place_organized': 28, 'open_or_wooded_land': 34, 'route_organized': 13, 'water_organized': 31} |

The content/profile/resolution diagnostic contains 96 stratum records; 6 are unresolved with fewer than ten works. Supported-stratum distances use the full generated condition, not matched generated subject matter. They cannot separate style from content. Collection memberships and all strata are retained in the numeric result; native-short-side bins are 1024–2047, 2048–4095 and ≥4096 pixels. Collections are not established capture workflows.

## Duplicates and copying limitations


| Service | Exact generated duplicate excess | Perceptual/exact candidates | Exact real-file matches |
| --- | --- | --- | --- |
| gpt-image-1 | 0 | 0 | 0 |
| gpt-image-2 | 0 | 0 | 0 |
| sd-turbo | 0 | 0 | 0 |

The search covers successfully measured development, qualification and confirmation images. The 63-bit perceptual-hash distance threshold of eight is uncalibrated screening, not adjudication. Finding no candidate cannot prove originality or training nonoverlap. Generated duplicates retain full statistical multiplicity.

## What remains before a research-paper claim

This completes the registered descriptive experiment only where the grid and measurement gates passed. A stronger model-level study still requires attested OAuth model identity and controllable settings, repeated GPT grids, better-validated uncertainty, and genuine independent captures with justified equivalence margins. Better control of subject matter, capture workflows, borders and training overlap is also needed. These data cannot establish physical brushwork, content-free style, artistic intent, authorship or oeuvre-wide reproduction. All checks are operator/LLM-assisted; no institutionally independent review is claimed.

## Evidence and reproduction

The [method evidence directory](../../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/) contains the shared freeze, one-time confirmation opening, scaler, access ledger, stage receipts, `empirical_analysis.json`, per-experiment `analysis.json`, and crop evidence. Every report table is rendered from these numeric artifacts. Frozen input hashes are commit-bound; raw media, HTTP bodies and model weights remain in the ignored research workspace and are not redistributed. Terminal studies are never rerun in place.

The [prospective empirical amendment](../../studies/painter_feature_generation_v2/PROTOCOL_1.2.md) defines the estimands and limits. The [earlier access report](AVAILABLE_IMAGE_MODELS.md) documents the neutral-image transport assessment, separate from this painter grid. Measurement rationale: [Székely and Rizzo's energy statistics](https://doi.org/10.1016/j.jspi.2013.03.018); the [pinned SD-Turbo model card](https://huggingface.co/stabilityai/sd-turbo/blob/b261bac6fd2cf515557d5d0707481eafa0485ec2/README.md) defines the local model contract.

```bash
uv run --locked --extra analysis --extra learned ruff check .
uv run --locked --extra analysis --extra learned pytest -q -m "not live"
uv run --locked --extra analysis --extra learned latent-art-bench verify-evidence
uv run --locked --extra analysis --extra learned latent-art-bench paper-study audit
```
