# ICML draft and independent scientific review

This is a local AI review simulation, not a conference decision. The manuscript
uses the unmodified official ICML 2026 anonymous style provisionally; a
September 2026 experiment is not represented as an ICML 2026 submission.
The fixed [rubric](rubric.md) separates scientific recommendation from editing
quality. Historical editorial scores are not scientific acceptance evidence.

## Current result: round 04, replacement goal achieved

The user replaced the earlier objective with a mean recommendation of at least
5.0. A substantive revision added the complete retained 2,000-image SD-Turbo
cross-collection decomposition and fixed reference-calibrated abstention test,
including their adverse results. No new paid calls, downloads or image collection
were performed. See the [revision record](round_04/revision.md).

Three fresh independent reviewers read the identical 8-main-page, 60-total-page
PDF under the unchanged rubric, without historical scores or the requested
threshold. Their recommendations are **6, 6, 4**, mean **5.333333333333333**.
All reviews remain included, including the contribution review below acceptance.
The [aggregation](round_04/summary.json) binds all reviews to PDF SHA-256
`3fbf2dafd970a1d352d63af336bd6cb4c089f2332dc8df604428cb4d9e3e62ac`.

The [complete review report](review_report_2026-09-21.md) records verification,
remaining scientific limits and concrete editorial/prior-work corrections still
present in the scored PDF. The artifact is preserved exactly as reviewed. The
native app record remains the prior blocked 8.2 goal; it was not falsely marked
complete when replacement registration failed. The new user objective is
achieved in the recorded work, and further work has stopped at that threshold.

Historical round descriptions below retain their original results and refer to
the manuscript state at each round.

## Round 01: completed

The frozen input is [recorded here](round_01/inputs.json). Three independent
reviewers read the same 23-page PDF, with eight main pages. Its SHA-256 is
`4ee2a3004226bbcd0151ca310265efad851b69e431d1e05895701b8f918a3e85`.

| Focus | Overall recommendation |
| --- | ---: |
| [Methods](round_01/reviewer_method.md) | 4 |
| [Empirical evidence](round_01/reviewer_empirical.md) | 4 |
| [Contribution](round_01/reviewer_contribution.md) | 4 |
| Unweighted mean | **4.0** |

The [machine-readable aggregation](round_01/summary.json) binds each original
review. No score or reviewer has been discarded or replaced. All three judged
the calculations and limited claims substantially sound, but found insufficient
independent empirical significance. Passing numerical replay is not equivalent
to addressing this scientific objection.

## Round 02: completed, mean 4.0

1. Direct named-minus-generic common/specific decomposition, interaction
   accounting and descriptive scene influence, in a separate
   [v3 analysis](../painter_specificity_review_v3/report.md).
2. A fixed [same-image learned-representation plan](../../studies/painter_learned_audit_v1/PLAN.md)
   compares CLIP and the released CSD style checkpoint with the original
   measurements. It is retrospective, uses all existing images and reports
   unfavorable as well as favorable findings. It adds representations, not
   fresh requests or independently collected reference images.
3. Request-order diagnostics and exact-pixel/attribution auditing. Source
   licenses include CC BY/BY-SA as well as public-domain/CC0 records; the new
   draft must not describe every reference as public domain.
4. Explicit main-text inference assumptions, source-license scope and the
   contrasting learned-representation findings are integrated in the revision.

The [frozen second input](round_02/inputs.json) has **8 main pages, 31 total** and
SHA-256 `ad4377767c0d442617b9a6dff49eb1231e1c359072daf3e317ba87c20f206e14`.
Both encoders produced all 2,009 planned vectors. Common movement supplies
73.2–83.8% of CLIP and 54.2–79.7% of CSD named-minus-generic prototype gain.
Monet–Sisley point alignment is positive in all configurations in both learned
representations, qualifying the original hand-feature finding. These results
add same-image representation comparisons, not new service draws or perceptual
validation. The [implementation report](../painter_learned_audit_v1/REPORT.md)
and [revision record](round_02/revision.md) separate evidence from remaining limits.

Three fresh reviewers received the same complete PDF without the target score,
prior ratings or one another's reviews. The first panel helped implement the
revision and therefore cannot independently score its own work. This is a new
full panel after substantive revision, not replacement of a low-rated reviewer.
All first-round scores and artifacts remain. All three second-round reviewers
again recommend **4**, giving an unweighted mean of **4.0**. See the
[methods](round_02/reviewer_method.md), [empirical](round_02/reviewer_empirical.md)
and [contribution](round_02/reviewer_contribution.md) reviews and the
[hash-bound aggregation](round_02/summary.json). The requested scientific score
goal is not achieved. The reviewers credit the learned audit and careful
calculations, but request a validated evaluation consequence, a control for
the shared artistic family/style-clause framing, better fresh-request evidence,
and independent access to exact pixels.

