# Held-scene prototype transfer audit v1

Retrospective prompt-name identification using existing embeddings; ordinary mean translation, not a new algorithm or a perceptual-fidelity test.

Input binding SHA-256: `bdcf38bb09da53c890a1a62ce268c0336824ccadfb6ba90ee711bdaf1a6f1baf`.

All two encoders × two source views × two reference targets × six configurations are retained. Each model/fold trains on 104 named images from the other 13 scenes, excluding both held-out repeats. Translation scale is exactly one. Reference prototypes are fixed. Generated-prototype context uses painter labels and is a supervised comparator.

The target mean averages unnormalized historical centroids, not normalized classification prototypes. Translation changes class intercepts and leaves centered painter geometry unchanged within each fold. Its fit uses no free or generic controls, so it does not isolate the named-minus-generic causal component.

All 112 predictions per rule/configuration, raw scores, correct-minus-best-incorrect margins, query/fold norms, tie/zero-query counts, confusion matrices and source identities are retained in analysis.json. Scores use raw translated queries. A zero translated query has all-zero linear scores and a first-index tie; its cosine is undefined. No p-values or uncertainty intervals are reported. Overlapping folds and the reused development panel are not independent replications.

Accuracy differences below are percentage points. Scene differences are ordered 0–13. B/T/G denote reference baseline, common translation and supervised generated prototypes. Painter recall lists follow Monet, Sisley, Pissarro, Cézanne.

## CLIP / original / primary

| Configuration | B % | T % | G % | T−B pp | Corrected | Newly incorrect | G−B pp |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 60.7 | 55.4 | 80.4 | -5.4 | 1 | 7 | +19.6 |
| gpt-image-2 | 68.8 | 66.1 | 75.0 | -2.7 | 1 | 4 | +6.2 |
| gpt-image-2.5-flare | 59.8 | 59.8 | 77.7 | +0.0 | 4 | 4 | +17.9 |
| gpt-image-2.5-sunburst | 58.9 | 62.5 | 69.6 | +3.6 | 6 | 2 | +10.7 |
| google/gemini-3.1-flash-image | 51.8 | 59.8 | 63.4 | +8.0 | 15 | 6 | +11.6 |
| black-forest-labs/flux.2-max | 41.1 | 53.6 | 71.4 | +12.5 | 24 | 10 | +30.4 |

Equal-configuration mean differences: paired_translation_vs_baseline: +2.68 pp; paired_generated_prototype_vs_baseline: +16.07 pp.

### gpt-image-1

- reference_baseline: painter recalls (%) [39.3, 46.4, 57.1, 100.0]; top ties 0; zero queries 0; mean margin 0.009788.
- common_translation: painter recalls (%) [42.9, 46.4, 46.4, 85.7]; top ties 0; zero queries 0; mean margin 0.007274.
- generated_prototype: painter recalls (%) [85.7, 60.7, 75.0, 100.0]; top ties 0; zero queries 0; mean margin 0.015899.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, -12.5, -37.5, -25.0, +0.0, +0.0, +0.0, +0.0, +12.5, +0.0, -12.5, +0.0, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+50.0, -12.5, -12.5, -12.5, +25.0, +25.0, +37.5, +37.5, +0.0, +50.0, -12.5, +37.5, +12.5, +50.0].
- Translation L2 norms by held-out scene: [0.323615, 0.320299, 0.323678, 0.329944, 0.324161, 0.319299, 0.324588, 0.321238, 0.318346, 0.325387, 0.324941, 0.325620, 0.317324, 0.321049].

### gpt-image-2

- reference_baseline: painter recalls (%) [60.7, 50.0, 67.9, 96.4]; top ties 0; zero queries 0; mean margin 0.013720.
- common_translation: painter recalls (%) [64.3, 50.0, 53.6, 96.4]; top ties 0; zero queries 0; mean margin 0.017818.
- generated_prototype: painter recalls (%) [71.4, 64.3, 64.3, 100.0]; top ties 0; zero queries 0; mean margin 0.029540.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +0.0, -12.5, +12.5, +0.0, +0.0, +0.0, +0.0, -12.5, -12.5, +0.0, -12.5, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+0.0, +25.0, -25.0, -12.5, +12.5, +37.5, +12.5, +25.0, -37.5, +12.5, +0.0, +25.0, +12.5, +0.0].
- Translation L2 norms by held-out scene: [0.327516, 0.328360, 0.334030, 0.338521, 0.327685, 0.328744, 0.329561, 0.328155, 0.329835, 0.334298, 0.337879, 0.329370, 0.328325, 0.329823].

### gpt-image-2.5-flare

- reference_baseline: painter recalls (%) [32.1, 50.0, 57.1, 100.0]; top ties 0; zero queries 0; mean margin 0.007075.
- common_translation: painter recalls (%) [42.9, 53.6, 42.9, 100.0]; top ties 0; zero queries 0; mean margin 0.009198.
- generated_prototype: painter recalls (%) [78.6, 67.9, 64.3, 100.0]; top ties 0; zero queries 0; mean margin 0.019961.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +0.0, -25.0, +0.0, +0.0, +0.0, +25.0, +0.0, +0.0, +0.0, -12.5, +0.0, +0.0, +12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +12.5, -37.5, -12.5, +12.5, +37.5, +50.0, +37.5, +12.5, +12.5, -12.5, +37.5, +50.0, +25.0].
- Translation L2 norms by held-out scene: [0.383586, 0.384506, 0.385900, 0.389139, 0.379938, 0.383575, 0.384382, 0.381375, 0.384313, 0.382044, 0.390660, 0.381330, 0.381210, 0.381501].

### gpt-image-2.5-sunburst

- reference_baseline: painter recalls (%) [21.4, 64.3, 50.0, 100.0]; top ties 0; zero queries 0; mean margin 0.010398.
- common_translation: painter recalls (%) [42.9, 64.3, 42.9, 100.0]; top ties 0; zero queries 0; mean margin 0.012939.
- generated_prototype: painter recalls (%) [71.4, 57.1, 50.0, 100.0]; top ties 0; zero queries 0; mean margin 0.022826.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +12.5, +0.0, +0.0, +0.0, +0.0, +12.5, +0.0, +25.0, -12.5, -12.5, +0.0, +0.0, +25.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+0.0, +12.5, +0.0, +0.0, +25.0, +50.0, +12.5, +0.0, +25.0, -37.5, -12.5, +25.0, +25.0, +25.0].
- Translation L2 norms by held-out scene: [0.372422, 0.371628, 0.369936, 0.377520, 0.365582, 0.366910, 0.370361, 0.367246, 0.370962, 0.368089, 0.378422, 0.366555, 0.365076, 0.366629].

### google/gemini-3.1-flash-image

- reference_baseline: painter recalls (%) [0.0, 39.3, 67.9, 100.0]; top ties 0; zero queries 0; mean margin 0.001718.
- common_translation: painter recalls (%) [50.0, 42.9, 53.6, 92.9]; top ties 0; zero queries 0; mean margin 0.007581.
- generated_prototype: painter recalls (%) [67.9, 25.0, 60.7, 100.0]; top ties 0; zero queries 0; mean margin 0.016363.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +0.0, +12.5, +0.0, +0.0, +12.5, +0.0, +12.5, +25.0, +25.0, +12.5, -12.5, +12.5, +12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+12.5, -12.5, +25.0, +0.0, +0.0, +25.0, +12.5, +25.0, +12.5, +12.5, +25.0, -12.5, +12.5, +25.0].
- Translation L2 norms by held-out scene: [0.433627, 0.424887, 0.427157, 0.432297, 0.423942, 0.422100, 0.425927, 0.423335, 0.429525, 0.430158, 0.436882, 0.423043, 0.423224, 0.428401].

### black-forest-labs/flux.2-max

