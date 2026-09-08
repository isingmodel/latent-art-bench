# Repository navigation and offline reproduction. No target collects images.
.DEFAULT_GOAL := help
UV := uv run --locked
PYTHON := $(UV) python
CONTROLLED := latent_art_bench.painter_distribution_study_v1
REVISION := latent_art_bench.painter_distribution_revision_v1
PAPER_BUILD := tmp/paper/build

.PHONY: help check evidence analysis plots responsiveness computational-responsiveness figures paper

help:
	@echo 'make check     Ruff and the complete offline test suite'
	@echo 'make evidence  Verify historical evidence bindings and ledgers'
	@echo 'make analysis  Replay controlled-study and revision numeric results'
	@echo 'make plots     Replay both report bundles and check manuscript figures'
	@echo 'make responsiveness  Replay the v1 mechanism diagnostics and plots'
	@echo 'make computational-responsiveness  Replay v2 computational results and plots'
	@echo 'make figures   Render the three manuscript figures from saved tables'
	@echo 'make paper     Render manuscript figures and compile paper/paper.pdf'
	@echo 'Other studies: docs/ANALYSES.md'

check:
	$(UV) ruff check .
	$(UV) pytest -q -m 'not live'

evidence:
	$(UV) latent-art-bench verify-evidence

analysis:
	$(PYTHON) -m $(CONTROLLED).analysis_publication check
	$(PYTHON) -m $(REVISION).analysis check

plots:
	$(PYTHON) -m $(CONTROLLED).main_report check
	$(PYTHON) -m $(REVISION).report_publication check
	$(PYTHON) paper/make_figures.py --check

responsiveness:
	$(PYTHON) -m latent_art_bench.painter_responsiveness_v1 check

computational-responsiveness:
	$(PYTHON) -m latent_art_bench.painter_responsiveness_v2 check-diagnostic
	$(PYTHON) -m latent_art_bench.painter_responsiveness_v2 check

figures:
	$(PYTHON) paper/make_figures.py

paper: figures
	mkdir -p $(PAPER_BUILD)
	cd paper && tectonic --outdir ../$(PAPER_BUILD) paper.tex
	cp $(PAPER_BUILD)/paper.pdf paper/paper.pdf
