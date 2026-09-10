# Terminal map-precision numerical release

The [pmrv1-20260910 public release](https://github.com/isingmodel/latent-art-bench/releases/tag/pmrv1-20260910) passes both fresh
local and anonymous-download replay. The archive is **2,725,809 bytes**, contains
**18 files**, and has SHA256
`00e82c31c2b3dd5719c324a1d26b882e3dc98ebbfd491122062df5ccde62cd9f`.
Its build source is `35aef913cfedafc7de2c746fd68b061b05f21b2c`; the
unchanged qualification source is `eb70ab8c30019b4b283366c170f8bdaf1405a023`.

| Check | Fresh local | Anonymous public download |
| --- | --- | --- |
| Archive/checksums and exact 18-file inventory | Passed | Passed before installation |
| Fresh locked Python 3.13.11 environment | Passed | Passed |
| Complete 81-cell numerical qualification | Exact values | Exact values |
| Public offline tests | 73 passed | 73 passed; no skips |
| Stopping decision | `stop_inferential_proposal` | Unchanged |

[LOCAL.json](LOCAL.json) records the first fresh replay.
[PUBLIC.json](PUBLIC.json) records the independent download path, commands,
runtime and log hashes. Anonymous retrieval used HTTPX with `trust_env=False`,
no Authorization or Cookie headers, and a new client for every redirect hop.
The downloaded archive matches the local receipt's checksum. Regular-file
membership, safe paths, the detached archive checksum, manifest and SHA256SUMS
were verified before installing dependencies; stdlib verification ran with
`-I -S`. The extracted package received a new environment with
`uv sync --locked --python 3.13.11 --extra analysis --extra dev`.

Public replay called the unchanged numerical qualification in memory and checked
all 81 cells; it did not invoke the scientific create-once writer or change its
stored results. The retained report matched its renderer. Public tests then
passed, and a final inventory/binding check confirmed the package was unchanged.
Logs and downloaded bytes are retained outside extraction under
`tmp/paper-map-release/numerical-anonymous-01/`.

Both runs used the maintainer's Mac, `macOS-26.6.2-arm64-arm-64bit-Mach-O`, Python
3.13.11, NumPy 2.5.2 and SciPy 1.18.1. They are
fresh environments, not separate machines or investigator replications. The
anonymous replay was performed by a maintainer-run LLM agent who implemented
qualification/variance and release components and contributed earlier reviews.

The comparison contract permits 1e-10 absolute/relative differences for finite
floating results while retaining exact structures, counts, identities, seeds,
hashes and decisions. **Every numerical value matched exactly here.** Each
`support_sha256` hashes reconstructed floating-array bytes, so exact support-hash
equality can require matching arithmetic/platform even where other floating
results meet tolerance. No broader cross-platform claim is established.

The package retains the failed v1 qualification: every allocation failed its
baseline Q half-width criterion despite passing coverage. Replay does not change
that result, validate actual service uncertainty, authorize collection, or
establish capture, perception or latent style. Any separately disclosed v2
proposal is outside this immutable release. The numerical package contains no
paper assets, raw pixels, preflight metadata bodies, current credit balance,
credentials, Git history or Korean drafts. Omitted DESIGN and old geometry
freeze/receipt bodies have provenance fingerprints only; public replay does
not verify absent bodies or authenticate absent source images.
