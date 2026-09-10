# Prospective clause experiment: manuscript integration proposal

Mutable writing proposal, 2026-09-10. This is not a result report or rescoring.
I read all 1,917 lines of the current manuscript, including appendices; TeX
SHA256 `e0be30f058d59140bcb8a30ef5ef89cadb00fd0524ea9b856c5af908febd12e6`.
The DeerFlow academic-paper-review skill and unchanged three-aspect rubric inform
the recommendations. Earlier reviews and scores remain untouched. I authored the
new protocol/scenes and supplied earlier literature/method advice; I am a
maintainer-run LLM, not an independent reviewer. No prospective outcomes, new
image pixels or additional analyses were accessed for this proposal.

## Recommendation and article structure

Keep the research narrative centered on the difference between approaching the
painting panel and predicting named scene means. Current Table 9
(`tab:targets`) is the most direct evidence: adding scale improves Q in every
primary cell but worsens reference energy in five. The new experiment adds two
distinct questions, rather than a replacement headline: does an actual named
clause outperform an actual generic clause, and do the unchanged historical
OAuth maps preserve or change their two-target ordering on new scenes?

1. **Introduction and related work:** retain the present empirical scope. Add
   the generic-control question in one sentence after the moment-map motivation.
   State that the question followed earlier findings but the new outcome
   collection and analysis were fixed prospectively. Do not call the entire
   research program preregistered or investigator-independent.
2. **Overview and four-painter context (current Sections 3–4):** add one compact
   row to Table 1 for 24 new scenes × 3 repeats × 4 actual arms. Preserve Monet,
   Sisley, Pissarro and Cezanne in Figure 1, Tables 2–3, their main-text findings
   and the complete appendix table. Preserve the fact that only Sisley's
   exploratory named median is below its free control; later two-painter results
   do not supersede that cohort.
3. **Original intervention and diagnostics (current Sections 5–7):** retain the
   original eight-test family, temporal FLUX comparison, held-scene maps,
   matched-mean scalar comparison and corrected conditional results. Keep Table 9
   in the main text and refer back to it when introducing prospective predictions.
4. **One short new section immediately after Section 7:** title it
   “Prospective validation with new scenes and a generic clause.” Use roughly
   500–700 words and one two-panel table. Present design, all two primary
   outcomes, then both fixed-map targets. This placement lets the established
   definitions do the methodological work and keeps the prospective test next
   to the predictions it assesses.
5. **Palette and measurement boundaries:** retain both original unresolved
   palette interactions and both later unresolved interactions, with their
   distinct inferential families. New no-palette energy results cannot resolve
   these chroma-response interactions. Keep the measurement section's substantive
   selectivity/resampling limits; it is not a validation of perceived style.
6. **Discussion and conclusion:** synthesize actual control dependence and
   two-target map performance using the observed branches below. Preserve the
   distinction between an attainable generated image and a diagnostic transformed
   coordinate. Do not turn a fixed-map success into a model-mechanism claim.

## Compact methods and displays

The new section needs one design paragraph: the fixed newly authored three-class
panel; four exact clauses without palette text; three repeats; shared F/G outputs;
the unchanged references, scalers and all-31 representation; 72 matched N/G pairs
per painter; conditional other-two-position sign tests with 99,999 draws and
Holm across exactly two endpoints. State the primary completeness and global
duration/identity gates, actual terminal allocation and delivery differences.
Cross-reference the existing energy, paired-statistic, map and Q definitions.
Explain that historical full-cohort OAuth maps were fixed before the new outputs;
the new study uses neither averaged folds nor evaluation-centered T2c.

Use a single table with two panels, both painters always present:

- **A, randomized actual-clause comparison:** available/planned pairs, E(G), E(N),
  N−G, Holm p and availability. No confidence interval has been qualified for
  these energy effects. An unavailable endpoint stays visible.
- **B, descriptive prospective predictions:** E(T1), E(T2), their difference,
  Q(T1), Q(T2) and their difference. Separate the energy and Q column groups and
  state their different units. These are full new-cohort scores, not the old
  four-fold averages; avoid direct old/new magnitude comparisons as time effects.

