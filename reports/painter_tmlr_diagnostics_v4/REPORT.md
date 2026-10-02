# TMLR revision diagnostics, version 4

Retrospective analysis under
[the plan](../../studies/painter_tmlr_diagnostics_v4/PLAN.md).

## Agreement on the 11 content-classed scenes (pooled vs class targets)

- 31 features GPT Image 1: pooled beta 0.923, D 1.557; class beta 0.776, D 1.366
- 31 features GPT Image 2: pooled beta 0.998, D 1.099; class beta 0.771, D 1.130
- 31 features GPT Image 2.5 Flare: pooled beta 0.774, D 1.726; class beta 0.638, D 1.539
- 31 features GPT Image 2.5 Sunburst: pooled beta 0.829, D 1.633; class beta 0.652, D 1.525
- 31 features Nano Banana 2: pooled beta 0.462, D 0.987; class beta 0.390, D 0.948
- 31 features FLUX.2 Max: pooled beta 0.480, D 0.750; class beta 0.390, D 0.786
- 31 features class-vs-pooled target distance / H 0.318; class spread / H 1.253

- CLIP GPT Image 1: pooled beta 0.515, D 0.886; class beta 0.450, D 0.904 [0.814, 0.985], P(D<1) 0.991
- CLIP GPT Image 2: pooled beta 0.757, D 1.067; class beta 0.648, D 1.091 [0.936, 1.235], P(D<1) 0.124
- CLIP GPT Image 2.5 Flare: pooled beta 0.551, D 1.059; class beta 0.472, D 1.074 [0.961, 1.183], P(D<1) 0.095
- CLIP GPT Image 2.5 Sunburst: pooled beta 0.638, D 1.163; class beta 0.532, D 1.200 [1.097, 1.298], P(D<1) 0.000
- CLIP Nano Banana 2: pooled beta 0.500, D 1.107; class beta 0.434, D 1.103 [0.962, 1.254], P(D<1) 0.082
- CLIP FLUX.2 Max: pooled beta 0.428, D 1.019; class beta 0.372, D 1.023 [0.925, 1.122], P(D<1) 0.317
- CLIP class-vs-pooled target distance / H 0.240; class spread / H 1.140

- CSD GPT Image 1: pooled beta 0.705, D 0.778; class beta 0.640, D 0.767 [0.680, 0.847], P(D<1) 1.000
- CSD GPT Image 2: pooled beta 0.926, D 0.750; class beta 0.826, D 0.759 [0.675, 0.851], P(D<1) 1.000
- CSD GPT Image 2.5 Flare: pooled beta 0.797, D 0.819; class beta 0.721, D 0.804 [0.736, 0.868], P(D<1) 1.000
- CSD GPT Image 2.5 Sunburst: pooled beta 0.851, D 0.933; class beta 0.755, D 0.930 [0.844, 1.027], P(D<1) 0.926
- CSD Nano Banana 2: pooled beta 0.491, D 0.976; class beta 0.437, D 0.971 [0.832, 1.118], P(D<1) 0.652
- CSD FLUX.2 Max: pooled beta 0.583, D 0.708; class beta 0.535, D 0.699 [0.591, 0.807], P(D<1) 1.000
- CSD class-vs-pooled target distance / H 0.169; class spread / H 1.135