- reference_baseline: painter recalls (%) [3.6, 28.6, 78.6, 53.6]; top ties 0; zero queries 0; mean margin -0.010507.
- common_translation: painter recalls (%) [46.4, 46.4, 42.9, 78.6]; top ties 0; zero queries 0; mean margin 0.003129.
- generated_prototype: painter recalls (%) [75.0, 67.9, 53.6, 89.3]; top ties 0; zero queries 0; mean margin 0.015735.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +25.0, +25.0, +25.0, +12.5, +12.5, +0.0, +0.0, +25.0, +12.5, +25.0, -12.5, +12.5, +12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+12.5, +62.5, +25.0, +12.5, +25.0, +37.5, +37.5, +12.5, +25.0, +25.0, +25.0, +25.0, +50.0, +50.0].
- Translation L2 norms by held-out scene: [0.414539, 0.412596, 0.417241, 0.418005, 0.409487, 0.412713, 0.414787, 0.407881, 0.415384, 0.417068, 0.420062, 0.410173, 0.407977, 0.410836].

## CLIP / original / development

| Configuration | B % | T % | G % | T−B pp | Corrected | Newly incorrect | G−B pp |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 60.7 | 55.4 | 80.4 | -5.4 | 5 | 11 | +19.6 |
| gpt-image-2 | 64.3 | 72.3 | 75.0 | +8.0 | 11 | 2 | +10.7 |
| gpt-image-2.5-flare | 60.7 | 58.0 | 77.7 | -2.7 | 4 | 7 | +17.0 |
| gpt-image-2.5-sunburst | 60.7 | 63.4 | 69.6 | +2.7 | 10 | 7 | +8.9 |
| google/gemini-3.1-flash-image | 50.0 | 59.8 | 63.4 | +9.8 | 15 | 4 | +13.4 |
| black-forest-labs/flux.2-max | 41.1 | 52.7 | 71.4 | +11.6 | 19 | 6 | +30.4 |

Equal-configuration mean differences: paired_translation_vs_baseline: +4.02 pp; paired_generated_prototype_vs_baseline: +16.67 pp.

### gpt-image-1

- reference_baseline: painter recalls (%) [28.6, 78.6, 35.7, 100.0]; top ties 0; zero queries 0; mean margin 0.008625.
- common_translation: painter recalls (%) [42.9, 46.4, 39.3, 92.9]; top ties 0; zero queries 0; mean margin 0.006548.
- generated_prototype: painter recalls (%) [85.7, 60.7, 75.0, 100.0]; top ties 0; zero queries 0; mean margin 0.015899.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +0.0, +12.5, +0.0, +0.0, -25.0, -25.0, -12.5, +12.5, -12.5, -12.5, +0.0, -25.0, +12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+50.0, -12.5, +37.5, +0.0, +25.0, +0.0, +12.5, +25.0, +25.0, +37.5, +0.0, +37.5, -12.5, +50.0].
- Translation L2 norms by held-out scene: [0.322660, 0.319967, 0.322997, 0.328749, 0.322775, 0.317876, 0.323108, 0.319816, 0.317923, 0.324793, 0.324406, 0.324244, 0.316106, 0.319175].

### gpt-image-2

- reference_baseline: painter recalls (%) [50.0, 82.1, 28.6, 96.4]; top ties 0; zero queries 0; mean margin 0.012384.
- common_translation: painter recalls (%) [64.3, 75.0, 53.6, 96.4]; top ties 0; zero queries 0; mean margin 0.016560.
- generated_prototype: painter recalls (%) [71.4, 64.3, 64.3, 100.0]; top ties 0; zero queries 0; mean margin 0.029540.
- paired_translation_vs_baseline, scene differences (pp): [+12.5, +0.0, +12.5, +37.5, +0.0, -12.5, +50.0, +0.0, +0.0, -12.5, +25.0, +0.0, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+12.5, +25.0, +0.0, -12.5, +12.5, +12.5, +37.5, +25.0, -12.5, +0.0, +0.0, +50.0, +0.0, +0.0].
- Translation L2 norms by held-out scene: [0.330993, 0.332423, 0.337849, 0.341514, 0.331307, 0.332020, 0.333020, 0.331656, 0.333994, 0.338095, 0.341878, 0.332922, 0.331622, 0.332831].

### gpt-image-2.5-flare

- reference_baseline: painter recalls (%) [32.1, 78.6, 32.1, 100.0]; top ties 0; zero queries 0; mean margin 0.007280.
- common_translation: painter recalls (%) [42.9, 53.6, 35.7, 100.0]; top ties 0; zero queries 0; mean margin 0.008290.
- generated_prototype: painter recalls (%) [78.6, 67.9, 64.3, 100.0]; top ties 0; zero queries 0; mean margin 0.019961.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +12.5, +0.0, +25.0, +0.0, -12.5, +0.0, +0.0, +0.0, -12.5, -25.0, +0.0, -25.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +25.0, -12.5, -12.5, +12.5, +25.0, +50.0, +37.5, +50.0, +0.0, -25.0, +37.5, +25.0, +0.0].
- Translation L2 norms by held-out scene: [0.383706, 0.384935, 0.386266, 0.388678, 0.379969, 0.383538, 0.384398, 0.381501, 0.385041, 0.382754, 0.391445, 0.381460, 0.381284, 0.381308].

### gpt-image-2.5-sunburst

- reference_baseline: painter recalls (%) [28.6, 92.9, 21.4, 100.0]; top ties 0; zero queries 0; mean margin 0.010005.
- common_translation: painter recalls (%) [50.0, 67.9, 35.7, 100.0]; top ties 0; zero queries 0; mean margin 0.011533.
- generated_prototype: painter recalls (%) [71.4, 57.1, 50.0, 100.0]; top ties 0; zero queries 0; mean margin 0.022826.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +12.5, +0.0, +37.5, -12.5, -12.5, +0.0, +0.0, +12.5, +0.0, -12.5, +12.5, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+0.0, +0.0, +0.0, +0.0, +12.5, +25.0, +37.5, +0.0, +50.0, -12.5, -25.0, +25.0, +12.5, +0.0].
- Translation L2 norms by held-out scene: [0.372318, 0.371773, 0.369917, 0.376791, 0.365452, 0.366652, 0.370139, 0.366968, 0.371344, 0.368556, 0.378942, 0.366404, 0.364650, 0.366218].

### google/gemini-3.1-flash-image

- reference_baseline: painter recalls (%) [0.0, 57.1, 42.9, 100.0]; top ties 0; zero queries 0; mean margin 0.002980.
- common_translation: painter recalls (%) [53.6, 46.4, 39.3, 100.0]; top ties 0; zero queries 0; mean margin 0.007721.
- generated_prototype: painter recalls (%) [67.9, 25.0, 60.7, 100.0]; top ties 0; zero queries 0; mean margin 0.016363.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +25.0, +25.0, +12.5, +0.0, +25.0, +0.0, +12.5, +25.0, +12.5, +0.0, +0.0, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+12.5, +0.0, +37.5, +0.0, +0.0, +25.0, +12.5, +25.0, +12.5, +12.5, +25.0, +12.5, -12.5, +25.0].
- Translation L2 norms by held-out scene: [0.432110, 0.423775, 0.426045, 0.430743, 0.422651, 0.420939, 0.424461, 0.422190, 0.428614, 0.429081, 0.435501, 0.421643, 0.421936, 0.426776].

### black-forest-labs/flux.2-max

