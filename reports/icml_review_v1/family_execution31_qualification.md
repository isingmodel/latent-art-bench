# Local raw31 extraction and replay qualification

19 September 2026. **Synthetic qualification only; no new service observations.**

The new `execution31.py` executes the retained historical measurement method on
every successful terminal image, explicitly using short side512 and crop0.
It compiles the hash-verified historical source bytes in a fresh module, decodes
hash-verified image bytes, records normalization metadata and writes raw float64
features in the fixed31-coordinate order. It neither fits a new scaler nor
executes a learned encoder. Outputs are create-once; a computation failure
cannot produce a complete execution receipt or become collector missingness.

The receipt is a local record, not execution attestation. The separate replay
operation recomputes every image and compares normalized-pixel hashes, complete
normalization metadata and raw little-endian float64 bytes with zero tolerance.
It verifies actual installed runtime fingerprints, fixed source bindings and
the same terminal census. Compression bytes need not reproduce; numerical
contents must reproduce exactly. Cross-runtime tolerance is not implemented.

## Independent review and limitations

A sub-agent independently reviewed the implementation without changing files.
It confirmed the direct source-byte execution and exact replay path, while
identifying two provenance boundaries:

1. Freshly compiled method code still imports installed dependency modules.
   A focused probe replaced `skimage.color.rgb2lab` in-process while leaving
   recorded package versions unchanged. Extraction and replay therefore run in
   separate fresh Python processes for the retained qualification. In-process
   API callers must trust their dependency modules; version fingerprints are
   explicitly not dependency-code attestation.
2. A nondefault project root could claim hashes for helper files that were not
   actually imported. The executor now requires its installed project root and
   checks implementation module paths against the claimed files. A regression
   test rejects copied roots.

This is not a hostile-host security proof, remote service attestation or an
independent scientific review. The general supplied-array loader and combined
reporter retain their explicit false execution-authentication flags. This new
raw31 replay result is separate evidence; it does not authenticate CLIP/CSD.

## Retained verification

- **295 tests pass**, including19 new execution/replay tests; Ruff passes.
- The new tests actually extract a nonuniform synthetic image. They cover a
  monkeypatched ordinary extractor import, rewritten raw vectors with updated
  hashes and receipt claims, float32 substitution, modified normalization,
  runtime, census identity, axes and pixels, failure, empty successful census,
  default simulation denial and create-once behavior.
- The final [three-image fixture](../painter_family_controls_v1/offline_execution31_v2/result.json)
  executes RGB PNG, embedded-sRGB PNG and EXIF-rotated JPEG inputs. All three
  rows exactly reproduce in a separate process. All original fixture pixels,
  collector records, manifests, vectors and receipts are retained in its
  compressed archive. Only its own temporary directory was removed.
- Both parent and child qualification processes block socket network operations.
  The mock $0.01 charges, $350 policy and100GiB storage return are fixture values.
  They are not financial authorization or actual spending.
- The initial successful fixture is preserved under `offline_execution31_v1`,
  including its exact earlier executor source. It predates the root guard and
  explicit dependency-code limitation; v2 is the current qualification.
- All15 prior qualification-v1 bindings and all31 qualification-v2 bindings
  remain unchanged. Earlier code and scientific evidence are preserved.

## Reproduction

```sh
uv run --locked pytest -c pytest-paper.ini -q tests/painter_family_controls_v1
uv run --locked python scripts/qualify_family_execution31_offline.py --output reports/painter_family_controls_v1/offline_execution31_NEW
```

The output directory must be new. The archived fixture can also be extracted
to a new scratch directory and replayed with the CLI using its externally
retained terminal and execution digests. This checks all rows, not a sample.

## Goal boundary

The ICML manuscript remains8 main/46total pages; latest independent scientific
scores remain4/4/4, mean4.0. No new review is warranted by this synthetic work.
The remaining empirical step requires fresh requests and actual learned-model
execution. The existing strict cumulative$120 ceiling, historical$112.293676
accounting, pending$350 proposal and missing40GiB destination remain unchanged.
Current free space is approximately4.63GiB. The same resource/authorization
conditions persisted across the preceding qualification and reporting goal
turns and this execution turn. Offline progress cannot supply the missing
independent observations or the requested scientific score.
