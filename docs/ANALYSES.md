# Analysis catalog

This is the navigation map for computation, plotting and reproduction. Run commands
from the repository root. **Current** identifies the evidence used by `paper/`;
**terminal** means a completed scientific bundle that must remain unchanged.
Historical development analyses remain useful context, but are not new confirmation
evidence. See [STATUS.md](STATUS.md) for the current paper-correction phase.

The [Makefile](../Makefile) provides the common entry points:

| Command | Scope |
| --- | --- |
| `make check` | Ruff and the complete offline test suite |
| `make evidence` | Historical evidence bindings, dispositions and retained-byte integrity |
| `make four-painter-analysis` | Replay four-painter exploration, Stage A controls and retry presentation (35 + 18 + 9 files) |
| `make analysis` | Replay Study 1 controlled and revision numeric results |
| `make plots` | Replay Study 1 controlled and revision report bundles and check manuscript figures |
| `make responsiveness` | Replay the earlier v1 responsiveness diagnostic JSON and all report bytes |
| `make computational-responsiveness` | Replay v2 scene retrieval, both completed experiment bundles, the quantile correction and their report bytes |
| `make palette-check` | Recompute Study 2 primary inference from committed chroma outcomes and the fixed schedule; no raw-response reads |
| `make validation-check` | Replay the computational challenge and all eight common-square contrasts |
| `make replication-check` | Replay the terminal temporal cohort from its retained measurements |
| `make figures` | Rebuild nine manuscript figures from retained numeric inputs |
| `make figures-check` | Check all nine manuscript figures without rewriting them or replaying full reports |
| `make paper` | Rebuild figures and compile the manuscript; see [paper/README.md](../paper/README.md) |

Numeric and report checks use temporary output and preserve the published bundles.
An evidence audit checks integrity; it is not necessarily a numeric recomputation.
Use the recorded implementation and locked runtime. Investigate a mismatch against
its recorded commit rather than changing a stored hash. Raw-byte audits may require
the ignored local research workspace. The commands below do not contact providers.

## Current evidence and presentation

Each input link identifies the complete recorded dependency list, in addition to
the principal data described here. Source paths are relative to
`src/latent_art_bench/`; they deliberately retain their study namespaces.

