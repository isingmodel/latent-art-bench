# GPT Image API testing contract

This project uses the standard OpenAI-compatible `POST /v1/images/generations` shape documented in the [OpenAI image-generation guide](https://developers.openai.com/api/docs/guides/image-generation). The response image is read from `data[0].b64_json`, decoded without transformation, content-addressed by SHA-256, and inspected with Pillow before a call can be marked successful.

## Fixed test boundary

- The runtime and schema allowlists contain exactly `gpt-image-1` and `gpt-image-2`.
- The configured base URL is `http://127.0.0.1:10531/v1`, supplied by the user-maintained `~/dev/openai-oauth` proxy. No API key is read or sent.
- The adapter rejects a non-loopback hostname under `pilot_0`.
- The request freezes prompt, model, repetition number, requested size, quality, and output format. The API does not expose a reproducible seed for this path, so repetitions are indexed instead.
- Only HTTP 429 and 5xx responses are retried. Moderation/refusal and other 4xx outcomes are recorded without retrying.
- Requested and returned dimensions are separate provenance fields. The adapter does not assume the proxy honored `size`.
- Every call records success, refusal, retry, or technical failure. There is no visual selection step.

## Qualification boundary

`generate` normally requires both frozen measurement cards to be `pass` or `conditional_pass`. Before that real-only gate opens, only these operations are permitted:

1. mocked adapter tests;
2. `generate --dry-run`, which writes request plans without contacting the endpoint;
3. `generate --allow-unqualified-test-generation`, which accepts only prompts carrying `test_only: true` and marks every resulting call with `qualification_bypass: true`.

Bypassed outputs are engineering artifacts. They cannot be included in target-gap analysis, open the WP5 gate, support a comparison between the two models, or appear as scientific pilot results.
