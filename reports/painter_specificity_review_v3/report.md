# Retrospective direct-naming and scene-stability diagnostics

This is a post-result analysis, not a preregistration. The full-frame named-minus-generic shared fractions had already been inspected before the plan was written. Existing scientific files and results are preserved.

## Estimands and limits

Each arm is averaged over scenes within repeat before taking cross-repeat products. Common = 4 times the cross-product of the four-name mean shifts; specific = the summed cross-products of departures from those shifts. Their sum is total squared change. Changing the common baseline leaves the specific component unchanged. Fractions use common/total only for positive totals; signed components and unbounded fractions are retained.

Let g = generic minus free, n = mean named minus generic, and c = mean named minus free, for each repeat. The exact vector identity is c = g+n. Thus 4<c1,c2> = 4<g1,g2> + 4<n1,n2> + 4(<g1,n2>+<n1,g2>). The final signed term is an algebraic interaction, not a causal factorial interaction. Squared generic and naming contributions cannot simply be added.

Deletion ranges recompute the full statistic after omitting each scene, holding the finite reference and scaler fixed. They are sensitivity ranges, not confidence intervals. Cross-repeat noise correction requires stable conditional means and independent mean-zero repeat errors; it does not verify service independence. The finite reference includes subject and capture differences. Neither pair alignment nor these feature shifts validate perceptual style. Square windows change content and are not an independent replication. No new tests or image generation were added.

## Full Frame

Shared fractions and deletion ranges are percentages. Pair beta uses the corresponding finite-reference Monet-minus-Sisley direction.

| Configuration | Named-free shared % [deletion range] | Named-generic shared % [deletion range] | Monet-Sisley beta [deletion range] |
|---|---:|---:|---:|
| GPT Image 1 | 82.5476 [79.4389, 83.9778] | 71.3157 [70.4194, 72.2924] | 0.0736 [0.0143, 0.1291] |
| GPT Image 2 | 85.7860 [85.0273, 86.3839] | 70.9236 [69.9885, 72.1352] | 0.4018 [0.3591, 0.4447] |
| GPT Image 2.5 Flare | 84.7817 [83.5686, 85.7929] | 71.1154 [69.8284, 72.2627] | -0.0105 [-0.0193, 0.0200] |
| GPT Image 2.5 Sunburst | 83.8744 [82.7176, 84.6545] | 66.6756 [65.9125, 67.6577] | -0.2494 [-0.2794, -0.2140] |
| Nano Banana 2 | 88.0911 [87.4223, 89.0213] | 69.1271 [66.8298, 70.9415] | -0.0437 [-0.1064, 0.0067] |
| FLUX.2 Max | 95.7106 [94.9791, 96.2207] | 88.3905 [86.1194, 90.2042] | 0.1286 [0.0663, 0.1776] |

Signed squared-change terms in standardized feature units:

| Configuration | Generic common G | Additional naming common N | Interaction I | Combined common C=G+N+I | Specific B |
|---|---:|---:|---:|---:|---:|
| GPT Image 1 | 29.8121 | 31.1219 | -1.7269 | 59.2072 | 12.5177 |
| GPT Image 2 | 37.1754 | 29.4498 | 6.2420 | 72.8673 | 12.0735 |
| GPT Image 2.5 Flare | 23.7137 | 29.5106 | 13.5512 | 66.7754 | 11.9862 |
| GPT Image 2.5 Sunburst | 18.1937 | 23.4850 | 19.3733 | 61.0520 | 11.7378 |
| Nano Banana 2 | 7.1912 | 8.0369 | 11.3229 | 26.5510 | 3.5894 |
| FLUX.2 Max | 22.3715 | 31.5897 | 38.6191 | 92.5803 | 4.1491 |

## Central Square

Shared fractions and deletion ranges are percentages. Pair beta uses the corresponding finite-reference Monet-minus-Sisley direction.

| Configuration | Named-free shared % [deletion range] | Named-generic shared % [deletion range] | Monet-Sisley beta [deletion range] |
|---|---:|---:|---:|
| GPT Image 1 | 82.5476 [79.4389, 83.9778] | 71.3157 [70.4194, 72.2924] | 0.0384 [-0.0164, 0.0960] |
| GPT Image 2 | 85.7860 [85.0273, 86.3839] | 70.9236 [69.9885, 72.1352] | 0.4077 [0.3646, 0.4500] |
| GPT Image 2.5 Flare | 84.7817 [83.5686, 85.7929] | 71.1154 [69.8284, 72.2627] | 0.0116 [0.0019, 0.0414] |
| GPT Image 2.5 Sunburst | 83.8744 [82.7176, 84.6545] | 66.6756 [65.9125, 67.6577] | -0.1850 [-0.2160, -0.1519] |
| Nano Banana 2 | 88.0911 [87.4223, 89.0213] | 69.1271 [66.8298, 70.9415] | -0.0172 [-0.0779, 0.0294] |
| FLUX.2 Max | 95.7106 [94.9791, 96.2207] | 88.3905 [86.1194, 90.2042] | 0.1318 [0.0616, 0.1838] |

