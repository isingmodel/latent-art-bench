# Documentation index

Use this index to distinguish current deliverables and guidance from preserved study evidence.
Frozen and hash-bound records retain their original paths because those paths are evidence
identities.

## Current guidance

- [Current status and boundary](STATUS.md)
- [Detailed English agent handover](AGENT_HANDOVER.md)
- [Root README](../README.md)
- [Architecture map](ARCHITECTURE.md)
- [Artifact retention policy](ARTIFACTS.md)
- [Agent guide](../AGENTS.md)
- [Config index](../configs/README.md)
- [Contributing](../CONTRIBUTING.md)

## Active controlled-distribution research round

- [Expansion decision, controlled study design and $100 budget](RESEARCH_PROPOSAL_20260906.md)
- [Authorized staged execution protocol](../studies/painter_distribution_study_v1/PROTOCOL.md)
- [Fixed existing-data diagnostic methods](../studies/painter_distribution_study_v1/DIAGNOSTICS.md)
- [Completed existing-data diagnostic report](../reports/painter_distribution_study_v1/pdsv1-diagnostics-20260906/REPORT.md)
- [Technical endpoint pilot and $75 spending contract](../studies/painter_distribution_study_v1/PILOT.md)
- [Reference identity screen, acquisition and content-coding contract](../studies/painter_distribution_study_v1/REFERENCES.md)
- [Completed technical pilot qualification](../reports/painter_distribution_study_v1/pdsv1-pilot-20260906/REPORT.md)
- [Wikimedia delivery correction and reduced reference panel](../studies/painter_distribution_study_v1/REFERENCE_DELIVERY_R2.md)
- [Conditional prompt inference and synthetic qualification](../studies/painter_distribution_study_v1/INFERENCE.md)
- [Controlled main study: reference mixture, requests and analysis](../studies/painter_distribution_study_v1/MAIN.md)
- [User-requested staggered parallel execution](../studies/painter_distribution_study_v1/PARALLEL_COLLECTION.md)
- [Main-study execution and reproduction commands](DISTRIBUTION_STUDY_WORKFLOW.md)
- [User-authorized bounded retry policy](../studies/painter_distribution_study_v1/RETRY_AMENDMENT.md)
- [Prepared human construct-validation follow-up](../studies/painter_distribution_study_v1/HUMAN_FOLLOWUP.md)
- [English paper prototype and build instructions](../papers/painter_distribution_study_v1/README.md)

Implementation authorized: two additional model families, two existing painter cases,
content/capture controls and a focused prompt intervention. See current status for stage progress.

## Distribution scatter and separability exploration

- [Original versus generated distributions: figures and results](../reports/painter_distribution_exploration_v1/REPORT.md)
- [Post-hoc methods and interpretation boundaries](../studies/painter_distribution_exploration_v1/METHODS.md)
- [Reproduction module](../src/latent_art_bench/painter_distribution_exploration_v1/report.py)

## Completed extension: Painter Prompt Study v1

- [Repeated generation, prompt methods, sample-size planning and commands](PROMPT_STUDY_WORKFLOW.md)
- [Prospective repeated-prompt protocol](../studies/painter_prompt_study_v1/PROTOCOL.md)
- [Approved 1,920-request configuration](../configs/painter_prompt_study_v1/study.json)
- [Original registered report and complete availability accounting](../reports/painter_prompt_study_v1/pps1-gpt-prompts-20260905/REPORT.md)
- [Terminal generation receipt](../data/manifests/painter_prompt_study_v1/pps1-gpt-prompts-20260905/generation_receipt.json)
- [Terminal measurement receipt](../data/manifests/painter_prompt_study_v1/pps1-gpt-prompts-20260905/measurement_receipt.json)
- [Generation freeze](../data/manifests/painter_prompt_study_v1/pps1-gpt-prompts-20260905/generation_freeze.json)
- [Randomization qualification](../data/manifests/painter_prompt_study_v1/pps1-randomization-20260905/decision.json)
- [Superseded interval-development calibration](../data/manifests/painter_prompt_study_v1/pps1-calibration-20260905/decision.json)

