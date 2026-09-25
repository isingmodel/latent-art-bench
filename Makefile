# Repository navigation and offline reproduction. No target collects images.
.DEFAULT_GOAL := help
UV := uv run --locked
PYTHON := $(UV) python
CONTROLLED := latent_art_bench.painter_distribution_study_v1
REVISION := latent_art_bench.painter_distribution_revision_v1
PAPER_BUILD := tmp/paper/build
# Fresh ICML builds go here; the round-04 reviewed build is tmp/paper/icml-resume-build.
ICML_BUILD ?= tmp/paper/icml-build
SPECIFICITY := latent_art_bench.painter_specificity_measurement_v1
# Scripts under reports/ are frozen audit records, and the ICML figure builder is
# hash-bound by the round-04 review; lint must not require rewriting their bytes.
LINT_SCOPE := --extend-exclude reports --extend-per-file-ignores 'paper/make_icml_selective_figure.py:I001'
# pytest-paper.ini is hash-bound by later analyses, so newer routine suites are listed here.
ROUTINE_EXTRA := tests/painter_cross_cohort_v1 tests/painter_selective_attribution_v1

.PHONY: help check check-all evidence analysis four-painter-analysis plots responsiveness computational-responsiveness palette-check validation-check replication-check geometry-check clause-check clause-successor-check figures figures-check paper specificity-check specificity-audit review-check review-images-check reference-quality-check reference-quality-images-check example-images example-images-check editorial-check paper-icml icml-format-check icml-evidence-check icml-extensions-check icml-artifact-check

help:
	@echo 'Start with docs/STATUS.md, then paper/README.md and docs/AGENT_HANDOVER.md'
	@echo 'make paper     Render manuscript figures and compile paper/paper.pdf'
	@echo 'make paper-icml  Build and check the anonymous ICML manuscript'
	@echo 'make icml-format-check  Check the ICML build in ICML_BUILD without recompiling'
	@echo 'make icml-evidence-check  Replay the ICML direct-naming, timing, learned, transfer and covariance analyses'
	@echo 'make icml-extensions-check  Replay the SD-Turbo and selective-attribution analyses and tables'
	@echo 'make icml-artifact-check  Verify the selected exact-pixel inventory locally'
	@echo 'make figures-check  Check manuscript figures without rewriting them'
	@echo 'make check     Ruff and the current analysis/integrity test suite'
	@echo 'make check-all Ruff and all retained offline tests, including historical workflows'
	@echo 'make specificity-check  Replay six-model recovery and reference sensitivities'
	@echo 'make review-check  Replay both versions of post-result diagnostics'
	@echo 'make example-images-check  Verify original/generated panels from retained pixels'
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
	@echo 'make figures   Render the manuscript and supporting figures from retained numeric inputs'
	@echo 'Other studies: docs/ANALYSES.md'

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
	$(PYTHON) paper/make_review_figures.py --check
	$(PYTHON) -m latent_art_bench.painter_specificity_review_v2 check

reference-quality-check:
	$(PYTHON) -m latent_art_bench.painter_reference_quality_v1 check

reference-quality-images-check:
	$(PYTHON) -m latent_art_bench.painter_reference_quality_v1 check-images

example-images:
	$(PYTHON) paper/make_example_figures.py

example-images-check:
	$(PYTHON) paper/make_example_figures.py --check

editorial-check:
	$(PYTHON) scripts/audit_paper_reviews.py

review-images-check:
	$(PYTHON) paper/make_review_figures.py --check --images

specificity-audit:
	$(PYTHON) -m $(SPECIFICITY).report --check

figures:
	$(PYTHON) paper/make_figures.py
	$(PYTHON) paper/replay_palette.py --figure paper/figures/palette_blocks.pdf
	$(PYTHON) paper/make_validation_figure.py
	$(PYTHON) paper/make_geometry_figure.py
	$(PYTHON) paper/make_specificity_figures.py
	$(PYTHON) paper/make_specificity_tables.py
	$(PYTHON) paper/make_review_figures.py

figures-check:
	$(PYTHON) paper/make_figures.py --check
	$(PYTHON) paper/replay_palette.py --check-figure paper/figures/palette_blocks.pdf
	$(PYTHON) paper/make_validation_figure.py --check
	$(PYTHON) paper/make_geometry_figure.py --check
	$(PYTHON) paper/make_specificity_figures.py --check
	$(PYTHON) paper/make_specificity_tables.py --check
	$(PYTHON) paper/make_review_figures.py --check

paper: figures
	mkdir -p $(PAPER_BUILD)
	cd paper && tectonic --outdir ../$(PAPER_BUILD) paper.tex
	cp $(PAPER_BUILD)/paper.pdf paper/paper.pdf

paper-icml:
	mkdir -p $(ICML_BUILD) output/pdf
	cd paper && tectonic --keep-logs --keep-intermediates --outdir ../$(ICML_BUILD) icml.tex
	$(PYTHON) scripts/check_icml_format.py --build-dir $(ICML_BUILD)
	cp $(ICML_BUILD)/icml.pdf output/pdf/latent_art_bench_icml.pdf

icml-format-check:
	$(PYTHON) scripts/check_icml_format.py --build-dir $(ICML_BUILD)

icml-evidence-check:
	$(PYTHON) -m latent_art_bench.painter_specificity_review_v3 check
	$(PYTHON) -m latent_art_bench.painter_request_timing_v1 check
	$(PYTHON) -m latent_art_bench.painter_learned_audit_v1 check
	$(PYTHON) paper/make_icml_learned_tables.py --check
	$(PYTHON) paper/make_icml_learned_calibration_tables.py --check
	$(PYTHON) -m latent_art_bench.painter_prototype_transfer_v1 check --execute-real
	$(PYTHON) paper/make_icml_transfer_tables.py --check
	$(PYTHON) -m latent_art_bench.painter_repeat_covariance_v1 check --execute-real
	$(PYTHON) paper/make_icml_covariance_tables.py --check

icml-extensions-check:
	$(PYTHON) -m latent_art_bench.painter_cross_cohort_v1 check --execute-real \
	  --inputs-sha256 94413b3ee5bd689f60df35e7a8135f79eb929fd9dbee36bd450b47df4db0e693
	$(PYTHON) paper/make_icml_cross_cohort_tables.py --check
	$(PYTHON) -m latent_art_bench.painter_selective_attribution_v1 check --execute-real \
	  --input-sha256 f9d6b94e19d8004463f7b0524dd72865e22c18b0786cf48387cb9257e0528826 \
	  --audit-file reports/icml_review_v1/resume_2026-09-21/selective_preoutcome_audit.json \
	  --audit-sha256 e3f26efb7286ad592e5ec30a50dd937690c29852d690c94b3baf09f31ae22569
	$(PYTHON) paper/make_icml_selective_tables.py --check

icml-artifact-check:
	$(PYTHON) scripts/check_icml_artifact_inventory.py
