# Final English manuscript assets — 2026-09-10

The current iteration is complete. The **39-page English paper**, its standalone
source bundle and detached checksums are published as additive assets of
[pmv2r-20260910](https://github.com/isingmodel/latent-art-bench/releases/tag/pmv2r-20260910).
The two existing numerical assets and every preceding release remain unchanged.
The final manuscript source commit is
`2969a31acb197ed5ae8fe728c2a0ae13f4c7c36e`.

| Published asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `paper.pdf` | 483283 | `cbf3f99595de28334e40ec7ae9693e01bda79cf3fe5998a77e189bc01f1e104e` |
| `paper-source.tar.gz` | 1373757 | `a5ac0ff241afce1fc6d45486ece89f1c72c20ec16aa812bd797cc3c1feb8833e` |
| `paper-assets-SHA256SUMS` | 162 | `5327dc58051844e8378631e7d5324902502079ced0a5f60e84416f923219c0f6` |

The archive contains exactly 16 regular files: the English TeX, bibliography,
nine figures, geometry presentation renderer and its stored numerical input,
license, README and internal checksums. The TeX hash is
`57504560780e74f60263ea182fc8099be61616fd90549b24246f2b853bae8840`.
The 14 committed inputs match the final source commit; the README and internal
checksum list are generated packaging documents. Deterministic tar/gzip output
was checked during packaging. Pixels, responses, credentials, literature full
text, other local drafts and full repository history are excluded.

## Build and access checks

[LOCAL_PAPER_BUILD.json](LOCAL_PAPER_BUILD.json) records a fresh archive extraction
and standalone Tectonic 0.17.0 compilation. All 39 pages match the canonical PDF
in extracted text and 100-dpi rendered pixels. The compiled PDF bytes differ;
the receipt makes no byte-identical compilation claim. The geometry presentation
reproduces byte for byte using the previously installed locked Python 3.13.11
environment. All 16 source files remain unchanged after these commands.

The coordinating maintainer-run LLM visually inspected the changed pages. The
preceding complete-page review, the intermediate 13-page wording comparison and
the final full-size checks of pages 24, 38 and 39 cover the final manuscript.
The final standalone comparison verifies all 39 canonical page renders. The
nine figures and bibliography are unchanged from the scored Round 4 snapshot.

[PAPER_ASSETS.json](PAPER_ASSETS.json) records HTTP 200 anonymous downloads of all
three published assets, matching their expected hashes, lengths and GitHub
digests. Requests used no authorization header, cookies, credential store or
environment proxy. All archive members and internal checksums pass, as does
the geometry presentation check on the downloaded copy. This access check does
not claim a second fresh compilation: its bytes match the separately compiled
local archive.

The first access-check driver used the system Python 3.9 and stopped after
successful downloads because that runtime lacks filtered tar extraction. Its
downloaded bytes remain in the ignored `anonymous-01` directory. A fresh
`anonymous-02` check used the locked Python 3.13.11 runtime and passed without
weakening archive checks. Neither attempt modifies scientific evidence.

## Scientific and review scope

The final text incorporates the prospective fixed-map result and the completed
[separate Ubuntu diagnostic](../../paper_map_portability_diagnostic_v1/pmpdv1-20260910/REPORT.md).
All 27 qualification failures in that diagnostic are reconstructed support
hashes. Other qualification floating differences are at most 3.56e-15; observed
differences are at most 2.67e-15. Displayed scientific results remain unchanged,
while exact observed JSON/report comparisons fail. This supplemental numerical
comparison does not turn the original strict Ubuntu attempt into a pass.

The latest scored nine-aspect mean is **8.9333**, compared with **8.9000** in
Round 3. These scores apply to the
[Round 4 snapshot](../../../docs/reviews/20260910_substantive_revision/ROUND4_SNAPSHOT.json),
not automatically to subsequent wording and diagnostic corrections. All three
reviewers are maintainer-run LLM subagents with disclosed later research or
writing involvement. They are not independent human or institutional reviewers.
The user changed the stopping instruction to finish this iteration and stop
after a score increase. That condition is met; the original above-9 goal is
not met. There is no fifth review. The fixed-support portable proposal remains
deferred before qualified implementation, support export or replay.

Final whole-tree validation passes **1,970 offline tests in 499.08 seconds**
and Ruff. The historical evidence audit at `be5cc37` passes **2,902 checks with
zero failures**, preserving its two old acknowledgements. Logs remain under
`tmp/paper/final-iteration-{offline-tests,ruff,evidence-audit}.log`.
Earlier exact nine-figure checks remain applicable because those inputs and
renderers did not change. This publication work adds no scientific reanalysis,
image acquisition, feature extraction or generation. It supplies numerical and
presentation access; capture validity and replication by separate investigators
remain unperformed.
