# Current status — 2026-09-09

**Computational painter responsiveness v2 is complete**, following the user's
instruction to continue without human reference ratings. The sole primary run
completed all 192 images and all three measurement pipelines. Its two primary
named-minus-generic color-response interactions remain unresolved. The
[scientific report](../reports/painter_responsiveness_v2/REPORT.md) combines these
results with a retained-data scene-retrieval counterexample to interpreting
contraction as lost scene distinguishability. No collector or image measurement
process is active. The [exact-weight quantile corrigendum](../reports/painter_responsiveness_quantiles_v1/prqv1-20260908/REPORT.md)
corrects a descriptive median defect found during review. Primary inference,
means, Wasserstein distances and range occupancy are unaffected.

## Completed collection and analysis

- Replacement: `prv2-oauth-recovery-20260908`; 192 measured images, six fixed
  scenes, four style arms,
  two color instructions and four repeats. Free and generic controls are shared.
- Transport: source/process-verified local OAuth `gpt-image-2`, at most two calls
  in flight, starts at least five seconds apart, bounded technical retries.
- Replacement source commit: `c020c3e`; freeze commit: `9574c35`; 145 bound inputs.
- Terminal collection commit: `8a14c93`; primary and ancillary analysis commit:
  `9741309`. The [primary bundle](../reports/painter_responsiveness_v2/prv2-oauth-recovery-20260908/experiment/REPORT.md)
  contains 19 tables and four plot pairs. No primary data are missing.
- Original source commit: `d3bbe65`; design freeze commit: `491cc10`; 131 bound inputs.
  Its terminal run retained 49 images, one complete HTTP 503 and 142 never-started
  slots. A [prospective correction](../studies/painter_responsiveness_recovery_v1/PROTOCOL.md)
  qualifies only that exact error form for existing bounded retries. Prior outputs
  remain ancillary; successful images were not visually reviewed and scientific
  features were not extracted before the replacement decision.
- No OpenRouter requests or charges in this experiment. The prior conservative
  accounting remains $45.6819185 within the $75 ceiling; OAuth subscription usage
  is not assigned a monetary value.
- The ancillary predecessor was measured only after replacement collection ended;
  its 49 images are not pooled into primary inference. Across both collections:
  242 actual attempts, 241 unique images, one HTTP 503, zero retries. Both terminal
  ledgers and all raw-response/image hashes verify.
- All 192 primary outputs were nonsquare despite a square request; 174 reported low
  quality and 18 medium despite a fixed medium request. These post-request fields
  remain unfiltered. Findings concern the complete delivered-service response.
- Human ratings, new original-painting acquisition and learned features are outside
  this scope. The manuscript now integrates both studies and their distinct test families.
- Quantile correction: source `2062eab`, freeze `7380f80`. Exact rational weights
  correct 51 primary-run and 15 ancillary-run quantile records, all medians. No
  10th/90th percentile endpoints or central-80 inclusion memberships change. The
  original bundles remain preserved; nine corrected report files replay exactly.

Do not edit frozen v2 or recovery sources, tests, configuration or protocol.
Collection is terminal; do not launch another collector. A stopped or completed allocation is
closed and cannot be resumed or refilled. See the
[implementation guide](../studies/painter_responsiveness_v2/README.md) and
[protocol](../studies/painter_responsiveness_v2/PROTOCOL.md).

## New retained-data finding

The [scene-retrieval report](../reports/painter_responsiveness_v2/prv2-oauth-20260908/diagnostics/REPORT.md)
is published. Painter naming reduces between-scene variation in all six historical
route/painter cells, but retrieval **improves in two and declines in four**.
FLUX/Monet improves from 44.4% to 59.7%, whereas Nano Banana 2/Cézanne declines from
66.7% to 41.7%. OAuth/Monet declines from 79.2% to 70.8%; OAuth/Cézanne from 83.3% to
69.4%. These are held-repetition, 24-scene nearest-centroid descriptions in the
fixed 31-feature space, not new significance tests or human scene-adherence scores.
Contraction alone therefore does not establish lost scene information.

The report includes all 450 comparisons across five feature views, three pipelines
and both 24-scene/within-class candidate controls. The sealed JSON retains exact
query/split identities and 25,920 predictions. A separate 5,000-trial-per-scenario
precision sensitivity uses historical OAuth residual proxies and hypothetical
interactions; it is not a human margin or a guarantee of future power.

## New intervention finding

