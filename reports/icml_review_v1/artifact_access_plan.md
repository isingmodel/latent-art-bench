# Exact-pixel artifact access and request-timing plan

Read-only local audit of the six-configuration study, completed 19 September
2026 (KST). No upload, publication, external resource creation, image download, or pixel
transformation was performed. The separately authorized new timing diagnostic is
listed in section 7. No frozen inputs or manuscript files were edited.

## 1. Feasibility: all required originals are retained

All 1,878 originals exist locally, have distinct SHA-256 values, and match their
recorded hashes. The total original-pixel payload is **4,355,822,632 bytes**
(4.36 GB decimal; approximately 4.06 GiB). All selected references and development
works have disjoint work identities. None of these pixel files is tracked by Git.

| Cohort | Count | Bytes | MiB | Actual formats | Audited source crops |
|---|---:|---:|---:|---|---:|
| Generated | 1,008 | 2,079,642,175 | 1,983.30 | 840 PNG; 168 JPEG | None |
| Primary reference | 649 | 1,710,001,212 | 1,630.78 | 645 JPEG; 3 PNG; 1 WEBP | 90 |
| Development scaler | 221 | 566,179,245 | 539.95 | 220 JPEG; 1 PNG | 41 |

The generated paths all end in `.png`, but the 168 Nano Banana 2 files contain
JPEG bytes. A package must preserve the original bytes and declare actual media
type; changing the extension alone does not convert a file. Decoders already
inspect the content. Generated IDs are not contiguous through 1007: the retained
14-scene subset preserves IDs from the earlier 16-scene allocation, ending at
`psv2-1151`. Enumerate the manifest rather than constructing numeric filenames.

The 1,008 gzip-compressed response bodies add **2,073,483,308 bytes**. Each has
only `created`, `data`, and `usage` at top level; each data item has `b64_json` and
`media_type`. They contain no hosted image URL. Every uncompressed response hash
matches its manifest. Original request authorization headers are not stored in
these response bodies. For an eventual release, use an explicit file allowlist;
do not copy the workspace or environment wholesale.

I also decoded the base64 payload in every retained response in memory and
verified that all 1,008 recovered image hashes match `image_sha256`. This proves
local recovery from those retained responses, not external availability.

## 2. Exact membership and join schema

All paths below are relative to `/Users/fred/dev/generative_art_diff`.

### Generated cohort

Base directory: `data/manifests/painter_specificity_v2/psv2-20260911/`.

- `requests.jsonl`: exactly 1,008 rows. Keys: `id`, `model`, `scene`,
  `original_scene`, `content`, `arm`, `repeat`, `payload`. The payload holds the
  exact text and requested provider/configuration. The six arms are `free`,
  `generic`, `claude_monet`, `alfred_sisley`, `camille_pissarro`, `paul_cezanne`.
- `collection.json`: `outcomes` has exactly 1,008 successful records, one attempt
  each. Join by `id`; retain `image_path`, `image_sha256`, `response_path`,
  `response_sha256`, `width`, `height`, `reported`, `ended_at`, `attempt`.
- Actual image path pattern:
  `research_workspace/painter_specificity_v2/psv2-20260911/images/<id>.png`.
- Actual response pattern:
  `research_workspace/painter_specificity_v2/psv2-20260911/responses/<id>-a1.json.gz`.
  `response_sha256` is the hash of the **decompressed response body**, not the
  gzip container. A new package inventory should additionally hash the gzip file.
- `attempts.jsonl`: 2,016 start/end events. Start fields include `id`, `attempt`,
  `started_at`, `payload_sha256`, `paid`; end records correspond to `outcomes`.
- `measurements.jsonl`: exactly 1,008 records with `id`, `image_sha256`, `status`,
  `values[31]`, `square_values[31]`, and `normalization`.
- Preserve `freeze.json`, `measurement_receipt.json`, the original analyses, and
  their bound dependencies. The corrected-reader freeze is separately at
  `data/manifests/painter_specificity_measurement_v1/psmv1-20260911/freeze.json`.

### Primary reference cohort