| Analysis and status | Methods | Computation | Plotting | Numeric inputs and published result |
| --- | --- | --- | --- | --- |
| **Distribution exploration** — current descriptive evidence, terminal / `painter_distribution_exploration_v1` | [Methods](../studies/painter_distribution_exploration_v1/METHODS.md) | [analysis.py](../src/latent_art_bench/painter_distribution_exploration_v1/analysis.py), [statistics.py](../src/latent_art_bench/painter_distribution_exploration_v1/statistics.py) | [report.py](../src/latent_art_bench/painter_distribution_exploration_v1/report.py) | Completed retry grid and 649 references: [provenance](../reports/painter_distribution_exploration_v1/provenance.json) → [PCA, grouped detection and spread report](../reports/painter_distribution_exploration_v1/REPORT.md). Scatter plots use the 1,536 named outputs. |
| **Controlled-study Stage A diagnostics** — current descriptive evidence, terminal / `pdsv1-diagnostics-20260906` | [Diagnostic scope](../studies/painter_distribution_study_v1/DIAGNOSTICS.md) | [diagnostics.py](../src/latent_art_bench/painter_distribution_study_v1/diagnostics.py) | Same module; saved Stage A reports | Historical 649 references and completed 1,920-output grid, plus coarse scene mappings: [freeze](../data/manifests/painter_distribution_study_v1/pdsv1-diagnostics-20260906/freeze.json) → [content, reference-baseline, PCA and transfer diagnostics](../reports/painter_distribution_study_v1/pdsv1-diagnostics-20260906/REPORT.md). These precede and remain separate from the later 70-reference controlled panel. |
| **Retry presentation revision** — current descriptive evidence, terminal / `ppr1-two-refusals-20260906-r2` | [Retry protocol](../studies/painter_prompt_retry_v1/PROTOCOL.md); presentation only | No new analysis | [painter_prompt_retry_report_v2.py](../src/latent_art_bench/painter_prompt_retry_report_v2.py) | Sealed retry `analysis.json`: [revision receipt](../data/manifests/painter_prompt_retry_v1/ppr1-two-refusals-20260906/report_revision_2.json) → [revised plot presentation](../reports/painter_prompt_retry_v1/ppr1-two-refusals-20260906-r2/REPORT.md). Both report versions are retained. |
| **Computational revision** — current, terminal; `pdrv1-numeric-20260907` | [Protocol](../studies/painter_distribution_revision_v1/PROTOCOL.md) | [analysis.py](../src/latent_art_bench/painter_distribution_revision_v1/analysis.py), [metrics.py](../src/latent_art_bench/painter_distribution_revision_v1/metrics.py), [diagnostics.py](../src/latent_art_bench/painter_distribution_revision_v1/diagnostics.py), [timing.py](../src/latent_art_bench/painter_distribution_revision_v1/timing.py) | [report.py](../src/latent_art_bench/painter_distribution_revision_v1/report.py); [publication/check](../src/latent_art_bench/painter_distribution_revision_v1/report_publication.py) | Controlled reference/generated/development vectors, metadata and ledgers: [103-input freeze](../data/manifests/painter_distribution_revision_v1/pdrv1-numeric-20260907/freeze.json). [Sealed numeric JSON](../data/manifests/painter_distribution_revision_v1/pdrv1-numeric-20260907/analysis.json) → [report, 31 CSVs and six figure pairs](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md). |
| **Controlled distribution study** — current source evidence, terminal; `pdsv1-analysis-20260907` | [Protocol](../studies/painter_distribution_study_v1/PROTOCOL.md), [main design](../studies/painter_distribution_study_v1/MAIN.md), [inference](../studies/painter_distribution_study_v1/INFERENCE.md), [publication adapter](../studies/painter_distribution_study_v1/ANALYSIS_PUBLICATION.md) | [analysis.py](../src/latent_art_bench/painter_distribution_study_v1/analysis.py), [statistics.py](../src/latent_art_bench/painter_distribution_study_v1/statistics.py); [numeric publication/check](../src/latent_art_bench/painter_distribution_study_v1/analysis_publication.py) | [main_report.py](../src/latent_art_bench/painter_distribution_study_v1/main_report.py) | 70 references, 1,006 generated images and 221 development works, measured under three pipelines: [publication freeze](../data/manifests/painter_distribution_study_v1/pdsv1-analysis-20260907/publication_freeze.json). [Numeric receipt](../data/manifests/painter_distribution_study_v1/pdsv1-analysis-20260907/analysis_receipt.json) → [report, tables and PCA coordinates](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md). |
| **Six summary figures** — current, editable presentation | [Manuscript/build guide](../paper/README.md) | No new statistics or PCA fit | [make_figures.py](../paper/make_figures.py) | Eight hash-checked inputs: exploration `points.csv` / `projections.json`, revision `metric_cells.csv` / `prompt_contrasts.csv`, controlled `projection_points.csv`, and responsiveness `retrieval_comparisons.csv` / `arm_means.csv` / `primary.csv` (seven CSVs and one JSON) → six PDFs in [paper/figures](../paper/figures/). |
| **Palette numerical replay and block display** — current, post-result presentation | [Review and scope](reviews/20260909_academic_review/REVIEW.md), paper Appendix E | [replay_palette.py](../paper/replay_palette.py) calls the unchanged factorial inference primitive; adds descriptive block signs and scene variance shares | Same script → [palette_blocks.pdf](../paper/figures/palette_blocks.pdf) | Three hash-checked compact inputs: chroma outcomes, request schedule and saved primary results. Replays the same primary estimates/intervals, then displays all 24 blocks per painter in collection order. This does not verify transport bytes, source pixels, measurement validity or repeat independence. |

The four-painter section restores 649 references (297 Monet, 106 Sisley, 141
Pissarro and 105 Cézanne) and 1,536 painter-conditioned outputs. The underlying
completed retry grid also contains 384 artist-free controls. Exploration, Stage A
controls and retry contrasts are post-result descriptive evidence; they do not
restore the incomplete original study's primary inference. The requested
`gpt-image-1` / `gpt-image-2` aliases are service labels, not verified distinct
model identities. The two later retry outcomes remain identified. This cohort
is separate from the 70-reference, 1,006-output controlled study and the later
192-image color experiment.

The revision's [metrics module](../src/latent_art_bench/painter_distribution_revision_v1/metrics.py)
owns feature-view comparisons, within/between-description variation, reference
influence, development-scaler omissions, painter specificity and identical-payload
controls. Its
[diagnostics module](../src/latent_art_bench/painter_distribution_revision_v1/diagnostics.py)
owns coverage curves and held-out-real controls, metadata associations and square
baselines, and cross-route detection with saved splits. Its
[timing module](../src/latent_art_bench/painter_distribution_revision_v1/timing.py)
owns request timing and per-attempt dispositions/costs; study accounting is
assembled by the analysis orchestrator.
All are rendered from the same sealed numeric JSON; the report renderer does not
recompute those scientific analyses.

Direct equivalents of the current Makefile replay targets:

```bash
uv run --locked python -m latent_art_bench.painter_distribution_exploration_v1.report check
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.diagnostics check
uv run --locked python -m latent_art_bench.painter_prompt_retry_report_v2 check
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.analysis_publication check
uv run --locked python -m latent_art_bench.painter_distribution_revision_v1.analysis check
uv run --locked python -m latent_art_bench.painter_distribution_study_v1.main_report check
uv run --locked python -m latent_art_bench.painter_distribution_revision_v1.report_publication check
uv run --locked python paper/make_figures.py --check
```