The approved `pps1-gpt-prompts-20260905` run is terminal: 1,920 requests, 1,918 generated and
measured images, two refusals, no replacements. The original complete-grid primary remains
unavailable. Existing evidence below remains sealed.

## Two-refusal retry follow-up

- [Two authorized exact-payload retries and descriptive completion protocol](../studies/painter_prompt_retry_v1/PROTOCOL.md)
- [Retry transport, measurement, reporting and verification module](../src/latent_art_bench/painter_prompt_retry_v1.py)
- [Completed main distance report and corrected comparison figure](../reports/painter_prompt_retry_v1/ppr1-two-refusals-20260906-r2/REPORT.md)
- [Retry generation and measurement accounting](../data/manifests/painter_prompt_retry_v1/ppr1-two-refusals-20260906/generation_receipt.json)
- [Figure revision receipt](../data/manifests/painter_prompt_retry_v1/ppr1-two-refusals-20260906/report_revision_2.json)

The user authorized exactly two additional attempts after the original study closed. Run
`ppr1-two-refusals-20260906` completed both successfully, giving 1,920 measured images in the
derived comparison. It retains disjoint evidence; later outputs cannot retroactively restore
the original randomized time slots. See [current status](STATUS.md) for results and verification.

## Post-registration supplement: Painter Prompt Supplement v1

- [Missingness supplement, qualification and reproducibility commands](PROMPT_SUPPLEMENT_WORKFLOW.md)
- [Supplement scientific contract](../studies/painter_prompt_supplement_v1/PROTOCOL.md)
- [Fixed supplement configuration](../configs/painter_prompt_supplement_v1/study.json)
- [Published supplement qualification](../data/manifests/painter_prompt_supplement_v1/ppss1-qualification-20260905/decision.json)
- [Committed supplement design freeze](../data/manifests/painter_prompt_supplement_v1/ppss1-missingness-20260905/design_freeze.json)
- [Completed exploratory report with comparison plots and full-precision exports](../reports/painter_prompt_supplement_v1/ppss1-missingness-20260905/REPORT.md)
- [Terminal supplement analysis](../data/manifests/painter_prompt_supplement_v1/ppss1-missingness-20260905/analysis.json)
- [Report evidence receipt](../data/manifests/painter_prompt_supplement_v1/ppss1-missingness-20260905/report_receipt.json)

Specified after source request sequence `415` was refused and before new feature measurement.
The source cap remains 1,920 requests, its incomplete-grid primary remains unavailable, and the
supplement adds no provider calls. Qualification passed and the design freeze was committed before
source measurement. The empirical report is complete, with all 48 exploratory endpoints and
three PNG/SVG comparison plots. [Current status](STATUS.md) records terminal accounting and
verification. Reviews are maintainer-run LLM subagent reviews, not institutional independence.

## Completed continuation: Painter Feature Generation v2

The empirical painter-feature analysis report is complete; the maintainer deferred a prototype
paper. Compact evidence lives under `data/manifests/painter_feature_generation_v2/`
and large bytes under the ignored `research_workspace/painter_feature_generation_v2/`.

- [Feature-distance report with comparison plots and exports](../reports/painter_feature_distance_v1/REPORT.md)
- [Feature-distance analysis contract and reproducibility commands](FEATURE_DISTANCE_ANALYSIS.md)

