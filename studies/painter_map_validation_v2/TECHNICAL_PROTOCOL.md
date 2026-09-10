# Fixed-map v2 operational contract

This prospective contract implements only `pmv2-20260910`, after the single
R10 qualification selected 240 outputs. The scientific definitions, fixed
historical maps/reference/scaler, complete-grid rule and uncertainty assumptions
are in [PROTOCOL.md](PROTOCOL.md). V1 remains stopped. There is no replacement,
partial-grid analysis, new allocation, provider fallback or automatic restart.
Qualification is proxy evidence and does not itself authorize an image request.

## Source, allocation and access gates

The create-once compact `inputs.json` is constructed offline by
`analysis.load_inputs`. It preserves the exact primary512 scaler, 32 Cezanne
reference vectors, full historical FLUX map and feature order, with both original
numerical file hashes. Preparation and subsequent verification require its exact
canonical equality to this immutable projection. No reference is re-extracted.

The frozen `study.json` selects twelve fixed reviewed scenes, ten repeats, two
arms and 240 unique slots. Seed 2026091071 independently permutes the free/named
positions within each pair, then globally shuffles all 120 pairs. Repetition
indices are fully interleaved. A pair drains before the next pair. Each payload
is the unchanged historical FLUX request: model `black-forest-labs/flux.2-max`,
provider `black-forest-labs/us-3` only, fallbacks disabled, `n=1`, aspect ratio
`1:1`, PNG output and the exact historical prompt builder. There is no resolution,
size or rendering-seed field. Delivered backend variability includes unspecified
backend seeds. Assignment randomization is not evidence of independent or
stationary errors, or of an independently attested checkpoint.

The prospective numerical qualification, its source and failed-v1 lineage,
all operational/scientific source and tests, reviewed design/protocols, software
lock, original numerical inputs and complete accounting ledgers must be bound to
clean committed bytes. Operational qualification additionally requires an explicit
`qualified: true` source-bound receipt. The source commit, qualification commit
and later freeze commit may differ; each is checked against the exact bytes it
claims. A changed bound source, index, runtime, scene, input or ledger closes
admission. The freeze and planned requests must be committed before collection.
No sealed prior source or terminal evidence is rewritten.

Two narrowly scoped metadata observations have separate create-once paths:
`pmv2-prefreeze-20260910` before qualification/freeze and
`pmv2-dispatch-20260910` immediately before image admission. Each permits exactly
one GET of OpenRouter credits and one GET of the fixed FLUX endpoint metadata,
without redirects or retries. The prior safe metadata projection/fetch primitive
is reused without global overrides. Only available credits, fixed model/provider
pricing and successful body hashes are retained; no credential or unrelated
account fields are output. Endpoint response hash
`765c865e57488f2620f6860c6562b4d4696460e442f596c24bdb89895f7ea99d`
must match the retained body, including payload capabilities. This deliberately
strict identity check can reject an otherwise benign metadata change.
Metadata source must be committed before either observation. The terminal
collection binds the dispatch observation; source and its bound metadata are
checked again after the final in-flight block drains. There is no per-block
network metadata polling.

## Conditional affordability, not guaranteed delivery

The historical project account is $50.7219185, including the permanent $5 old
unknown-cost reserve. Verification independently reconciles prior event chains
and the later zero-paid cohorts. The recorded legacy floating value
50.72191850000009 is compared at absolute tolerance 1e-10, with zero relative
tolerance; original bytes/hashes are never refreshed. There must be no new
pending intent or unknown liability when this namespace starts. No other paid
collection may run concurrently. No top-up or purchase is authorized.

The endpoint quotes $0.07 per output megapixel, not a guaranteed price per image.
All observed historical FLUX successes cost $0.07, but an aspect ratio does not
fix delivered pixel dimensions. The conditional planning allowance is $0.075 per
attempt, including eight possible known-cost technical attempts: 248 × $0.075 =
$18.60. Each fresh metadata receipt must show at least this much actual available
credit. An earlier observation does not establish the balance at either new gate. The $75 project ceiling is unchanged.

Before **each** admitted attempt, two separate retained safeguards apply:

1. Known settled charges, terminal unknown-cost reserves at $5 each, and $0.075
   times all remaining permitted attempts (including already pending attempts
   once) must fit both the observed dispatch credits and project ceiling. The
   forecast keeps the unused technical-attempt allowance until admission ends.
2. Project accounting includes a $5 liability for every pending paid attempt;
   admitting another requires another $5 within $75. If only a current pending
   liability prevents admission, wait for that worker to settle; do not treat
   temporary exposure as a failed scientific cohort. This automatically serializes
   the last part of collection when two reservations no longer fit.

