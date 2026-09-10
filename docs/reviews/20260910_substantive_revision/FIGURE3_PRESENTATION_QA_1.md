# Figure 3 presentation QA — Reviewer 1

Date: 2026-09-10. This create-once record covers the separate manuscript presentation derivative, not a scientific reanalysis or a new manuscript review. I am a maintainer-run LLM agent and implemented this renderer, earlier variance primitives and other disclosed analysis/release components. These are implementer checks, not independent human or institutional verification. No review score is assigned or changed.

## Change and dimensions

`paper/make_geometry_figure.py` reads only the sealed geometry `analysis.json`, rejects any SHA256 mismatch and selects its saved `primary512`/`all31` records. It stacks the original panels A and B at a **160 mm × 152.4 mm** figure size (453.543 × 432 PDF points), matching the manuscript's full text width. Tick and axis labels are 9 pt, titles 10 pt, and legends 8.5 pt; the smallest visible Matplotlib text was measured as **8.5 pt**. These sizes apply when placed at the intended 160 mm width.

Only presentation changes. The Makefile's geometry figure render/check commands use the new renderer, with a short pointer in `paper/README.md`. The sealed report renderer, original report PDF and its existing manuscript copy remain unchanged. The renderer neither fits maps nor computes energies, means, folds, deletion ranges, intervals or tests.

## Completed checks

- **Exact source-to-artist parity:** all 24 fold residuals, 12 stored residual means and eight energy bar heights match the selected stored fields exactly. All 192 primary-cell deletion records remain in the unchanged input; they are not plotted or recomputed.
- **Direct sealed-renderer comparison:** rendered the unchanged report implementation into a temporary directory and compared its Matplotlib artists with the new figure. All **29 artists** (21 scatter collections, including three empty legend proxies, and eight bars) preserve exact coordinates, axis bounds and tick text, axis labels, colors, marker paths, bar widths and ordering. The two panel-title strings retain their A/B labels and meanings. Layout and font sizes deliberately differ.
- **Negative input check:** appended a newline to a temporary copy of the source JSON, without changing its parsed values. Pointing the loader at that copy raised `ValueError: sealed geometry figure input changed`. No sealed input was modified.
- **Nonmutation check:** the renderer compares the full parsed result before/after drawing and rechecks the source hash. Both checks pass, preserving stored mean/fold/deletion values.
- **Deterministic PDF replay:** `uv run --locked python paper/make_geometry_figure.py` followed by the same command with `--check` passes byte for byte. Creation/modification timestamps are omitted from PDF metadata.
- **Fonts:** PDF saving explicitly retains `pdf.fonttype=42`. `pdffonts paper/figures/naming_geometry_presentation.pdf` reports embedded, subsetted **CID TrueType / Identity-H** DejaVu Sans fonts with Unicode maps, not Type 3 fonts.
- **Visual inspection:** inspected the final 150-dpi rendering at `tmp/paper/naming-geometry-presentation-final-reviewer1.png`. Both panels, service labels, axes and legends are visible with no clipping or overlap.
- **Lint:** `uv run --locked ruff check paper/make_geometry_figure.py` passes. The coordinator is running the integrated full suite and final manuscript PDF QA separately; neither is claimed completed by this record.

## Exact identities

| Repository-relative file | SHA256 |
| --- | --- |
| `paper/make_geometry_figure.py` | `c3f6120f3b0c80dfaf1cb5146aac9e56d926f748c5172f4aec549d46871b9ace` |
| `paper/figures/naming_geometry_presentation.pdf` | `5ca6af3ba8509fb8614c5595210c4ed5b03eff913cd6e80b56d3bfeef246733d` |
| `data/manifests/painter_naming_geometry_v1/pngv1-20260910/analysis.json` | `f50be0f772a3bff8f4bc66ddc20f3e19b5c13736fd6cced632d80224e2203324` |
| `src/latent_art_bench/painter_naming_geometry_v1/report.py` | `1c369f18fb78d436235d8123153768c1dd3adbe7c702ee9cda1e2ff4da2a4704` |
| `reports/painter_naming_geometry_v1/pngv1-20260910/naming_geometry.pdf` | `c08cbe9d5fe24daec1d7901065a867ae993b9c072920d544d141424e0b4ed312` |
| `paper/figures/naming_geometry.pdf` | `c08cbe9d5fe24daec1d7901065a867ae993b9c072920d544d141424e0b4ed312` |

The new PDF is one page and 21,749 bytes. These checks establish presentation parity with retained numerical results. They do not establish new statistical validity, acquisition authenticity, perceptual validity or cross-platform PDF byte identity. No old public release or frozen scientific artifact was changed.
