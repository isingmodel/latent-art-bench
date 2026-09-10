# Fixed-map v2 terminal and measurement audit — reviewer 2

Date: 2026-09-10. Run: `pmv2-20260910`. Audited repository HEAD: `223a420b87c9e982be2022f50766423a87bb7c68`. This is an additive, read-only audit of actual terminal evidence, not a new collection, extraction, precision simulation, or paper score.

**Conclusion: pass; no terminal/provenance or saved-number replay blocker found.** The complete 240-output collection satisfies the frozen eligibility gates, and all 240 measurement rows and the exact report replay agree with the retained receipts. This finding does not establish the service assumptions underlying the approximate intervals.

## Scope and disclosure

I am a maintainer-run LLM reviewer, not an independent human or institution. I implemented this study's operational common/metadata/collector/workflow code and assisted earlier geometry, centering and clause-study implementations. That involvement limits implementation independence. Here I checked actual bytes, chains, assignments and arithmetic separately, then invoked the unchanged ordinary replay. Root separately audits the scientific arithmetic. I accessed private response bodies locally to authenticate recorded costs and hashes; I did not re-extract features, generate images, access the network, run a formal qualification, or alter evidence. No account balance is reproduced here.

## Terminal provenance, delivery and accounting

- The unchanged `workflow.verify` passed all **188** freeze bindings, committed-source comparisons, qualification/precision lineage, exact prospective plan, retained reference/scaler/map bridge, and predecessor accounting checks. The freeze records source commit `aaf431afa1b2b268723df0442f4937dd099af8b4` and qualified source `c82e1604e60cc7e3d7e4707b77162d7639667a06`; operational source was `765c5f7a7ad7e240f7792ea814f00ea63e6453ba`, with freeze committed as `c68c23568140be267b43f346e9424da0b76d0833`.
- Both separate metadata gates authenticate exactly the two permitted GET records. Prefreeze metadata completed at 10:06:34.335285 UTC on source `765c5f7`; dispatch metadata completed at 10:11:39.580329 UTC on `c68c235`. Their endpoint body hash is identical, `765c865e57488f2620f6860c6562b4d4696460e442f596c24bdb89895f7ea99d`; both passed the $18.60 allowance gate. The source/freeze/dispatch/start chronological chain agrees. These are recorded metadata checks, not fresh account queries by this audit.
- The **240** assignments exactly equal the frozen seeded plan: 12 scenes × 10 repeats × two arms, 120 unique pairs, 120 outputs per arm and 80 per content class. All payload hashes agree. The 480 generation events authenticate as 240 unique intents followed by their unique attempt-1 terminals; sequence numbers and previous/event hash chains agree. Every slot selects that first valid attempt. There are no retries, refusals, missing slots, cancellations or additional outputs.
- For every selected response I checked the stored gzip SHA, decompressed entity SHA and byte count, strict base64 image SHA/length, and PNG container validity and recorded dimensions/mode. All **240** images are RGB PNGs of 1024 × 1024. These are observed dimensions, not a general size guarantee from the unchanged aspect-ratio payload. All responses omit a model field: requested FLUX route/provider and endpoint metadata are verified; an independently reported backend checkpoint is absent. The ordered response storage/entity/image inventory hashes to `b383d8ec547d8348c1602aaf1dba1106d6e374bb2312b6033cfd7f82d88d0fd4`.
- Every raw response supplies `usage.cost = 0.07`, matching its provider-reported ledger entry. Decimal summation gives **$16.80** new reported cost and **$67.5219185** project-accounted total from the preserved $50.7219185 baseline. The inherited historical reserve remains in that baseline. There are zero new unknown costs, pending attempts or reserves; no client-rejection zero convention was needed. Every admission separately passes the conditional remaining-grid/credit forecast and $5 pending-liability project guard. There is no terminal halt or unresolved disposition: the sole operator event is a successful final source/endpoint identity check after drainage.

## Actual timing and serialization

Collection receipt elapsed time is **5443.928105 s**, below 24 hours. The start marker is 10:11:49.927730 UTC and terminal receipt 11:42:35.756589 UTC; their wall-clock span is 5445.828859 s. These distinct recorded clocks were not treated as equal. The first and last recorded transport starts are 10:12:00.574602 and 11:42:06.073296 UTC.

Reconstruction from recorded monotonic starts and latencies gives maximum overlap **2** and minimum start spacing **5.000202250 s**, consistent with independently counted pending intents. Each pair drains before the next pair starts. Pairs 1–102 overlap within pair; pairs **103–120** are serialized. After 204 settled $0.07 successes, baseline + known cost + two $5 reservations would be $75.0019185, so the retained project guard permits only one pending reservation. The observed final serialization therefore matches the guard. These are client-recorded admission/transport intervals, not measurements of backend arrival, execution concurrency or repeat independence.

## Measurement and unchanged replay

Measurement began at **11:43:56.228261 UTC**, after terminal collection. The measurement receipt binds the correct collection receipt and exactly four distinct outputs: measurements, analysis, Markdown report and one-shot start marker. All four bodies match.