## Measurement and temporal follow-up

The September 10 successors preserve the original cohorts and scalers. The
[measurement protocol](../studies/painter_measurement_validation_v1/PROTOCOL.md)
fixes ten conditions on all 70 Study 1 references and central-square extraction
on all 1,006 generated images. Its
[pipeline](../src/latent_art_bench/painter_measurement_validation_v1/pipeline.py)
verifies identities, extracts once and replays the calculations; its
[statistics](../src/latent_art_bench/painter_measurement_validation_v1/statistics.py)
compute paired processing challenges, descriptive work-bootstrap intervals and
all original energy contrasts. The
[report renderer](../src/latent_art_bench/painter_measurement_validation_v1/report.py)
produces the [complete results](../reports/painter_measurement_validation_v1/pmvv1-20260910/REPORT.md).
The editable [manuscript renderer](../paper/make_validation_figure.py) supplies
the eighth figure from that saved analysis, with byte-for-byte checking.
The frozen geometry figure uses the shorthand “generic” for the original
short-scene named condition; the manuscript correctly labels it detailed minus
short scene. Both conditions name the painter.

The [temporal replication protocol](../studies/painter_naming_replication_v1/PROTOCOL.md)
allocates 72 FLUX naming outputs and 192 OAuth palette outputs in a new collection.
Its [collector](../src/latent_art_bench/painter_naming_replication_v1/collection.py)
uses two bounded workers, spaced starts, fixed whole blocks and exact qualified
retries. Its [analysis](../src/latent_art_bench/painter_naming_replication_v1/analysis.py)
reuses the original energy and palette primitives with a new four-endpoint Holm
family; [workflow](../src/latent_art_bench/painter_naming_replication_v1/workflow.py)
separates collection, measurement, numerical replay and private-response checks.
Operational completion is recorded in [STATUS.md](STATUS.md); live commands are
never invoked by Makefile replay targets. The new collection is temporal
replication by the same maintainer, without independent investigators or verified
independent backend states.

The [public reproduction adapter](../tools/paper_release.py) exports compact
inputs and invokes unchanged scientific functions in an isolated environment.
Its [release guide](../studies/paper_reproducibility_v1/README.md) distinguishes
numerical replay, private-pixel verification and actual public access. The core
export and each successor extension are separate create-once records, with no
pooling or overwrite of original evidence. The [public verification report](../reports/paper_reproducibility_v1/pprv1-20260910/REPORT.md) records the completed archive, hosted and anonymous checks.

## Computational intervention without human ratings

The [v2 protocol](../studies/painter_responsiveness_v2/PROTOCOL.md) defines the completed
192-image, four-arm, two-polarity OAuth experiment. The
[scientific synthesis](../reports/painter_responsiveness_v2/REPORT.md) connects its
results to the original paintings and scene-retrieval findings. It estimates two named-minus-generic
chroma-response interactions with shared controls. It does not identify human style
fidelity or an internal training mechanism. The retained-data diagnostic additionally
tests whether contraction reduces held-repetition scene retrieval.

| Component | Computation / plotting | Inputs and output |
| --- | --- | --- |
| Scene retrieval | [diagnostics.py](../src/latent_art_bench/painter_responsiveness_v2/diagnostics.py) | Exposed controlled-study vectors; 24-scene and within-class retrieval, all three pipelines and five feature views |
| Prospective intervention | [analysis.py](../src/latent_art_bench/painter_responsiveness_v2/analysis.py) | 192 planned outputs, old fixed scalers and already measured 70-reference panel; two primary interactions, descriptive processing/coordinate/reference comparisons |
| Collection, measurement and replay | [workflow.py](../src/latent_art_bench/painter_responsiveness_v2/workflow.py), [collection.py](../src/latent_art_bench/painter_responsiveness_v2/collection.py) | Exact committed request inventory, source/proxy freeze, all-slot ledger, raw-response and measurement bindings |
| Scientific reports and plots | [report.py](../src/latent_art_bench/painter_responsiveness_v2/report.py) | Saved numerical results → [retrieval](../reports/painter_responsiveness_v2/prv2-oauth-20260908/diagnostics/REPORT.md), [primary experiment](../reports/painter_responsiveness_v2/prv2-oauth-recovery-20260908/experiment/REPORT.md) and [ancillary predecessor](../reports/painter_responsiveness_v2/prv2-oauth-20260908/experiment/REPORT.md) |
| Exact-weight quantile correction | [painter_responsiveness_quantiles_v1.py](../src/latent_art_bench/painter_responsiveness_quantiles_v1.py), [protocol](../studies/painter_responsiveness_quantiles_v1/PROTOCOL.md) | Both sealed experiment JSONs → [corrected medians and reference-context plots](../reports/painter_responsiveness_quantiles_v1/prqv1-20260908/REPORT.md); primary inference, means, Wasserstein distances and range occupancy are unchanged |

