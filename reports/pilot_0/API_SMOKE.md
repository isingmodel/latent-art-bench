# GPT Image API test record

Date: 2026-08-30 (Asia/Seoul)

Purpose: exercise the selected-artist test grid through the user's local `openai-oauth` checkout. One frozen riverside-landscape prompt was instantiated for Claude Monet, Alfred Sisley, Camille Pissarro, and Paul Cezanne, plus one artist-free control. Every prompt was sent once to exactly `gpt-image-1` and `gpt-image-2` with `size=1024x1024`, `quality=low`, and `output_format=png`.

All ten calls used the explicit unqualified-test bypass because the scientific qualification gate is closed. They are API artifacts, not benchmark evidence, and no output was selected or discarded by visual quality.

| Prompt target | Model | Status | Retries | Returned size | Output SHA-256 |
|---|---|---|---:|---|---|
| Claude Monet | `gpt-image-1` | succeeded | 0 | 1403×1121 | `169e16f42c52eceea69177c5e165e43e780d571240d6dcdd0b68a0256928a66b` |
| Claude Monet | `gpt-image-2` | succeeded | 0 | 1402×1122 | `493c3cc20a0521489665407e915f20d1886a35e56e66c14daa5ea0ff87ee9c49` |
| Alfred Sisley | `gpt-image-1` | succeeded | 0 | 1409×1117 | `01fb1e3a679286e3a4ffddcf9570a1e32c3df2de4b5ae0e7bb6bfaa6e685a889` |
| Alfred Sisley | `gpt-image-2` | succeeded | 0 | 1403×1121 | `d17e2de7ef5e81ec10380a616147732df17a81780d58e99759f5b1639bba77f2` |
| Camille Pissarro | `gpt-image-1` | succeeded | 0 | 1405×1120 | `233cc33a6a298aaa2143175c5ec3d4dc6f7cdc25a73a884ef8aabeefdd11c187` |
| Camille Pissarro | `gpt-image-2` | succeeded | 0 | 1403×1121 | `7f03ee603c79558301ed9514aea6ba5bce17dcd9ace46a17311948e257c6252a` |
| Paul Cezanne | `gpt-image-1` | succeeded | 0 | 1399×1124 | `8468b48d74b3547d8d8189c230a4e98809ffb514871014143ef2793eec447978` |
| Paul Cezanne | `gpt-image-2` | succeeded | 0 | 1402×1122 | `476b53265a05c545fb59a2cd66eb252e3b2bf6daf30b280bd551e55d3009ad89` |
| Artist-free control | `gpt-image-1` | succeeded | 0 | 1406×1119 | `c5a40faa266e04a1eaaef5e25522933a0abd1298d93c8c5ff9e44f7573c26a4a` |
| Artist-free control | `gpt-image-2` | succeeded | 0 | 1405×1120 | `44902f930b5161ee4455582b520c7da1029cceaf64c5b7386fcb74dfe33c4c33` |

The response bytes decoded as valid PNG files and their hashes were recomputed from disk. Requested and actual dimensions are separate provenance fields because the OAuth-backed endpoint returned landscape-oriented images despite the nominal `1024x1024` request. The complete local grid and contact sheet are under `outputs/pilot_0/api_smoke/`; generated images remain intentionally ignored by Git.

## Proxy provenance

The checkout was at Git commit `7dbbdea0e94a5e542b0af34dcb11c5957b158bed`, with uncommitted image-support changes. Because the tree was dirty, the tested implementation is identified by content hashes:

| Proxy file | SHA-256 |
|---|---|
| `packages/openai-oauth/src/images.ts` | `25ee6fe00dc96edecc3483415177071635dc9d3d51e8a55de38a608fbfa16aa4` |
| `packages/openai-oauth/src/server.ts` | `e61468ece2fe46aa6219fa61399581bc94bd220e7c3379e8ba235ef44c605622` |
| `packages/openai-oauth/src/models.ts` | `6986a184f1a1b9c983489e9cc25a887d674ec6ef98e891394f781623ae06dbb4` |
| `packages/openai-oauth-core/src/image-models.ts` | `ab0507b1768cfd051e1f82d73946d5582163fd4dd7591b371463957c6c59c66b` |
| `bun.lock` | `4b8d72638023cb6b9ce104ee049d5d3b67314fbdb4aa19f76c4a2c1c31173cb3` |

The loopback proxy health check returned `{"ok":true,"replay_state":"stateful"}`, and `/v1/models` advertised both `gpt-image-1` and `gpt-image-2` before the run.
