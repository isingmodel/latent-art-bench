# Results index

Start with the current experiment and its separate post-result diagnostics.
Other directories contain supporting or historical evidence at their recorded
paths. For source code, plotting and offline commands, see
[the analysis catalog](../docs/ANALYSES.md).

## Current experiment

| Result | Contents |
| --- | --- |
| [Six-model artist specificity](painter_specificity_v2/psv2-20260911/REPORT.md) | Primary slopes, paired model comparisons, all four artists and accounting; full values in sibling CSVs |
| [Reference-target diagnostics](painter_specificity_review_v1/REPORT.md) | Scene decomposition, calibrated response, artist pairs, reference controls and limitations; [numerical record](painter_specificity_review_v1/analysis.json) |
| [Image inspection](painter_specificity_review_v1/inspection.json) | Selection rules, prompts, source identities, rights metadata and hashes for the 40 example images |

The [current paper](../paper/paper.pdf) is the scientific synthesis.
[Status](../docs/STATUS.md) records what remains unresolved. The new six-model
study does not yet have a dedicated versioned release.

## Supporting evidence

| Result | Role and boundary |
| --- | --- |
| [Four-painter distributions](painter_distribution_exploration_v1/REPORT.md) | Descriptive scatter, spread and detection; original and generated samples for every artist |
| [Content and reference controls](painter_distribution_study_v1/pdsv1-diagnostics-20260906/REPORT.md) | Earlier four-painter panel, reference baselines and saved projections |
| [Controlled naming](painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md) | Named/free comparisons on the separate controlled panel |
| [Computational diagnostics](painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md) | Content, metadata, timing, coverage and reference/scaler sensitivity |
| [Palette intervention](painter_responsiveness_v2/prv2-oauth-recovery-20260908/experiment/REPORT.md) | Separate complete 192-image run; [ancillary incomplete run](painter_responsiveness_v2/prv2-oauth-20260908/experiment/REPORT.md) remains distinct |
| [Scene retrieval](painter_responsiveness_v2/prv2-oauth-20260908/diagnostics/REPORT.md) | Retained-data diagnostic, without human style ratings |
| [Quantile correction](painter_responsiveness_quantiles_v1/prqv1-20260908/REPORT.md) | Corrected descriptive chroma displays; primary inference unchanged |
| [Measurement challenges](painter_measurement_validation_v1/pmvv1-20260910/REPORT.md) | Computational transformations and common-square sensitivity |
| [Temporal replication](painter_naming_replication_v1/pnrv1-20260910/REPORT.md) | Separate naming/palette cohort collected by the same maintainer |
| [Naming geometry](painter_naming_geometry_v1/pngv1-20260910/REPORT.md), [centering](painter_naming_centering_v1/pncv1-20260910/REPORT.md) | Held-scene moment maps and evaluation-reference sensitivity |
| [Initial clause experiment](painter_clause_validation_v1/pcvv1-20260910/REPORT.md), [successor](painter_clause_successor_v1/pcsv1-20260910/REPORT.md) | Initial primary unavailable; separate complete Cézanne/generic result, without pooling |
| [Prospective fixed-map comparison](painter_map_validation_v2/pmv2-20260910/REPORT.md) | Both new endpoints favor translation/scaling; historical opposing ordering does not transfer |
| [Capture audit](painter_capture_audit_v1/pcav1-20260910/REPORT.md) | No qualified independent capture pairs; [portable ledger context](../docs/ARTIFACTS.md#unique-local-material) |

## Earlier development

| Retained result | Purpose |
| --- | --- |
| [Corpus determination](painter_feature_generation_v1/R1_DETERMINATION_KO.md), [scene prescreen](painter_feature_generation_v1/SCENE_SUPPORT_PRESCREEN_KO.md) | Original corpus construction; related machine-readable evidence remains in the same directory |
| [Empirical baseline](painter_feature_generation_v2/EMPIRICAL_ANALYSIS.md), [feature distances](painter_feature_distance_v1/REPORT.md) | Earlier measured-image comparisons |
| [Prompt grid](painter_prompt_study_v1/pps1-gpt-prompts-20260905/REPORT.md), [missingness supplement](painter_prompt_supplement_v1/ppss1-missingness-20260905/REPORT.md) | Preserve the incomplete-grid inference boundary |
| [Retry result](painter_prompt_retry_v1/ppr1-two-refusals-20260906/REPORT.md), [revised presentation](painter_prompt_retry_v1/ppr1-two-refusals-20260906-r2/REPORT.md) | Two later outputs complete the descriptive grid, without restoring original primary inference |
| [Mechanism diagnostic](painter_responsiveness_v1/prv1-diagnostic-20260908/REPORT.md), [technical pilot](painter_distribution_study_v1/pdsv1-pilot-20260906/REPORT.md) | Development and feasibility evidence |

## Historical public releases

The following receipts describe earlier versioned assets, not the current PDF.
Release tags and archive identities are recorded in their linked JSON files.
The original archives remain unchanged; redundant release prose was retired.

| Release and guide | Retained verification |
| --- | --- |
| [Core numerical release](../studies/paper_reproducibility_v1/README.md), `pprv1-20260910` | [Publication](paper_reproducibility_v1/pprv1-20260910/PUBLICATION_VERIFICATION.json), [local](paper_reproducibility_v1/pprv1-20260910/LOCAL_REPLAY.json), [Ubuntu](paper_reproducibility_v1/pprv1-20260910/HOSTED_VERIFICATION.json), [anonymous](paper_reproducibility_v1/pprv1-20260910/ANONYMOUS_REPLAY.json); [paper erratum](paper_reproducibility_v1/pprv1-20260910/PAPER_ERRATUM.md) |
| [Geometry adapter](../tools/paper_geometry_release.py), `ppgv1-20260910` | [Local replay](paper_geometry_reproducibility_v1/ppgv1-20260910/REPLAY.json), [anonymous download](paper_geometry_reproducibility_v1/ppgv1-20260910/DOWNLOAD.json) |
| [Clause addendum](../studies/paper_clause_reproducibility_v1/README.md), `pcrv1-20260910` | [Publication](paper_clause_reproducibility_v1/pcrv1-20260910/PUBLICATION.json), [local](paper_clause_reproducibility_v1/pcrv1-20260910/LOCAL_REPLAY.json), [anonymous](paper_clause_reproducibility_v1/pcrv1-20260910/ANONYMOUS_REPLAY.json) |
| [Failed map-precision adapter](../tools/paper_map_release.py), `pmrv1-20260910` | [Local](paper_map_reproducibility_v1/pmrv1-20260910/LOCAL.json), [anonymous](paper_map_reproducibility_v1/pmrv1-20260910/PUBLIC.json); the failed scientific qualification replays as failed |
| [Prospective map adapter](../tools/paper_map_validation_release.py), `pmv2r-20260910` | [Local/anonymous report](paper_map_validation_reproducibility_v2/pmv2r-20260910/REPORT.md), [strict Ubuntu failure](paper_map_validation_reproducibility_v2/pmv2r-20260910/HOSTED_REPORT.md), [historical manuscript assets](paper_map_validation_reproducibility_v2/pmv2r-20260910/PAPER_ASSETS.json) |
| [Separate portability diagnostic](paper_map_portability_diagnostic_v1/pmpdv1-20260910/REPORT.md) | Support-hash mismatches and small floating differences; preserves the failed strict contract |

Successful replay of compact vectors does not authenticate absent artwork,
establish an independent research team or validate perceptual style. Exact
cross-platform replay is not claimed where it failed.

## Retention

Numerical JSON/CSV, report figures, memberships, provenance and release receipts
remain at their original paths because analyses and verification bind them.
Superseded reviews and duplicate authored summaries are recoverable from Git;
see [artifact retention](../docs/ARTIFACTS.md#retired-documentation).
