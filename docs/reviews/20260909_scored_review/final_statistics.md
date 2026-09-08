# Final verification — statistical and experimental validity

Internal maintainer-run LLM subagent review, not independent human peer review or institutional validation. Scores use the same eight equally weighted aspects and anchors as Rounds 1–2: 5 substantial unresolved defects; 7 sound but substantial revision needed; 8 strong with limited revisions; 9 publication-ready as a carefully scoped empirical paper; 10 exceptional. I did not consult peer reports or coordinate scores.

Baseline Git commit: `f0fe89a9179377b0a91630b775bcf7163853e66b`. This assessment applies to the final working-tree artifacts verified on 2026-09-09:

- `paper/paper.tex` SHA-256: `2cf3b63c9fac000c1f43da5b23f3283e0318bc853a6ccd22ea77f9f6f021c065`
- `paper/paper.pdf` SHA-256: `8bd68aeb0f2f1a165eeeaf38ad3d688183e627ba9fe87db89a70dc7e42b51b2c`

| Aspect | Final score / 10 |
| --- | ---: |
| 1. Research question and contribution | 8.5 |
| 2. Study design and controls | 8.5 |
| 3. Statistical validity | 9.0 |
| 4. Evidence and robustness | 8.5 |
| 5. Interpretation and claim calibration | 9.0 |
| 6. Literature and positioning | 8.5 |
| 7. Reproducibility and transparency | 8.5 |
| 8. Structure, writing and figures | 8.5 |

**Arithmetic mean: 69.0 / 8 = 8.625 / 10.** Scores remain unchanged from Round 2: the repairs resolve its limited editorial requests without changing the underlying design, data or inferential strength.

The abstract now identifies approximate simultaneous intervals and the k=3 occupancy comparison (lines 32–42). Its coexistence wording and the conclusion's “accompanies” avoid a causal interpretation of contraction (34–35, 703–711). The simulation description correctly distinguishes baseline noise from scene, polarity and arm multipliers (833–846). The shortened collection appendix preserves the eligibility exclusion, quality differences, totals, refusals, retry, randomized order and batch limitation (731–747). The feature inventory has a proper subsection and reference target (771–789).

I inspected these changes in TeX and final rendered pages 1, 13, 14 and 15. The abstract, revised appendix, feature inventory, inference formulas and simulation table remain legible, without clipping or displaced labels. Git diff reports no changes under scientific source, tests, studies, configurations or bound data paths. Earlier numerical checks and the 18 focused inference tests from Round 2 remain applicable; no redundant tests, new analysis or collection were run.

**No unresolved blocking statistical or scientific defect was identified for the present scoped manuscript.** No numerical correction or new collection is required. The paper remains a finite-panel, delivered-service computational study; broader construct validation and transfer require a prospective successor, not additional caveats or post-result tests.

External artifact release remains separate unfinished publication preparation. Lines 713–726 accurately disclose the pending numeric/code snapshot and the lack of externally arranged raw-media access. That condition explains the retained reproducibility score; it is not a hidden statistical defect or a reason to alter frozen evidence. The scientific submission can proceed within its stated scope once the intended reviewer/public artifact access is prepared.

## Delivery addendum — layout only

The final 19-page delivery artifacts have verified SHA-256 identities:

- TeX: `978b601ac8cd01db7eb699ac13f46873310fa88a87bd3e6565a1d6909239fff2`
- PDF: `5dbd0061c3c2d96c76dbbccf9d701f4b26505ed962f5f7a2f673f09c2038ceec`

Reversing the sole `\begin{table}[!htbp]` directive to `\begin{table}[tbp]` in memory exactly reconstructs the reviewed TeX hash `2cf3b63c9fac000c1f43da5b23f3283e0318bc853a6ccd22ea77f9f6f021c065`. Thus the scientific text is unchanged. Pagination QA is handled by the coordinator/editorial reviewer. All eight scores and the **8.625/10** mean remain unchanged; this addendum binds the delivered artifacts and is not another assessment round.

### Superseding delivered identities

The subsequent 19-page delivery has TeX SHA-256 `8f6c990bc730b41d22a4d6e89d47ec91255d9676c1c769e41345bf51fe3f2aa8` and PDF SHA-256 `b8d583716461cce1c85d554b4c16dd212e86530705868b38be84c42006cdd0f2`, both verified. In-memory reversal of Table 7's `[!htbp]` placement and the `\FloatBarrier` before Appendix F exactly reconstructs `978b601ac8cd01db7eb699ac13f46873310fa88a87bd3e6565a1d6909239fff2`; reversal of Table 3's placement then exactly reconstructs the reviewed `2cf3b63c9fac000c1f43da5b23f3283e0318bc853a6ccd22ea77f9f6f021c065`. This verifies the complete layout-only chain without modifying the source. The assessment, all eight scores and **8.625/10** mean remain unchanged.
