# Painter capture audit v1 — stage R0 metadata feasibility

**Status:** prospective; collection must wait for the maintainer's review and commit of this protocol and `candidates.json`. Namespace: `painter_capture_audit_v1`. Run: `pcav1-20260910`. Date: 2026-09-10.

## Question and scope

Can retained provenance leads establish two separately attributed photographic capture events of the **same physical painting**, suitable for designing a later capture-robustness comparison? This audit examines only the five existing controlled-reference identities in `candidates.json`. It does not estimate capture variability, validate perceptual style, test the paper's numerical effects, or qualify Protocol 2.1's broader reproduction study.

The prior four-work audit at `studies/painter_responsiveness_v1/CAPTURE_FEASIBILITY.md` remains unchanged. No terminal cohort is reopened or rescued. Candidate order was chosen from retained metadata, without feature values, omission influence, image appearance, or desired review scores. This is a maintainer-run LLM audit with prior paper, design, and writing involvement; it is not an independent human or institutional review.

Stage R0 permits public **metadata text only**. Artwork images, thumbnails, image-bearing PDF downloads, external-holdout access, image acquisition/inspection, feature extraction, generation, credentials, login, and messages to institutions/contributors are outside scope. Do not open embedded media or image-service URLs. Reading an image URL as text does not authorize requesting it.

## Fixed order, activation, and attempt limits

1. Audit priorities 1, 2, and 3 in that order, completing the disposition of each before proceeding. Each identity has at most **three attempts**, including redirects and failures. Unused attempts cannot move to another identity.
2. Priorities 4 and 5 activate only if the first three yield **new actionable capture/master evidence in a source family also present in their retained routes**: the Rlbberlin/Commons own-work lineage or the Cézanne-catalogue-to-institution lineage. Record the triggering evidence and why it applies before opening priority 4. A reachable page, repeated own-work assertion, artwork date, or catalogue entry alone is insufficient. A Flickr-only finding does not activate unrelated source families. Audit 4 then 5, each with the same three-attempt cap; otherwise both remain `not_activated`.
3. The maximum is therefore **15 attempts**. Each outbound metadata request is one attempt, even if it fails, is cancelled after intent, times out, returns an error/nontext response, or only reports a redirect. A requested redirect destination is a separate attempt charged to the same identity. No automatic redirects or retries are allowed. No parallel requests, searches, batch APIs, pagination, or broad harvesting.
4. Begin from that identity's inventory URLs. Within its remaining cap, a redirect or directly linked metadata/provenance page may be followed only if it concerns the same painting, its named image source, or its exact capture/master lineage. Log the originating page and reason. Do not invent alternate endpoints, search for another artwork, or follow media links. Access-denied responses end that route; do not bypass controls.

The listed URLs are an allowed set, not a requirement to spend every attempt. Prefer the source-credit route and the institutional/master route needed to resolve the missing facts. Stop an identity once qualified, conclusively ineligible, or unable to progress within its cap. Stop the run when all activated identities are disposed, the global cap is reached, or the operator stops; interruption does not erase attempts or authorize a replacement run.

## Text transport and append-only record

Before the first request, record the committed Git revision and SHA256 hashes of this protocol and inventory in `data/manifests/painter_capture_audit_v1/pcav1-20260910/start.json`. Verify that both committed inputs are clean. Record an attempt intent **before** every outbound request in `attempts.jsonl` in the same directory, followed by its outcome. An unmatched intent consumes its attempt and is reported as interrupted; never silently retry it.

Use a transport with automatic redirects and retries disabled. Inspect response headers before reading the body; accept only HTML, plain text, XHTML, or JSON metadata. Do not read a nontext body. Do not execute scripts or fetch page subresources. A minimal one-off standard-library GET is sufficient; no new scientific package or collector framework is required. Tools that conceal request/redirect accounting must not be used for this capped audit. A failed tool invocation after intent counts even if transmission cannot be established.

Each record includes attempt number, candidate identity, UTC time, exact requested URL, parent/redirect URL if applicable, purpose, tool/transport, status or error, response content type, reported redirect location, and retained-text path/hash when a text body is read. A malformed or apparently binary response is not rendered or interpreted as an image. Text responses, including failures, may be retained under `research_workspace/painter_capture_audit_v1/pcav1-20260910/`; do not alter earlier research bytes. No authentication is supplied. Source excerpts and conclusions must distinguish metadata assertions from independently established facts.

## Metadata qualification rules

A `metadata_qualified_pair` requires affirmative cited text for **all** of the following:

- Exact common physical-work identity, supported by accession/authority identifiers; a same-title work, replica, printed reproduction, or unidentified detail does not qualify.
- Two separately attributed photographic/scan events, with photographer/institution and capture-event date or event/master identifier sufficient to distinguish the events. A new master identifier qualifies only with evidence that it represents a new capture, not a derivative export. Own-work credit plus file/upload date alone is insufficient.
- A documented ancestry relationship that supports distinct acquisitions rather than mirrors, crops, re-encodings, scans of the same prior photograph, or republished institutional files. Distinct websites and resolutions do not establish this. Distinct events are not a claim of statistical independence between workflows.
- Metadata supports comparable full views of the same physical surface and identifies no intervening restoration or object change. Unknown view/condition comparability remains unresolved; stage R0 cannot verify pixels.
- Exact candidate-file locators and recorded rights/attribution terms permit a later review of acquisition eligibility. A painting's public-domain status alone does not establish the reproduction's rights.

The retained reference capture must be one member of a qualified pair for a direct replacement of that reference. Two other qualified captures are recorded separately and cannot authenticate the retained image by association. No pixels are acquired even after metadata qualification; a later measurement experiment requires its own authorization, protocol, and applicable gates.

## Terminal deliverable

Write a compact `reports/painter_capture_audit_v1/pcav1-20260910/REPORT.md` with all five candidate dispositions, attempt totals and failures, source citations with short supporting excerpts, and explicit unresolved facts. Allowed dispositions are `metadata_qualified_pair`, `one_event_supported`, `pair_claim_unresolved`, `no_qualifying_evidence`, `ineligible`, and `not_activated`; explain any interrupted/incomplete investigation separately. Give the number of qualified pairs, including **zero**, and whether the retained reference is a member. Preserve attempt records and source hashes.

There is no hypothesis test, power claim, numerical feature analysis, automatic follow-on acquisition, or score reassessment. A negative audit remains a valid feasibility result. Do not substitute transform sensitivity, painter classification, extra identities, or another unbounded search for the stated question.
