# Current status and research boundary — 2026-09-07

## Active goal: implement the controlled study and paper prototype

The user supplied `OPENROUTER_API_KEY` locally and requested implementation plus an English
paper prototype, then explicitly delegated the outstanding choices to the recommendations.
The adopted scope is multi-day collection, a computational paper with human evaluation prepared
for follow-up, and prospective reference-panel adaptation when availability requires it.

Implementation is in the new `painter_distribution_study_v1` namespace. Its
[staged protocol](../studies/painter_distribution_study_v1/PROTOCOL.md) preserves closed historical
studies. The operating cap is **$75**, including the pilot, and the generation cap is 1,026 initial
attempts, including at most 588 paid initial attempts. The user's subsequent
[retry instruction](../studies/painter_distribution_study_v1/RETRY_AMENDMENT.md) adds at most 24
bounded transient-error retries: 1,050 total / 612 paid attempts, with the same $75 ceiling.
The user reaffirmed $75 after the authenticated
preflight showed about $50 available and stated that replenishment is configured. This supersedes
the interim $45 planning limit. The technical pilot spent **$0.8304855**. The first parallel collector is terminal after a diagnosed refusal.
Its closing study charges were $3.3797815, with no unresolved intents or charges;
the remaining-slot continuation later stopped on a complete FLUX 502 with missing cost.
It retains 51 more images and that failure. The bounded recovery later closed at the user's request after four batches.
Its FLUX retry succeeded; the remaining 504 slots are moving to immediate dispatch.

Stage A is complete. The [diagnostic report](../reports/painter_distribution_study_v1/pdsv1-diagnostics-20260906/REPORT.md)
and all 18 output files reproduce byte-for-byte. Content-equal spread ratios are 0.211–0.372 for
named conditions and 0.378–0.728 for artist-free conditions. Artist-free separability is also high;
coarse title-derived content labels do not rule out content differences. Disjoint original splits
give substantially smaller energy discrepancies than the generated/original comparisons.
These remain descriptive diagnostics, not calibrated painter-style conclusions.

GET-only reference and endpoint discovery is complete under `pdsv1-metadata-20260906`: 81 requests,
172,175,160 received bytes, all retained and hashed. The key
authenticated successfully; both proposed image models and pinned providers are listed.
The [technical pilot contract](../studies/painter_distribution_study_v1/PILOT.md) completed all 18
requests successfully, without retries. Google returned six 1024×1024 JPEGs; BFL returned six
1024×1024 PNGs. OAuth returned six nonsquare PNGs and reported low rather than requested medium
quality. Paid routes share geometry but not encoding; OAuth requires a separate service comparison.
The pilot source was committed at `2bd2fb9` and its freeze at `f202082`, before the first POST.
The [pilot qualification report](../reports/painter_distribution_study_v1/pdsv1-pilot-20260906/REPORT.md)
verifies raw hashes, costs and container metadata. The projected research charge, plus 25% headroom
and pilot cost, is $50.6952. All three routes meet the prospective technical criterion.

The [new reference contract](../studies/painter_distribution_study_v1/REFERENCES.md) selects 64 Monet
and 48 Cézanne candidates using recorded identity/exposure checks, a 512-native-pixel minimum and
an explicit outdoor-title screen. Its original-delivery run is now permanently terminal: 97 attempts,
five acquired files, 92 HTTP 429 responses, 15 unattempted. The operator stopped it between requests
after observing rate limits. Its first collector lacked a rate-limit stop guard; preserve the record.

Wikimedia explicitly recommends supported thumbnail sizes. The prospective
[R2 delivery amendment](../studies/painter_distribution_study_v1/REFERENCE_DELIVERY_R2.md) uses a
ten-minute cooldown and stops on the first new rate limit. Its fixed standard-thumbnail inventory
has 38 Monet and 33 Cézanne works; 41 candidates cannot meet both standard delivery and nonupsampling
512-pixel geometry. Four fresh imageinfo responses confirm unchanged parent SHA-1s. R2 requires its
own committed freeze and disjoint paths. R2 completed all **71/71** deliveries; every retained
raw file and the event hash verified. Single-maintainer LLM visual coding admits **70 works**:
38 Monet (21 water / 4 built / 13 land) and 32 Cézanne (3 water / 11 built / 18 land).
One figure-led Cézanne is excluded. Mixed content and visible thin borders are recorded.
This is not expert or independent human annotation. Conditional prompt-inference qualification
passed both fixed-seed phases. The implemented main collector, three measurement pipelines and
analysis pass **813 offline tests** (77.64 seconds); Ruff and the 2,902-check historical evidence
audit pass. Main method source was committed at `d06cb95`; its four-file freeze/inventory
was committed at `a03503b`. Development remeasurement completed all 442 sensitivity vectors
from the same 221 works, and both new scalers are available. Fresh reference measurement now has 210 successful vectors (70 works × three
pipelines), with no failed vectors or duplicate raw hashes. Generated fidelity
vectors remain pending terminal collection.

Before the first research POST, the user requested staggered parallel calls. The sequential
collector was stopped while waiting for its first window and permanently closed with status
`superseded_before_dispatch`: **zero research attempts**. A prospective parallel successor is
implemented with at most three in-flight requests, at least five seconds between starts,
and one active request per model route. It retains the frozen content/analysis design and
the $75/1,050-attempt caps, with new execution paths and predecessor-bound evidence.
Parallel source was committed at `1751557`, its execution freeze at `7ead740`.
The first coordinator was started with eight windows beginning September 6 at
14:30 UTC (23:30 KST), ending with the September 7 23:30 UTC window. It is now
closed after the diagnosed refusal below; the continuation keeps those window times.
All 819 pre-execution offline tests, Ruff and the historical evidence audit pass.
The first live inspection observed nine started requests, six successful completed
images, no failed outcomes, peak concurrency three, peak per-route concurrency one,
and a minimum recorded start gap of 5.0043 seconds. These are an early operational
snapshot, not a partial fidelity analysis. Full report rendering is implemented
and its synthetic fixtures reproduce all 22 output files byte-for-byte. Final
generated measurement, numeric analysis, report and paper results await collection.

The English LaTeX/PDF paper prototype is drafted and visually checked; it distinguishes
completed diagnostics and pilot outcomes from pending new-model comparisons. Human construct
validation is prepared as a follow-up. The user-authorized retry amendment is prospective for
the new collection and preserves all terminal historical evidence.

`.env` is ignored and untracked. Tectonic, Pandoc and Poppler are available. Free storage was
18.7 GiB at preflight; every collection stage preserves the 5 GiB reserve. Stage A validation:
Ruff passed; the earlier pilot-stage suite passed 779 tests before the main implementation.
The parallel and reporting implementations added nine offline tests; that pre-correction
suite passed 822 tests. Reference raw-to-feature replay verifies all 210 vectors. The historical v1 evidence audit passes 2,902 checks. No subagent or
institutionally independent review was used.

### Refusal diagnosis and continuation

The parallel collector stopped at 14:35 UTC with 48 terminal slots: **47 images
and one OAuth HTTP 400 moderation refusal** (`slot0036`). Its generic HTTP 400
rule classified the explicit `moderation_blocked` error as a contract problem.
All 48 retained raw responses verified. Preserve the closed census and its
[diagnosis and continuation contract](../studies/painter_distribution_study_v1/REFUSAL_CONTINUATION.md).

