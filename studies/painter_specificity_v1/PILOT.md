# GPT Image 2.5 transport qualification

Authorized by the user's 2026-09-10 instruction to add both released variants and
include them in the painter-specificity experiment. This is a new scope; no
terminal census or frozen experiment is reopened. Pilot images are excluded from
scientific analysis and allocation choices will not use their feature outcomes.

Two requests, one each for `gpt-image-2.5-flare` and
`gpt-image-2.5-sunburst`, use the standard Image API payload with medium quality,
1024-square size and PNG output. The local adapter forwards the exact requested
ID; no fallback model is allowed. Keep the raw responses, request timestamps,
payloads, service source commit and hashes. No feature extraction in this pilot.
At most two requests overlap with starts at least five seconds apart. A model
rejection triggers transport diagnosis, not substitution. The pilot adds no
OpenRouter charge and never queries a credit balance.

Official model source, read 2026-09-10:
https://developers.openai.com/api/docs/guides/image-generation

Adapter source: openai-oauth commit `d0a390f`, dedicated loopback port 10533.
Offline verification: 42 server tests pass (one live test skipped), all three
packages typecheck; changed TypeScript files pass Biome. Existing forwarding
checks exercise all four accepted model IDs and assert unchanged upstream payloads.
