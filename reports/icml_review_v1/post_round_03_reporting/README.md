# Unscored literature correction after round 03

The current ICML PDF remains **8 main pages, 46 total**, using the unmodified
official provisional ICML 2026 style. SHA-256:
`115f9ff33762e932d44fa3e8dbc9582af5f4ffd6a13e8406695c4eb43de89147`.
The exact PDF and two changed source files are preserved here and bound by
[inputs.json](inputs.json).

## Changes and evidence

- Added the omitted [Frochte CSD diagnostic preprint, version 2](https://arxiv.org/html/2605.09030v2),
  which studies absolute-score interpretation and pair verification and
  explicitly excludes closed-set discrimination. The comparison distinguishes
  this paper's controlled name intervention and separate prompt-name decisions.
- Clarified the generated-versus-real retrieval precedent in
  [Su et al., Sections 9.1 and 9.4](https://arxiv.org/html/2507.18633v1), rather
  than presenting a generated-domain recognition advantage as new.
- Shortened the Introduction to preserve the eight-page main-body limit.

These are literature and presentation corrections. All source from Design and
Measurements onward and every numerical artifact remain byte-identical to
round 03. All 46 pages were rendered. Independent [editorial QA](editorial_qa.md)
inspected pages 1–10; root inspected contacts for pages 11–46. No clipping,
overlap, missing glyphs or unresolved citations were observed. Text on pages
3–8 and 11–46 is byte-identical to the reviewed version's extracted text.
See [render evidence](render_evidence.json). The format check passes.

## Scoring boundary and remaining work

The three round-03 recommendations remain **4, 4, 4; mean 4.0**, attached only
to their frozen input. No fourth round or new score is warranted by this
editorial correction. The requested scientific threshold remains unmet.

The [corrected prospective design](../prospective_controls_v3.md) addresses the
need for independent requests, a contemporaneous family prompt and a frozen
old-to-new recognition test. Its budget, storage and executable qualification
remain outstanding. The [new external-data check](../frochte_external_feasibility.md)
found no accessible compact release that could currently substitute for those
observations. The [numerical bundle](../numeric_bundle_v1/README.md) improves
portability without supplying new evidence or a public pixel archive.