The implemented continuation executes only the 960 unattempted original slots,
with the original window origin, three staggered route workers and unchanged caps.
The refused slot is neither retried nor rewritten. Recognized explicit refusals
remain failed observations; unknown/bad requests still stop, and predecessor
failures continue to count toward the route failure-cluster rule. Combined results
will retain all original slot identities, the 47 prior images and the missing refusal.
Continuation source/terminal evidence was committed at `29027dd`, its freeze
at `ec4ef09`, before resumed dispatch. That coordinator later closed as described
below. The first nine
continuation outcomes were successful, across all three routes; recorded study charges
were $3.8616185 at that early check, with no stop event or uncertain charge. All **828 offline
tests**, Ruff and the 2,902-check historical evidence audit pass.
No generated fidelity vector has been measured. The 11-page paper now specifies
the controlled statistics and their assumptions; final data/results remain pending.

### Complete transient failure and reserved-cost recovery

The remaining-slot collector is now also terminal: 52 attempts, 51 images and one
complete FLUX HTTP 502 submission error (`slot0108`), with no image, generation ID
or reported charge. All 52 raw responses verified. Across both censuses there are
100 original attempted slots and 98 images. Provider-reported study charges are
$5.601998; raw conservative accounting retains another $5 for the missing cost.
There is no unresolved request, but the frozen accounting marks the cost unknown.

OpenRouter's published Image API billing policy waives failed-image requests. The
[new recovery contract](../studies/painter_distribution_study_v1/TRANSIENT_RECOVERY.md)
does not invent a zero-cost receipt: it retains the full $5 reserve while allowing
one technical retry of this narrowly identified complete error. Incomplete or
unclassified responses still stop; the refusal rule and failure-cluster guard remain.
The recovery implements 908 untouched original slots plus one bound retry of
`slot0108`, with the unchanged study design, schedule and caps. The earlier OAuth
refusal stays missing. No generated features have been measured. All 838 offline tests,
Ruff and the 2,902-check historical evidence audit pass. The updated 11-page PDF has
been rendered and visually checked. Recovery source was committed at `94c602e`,
its execution freeze at `fb21593`, before dispatch. The sole coordinator is
`recovery run --watch`; its retry of `slot0108` returned a verified image.
Original window times remain unchanged. Neither closed collector may be resumed.

Windows 0–3 are complete across the three components: **504 original slots,
503 selected images and one retained OAuth refusal**, with one extra FLUX retry.
Windows 1–3 each returned all 126 images on initial attempts. All 405 recovery responses
and image-container metadata verified; the execution freeze and 2,902-check
historical evidence audit pass. Live recovery timestamps showed a peak of three
concurrent calls, one per route, and a minimum start gap of 5.0213 seconds.
Including the 18-request pilot, 523 attempts have completed; reported charges
total $20.7569045 plus the unchanged $5 contingency, with no unresolved request
or unclassified cost. The coordinator had been waiting for window 4,
September 7 at 14:30 UTC (September 7, 23:30 KST). This longer scheduled interval
preserves the prospectively declared separation across days. Four windows / 504
initial slots remain. No generated fidelity feature has been measured.

### User-requested immediate completion

The user explicitly requested the remaining generation now, without waiting for
night. The waiting recovery process was stopped between requests and permanently
closed as `superseded_by_user_schedule_change`, with no unresolved or uncertain
request. Its 405 selected outcomes and all three components' 503 images remain.
The prospective [immediate amendment](../studies/painter_distribution_study_v1/IMMEDIATE_COLLECTION.md)
schedules the 504 untouched slots in batches 4–7 consecutively, preserving their
order, prompts, three staggered workers, references, scalers, analysis and $75 cap.
Original assignment/timing records remain; the paper must disclose that the full
33-hour schedule was not executed. No generated fidelity feature has been measured.
All 843 offline tests, Ruff and the 2,902-check historical evidence audit pass.
Source was committed at `6697108` and the new execution freeze at `d0f8170`, before
dispatch. The sole live coordinator is `immediate run`, execution session `25215`.
Its first 14 completed calls across all three routes returned verified images.
The four remaining batches now run consecutively without scheduled night waits.
The updated 11-page paper records the timing change and has been rendered and
visually checked. The old recovery session `68624` is terminal and must not be restarted.

## Original proposal snapshot, before execution authorization

The user requested an English research proposal and an explicit choice of expansion axis, with
approximately $100 of OpenRouter credit and inexpensive OAuth access. Venue is undecided; learned
features may wait, and new reference evidence/human evaluation are possible. Read the
[research proposal](RESEARCH_PROPOSAL_20260906.md) for the reasoning, literature and cost sources.

The recommendation is to expand **model-family breadth** with Nano Banana 2 and FLUX.2 Max,
preceded by content/capture diagnostics. Add no painters in this round; focus new generation on
Monet and Cézanne, with named/artist-free controls and a generic/detailed intervention on one
OAuth route. All four existing painters remain in the initial existing-data diagnostics.

The proposed ceiling is 1,008 research attempts plus 18 technical attempts, including 588 paid
attempts. Image-output estimates total $40.34 before ancillary costs; the initial operating
envelope is $75 with $25 uncommitted. These are planning quantities, not established power or
an executable spending contract. Reference feasibility, dependence-aware statistical qualification
and actual endpoint cost/rendering contracts must be resolved in a new versioned protocol.

This task changed documentation only. No generation, acquisition, feature extraction, encoder
download or human recruitment was performed. Existing studies remain terminal and their evidence
unchanged. The recommended next task is existing-data diagnostics and a reference-feasibility audit.

## Completed exploration: original versus generated distributions

The user requested scatter plots and an exploration of whether each painter's original and
style-conditioned generated feature distributions separate. The new, explicitly post-hoc
[distribution report](../reports/painter_distribution_exploration_v1/REPORT.md) uses existing
numeric evidence only: 649 originals and 1,536 painter-conditioned generations from the complete
1,920-image derived grid. The 384 artist-free outputs are outside this comparison. No images
were generated, downloaded, opened or remeasured; original evidence and the two retry identities
remain unchanged. This is a newly versioned derived analysis, not active-census work.

- Four painter-specific common PCA bases, all 31 features and each of the three families;
  balanced original/generated mass, with original-only all-31 PCA as a projection sensitivity.
  The 14 PNG/SVG figures retain every point and shared limits within painter/feature set.
- The first two joint PCs retain 42.9–47.8% of balanced all-31 variance. Scatter plots overlap,
  while generated clouds are more concentrated and often shifted relative to originals.
- Full-space generated/original total within-group sample variance ratios are 0.206–0.376
  across the 24 all-31 cells (median 0.252). This is outlier-sensitive feature spread, not a
  calibrated measure of artistic diversity. This summary was added after first plot inspection.
- Fixed linear/RBF kernel ridge classifiers, without tuning or PCA input, use held-out whole
  scenes and disjoint original works. Across all 24 all-31 cells, balanced accuracy is
  0.913–0.976 (linear) / 0.940–0.983 (RBF). A nominal-block split is also reported. These are
  descriptive scores, without p-values, confidence intervals or independent-session claims.
- Exported 20 projection bases, 10,925 point coordinates, 240 classifier summaries, 10,860
  all-31 out-of-fold prediction records and 96 within-group variance comparisons. Capture,
  content and service artifacts remain possible explanations; painter style is not isolated.

Read the [exact methods](../studies/painter_distribution_exploration_v1/METHODS.md). Reproduce with:

```bash
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_distribution_exploration_v1.report check
```

The implementation and 96 consumed inputs are bound to commit `1a8065b` in the report's
provenance. All 35 report files reproduce byte-for-byte, including 14 PNG/SVG figures; the actual
figures were visually inspected. Ruff passed and all **749 offline tests passed** (76.25 seconds).
Historical v1/v2 audits passed 2,902 / 15,809 checks. A separate primal linear-ridge calculation
reproduced all all-31 held-out scores within 2.25e-14; SVD reproduced all 20 PCA variance ratios
within 3.89e-16. Both calculations were run by the same maintainer agent, not an independent review.
Portable-path and document-link checks passed. Historical frozen studies remain unchanged;
this does not restore the original primary result.

