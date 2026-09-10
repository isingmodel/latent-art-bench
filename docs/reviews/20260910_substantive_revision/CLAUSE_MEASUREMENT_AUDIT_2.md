# Clause-v1 terminal measurement audit

Date: 2026-09-10. Run: `painter_clause_validation_v1/pcvv1-20260910`.
Reviewer 2 is a maintainer-run LLM agent and implemented the clause-v1 and
successor collector/workflow code and earlier geometry/centering components.
This involved audit is not an independent human or institutional review. No
scientific score is assigned; earlier source-review snapshots remain unchanged.

**Conclusion:** the complete terminal measurement inventory, retained-scaler
mapping, receipt bindings, delivery counts and all required withholding checks
pass. The unchanged numerical/report replay passes. No primary or completed-grid
secondary scientific result is available from this stopped cohort.

## Inventory and numerical integrity

I inspected all **864 rows**: 288 allocated slots × three fixed pipelines.
These contain **633 measured vectors**, representing 211 returned images each
measured three ways, and **231 rows with null vectors**. Neither 633 nor 864 is
a count of independently generated images.

| Status | Per pipeline | Across three pipelines |
| --- | ---: | ---: |
| Measured | 211 | 633 |
| Refused | 1 | 3 |
| HTTP error | 1 | 3 |
| Cancelled before posting | 1 | 3 |
| Unattempted after collection stopped | 74 | 222 |
| Total | 288 | 864 |

Every row appears once in the exact frozen request/pipeline order. Request IDs,
sequence, block/order/position, scene, class, repetition, clause, experiment,
route and polarity agree with the planned requests. Image IDs, selected attempts,
response paths/hashes and observed metadata agree with the corresponding terminal
slots. Every returned image has a measured vector in every pipeline: there are
no additional extraction failures or discarded returned images.

For all 633 measured rows, I independently checked finite 31-element raw and
scaled vectors, the canonical feature digest, and exact elementwise equality
to `(raw - frozen_center) / frozen_scale` for that pipeline. The selected encoded
image hash matches the previously recorded delivery hash. The normalization
records preserve the delivered dimensions, use the required short side (512,
256 or 512), and record zero cropping. The JPEG sensitivity records specify
quality 90, subsampling 2, nonprogressive encoding without optimization.

All 231 unavailable rows retain their original terminal status, null raw/scaled
vectors and absent selected-image metadata. No failed/unattempted slot is
silently removed, substituted or converted into a measurement.

These are checks on stored vectors, identities, hashes and normalization
metadata. I did not decode images, rerun feature extraction, or independently
reproduce normalized pixel arrays. The underlying frozen extractor and its
qualification remain part of the measurement provenance.

## Withholding and report interpretation

Both primary records have `estimate=null`, `raw_p=null`, `interval=null`,
`status="withheld_collection_contract"`, `reject=false` and the fixed planned
72 pairs. Neither record contains randomization output, contributions or ordered
tested pairs. Each `holm_p=1.0` is the frozen bookkeeping value for an unavailable
test, **not an observed p-value or evidence supporting a null result**.

All six painter/pipeline views are retained: Monet and Cezanne in `primary512`,
`resolution256` and `jpeg90_512`. Their 24 arm-summary cells contain only
`withheld_incomplete_allocated_arm`. Every map and contrast dictionary is empty;
every reported trace ratio is unavailable, and all map-target differences have
`unavailable_incomplete_free_arm`. No energy, variance, retrieval, map superiority
or conditional-residual estimate is recovered from a complete-case subset.
Reference IDs and the fixed 72-observation weight inventories remain present
for transparent accounting but do not make these missing estimates available.

The Markdown report matches this state: primary estimates and every secondary
table entry are unavailable. Its generic method text describes the planned
analysis; it should not be read as asserting that contributions, predictions
or maps were computed for this stopped run. The JSON confirms that they were
not. The false identity flag and missing allocated grids are both retained.

## Delivery counts

I recomputed delivery summaries directly from primary-pipeline rows and matched
every status, dimension, format and reported-quality count to the saved report.
Each physical output is counted once, not once per pipeline.

| Arm | Allocated | Measured images | Reported low | Reported medium |
| --- | ---: | ---: | ---: | ---: |
| Free | 72 | 53 | 40 | 13 |
| Generic | 72 | 53 | 37 | 16 |
| Monet | 72 | 53 | 45 | 8 |
| Cezanne | 72 | 52 | 43 | 9 |
| Total | 288 | 211 | 165 | 46 |

All 211 delivered images are recorded as PNG and nonsquare; exact dimensions
remain in the report. Geometry and reported-quality differences were retained
without adjustment or quality-based filtering. These are service metadata,
not human quality ratings or evidence of painter-style validity.

## Provenance and exact replay

The measurement receipt has exactly four distinct expected bindings:
`measurements.jsonl`, `analysis.json`, `REPORT.md` and the one-shot measurement
marker. All four hashes verify, and the receipt points to the unchanged stopped
collection receipt. This explicit inventory check is additional to the frozen
replay function's hash verification.

The measurement marker is `2026-09-10T05:54:04.884933+00:00`. The already-fixed
successor freeze was prepared at `05:52:42.730058+00:00`; commit
`6effea1fc4a0f1139197453b7f31d6bdf1988d9c` has recorded commit time
`05:53:13+00:00`. The recorded ordering therefore places this measurement after
the committed successor freeze, as required. This audit did not use these
measurements to alter that design or any source.

The unchanged `workflow.check(..., pixels=False)` returns
`status="numbers_replayed"` and `raw_response_access=false`, with exact equality
of the replayed JSON and Markdown report. I separately verified the inventories,
scaling, counts and withholding above rather than relying only on that same-code
replay. No live request, image extraction, evidence modification or new
scientific analysis was performed by this audit.

| Artifact | SHA256 |
| --- | --- |
| Collection receipt | `5df074e6c90df761385e61e5118d181244671bd3eebc263d4d9e900ac0e6fdd1` |
| Measurement receipt | `c7679e82eb245af7c63919acf094389d95edd8e9ff4e8a77e464a5627fd7ed1c` |
| `measurements.jsonl` | `a431951f9d7cf7020d39dc67dc9b2e2da9f23b523cbb6f8c9be4e162c5ac5e9f` |
| `analysis.json` | `5580d9699ce15b69a47556bf80d0fd0e986810cfd18f4f0da013c9b23a52a2b2` |
| `REPORT.md` | `8b5cfbe9d60582ffa50907c8b661d790c13bcf514d681a700712ed8e80504986` |
| Measurement marker | `d9508718c8335defa323ff83d7c8796801a1dc4e1a581dc84384f7d813f3b3ba` |
| Frozen retained reference/scaler input | `4bd002c9319410946e7bedc5b6397e019cd2485e15f16b693259e3a7675e0280` |

Collection and measurement manifests are under
`data/manifests/painter_clause_validation_v1/pcvv1-20260910/`; report files are
under `reports/painter_clause_validation_v1/pcvv1-20260910/`; the marker is under
the corresponding ignored `research_workspace/` namespace. The numerical input
is `studies/painter_clause_validation_v1/inputs.json`.

The original unavailable endpoints remain closed. This audit makes no claim
about a successor outcome, a released public package, perceptual validity,
population generalization or upstream-service recovery.
