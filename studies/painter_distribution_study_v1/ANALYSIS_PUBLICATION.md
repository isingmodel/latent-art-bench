# Publication-only Boolean conversion — 2026-09-07

The completed scientific calculation in `immediate_results.analyze` reached its
JSON publication step, which raised `TypeError: Object of type bool is not JSON
serializable`. NumPy's false comparison result can survive Python's short-circuit
`and` in `analysis.prompt_endpoints`; a true first operand instead yields a native
Boolean from the second operand. Four `endpoints[*].reject_at_05` fields were NumPy
Booleans. No analysis file or analysis receipt was written by that failed call.

The frozen scientific source and immediate-results publisher remain unchanged.
The new `pdsv1-analysis-20260907` namespace publishes the same calculation through
`analysis_publication.py`. It converts only the rejection fields to native JSON
Booleans, requires exact value equality after JSON round-trip, and rejects other
unsupported or nonfinite values. Estimates, p-values, rejection truth values,
weights, memberships, features, references, availability and all random seeds
are unchanged. It authorizes no generation, new feature extraction, endpoint
selection or additional statistical analysis.

This is a disclosed publication correction after measurement, not a prospectively
changed scientific method. The failed publisher remains the recorded source;
its compact diagnosis identifies the affected paths. The adapter, tests, this
contract, diagnosis and completed measurement inputs must be committed before
preparing its create-once publication freeze; commit the freeze before publication.
Its numerical check reruns the unchanged scientific calculation and verifies the
published data. The report binds the new analysis path and its own committed
renderer. Closed generation components and all prior evidence remain untouched.

```bash
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.analysis_publication prepare
# Commit publication_freeze.json before build or verify.
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.analysis_publication verify
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.analysis_publication build
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.analysis_publication check
```
