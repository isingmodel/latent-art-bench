# Round 1 → triage (no revision yet)

The owner asked for this round on 2026-10-03 ("Run a new review round on this revision"). It
reviewed PDF `af4eea64…` (38 pages; `paper/tmlr` at commit `8ab2a67`). The three reviewers are
fresh language-model subagents. Their prompts are those of round 6 of the first record, with three
changes: the round paths, the page range, and the supplementary list, which adds the second
collection's protocol, its records and the diagnostics-v6 plan. The exact prompts are in
[`prompts.json`](prompts.json).

**The round does not pass the [rubric](../rubric.md).** All three reviewers answered criterion 1
*partially*, and four factual errors are confirmed below. No revision has been made yet; this
record only checks the reviewers' claims.

| Reviewer | Recommendation | Criterion 1 (claims and evidence) | Criterion 2 (audience and clarity) | Desk risk | Factual errors reported | Confirmed |
| --- | --- | --- | --- | --- | --- | --- |
| Methods | minor revision | *partially* | *yes* | low | 1 | 1 |
| Empirical | minor revision | *partially* | *yes* | low | 3 | 3 |
| Editor | minor revision | *partially* | *yes* | low | 0 | — |

Each reviewer gave confidence 4. All three report the same PDF hash, and they changed no file other
than their own outputs.

## Critical issues raised by more than one reviewer

| Issue | Raised by | Check |
| --- | --- | --- |
| **The closeness claim is too strong.** The abstract says the second collection "confirms" that the shared fraction follows closeness, and §5.2 is titled "The shared fraction tracks how close the painters are". | all three | **Valid.** Table 2 averages show the problem. The faithful benchmark, which reflects closeness alone, predicts a century-minus-Hudson difference of −30.9 points (62.65% vs 93.55%); the observed difference is −72.7. The Impressionists and the Hudson River School are about equally close (H 5.92 vs 6.24; faithful 84.8–95.2% vs 89.4–97.0%), yet their observed fractions differ by 21.4 points on average (72.9% vs 94.35%). For GPT Image 1 the faithful value is higher for the Impressionists (95.2 vs 90.2) while the observed one is far lower (71.3 vs 95.7). The Hudson River School's high fraction comes with β near 0, so it is not the "good imitation" case. Two reviewers independently recomputed H2 within pair types: 0.78 within the century group, 0.74 across groups, 0.09 within the Hudson River School. These are reviewer computations, not recorded analyses. |
| **"Near their size"** (abstract) and "roughly in size" (§5.2) for the century group. | all three | **Valid.** β (0.840–1.292) is the amplitude along the reference pattern only. Table 32 gives Q 1.41–3.13 and D 0.73–1.58, and only FLUX.2 Max's D interval lies below 1. That is about the Impressionists' range (0.80–1.74). |
| **The generated images are not released.** | editor (critical); methods, empirical (minor) | An owner decision, already open. |
| **Prespecified v6 readouts are not reported.** The intro states without scope that "recognition rises with the alignment ratio (0.94 / 0.89)". | empirical (critical) | **Valid.** These values come from `reports/painter_tmlr_diagnostics_v6/analysis.json` and are unreported in the paper. The Spearman correlation of alignment ratio with recognition is 0.29 (CLIP) and 0.64 (CSD) for the century group, and 0.94 and 0.66 for the Hudson River School. The claim holds as stated only for the Impressionists. Eight-way recognition is 62.5–78.1% (CLIP) and 64.6–87.5% (CSD) for the century group, and 29.2–50.0% (CLIP) and 31.2–45.8% (CSD) for the Hudson River School. The correlation of the proximity gain with its shared term is 0.97 and 0.83 for the century group, and 0.99 and 1.00 for the Hudson River School. |

## Factual errors

| Reported error | Reviewer | Check |
| --- | --- | --- |
| Appendix C says bootstrap draws with a non-positive denominator are "dropped and counted", but the frozen H1 code keeps them. | methods | **Confirmed.** Replaying `analysis.closeness_test` (seed 20261003) gives 90 of 5,000 draws with N+B ≤ 0, all for FLUX.2 Max on the Hudson River School. They produce Table 2's interval of [−198.2, +90.2]. The pooled H1 result is unaffected. |
| §5.2 presents post-collection faithful values (45.0–75.4%, 89.4–97.0%) as the predictions recorded before collection. | empirical | **Confirmed as a misattribution.** The sentence says "from the new generic outputs". It still attaches those values to "the predictions recorded before collection", which were 47.0–73.3% and 90.1–96.9% (Table 30, from the September generic outputs). |
| The Table 32 caption attributes the feature-space shared gain to Eq. 4. | empirical | **Confirmed.** `painter_tmlr_diagnostics_v1.decomposition` uses the squared-distance identity of Appendix C ("Centroid proximity", shared term 2⟨c,t⟩−‖c‖²), not the linear prototype identity of Eq. 4. |
| Appendix H and Table 31 present H1 as holding "in the central square window", but it is identical by construction. | empirical | **Confirmed.** The pooled difference (−0.72704) and its interval are equal to every digit in both rows. The generated images are square, and the shared fraction does not use the references. |

The empirical reviewer listed one further point as minor: §3 says "we have no further documentation of
how [Flare and Sunburst] differ". **This is confirmed.** Public descriptions of OpenAI's release of
8 September 2026 exist. They describe Flare as the faster default and Sunburst as tuned for quality and
precise editing.

## Revision these findings call for (text and table edits; no new data)

1. **Closeness.** Replace "confirms" with "is consistent with" and name the familiarity confound in
   the abstract. Retitle §5.2 so it states what the second collection shows: the ordering
   follows closeness, while the size also depends on how strongly the generators separate the
   names. Give the matched-closeness comparison of the Impressionists and the Hudson River School,
   and the faithful contrast (−30.9 against −72.7). Describe the Hudson River School's high
   fraction as a lack of differentiation, not as good imitation. Reporting H2 within pair types
   would be a new descriptive analysis of retained data. It needs a short plan written first.
2. **Size.** Limit the century group's agreement to direction and to amplitude along the pattern.
   Report Q and D beside β.
3. **v6 readouts.** Report the readouts the plan fixed. Restrict the 0.94/0.89 statement to the
   Impressionists.
4. **Factual errors.** Fix all four, plus the Flare and Sunburst sentence.
5. **Minor items.** These include: the phrase "first rounds of review" (p. 4, Appendix H), which
   may read as an undeclared prior submission; the 285-word abstract; and §4.3's density. Also: the
   "–" entry in Table 32; the Spearman statistic in the Figure 4 caption; the prespecified
   artist-free split (82.5–95.7%) beside the generic-baseline split; and the coverage of percentile
   intervals for ratios. Finally, add a note that `freeze.json` binds a protocol whose header still
   reads "draft".

Owner decisions that stay open: release of the generated images (raised as critical by the editor),
and the length (about 15–16 main pages; declare a long submission or cut).