- reference_baseline: painter recalls (%) [7.1, 50.0, 46.4, 60.7]; top ties 0; zero queries 0; mean margin -0.008260.
- common_translation: painter recalls (%) [50.0, 53.6, 35.7, 71.4]; top ties 0; zero queries 0; mean margin 0.002538.
- generated_prototype: painter recalls (%) [75.0, 67.9, 53.6, 89.3]; top ties 0; zero queries 0; mean margin 0.015735.
- paired_translation_vs_baseline, scene differences (pp): [+25.0, +12.5, +12.5, -12.5, +0.0, +12.5, +12.5, +0.0, +37.5, +12.5, +37.5, +0.0, +0.0, +12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +62.5, +25.0, +0.0, +25.0, +37.5, +50.0, +12.5, +25.0, +25.0, +12.5, +37.5, +37.5, +50.0].
- Translation L2 norms by held-out scene: [0.413922, 0.412544, 0.417016, 0.417152, 0.409205, 0.411980, 0.414071, 0.407463, 0.415447, 0.416972, 0.419836, 0.409643, 0.407315, 0.410011].

## CLIP / audited_region / primary

| Configuration | B % | T % | G % | T−B pp | Corrected | Newly incorrect | G−B pp |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 59.8 | 55.4 | 80.4 | -4.5 | 2 | 7 | +20.5 |
| gpt-image-2 | 69.6 | 66.1 | 75.0 | -3.6 | 1 | 5 | +5.4 |
| gpt-image-2.5-flare | 57.1 | 57.1 | 77.7 | +0.0 | 2 | 2 | +20.5 |
| gpt-image-2.5-sunburst | 59.8 | 61.6 | 69.6 | +1.8 | 5 | 3 | +9.8 |
| google/gemini-3.1-flash-image | 50.0 | 58.0 | 63.4 | +8.0 | 13 | 4 | +13.4 |
| black-forest-labs/flux.2-max | 40.2 | 53.6 | 71.4 | +13.4 | 22 | 7 | +31.2 |

Equal-configuration mean differences: paired_translation_vs_baseline: +2.53 pp; paired_generated_prototype_vs_baseline: +16.82 pp.

### gpt-image-1

- reference_baseline: painter recalls (%) [39.3, 42.9, 57.1, 100.0]; top ties 0; zero queries 0; mean margin 0.009883.
- common_translation: painter recalls (%) [42.9, 46.4, 46.4, 85.7]; top ties 0; zero queries 0; mean margin 0.007267.
- generated_prototype: painter recalls (%) [85.7, 60.7, 75.0, 100.0]; top ties 0; zero queries 0; mean margin 0.015899.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, -12.5, -37.5, -25.0, +0.0, +0.0, +0.0, +0.0, +25.0, +0.0, -12.5, +0.0, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+50.0, -12.5, -12.5, -12.5, +25.0, +25.0, +37.5, +37.5, +12.5, +50.0, -12.5, +37.5, +12.5, +50.0].
- Translation L2 norms by held-out scene: [0.322577, 0.319154, 0.322635, 0.328814, 0.323304, 0.318348, 0.323818, 0.320331, 0.316992, 0.324080, 0.323585, 0.324673, 0.316446, 0.320109].

### gpt-image-2

- reference_baseline: painter recalls (%) [60.7, 53.6, 67.9, 96.4]; top ties 0; zero queries 0; mean margin 0.014061.
- common_translation: painter recalls (%) [64.3, 50.0, 53.6, 96.4]; top ties 0; zero queries 0; mean margin 0.018072.
- generated_prototype: painter recalls (%) [71.4, 64.3, 64.3, 100.0]; top ties 0; zero queries 0; mean margin 0.029540.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +0.0, -12.5, +12.5, +0.0, +0.0, +0.0, +0.0, +0.0, -25.0, +0.0, -25.0, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+0.0, +25.0, -25.0, -12.5, +12.5, +37.5, +12.5, +25.0, -37.5, +0.0, +0.0, +25.0, +12.5, +0.0].
- Translation L2 norms by held-out scene: [0.325524, 0.326418, 0.332030, 0.336626, 0.325799, 0.326827, 0.327630, 0.326417, 0.327743, 0.332145, 0.335780, 0.327391, 0.326539, 0.327804].

### gpt-image-2.5-flare

- reference_baseline: painter recalls (%) [28.6, 50.0, 50.0, 100.0]; top ties 0; zero queries 0; mean margin 0.007293.
- common_translation: painter recalls (%) [32.1, 53.6, 42.9, 100.0]; top ties 0; zero queries 0; mean margin 0.009387.
- generated_prototype: painter recalls (%) [78.6, 67.9, 64.3, 100.0]; top ties 0; zero queries 0; mean margin 0.019961.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +12.5, -12.5, +0.0, +0.0, +0.0, +0.0, +0.0, +12.5, +0.0, -12.5, +0.0, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +25.0, -25.0, +0.0, +12.5, +37.5, +37.5, +37.5, +25.0, +12.5, -12.5, +37.5, +50.0, +25.0].
- Translation L2 norms by held-out scene: [0.382033, 0.383050, 0.384278, 0.387709, 0.378443, 0.382088, 0.382914, 0.379912, 0.382666, 0.380299, 0.388856, 0.379702, 0.379758, 0.379871].

### gpt-image-2.5-sunburst

- reference_baseline: painter recalls (%) [25.0, 64.3, 50.0, 100.0]; top ties 0; zero queries 0; mean margin 0.010503.
- common_translation: painter recalls (%) [42.9, 60.7, 42.9, 100.0]; top ties 0; zero queries 0; mean margin 0.013074.
- generated_prototype: painter recalls (%) [71.4, 57.1, 50.0, 100.0]; top ties 0; zero queries 0; mean margin 0.022826.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +12.5, +0.0, +0.0, +0.0, +0.0, +12.5, +0.0, +12.5, -25.0, -12.5, +0.0, +0.0, +25.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+0.0, +12.5, +0.0, +0.0, +25.0, +50.0, +12.5, +0.0, +12.5, -37.5, -12.5, +25.0, +25.0, +25.0].
- Translation L2 norms by held-out scene: [0.370735, 0.370134, 0.368233, 0.375927, 0.364017, 0.365282, 0.368745, 0.365738, 0.369270, 0.366315, 0.376546, 0.364917, 0.363658, 0.364909].

### google/gemini-3.1-flash-image

- reference_baseline: painter recalls (%) [0.0, 39.3, 64.3, 96.4]; top ties 0; zero queries 0; mean margin 0.001514.
- common_translation: painter recalls (%) [46.4, 39.3, 53.6, 92.9]; top ties 0; zero queries 0; mean margin 0.007502.
- generated_prototype: painter recalls (%) [67.9, 25.0, 60.7, 100.0]; top ties 0; zero queries 0; mean margin 0.016363.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +12.5, +12.5, +12.5, +0.0, +12.5, +0.0, +12.5, +12.5, +25.0, +0.0, -12.5, +12.5, +12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+12.5, +0.0, +25.0, +12.5, +0.0, +25.0, +12.5, +25.0, +12.5, +12.5, +25.0, -12.5, +12.5, +25.0].
- Translation L2 norms by held-out scene: [0.431796, 0.423010, 0.425218, 0.430466, 0.422021, 0.420124, 0.424145, 0.421319, 0.427529, 0.428174, 0.435009, 0.421099, 0.421292, 0.426429].

### black-forest-labs/flux.2-max

- reference_baseline: painter recalls (%) [3.6, 32.1, 71.4, 53.6]; top ties 0; zero queries 0; mean margin -0.010495.
- common_translation: painter recalls (%) [46.4, 42.9, 46.4, 78.6]; top ties 0; zero queries 0; mean margin 0.003382.
- generated_prototype: painter recalls (%) [75.0, 67.9, 53.6, 89.3]; top ties 0; zero queries 0; mean margin 0.015735.
- paired_translation_vs_baseline, scene differences (pp): [+12.5, +12.5, +25.0, +25.0, +12.5, +12.5, +0.0, +0.0, +37.5, +0.0, +25.0, +0.0, +12.5, +12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +50.0, +25.0, +12.5, +25.0, +37.5, +37.5, +12.5, +25.0, +25.0, +25.0, +37.5, +50.0, +50.0].
- Translation L2 norms by held-out scene: [0.411248, 0.409339, 0.413989, 0.414754, 0.406291, 0.409488, 0.411644, 0.404646, 0.411899, 0.413692, 0.416714, 0.406845, 0.404784, 0.407529].