- Membership:
  `data/manifests/painter_feature_generation_v2/pfg2-method-20260905/confirmation_features.jsonl`.
  Select `status == "measured"` only: **649 of 653** rows. The four historical
  failed records are not part of this paper's pixel cohort.
- Features/identity: `image_id`, `painter_id`, `raw_sha256`, `values[31]`,
  `normalization`, `feature_sha256`, and role/stage fields.
- Join `image_id` to `work_id` in
  `data/manifests/painter_feature_generation_v2/pfg2-renderings-r2-20260905/acquisitions.jsonl`.
  Do not package all 1,193 acquisition rows as if they were evaluated references.
- Acquisition fields include `raw_path`, `raw_sha256`, `bytes`, `format`,
  `width`, `height`, `has_icc`, `url`, `licence`, `source_kind`, `source_sha1`,
  `source_timestamp`, `source_width`, `source_height`, and acquisition events.
- The exact raw path is content-addressed and extensionless:
  `research_workspace/painter_feature_generation_v2/pfg2-renderings-r2-20260905/raw/<raw_sha256>`.
- Full/square variants for these same 649 are at
  `data/manifests/painter_specificity_v2/psv2-20260911/reference_windows.jsonl`.
  Join its `id` to the reference `image_id`; `image_sha256` equals `raw_sha256`.

### Development cohort

- Membership:
  `data/manifests/painter_feature_generation_v2/pfg2-method-20260905/development_features.jsonl`.
  Select **`role == "development"`**, yielding 221 rows. The file has 312 rows;
  its other 91 `historical_development` rows must not enter this scaler archive.
- Join `image_id` to the same acquisition table's `work_id`; original raw path
  and hash use the same extensionless content-addressed store as references.
- Preserve the neighboring `scaler.json`, including development feature binding,
  coordinate center/scale, and equal-painter weighting rule.

### Painting-region and label audit

- `reports/painter_reference_quality_v1/audit_monet.json`: 398 `records`.
- `reports/painter_reference_quality_v1/audit_others.json`: 472 `records`.
- Combined 870 unique records exactly cover 649 reference + 221 development.
- Core fields: `image_id`, `painter_id`, `role` (`reference` or `development`),
  `raw_path`, `raw_sha256`, `region_box[4]`, `region_note`, `flags`, `inspected`,
  `visual_class`, `original_content_class`, `class_note`.
- `reports/painter_reference_quality_v1/measurements.json` has 870 `records`
  keyed by `image_id`, with corrected `values[31]` and `normalization`.
  The 131 cropped records have `pixel_box`, dimensions, `removed_area_fraction`,
  `normalized_sha256`, and `reused_original: false`; the 739 unchanged rows reuse
  original features. Include the corresponding analysis/scalers and source plan.
- The audit's `tmp/reference-quality/...` contact sheets are local presentation
  aids, not canonical image sources. Regenerate them from the selected originals
  and recorded boxes if useful; do not make recovery depend on ignored temp files.

## 3. What full-frame, square, and cropped pixels mean

Canonical pixels are the original payload bytes. Derived arrays can be rebuilt;
there is no need to package separately compressed copies of every variant.

1. **Full frame:** `features.normalize(path, short_side=512)`, in
   `src/latent_art_bench/painter_feature_generation_v2/features.py`. It applies
   EXIF orientation; valid ICC-to-sRGB conversion; compatible missing-profile
   sRGB assumption; and aspect-preserving Lanczos resize without upsampling.
2. **Center-square sensitivity:** `measure_one` in
   `src/latent_art_bench/painter_specificity_v1/workflow.py` selects the central
   512-by-512 window **after** full-frame normalization. This exists for 1,008
   generated and 649 primary references. Generated sources are already square.
3. **Audited painting region:** `normalize_region` in
   `src/latent_art_bench/painter_reference_quality_v1.py` interprets `region_box`
   after EXIF orientation, converts color, rounds normalized boundaries using
   `half_up`, crops, and resizes to a 512-pixel short side. The 90 reference and
   41 development crops are recorded decisions, not automatic masks. Other
   works use `[0,0,1,1]` and retain their full frames.

