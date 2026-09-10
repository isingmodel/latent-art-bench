# Proposed metadata-only feasibility check

Not executed at preparation. This is standing-user-authorized account/model
metadata inspection, not a new scientific collection or permission to generate.
The parent has inspected the exact two-GET scope and will commit source/tests
before executing it. No old study or evidence is modified.

Exact proposed invocation, from repository root:

```bash
uv run --locked python studies/painter_map_validation_v1/preflight.py --receipt-id pmv-feasibility-20260910a --live-metadata
```

Exactly one GET is attempted to each of:

- `https://openrouter.ai/api/v1/credits` (existing `.env` key in its Authorization header).
- `https://openrouter.ai/api/v1/images/models/black-forest-labs/flux.2-max/endpoints` (no credential sent).

No query parameters, redirects, POST, API-key endpoint, broad model catalog,
image access, retry, proxy environment or generation call is used. Requests are
sequential, timeout 30 seconds/connect 15 seconds, maximum 8 MiB per response.
The script reuses the existing literal key loader and create-once JSON writer.
It cannot invoke the closed predecessor discovery command.

Before requests, create-once `data/manifests/painter_map_validation_v1/metadata/
<receipt-id>/started.json` records scope, HEAD, script hash and runtime. A terminal
`receipt.json` retains request times/statuses, successful raw response hashes,
the available balance as an exact decimal string, and the fixed model/provider's
pricing billable/unit/amount fields. Full account data, response bodies, credentials,
headers and exception messages are not retained or printed. An incomplete result
or interrupted directory cannot automatically resume or be overwritten.

The receipt is dated feasibility information. It does not establish immutable
backend identity, exact future billed cost, a model-generation contract, an
unexposed scientific validation or current project-ledger spending. Per-megapixel
pricing must not be read as a universal per-image charge. An absent or changed
model/provider fails this projection; no alternative endpoint/model is queried.
