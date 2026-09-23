# Primary-D cross-repeat covariance sensitivity

Retrospective point-estimate scenarios for the complete retained panel. The same hypothetical trace correlation rho is applied to all six configurations. No correlation is estimated from these data.

Repeat differences estimate q = V − C, with marginal noise power V and cross-repeat covariance trace C, normalized by H. Assuming rho = C/V gives bias C = rho q/(1 − rho). The scenario curve subtracts this implied bias from D.

## All configuration scenarios

| Configuration | rho | Original D | q | Implied bias | Adjusted D | Negative |
|---|---:|---:|---:|---:|---:|---|
| GPT Image 1 | 0.00 | 1.572416 | 2.023823 | 0.000000 | 1.572416 | no |
| GPT Image 1 | 0.10 | 1.572416 | 2.023823 | 0.224869 | 1.347547 | no |
| GPT Image 1 | 0.25 | 1.572416 | 2.023823 | 0.674608 | 0.897808 | no |
| GPT Image 1 | 0.50 | 1.572416 | 2.023823 | 2.023823 | -0.451407 | yes |
| GPT Image 1 | 0.75 | 1.572416 | 2.023823 | 6.071469 | -4.499053 | yes |
| GPT Image 2 | 0.00 | 1.225931 | 0.959822 | 0.000000 | 1.225931 | no |
| GPT Image 2 | 0.10 | 1.225931 | 0.959822 | 0.106647 | 1.119284 | no |
| GPT Image 2 | 0.25 | 1.225931 | 0.959822 | 0.319941 | 0.905990 | no |
| GPT Image 2 | 0.50 | 1.225931 | 0.959822 | 0.959822 | 0.266108 | no |
| GPT Image 2 | 0.75 | 1.225931 | 0.959822 | 2.879467 | -1.653536 | yes |
| GPT Image 2.5 Flare | 0.00 | 1.737719 | 0.423596 | 0.000000 | 1.737719 | no |
| GPT Image 2.5 Flare | 0.10 | 1.737719 | 0.423596 | 0.047066 | 1.690653 | no |
| GPT Image 2.5 Flare | 0.25 | 1.737719 | 0.423596 | 0.141199 | 1.596520 | no |
| GPT Image 2.5 Flare | 0.50 | 1.737719 | 0.423596 | 0.423596 | 1.314123 | no |
| GPT Image 2.5 Flare | 0.75 | 1.737719 | 0.423596 | 1.270788 | 0.466931 | no |
| GPT Image 2.5 Sunburst | 0.00 | 1.641417 | 0.582533 | 0.000000 | 1.641417 | no |
| GPT Image 2.5 Sunburst | 0.10 | 1.641417 | 0.582533 | 0.064726 | 1.576691 | no |
| GPT Image 2.5 Sunburst | 0.25 | 1.641417 | 0.582533 | 0.194178 | 1.447240 | no |
| GPT Image 2.5 Sunburst | 0.50 | 1.641417 | 0.582533 | 0.582533 | 1.058884 | no |
| GPT Image 2.5 Sunburst | 0.75 | 1.641417 | 0.582533 | 1.747598 | -0.106181 | yes |
| Nano Banana 2 | 0.00 | 1.109451 | 2.595883 | 0.000000 | 1.109451 | no |
| Nano Banana 2 | 0.10 | 1.109451 | 2.595883 | 0.288431 | 0.821020 | no |
| Nano Banana 2 | 0.25 | 1.109451 | 2.595883 | 0.865294 | 0.244157 | no |
| Nano Banana 2 | 0.50 | 1.109451 | 2.595883 | 2.595883 | -1.486432 | yes |
| Nano Banana 2 | 0.75 | 1.109451 | 2.595883 | 7.787649 | -6.678198 | yes |
| FLUX.2 Max | 0.00 | 0.800928 | 1.674010 | 0.000000 | 0.800928 | no |
| FLUX.2 Max | 0.10 | 0.800928 | 1.674010 | 0.186001 | 0.614927 | no |
| FLUX.2 Max | 0.25 | 0.800928 | 1.674010 | 0.558003 | 0.242925 | no |
| FLUX.2 Max | 0.50 | 0.800928 | 1.674010 | 1.674010 | -0.873082 | yes |
| FLUX.2 Max | 0.75 | 0.800928 | 1.674010 | 5.022030 | -4.221101 | yes |

## All paired point differences and analytic crossings

Differences are first minus second. Thresholds use unrounded values, and refer only to point ordering under the common-rho assumption. They are not thresholds for statistical significance. A crossing can lie above the displayed grid.

