# pilot_1 report

This artifact is an API-integration development report, not a benchmark scorecard.
The configuration disables scientific claims and restricts generation to `gpt-image-1` and `gpt-image-2`.

## Frozen design

Common corpus view: `landscape_and_outdoor_place_scene`.

| Target artist | Frozen neighbor |
|---|---|
| Claude Monet | Alfred Sisley |
| Alfred Sisley | Claude Monet |
| Camille Pissarro | Paul Cezanne |
| Paul Cezanne | Camille Pissarro |

## Qualification

| Measurement | Status | Real works | Reproduction pairs |
|---|---|---:|---:|
| `chromatic` | `fail` | 108 | 7 |
| `learned_formal` | `fail` | 108 | 7 |

`chromatic` evidence:
- source behavior was not recovered
- stability exceeded the frozen margin
- source confounding was not controlled
- The Q85 4:2:0 branch remains an unsupported diagnostic; it is not part of a scientific pass.
- Unsupported: JPEG recompression after scientific canonicalization was not qualified
- Unsupported: upsampling sources below a requested branch size was not qualified
- Unsupported: Lee et al.'s real-image full normalized-distribution collapse across sizes
- Unsupported: museum-source robustness in every held-source fold
- Unsupported: diagnostic matched 1024 Q85 4:2:0 codec perturbation; this does not veto the lossless PNG scientific domain
- Unsupported: same-work reproduction generalization beyond exact versioned primary files

`learned_formal` evidence:
- stability exceeded the frozen margin
- source confounding was not controlled
- Unsupported: Kim et al. primary-input domain (known dimensions, native area > 410*410, and aspect ratio < 2)
- Unsupported: frozen 95% PCA variance target
- Unsupported: same-work reproduction stability
- Unsupported: museum-source confounding control with complete artist-by-source split coverage
- The VAE-only weights were independently verified bit-for-bit against the recovered full 512-base-ema.ckpt first-stage state.

Test-only analysis gate: `closed`.

## Generation accounting

- Model counts below are requested labels. The retained responses do not prove which backend model executed, so no `gpt-image-1` versus `gpt-image-2` comparison is permitted.
- Transport: local `openai-oauth` compatibility proxy to the ChatGPT Codex images backend; this was not the public `api.openai.com` Images API.
- Attested use: `engineering_only`; requested-dimension contract: `violated`.
- `gpt-image-1`: refused=1, succeeded=20
- `gpt-image-2`: succeeded=20
- Attempt records retained: 41
- Frozen cells resolved for gated test-only analysis: 40/40
- Frozen cells still unresolved: 0
- Cells resolved after a retained refusal or failure record: 1
- Matching request identity recorded across the failed and succeeding calls: 1/1 cells
- Matching identities reconstructed from retained legacy run metadata: 1 cells. This attestation verifies the retained request contract, but is not a native pre-request identity capture.
- Returned image dimensions recorded: 40/40 successful outputs
- Exact requested-size matches: 0/40 comparable successful outputs
- Requested dimensions: 1024x1024 (40)
- Returned dimensions: 9 distinct sizes; width 1392–1412 px, height 1114–1130 px
- Calls using the explicit unqualified test bypass: 0

## Test-only distribution diagnostics

