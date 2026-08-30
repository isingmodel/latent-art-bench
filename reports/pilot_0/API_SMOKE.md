# GPT Image API smoke record

Date: 2026-08-29 (Asia/Seoul)

Purpose: verify the test-only image path through the user's local `openai-oauth` checkout. One neutral, artist-free prompt was sent once to each allowed model with `size=1024x1024`, `quality=low`, and `output_format=png`. Both calls used the explicit unqualified-test bypass.

| Model | Status | Retries | Requested size | Returned size | Format | Output SHA-256 |
|---|---|---:|---|---|---|---|
| `gpt-image-1` | succeeded | 0 | 1024x1024 | 1329x1183 | PNG | `074ee9bbcf59bd5122fa4e4af23b7260037bbccd8c9ae9e94201add8472d75d3` |
| `gpt-image-2` | succeeded | 0 | 1024x1024 | 1329x1183 | PNG | `983ac74fca5d86dd372184c54108f01bc91ef36d5f51beef8cdfcccce07669a4` |

The returned bytes decoded as valid PNG files, and both recorded hashes were re-computed from disk. The size mismatch is intentionally retained in provenance; the adapter does not rewrite the images or claim that the requested dimensions were honored.

## Proxy provenance

The checkout was at Git commit `7dbbdea0e94a5e542b0af34dcb11c5957b158bed`, with uncommitted image-support changes. Because the tree was dirty, the relevant tested files are identified by content hashes:

| Proxy file | SHA-256 |
|---|---|
| `packages/openai-oauth/src/images.ts` | `25ee6fe00dc96edecc3483415177071635dc9d3d51e8a55de38a608fbfa16aa4` |
| `packages/openai-oauth/src/server.ts` | `e61468ece2fe46aa6219fa61399581bc94bd220e7c3379e8ba235ef44c605622` |
| `packages/openai-oauth/src/models.ts` | `6986a184f1a1b9c983489e9cc25a887d674ec6ef98e891394f781623ae06dbb4` |
| `packages/openai-oauth-core/src/image-models.ts` | `ab0507b1768cfd051e1f82d73946d5582163fd4dd7591b371463957c6c59c66b` |
| `bun.lock` | `4b8d72638023cb6b9ce104ee049d5d3b67314fbdb4aa19f76c4a2c1c31173cb3` |

This record establishes API compatibility only. The outputs are ignored local artifacts, the measurement cards remain pending, and no comparison between the models is authorized.