- [Completed empirical painter-feature analysis report](../reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS.md)
- [Korean translation of the completed empirical analysis report](../reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS_KO.md)
- [Earlier available-model access and research-suitability report](../reports/painter_feature_generation_v2/AVAILABLE_IMAGE_MODELS.md)
- [V2 empirical workflow and reproducibility commands](V2_ANALYSIS_WORKFLOW.md)
- [Shared empirical method freeze](../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/method_freeze.json)
- [Sealed primary empirical results](../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/empirical_analysis.json)
- [Complete paired crop sensitivity](../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/robustness/robustness_analysis.json)
- [Final report evidence receipt](../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/report_receipt.json)
- [V2 prospective study protocol](../studies/painter_feature_generation_v2/PROTOCOL.md)
- [V2 acquisition amendment 1.1](../studies/painter_feature_generation_v2/PROTOCOL_1.1.md)
- [V2 empirical comparison amendment 1.2](../studies/painter_feature_generation_v2/PROTOCOL_1.2.md)
- [V2 rendering transport correction 1.3](../studies/painter_feature_generation_v2/PROTOCOL_1.3.md)
- [Model-access assessment protocol 1.0](../studies/painter_feature_generation_v2/MODEL_ASSESSMENT_PROTOCOL_1.0.md)
- [Sealed GPT Image access receipt](../data/manifests/painter_feature_generation_v2/pfg2-image-access-20260905/assessment_receipt.json)
- [Offline response diagnosis](../data/manifests/painter_feature_generation_v2/pfg2-image-access-20260905/response_diagnostics.json)

## Historical study: Painter Feature Generation v1

- [V1 Protocol 2.2: collection amendment](../studies/painter_feature_generation_v1/PROTOCOL_2.2.md)
- [V1 Protocol 2.3: Wikidata authority amendment](../studies/painter_feature_generation_v1/PROTOCOL_2.3.md)
- [Recorded v1 R1 determination](../reports/painter_feature_generation_v1/R1_DETERMINATION_KO.md)

- [Study overview](../studies/painter_feature_generation_v1/README.md)
- [**Canonical generated-versus-real protocol (2.1)**](../studies/painter_feature_generation_v1/PROTOCOL_2.1.md)
- [Frozen Protocol 2.0 (superseded; authority for the completed censuses)](../studies/painter_feature_generation_v1/PROTOCOL.md)
- [Detailed Korean research and data report](../reports/painter_feature_generation_v1/RESEARCH_PLAN_AND_DATA_REPORT_KO.md)
- [Official source-route audit (Korean)](../reports/painter_feature_generation_v1/SOURCE_ROUTE_AUDIT_KO.md)
- [Corpus-adequacy pre-screen (Korean, non-binding)](../reports/painter_feature_generation_v1/SCENE_SUPPORT_PRESCREEN_KO.md)
- [Corpus-adequacy pre-screen evidence](../reports/painter_feature_generation_v1/evidence/scene_support_prescreen.json)
- [§11.1 prompt library artifact](../data/manifests/painter_feature_generation_v1/prompt_library.json)
- [§7.4 content lexicon artifact](../data/manifests/painter_feature_generation_v1/content_lexicon.json)
- [§8 exposure denylist](../data/manifests/painter_feature_generation_v1/exposure_denylist.jsonl) and [its receipt](../data/manifests/painter_feature_generation_v1/exposure_denylist_receipt.json)
- [Evidence acknowledgements](../data/manifests/painter_feature_generation_v1/evidence_acknowledgements.json)
- [Data-readiness evidence](../reports/painter_feature_generation_v1/evidence/data_readiness_audit.json)
- [Completed fixed-seed execution receipt](../data/manifests/painter_feature_generation_v1/federated_seed_metadata_execution_receipt_r2.json)
- [Completed fixed-seed candidate manifest](../data/manifests/painter_feature_generation_v1/federated_seed_metadata_candidates_r2.jsonl)
- [Completed fixed-seed hash-chained request events](../data/manifests/painter_feature_generation_v1/federated_seed_metadata_request_events_r2.jsonl)
- [Completed broad no-P186 execution receipt](../data/manifests/painter_feature_generation_v1/broad_wikidata_execution_receipt_r2.json)
- [Completed broad no-P186 candidate manifest](../data/manifests/painter_feature_generation_v1/broad_wikidata_candidates_r2.jsonl)
- [Completed broad no-P186 hash-chained request events](../data/manifests/painter_feature_generation_v1/broad_wikidata_request_events_r2.jsonl)
- [Terminal broad-media R1 request events](../data/manifests/painter_feature_generation_v1/broad_media_followup_request_events.jsonl)
- [Broad-media R1 neutral review](../data/manifests/painter_feature_generation_v1/broad_media_followup_review.json)
- [Completed broad-media R2 execution receipt](../data/manifests/painter_feature_generation_v1/broad_media_followup_publication_r2/execution_receipt.json)
- [Completed broad-media R2 candidate manifest](../data/manifests/painter_feature_generation_v1/broad_media_followup_publication_r2/candidates.jsonl)
- [Completed broad-media R2 hash-chained request events](../data/manifests/painter_feature_generation_v1/broad_media_followup_request_events_r2.jsonl)
- [Broad-media R2 neutral review](../data/manifests/painter_feature_generation_v1/broad_media_followup_review_r2.json)
- [Terminal AIC R1 request events](../data/manifests/painter_feature_generation_v1/aic_metadata_request_events.jsonl)
- [AIC R1 neutral review](../data/manifests/painter_feature_generation_v1/aic_metadata_review.json)
- [Completed AIC R2 execution receipt](../data/manifests/painter_feature_generation_v1/aic_metadata_publication_r2/execution_receipt.json)
- [Completed AIC R2 candidate manifest](../data/manifests/painter_feature_generation_v1/aic_metadata_publication_r2/candidates.jsonl)
- [Completed AIC R2 hash-chained request events](../data/manifests/painter_feature_generation_v1/aic_metadata_request_events_r2.jsonl)
- [AIC R2 neutral review](../data/manifests/painter_feature_generation_v1/aic_metadata_review_r2.json)
- [Traceable official-source live-item audit (not an as-of-date census)](../reports/painter_feature_generation_v1/evidence/official_source_extension_audit.json)
- [Federated candidate census evidence](../reports/painter_feature_generation_v1/evidence/federated_candidate_census.json)
- [Focused generated-versus-real literature audit](../literature_reviews/reviews/06_generated_vs_real_painter_fidelity.md)
- [Literature review package](../literature_reviews/README.md)
- [Evidence synthesis](../literature_reviews/SYNTHESIS.md)
- [Method decision ledger](../literature_reviews/METHOD_DECISIONS.md)