`make computational-responsiveness` recomputes saved-vector
analyses and compares report bytes offline. The primary intervention is the
[prospectively designated replacement](../studies/painter_responsiveness_recovery_v1/PROTOCOL.md),
`prv2-oauth-recovery-20260908`; the original partial run is ancillary. The recovery
package changes only qualification of one exact plain-text 503 response. It
reuses the unchanged v2 analysis and renderer. Replay verifies raw-response hashes
and therefore needs the retained local response archive. It never sends generation
requests or extracts image features. The [implementation guide](../studies/painter_responsiveness_v2/README.md)
separates explicit live collection from replay. The earlier human-reference v1
scope below remains preserved and has not been retrospectively qualified.

The final target also runs
`uv run --locked python -m latent_art_bench.painter_responsiveness_quantiles_v1 check`.
This replays the versioned descriptive quantile correction from committed numeric
inputs. It verifies exact rational CDF boundaries and all nine correction report
files without duplicating or modifying the earlier 65-file publication.

## Preserved responsiveness v1 scope

The earlier `painter_responsiveness_v1` namespace implements the
[mechanism proposal](RESEARCH_IDEA_20260908.md). Its
[protocol and continuation guide](../studies/painter_responsiveness_v1/README.md)
separate completed retained-data diagnostics from prospective generation and
actual human validation. Its diagnostic is complete; human validation is
unperformed and its preflight is closed. No stage is active. The manuscript does
not establish a causal mechanism or perceptual conclusion.

| Component | Code | Evidence / output |
| --- | --- | --- |
| Equal-brief empirical and cross-repeat diagnosis; reference chroma support | [analysis.py](../src/latent_art_bench/painter_responsiveness_v1/analysis.py) | Original 31-feature vectors and metadata, unchanged; all six named/free cells and all 70 retained references |
| Factorial order, shared-control inference and simulation | [design.py](../src/latent_art_bench/painter_responsiveness_v1/design.py), [inference.py](../src/latent_art_bench/painter_responsiveness_v1/inference.py) | Fixed six-template × four-arm × two-polarity × four-repeat, 192-slot design; 18 noise/effect settings |
| Diagnostic publication and plotting | [workflow.py](../src/latent_art_bench/painter_responsiveness_v1/workflow.py), [report.py](../src/latent_art_bench/painter_responsiveness_v1/report.py) | [Diagnostic report](../reports/painter_responsiveness_v1/prv1-diagnostic-20260908/REPORT.md), full numeric JSON, tables and three plot pairs |
| Human reference qualification | [human_package.py](../src/latent_art_bench/painter_responsiveness_v1/human_package.py), [reference_validation.py](../src/latent_art_bench/painter_responsiveness_v1/reference_validation.py) | Blinded reference preview and actual-response import; pilot and validation remain distinct |
| Gated generation and measurement | [generation_prepare.py](../src/latent_art_bench/painter_responsiveness_v1/generation_prepare.py), [collection.py](../src/latent_art_bench/painter_responsiveness_v1/collection.py), [measurement.py](../src/latent_art_bench/painter_responsiveness_v1/measurement.py) | Prospective implementation only; no live generation until actual reference/human/precision/provider evidence passes |

`make responsiveness` recomputes diagnostic numbers and compares every rendered
report byte. It is offline and does not open artwork pixels. New-study checks are
separate from the historical `make evidence` audit. The human H0 preview normalizes
only already exposed reference bytes under an exact-source freeze; it is not a
new scientific measurement or human judgment.

## Earlier generated-versus-original analyses

These rows are **terminal upstream evidence or development context** for the
current analyses above. Replay commands below follow the same order. The original 1,920-slot prompt study had
1,918 measured successes. Its complete-grid primary remains unavailable; the
available-output supplement and later two-image retry are distinct analyses.