## CLIP / audited_region / development

| Configuration | B % | T % | G % | T−B pp | Corrected | Newly incorrect | G−B pp |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 58.9 | 55.4 | 80.4 | -3.6 | 4 | 8 | +21.4 |
| gpt-image-2 | 66.1 | 69.6 | 75.0 | +3.6 | 6 | 2 | +8.9 |
| gpt-image-2.5-flare | 63.4 | 58.0 | 77.7 | -5.4 | 1 | 7 | +14.3 |
| gpt-image-2.5-sunburst | 62.5 | 61.6 | 69.6 | -0.9 | 8 | 9 | +7.1 |
| google/gemini-3.1-flash-image | 50.9 | 59.8 | 63.4 | +8.9 | 14 | 4 | +12.5 |
| black-forest-labs/flux.2-max | 42.9 | 53.6 | 71.4 | +10.7 | 19 | 7 | +28.6 |

Equal-configuration mean differences: paired_translation_vs_baseline: +2.23 pp; paired_generated_prototype_vs_baseline: +15.48 pp.

### gpt-image-1

- reference_baseline: painter recalls (%) [32.1, 67.9, 35.7, 100.0]; top ties 0; zero queries 0; mean margin 0.009021.
- common_translation: painter recalls (%) [42.9, 46.4, 39.3, 92.9]; top ties 0; zero queries 0; mean margin 0.006540.
- generated_prototype: painter recalls (%) [85.7, 60.7, 75.0, 100.0]; top ties 0; zero queries 0; mean margin 0.015899.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +0.0, +0.0, +12.5, +0.0, -25.0, -12.5, -12.5, +12.5, +0.0, -12.5, +0.0, -25.0, +12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+50.0, -12.5, +25.0, +12.5, +25.0, +0.0, +25.0, +25.0, +25.0, +50.0, +0.0, +37.5, -12.5, +50.0].
- Translation L2 norms by held-out scene: [0.318084, 0.315218, 0.318356, 0.324161, 0.318463, 0.313287, 0.318973, 0.315260, 0.312813, 0.319737, 0.319091, 0.319796, 0.311693, 0.314768].

### gpt-image-2

- reference_baseline: painter recalls (%) [60.7, 78.6, 28.6, 96.4]; top ties 0; zero queries 0; mean margin 0.013169.
- common_translation: painter recalls (%) [64.3, 71.4, 46.4, 96.4]; top ties 0; zero queries 0; mean margin 0.016916.
- generated_prototype: painter recalls (%) [71.4, 64.3, 64.3, 100.0]; top ties 0; zero queries 0; mean margin 0.029540.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +0.0, +12.5, +12.5, +0.0, +0.0, +37.5, +0.0, +0.0, -12.5, +12.5, +0.0, -12.5, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+0.0, +25.0, +0.0, -25.0, +12.5, +25.0, +25.0, +25.0, -12.5, +0.0, +0.0, +50.0, +0.0, +0.0].
- Translation L2 norms by held-out scene: [0.326596, 0.328109, 0.333406, 0.337407, 0.327062, 0.327696, 0.328646, 0.327526, 0.329362, 0.333443, 0.337186, 0.328577, 0.327501, 0.328372].

### gpt-image-2.5-flare

- reference_baseline: painter recalls (%) [42.9, 78.6, 32.1, 100.0]; top ties 0; zero queries 0; mean margin 0.007770.
- common_translation: painter recalls (%) [42.9, 53.6, 35.7, 100.0]; top ties 0; zero queries 0; mean margin 0.008468.
- generated_prototype: painter recalls (%) [78.6, 67.9, 64.3, 100.0]; top ties 0; zero queries 0; mean margin 0.019961.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +0.0, +0.0, +0.0, +0.0, -12.5, +0.0, +0.0, +0.0, -12.5, -25.0, +0.0, -25.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +12.5, -12.5, -37.5, +12.5, +25.0, +50.0, +37.5, +50.0, +0.0, -25.0, +37.5, +25.0, +0.0].
- Translation L2 norms by held-out scene: [0.381007, 0.382392, 0.383450, 0.386309, 0.377330, 0.380866, 0.381789, 0.378841, 0.382165, 0.379725, 0.388201, 0.378670, 0.378670, 0.378496].

### gpt-image-2.5-sunburst

- reference_baseline: painter recalls (%) [32.1, 96.4, 21.4, 100.0]; top ties 0; zero queries 0; mean margin 0.010517.
- common_translation: painter recalls (%) [46.4, 64.3, 35.7, 100.0]; top ties 0; zero queries 0; mean margin 0.011694.
- generated_prototype: painter recalls (%) [71.4, 57.1, 50.0, 100.0]; top ties 0; zero queries 0; mean margin 0.022826.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +12.5, +0.0, +25.0, -25.0, -12.5, +0.0, +0.0, +12.5, -12.5, -12.5, +0.0, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+0.0, +0.0, +0.0, +0.0, +0.0, +25.0, +37.5, +0.0, +50.0, -25.0, -25.0, +25.0, +12.5, +0.0].
- Translation L2 norms by held-out scene: [0.369633, 0.369409, 0.367177, 0.374360, 0.362914, 0.363945, 0.367496, 0.364494, 0.368621, 0.365698, 0.375781, 0.363796, 0.362336, 0.363461].

### google/gemini-3.1-flash-image

- reference_baseline: painter recalls (%) [3.6, 57.1, 42.9, 100.0]; top ties 0; zero queries 0; mean margin 0.003742.
- common_translation: painter recalls (%) [53.6, 46.4, 39.3, 100.0]; top ties 0; zero queries 0; mean margin 0.007924.
- generated_prototype: painter recalls (%) [67.9, 25.0, 60.7, 100.0]; top ties 0; zero queries 0; mean margin 0.016363.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +25.0, +12.5, +12.5, +0.0, +25.0, +0.0, +12.5, +25.0, +12.5, +0.0, +0.0, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+12.5, +0.0, +25.0, +0.0, +0.0, +25.0, +12.5, +25.0, +12.5, +12.5, +25.0, +12.5, -12.5, +25.0].
- Translation L2 norms by held-out scene: [0.428112, 0.419570, 0.421799, 0.426826, 0.418380, 0.416481, 0.420435, 0.417708, 0.424261, 0.424735, 0.431260, 0.417412, 0.417616, 0.422500].

### black-forest-labs/flux.2-max

- reference_baseline: painter recalls (%) [10.7, 50.0, 50.0, 60.7]; top ties 0; zero queries 0; mean margin -0.008262.
- common_translation: painter recalls (%) [50.0, 53.6, 35.7, 75.0]; top ties 0; zero queries 0; mean margin 0.002469.
- generated_prototype: painter recalls (%) [75.0, 67.9, 53.6, 89.3]; top ties 0; zero queries 0; mean margin 0.015735.
- paired_translation_vs_baseline, scene differences (pp): [+25.0, +12.5, +25.0, -37.5, +0.0, +12.5, +12.5, +0.0, +37.5, +12.5, +37.5, +0.0, +0.0, +12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +62.5, +25.0, -25.0, +25.0, +37.5, +50.0, +12.5, +25.0, +25.0, +12.5, +37.5, +37.5, +50.0].
- Translation L2 norms by held-out scene: [0.406404, 0.405091, 0.409590, 0.409781, 0.401793, 0.404465, 0.406764, 0.399969, 0.407622, 0.409248, 0.412202, 0.402109, 0.399875, 0.402534].

## CSD / original / primary