## Completed follow-up: two refusal retries

**Both user-authorized retries succeeded and were measured.** The latest
[main distance report](../reports/painter_prompt_retry_v1/ppr1-two-refusals-20260906-r2/REPORT.md)
uses a complete derived grid of **1,920 measured images**, with 64 per alias/method/condition.
The earlier 1,920 attempts plus these two retries total **1,922 requests**, 1,920 generated images
and two preserved original refusals. No third retry, rewording or fallback was used.

Run `ppr1-two-refusals-20260906` dispatched the exact original `gpt-image-1`/`by_name` payloads
for source sequences 415 (Pissarro) and 1718 (Cézanne), in that order. Both returned HTTP 200;
generation ended at **2026-09-06 00:57:04 UTC**. Their returned images are 1403×1121 and 1402×1122,
both reported quality low despite requested 1024×1024/medium. Two gzip bodies totaling 5,809,781
bytes retain the original responses under the disjoint shared-transport runtime path
`research_workspace/painter_prompt_study_v1/ppr1-two-refusals-20260906/`.

The [retry protocol](../studies/painter_prompt_retry_v1/PROTOCOL.md), source and tests were committed
at `38f1139`; the 82-input retry freeze was committed at `861dcc3` before either request. Original
study and supplement files remain unchanged. Successful retry features are associated with their
original missing slots only in the derived analysis, with explicit replacement provenance.

The main results retain the same 649 reference paintings, 221-work scaler and all 31 features:

- By-name prompts have the smallest distance among all three methods in **19/24**
  alias × painter × family cells; style plus aspects is smallest in the other **5/24**.
- Explicit style instruction has larger distance than by-name prompting in **24/24** comparisons.
  Adding aspects reduces distance relative to style instruction in **13/24** comparisons.
- Exactly 24 full-matrix cells changed, involving the two retried conditions against all four
  reference painters and three families. Only six target distances changed; the largest absolute
  target change was 0.0078919015 (Pissarro texture under `gpt-image-1`).
- Exported all 360 distances, 72 targets, 48 adjacent-method differences, 72 artist-free comparisons,
  24 changed cells, 30 availability rows and a PNG/SVG figure. No new randomization p-values or
  confidence intervals are claimed: these later outputs do not occupy the original randomized
  time slots. The original primary and pre-retry exploratory tests keep their original status/data.

A separate direct uniform-energy calculation reproduced every new distance within **2.45e-15**.
The retry's numeric/report-byte check passed, including retained response hashes. Ruff passed;
the full offline suite passed **732 tests in 74.54 seconds**. Historical v1/v2 audits passed
2,902 / 15,809 checks, the original prompt-study audit passed 5,977 checks, and the original
supplement audit passed. The two historical acknowledgements remain unchanged. The final figure
revision check reproduced all nine files byte-for-byte with no numeric changes; its actual PNG
was visually inspected and every point is inside the shared family bounds. No subagent review
was used for this follow-up.

The first retry report's shared-axis plot clipped a lower-row point. A separate revision at the
linked `-r2` path fixes family limits using both aliases plus an 8% margin; all CSVs and numeric
results are unchanged. Its renderer/tests are committed at `0e8080f`. The original report and its
hash receipt remain preserved. No image generation or feature extraction was repeated for this fix.

Reproduce from the repository root without provider calls or feature extraction:

```bash
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_retry_report_v2 check
```

All retry stages are terminal. Do not redispatch these requests or reuse the run ID. The original
no-extra-request wording below describes the preceding closed run; the user's later authorization
applied only to this completed two-attempt follow-up.

## Completed goal: repeated GPT Image prompt study

The approved extension is **complete**. Read the
[exploratory prompt-comparison report](../reports/painter_prompt_supplement_v1/ppss1-missingness-20260905/REPORT.md)
and [reproduction workflow](PROMPT_SUPPLEMENT_WORKFLOW.md). The original
[registered report](../reports/painter_prompt_study_v1/pps1-gpt-prompts-20260905/REPORT.md)
retains its `unavailable_incomplete_grid` primary status.

### Terminal accounting

Run `pps1-gpt-prompts-20260905` attempted all **1,920 approved requests exactly once**, producing
**1,918 generated and measured images** and **two moderation refusals**. There were no additional
measurement failures, replacement requests or retries. Generation ended at **2026-09-06 00:04:14
UTC**; measurement ended at **00:22:12 UTC**. Both completion workers exited successfully; the
supplement's build, check and audit finished at **00:23:39 UTC**. All stages are terminal.

- Requested aliases: `gpt-image-1` has 958 measured outputs and two refusals; `gpt-image-2` has 960
  measured outputs. These are service labels, without attested underlying model snapshots.
- Design: three prompt methods × two aliases × four painters plus matched artist-free controls ×
  16 scenes × four repetitions. This gives 64 planned outputs per alias/method/condition.
- Both refusals were HTTP 400 input-moderation responses under `gpt-image-1`/`by_name`: sequence
  `415` (Pissarro, L3, block 0) and `1718` (Cézanne, B2, block 3). Their original responses and
  positions remain evidence. They consume two of the approved requests; do not top up the grid.
- The exposed reference remains 649 measured painting surrogates (Monet 297, Sisley 106,
  Pissarro 141, Cézanne 105), with the unchanged 221-work development scaler and all 31 color,
  spatial and digital-texture features at the original 512-short-side normalization.
- Losslessly compressed original HTTP bodies remain under the ignored
  `research_workspace/painter_prompt_study_v1/pps1-gpt-prompts-20260905/`. Compact terminal
  ledgers, measurements, receipts and report hashes are in its manifest namespace. Preserve both.
  Exactly 1,920 unique gzip bodies occupy 5,764,937,227 bytes (5.369 GiB), retaining 7,642,864,266
  uncompressed response bytes. Both stored and uncompressed hashes passed verification.

### Available-output supplement

The [post-registration supplement](PROMPT_SUPPLEMENT_WORKFLOW.md), `ppss1-missingness-20260905`,
was specified after the first refusal and before new-image feature measurement. It does not
restore the original primary result. Its 18-file report bundle contains 10 full-precision CSVs,
three PNG/SVG plots, a Markdown report and diagnostics JSON.

- All 360 descriptive distance cells, 72 target summaries, 744 coordinate diagnostics and 72
  secondary contrasts are available. Available outputs receive equal total mass across 16 scenes.
- All 48 exploratory prompt endpoints are retained and available: 42 use 64 common measured
  pairs and six use 63. The 1,024 planned pair records retain both exclusions; the 3,072 family
  contribution records retain all six excluded contributions. Before/after distances in these
  tests use common support, which differs from all-available support where a request was refused.
- All 24 by-name → style-instruction estimates are positive on their observed supports, meaning
  greater finite feature distance after the explicit instruction. Three reject the joint null
  after Holm correction: Monet color under both aliases, and Pissarro texture under `gpt-image-2`.
  Added-aspect directions are mixed and none rejects after Holm correction. These observations
  do not establish a population effect, a feature-only causal effect or an aesthetic ranking.
- The tests address a joint sharp null of no method effect on availability AND measured features,
  conditional on third-method positions, with no interference. There are 99,999 seeded swaps per
  endpoint, a fixed 48-test Holm family and no confidence intervals or equivalence claims.
