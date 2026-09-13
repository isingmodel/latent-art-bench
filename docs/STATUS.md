# Current status — 2026-09-13

The canonical English [paper](../paper/paper.tex), **Artist-Name Responses
beyond a Shared Painting Effect in Text-to-Image Generation**, has been revised
in the working tree. The [PDF](../paper/paper.pdf) is 22 pages, down from 23,
with no human evaluation added, as requested. Original scientific records remain
preserved; new analyses have separate versioned plans and source bindings.

## Findings and review corrections

The completed primary experiment contains **1,008 generated images**: six
models × 14 scenes × six clauses × two repeats. Its reference panel contains
649 works (Monet 297, Sisley 106, Pissarro 141, Cézanne 105); a separate
221-work development panel scales all 31 features.

- All six aggregate reference-aligned slopes remain positive under the declared
  simultaneous procedure, including the source-correction sensitivities.
- FLUX.2 Max retains the lowest uncalibrated error point estimate: original
  D = 0.801, corrected regions D = 0.832, corrected regions and scaler D = 0.872.
  The originally resolved Sunburst comparison loses adjusted separation after
  correction; Flare remains separated. The corrected GPT Image 1 interval also
  moves above zero, a retrospective sensitivity rather than a new confirmatory
  claim. No model is established to beat the D = 1 no-contrast benchmark.
- GPT Image 2 retains the lowest held-scene calibrated error. Full-procedure
  scene deletion preserves its descriptive advantage over FLUX; dependent folds
  do not establish a new superiority test.
- Aggregate alignment remains uneven across artist pairs, especially Monet–Sisley.
  Calibration, response magnitude and target agreement answer different questions.
- An assistant audit covers all 870 reference/development sources. Separate
  measurements remove peripheral regions in 90 reference and 41 development
  images. Ten calibration-strip cases are identified; 43 uncertain boundaries
  remain unchanged. Alternative visual classes differ from 230 title assignments,
  with 42 unclear cases retained. These labels are not independent ground truth.
- Cross-repeat generic/common alignment remains positive after removing the
  shared-control covariance term. Integrating out sparse painting draws greatly
  narrows real-control ranges; those distributions do not validate artistic fidelity.

See the [primary report](../reports/painter_specificity_v2/psv2-20260911/REPORT.md),
[initial diagnostics](../reports/painter_specificity_review_v1/REPORT.md),
[follow-up diagnostics](../reports/painter_specificity_review_v2/REPORT.md) and
[source-quality sensitivity](../reports/painter_reference_quality_v1/REPORT.md).
The paper retains the generic/palette controls and contrary prospective fixed-map
result. Cohorts remain separate; no images were generated or acquired for this revision.

## Remaining limits

The reviews in `critics/` motivated these corrections. No human ratings or learned
feature validation were added. Assistant crop and content judgments do not correct
all capture variation or establish perceptual artistic fidelity. The six-model
experiment still lacks a dedicated versioned public release and exact-pixel archive.
Local hashes and replay do not constitute independent research replication.

Recorded cumulative paid accounting remains **$112.293676** against the user's
$120 ceiling. This revision made no paid requests and did not change the ledger.

## Verification

On 2026-09-13, `make check` passed Ruff and all **848 routine tests**. All four
primary numerical views, both diagnostic versions, source-quality numerical
results and existing figures/tables replayed exactly. The image check verified
all 870 source hashes and exact crop-feature re-extraction for 131 images.
The historical evidence audit passed all 2,902 checks. The PDF compiled without
warnings and all 22 pages were visually inspected. The full historical test
suite was not rerun; see [the analysis catalog](ANALYSES.md) for reproduction.

Earlier versioned releases retain their own receipts. The fixed-map release's
strict Ubuntu replay failed; its separate diagnostic did not repair that
exact-comparison contract.
