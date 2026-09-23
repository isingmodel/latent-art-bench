# Offline family-control collector qualification

19 September 2026. **Implementation and constructed fixtures only. No live
collector, new service observations, paid requests, credentials, downloads,
old collector restart, or scientific rating.** The six-configuration,
12-scene, eight-arm, eight-window proposal remains 4,608 slots. The retained
historical accounting is $112.293676; the approved cumulative ceiling remains
strictly below $120. A test's $350 setting is a simulation parameter, not
authorization. The proposal and old terminal records are unchanged.

## Implemented boundary

`src/latent_art_bench/painter_family_controls_v1/collector.py` is a synchronous,
offline state machine. It contains no HTTP client, credential discovery, image
URL retrieval, scheduler, or live adapter. Construction defaults to denying
every start. `simulation=True` enables only local fixture bookkeeping;
`execute_one` accepts the finite built-in `MockTransport` and `MockResponse`.
`start` and `finish` also permit explicit stepping for concurrency and recovery
tests. An arbitrary transport cannot be passed to `execute_one`.

Assignments come from the separate protocol module. The collector stores their
exact payloads and order in a create-once `run.json`, binds recovery to that
manifest and accounting policy, and requires a sole `provider.only` route with
fallbacks disabled. OpenAI configuration labels are checked against the full
requested payload route. The protocol module owns full-grid membership checks;
the collector intentionally accepts small fixture subsets for qualification.

## Durable behavior and admission

- Starts are durable, hashed, append-only intents in `events.jsonl` before the
  fixture transport is invoked. Ends record retained response/image paths,
  detected media types, timestamps, charges, diagnostics and assigned windows.
  Files and parent directories are fsynced. Exclusive artifact creation retains
  crash-created partial files and refuses replacement.
- A process-level `flock` permits one owner. Its persistent file is not deleted
  during release. Process death releases ownership but never reconciles an
  outstanding intent. Replay detects damaged or truncated journal chains and
  pauses without rewriting them.
- Admission requires the assigned UTC four-hour window, at least five seconds
  since the previous global start and no more than three open attempts.
  Completion after cutoff is retained under the original assignment. Retry
  admission uses that same window; there is no late backfill.
- Money uses `Decimal`. Every start reserves $5. Known charges settle exactly;
  unknown charges and unclosed starts keep their reservations. Admission
  requires historical plus new settled plus all outstanding and proposed
  reservations to remain strictly below the configured ceiling. The default
  ceiling is $120. The $220 new-settled operating stop is implemented but can
  only become meaningful under a separately authorized future budget; its
  present exercise is a simulation.
- A response error never implies a zero charge. Explicit `usage.cost` or
  separately supplied fixture billing evidence is required. Contradictory
  billing evidence remains unknown. Unknown/excess charges, archive errors,
  transport ambiguity and technical mismatches pause admission.
- Only known-charge 429/500/502/503/504 technical failures can retry. Content
  refusals cannot retry. Delays are 20 seconds then 60 seconds from completion;
  limits are two retries per slot and 96 globally. Three consecutive technical
  failures pause dispatch. A persisted pause has no automatic resume API.
- Each configured write volume is checked using actual free bytes, with a
  5 GiB floor plus 256 MiB per outstanding/proposed request reservation.
  Response archiving rechecks capacity. Small intent/end/diagnostic records are
  still attempted after storage trouble to preserve accounting evidence. The
  separate initial 40 GiB planning requirement belongs to preflight. No evidence
  or cache is deleted to manufacture capacity.
- Response consumption stops at 64 MiB and retains a gzip partial archive on
  overflow or stream interruption. Complete response bytes are retained in gzip.
  Every decoded image's original bytes are retained before image inspection;
  media type comes from those bytes. Unexpected image count, geometry other
  than 1,024 square, invalid bytes or contradictory model/provider echoes pause
  dispatch. Missing echoes stay missing. No resizing or replacement is applied.
- `terminal.json` is create-once and permanently blocks reopen, including when
  a crash left a partial terminal file. Closure requires currently owned
  attempts to drain, records every planned slot, and keeps uncertain charges
  and unclosed recovered intents in an explicitly incomplete census. Terminal
  archive failure persists a pause where journal writes remain possible.

## Constructed qualification

Command run in the existing local environment:

```
.venv/bin/python -m pytest tests/painter_family_controls_v1/test_collector.py -q
.venv/bin/ruff check src/latent_art_bench/painter_family_controls_v1/collector.py tests/painter_family_controls_v1/test_collector.py
```

Result: **42 collector tests passed; Ruff passed.** The tests exercise default
denial, current and exact-boundary budgets, global start spacing/concurrency,
window cutoff/stragglers, actual zero disk space and all write volumes, retry
delays and the 96-retry ceiling, refusals, excessive/unknown/conflicting charges,
the simulated $220 stop, original-byte and gzip retention, count/geometry/echo
mismatches, bounded response overflow, interrupted streams, exclusive archive
collisions, archive/terminal failures, durable intent fsync failure before
transport, abrupt child-process exit, exclusive ownership, replay and changed
manifest denial. An integration test uses an actual protocol assignment and
its exact OpenAI route/provider payload.

These tests use generated in-memory solid-color fixtures and temporary paths.
They do not verify a current provider route, price, billed request behavior,
service identity, production transport, eventual scheduler, or real free space
for the proposed collection. Initial capacity, live authorization, complete
freeze inputs and independently verified routes/prices remain separate gates.
Evidence reconciliation after ambiguity is intentionally manual and no live
reconciliation or resume implementation is provided here.

State and accounting updates use cached indexes, and journal replay is linear
in its event count. `select` preserves frozen order by scanning eligible slots;
future scheduling may step directly through the frozen list. The engine is
qualified offline infrastructure, not a claim that the proposed study has run.