- Returned geometry differs from requested 1024×1024 in all 1,918 outputs; reported quality is
  `low` for 1,906 and `medium` for 12 despite a medium request. Content, capture and hidden service
  behavior can affect distances. No exact generated duplicates or reference perceptual-hash
  candidates were found; that uncalibrated screen is not a copying or originality verdict.

### Frozen design and validation

The authorized source inputs were committed at `3251bda` and the generation freeze at `04106cc`.
All 62 original freeze-bound inputs remain unchanged. The supplement implementation/tests are
bound to `b029031`, qualification to `ea6ee7b`, and design freeze to `f877cf0`. The supplement
freeze was created **2026-09-05 15:06:53 UTC** and committed at **15:06:57 UTC**, before measurement.
It binds 83 inputs and a source-ledger prefix containing 579 generated outputs and one refusal;
these are immutable checkpoint counts, not the terminal counts above.

All eight development and eight unseen-validation valid-null cells passed the fixed Wilson-upper
criterion of 0.065 at 2,000 trials per cell. Maximum observed family-wise rejection was
0.0475 / 0.043, with maximum Wilson 95% upper bounds 0.0577209072 / 0.0528011087. Full numerical
qualification replay passed; no thresholds or seeds were tuned. Synthetic qualification does not
establish the actual service's assumptions or guarantee power for image outcomes.

Final handoff verification passed on 2026-09-06:

- Ruff clean; all **722 offline tests passed** (79.57 seconds).
- Source audit: **5,977 checks passed**, including the inspected proxy source and retained bodies.
  Source and supplement numeric/report-byte replay passed for all five and 18 files respectively.
  The earlier distance bundle's 26 files also reproduce byte-for-byte.
- Supplement evidence audit passed. Current bytes and recorded Git blobs match all 62 original,
  79 qualification and 83 supplement inputs. Committed supplement publication preceded the
  hash-chained measurement start by 8h57m20.661s. No frozen input or acknowledgement changed.
- Historical v1/v2 audits: **2,902 / 15,809 checks passed**, retaining exactly the two existing
  v1 acknowledgements. Portable-path checks passed for all new terminal text artifacts.
- A separate numerical implementation recomputed all 360 weighted distances (maximum absolute
  error 1.56e-15), all 744 coordinate records (exact), 48 paired estimates, 3,066 included
  coefficients and 72 secondary contrasts. All 48 raw and Holm p-values match exactly.
- All three actual PNG/SVG plots and full-precision CSV inventories were reviewed. The original
  unavailable-primary report has no plots; its generic figure-footer wording is explained in
  [the source workflow](PROMPT_STUDY_WORKFLOW.md) without changing frozen report bytes.

Reviews, including the separate numeric implementation and visual checks, are **maintainer-run
LLM subagent reviews**, not institutionally independent reviews. Diagnostic verification logs
are retained under `tmp/final-evidence-audit-20260906/`; durable manifests and reports remain
the evidence authority.

Do not resume generation, remeasure images, rewrite terminal evidence or reuse immutable run IDs.
Read-only `check`/`audit` commands are in the workflow. Future empirical expansion requires a new
versioned design and authorization; manuscript drafting remains deferred.

## Completed existing-data deliverable

The earlier existing-data deliverable is the **[feature-distance report with comparison
plots](../reports/painter_feature_distance_v1/REPORT.md)**. The user explicitly selected existing
painters/images, the existing 31 interpretable features, and reproducible commands plus a plotted
report. The implementation under `painter_feature_distance_v1` is a separate descriptive analysis
of already exposed numeric v2 evidence; it is not a new image acquisition or generation study.

- Completed 180 generated-condition × reference-painter × family distance cells, 36
  target/control/specificity summaries, 372 coordinate diagnostics, and 48 reference distances.
- All existing outputs and the 649 measured confirmation paintings retain their original feature
  values and frozen development-only scaler. Every original endpoint and coordinate diagnostic
  agrees with recomputation before report publication.
- Sample-count sensitivity retains all 25 SD-Turbo blocks and the two single GPT blocks, with
  16 templates per condition: 324 block comparisons. Observed min–max ranges are descriptive,
  not confidence intervals, and do not match model identity or image geometry.
- Delivered nine comparison plots in PNG/SVG, six full-precision CSV exports, JSON results,
  Markdown report, and consumed-input/implementation/output hash provenance. No raw image was
  read, no feature was extracted, no provider was contacted, and no study access ledger changed.
- Commands: `latent-art-bench feature-distances build` creates a new output directory;
  `latent-art-bench feature-distances check` validates and reproduces the existing bundle.
  See the [analysis guide](FEATURE_DISTANCE_ANALYSIS.md) for locked-environment commands.
- Validation after implementation: Ruff passed; **357 offline tests passed** (23 new distance
  cases); v1 evidence audit passed with its two existing acknowledgements unchanged; v2 audit
  passed 15,809 checks with zero failures. All 26 derived report files reproduce byte-for-byte.
  The original English report hash is unchanged. Code review was a maintainer-run LLM subagent
  review, not institutionally independent.

The analysis reports observed feature distances. It makes no overall model-ranking or equivalence
claim. Manuscript drafting remains deferred; all source-study stages remain terminal.

## Sealed source study: Painter Feature Generation v2

The **empirical painter-feature analysis is complete**. Read the
[final analysis report](../reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS.md), covering
2,000 SD-Turbo images, 160 GPT Image service outputs, 649 confirmation works and full paired crop
sensitivity. No manuscript was drafted, as requested. The prospective extension is
[amendment 1.2](../studies/painter_feature_generation_v2/PROTOCOL_1.2.md). See also the earlier
[completed model-access analysis](../reports/painter_feature_generation_v2/AVAILABLE_IMAGE_MODELS.md).
**Painter Feature Generation v2** is the sealed source implementation;
[its protocol](../studies/painter_feature_generation_v2/PROTOCOL.md) preserves the original research
question and the v1 evidence while enabling a complete comparative analysis without asserting
uncalibrated equivalence. V1's strict reproduction claim remains unestablished.

Current v2 state:

- 1,193 recorded work identities retained; no additional works acquired from new metadata routes.
- Roles assigned prospectively within painter. Confirmation: Monet 303, Sisley 107, Pissarro 142,
  Cézanne 106 (658 total). Historical exposure matching restricts 91 records to development;
  incomplete exposure identifiers remain an explicit limitation.
- The 31-coordinate feature implementation, paired-block energy estimator, and immutable-stage
  artifact code exist and have focused offline tests.
- SD-Turbo revision `b261bac6fd2cf515557d5d0707481eafa0485ec2` is downloaded under the ignored v2
  workspace. Its prospective configuration is 512×512, one step, 25 blocks × 16 prompts × five
  conditions (2,000 attempts), executed locally with no paid API spending.
- The registered SD-Turbo run completed all 2,000 requests with 2,000 generated images and no
  failures. Its terminal receipt, ledger, measured features and analysis are retained unchanged.
- Original-image acquisition is terminal-aborted under its 64 MiB resource contract: 41 terminal
  dispositions, 33 acquired and eight failed. Retain every byte and the terminal receipt; never
  resume this run in place or splice its successes into the replacement.
- Acquisition amendment 1.1 registered renderings for all 1,193 works using 191 successful metadata
  requests. Its first image collector is now terminal: 272 dispositions, 78 acquired / 194 failed,
  and one interrupted request. It incorrectly assumed the old thumbnail host and exact reported
  thumbnail dimensions. All evidence is retained, and none is spliced into the successor.
