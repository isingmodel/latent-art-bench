# Revisions after round 30

All three reviews count: 9.125, 9.25 and 9.0; mean 9.125.
The fixed rubric and blind review procedure remain unchanged.

- All three reviewers requested a concrete finding-to-recommendation bridge
  in the Discussion. It now opens with FLUX's lowest uncalibrated error
  estimate despite weak Monet-Sisley alignment and GPT Image 2's near-unit
  alignment without low error. Those examples motivate reporting overall and
  pair scores with their inferential status, and treating scene averaging and
  contrast calibration as separate evaluation choices. It does not catalogue
  all three rankings or repeat the metric definitions.
- Reviewers A and C requested less repetitive abstract status language.
  Retrospective diagnostics introduce the pair result, followed by calibration
  described directly as shrinking each model's measured differences using a
  factor fitted on other scenes. The next sentence states the changed lowest
  held-out mean error estimate. The operation and consequence are separated
  into readable sentences. Reviewer B's more direct “none is shown to have
  lower mismatch” replaces the nested uncertainty construction. The predictor,
  before-calibration scope and perceptual boundary remain. The abstract is
  151 words, down from 152; Section 4.4 still explicitly marks calibration
  and the other diagnostics as retrospective.
- Reviewer B requested visible separation of aggregation and calibration in
  Section 5.4. Short italic paragraph leads, “Averaging scenes” and “Rescaling
  contrasts,” replace the existing openings without adding a section. All
  estimates, their table order, and the distinction between averaging contrasts
  and averaging scene errors remain.
- Reviewer C requested the size, not only direction, of the common/generic
  difference. A separate factual agent reconstructed all control components
  from the retained 1,008 measured rows with zero discrepancy from the control
  JSON. The main text now reports a descriptive 1.96–4.14 ratio of the
  scene-averaged, repeat-corrected squared magnitudes, with the shared artist-free
  baseline explicit. It retains the corrected cosine range .689–.930 and its
  parallel-direction anchor. The endpoint model names are omitted for space;
  their values are retained in the supporting record.
  [CONTROL_MAGNITUDE_SUMMARY.json](CONTROL_MAGNITUDE_SUMMARY.json) records all
  six quotients, components, cosine values and source hashes. The numerator
  is primary common_ss divided by four, not the four-arm total or Table 3's
  shared/total percentage. The ratio is descriptive; no uncertainty test or
  claim of an unbiased ratio is added.

This adds a compact descriptive ratio calculated from existing stored components;
it changes no scientific record, estimator, input, image, experiment or human
evaluation. All tables and figures remain byte-identical to round 30.
