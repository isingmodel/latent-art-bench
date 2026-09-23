# Reference-calibrated selective attribution v1

Retrospective diagnostic using the fixed retained cohort. Standard abstention, not a new algorithm; no generated-image coverage guarantee under domain shift.

Input SHA-256: `f9d6b94e19d8004463f7b0524dd72865e22c18b0786cf48387cb9257e0528826`.

Primary setting: **csd/original/primary**. Joint descriptive usefulness criterion: **False**.

All eight settings, six configurations, four painters and 1,008 generated observations are retained. The gate's alpha is fixed at 0.10. Error concerns recorded prompt names, not perceptual fidelity or physical authorship.

The margin comparator uses the named query distribution to match coverage. Its numeric threshold is applied inclusively to controls, with ties retained. Control attribution rates do not establish visual misattribution.

## clip/original/primary

| Configuration | Coverage % | Baseline error % | Gate error % | Margin error % | Baseline−gate pp | Margin−gate pp |
|---|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 49.11 | 39.29 | 25.45 | 25.45 | 13.83 | 0.00 |
| gpt-image-2 | 63.39 | 31.25 | 21.13 | 19.72 | 10.12 | -1.41 |
| gpt-image-2.5-flare | 55.36 | 40.18 | 25.81 | 29.03 | 14.37 | 3.23 |
| gpt-image-2.5-sunburst | 52.68 | 41.07 | 18.64 | 22.03 | 22.43 | 3.39 |
| google/gemini-3.1-flash-image | 74.11 | 48.21 | 38.55 | 44.58 | 9.66 | 6.02 |
| black-forest-labs/flux.2-max | 70.54 | 58.93 | 56.96 | 55.70 | 1.97 | -1.27 |

Equal-configuration baseline−gate / margin−gate reductions (pp): 12.06 / 1.66.

Failed joint criteria: every_configuration_coverage_at_least_half. Missing means: none.

| Configuration | Free gate % | Free margin % | Generic gate % | Generic margin % | Gate accepted counts by painter |
|---|---:|---:|---:|---:|---|
| gpt-image-1 | 21.43 | 21.43 | 28.57 | 14.29 | 6, 13, 13, 23 |
| gpt-image-2 | 25.00 | 28.57 | 39.29 | 35.71 | 13, 15, 17, 26 |
| gpt-image-2.5-flare | 17.86 | 25.00 | 25.00 | 28.57 | 9, 16, 11, 26 |
| gpt-image-2.5-sunburst | 21.43 | 17.86 | 17.86 | 21.43 | 6, 12, 14, 27 |
| google/gemini-3.1-flash-image | 14.29 | 28.57 | 28.57 | 60.71 | 12, 23, 22, 26 |
| black-forest-labs/flux.2-max | 17.86 | 35.71 | 46.43 | 71.43 | 16, 24, 20, 19 |

Complete predictions, nonconformity scores, set memberships, painter risks/confusions, abstention reasons, numeric boundary ties and all scene-deletion records are retained in analysis.json. Undefined risks and means remain null; no configuration is dropped.

## clip/original/development

| Configuration | Coverage % | Baseline error % | Gate error % | Margin error % | Baseline−gate pp | Margin−gate pp |
|---|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 46.43 | 39.29 | 19.23 | 25.00 | 20.05 | 5.77 |
| gpt-image-2 | 51.79 | 35.71 | 18.97 | 17.24 | 16.75 | -1.72 |
| gpt-image-2.5-flare | 48.21 | 39.29 | 16.67 | 24.07 | 22.62 | 7.41 |
| gpt-image-2.5-sunburst | 48.21 | 39.29 | 22.22 | 25.93 | 17.06 | 3.70 |
| google/gemini-3.1-flash-image | 53.57 | 50.00 | 30.00 | 31.67 | 20.00 | 1.67 |
| black-forest-labs/flux.2-max | 48.21 | 58.93 | 51.85 | 51.85 | 7.08 | 0.00 |

