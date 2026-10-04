# Repository navigation and offline reproduction. No target collects images.
.DEFAULT_GOAL := help
UV := uv run --locked
PYTHON := $(UV) python
CONTROLLED := latent_art_bench.painter_distribution_study_v1
REVISION := latent_art_bench.painter_distribution_revision_v1
# TMLR manuscript builds go here; the PDF is copied to output/pdf/ (ignored by Git).
# The build fixes the PDF date (2026-01-01 UTC) so that no local time zone is embedded.
TMLR_BUILD ?= tmp/paper/tmlr-build
TMLR_KO_BUILD ?= tmp/paper/tmlr-ko-build
SPECIFICITY := latent_art_bench.painter_specificity_measurement_v1
# Scripts under reports/ are frozen audit records; lint must not require rewriting their bytes.
LINT_SCOPE := --extend-exclude reports
# pytest-paper.ini is hash-bound by later analyses, so newer routine suites are listed here.
ROUTINE_EXTRA := tests/painter_cross_cohort_v1 tests/painter_selective_attribution_v1 tests/painter_tmlr_diagnostics_v1 tests/painter_tmlr_diagnostics_v2 tests/painter_tmlr_diagnostics_v3 tests/painter_tmlr_diagnostics_v4 tests/painter_tmlr_diagnostics_v5 tests/painter_specificity_v3 tests/painter_tmlr_diagnostics_v6 tests/painter_tmlr_diagnostics_v7 tests/test_repository_artifacts.py

.PHONY: restore-analysis install-hooks git-size-check

.PHONY: help check check-all evidence analysis four-painter-analysis plots responsiveness computational-responsiveness palette-check validation-check replication-check geometry-check clause-check clause-successor-check figures-check specificity-check specificity-audit review-check reference-quality-check reference-quality-images-check editorial-check paper-tmlr paper-tmlr-ko tmlr-ko-assets tmlr-ko-check tmlr-assets tmlr-check retrospective-check extensions-check artifact-check icml-evidence-check icml-extensions-check icml-artifact-check

help:
	@echo 'Start with docs/STATUS.md, then paper/README.md and docs/AGENT_HANDOVER.md'
	@echo 'make paper-tmlr  Check assets and build the anonymous TMLR manuscript'
	@echo 'make tmlr-check  Verify TMLR tables, figure, quoted numbers and style files'
	@echo 'make paper-tmlr-ko  Build the Korean translation of the TMLR manuscript'
	@echo 'make tmlr-assets  Regenerate the TMLR tables and figure from retained analyses'
	@echo 'make retrospective-check  Replay the direct-naming, timing, learned, transfer, covariance and TMLR diagnostics'
	@echo 'make extensions-check  Replay the SD-Turbo and selective-attribution analyses'
	@echo 'make artifact-check  Verify the selected exact-pixel inventory locally'
	@echo 'make restore-analysis  Restore and verify the compressed frozen transfer result'
	@echo 'make install-hooks  Enable the staged-file size check in this checkout'
	@echo 'make git-size-check  Check staged Git blobs against the 100 MiB limit'
	@echo 'make figures-check  Check the retained palette figure against its replay'
	@echo 'make check     Ruff and the current analysis/integrity test suite'
	@echo 'make check-all Ruff and all retained offline tests, including historical workflows'
	@echo 'make specificity-check  Replay six-model recovery and reference sensitivities'
	@echo 'make review-check  Replay both versions of post-result diagnostics'
	@echo 'make editorial-check  Audit archived review hashes and scores without model calls'
	@echo 'make reference-quality-check  Replay the source-region and label sensitivity'
	@echo 'make specificity-audit  Verify the new terminal report and retained raw bytes'
	@echo 'make evidence  Verify historical evidence bindings and ledgers'
	@echo 'make analysis  Replay controlled naming and revision numeric results'
	@echo 'make four-painter-analysis  Replay four-painter distributions and controls'
	@echo 'make plots     Replay controlled naming report bundles and check manuscript figures'
	@echo 'make responsiveness  Replay the v1 mechanism diagnostics and plots'
	@echo 'make computational-responsiveness  Replay v2 computational results and plots'
	@echo 'make palette-check  Replay palette primary inference from compact numeric inputs'
	@echo 'make validation-check  Replay computational challenges and geometry sensitivity'
	@echo 'make replication-check  Replay the terminal temporal replication from retained measurements'
	@echo 'make geometry-check  Replay held-scene maps and evaluation centering'
	@echo 'make clause-check  Replay the stopped four-arm clause study'
	@echo 'make clause-successor-check  Replay the separate Cezanne/generic result after terminal measurement'
	@echo 'Other studies: docs/ANALYSES.md'

