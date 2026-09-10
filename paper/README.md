# Research paper

[paper.tex](paper.tex) is the canonical English manuscript and
[paper.pdf](paper.pdf) is the completed 17-page version. It centers on
**artist-specific recovery beyond a shared painting response**. All 1,008 new
images have been measured. Every model shows aligned artist variation, but
response strength does not track geometry recovery; the adjusted comparisons
favor FLUX.2 Max over both GPT Image 2.5 variants, with other differences unresolved.
Earlier published paper/source assets remain immutable in the
[versioned releases](https://github.com/isingmodel/latent-art-bench/releases).

All four painters remain: Monet, Sisley, Pissarro and Cézanne. The new experiment
uses 14 common scenes, six clauses and two repeats per cell, for 1,008 measured
images across six models. Its primary outcomes are reference-aligned slopes and
repeat-corrected artist-geometry error. The paper retains complementary energy
and spread outcomes, generic/palette controls and the contrary fixed-map transfer
result. Operational histories are outside the main argument.

## Replay and build

```bash
make specificity-check  # Four numeric views; no API or raw-image access
make specificity-audit  # Terminal report and retained response/image hashes
make paper              # Figures/tables and Tectonic compilation
make figures-check      # Exact local presentation replay
```

The [corrected measurement entry point](../studies/painter_specificity_measurement_v1/CORRECTION.md)
selects the intended 649 valid reference vectors from a manifest also retaining
four historical failures. Do not use the earlier measurement/reader CLIs.
Collection and measurement are permanently complete. Do not invoke either
one-shot command again; use the offline replay targets. See [STATUS.md](../docs/STATUS.md).

## Source organization

- `paper.tex`: argument, methods, interpretation and supporting evidence.
- `specificity_results.tex`: the completed six-model results and three main figures.
- `references.bib`: primary literature and source documentation.
- `make_specificity_figures.py`: model intervals, reference-contrast scatter plots,
  and error/spread diagnostics from the verified new vectors and results.
- `make_specificity_tables.py`: model regression and complete per-painter tables;
  the generated `specificity_model_table.tex` and `specificity_supplement_tables.tex`
  are included by the manuscript.
- `make_figures.py`, `make_geometry_figure.py`, `replay_palette.py`,
  `make_validation_figure.py`: retained presentation of earlier evidence. These
  preserve sealed numerical inputs; transport labels are replaced by model names.

Build intermediates and rendered-page checks belong in `tmp/paper/`.
The new comparison concerns digital feature geometry and recorded model
configurations; it does not establish perceptual fidelity or internal mechanisms.
The [analysis catalog](../docs/ANALYSES.md) maps every supporting claim to its
immutable source. Preserve user-owned Korean files and all frozen research bytes;
see [ARTIFACTS.md](../docs/ARTIFACTS.md).
