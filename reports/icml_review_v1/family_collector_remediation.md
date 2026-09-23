# Offline collector remediation after independent audit

19 September 2026. This is software qualification using constructed fixtures.
It contains no live acquisition, route/price validation, credentials, downloads,
new observations, old collector changes or scientific rating. The existing
approved ceiling remains strictly below $120; $350 occurs only in simulations.

The [independent audit](family_collector_independent_audit.md) preserves the
initial adverse findings and original source hash. After preserving that report,
the audit agent implemented the corrections below. The later integration run
and review are owned by the coordinating agent; the audit agent's remediation
tests alone are not an independent review of its own fixes.

## Corrected behavior

| Initial finding | Change and retained regression |
| --- | --- |
| Completion exceptions left dispatch enabled | Corrupt PNG CRC is diagnosed, its known cost settles, and the run pauses. An unexpected processing exception persists a pause and leaves its intent/reservation for reconciliation. Nonfinite/malformed status is normalized to missing status with a diagnostic and a durable end. |
| Truncated JPEG passed verification | Expected-size images undergo actual pixel decoding after the original bytes are retained. Truncated JPEG and corrupt PNG cases remain in tests. Unexpected dimensions are diagnosed without allocating their potentially enormous pixel buffers. |
| Foreign journal and missing artifacts accepted | Every event includes its exact manifest hash. Replay validates assigned payload hash, window, attempt, fields and ordering; checks end/intent identity and typed status; and verifies each referenced original and decompressed response against its size/hash. Terminal closure independently rechecks retained bytes. |
| Mutable assignments/events/policy | Operational dictionaries are private. Public assignments, events, starts, ends, pauses, returned intents and policy are independent snapshots. The exact validated `CollectorPolicy` type is required; subclasses, booleans and arbitrary policy objects are rejected. |
| Missing storage check before original writes | Admission checks every configured volume and both artifact directories. Each response and original write rechecks actual destination capacity. Symlink artifact directories are rejected. Loss of space after the response archive stops original writes, settles known cost and pauses. |
| Direct calls bypassed order | `start` now requires the first unstarted assignment in the same session. Eligible retries remain governed by the existing delay/window/cap rules and may interleave with first attempts. Replay checks the same first-dispatch order. |
| Wrong-schema response fields silently coerced | HTTP status must be an exact integer in 100–599 or missing; refusal must be boolean; JSON nonfinite constants are rejected. Malformed usage/error fields and contradictory 200/error envelopes are diagnosed. Explicit billing evidence must be nonblank text. |
| New run path lacked durable parent links | Every newly created directory has its parent synced before dispatch can follow. The regression observes syncs of both newly created run-directory ancestors. |

Financial sums now use a sufficient local Decimal precision instead of relying
on the process's default precision. A 36-place observed charge is retained
exactly in cumulative accounting. Financial input with over 1,000 coefficient
digits or an exponent magnitude above 1,000 is treated as invalid/unknown;
its original response remains retained and the reservation remains. Boolean,
nonfinite, negative and extreme-exponent costs are regression cases. No error
implies a zero charge.

The manifest now uses `painter-family-controls-collector/2.0` and includes the
reservation, settled stop, storage floor/reservation and response limit as well
as the existing ceiling, history, write paths and exact ordered assignments.
Old unbound fixture manifests/journals are intentionally incompatible and are
never silently upgraded, rewritten or resumed. Broken terminal symlinks also
count as permanent terminal barriers.

## Validation completed by the remediation agent

```sh
.venv/bin/python -m pytest tests/painter_family_controls_v1/test_collector.py tests/painter_family_controls_v1/test_protocol.py -q
.venv/bin/ruff check src/latent_art_bench/painter_family_controls_v1/collector.py tests/painter_family_controls_v1/test_collector.py
```

Result: **115 passed in 1.38 seconds; Ruff passed.** This adds 51 collected
adversarial cases to the original combined 64 collector/protocol cases, while
retaining the original cases. Tests use temporary storage, a synthetic clock,
generated image bytes and mock responses; the family-control test suite disables
socket connections, sends and DNS resolution.

Validated source SHA-256:

- Collector: `a07d21b13daf940023be2c7ba91847dc6138aa31c87915f004493f22e5f88d09`
- Collector tests: `7a11e3c5dbdcd34b630527c1902bcee64a03c3b74ed52842550dab199bd65c69`

The coordinating agent was informed that the API was stable for its separate
full 4,608-slot fixture census and full-journal replay. That run's result is
reported separately rather than predicted here.

## Remaining boundaries

There is still no live transport, scheduler, credential lookup, URL downloader,
automatic charge reconciliation or resume API. Small intent/accounting/diagnostic
records remain attempted after space trouble so uncertainty is not hidden.
Durability is tested with filesystem calls and constructed process/crash cases;
this is not a physical power-loss/storage-controller certification. The final
freeze, current route/price verification, actual initial storage capacity and
financial/acquisition authorization remain separate gates.