restore-analysis:
	python3 scripts/restore_analysis.py

install-hooks:
	git config --local core.hooksPath .githooks

git-size-check:
	python3 scripts/check_git_sizes.py

check:
	$(UV) ruff check . $(LINT_SCOPE)
	$(UV) pytest -c pytest-paper.ini -q -m 'not live'
	$(UV) pytest -c pytest-paper.ini -q -m 'not live' $(ROUTINE_EXTRA)

check-all:
	$(UV) ruff check . $(LINT_SCOPE)
	$(UV) pytest -q tests -m 'not live'

evidence:
	$(UV) latent-art-bench verify-evidence

analysis:
	$(PYTHON) -m $(CONTROLLED).analysis_publication check
	$(PYTHON) -m $(REVISION).analysis check

four-painter-analysis:
	$(PYTHON) -m latent_art_bench.painter_distribution_exploration_v1.report check
	$(PYTHON) -m $(CONTROLLED).diagnostics check
	$(PYTHON) -m latent_art_bench.painter_prompt_retry_report_v2 check

plots:
	$(PYTHON) -m $(CONTROLLED).main_report check
	$(PYTHON) -m $(REVISION).report_publication check
	$(MAKE) figures-check

responsiveness:
	$(PYTHON) -m latent_art_bench.painter_responsiveness_v1 check

computational-responsiveness:
	$(PYTHON) -m latent_art_bench.painter_responsiveness_v2 check-diagnostic
	$(PYTHON) -m latent_art_bench.painter_responsiveness_recovery_v1 check
	$(PYTHON) -m latent_art_bench.painter_responsiveness_v2 check
	$(PYTHON) -m latent_art_bench.painter_responsiveness_quantiles_v1 check

palette-check:
	$(PYTHON) paper/replay_palette.py

validation-check:
	$(PYTHON) -m latent_art_bench.painter_measurement_validation_v1 check

replication-check:
	$(PYTHON) -m latent_art_bench.painter_naming_replication_v1 check

geometry-check:
	$(PYTHON) -m latent_art_bench.painter_naming_geometry_v1 verify
	$(PYTHON) -m latent_art_bench.painter_naming_centering_v1 verify

clause-check:
	$(PYTHON) -m latent_art_bench.painter_clause_validation_v1 check

clause-successor-check:
	$(PYTHON) -m latent_art_bench.painter_clause_successor_v1 check

specificity-check:
	$(PYTHON) -m $(SPECIFICITY).workflow analyze --check
	$(PYTHON) -m $(SPECIFICITY).workflow analyze --square --check
	$(PYTHON) -m $(SPECIFICITY).workflow analyze --reference --check
	$(PYTHON) -m $(SPECIFICITY).workflow analyze --reference --square --check

review-check:
	$(PYTHON) -m latent_art_bench.painter_specificity_review_v1 check
	$(PYTHON) -m latent_art_bench.painter_specificity_review_v2 check

reference-quality-check:
	$(PYTHON) -m latent_art_bench.painter_reference_quality_v1 check

reference-quality-images-check:
	$(PYTHON) -m latent_art_bench.painter_reference_quality_v1 check-images

editorial-check:
	$(PYTHON) scripts/audit_paper_reviews.py

