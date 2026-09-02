# GPT Image API testing contract

## Compatibility shape versus actual transport

The benchmark client sends the OpenAI-compatible `POST /v1/images/generations` request shape documented in the [OpenAI image-generation guide](https://developers.openai.com/api/docs/guides/image-generation). Official model pages list that endpoint for [`gpt-image-1`](https://developers.openai.com/api/docs/models/gpt-image-1) and [`gpt-image-2`](https://developers.openai.com/api/docs/models/gpt-image-2).

That request shape does **not** mean this run used the public OpenAI API. The configured URL is `http://127.0.0.1:10531/v1`, served by the user-maintained `~/dev/openai-oauth` checkout. The running command supplied no upstream `--base-url`, so the proxy's default transport forwarded local `/v1/images/generations` requests to `https://chatgpt.com/backend-api/codex/images/generations` using ChatGPT/Codex OAuth. It did not send them to `https://api.openai.com/v1/images/generations`.

The local proxy validates and forwards the requested `model`, `size`, `quality`, and `output_format` fields. The retained responses do not echo an independently verified executed-model identity, upstream request identifier, or routing record. Consequently:

- `gpt-image-1` and `gpt-image-2` in the manifests are **requested labels**, not proof of which backend model executed;
- `/v1/models` advertising both labels proves only local discovery/allowlisting, not execution; and
- no model-to-model scientific or engineering performance comparison is permitted from these outputs.

## Fixed client boundary

- Runtime, schema, and configuration allowlists contain exactly `gpt-image-1` and `gpt-image-2`.
- The adapter requires a loopback hostname for this test-only OAuth configuration and does not read or send a project API key. The proxy separately uses the user's ChatGPT/Codex OAuth credentials upstream.
- A logical cell freezes the complete prompt record, requested model label, repetition index, endpoint, `n=1`, requested size, quality, and output format. The API path exposes no seed used by this project, so repetitions are indexed rather than claimed reproducible.
- The success path requires `data[0].b64_json`. Bytes are base64-decoded without transformation, hashed with SHA-256, written under a content-addressed name, decoded with Pillow, and recorded with actual format and dimensions.
- Requested and returned dimensions are separate provenance fields. A successful HTTP response is not treated as proof that `size` was honored.
- Within one logical call, transport exceptions, HTTP 429, and 5xx responses can be retried up to `max_retries=2`, or three HTTP sends total. Moderation/refusal and other 4xx responses are retained without an automatic retry. The separate exact-cell retry command creates a new logical attempt and never deletes the prior failure.
- Every attempt is retained as succeeded, refused, or failed. There is no visual curation step.

## Qualification and attestation boundary

Normal generation remains blocked while either required measurement card fails. A dry run may write plans without contacting the endpoint. A future unqualified generation run requires `--allow-unqualified-test-generation`, accepts only prompts marked `test_only: true`, and stamps the resulting calls as qualification bypasses.

The 41 retained attempts are older records created before the current failed cards. None has `qualification_bypass: true`, but that historical field does not make them scientifically eligible. The current [generation attestation](../../reports/pilot_1/evidence/generation_manifest_attestation.json) establishes the following narrower facts:

- all 41 legacy request identities can be reconstructed from the originating run record, exact prompt-manifest hash, resolved generation configuration, and call fields;
- all 40 successful output files still match their recorded hashes, formats, and dimensions;
- the exact frozen 40-cell request grid is resolved with no unexpected or selectively omitted cell; and
- the current qualification context is bound and both current cards are `fail`.

All 41 identities are legacy reconstructions, not contemporaneous wire-body captures. The originating runs do not bind the current card/evidence hashes, and the attestation explicitly assigns `grandfathered_engineering_only` / `scientific_eligibility.eligible: false`. It must not be read as a retroactive qualification pass.

With the scientific gate closed, downstream processing also requires explicit, separate authorization:

- `prepare-generated-features --allow-unqualified-test-preparation` verifies the attestation and full grid, then stamps each generated feature with the preparation bypass, generation-manifest hash, attestation hash, request-identity hash, call ID, and output hash;
- `analyze-pilot --allow-unqualified-test-analysis` revalidates those feature manifests, both failed qualification artifacts, the learned PCA state, generation manifest, attestation, and exact 16-cell analysis grid; and
- the report labels the outcome `scientific gate closed; engineering traversal complete`.

These bypasses authorize only `purpose: api_integration_test_only` with `scientific_claims_enabled: false`. They do not open the scientific gate.

## Retained pilot_1 run

The frozen grid contains two shared content descriptions, four named-artist variants plus one artist-free control for each description, both requested model labels, and two repetitions: `2 x 5 x 2 x 2 = 40` cells. The manifest retains 41 attempts:

- requested `gpt-image-1`: 20 successes and one moderation refusal;
- requested `gpt-image-2`: 20 successes;
- the refused `gpt-image-1` cell, `pilot1-riverside-camille-pissarro` repetition 1, succeeded on one later explicit exact-cell attempt; and
- 40/40 cells resolved to 40 unique PNG files.

Every success requested `1024x1024`. Actual outputs used nine non-square sizes, with widths 1392-1412 pixels and heights 1114-1130 pixels. Exact requested-size matches were **0/40**; requested-format matches were 40/40. The attestation therefore records the size contract as `violated`.

This is systematic upstream behavior in the retained grid, not an unresolved-cell failure. More paid retries would neither change the preserved 0/40 result nor prove the executed model identity, so this investigation makes no further image calls. Generation should resume only after a new transport can return auditable executed-model provenance and satisfy a prospectively smoke-tested size contract.

All generated-feature and distribution outputs remain engineering diagnostics. The [complete `pilot_1` report](../../reports/pilot_1/REPORT.md) contains the exact 16 named-artist cells and the paired artist-free controls; it forbids scientific style claims and requested-label model rankings.

## Proxy source provenance

The tested local proxy checkout had Git HEAD `7dbbdea0e94a5e542b0af34dcb11c5957b158bed` with uncommitted image-support changes. The commit alone therefore does not reproduce the executed proxy. The original smoke record and benchmark artifacts retain content hashes and observed request/response evidence, while the current attestation makes no claim that the dirty checkout was a released or official OpenAI API implementation.
