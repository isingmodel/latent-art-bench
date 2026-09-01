# Configuration index

Configurations are versioned study inputs, not templates to edit in place after results are
observed.

| Path | Role | Mutability |
|---|---|---|
| `pilot_0/` | Original development-pilot configuration | Historical |
| `pilot_1/` | Post-failure engineering redesign | Historical |
| `pilot_2/` | Frozen requested-label execution study | Immutable study record |
| `pilot_3/` | Freeze-A1, Phase-A, and later prospective contracts | Reboot-frozen; R2 cohort closed |

Under this reboot's governance boundary, Pilot 3 is not an active resumable workflow. Its
official-Met R2 cohort closed after the first metadata request returned HTTP 403. See
[current status](../docs/STATUS.md).

For reboot work, add a new clearly versioned study namespace. Do not repurpose a historical
pilot directory, edit a frozen prompt or schedule, or interpret config changes as authorization
for network, external-holdout, or generation activity.
