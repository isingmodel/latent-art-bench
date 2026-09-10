# Terminal fixed-map precision replay: pmrv1-20260910

Final local build; publication is separate.
The proposal stopped: all three allocations failed the baseline Q half-width
criterion. This numerical replay does not reopen it, authorize collection, or
establish service validation. No new images were generated for this qualification.

```sh
python tools/paper_map_release.py verify --root .
uv sync --locked --python 3.13.11 --extra analysis --extra dev
uv run --locked python tools/paper_map_release.py check --root .
uv run --locked pytest -q --import-mode=importlib tests/test_paper_map_release.py \
  tests/painter_map_validation_v1/test_precision.py
```

The dedicated public check calls unchanged qualify(load_proxy(...)) in memory,
compares the complete 81-cell qualification, and never calls the create-once
study build command. It writes no scientific results. Public verify uses only
stdlib; check requires installed NumPy/SciPy but no Git, network, proxy, images,
credentials or current credit balance. Optional tests need Git for temporary
provenance fixtures. Installation may download dependencies. RUN.json records
the original interpreter/library/platform; use its Python 3.13.11 runtime.

Floating results use the existing 1e-10 absolute/relative comparison contract;
structures, integers, identities, seeds, hashes, nulls and decisions are exact.
Each support_sha256 hashes reconstructed floating-point array bytes. Exact support
hash equality can restrict replay to matching numerical arithmetic/platform even
when other floating values meet 1e-10; cross-platform portability is not promised.
No tolerance alters counts, stopping decisions or the retained original report.
The stored report is verified bytewise against the unchanged report renderer
applied to the stored result; computed qualification values are checked separately.
Source mismatches or changed Monte Carlo counts fail rather than being repaired.

Included source/protocol/numerical/result bytes are unchanged. RUN.json retains
all 12 source-binding fingerprints; nine bound files are included. DESIGN.md is
omitted because it contains private operational credit information; old geometry
freeze/receipt bodies are also omitted. Their hashes are provenance, not a public
check of absent bodies. The builder verifies all 12 locally against the recorded
source commit before export. No Git history, preflight records, metadata bodies,
raw pixels, .env, Korean drafts, artwork or capture-audit raw ledger is included.
Underlying image acquisition, capture ancestry and service identity are not
independently authenticated by these vectors or a checksum manifest. Earlier
immutable numerical packages remain necessary for their historical results.

This qualification uses discrete historical noise proxies, not verified current
service laws or new-scene outcomes. Passing coverage simulations did not overcome
the failed precision gate. No perceptual, independent-capture, scene-population
or internal-mechanism validation follows. Design, implementation and reviews were
maintainer-run LLM work with disclosed assistance, not independent human reviews.
