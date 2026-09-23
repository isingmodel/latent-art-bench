# Independent implementation/result audit: held-scene prototype transfer v1

**Verdict: PASS for the retained implementation and numeric results.** No critical defect was found. This is implementation/result QA, not a scored scientific review or a revision of the round-02 reviews. The independently reconstructed results retain all harmful and null outcomes.

Completed: 2026-09-18T15:58:55.627593+00:00.

## Scope and independence

The reviewer read the frozen plan, transfer implementation, and both test modules. The independent calculation imports NumPy and standard-library modules only; it does not import or call the transfer implementation, its row assembly, evaluation, summary helpers, or original analysis helpers. It reconstructs cells directly from manifest `(model, scene, repeat, arm)` identities and historical `(id, view)` identities. No image was collected, decoded, re-extracted, selected by outcome, or modified. No frozen plan, code, input, or result was changed.

The requested original-view/primary audit covers both encoders and all six configurations: 12 combinations, 36 rule results, and 4,032 retained held-out predictions. The same direct reconstruction was also applied to every prespecified sensitivity: 48 encoder/view/target/configuration combinations, 144 rule results, 672 model/target folds, 16,128 predictions and 64,512 scalar scores. These counts reuse the same 672 named generated images across representations, reference targets and views; they are not independent generated observations.

## Verified equations and membership

For each model and held-out scene, both held-out repeats are excluded by selecting the other 13 scenes explicitly: 104 named generated images. The supervised context uses the same training scenes, with 26 training images per prompted painter. No generators are pooled. Historical painter centroids are arithmetic means of their unit embeddings, and the target mean averages the four unnormalized centroids equally. Only the classification prototypes are normalized.

With historical centroid `mu[a]`, `u[a] = mu[a]/||mu[a]||`, pooled training mean `g`, and held-out embedding `x`, the independent scores are:

- Reference baseline: `dot(x, u[a])`.
- Common translation: `dot(x + mean_a(mu[a]) - g, u[a])`, with scale exactly one.
- Generated-prototype context: `dot(x, nu[a]/||nu[a]||)`, where `nu[a]` averages other-scene examples with generated painter label `a`.

The audit independently confirms translation acts as a class-specific intercept, and the same vector added to all painters leaves their centered geometry unchanged within each fold. Query normalization produces the same translated argmax for every retained query. Margins are the reported raw linear correct-minus-best-incorrect gaps; translated-query norms vary, so those gaps are not normalized cosine margins.

All generated image IDs, original/region selections, primary counts `[297, 106, 141, 105]` (649 works), and development counts `[101, 36, 48, 36]` (221 works) match. The row manifest contains 1,008 generated originals, 649 primary originals, 221 development originals and 131 historical region embeddings (90 primary, 41 development). Regions substitute for their original work and do not create extra observations. Free/generic generated arms are absent from all three classification rules.

## Numeric verification

- All 20 frozen binding hashes match, before and after independent execution. The result also records the correct input-binding hash. Original learned-audit binding hashes match.
- All independently recomputed predictions, correctness arrays, confusion matrices, per-painter counts and paired decision-transition counts match exactly. Every rule has 112 predictions, 28 observations per prompted painter, and a confusion total of 112.
- All raw scores, margins, macro/micro accuracy, painter recalls, scene accuracies/differences, fold means, translations, prototypes and norms match within absolute tolerance `1e-12`. Maximum scalar-score discrepancy: 2.89e-15; maximum checked numeric discrepancy: 3.22e-15. There were 8732 numeric/array assertions in addition to scalar, identity and census checks.
- All 48 reference-baseline confusion matrices, painter recalls, counts and macro/micro accuracies exactly reproduce the retained learned audit.
- All aggregate equal-configuration means and every corrected/newly-incorrect/unchanged transition count reconcile with individual predictions.
- No exact top ties or zero translated queries occur in the retained results. Translated-query norms span 0.757253–1.111137.
- Constructed-array/protocol suite: `uv run --locked pytest -q tests/painter_prototype_transfer_v1` → **39 passed**. Tests cover held-out leakage, training-label permutation invariance, identity/additive-offset/harmful examples, ties/zero queries, invalid vectors, membership, baseline agreement, frozen bindings and replay safeguards.

## Original-view primary results

B/T/G give numbers correctly classified out of 112 for reference baseline, common translation and supervised generated prototypes. Delta is T−B in percentage points. Scene W/T/L counts positive/zero/negative paired scene accuracy changes over the 14 fixed scenes; they are descriptive, not independent replications.

| Encoder | Configuration | B | T | G | T−B pp | Corrected | Newly incorrect | Scene W/T/L |
|---|---|---:|---:|---:|---:|---:|---:|---|
| CLIP | gpt-image-1 | 68 | 62 | 90 | -5.357 | 1 | 7 | 1/9/4 |
| CLIP | gpt-image-2 | 77 | 74 | 84 | -2.679 | 1 | 4 | 1/9/4 |
| CLIP | gpt-image-2.5-flare | 67 | 67 | 87 | +0.000 | 4 | 4 | 2/10/2 |
| CLIP | gpt-image-2.5-sunburst | 66 | 70 | 78 | +3.571 | 6 | 2 | 4/8/2 |
| CLIP | google/gemini-3.1-flash-image | 58 | 67 | 71 | +8.036 | 15 | 6 | 8/5/1 |
| CLIP | black-forest-labs/flux.2-max | 46 | 60 | 80 | +12.500 | 24 | 10 | 10/3/1 |
| CSD | gpt-image-1 | 81 | 82 | 95 | +0.893 | 3 | 2 | 3/9/2 |
| CSD | gpt-image-2 | 85 | 86 | 106 | +0.893 | 4 | 3 | 3/9/2 |
| CSD | gpt-image-2.5-flare | 70 | 83 | 104 | +11.607 | 16 | 3 | 8/5/1 |
| CSD | gpt-image-2.5-sunburst | 69 | 79 | 101 | +8.929 | 17 | 7 | 9/3/2 |
| CSD | google/gemini-3.1-flash-image | 57 | 69 | 84 | +10.714 | 22 | 10 | 9/3/2 |
| CSD | black-forest-labs/flux.2-max | 44 | 74 | 84 | +26.786 | 39 | 9 | 13/1/0 |

