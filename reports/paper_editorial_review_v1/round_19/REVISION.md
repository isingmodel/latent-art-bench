# Revisions after round 19

All three reviews count: 9.1875, 9.25 and 9.1875; mean 9.208333333333334.
The fixed rubric and blind review procedure remain unchanged.

- Reviewer A found “displacing FLUX” implicit in the abstract. The replacement
  explicitly identifies GPT Image 2's lowest held-out calibrated error estimate
  and FLUX's lowest uncalibrated estimate, while retaining the excess-response
  shrinkage rationale, separate retrospective calibration and unchanged images.
  The abstract is 155 whitespace words, within the original ceiling.
- Reviewer A requested distinguishing displayed reference regions from the
  primary scoring regions. Figure 1 now says the audited regions are for
  display and primary scores use full frames. Appendix D still records which
  two examples are cropped; source sensitivities remain in Section 5.5.
- Reviewer B requested recognizable reference labels. Figure 1 replaces four
  Q-identifiers with shortened titles from the recorded metadata: Rocks at
  Port-Goulphar; The Loing and the Mills of Moret; River Oise near Pontoise;
  Along the Banks of the Marne. Full titles and IDs remain in the manifest,
  which gains only four display_title fields. All 40 image arrays, crops,
  extents, axes positions and limits, and the 6.7-by-7.4-inch footprint are
  unchanged. The separate control PDF is byte-identical. All source hashes
  and exact PDF/manifest replay pass; two-line labels fit their existing cells.
- Reviewer C requested explicit scene averaging in Figure 2. Its caption now
  states that circles average generated contrasts over all 14 scenes and both
  repeats, with lines joining painter labels. This prevents treating projected
  mean distances as a direct picture of the scene-by-scene primary error.
- Reviewer A requested avoiding conflation of weak alignment and weak separation.
  Section 5.3 now says pair diagnostics locate weaker reference alignment.
- Reviewers B and C requested moving the energy-metric introduction beside its
  appendix-only outcomes. Section 4.4 retains the control-arm explanation and
  calibration method; Appendix E now defines energy and links to the unchanged
  formulas/correction in B and C. Consolidation preserves every collection-level
  result and subject-mixture qualification while reducing main-text burden.
- Reviewer C requested more direct reporting advice. The Discussion's nested
  subject is replaced with two short sentences about reporting the scores and
  declaring the scene-aggregation choice.

The paper remains 22 pages. Scientific inputs, results, source images and
inferential procedures remain unchanged.