Equal-configuration baseline−gate / margin−gate reductions (pp): 17.26 / 2.80.

Failed joint criteria: every_configuration_coverage_at_least_half. Missing means: none.

| Configuration | Free gate % | Free margin % | Generic gate % | Generic margin % | Gate accepted counts by painter |
|---|---:|---:|---:|---:|---|
| gpt-image-1 | 39.29 | 14.29 | 25.00 | 3.57 | 7, 9, 10, 26 |
| gpt-image-2 | 32.14 | 25.00 | 25.00 | 21.43 | 7, 13, 11, 27 |
| gpt-image-2.5-flare | 32.14 | 17.86 | 10.71 | 3.57 | 6, 11, 9, 28 |
| gpt-image-2.5-sunburst | 35.71 | 14.29 | 14.29 | 14.29 | 5, 10, 12, 27 |
| google/gemini-3.1-flash-image | 21.43 | 14.29 | 17.86 | 17.86 | 9, 14, 11, 26 |
| black-forest-labs/flux.2-max | 25.00 | 17.86 | 21.43 | 28.57 | 9, 14, 12, 19 |

Complete predictions, nonconformity scores, set memberships, painter risks/confusions, abstention reasons, numeric boundary ties and all scene-deletion records are retained in analysis.json. Undefined risks and means remain null; no configuration is dropped.

## clip/audited_region/primary

| Configuration | Coverage % | Baseline error % | Gate error % | Margin error % | Baseline−gate pp | Margin−gate pp |
|---|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 45.54 | 40.18 | 21.57 | 19.61 | 18.61 | -1.96 |
| gpt-image-2 | 61.61 | 30.36 | 18.84 | 17.39 | 11.52 | -1.45 |
| gpt-image-2.5-flare | 55.36 | 42.86 | 24.19 | 27.42 | 18.66 | 3.23 |
| gpt-image-2.5-sunburst | 50.89 | 40.18 | 15.79 | 17.54 | 24.39 | 1.75 |
| google/gemini-3.1-flash-image | 65.18 | 50.00 | 39.73 | 41.10 | 10.27 | 1.37 |
| black-forest-labs/flux.2-max | 65.18 | 59.82 | 56.16 | 54.79 | 3.66 | -1.37 |

Equal-configuration baseline−gate / margin−gate reductions (pp): 14.52 / 0.26.

Failed joint criteria: every_configuration_coverage_at_least_half. Missing means: none.

| Configuration | Free gate % | Free margin % | Generic gate % | Generic margin % | Gate accepted counts by painter |
|---|---:|---:|---:|---:|---|
| gpt-image-1 | 21.43 | 21.43 | 21.43 | 10.71 | 5, 10, 14, 22 |
| gpt-image-2 | 28.57 | 32.14 | 32.14 | 25.00 | 12, 14, 17, 26 |
| gpt-image-2.5-flare | 17.86 | 25.00 | 25.00 | 28.57 | 9, 16, 12, 25 |
| gpt-image-2.5-sunburst | 25.00 | 21.43 | 17.86 | 21.43 | 5, 11, 14, 27 |
| google/gemini-3.1-flash-image | 17.86 | 14.29 | 28.57 | 50.00 | 11, 20, 17, 25 |
| black-forest-labs/flux.2-max | 17.86 | 25.00 | 35.71 | 60.71 | 16, 22, 16, 19 |

Complete predictions, nonconformity scores, set memberships, painter risks/confusions, abstention reasons, numeric boundary ties and all scene-deletion records are retained in analysis.json. Undefined risks and means remain null; no configuration is dropped.

## clip/audited_region/development

