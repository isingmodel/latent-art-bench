# Offline preparation status

19 September 2026. **No prospective observations, paid calls or live transport.**
This directory is preparation for the [prospective study](../../studies/painter_family_controls_v1/PLAN.md),
not a report of its empirical results or a complete precollection freeze.

## Verified this turn

- The complete new namespace now passes **295 tests**, including actual synthetic-pixel extraction/replay, and Ruff.
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
- Prepared both encoders' four reference panels (primary/development ×
  original/audited-region), preserving all649/221 reference memberships and
  the previously declared131 replacements. The bound candidate digest is
  `0e3cf3628118324c7526a9a01e3fa9195ee1ace55ea401fa569c595696bcbd82`.
- Added terminal-to-feature validation. Four independently reproduced defects
  were fixed; ten invalid-input probes now reject. Successful image bytes must
  match their raw responses and actual geometry; completed successes cannot be
  replaced by retries; closure cannot precede completion; detached objects cannot
  erase simulation identity. The [verification](../icml_review_v1/family_census_remediation_verification.md)
  preserves the original adverse cases and the still-unverified execution boundary.
- The [reporting fixture](offline_reporting_v1/result.json) connects four mock
  completions and4,604 missing slots to bound learned/raw31 feature inputs, one
  primary report, seven secondary reference/encoder reports, two frozen
  recognition reports and31-feature energies. All incomplete primary decisions
  remain unavailable. No encoder or31-feature extractor executes in this test.
- The [v4 amendment](../icml_review_v1/prospective_controls_v4.md) resolves the
  remaining31-feature secondary before collection. It reports realized,
  noise-inclusive per-window energies and signed path interactions, with no
  new energy fractions, noise correction or inferential claim. Primary
  endpoints and the4,608-image allocation stay unchanged.

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
uv run --locked python scripts/qualify_family_reporting_offline.py --output reports/painter_family_controls_v1/offline_reporting_NEW
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

Feature manifests, reference-view adapters, fixed-scaler loading and report
assembly are implemented and fixture-verified. The raw31 extractor now executes
and exactly replays three synthetic images in separate processes; see the
[execution qualification](../icml_review_v1/family_execution31_qualification.md).
Actual learned-encoder execution and prospective image measurement remain pending. A valid hash/row manifest
does not prove that an encoder calculated the supplied vectors. The reporting
adapter explicitly leaves execution authentication false; the new raw31 replay
evidence is separate and does not authenticate learned encoders. Actual routes/prices,
complete freeze inputs and future live scheduler/transport qualification also
remain outstanding.

The ICML manuscript remains eight main pages and 46 pages total. The latest
editorial PDF is unscored; the last independent scientific panel was 4/4/4,
mean 4.0, below the requested mean above 8.2. These code and fixture results do
not warrant a new scientific review round. All 23 round-three scientific
evidence bindings and all three reviews were verified unchanged.

The earlier preparation summary is preserved as
[README_qualification_v1.md](README_qualification_v1.md); earlier source/test
bindings remain intact. Current integration detail is in the
[reporting note](../icml_review_v1/family_reporting_integration.md).

Current raw31 qualification: [offline_execution31_v2/result.json](offline_execution31_v2/result.json).
Its three original synthetic images and complete extraction inputs are retained
for exact replay. No new paid calls or study observations were made.