| Analysis / run | Methods | Computation and plotting | Numeric inputs → report |
| --- | --- | --- | --- |
| **Feature-distance report** / `painter_feature_distance_v1` | [Feature-distance methods](FEATURE_DISTANCE_ANALYSIS.md) | [analysis.py](../src/latent_art_bench/painter_feature_distance_v1/analysis.py); plots in [report.py](../src/latent_art_bench/painter_feature_distance_v1/report.py); [replay CLI](../src/latent_art_bench/painter_feature_distance_v1/cli.py) | v2's 649 confirmation references, 221 development works, 2,000 SD-Turbo and 160 OAuth outputs; [input/output provenance](../reports/painter_feature_distance_v1/provenance.json) → [distances, coordinate diagnostics and equal-count block plots](../reports/painter_feature_distance_v1/REPORT.md). |
| **Initial prompt study** / `pps1-gpt-prompts-20260905` | [Protocol](../studies/painter_prompt_study_v1/PROTOCOL.md) | [analysis.py](../src/latent_art_bench/painter_prompt_study_v1/analysis.py), [statistics.py](../src/latent_art_bench/painter_prompt_study_v1/statistics.py); [report.py](../src/latent_art_bench/painter_prompt_study_v1/report.py), [reproduction.py](../src/latent_art_bench/painter_prompt_study_v1/reproduction.py) | [Generation freeze](../data/manifests/painter_prompt_study_v1/pps1-gpt-prompts-20260905/generation_freeze.json), measured vectors and fixed v2 references/scaler → [availability report](../reports/painter_prompt_study_v1/pps1-gpt-prompts-20260905/REPORT.md). No primary fidelity plots were published for the incomplete grid. |
| **Available-output supplement** / `ppss1-missingness-20260905` | [Protocol](../studies/painter_prompt_supplement_v1/PROTOCOL.md) | [statistics.py](../src/latent_art_bench/painter_prompt_supplement_v1/statistics.py), [artifacts.py](../src/latent_art_bench/painter_prompt_supplement_v1/artifacts.py); plots in [report.py](../src/latent_art_bench/painter_prompt_supplement_v1/report.py) | The same 1,918 outputs under fixed missingness rules: [design freeze](../data/manifests/painter_prompt_supplement_v1/ppss1-missingness-20260905/design_freeze.json) → [report and plots](../reports/painter_prompt_supplement_v1/ppss1-missingness-20260905/REPORT.md). |
| **Two-refusal retry** / `ppr1-two-refusals-20260906` | [Protocol](../studies/painter_prompt_retry_v1/PROTOCOL.md) | Computation, plotting and replay in [painter_prompt_retry_v1.py](../src/latent_art_bench/painter_prompt_retry_v1.py) | Original 1,918 vectors plus two later successes: [retry freeze](../data/manifests/painter_prompt_retry_v1/ppr1-two-refusals-20260906/retry_freeze.json) → [descriptive completed-grid report](../reports/painter_prompt_retry_v1/ppr1-two-refusals-20260906/REPORT.md), without new randomization inference. |

These checks reconstruct numerical summaries and their published presentation
from retained vectors, without re-extracting features:

```bash
uv run --locked --extra analysis --extra learned latent-art-bench feature-distances check --output reports/painter_feature_distance_v1
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli check-run pps1-gpt-prompts-20260905
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_supplement_v1.cli check ppss1-missingness-20260905
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_retry_v1 check
```

## Foundational and technical stages

These are also **terminal**. Some early stages have integrity audits but no
nonwriting numeric replay command; their create-once writers must not be used to
overwrite a retained result. Authored reports are distinguished from renderers.

