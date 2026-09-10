# Clause-v1 terminal transport audit

Date: 2026-09-10. Run: `painter_clause_validation_v1/pcvv1-20260910`.
Reviewer 2 is a maintainer-run LLM agent who implemented the clause-v1 and
successor collectors/workflows and earlier geometry/centering components.
This is a separate read-only terminal audit by an involved implementer, not an
independent human or institutional review. No score is assigned. Earlier source
reviews remain immutable snapshots of their precollection evidence.

## Terminal finding

The run is permanently **stopped**, with 211 returned images, one moderation
refusal, one complete HTTP error, one cancellation before posting and 74
unattempted slots. The global identity flag is false. Both original primary
endpoints are unavailable; this is no longer only a missing Cezanne comparison.
No retry, resumption, refill or retrospective error reclassification is permitted.

The stored HTTP 500 response at `c:pcv_water05:r00:cezanne` contains exactly one
`error` object, with `type="server_error"`, `param=null`, and `code=null`.
The message reports a server processing error and suggests retrying. It contains
no image/data field and is 369 bytes. The response was completely received; its
storage/entity hashes agree with the terminal ledger.

This indicates a backend-reported server failure. It does not identify its
internal cause, prove that it was transient or establish recovery. There is no
authentication, quota or rate-limit indication in the retained response. The
collector stopped because the frozen JSON retry rule requires an integer error
code equal to the qualifying HTTP status. A null code does not meet that rule.
Thus `recognized_technical_error=false` and `unrecognized_backend_error` are
correct dispositions under the frozen contract. The response's retry suggestion
does not authorize an exception. No collector-source fix is warranted by these
bytes, and the same response remains nonretryable in the fixed successor.

## Verified accounting and timing

The unchanged sealed `workflow.collection_inputs` passes. I also recomputed
counts, admission order, timing intervals, per-arm availability and accounting
from the request/slot/attempt records. All four receipt output bindings and both
append-only event chains verify. All 213 stored response files and uncompressed
entity hashes verify. Image entities were used only for byte hashing: no image
base64 decoding, rendering, visual inspection or feature extraction occurred.

| Check | Result |
| --- | --- |
| Planned slots / ledger rows | 288 / 428 |
| Durable intents / terminal attempt records | 214 / 214 |
| Recorded posted requests / cancelled before posting | 213 / 1 |
| Retry decisions, retry intents and posted retries | All zero |
| Unresolved intents | None |
| Dispatch tickets | Exact consecutive sequence 0–213 |
| Posted slot sequences | Exact consecutive sequence 0–212 |
| First recorded admission | 04:39:39.017889 UTC |
| Last recorded admission | 05:42:21.313906 UTC |
| Minimum recorded admission spacing | 5.000140375 seconds |
| Maximum overlapping recorded response intervals | 2 |
| Minimum next-block start minus previous-block completion | 6.981495291 seconds |
| Complete four-position image blocks | 52 of 72 |
| Receipt elapsed duration | 3778.145781334 seconds |
| Marker-to-receipt wall-clock duration | 3780.004228 seconds |
| New reported cost / new reserve | $0 / $0 |
| Historical conservative accounting | $50.7219185 |
| OAuth subscription monetary valuation | None assigned |

The receipt duration satisfies the 24-hour limit. Its timer begins after the
initial durable marker and before admission; the two duration measurements
therefore need not be identical. The last error terminal was recorded at
05:42:24.831377 UTC; identity invalidation and the halt were recorded at
05:42:24.831769 and 05:42:24.832012. The waiting generic request was cancelled
before posting and recorded at 05:42:24.876207. The final check was recorded at
05:42:32.083956 and the receipt ended at 05:42:32.088282. No later post is present.

These are collector admission and response-interval checks. They do not measure
backend arrival times or prove independent backend state. No account/balance
endpoint was called. Every retained attempt uses the OAuth route, `paid=false`
and zero reservation/cost; the independently derived namespace budget equals
the receipt budget.

The final operator record has `source_verified=true` and `proxy_verified=true`.
I also independently read the current local process/source snapshot; it exactly
matches the frozen snapshot, whose proxy source commit is
`0a664bcc8e09649fcdd558e0bfbdd6447b85bca2`. This local check makes no HTTP request
and does not establish upstream service health. Local source/process continuity
does not overturn the false global identity flag caused by the unrecognized
backend error.