CLIP translation changes 51 decisions from incorrect to correct and 33 from correct to incorrect: a net 18/672 and an equal-configuration gain of **+2.679 pp**. It harms gpt-image-1 and gpt-image-2 and leaves the flare configuration tied. CSD translation changes 101 decisions from incorrect to correct and 34 from correct to incorrect: a net 67/672 and **+9.970 pp**. All six CSD primary configuration aggregates improve, while five retain at least one harmful scene.

The supervised generated prototypes exceed both baseline and translation in **all 12 original-primary combinations**. Their mean gains over baseline are +16.071 pp for CLIP and +25.000 pp for CSD. This comparison must remain visible: it uses painter-labeled generated training images, so it is not an equal-information zero-shot comparator.

## All prespecified aggregate sensitivities

Each mean equally weights all six configurations. Positive/zero/negative counts describe the individual T−B configuration differences.

| Encoder | View | Target | Mean T−B pp | Mean G−B pp | Positive / zero / negative |
|---|---|---|---:|---:|---|
| CLIP | original | primary | +2.679 | +16.071 | 3 / 1 / 2 |
| CLIP | original | development | +4.018 | +16.667 | 4 / 0 / 2 |
| CLIP | audited_region | primary | +2.530 | +16.815 | 3 / 1 / 2 |
| CLIP | audited_region | development | +2.232 | +15.476 | 3 / 0 / 3 |
| CSD | original | primary | +9.970 | +25.000 | 6 / 0 / 0 |
| CSD | original | development | +9.821 | +30.208 | 6 / 0 / 0 |
| CSD | audited_region | primary | +9.673 | +25.149 | 4 / 1 / 1 |
| CSD | audited_region | development | +10.119 | +30.357 | 6 / 0 / 0 |

All ten adverse configuration results across primary and sensitivity targets are retained:

| Encoder | View | Target | Configuration | T−B pp | Corrected | Newly incorrect |
|---|---|---|---|---:|---:|---:|
| CLIP | audited_region | development | gpt-image-1 | -3.571 | 4 | 8 |
| CLIP | audited_region | development | gpt-image-2.5-flare | -5.357 | 1 | 7 |
| CLIP | audited_region | development | gpt-image-2.5-sunburst | -0.893 | 8 | 9 |
| CLIP | audited_region | primary | gpt-image-1 | -4.464 | 2 | 7 |
| CLIP | audited_region | primary | gpt-image-2 | -3.571 | 1 | 5 |
| CLIP | original | development | gpt-image-1 | -5.357 | 5 | 11 |
| CLIP | original | development | gpt-image-2.5-flare | -2.679 | 4 | 7 |
| CLIP | original | primary | gpt-image-1 | -5.357 | 1 | 7 |
| CLIP | original | primary | gpt-image-2 | -2.679 | 1 | 4 |
| CSD | audited_region | primary | gpt-image-1 | -1.786 | 4 | 6 |

## Interpretation boundaries

These are **retrospective out-of-fold prompt-label accuracies** in a fixed four-painter candidate set. They test recovering the name present in the generation prompt. They do not establish artistic fidelity, physical authorship, human recognition, unseen-painter generalization, an unwanted shared painting response, or validity of pooled contrast error D. The common translation is ordinary mean alignment and does not isolate a named-minus-generic causal component. Its translated vector need not be an image-realizable unit embedding.

Existing baseline outcomes were known before this retrospective extension. Overlapping training folds, related encoders with unknown training overlap, fixed authored scenes, reused development references and one service session do not establish independent replication. No p-values, significance claims, uncertainty intervals or scientific acceptance score are introduced by this audit.

## Reproduction and receipts

Independent implementation: [transfer_independent_audit.py](transfer_independent_audit.py). Machine-readable receipt and all primary summary rows: [transfer_independent_audit.json](transfer_independent_audit.json).

```sh
uv run --locked python reports/icml_review_v1/transfer_independent_audit.py
uv run --locked pytest -q tests/painter_prototype_transfer_v1
```

Frozen input binding SHA-256: `bdcf38bb09da53c890a1a62ce268c0336824ccadfb6ba90ee711bdaf1a6f1baf`.

Frozen analysis SHA-256: `e1d1fbb924feb797f67e0907677511ed7c745335a4f2827e99d2f286e6be5448`.

Frozen report SHA-256: `9e7546198fd04c047f1b8a44f6575e957ef331282a6b879b32ddf900d2e0b81e`.

Independent script SHA-256: `e5f986ea700d54ffb9e493aa33b7c9058da8b6b5e5d76abe3af2883583a492d3`.

Execution note: the first command used to save the independent script invoked an unavailable bare `python` executable and therefore did not run that script. Repeating the save/run through the locked `uv run --locked python` environment succeeded. No numerical audit check or synthetic test failed, and no result was changed.
