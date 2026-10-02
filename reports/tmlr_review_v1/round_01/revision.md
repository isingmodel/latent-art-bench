# Round 1 → revision

Round 1 reviewed PDF `33c87a6f…` (20 pages). All three reviewers (methods, empirical,
editor) recommended **major revision**; each answered criterion 1 (claims and evidence)
*partially*, criterion 2 (audience and clarity) *yes*, and rated desk-rejection risk
*low*. The round does not pass the rubric. All six review files are unchanged.

## New analysis

A post-result analysis, [`painter_tmlr_diagnostics_v1`](../../painter_tmlr_diagnostics_v1/REPORT.md),
was planned before any of its quantities were computed by this project
([plan](../../../studies/painter_tmlr_diagnostics_v1/PLAN.md)). Addenda A and B record
that the empirical and methods reviewers had already computed some of the same values
(faithful-imitation fractions, texture fractions, bootstrap orderings) before the module
ran; the module's results agree with those reports. It uses retained vectors and
embeddings only; `make retrospective-check` replays it exactly, and 8 constructed-data
tests are in the routine suite.

## Critical issues and responses

| Issue (reviewers) | Response |
| --- | --- |
| Shared fraction has no benchmark; a faithful imitator may share more (all three) | Added the exchangeable null (25%) and the faithful-imitation value. The faithful value exceeds the observed fraction in every configuration and representation (31 features 84.8–95.2% vs 66.7–88.4%). The paper is reframed: proximity gain mostly measures shared movement, even for a faithful imitator, so specificity is read from the between-name comparison. New title, abstract, introduction, Section 5.1–5.2, Figure 3 |
| Direction of the shared change only shown in embeddings; §6 overclaim (editor, empirical) | Added cosine to the reference centroid (0.57–0.86), gap covered (24.8–64.6%), an exact 31-feature centroid-proximity decomposition, and the share along the generic shift (52.8–55.5% for Nano Banana 2 and FLUX.2 Max). Discussion rewritten; "dominates" removed where the share is near 54% |
| No feature-family or weighting sensitivity for the main collection (all three) | New Table 6: families, equal-family and covariance weightings, leave-one-feature-out; texture is least shared in both collections. §5.6 corrected: the split does not depend on the reference collection, but its benchmarks and B/H do |
| Readout-ranking claim has no uncertainty (all three) | Scene bootstrap (5,000 paired resamples) and deletion ranges; new Table 5; text states which orderings are stable and which are not |
| Squared ratios read as linear (editor) | Root-mean-square equivalents given; N/H no longer used as a headline |
| Prespecified reference resampling unreported (methods, empirical) | Added to Table 2 and §5.3 |
| Genuine-painting control for D unreported (methods) | Added to §5.3 and Appendix D |
| Scope and generic-painterliness alternative (empirical, editor) | Title scoped to four painters; limitation and Discussion state that a generic artist-name effect cannot be excluded |

## Factual errors corrected

- Appendix A: repeat dependence biases D **upward**, not downward (methods); the third
  covariance crossing (GPT Image 1–FLUX.2 Max, ρ = 0.688) is now named (editor).
- Related work: Fu et al. do not name a dataset "AI-WikiArt"; Moayeri et al.'s at-risk
  criterion also requires recognition in generated images; Su et al.'s same-seed
  artist-removed comparison is acknowledged; Casper et al. 2023, Kumari et al. 2023 and
  DiffusionDB added (empirical).
- Prompts spelled "Paul Cezanne" without the accent; stated (empirical).
- Table 4 ties bolded consistently (empirical, editor).

## Minor changes

Estimand table (Appendix C); consistent terminology ("shared fraction", "between-name",
"painter-specific" only for the aligned term); de-overloaded symbols (Ref./Shift/Gen.
rules, κ, N_free); geometry schematic (Figure 1) replaces the old component bar chart;
gateway and configurations named; reference inclusion criteria and subject mix;
SD-Turbo scene texts described; AI-assistance statement; finite-sample bias of H;
repeat noise per configuration; within-scene generic-baseline shares; caption spacing;
BibTeX capitalization.

## Not changed

- No human verification of the AI-proposed crops and no human evaluation (the owner
  excluded human evaluation; the limitation is stated).
- Generated images are not released with the submission (owner's decision pending).
- No new image generation (out-group painters or a family clause); stated as the test
  that would separate family resemblance from a generic artist-name effect.