| Configuration | Coverage % | Baseline error % | Gate error % | Margin error % | Baseline−gate pp | Margin−gate pp |
|---|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 45.54 | 41.07 | 19.61 | 25.49 | 21.46 | 5.88 |
| gpt-image-2 | 49.11 | 33.93 | 12.73 | 16.36 | 21.20 | 3.64 |
| gpt-image-2.5-flare | 47.32 | 36.61 | 16.98 | 22.64 | 19.63 | 5.66 |
| gpt-image-2.5-sunburst | 48.21 | 37.50 | 22.22 | 25.93 | 15.28 | 3.70 |
| google/gemini-3.1-flash-image | 50.00 | 49.11 | 26.79 | 28.57 | 22.32 | 1.79 |
| black-forest-labs/flux.2-max | 45.54 | 57.14 | 52.94 | 50.98 | 4.20 | -1.96 |

Equal-configuration baseline−gate / margin−gate reductions (pp): 17.35 / 3.12.

Failed joint criteria: every_configuration_coverage_at_least_half. Missing means: none.

| Configuration | Free gate % | Free margin % | Generic gate % | Generic margin % | Gate accepted counts by painter |
|---|---:|---:|---:|---:|---|
| gpt-image-1 | 32.14 | 14.29 | 17.86 | 3.57 | 7, 9, 9, 26 |
| gpt-image-2 | 35.71 | 21.43 | 25.00 | 14.29 | 8, 11, 10, 26 |
| gpt-image-2.5-flare | 32.14 | 21.43 | 14.29 | 3.57 | 6, 10, 9, 28 |
| gpt-image-2.5-sunburst | 39.29 | 25.00 | 14.29 | 17.86 | 5, 10, 12, 27 |
| google/gemini-3.1-flash-image | 21.43 | 14.29 | 25.00 | 14.29 | 7, 12, 11, 26 |
| black-forest-labs/flux.2-max | 32.14 | 21.43 | 21.43 | 25.00 | 11, 13, 10, 17 |

Complete predictions, nonconformity scores, set memberships, painter risks/confusions, abstention reasons, numeric boundary ties and all scene-deletion records are retained in analysis.json. Undefined risks and means remain null; no configuration is dropped.

## csd/original/primary

| Configuration | Coverage % | Baseline error % | Gate error % | Margin error % | Baseline−gate pp | Margin−gate pp |
|---|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 26.79 | 27.68 | 0.00 | 0.00 | 27.68 | 0.00 |
| gpt-image-2 | 33.04 | 24.11 | 2.70 | 2.70 | 21.40 | 0.00 |
| gpt-image-2.5-flare | 24.11 | 37.50 | 0.00 | 0.00 | 37.50 | 0.00 |
| gpt-image-2.5-sunburst | 26.79 | 38.39 | 0.00 | 0.00 | 38.39 | 0.00 |
| google/gemini-3.1-flash-image | 45.54 | 49.11 | 25.49 | 33.33 | 23.62 | 7.84 |
| black-forest-labs/flux.2-max | 57.14 | 60.71 | 53.12 | 48.44 | 7.59 | -4.69 |

Equal-configuration baseline−gate / margin−gate reductions (pp): 26.03 / 0.53.

Failed joint criteria: every_configuration_coverage_at_least_half, every_painter_accepted_in_every_configuration. Missing means: none.

| Configuration | Free gate % | Free margin % | Generic gate % | Generic margin % | Gate accepted counts by painter |
|---|---:|---:|---:|---:|---|
| gpt-image-1 | 50.00 | 17.86 | 32.14 | 28.57 | 1, 0, 1, 28 |
| gpt-image-2 | 25.00 | 14.29 | 25.00 | 25.00 | 1, 1, 8, 27 |
| gpt-image-2.5-flare | 14.29 | 0.00 | 21.43 | 7.14 | 0, 0, 2, 25 |
| gpt-image-2.5-sunburst | 14.29 | 0.00 | 17.86 | 7.14 | 0, 0, 2, 28 |
| google/gemini-3.1-flash-image | 50.00 | 17.86 | 60.71 | 39.29 | 6, 9, 8, 28 |
| black-forest-labs/flux.2-max | 46.43 | 28.57 | 75.00 | 75.00 | 8, 17, 22, 17 |

