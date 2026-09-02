# Documentation index

Use this index to distinguish current guidance from immutable study history. Unbound legacy
planning documents are under `docs/old/`; frozen and hash-bound pilot records retain their original
paths because those paths are evidence identities.

## Current mutable guidance

- [Current status and reboot boundary](STATUS.md) — operational truth for the next agent.
- [Architecture map](ARCHITECTURE.md) — current modules, data flow, and safe reboot seams.
- [Artifact retention policy](ARTIFACTS.md) — what may be cleaned and what must be preserved.
- [Root README](../README.md) — short orientation, setup, and repository map.
- [Agent guide](../AGENTS.md) — repository-specific working rules.
- [Config index](../configs/README.md) — version and mutability of study inputs.
- [Contributing](../CONTRIBUTING.md) — development and validation expectations.

## Current Painter Features v1 research

- [Painter-feature relaunch overview](../studies/painter_features_v1/README.md)
- [**Canonical painter-feature measurement protocol**](../studies/painter_features_v1/MEASUREMENT_PROTOCOL.md)
- [Collection execution records](../studies/painter_features_v1/execution/README.md) — subordinate,
  hash-bound instantiations of the canonical method, not another plan.
- [Collection plan and result report](../reports/painter_features_v1/COLLECTION_REPORT.md)
- [Collection result evidence](../reports/painter_features_v1/evidence/collection_result.json)
- [Independent collection-result audit](../reports/painter_features_v1/evidence/collection_result_audit.json)
- [Painter-feature literature review](../literature_reviews/README.md)
- [Literature evidence synthesis](../literature_reviews/SYNTHESIS.md)
- [Painter-feature method decisions](../literature_reviews/METHOD_DECISIONS.md)
- [Relaunch process and result report](../reports/painter_features_v1/RESEARCH_REPORT.md)

Only the measurement protocol is the active method plan. Execution freezes instantiate a narrow
operation, while the overview, literature, and report files are navigation or supporting evidence
rather than alternate protocols.

## Legacy research references (noncanonical)

- [Legacy archive index](old/README.md)
- [Research proposal](old/RESEARCH_PROPOSAL.md)
- [Benchmark specification](old/BENCHMARK_SPECIFICATION.md)
- [Corpus design](old/CORPUS_DESIGN.md)
- [Legacy validation protocol](old/VALIDATION_PROTOCOL.md)
- [Chromatic method](old/CHROMATIC_METHOD.md)
- [Learned-formal feasibility](LEARNED_FORMAL_FEASIBILITY.md)
- [Source-method matrix](old/SOURCE_METHOD_MATRIX.md)
- [References](old/REFERENCES.md)

These documents describe earlier versions of the broader research program. They may supply
background or provenance, but they are not part of the Painter Features v1 plan and must not
override its canonical measurement protocol. Some operational examples predate the latest
pilots; consult [STATUS.md](STATUS.md) before treating a command as current.

## Archived painter-feature predecessor plans

- [Archive index](../studies/painter_features_v1/old/README.md)
- [Rejected-execution index](../studies/painter_features_v1/old/rejected/README.md)
- [Superseded validation protocol](../studies/painter_features_v1/old/VALIDATION_PROTOCOL.md)
- [Superseded analysis and claims policy](../studies/painter_features_v1/old/ANALYSIS_AND_CLAIMS.md)

These files preserve review provenance only. They are noncanonical and must not be combined with
the version 2.0 measurement protocol.

## Pilot 3 frozen design and incident record

- [Frozen Pilot 3 protocol](PILOT_3_PROTOCOL.md)
- [Freeze-A1 planning report](../reports/pilot_3/PLANNING_REPORT.md)
- [Freeze-A1 planning index](../reports/pilot_3/planning_index.json)
- [AIC browser recovery](PILOT_3_AIC_BROWSER_RECOVERY.md)
- [Preprocessing incident amendment](PILOT_3_PREPROCESSING_DETERMINISM_AMENDMENT.md)
- [Official-Met R2 protocol](PILOT_3_R2_OFFICIAL_MET.md)
- [Committed Pilot 3 evidence](../reports/pilot_3/evidence/)

These are immutable protocol/evidence snapshots. The planning report's statement that no
artwork bytes had been opened was true at Freeze A1, not at current `main`.

## Historical pilot results

- [Pilot 2 protocol](PILOT_2_PROTOCOL.md)
- [Pilot 2 failure investigation](old/PILOT_2_FAILURE_INVESTIGATION.md)
- [Pilot 2 result](../reports/pilot_2/REPORT.md)
- [Pilot 2 artifact index](../reports/pilot_2/artifact_index.json)
- [Pilot 1 result](../reports/pilot_1/REPORT.md)
- [Pilot 1 evidence anchor](../reports/pilot_1/EVIDENCE.md)
- [Pilot 0 result](../reports/pilot_0/REPORT.md)

## Historical planning commentary

- [Implementation-status snapshot](old/IMPLEMENTATION_STATUS.md)
- [Post-Pilot-1 roadmap](old/ROADMAP.md)
- [Project decisions](old/DECISIONS.md)
- [Artist selection](old/ARTIST_SELECTION.md)
- [Failure investigation](old/FAILURE_INVESTIGATION.md)
- [Image API testing](old/IMAGE_API_TESTING.md)

These files retain useful rationale but are not current operational status. They were moved as
content-preserving Git renames because no committed evidence bound their literal paths. Frozen
Pilot 2/3 protocols, learned-formal feasibility, and historical pilot namespaces were not moved.
