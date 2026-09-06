# Technical pilot contract — 2026-09-06

This prospective Stage C contract permits exactly 18 technical generation attempts:
two painter names × three literal scene sentences × three routes, one image each.
`pilot.json` fixes the scene text. Prefix each scene with `An oil painting by
{painter}. `, for `Claude Monet` then `Paul Cezanne`. Within each scene, dispatch
Nano Banana 2, FLUX.2 Max, then the OAuth `gpt-image-2` alias. All pilot images are
excluded from research outcomes. No feature extraction or favorable-image selection
is permitted. Decode only to inspect container integrity, dimensions and metadata.

## Routes and evidence

`pilot_endpoints.json` records the authenticated-free public endpoint observations
and binds their retained raw responses. Google uses `google/gemini-3.1-flash-image`,
provider `google-ai-studio`, `resolution=1K`, `aspect_ratio=1:1`, `n=1`. BFL uses
`black-forest-labs/flux.2-max`, provider `black-forest-labs/us-3`, `aspect_ratio=1:1`,
`output_format=png`, `n=1`. Both pins use `allow_fallbacks=false`. BFL's endpoint
does not advertise a resolution field; its returned dimensions must be measured.
Do not silently add unsupported parameters, rewrite prompts or enable grounding.
Unreported provider-side rewriting remains unknown.

Both paid routes use the dedicated `https://openrouter.ai/api/v1/images` endpoint.
The local alias uses `http://127.0.0.1:10532/v1/images/generations`, requests
1024×1024, medium quality, opaque PNG and one image. Bind the inspected proxy source
commit, files and process identity before dispatch. The alias does not attest an
underlying model snapshot. No key is sent to the loopback route.

## Spending and execution

The user's later instruction confirms **$75 as the study spending ceiling** and
states that account replenishment has been configured. The observed ~$50 account
balance is a dated preflight observation, not the authorization ceiling. This
contract supersedes the maintainer's interim proposal to use a $45 ceiling.
Do not spend the remaining $25 without further instruction.

The endpoint listings price Google's output image tokens at $0.00006 each and BFL
output at $0.07 per megapixel. A 1K Google image is expected to cost about $0.0672;
BFL's documented default is 1024×1024 and its megapixel unit is 1024² pixels. These
are estimates. Record the dedicated API's `usage.cost` as actual returned billing.
Budget all study generation ledgers together, reserving **$5 before every paid
request** as a deliberately conservative allowance for complete-request cost.
Never dispatch when accounted cost plus that reserve exceeds $75. An unknown cost
holds the reservation and stops subsequent generation. A returned cost above $5
also stops the worker. This is a client accounting guard; the API does not expose
a per-request dollar cap, so it cannot guarantee against arbitrary provider
misbilling. Do not infer a zero cost from missing usage on a successful response.
Explicit fully received client rejection envelopes use the Image API's stated
non-billable failure rule. No paid calls preceded this pilot.

The maximum is 1,026 study attempts, including at most 588 paid attempts; these 18
technical attempts consume that allocation, including failures. Use one serial
writer for all new-study generation. Persist and fsync each intent before POST.
No automatic retries, fallback, redirects or remote output-URL fetches. Retain
compressed original responses, including failed or partial bodies, with raw and
stored hashes. Maximum response 64 MiB; timeout 240 seconds; at least 15 seconds
between dispatches; at least 5 GiB plus the response allowance free before each
dispatch. An uncertain in-flight attempt is never blindly redispatched. API keys
and Authorization headers must not enter evidence or logs.

Complete the planned inventory if failures are fully resolved, except stop on
authentication, quota/rate-limit, cost, storage or uncertain-outcome guards. A
terminal run is never reused. Any required successor must have a new identity,
disjoint paths, explicit binding to predecessor evidence and a prospective change
contract; it is not an undeclared replacement sample.

## Qualification for the main study

Publish all 18 dispositions, returned costs, latency, image geometry, encoding and
reported render fields. Choose settings only from technical compatibility and cost.
Require at least five decodable ≥512-short-side outputs out of six for each route,
with every paid cost resolved and the projected research cost plus 25% headroom
within $75. Retain every failure; no topping up this pilot. Main research requires
its own frozen contract and request inventory, regardless of pilot success.
If exact rendering cannot be matched, specify a separate OAuth service comparison
and matched paid-route comparison. Do not claim matched geometry from request text.

## Sources

- [OpenRouter dedicated image API](https://openrouter.ai/docs/guides/overview/multimodal/image-generation):
  capability discovery, provider pins, embedded image response, cost and failure billing.
- [Google pricing](https://ai.google.dev/gemini-api/docs/pricing): 1K image-token estimate.
- [BFL pricing](https://bfl.ai/pricing?category=flux.2): megapixel definition.
- [BFL output dimensions](https://help.bfl.ai/articles/8916739058-what-aspect-ratios-and-output-dimensions-are-supported):
  default dimensions and maximum resolution.

These sources were inspected on 2026-09-06. Actual endpoint responses are retained
separately; observed performance or price is not a permanent provider guarantee.