| Stage | Methods and source | Inputs and outputs | Existing check |
| --- | --- | --- | --- |
| **v1 corpus census, scene-support prescreen and R1 determination** | [Canonical 2.1 protocol](../studies/painter_feature_generation_v1/PROTOCOL_2.1.md), [2.2 collection](../studies/painter_feature_generation_v1/PROTOCOL_2.2.md), [2.3 determination](../studies/painter_feature_generation_v1/PROTOCOL_2.3.md). Sources in [v1 package](../src/latent_art_bench/painter_feature_generation_v1/), especially [scene_prescreen.py](../src/latent_art_bench/painter_feature_generation_v1/scene_prescreen.py) and [determine.py](../src/latent_art_bench/painter_feature_generation_v1/determine.py). | [Metadata freezes, ledgers and determinations](../data/manifests/painter_feature_generation_v1/) → [R1 determination](../reports/painter_feature_generation_v1/R1_DETERMINATION_KO.md), [scene prescreen](../reports/painter_feature_generation_v1/SCENE_SUPPORT_PRESCREEN_KO.md), [source audit](../reports/painter_feature_generation_v1/SOURCE_ROUTE_AUDIT_KO.md), [data-readiness narrative](../reports/painter_feature_generation_v1/RESEARCH_PLAN_AND_DATA_REPORT_KO.md). No fidelity experiment or plot bundle. | `make evidence` verifies census and determination evidence. The nonbinding prescreen and authored summaries have no dedicated nonwriting replay CLI. |
| **v2 empirical baseline and crop sensitivity** / `pfg2-method-20260905` | [Protocol](../studies/painter_feature_generation_v2/PROTOCOL.md), [empirical amendment 1.2](../studies/painter_feature_generation_v2/PROTOCOL_1.2.md), [crop amendment 1.3](../studies/painter_feature_generation_v2/PROTOCOL_1.3.md). [pipeline.py](../src/latent_art_bench/painter_feature_generation_v2/pipeline.py) computes SD-Turbo repeated blocks and qualification diagnostics; [empirical.py](../src/latent_art_bench/painter_feature_generation_v2/empirical.py) computes common finite comparisons; [robustness.py](../src/latent_art_bench/painter_feature_generation_v2/robustness.py) computes paired crop sensitivity. | [Method freeze and measured stages](../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/method_freeze.json), including 649 confirmation works, 2,000 SD-Turbo and 160 OAuth outputs → [English report](../reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS.md) rendered by [report.py](../src/latent_art_bench/painter_feature_generation_v2/report.py); [Korean companion](../reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS_KO.md). No dedicated plot renderer. | `paper-study audit` below checks integrity; no nonwriting full numeric/report replay CLI. |
| **v2 image-service access assessment** / `pfg2-image-access-20260905` | [Assessment protocol](../studies/painter_feature_generation_v2/MODEL_ASSESSMENT_PROTOCOL_1.0.md); [model_assessment.py](../src/latent_art_bench/painter_feature_generation_v2/model_assessment.py), [assessment_diagnostics.py](../src/latent_art_bench/painter_feature_generation_v2/assessment_diagnostics.py). | [Assessment freeze](../data/manifests/painter_feature_generation_v2/pfg2-image-access-20260905/assessment_freeze.json), two retained neutral responses and [response diagnostics](../data/manifests/painter_feature_generation_v2/pfg2-image-access-20260905/response_diagnostics.json) → authored [access report](../reports/painter_feature_generation_v2/AVAILABLE_IMAGE_MODELS.md). No fidelity analysis or plots. | v2 integrity audit; no separate numeric replay command. |
| **Controlled-study technical pilot** / `pdsv1-pilot-20260906` | [Pilot contract](../studies/painter_distribution_study_v1/PILOT.md); computation/report/check in [pilot_summary.py](../src/latent_art_bench/painter_distribution_study_v1/pilot_summary.py). | 18 technical requests, events and retained response bodies → [summary JSON](../reports/painter_distribution_study_v1/pdsv1-pilot-20260906/summary.json) and [report](../reports/painter_distribution_study_v1/pdsv1-pilot-20260906/REPORT.md). No fidelity features or plots. | Separate offline check below **decodes retained image responses**; it is not part of numeric-only Makefile replay. |

```bash
uv run --locked --extra analysis --extra learned latent-art-bench paper-study audit
# Pilot response replay reads retained image bytes; outside numeric-only replay.
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.pilot_summary check
```

The deterministic v1 prompt library, content lexicon and exposure denylist are
protocol inputs, not separate empirical analyses. Their compatibility checks are:

```bash
uv run --locked latent-art-bench prompt-library --check
uv run --locked latent-art-bench content-lexicon --check
uv run --locked latent-art-bench exposure-denylist --check
```

## Synthetic qualification analyses

These **terminal development/validation records** assess statistical procedures;
they do not add paintings or model comparisons. They publish JSON records and
decisions rather than plots. Input parameters, seeds, source bindings and outputs
are recorded in each linked directory.

| Qualification | Methods / computation | Recorded inputs and result | Replay |
| --- | --- | --- | --- |
| v2 interval calibration | [v2 protocol](../studies/painter_feature_generation_v2/PROTOCOL.md); [calibration.py](../src/latent_art_bench/painter_feature_generation_v2/calibration.py) | [pfg2-calibration-20260905](../data/manifests/painter_feature_generation_v2/pfg2-calibration-20260905/) | v2 integrity audit only; no dedicated nonwriting simulation replay CLI. |
| Prompt interval development | [Prompt protocol](../studies/painter_prompt_study_v1/PROTOCOL.md); [calibration.py](../src/latent_art_bench/painter_prompt_study_v1/calibration.py), [calibration_record.py](../src/latent_art_bench/painter_prompt_study_v1/calibration_record.py) | [pps1-calibration-20260905](../data/manifests/painter_prompt_study_v1/pps1-calibration-20260905/) | First command below. |
| Prompt randomization qualification | Same prompt protocol; [randomization.py](../src/latent_art_bench/painter_prompt_study_v1/randomization.py), [randomization_record.py](../src/latent_art_bench/painter_prompt_study_v1/randomization_record.py) | [pps1-randomization-20260905](../data/manifests/painter_prompt_study_v1/pps1-randomization-20260905/) | Second command below. |
| Missingness supplement qualification | [Supplement protocol](../studies/painter_prompt_supplement_v1/PROTOCOL.md); [validation.py](../src/latent_art_bench/painter_prompt_supplement_v1/validation.py), [artifacts.py](../src/latent_art_bench/painter_prompt_supplement_v1/artifacts.py) | [ppss1-qualification-20260905](../data/manifests/painter_prompt_supplement_v1/ppss1-qualification-20260905/) | Third command below. |
| Controlled prompt inference qualification | [Inference contract](../studies/painter_distribution_study_v1/INFERENCE.md); [inference.py](../src/latent_art_bench/painter_distribution_study_v1/inference.py) | [pdsv1-inference-20260906](../data/manifests/painter_distribution_study_v1/pdsv1-inference-20260906/) | Fourth command below. |

