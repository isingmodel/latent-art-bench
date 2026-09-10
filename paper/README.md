# Research paper

[paper.tex](paper.tex) is the canonical English manuscript. It is being rewritten
around **artist-specific recovery beyond a shared painting response**. The new
six-model experiment is still collecting; result text is explicitly pending.
[paper.pdf](paper.pdf) remains the previous completed 39-page version until the
new terminal analysis is integrated. Earlier published paper/source assets are
immutable and remain available in the [versioned releases](https://github.com/isingmodel/latent-art-bench/releases).

All four painters remain: Monet, Sisley, Pissarro and Cézanne. The new experiment
uses 14 common scenes, six clauses and two repeats per cell, for 1,008 planned
images across six models. Its primary outcomes are reference-aligned slopes and
repeat-corrected artist-geometry error. The paper retains complementary energy
and spread outcomes, generic/palette controls and the contrary fixed-map transfer
result. Operational histories are outside the main argument.

## Build after terminal analysis

```bash
make specificity-check  # Four numeric views; no API or raw-image access
make specificity-audit  # Terminal report and retained response/image hashes
make paper              # Figures/tables and Tectonic compilation
make figures-check      # Exact local presentation replay
```

The [corrected measurement entry point](../studies/painter_specificity_measurement_v1/CORRECTION.md)
selects the intended 649 valid reference vectors from a manifest also retaining
four historical failures. Do not use the earlier measurement/reader CLIs.
The collector and its postprocessing worker are currently active; do not launch
duplicate collection or measurement. See [STATUS.md](../docs/STATUS.md).

## Source organization

- `paper.tex`: argument, methods, interpretation and supporting evidence.
- `specificity_results.tex`: new empirical result text, pending measurement.
- `references.bib`: primary literature and source documentation.
- `make_specificity_figures.py`: model intervals, reference-contrast scatter plots,
  and error/spread diagnostics from the verified new vectors and results.
- `make_specificity_tables.py`: model regression and complete per-painter tables.
- `make_figures.py`, `make_geometry_figure.py`, `replay_palette.py`,
  `make_validation_figure.py`: retained presentation of earlier evidence. These
  preserve sealed numerical inputs; transport labels are replaced by model names.

Build intermediates and rendered-page checks belong in `tmp/paper/`.
The new comparison concerns digital feature geometry and recorded model
configurations; it does not establish perceptual fidelity or internal mechanisms.
The [analysis catalog](../docs/ANALYSES.md) maps every supporting claim to its
immutable source. Preserve user-owned Korean files and all frozen research bytes;
see [ARTIFACTS.md](../docs/ARTIFACTS.md).
