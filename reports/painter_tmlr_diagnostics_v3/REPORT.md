# TMLR revision diagnostics, version 3

Retrospective analysis under
[the plan](../../studies/painter_tmlr_diagnostics_v3/PLAN.md).

## Genuine-painting controls with distinct works (mean error D, share above 1)

- hand31: pooled_real 0.125 (5.1% > 1); class_real_pooled_target 0.185 (9.1% > 1); class_real_class_target 0.328 (6.6% > 1)
- clip: pooled_real 0.064 (0.0% > 1); class_real_pooled_target 0.203 (0.0% > 1); class_real_class_target 0.216 (0.0% > 1)
- csd: pooled_real 0.060 (0.0% > 1); class_real_pooled_target 0.139 (0.0% > 1); class_real_class_target 0.193 (0.0% > 1)

## Embedding agreement

- clip GPT Image 1: beta 0.527, D 0.847 [0.757, 0.934], P(D<1) joint 0.999, normalized-prototype share 0.746
- clip GPT Image 2: beta 0.770, D 1.061 [0.923, 1.192], P(D<1) joint 0.210, normalized-prototype share 0.734
- clip GPT Image 2.5 Flare: beta 0.558, D 1.057 [0.962, 1.152], P(D<1) joint 0.144, normalized-prototype share 0.790
- clip GPT Image 2.5 Sunburst: beta 0.651, D 1.136 [1.058, 1.213], P(D<1) joint 0.001, normalized-prototype share 0.780
- clip Nano Banana 2: beta 0.523, D 1.078 [0.943, 1.228], P(D<1) joint 0.158, normalized-prototype share 0.839
- clip FLUX.2 Max: beta 0.438, D 1.058 [0.950, 1.165], P(D<1) joint 0.164, normalized-prototype share 0.819
- csd GPT Image 1: beta 0.728, D 0.735 [0.644, 0.829], P(D<1) joint 1.000, normalized-prototype share 0.728
- csd GPT Image 2: beta 0.936, D 0.741 [0.666, 0.822], P(D<1) joint 1.000, normalized-prototype share 0.547
- csd GPT Image 2.5 Flare: beta 0.804, D 0.819 [0.777, 0.862], P(D<1) joint 1.000, normalized-prototype share 0.654
- csd GPT Image 2.5 Sunburst: beta 0.860, D 0.944 [0.866, 1.024], P(D<1) joint 0.807, normalized-prototype share 0.677
- csd Nano Banana 2: beta 0.526, D 0.999 [0.876, 1.128], P(D<1) joint 0.513, normalized-prototype share 0.796
- csd FLUX.2 Max: beta 0.598, D 0.714 [0.620, 0.801], P(D<1) joint 1.000, normalized-prototype share 0.777

## Family contrasts (mean over configurations)

- texture-color: -0.061 [-0.135, -0.020], below zero 99.7%
- texture-spatial: -0.034 [-0.136, 0.103], below zero 65.2%
- color-spatial: 0.027 [-0.085, 0.182], below zero 27.9%
- dropped draws: 35