The `normalized_sha256` fields hash **little-endian float64 RGB array bytes**
(`rgb.astype("<f8").tobytes()`), not a PNG/JPEG file. Do not compare a rendered PNG
file hash with these array hashes. Source bytes plus locked dependencies,
normalization code, boxes, and expected array hashes are the reproducible unit.
Original raw-byte hashes must remain separate from derived-array hashes. Of the
870 historical source captures, 318 report ICC profiles and 552 do not.

## 4. Rights/provenance records and actual gaps

The original **paintings** and the distributed **digital reproduction files**
are separate metadata objects. The recorded source-file license distribution is:

| Recorded license | Primary reference | Development | Total |
|---|---:|---:|---:|
| Public domain | 567 | 196 | 763 |
| CC0 | 19 | 4 | 23 |
| CC BY-SA 4.0 | 42 | 15 | 57 |
| CC BY-SA 3.0 | 4 | 0 | 4 |
| CC BY-SA 2.0 | 2 | 2 | 4 |
| CC BY 4.0 | 2 | 1 | 3 |
| CC BY 3.0 | 9 | 2 | 11 |
| CC BY 2.5 | 1 | 0 | 1 |
| CC BY 2.0 | 3 | 1 | 4 |
| **Total** | **649** | **221** | **870** |

Thus **84 source files** have CC BY or CC BY-SA metadata (63 reference, 21
scaler), and 35 of these have audited crops. A package should carry per-file
license/credit records and identify transformations, rather than labeling the
whole cohort public domain. This audit records metadata, not a legal determination.

### Rich metadata is already retained

`frame.jsonl` under `pfg2-frame-20260905` supplies `surrogate.commons_filename`,
`surrogate.metadata_sha256`, `item_qids`, `labels`, `object_urls`, collections,
accessions, and origin URLs. For **all 870** selected sources, the stored
`metadata_sha256` exactly matches `digest(candidate["media"])` from:

`data/manifests/painter_feature_generation_v1/broad_media_followup_publication_r2/candidates.jsonl`.

The digest implementation is in
`src/latent_art_bench/painter_feature_generation_v2/artifacts.py`.
The matched `media` records contain `artist_text`, `credit_text`,
`license_short_name`, `license_url`, `description_url`, `canonical_title`,
`permission`, `usage_terms`, `copyrighted`, `restrictions`, `metadata_urls`,
`raw_response_sha256`, and image/source metadata. Subset these 870 matches into
an attribution file; do not discard the recorded source text or its provenance.

All 84 CC BY/BY-SA records have nonempty `license_url`, `credit_text`, and Commons
`description_url`. Two lack `artist_text` and need explicit attribution review:

- Reference `wikidata:Q17492310`, CC BY-SA 4.0:
  `File:La Seine à Port-Villez - v1890- Claude Monet - Musée d'Orsay.jpg`.
- Development `wikidata:Q17492316`, CC BY-SA 4.0:
  `File:Monet - La Seine à Vétheuil, 1879.jpg`.

Across all 870, five lack `artist_text`; one public-domain record,
`wikidata:Q19820375`, lacks `credit_text`. All have Commons description links and
usage terms. All recorded `restrictions` fields are empty. A nonempty artist or
credit string does not itself establish that the correct photographer/reproducer
attribution has been identified. The later acquisition metadata requests fetched
only `LicenseShortName|Restrictions`; use the richer matched candidate record,
not that reduced metadata snapshot alone. Generated-output redistribution terms
are not stored as per-image rights records in this cohort; that is a separate
release-documentation question, not something image hashes can establish.

### Manuscript wording: no blanket public-domain assertion found

In the frozen manuscript and matching working TeX:

- `icml.tex:60-61` (PDF p.9, Impact Statement) says **“The reference examples have
  recorded public-domain metadata”**. It says examples, not the complete cohort.
- `icml_appendix.tex:430-435` (PDF p.16, Appendix D) restricts the Figure 1
  selection to water-organized examples with recorded public-domain status.
- `icml_main.tex:83-87` (PDF p.2, Section 3.1) says source metadata supports
  selection and rights records; it does not call all sources public domain.