```bash
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli reproduce-interval-development pps1-calibration-20260905
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_study_v1.cli reproduce-randomization pps1-randomization-20260905
uv run --locked --extra analysis --extra learned python -m latent_art_bench.painter_prompt_supplement_v1.cli check-qualification ppss1-qualification-20260905
uv run --locked --extra analysis python -m latent_art_bench.painter_distribution_study_v1.inference check
```

## Code and test organization

[src/latent_art_bench/](../src/latent_art_bench/) and [tests/](../tests/) mirror
the study namespaces above. The retry analysis and its presentation revision use
standalone modules with matching `tests/test_painter_prompt_retry_*.py` files.
Shared I/O and evidence utilities remain at package root; reused feature and
statistical primitives remain in the historical packages that defined them.
Moving those modules or their tests would change recorded evidence identities.

The root CLI retains older public commands. Later studies expose their own
`python -m` entry points, and the Makefile groups the current checks without
introducing another Python dispatcher. Retained [scripts/](../scripts/) are
freeze-bound collection launchers or compatibility aliases. They are not the
place to add new analysis or plotting logic. For new scientific work, use a new
study namespace and add its computation, renderer, inputs and replay here.

Current pytest runner settings are in [pytest.ini](../pytest.ini). Importlib mode
allows versioned studies to reuse test filenames; two legacy helper-import paths
are retained explicitly. The old pyproject configuration is a frozen scientific
input and remains unchanged.

## Post-result naming geometry

| Analysis | Methods / results | Source and plotting | Replay |
| --- | --- | --- | --- |
| Whole-scene moment maps, original-map temporal transfer, corrected conditional variance | [Protocol](../studies/painter_naming_geometry_v1/PROTOCOL.md); [report](../reports/painter_naming_geometry_v1/pngv1-20260910/REPORT.md) | `src/latent_art_bench/painter_naming_geometry_v1/`; immutable `report.py` figure, with a separate readable manuscript display in [make_geometry_figure.py](../paper/make_geometry_figure.py) | `uv run --locked python -m latent_art_bench.painter_naming_geometry_v1 verify` |
| Evaluation-free centering at unchanged scalar/displacement | [Protocol](../studies/painter_naming_centering_v1/PROTOCOL.md); [report](../reports/painter_naming_centering_v1/pncv1-20260910/REPORT.md) | `src/latent_art_bench/painter_naming_centering_v1/`; no additional figure | `uv run --locked python -m latent_art_bench.painter_naming_centering_v1 verify` |

Both namespaces are terminal, post-result retained-vector analyses with 60
original and 18 transfer views each. Their own source/input bindings and exact
replay are required in addition to the historical evidence audit. They neither
reopen prior collections nor replace the public predecessor release.


## Actual-clause validation and final successor

| Scope | Design / source | Replay and boundary |
| --- | --- | --- |
| `painter_clause_validation_v1/pcvv1-20260910` | [Protocol](../studies/painter_clause_validation_v1/PROTOCOL.md), [precision assessment](../studies/painter_clause_validation_v1/PRECISION.md); `src/latent_art_bench/painter_clause_validation_v1/` | `make clause-check` after its terminal measurement receipt. 288 allocated outputs, 211 returned; both primary tests and complete-grid secondary summaries unavailable. |
| `painter_clause_successor_v1/pcsv1-20260910` | [Protocol](../studies/painter_clause_successor_v1/PROTOCOL.md), [fixed availability-triggered decision](../studies/painter_clause_successor_v1/DESIGN_DECISION.md); `src/latent_art_bench/painter_clause_successor_v1/` | `make clause-successor-check`. Complete: 96 fresh outputs, 288 vectors; Cezanne−generic energy −1.195419353, p=.00001 at alpha .025; observed trace ratio .552327. |

Both scopes preserve all 31 features and three fixed pipelines. Their `analysis.py`
files compute statistics and render numerical reports; no new scatter basis or
figure is fitted. The manuscript summarizes the actual terminal outcomes in
a compact table. The successor has no free arm, maps/Q or conditional-variance
endpoints. Original results cannot be repaired by pooling or complete cases.
There is no further replacement if the single successor fails or is unresolved.

