# Offline preparation status

19 September 2026. **No prospective observations, paid calls or live transport.**
This directory is preparation for the [prospective study](../../studies/painter_family_controls_v1/PLAN.md),
not a report of its empirical results or a complete precollection freeze.

## Verified this turn

- The complete new namespace passes **176 constructed tests** and Ruff.
- An independent analysis audit found and preserved two initial defects:
  unstable Fieller inversion and unnecessary secondary missingness. Subsequent
  adversarial checks also exposed weak-denominator and scaling problems, which
  were fixed before fitting the old parameter candidate. The retained
  [numerical verification](../icml_review_v1/family_analysis_decimal_verification.json)
  has 309 constructed cases, 2,751 decisive high-precision comparisons and no
  failures. It explicitly retains 46 comparisons excluded at floating-point
  boundary precision; this is not a proof for all possible numeric inputs.
- The independent [collector audit](../icml_review_v1/family_collector_independent_audit.md)
  preserved eight initial findings. The [remediation record](../icml_review_v1/family_collector_remediation.md)
  documents fixes to manifest/event binding, mutable state, damaged-image
  decoding, space checks, ordering, policy types, exceptional completions and
  durable directories. The original audit and implementation notes remain
  historical snapshots, rather than being rewritten to imply they passed.
- The [full-grid fixture run](offline_full_grid_v1/result.json) exercised all
  4,608 exact assignments and all six historical route descriptions. Every
  original PNG and raw gzip response was compared to its fixture. A fresh
  collector instance replayed the entire drained journal, then terminal
  closure permanently denied reopen. A separate
  [ledger check](offline_full_grid_v1/independent_ledger_verification.json)
  verified all 9,216 chained events, exact assignment order/payloads, accounting
  and archive/source hashes.
- [Old-only transport parameters](old_transport_candidate_v1_receipt.json)
  were prepared for CLIP and CSD from the existing 672 named generated images
  and 649 full-frame references. An independent calculation found exact equality
  for every parameter array in both encoders. No new-query accuracy or other
  prospective outcome was calculated. The externally bound digest is
  `fd6e80de75b7578059ecaee602b4ea5fc9e74f06d7711e52e8bd532cddbabac2`.

The full-grid run uses synthetic timestamps starting in 2000, one solid-color
PNG, mock $0.01 charges, a mock $350 ceiling and mock 100 GiB free space.
Its $46.08 fixture charge and $158.373676 fixture total are **not actual spending**.
Compressed simulation manifests, events and terminal records are retained.
Only the run's temporary fixture images/responses were removed afterward.

## Reproduction

```sh
uv run --locked pytest -c pytest-paper.ini -q tests/painter_family_controls_v1
uv run --locked ruff check src/latent_art_bench/painter_family_controls_v1 tests/painter_family_controls_v1 scripts/qualify_family_controls_offline.py
uv run --locked python scripts/qualify_family_controls_offline.py --output reports/painter_family_controls_v1/offline_full_grid_NEW
uv run --locked python -m latent_art_bench.painter_family_controls_v1 preflight
```

The fixture command requires a new output directory and blocks socket network
operations. Its generated archives cannot be imported as study observations.
`design_preview.json` is an earlier draft; `design_preview_v2.json` binds the
current protocol. Neither supplies approved absolute collection windows.

## Remaining requirements

The approved cumulative ceiling remains strictly below **$120** and historical
accounting remains **$112.293676**. The proposed $350 ceiling and a writable
destination with at least 40 GiB actually free await the user's decision.
Current preflight still denies live collection. No unique historical data was
removed, no weights downloaded and no old collector reopened.

Feature extraction and reference-view/report assembly are not yet implemented
for the prospective census. The 31-feature secondary estimand also needs an
explicit precollection resolution after the v3 removal of cross-session
squared-error comparisons. Actual routes/prices, complete freeze inputs and
future live scheduler/transport qualification remain outstanding.

The ICML manuscript remains eight main pages and 46 pages total. The latest
editorial PDF is unscored; the last independent scientific panel was 4/4/4,
mean 4.0, below the requested mean above 8.2. These code and fixture results do
not warrant a new scientific review round. All 23 round-three scientific
evidence bindings and all three reviews were verified unchanged.
