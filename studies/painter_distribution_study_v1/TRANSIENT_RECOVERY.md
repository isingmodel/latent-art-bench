# Complete transient failures with missing cost: bounded recovery

Issued 2026-09-07 KST (2026-09-06 UTC), before generated-feature measurement.
The user's existing instruction authorizes single retries for isolated failures
and diagnosis for widespread failures, within the unchanged $75 ceiling.

## Observed failure and billing evidence

The remaining-slot continuation `pdsv1-main-continuation-20260906` is permanently
terminal after 52 slots: 51 images and one complete FLUX HTTP 502 response at
`slot0108`. Its body explicitly reports a Black Forest Labs submission failure,
returns no image or generation ID, and omits `usage.cost`. The frozen guard stopped
on missing cost. All 52 retained responses verified. Together with its predecessor,
100 original slots have been attempted, producing 98 images, one OAuth refusal and
one FLUX server failure. The 908 remaining original slots are still unattempted.
No generated fidelity vector has been extracted or examined.

OpenRouter's [Image API tutorial](https://openrouter.ai/blog/tutorials/image-generation-models/)
(published 2026-07-27, checked 2026-09-06 UTC) states: "failed image requests are not billed".
Its [Zero Completion Insurance support article](https://openrouter.zendesk.com/hc/en-us/articles/51693138951451-Was-I-charged-for-a-failed-errored-or-empty-response-Zero-Completion-Insurance)
(published 2026-06-14) explains the waiver and distinguishes valid output and
separate plugin charges. These requests use the dedicated Image API, no plugins,
and no provider fallback. The failed response has no generation ID with which
to query the per-generation billing endpoint.

This is evidence for a documented failure-billing policy, **not a per-request
invoice**. Keep the raw terminal `cost_usd=null`; do not rewrite it to zero or claim
an observed refund. Continue to count its full **$5 contingency reserve** against
the $75 study limit, separately from provider-reported charges.

## Narrow prospective exception

For the two paid study routes only, recognize a complete HTTP 500/502/503/504
`http_error` with missing reported cost as a known failed submission when its
hash-verified JSON is an error-only object, with a nonempty error message and
numeric error code equal to its HTTP status. No image/data, job ID, output tokens
or other top-level fields may be present. This narrow contract covers the observed
502 without treating arbitrary missing-cost responses as free or safe to repeat.

Such a failure retains its $5 reserve and is eligible for the already-authorized
single delayed technical retry. It does not count as an unknown generation outcome.
An incomplete response, timeout, non-error body, malformed body, successful image
with missing cost, or an error outside this contract still stops new dispatch.
Reported charges, contingency reserves and any unresolved intents must be exported
separately. Never reduce a historical reservation or revise a terminal receipt to
make the spending guard pass.

Retain the explicit OAuth moderation rule: preserve refusals without retry,
rewriting or rerouting. All failed initial attempts, including both predecessors,
count toward the unchanged per-route cluster rule. One failure does not trigger an
unbounded retry loop. A retry that fails receives no second retry.

## Recovery inventory and limits

Use new census `pdsv1-main-recovery-20260907`, with disjoint paths. It schedules
exactly 908 unattempted original slots plus one conditional retry of `slot0108`.
The failed predecessor remains terminal. The retry child binds its actual parent
run, terminal event and identical original payload. All prior successes are retained;
no successful image or OAuth-refused slot is attempted again.

Keep the original 1,008-slot scientific design, window origin 2026-09-06 14:30 UTC,
eight offsets, route subsequences, content weights, references, scalers and endpoints.
Keep three workers, one active call per route, globally staggered starts of at least
five seconds, 1,050 total / 612 paid attempt caps, at most 24 single retries across
all main-study censuses, a $5 paid in-flight reservation and a 5 GiB storage reserve.
The existing $5 failed-call contingency remains reserved in addition to new in-flight
calls. Retry delay is at least 60 seconds and honors Retry-After.

Commit the new contract, source, tests and predecessor terminal evidence before
preparing the recovery freeze; commit that freeze before resumed dispatch.

## Derived analysis

After completion, combine the two closed predecessors and recovery ledger by original
slot identity. Only `slot0108` has a prospectively authorized cross-census retry update;
validate its predecessor event and retry authority rather than arbitrarily selecting
among duplicate rows. Preserve its initial failure and actual delayed retry time.
Within-census retries continue to retain their original failed attempts as usual.
The final view contains 1,008 original identities, with the OAuth refusal remaining
missing. The completed census statuses are reported separately from this derived view.

Measure all first valid selected images under the unchanged three pipelines in the
new workspace. Reuse completed reference/development records and frozen analysis
primitives. Retain missing pairs, the initial-only sensitivity, eight-endpoint Holm
family, actual timing and no-interference limitation. The correction concerns observed
transport failures before generated-feature exposure; it does not select an effect.
