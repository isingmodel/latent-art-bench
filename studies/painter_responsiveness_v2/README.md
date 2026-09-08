# Computational painter responsiveness

This successor implements the user's instruction to continue without human reference
ratings. It tests a deployed service's response to muted/vivid instructions, with
shared artist-free and generic-painting controls for Monet and Cézanne. Its
[prospective protocol](PROTOCOL.md) defines the claim and all 192 slots. Human
perception and the underlying training mechanism are outside this experiment's
identified scope. Earlier v1 evidence and its human requirements remain unchanged.

## Stages

Run commands from the repository root. Preparation requires clean committed source
and the real local proxy source directory. The example relative path is a runtime
argument; no machine-specific proxy path is persisted in research evidence.

```bash
uv run --locked python -m latent_art_bench.painter_responsiveness_v2 prepare --proxy-root ../openai-oauth
# Commit the newly prepared freeze.json and planned_requests.jsonl.
uv run --locked python -m latent_art_bench.painter_responsiveness_v2 diagnose
uv run --locked python -m latent_art_bench.painter_responsiveness_v2 collect --live --proxy-root ../openai-oauth
uv run --locked python -m latent_art_bench.painter_responsiveness_v2 measure
```

All commands default to `prv2-oauth-20260908`; `--run-id` is explicit for a successor.
Preparation, collection, measurement and report publication are create-once stages.
Never use these commands to overwrite, refill or resume a terminal allocation.
The collector sends at most two simultaneous requests, spaces starts by five
seconds, and permits only bounded identical-payload retries for fully received
technical errors. No OpenRouter endpoint is contacted or billed in this study.

The collector binds local proxy source/process identity and records actual returned
geometry, reported rendering fields and timing. An alias is not an attested model
snapshot. Supported delivered images are retained even if requested quality or
geometry is not honored. Every planned missing slot stays visible; any missing
primary endpoint withholds inference for the allocated grid.

## Reproduction

After publication, these commands make no network requests or new image-feature
measurements. They verify committed input bindings, recompute statistics from
retained vectors, and compare every rendered report byte:

```bash
uv run --locked python -m latent_art_bench.painter_responsiveness_v2 check-diagnostic
uv run --locked python -m latent_art_bench.painter_responsiveness_v2 check
```

The first report is at
`reports/painter_responsiveness_v2/prv2-oauth-20260908/diagnostics/REPORT.md`;
the prospective outcome report is at the sibling `experiment/REPORT.md`.
Current execution state and result links belong in [STATUS.md](../../docs/STATUS.md),
not in this frozen implementation guide.

## Source organization

- `common.py`: fixed configuration and exact randomized request inventory.
- `collection.py`: verified OAuth transport, staggered dispatch, retries and all-slot ledger.
- `workflow.py`: clean-source freeze, publication, measurement and offline byte replay.
- `diagnostics.py`: retained-data held-repetition scene retrieval and contraction comparisons.
- `analysis.py`: two primary shared-control interactions, processing sensitivity, all-coordinate
  descriptions and the exposed-reference chroma comparison.
- `report.py`: deterministic tables, scientific prose and plots from saved numerical results.

The package reuses frozen transport inspection, feature extraction, scaling,
randomized-block construction and statistical primitives; it does not change their
contracts. Tests use synthetic values and mock transport. Implementation review is
by maintainer-run LLM subagents with coordinator checks, not independent human or
institutional review. The historical `latent-art-bench verify-evidence` audit is
separate from this namespace's explicit replay commands.
