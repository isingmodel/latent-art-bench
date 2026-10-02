# Round 6 → final revision (not reviewed)

Round 6 reviewed PDF `4ae5600e…` (32 pages). The round does not pass the rubric: criterion 2 was *partially* for the editor, criterion 1 was *partially* for the empirical reviewer, and each reviewer reported at least one factual error. Round 6 is the last round the [rubric](../rubric.md) allows (at most six), so the review loop stops here.

| Reviewer | Recommendation | Criterion 1 (claims and evidence) | Criterion 2 (audience and clarity) | Desk risk | Factual errors reported |
| --- | --- | --- | --- | --- | --- |
| Methods | minor revision | *yes* | *yes* | none | 1 |
| Empirical | minor revision | *partially* | *yes* | low | 1 |
| Editor | minor revision | *yes* | *partially* | low | 3 |

**Prompts.** Identical to round 5 except for the round paths, the page range and the supplementary list, which added the diagnostics-v5 plan.

The changes below were made after round 6 and **have not been reviewed**. No new analysis was run. Every new number comes from recorded outputs and is checked by the builder.

## Critical issues and responses

| Issue (reviewer) | Response |
| --- | --- |
| The supplementary archive packed `make_supplement.py`, whose identifier regex names the author, and exempted it from its own scan (editor) | The packager is now excluded from the archive. The self-exemption is removed. Identifiers come from the `SUPPLEMENT_IDENTIFIERS` environment variable, and the scan now also covers decompressed `.gz` files, raw PDF bytes and the written zip. The rebuilt archive (72 files, 54.4 MiB) passes this scan and an independent re-scan. |
| Sign error: the drift model's squared prediction error rose by 0.7–3.4%; it did not fall (methods) | Corrected in Appendix A and registered as a new claim. |
| The protocol ranked configurations only on D, and the alignment-ratio ranking was defined after collection (methods, empirical) | Now stated in §4.5, the abstract and intro bullet 3. §4.5 no longer says the post-hoc plans were "fixed before [their] outcomes were computed". Intro bullet 3 now gives the prespecified outcome: 2 of 15 pairwise differences resolved. |
| The alignment ratio is not "direction regardless of size", because it also penalizes variation across scenes (empirical, methods) | Redefined in §4.3 and the table captions. The scene-averaged alignment β/√(B/H) is added; it also ranks GPT Image 2 first in all three representations (0.699, 0.711, 0.782). D_held is noted to largely restate the alignment ratio. |
| Recognition does not reward direction "whatever their size" (empirical, factual error) | Corrected in §5.4 and intro bullet 4. Recognition "rises with" the alignment ratio across the six configurations, and it also depends on size relative to image spread and on shared offsets. |
| The intro's D > 1 verdicts were unqualified (all three) | Bullet 3 now names Flare and Sunburst, adds "GPT Image 1 too, but not after a multiplicity adjustment", and is marked as descriptive. |
| Factual errors: faithful benchmark called an "upper reference"; "Table 8 lists every symbol"; Figure 5 missing from Appendix H's list of generated figures (editor) | All three corrected. |

## Minor changes

- The Spearman correlations are now described as rank agreement over six configurations.
- The CLIP scene-averaged errors are all below 1 (0.587–0.798). All CLIP errors above 1 therefore come from variation across scenes.
- The content claim is narrowed to reference-side content matching.
- The Figure 3 caption notes that the faithful benchmark in the embeddings inherits the reference works' variety. Their mean embeddings are shorter, markedly so in CSD.
- The K-painter form Hβ/K of the painter-specific term is added.
- Top-k similarity is named among the readouts outside Eq. 4's scope.
- The Verma et al. wording is made more general.
- The claim "as in CSD's prototype scoring" is removed.
- §6 now says "whenever β ≤ 1".
- Model selection now says "distinguishable outputs", not distinct generators.
- The four eligible reference works that failed measurement are reported: one had a transparent layer, three used unprofiled non-RGB color spaces.
- Bold in Table 3 is now defined as "largest (lowest for D)".
- "(less for Cézanne alone)" is clarified.
- The label overlaps in Figures 1 and 5 are fixed.
- Appendix H no longer uses "registered sentence context".

## Not changed (owner decisions or new evidence)

- **Images:** no release commitment for the generated images and no contact sheets.
- **New data:** no human check of the AI crops and content labels, no positive or generic-name control, and no third repeat.
- **Unreviewed extras:** no recognition intervals, no raw-proximity column and no content probes of the generated images.
- **Length:** the main text is about 13.3 pages. It must be declared a long submission on OpenReview, or cut further.
- **Metadata:** the empirical reviewer's report of a KST time zone in the PDF metadata is a display artifact of `pdfinfo`. The raw CreationDate is `D:20260101000000-00'00'` (UTC).