| Configuration | B % | T % | G % | T−B pp | Corrected | Newly incorrect | G−B pp |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 72.3 | 73.2 | 84.8 | +0.9 | 3 | 2 | +12.5 |
| gpt-image-2 | 75.9 | 76.8 | 94.6 | +0.9 | 4 | 3 | +18.8 |
| gpt-image-2.5-flare | 62.5 | 74.1 | 92.9 | +11.6 | 16 | 3 | +30.4 |
| gpt-image-2.5-sunburst | 61.6 | 70.5 | 90.2 | +8.9 | 17 | 7 | +28.6 |
| google/gemini-3.1-flash-image | 50.9 | 61.6 | 75.0 | +10.7 | 22 | 10 | +24.1 |
| black-forest-labs/flux.2-max | 39.3 | 66.1 | 75.0 | +26.8 | 39 | 9 | +35.7 |

Equal-configuration mean differences: paired_translation_vs_baseline: +9.97 pp; paired_generated_prototype_vs_baseline: +25.00 pp.

### gpt-image-1

- reference_baseline: painter recalls (%) [57.1, 75.0, 57.1, 100.0]; top ties 0; zero queries 0; mean margin 0.065338.
- common_translation: painter recalls (%) [53.6, 71.4, 67.9, 100.0]; top ties 0; zero queries 0; mean margin 0.051412.
- generated_prototype: painter recalls (%) [82.1, 71.4, 85.7, 100.0]; top ties 0; zero queries 0; mean margin 0.066438.
- paired_translation_vs_baseline, scene differences (pp): [+12.5, +0.0, +0.0, +12.5, +0.0, -12.5, -12.5, +0.0, +0.0, +12.5, +0.0, +0.0, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+12.5, +25.0, +0.0, +12.5, +25.0, +0.0, +37.5, +12.5, +12.5, +12.5, +12.5, +12.5, +25.0, -25.0].
- Translation L2 norms by held-out scene: [0.559053, 0.551887, 0.552573, 0.569805, 0.556636, 0.554393, 0.559288, 0.552970, 0.553075, 0.560812, 0.553739, 0.553630, 0.551974, 0.555678].

### gpt-image-2

- reference_baseline: painter recalls (%) [75.0, 60.7, 67.9, 100.0]; top ties 0; zero queries 0; mean margin 0.052729.
- common_translation: painter recalls (%) [75.0, 75.0, 57.1, 100.0]; top ties 0; zero queries 0; mean margin 0.071043.
- generated_prototype: painter recalls (%) [100.0, 92.9, 85.7, 100.0]; top ties 0; zero queries 0; mean margin 0.090467.
- paired_translation_vs_baseline, scene differences (pp): [-12.5, +0.0, +0.0, +0.0, +0.0, +12.5, +12.5, +0.0, +0.0, +0.0, +12.5, -12.5, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +25.0, +12.5, +25.0, +37.5, +25.0, +25.0, +50.0, -25.0, +0.0, +12.5, +0.0, +37.5, +12.5].
- Translation L2 norms by held-out scene: [0.471200, 0.469629, 0.471462, 0.488171, 0.470782, 0.469956, 0.470008, 0.473220, 0.471189, 0.474513, 0.475055, 0.469463, 0.472242, 0.470010].

### gpt-image-2.5-flare

- reference_baseline: painter recalls (%) [21.4, 67.9, 60.7, 100.0]; top ties 0; zero queries 0; mean margin 0.027769.
- common_translation: painter recalls (%) [60.7, 85.7, 50.0, 100.0]; top ties 0; zero queries 0; mean margin 0.052190.
- generated_prototype: painter recalls (%) [100.0, 89.3, 82.1, 100.0]; top ties 0; zero queries 0; mean margin 0.082518.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +12.5, +0.0, +25.0, +0.0, +12.5, +12.5, +0.0, -12.5, +25.0, +37.5, +0.0, +25.0, +25.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+37.5, +37.5, +0.0, +37.5, +50.0, +37.5, +12.5, +50.0, +12.5, +25.0, +25.0, +37.5, +37.5, +25.0].
- Translation L2 norms by held-out scene: [0.549802, 0.551935, 0.550322, 0.558921, 0.547996, 0.549267, 0.550469, 0.546712, 0.551095, 0.546382, 0.553670, 0.547707, 0.549224, 0.548550].

### gpt-image-2.5-sunburst

- reference_baseline: painter recalls (%) [7.1, 67.9, 71.4, 100.0]; top ties 0; zero queries 0; mean margin 0.035849.
- common_translation: painter recalls (%) [53.6, 82.1, 46.4, 100.0]; top ties 0; zero queries 0; mean margin 0.057292.
- generated_prototype: painter recalls (%) [89.3, 89.3, 82.1, 100.0]; top ties 0; zero queries 0; mean margin 0.094276.
- paired_translation_vs_baseline, scene differences (pp): [+12.5, +12.5, +12.5, +0.0, +12.5, +0.0, +25.0, +0.0, +12.5, -12.5, +25.0, +12.5, -12.5, +25.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+12.5, +37.5, +25.0, +12.5, +50.0, +25.0, +25.0, +37.5, +12.5, +25.0, +50.0, +25.0, +37.5, +25.0].
- Translation L2 norms by held-out scene: [0.511283, 0.513936, 0.510481, 0.521952, 0.509936, 0.509087, 0.511832, 0.508700, 0.513400, 0.508941, 0.515798, 0.508395, 0.509691, 0.508717].

### google/gemini-3.1-flash-image

