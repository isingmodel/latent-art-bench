# Round 1 → revision (not reviewed)

Round 1 reviewed PDF `af4eea64…` (38 pages) and did not pass ([triage](triage.md)). On 2026-10-04
the owner asked for the revision ("gogo"). The changes below were made afterwards and **have not
been reviewed**.

**One new analysis.** Diagnostics v7 ([plan](../../../studies/painter_tmlr_diagnostics_v7/PLAN.md),
[report](../../painter_tmlr_diagnostics_v7/REPORT.md)) reads retained outputs and features. Its plan
was committed (`025a272`) before the analysis ran, and it lists the point values the reviewers had
already computed. No image, request or human evaluation was added.

**Numbers.** Every new number in the text comes from recorded outputs and is checked by the
builder (39 generated files, 259 claims). The revised PDF has 40 pages; the main text now ends on
page 15, against page 16 before.

## Critical issues and responses

| Issue (reviewer) | Response |
| --- | --- |
| The closeness claim is too strong: the abstract said the second collection "confirms" it, and §5.2 was titled "The shared fraction tracks how close the painters are" (all three) | **Abstract:** "is consistent with". It now says that closeness alone predicts 42–58% of the gap and that the rest is confounded with how familiar the names are. **Intro bullet 2 and §5.2:** retitled "Distant painters leave less of the change shared, but not by closeness alone". §5.2 now reports the faithful (closeness-only) contrast: 30.9 points [26.6, 32.9] of the 72.7, leaving an excess of 41.8 [34.9, 47.2]; in CLIP 22.9 of 40.1, in CSD 27.3 of 47.4. It adds the comparison at matched closeness: the Impressionists and the Hudson River School have spreads of 5.92 vs 6.24, yet their shared fractions differ by 21.4 points, against 3.7 for a faithful imitator. It gives H2 by pair type: 0.78 within the century group, 0.74 across the groups, 0.09 within the Hudson River School (0.49 in CLIP, 0.27 in CSD). The Hudson River School's high fraction is now described as a lack of differentiation, not good imitation. **Table 2:** gains a closeness-only column and a mean row; new Appendix Table 34 holds the breakdowns. **Discussion and limitations:** they name the confounds of familiarity and subject matter. |
| "Near their size" (abstract) and "roughly in size" (§5.2) for the century group (all three) | The size claim now holds only along the reference pattern. §5.2 adds that the differences are oversized ($B/H$ 1.33–2.56, $Q$ 1.41–3.13) and that 89.8–97.9% of their error lies off the pattern, so $D$ is 0.73–1.58 and only FLUX.2 Max's interval lies below 1. The abstract now speaks only of direction. |
| Prespecified v6 readouts were unreported, and "recognition rises with the alignment ratio (0.94/0.89)" was unscoped (empirical) | Intro bullet 5 and §5.5 now scope the claim to the Impressionists and give the century group's 0.29 (CLIP) and 0.64 (CSD). New Appendix Table 35 reports eight-way recognition, the per-group Spearman correlations and the proximity correlations from the v6 plan. |
| The generated images are not released (editor; minor for the others) | Owner decision; not changed. |

## Factual errors (all confirmed in the triage)

| Error | Correction |
| --- | --- |
| Appendix C said non-positive bootstrap denominators are "dropped and counted"; the H1 code keeps them | Appendix C now limits that rule to the first collection's analyses. Appendix "The second collection" and the Table 2 caption report the count: 90 of 5,000 draws for FLUX.2 Max with the Hudson River School. Fractions fell outside [0, 1] in 150 century draws and 237 Hudson River draws. |
| §5.2 attached post-collection faithful values to "the predictions recorded before collection" | §5.2 now quotes the recorded predictions (47.0–73.3% and 90.1–96.9%, Table 30). The post-collection values appear separately, as the closeness-only contrast. |
| The Table 32 caption cited Eq. 4 for the feature-space proximity share | The caption now cites the squared-distance identity, newly labelled in Appendix C, and explains the "–" entry: the reduction is not positive. |
| H1 in the central square window was presented as a robustness result | The Table 31 caption and Appendix "Tests and sensitivity" now say it is unchanged by construction. |
| §3 said there was no documentation of how Flare and Sunburst differ | It now says that OpenAI released both on 8 September 2026, two days before collection, and that the release notes describe Flare as the faster default and Sunburst as tuned for quality and precise editing; how they differ technically is not documented. |

## Minor changes

**Wording**
- "First rounds of review" (§3, Appendix "The second collection") is replaced by "after the results above were known".
- §5.3: "drives" is replaced by "tracks".
- The elliptical sentence on the fictitious-name and group controls (§6) is expanded.
- The Figure 3 caption now says "dashed", not "dotted".

**Abstract and structure**
- The abstract is shortened from 285 to 226 words.
- Intro bullet 4 no longer carries the 31-feature D > 1 detail, which remains in §5.4.
- §4.3 now lists relative size, alignment ratio and scene variation as items.
- The detail of §5.6 (feature families, reference sources, other checks) moves to a new Appendix "Feature families and sensitivity"; §5.6 keeps a summary.

**Clarifications**
- §4.5 states the following:
  - the coverage of percentile intervals for ratios is unverified;
  - the H2 panel-size correction was fixed in the frozen analysis code, not in the protocol text;
  - diagnostics v7 was planned after review, with its point values known.
- The second-collection appendix explains why the protocol header still reads "draft".
- §5.1 and the Table 1 caption flag the generic baseline as chosen after collection and give the prespecified artist-free split (82.5–95.7%).

**Text added to §5.2 and the figures**
- §5.2 says the century-vs-Impressionist alignment comparison is descriptive, since each group has its own H.
- It rewrites the panel-size sentence with its quantities named.
- It adds the feature-space proximity share for the century group: 73.0–100.7% in five configurations, 31.5% for FLUX.2 Max.
- The Figure 4 caption says the panel titles show the mean of per-configuration Spearman correlations.

**Discussion, limitations and citations**
- Recommendations: the genuine-painting control is a partial positive control, and a generator-side positive control is missing.
- Limitations: the identical requests of the two collections argue against slow service drift but not against dependence between repeats.
- New citations: Mantel (1967) for the Mantel test; Karayev et al. (2014), Saleh and Elgammal (2016) and ArtFID (Wright and Ommer 2022) in related work.

**Layout and supplement**
- Float parameters now let several tables share a page.
- The supplement adds the v7 plan.

The Korean translation follows all of these changes (`make tmlr-ko-check` passes).

## Not changed (owner decisions or new evidence)

- **Images:** there is no release commitment for the 2,686 generated images. The editor rated this critical.
- **Length:** the main text runs to about 14 pages. Declare a long submission or cut further.
- **New data:** a fictitious-name or group-clause control, groups that separate closeness from familiarity, a familiarity proxy, a human check of the AI audits, and a third representation (for example DINOv2) would each need a new budget or new work.
- **Not adopted:** reviewer suggestions without a verified source. The empirical reviewer's link to Frochte (2026)'s "shared-tradition failures" is one; N/H and B/H intervals per configuration for the second collection are another.
