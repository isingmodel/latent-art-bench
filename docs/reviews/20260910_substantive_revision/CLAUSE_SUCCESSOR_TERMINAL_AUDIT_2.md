# Clause successor terminal and measurement audit

Date: 2026-09-10. Run: `painter_clause_successor_v1/pcsv1-20260910`.
Reviewer 2 is a maintainer-run LLM agent who implemented both clause collectors
and workflows, their transport tests, and earlier geometry/centering components.
This is a separately performed audit by an involved implementer, not an
independent human or institutional review. No score is assigned or changed;
the earlier precollection reviews remain immutable snapshots.

**Conclusion:** the actual terminal ledger, complete allocation, source and
predecessor lineage, identity/duration gates, accounting, all 96 retained response
hashes, all 288 measurement rows, delivery counts and receipt bindings pass.
The unchanged numerical/report replay also passes. No frozen source or evidence change,
new request, image decoding or feature re-extraction was performed by this audit.

## Terminal allocation, timing and accounting

The successor is permanently **complete**: all 96 planned outputs returned on
their first attempt. There are no refusals, HTTP errors, uncertain outputs,
cancellations, unattempted slots, retries or unresolved intents. All 48 two-arm
scene/repetition blocks contain both newly generated outputs. Each of the 24
unchanged scenes appears twice in each arm, with eight scenes per content class;
each class/arm cell therefore contains 16 outputs.

I called the unchanged sealed `workflow.collection_inputs` and separately
verified the full ledger and slot records. All 192 event hashes and links are
valid, with exact sequence numbers, 96 durable intents and 96 corresponding
terminal records. Dispatch tickets and admitted slot sequences are exactly
0–95. Every intent's payload digest agrees with its frozen request. All
terminals record a complete HTTP 200 response, `paid=false`, zero cost and no
transport error. Every selected slot equals its first successful attempt's
response identity and observed metadata. The collection receipt contains the
exact four distinct expected output bindings, all of which verify; its final
operator event chain also verifies.

All **96 compressed-storage hashes and all 96 decompressed response-entity
hashes** agree with the terminal ledger. Entity sizes agree with both recorded
byte counts, remain below the response limit, and sum to 389,325,154 bytes. The
response directory contains exactly the 96 expected compressed files. These
checks hash retained response entities without decoding their embedded image
base64, loading images, inspecting pixels or recomputing features.

| Check | Verified result |
| --- | --- |
| Allocated outputs / ledger events | 96 / 192 |
| Intents / returned terminal records | 96 / 96 |
| Completed two-position blocks | 48 of 48 |
| Retry decisions, retry intents and posted retries | All zero |
| First recorded admission | 05:54:07.080740 UTC |
| Last recorded admission | 06:38:22.698691 UTC |
| Minimum recorded admission spacing | 5.000218459 seconds |
| Maximum overlapping admitted response intervals | 2 |
| Minimum next-block admission minus prior-block completion | 14.391762167 seconds |
| Last terminal event | 06:39:08.842436 UTC |
| Final source/proxy check | 06:39:23.306027 UTC |
| Terminal receipt end | 06:39:23.308075 UTC |
| Receipt monotonic elapsed duration | 2732.090957042 seconds (45.53 minutes) |
| Marker-to-receipt UTC difference | 2731.922732 seconds |
| New paid cost / new reserve / pending intents | $0 / $0 / none |
| Historical conservative accounting | $50.7219185 |
| OAuth subscription monetary valuation | None assigned |

Admission order and spacing were checked from the recorded monotonic starts.
Overlap and block drainage were checked using each recorded start plus its
returned latency; every block drained before the next was admitted. The marker
is `05:53:51.385343 UTC`. The receipt's monotonic timer controls the duration
gate and is comfortably below 24 hours; the UTC timestamps independently
establish event order. The two clock measurements are not asserted to be
identical or microsecond-accurate observations of backend timing.

These records establish the collector's admission and completion behavior, not
actual upstream arrival times, a stable remote checkpoint, independent service
states or absence of carryover. The audit made no account/balance request. The
independently derived OAuth-only namespace ledger budget equals the receipt.
The retained paid-study baseline remains $50.72191850000009, accepted under the
prequalified absolute machine-arithmetic tolerance of 1e-10 against the stated
$50.7219185; no historical cost or reserve was revised.

