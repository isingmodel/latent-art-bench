# Available image-model assessment — protocol 1.0

Issued 2026-09-05 after the maintainer requested GPT-Image-1 and GPT-Image-2 through
the local openai-oauth proxy, and replaced the draft-paper deliverable with an analysis report.
This is a new auxiliary experiment, not an amendment of any running generation contract.

## Scope and authorization

Assess documented capabilities, actual local access, transport controls, reproducibility, and
fitness for the painter-feature experiment. Documentation recommendations are not measured
painter-fidelity results. SD-Turbo remains a previously registered local baseline; its running
ledger, parameters, outputs, and denominator must not be changed to implement this assessment.
Do not open protected real-image features or generate a manuscript for this assessment.

The maintainer explicitly offered the localhost OAuth image route. Use that route only:
`http://127.0.0.1:10532`, an isolated instance of the current proxy code using the same Codex
auth file. The existing server on port 10531 predates the source update and reports an expired
token; a fresh client using the current source authenticated successfully. Do not restart the
existing server or clear its replay state. Never print, copy, or export credentials, use a public
paid API fallback, change the user's proxy, pool accounts, or bypass provider limits. Login,
if needed, requires the user's action. Existing subscription quota is not unlimited capacity.
Only boolean credential-presence/freshness metadata was inspected; the proxy itself handles
bearer-token loading and transport to its fixed upstream.

## Bounded prospective access experiment

Before transport, bind clean committed protocol, code, environment lock, and exact requests.
Record the external proxy repository commit and hashes of its public source files, without
recording an absolute workstation path or auth-file contents.

1. GET `/health` once, then GET `/v1/models` once. Retain both responses and HTTP status.
2. If either check fails, or both exact image aliases are not listed, terminate with access
   unresolved and zero image attempts. A healthy server or static alias list alone is not a
   successful generation. An expired-token response does not mean the account lacks the model.
3. Otherwise POST `/v1/images/generations` once for `gpt-image-1`, then once for `gpt-image-2`.
   The order is fixed for transport verification, not a randomized quality comparison.
4. Use exactly: prompt "A single red circle centered on a plain white background, no text.";
   size `1024x1024`; quality `medium`; output_format `png`; background `opaque`; `n=1`.
   No seed, reference image, prompt rewrite, moderation override, or aesthetic selection.
5. Maximum two image attempts per run. No automatic retries, including on timeout, HTTP 429,
   refusal, or ambiguous completion. If the first model produces an authentication or quota
   failure, do not submit the second request into the same known blocker. Mark it unattempted.
6. Retain exact response bytes, latency, allowlisted response headers, image SHA-256, full decode,
   actual dimensions, and any returned model identity. A requested alias is not a verified
   snapshot. Base64 response images only: do not follow output URLs or redirects.

Timeout: 30 seconds for readiness, 240 seconds for an image; maximum response 64 MiB;
minimum free disk 5 GiB. Environment proxies and HTTP redirects are disabled. One writer and
one execution per run. If interrupted after an attempt, do not repeat it in place. Any later
attempt is a new run ID, disjoint outputs, and a binding to the predecessor's terminal receipt.
Interrupted runs first need an explicit terminal record; an incomplete prefix is not a result.

## Interpretation and next empirical comparison

These at most two synthetic images test transport only. They are not active-study images and
cannot rank artistic quality, style reproduction, feature distributions, or prompt adherence.
Report separately: documented support, proxy implementation support, authenticated catalog,
successful generation, parameter compliance, and research qualification.

A subsequent exploratory painter comparison needs a separate prospective request freeze using
all 16 existing templates and all five conditions, common normalization, fixed quality/resolution,
and explicit repetition and quota ceilings. Keep all failures and duplicates. Without a seed
contract, pair by prompt and scheduled repetition only; do not claim paired latent randomness.
Do not reuse a model's exploratory outputs as unexposed confirmatory evidence. A full two-model
study would require 4,000 image attempts at 25 repetitions; authorization to verify access is not
authorization for an unbounded run. No inferential winner or equivalence claim comes from this
access assessment. The analysis report must clearly separate completed checks from proposed work.

All work here is operator/LLM-assisted. No institutionally independent review is claimed.