- reference_baseline: painter recalls (%) [0.0, 28.6, 75.0, 100.0]; top ties 0; zero queries 0; mean margin 0.019625.
- common_translation: painter recalls (%) [53.6, 42.9, 53.6, 96.4]; top ties 0; zero queries 0; mean margin 0.024323.
- generated_prototype: painter recalls (%) [75.0, 50.0, 75.0, 100.0]; top ties 0; zero queries 0; mean margin 0.053919.
- paired_translation_vs_baseline, scene differences (pp): [-12.5, -12.5, +25.0, +12.5, +0.0, +12.5, +12.5, +0.0, +12.5, +37.5, +37.5, +12.5, +0.0, +12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [-25.0, +0.0, +37.5, +12.5, +25.0, +25.0, +50.0, +12.5, +25.0, +37.5, +50.0, +12.5, +25.0, +50.0].
- Translation L2 norms by held-out scene: [0.616962, 0.604506, 0.607301, 0.619714, 0.608685, 0.606638, 0.612118, 0.602423, 0.614095, 0.609700, 0.620597, 0.608674, 0.607097, 0.611392].

### black-forest-labs/flux.2-max

- reference_baseline: painter recalls (%) [0.0, 10.7, 89.3, 57.1]; top ties 0; zero queries 0; mean margin -0.018893.
- common_translation: painter recalls (%) [57.1, 57.1, 57.1, 92.9]; top ties 0; zero queries 0; mean margin 0.029962.
- generated_prototype: painter recalls (%) [78.6, 60.7, 64.3, 96.4]; top ties 0; zero queries 0; mean margin 0.047835.
- paired_translation_vs_baseline, scene differences (pp): [+25.0, +50.0, +37.5, +37.5, +12.5, +25.0, +25.0, +12.5, +25.0, +0.0, +50.0, +25.0, +12.5, +37.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +62.5, +50.0, +25.0, +37.5, +62.5, +62.5, +37.5, +25.0, +0.0, +25.0, +37.5, +12.5, +37.5].
- Translation L2 norms by held-out scene: [0.541517, 0.532947, 0.532992, 0.552232, 0.534332, 0.533094, 0.536029, 0.529573, 0.538019, 0.533360, 0.536611, 0.530474, 0.529872, 0.534369].

## CSD / original / development

| Configuration | B % | T % | G % | T−B pp | Corrected | Newly incorrect | G−B pp |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 60.7 | 67.9 | 84.8 | +7.1 | 16 | 8 | +24.1 |
| gpt-image-2 | 67.0 | 76.8 | 94.6 | +9.8 | 15 | 4 | +27.7 |
| gpt-image-2.5-flare | 59.8 | 64.3 | 92.9 | +4.5 | 10 | 5 | +33.0 |
| gpt-image-2.5-sunburst | 56.2 | 63.4 | 90.2 | +7.1 | 13 | 5 | +33.9 |
| google/gemini-3.1-flash-image | 44.6 | 60.7 | 75.0 | +16.1 | 23 | 5 | +30.4 |
| black-forest-labs/flux.2-max | 42.9 | 57.1 | 75.0 | +14.3 | 32 | 16 | +32.1 |

Equal-configuration mean differences: paired_translation_vs_baseline: +9.82 pp; paired_generated_prototype_vs_baseline: +30.21 pp.

### gpt-image-1

- reference_baseline: painter recalls (%) [28.6, 96.4, 17.9, 100.0]; top ties 0; zero queries 0; mean margin 0.048151.
- common_translation: painter recalls (%) [42.9, 67.9, 60.7, 100.0]; top ties 0; zero queries 0; mean margin 0.045278.
- generated_prototype: painter recalls (%) [82.1, 71.4, 85.7, 100.0]; top ties 0; zero queries 0; mean margin 0.066438.
- paired_translation_vs_baseline, scene differences (pp): [+12.5, +12.5, +0.0, +0.0, +0.0, +25.0, -12.5, +0.0, +12.5, +37.5, +12.5, +12.5, +0.0, -12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +25.0, +0.0, +12.5, +25.0, +37.5, +25.0, +25.0, +50.0, +37.5, +25.0, +50.0, +25.0, -25.0].
- Translation L2 norms by held-out scene: [0.549866, 0.543078, 0.542968, 0.560367, 0.546926, 0.544695, 0.549803, 0.543158, 0.543863, 0.550895, 0.544117, 0.543949, 0.542483, 0.545236].

### gpt-image-2

- reference_baseline: painter recalls (%) [53.6, 92.9, 21.4, 100.0]; top ties 0; zero queries 0; mean margin 0.047668.
- common_translation: painter recalls (%) [75.0, 78.6, 53.6, 100.0]; top ties 0; zero queries 0; mean margin 0.066850.
- generated_prototype: painter recalls (%) [100.0, 92.9, 85.7, 100.0]; top ties 0; zero queries 0; mean margin 0.090467.
- paired_translation_vs_baseline, scene differences (pp): [-12.5, +0.0, +12.5, +12.5, -12.5, +12.5, +25.0, +12.5, +0.0, +12.5, +37.5, +25.0, +12.5, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +25.0, +25.0, +25.0, +25.0, +37.5, +25.0, +62.5, -12.5, +25.0, +37.5, +37.5, +37.5, +12.5].
- Translation L2 norms by held-out scene: [0.468901, 0.468329, 0.469656, 0.485761, 0.468794, 0.468195, 0.467792, 0.471525, 0.469126, 0.471948, 0.473384, 0.467341, 0.470031, 0.467328].

### gpt-image-2.5-flare

- reference_baseline: painter recalls (%) [28.6, 96.4, 14.3, 100.0]; top ties 0; zero queries 0; mean margin 0.023817.
- common_translation: painter recalls (%) [53.6, 78.6, 25.0, 100.0]; top ties 0; zero queries 0; mean margin 0.045483.
- generated_prototype: painter recalls (%) [100.0, 89.3, 82.1, 100.0]; top ties 0; zero queries 0; mean margin 0.082518.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +0.0, +12.5, -12.5, -12.5, +0.0, +12.5, -12.5, +25.0, +12.5, +0.0, +25.0, +25.0, -12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+37.5, +25.0, +25.0, +12.5, +37.5, +50.0, +50.0, +25.0, +50.0, +37.5, +25.0, +50.0, +37.5, +0.0].
- Translation L2 norms by held-out scene: [0.555676, 0.558348, 0.556511, 0.564565, 0.554071, 0.555631, 0.556400, 0.552942, 0.557356, 0.552360, 0.560056, 0.553556, 0.555392, 0.554025].

### gpt-image-2.5-sunburst

- reference_baseline: painter recalls (%) [14.3, 92.9, 17.9, 100.0]; top ties 0; zero queries 0; mean margin 0.032587.
- common_translation: painter recalls (%) [57.1, 75.0, 21.4, 100.0]; top ties 0; zero queries 0; mean margin 0.050455.
- generated_prototype: painter recalls (%) [89.3, 89.3, 82.1, 100.0]; top ties 0; zero queries 0; mean margin 0.094276.
- paired_translation_vs_baseline, scene differences (pp): [+25.0, +0.0, +0.0, +25.0, -12.5, +12.5, +0.0, -12.5, +25.0, +0.0, +25.0, +25.0, +0.0, -12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +25.0, +12.5, +25.0, +37.5, +50.0, +50.0, +25.0, +50.0, +37.5, +50.0, +37.5, +37.5, +12.5].
- Translation L2 norms by held-out scene: [0.514714, 0.517927, 0.513631, 0.524876, 0.513210, 0.512532, 0.515215, 0.512214, 0.517020, 0.512272, 0.519481, 0.511780, 0.512995, 0.511469].

### google/gemini-3.1-flash-image

- reference_baseline: painter recalls (%) [0.0, 32.1, 46.4, 100.0]; top ties 0; zero queries 0; mean margin 0.015927.
- common_translation: painter recalls (%) [60.7, 50.0, 39.3, 92.9]; top ties 0; zero queries 0; mean margin 0.020388.
- generated_prototype: painter recalls (%) [75.0, 50.0, 75.0, 100.0]; top ties 0; zero queries 0; mean margin 0.053919.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +12.5, +25.0, +12.5, +0.0, +0.0, +12.5, +0.0, +50.0, +25.0, +37.5, +12.5, +12.5, +25.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [-12.5, +12.5, +37.5, +25.0, +25.0, +12.5, +62.5, +12.5, +50.0, +50.0, +62.5, +12.5, +25.0, +50.0].
- Translation L2 norms by held-out scene: [0.610475, 0.598128, 0.600598, 0.612991, 0.601830, 0.600212, 0.605620, 0.595876, 0.607781, 0.602721, 0.613906, 0.601787, 0.600518, 0.604137].

### black-forest-labs/flux.2-max

- reference_baseline: painter recalls (%) [0.0, 17.9, 89.3, 64.3]; top ties 0; zero queries 0; mean margin -0.014566.
- common_translation: painter recalls (%) [42.9, 53.6, 39.3, 92.9]; top ties 0; zero queries 0; mean margin 0.025281.
- generated_prototype: painter recalls (%) [78.6, 60.7, 64.3, 96.4]; top ties 0; zero queries 0; mean margin 0.047835.
- paired_translation_vs_baseline, scene differences (pp): [+37.5, +0.0, +37.5, +0.0, +12.5, +25.0, +0.0, +12.5, +12.5, -12.5, +25.0, +12.5, +12.5, +25.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+37.5, +37.5, +50.0, +12.5, +37.5, +62.5, +62.5, +37.5, +12.5, +0.0, +25.0, +37.5, +12.5, +25.0].
- Translation L2 norms by held-out scene: [0.527610, 0.520461, 0.519854, 0.538085, 0.520835, 0.519416, 0.522516, 0.516474, 0.524916, 0.519781, 0.523623, 0.516871, 0.516054, 0.520888].

## CSD / audited_region / primary