- [Acquisition correction 1.3](../studies/painter_feature_generation_v2/PROTOCOL_1.3.md) recognizes
  Wikimedia's documented `thumb.wikimedia.org` migration and larger standard-size thumbnails.
  The complete disjoint `pfg2-renderings-r2-20260905` acquisition is terminal: 1,185 acquired,
  six below the fixed 1,024-pixel floor and two unsupported formats. Acquired roles: 221 new
  development, 91 historical development, 220 qualification and 653 confirmation.
- Shared method `pfg2-method-20260905` was frozen at 02:29 UTC, bound to clean committed code,
  protocols, calibration and both generation freezes. Development completed 312/312 measurements;
  the scaler uses 221 new-development works and all 31 coordinates have valid IQRs. Qualification
  completed 219 measured / one unprofiled non-RGB failure. Both stages and the scaler are sealed.
- The current Codex credentials work. The old port-10531 proxy predates its source update and
  returns an expired-token error. A separate current-source instance on port 10532 authenticated
  and completed the two-request access experiment without restarting the original server.
- Both GPT Image aliases returned valid PNG bytes, but **1254×1254 / reported quality low**, despite
  requesting 1024×1024 / medium. Neither response identifies a model snapshot. The sealed access
  receipt retains `invalid_output`; a separate offline diagnosis records two decodable images and
  zero contract-compliant images. This is access evidence, not an artistic-quality comparison.
- The 160-request OAuth pilot `pfg2-oauth-pilot-20260905` is terminal: 160 generated / no failures,
  both aliases, all 16 templates and five conditions, one repetition, no seeds or rerolls. All
  responses report quality low with no model snapshot; sizes vary, mostly around 1400×1120,
  rather than the requested 1024-square / medium. Its service-level comparisons are descriptive.
- Confirmation was opened once at the recorded receipt, after both generation grids and all
  prerequisites were committed. Its terminal reference contains 649 measured works: Monet 297,
  Sisley 106, Pissarro 141, Cézanne 105. Three unprofiled non-RGB images and one nonopaque-alpha
  image failed normalization; all are retained. All 2,160 generated images measured successfully.
- Primary numeric results are complete and sealed: the 60-endpoint repeated SD-Turbo analysis,
  finite comparisons for all three service conditions, 124 coordinate diagnostics per condition,
  source/profile/resolution strata and copy screens. Painter-name control improvement and
  wrong-painter specificity are distinct and mixed; no reproduction or model-ranking claim is made.
- Full paired crop sensitivity completed all 3,340 images in each 496-pixel branch, with no
  measurement failures or invalid scaler coordinates. None of the 36 named-minus-control signs
  reversed between the uncropped and cropped branches. This does not validate independent captures.
- The Markdown report and its hash-bound receipt are complete. Shared measurement, finite
  comparisons, repeated-block analysis and robustness are implemented, tested and executed.
  No active result was used to retune the frozen analysis. No manuscript was produced.
- The prespecified synthetic calibration completed 100 trials in each of three scenarios.
  Joint nondegenerate-endpoint coverage was 1.00 / 0.86 / 0.96 (null / shift / dispersion),
  with 48 zero-variance null contrasts lacking intervals. Nominal 95% intervals are therefore
  reported as exploratory, not validated confidence guarantees. No active-outcome retuning.

Canonical frame: `data/manifests/painter_feature_generation_v2/pfg2-frame-20260905/`.
CLI: `uv run --locked --extra analysis --extra learned latent-art-bench paper-study -- --help`.
Access CLI: `latent-art-bench model-assessment --help`; v2 audit: `latent-art-bench paper-study audit`.

Latest complete-suite validation: Ruff passed; 334 offline tests passed; v1 audit 2,902 checks
and v2 audit 15,809 checks, both with zero unacknowledged failures. All study collection and
measurement stages are terminal. The report reproduces byte-for-byte from sealed results and
all six local report links resolve. The two historical v1 acknowledgements remain unchanged.

Large runtime bytes remain under `research_workspace/painter_feature_generation_v2/`. Preserve all
v1 evidence and its ignored raw responses. V2 outputs have disjoint paths; none repairs or replaces
a terminal v1 census. Reviews performed by the operator or an LLM are not institutionally
independent reviews.

## Historical v1 status (retained context; superseded as current operational guidance)

Operational date: 2026-09-04

This page is mutable operational state. Frozen historical protocols, ledgers, and receipts remain
authoritative for their own completed actions.

## Active research question

The active study is **Painter Feature Generation v1**:

> For one exact model and one pre-label outdoor-place prompt census, do painter-name outputs
> reproduce the distribution of color, spatial/orientation, and digital-texture features in
> authority-record-exactly-attributed, metadata-declared outdoor-place paintings by Monet, Sisley,
> Pissarro, and Cézanne?

The canonical plan is 2.1 as amended by 2.2 and
[2.3](../studies/painter_feature_generation_v1/PROTOCOL_2.3.md). **2.2 replaces the R0 collection
rules; 2.3 makes Wikidata the authority layer and renames the construct. Every other section of 2.1
stands.**

Protocol 2.3 records the maintainer's decision of 2026-09-04 to accept Wikidata's own statements as
authority. The collection-identity census that day found the 3,543 discovered items spread across
**449 institutions**, with the ten largest covering 28.7% of item-collection links and the fifty
largest 56.1%. Reaching institutional catalogue records at that spread would take roughly fifty
museum routes. The construct is therefore now **Wikidata-declared outdoor-place digital-surrogate
feature reproduction**, and no report may describe the corpus as authority-verified.

**The R1 determination was carried out on 2026-09-04** and is the study's first recorded corpus.
Applying 2.3 Sections 2 and 3 with 2.1 Sections 7.3 and 7.4 to the recorded census admitted
**1,193 physical works**: Monet 538, Sisley 196, Pissarro 259, Cézanne 200, against a floor of 179.
All four clear it. **Sisley clears by seventeen works**, which makes him the binding constraint on
every subsequent decision; no later rule may be adopted without checking his count first. The
determination downloaded nothing and assigned no role.

- receipt: `data/manifests/painter_feature_generation_v1/pfg_v1_r1_20260904_determination_receipt.json`
- determination: `data/manifests/painter_feature_generation_v1/pfg_v1_r1_20260904_determination.jsonl` (3,543 rows)
- Korean summary: [R1 판정](../reports/painter_feature_generation_v1/R1_DETERMINATION_KO.md)
- judge: `src/latent_art_bench/painter_feature_generation_v1/determine.py`

The counts in Protocol 2.3 Section 6 (Monet 521, Sisley 187, Pissarro 252, Cézanne 197) came from
an exploratory script written while drafting that version; an erratum in Section 6 records the
supersession. The determination receipt is the authority.

Protocol 2.0 (`PROTOCOL.md`) and 2.1 (`PROTOCOL_2.1.md`) stay at their paths as the
frozen authority for the censuses executed under them; neither is edited.

Protocol 2.2 was issued on 2026-09-04 after the Cleveland census showed the cost of judging at
collection time. It reduces R0 to four principles: write the request down first, keep everything,
do not judge at collection, and keep the source list closed. The freeze of every input file, the
neutral review, the authorization seal, the one-shot lock, the hash-chained ledger, and
termination of the whole census on any anomaly are no longer required at R0. They remain required
from R1 onward, and the hash-chained ledger is retained at G1 where dropping an unfavourable
attempt is a real temptation.

The claim is deliberately finite and technical: metadata-declared outdoor-place digital-surrogate
feature reproduction in the closed accessible frame. It is not painter classification, authorship,
content-free style, physical brushwork, artistic intention, or a probability-sampled oeuvre claim.

## Current stage

The study completed R0 metadata collection and the **R1 metadata determination**, and remains
**NO-GO for image acquisition** until the Protocol 2.2 Section 4 freeze and authorization seal are
issued. Zero images have been downloaded, zero roles assigned, zero generation attempts made, and
zero results produced.