| Cell | Requested model label | Feature | Calibrated target gap (reference-resampling quantiles) | Specificity margin (reference-resampling quantiles) |
|---|---|---|---:|---:|
| pilot_1-chromatic-gpt-image-1-alfred_sisley | gpt-image-1 | chromatic_distance_seamlessness | 2.21405 [0.467638, 7.25216] | -1.73303 [-3.06938, 0.250075] |
| pilot_1-chromatic-gpt-image-1-camille_pissarro | gpt-image-1 | chromatic_distance_seamlessness | 3.37929 [-1.13247, 13.4623] | 1.27386 [-3.51057, 4.3046] |
| pilot_1-chromatic-gpt-image-1-claude_monet | gpt-image-1 | chromatic_distance_seamlessness | 1.56323 [-0.849892, 8.78416] | 2.28589 [-1.17349, 3.89019] |
| pilot_1-chromatic-gpt-image-1-paul_cezanne | gpt-image-1 | chromatic_distance_seamlessness | -0.0145354 [-2.94816, 4.10499] | 0.256018 [-1.53871, 1.9206] |
| pilot_1-chromatic-gpt-image-2-alfred_sisley | gpt-image-2 | chromatic_distance_seamlessness | 2.55521 [0.590442, 8.39205] | -1.73677 [-2.99334, 0.280101] |
| pilot_1-chromatic-gpt-image-2-camille_pissarro | gpt-image-2 | chromatic_distance_seamlessness | 3.01247 [-1.26795, 11.8581] | 1.1962 [-3.49655, 4.3046] |
| pilot_1-chromatic-gpt-image-2-claude_monet | gpt-image-2 | chromatic_distance_seamlessness | 0.892371 [-2.05882, 6.72592] | 2.20173 [-1.17349, 3.78322] |
| pilot_1-chromatic-gpt-image-2-paul_cezanne | gpt-image-2 | chromatic_distance_seamlessness | 0.259487 [-2.46962, 5.75843] | 0.465662 [-1.46345, 2.27853] |
| pilot_1-learned_formal-gpt-image-1-alfred_sisley | gpt-image-1 | learned_formal | -0.517651 [-0.98027, -0.175308] | 0.166025 [-0.355551, 0.647526] |
| pilot_1-learned_formal-gpt-image-1-camille_pissarro | gpt-image-1 | learned_formal | -0.618651 [-1.2508, -0.0861481] | 0.451985 [-0.195517, 0.960223] |
| pilot_1-learned_formal-gpt-image-1-claude_monet | gpt-image-1 | learned_formal | -0.757846 [-1.64247, -0.00789506] | 0.02887 [-0.395621, 0.44179] |
| pilot_1-learned_formal-gpt-image-1-paul_cezanne | gpt-image-1 | learned_formal | -0.691943 [-1.56295, -0.0901861] | 0.129024 [-0.626481, 0.805022] |
| pilot_1-learned_formal-gpt-image-2-alfred_sisley | gpt-image-2 | learned_formal | -0.550327 [-1.06339, -0.203178] | 0.134344 [-0.295005, 0.586816] |
| pilot_1-learned_formal-gpt-image-2-camille_pissarro | gpt-image-2 | learned_formal | -0.565309 [-1.22413, -0.0481482] | 0.432353 [-0.199127, 0.913871] |
| pilot_1-learned_formal-gpt-image-2-claude_monet | gpt-image-2 | learned_formal | -0.614098 [-1.40721, 0.0800965] | 0.134347 [-0.361037, 0.597185] |
| pilot_1-learned_formal-gpt-image-2-paul_cezanne | gpt-image-2 | learned_formal | -0.61869 [-1.48284, 0.0546391] | 0.222328 [-0.580845, 0.887017] |

A positive specificity margin means the generated distribution is closer to the requested target than to its nearest configured neighbor, after dividing by that target-neighbor separation.
The generated side is fixed at n=4 in every cell and is not resampled.
Bracketed ranges are empirical quantiles from subsampling the real-reference works only. They are not inferential confidence intervals and omit generator-sampling and prompt-cluster uncertainty.
Specificity reference-resampling ranges include zero in 16/16 cells, so point-estimate signs do not support a model or artist ranking.
Negative learned-formal calibrated gaps mean the generated-target distance fell below the held-out real-real baseline after normalization. They are not quality scores or evidence of artist-style fidelity.

## Committed evidence snapshots

- `evidence/analysis_cells.provenance.jsonl`: `19f98e339d79ab22dd9d5ae83b63b6156875cae9e2a28fad5560bdfb91012206`
- `evidence/analysis_results.jsonl`: `eb9cda2a8fcc4226b1798426635699a8bfbb6b70bd8c1f85823ff7e782129576`
- `evidence/artist_free_control_diagnostics.json`: `dff4314c6bdf267a907219c7bb24d4ec34bfc1bca2e846ce0881bc96c1da74a5`
- `evidence/generation_calls.attested.jsonl`: `391ea9f9550ff0f992aedcc8930b5e48c92b54f822e1924309ccc7073a424fb1`
- `evidence/generation_runs.sanitized.jsonl`: `d73b560b2dcaf406d97f5758532af0ca7d2fbbec3fc96d6855d98320b11d72d1`

## Artist-free paired controls

These complete matched pairs measure how much the requested-artist wording changed each output relative to the same content prompt without an artist. Distances are raw within-measurement diagnostics, not fidelity scores or inferential tests.

| Measurement | Requested model label | Pairs | Median raw distance |
|---|---|---:|---:|
| `chromatic` | `gpt-image-1` | 16 | 0.0587337 |
| `chromatic` | `gpt-image-2` | 16 | 0.0797196 |
| `learned_formal` | `gpt-image-1` | 16 | 99.4847 |
| `learned_formal` | `gpt-image-2` | 16 | 96.8956 |

The final artifact and run ledgers are content-addressed by `EVIDENCE.md`.

## Decision

Decision: scientific gate closed; engineering traversal completed under an explicit test-only qualification bypass. The resulting diagnostics are not scientific evidence.
