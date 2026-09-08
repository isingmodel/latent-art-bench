# Three-reviewer manuscript revision

This record concerns the user's request for three skeptical paper reviews and
revision until the equal-weight average exceeds 8.5/10. These are maintainer-run
LLM subagent reviews with coordinator checks, not independent human or
institutional peer review. Scores describe these reviewers' assessment of the
manuscript; they do not predict acceptance by a journal or conference.

## Fixed rubric and stopping rule

Each reviewer evaluates the full paper, with a different emphasis: statistics,
scientific interpretation, or editorial quality. Reviewers submit their reports
separately without consulting each other's evaluations. The same eight aspects
and scoring anchors apply in every round:

1. Research question and contribution.
2. Study design and controls.
3. Statistical validity.
4. Evidence and robustness.
5. Interpretation and claim calibration.
6. Literature and positioning.
7. Reproducibility and transparency.
8. Structure, writing and figures.

Scores range from 1 to 10, with half-points allowed. The anchors are: 5 means
substantial unresolved defects; 7 means sound but needing substantial revision;
8 means strong with limited revisions; 9 means publication-ready as a carefully
scoped empirical paper; 10 means exceptional. Limitations, effort and the requested
threshold do not themselves justify higher scores. Each reviewer mean averages
all eight aspects; the overall mean averages all 24 aspect scores equally.
Completion requires an overall mean strictly above 8.5, no unresolved blocking
validity defect, and verification of the final manuscript. The rubric is not
changed to make the threshold easier to reach.

The initial manuscript is commit `f0fe89a`, TeX SHA-256
`a86ab853dddedcbf45c8d944aef3a4bc9871f022e583b2a7830c69ddfba25a17`.
Individual reports preserve their findings and the manuscript identity assessed.
The current operation is an editorial revision. Published scientific evidence,
closed collections, protocols and primary test families remain unchanged unless
a separately versioned scientific correction is required.

## Review rounds and responses

### Round 1

| Aspect | Statistics | Science | Editorial |
| --- | ---: | ---: | ---: |
| Research question and contribution | 8.0 | 7.5 | 7.5 |
| Study design and controls | 7.5 | 7.0 | 7.5 |
| Statistical validity | 8.0 | 8.0 | 8.0 |
| Evidence and robustness | 7.5 | 7.5 | 8.0 |
| Interpretation and claim calibration | 8.5 | 8.5 | 8.5 |
| Literature and positioning | 7.5 | 7.0 | 6.5 |
| Reproducibility and transparency | 8.5 | 8.5 | 8.0 |
| Structure, writing and figures | 8.0 | 8.0 | 8.0 |
| **Reviewer mean** | **7.9375** | **7.7500** | **7.7500** |

Overall mean: **187.5 / 24 = 7.8125/10**. Individual reports:
[statistics](round1_statistics.md), [science](round1_science.md),
[editorial](round1_editorial.md).

### Revision before round 2

| Finding | Concrete revision |
| --- | --- |
| Contribution obscured by general metric distinctions | Rewrote the title, abstract, introduction and discussion around the observed original/generated gap and repeated painter-name intervention; each study now contains its own methods and results. |
| Underused painter-specific control | Promoted the saved joint own/cross-painter interaction, including all three services, unchanged negative sensitivity directions, identical-free controls and the NB2/Monet cross-painter preference. No stochastic common-response null is claimed rejected. |
| Forced palette mixture had too much explanatory weight | Moved the detailed illustration to an appendix; used the existing matched-anchor real/generated neighborhood comparison for ordinary Study 1 prompts, with the complete k=1/3/5 named sensitivity and saturation example. |
| Spread/energy dependence was too abstract | Explained the existing FLUX/Monet cross-domain and within-generated energy terms, including why the latter decrease opposes the observed energy improvement. |
| Nearest prior literature omitted or underspecified | Added Deliège et al. (2025), distinguished its expert-rated corpus distributions from the repeated prompt intervention; expanded Asperti (2026) beyond its CLIP headline and clarified AI-Pastiche's evaluators. |
| Primary/prospective/post-result hierarchy inaccurate | Added a design/evidence table and corrected the original prospective descriptive analyses versus subsequent diagnostics. |
| Precision hidden by total image count | Added standard errors, effective degrees of freedom, interval magnitude context and the retained prospective proxy simulations with Monte Carlo intervals and explicit independent-error assumptions. |
| Scene heterogeneity hidden by aggregate means | Figure 4 now shows all six saved scene interactions per painter alongside the unchanged pooled effects and family intervals; no new statistic is computed. |
| General wording outpaced finite comparisons | Restricted claims to the tested generic clause and realized retrieval diagnostic; distinguished the two studies from mediation analysis. |
| Release status and service timing unclear | Added verified UTC dates, 11.5-hour/49.5-minute collection durations, repository URL, local scientific snapshot and explicit pending public release/raw-access status. |

