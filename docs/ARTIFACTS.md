# Artifact retention policy

The repository contains both compact committed evidence and large ignored local bytes. Their
directory names overlap for historical reasons, so Git ignore status alone does not mean a
file is disposable.

## Canonical tracked material

Preserve and review normally:

- source, tests, configs, documentation, and compact reports;
- Painter Features v1 frames, denylist, chained collection ledgers, freeze/review/seal records,
  and compact result evidence;
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

## Reboot target

Painter Features v1 implements this boundary: all nonredistributed runtime bytes live under the
ignored `research_workspace/painter_features_v1/` root, while compact manifests, execution
records, reviews, and reports are tracked. Future operations should add explicit subdirectories for
normalized inputs, models, vectors, outputs, caches, and locks only when a reviewed freeze
authorizes them. All recorded paths remain repository-relative or workspace-root-relative.

## Archive layout and fixed-path exceptions

Unbound legacy planning documents are archived under `docs/old/`, and superseded Painter Features
v1 material is under study/report `old/` directories. These are Git moves, not deletions.

Do not apply that cleanup mechanically to frozen Pilot 2/3 protocols, learned-formal feasibility,
pilot configs, reports, ledgers, scripts, tests, or ignored evidence. Their literal paths or hashes
are part of the historical evidence graph and must remain fixed.
