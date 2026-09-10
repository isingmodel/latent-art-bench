# Fixed-map v2 actual numerical audit — reviewer 1

Date: 2026-09-10. Run: `pmv2-20260910`. Repository HEAD observed during report preparation: `bd3c9ca1261541f523617f9c8ed908db3acaac2d`.

**Pass: no numerical discrepancy affecting interpretation was found.** Both prespecified contrasts and both approximate intervals are negative. The historical opposing ordering did not transfer to this prospective fixed panel: translation plus scaling has lower reference energy and lower corrected named-scene-mean mismatch than translation alone. This is the retained contrary outcome, not a failed computation or a reason to replace the cohort.

## Scope and involvement

This is a maintainer-run LLM audit, not an independent human or institutional replication. I contributed earlier variance primitives, the map precision protocols and implementations, independent analysis-oracle tests, release adapters and manuscript presentation, and reviewed the study design. I was given the reported contrast signs before this audit. Implementation and selection independence are therefore limited. The arithmetic below uses a new literal NumPy/SciPy calculation that imports **no `latent_art_bench` module**, rather than calling the qualified analysis or precision functions.

I used only the fixed endpoints, saved vectors and historical inputs. No images or response bodies were opened; no extraction, generation, new fit, endpoint, simulation, formal qualification writer, score or evidence edit was performed. The separate [reviewer 2 terminal audit](MAP_VALIDATION_TERMINAL_AUDIT_2.md) covers operational eligibility, response provenance and ordinary exact replay; those are not independently reauthenticated from raw bodies here.

## Inputs, eligibility and calculation

All 240 saved rows are measured, with 120 images per arm and exactly one vector for every scene/repeat/arm assignment. Their identity fields match the saved requests with exact types, and their 31 feature names match the unchanged color/spatial/texture ordering read from the source's literal inventory. All **7,440** standardized coordinates equal `(raw − old_center) / old_scale` exactly. The compact input's complete scaler, 32-reference object and fitted-map object equal their hash-checked historical origins. No standardization is applied twice.

Reference weights are 1/32. Scene order is water01–04, built01–04, land01–04; corresponding scene weights are four copies each of **3/128, 11/128 and 18/128**, summing to one. Each original image receives its scene weight divided by ten. Every saved membership, pair ID, repetition and image weight agrees. Collection eligibility is literally `true` with an empty reason list, and saved analysis eligibility agrees. The measurement receipt binds the collection receipt and exactly the four specified output bodies, all hash-exact.

The old maps are held fixed: `T1(f)=f+muN−muF` and `T2(f)=muN+a(f−muF)`, with `a=0.6785365094757265`. For each complete transformed cloud, I computed Euclidean distances directly with NumPy norms and evaluated all three weighted V-energy sums, including zero self diagonals. For Q, I explicitly summed every unordered distinct-repeat residual dot product, doubled that sum, and divided by `R(R−1)` within each scene before scene weighting. An independent mean-squared-residual minus unbiased sample-trace/R identity agrees to at most **1.07e−14**, including deletions. Neither calculation truncates negative estimates.

All **120 paired deletions** were recomputed from their literal remaining clouds. Deleting pair `(j,r)` removes the same F/N repetition only from scene j; that scene's nine images receive `w_j/9` and its Q denominator becomes `9×8`. Every other scene retains ten images and its original total mass. No optimized kernel/deletion formula is reused. For each endpoint, I then calculated `VJ=(9/10) sum_j,r (T_−jr − mean_r T_−jr)^2` and `T ± t_(9,.9875) sqrt(VJ)`. The critical value is **2.6850108468164575**; both variances are finite and positive, so the family withholding rule is not activated.

## Numerical agreement

The following are the authoritative saved values, with independently calculated discrepancies reported separately.

| Point-value interpretation aid | Saved value | Independent absolute difference |
| --- | ---: | ---: |
| E(X,T1F) | 1.6706635369007783 | 1.78e−15 |
| E(X,T2F) | 1.2804766583666742 | 1.78e−15 |
| Q1 | 6.949537455161918 | 0 |
| Q2 | 1.903027002213590 | 0 |

| Endpoint | T2−T1 | Jackknife variance | Half-width | Approximate simultaneous 95% interval |
| --- | ---: | ---: | ---: | --- |
| deltaE | −0.3901868785341036 | 0.001959192828350537 | 0.11884601817516997 | [−0.5090328967092735, −0.2713408603589336] |
| deltaQ | −5.046510452948327 | 1.1132765436676098 | 2.8330065188986286 | [−7.8795169718469555, −2.2135039340496987] |

Maximum absolute differences for deltaE/deltaQ, respectively:

- Point estimates: **4.00e−15 / 8.88e−16**.
- All 120 paired deletion estimates: **5.27e−15 / 1.78e−15**.
- Jackknife variances: **2.81e−16 / 1.78e−15**.
- Interval endpoints: **1.25e−14 / 3.11e−15**.

All comparisons pass an audit arithmetic tolerance of 1e−12 absolute and relative. This audit tolerance does not alter any public replay or scientific contract. All saved paired-deletion contrasts also remain negative; these are the prespecified variance inputs, not an additional inferential test. The report's rounding, direction labels and `resolved_other_ordering` classification agree with the independently reconstructed bounds. No extra component intervals or p-values are introduced.

