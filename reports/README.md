# Results index

Start with the primary experiment, its post-result diagnostics and the
retrospective analyses behind the TMLR manuscript. Other directories contain
supporting or historical evidence at their recorded paths; every result
directory is a record and keeps its original bytes. For source code, plotting
and offline commands, see [the analysis catalog](../docs/ANALYSES.md).

## Current experiment

| Result | Contents |
| --- | --- |
| [Six-model artist specificity](painter_specificity_v2/psv2-20260911/REPORT.md) | Primary slopes, paired model comparisons, all four artists and accounting; full values in sibling CSVs |
| [Reference-target diagnostics](painter_specificity_review_v1/REPORT.md) | Scene decomposition, calibrated response, artist pairs, reference controls and limitations; [numerical record](painter_specificity_review_v1/analysis.json) |
| [Diagnostic clarification](painter_specificity_review_v2/REPORT.md) | Shared-control correction, sampling-integrated real controls, calibrated stability and broader noise simulations |
| [Reference quality](painter_reference_quality_v1/REPORT.md) | Audit of 870 source reproductions; separate region, scaler and visual-class sensitivities, with original measurements preserved |
| [Current image examples](../paper/example_selection.json) | Selection rules, prompts, source identities, rights metadata, crop boxes and hashes for the manuscript's 40 example images |
| [Historical image inspection](painter_specificity_review_v1/inspection.json) | Preserved full-frame examples before the source-quality corrections; separate from the current presentation |

[Status](../docs/STATUS.md) summarizes these results and what remains
unresolved. The six-model study does not yet have a dedicated versioned release.

## Retrospective analyses

Added 2026-09-18 to 2026-09-21. Each reuses previously exposed data under a plan
fixed before its new outcomes; none collects new observations.

| Result | Contents |
| --- | --- |
| [Direct naming decomposition](painter_specificity_review_v3/report.md) | Named-minus-generic common/specific split, interaction term and scene deletion; [interpretation note](painter_specificity_review_v3/interpretation.md) |
| [Request timing](painter_request_timing_v1/REPORT.md) | Within-cell linear drift with held-scene predictive gain |
| [Learned representations](painter_learned_audit_v1/REPORT.md) | CLIP and CSD vectors for all 1,878 original images plus 131 audited views; [extraction review](painter_learned_audit_v1/EXTRACTION_REVIEW.md) and [implementation notes](painter_learned_audit_v1/IMPLEMENTATION_NOTES.md) |
| [Held-scene prompt-name transfer](painter_prototype_transfer_v1/REPORT.md) | All 48 encoder/view/target/configuration conditions and three decision rules |
| [Repeat covariance scenarios](painter_repeat_covariance_v1/REPORT.md) | Primary-D curves under fixed hypothetical cross-repeat correlations |
| [Separate SD-Turbo collection](painter_cross_cohort_v1/REPORT.md) | 2,000 retained images, 25 paired-seed blocks; [implementation](painter_cross_cohort_v1/IMPLEMENTATION.md) |
| [Selective attribution](painter_selective_attribution_v1/REPORT.md) | Reference-calibrated abstention against matched-margin filtering; [pre-outcome readiness](painter_selective_attribution_v1/PRE_OUTCOME_READINESS.md) |
| [Family-control preparation](painter_family_controls_v1/README.md) | Offline qualification of an uncollected, unapproved prospective study; no observations |
| [TMLR revision diagnostics](painter_tmlr_diagnostics_v1/REPORT.md) | Faithful-imitation and exchangeable benchmarks for the shared fraction, its direction, feature-family and weighting sensitivity, and scene-bootstrap stability of the readouts; added 2026-10-01 for the TMLR revision |
| [TMLR revision diagnostics v2](painter_tmlr_diagnostics_v2/REPORT.md) | Exact-differences benchmark, scene and reference intervals for the new quantities, joint resampling of D, 31-feature separability and SD-Turbo benchmarks; added 2026-10-01 |
| [TMLR revision diagnostics v3](painter_tmlr_diagnostics_v3/REPORT.md) | Genuine-painting controls with two distinct works per pseudo-repeat in all three representations, CLIP and CSD agreement intervals, normalized-prototype shares and paired feature-family contrasts; added 2026-10-01 after the round-3 reviews |
| [TMLR revision diagnostics v4](painter_tmlr_diagnostics_v4/REPORT.md) | CLIP and CSD agreement against title-derived content-class targets on the 11 non-mixed scenes, with scene intervals; added 2026-10-01 after the round-4 reviews |
| [TMLR revision diagnostics v5](painter_tmlr_diagnostics_v5/REPORT.md) | Direction-only agreement (alignment ratio, held-out rescaled error) and its scene stability in all three representations, the split of D along and off the reference pattern in the embeddings, Student intervals, repeat-dependence thresholds, proximity correlations across configurations and configuration distinctness; added 2026-10-01 after the round-5 reviews |

## Review records

Each score applies to its recorded manuscript hash. These are internal AI
assessments, separate from the scientific results above; see
[the paper guide](../paper/README.md#review-records) for a summary.

| Record | Contents |
| --- | --- |
| [TMLR review](tmlr_review_v1/README.md) | Rubric and subagent review rounds of the TMLR manuscript, with revision records |
| [ICML scientific review](icml_review_v1/README.md) | Rubric, four review rounds of the retired ICML draft and its exact sources, revision records, independent audits, prospective-control proposals and the local numerical bundle |
| [Editorial review](paper_editorial_review_v1/README.md) | Reader-experience rubric, 33 internal rounds, paired external reviews and final-update decisions for the full-length paper |
| [External reviews, 2026-09-13](../critics/ASSESSMENT.md) | Three reviews of the full-length paper and their assessment |

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
Retired reviews and duplicate authored summaries are recoverable from Git;
see [artifact retention](../docs/ARTIFACTS.md#retired-documentation).