Report primary-pipeline trace/retrieval directions in a short secondary paragraph
covering both painters, with full arm/weight/pipeline summaries in the numerical
report. All three prespecified pipelines must remain available regardless of
direction. Do not add another feature grid or select a favorable view for the
main table. No new figure is necessary, and the main text need not reproduce
every secondary JSON field.

Reuse Appendix A for two sentences identifying exact clause construction and the
new scene inventory; Appendix C already supplies the swap identity; Appendix J
already supplies the map/Q definitions. Add a short scope note for the fixed
historical OAuth fits. Put precision scenario tables, transport retry details,
all 24 scene texts and computational qualification in the released protocol and
reports, not a new long manuscript appendix. Extend the reproduction section
only after a new artifact is actually published and verified.

## Outcome branches to treat equally

| Actual N−G result | Defensible main-text interpretation |
| --- | --- |
| Negative with Holm rejection | The named clause gives closer measured distributions than this particular generic clause in the fixed comparison. Neither semantic matching of clauses nor an internal artist representation follows. |
| Positive with Holm rejection | The attainable generic-clause outputs are closer to that painting panel. Earlier named-versus-free gains therefore do not establish superiority over this actual generic control. |
| Either sign without rejection | Report sign, magnitude and p-value; the additional naming effect is unresolved. Do not claim generic sufficiency, no effect or equivalence. |
| Mixed painters or unavailable endpoint | Preserve each painter's status in the same table. No pooled winner, complete-case rescue or relabeling of a secondary result as primary. |

For the maps, define ΔE=E(T2)−E(T1) and ΔQ=Q(T2)−Q(T1).
Opposite signs reproduce a two-target disagreement on this new panel; the
particular old pattern is ΔE>0 and ΔQ<0. The reverse signs would still be a
disagreement but would reverse the favored transformations. Same-direction
changes show agreement in this cohort and delimit the earlier pattern; they
must not be recast as confirmation of universal disagreement. Report zero or
near-zero estimates without an invented equivalence threshold. Q can be negative
after correction and has no new test. A missing named arm can leave map energy
available while Q is unavailable. These diagnostic outcomes neither inherit
N−G p-values nor establish a causal account.

The new panel and collection occasion change together. Refer to prospective
evaluation on new scenes, not a separately identified scene-transfer effect,
backend-time effect or unseen-artist generalization.

## Space recovery and positioning

Recover space rather than append another methods narrative. Current Section 5.2
defines the observed variance decomposition and Section 7 explains it again;
keep its equation once and shorten the earlier interpretation. The discussion's
first three paragraphs repeat most Section 6 numbers; retain the two-target
inference and cross-references instead of the numerical recap. The abstract
should replace, rather than append to, its existing diagnostic inventory:
four-painter context, original controlled result, central target disagreement,
the actual prospective N−G and map outcomes, and the measurement limits. Preserve
an explicit statement that both palette collections remain unresolved.

Update Section 7's “transfer to new scenes ... remains untested” and the future
work paragraph only to the extent supported by the completed new study. A fixed
new panel does not remove generalization limits. These edits should recover most
of the new section's prose without demoting Sisley/Pissarro or concealing contrary
results.

Keep the current fair acknowledgment of [Su et al.](https://arxiv.org/html/2507.18633v1):
fixed-content artist substitution, held-out prompts and named/free/real-prototype
comparisons already exist. Keep [Benny et al.](https://link.springer.com/article/10.1007/s11263-020-01424-w)
as prior conditional-evaluation theory and
[Zhang et al.](https://arxiv.org/html/2510.19557v1) as prior empirical evidence that
reference metrics and conditional diversity can move differently. These are
primary sources previously read during this review series, not a fresh systematic
survey. The additional contribution can be the prospectively observed behavior
of an actual generic control and fixed maps on both targets in this painting
setting; it cannot be novelty of name substitution, held-out prompts or the
marginal/conditional distinction itself. No result branch guarantees an
exceptional contribution or a higher score.