Signed squared-change terms in standardized feature units:

| Configuration | Generic common G | Additional naming common N | Interaction I | Combined common C=G+N+I | Specific B |
|---|---:|---:|---:|---:|---:|
| GPT Image 1 | 29.8121 | 31.1219 | -1.7269 | 59.2072 | 12.5177 |
| GPT Image 2 | 37.1754 | 29.4498 | 6.2420 | 72.8673 | 12.0735 |
| GPT Image 2.5 Flare | 23.7137 | 29.5106 | 13.5512 | 66.7754 | 11.9862 |
| GPT Image 2.5 Sunburst | 18.1937 | 23.4850 | 19.3733 | 61.0520 | 11.7378 |
| Nano Banana 2 | 7.1912 | 8.0369 | 11.3229 | 26.5510 | 3.5894 |
| FLUX.2 Max | 22.3715 | 31.5897 | 38.6191 | 92.5803 | 4.1491 |

## Replay and input bindings

All per-scene deletions, pair summaries, common vectors and identity residuals are retained in `analysis.json`. The commands below are offline:

```sh
uv run --locked pytest -q tests/painter_specificity_review_v3
uv run --locked python -m latent_art_bench.painter_specificity_review_v3 check
```

SHA-256 bindings (including the plan, implementation and analytical tests):

