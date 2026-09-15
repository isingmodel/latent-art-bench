# Revisions after round 22

All three reviews count: 9.125, 9.25 and 9.125; mean 9.166666666666666.
The fixed rubric and blind review procedure remain unchanged.

- All reviewers identified repeated scene-averaging language in the Discussion.
  The repeated last sentence is removed. One declarative recommendation now
  connects overall/pairwise alignment, original/calibrated error and explicit
  scene treatment to the preceding evaluation-target explanation.
- Reviewer B requested a clearer calibrated table heading. “Calibrated scene
  error” replaces “Error after calibration,” making its scene-wise target
  visible beside uncalibrated scene error and error after averaging scenes.
  The numerical cells and all other generated outputs remain unchanged;
  exact presentation replay and Ruff pass.
- Reviewer B requested a route to Appendix E's plots. Its opening now names
  both the tables and figures, covering model comparisons, error components,
  proximity and spread. All existing explanations and captions remain intact.
- Reviewer C requested a plain-language definition of H. Section 4.2 now
  identifies it as the total squared size of the reference contrasts before
  using it to normalize both scores. The definition and computations are unchanged.
- Reviewers A and C requested a clearer calibration lesson and less repeated
  setup in the abstract. Three new authoring agents supplied fresh drafts,
  retained in ABSTRACT_DRAFTS.md. The aggregate rewrite begins with the
  distinction between changing an image and reproducing painter differences,
  explicitly measures features in both image sets, and explains how shrinking
  GPT Image 2's measured differences lowers its held-out error. All core counts,
  arms, primary findings, separate calibration, unchanged images and the
  perceptual limitation remain. The abstract is 152 whitespace words.

The Introduction now opens with an actual painter-name phrase, avoiding the
abstract's repeated opening and making the prompt intervention concrete.

These are editorial changes only. No experiment, scientific result, source image,
feature, inferential procedure or human evaluation is added or changed.