The $5 in-flight liability is a project-ceiling safeguard. Actual credits use the
explicitly conditional full-plan forecast, not a guaranteed $5-per-request
credit hold. These are not contractual billing caps or a completion guarantee.
A missing cost retains a $5 terminal reserve and stops/drains immediately;
remaining planned credit cannot be assumed. A reported charge above $5 stops
immediately, including on the final otherwise successful slot. Known charges
above the $0.075 forecast can also close the plan at its next admission guard.
An authentication, quota or credit failure closes admission; no live balance
reconciliation or additional attempt is automatic. Reconciliation can document
liabilities but cannot reopen this terminal cohort.

A complete response with finite nonnegative numeric `usage.cost` takes precedence
and is labeled `provider_reported`. The inherited convention treats a fully
received, well-formed **error-only** explicit 400/401/402/403/404/422/429 client
rejection without reported cost as $0, labeled
`retained_explicit_client_rejection`; this is not provider-attested billing.
An image/data-bearing, truncated, malformed, ambiguous, timeout or unpriced 500
response never obtains this zero-cost convention. Its cost remains unresolved.

## Admission, technical failures and permanent stopping

Collection requires explicit `--live`; tests use only `httpx.MockTransport`.
The one-shot workspace/ledger cannot exist already. Every intent, including its
$5 reservation, exact payload hash and ordered dispatch ticket, is durably
appended before transport. At most two attempts are admitted concurrently and
recorded starts are at least five seconds apart. These local admission records
do not attest backend arrival order. Requests have a 240-second HTTP timeout,
20-second connection timeout, a 64 MiB response cap and no redirects. Responses
are retained compressed with entity/storage hashes and technical image metadata;
no aesthetic inspection or feature extraction occurs during collection.

Only the unchanged strict technical-error recognizer qualifies a retry: a
complete error-only JSON envelope with an integer code exactly matching an
allowed 429/500/502/503/504 status and a nonempty message. The OAuth-specific
plain-text exception is irrelevant to this paid FLUX route. No broad retry is
allowed for an unqualified server message, authentication, refusal, unsupported
success or ambiguous delivery. A qualified but unpriced 5xx still stops because
its cost is unknown. Because the strict error-only schema excludes `usage`, the practically reachable
known-cost technical retry is the 429 client-rejection convention. A priced 5xx
envelope carrying `usage` does not qualify. Qualified attempts may retry the identical
payload once per slot, at most eight times across the cohort, after the retained
60-second/Retry-After rule (maximum accepted delay 300 seconds). Needing a ninth
retry stops; merely having used eight successful retries does not stop later
first attempts. No image quality criterion can trigger another request.

Any irrevocably unavailable required slot stops/drains immediately, including a
moderation refusal or second technical failure. Other immediate stops are
unrecognized backend errors, uncertain or unsupported delivery, reported model
mismatch, source/identity failure, unknown or over-reservation cost, unaffordable
remaining grid, attempt-limit exhaustion, fewer than 5 GiB free storage, or three
failures among the latest eight posted attempts. Dispatch closes five minutes
before the 24-hour collection deadline to leave drainage time. An interruption
stops admission and drains workers; all terminal statuses and every unattempted
slot remain recorded. A later identity failure is recorded even if an earlier
resource stop was already the primary reason. There is no resume or repair.

## Terminal eligibility and one-shot measurement

The receipt records all 240 slots, attempts/retries, terminal charges/reserves,
local timing, explicit source/endpoint identity checks and the dispatch metadata
binding. Workflow re-derives eligibility from these records, authenticates every
retained response cost basis and verifies the first-valid-output rule. Scientific
eligibility requires a complete 240-image grid, intact global source/identity and
24-hour/admission-timing contracts, and resolved admissible terminal accounting.
An unavailable slot or global failure withholds all scientific points and
intervals. This rule does not imply that availability is independent of image
content, costs, prompts or delivered outcomes.

Measurement is separately one-shot after terminal verification. It retains one
primary512 status row for every planned slot, exact identity/feature order,
raw and fixed-scaled coordinates, and response provenance. Failed collection
eligibility remains unavailable even if some images can be measured. All 240
finite eligible vectors are required for the four component scores and both
contrasts; the scientific protocol's interval-only variance exception applies
only to a valid complete finite grid. Measurement/report/analysis/start-marker
hashes form an exact four-file receipt. Ordinary local `check` authenticates
private response bodies for costs and replays stored numerical rows/reports;
it does not extract features again. A public numerical adapter must use the
pure scientific analysis API, distinguish transport attestation from numerical
recomputation, and exclude private responses, keys and credit balances.
