# Revisions after round 20

All three reviews count: 9.25, 9.125 and 9.1875; mean 9.1875.
The fixed rubric and blind review procedure remain unchanged.

- Reviewers A and C requested clearer abstract hierarchy and magnitude wording.
  FLUX's lowest uncalibrated estimate now precedes the retrospective checks.
  “Measured differences” replaces the ambiguous “excess response,” which could
  be mistaken for excessive aligned amplitude. The main text still explains
  the excess total magnitude and shrinkage tradeoff. The abstract remains
  exactly 155 whitespace words, with separate retrospective calibration,
  held-out scoring and unchanged images.
- Reviewer A requested a meaningful color scale for pair response. Figure 3(a)
  now uses linear cividis_r for signed beta values, with explicit zero/no-alignment
  and one/reference-strength markers. It is not a goodness scale. All 72 values,
  annotation text/positions/fonts, dimensions and limits remain identical;
  Figure 3(b) is pixel-identical. Cell numeral colors maintain at least 4.66:1
  contrast, and marker labels fit without collisions. Figure replay and Ruff pass.
- Reviewer C requested a direct geometry-reading rule. Figure 2 now states that
  shorter matching-label lines indicate less projected mismatch; the all-feature
  limitation and scene/repeat averaging remain explicit.
- Reviewer A requested unambiguous cropping language. Section 5.5 now specifies
  crops that exclude peripheral artifacts, with no human verification.
- Reviewers B and C requested labeling Table 10's two values at the point of
  reading. A compact header key names energy change and total variance ratio;
  the shortened caption retains both directions, empirical/descriptive status,
  and no added tests. All numerical cells and the primary table remain unchanged;
  exact table replay and Ruff pass.
- Reviewer B requested a link back to the tangible example. Section 5.3 now
  connects the single lightness coordinate in Section 4.1 to the all-31-feature
  pair comparison, without claiming lightness explains its aggregate result.
- Reviewer B requested explicit inputs and targets for the historical maps.
  A read-only source/protocol check confirms that individual artist-free feature
  vectors are translated, optionally scaled, and evaluated against named-prompt
  conditional scene means. Fits use generated-cloud moments, not reference
  optimization or scene-mean least squares. Appendix F.2 names input and target
  immediately. Historical and prospective contrary results remain intact.

The paper remains 22 pages, with no changed scientific input, result, image
source or inferential procedure. The historical map check used geometry.py
and analysis.py under painter_naming_geometry_v1, the associated protocol,
and painter_map_validation_v2's protocol, analysis and retained report.