Complete predictions, nonconformity scores, set memberships, painter risks/confusions, abstention reasons, numeric boundary ties and all scene-deletion records are retained in analysis.json. Undefined risks and means remain null; no configuration is dropped.

## csd/original/development

| Configuration | Coverage % | Baseline error % | Gate error % | Margin error % | Baseline−gate pp | Margin−gate pp |
|---|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 33.04 | 39.29 | 5.41 | 8.11 | 33.88 | 2.70 |
| gpt-image-2 | 26.79 | 33.04 | 0.00 | 0.00 | 33.04 | 0.00 |
| gpt-image-2.5-flare | 25.89 | 40.18 | 3.45 | 3.45 | 36.73 | 0.00 |
| gpt-image-2.5-sunburst | 34.82 | 43.75 | 15.38 | 15.38 | 28.37 | 0.00 |
| google/gemini-3.1-flash-image | 42.86 | 55.36 | 29.17 | 33.33 | 26.19 | 4.17 |
| black-forest-labs/flux.2-max | 36.61 | 57.14 | 48.78 | 41.46 | 8.36 | -7.32 |

Equal-configuration baseline−gate / margin−gate reductions (pp): 27.76 / -0.07.

Failed joint criteria: every_configuration_coverage_at_least_half, every_painter_accepted_in_every_configuration, positive_mean_margin_minus_gate. Missing means: none.

| Configuration | Free gate % | Free margin % | Generic gate % | Generic margin % | Gate accepted counts by painter |
|---|---:|---:|---:|---:|---|
| gpt-image-1 | 32.14 | 25.00 | 39.29 | 39.29 | 0, 7, 2, 28 |
| gpt-image-2 | 10.71 | 3.57 | 10.71 | 14.29 | 1, 2, 0, 27 |
| gpt-image-2.5-flare | 3.57 | 0.00 | 14.29 | 10.71 | 0, 3, 1, 25 |
| gpt-image-2.5-sunburst | 3.57 | 0.00 | 10.71 | 7.14 | 2, 5, 4, 28 |
| google/gemini-3.1-flash-image | 21.43 | 25.00 | 42.86 | 42.86 | 8, 7, 5, 28 |
| black-forest-labs/flux.2-max | 35.71 | 28.57 | 78.57 | 82.14 | 4, 9, 14, 14 |

Complete predictions, nonconformity scores, set memberships, painter risks/confusions, abstention reasons, numeric boundary ties and all scene-deletion records are retained in analysis.json. Undefined risks and means remain null; no configuration is dropped.

## csd/audited_region/primary

| Configuration | Coverage % | Baseline error % | Gate error % | Margin error % | Baseline−gate pp | Margin−gate pp |
|---|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 25.89 | 26.79 | 0.00 | 0.00 | 26.79 | 0.00 |
| gpt-image-2 | 32.14 | 24.11 | 2.78 | 2.78 | 21.33 | 0.00 |
| gpt-image-2.5-flare | 24.11 | 38.39 | 0.00 | 0.00 | 38.39 | 0.00 |
| gpt-image-2.5-sunburst | 26.79 | 39.29 | 0.00 | 0.00 | 39.29 | 0.00 |
| google/gemini-3.1-flash-image | 46.43 | 49.11 | 28.85 | 34.62 | 20.26 | 5.77 |
| black-forest-labs/flux.2-max | 56.25 | 60.71 | 50.79 | 50.79 | 9.92 | 0.00 |

Equal-configuration baseline−gate / margin−gate reductions (pp): 26.00 / 0.96.

Failed joint criteria: every_configuration_coverage_at_least_half, every_painter_accepted_in_every_configuration. Missing means: none.