Median-chroma vivid-minus-muted responses are 3.489, 2.636, 2.351 and 2.618 fixed
development-IQR units for artist-free, generic, Monet and Cézanne. The secondary
generic-minus-free contrast is −0.853 (nominal 95% interval [−1.136, −0.570]).
Additional painter-minus-generic effects are Monet −0.284 (simultaneous family
interval [−0.585, 0.016], Holm p=0.0649) and Cézanne −0.018 ([−0.343, 0.308],
p=0.8886). Neither primary direction is resolved. The JPEG sensitivity's marginal
Monet threshold crossing does not replace the prespecified primary result.

The report compares empirical original/generated chroma distributions, including
Wasserstein distance and directional range occupancy. Close means or wide range
overlap do not establish matching distributions. Two extreme color instructions
cannot identify a response curve or explain the original/generated gap by themselves.

## Preserved earlier work

| Item | State |
| --- | --- |
| Controlled study | 1,006 generated images, 70 Monet/Cézanne references and 221 development works; [report](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md) |
| Computational revision | Four feature views, variance decomposition, reference/scaler sensitivity and cross-route diagnostics; [report](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md) |
| Current manuscript | Integrated English research paper, one TeX source, five vector figures and compiled PDF; [guide](../paper/README.md) |
| Responsiveness v1 D0 | Six equal-brief diagnostics and original-reference chroma summaries; [report](../reports/painter_responsiveness_v1/prv1-diagnostic-20260908/REPORT.md) |
| Responsiveness v1 H0/R0 | Reference tasks prepared with zero human responses; closed FLUX preflight does not qualify its paid/human scope. This does not block the new computational OAuth scope. |

The original eight conditional randomization tests and all earlier evidence remain
unchanged. The v1 human/reference prerequisites were not retroactively waived or
fulfilled. Its source commit `79f3573`, D0/H0 freezes, reports, closed R0 receipt and
ignored displays remain preserved. The updated manuscript integrates new findings as a second study and descriptive
diagnostic bridge. It does not pool cohorts or alter the earlier tests.

## Verification

The three-reviewer scored manuscript revision is complete. The equal-weight
average increased from **7.8125 to 8.5417/10**, exceeding the requested 8.5
threshold. Final reviewer means are **8.625, 8.500 and 8.500** under the same eight-aspect
rubric, with no unresolved blocking manuscript finding. These are maintainer-run
LLM assessments, not external peer-review scores. The
[scored review record](reviews/20260909_scored_review/REVIEW.md) preserves both full
review rounds, all aspect scores, concrete responses and final artifact checks.

The **19-page PDF with five vector figures** gives each study its own methods and
results, promotes existing painter alignment and matched-real coverage controls,
corrects the prespecification map, and exposes scene-level color interactions and
the prospective proxy calibration. Literature positioning and actual
release/access status are explicit. All 19 delivered pages were visually checked;
final table-placement defects were corrected. Public archival release of the
local scientific snapshot remains pending.

The current build has no TeX warnings. All five figures reproduce byte for byte.
Ruff passes and the full offline suite passes **1,135 tests in 115.43 seconds**.
No scientific source, frozen result, protocol or acquisition record changed;
no new images or charges were incurred. The earlier
[integration review](reviews/20260908_manuscript.md) remains historical.

The complete offline suite, including transport and quantile corrections, passes
**1,135 tests** (115.42 s), including deterministic byte replay and
unavailable-primary output.
Ruff passes. The retained-data analysis and both experiment analyses reproduce;
all **65 published report files** match byte for byte. Both actual diagnostic plots,
all four actual primary plots, and synthetic unavailable-result plots were visually
checked. Both corrected reference-context displays were also visually verified,
and all 66 median correction records matched a separate exact-weight reconstruction.
Three
maintainer-run LLM subagents reviewed methods, transport and rendering, with
coordinator checks; these are not independent human or institutional reviews.
See the [review record](reviews/20260908_computational_responsiveness/REVIEW.md).

The historical evidence audit passes **2,902 checks with zero failures**, retaining
only its two existing acknowledgements. This historical audit does not register v2;
its own offline numerical/report replay commands are separate.
`make computational-responsiveness` verifies the diagnostic, primary replacement
and ancillary predecessor report bundles using the retained response archive,
then the numerical quantile correction. Together these checks cover **74 report
files**, in addition to their saved-vector calculations and input/output hashes.
Current guidance is mutable; [ARTIFACTS.md](ARTIFACTS.md) governs retained evidence.
