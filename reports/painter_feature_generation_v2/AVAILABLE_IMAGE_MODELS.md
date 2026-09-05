# Available image-generation models: access and research suitability

Historical access-stage snapshot. The subsequent
[completed empirical analysis](EMPIRICAL_ANALYSIS.md) supersedes the operational status and
unexecuted-work statements below; the access measurements themselves remain unchanged.

Assessed 2026-09-05. Deliverable: analysis report, not a prototype paper.
Scope: models available through the specified local OAuth setup and the already registered
local baseline. This is not an exhaustive market survey or a painter-fidelity benchmark.

## Bottom line

**The current Codex credentials work. Both `gpt-image-1` and `gpt-image-2` requests returned
decodable image bytes. Neither satisfied the requested size/quality contract.** Therefore the
current route is usable for exploratory image generation, but is not yet qualified for a
controlled comparison of those two underlying models.

Use GPT-Image-2 as the main candidate for the next experiment and GPT-Image-1 as the explicitly
requested comparator. Keep SD-Turbo as a pinned, inexpensive local baseline, not the sole basis
for conclusions about contemporary image generators. This selection follows the documented
product roles, not an empirical finding about painter reproduction.
[OpenAI's model guidance](https://developers.openai.com/cookbook/examples/multimodal/image-gen-models-prompting-guide#model-summary)
recommends GPT-Image-2 for new workflows and positions GPT-Image-1 primarily for legacy compatibility.

## Models and what is actually established

| Candidate | Documented / local contract | Observed access | Research interpretation |
|---|---|---|---|
| SD-Turbo | Pinned checkpoint; local weights; registered 512×512, one step, guidance 0, controlled seeds | Previously registered 2,000-request run is ongoing | Useful reproducible distilled-model baseline; not representative of all current models |
| `gpt-image-1` | Previous OpenAI text/image-to-image model; local proxy accepts this exact alias | One HTTP 200 response containing a PNG | Requested alias is known; actual snapshot and parameter compliance are not established |
| `gpt-image-2` | Current OpenAI image generation/editing model; public documentation lists snapshot `gpt-image-2-2026-04-21` | One HTTP 200 response containing a PNG | Primary candidate, but the OAuth response does not attest that snapshot |

The [GPT-Image-1 model page](https://developers.openai.com/api/docs/models/gpt-image-1) documents
image generation and editing. The [GPT-Image-2 model page](https://developers.openai.com/api/docs/models/gpt-image-2)
documents flexible sizing and a dated snapshot. These public API descriptions do not prove that
the separate Codex OAuth backend exposes identical controls or routing.

The [pinned SD-Turbo model card](https://huggingface.co/stabilityai/sd-turbo/blob/b261bac6fd2cf515557d5d0707481eafa0485ec2/README.md)
describes a distilled Stable Diffusion 2.1 research model, recommends 512×512 generation and
guidance 0, and acknowledges lower quality/prompt alignment than SDXL-Turbo. Its local checkpoint
and software are hash-bound; reproducibility across different hardware is not assumed.

The specified proxy currently accepts only the two exact GPT Image aliases, even though other
image models exist in OpenAI's public documentation. Its `/v1/models` implementation appends
these aliases to the authenticated text-model catalog. Listing is therefore not an entitlement
test, and distinct requested names do not by themselves prove distinct underlying weights.

## Measured access experiment

The [prospective access protocol](../../studies/painter_feature_generation_v2/MODEL_ASSESSMENT_PROTOCOL_1.0.md)
registered exactly one request per alias, with the same neutral red-circle prompt, `n=1`,
`quality=medium`, `size=1024x1024`, `output_format=png`, and an opaque background. The prompt has
no painter name, and neither output enters the painter study. No retry or aesthetic selection
was performed. Requests ran in fixed model order; one observation per model is not a latency
benchmark.

| Observation | `gpt-image-1` | `gpt-image-2` |
|---|---:|---:|
| HTTP status | 200 | 200 |
| Request-to-response latency | 14.016 s | 13.539 s |
| Requested size / quality | 1024×1024 / medium | 1024×1024 / medium |
| Decoded PNG dimensions | 1254×1254 | 1254×1254 |
| Response-reported quality | low | low |
| Decoded mode / opacity | RGB / opaque | RGB / opaque |
| Returned model/snapshot identifier | absent | absent |
| Response-reported input / output tokens | 20 / 229 | 20 / 229 |
| Satisfies registered output contract | no | no |

Source: [response diagnostics](../../data/manifests/painter_feature_generation_v2/pfg2-image-access-20260905/response_diagnostics.json),
derived offline from the retained HTTP bodies and
[sealed access receipt](../../data/manifests/painter_feature_generation_v2/pfg2-image-access-20260905/assessment_receipt.json).
The two image hashes differ. That demonstrates different returned files, not different models.
The provider's `low` label is metadata, not a measured visual-quality score.

The terminal receipt records `invalid_output` and zero **contract-valid** generated images.
That is not a refusal or authentication failure: post-hoc decoding confirms two returned images.
The terminal receipt is unchanged; the separate diagnostic explains the discrepancy rather than
retroactively accepting outputs that violated its contract. Raw response bodies, including the
base64 image bytes, remain intact in the ignored research workspace.

## Authentication and transport findings

The checkout is `dev/openai-oauth` under the user's home directory, not the initially suggested
home-level `openai-oauth`. The source revision inspected was
`0a664bcc8e09649fcdd558e0bfbdd6447b85bca2`.

The existing port-10531 process started on August 30, before that checkout's September 1 image
and authentication update. It returned an expired-token error. The configured auth path was
already the Codex auth file; a freshness check found the on-disk access token unexpired, and a
fresh client using current source authenticated successfully. This supports a stale running
process as the operational explanation; the old process's in-memory token was not inspected.

A separate current-source instance on `127.0.0.1:10532` successfully handled the sealed image
requests. The existing service and its replay state were not restarted or modified. Credentials
were loaded by the proxy, never copied into this repository, printed, or sent in a localhost
client header. No public paid-API fallback was used. The proxy forwards to the Codex OAuth image
route, not the public API-key image route. This is the user's community-maintained proxy, not an
officially documented public API transport or a promise of unlimited subscription quota.

Source inspection shows that the image payload is forwarded without the text-Responses
normalization step. The proxy's two existing offline generation-forwarding tests also passed,
including assertions that `medium` and `1024x1024` reach the outgoing request unchanged.
These checks make local payload rewriting an unlikely cause of the observed mismatch. The
remaining inference is that the upstream route did not honor those controls in these calls;
its internal routing and reason for the change are not known.

## Consequences for a defensible analysis

1. **Separate model comparison from service comparison.** Until routing is documented or
   otherwise attested, label conditions by requested alias plus route, date, and actual returned
   settings. Do not describe them as verified independent model snapshots.
2. **Do not silently repair the parameter mismatch.** Downsampling 1254-pixel images does not
   make them native 1024-pixel, medium-quality generations. A future experiment must first
   verify the intended controls or prospectively define the observed service behavior as its
   target. Preserve requested and returned values separately.
3. **Keep a common measurement scale.** A three-way comparison can use 512-pixel short-side
   normalization without upsampling. This controls analysis scale, not native-generation quality
   or acquisition texture. A GPT-only 1024-pixel sensitivity would require its own frozen method.
4. **Do not assume seed matching.** This OAuth experiment supplied no seed and established no
   reproducible seed contract. Future pairing can use template and scheduled repetition, not
   asserted shared latent noise across aliases or with SD-Turbo.
5. **Retain the scientific safeguards.** Use all 16 templates and five conditions, preserve all
   failures/refusals/duplicates, and keep confirmation sealed until the model/route contract and
   measurement method are fixed. The access images provide no evidence of painter specificity,
   distribution coverage, copying, or equivalence.

The [official Image API guide](https://developers.openai.com/api/docs/guides/image-generation)
distinguishes direct image-model selection from Responses tool orchestration. For this study,
direct selection is preferable when the route genuinely exposes it. The current proxy's fixed
alias whitelist does not accept the dated GPT-Image-2 snapshot string, so public snapshot
availability cannot be assumed to solve local routing uncertainty.

## Scale, cost, and next experiment

Start with transport qualification, then a separately frozen exploratory painter grid if the
service behavior is acceptable. One complete block is 80 images per alias, or 160 for both;
this would be exploratory, without repetition-based confidence intervals. The full existing
25-block design would require 2,000 requests per alias, or 4,000 total. Do not enlarge the run
based on an attractive prefix, and do not reuse an exploratory grid as unopened confirmation.

The OAuth route's remaining quota and billing treatment were not established. For context only,
the [public API output-price table](https://developers.openai.com/api/docs/guides/image-generation#calculating-costs)
lists medium-quality 1024-square output estimates of $0.042 for GPT-Image-1 and $0.053 for
GPT-Image-2: $84 and $106 respectively for 2,000 outputs, plus input costs. These are not prices
charged by the tested subscription route and do not apply to its unexpected low-quality responses.
No paid API spending was initiated.

The immediate research limitation is now control/identity verification, not lack of Codex
credentials. This report completes the available-model access assessment; the full empirical
painter comparison remains unexecuted. No draft manuscript, fidelity ranking, or reproduction
claim is produced.

## Project evidence and reproducibility

The 1,193-work frame and its 658 confirmation assignments remain unchanged. Replacement Commons
rendering metadata completed all 191 requests and registered a rendering for every work; that
replacement image-download stage has not started. The earlier original-image acquisition remains
terminal and its partial bytes are retained. SD-Turbo generation continues under its original
2,000-request freeze; an unfinished prefix is not reported as a completed study.

Read-only verification:

Validation on 2026-09-05: Ruff passed; **298 offline tests passed**; the v1 evidence audit passed
2,902 checks with zero unacknowledged failures; the v2 audit passed 1,525 checks with zero failures.
The v2 count includes the then-current SD-Turbo ledger prefix and grows while generation runs;
it is not a terminal-generation certificate. The proxy's two focused offline forwarding tests
also passed. Mock test responses are not included in the measured access results above.

```bash
uv run --locked --extra analysis --extra learned ruff check .
uv run --locked --extra analysis --extra learned pytest -q -m "not live"
uv run --locked --extra analysis --extra learned latent-art-bench verify-evidence
uv run --locked --extra analysis --extra learned latent-art-bench paper-study audit
```

Completed access runs cannot be rerun in place. A new access run needs a new ID, predecessor
binding, clean committed inputs, and a new freeze. All analysis is operator/LLM-assisted; no
institutionally independent review is claimed. Two previously acknowledged historical v1 input
mismatches remain unchanged and do not excuse any new discrepancy.
