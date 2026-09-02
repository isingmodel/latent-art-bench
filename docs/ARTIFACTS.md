# Artifact retention policy

The repository contains both compact committed evidence and large ignored local bytes. Their
directory names overlap for historical reasons, so Git ignore status alone does not mean a
file is disposable.

## Canonical tracked material

Preserve and review normally:

- source, tests, configs, documentation, and compact reports;
- Painter Features v1 historical frames, denylist, chained collection ledgers,
  freeze/review/seal records, and compact result evidence;
- Painter Feature Generation v1 protocols, future R0/R1/R2/M0/G0/G1/C0 freezes and seals,
  compact manifests, complete-population assignments, population-calibration vectors, auxiliary-
  reproduction-census manifests, hashes, reviews, and reports;
- `data/manifests/pilot_3/`;
- committed JSON/JSONL ledgers directly under `artifacts/pilot_3/`;
- the 320 Pilot 2 per-attempt receipt sidecars under
  `artifacts/pilot_2/.generation_attempts.jsonl.attempt_rows/`; and
- Pilot 2 downsampled visual-QC sheets under `reports/pilot_2/visual_qc/`.

The Pilot 2 receipts and QC sheets look generated but are intentional recovery and audit
evidence. Do not collapse or regenerate them during general cleanup.

## Ignored but valuable local evidence

Archive before removing:

- `outputs/pilot_1/` and `outputs/pilot_2/` generated PNGs;
- manifest-backed real/generated derived files under `artifacts/pilot_0/` through
  `artifacts/pilot_2/`;
- `data/pilot_0/source/` museum images;
- `artifacts/pilot_3/real_raw/`, `real_normalized/`, and `met_r2/`;
- `artifacts/models/sd2-base-vae/` pinned model weights;
- `artifacts/sources/kim-art-history/` pinned source checkout;
- `tmp/pdfs/`, which legacy Pilot 3 Lee-replication code still addresses directly; and
- `research_workspace/painter_features_v1/raw/`, containing four content-addressed NGA JPEG
  deliveries (1,367,595 bytes) from Collection Freeze 3.

Some of these bytes are copyrighted or expensive to reproduce. Their hashes are retained in
compact evidence, but the repository does not distribute them.

A Git commit or tag preserves only tracked history, not this full evidence graph. Before a
machine migration or broad local cleanup, create a separate checksum inventory and archive of
the ignored media, content-addressed stores, model/source artifacts, and outputs that must
remain byte-verifiable.

## Safe disposable state

The following may be removed whenever no process is using them:

- `.pytest_cache/`, `.ruff_cache/`, and `__pycache__/`;
- `.venv/`, after validation, because `uv.lock` can rebuild it;
- inactive zero-byte `*.lock` files;
- `artifacts/synthetic-dry-run/`;
- smoke/template outputs that are not referenced by a manifest; and
- unreferenced one-off diagnostics in `tmp/`.

Delete exact targets only. Do not use `git clean -xfd` and do not recursively delete
`artifacts/`, `data/`, or `outputs/`: each contains a mixture of tracked records and ignored
research bytes.

## Active reboot boundary

Historical Painter Features v1 uses the ignored `research_workspace/painter_features_v1/` root.
The active Painter Feature Generation v1 Protocol 2.0 uses the separate ignored
`research_workspace/painter_feature_generation_v1/` root. It contains exploratory metadata, the
completed fixed-seed audit's 165 content-addressed raw responses (about 51 MiB), the terminal broad
R1 responses, and the completed broad R2 census's four raw responses (1,163,447 bytes); compact
hashes, events, candidate manifests, and limitations are tracked. No active-study image,
eligibility derivative, normalized array, feature vector, registered generation request, generated
output, or result exists yet.

The broad-media follow-up R1 additionally retains one ignored content-addressed HTTP 200 response
and one lock file. Its tracked three-event ledger is terminal because the successful provider body
also carried an unexpected `Retry-After` header. It has no candidate manifest or execution receipt;
do not delete, retry, or splice its partial response into another census.

The metadata-audit layer may retain exact request intents, raw provider responses, hashes, terminal
receipts, and a compact non-admission candidate manifest. Raw responses remain ignored where their
size or terms make redistribution inappropriate. A metadata row never increments the admitted-work
or downloaded-image count. Every frozen source must reach its declared terminal condition; a target
count, favourable prefix, provider substitution, or later top-up is not a terminal rule.

Later R1 acquisition bytes must stay beneath the same ignored workspace. The tracked counterpart is
one compact physical-work/capture graph containing authority IDs, rights receipts, provider asset
IDs, canonical work IDs, capture ancestry, raw/normalized hashes, and one terminal disposition per
candidate. Multiple files, crops, mirrors, hosts, encodings, or hashes from one painting do not
create additional works. Only provenance-demonstrated independent captures enter the auxiliary
reproduction-disturbance set, and those works remain outside confirmation.

Masked 512-pixel eligibility derivatives, the two raw code streams, and adjudication imagery are
also ignored role-separated bytes. Their hashes, access events, calibration results, raw-agreement/
Krippendorff-alpha receipts, and terminal consensus are compact tracked evidence. Previously viewed
or feature-exposed works remain on a tracked denylist and are development-only. Every new eligible
work receives the fixed painter × scene × workflow 20%/20%/60% development/qualification/
confirmation assignment; no fixed 360-work quota exists in Protocol 2.0.

M0 artifacts must bind the exact normalization and three feature families, fixtures, common pooled
median/IQR transform, same-work capture results, source/crop sensitivity, margins, and whole-decision
simulations. G0 artifacts bind the supported scene groups, `T=4G` prompt census, model identity,
paired seeds, `R` selected from `{25,50,75,100}`, request order, failure policy, and analysis. G1
retains every attempt/output/hash while confirmation features remain unopened. C0 records the
one-time reference opening and complete frozen analysis.

All committed paths are repository-relative. Add an ignored runtime subdirectory only when the
corresponding reviewed freeze authorizes that stage; directory existence alone is never permission.

## Archive layout and fixed-path exceptions

Unbound legacy planning documents are archived under `docs/old/`, and superseded Painter Features
v1 material is under study/report `old/` directories. These are Git moves, not deletions.

Do not apply that cleanup mechanically to frozen Pilot 2/3 protocols, learned-formal feasibility,
pilot configs, reports, ledgers, scripts, tests, or ignored evidence. Their literal paths or hashes
are part of the historical evidence graph and must remain fixed.
