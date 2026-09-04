# Configuration index

Configurations are versioned study inputs, not templates to edit in place after results are
observed.

| Path | Role | Mutability |
|---|---|---|
| `painter_feature_generation_v1/` | Active Protocol 2.1 metadata and future staged study contracts (the completed censuses bind Protocol 2.0) | Versioned; each execution requires its own reviewed freeze |

Every config in the active namespace is a hash-bound frozen input of at least one census freeze.
Verification is commit-bound, so an edit no longer breaks the freeze's verification, but editing a
config that authorized a census still rewrites the record of what ran. A corrected contract is a
new file under a new census ID, not an edit.

`cleveland_metadata_census.json` is the first contract written for the shared census engine. It
has no freeze yet; `latent-art-bench cleveland-metadata prepare` writes its intents and a
commit-bound freeze only from a clean tree, and execution still needs a neutral review that
states `reviewer_kind` and an authorization seal.

Adding a config is not authorization for network, external-holdout, or generation activity. See
[current status](../docs/STATUS.md) and
[Protocol 2.1](../studies/painter_feature_generation_v1/PROTOCOL_2.1.md).
