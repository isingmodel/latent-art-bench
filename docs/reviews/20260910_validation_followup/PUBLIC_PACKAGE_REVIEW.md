# Unpublished numerical package review — 2026-09-10

This is a bounded maintainer-run LLM security/portability audit by reviewer 3,
who also implemented the temporal-replication namespace and previously assisted
the manuscript replay. It is not external peer review, independent research
replication, media verification or evidence of public availability. The release
builder remains mutable before publication.

## Reviewed candidate and scope

- Candidate: `tmp/paper-release/core-draft-04.tar.gz`, **unpublished draft**.
- Archive SHA256: `26f3fa0c1de1bcb58f90288897334641526896a10b869fbcdaa8c7ab35d29ddc`.
- Archived builder SHA256: `c7ef7cdcc70039cbfd24338c1f7751765f400660fb97fe49dc2c5d14dd4270fc`.
- Contents: core numerical export, completed measurement extension, manuscript
  and eight figures; no pending temporal-replication outcomes.

The reviewer inspected the builder, tests, export/extension contracts, generated
CI and actual archive members. All **290 members** equal the 288 manifest-listed
files plus `RELEASE_MANIFEST.json` and `SHA256SUMS`; there are no extra/missing
members, links or unsafe member names. Every declared file hash verifies.
Text, decompressed numerical JSON, PDF text and PDF metadata scans found no
credentials, personal paths, raw artwork, local configuration or Korean drafts.
The only path-pattern match was the intentionally fictitious test fixture.
The PDF raster objects correspond to the challenge heatmap/colorbar.

Numerical portability permits finite float differences of 1e-10 absolute/relative
while preserving structure, identities, counts and decisions exactly. Every
p-value key present in the retained outputs (`p_holm`, `p_two_sided`, `holm_p`,
`raw_p`) receives exact comparison. Extension replay preserves missingness and
duration-based withholding; allowlisted delivery metadata excludes bodies,
headers and paths and retains absent fields as nulls.

CI has `contents: read`, disables persisted checkout credentials, uses verified
commit pins from the official [checkout](https://github.com/actions/checkout/commit/11d5960a326750d5838078e36cf38b85af677262),
[setup-python](https://github.com/actions/setup-python/commit/a26af69be951a213d495a4c3e4e4022e16d87065)
and [upload-artifact](https://github.com/actions/upload-artifact/commit/ea165f8d65b6e75b540449e92b4886f43607fa02)
repositories, and has no `pull_request_target` trigger or publication step.

R2's fresh-environment strict replay receipt was inspected: **96 exact checks**,
including eight byte-identical PDFs, in 53.23 seconds; zero network/process
attempts. One optional macOS `SystemVersion.plist` read was blocked and recorded.
Receipt SHA256: `961bb7e2a3d1e6e887faae2402dc908077ed6c31e2a6137fbb870d2fd22ef03b`.
That replay was run by R2, not independently duplicated by this reviewer.

## Findings and resolutions

1. **Datagram audit gap.** Draft04's guard omitted `socket.sendto`; a synthetic
   audit event passed without incrementing the network counter. No packet was
   sent. R2 added socket creation, `sendto` and `sendmsg` blocking and a test of
   five synthetic socket audit events. Instructions now describe an ordinary
   Python audit-hook I/O guard, not an OS sandbox or hostile-code containment.
2. **Unspecified supported Python.** Draft04's instructions did not name a Python
   version, while copied package metadata allowed 3.9 and unchanged computation
   uses `zip(strict=True)`. R2 now prescribes tested Python **3.13.11**, uv
   **0.9.28**, and `uv sync --locked --extra analysis --python 3.13.11`, without
   changing frozen package metadata.

The reviewer inspected both fixes and independently ran all **17 release tests**
(0.56 seconds) and namespace Ruff successfully. Resolved builder SHA256:
`d87effbe398ce6780fe2b9f75dfa23640683f2a938aacfbdf81a4a9bf1c6a6ce`;
tests: `708d9991a2157aafbc095e3e82801d707398b397851a1b8e22d378688146769a`.
Draft04 is unchanged and does **not** contain these fixes; the successor candidate
must receive its own archive hash and full replay receipt.

The verifier intentionally allows unlisted installed/runtime files such as
`.venv`, caches and new replay receipts. The reviewed archive itself contains
none. Authenticating a downloaded candidate requires checking its externally
recorded archive SHA256; the internal manifest alone is not that trust anchor.
Publication and anonymous-download verification remain pending. No outstanding
must-fix finding remains in the reviewed builder revision; this statement does
not certify later edits or an unpublished successor archive.
