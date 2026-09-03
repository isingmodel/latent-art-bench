# Configuration index

Configurations are versioned study inputs, not templates to edit in place after results are
observed.

| Path | Role | Mutability |
|---|---|---|
| `painter_feature_generation_v1/` | Active Protocol 2.0 metadata and future staged study contracts | Versioned; each execution requires its own reviewed freeze |

Every config in the active namespace is a hash-bound frozen input of at least one census freeze.
Editing one in place invalidates the freeze that binds it and therefore the evidence chain of the
census it authorized. A corrected contract is a new file under a new census ID, not an edit.

Adding a config is not authorization for network, external-holdout, or generation activity. See
[current status](../docs/STATUS.md) and
[Protocol 2.0](../studies/painter_feature_generation_v1/PROTOCOL.md).
