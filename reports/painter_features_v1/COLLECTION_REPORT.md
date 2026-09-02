# Painter Features v1 data-collection and archive report

Status: **collection complete; scientific measurement not started**  
Collection window: 2026-09-01 22:43:41–22:43:51 UTC  
Canonical method: [`MEASUREMENT_PROTOCOL.md`](../../studies/painter_features_v1/MEASUREMENT_PROTOCOL.md)  
Approved execution: [`COLLECTION_FREEZE_3.json`](../../studies/painter_features_v1/execution/COLLECTION_FREEZE_3.json)

## 1. Result in one sentence

Four exact public-domain NGA JPEG deliveries—two Camille Pissarro and two Claude Monet works in
two metadata-matched outdoor-place strata—were acquired once, admitted, content-addressed, and
independently verified; this establishes a small auditable corpus only and does **not** establish a
painter feature.

## 2. Scope and research boundary

The collection was designed as the first controlled empirical operation beneath the standalone
Painter Features v1 measurement protocol. It was deliberately narrower than a feature study.
The reviewed authorization permitted only transport, exact-byte preservation, checksum creation,
and noninterpretive technical admission. It prohibited:

- normalization or resampling;
- feature extraction or visual-outcome inspection;
- model download or model inference;
- assignment to a future analysis partition;
- human data, external-holdout access, or image generation; and
- any conclusion about Pissarro, Monet, painter identity, style, reproduction reliability, or
  source transfer.

This boundary matters because the historical pilots showed that acquiring images, computing
features, and making a scientific painter claim are separate evidential stages. Finishing the
first stage does not imply the others.

## 3. Lessons carried forward from the previous phases

The collection plan incorporated seven concrete lessons from the prior `phase_*` and Pilot 0–3
records.

1. **Freeze identities before pixels.** The exact work, delivery URL, order, rights basis,
   expected geometry, failure actions, and output locations were fixed before any request.
2. **Normalize historical identity across schemas.** `nga:52195`, `work-nga-52195`, a source
   filename, and an IIIF UUID may denote the same work or asset. Checking only one spelling caused
   the first proposed collection to falsely label eight old Pilot 0/1 images as fresh.
3. **Keep physical work, capture, asset family, and delivered file distinct.** A second URL or IIIF
   size is not an independent reproduction. The current four assets have unknown capture ancestry
   and therefore support no reproduction claim.
4. **Treat support and attrition prospectively.** The frame is balanced by painter within two
   content strata, but it contains only one work in each painter-content cell. That is below the
   canonical floor and remains inadequate even when all four requests succeed.
5. **Make transport failure durable and terminal.** An intent is fsynced before each request. There
   is one attempt, no retry, no redirect, no replacement, and no provider or URL fallback. One
   failure would have stopped the rest of the batch.
6. **Preserve received bytes before transformations.** Raw JPEGs are stored by SHA-256 under one
   ignored workspace. The tracked ledgers retain rights, request, response, codec, dimensions,
   ICC, EXIF/XMP, content, medium, and identity metadata.
7. **State the claim ceiling first.** The collection was not allowed to inherit a claim from a
   failed or incomplete predecessor. Its ceiling is corpus preservation.

## 4. Historical-exposure audit

The old metadata census contained 194 candidate rows, but metadata exposure is not the same as
pixel exposure. A normalized pixel-exposure audit combined ignored local source filenames with
the Pilot 3 acquisition ledger and cross-checked Pilot 0–3 manifests, asset URLs, UUIDs, feature
records, and reports.

- 118 unique physical works had demonstrated historical pixel exposure.
- The exact denylist is
  [`historical_pixel_exposure_denylist.jsonl`](../../data/manifests/painter_features_v1/historical_pixel_exposure_denylist.jsonl).
- The four selected works were present only in the old metadata audit; no prior pixels, feature
  rows, matching asset UUIDs, or local filenames were located.
- The audit cannot exclude an unrecorded cross-provider visual duplicate because pre-acquisition
  byte and perceptual hashes did not yet exist.

