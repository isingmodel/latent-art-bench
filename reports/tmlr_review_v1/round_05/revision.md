# Round 5 → revision

Round 5 reviewed PDF `764356d8…` (30 pages).

| Reviewer | Recommendation | Criterion 1 (claims and evidence) | Criterion 2 (audience and clarity) | Desk risk |
| --- | --- | --- | --- | --- |
| Methods | minor revision | *partially* | *yes* | low |
| Empirical | minor revision | *partially* | *yes* | low |
| Editor | minor revision | *yes* | *yes* | low |

The round does not pass the rubric.

**Prompts.** Identical to round 4 except for the round paths, the page range and the supplementary
list, which added the diagnostics-v4 plan.

## New analysis

[`painter_tmlr_diagnostics_v5`](../../painter_tmlr_diagnostics_v5/REPORT.md) ran under a
[plan](../../../studies/painter_tmlr_diagnostics_v5/PLAN.md) that lists the values the round-5
reviewers had already computed. It covers the following:

- **Direction-only agreement.** Alignment ratio and held-out rescaled error in all three representations, with their scene-resampling stability and Spearman correlations.
- **Embedding error parts.** The split of D along and off the reference pattern, and Student intervals for β and D.
- **Repeat dependence in the embeddings.** Repeat noise and ρ thresholds.
- **Proximity across configurations.** Correlations and variance ratios, with scene intervals and leave-one-configuration-out ranges.
- **Distinct configurations.** Between-configuration versus repeat distances.
- **Projection coordinates** for a figure.

It replays the recorded 31-feature split and repeat noise, the embedding calibration of the learned audit, the v4 content values and the proximity shares exactly. `make retrospective-check` replays it, and 5 constructed-data tests run in the routine suite.

## Critical issues and responses

| Issue (reviewers) | Response |
| --- | --- |
| "Aligned but oversized" contradicts the prespecified split of D (methods) | The split is now reported: Table 14 in the features, Table 23 in all representations. Abstract, intro and §5.3 now say the three configurations above 1 have near-reference amplitude along the pattern, and that 96.9–98.2% of their error lies off it. The §6 recommendation now distinguishes amplitude along the pattern from off-pattern differences. |
| Representation dependence and readout disagreement rest on the size-sensitive D (empirical) | Direction-only agreement is added for the embeddings (Table 5: Q, alignment ratio, D_held) and to the readouts table and the stability table. By direction, GPT Image 2 is best in all three representations (98.0, 99.7 and 100.0% of resamples), the alignment ratio orders the configurations consistently (Spearman 0.60–0.77) and tracks recognition (0.94, 0.89). Abstract, intro, §5.3 (new title and labelled paragraphs) and §5.4 now say that the representations and readouts differ in how they weigh size. |
| Content-matched sentence contradicted by Table 5 (all three) | Table 5 now shows the 11-scene pooled D next to the class D. The text says "relative to the pooled target on the same scenes", and the builder now checks the full ordering. |

## Minor changes

- Figure 3 caption corrected: observed shares are "mostly at or above" faithful in the embeddings, and Table 24 is cited.
- FLUX.2 Max: the intro drops the "lowest error" highlight, and §5.3 states that it is resolved only against Flare and Sunburst.
- Embedding intervals are now paired-scene Student intervals, matching Table 4. Interval types and "resolved" are defined once in §4.5.
- Repeat dependence: errors below 1 are conservative; the CLIP thresholds are 0.03–0.14; Appendix A now says the point estimates imply ρ < 0.3.
- Proximity correlations now carry intervals and the CSD variance ratio 5.8, with n = 6 and the part–whole caveat.
- Omitted prespecified diagnostics are now reported or accounted for:
  - distribution diagnostics: new Table 20;
  - the fixed-effects regression, which reproduces the pairwise differences;
  - the PCA display, replaced by a projection figure of the means (Figure 5).
- Model selection: the explicit routes were not tested with an invalid identifier. Costs and configuration distinctness (≥ 91.7% of cells) are reported.
- Sunburst's negative Monet–Sisley amplitude is in the main text.
- "Movement toward any painting-like image" removed from §6. The recommendations acknowledge the lack of perceptual or positive-control validation.
- The Naeem et al. citation was removed from the conditional-metrics sentence.
- Cézanne mentioned in the intro bullet.
- Exchangeable null removed from the main text.
- "(computed before rounding)" replaced by one global note.
- Editor sentence fixes: "either", "that level", three caveats in one sentence, "reference point", "sampled this way", and the CSD gain tie.
- Route works: they enter the pooled target but no class target.
- Crop asymmetry noted in Appendix E.
- The reproducibility statement now says "registered number".
- `figures/PROVENANCE.json` now labels the panel as Figure 2.
- The claim registry caught a rounding error in a new sentence: 87.0%, not 86.9%.

## Not changed

- **Images:** no release commitment for the generated images and no contact sheets. Both are owner decisions.
- **New data:** no positive control, perceptual check, generic-name control or third repeat.
- **Bibliography:** name formats not harmonized, to avoid guessing full author names.
- **Figure 3:** keeps its mixed panels; the caption explains them.
- **Length:** the main text runs to about 13.3 pages, so the paper must be declared a long submission.
