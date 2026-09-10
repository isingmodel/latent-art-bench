# Prospective correction of one technical-error qualification rule

Issued 2026-09-08 after the terminal collection receipt of `prv2-oauth-20260908`
and before any request in `prv2-oauth-recovery-20260908`.
The [v2 scientific protocol](../painter_responsiveness_v2/PROTOCOL.md), all prompts,
controls, endpoints, feature transforms, randomization order, inference and human-free
claim limits remain unchanged. This document specifies one transport correction and
one prospectively designated replacement run, not repeated collection until a
complete or favorable result appears.

## Observed failure and decision

The predecessor dispatched 50 attempts, returning 49 images and one completely
received HTTP 503 response. Its `text/plain` body was exactly these 95 UTF-8 bytes,
without a trailing newline:

```text
upstream connect error or disconnect/reset before headers. reset reason: connection termination
```

The collector's JSON-error-envelope rule did not recognize this technical response
as eligible for a retry. The maintainer stopped dispatch rather than completing an
allocation whose primary analysis was already unavailable. In-flight calls drained;
all 192 planned statuses and the terminal receipt remain preserved. The decision
used transport metadata and this error body. Successful images had not been visually reviewed, and no scientific feature
outcomes had been extracted or inspected. Automatic container decoding and
dimension checks had run as required by the transport policy. Earlier retained-data retrieval results
were available, but did not change the replacement design or hypotheses.

The user had already requested bounded retries of occasional failed requests and
continuation without human reference ratings. The correction implements that scope;
it does not require invented human evidence or additional paid access.

## Narrow correction

A response is newly eligible only when all of the following hold: delivery to the
collector is complete, the HTTP status is 503, the media type is `text/plain`, and
the retained body exactly matches the bytes above. There is no prefix, arbitrary
HTML, generic string or malformed-success exception. The response body, headers and
hashes remain unchanged. The terminal event records the exact qualification rule
and the original classifier result. The compatibility field `known_error_envelope`
then means a recognized technical-error body, including this exact plain-text form;
it does not assert that the body was JSON.

A completely received 503 does not establish that upstream computation never
occurred. This is an observable, bounded retry policy for the delivered service.
Keep the existing maximum of one identical-payload retry per slot, six technical
retries in total, two in-flight requests and five seconds between starts. Keep all
existing stop rules. Incomplete delivery, timeouts, refusals, invalid successes and
other unqualified error bodies remain ineligible. No provider, rendering parameter
or payload is changed.

## Allocation and evidence

The replacement contains 192 fresh requests under the same fixed design. It is the
sole primary intervention dataset for this continuation. Request labels are reused
for the unchanged design; the composite `(run_id, request_id)` identifies an
attempted experimental unit. Every artifact path uses the new run ID and is disjoint
from the predecessor. Do not fill missing predecessor slots or combine its successes
with the replacement. The new time period does not establish an identical hidden
service state or an independent model replication.

The correction lives in a separate source package. It reuses frozen v2 inspection,
staggered-dispatch helpers, measurement, analysis and report code where their
contracts remain unchanged. The replacement freeze binds the new implementation
and tests, this protocol, the unchanged v2 inputs, the predecessor's terminal
receipt, ledger and slot inventory, and the exact failed-response hashes. Prepare
from clean committed sources and commit the freeze before the first replacement
request. A terminal or interrupted replacement cannot resume or refill.

Measure the predecessor's 49 available images only after the replacement collection
is terminal. They remain ancillary selected outcomes, with original-grid inference
withheld. Report attempted and received totals across both runs. A missing primary
measurement in the replacement still withholds its allocated-grid inference; this
correction does not authorize another restart merely to obtain completeness.

## Commands and review

From the repository root:

```bash
uv run --locked python -m latent_art_bench.painter_responsiveness_recovery_v1 prepare --proxy-root ../openai-oauth
# Commit the replacement freeze and planned request inventory.
uv run --locked python -m latent_art_bench.painter_responsiveness_recovery_v1 collect --live --proxy-root ../openai-oauth
uv run --locked python -m latent_art_bench.painter_responsiveness_recovery_v1 measure
uv run --locked python -m latent_art_bench.painter_responsiveness_recovery_v1 check
```

The replacement uses `painter_responsiveness_v2` manifest, report and workspace
boundaries with its disjoint run ID. `measure` and `check` delegate to frozen v2
code; `check` makes no network calls or new scientific feature measurements.
The existing diagnostic report remains the predecessor's completed D0 result.
Transport and scientific recovery review is by maintainer-run LLM subagents with
coordinator checks, not independent human or institutional validation.
