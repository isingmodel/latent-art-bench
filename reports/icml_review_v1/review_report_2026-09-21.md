# ICML manuscript revision and scientific review report

Review date: 21 September 2026. This report concerns the user's replacement
objective: an arithmetic mean of at least 5.0 from all three independent
ICLR-style AI scientific reviewers on the exact final PDF. These are simulated
reviews, not an official conference decision or a prediction of acceptance.
The fixed overall scale is 0, 2, 4, 6, 8, 10; presentation subscores are not the
stopping statistic.

## Current review status

**The replacement goal is achieved: (6 + 6 + 4) / 3 = 5.333333333333333.**
All three reviewers inspected the identical frozen PDF listed below. No review
was excluded, replaced or rounded upward to reach the threshold.

| Reviewer | Overall / 10 | Soundness / 4 | Presentation / 4 | Contribution / 4 | Confidence / 5 |
|---|---:|---:|---:|---:|---:|
| [Methods](round_04/reviewer_method.md) | 6 | 3 | 3 | 3 | 4 |
| [Empirical evidence](round_04/reviewer_empirical.md) | 6 | 3 | 3 | 3 | 4 |
| [Contribution](round_04/reviewer_contribution.md) | 4 | 3 | 3 | 2 | 4 |

The methods and empirical reviewers lean toward acceptance as a careful,
bounded evaluation case study. The contribution reviewer remains below the
acceptance boundary because the four-painter scope, overlap with prior work
and incomplete public pixels limit significance. All three independently
reproduced central computations. The [complete aggregation record](round_04/summary.json)
binds every review and the exact PDF. Round 03 remains preserved at 4/4/4;
it is neither replaced nor relabeled as a review of this revision.

The paper's reviewed bytes are preserved after review. The following substantive
limits and identified editorial corrections are recorded for a future revision,
not represented as changes already made to the scored PDF.

## Reviewed artifact

- PDF: `output/pdf/latent_art_bench_icml.pdf`.
- SHA-256: `3fbf2dafd970a1d352d63af336bd6cb4c089f2332dc8df604428cb4d9e3e62ac`.
- Main text: 8 pages. Complete document: 60 pages.
- Format: unchanged official ICML 2026 anonymous style, used as a provisional
  format target; no claim of an ICML 2026 submission.
- [Frozen round-04 inputs](round_04/inputs.json) bind the PDF, text extraction,
  manuscript sources, bibliography and figures.
- [Scientific evidence manifest](round_04/evidence_manifest.json) binds 44
  retained evidence files. All 23 round-03 scientific bindings are unchanged.
- [Format validation](round_04/format_validation.json) and
  [visual QA](round_04/visual_qa.json) passed. The final document has no detected
  clipping, overlapping text, broken tables, unreadable figures or blank pages.

## Substantive changes

### Separate SD-Turbo collection

A frozen retrospective decomposition now covers all 2,000 retained images:
25 paired-seed repeat blocks, 16 scenes, all four painters and a baseline
already requesting oil painting. Within a scene/block, conditions share seeds;
independent-block cross-products preserve this pairing. Every generated pixel
hash differs from the main 1,008-image collection. The historical target and
scaler are shared and previously exposed.

The complete 31-coordinate metric has 64.18% common naming change after scene
averaging, with 63.87–64.59% across all 25 block deletions. Color and spatial
coordinates also have majority-common change. Texture does not: 36.58% pooled
and 48.50% within scenes, with negative majority contrasts throughout deletion
checks. Pooled error is .917 and scene-wise error is 1.637. Both aggregation
targets, all feature families and every painter pair remain in the paper and
numeric record.

This is a different retained collection, not a new prospective validation set.
It changes checkpoint, prompt template, resolution and generation mechanism
together. It does not establish closed-service independence or supply the
missing shared-family control.

### Reference-calibrated abstention

A fixed historical-artwork calibration rule at alpha .10 now decides whether
to issue an unchanged prompted-name prediction. It is compared with ordinary
prototype-margin filtering at exactly the same number of accepted named
queries. No generated label fits either selection rule. All eight
encoder/view/target settings, six configurations, four painters, control arms
and 14 scene deletions are retained.

In the primary CSD/original/primary setting, accepted error decreases by a mean
26.03 percentage points relative to unrestricted prediction but by only .526
points relative to the matched-margin comparator. Coverage is 24.11–57.14%.
Five configurations miss the declared 50% coverage floor, and three omit at
least one painter. GPT Image 1 has zero accepted errors, but its 30 accepted
queries include 28 Cezanne and no Sisley. FLUX retains over half its queries
while retaining 53.13% error, worse than the comparator's 48.44%.