## Identity, source and predecessor lineage

All **167 freeze bindings** match the committed source and retained bytes.
The qualified scientific source is
`07f8231ab47ef51a26d68fcfd5a16acc12c0e293`; the freeze records qualification/source
commit `d5887f86dfe34fc3c0db775358797aca92a8fe1d`. The prepared freeze was committed
as `6effea1fc4a0f1139197453b7f31d6bdf1988d9c` at 05:53:13 UTC, before collection.
Configuration, runtime, qualification, full request inventory and exact
reference/scaler lineage all pass the unchanged verifier.

The final operator event follows the last terminal event and records literal
`source_verified=true` and `proxy_verified=true`. There are no identity-invalidating
terminal or operator events. The receipt's literal identity and duration flags
are therefore true under the frozen contract. A separate read-only local process
and source snapshot still equals the frozen proxy identity, whose source commit
is `0a664bcc8e09649fcdd558e0bfbdd6447b85bca2`. This check uses local source/process
metadata without an HTTP call or credential inspection. It does not attest the
upstream model, account or service checkpoint independently.

The predecessor's six bound terminal/source files and its transitively bound
collection marker verify. The original error-only HTTP 400 moderation refusal
at `c:pcv_built04:r00:cezanne` is unchanged and authenticated. The successor's
stored predecessor fingerprint exactly matches the verified stopped original
receipt, freeze and source commit, with `cezanne_primary_complete=false` and
`numerical_outcomes_accessed=false` in the frozen decision record.

I independently checked the new input as the exact Cezanne-only JSON projection
of the original input: origin path/hash, target masses, all three 32-reference
cells and the complete retained scaler objects agree. All 96 request IDs are
disjoint from the original. Corresponding scene/repetition/clause payloads are
byte-equivalent as serialized request objects, and the previously refused scene
is retained. No original response or measurement enters a successor generated
arm.

The design commit `f0ab2d4` is recorded at 05:36:13 UTC, and the committed freeze
precedes the original study's one-shot measurement marker at 05:54:04.884933 UTC.
This verifies the recorded design/freeze-before-measurement chronology; it is
not independent evidence about unrecorded actions. Both original primary
comparisons remain unavailable in the original terminal result. This new
complete cohort neither fills an original slot nor restores its free-arm maps,
Monet endpoint or original inferential family.

## Measurement inventory and delivery

Measurement began at **06:41:09.603768 UTC**, after the successor's terminal
receipt. All **288 rows** are present in exact frozen request/pipeline order:
96 measured rows in each of `primary512`, `resolution256` and `jpeg90_512`.
They represent 96 physical outputs, not 288 independently generated images.
There are no additional measurement failures, missing rows or discarded outputs.

For every row, I independently verified all request identity fields, image ID,
selected attempt, terminal response path/hash and observed metadata. Each stored
encoded-image hash agrees with its terminal delivery hash. All raw and scaled
vectors contain 31 finite values, every canonical feature digest matches, and
each stored scaled vector equals `(raw - frozen_center) / frozen_scale`
elementwise for its pipeline. This checks the retained mapping without refitting
the scaler or recalculating features.

All normalization records preserve the delivered dimensions, use the specified
short side (512, 256 or 512), record zero cropping and have the expected rounded
resized dimensions. JPEG sensitivity records specify quality 90, subsampling 2,
nonprogressive encoding without optimization, with their retained encoding and
normalization hashes. I did not independently reproduce those pixel arrays.

I recomputed every recorded delivery dimension, format, status and quality count
from the primary-pipeline rows and matched the report exactly. Each output is
counted once:

| Arm | Allocated / measured outputs | PNG, nonsquare | Reported low | Reported medium |
| --- | ---: | ---: | ---: | ---: |
| Generic | 48 / 48 | 48 | 32 | 16 |
| Cezanne | 48 / 48 | 48 | 42 | 6 |
| Total | 96 / 96 | 96 | 74 | 22 |

All requests specified medium quality and 1024-by-1024 geometry. Valid delivered
differences remain in the service-response comparison without quality filtering
or adjustment. Reported quality is provider metadata, not a human judgment of
quality or painter-style fidelity.

## Receipt, replay and scientific scope

