# User-authorized bounded retry amendment

Issued 2026-09-06 before the new research generation freeze. The user requested
retry logic for a few failed requests, and diagnosis plus a fix for widespread
failure. This supersedes the umbrella protocol's no-retry rule prospectively for
the new research collection. Historical terminal studies remain untouched.

Keep 1,008 research slots and 18 completed technical attempts. Add at most **24
technical retry attempts**, at most one per failed slot, for a study-wide ceiling
of **1,050 attempts**, including at most **612 paid attempts**. The **$75 aggregate
spending ceiling is unchanged** and includes all failures and retries. The maximum
number of successful research images stays 1,008: a successful image is never
retried or replaced. No model, provider or prompt fallback is authorized.

Retry only a completely received, explicit transient error with a known charge:
HTTP 429, 500, 502, 503 or 504 and a JSON error envelope. Wait at least 60 seconds
and honor a longer Retry-After instruction. Do not retry policy refusals,
authentication/balance failures, invalid payloads, malformed successful responses,
decode/geometry problems or an uncertain timeout. Investigate these first. An
uncertain request or unknown charge blocks further generation until reconciled.

Every retry has a new request ID, disjoint raw-response path and a create-once
child-attempt record binding the predecessor's terminal event. It runs as part of
the prospectively randomized slot policy, before proceeding to the next slot.
Keep both initial-only and first-success-with-retry analyses. Later replacements
cannot restore an earlier terminal study's randomized primary result.

Stop the collection if any route has three consecutive failed initial attempts,
or at least four failures among its last 20 initial attempts once 20 exist.
Authentication, payment, payload-contract and unexpected successful-response
failures also stop immediately. A failed retry closes that slot; it does not
trigger another attempt. Preserve all evidence, diagnose the cause and implement
the necessary fix before any successor collection. Never use retries to conceal
a systematic transport defect. The exact main orchestration and offline tests
must be committed and frozen before dispatch.
