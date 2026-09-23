# ICML revision: evidence and reproducibility audit

Audit date: 2026-09-18. This audit inspected the canonical English manuscript,
its included result/diagnostic tables and appendices, repository handover,
Makefile, primary protocols, retained manifests, numerical reports and focused
tests. It did not generate images, modify scientific records, or rerun an AI
editorial evaluation. The new manuscript appendix is
`paper/icml_reproducibility.tex`; this report records the audit's own checks.

## Verification performed for this revision

Environment: `uv run --locked python` reports **Python 3.13.11**.

| Command or check | Observed result |
| --- | --- |
| `uv run --locked pytest -q tests/painter_specificity_v1 tests/painter_specificity_v2 tests/painter_specificity_measurement_v1 tests/painter_specificity_review_v1 tests/painter_specificity_review_v2 tests/painter_reference_quality_v1` | **38 passed in 2.61 s** |
| `make specificity-check` | All four exact numerical replays passed: primary, square, content-reweighted reference, content-reweighted/square |
| `make review-check` | Initial exact diagnostic replay, diagnostic presentation check, and exact v2 diagnostic replay all passed, including the original real-control draws |
| `make reference-quality-check` | Reference-quality numerical result verified |
| `make specificity-audit` | Report and raw-byte audit verified, covering all **1,008 raw response hashes** and **1,008 output image hashes**, assignment/outcome identities, terminal accounting and dispatch constraints |
| `make example-images-check` | Verified 28 original/named and 12 control examples; all **40 source hashes** checked |
| `make reference-quality-images-check` | All **870 reference/development source hashes** and exact normalized-pixel/feature replay for **131 audited crops** verified |
| `make figures-check` | All numerical figure/table checks passed, including supporting figures, palette blocks, challenge matrix, geometry, eight specificity figures, specificity tables and review presentation |
| Recompute SHA-256 of all paths in the primary `freeze.json` | **27 bindings, zero mismatches** |
| Inspect all terminal attempt records | **1,008** successes; all reported model, quality, size and output-format fields are null |

The tests include analytical noise controls, a reference-recovery oracle,
training-only calibration, full inner refitting after scene deletion, the
cross-repeat shared-control correction, finite-pool expectations, and source
region/scaling checks. Test success validates those implementations under the
tested conditions; it does not establish service independence or perceptual
validity.

All required local response and pixel inputs were available for the four added
checks; none was skipped. They ran as read-only checks and did not rewrite
figures, vectors or scientific records. Crop-feature re-extraction covers the
131 audited regions, not a fresh extraction of every generated or uncropped
reference vector. `make figures-check` covers its existing Makefile targets;
the new ICML manuscript's compiled layout requires its separate build and
visual inspection.

Not rerun in this audit: the full routine or historical suite, historical
editorial archive checks, or a manuscript build. Those checks may be performed
separately by the integrating revision. Historical dated receipts must not be
reported as freshly executed checks.

## Provenance findings

- All current requests use `https://openrouter.ai/api/v1/images`, one output,
  `aspect_ratio=1:1`, and `provider.allow_fallbacks=false`.
- The four OpenAI request identifiers are `openai/gpt-image-1`,
  `openai/gpt-image-2`, `openai/gpt-image-2.5-flare` and
  `openai/gpt-image-2.5-sunburst`. Each restricts the provider to `openai` and
  sets `quality=medium` and `background=opaque`.
- Nano Banana 2 requests `google/gemini-3.1-flash-image`, provider
  `google-ai-studio`, and `resolution=1K`.
- FLUX requests `black-forest-labs/flux.2-max`, provider
  `black-forest-labs/us-3`, and `output_format=png`. Its recorded payload does
  not explicitly set resolution or quality.
- No current payload contains a seed or image input. Every output's recorded
  decoded dimensions are 1,024 by 1,024. None of the 1,008 results echoes model,
  quality, size or output format. Thus the record supports exact **requested
  configuration** labels, not independent attestation of served checkpoints.
- The primary freeze is `2026-09-10T15:34:19.942590+00:00`; the first request
  starts at `2026-09-10T15:34:20.846233+00:00`; collection closes at
  `2026-09-10T18:21:04.039850+00:00`; the measurement receipt is
  `2026-09-10T18:30:03.866908+00:00`. These are all 11 September in UTC+9,
  explaining the `psv2-20260911` identifier and protocol date. Writing
  “10 September 2026 UTC” avoids an apparent date discrepancy.
- The terminated 31-output attempt and technical probes are separate from the
  analyzed collection. A reader correction selects 649 successfully measured
  references while preserving four failed historical records.
- The compact repository permits numerical replay. Current exact pixels still
  require local retained files; a dedicated public archive or verified recovery
  route remains missing. This audit verified the retained local raw response and
  image bytes for all 1,008 current outputs, all 40 display sources, and all 870
  reference/development sources; the 131 cropped regions also reproduce exact
  normalized pixels and features. Local availability and matching hashes do
  not establish public exact-pixel access.

## Claim support