| Configuration | B % | T % | G % | T−B pp | Corrected | Newly incorrect | G−B pp |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 73.2 | 71.4 | 84.8 | -1.8 | 4 | 6 | +11.6 |
| gpt-image-2 | 75.9 | 75.9 | 94.6 | +0.0 | 5 | 5 | +18.8 |
| gpt-image-2.5-flare | 61.6 | 74.1 | 92.9 | +12.5 | 17 | 3 | +31.2 |
| gpt-image-2.5-sunburst | 60.7 | 72.3 | 90.2 | +11.6 | 17 | 4 | +29.5 |
| google/gemini-3.1-flash-image | 50.9 | 61.6 | 75.0 | +10.7 | 23 | 11 | +24.1 |
| black-forest-labs/flux.2-max | 39.3 | 64.3 | 75.0 | +25.0 | 37 | 9 | +35.7 |

Equal-configuration mean differences: paired_translation_vs_baseline: +9.67 pp; paired_generated_prototype_vs_baseline: +25.15 pp.

### gpt-image-1

- reference_baseline: painter recalls (%) [64.3, 71.4, 57.1, 100.0]; top ties 0; zero queries 0; mean margin 0.066455.
- common_translation: painter recalls (%) [46.4, 71.4, 67.9, 100.0]; top ties 0; zero queries 0; mean margin 0.051005.
- generated_prototype: painter recalls (%) [82.1, 71.4, 85.7, 100.0]; top ties 0; zero queries 0; mean margin 0.066438.
- paired_translation_vs_baseline, scene differences (pp): [+12.5, -12.5, +0.0, +12.5, +0.0, -12.5, -12.5, +0.0, +0.0, +12.5, -12.5, -25.0, +0.0, +12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+12.5, +12.5, +0.0, +12.5, +25.0, +0.0, +37.5, +12.5, +0.0, +12.5, +12.5, +12.5, +25.0, -12.5].
- Translation L2 norms by held-out scene: [0.561565, 0.554445, 0.555263, 0.572186, 0.559348, 0.557052, 0.561868, 0.555639, 0.555560, 0.563127, 0.556355, 0.556296, 0.554591, 0.558352].

### gpt-image-2

- reference_baseline: painter recalls (%) [75.0, 57.1, 71.4, 100.0]; top ties 0; zero queries 0; mean margin 0.054146.
- common_translation: painter recalls (%) [71.4, 75.0, 57.1, 100.0]; top ties 0; zero queries 0; mean margin 0.070939.
- generated_prototype: painter recalls (%) [100.0, 92.9, 85.7, 100.0]; top ties 0; zero queries 0; mean margin 0.090467.
- paired_translation_vs_baseline, scene differences (pp): [-12.5, +0.0, +0.0, +0.0, +0.0, +12.5, +12.5, +0.0, +0.0, +0.0, +25.0, -25.0, +0.0, -12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +25.0, +12.5, +25.0, +37.5, +25.0, +25.0, +50.0, -25.0, +0.0, +25.0, +0.0, +37.5, +0.0].
- Translation L2 norms by held-out scene: [0.473638, 0.471918, 0.473812, 0.490510, 0.473236, 0.472345, 0.472445, 0.475630, 0.473537, 0.476657, 0.477361, 0.471871, 0.474680, 0.472419].

### gpt-image-2.5-flare

- reference_baseline: painter recalls (%) [21.4, 60.7, 64.3, 100.0]; top ties 0; zero queries 0; mean margin 0.029060.
- common_translation: painter recalls (%) [60.7, 82.1, 53.6, 100.0]; top ties 0; zero queries 0; mean margin 0.052283.
- generated_prototype: painter recalls (%) [100.0, 89.3, 82.1, 100.0]; top ties 0; zero queries 0; mean margin 0.082518.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +12.5, +0.0, +25.0, +0.0, +12.5, +12.5, +0.0, -12.5, +37.5, +25.0, +12.5, +25.0, +25.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+37.5, +37.5, +0.0, +37.5, +50.0, +37.5, +12.5, +50.0, +12.5, +37.5, +25.0, +37.5, +37.5, +25.0].
- Translation L2 norms by held-out scene: [0.551035, 0.553033, 0.551451, 0.560110, 0.549179, 0.550314, 0.551716, 0.547946, 0.552268, 0.547286, 0.554715, 0.548886, 0.550439, 0.549763].

### gpt-image-2.5-sunburst

- reference_baseline: painter recalls (%) [7.1, 64.3, 71.4, 100.0]; top ties 0; zero queries 0; mean margin 0.037514.
- common_translation: painter recalls (%) [50.0, 82.1, 57.1, 100.0]; top ties 0; zero queries 0; mean margin 0.057857.
- generated_prototype: painter recalls (%) [89.3, 89.3, 82.1, 100.0]; top ties 0; zero queries 0; mean margin 0.094276.
- paired_translation_vs_baseline, scene differences (pp): [+12.5, +12.5, +25.0, -12.5, +12.5, +0.0, +25.0, +0.0, +0.0, +25.0, +37.5, +12.5, -12.5, +25.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+12.5, +37.5, +37.5, +12.5, +50.0, +25.0, +25.0, +37.5, +0.0, +37.5, +50.0, +25.0, +37.5, +25.0].
- Translation L2 norms by held-out scene: [0.513141, 0.515578, 0.512291, 0.523713, 0.511673, 0.510766, 0.513605, 0.510459, 0.515145, 0.510401, 0.517433, 0.510189, 0.511516, 0.510497].

### google/gemini-3.1-flash-image

