# Revisions after round 16

All three reviews count: 8.9375, 8.9375 and 9.0; mean 8.958333333333334.
The rubric, blind review prompt and scoring procedure remain unchanged.

- Reviewers A and C identified a dense calibration passage in the abstract.
  It now states the single multiplier per model, 13-scene fitting and omitted-scene
  scoring in one clause, followed by the excess-size explanation and changed
  leading estimate. Calibration remains explicitly separate and retrospective;
  images remain unchanged. The abstract falls from 155 to 152 whitespace words.
  The fitting objective remains explicit in the main method.
- Reviewers A and C found Figure 2's centroid details too small. Detail axes gain
  width within the same figure footprint; their ticks, titles and reference
  letters increase to 8 points, with stronger marker outlines. The six overview
  panels, all 756 scatter points and 54 line artists (including detail duplicates),
  numerical coordinates and all axis limits are preserved.
- Reviewer B asked how shrinkage helps despite weakening the near-unit aligned
  response. Section 5.4 now states the tradeoff directly. A read-only replay of
  the actual 14 held-out multipliers verifies that aligned response decreases
  from .998650 to .448730, the aligned-amplitude error rises from -.003006 to
  .303412, and the off-axis error falls from 1.228937 to .250890, reproducing
  the retained total change from 1.225931 to .554301. These supporting numbers
  are not added to the paper; no new analysis result is claimed.
- All three reviewers requested a more synthetic Discussion. Its opening now
  connects shared appearance, painter-pair distinctions, scene averaging and
  calibration to the evaluation choices a reader should report. It replaces
  a repeated model/ranking recap; the numerical evidence remains in Results.

No scientific input, result, image or inferential procedure was altered.