| Claim | Supported interpretation and boundary |
| --- | --- |
| All six configurations align with reference contrasts | Each declared simultaneous beta interval is above zero, including the source-correction sensitivity. This concerns the specified reference target and 31-feature metric; it does not imply agreement for every painter pair. |
| FLUX has the lowest uncalibrated error | Supported as the observed point-estimate ordering: D = 0.800928 with full frames. Only Flare and Sunburst exceed FLUX under the original adjusted pair comparisons. Source correction removes Sunburst's separation. A universal or significant six-model ranking is unsupported. |
| No model is established to beat no painter distinctions before calibration | Supported. FLUX's nominal D interval is [0.586004, 1.015853]; other estimates do not establish D < 1. Absolute-D intervals are descriptive and outside the declared 21-comparison family. This is failure to establish superiority, not evidence of equivalence. |
| Most named-minus-free change is shared | The scene-averaged repeat-corrected shared fractions are 82.5–95.7%. They are squared feature-change shares including the oil-painting clause. They are not percentages of perceptual style, model knowledge, causal mechanisms, or name-only effects. |
| Generic and shared named shifts point in similar directions | The corrected cross-repeat ratios are .689–.930 and remain positive under every scene deletion. Corrected squared-size ratios are 1.960–4.138. These ratios are descriptive; finite estimates are not unbiased or necessarily bounded like ordinary cosines. |
| GPT Image 2 has the lowest calibrated error | Supported as retrospective held-scene point estimates: .554 versus FLUX .714. One nonnegative scalar per model is fitted on the other 13 scenes. GPT Image 2 wins 12/14 folds and retains its advantage under fully refitted scene deletion. Overlapping folds do not establish a new superiority test. |
| Calibration improves generated images | Unsupported. Calibration rescales measured centered feature contrasts; no images are changed and realizability is not shown. Historical reference targets are shared across folds; only generated scenes are held out. |
| Monet–Sisley agreement is weak or reversed in five configurations | Supported descriptively in the original metric, where five slopes range from −.249 to .129 and GPT Image 2 is .402. Pair signs near zero can change after source correction. There are no pairwise significance tests or perceptual-failure judgments. |
| Repeated requests establish independent noise | Unsupported. Independence is an assumption. Analytical tests and simulations probe specified noise laws; the retained shared-state simulation demonstrates severe failure when the assumption is violated. |
| Exact computation validates artistic fidelity or supplies independent replication | Unsupported. Reproducibility is conditional on vectors, reference construction and feature choices; model weights, capture variation and perceptual fidelity remain unverified. |

## Compact-paper priorities

1. Keep a three-row explanation of the distinct targets: scene-conditional D,
   aggregate D, and held-scene calibrated D. The comparison table's minima are
   descriptive and answer different questions.
2. Preserve the D = 1 theoretical no-contrast benchmark distinction from the
   observed generic arm. A common response can be large while centered contrasts
   vanish; shared percentage and reference agreement require separate scores.
3. State “requested model configurations” and give the exact routes/settings in
   the new appendix. The absence of response attestations is material provenance,
   not merely a generic reproducibility disclaimer.
4. Retain one sentence in the main results stating that source correction changes
   the resolved Sunburst comparison. This is stronger evidence of sensitivity
   than a long undifferentiated robustness list.
5. Label the shared-change, pair, calibration and source-audit results as
   retrospective; distinguish approximate simultaneous intervals, nominal
   absolute-D summaries, and sensitivity ranges.
6. Keep the independent-repeat assumption, fixed-scene scope, reproduction target,
   and numerical-versus-pixel access boundary explicit. No human evaluation is
   necessary to state these limits accurately.

## Scientific artifacts hashed in this audit

SHA-256 values below were computed from the retained files during this audit.

| Artifact | SHA-256 |
| --- | --- |
| `data/manifests/painter_specificity_v2/psv2-20260911/freeze.json` | `2f32de5182357e960eb4520b45e90f23e6fe812168679cba9072a435675cdf27` |
| `data/manifests/painter_specificity_v2/psv2-20260911/requests.jsonl` | `0aa60f491be08dbd48f1f018e225b22bcae2aacd724abf3371a6312d59acc679` |
| `data/manifests/painter_specificity_v2/psv2-20260911/attempts.jsonl` | `b131798cd2b803d6d60569def72700bb35daacdd2c5602e0dc854b7bd77a3ffd` |
| `data/manifests/painter_specificity_v2/psv2-20260911/collection.json` | `3491468b0dc6875d28e530595341d2a5a659a5aec175e5f6f7999f05b5851480` |
| `data/manifests/painter_specificity_v2/psv2-20260911/measurement_receipt.json` | `e71a1a7c64ba6d443e899f7913d4e97ee5db4e15cda132955fd2b41243d31c06` |
| `data/manifests/painter_specificity_v2/psv2-20260911/analysis.json` | `c1d21b16f840a10fd253c1d558743a09671acf3d4e48601ddcc96625a5a90be0` |
| `reports/painter_specificity_review_v1/analysis.json` | `2fabb78e15dfcc7b027a73170f6ad0c87af0196c754b4e6f45275269c2c961e2` |
| `reports/painter_specificity_review_v2/analysis.json` | `92f2c74c92232b1fae03ab195a8c81749a0a4b9676fd737e2e5741dc67571a16` |
| `reports/painter_reference_quality_v1/analysis.json` | `089f636335129d6377328088ccc9fdc763488aba2a88463939322326707052b4` |

## Historical editorial scores

The archived AI editorial scores assess expression, structure, reader
understanding and engagement for particular frozen manuscript versions.
They are not scientific peer-review scores, empirical validity evidence, or
human assessments. The latest previous final update has no independent new
score; the earlier scores must not be assigned to this ICML revision. This
audit issues no numerical scientific-review or editorial rating.
