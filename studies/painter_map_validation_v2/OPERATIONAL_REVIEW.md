# Fixed-map v2 precollection operational review

2026-09-10. Scope: the prospective `pmv2-20260910` collection and its terminal
eligibility/measurement handoff. **No remaining must-fix issue was found in this
bounded review of the snapshot below.** This is a source review, not a live
authorization, service guarantee, or new paper score. The separate source-bound
qualification, fresh metadata checks, clean source and freeze commits remain
required before collection.

The reviewer is a maintainer-run LLM agent. I authored the scientific protocol
and scene inventory, contributed the pre-data redesign interpretation and
manuscript/literature advice, and identified implementation issues during this
review. I did not implement the collector or operational tests. This is not an
independent human or institutional assessment. Existing paper reviews and
scores are unchanged.

## Reviewed snapshot and evidence

I read `PROTOCOL.md`, `TECHNICAL_PROTOCOL.md`, the configuration, common,
metadata, collection, workflow and CLI source, the operational tests, and the
analysis input/eligibility interface. I also inspected the inherited prompt,
payload, response inspection, retry recognition and ordered-start primitives.
The scientific numerical oracle review is separate. Repository HEAD during the
final checks was `dabc2f85f5f3eada7ea6fdcbb84181ae320953d1`; the new operational
files were still uncommitted. This report binds the reviewed bytes by hash,
rather than claiming that HEAD already contained them. The implementation agent
confirmed the final source/contract snapshot was held stable.

| File, relative to the repository | SHA256 |
| --- | --- |
| `src/latent_art_bench/painter_map_validation_v2/common.py` | `d5cc5410d00c91c627c78fb2f540b7f1ca027976fb426750a4d3fba329c6b119` |
| `src/latent_art_bench/painter_map_validation_v2/metadata.py` | `c43b0311928e8ee21a5b97043378022cbe31d4c2bc737f631ba4d85d27fe0e27` |
| `src/latent_art_bench/painter_map_validation_v2/collection.py` | `019c8df4fcc7f3ff9852fd457b389d0e7dd7389b21fab468a22421d690f1564c` |
| `src/latent_art_bench/painter_map_validation_v2/workflow.py` | `e3ed2ed6b7e0479c5247955603ef7a275eeae465aee14ce0ca965a848b8d7b17` |
| `src/latent_art_bench/painter_map_validation_v2/__main__.py` | `09d58f1b54df17b320c799c2478fd44b54f2735b991a80177589e33ba2e0ff73` |
| `src/latent_art_bench/painter_map_validation_v2/analysis.py` | `7e06025be026312174a5335238233b42a3da2082ba88490e96b97d9316b64209` |
| `tests/painter_map_validation_v2/test_operations.py` | `ce58975358166d2b14af5880296e15cc2d7f8fcf2a5b2b27ce3ff5fc553065ea` |
| `studies/painter_map_validation_v2/TECHNICAL_PROTOCOL.md` | `08e07a0a0a555738f02dd925e7c12a91ad8a42a15d90a8661a0ac04f8f6f75ad` |
| `studies/painter_map_validation_v2/PROTOCOL.md` | `d40f05a8714279ede08d395238739defda96d9a950e81f2b67d81d9caebca212` |
| `studies/painter_map_validation_v2/study.json` | `287fbd5d11c901ac8937ce6148395b65d8d2615c4f494cad5a7ea65d90e657a8` |
| `studies/painter_map_validation_v2/scenes.json` | `f530b6d2b0cff99d30f123fee90bddd6732eeffc104124147739a89d13580a57` |
| `studies/painter_map_validation_v2/inputs.json` | `8c7d3c74a420b12782fabf306f85e9953ac6cb794f31d2e365f2adf0b7094a04` |

My final offline run of
`uv run --locked pytest -q -m 'not live' tests/painter_map_validation_v2/test_operations.py`
passed **52 tests in 27.28 seconds**. Scoped Ruff on the v2 source and tests also
passed. These include complete artificial-grid collection/replay, refusal and
unknown-cost stopping, identical-payload retry, the eight-versus-ninth retry
boundary, final identity failure, metadata rejection, timing validation,
source/freeze gates and exact measurement-receipt inventory. Fixtures replace
wall-clock waits and real feature extraction; separate predicates test local
spacing/overlap. These are not live-service or empirical-power tests. The full
project suite and aggregate qualification are the parent's separate checks.

