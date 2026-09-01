# Current status and reboot boundary

This is the mutable operational status page for LatentArtBench. It summarizes committed state
through `612d09e` (`Record terminal Met R2 metadata denial`, 2026-09-01). Frozen protocols,
reports, indexes, and append-only ledgers remain the authority for their own historical facts.

## Outcome

The Pilot 3 official-Met R2 path is stopped. Its first metadata request returned HTTP 403 and
was durably recorded as `protocol_rejected`. The prospective R2 protocol states that a
terminal transport or protocol failure closes that cohort and permits no retry, alternate
field, derivative, host, provider, or replacement work.

This is a terminal condition for Pilot 3 R2, not permission to improvise a new transport. The
protocol does not rule out every conceivable prospective Pilot 3 successor. Separately, the
requested reboot adopts a simpler governance boundary: preserve Pilots 0–3 as history and put
further work in a new versioned namespace.

## Painter-feature relaunch

The first new scientific reboot is designed under `studies/painter_features_v1`. Its target is a
**painter-associated distribution across held physical works**, not a generic feature of one
painting and not era or movement classification.

There is one canonical active plan:
`studies/painter_features_v1/MEASUREMENT_PROTOCOL.md`, protocol version 2.0. It is a standalone
real-image measurement protocol containing the construct, sampling and observation model,
preprocessing, feature algorithms, qualification gates, inference, outputs, execution-freeze
checklist, and claim ceilings.

The design package contains:

- the standalone canonical measurement protocol;
- a structured literature review with 138 evidence-matrix records and a 201-source audited
  bibliography, including the exact Kim et al. paper/code audit;
- candidate interpretable color, spatial, wavelet, ordinal, and composition coordinates;
- separately named learned-appearance and contextual diagnostics;
- independent-reproduction, perturbation, leave-source-out, leave-content-out, human, and
  external-confirmation gates; and
- a 19-item checklist for the next execution-freeze artifact.

The former standalone validation and analysis documents are archived under
`studies/painter_features_v1/old/` as noncanonical review provenance. They must not be combined
with or used to relax protocol 2.0.

This is a prospective design result, not execution authorization. No new artwork was acquired,
no historical or external holdout was opened, no feature was extracted, no model weight was
downloaded, and no image was generated. A new frozen execution protocol must specify painters,
crossed sources/content/phases/media, independent reproductions, rights, precision simulations,
thresholds, artifacts, partitions, decision rules, and terminal actions before any of those
operations.

## What exists

| Layer | State |
|---|---|
| Freeze A1 | Committed for 40 development works and a sealed 12-work external holdout |
| AIC development acquisition | 20/20 works acquired and normalized; raw and normalized bytes remain ignored local artifacts |
| Preprocessing remediation | 12 earlier AIC rows revalidated: 11 unchanged and one container superseded with exact RGB-pixel equality; the remaining 8 were acquired under the amended contract |
| Original Met path | Quarantined as protocol-ineligible after the provider incident |
| Met R2 | Offline authorization committed; first metadata request returned HTTP 403; cohort closed before any Met image request |
| Development features | Not created |
| Determinism probes | Not run |
| Freeze A2 / external unseal | Not created; external artwork access remains closed |
| Generation transport | Not qualified |
| Pilot 3 generation or analysis | Not started |

Primary state records:

- `artifacts/pilot_3/development_acquisitions.jsonl`
- `artifacts/pilot_3/development_normalization_revalidations.jsonl`
- `reports/pilot_3/evidence/preprocessing_determinism_incident.json`
- `reports/pilot_3/evidence/preprocessing_determinism_amendment.json`
- `reports/pilot_3/evidence/met_asset_provider_incident.json`
- `reports/pilot_3/evidence/met_r2_authorization.json`
- `artifacts/pilot_3/met_r2_metadata_attempts.jsonl`
- `docs/PILOT_3_R2_OFFICIAL_MET.md`

## Historical studies

- Pilot 0 is a historical failed qualification path.
- Pilot 1 completed an engineering traversal, but both scientific measurement gates failed.
- Pilot 2 executed all 320 assigned requests. Five moderation refusals left both registered
  requested-label feature grids incomplete, so all four primary tests were not run and the
  study decision was `REDESIGN`.
- Pilot 3 was a prospective redesign. Its AIC half reached acquisition, but its Met R2 cohort
  closed before metadata capture could proceed beyond the first fixed object.

These negative and incomplete outcomes are evidence. A reboot must not relabel them, remove
terminal attempts, retry closed cells, or overwrite their protocols.

## Known repository health boundary

The ordinary development baseline is healthy:

```bash
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
```

At this status snapshot, Ruff passes and all 490 tests pass.

Two historical verifier commands intentionally fail against current `main`:

- `pilot2 verify` first rejects a qualification contract whose closure binds an earlier root
  CLI. Even after resolving that source-hash drift, complete verification would require the
  retained ignored media, derived data, model/source artifacts, and outputs.
- `pilot3 verify` checks only the planning/Freeze-A1 bundle. It rejects that planning index
  because later Pilot 3 commands changed the hash of
  `src/latent_art_bench/pilot3/cli.py`; it does not verify the latest operational ledger or a
  complete Pilot 3 execution.

Those failures expose implementation drift from frozen evidence; they are not fixed by
rewriting the evidence. The stale planning index does not invalidate the separately committed
Met R2 terminal record. In particular, do not run `pilot3 plan` as cleanup because it writes
the deterministic planning bundle.

## Reboot boundary for the next agent

The reboot chose one small objective outside `pilot_0` through `pilot_3`: a new prospective
painter-feature measurement study. Good future work may reuse shared deterministic I/O,
preprocessing, provenance, and test utilities, but it must not inherit a closed acquisition or
generation authorization.

The next authorized research artifact is one real-only execution freeze satisfying all 19 items
in Section 12 of the canonical Painter Features v1 measurement protocol. Do not combine that
qualification execution with a generated-image study. Any approved execution should use
repository-relative paths, keep mutable status separate from immutable evidence, and put all
large runtime bytes under one clearly ignored workspace boundary.

## Explicitly closed actions

Until a new protocol is reviewed and committed, do not:

- retry the Met R2 metadata request;
- switch to a Met search endpoint, alternate image field, Commons, browser, or other fallback;
- acquire the sealed external holdout;
- extract Pilot 3 features or fit a Phase-A model from an incomplete development cohort;
- qualify generation transport or send image-generation requests; or
- regenerate, rewrite, or move frozen/hash-bound evidence for cosmetic organization.