The [clause public adapter](../studies/paper_clause_reproducibility_v1/README.md)
is a [published numerical addendum](../reports/paper_clause_reproducibility_v1/pcrv1-20260910/REPORT.md).
It replays both cohorts separately from compact measurements, with exact fresh
local and anonymous replay and 152 tests/eight explicit skips per environment. Local `verify-responses` additionally
checks private retained response hashes without decoding/re-extracting images.

## Prospective fixed-map precision and validation

| Scope | Contract and retained result | Computation / boundary |
| --- | --- | --- |
| Failed `painter_map_validation_v1/pmvqv1-20260910` | [Precision protocol](../studies/painter_map_validation_v1/PRECISION_PROTOCOL.md), [81-cell result](../studies/painter_map_validation_v1/pmvqv1-20260910/PRECISION.md) | Immutable `painter_map_validation_v1/precision.py`; 96/144/192-output candidates all fail the fixed Q-width criterion. Formal writer is closed. |
| Single `painter_map_validation_v2/pmvqv2-20260910` assessment | [Redesign decision](../studies/painter_map_validation_v2/DECISION.md), [precision protocol](../studies/painter_map_validation_v2/PRECISION_PROTOCOL.md), [27-cell result](../studies/painter_map_validation_v2/pmvqv2-20260910/PRECISION.md) | V2 imports unchanged v1 primitives; R10/240 outputs passes historical-proxy criteria. The formal assessment is complete and must not be rerun. Separate operational qualification precedes collection. |

No images or fitted plots are produced by either qualification. The proposed
[scientific comparison](../studies/painter_map_validation_v2/PROTOCOL.md) has two
fixed primary endpoints, with all-31-feature primary512 measurement only.
There is no further allocation assessment if its collection is unavailable or
its actual uncertainty is unresolved.

The [technical contract](../studies/painter_map_validation_v2/TECHNICAL_PROTOCOL.md)
is qualified and its sole collection/measurement is complete: 240/240 vectors.
Do not rerun `prepare`, `metadata`, `collect` or `measure`. The
[two-endpoint report](../reports/painter_map_validation_v2/pmv2-20260910/REPORT.md)
gives deltaE −.390187 and deltaQ −5.046510, with both approximate intervals
below zero. Thus both targets favor translation/scaling on the new panel;
the historical opposing ordering does not transfer. The observed Q half-width
2.833 exceeds the proxy planning threshold, illustrating its limited forecast.
`analysis.py` uses fixed maps and qualified jackknife primitives; it fits no
plotting basis or new map. The manuscript uses a compact endpoint table.
The ordinary offline `uv run --locked python -m latent_art_bench.painter_map_validation_v2 check`
authenticates retained private response costs and replays numerical rows without
extracting features again; the terminal audit passed this check. It is not a
public-pixels check. The separate [public adapter and numerical archive](../reports/paper_map_validation_reproducibility_v2/pmv2r-20260910/REPORT.md)
pass exact fresh local/anonymous replay of all 27 qualification cells and the
observed analysis/report, with 75 tests each. From its extracted root, verify
with `python -I -S tools/paper_map_validation_release.py verify --root .`,
install the locked Python 3.13.11 environment, then run
`uv run --locked python tools/paper_map_validation_release.py check --root .`.
A [strict Ubuntu attempt](../reports/paper_map_validation_reproducibility_v2/pmv2r-20260910/HOSTED_REPORT.md)
fails the qualification comparison before reaching observed replay; passing
synthetic tests and inventory checks do not replace that failed numerical check.

The separate [completed diagnostic](../reports/paper_map_portability_diagnostic_v1/pmpdv1-20260910/REPORT.md)
retains actual reconstructed objects and field differences without invoking the
formal qualification writer. Its source is `tools/paper_map_portability_diagnostic.py`,
with 31 artificial tests. Ubuntu's 27 qualification failures are support hashes;
all other numerical differences are below 4e-15. Observed displayed tables match,
but exact JSON/report checks fail. This does not repair the closed strict route.
The fixed-support portable proposal is deferred at the user's stopping instruction.
No new qualification, support export, data collection or review round is pending.

The [final manuscript assets](../reports/paper_map_validation_reproducibility_v2/pmv2r-20260910/PAPER_ASSETS.md)
contain the unchanged nine figures and a 39-page paper. Fresh standalone source
compilation matches all page text/pixels, and anonymous access checks match all
asset hashes. The fixed-map result is a table, not a new fitted plot.

The failed v1 grid has a separately verified [public numerical archive](../reports/paper_map_reproducibility_v1/pmrv1-20260910/REPORT.md).
From the extracted `pmrv1-20260910/` archive root, first verify with
`python -I -S tools/paper_map_release.py verify --root .`, install its locked
environment, then use `uv run --locked python tools/paper_map_release.py check --root .`.
This replays in memory and compares all 81 cells without invoking the terminal
writer. All values match exactly in fresh local and anonymous-download Mac
environments; exact reconstructed support hashes limit portability claims.
