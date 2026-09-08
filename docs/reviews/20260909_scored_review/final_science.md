# Final scientific artifact verification — 9 September 2026

Internal maintainer-run LLM subagent review, not independent human or
institutional peer review. This verifies the final artifact against my round 2
assessment under the same eight-aspect rubric. I did not consult peer reviews or
coordinate scores.

Verified TeX SHA-256:
`2cf3b63c9fac000c1f43da5b23f3283e0318bc853a6ccd22ea77f9f6f021c065`.

Verified PDF SHA-256:
`8bd68aeb0f2f1a165eeeaf38ad3d688183e627ba9fe87db89a70dc7e42b51b2c`.

## Final scores

Scores remain unchanged from round 2. The final edits resolve small wording and
presentation findings; they do not add evidence or remove design limitations.
The equal-weight anchors remain 5 for substantial unresolved defects, 7 for
sound work needing substantial revision, 8 for strong work with limited revisions,
9 for publication-ready work as a carefully scoped empirical paper, and 10 for
exceptional work.

| Aspect | Score / 10 |
| --- | ---: |
| 1. Research question and contribution | 8.5 |
| 2. Study design and controls | 8.0 |
| 3. Statistical validity | 8.5 |
| 4. Evidence and robustness | 8.5 |
| 5. Interpretation and claim calibration | 9.0 |
| 6. Literature and positioning | 8.5 |
| 7. Reproducibility and transparency | 8.5 |
| 8. Structure, writing and figures | 8.5 |

**Arithmetic mean: 68.0 / 8 = 8.50 / 10.**

**Blocking status: no remaining scientific or editorial finding blocks handoff
of this bounded manuscript.** Public archival release of the compact scientific
snapshot remains pending, as the manuscript truthfully states; this verification
does not certify a completed public release or external access to raw media.

## Verified corrections

- The abstract now says that the distributional patterns coexist with
  heterogeneous scene-distinguishability changes. The Conclusion says that
  contraction accompanies those changes. Neither attributes the retrieval
  outcome causally to contraction.
- The abstract qualifies lower reference-neighborhood occupancy by k=3 and
  labels the color interaction intervals approximate. The main text and appendix
  retain the k=5 FLUX/Cézanne saturation exception.
- The proxy simulation description now identifies scene factors as
  standard-deviation multipliers applied to arm-specific baseline noise, followed
  by the palette and arm factors. Its deployment-assumption limitations remain.
- The shortened Appendix A.1 retains the figure-led eligibility exclusion,
  format/geometry and reported-quality details, counts, randomized OAuth order,
  missing requests and exact-payload retry accounting. The feature inventory has
  its own subsection.
- The central safeguards remain: the NB2/Monet individual cross-painter
  preference, no rejection of a stochastic common-response model by the
  descriptive alignment contrast, finite-query retrieval interpretation, both
  unresolved primary color interactions, and the pending-release/raw-access
  boundaries.

I visually inspected final pages 14–20, plus the abstract on page 1 and the
Conclusion/access statement on page 13. Equations, tables, the PCA figure,
captions, artifact paths and bibliography were readable. No clipping, overlap,
broken labels or material layout defect was apparent in these pages.

## Unchanged scientific judgment

The paper supports an interesting finite-feature result: painter naming improves
joint relative reference-panel alignment while generated distributions contract
and retain lower matched reference-neighborhood occupancy, with heterogeneous
repeated-scene behavior. The relevant retained controls now support that central
claim. New human ratings are not required for this computational scope.

The same limitations remain substantive: selected sparse reference panels,
unresolved capture and fine-content differences, prompt-associated rendering,
correlated feature sensitivities, a short single-service color experiment,
approximate small-repeat inference, one generic sentence and only two palette
endpoints. These prevent broader perceptual, painter-population, response-curve
or mechanistic conclusions. The final text does not claim to resolve them.

No further manuscript revision or new analysis is requested by this reviewer.
Proceed with the stated finite empirical scope and handle public release as
separate concrete work. Further polishing should not be used to seek higher
scores for an unchanged evidence base.

## Verification boundary

I reread `docs/STATUS.md`, then `docs/ARTIFACTS.md`, inspected Git status, and
preserved existing changes. This was read-only editorial verification except for
this Markdown report. I did not edit the paper or scientific files, rerun the
already completed full tests, or perform image acquisition, generation, feature
extraction or new scientific analysis. The coordinator's warning-free 20-page
build and prior full-suite/Ruff checks remain the reported build/test evidence.

## Delivery addendum — 19-page pagination

Delivered TeX SHA-256:
`978b601ac8cd01db7eb699ac13f46873310fa88a87bd3e6565a1d6909239fff2`.

Delivered PDF SHA-256:
`5dbd0061c3c2d96c76dbbccf9d701f4b26505ed962f5f7a2f673f09c2038ceec`.

I verified both hashes locally. There is exactly one
`\begin{table}[!htbp]` directive in the delivered source. Replacing it in memory
with `\begin{table}[tbp]` restores SHA-256
`2cf3b63c9fac000c1f43da5b23f3283e0318bc853a6ccd22ea77f9f6f021c065`
exactly. Thus the only TeX change since my final scientific review is that float
placement directive; the scientific text is unchanged.

I visually inspected delivery pages 14–19. The equations, calibration and coverage
tables, PCA figure, mixture results, artifact paths and references remain readable,
without clipping or overlap. One minor pagination side effect is that Table 7
appears below the References heading and first entry on page 18. Moving that table
before the artifact/bibliography sections would improve adjacency if further
layout polishing is undertaken, but the table is clearly labeled and this is not
a scientific blocker.

All eight scores remain **8.5, 8.0, 8.5, 8.5, 9.0, 8.5, 8.5, 8.5** in rubric
order; mean **8.50/10**. The scientific blocking status remains **none**. The
scope, design limitations and pending public release assessment above are
unchanged. No scientific file was edited, no new analysis or test was run, and
the directive reversal was performed only in memory for hash comparison.

## Final delivery addendum — table placement resolved

Final delivered TeX SHA-256:
`8f6c990bc730b41d22a4d6e89d47ec91255d9676c1c769e41345bf51fe3f2aa8`.

Final delivered PDF SHA-256:
`b8d583716461cce1c85d554b4c16dd212e86530705868b38be84c42006cdd0f2`.

Both hashes were verified locally. Reversing Table 7's `[!htbp]` placement and
removing the added `\FloatBarrier` immediately before Appendix F, in memory,
exactly restores the preceding delivered TeX hash
`978b601ac8cd01db7eb699ac13f46873310fa88a87bd3e6565a1d6909239fff2`.
The source difference is therefore limited to those two pagination directives.

I inspected final delivery pages 18–19. Table 7 now remains within Appendix E,
before Appendix F and the References section. Its values, caption and adjacent
interpretation are readable; the bibliography continues normally on page 19.
The minor placement issue identified in the preceding addendum is resolved.

All eight scores remain **8.5, 8.0, 8.5, 8.5, 9.0, 8.5, 8.5, 8.5**; mean
**8.50/10**. No scientific or editorial blocking finding remains. Scientific
limitations and pending-release status are unchanged. No new scientific work or
tests were performed during this final pagination verification.
