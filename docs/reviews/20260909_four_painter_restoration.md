# Four-painter manuscript restoration — 2026-09-09

The user identified that the manuscript had dropped substantive analysis of
Sisley and Pissarro. This correction restores the retained four-painter evidence
to the main paper. It changes presentation and navigation, not scientific
measurements, completed protocols or inference.

## Why the coverage narrowed

The [September 6 proposal](../RESEARCH_PROPOSAL_20260906.md) prioritized new
service families and improved reference controls within the $75 ceiling. It
selected Monet/Cézanne for new collection after observing earlier results, while
explicitly retaining Sisley/Pissarro in existing-data diagnostics. The
[controlled protocol](../../studies/painter_distribution_study_v1/PROTOCOL.md)
records the same boundary. Neither document required removing two artists from
the paper.

A maintainer-run LLM subagent traced the writing history: proposal `e401364` and
protocol `ad79194` establish the scope; prototype `1c5b7b4` includes substantive
four-painter development evidence; `c092a6e` compresses it; rewrite `52fa1d6`
removes the artists' names, counts and findings, leaving a vague reference to
earlier exploration. Subsequent manuscripts inherited that editorial omission.
The data and complete reports were retained throughout.

## Restored evidence and presentation

- Main-text exploratory analysis: 649 references (Monet 297, Sisley 106,
  Pissarro 141, Cézanne 105), 1,536 painter-conditioned outputs and 384 shared
  artist-free controls. These remain separate from the 70-reference/1,006-output
  controlled study and 192-image color experiment.
- A twelve-panel figure shows all four painters, all three prompt methods and
  both requested aliases using the saved balanced PCA coordinates. All points,
  outliers and two later retry identities remain visible; no new PCA is fitted.
- Main tables report all-painter ranges of sample-trace ratios and both fixed
  classifiers, plus matched-size original/original, named/original and
  artist-free/original energy baselines. The appendix retains every one of the
  24 alias/painter/method cells.
- Abstract, introduction, common feature methods, discussion, conclusion and
  artifact access now cover the four-painter evidence. The controlled studies'
  primary tests and numerical results are unchanged.
- `make four-painter-analysis` groups the three existing nonwriting replay
  commands; `make figures-check` now verifies six manuscript figures. The five
  earlier figure PDFs are byte-unchanged.

The exploratory complete grid includes two later retries and does not regain
the original randomized complete-grid inference. Aliases are requested service
labels, not attested independent model snapshots. The restored comparisons are
post-hoc finite-panel descriptions; they do not establish population separation,
perceptual fidelity or the controlled naming effect for Sisley/Pissarro.

## Skeptical review and responses

Two maintainer-run LLM subagents reviewed the restoration. These are internal
reviews, not independent human or institutional peer review. They did not assign
scores. The earlier 8.5417 score applies only to the prior 19-page manuscript.

| Review | Finding | Response |
| --- | --- | --- |
| Evidence and methods | All 24 appendix rows, four-painter ranges, counts, PCA fractions and matched-size medians match saved tables. Fixed kernel bandwidth and intercept should be explicit. | Added the exact linear/RBF kernels and regularized intercept; retained both classifiers. |
| Scope and paper quality | Restoration is substantive and preserves distinct cohorts, but pooled exploratory medians must not be described as a controlled naming effect. | Reworded results and discussion as descriptive orderings. |
| Scope and paper quality | Artist-free discrimination is an important competing explanation. | Added artist-free RBF accuracy .915–.990 and trace ratios .369–.750; retained the artist-free energy column and the Sisley-only lower named median. |
| Scope and paper quality | Defensive explanations about artist suitability and an opaque contribution sentence weaken research prose. | Removed the defensive sentence and stated the contribution directly; selection timing and resource rationale remain explicit. |
| Visual review | Bottom float placement created large gaps; a feature-inventory heading separated from its table. | Revised float placement and kept the feature heading/table together. Final page inspection is recorded below. |

## Sources and verification

The [exploration bundle](../../reports/painter_distribution_exploration_v1/REPORT.md)
supplies `points.csv`, `projections.json`, `spread.csv` and `separability.csv`.
Its recorded implementation is `1a8065b037d3b1f53e7b28aa3bbb277921ad9976`.
The [Stage A diagnostics](../../reports/painter_distribution_study_v1/pdsv1-diagnostics-20260906/REPORT.md)
supply `reference_splits.csv`, `matched_comparisons.csv`, `cells.csv` and
`classifiers.csv`; generated baseline medians summarize 768 distance estimates
per painter/condition, not pooled images. The
[retry presentation](../../reports/painter_prompt_retry_v1/ppr1-two-refusals-20260906-r2/REPORT.md)
supplies the 24/24 and 13/24 feature-family prompt directions. Each bundle keeps
its own provenance and immutable inputs.

Executed checks:

- Small relevant offline suite: 19 passed.
- Full offline suite: 1,135 passed in 113.56 seconds; Ruff passed.
- Exploration replay: 35 files; Stage A replay: 18 files; retry presentation
  replay: 9 files, no numerical changes. All 62 report files reproduce.
- Historical evidence audit: 2,902 checks, zero failures, only the two existing
  acknowledgements. This is an integrity audit, separate from numerical replay.
- `make paper`: 24-page PDF, six vector figures, no TeX warnings. All 24 pages
  were visually inspected by the maintainer and its LLM reviewer; the revised
  table/figure placements and feature-inventory grouping pass final inspection.
- `make figures-check`: all six figures reproduce byte for byte. The previous
  five figure files remain identical to the pre-correction version.
- All 316 checked local documentation links resolve; `git diff --check` passes.
- SHA-256 checks confirm both user-owned Korean files are unchanged.

Delivered artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| `paper/paper.tex` | `510738e56bd56ec081a83d6d39ee317a6cd3ce296dcb4f97201fa0fe396ecfe9` |
| `paper/paper.pdf` | `79f6cf4f697880734a894a3e4f61b0f3acbe4f67e4b4359bb0e83bc424356103` |
| `paper/figures/four_painter_distributions.pdf` | `e2caed73ab1161798a3e3f7f3efda76343933bc15e841f21db5813e3ae6423a8` |

No new image requests, artwork access or feature extraction occurred. Frozen
scientific sources, evidence and ledgers were preserved. User-owned Korean
manuscript files were not edited or included in the correction.