## Scientific and operational fidelity

An additional offline comparison confirmed that compact inputs equal the exact
immutable numerical projection: 32 Cezanne references, all 31 features, the old
scaler and the unique full historical FLUX map with scalar
`0.6785365094757265`. This is not an average of fold fits. All 240 planned
payloads equal the historical prompt/payload builders, with 120 unique pairs
and four scene briefs per class. No rendering seed, size, resolution, palette,
generic clause or reference image is added. Assignment seed 2026091071 fixes
within-pair arm order and interleaves all scene/repeat pairs; each pair drains
before another begins.

Both E/Q contrasts and all four component points require the entire allocated
primary grid plus intact global collection contracts. A complete image grid
does not override a timing, identity, resource or accounting failure. Numerical
interval unavailability alone retains the scientific protocol's narrower
exception for finite, otherwise eligible full-grid points. No partial-case
repair, reference re-extraction, new map fit, evaluation centering, alternative
feature pipeline or extra scientific endpoint is introduced.

The historical ledger calculation independently reproduces $50.7219185,
including its permanent old unknown reserve. Before each new intent, the
collector separately checks (a) the remaining full-plan forecast against fresh
dispatch credits and the $75 ceiling and (b) the additional $5 pending liability
against that ceiling. Pending attempts appear once at $0.075 in the conditional
credit forecast; temporary project-reservation pressure waits for settlement.
The $18.60 forecast is not a service price cap. Unknown cost retains $5 and
stops; any reported charge above $5 stops, including a final successful slot.

Finite nonnegative numeric `usage.cost` overrides an assumed rejection charge.
Only a fully received, well-formed error-only explicit client rejection obtains
the separately labeled zero-cost convention; it is not provider-attested
billing. Truncated, data-bearing, malformed and unpriced server responses do
not obtain that convention. Because the inherited strict retry schema permits
only an `error` top-level field, its practically reachable paid-route retry is
the zero-convention 429. A `usage`-bearing 5xx does not qualify. The final
technical text now states this accurately.

Admission stops and workers drain as soon as a required slot cannot recover,
including refusal or a second technical failure. The first valid output is
retained; image appearance cannot trigger retry. Source and dispatch-metadata
bindings are checked after drainage. Local starts, durations, costs, all
unattempted slots and the unique primary halt remain recorded. Metadata uses
two separate create-once two-GET observations with no redirect/retry; exact
endpoint-body equality deliberately rejects even benign metadata changes.

## Material defect found and resolved before collection

I independently constructed an artificial complete grid with 239 successes at
$0.01 and a final success at $5.01. Total new cost was $7.40, so neither overall
budget test independently exposed the reservation breach. Collection correctly
stopped, but the earlier verifier accepted a receipt changed to
`complete`/eligible despite the unchanged cost and halt ledgers. This was a
real verification gap, not evidence of a live billing failure.

The final verifier derives terminal disposition from the unique retained halt
or duration failure, and rejects missing mandatory stop evidence for unknown,
over-reservation or unrecoverable outcomes. The exact low-total-cost forgery
now has a passing rejection regression. The parent's earlier immediate-stop
corrections for final-slot overcharge and permanent slot loss are also present
and tested. An intermediate synthetic decimal fixture had an incorrect
expected literal; its correction, not a change to metadata arithmetic, produced
the final passing suite.

## Limits and handoff

Completeness prevents selective deletion; it does not establish that completion
is independent of prompts, costs, refusals or generated content. Conditioning on
a completed cohort can still select service outcomes. Randomized scheduling
does not establish independent stationary repeat errors, backend arrival order
or absence of cross-request interference. The historical-proxy qualification
therefore cannot guarantee actual interval coverage. Results must retain these
limits and remain conditional on the fixed scenes, old maps, scaler and
reference reproductions.

The retained $0 client-rejection convention, non-guaranteed pricing and absence
of concurrent paid work are explicit operational assumptions. No top-up,
reserve reduction, in-place resume or further replacement is authorized here.
The implementation is suitable for the parent's remaining precollection gates
within this stated scope; only their successful completion can establish a
dispatch-ready freeze. No real image request, artwork access, protected-holdout
access or research-image feature extraction occurred during this review.
