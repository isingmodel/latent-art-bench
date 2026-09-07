# Manuscript rewrite: skeptical review and revision

Date: 2026-09-07. Scope: the editable English manuscript and presentation figures.
The scientific data, analysis, frozen protocols and published reports are unchanged.

## Review process

The coordinator wrote a new, complete `paper.tex` from a blank source. Three
maintainer-run LLM subagents then reviewed that draft: `revision_validation`
assessed the argument, contribution, literature positioning and scientific prose;
`revision_metrics` checked the design, equations, numerical claims and inference;
`revision_detection` checked visualization, detection, coverage and figure clarity.
The coordinator adjudicated their findings, revised the draft and visually
inspected all final PDF pages. These are internal LLM reviews, not independent
human or institutional peer review.

The replacement is an 11-page research manuscript with three vector figures,
two tables and short technical appendices. Its argument proceeds from the prompt
intervention to proximity, the within/between-description decomposition, and
measurement limits. It no longer narrates the project's budget, collection
interruptions, freeze process, implementation review or future recruitment plan.

## Findings and responses

| Review finding | Revision |
|---|---|
| Family rescaling was ambiguous and described as equalizing coordinate counts. | State division by the square root of family dimension and its squared-distance interpretation; observed variance is not equalized. |
| “Source groups” could imply photographic capture control. | Define exact holding-collection-ID sets and distinguish them from capture workflows. |
| Deletion diagnostics omitted how reference weights change. | State preserved class masses for work/collection deletion and renormalization after class deletion. |
| Aggregate contraction could sound inferential or relative to originals in every view. | Describe empirical variation, explicitly identify the artist-free denominator in the abstract, and limit consistency claims to the fixed diagnostic grid. |
| Painter interaction could imply that each collection is individually nearest its own painter. | State that joint own-painter alignment does not guarantee individual own-nearest results. |
| Detector transfer needed reproducible kernels and precise AUC wording. | Give both kernel formulas, penalty and threshold; distinguish fold-wise AUC averaged across folds from pooled balanced accuracy. |
| Coverage methods lacked sizes and draw counts. | Add 100 draws, full/half reference-panel sizes and largest-remainder class allocation. |
| Specificity interrupted the measurement-robustness subsection. | Move it next to the primary proximity results. |
| Isolated correlation/placebo values added detail without advancing the argument. | Remove those numbers while retaining their interpretation and complete report evidence. |
| Figures and appendices disrupted page flow. | Replace oversized report charts with compact manuscript figures, prevent figures preceding their introduction, and fix orphan lines and the lone-reference final page. |

The reviewers found no confirmed equation error or numerical contradiction in the
new draft. Checks covered all eight primary effects and adjusted p-values, six
variance decompositions, 72 sensitivity comparisons, painter interactions, PCA
proportions and the fixed-threshold/AUC counterexample. A final editorial pass
identified the abstract's missing spread denominator; it was added before delivery.

## Verification

- The 11-page Tectonic build completes without warnings or unresolved references.
- All final pages and all three vector figures were visually inspected.
- The figure builder verifies its three saved-table hashes and reproduces all
  three manuscript PDFs byte-for-byte. It does not refit PCA or compute endpoints.
- Ruff passes; all 886 offline tests pass (88.64 seconds).
- The historical evidence audit passes 2,902 checks with zero failures, retaining
  only the pre-existing acknowledgements and informational drift.
- No source analysis, sealed result or reported scientific value was changed.

The remaining limitations are scientific, not editorial: selected reference
panels, unresolved capture provenance, variable service behavior and absent human
construct validation. The rewrite does not claim that internal review resolves them.