| Path | SHA-256 |
|---|---|
| `data/manifests/painter_feature_generation_v2/pfg2-frame-20260905/frame.jsonl` | `43c71972635421645b276051feaefc62ee6845d3807fcad352aaa72926e9bed2` |
| `data/manifests/painter_feature_generation_v2/pfg2-method-20260905/confirmation_features.jsonl` | `01cc5167c09b88eab6a86885b72040f76fc8a7ca8a62acd56d85a8b16b2f7717` |
| `data/manifests/painter_feature_generation_v2/pfg2-method-20260905/scaler.json` | `71f511235081dfc1e9846976320c69477bcbd04dd43fc9a2e271f7b0375497b9` |
| `data/manifests/painter_feature_generation_v2/pfg2-renderings-r2-20260905/acquisitions.jsonl` | `3933e1627a0e7182baf899917cf651530f86c04b8e92b0312f7ada15dae98f5e` |
| `data/manifests/painter_specificity_measurement_v1/psmv1-20260911/freeze.json` | `c6c89dd1fdca14bb47a20dfb761c224176b8507acf204772bb11164b689ba571` |
| `data/manifests/painter_specificity_reference_v1/psrv1-20260911/freeze.json` | `662947f7c0758de6b315fb44752ba5b080cb4c2eee6b79313a37f00c4ee09523` |
| `data/manifests/painter_specificity_v1/openai_provider_quotes.json` | `afc7da39c3890858484a5ee152e550cb2fd907d77c7e982038b354e4a62fef92` |
| `data/manifests/painter_specificity_v1/provider_quotes.json` | `ba4473c151a89bed18f04831bff9c376d4ae467489d598930a93a2386d5605f7` |
| `data/manifests/painter_specificity_v1/psv1-20260910/collection.json` | `5e105c1f1ccb8af9a43c29a9121dc392297d45228470a7329cba3696aaccfca9` |
| `data/manifests/painter_specificity_v2/medium_cost_pilots.jsonl` | `ddb78ef482917f1f31564ead9d447e81406d01a4d58bd00f9aa1d6ee93191adb` |
| `data/manifests/painter_specificity_v2/pilot.jsonl` | `26fbb3e920e02453c4e6c9748130637bd09fa301b7595cce41af03c0d14a7280` |
| `data/manifests/painter_specificity_v2/psv2-20260911/collection.json` | `3491468b0dc6875d28e530595341d2a5a659a5aec175e5f6f7999f05b5851480` |
| `data/manifests/painter_specificity_v2/psv2-20260911/freeze.json` | `2f32de5182357e960eb4520b45e90f23e6fe812168679cba9072a435675cdf27` |
| `data/manifests/painter_specificity_v2/psv2-20260911/measurement_receipt.json` | `e71a1a7c64ba6d443e899f7913d4e97ee5db4e15cda132955fd2b41243d31c06` |
| `data/manifests/painter_specificity_v2/psv2-20260911/measurements.jsonl` | `5db95709f48a25e31ef212b588c2aa3e0f7af4fb5dbaf413cfc16690de60cac1` |
| `data/manifests/painter_specificity_v2/psv2-20260911/reference_windows.jsonl` | `2fa580f51f63c2d15aa9cae058b2c073939f029224cc90fba96243f2efb7c42b` |
| `data/manifests/painter_specificity_v2/psv2-20260911/requests.jsonl` | `0aa60f491be08dbd48f1f018e225b22bcae2aacd724abf3371a6312d59acc679` |
| `pyproject.toml` | `5eb878e4cd9607f6dde074f4a341d54889f6405d65621821cdc4beb6713a2bf8` |
| `src/latent_art_bench/painter_distribution_study_v1/discovery.py` | `211fe3d93077aec9861915b58fa57b2e8954dd17cdc291fdc1e5d33072d1d0eb` |
| `src/latent_art_bench/painter_feature_generation_v2/features.py` | `b295c2de1a8501e8ab335d88ed56ab8f2dc8b3ca704141b92e02ef586d48d172` |
| `src/latent_art_bench/painter_feature_generation_v2/statistics.py` | `20830e7a90bc49666f0937ef7bc2ae3f11206f986c72eb8f80ad30cc24fcdaa8` |
| `src/latent_art_bench/painter_specificity_measurement_v1/workflow.py` | `7ce26e70d7db3768a80764405c3c764342c94a3dee0fc18fbbdc6664dbbe2d07` |
| `src/latent_art_bench/painter_specificity_reference_v1/analysis.py` | `505cee3dc82907b6b543d974ccd10c0e71f64237a577d948e7c2db6f563c4e53` |
| `src/latent_art_bench/painter_specificity_review_v3.py` | `0c7752720ee24981475a33c6460b49c2311d7fa856cf326e90bbcf03530ed8cc` |
| `src/latent_art_bench/painter_specificity_v1/__init__.py` | `5b6b6fdec0b62d962c14323a847c3d76b40b02232745296bd469bc4bd3810fc9` |
| `src/latent_art_bench/painter_specificity_v1/analysis.py` | `ac5df333a8768dc66b84be0d2c1403f9dba3b229f101de8d65ad6cdb27bce06c` |
| `src/latent_art_bench/painter_specificity_v1/study.py` | `e2da0d39e65f7f069c3b05cc959b0ee7dfd771944cabf7966baad573d6d84688` |
| `src/latent_art_bench/painter_specificity_v1/workflow.py` | `504c87bf7d4161d537d0cdf59f2015a42e2a63224ebab83e3a1db1c9927fc018` |
| `src/latent_art_bench/painter_specificity_v2/__init__.py` | `43e1d704341f2a29df5930bae839ffb4870e9b399e9be8fb7c268dea1f4024f5` |
| `src/latent_art_bench/painter_specificity_v2/analysis.py` | `bdfe4691d4b956bceab2b3a286b415df60a762c5a12fdbafcdc3d85818279b7e` |
| `src/latent_art_bench/painter_specificity_v2/study.py` | `cfd1c0ea94951db592945745137a609400f31d2c1b12a56da5bc1b9feb19e46b` |
| `src/latent_art_bench/painter_specificity_v2/workflow.py` | `d7a2cf481115e95bf99fe950f05b8a0dc421c180882494fa1b3cfa6733c6358e` |
| `studies/painter_specificity_measurement_v1/CORRECTION.md` | `b30623fb8889b5e8ad86fb694822d2a6bf24b050d8beff79c51a120c33a93fe9` |
| `studies/painter_specificity_reference_v1/PROTOCOL.md` | `b8f74092a7fa5566b3b777344e097b1cb1e2ee63e3c94d2a78c2ce6b565b9090` |
| `studies/painter_specificity_review_v3/PLAN.md` | `57ca293a590dc52768b34e516445ae462e9c3cd03bd949b0fda4c188f506d70a` |
| `studies/painter_specificity_v1/PROTOCOL.md` | `292514599bd88f06c011b7fc8f1354a4c274335c5dc79b4a68b35ab51c63c5dc` |
| `studies/painter_specificity_v2/DECISION.md` | `88b865f3e674a018640e7cb307ffd287549917f5ba27d197daa545ae589838a5` |
| `studies/painter_specificity_v2/PROTOCOL.md` | `ce374c9d56e4d5bc5bf1cbbc44abd931516820321839b9768260741528ca69b2` |
| `tests/painter_specificity_measurement_v1/test_membership.py` | `0c86e5bedc321300846265bfcbcf2b4580f1b71c9f1127c6abcc7981190b2367` |
| `tests/painter_specificity_reference_v1/test_reference.py` | `f495215aadbdf4f21cae250dae1ba5362c5e6848bfc6e13152dd4c18c017442c` |
| `tests/painter_specificity_review_v3/test_decomposition.py` | `22bc4a476e0502bb1b4e237fc6ccc358d248562130b5802eaa85063492c23709` |
| `tests/painter_specificity_v1/test_analysis.py` | `8577989bcf88574832d8fadf1e76e889f234cbb4a47870481eb7560393bad43e` |
| `tests/painter_specificity_v2/test_routes.py` | `fce946d3fc1cb01d7d4cff0ec47434eaf6218eafb75d22b901878102e7f3dd20` |
| `uv.lock` | `d78b12a1ae92d586b9945d4bf50ed4398300780c462867e634abaab78941eb5a` |