All eight settings fail the joint declared operating criterion. The 50% floor
is a study-specific choice, not a universal standard. Continuous results and
positive CLIP improvements remain explicit; no alternate gate or alpha was
selected after seeing adverse outcomes. The new main-text heatmap displays all
24 primary painter-acceptance counts.

## Remaining review findings and concrete corrections

All three reviews identify narrow painter/reference scope, unidentified actual
closed-service dependence, and incomplete public exact-pixel access. The
separate collection improves evidence but does not establish prevalence across
artist groups. The selective result should be interpreted through continuous
coverage, painter omissions and matched-margin differences, rather than treating
the chosen 50% floor as a universal boundary.

The reviews also identify concrete corrections still present in the scored PDF:

1. **Table 2, page 5:** the artist-free arm has no painting instruction. Its
   caption should say that the *named-minus-artist-free change* includes the
   painting clause, rather than attributing that clause to the baseline.
2. **Related work, Section 2:** the description of Frochte v2 as excluding
   closed-set discrimination is too broad. Its Section 8 and Appendix E include
   generated-image top-1/top-5 recognition and LoRA stress tests. The distinct
   claim should instead emphasize the present controlled generic-baseline
   decomposition and mean-offset intervention. This was checked directly against
   [Frochte v2](https://arxiv.org/html/2605.09030v2).
3. **Selective-classification positioning:** acknowledge established results on
   improved aggregate accuracy coexisting with group disparities. Painter-class
   coverage is a different setting, so the paper should explain the connection
   without claiming the general warning as new. See the primary paper by
   [Jones et al.](https://arxiv.org/abs/2010.14134).
4. **Conclusion:** change “an coverage-matched comparator” to
   “a coverage-matched comparator.”

These corrections are explicitly disclosed here. The evaluated PDF is unchanged,
so the reported mean applies to the exact delivered artifact. A broader claim
would require new evidence; none of the reviewers treats code tests or added
caveats as a substitute for that evidence.

## Verification

- Independent pre-outcome audits passed after resolving exact pair/family
  definitions and selective audit/runtime enforcement.
- The two implementations passed 110 constructed tests combined.
- Independent raw-input cross-cohort replay compared 22,553 numeric values and
  7,488 categorical/null values, with maximum numeric difference 1.85e-13.
  All 47 input bindings and 3,657 source-image hashes matched.
- Independent selective replay compared 435,066 values across every setting,
  configuration, gate, comparator, control and scene deletion. Maximum absolute
  difference was 1.11e-16; all decisions and counts agreed exactly.
- Exact result/report replays and deterministic table checks passed.
- All legacy `make icml-evidence-check` computations and tables passed.
- The original Korean PDF remains unchanged from its completed notice-removal
  build: 26 pages, SHA-256
  `096db88b2a5119dc6697e2064ceff554e90a581fb3cec93329507cc221e27ab2`.

These checks establish computation and layout consistency conditional on retained
inputs. They do not establish scientific acceptance, perceived painter fidelity,
unknown service independence, or complete public exact-pixel recovery.

Audit records:

- [Cross-cohort method/code audit](resume_2026-09-21/cross_cohort_preoutcome_audit.md)
- [Cross-cohort numerical audit](resume_2026-09-21/cross_cohort_numeric_audit.md)
- [Selective method/code audit](resume_2026-09-21/selective_preoutcome_audit.md)
- [Selective numerical audit](resume_2026-09-21/selective_numeric_audit.md)

## Review integrity and remaining scope

The three reviewers are fresh agents with no inherited conversation history.
Each receives the same frozen PDF and unchanged rubric, reads the complete
manuscript, and writes its own report. They are instructed not to read the
user's threshold, historical scores, other current reviews or working goal
records. No reviewer is replaced or excluded because of a score. All prior
rounds and negative evidence remain preserved.

The scientific scope remains four related painters and finite digital reference
panels. The new analyses reuse previously exposed observations, no shared-family
prompt control was added, and closed-service repeat dependence remains unknown.
Exact pixels were verified locally; a complete public recovery route remains
outstanding. No new paid generation, image collection, model download or human
evaluation occurred in this revision.

The app's native goal record still contains the prior blocked 8.2 objective.
The attempt to register the replacement 5.0 goal was rejected because that
record is unfinished. It was not falsely marked complete. The replacement
request and current work are recorded in
[the resumed goal request](resume_2026-09-21/goal_request.json).
