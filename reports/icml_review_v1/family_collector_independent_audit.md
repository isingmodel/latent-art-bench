# Independent offline collector audit

19 September 2026. Initial adversarial audit of `collector.py`, `protocol.py`,
the prospective v3 requirements and the implementation report. No service calls,
credentials, downloads, old collector edits, new observations, or scientific
score. All constructed acquisition fixtures were created in temporary directories.

Audited collector SHA-256:
`effad0554795ffaa6799843a9aa60a14e54e5ec845c78936150ef46ca0aed268`.
This report records the **pre-remediation** implementation. Subsequent fixes and
validation belong in the separate remediation note; these findings are retained.

## Result

**The initial engine does not yet satisfy the v3 qualification requirements.**
Its original collector and protocol suites passed together: **64 passed in
0.97 seconds**. The independent cases below expose gaps outside those tests.
They are software correctness findings, not evidence about a provider or the
proposed scientific effect.

## Confirmed findings

### 1. Corrupt-image and malformed-status exceptions leave dispatch enabled

High priority; original `collector.py:477–503, 582–595`.

Construct a valid in-memory 1,024-square PNG, find an `IDAT` chunk and flip one
bit of its CRC. The retained fixture reports known cost `0.05`. `finish` raises
`SyntaxError: broken PNG file (bad header checksum in b'IDAT')`, which `_images`
does not catch. The run has one open intent, zero settled dollars and **no
pause**, and a different slot has no admission objections five seconds later.
The response and original bytes survive, but known accounting and the required
technical-mismatch pause are not completed.

Separately, `MockResponse(float('nan'), b'{"usage":{"cost":"0.05"}}')`
reaches event serialization, raises `ValueError`, leaves no pause, and permits a
second start. Nonfinite status and other malformed response fields require
validation before they can poison the durable end record. Unexpected completion
processing errors must also fail closed while preserving the intent/reservation.

### 2. Image verification does not establish successful pixel decoding

High priority; original `collector.py:493–496`.

Save a white 1,024-square JPEG using Pillow and remove its last 20 bytes. A fresh
`Image.open(...).load()` raises `OSError: image file is truncated`, while the
collector's `Image.verify()` succeeds. The collector reports `success=True`,
dimensions 1,024 by 1,024 and no pause. Fully decode pixels after preserving the
original bytes; retain the image and diagnose decode failure without replacement.

### 3. Valid journals are not bound to their run or retained artifacts

High priority; original `collector.py:313–348`.

Create run A using actual protocol slots and finish its first slot successfully.
Create run B with the same IDs but a different first prompt, then copy only A's
unaltered `events.jsonl` into B. No hashes are forged or recomputed. Reopen B:
`journal_corrupt=False`, `pauses=[]`, accounted dollars `112.343676`; terminal
census calls that slot `successful` even though its original image is absent.
Events need a manifest identity, start fields must match the assigned slot, and
recovery must verify referenced raw response/original files and their hashes.
The existing manifest comparison does correctly reject a changed manifest
argument in the same intact directory, but does not cover this transplant.

### 4. Frozen assignments, events and policy are mutable through public access

High priority for a future scheduler; original `collector.py:178, 182–204,
350–356, 438–453, 597–606`.

After construction, change `run.slots[first_id]['payload']['prompt']`. A built-in
mock exchange sends the changed prompt and reports success; `run.json` still
contains the old prompt. Returned events and the nested values in mapping proxies
also alias indexed state. Use private immutable snapshots or deep-copy public
views, and use the frozen intent payload for exchange.

An arbitrary `SimpleNamespace` policy with reservation `Decimal('0')` is accepted.
The first intent states reservation `5`, but accounted dollars remain
`112.293676` with one outstanding request. The manifest omits that custom
reservation value. Require the exact validated `CollectorPolicy` type and bind
all operative policy constants to the manifest.

### 5. Free-space admission is missing before original-image writes

High priority; original `collector.py:489–490, 548–569`.

An injected actual-space function returns 50 GiB through start and response
admission. Immediately after the gzip response is created, set it to zero. The
image is still written and the run returns success with no pause. Exactly two
space checks occur; there is none before the original-image write. Check every
large destination write, retain accounting/diagnostic writes on failure, and
ensure nested/symlink destinations do not evade actual-volume inspection.

### 6. Direct dispatch does not enforce frozen first-attempt order

Medium priority; original `collector.py:428–451`.

Pass four consecutive actual protocol assignments and call `start` on the fourth
at its window opening. It is accepted at `session_order=3` before order zero.
`select` prefers frozen order, but `start` and `execute_one` do not enforce it.
The state-machine boundary needs to enforce first-dispatch order, while leaving
the prespecified eligible retry rules intact. Merely relying on a future caller
does not qualify the current collector for the v3 ordering requirement.

### 7. Wrong response schema can silently acquire valid meaning

Medium priority; original `collector.py:520, 558–581`.

`status_code=200.0` produces success. `refusal='false'` and JSON `refusal:NaN`
both become a content refusal without a diagnostic pause. The JSON parser permits
nonfinite constants and refusal uses generic truthiness. Require an integer HTTP
status or explicit missing status, a boolean refusal when present, and strict
JSON constants. A malformed field must not silently consume a slot as refusal.

### 8. Newly created run-directory ancestors are not durably linked

Medium priority; original `collector.py:206, 234–249, 282–286`.

Instrument directory fsync while creating `temporary/new-parent/new-run`, then
starting the first slot. Both observed syncs target `new-run`; neither parent of
a newly created directory is synced. The files and immediate run directory are
synced, but durable creation of the run path itself is not established. Sync the
parent of each newly created directory before any intent may lead to dispatch.
This is a filesystem durability argument and instrumentation result, not a
simulated power-loss experiment.

## Controls that held

- Exact protocol census and canonical hashing distinguish changed membership,
  order, payloads, windows, booleans and floating-point stand-ins for integers.
- Default construction denies starts; only the finite built-in mock transport
  is admitted. This remains offline bookkeeping, without a live adapter.
- Current and strict-boundary cumulative budgets, five-second global spacing,
  three active requests, window cutoff and post-cutoff draining pass the suite.
- Unknown, boolean, nonfinite and negative JSON costs retain the $5 reservation,
  pause and cannot retry. An ordinary JSON decimal number is parsed as Decimal
  and is legitimately accepted; this is distinct from accepting a Python float
  policy/explicit charge. Explicit/conflicting billing evidence tests also pass.
- Known-zero technical retries, fixed-window retry confinement, per-slot/global
  caps, refusals, excess charges and the simulated new-settled stop pass.
- Exclusive ownership, process death, durable intent before transport, partial
  streams, bounded archives, archive collisions and torn-journal preservation
  pass. Recovered unresolved intents cannot resume automatically.
- Permanent terminal closure, partial terminal barriers, archive failure pause,
  and the explicit incomplete census pass their existing constructed tests.

## Reproduction and limits

Baseline command:

```sh
.venv/bin/python -m pytest tests/painter_family_controls_v1/test_collector.py tests/painter_family_controls_v1/test_protocol.py -q
```

Independent probes used `TemporaryDirectory`, `protocol.assignments` starting at
the synthetic `2030-01-01T00:00:00Z`, at most four protocol slots, generated solid
Pillow images, built-in mock responses and injected free-byte/creation observers.
The 350-dollar setting was only a simulation fixture. Each adverse case above
must be retained as a regression during remediation. No live route, price,
service identity, production network behavior or actual acquisition capacity was
qualified; no scientific or acquisition authorization follows from this audit.