| Configuration | Free gate % | Free margin % | Generic gate % | Generic margin % | Gate accepted counts by painter |
|---|---:|---:|---:|---:|---|
| gpt-image-1 | 46.43 | 17.86 | 32.14 | 28.57 | 0, 0, 1, 28 |
| gpt-image-2 | 17.86 | 7.14 | 21.43 | 17.86 | 1, 1, 7, 27 |
| gpt-image-2.5-flare | 7.14 | 0.00 | 21.43 | 7.14 | 0, 0, 2, 25 |
| gpt-image-2.5-sunburst | 17.86 | 0.00 | 10.71 | 7.14 | 0, 0, 2, 28 |
| google/gemini-3.1-flash-image | 32.14 | 17.86 | 57.14 | 39.29 | 7, 9, 8, 28 |
| black-forest-labs/flux.2-max | 39.29 | 28.57 | 75.00 | 75.00 | 8, 17, 22, 16 |

Complete predictions, nonconformity scores, set memberships, painter risks/confusions, abstention reasons, numeric boundary ties and all scene-deletion records are retained in analysis.json. Undefined risks and means remain null; no configuration is dropped.

## csd/audited_region/development

| Configuration | Coverage % | Baseline error % | Gate error % | Margin error % | Baseline−gate pp | Margin−gate pp |
|---|---:|---:|---:|---:|---:|---:|
| gpt-image-1 | 37.50 | 41.07 | 14.29 | 7.14 | 26.79 | -7.14 |
| gpt-image-2 | 26.79 | 32.14 | 0.00 | 0.00 | 32.14 | 0.00 |
| gpt-image-2.5-flare | 27.68 | 41.07 | 6.45 | 3.23 | 34.62 | -3.23 |
| gpt-image-2.5-sunburst | 38.39 | 42.86 | 20.93 | 20.93 | 21.93 | 0.00 |
| google/gemini-3.1-flash-image | 40.18 | 55.36 | 26.67 | 31.11 | 28.69 | 4.44 |
| black-forest-labs/flux.2-max | 33.93 | 57.14 | 47.37 | 39.47 | 9.77 | -7.89 |

Equal-configuration baseline−gate / margin−gate reductions (pp): 25.66 / -2.30.

Failed joint criteria: every_configuration_coverage_at_least_half, every_painter_accepted_in_every_configuration, positive_mean_margin_minus_gate. Missing means: none.

| Configuration | Free gate % | Free margin % | Generic gate % | Generic margin % | Gate accepted counts by painter |
|---|---:|---:|---:|---:|---|
| gpt-image-1 | 28.57 | 25.00 | 39.29 | 39.29 | 1, 8, 5, 28 |
| gpt-image-2 | 10.71 | 3.57 | 17.86 | 14.29 | 1, 2, 0, 27 |
| gpt-image-2.5-flare | 3.57 | 0.00 | 17.86 | 14.29 | 0, 4, 2, 25 |
| gpt-image-2.5-sunburst | 0.00 | 0.00 | 7.14 | 7.14 | 2, 6, 7, 28 |
| google/gemini-3.1-flash-image | 21.43 | 17.86 | 46.43 | 42.86 | 7, 6, 4, 28 |
| black-forest-labs/flux.2-max | 35.71 | 28.57 | 75.00 | 75.00 | 2, 9, 13, 14 |

Complete predictions, nonconformity scores, set memberships, painter risks/confusions, abstention reasons, numeric boundary ties and all scene-deletion records are retained in analysis.json. Undefined risks and means remain null; no configuration is dropped.

## Limits

Prior baseline outcomes informed the retrospective question. The historical panels, generated observations and two related encoders are reused. Scene-deletion ranges describe influence, not uncertainty coverage. No p-values, new observations, perceptual validation or independent session replication are supplied. Adverse and undefined results remain part of the primary finding; no alternative gate is substituted.