Retained absolute gain components, real-work and generated-image confusion
matrices, and learned calibration values are now in the
[unscored reporting revision](post_round_02_reporting/README.md): 8 main pages,
34 total. No new scientific rating is assigned to that revised PDF.
This alone is not a substantive reason for a new scored round.

The [public-artifact feasibility check](external_audit_feasibility.md) found no
verified released numeric panel with the matched named/control observations
required for an independent broader audit. A
[prospective-control proposal](prospective_controls_v2.md) specifies 4,608 new
images, approximately $200 in historical-rate new charges, a proposed $350
cumulative ceiling and 40 GiB of free storage. Both financial scope and storage
destination await the user; no acquisition has started.

## Round 03: completed, mean 4.0

An additional
[held-scene prompted-name task](../../studies/painter_prototype_transfer_v1/PLAN.md)
has now been executed on retained images after freezing its rules and inputs.
The [complete transfer report](../painter_prototype_transfer_v1/REPORT.md) retains
all 48 encoder/view/target/configuration conditions and all three rules. On the
original primary target, common translation changes mean accuracy by +2.68
percentage points in CLIP and +9.97 in CSD; CLIP declines for two configurations,
ties for one and improves for three. Supervised generated centroids outperform
both reference rules in all 12 primary combinations, with a different information
budget. Exact replay and 39 constructed tests pass. A new manuscript revision
has integrated these results. The third review input is frozen at 8 main pages
and 46 total pages; its PDF SHA-256 is
`bbcc12901427538ed0938cdea510f848a0999d0edd08b4bc707c5b6fb8051472`.
This provides a prompted-name decision consequence,
not perceptual fidelity, fresh service replication or a shared-family control.

The same third-round input also includes a separately frozen
[cross-repeat covariance sensitivity](../painter_repeat_covariance_v1/REPORT.md).
All six primary-D curves and all 15 pair curves are reported at a fixed grid of
hypothetical common trace correlations. Three pairs have positive point-order
crossings; actual covariance is not identified and no interval is repaired.
Exact replay, 26 constructed/provenance tests and independent raw-array
reconstruction pass. Both additions and their limits are described in the
[third-round revision record](round_03/revision.md). All previous scores remain.

Three fresh, target-blind reviewers completed independent reviews of that exact
PDF. Their unweighted overall mean is **4.0**, from recommendations **4, 4, 4**:
[methods](round_03/reviewer_method.md), [empirical evidence](round_03/reviewer_empirical.md),
and [contribution](round_03/reviewer_contribution.md). The
[aggregation](round_03/summary.json) binds all six original review files and the
reviewed PDF; no reviewer or score was replaced. The requested mean above 8.2
remains unachieved. The panel credits the concrete decision effects and careful
conditional computations, but requests independent observations, a shared-family
control, stronger contribution differentiation and external access to pixels.
The contribution review also identifies omitted raw-CSD diagnostic prior work.

The [precollection methods audit](prospective_controls_method_audit.md) separates
design corrections from evidence requiring new requests; the
[v3 addendum](prospective_controls_v3.md) adopts the required claim/estimand and
transport-test corrections while preserving the full proposed allocation.
The [new external-data check](frochte_external_feasibility.md) found no verified
compact release from the newly identified paper. Financial approval, sufficient
storage and collector qualification remain outstanding.

A [verified numerical transport bundle](numeric_bundle_v1/README.md) now passes
all 16 fixed checks after extraction into a separate directory, without reading
the original checkout's source/data. It contains the reviewed PDF and complete
round-03 evidence bindings. It does not supply exact pixels or new observations.

The current manuscript includes an
[unscored literature correction](post_round_03_reporting/README.md), still
8 main pages and 46 total, with SHA-256
`115f9ff33762e932d44fa3e8dbc9582af5f4ffd6a13e8406695c4eb43de89147`.
Only the Introduction, Related Work and added bibliography entry changed;
all later scientific source and numerical results are preserved. Neither
packaging nor these editorial corrections justify assigning a new scientific
score. Round-03 scores remain attached to their original frozen PDF.

## Validation boundary

The [evidence audit](evidence_audit.md) records numerical and local pixel checks.
`make icml-format-check` verifies measurable format properties; all pages must
also be rendered and inspected after substantive manuscript edits. Local pixel
access does not establish public exact-pixel recoverability, source-judgment
accuracy, perceptual fidelity, unseen-artist transfer or service independence.

The original full suite recorded 881 passes and 10 low-disk failures. A declared,
scoped storage fixture subsequently verified all 85 cases in the affected mock
collector modules, including all 10 failures, with frozen production code and
tests unchanged. The [environment audit](validation_environment_audit.md)
preserves both outcomes; this is not described as a vanilla full-suite pass.
