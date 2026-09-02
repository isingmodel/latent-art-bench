# Artifact retention policy

The repository contains both compact committed evidence and large ignored local bytes. Their
directory names overlap for historical reasons, so Git ignore status alone does not mean a
file is disposable.

## Canonical tracked material

Preserve and review normally:

- source, tests, configs, documentation, and compact reports;
- Painter Features v1 historical frames, denylist, chained collection ledgers,
  freeze/review/seal records, and compact result evidence;
- Painter Feature Generation v1 protocols, future R0a/R1a/R0b/R1b/G0/G1a/G1b freezes and seals,
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
The active Painter Feature Generation v1 protocol 1.7 uses the separate ignored
`research_workspace/painter_feature_generation_v1/` root. It currently contains only three
exploratory metadata-response files for the federated scale census; their compact hashes and limits
are tracked in the census evidence. A separate tracked official-source audit records 43 all-content
metadata candidates without downloading their images. It is traceable live-item evidence, not a
reproducible as-of-date source snapshot, and none of its records is admitted to the four-broad-
scene-group outdoor-place real-work frame. No active-study image, eligibility derivative, normalized
derivative, feature vector, registered generation request, generated output, or result exists yet;
R0a remains NO-GO.

The four-painter request count is `120R`, with the same `R` for every named condition and shared
painter-free control in every selected template. The former `R=16`/1,920-request scenario is a
retired design artifact because it cannot clear the boundary-safe availability gate. The best-case
mathematical floor is `R>=25` and at least 3,000 requests only when every repetition is its own
auditable independent unit; the actual Bonferroni endpoint inventory, independence-unit audit, and
whole-decision simulation require a larger, still-unfrozen `R`. No active request artifact exists.
For a fixed deterministic local map, G0 will retain independent per-template IID-uniform-with-
replacement seed lists and chance duplicates. For an opaque/remote endpoint, it will instead retain
`C` equal-size common-shock units, each containing `L` complete balanced template×condition waves,
their randomized request order, and the identity/episode receipts establishing `R=C*L`.

The minimum acquired, adjudicated, and analyzed internal frame will contain 1,440 physical works:
72 development, 108 qualification, and at least 180 confirmation works per painter. Registering
external replication adds a complete 96-work census per painter, or 384 works, for at least 1,824
acquired and analyzed real works. A separate auxiliary independent-capture census contains every
eligible work in its frozen auxiliary frame and at least 32 physical works—at least eight per
painter, with at least two independently produced captures per work. Neither its works nor extra
captures count toward the internal or external totals. Its raw captures belong under the ignored
active-study workspace, while its identity, capture-ancestry, rights, and hash manifest is compact
tracked evidence.

When R0a authorizes content coding, frozen derivatives with long side at most 512 pixels, coder
notes, and adjudication imagery are ignored research bytes inside a role-separated eligibility
store. They are real pixel exposure and their hashes/access events belong in compact tracked
ledgers, but feature, method, and generation analysts may not view them. Analysis-resolution
qualification/final files occupy a separate access-controlled store; final-reference files remain
sealed through G1a. The compact R0a reliability receipt must preserve the complete visual-screening
and union-eligible denominators, missing labels, three-way eligibility agreement (`>=0.90` per
painter), each coder's ambiguous share (`<=0.10`), broad-scene and each five-property three-state
agreement (`>=0.85` in every required frame/population scope), and each coder's season/illumination/
depth indeterminate fractions (`<=0.20`). A failure remains R0a NO-GO and adjudication cannot erase
the receipt. The compact R0a record must retain the complete eligible frame, the painter-level
CSPRNG permutation assigning ranks 1–72 to development, 73–180 to qualification, and 181 onward to
sealed confirmation, and complete-population access receipts. It must also retain all 12 byte-exact,
hash-complete candidate prompt frames—the artist-free/named-placeholder text, punctuation, language,
negative prompt, insertion point, painter-name substitution table, scene label, five content values,
and render contract—the selected 24-template frame, its four broad-scene proportions, the five
predeclared binary visible-property targets, and each complete population's entropy
projection `q*`, including its joint convex-hull, weight-cap, and effective-sample-size receipt.
Those vectors are frozen before feature access and are never refit; `q*` is primary and the uniform
complete population is a mandatory sensitivity. G0 verifies the selected text/render hashes but may
not rewrite them. The locked analysis contract also retains the one equal-painter pooled-development
weighted-median/IQR transform; full-frame unweighted-only and assigned-population unweighted/`q*`
source-share receipts, explicitly with no full-frame `q*`; the exact source-versus-complement median-
shift RMS functional and uniform repetition; the exact real-side summation in the generated–real
term; the exact real–real finite component; the estimated-generator equal-template U-statistic;
`1/(24 m_t)` generated-quantile weights; and the
binding realized-content entropy-projection specification. Continuous inference must use the same
G0 independence partition as rates: local deterministic execution resamples whole seed-condition
vectors within template, whereas opaque/remote execution resamples only whole balanced common-shock
units carrying every wave and template×condition outcome. Real censuses stay fixed and templates are
never resampled. Continuous endpoints use the max-statistic contract; rate artifacts instead
retain the alpha allocation, weighted-Hoeffding and conservative-ratio formulas, and an endpoint
inventory counting `A` lower, `A` upper, `J` lower, and `K` upper as four directional events,
plus request-to-independence-unit mapping, aggregate `W_c` weights, independence rationale, remote-
service common-shock grouping, and clustered pixel/feature-failure coverage fixtures. A crossed
shock, unusable balanced unit, or partition not aligned with fixed-template resampling makes both
affected rate and continuous endpoints ineligible or inconclusive. A nonstructural zero replicate
variance is an inconclusive endpoint. There
are no active real-work inclusion-probability records, sampling fractions, or Rao–Wu replicate
weights. R0b releases the complete qualification populations and cannot add or redefine eligible
works. Source labels remain available for binding robustness analyses but are not sampling strata.
G1a output bytes and their append-only ledger likewise remain sealed
while final-reference bytes are unopened. G1b must retain two independent raw code streams for every
sealed-confirmation and technically analyzable generated image, condition-scoped 0.85/0.20
reliability receipts sealed before adjudication, the third blinded adjudicator's deterministic
consensus, and any affected-endpoint inconclusive disposition. G1b also records the one-time
reference opening. Add exact subdirectories for these bytes, models, caches, and locks only when the
corresponding reviewed freeze authorizes them. All paths remain repository-relative or workspace-
root-relative.

## Archive layout and fixed-path exceptions

Unbound legacy planning documents are archived under `docs/old/`, and superseded Painter Features
v1 material is under study/report `old/` directories. These are Git moves, not deletions.

Do not apply that cleanup mechanically to frozen Pilot 2/3 protocols, learned-formal feasibility,
pilot configs, reports, ledgers, scripts, tests, or ignored evidence. Their literal paths or hashes
are part of the historical evidence graph and must remain fixed.