The next authorized action is **role assignment under 2.1 Section 8.1**: apply
`SHA256("pfg-v1/2.1-role" ‖ physical_work_id)` to the 1,193 admitted works to split development,
qualification, and sealed confirmation, and pin the 122-work exposure denylist to development only.
That step needs no image either. Image acquisition follows, and the freeze and seal fall due before
its first byte.

Two facts from the determination bind later work:

- **geometry is the largest single loss (784 works).** Commons scan resolution, not authority or
  content, sets the corpus size. The 1,024 px floor is 2.1 Section 7.3 and is not to be lowered to
  buy works.
- **the admitted content mix differs sharply by painter.** 64% of Monet's admitted works are
  water-organized against 22% of Pissarro's. Section 13.4's specificity contrast must report this,
  because part of any cross-painter feature difference is subject matter rather than style.

**Protocol 2.1 was issued on 2026-09-04.** The decision it records: the study runs without
coders or an adjudicator. Every human coding step is removed and content eligibility is declared
by a frozen metadata lexicon (§7.4); scene-group stratification is gone and the real target is
uniform over works; all 16 prompt templates are always rendered; adherence is an automated
diagnostic; copy adjudication is a deterministic two-threshold rule; and one operator may hold the
custodian, method-analyst, and generation-operator roles sequentially under technical sealing with
an access ledger, a limitation every report must disclose. Section 0 of the protocol lists every
change.

The decision followed a non-binding pre-screen
([Korean summary](../reports/painter_feature_generation_v1/SCENE_SUPPORT_PRESCREEN_KO.md),
[evidence](../reports/painter_feature_generation_v1/evidence/scene_support_prescreen.json)) that
applied the corpus arithmetic to the completed R0 manifests. Under Protocol 2.0 the four-way scene
cells needed 57 newly eligible works each and no scene cleared that floor for all four painters at
the metadata upper bound. Under Protocol 2.1 each painter needs 179 newly eligible works (100
confirmation at uniform weights, 10 development, 10 qualification, 12 auxiliary). The lexicon
upper bound of eligible items that carry a collection QID is Monet 529, Sisley 193, Pissarro 256,
and Cézanne 200, so all four clear the floor at the upper bound and Sisley is the binding risk:
authority verification, deduplication, complete-view checks, and private-collection exclusion can
only lower these counts, and NO-GO after R2 remains possible.

That pre-screen has since been superseded by the R1 determination above, and one of its claims did
not hold: it called its counts an upper bound, but the determination admitted 538 Monets against
the pre-screen's 529. The pre-screen read one row per item, so it missed works whose only
sufficiently large Commons file sat on a second row. A figure is an upper bound only for the exact
rule that produced it.

Completed in the Protocol 2.0 redesign:

- corrected the estimand to generated-versus-real painter feature distributions;
- retired the unsupported equal 360-work quota, three-way active-real split, 24-template selection,
  and high-dimensional entropy weighting;
- fixed an exhaustive named source union and physical-work/capture identity graph;
- defined actual unequal painter populations with equal mass across every commonly supported broad
  scene group and all eligible works retained within group;
- defined screening floors of at least three common groups, at least 20 physical works per retained
  group, equal-scene ESS at least 100, crossed source workflows, and a 60-work independent-capture
  auxiliary panel, with whole-decision simulation still binding;
- restricted historically exposed works to development and fixed a prospective 20%/20%/60%
  development/qualification/confirmation assignment for every new eligible work;
- fixed all 16 candidate prompt strings and the render-independent contract before active visual
  labels; unsupported groups can only be removed by the deterministic count rule;
- specified three required feature families—color, spatial/orientation, and digital texture—with
  common normalization and no learned feature as primary;
- required all three families to qualify; no favourable family subset can produce the painter label;
- specified energy-distance estimation, margins, specificity, artist-free control improvement,
  coordinate coverage, per-scene coverage, source/work influence, simulation, and simultaneous
  inference;
- kept every off-topic generated output in its assigned primary cell; adherent-only analysis is a
  sensitivity, not a selection rule;
- required a complete technically analyzable generated grid and zero confirmed searched-corpus
  real-work copies for a positive claim; generated duplicates remain with full multiplicity; and
- defined role-separated acquisition, blind coding, method, generation, and confirmation access.

The first authorized fixed-seed audit was executed on 2026-09-02 and terminated exactly as
specified. Four Wikidata batches succeeded. The fifth returned HTTP 200 but exposed a valid
MediaWiki `languagefallback` term representation that the frozen parser did not support, producing
`terminal_stage_schema_failure`. Its 11-event hash-chained ledger and five response bodies are
preserved; no result manifest or execution receipt was issued, and none of its successes will be
spliced into the retry.

The complete, newly authorized R2 retry then repeated that follow-up under a new census ID:

- a metadata-only follow-up of 3,190 Wikidata items and 3,364 Commons filenames across 165 exact
  GET intents (80 Wikidata entity batches and 85 Commons file batches);
- a fail-closed collector with a corrected fallback-term parser and focused regression tests, which
  validates current P18 linkage, rights markers, reported geometry, exact member coverage,
  origin/redirect behaviour, retries, atomic receipts, and non-admission manifests;
- separate output paths and explicit hash-bound linkage to the terminal first census;
- maintainer-run LLM subagent review with no blocking finding (not institutional independence); and
- all 165 requests completed on first attempt, producing 331 hash-chained events, 165
  content-addressed raw responses (about 51 MiB locally), and a 3,367-row non-admission candidate
  manifest with its execution receipt.

The first prospective broad no-`P186` census (`pfg-v1-broad-wikidata-no-p186-20260902`) was
approved after maintainer-run LLM subagent review and executed on 2026-09-02. Monet completed with
1,317 discovery-only rows.
The next, Sisley, request returned provider HTTP 502 with `text/html`; the census therefore ended
terminally after five hash-chained events. Its one-shot lock and both raw responses are preserved,
and it emitted neither a candidate manifest nor an execution receipt. No R1 row is reusable.

The R2 census, reviewed by a maintainer-run LLM subagent, repeated the same four queries and parser, scope,
cutoff, and all-or-none terminal rule under a new census ID and disjoint paths. Its only operational
change was a five-second rather than two-second minimum request interval. The retry gate binds the
exact R1 config, freeze, review, authorization, terminal ledger/event, one-shot lock, both raw
responses, absent candidate/receipt, and exact allowed config delta. Neutral quality review found
and closed two execution-boundary file-binding defects before approval. R2 then completed all four
requests on first attempt and emitted 3,722 discovery-only item-image rows: 3,543 distinct Wikidata
item IDs and 3,718 distinct Commons filenames. No image was downloaded and no work was admitted.

The separately reviewed broad-media follow-up R1 then froze 182 exact metadata-only requests
covering all 3,543 item IDs and 3,718 filenames. Neutral review identified and closed deterministic
ordering, single-read CAS, terminalization, retry-ledger, cutoff/resume, path-confinement, and
atomic-publication defects before approval. Its first Wikidata response was HTTP 200 with
`Retry-After: 5`, but the body was a plural MediaWiki `errors` envelope containing `maxlag`, not a
parser-complete success. Because R1 did not recognize that error representation, it terminated
fail-closed after one request. Its three-event ledger and raw response remain frozen; no partial
manifest or receipt was issued or reused.