## Scientific interpretation and limits

On these twelve authored scenes, the unchanged scaling map favors **both** targets. The prospective result therefore fails to reproduce the historical expectation of higher reference energy but lower conditional mismatch. It neither erases the historical observations nor supports a general claim that the two targets always agree. E concerns the expected empirical finite-R10 transformed-free/reference energy; Q concerns fixed-scene conditional named-mean mismatch under independent stationary repeat errors, allowing F/N dependence within a pair. These are different estimands and units. The experiment is not a randomized map treatment or a direct named-versus-free reference-energy test.

The actual Q half-width **2.8330** exceeds the **1.0** baseline-proxy planning tolerance. That tolerance gated the median width of predeclared artificial laws before collection; it was neither an actual-outcome eligibility threshold nor a guaranteed service precision. The wider observed interval is material evidence of that planning limitation and remains reportable. Both bounds nevertheless remain negative under the sole approximate procedure. Neither its Bonferroni construction nor passing proxy qualification establishes actual simultaneous coverage, repeat stationarity/independence, or absence of service drift. Map-estimation uncertainty is conditioned away rather than estimated here.

The panel is fixed, not sampled from a scene population. The result provides no perceptual-style, independent-capture, model-checkpoint, internal-mechanism or separate-investigator validation. V1's failed precision decisions and the v2 terminal stopping rule remain unchanged; this outcome authorizes no further repetitions, alternative interval or replacement cohort.

## Execution and exact fingerprints

Command: `uv run --locked python tmp/paper/map-validation-results-audit-1.py`, exit 0. Runtime: Python 3.13.11, NumPy 2.5.2, SciPy 1.18.1, macOS 26.6.2 arm64. Scoped Ruff F checks pass. The create-once ignored audit JSON retains every independently calculated deletion and the complete 20-file fingerprint inventory. All 20 scientific/source/input fingerprints checked before and after arithmetic were unchanged. The audit itself is additional verification, not a fresh scientific analysis result or a public cross-platform replay.

| File | SHA-256 |
| --- | --- |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/freeze.json` | `e91fe3adbb41fd7a45e43c532eb680e86634168529ca9150da12f970bb29cb1e` |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/planned_requests.jsonl` | `a0aa1f059f961d624e09a59d5ad1277448791b783ce24a72dd48047e4c19cec8` |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/collection_receipt.json` | `03bbf8bf5f7679401051f52a803d6a1c18c0eb23140e3b04a9b5ad232c3618b2` |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/measurement_receipt.json` | `13aa9a0ab21e5efd235ab40034c81399dd02e5415d19e322b8be00a79ba6bd51` |
| `data/manifests/painter_map_validation_v2/pmv2-20260910/measurements.jsonl` | `157d2e541db3e65336a8583ad2c829e62e3834c05750c93e65e767a126430ba2` |
| `reports/painter_map_validation_v2/pmv2-20260910/analysis.json` | `11159b1b9b15dc6be3b1b3e03659298a8bed6bcd38a52aa992f16d2f26833386` |
| `reports/painter_map_validation_v2/pmv2-20260910/REPORT.md` | `57470eb939a4120e632690be4e4b6e55ee15deb87f93b7a585cb62ca3e52b498` |
| `studies/painter_map_validation_v2/inputs.json` | `8c7d3c74a420b12782fabf306f85e9953ac6cb794f31d2e365f2adf0b7094a04` |
| `studies/painter_map_validation_v2/PROTOCOL.md` | `d40f05a8714279ede08d395238739defda96d9a950e81f2b67d81d9caebca212` |
| `studies/painter_map_validation_v2/PRECISION_PROTOCOL.md` | `b9fd2ada9726b2ac0878f2e2bdd3caaefcbc5f8d42881fd6a07e8638ef719377` |
| `studies/painter_map_validation_v2/pmvqv2-20260910/precision.json` | `8b02aea081d16484c6179849ad33b289cd16eae376e4bea92590f657a04731d9` |
| `data/manifests/painter_naming_geometry_v1/pngv1-20260910/inputs.json` | `eeb3890268a85885f372bdb494e29ab558c271749667fb7e264a7e30881733de` |
| `data/manifests/painter_naming_geometry_v1/pngv1-20260910/analysis.json` | `f50be0f772a3bff8f4bc66ddc20f3e19b5c13736fd6cced632d80224e2203324` |
| `src/latent_art_bench/painter_map_validation_v2/analysis.py` | `7e06025be026312174a5335238233b42a3da2082ba88490e96b97d9316b64209` |
| `src/latent_art_bench/painter_map_validation_v1/precision.py` | `971d909e63346cea64a1b7dd7b695ec8c112dc16562230d9d5dd7d968bd0b44d` |
| `src/latent_art_bench/painter_map_validation_v2/precision.py` | `0ed0cd14e5e2c925f63311136eb8ba7960ee50e12ac5b8c81dda263c84602c7a` |
| `tmp/paper/map-validation-results-audit-1.py` | `18271ed62b49ead5b2448133e2f6b09c308b8db9210368043bb735cb1fa35803` |
| `tmp/paper/map-validation-results-audit-1.json` | `9d3d0ef0033573db3d29e3e0bdf03a21fa0a34fe5975fd9827633c1d8e24e16f` |
