# Integrated manuscript review and revision

The current `paper/paper.tex` integrates Study 1 (1,006 generated images), its
descriptive diagnostics, and Study 2 (192 primary images). The 49-image incomplete
predecessor remains ancillary. The underlying scientific records were not changed.
This is a revision of the research paper, not an additional experiment.

Three maintainer-run LLM subagents reviewed the complete manuscript for statistical
accuracy, scientific interpretation, literature and writing quality, and figure
consistency, with coordinator checks. These are internal computational/editorial
reviews, not independent human or institutional peer review.

## Findings and revisions

| Review finding | Revision |
| --- | --- |
| Adding results as a separate project update would fragment the argument. | Reorganized the abstract, introduction, methods, results, discussion and conclusion around proximity, scene distinguishability and the controlled color experiment. |
| The old short-scene named arm and new generic style arm could be confused. | Renamed the old condition consistently in text, tables and PCA legend; explained that both old named arms include the painter. |
| A generic-versus-named comparison could be misread as a factorial isolation of artist identity. | Described the clauses as alternatives and restricted conclusions to comparison with this particular generic clause. |
| Retrieval is invariant to uniform positive rescaling. | Explicitly separated relative scene distinguishability from absolute response gain and narrowed the abstract and conclusion. |
| The two studies have different inference and weighting. | Kept the eight sharp-null tests separate from the two approximate interaction tests; distinguished reference-class-weighted variation from equal-scene retrieval diagnostics. |
| Fixed scenes do not make their estimated means nonrandom. | Clarified the finite-scene estimand and gave the within-scene covariance and Welch–Satterthwaite formulas, preserving generation noise. |
| The new request order and rendering settings needed precision. | Specified randomized blocks and within-block order, requested rendering, actual delivery differences and the total-service estimand. |
| Null results and processing sensitivity could be overstated. | Preserved both unresolved primary interactions and identified the JPEG boundary crossing as descriptive. |
| Original/generated range overlap could imply distributional equivalence. | Reported directional mass occupancy with means and Wasserstein distance; explicitly identified the forced two-polarity mixture. |
| Peripheral results and implementation details could obscure the paper. | Moved painter alignment and PCA/detection specifications to the appendix and retained peripheral coverage variants in the full analysis reports; kept acquisition exclusion accounting brief and operational histories outside the article. |
| Prior-work positioning required precise scope. | Refined the Kim and CLIP-separation descriptions; added only T2I-CompBench to distinguish global chroma response from semantic color binding. |
| Reproduction requirements differ by task. | Distinguished figure rebuilding from committed tables from full integrity-checked replay requiring the separately retained response archive. |

The statistical review verified cohort counts, primary effects, intervals, adjusted
p-values, original-reference summaries and acquisition accounting against the
frozen results. The two new manuscript figures extract saved retrieval accuracies,
arm means and primary intervals from hash-checked tables. The existing energy and
variation figures remain byte-identical; the PCA data are unchanged and only its
condition label is revised. Weighted quantile interpretation follows the published
exact-weight correction, with no changes to primary results.

## Verification

All five manuscript figures reproduce byte for byte. The complete offline suite
passes **1,135 tests in 115.42 seconds**, and Ruff passes. Input-hash and missing-cell
probes reject altered or incomplete figure inputs. The final 16-page PDF builds
without TeX warnings. All citations and cross-references resolve. The coordinator
visually inspected pages 1–8 and a maintainer-run LLM reviewer inspected every page
9–16; no clipping, overlap, missing glyphs, cropped equations or reference overflow
remained. Both mathematical notation and the distinction between condition means
and interaction intervals are legible in the final rendering.

Remaining scientific limits are retained in the manuscript: selected digital
reference panels, one service and six scenes in Study 2, approximate small-repeat
inference, unvalidated perceptual interpretation, and differing delivered geometry
and quality. The paper does not claim that a latent model mechanism is identified.
