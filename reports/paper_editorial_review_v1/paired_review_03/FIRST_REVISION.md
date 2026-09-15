# First revision before fresh paired review

The user's required order is **revise → evaluate in new sessions → revise again**.
The `*_review_02` requests were cancelled when that order was clarified; they
provide no accepted assessments or scores. This first revision addresses valid
findings from the completed `*_review_01` reviews of the frozen round-33 paper.

The frozen evaluation input is recorded in `INPUT_SNAPSHOT.json`. It has 22
pages and a 151-word abstract. Its PDF SHA-256 is
`136e17776537dd95e62201522a485b731ced7200c4caa24b5086c59206fc1524`.
`FIRST_REVISION.diff` records the textual changes from round 33.

## Accepted changes

- Rewrote the abstract's shared-effect and calibration statements: the common
  change includes the oil-painting clause, and FLUX's lowest uncalibrated error
  is distinguished from GPT Image 2's lowest held-out calibrated estimate.
  The abstract remains 151 words.
- Explained the primary cross-partition estimator and complementary energy
  statistic in related work, preserving the citations and method distinctions.
- Introduced short model names at their first list and described the separate
  development panel as setting common feature units.
- Explained the 21-comparison interval family and the unadjusted, descriptive
  absolute-error intervals in plain language, preserving the fixed-scene and
  repeat-dependence qualifications.
- Added matching outline rectangles in the Figure 2 overview panels to identify
  the adjacent enlarged region. Axes, points, lines, labels and dimensions are
  unchanged; all four painters remain visible.
- Explained why a negative pair alignment makes a label swap reduce error,
  and anchored squared contrast size at Q = 1 in the main text.
- Removed redundant qualifications in selected captions while preserving the
  relevant primary, retrospective and historical distinctions at their actual
  locations. Clarified that Table 5's second column uses both cropping and
  development-scaling correction.
- Led Discussion with the distinction between name response and agreement with
  painter differences, and made Conclusion's practical implication explicit.
- Moved a brief historical model-identity qualification to Appendix F's opening;
  the full provenance limitation remains in Appendix G.

## Suggestions not adopted

The first Claude review miscounted the abstract, recommended adding wording
that would exceed its cap, and suggested replacing a correctly computed
86.99% with a sum of rounded axis labels. The exact combined variance is
86.98639269401075%; the manuscript's 86.99% is retained.

A blanket declaration that several sections and appendices are retrospective
would misclassify prespecified comparisons and separate historical inferential
families. Qualifications were consolidated locally instead. The prospective
contrary transfer result and all existing uncertainty limits are retained.

No experiments, human evaluation, scientific estimates, image examples or
inference families were added or changed. Builder replay, Ruff, whitespace
checks, PDF build and layout inspection are recorded in `FIRST_REVISION_QA.json`.

## Fresh review conditions

Both reviewers receive this changed manuscript and the unchanged version-1
rubric. They receive no previous scores, reviews, stopping target or conversation
history. Claude Code uses a fresh, nonpersistent isolated session with Opus 5;
Astra uses the user's local OAuth core client with `gpt-6-astra`, `xhigh`, and
no previous response or stored client conversation. The manuscript is frozen
during evaluation. The final second revision will be recorded separately;
these review scores will not be presented as scores of that later revision.