| Pair | Delta q | rho=0 | rho=.10 | rho=.25 | rho=.50 | rho=.75 | Crossing rho | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| GPT Image 1 minus GPT Image 2 | 1.064001 | 0.346485 | 0.228263 | -0.008182 | -0.717515 | -2.845517 | 0.245650 | positive_interior_crossing |
| GPT Image 1 minus GPT Image 2.5 Flare | 1.600227 | -0.165303 | -0.343106 | -0.698712 | -1.765530 | -4.965984 | — | no_positive_interior_crossing |
| GPT Image 1 minus GPT Image 2.5 Sunburst | 1.441290 | -0.069001 | -0.229144 | -0.549431 | -1.510291 | -4.392872 | — | no_positive_interior_crossing |
| GPT Image 1 minus Nano Banana 2 | -0.572060 | 0.462965 | 0.526527 | 0.653652 | 1.035025 | 2.179145 | — | no_positive_interior_crossing |
| GPT Image 1 minus FLUX.2 Max | 0.349813 | 0.771488 | 0.732620 | 0.654883 | 0.421675 | -0.277952 | 0.688029 | positive_interior_crossing |
| GPT Image 2 minus GPT Image 2.5 Flare | 0.536227 | -0.511788 | -0.571369 | -0.690530 | -1.048015 | -2.120468 | — | no_positive_interior_crossing |
| GPT Image 2 minus GPT Image 2.5 Sunburst | 0.377290 | -0.415486 | -0.457407 | -0.541249 | -0.792776 | -1.547355 | — | no_positive_interior_crossing |
| GPT Image 2 minus Nano Banana 2 | -1.636061 | 0.116480 | 0.298264 | 0.661834 | 1.752541 | 5.024662 | — | no_positive_interior_crossing |
| GPT Image 2 minus FLUX.2 Max | -0.714187 | 0.425003 | 0.504357 | 0.663065 | 1.139190 | 2.567565 | — | no_positive_interior_crossing |
| GPT Image 2.5 Flare minus GPT Image 2.5 Sunburst | -0.158937 | 0.096302 | 0.113962 | 0.149281 | 0.255239 | 0.573113 | — | no_positive_interior_crossing |
| GPT Image 2.5 Flare minus Nano Banana 2 | -2.172287 | 0.628268 | 0.869633 | 1.352364 | 2.800555 | 7.145129 | — | no_positive_interior_crossing |
| GPT Image 2.5 Flare minus FLUX.2 Max | -1.250414 | 0.936791 | 1.075726 | 1.353596 | 2.187205 | 4.688033 | — | no_positive_interior_crossing |
| GPT Image 2.5 Sunburst minus Nano Banana 2 | -2.013350 | 0.531966 | 0.755672 | 1.203083 | 2.545316 | 6.572017 | — | no_positive_interior_crossing |
| GPT Image 2.5 Sunburst minus FLUX.2 Max | -1.091477 | 0.840489 | 0.961764 | 1.204315 | 1.931966 | 4.114920 | — | no_positive_interior_crossing |
| Nano Banana 2 minus FLUX.2 Max | 0.921873 | 0.308523 | 0.206092 | 0.001232 | -0.613350 | -2.457097 | 0.250751 | positive_interior_crossing |

## Interpretation limits

Equal trace correlation allows different covariance biases when q differs. Equal normalized covariance bias would instead shift all D values equally and preserve all paired differences. Model-specific correlations are outside this fixed scenario.

These calculations assume stable conditional means and mean-zero errors with finite second moments. Two repeats do not identify covariance: a state shared by both repeats disappears from their difference, and no finite upper covariance bound follows from q alone. The grid is not a plausible-range estimate or a robustness guarantee. A state conditioned on as fixed changes the mean target relative to a state averaged over new collection sessions.

Negative adjusted estimates are retained and flagged; they are not physical negative squared errors or formal rejections of an assumed rho. Uncertainty in q and its association with D are not quantified. No intervals are shifted or recomputed, and no significance, coverage, or correct-ordering claim is made. This analysis does not address mean drift, beta uncertainty, shared fractions, learned representations, or reference validity.

## Replay

`uv run --locked python -m latent_art_bench.painter_repeat_covariance_v1 check --execute-real`

The create-once input binding and analysis JSON retain all source/input hashes, 84 per-scene D and q values, every configuration/grid value, all 15 paired curves, unrounded crossings and implied covariance biases. Primary-D and review-v2 direct-q values are checked against preserved results. Input binding SHA-256: `43a44d769700b1a8fd0122d9a4e4d8e34726c121313641d892aa85b843bf2346`.
