# Pilot 3 preprocessing-determinism technical amendment

This amendment repairs a container-level determinism defect detected after the first 12
development AIC acquisitions and before development feature extraction, P3-T07, external
unsealing, P3-T11, P3-T14, or analytic generation. It does not change the frozen corpus,
URLs, delivered dimensions, providers, partitions, pixel transform, input domain, or the
sealed external holdout. Pilot 2 remains unchanged.

The incident is immutably recorded at commit
`582fc07ad34e90f0ba585f88a7e3efce8236780c` in
`reports/pilot_3/evidence/preprocessing_determinism_incident.json`. The original browser
authorization, HTTP/browser journals, acquisition rows, raw CAS objects, and normalized
CAS objects remain append-only and are never rewritten. Historical validation is allowed
only through the exact incident checkpoint and the exact Git blobs at
`83f4d9a679f45324367654f64eb735a4f1a5f874`; it is not a caller-selectable compatibility
mode.

## Effective v2 normalization

Pilot 3 applies the same EXIF orientation, embedded-ICC-to-sRGB pixel conversion, alpha
compositing, optional long-side resize, and RGB conversion as the frozen base config. It
then detaches the RGB pixels from Pillow metadata and serializes a PNG containing exactly
one first `IHDR`, one or more contiguous `IDAT` chunks, and exactly one final `IEND`, with
no ancillary chunks. Every output is decoded and checked as metadata-free RGB.
The authorization also freezes the active Python/Pillow codec stack, including zlib,
libjpeg, JPEG 2000, LittleCMS, libtiff, and WebP versions; a different runtime fails the
amendment verifier before normalization or admission.

The immutable `configs/pilot_3/phase_a.json` remains the base v1 contract. Every v2
browser/HTTP attempt, acquisition, effective acquisition view, feature row, determinism
probe, and P3-T07 artifact binds both its base-config hash and the explicit v2 effective
contract hash plus the technical-amendment authorization hash.

## Three-commit recovery sequence

The chronology has three strict boundaries: an implementation commit, a later amendment
commit, and a still-later revalidation commit. First commit the implementation, this
amendment text, and tests. Then, with a clean
worktree at that commit, create the prospective authorization without image, browser,
feature, external, or network I/O:

```sh
PYTHONPATH=src .venv/bin/python scripts/import_pilot3_browser_acquisition.py \
  --root . authorize-preprocessing-amendment
git add reports/pilot_3/evidence/preprocessing_determinism_amendment.json
git commit -m "Authorize Pilot 3 deterministic PNG remediation"
```

Only after that authorization is committed and clean, recompute all 12 historical raw
objects twice in memory, require exact RGB-pixel equality, require the exact difference set
to be only `work-aic-45240`, and append the 12-row revalidation ledger:

```sh
PYTHONPATH=src .venv/bin/python scripts/import_pilot3_browser_acquisition.py \
  --root . revalidate-normalization
git add artifacts/pilot_3/development_normalization_revalidations.jsonl
git commit -m "Record Pilot 3 normalization revalidation"
PYTHONPATH=src .venv/bin/python scripts/import_pilot3_browser_acquisition.py \
  --root . verify-preprocessing-remediation
```

The normalized CAS is intentionally local/ignored. Its bytes remain create-once and are
verified against the append-only ledger on every use; do not force-add image blobs. Eleven
rows have disposition `revalidated_unchanged`. Only `work-aic-45240` has disposition
`superseded`, and only its effective normalized path/hash changes. The old CAS and all
original evidence remain required and preserved.

Until both the amendment and the complete revalidation ledger are committed and clean,
all acquisition resume, browser prepare/import, extraction, determinism-probe, P3-T07,
external-unseal, and downstream execution entry points fail closed. After resolution, each
remaining AIC work must follow the already-authorized per-work sequence: prepare and fsync
the exact browser start, perform one fresh download into its dedicated empty directory,
then reconcile that one completed file. The generic acquisition command cannot create an
AIC HTTP route.
