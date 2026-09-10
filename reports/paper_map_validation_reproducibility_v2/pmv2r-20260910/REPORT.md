# Prospective fixed-map numerical release: local and anonymous replay

Date: 2026-09-10. Release **[pmv2r-20260910](https://github.com/isingmodel/latent-art-bench/releases/tag/pmv2r-20260910)**. Both fresh checks pass: all **27** v2 qualification cells reproduce exactly, the actual two-endpoint analysis and Markdown report reproduce exactly, and **75 public tests pass with zero skips** in each environment. These checks preserve the observed negative/negative contrasts and the permanently failed v1 allocation record; they do not reopen either study.

The immutable numerical archive contains **74 regular files** and **3,059,166 bytes**, SHA-256 `8688085fe001e6b45ca34f6d39a5979e3e762a2678cd5ecb8169a698defb4eb6`. Its 88-byte detached checksum hashes to `32b25e0954eb7e28d22b598ac0d41f40eafc0c1305b52d16430daceef978089f`. The bundle was built from source commit `bd3c9ca1261541f523617f9c8ed908db3acaac2d` and numerical export commit `4024d52e04104dad279b1091992ed577df052c7a`. The coordinator records history-free public root `f38da21b7ea1c49b5cb5c1678a8410c65df19733`; the anonymous check independently verifies the released asset bytes.

| Check | Fresh local archive | Fresh anonymous download |
| --- | --- | --- |
| Retained receipt | [LOCAL.json](LOCAL.json) | [PUBLIC.json](PUBLIC.json) |
| Pre-install stdlib verification | Exact 74-file inventory; no payload writes | Exact 74-file inventory; no payload writes |
| V2 qualification replay | 27 cells, 270,000 deterministic trials; exact | 27 cells, 270,000 deterministic trials; exact |
| Actual endpoint/components/report | Exact | Exact |
| Numerical-check elapsed time | 41.94 s | 40.95 s |
| Public tests | 75 passed, zero skips; 161.70 s | 75 passed, zero skips; 161.88 s |
| Post-test stdlib inventory | All 74 original payload files unchanged | All 74 original payload files unchanged |

## Anonymous acquisition and reproducible commands

The public check ran from **2026-09-10T12:04:20.221163+00:00** to **2026-09-10T12:07:50.789894+00:00**. It downloaded the archive and detached checksum through HTTPX 0.28.1 with `trust_env=False`, `auth=None`, no automatic redirect following, and a fresh cookie-empty client for every redirect hop. Each asset returned one HTTP 302 followed by HTTP 200. Every actual request was checked for the absence of Authorization, Cookie and Proxy-Authorization headers; no environment proxy was used. The receipt retains sanitized redirect locations and request-status metadata, omitting signed query strings. Dependency installation is separately recorded and is not described as an anonymous service experiment.

Before extraction, both drivers checked the fixed archive hash/size and detached checksum, all 74 member paths, regular-file types, uniqueness, canonical modes/timestamps and bounded total size. Absolute/traversal paths and links are rejected. Pre-install verification ran with Python `-I -S`. Each extracted root then received its own newly created environment:

```sh
uv sync --locked --python 3.13.11 --extra analysis --extra dev
uv run --locked python tools/paper_map_validation_release.py check --root .
uv run --locked pytest -q --import-mode=importlib \
  tests/test_paper_map_validation_release.py \
  tests/painter_map_validation_v2/test_analysis.py \
  tests/painter_map_validation_v2/test_analysis_oracle.py
```

After tests, each driver invoked the unchanged stdlib `verify(root, runtime=True)` and independently rehashed every original payload file and the archive. Logs remain outside extraction, with their hashes and complete command records in the receipts. Both use Python **3.13.11**, NumPy **2.5.2**, SciPy **1.18.1** and pytest **8.4.2** on the same macOS 26.6.2 arm64 host; NumPy reports Apple Accelerate BLAS/LAPACK. Existing uv caches were available. Neither driver invoked a collection, feature extractor or formal qualification output writer. The scientific checker recomputes deterministic qualification in memory and compares saved results; the failed v1 81-cell record is retained, not resimulated here.

## Scope, provenance and limitations

These are maintainer-run LLM checks. Reviewer 2 performed the fresh local replay and authored operational study code; reviewer 1 performed the anonymous replay and authored precision code, oracle tests and the public adapter, with earlier statistical/release contributions. Neither is an independent human or institutional investigator. A fresh same-host environment and anonymous asset access establish numerical accessibility within this runtime, not cross-platform portability or independent acquisition.

The adapter permits 1e−10 absolute/relative differences for qualification floating leaves while requiring exact identities, counts, decisions and reconstructed support hashes. Here `qualification_exact=true` additionally reports exact values. Those support hashes cover floating-array bytes, and the observed analysis/report require exact replay; differences in numerical builds or platforms can therefore fail the unchanged contract. Same-Mac success does not establish compatibility elsewhere or the actual service coverage of the approximate intervals. Any hosted-platform attempt requires its own outcome record.

Public collection eligibility remains an attestation projected from locally verified receipts. Omitted source-binding bodies are provenance fingerprints, not publicly verified contents. The archive excludes private acquisition responses, pixel images, credentials, current credit balances, metadata bodies, Git history and Korean drafts. Saved raw vectors are 31 numerical features, not raw image pixels. Replay does not authenticate absent acquisition/cost/identity/timing bytes or validate capture equivalence, perceptual meaning, stationary independent repeats or an internal model mechanism. Manuscript assets are outside this numerical package.

| Retained record | SHA-256 |
| --- | --- |
| `LOCAL.json` | `0b0f1d986413953bb028c1702745c27ba9f86a7288dcc0b163ec41e6c0a48c9d` |
| `PUBLIC.json` | `515e3488e3f20413631447352724eaf57fb3d576aa99ba0d18db73f598783405` |
| Public `MAP_VALIDATION_RELEASE_MANIFEST.json` | `186f1efd018420a2cbad1c2cd8e9ba0e9ebf7792703ea88373adfd3e93357d84` |
| Public `SHA256SUMS` | `4d0a102c0c70c555431483375b6c64a77d2f18b6825adf104b80287259fb0f26` |
| Actual `analysis.json` | `11159b1b9b15dc6be3b1b3e03659298a8bed6bcd38a52aa992f16d2f26833386` |
| Actual `REPORT.md` | `57470eb939a4120e632690be4e4b6e55ee15deb87f93b7a585cb62ca3e52b498` |
| Anonymous driver | `be2689776fd42e12a2bcec91285f03a34de0f29ba72c13c772bac895ffd12b93` |