All **240** rows are `measured` on `primary512`, with exact planned identities, selected response/attempt links, image hashes, 31 feature names and feature-vector digests. All **7,440** raw coordinates are finite; all 7,440 standardized coordinates equal `(raw − old_center) / old_scale` exactly. The whole compact input equals `analysis.load_inputs(root)`, including the fixed historical scaler, references and full old FLUX/Cézanne map. Counts remain 120 per arm, 80 per class and ten repeats per scene/arm. Normalization records uniformly state 1024-to-512, zero crop and `missing_assumed_srgb`.

The actual command `uv run --locked python tmp/paper-map-validation-terminal-audit-2-20260910/measurement.py` invoked unchanged `workflow.check(root, "pmv2-20260910", pixels=False)` and returned `numbers_replayed`, `status_summary=approximate_simultaneous_intervals`, `raw_response_access=True`, `feature_reextraction=False`. Both saved analysis and report reproduced exactly. The terminal audit command was `uv run --locked python tmp/paper-map-validation-terminal-audit-2-20260910/audit.py`; both commands exited 0 under Python 3.13.11 on macOS 26.6.2 arm64. All **199** source/evidence/output files hashed before and after the measurement audit were unchanged.

No normalized-image hash was independently regenerated, and this audit does not validate feature extraction against pixels or perceptual meaning. Complete delivery and clean timing do not establish stationary independent service repeats, outcome-independent availability, new-scene population inference, capture equivalence or cross-platform arithmetic portability. Public export, a fresh full qualification replay and anonymous reproduction are outside this audit. The permanently stopped v1 qualification remains closed.

## Exact audited fingerprints

Paths are repository-relative. The ignored QA scripts/receipts retain the detailed local checks; the authoritative scientific evidence remains at the bound paths below.

| File | SHA-256 |
| --- | --- |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/freeze.json` | `e91fe3adbb41fd7a45e43c532eb680e86634168529ca9150da12f970bb29cb1e` |
| `studies/painter_map_validation_v2/qualification.json` | `91c148fab151a9b3bf63e7bd4fe31387716856a9fe6158be687002b578aed884` |
| `studies/painter_map_validation_v2/inputs.json` | `8c7d3c74a420b12782fabf306f85e9953ac6cb794f31d2e365f2adf0b7094a04` |
| `data/manifests/painter_map_validation_v2/metadata/pmv2-prefreeze-20260910/receipt.json` | `71ee34ce258eef04e89e721ff1c865e8bd5516bd65e68b7683680e0bb21becb5` |
| `data/manifests/painter_map_validation_v2/metadata/pmv2-dispatch-20260910/receipt.json` | `7b47dd3b79829b85b59c988eba3d4ed525f62acd3e13fe2bac99dcea1d4cfac2` |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/planned_requests.jsonl` | `a0aa1f059f961d624e09a59d5ad1277448791b783ce24a72dd48047e4c19cec8` |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/collection_receipt.json` | `03bbf8bf5f7679401051f52a803d6a1c18c0eb23140e3b04a9b5ad232c3618b2` |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/generation_events.jsonl` | `10b0f8019faf04756a3668f7dd284c39bde3628ae2cb02ca31bb5ccb6e3cdf11` |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/slot_outcomes.jsonl` | `d2f7918f55392958963da6641c246ed9b97bf209ec20c171c90a10842eae3ef9` |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/operator_events.jsonl` | `9ecccd3601fd74ab1dfafbbea0c53187b06b7185407d1ee95836ef714d7b5880` |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/measurement_receipt.json` | `13aa9a0ab21e5efd235ab40034c81399dd02e5415d19e322b8be00a79ba6bd51` |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/measurements.jsonl` | `157d2e541db3e65336a8583ad2c829e62e3834c05750c93e65e767a126430ba2` |
| `reports/painter_map_validation_v2/pmv2-20260910/REPORT.md` | `57470eb939a4120e632690be4e4b6e55ee15deb87f93b7a585cb62ca3e52b498` |
| `reports/painter_map_validation_v2/pmv2-20260910/analysis.json` | `11159b1b9b15dc6be3b1b3e03659298a8bed6bcd38a52aa992f16d2f26833386` |
| `research_workspace/painter_map_validation_v2/pmv2-20260910/measurement_started.json` | `b77c0d5ea9670bde912d499e1efeca9e613877fdc7ef9fd1e6dc8d72b2e40996` |
| `tmp/paper-map-validation-terminal-audit-2-20260910/audit.py` | `18f0692af26b4d508febf4e2203645d4a53aa75b0f01a300e06d40f88e9d3e4b` |
| `tmp/paper-map-validation-terminal-audit-2-20260910/terminal.json` | `77ce51392203ebc4f478a53a289150ea92836f2b79fbf63d948ac8348be75446` |
| `tmp/paper-map-validation-terminal-audit-2-20260910/measurement.py` | `59c280100f21bdaafaaed8961997d01c6a1590c86b7e620fa22b7535af414246` |
| `tmp/paper-map-validation-terminal-audit-2-20260910/measurement.json` | `3a60fe77b85c2f9342d3086881fe20234bff2931ae85ed5afc314f4829f02b2e` |