The detailed audit is in
[`historical_exposure_audit.json`](evidence/historical_exposure_audit.json).

## 5. Frozen collection frame

The target was Camille Pissarro and the balancing hard neighbor was Claude Monet. This pairing is
used only to construct a balanced acquisition frame; it is not yet a painter-specificity test.
All four works are catalogued by the owning institution as oil on canvas, dated 1880–1891, and
available through the same NGA Open Access IIIF workflow. The NGA identifies its open-access
images for unrestricted reuse under CC0; the freeze binds the
[Open Access policy](https://www.nga.gov/artworks/free-images-and-open-access) and
[terms](https://www.nga.gov/terms-and-notices) checked on 2026-09-02.

| Order | Painter | Work | Year | Metadata stratum |
|---:|---|---|---:|---|
| 1 | Camille Pissarro | *Peasant Girl with a Straw Hat* | 1881 | `figure_in_outdoor_place` |
| 2 | Claude Monet | *Woman Seated under the Willows* | 1880 | `figure_in_outdoor_place` |
| 3 | Camille Pissarro | *Hampton Court Green* | 1891 | `populated_garden_or_park` |
| 4 | Claude Monet | *The Artist's Garden at Vétheuil* | 1881 | `populated_garden_or_park` |

The figure-dominant pair is not mislabeled as pure landscape. The exact machine-readable frame is
[`collection_frame.jsonl`](../../data/manifests/painter_features_v1/collection_frame.jsonl).

## 6. Prospective review and revision history

No network request was sent until a skeptical reviewer approved the exact design hash.

### Freeze 1 — rejected

The first proposal used eight NGA rows and checked overlap only against Pilot 2 and selected Pilot
3 identities. Independent review found that all eight had identical URLs, local bytes, and feature
outcomes in Pilots 0/1. The proposal was rejected before execution. The correction was a
provider-normalized 118-work pixel denylist and an explicit distinction between metadata exposure
and pixel exposure.

### Freeze 2 — rejected

The replacement cohort was pixel-fresh, but completed-ledger validation did not re-hash raw files,
did not require every admitted file to have a durable pre-request intent, and did not compare the
delivered JPEG geometry with the frozen source geometry. The capture label also overstated what
was known about ancestry. This proposal was also rejected before execution.

### Freeze 3 — approved

Freeze 3 corrected those deficiencies. The collector now:

- validates every bound protocol, frame, audit, denylist, simulation, dependency, and source hash;
- requires an `APPROVE` review of the exact freeze and identical scope;
- validates every ledger chain and one-to-one intent/terminal/acquired relationship;
- rechecks raw-path containment, content-addressed location, existence, byte count, and SHA-256;
- requires the exact frozen GET URL, attempt zero, and no-retry contract;
- rejects nonidentity content encoding, redirects, non-200 responses, non-JPEG MIME/codec,
  oversized or empty bodies, decode failures, and undersized files;
- requires a 1024-pixel long edge and source-aspect relative error no greater than 0.002; and
- labels capture ancestry as unknown.

The independent review approved exact freeze SHA-256
`ff8ddbc4bd0aced57292543955b901f39c6b5224dfd8b72874c14872c27ea59e`.
The review and seal are
[`collection_freeze_3_review.json`](evidence/collection_freeze_3_review.json) and
[`COLLECTION_FREEZE_3_SEAL.json`](../../studies/painter_features_v1/execution/COLLECTION_FREEZE_3_SEAL.json).
Rejected designs and reviews remain under
[`studies/painter_features_v1/old/rejected/`](../../studies/painter_features_v1/old/rejected/).

## 7. Acquisition result

All four rows succeeded on their first and only request. The run created four intents, four
admitted terminal events, and four linked acquisition records. There were zero failures, retries,
redirects, replacements, or fallback requests.

| Work ID | Delivery | Bytes | SHA-256 prefix | ICC | Aspect error |
|---|---:|---:|---|---|---:|
| `work-nga-155712` | 836 × 1024 | 399,996 | `8b77a4644b22` | embedded sRGB | 0.00022944 |
| `work-nga-46653` | 758 × 1024 | 306,319 | `85681ef01c95` | embedded sRGB | 0.00057550 |
| `work-nga-52197` | 1024 × 754 | 299,372 | `acae05ce2197` | embedded sRGB | 0.00066223 |
| `work-nga-52189` | 818 × 1024 | 361,908 | `f1ecf527790b` | embedded sRGB | 0.00039059 |

Total preserved bytes: **1,367,595**. All files decode as RGB JPEG, have embedded sRGB ICC
profiles, lack EXIF and XMP, meet the short- and long-edge requirements, and fall inside the
frozen aspect tolerance.

Raw files live under the ignored, content-addressed
`research_workspace/painter_features_v1/raw/` boundary. They are intentionally not committed.
The compact tracked evidence consists of:

- [`acquisition_intents.jsonl`](../../data/manifests/painter_features_v1/acquisition_intents.jsonl)
- [`acquisition_attempts.jsonl`](../../data/manifests/painter_features_v1/acquisition_attempts.jsonl)
- [`acquired_files.jsonl`](../../data/manifests/painter_features_v1/acquired_files.jsonl)
- [`collection_result.json`](evidence/collection_result.json)

A second invocation validated all raw bytes and ledgers, reported that every frozen row was
already admitted, and sent no request.

A final independent read-only audit rehashed and decoded all four files, checked all twelve ledger
events and reciprocal freeze/review/seal bindings, confirmed the absence of downstream analysis
artifacts, and returned no P0–P2 findings. Its compact record is
[`collection_result_audit.json`](evidence/collection_result_audit.json).

## 8. Scientific interpretation

This collection is useful as an audited starting point, but it is not a measurement result.

- There is only one work per painter-content cell, below the protocol floor of two per cell in
  each partition and workflow.
- There is one provider workflow, so source transfer is not estimable.
- There are no independently documented capture pairs, so reproduction error is not estimable.
- Capture ancestry remains unknown.
- No analysis partition has been assigned.
- No feature algorithm, perturbation test, estimator, SESOI, multiplicity tree, or inferential
  simulation has been authorized.

Accordingly, no statement such as “these are Pissarro features,” “the painters differ,” or “the
measure is robust” is supported. A future measurement operation must use a new reviewed freeze.
The earlier feasibility audit estimated that a domain-limited design with Pissarro, Cézanne,
Monet, and a broad negative; two content cells; two workflows; development and qualification
partitions; and an independent-capture subset would begin at roughly 64 physical works and 88
capture files. That is an identifiability floor, not a justified final sample size; prospective
precision simulation may require more.

## 9. Artifact reorganization

Unbound pre-reboot documents were moved, without deletion, to explicit archives:

- 14 legacy planning/method documents moved from `docs/` to [`docs/old/`](../../docs/old/);
- two superseded Painter Features v1 review documents moved to
  [`reports/painter_features_v1/old/`](old/); and
- two superseded Painter Features v1 plan documents and both rejected collection freezes remain
  under [`studies/painter_features_v1/old/`](../../studies/painter_features_v1/old/).

Frozen Pilot 2/3 protocols, learned-formal feasibility, pilot configs, reports, ledgers, scripts,
tests, and ignored research bytes were not moved. Their literal paths or hashes are part of the
historical evidence graph. This is why the repository now has a visible `old/` archive but still
retains fixed-path historical namespaces.

## 10. Bottom line and next decision

The repository now has one canonical Painter Features v1 method, one approved subordinate
collection execution, four verified raw NGA deliveries, compact provenance sufficient to audit
them, and explicit archives for unbound predecessor material. The next defensible research action
is a metadata/rights/capture-ancestry census large enough to construct a full common-support and
independent-reproduction design. Feature extraction from these four files is not the next automatic
step and remains closed until that separate design is frozen and approved.
