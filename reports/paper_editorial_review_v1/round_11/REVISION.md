# Revisions after round 11

All three independent reviews count: 9.125, 9.0625 and 9.0; mean 9.0625.
The fixed rubric and scoring procedure remain unchanged.

- All reviewers found the abstract’s multiplier/contrast phrase unnecessarily
  compressed. It now says that painter differences are uniformly rescaled to
  minimize error on 13 scenes, with evaluation on the remaining scene in turn.
  The operation, objective and held-out procedure are explicit within 155 words.
- Reviewers A and B asked the conclusion to restore the dominant shared response.
  Its opening now gives that finding, retaining the no-distinction benchmark,
  uneven artist-pair agreement, calibration and source-correction qualification.
- Reviewer B noted ambiguity about title/visual labels. The robustness paragraph
  now identifies them as reference labels and directs readers to Appendix C for
  the classes and controls.
- Reviewer C asked when the primary inferential family was declared. An independent
  read-only protocol check confirmed the six-plus-15 family existed in precollection
  commit d223402 and the frozen protocol preceded generation. The main text now
  says “Before inspecting the new feature outcomes”; “new” preserves the fact
  that historical reference measurements had already been exposed. The table
  caption uses “prespecified family.” Supporting files: studies/painter_specificity_v2/
  PROTOCOL.md:86–88; data/manifests/painter_specificity_v2/psv2-20260911/freeze.json;
  attempts.jsonl; measurement_receipt.json. No protocol or evidence file was edited.
- Reviewer C requested interpretation in the discussion instead of repeated metric
  definitions. Its opening connects the original and calibrated point-estimate
  leaders to response strength and painter-difference patterns, and explains why
  both scores and painter-pair coverage are useful.

The introductory overview was also shortened without dropping its design,
noise-correction assumptions or contribution, keeping it entirely on page 1.

No experimental result, input data, inferential procedure or scientific analysis
was changed. Generated table wording was replayed; no human evaluation was added.