All four Figure 1 references in `paper/example_selection.json` are indeed marked
`Public domain`: Q10346982, Q104774055, Q104773676, Q19682454. **I found no
literally incorrect blanket public-domain statement in this frozen manuscript.**
A useful clarification would explicitly distinguish the four displayed examples
from the full cohort's per-file licenses in the reproducibility appendix. Avoid
“correcting” the currently accurate example-specific claim into an assertion that
those examples have CC licenses.

## 5. Safe portable-package options

### A. Original-layout local bundle (most direct exact replay)

Assemble a new local directory or tar archive with the required selected files at
their **existing repository-relative paths**. Include the 1,878 originals, compact
manifests, matched 870 metadata records, audit/box records, feature/scaler files,
locked dependencies, and the relevant code/test/protocol dependency closure. Hash
an inventory of every copied file. Include optional gzip responses in a separate
part: they duplicate generated pixel payloads but allow response-provenance checks.

- Originals alone: 4.36 GB plus small code/manifests.
- Originals plus recorded responses: 6.43 GB plus small code/manifests.
- Keep `.env`, credentials, machine state, unrelated experiments, ignored temp
  files, and historical editorial transports out of the allowlist.
- `.gitignore` explicitly excludes `research_workspace/` and common image
  extensions; compact JSON/JSONL evidence is tracked. Do not force-add multi-GB
  pixels to Git merely to make the paper reproducible.
- Record the package inventory/archive checksum and exact code revision. Existing
  frozen source bindings must continue to match; a copied path remapping must not
  overwrite original manifests. An extraction adapter can restore original
  relative paths into a clean checkout.
- Local availability and creation of a local archive do **not** establish public
  accessibility. The manuscript must retain its public-access limitation until a
  reviewed package is actually made retrievable.

Suggested new index schema (one row per original):

```json
{
  "cohort": "generated|reference|development",
  "id": "request-id or wikidata work-id",
  "archive_relative_path": "preserved repository-relative path",
  "sha256": "original payload hash",
  "bytes": 123,
  "media_type": "image/jpeg",
  "source_manifest": "path",
  "source_record_key": "id or work_id",
  "source_url": "recorded URL or null",
  "source_page_url": "Commons description URL or null",
  "recorded_license": "per-file metadata or null",
  "attribution_record": "key into matched media metadata",
  "variants": [
    {"kind": "full_512", "normalization_record": "path/key"},
    {"kind": "center_square_512", "feature_record": "path/key"},
    {"kind": "audited_region_512", "audit_record": "path/key"}
  ]
}
```

Only list applicable variants; development sources have no primary square-window
variant. Keep reconstruction array hashes in the referenced records. This is a
proposed packaging schema. Section 8 records the subsequently materialized local
inventory; no pixel archive has been built.

### B. Manifest plus recovery tools (smaller but not currently complete public access)

- Historical sources: all 870 have source URLs and Commons filenames; 500 are
  original file URLs and **370 are provider-rendered thumbnails**. Re-download
  must match the recorded raw SHA-256, byte count, and dimensions. A changed
  thumbnail or a higher-resolution original is not the same input and must not
  silently replace it. This audit did not probe live URLs or verify current
  remote recovery. Prefer retaining the exact captured bytes.
- Generated sources: all responses contain base64 payloads, so retained local
  response archives can recover the generated originals exactly. Those responses
  are themselves currently local; rerunning prompts cannot guarantee the same
  pixels and no seed was supplied.
- A public recovery-only route would need a measured success census for all
  selected files and a retained fallback for missing/changed bytes. Current
  filenames and URLs alone do not meet that standard.

### Checks after a local package is assembled

In a clean extraction, first verify the new file inventory, then run:

```text
make specificity-audit
make reference-quality-images-check
make example-images-check
make specificity-check
make review-check reference-quality-check
```

`reference-quality-images-check` verifies all 870 source hashes and re-extracts
131 cropped regions; it does not re-extract all unchanged primary full frames.
For a complete independent measurement exercise, add a **new non-overwriting**
verification driver for all 1,008 generated, 649 reference, and 221 development
originals and their applicable variants. `measure` commands are one-shot writers
and should not be used to overwrite the frozen measurement manifests. Array and
feature equality should be checked under the locked environment with declared
numeric tolerance, while original payload hashes must match exactly.