specificity-audit:
	$(PYTHON) -m $(SPECIFICITY).report --check

# Other presentation builders were retired on 2026-10-01 (see docs/ARTIFACTS.md);
# the palette figure stays because hash-bound routine tests read it at this path.
figures-check:
	$(PYTHON) paper/replay_palette.py --check-figure paper/figures/palette_blocks.pdf

tmlr-assets: restore-analysis
	$(PYTHON) paper/tmlr/build_assets.py

tmlr-check: restore-analysis
	$(PYTHON) paper/tmlr/build_assets.py --check

paper-tmlr: tmlr-check
	mkdir -p $(TMLR_BUILD) output/pdf
	cd paper/tmlr && TZ=UTC SOURCE_DATE_EPOCH=1767225600 tectonic --keep-logs --outdir ../../$(TMLR_BUILD) main.tex
	cp $(TMLR_BUILD)/main.pdf output/pdf/latent_art_bench_tmlr.pdf

# Korean translation: Korean tables are derived from paper/tmlr/generated, and the
# numbers of the Korean prose are compared with the English manuscript.
tmlr-ko-assets:
	$(PYTHON) paper/tmlr_ko/build_korean.py

tmlr-ko-check:
	$(PYTHON) paper/tmlr_ko/build_korean.py --check

paper-tmlr-ko: tmlr-check tmlr-ko-check
	mkdir -p $(TMLR_KO_BUILD) output/pdf
	cd paper/tmlr_ko && TZ=UTC SOURCE_DATE_EPOCH=1767225600 tectonic --keep-logs --outdir ../../$(TMLR_KO_BUILD) main.tex
	cp $(TMLR_KO_BUILD)/main.pdf output/pdf/latent_art_bench_tmlr_korean.pdf

# The icml-* names are kept as aliases because dated records under reports/ cite them.
icml-evidence-check: retrospective-check
icml-extensions-check: extensions-check
icml-artifact-check: artifact-check

retrospective-check: restore-analysis
	$(PYTHON) -m latent_art_bench.painter_specificity_review_v3 check
	$(PYTHON) -m latent_art_bench.painter_request_timing_v1 check
	$(PYTHON) -m latent_art_bench.painter_learned_audit_v1 check
	$(PYTHON) -m latent_art_bench.painter_prototype_transfer_v1 check --execute-real
	$(PYTHON) -m latent_art_bench.painter_repeat_covariance_v1 check --execute-real
	$(PYTHON) -m latent_art_bench.painter_tmlr_diagnostics_v1 check
	$(PYTHON) -m latent_art_bench.painter_tmlr_diagnostics_v2 check
	$(PYTHON) -m latent_art_bench.painter_tmlr_diagnostics_v3 check
	$(PYTHON) -m latent_art_bench.painter_tmlr_diagnostics_v4 check
	$(PYTHON) -m latent_art_bench.painter_tmlr_diagnostics_v5 check
	$(PYTHON) -m latent_art_bench.painter_specificity_v3.report check
	$(PYTHON) -m latent_art_bench.painter_tmlr_diagnostics_v6 check
	$(PYTHON) -m latent_art_bench.painter_tmlr_diagnostics_v7 check

extensions-check:
	$(PYTHON) -m latent_art_bench.painter_cross_cohort_v1 check --execute-real \
	  --inputs-sha256 94413b3ee5bd689f60df35e7a8135f79eb929fd9dbee36bd450b47df4db0e693
	$(PYTHON) -m latent_art_bench.painter_selective_attribution_v1 check --execute-real \
	  --input-sha256 f9d6b94e19d8004463f7b0524dd72865e22c18b0786cf48387cb9257e0528826 \
	  --audit-file reports/icml_review_v1/resume_2026-09-21/selective_preoutcome_audit.json \
	  --audit-sha256 e3f26efb7286ad592e5ec30a50dd937690c29852d690c94b3baf09f31ae22569

artifact-check:
	$(PYTHON) scripts/check_icml_artifact_inventory.py