Broad-media R2 was then prospectively frozen under a new census ID and disjoint workspace. Its
only semantic change was strict recognition of a nonempty top-level plural `errors` array whose
entries carry one unambiguous nonblank error code; existing retry classifications and ceilings were
unchanged. The freeze bound 28 inputs, the complete R1 CAS/lock/event lineage, 182 deterministic
intents, and six absent pre-execution outputs. Maintainer-run LLM subagent review approved the exact
freeze with no blocker. R2 completed all 182 requests on their first R2 attempt: 89 Wikidata entity
batches and 93 Commons media batches, 365 hash-chained events, 182 content-addressed raw responses
(55,899,277 bytes locally), and a 3,722-row non-admission manifest. Of those rows, 2,029 pass the
federated metadata discovery gate, representing 1,967 distinct item IDs; none is yet an
authority-verified physical work, downloaded image, or active-study admission.

The first Art Institute of Chicago route census (`pfg-v1-aic-metadata-20260902`) received
maintainer-run LLM subagent review and was authorized and executed on 2026-09-02. Its first
request returned HTTP 200 with a
schema-valid body, but AIC returns `classification_id` as a nonblank string identifier such as
`TM-66` while the frozen parser required an integer. The census therefore terminated fail-closed
after one request with `terminal_delivery_or_schema_failure`. Its three-event hash-chained ledger,
one-shot lock, and single 129,424-byte raw response are preserved; it issued neither a candidate
manifest nor an execution receipt, and none of its rows was reused.

AIC R2 (`pfg-v1-aic-metadata-r2-20260902`) was then frozen under a new census ID with disjoint
manifest, publication, workspace, and CAS paths. Its only semantic change is that `classification_id`
is an optional nonblank string identifier; every source, query, transport, screening, retention, and
publication rule is unchanged. The freeze binds 25 inputs, six absent pre-execution outputs, and the
complete R1 config/freeze/review/authorization/intent/ledger/lock/CAS lineage together with the
exact allowed config delta. Maintainer-run LLM subagent review verified every frozen hash and
absence, reconstructed the four intents identically under five hash seeds, replayed the exact R1
terminal body — the R1 parser still fails with the recorded error while the R2 parser returns 46
rows — and passed a production-gate mock over the exact committed seal. It approved with no blocking
finding.

R2 then completed all four exact artist-ID requests on their first attempt on 2026-09-03: 9
hash-chained events, four content-addressed raw responses (308,569 bytes locally), and a 153-row
non-admission candidate manifest. No R1 response body was reused. Of those rows, 57 pass both the
AIC authority-record screen and the metadata/media screen, across 57 distinct accession numbers:
Monet 33 of 46 rows, Sisley 6 of 8, Pissarro 9 of 65, and Cézanne 9 of 34. The Pissarro and Cézanne
row counts are dominated by prints and works on paper, which the painting and oil-on-canvas screens
reject. No image endpoint was requested, no work was admitted, and the AIC rows are not yet
reconciled against the Wikidata/Commons census.

Still not completed:

- neutral review and freeze of the prompt library, content lexicon, and exposure denylist;
- an Europeana API key and a Paris Musées API token — both are absent from the repository and the
  environment, so those two routes will be recorded `not_executed_missing_authorized_credential`
  unless credentials are obtained before their freezes;
- the remaining terminal source routes named in Protocol 2.1 — Europeana, NGA, Cleveland, Yale,
  Getty, Minneapolis, Paris Musées, and POP/Joconde;
- authority, rights, physical-work, capture-family, and image-quality reconciliation;
- active image acquisition;
- the R2 metadata eligibility run, source crossing, and corpus closure;
- the frozen new-work role manifest and the 60-work capture panel;
- feature implementation/fixtures/qualification, margins, or simulation results;
- model/prompt/seed G0 freeze;
- generation; or
- confirmation and generated-versus-real results.

## R0 artifacts added 2026-09-04