## 6. Request-order audit and design constraint

The 1,008 start events exactly follow `requests.jsonl`; every request succeeds on
attempt 1. `assignments()` in `painter_specificity_v1/study.py` uses seed
2026091017, permutes scenes, then permutes all 72 model/arm/repeat combinations
within each scene. The v2 study selects 14 scenes before feature outcomes.

Observed compact scene order:
`8, 13, 7, 4, 9, 0, 6, 11, 10, 1, 2, 12, 5, 3`.
Every block has 72 starts. The first-to-last-start span per block ranges from
572.9 to 1,468.9 seconds (median 635.8). Request latency ranges from 9.0 to
88.5 seconds (median 18.5). Within-cell repeat gaps range from 5.0 to 1,198.9
seconds (median 188.8). Recorded repeat 1 occurs later in 271 of 504 pairs and
earlier in 233. The recorded repeat index is **not** chronological order.

Global collection time is confounded with scene because scenes are consecutive
blocks. A trend of scene score against global time cannot separate content from
service drift. Randomized within-block order supports a limited within-cell
sensitivity, not a general claim of temporal independence. Start times, rather
than completion order, should define chronology.

## 7. Implemented retrospective timing sensitivity

Authorized new files:

- `studies/painter_request_timing_v1/PLAN.md` — written before outcome analysis.
- `src/latent_art_bench/painter_request_timing_v1.py`.
- `tests/painter_request_timing_v1/test_timing.py`.
- `reports/painter_request_timing_v1/analysis.json` and `REPORT.md`.

For each model's 84 scene/arm cells, fit
`delta_z = b * delta_t + error`, using signed repeat differences and start-time
gaps in minutes. The 31-vector slope is common to all arms. This removes stable
scene/arm means and is invariant to joint repeat-label reversal. Evaluate each
scene with slopes fitted on the other 13; compare squared-error prediction with
zero difference. Full refit after each scene deletion assesses influence.

| Configuration | Held-out gain (%) | Full-refit scene-deletion range (%) |
|---|---:|---:|
| GPT Image 1 | -0.86 | -1.87, -0.62 |
| GPT Image 2 | -3.38 | -3.92, -0.87 |
| GPT Image 2.5 Flare | -2.28 | -3.82, -1.19 |
| GPT Image 2.5 Sunburst | -2.62 | -3.01, -2.05 |
| Nano Banana 2 | -0.72 | -2.02, -0.43 |
| FLUX.2 Max | -1.19 | -1.80, -0.99 |

The common linear within-cell drift model adds no held-out predictive value in
this diagnostic. This does **not** establish service independence, stationarity,
or absence of nonlinear/arm-specific/shared-state effects. Negative gain is not
a significance test. Overlapping folds are dependent; deletion ranges are not
confidence intervals. Primary scores were not detrended. The report retains
model-specific slope/effect sizes, all folds, pair identities, and input hashes.

Verification: four focused tests passed; Ruff passed; exact replay passed using
`uv run --locked python -m latent_art_bench.painter_request_timing_v1 check`.

## 8. Materialized reviewable inventory (no pixel copies)

The next revision now has concrete local release-content records:

- `reports/icml_review_v1/artifact_inventory.json`: exactly 1,878 selected original
  paths, hashes, byte counts, detected media types/dimensions, cohort membership,
  and attribution keys. Historical rows also retain audited region boxes.
- `reports/icml_review_v1/artifact_attribution.json`: exactly 870 matched historical
  source records, including license/credit fields, Commons source-page links,
  captured and original source URLs, and complete canonically hash-bound richer
  media metadata. No generated-image rights are inferred from historical licenses.
- `scripts/check_icml_artifact_inventory.py`: `--write` creates the two files only
  if neither exists; default mode reconstructs them deterministically and verifies
  every selected original hash against the files. The selected-pixel path allowlist
  excludes response archives, environments, secrets, and unrelated cohorts.

Replay with `uv run --locked python scripts/check_icml_artifact_inventory.py`.
The script never copies, uploads, or downloads pixels. Its output explicitly
states local-only availability and does not claim a public archive or verified
live URL recovery. The inventories bind their generator and source manifests.
