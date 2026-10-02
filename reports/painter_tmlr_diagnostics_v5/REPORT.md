# TMLR revision diagnostics, version 5

Retrospective analysis under
[the plan](../../studies/painter_tmlr_diagnostics_v5/PLAN.md).

## Agreement, direction and repeat dependence

- hand31 GPT Image 1: beta 0.938, Q 2.449, alignment 0.600, D 1.572 [1.129, 2.016], held-out 0.645, along 0.029, off 1.543, repeat noise 2.024, rho at D=1 0.220
- hand31 GPT Image 2: beta 0.999, Q 2.223, alignment 0.670, D 1.226 [0.957, 1.495], held-out 0.554, along -0.003, off 1.229, repeat noise 0.960, rho at D=1 0.191
- hand31 GPT Image 2.5 Flare: beta 0.772, Q 2.281, alignment 0.511, D 1.738 [1.477, 1.999], held-out 0.741, along 0.054, off 1.683, repeat noise 0.424, rho at D=1 0.635
- hand31 GPT Image 2.5 Sunburst: beta 0.824, Q 2.289, alignment 0.545, D 1.641 [1.312, 1.971], held-out 0.706, along 0.044, off 1.598, repeat noise 0.583, rho at D=1 0.524
- hand31 Nano Banana 2: beta 0.442, Q 0.994, alignment 0.444, D 1.109 [0.582, 1.636], held-out 0.832, along 0.317, off 0.793, repeat noise 2.596, rho at D=1 0.040
- hand31 FLUX.2 Max: beta 0.470, Q 0.741, alignment 0.546, D 0.801 [0.586, 1.016], held-out 0.714, along 0.304, off 0.497, repeat noise 1.674, rho at D=1 n/a

- clip GPT Image 1: beta 0.527, Q 0.900, alignment 0.555, D 0.847 [0.746, 0.947], held-out 0.694, along 0.231, off 0.616, repeat noise 1.200, rho at D=1 n/a
- clip GPT Image 2: beta 0.770, Q 1.602, alignment 0.609, D 1.061 [0.905, 1.217], held-out 0.631, along 0.057, off 1.004, repeat noise 1.133, rho at D=1 0.051
- clip GPT Image 2.5 Flare: beta 0.558, Q 1.173, alignment 0.515, D 1.057 [0.947, 1.167], held-out 0.735, along 0.201, off 0.856, repeat noise 0.803, rho at D=1 0.066
- clip GPT Image 2.5 Sunburst: beta 0.651, Q 1.439, alignment 0.543, D 1.136 [1.047, 1.225], held-out 0.705, along 0.129, off 1.007, repeat noise 0.834, rho at D=1 0.140
- clip Nano Banana 2: beta 0.523, Q 1.124, alignment 0.493, D 1.078 [0.918, 1.238], held-out 0.759, along 0.230, off 0.848, repeat noise 1.587, rho at D=1 0.047
- clip FLUX.2 Max: beta 0.438, Q 0.933, alignment 0.453, D 1.058 [0.935, 1.182], held-out 0.796, along 0.316, off 0.743, repeat noise 1.777, rho at D=1 0.032

- csd GPT Image 1: beta 0.728, Q 1.192, alignment 0.667, D 0.735 [0.629, 0.842], held-out 0.557, along 0.085, off 0.650, repeat noise 0.726, rho at D=1 n/a
- csd GPT Image 2: beta 0.936, Q 1.612, alignment 0.737, D 0.741 [0.652, 0.830], held-out 0.458, along 0.005, off 0.736, repeat noise 0.543, rho at D=1 n/a
- csd GPT Image 2.5 Flare: beta 0.804, Q 1.428, alignment 0.673, D 0.819 [0.771, 0.867], held-out 0.547, along 0.041, off 0.778, repeat noise 0.356, rho at D=1 n/a
- csd GPT Image 2.5 Sunburst: beta 0.860, Q 1.664, alignment 0.666, D 0.944 [0.852, 1.037], held-out 0.556, along 0.024, off 0.920, repeat noise 0.417, rho at D=1 n/a
- csd Nano Banana 2: beta 0.526, Q 1.051, alignment 0.513, D 0.999 [0.850, 1.148], held-out 0.739, along 0.231, off 0.768, repeat noise 1.040, rho at D=1 n/a
- csd FLUX.2 Max: beta 0.598, Q 0.910, alignment 0.627, D 0.714 [0.609, 0.818], held-out 0.610, along 0.162, off 0.551, repeat noise 1.012, rho at D=1 n/a

## Best-configuration frequencies (scene resampling)

- hand31 alignment: gpt-image-2 0.980
- hand31 held_out_d: gpt-image-2 0.990
- hand31 d: black-forest-labs/flux.2-max 0.847
- clip alignment: gpt-image-2 0.997
- clip held_out_d: gpt-image-2 0.998
- clip d: gpt-image-1 0.993
- csd alignment: gpt-image-2 1.000
- csd held_out_d: gpt-image-2 1.000
- csd d: black-forest-labs/flux.2-max 0.479

## Spearman correlations

- alignment_recognition_clip: 0.943
- alignment_recognition_csd: 0.886
- alignment_hand31_clip: 0.657
- d_hand31_clip: -0.143
- alignment_hand31_csd: 0.600
- d_hand31_csd: 0.314
- alignment_clip_csd: 0.771
- d_clip_csd: 0.657

## Proximity across configurations

- clip corr_shared: 0.960 [0.908, 0.985], leave-one-out 0.915--0.986
- clip corr_specific: 0.401 [0.048, 0.619], leave-one-out 0.261--0.736
- clip variance_ratio: 10.819 [4.564, 29.284], leave-one-out 4.731--31.078
- csd corr_shared: 0.949 [0.792, 0.987], leave-one-out 0.836--0.979
- csd corr_specific: -0.646 [-0.846, -0.086], leave-one-out -0.847---0.320
- csd variance_ratio: 5.819 [2.532, 13.826], leave-one-out 2.983--8.871

## Distinct configurations (share of cells)

- hand31: Flare vs Sunburst 0.952; minimum over pairs 0.952
- clip: Flare vs Sunburst 0.917; minimum over pairs 0.917
- csd: Flare vs Sunburst 1.000; minimum over pairs 0.988
