# Revisions after round 12

All three independent reviews count: 9.125, 9.25 and 9.25; mean
9.208333333333334. The fixed rubric and scoring procedure remain unchanged.

- Reviewer A requested pair-scale information in the Figure 3 caption. It now
  states that each pair uses all 31 features and is normalized by its squared
  reference distance. An independent read-only check verified the formula against
  painter_specificity_review_v1.py:37 and :295. No heatmap values changed.
- Reviewer A requested a more direct discussion implication. The opening now
  leads with the recommendation to report aligned response, both error versions
  and painter-pair coverage; it explains why low error alone is insufficient.
- Reviewer B found the visual-label sensitivity easy to confuse with primary
  class equalization. The final Section 5.5 paragraph now identifies class-specific
  reference means, the 11 included briefs and the three excluded mixed briefs.
  A read-only code check confirmed FLUX remains the minimum in both implemented
  visual-label views (original images/scaler and cropped images/refitted scaler).
- Reviewer B requested simpler Appendix F.2 terminology. “Generated-only moment
  maps” and “review-driven ... counterfactual” become translation/scaling maps
  fitted to historical generated images and retrospective painter-contrast
  calibration. The contrary prospective finding and all numbers remain intact.
- Reviewer C requested a distinction between contrast calibration and reference
  treatment. Tables 2–3 use “uncalibrated”; Table 3 specifies full-frame references;
  Table 4 labels full-frame and crop-corrected differences and explicitly identifies
  uncalibrated error. Its caption retains the refitted-scaler and retrospective
  interval qualifications.
- Reviewer C requested visual emphasis for Table 3. Only the three error-column
  minima are bold; the scene-variation column is unranked. The caption explicitly
  says bold is not significance. Every numerical row was compared with round 12
  after stripping bold markup and is unchanged.
- Reviewer C identified paragraphs interrupted by floats. The content-target
  paragraph and final coordinate-deletion sentences are kept together. Appendix
  weighting prose was shortened while preserving the exact metric and results.

All figures are byte-identical to round 12. The relevant table builders, replay
checks, scoped Ruff and git diff --check passed. No new evidence, experiments,
image requests or human evaluation were added.
