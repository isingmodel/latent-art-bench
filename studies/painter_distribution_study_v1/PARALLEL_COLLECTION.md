# Staggered parallel execution amendment

Issued 2026-09-06 after the user explicitly requested parallel API calls with
staggered starts. The sequential census `pdsv1-main-20260906` was stopped before
its first research POST and permanently closed: zero research attempts. Its
scientific freeze and completed 221-work development remeasurement remain evidence.

The successor `pdsv1-main-parallel-20260906` reuses the exact 1,008 slot payloads,
within-route randomized condition order, reference panel, fixed content masses,
three processing pipelines and eight inferential endpoints from `MAIN.md`.
It binds the predecessor's terminal receipt and development scalers. No fresh
reference or generated fidelity vectors were viewed before this amendment.

## Concurrency and timing

Use at most **three in-flight HTTP requests**, with **one per model route** and
at least **five seconds between globally recorded dispatch starts**. Three route
workers consume their respective subsequences of the frozen inventory in order.
Within each window their initial readiness is staggered by route index × five
seconds. Subsequent readiness depends on completion; the global start gate still
applies. A waiting retry occupies its route but does not block the other routes.
The single coordinator lock protects request intents, reservations and terminal
ledger updates. A process-wide writer lock excludes another collector.

This supersedes the sequential global order and 15-second interval in `MAIN.md`.
Within each route, randomized group/condition order remains unchanged. Record
actual request and completion times rather than claiming simultaneous matched
exposure or independent backend sessions. Concurrent gateway traffic and shared
service state can challenge the no-interference assumption of the conditional
prompt tests; the absolute feature-distribution comparisons remain descriptive.

Keep eight windows at offsets 0, 3, 6, 9, 24, 27, 30 and 33 hours from a new
prospectively recorded UTC origin. Every brief retains three distinct windows.
The new freeze must be committed before any successor POST or fresh reference
measurement. A delayed run records late actual times without fabricating spacing.

## Budget, retries and stopping

The same $75 study ceiling, 1,050 total attempts including the pilot, 612 paid
attempts, and at most 24 single retries apply. Reserve $5 for every paid request
under the coordinator lock **before** releasing transport. Other requests in
flight retain their reservations in the shared budget. Only unresolved intents
owned by the current live coordinator may coexist with a new dispatch; an orphan
intent or unknown recorded charge prevents further calls.

Apply the existing transient-error and Retry-After rules. Child retry censuses
have disjoint successor paths and create-once authority records binding their
initial terminal event and execution freeze. A successful image is never rerolled.
Three consecutive failed initial attempts on one route, or four among its last
20, stops new dispatch across all routes. Authentication/payment/payload defects,
invalid successful responses and uncertain outcomes also stop new dispatch.
Allow already accepted calls to finish and retain their results; do not cancel
them and assume they were unbilled. A failed retry receives no further retry.

Closed sequential or parallel censuses are never resumed. A fix after a terminal
failure requires a disjoint successor bound to its evidence. The user-authorized
parallel change does not authorize changing the scientific endpoints or spending
ceiling after seeing new outcomes.

## Measurement and analysis reuse

`parallel_results.py` writes successor measurement and analysis records in the new
directory. It calls the frozen `measurement.measure_path` and `analysis.compute`
primitives with the existing scalers, payload membership and content weights.
It does not edit or rerun the closed sequential collector or development stage.
New image-decoding temporary files also stay under the successor workspace.

The PDF prototype and final report must identify the executed successor, actual
concurrency, retries, timing, costs, availability and remaining assumptions.
