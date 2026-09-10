# Validation follow-up: implementation and manuscript review

This is a maintainer-run LLM review record, not independent human peer review or
replication by an external research group. Three agents assessed the manuscript
under the unchanged [three-aspect rubric](../20260909_academic_review/RUBRIC.md),
using the requested [academic review guide](https://github.com/bytedance/deer-flow/blob/main/skills/public/academic-paper-review/SKILL.md).
Their implementation involvement is disclosed in each report. Scores describe
observed versions; the historical requested threshold does not justify changing
the rubric or raising scores without evidence.

## New evidence and limits

- Computational measurement validation: 1,076 retained raw-image hashes verified,
  1,706 vectors, ten reference conditions and common-square generated views.
  All three specified change-minus-processing averages are positive; all eight
  square-view contrast signs and the same four adjusted rejections persist.
  Cross-family responses, resampling sensitivity and LBP concentration restrict
  interpretation. No human-perceptual or independent-capture validation is claimed.
- Temporal replication: 264 new outputs, zero failed attempts/retries, 64.3 minutes,
  792 slot/pipeline measurements. Both FLUX naming directions recur in the new
  four-endpoint family. Both additional named-palette effects remain unresolved.
  The same maintainer collected the data; investigators, backend states and a
  population of dates are not independently replicated.
- Public numerical replay: all numerical exports and eight manuscript figures
  pass 98 exact checks in a fresh local locked environment. Publication,
  hosted execution and anonymous download passed and are recorded below.
  Raw pixels are excluded, so numerical replay does not provide public feature
  re-extraction or authentication of the original transport.

See [precollection review](PRECOLLECTION_REVIEW.md),
[measurement results review](RESULTS_REVIEW.md),
[temporal results review](TEMPORAL_RESULTS_REVIEW.md) and
[public package review](PUBLIC_PACKAGE_REVIEW.md) for calculation and scope checks.

## Full manuscript review, round 1

All three reviewers assessed TeX SHA256
`be91c40bc9434d4b4f5659d7e5de1741e56302f19d3f7a90bc31475916e3a25b`
and 30-page PDF SHA256
`df0ed7517857c7c27aef6e997d38fce0a5daef0577744318bcda61cec82b0d1b`.
No reviewer awarded credit for public access or hosted execution at that stage.

| Review | Scientific rigor | Contribution/significance | Clarity/reproducibility | Mean |
| --- | ---: | ---: | ---: | ---: |
| [Reviewer 1](REVIEWER_1_ROUND1.md) | 8.5 | 7.8 | 8.5 | 8.2667 |
| [Reviewer 2](REVIEWER_2_ROUND1.md) | 8.4 | 7.9 | 8.7 | 8.3333 |
| [Reviewer 3](REVIEWER_3_ROUND1.md) | 8.4 | 7.8 | 8.4 | 8.2000 |

The nine-score mean is **8.2667/10**, compared with 7.8889 for the preceding
academic-review version. Remaining scientific limitations prevent treating
stronger documentation as complete construct validation or broad generalization.

## Revisions in response

| Issue | Revision and verification |
| --- | --- |
| Fresh distributional behavior absent beyond significance | Added absolute fresh FLUX energies and reference-relative trace ratios for both painters. Explained the already-contracted new free baseline, different counts/shared controls, and absence of a test of time effects. |
| Generic-clause finding underreported | Added the new secondary generic-minus-free estimate −.891 and nominal 95% interval [−1.078,−.704], explicitly outside the four primary endpoints. Both named interactions remain unresolved. |
| Measurement validation too easily overread | Reported the full challenge matrix, cross-family responses, texture resampling sensitivity and post-result 83.9% LBP8 contribution under first-dose blur. Preserved the computational-versus-perceptual distinction. |
| Replication and service delivery | Reported all 264 outputs, actual nonsquare OAuth delivery and reported-quality distribution, no retries, duration, and same-maintainer temporal scope. Preserved the original and new multiplicity families separately. |
| Paragraphs interrupted by floats and awkward wording | Revised figure placement, appendix starts, agreement and inference phrasing; rebuilt the complete English PDF and inspected its pages. |
| Public access claimed before publication | Published the versioned archive and verified actual hosted execution, anonymous download and exact fresh replay. Added a separately identified corrected paper and erratum for the final portability wording. |

The revised prepublication source is SHA256
`2b4dd5c04415300bee29977bf0762555f4af5e2b75490ca65ed90b4ba6fece71`;
the 32-page PDF is
`e78c56e664522bb1b9fc584319fe47615bc6b51dc3ed5c4cb40e483142817673`.
Reviewer 1's focused final check found no new substantive numerical or inferential
defect. Reviewer 3 inspected contact sheets for all 32 pages and affected pages
in full; the previously interrupted numeric range, source paragraph and Appendix H
opening now stay together, with no serious layout regression. Final access-specific reassessments are recorded below; scientific scores do not
automatically increase with successful publication.

## Hosted portability investigation

The first Ubuntu run, [34423375314](https://github.com/isingmodel/latent-art-bench/actions/runs/34423375314),
reproduced Study 1 and its revision within the original 1e-10 numerical tolerance
and measurement results exactly, then rejected the temporal result. A strict
adapter diagnostic was added without relaxing acceptance. The second run,
[34423830742](https://github.com/isingmodel/latent-art-bench/actions/runs/34423830742),
identified exactly six rejected leaves: Monet's continuous Welch p-value and its
Holm-adjusted copy in the primary512 and resolution256 palette results, plus the
two primary512 copies in the top-level four-endpoint table. Absolute differences
were 2.7755575615628914e-17 or 5.551115123125783e-17. All other leaves passed the
existing comparison, including exact randomization probabilities/counts and
scientific decisions.

The original adapter forced exact equality for every p-valued field, despite
allowing 1e-10 for other continuous calculations. A narrowly scoped adjustment
for identified expected-schema Welch results passed separate review, 32 targeted
tests and 15 additional schema probes. It is a
post-CI release-comparator amendment, not a prospective analysis amendment;
scientific functions, expected outputs and hashes remain unchanged. The final hosted
verification succeeded under the documented contract.

The [third Ubuntu run](https://github.com/isingmodel/latent-art-bench/actions/runs/34424383262)
then passed all numerical result families, including the four-painter exploration
and Stage A controls. It reached figure generation but found an additional exact
comparison inside the palette plotting helper. The correction preserves that
helper's strict standalone default and passes the already reviewed comparator
from the portable release adapter; it does not alter inference, image identities,
block checks or plotting values. Final end-to-end verification subsequently passed.

## Completed public verification and corrected manuscript

The [release](https://github.com/isingmodel/latent-art-bench/releases/tag/pprv1-20260910)
was published at 2026-09-10 01:25:30 UTC. The
[canonical verification report](../../../reports/paper_reproducibility_v1/pprv1-20260910/REPORT.md)
and [publication receipt](../../../reports/paper_reproducibility_v1/pprv1-20260910/PUBLICATION_VERIFICATION.json)
record all identities and actual checks:

- Archive SHA256 `165ffbde2ba234e80a1da450f0e10453b127d79538317b6113ed8c145c6c6de4`;
  public commit `2592dfbe6667586e30d945119418bfefe24690ad`.
- Fresh macOS and anonymous-download runs each pass all 98 checks exactly,
  including all eight PDF figures. The archive download used no GitHub credentials.
- [Ubuntu run 34425107886](https://github.com/isingmodel/latent-art-bench/actions/runs/34425107886)
  passes all 98 checks under the documented portable contract. Seven figure PDFs
  match exactly; the challenge figure renders from verified inputs with different
  platform bytes. Recorded continuous Welch p-value differences reach
  1.1102230246251565e-16 across the original and fresh palette cohorts, with no
  scientific decision changed.

The final reviewers found that Appendix H still described all p-values as exact.
The public release preserves its original archive and original paper asset while
adding an explicit [erratum](../../../reports/paper_reproducibility_v1/pprv1-20260910/PAPER_ERRATUM.md)
and `paper-r1.pdf` / `paper-r1.tex`. This corrects the portable-comparison wording
and one verb agreement; numerical results and figures are unchanged. The additive
assets were anonymously downloaded and hash-verified. The canonical local files
match this corrected r1 manuscript:

- TeX: `4abff8f0b31110746eb6ab4a6de5cdc9992847fa0f0383c3ebb06d3abcbb5535`.
- PDF: `dd7cca03dcd18a999b348577f65b28979d594654c577ec73037d8aa8456891bc`, 32 pages.

All pages underwent visual QA; the final one-word change received a targeted
page check after the corrected paragraph and all 32 pages had passed inspection.

## Final fixed-rubric reassessment

| Review | Scientific rigor | Contribution/significance | Clarity/reproducibility | Mean |
| --- | ---: | ---: | ---: | ---: |
| [Reviewer 1](FINAL_REVIEWER_1.md) | 8.5 | 7.8 | 9.0 | 8.4333 |
| [Reviewer 2](FINAL_REVIEWER_2.md) | 8.4 | 7.9 | 9.1 | 8.4667 |
| [Reviewer 3](FINAL_REVIEWER_3.md) | 8.4 | 7.8 | 8.8 | 8.3333 |

The nine-score average is **8.4111/10**. The increase from this follow-up's round-1
8.2667 reflects actual public access, demonstrated replay and corrected writing.
It does not establish new measurement validity or scientific novelty. The earlier
requested >9 threshold is not met; the rubric was not changed or scores inflated.

No reviewer identified a remaining must-fix defect for the stated computational
scope. Material limitations remain: representation/capture validity, fixed panels
and templates, narrow temporal transfer, unresolved palette effects and service
assumptions, unavailable public pixels, and no external-investigator replication.
These require different evidence, not a higher score from another wording cycle.
All reviewers disclose maintainer-run LLM status and implementation involvement.

Final engineering verification: 1,245 offline tests passed; Ruff passed; the
historical evidence audit passed 2,902 checks with the same two acknowledgements.
Standalone palette replay and all eight local figure bytes also pass. User-owned
Korean drafts remain unchanged and outside the public release.