These are editorial uses of existing published evidence. No new experiment,
image acquisition, feature extraction, scientific test, primary endpoint or
preferred representation was introduced. All three reviewers identified a
meaningful revision path without new data. More repetitions would not resolve
their control, capture and construct-validity objections, and no collection was
extended to change a primary result or reviewer score.

Round 2 manuscript identities:

- TeX SHA-256: `2d28cec5b0bf7e62cb8e76338b4c3b52809c63c0ab6e8bb9aba4dced9a931a52`.
- PDF SHA-256: `48bb8772bd0bf8da48c621de1610ce8e7a29690c5aeeb9b6e330c803daf87666`.

The manuscript builds without TeX warnings. All five figures reproduce byte for
byte; all twelve displayed scene estimates and both pooled intervals match the
saved table. Ruff and all **1,135 offline tests** pass (115.43 seconds). Reviewers
then reassessed the complete revised paper under the unchanged rubric; no higher
score was promised as a condition of accepting revisions.


### Round 2 and final verification

| Aspect | Statistics | Science | Editorial |
| --- | ---: | ---: | ---: |
| Research question and contribution | 8.5 | 8.5 | 8.5 |
| Study design and controls | 8.5 | 8.0 | 8.0 |
| Statistical validity | 9.0 | 8.5 | 8.5 |
| Evidence and robustness | 8.5 | 8.5 | 8.5 |
| Interpretation and claim calibration | 9.0 | 9.0 | 9.0 |
| Literature and positioning | 8.5 | 8.5 | 9.0 |
| Reproducibility and transparency | 8.5 | 8.5 | 8.0 |
| Structure, writing and figures | 8.5 | 8.5 | 8.5 |
| **Reviewer mean** | **8.6250** | **8.5000** | **8.5000** |

Overall mean: **205 / 24 = 8.5416667/10**, strictly above 8.5. Scores remained
unchanged after final repairs and artifact verification; no reviewer was asked
to increase a score to meet the target.

Round 2 reports: [statistics](round2_statistics.md), [science](round2_science.md),
[editorial](round2_editorial.md). Final assessments and delivery addenda:
[statistics](final_statistics.md), [science](final_science.md),
[editorial](final_editorial.md).

The final repairs qualify abstract coverage at k=3, label the interaction
intervals approximate, replace causal “consequences” with coexistence, describe
simulation standard-deviation factors as multipliers, remove duplicated
main/appendix methods, separate the feature inventory, and keep alignment and
chroma tables with their respective sections. Two pagination checks caught an
excess blank region and a table entering the bibliography; both are corrected.
No primary value or scientific result changed.

All three reviewers report no unresolved blocking defect for this scoped empirical
manuscript. Their scores still reflect finite reference panels, uncertain
capture/content comparability, one generic clause, limited follow-up scenes and
repetitions, unvalidated perceptual interpretation, and pending public artifact
release. Those limitations were not erased or turned into new findings.

## Delivered artifact and verification

- Manuscript: `paper/paper.tex`, SHA-256
  `8f6c990bc730b41d22a4d6e89d47ec91255d9676c1c769e41345bf51fe3f2aa8`.
- **19-page PDF**: `paper/paper.pdf`, SHA-256
  `b8d583716461cce1c85d554b4c16dd212e86530705868b38be84c42006cdd0f2`.
- Five vector figures; only the color-response figure changed, adding saved
  scene estimates. The other four PDFs remain byte-identical to the baseline.
- Ruff and all **1,135 offline tests pass** (115.43 seconds). Every figure
  byte-reproduces, and all newly reported calibration/coverage values were checked
  against the retained tables. No new scientific calculation is introduced by
  manuscript rendering.
- The final PDF builds without TeX warnings; citations and cross-references
  resolve. All 19 final pages have visual coverage through the coordinator and
  reviewers, including byte-identity checks for unchanged pages. Final pages
  18–19 were inspected after the last table-placement correction.
- The two final pagination changes were verified by reversing only the relevant
  float directives and reconstructing the previously reviewed TeX hashes exactly.
  All three final reviewer reports bind the delivered identities above.
- Documentation links and `git diff --check` pass. No evidence-bound input,
  protocol, ledger, source, scientific test or raw research byte was modified;
  the historical evidence audit therefore did not need a new run for this task.
- No new images, paid requests, human ratings, feature extraction, remote push or
  public release occurred. The compact scientific snapshot's archival release
  and external raw-media access remain explicitly pending.

The requested internal review threshold is met. This records manuscript revision
quality under the fixed rubric, not external peer acceptance or validation of
broader stylistic/mechanistic claims.