| Artifact | Path | State |
|---|---|---|
| §11.1 prompt library | `data/manifests/painter_feature_generation_v1/prompt_library.json` | rendered from `PROTOCOL_2.1.md` by `latent-art-bench prompt-library`; 16 artist-free + 64 named strings; `strings_sha256` `c0d305dd…`; not yet neutrally reviewed or sealed |
| §7.4 content lexicon | `data/manifests/painter_feature_generation_v1/content_lexicon.json` | rendered by `latent-art-bench content-lexicon`; 5 override phrases, 106 exclusion tokens, 281 positive tokens; must be reviewed and frozen before R2 |
| §8 exposure denylist | `data/manifests/painter_feature_generation_v1/exposure_denylist.jsonl` + `exposure_denylist_receipt.json` | rebuilt by `latent-art-bench exposure-denylist` from eight pinned git blobs; 122 pixel-exposed physical works are development-only (AIC 40, NGA 45, Met 27, CMA 10); 39 pilot-3 metadata-only selections carry no restriction; 5 works lack a resolved painter; not yet frozen for M0 |
| corpus-adequacy pre-screen | `reports/painter_feature_generation_v1/evidence/scene_support_prescreen.json` + `SCENE_SUPPORT_PRESCREEN_KO.md` | non-binding lexicon proxy against the 2.1 floors, with the retired 2.0 scene-cell arithmetic kept for the record; regenerate with `latent-art-bench scene-prescreen` |
| commit-bound evidence audit | `latent-art-bench verify-evidence` | 9 freezes, 8 ledgers, 4 receipts verify; 2 acknowledged unrecoverable inputs |
| review fixes (PR #3) | `panel.py`, `artifact_cli.py`, and fixes across the new modules | the acknowledgement file now excuses only the exact bound hash it names; receipts cross-check their ledger and fall back to git history; the content lexicon folds typographic apostrophes; `--check` covers the denylist receipt; the pre-screen refuses to run without its inputs |
| shared census engine + Cleveland route | `census_engine.py`, `cleveland_metadata.py` | executed 2026-09-04 under Protocol 2.1; retained as evidence, superseded for new routes |
| Protocol 2.2 collector | `collect.py`, `latent-art-bench collect` | one module for every JSON route, 304 lines, no per-route parser, no collection-time verdict |
| Getty route contract | `configs/painter_feature_generation_v1/getty_collection.json` | written and offline-validated; not executed. The recorded exploratory query's object-type and material filters are deliberately removed |

The denylist already intersects the AIC R2 screened candidates: 17 of Monet's 33, all 6 of
Sisley's, 6 of Pissarro's 9, and 5 of Cézanne's 9 were pixel-exposed in the pilots and can only be
development works.

## Review provenance and staffing

Every neutral independent review under `data/manifests/painter_feature_generation_v1/*review*.json`
was produced by a large-language-model review subagent (recorded, for example, as
`Mencius (independent neutral quality review subagent)`) run by the single maintainer of this
repository. The reviews are procedurally separate from the freeze author and did find and close
real defects, but they are not institutionally independent, and every report must say so. Reviews
produced on the shared census engine must state `reviewer_kind` (`human` or `llm_subagent`).

Protocol 2.1 §8.2 has no coder or adjudicator role. The repository has one maintainer, who may
hold the acquisition-custodian, method-analyst, and generation-operator roles sequentially only
under technical sealing: confirmation-resolution bytes go into a sealed store whose manifest is
committed before M0, every read of a sealed path is ledgered, and any ledgered read before the C0
opening voids the affected confirmation claim. This cannot exclude covert access and is a stated
limitation of the study.

## Active counts

| Quantity | Count | Meaning |
|---|---:|---|
| exploratory Wikidata item candidates | 3,190 | material-constrained discovery identifiers, not verified works |
| distinct Commons filenames in that seed | 3,364 | file identifiers, not physical works |
| fixed-seed R1 completed requests | 4 / 165 | verified successes before the fifth request terminated R1 |
| fixed-seed R1 terminal requests | 1 | valid provider representation unsupported by the frozen parser |
| fixed-seed R2 completed requests | 165 / 165 | all first-attempt successes; no R1 success reused |
| fixed-seed R2 metadata-qualified rows | 2,029 / 3,367 | discovery gate only; not physical works |
| fixed-seed R2 distinct qualified item IDs | 1,967 | not identity-reconciled physical works |
| fixed-seed R2 distinct qualified filenames | 2,028 | files, not independent works or captures |
| broad no-P186 R1 successful requests | 1 / 4 | Monet response only; not reusable outside terminal R1 evidence |
| broad no-P186 R1 terminal requests | 1 | Sisley HTTP 502; whole R1 census incomplete |
| broad no-P186 R1 observed rows | 1,317 | discovery-only Monet rows inside an incomplete census; no manifest issued |
| broad no-P186 R2 requests | 4 / 4 | all first-attempt successes; R1 success was not reused |
| broad no-P186 R2 discovery rows | 3,722 | exact-creator painting+image rows; not physical works |
| broad no-P186 R2 distinct item IDs | 3,543 | current Wikidata identifiers before authority/identity reconciliation |
| broad no-P186 R2 distinct filenames | 3,718 | Commons filenames; not independent works or captures |
| broad-media R1 attempted requests | 1 / 182 | terminal plural `errors:[maxlag]` representation; no result publication |
| broad-media R2 completed requests | 182 / 182 | 89 entity + 93 media batches; all first-R2-attempt successes |
| broad-media R2 candidate rows | 3,722 | current entity/media metadata rows; not physical works |
| broad-media R2 metadata-qualified rows | 2,029 | discovery gate only; 1,967 distinct item IDs |
| broad-media R2 raw responses/events | 182 / 365 | content-addressed responses / hash-chained events |
| AIC R1 attempted requests | 1 / 4 | terminal string `classification_id`; no result publication |
| AIC R2 completed requests | 4 / 4 | one exact request per frozen AIC agent ID; all first-R2-attempt successes |
| AIC R2 candidate rows | 153 | returned holding records; not physical works |
| AIC R2 screened candidates | 57 | painting + oil/canvas + accession + public-domain flag + image ID + short side ≥ 1,024 |
| AIC R2 raw responses/events | 4 / 9 | content-addressed responses / hash-chained events |
| separately observed official-source all-content candidates | 43 | traceable live records, not a terminal source census |
| admitted active physical works | 0 | none has passed every gate |
| downloaded active-study image files | 0 | metadata collection cannot download images |
| sealed confirmation works | 0 | frame not closed |
| registered generation attempts | 0 | G0 closed |
| generated outputs | 0 | G1 closed |
| generated-versus-real results | 0 | no empirical painter claim authorized |

The earlier 40-file Commons follow-up ended with HTTP 429 and remains superseded evidence. The R2
fixed-seed result establishes current metadata attrition only. It does not establish a reusable-file
corpus, authority-verified work count, complete source frame, or outdoor-place content yield.

## Data and source policy

Protocol 2.1 keeps the Protocol 2.0 candidate union unchanged:

1. the broader exact-creator Wikidata/Commons painting+image census without material filtering;
2. Europeana exact creator;
3. AIC, NGA, Cleveland, Yale, Getty, Minneapolis, and Paris Musées APIs/exports;
4. POP/Joconde; and
5. the material-constrained fixed seed for current attrition/reconciliation only.

Discovery records locate candidates. Authority records establish work identity, exact attribution,
object type, medium/support, and accession. Media/capture records establish lawful reuse, geometry,
and delivery. These layers can describe the same work and are never added as independent counts.

Every source must reach its frozen terminal condition. Reaching a capacity number is not a stop
rule. A source is not replaced or topped up after results. One physical work contributes once;
mirrors, crops, filenames, encodings, or hashes do not increase the work count. Only provenance-
demonstrated distinct capture events enter the auxiliary capture panel.

The active source mixture must be crossed with painter: every painter requires at least two
authority/capture workflows, the incidence graph must be connected, and no workflow may carry more
than 0.80 of a painter's equal-scene weight. Otherwise painter and source are inseparable and no
painter-reproduction label is allowed.

## Required next sequence

0. Done 2026-09-04: Protocol 2.1 issued; the prompt library, content lexicon, and exposure
   denylist rendered. Their neutral review and freeze remain.
1. Preserve and report the completed fixed-seed, broad no-`P186`, broad-media, and AIC censuses
   without calling any of them a complete source frame or an acquired image corpus.
2. Freeze and execute the remaining named source routes to their terminal conditions, then
   reconcile the whole union to physical works.
3. Under a separate R1 authorization, verify authority/rights/capture identity and acquire lawful
   technically adequate image bytes.
4. Run the R2 metadata eligibility rule with the frozen lexicon, reserve the auxiliary panel, apply
   the denylist, assign roles by the hash rule, and close the unequal finite frame; generation
   remains NO-GO until every corpus adequacy gate passes.
5. Run M0a/M0b, auxiliary capture qualification, margins, copy calibration, and whole-decision
   simulation. All three families must pass.
6. Freeze one exact model, the 16 prompts, render settings, seeds, `R`, request order, the
   adherence classifier, and analysis at G0; then generate and seal G1 while confirmation features
   remain inaccessible.
7. Open the confirmation reference once at C0 and execute the frozen decision.

## Terminal evidence boundary

Three R1 censuses reached a terminal condition and stay terminal: the broad no-`P186` discovery
census on a provider HTTP 502, the broad-media follow-up on an unrecognized plural
`errors:[maxlag]` envelope, and the Art Institute route on a string `classification_id`. Each
retains its config, module, tests, ledger, and raw response, and each is bound both by the freeze
that authorized it and by the successor freeze that records its terminal evidence.

These outcomes are evidence. Do not repair them with new data, retry them in place, splice their
responses into a successor, or refresh their hashes.

## Explicitly closed actions

Under the historical v1 procedure, until the corresponding Protocol 2.1 freeze is reviewed
(past reviews were maintainer-run LLM subagents, not institutional independence), do not:

- retry, replace, or splice any terminal R1 census;
- treat metadata rows or files as an active painter distribution;
- download active-study images under the metadata-only census;
- read any sealed confirmation path before the C0 opening receipt;
- tune prompts, features, thresholds, margins, or source rules on generated/confirmation outcomes;
- send generation requests; or
- rewrite or move frozen evidence.

## Repository health boundary

The standard offline checks are:

```bash
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
```

Evidence verification is commit-bound:

```bash
uv run --locked latent-art-bench verify-evidence
```

The audit resolves each freeze to the git commit that recorded it (a declared
`recorded_git_commit`, or the commit that introduced the freeze blob), verifies every bound input
against the bytes at that commit, verifies untracked research bytes in the working tree, and checks
every event ledger's hash chain and every execution receipt's ledger, manifest, and content-
addressed responses. Hashes are never refreshed. Later edits to `pyproject.toml`, `uv.lock`, or a
shared module therefore no longer invalidate earlier freezes; they are reported only as informational
working-tree drift.

Exactly two bound inputs can never re-verify. The fixed-seed R1 freeze bound the pre-repair
`federated_census.py` and its test module, and the R2 retry replaced those bytes before the first
commit that contains either freeze, so no commit holds them. They are recorded in
`data/manifests/painter_feature_generation_v1/evidence_acknowledgements.json` with the cause and the
remaining evidence, and `tests/test_evidence.py` asserts that these are the only failures. Do not add
to that file to hide a new mismatch. New freezes must record `recorded_git_commit` and be prepared
from a tree whose bound inputs are clean against that commit.