- reference_baseline: painter recalls (%) [0.0, 28.6, 75.0, 100.0]; top ties 0; zero queries 0; mean margin 0.020020.
- common_translation: painter recalls (%) [53.6, 46.4, 50.0, 96.4]; top ties 0; zero queries 0; mean margin 0.023782.
- generated_prototype: painter recalls (%) [75.0, 50.0, 75.0, 100.0]; top ties 0; zero queries 0; mean margin 0.053919.
- paired_translation_vs_baseline, scene differences (pp): [-12.5, -12.5, +25.0, +12.5, +0.0, +12.5, +12.5, +0.0, +12.5, +37.5, +37.5, +12.5, +0.0, +12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [-25.0, +0.0, +37.5, +12.5, +25.0, +25.0, +50.0, +12.5, +25.0, +37.5, +50.0, +12.5, +25.0, +50.0].
- Translation L2 norms by held-out scene: [0.620620, 0.608030, 0.610864, 0.623366, 0.612297, 0.610254, 0.615884, 0.605906, 0.617801, 0.613148, 0.624269, 0.612302, 0.610667, 0.615159].

### black-forest-labs/flux.2-max

- reference_baseline: painter recalls (%) [0.0, 10.7, 89.3, 57.1]; top ties 0; zero queries 0; mean margin -0.017491.
- common_translation: painter recalls (%) [53.6, 53.6, 57.1, 92.9]; top ties 0; zero queries 0; mean margin 0.030016.
- generated_prototype: painter recalls (%) [78.6, 60.7, 64.3, 96.4]; top ties 0; zero queries 0; mean margin 0.047835.
- paired_translation_vs_baseline, scene differences (pp): [+25.0, +50.0, +37.5, +37.5, +12.5, +25.0, +12.5, +12.5, +25.0, +0.0, +37.5, +25.0, +12.5, +37.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +62.5, +50.0, +25.0, +37.5, +62.5, +62.5, +37.5, +25.0, +0.0, +25.0, +37.5, +12.5, +37.5].
- Translation L2 norms by held-out scene: [0.546663, 0.537892, 0.537988, 0.557251, 0.539335, 0.538180, 0.541087, 0.534607, 0.542986, 0.538163, 0.541497, 0.535432, 0.534904, 0.539390].

## CSD / audited_region / development

| Configuration | B % | T % | G % | T−B pp | Corrected | Newly incorrect | G−B pp |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 58.9 | 68.8 | 84.8 | +9.8 | 19 | 8 | +25.9 |
| gpt-image-2 | 67.9 | 76.8 | 94.6 | +8.9 | 14 | 4 | +26.8 |
| gpt-image-2.5-flare | 58.9 | 64.3 | 92.9 | +5.4 | 11 | 5 | +33.9 |
| gpt-image-2.5-sunburst | 57.1 | 63.4 | 90.2 | +6.2 | 14 | 7 | +33.0 |
| google/gemini-3.1-flash-image | 44.6 | 60.7 | 75.0 | +16.1 | 23 | 5 | +30.4 |
| black-forest-labs/flux.2-max | 42.9 | 57.1 | 75.0 | +14.3 | 32 | 16 | +32.1 |

Equal-configuration mean differences: paired_translation_vs_baseline: +10.12 pp; paired_generated_prototype_vs_baseline: +30.36 pp.

### gpt-image-1

- reference_baseline: painter recalls (%) [25.0, 96.4, 14.3, 100.0]; top ties 0; zero queries 0; mean margin 0.048827.
- common_translation: painter recalls (%) [46.4, 67.9, 60.7, 100.0]; top ties 0; zero queries 0; mean margin 0.045588.
- generated_prototype: painter recalls (%) [82.1, 71.4, 85.7, 100.0]; top ties 0; zero queries 0; mean margin 0.066438.
- paired_translation_vs_baseline, scene differences (pp): [+12.5, +12.5, +0.0, +0.0, +0.0, +25.0, +0.0, +0.0, +25.0, +37.5, +12.5, +12.5, +0.0, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +25.0, +0.0, +12.5, +25.0, +37.5, +37.5, +25.0, +50.0, +37.5, +25.0, +50.0, +25.0, -12.5].
- Translation L2 norms by held-out scene: [0.549300, 0.542596, 0.542593, 0.559898, 0.546588, 0.544304, 0.549450, 0.542864, 0.543304, 0.550243, 0.543634, 0.543540, 0.542150, 0.544830].

### gpt-image-2

- reference_baseline: painter recalls (%) [57.1, 92.9, 21.4, 100.0]; top ties 0; zero queries 0; mean margin 0.048361.
- common_translation: painter recalls (%) [75.0, 78.6, 53.6, 100.0]; top ties 0; zero queries 0; mean margin 0.067219.
- generated_prototype: painter recalls (%) [100.0, 92.9, 85.7, 100.0]; top ties 0; zero queries 0; mean margin 0.090467.
- paired_translation_vs_baseline, scene differences (pp): [-12.5, +0.0, +12.5, +12.5, -12.5, +12.5, +12.5, +12.5, +0.0, +12.5, +37.5, +25.0, +12.5, +0.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +25.0, +25.0, +25.0, +25.0, +37.5, +12.5, +62.5, -12.5, +25.0, +37.5, +37.5, +37.5, +12.5].
- Translation L2 norms by held-out scene: [0.469455, 0.468682, 0.470144, 0.486365, 0.469398, 0.468708, 0.468413, 0.472206, 0.469607, 0.472296, 0.473761, 0.467842, 0.470653, 0.467896].

### gpt-image-2.5-flare

- reference_baseline: painter recalls (%) [28.6, 96.4, 10.7, 100.0]; top ties 0; zero queries 0; mean margin 0.024649.
- common_translation: painter recalls (%) [53.6, 78.6, 25.0, 100.0]; top ties 0; zero queries 0; mean margin 0.045961.
- generated_prototype: painter recalls (%) [100.0, 89.3, 82.1, 100.0]; top ties 0; zero queries 0; mean margin 0.082518.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +0.0, +12.5, -12.5, -12.5, +0.0, +12.5, +0.0, +25.0, +12.5, +0.0, +25.0, +25.0, -12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+37.5, +25.0, +25.0, +12.5, +37.5, +50.0, +50.0, +37.5, +50.0, +37.5, +25.0, +50.0, +37.5, +0.0].
- Translation L2 norms by held-out scene: [0.555492, 0.558028, 0.556262, 0.564420, 0.553914, 0.555353, 0.556243, 0.552858, 0.557113, 0.551973, 0.559679, 0.553340, 0.555227, 0.553831].

### gpt-image-2.5-sunburst

- reference_baseline: painter recalls (%) [14.3, 100.0, 14.3, 100.0]; top ties 0; zero queries 0; mean margin 0.033400.
- common_translation: painter recalls (%) [57.1, 75.0, 21.4, 100.0]; top ties 0; zero queries 0; mean margin 0.050818.
- generated_prototype: painter recalls (%) [89.3, 89.3, 82.1, 100.0]; top ties 0; zero queries 0; mean margin 0.094276.
- paired_translation_vs_baseline, scene differences (pp): [+25.0, -12.5, +0.0, +12.5, -12.5, +12.5, +0.0, -12.5, +25.0, +0.0, +25.0, +25.0, +12.5, -12.5].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+25.0, +25.0, +12.5, +12.5, +25.0, +50.0, +50.0, +25.0, +50.0, +37.5, +50.0, +37.5, +50.0, +12.5].
- Translation L2 norms by held-out scene: [0.514913, 0.517977, 0.513861, 0.525107, 0.513476, 0.512673, 0.515416, 0.512530, 0.517196, 0.512300, 0.519531, 0.512006, 0.513283, 0.511665].

### google/gemini-3.1-flash-image

- reference_baseline: painter recalls (%) [0.0, 32.1, 46.4, 100.0]; top ties 0; zero queries 0; mean margin 0.017164.
- common_translation: painter recalls (%) [64.3, 46.4, 39.3, 92.9]; top ties 0; zero queries 0; mean margin 0.020629.
- generated_prototype: painter recalls (%) [75.0, 50.0, 75.0, 100.0]; top ties 0; zero queries 0; mean margin 0.053919.
- paired_translation_vs_baseline, scene differences (pp): [+0.0, +12.5, +25.0, +12.5, +0.0, +0.0, +12.5, +0.0, +50.0, +25.0, +37.5, +12.5, +12.5, +25.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [-12.5, +12.5, +37.5, +25.0, +25.0, +12.5, +62.5, +12.5, +50.0, +50.0, +62.5, +12.5, +25.0, +50.0].
- Translation L2 norms by held-out scene: [0.611708, 0.599259, 0.601865, 0.614362, 0.603087, 0.601505, 0.607011, 0.597182, 0.608996, 0.603759, 0.615004, 0.603035, 0.601744, 0.605477].

### black-forest-labs/flux.2-max

- reference_baseline: painter recalls (%) [0.0, 17.9, 89.3, 64.3]; top ties 0; zero queries 0; mean margin -0.014541.
- common_translation: painter recalls (%) [42.9, 53.6, 39.3, 92.9]; top ties 0; zero queries 0; mean margin 0.025335.
- generated_prototype: painter recalls (%) [78.6, 60.7, 64.3, 96.4]; top ties 0; zero queries 0; mean margin 0.047835.
- paired_translation_vs_baseline, scene differences (pp): [+37.5, +0.0, +37.5, +0.0, +12.5, +25.0, +0.0, +12.5, +12.5, -12.5, +25.0, +12.5, +12.5, +25.0].
- paired_generated_prototype_vs_baseline, scene differences (pp): [+37.5, +37.5, +50.0, +12.5, +37.5, +62.5, +62.5, +37.5, +12.5, +0.0, +25.0, +37.5, +12.5, +25.0].
- Translation L2 norms by held-out scene: [0.528732, 0.521318, 0.520810, 0.539209, 0.521891, 0.520492, 0.523610, 0.517613, 0.525780, 0.520553, 0.524478, 0.517879, 0.517104, 0.521829].

## Replay

```sh
uv run --locked python -m latent_art_bench.painter_prototype_transfer_v1 check --execute-real
```

Improved prompt-name recovery would not establish physical authorship, human fidelity, validity of pooled contrast error, an unwanted common painting effect, unseen-artist generalization, or independence from service drift. CLIP/CSD training overlap is unknown and the encoders are related. Every adverse outcome is retained.