The measurement receipt has exactly four distinct expected bindings:
`measurements.jsonl`, `analysis.json`, `REPORT.md` and the one-shot measurement
marker. All hashes verify, and its collection-receipt hash matches the unchanged
complete terminal receipt. The analysis preserves that receipt and the exact
input origin.

The single Cezanne-minus-generic primary is structurally eligible with all 48
ordered pairs and contributions. Its stored estimate is
`-1.1954193528663188`, raw p-value `0.00001`, alpha `.025`, status `available`
and `reject=true`. The stored randomization record contains 99,999 draws.
There is no new Holm family or confidence interval. The three pipeline views
contain exactly the six allowed complete arm summaries and their observed-trace
ratios; no free-arm, map, conditional-variance, retrieval or extra endpoint
appears.

The unchanged `workflow.check(..., pixels=False)` passes with
`status="numbers_replayed"`: numerical JSON and Markdown match exactly.
Its `raw_response_access=false` flag denotes omission of optional pixel replay;
the normal terminal verifier still authenticates the predecessor's error-only
refusal entity. This audit performed no generated-image decoding or feature
re-extraction. Reviewer 1 separately owns direct energy/trace/contribution and
Monte Carlo arithmetic verification; the same-code replay here is not presented
as a second independent recalculation of those scientific statistics.

Eligibility and exact replay do not establish the sharp-null assumptions,
independent backend states, scene-population generalization or perceptual style
validity. The observed comparison includes the delivered geometry and reported
quality differences. No actual public release or anonymous replay is established
by this terminal audit, and no further replacement cohort is authorized by it.

## Bound evidence

Manifest filenames below are under
`data/manifests/painter_clause_successor_v1/pcsv1-20260910/`; report files are
under `reports/painter_clause_successor_v1/pcsv1-20260910/`; workspace markers
are under the corresponding ignored `research_workspace/` run directory.

| Artifact | SHA256 |
| --- | --- |
| `freeze.json` | `9698450d1e0f90a8182b2e80150a17dedfee4a71b901b269c18d1d244d9d2947` |
| `planned_requests.jsonl` | `bb0bfb40d30aa79bc9a56f1adeca96c0d9d6c7bf2ebd03041696717dd8dab25e` |
| `collection_receipt.json` | `06504656c0fcb927068a076f78fde35c261ea86bda37d8d9f9fec6c442b2fd75` |
| `generation_events.jsonl` | `e8c4c97c69e4c0495d8e078211ec2f966516924655d5da09167b640ef9cc22ed` |
| `slot_outcomes.jsonl` | `3cf414bf513b8665702d48eb8cd526dea3c467b32183e67b207b57f8ba22ba75` |
| `operator_events.jsonl` | `c3f7fad4543ae160ae4cd88f0ded04741bee7298da27ff7588b62749cb9e24ba` |
| Workspace `collection_started.json` | `baff14e3f35eb724482c1850d5ed672795358e62fdcc20364c1df43b99f71e38` |
| `measurement_receipt.json` | `6446d7f77877153f9ee40faaefc10e1c83a7f074d425630bab79e129e0c3069d` |
| `measurements.jsonl` | `32f30fea7fbcaa9862186cbd5b63ae18d439e0f6a519533ac1defaab4ad718c7` |
| Report `analysis.json` | `00ab620f5c3e67b6fcac16cc8e4456504a3001e7a82a2524b8c58fcacfe9deb8` |
| Report `REPORT.md` | `942d9ea11ae8f1a893b31b9ddcc7cea17fcf6689c02806e6a109a3e1148fd8dd` |
| Workspace `measurement_started.json` | `72749c352914c284cde13d8caac8f28dc0076e5f310f05b3b0c9e439b70b7a6e` |
| `studies/painter_clause_successor_v1/inputs.json` | `948680079fa8646dc0088808b6aced037d9050680bae63eb5086cf4acb2665cc` |

The predecessor collection receipt remains
`5df074e6c90df761385e61e5118d181244671bd3eebc263d4d9e900ac0e6fdd1`, and its
moderation-trigger entity remains
`5f383689fcebc2c43f5bb0fdef45dc1558f6e16726c2c4a39559de68ba4eb9b5`.
No original evidence or hash was refreshed.