Within historical v1, `PROTOCOL_2.1.md` with amendments 2.2/2.3 is canonical.
`PROTOCOL.md` is the frozen 2.0 text that
authorized the completed censuses and is not edited. Reports and literature files explain or support
the plan; they do not independently authorize execution or override its rules.

Protocol 2.1 compares one exact model's painter-name outputs with complete authority-backed finite
populations of Monet, Sisley, Pissarro, and Cézanne metadata-declared outdoor-place oil-on-canvas
paintings. It keeps actual unequal painter counts, weights every work uniformly, and uses three
separately qualified interpretable feature families: color, spatial/orientation, and digital texture
organization. Previously exposed works are development-only; every new eligible work is assigned
once to development, qualification, or sealed confirmation by a fixed hash rule within painter ×
workflow.

The former 360-per-painter quota, three-way real split, 24-template frame, entropy weights, scene
stratification, and human coding are retired. Source collection is exhaustive rather than
count-stopped. Generation remains NO-GO until every painter has at least 10 development, 10
qualification, and 100 confirmation works; the auxiliary capture panel and workflow-crossing gates
hold; and the actual design passes whole-decision simulation. These are adequacy gates, not
permission to stop a source census.

R0 metadata tools cannot download or admit images. R1 separately binds authority, rights, identity,
capture, and technical image acquisition. R2 applies the frozen content lexicon and the role rule.
M0 qualifies measurements and freezes margins and copy thresholds. G0 freezes the 16 exact prompts,
one model, paired seeds, the adherence classifier, and `R` selected from `{25,50,75,100}`. G1
records every attempt while confirmation remains sealed; C0 opens the reference once. A
reproduction statement requires absolute target fit, specificity against every other painter,
improvement over the artist-free control, coverage, availability, and copy exclusion; adherence is
an automated diagnostic. Learned evaluators remain diagnostics.
