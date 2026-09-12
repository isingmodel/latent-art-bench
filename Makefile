# Repository navigation and offline reproduction. No target collects images.
.DEFAULT_GOAL := help
UV := uv run --locked
PYTHON := $(UV) python
CONTROLLED := latent_art_bench.painter_distribution_study_v1
REVISION := latent_art_bench.painter_distribution_revision_v1
PAPER_BUILD := tmp/paper/build
SPECIFICITY := latent_art_bench.painter_specificity_measurement_v1

.PHONY: help check check-all evidence analysis four-painter-analysis plots responsiveness computational-responsiveness palette-check validation-check replication-check geometry-check clause-check clause-successor-check figures figures-check paper specificity-check specificity-audit review-check review-images-check

help:
	@echo 'Paper correction: paper/README.md and docs/AGENT_HANDOVER.md'
	@echo 'make paper     Render manuscript figures and compile paper/paper.pdf'
	@echo 'make figures-check  Check manuscript figures without rewriting them'
	@echo 'make check     Ruff and the current analysis/integrity test suite'
	@echo 'make check-all Ruff and all retained offline tests, including historical workflows'
	@echo 'make specificity-check  Replay six-model recovery and reference sensitivities'
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
	$(UV) ruff check .
	$(UV) pytest -c pytest-paper.ini -q -m 'not live'

check-all:
	$(UV) ruff check .
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
