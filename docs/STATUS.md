# Current status — 2026-09-15

The canonical English [paper](../paper/paper.tex), **Artist-Name Responses
beyond a Shared Painting Effect in Text-to-Image Generation**, now incorporates
the final editorial update. The [PDF](../paper/paper.pdf) is 23 pages with a
151-word abstract. The user lifted the manuscript length limit for this update;
no human evaluation was added. Original scientific records remain
preserved; new analyses have separate versioned plans and source bindings.

The main text now pairs four original painting reproductions with all six models
on one shared brief; artist-free/generic controls appear in the same model rows.
The [presentation manifest](../paper/example_selection.json) records the 40 source
identities, prompts, reference-selection rule and audited crops. This is a
presentation change using retained images, with no new scientific results.

Reader-experience editing uses a [fixed four-part rubric](../reports/paper_editorial_review_v1/RUBRIC.md)
for expression, structure, new-reader understanding and engagement. Every
round assigns a frozen manuscript to three fresh independent agents, without
earlier scores or the stopping threshold. The [editorial record](../reports/paper_editorial_review_v1/README.md)
retains every review, revision decision, snapshot hash and arithmetic result.
These are internal language-model judgments, not human-reader evidence.
The original goal was completed in round 33: 99 distinct reviewing agents;
scores 9.375, 9.0625 and 9.4375, averaging **9.2916666667** (above 9.25).
Those scores apply to the preserved round-33 snapshot, not later revisions.
The first [independent reviews](../reports/paper_editorial_review_v1/INDEPENDENT_REVIEWS.md)
scored that snapshot 8.3125 (Claude Code / Opus 5) and 8.9375 (Astra / xhigh).

The user then requested **revision, fresh evaluation, and another revision**.
The [paired review record](../reports/paper_editorial_review_v1/paired_review_03/README.md)
tracks that sequence. Requests `_02` were cancelled before the first revision and
supply no scores. Fresh `_03` reviews scored the frozen first revision **8.0625**
(Claude) and **8.8125** (Astra). Those reviews informed a subsequent
second revision; the `_03` scores concern the preceding version. That second
revision had 22 pages, a 151-word abstract and 9,593 extracted PDF words.

A final [evaluation-only round `_04`](../reports/paper_editorial_review_v1/paired_review_04/README.md)
assessed the unchanged second revision in fresh sessions: **8.0625** from
Claude Code / Opus 5 and **8.8125** from Astra / xhigh, mean **8.4375**.
Overall scores happen to match `_03`, with different dimension scores. Both raw
reviews and host fact checks are retained.

The subsequent [final update](../reports/paper_editorial_review_v1/final_update/README.md)
clarifies the three error criteria and what calibration rescales, adds per-model
shared/generic comparisons, restores the artist-free baseline in the conclusion,
and links the main text to model-provenance and historical-cohort details.
Repeated qualifications are shortened while their substantive limits remain.
These last edits have **not** received a new independent score; `_04` still
refers to its preserved earlier snapshot. Existing images and scientific
analysis records are unchanged.

Repository guides now distinguish current and historical image panels and
scientific replay from editorial-record verification. The
[portable archive](../reports/paper_editorial_review_v1/ARCHIVE.md) retains all
99 original and six completed external reviews; bulky CLI traces and local
runners remain intact locally and are excluded from Git. Local and remote
branches are consolidated on `main`; stale remote-tracking references were pruned.

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
$120 ceiling. No new image-generation requests were made; the image-generation ledger is unchanged.

## Verification

The final 2026-09-15 update passed Ruff and all **848 routine tests**.
`make figures-check`, `make example-images-check` (all 40 source hashes), and
`make editorial-check` passed. Optional local review verification checked all
36 historical manuscript snapshots and 24 execution artifacts. The final PDF
compiled without warnings; all 23 pages were rendered and visually inspected.
It contains 9,655 extracted PDF words. The
[final validation receipt](../reports/paper_editorial_review_v1/final_update/VALIDATION.json)
binds these checks to the final PDF. No scientific analysis inputs, code or
results changed; the full historical suite and crop-feature extraction were not
rerun for this editorial update.

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

The example-panel edit passed Ruff and exact image-presentation replay with all
40 source hashes verified. Subsequent editorial revisions add concrete metric
examples, separate main-text explanation from optional derivations, improve plot
legibility and table comparisons, and shorten repeated qualifications. Figure
and table builders pass their relevant replay checks; geometry checks preserve
all plotted coordinates and axis limits. The current PDF compiles without warnings
and has been rendered for page inspection. Scientific records remain unchanged.
