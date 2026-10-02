# Round 4 → revision

Round 4 reviewed PDF `caa3b429…` (29 pages). Recommendations: methods **minor revision**,
empirical **minor revision**, editor **minor revision**. Criterion 1 (claims and evidence) was
*partially* for all three; criterion 2 (audience and clarity) *yes* for all three; desk-rejection
risk *low* for all three. The round does not pass the rubric.

**Prompts.** Identical to round 3, including its calibration clause, except for the round paths,
the page range and the supplementary list, which added the diagnostics-v3 and request-timing plans.

## New analysis

[`painter_tmlr_diagnostics_v4`](../../painter_tmlr_diagnostics_v4/REPORT.md), under a
[plan](../../../studies/painter_tmlr_diagnostics_v4/PLAN.md) written before its values were
computed: CLIP and CSD β and D against title-derived content-class targets on the 11 non-mixed
scenes, with scene intervals, replaying the recorded 31-feature values exactly. Content matching
changes the embedding errors by at most 0.037 and keeps their orderings. Replayed by
`make retrospective-check`; 2 constructed-data tests in the routine suite. Everything else in this
revision uses values already in the supplement.

## Critical issues and responses

| Issue (reviewers) | Response |
| --- | --- |
| "No genuine split has an error above 0.53" misreads a 97.5th percentile (all three) | Sentence replaced: no embedding split exceeds 1; the 31-feature 95% ranges end at 1.16–1.36 and contain several generated errors. The registered claim was dropped. |
| D-vs-1 headline stated without its caveats; "in CSD none does" rests on point estimates (all three) | Abstract, intro and §5.3 now say the three 31-feature cases are aligned but oversized (β/√Q 0.511–0.600, comparable with FLUX.2 Max's 0.546; the alignment ratio is added to Table 4). They also state that GPT Image 1 fails the six-way adjustment and would fall below 1 at a repeat correlation of 0.22 (Flare 0.64, Sunburst 0.52; admissible ρ below about 0.3). For CSD: four intervals below 1 and none above, with Nano Banana 2 indistinguishable from 1. |
| FLUX.2 Max's low error rests on Cézanne (empirical) | §5.3 and the intro give its amplitude without Cézanne (0.096), its Impressionist pair amplitudes (0.02–0.17) and its Monet–Sisley and Monet–Pissarro pair errors (1.16, 1.51). |
| "Proximity mostly measures the shared change" argued from the level only (editor; methods and empirical minor) | New §5.2 paragraph and Table 3 (readouts split into shared and painter-specific terms). CLIP gain ranks the configurations exactly as its shared term does, and the shared term varies 11 times as much. In CSD the gain correlates 0.95 with the shared term and −0.65 with the specific term. Abstract, intro and §5.4 rest on this. |
| Feature-family finding reported without its benchmarks (empirical) | Family faithful and exact-differences means added to the family table (moved to the appendix). The intro bullet is dropped. §5.5 reads the texture–color gap against the benchmarks: exact is also lower for texture, every family sits 3.6–7.6 points below its benchmark, and GPT Image 1's 48.6% comes from oversized texture differences (B/H 3.11). |
| Su et al. credited with the proximity gain (empirical) | Attribution removed. §1 says the paper analyzes the gain over a generic clause and that raw proximity adds a further name-independent term. |
| "Whatever the model does" false when β > 1 (empirical) | Now "unless the model exaggerates the reference differences (β > 1)". |
| CSD "close to faithful" hides that it is above (editor) | §5.2 states that CSD shares are above the faithful values for all six configurations. |

## Minor changes

- **Content confound (all three):** content-matched embedding targets added (Table 5, v4 analysis).
- **Abstract logic (methods):** the exact-differences reasoning now rests on the size of the shared change relative to the painters' differences.
- **Scope of Eq. 4:** limited to scores linear in the embedding; rank, maximum and threshold readouts are excluded.
- **Genuine controls:** the comparison with them is explained (no scene effect in the pseudo-scenes).
- **Rescaling:** D_held ≈ 1 − β²/Q ≤ 1 by construction, so the ranking follows the alignment ratio; Q = B/H + V_scene is stated.
- **Tables:**
  - reference-resampling β intervals noted as shifted low;
  - tie rule stated in the stability table, which moved to the appendix;
  - embedding β intervals added;
  - Table 1 frequencies shown to one decimal.
- **Figure 3:** the caption explains why observed is below faithful on the left panel but not in the embeddings.
- **Wording:**
  - exchangeable null used in §5.1;
  - hat notation explained;
  - six-way adjustment labelled descriptive;
  - "computed before rounding" added for the recognition deltas;
  - "widely read" attributed to Frochte;
  - Figure 2 label note simplified;
  - AI-assigned visual labels disclosed;
  - Kynkäänniemi et al. cited on content sensitivity;
  - repeated caveats and several "X, not Y" constructions cut.
- **Moved to the appendix:** the SD-Turbo details, the N_free split, the family bookkeeping and the translation details.
- **Result:** the main text now ends on p. 13.

## Not changed

- **Images:** no release commitment for the generated images and no contact sheet. Both are owner decisions.
- **Third repeat:** none collected.
- **Bias-corrected intervals:** reference intervals keep their percentile form; the shift is noted instead of switching to bias-corrected intervals.