## Scientific consequences without measuring images

| Arm | Returned | Refused | HTTP error | Cancelled | Unattempted |
| --- | ---: | ---: | ---: | ---: | ---: |
| Free | 53 | 0 | 0 | 0 | 19 |
| Generic | 53 | 0 | 0 | 1 | 18 |
| Monet | 53 | 0 | 0 | 0 | 19 |
| Cezanne | 52 | 1 | 1 | 0 | 18 |

Each arm required 72 outputs. Consequently neither named/generic primary has
its allocated complete grid, independently of the global identity failure.
The original analysis also requires complete arms before constructing its
distribution, variance and retrieval summaries, and a complete free arm before
applying historical maps. Its completed-grid arm summaries and maps therefore
cannot become available merely by measuring the 211 returned images. This is a
structural consequence of the frozen code and recorded availability, not a
numerical result. Delivery/status reporting remains possible. Existing older
geometry evidence is unaffected.

## Fixed successor feasibility

The successor's read-only `predecessor_terminal` gate **passes the actual closed
receipt** and verifies the original designated moderation refusal at
`c:pcv_built04:r00:cezanne`. A stopped predecessor is permitted; its unavailable
endpoints are never repaired. The successor design was already fixed from prior
availability information, retains all 24 scenes and both newly generated C/G
arms, and explicitly retains alpha .025 even if original Monet becomes
unavailable. The subsequent Monet loss does not authorize another cohort,
additional outputs, pooling or alpha recycling.

There is no evidence here requiring a source modification, account switch or
endpoint substitution. The one fixed successor can proceed to its own
qualification and freeze gates with the unchanged retry rule. Preparation is
not itself a service-health probe. A fresh source/process identity check and
all required committed-source, qualification and predecessor bindings must pass
before explicit live dispatch. A generic server-error response alone neither
guarantees recovery nor establishes that a new separately frozen collection is
invalid. If the same response recurs, the successor must stop under its existing
contract; there is no further replacement. This audit made no API call, probe,
generation request, restart, real preparation or source/evidence edit.

## Bound evidence

All paths below are relative to
`data/manifests/painter_clause_validation_v1/pcvv1-20260910/` unless stated
otherwise. The freeze records commit
`90a993f7b34419544a5b3afda4f5b120e9f726c2` and qualified scientific source
`dff2804d9b4f5e092201a38fe51eda1fc76e2b73`.

| Artifact | SHA256 |
| --- | --- |
| `freeze.json` | `a6cc05efdfa07c59867e987f41748e3a78ca42047c4c0c4938a8e9035140d022` |
| `planned_requests.jsonl` | `e30ab97d4b6f7bf039210b4c0951fd492a97e2373ade0a298747279bd52593d5` |
| `collection_receipt.json` | `5df074e6c90df761385e61e5118d181244671bd3eebc263d4d9e900ac0e6fdd1` |
| `generation_events.jsonl` | `7ef4e600f9c0bef091c2dfe2e882182916cbc603d3f0f5e05028493c9b9f68b0` |
| `slot_outcomes.jsonl` | `4b72234d4c07a6b1ee9de476943de562d514681218902fcc2f948ea78f85b77a` |
| `operator_events.jsonl` | `dc0cbd47682697c72fc83ff17811dbcf38292d838ba49a4c8cffd0febf8064d8` |
| Workspace `collection_started.json` | `3cd48bcac914fc84ae3b74a14197b90d039636d1979826b1be893eadb263aa34` |
| HTTP 500 uncompressed error entity | `4239661b348f59a9139b8fce613e87715935e656f4d28d290bd353c7ed35fb7e` |
| Original moderation refusal entity | `5f383689fcebc2c43f5bb0fdef45dc1558f6e16726c2c4a39559de68ba4eb9b5` |

The successor gate examined here is in workflow source SHA256
`5c7b1723b73ae4857411456785a06f490ad9c21c11fb91fccc07e00b159cb427`.
This additive audit does not alter its precollection review or any frozen
predecessor artifact.
