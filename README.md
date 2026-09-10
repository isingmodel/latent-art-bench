# Prospective fixed-map numerical replay: pmv2r-20260910

Final local build; publication is separate.
This separate release preserves the failed v1 qualification and the single
passing R10 redesign. It replays all 27 new qualification cells and the two
observed endpoint/component results, including any unavailable family.

```sh
python tools/paper_map_validation_release.py verify --root .
uv sync --locked --python 3.13.11 --extra analysis --extra dev
uv run --locked python tools/paper_map_validation_release.py check --root .
uv run --locked pytest -q --import-mode=importlib tests/test_paper_map_validation_release.py \
  tests/painter_map_validation_v2/test_analysis.py \
  tests/painter_map_validation_v2/test_analysis_oracle.py
```

Verify is stdlib-only and checks exact inventory before installation. Check calls
unchanged numerical functions in memory, never the qualification build writer,
collector, extractor, private workflow, network or Git. Installation may download
dependencies; optional tests use temporary Git fixtures. The public CLI above is
the supported entry point. Collection/workflow/metadata source is for inspection;
its private runtime dependencies are deliberately absent. Other included tests
record qualification provenance and are not all standalone public test commands.

Qualification floating leaves use 1e-10 absolute/relative tolerance; identities,
counts, seeds, decisions and support hashes are exact. Reconstructed support
hashes cover floating-array bytes and can restrict replay to matching numerical
arithmetic/platform even when other floats satisfy tolerance. Observed analysis
and its report must replay exactly. The descriptor records the frozen runtime;
Python 3.13.11 is the recorded interpreter. Source or numerical mismatches fail;
no retained result is overwritten or repaired.

The public check recomputes qualification, assignment/order, exact fixed-input
lineage, all 240 row identities/statuses, raw-vector-to-fixed-scaler equality,
complete-vector eligibility, and the observed points/deletions/intervals/report.
Here "raw vector" means 31 numeric features, not image pixels. The collection
eligibility flags/reasons are a projection of a locally verified private receipt:
budget, service identity, transport timing and acquisition remain **attestations**,
not independently recomputed public facts. Projected rows do not authenticate the
omitted full measurement or response bytes. Omitted source-binding/terminal hashes
are provenance fingerprints, not verified public contents. No private current
credit balance, metadata response body, image, credential, .env, history or Korean
draft is included. Numerical replay does not establish raw-pixel authenticity.

The earlier immutable packages are still required for their historical results.
This archive contains no manuscript assets and does not change any previous
release. Fixed-panel stationarity/independence assumptions and historical proxy
limitations remain; no guaranteed service coverage, perceptual, capture,
scene-population or mechanism validation follows. Maintainer-run LLM agents
designed, implemented and reviewed these studies; this is not independent-human
replication. No further collection or replacement is authorized by replay.
