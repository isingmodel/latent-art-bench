# Research paper

The canonical English manuscript is [paper.tex](paper.tex), compiled to
[paper.pdf](paper.pdf), with [references.bib](references.bib) and nine vector
figures. It retains the four-painter exploration, controlled naming and palette
studies, scene retrieval, measurement challenges and temporal follow-up.
Generated-only moment maps and evaluation centering diagnose the limits of a
reference-proximity gain.

The prospective generic-clause successor uses 96 outputs on 24 new scenes;
Cezanne naming lowers energy by 1.195 against the generic clause (p=.00001 at
alpha .025). The stopped 288-slot predecessor retains its 211 images and
unavailable original endpoints. Neither cohort is pooled with another.

The separate [240-output fixed-map comparison](../reports/painter_map_validation_v2/pmv2-20260910/REPORT.md)
uses 12 new FLUX/Cezanne scenes and ten paired repetitions per scene. Both
reference energy and corrected conditional-mean mismatch favor unchanged
translation/scaling, with approximate contrast intervals below zero. The
historical opposing ordering does not transfer. The observed Q half-width 2.833
exceeds the proxy median-width planning criterion 1.0, a retained limitation of
anticipated precision. This extension adds a two-row table, without new plots
or refitted maps.

The fixed three-reviewer score means are 8.2333, 8.6889 and **8.9000/10** across
three rounds. The new evidence is awaiting a complete fourth review; no score
changes automatically. Reviewers are maintainer-run LLM agents with disclosed
design/implementation involvement, not independent human peer reviewers.
See the [review record](../docs/reviews/20260910_substantive_revision/REVIEW.md).

The latest published manuscript remains the [36-page clause version](https://github.com/isingmodel/latent-art-bench/releases/tag/pcrv1-20260910);
its immutable paper/source assets and earlier versions are preserved. The
[fixed-map numerical addendum](https://github.com/isingmodel/latent-art-bench/releases/tag/pmv2r-20260910)
is separate; it contains no manuscript assets yet. Current integration, public
replay and final paper verification are recorded in [STATUS.md](../docs/STATUS.md).

Edit only the canonical English manuscript and its presentation code here.
Preserve the user-owned Korean drafts. Use the [analysis catalog](../docs/ANALYSES.md)
to trace a claim to its immutable result; [ARTIFACTS.md](../docs/ARTIFACTS.md)
specifies retention boundaries.

## Build and check

From the repository root, after `uv sync --locked --extra analysis --extra dev`:

```bash
make paper          # Render figures and compile paper/paper.pdf with Tectonic
make figures-check  # Check manuscript figures without rewriting them
make palette-check  # Replay Study 2 primary inference using compact inputs only
make validation-check # Replay controlled measurement challenges and square views
make replication-check # Replay the separate terminal temporal collection
make geometry-check # Replay both new retained-vector geometry diagnostics
```

`make_figures.py` verifies the hashes of eight published inputs: seven CSVs and
the exploration's `projections.json`. It extracts saved endpoints and PCA
coordinates without fitting projections or
computing new statistics. Its only permanent outputs are the six PDFs in `figures/`.
The four-painter figure displays 649 unique originals and 1,536 painter-conditioned
outputs using the saved all-31-feature balanced-joint coordinates. Each painter
shares a basis and axis limits across its three prompt methods; equal aspect and
all outliers are retained, with the two later retry points marked. The color-response figure
extracts the six saved scene estimates for each painter as well as the pooled
estimates and intervals; it does not calculate new interactions.

`replay_palette.py` supplies the seventh figure, `palette_blocks.pdf`, and the
numeric-only `make palette-check` command. It reads exactly three SHA-256-pinned
files from the sole primary Study 2 run, `prv2-oauth-recovery-20260908`:

- `data/manifests/painter_responsiveness_v2/<run>/planned_requests.jsonl`
- `reports/painter_responsiveness_v2/<run>/experiment/generated_chroma.csv`
- `reports/painter_responsiveness_v2/<run>/experiment/primary.csv`

The command verifies all 576 pipeline outcomes against the 192 planned identities,
passes the primary-512 values to the unchanged factorial inference implementation,
and requires exact agreement with both saved primary rows. It derives the 24 block
interactions, their signs and scene variance shares as post-result descriptive
summaries. The figure shows every block in dispatch order, which was separately
checked against recorded collection slots and transport timing during review.
These checks do not verify raw responses, source pixels, feature extraction,
service independence or public availability. The full archive checks are unchanged.
The command was also tested with only these three data files in a temporary input
root. Its code dependencies and locked Python environment are still required.
The public package's portable check supplies its documented comparator for
identified continuous Welch roundoff and records the primary comparison alongside
the figure. The standalone command retains exact primary matching.

`make_validation_figure.py` supplies the eighth figure, `challenge_matrix.pdf`,
using the unchanged measurement report renderer and saved analysis. Its
`--check` mode requires byte identity. The common-window appendix table reports
all eight retained contrasts; the original full-view results remain unchanged.

`make_geometry_figure.py` supplies the readable Figure 3 derivative,
`naming_geometry_presentation.pdf`: the same two panels stacked at the 160 mm
manuscript width, with text at least 8.5 pt. It hash-checks the sealed geometry
`analysis.json`, verifies plotted coordinates against its stored values and
supports byte-identical `--check` replay. `make figures` and `make figures-check`
use this presentation renderer. The original `naming_geometry.pdf` and sealed
report renderer remain unchanged; `make geometry-check` independently recomputes
both scientific analyses and their complete numerical reports.

For temporary PNG previews of the six summary figures:

```bash
uv run --locked python paper/make_figures.py --preview-dir tmp/paper/preview
```

Build files go to `tmp/paper/build/`. Render and inspect every PDF page after
manuscript edits, for example:

```bash
mkdir -p tmp/paper/pages
pdftoppm -r 100 -png paper/paper.pdf tmp/paper/pages/page
```

## Scientific inputs

The four-painter exploration uses 649 painting reproductions: 297 Monet,
106 Sisley, 141 Pissarro and 105 Cézanne. Its completed retry grid contains
1,536 painter-conditioned outputs (three prompt methods × two requested aliases
× four painters × 64 outputs) and 384 artist-free controls. The exploration,
Stage A diagnostics and retry contrasts are descriptive post-result analyses.
Two later successes remain identified, the original incomplete-grid primary
inference remains unavailable, and the requested `gpt-image-1` / `gpt-image-2`
aliases do not establish distinct underlying model identities.

Study 1 separately uses 1,006 generated images across three services; Study 2 uses
192 images from one service. These later studies share a 70-work Monet/Cézanne
reference panel and a development scaler fitted on 221 works. Their controlled
results are not pooled with the earlier four-painter cohort. The 49-image
incomplete color-experiment predecessor remains ancillary and is not pooled
into either primary cohort. The eight original
conditional randomization tests, original two palette interaction tests,
new four-endpoint temporal family and post-result diagnostics remain distinct. Human judgments, independent capture
replication and learned-feature validation are unperformed.

- [Four-painter exploration methods](../studies/painter_distribution_exploration_v1/METHODS.md)
- [Four-painter distributions and complete tables](../reports/painter_distribution_exploration_v1/REPORT.md)
- [Stage A diagnostic controls](../reports/painter_distribution_study_v1/pdsv1-diagnostics-20260906/REPORT.md)
- [Descriptive retry contrasts](../reports/painter_prompt_retry_v1/ppr1-two-refusals-20260906-r2/REPORT.md)
- [Controlled study methods](../studies/painter_distribution_study_v1/MAIN.md)
- [Controlled report and complete tables](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md)
- [Diagnostic methods](../studies/painter_distribution_revision_v1/PROTOCOL.md)
- [Diagnostic report and complete tables](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md)
- [Computational follow-up synthesis](../reports/painter_responsiveness_v2/REPORT.md)
- [Color experiment and inference](../studies/painter_responsiveness_v2/PROTOCOL.md)
- [Primary color-response results](../reports/painter_responsiveness_v2/prv2-oauth-recovery-20260908/experiment/REPORT.md)
- [Exact-weight quantile corrigendum](../reports/painter_responsiveness_quantiles_v1/prqv1-20260908/REPORT.md)
- [Computational measurement protocol](../studies/painter_measurement_validation_v1/PROTOCOL.md)
- [Measurement results](../reports/painter_measurement_validation_v1/pmvv1-20260910/REPORT.md)
- [Temporal replication protocol](../studies/painter_naming_replication_v1/PROTOCOL.md)
- [Temporal results](../reports/painter_naming_replication_v1/pnrv1-20260910/REPORT.md)
- [Public numerical release guide](../studies/paper_reproducibility_v1/README.md)
- [Analysis and plotting source map](../docs/ANALYSES.md)

`make four-painter-analysis` replays the exploration, Stage A diagnostics and
retry presentation, verifying 35 + 18 + 9 published files. `make analysis`
replays the later controlled study and revision.
`make plots` byte-checks those two Study 1 report bundles and the manuscript figures.
`make computational-responsiveness` replays the subsequent computational studies
and quantile correction. These commands use retained
vectors and metadata; full integrity-checked computational replay also requires
the separately retained raw response archive. Figure rebuilding uses only
committed compact inputs. None of these commands regenerates images or restarts
terminal studies.

## Release and access status

The [public release](https://github.com/isingmodel/latent-art-bench/releases/tag/pprv1-20260910)
is verified through a fresh local replay, hosted Ubuntu execution and anonymous
archive download/replay. The [verification report](../reports/paper_reproducibility_v1/pprv1-20260910/REPORT.md)
links the actual receipts and scope. All 98 checks match exactly on the recorded
macOS runtime; Ubuntu passes the documented floating comparison, with seven exact
PDFs and platform-dependent challenge-figure bytes.

The preceding manuscript remains available as additive `paper-r1.pdf` and
`paper-r1.tex` assets. The current substantive revision differs from those assets;
its new geometry analyses are not in the unchanged predecessor archive. The [erratum](../reports/paper_reproducibility_v1/pprv1-20260910/PAPER_ERRATUM.md)
clarifies the scoped Welch p-value comparison and one verb agreement. The original
archive and original `paper.pdf` asset remain unchanged. Corrected TeX can be
compiled alongside the original archive's manuscript, using the same figures and
bibliography, without modifying any manifest-bound archive file.

The adapter invokes unchanged scientific calculations from compact vectors,
scalers, memberships and seeds, then checks direct report bridges and all figures.
It includes both the measurement extension and the completed terminal replication
extension. See the release guide for commands and
explicit coverage. This supplies numerical reproducibility; feature re-extraction
and private-response verification still require retained raw bytes. Source URLs
and recorded license metadata are not guarantees of current raw-image access or
permission to redistribute artwork.

## Substantive geometry diagnostics

- [Global moment protocol](../studies/painter_naming_geometry_v1/PROTOCOL.md) and [complete results](../reports/painter_naming_geometry_v1/pngv1-20260910/REPORT.md).
- [Evaluation-centering protocol](../studies/painter_naming_centering_v1/PROTOCOL.md) and [complete results](../reports/painter_naming_centering_v1/pncv1-20260910/REPORT.md).
- [Fresh baseline and result audits](../docs/reviews/20260910_substantive_revision/BASELINE.json). Reviewers are maintainer-run LLMs; Reviewers 1/2 subsequently helped implement statistical primitives, and Reviewer 3 supplied literature/structure advice.

The fixed translation/scale predictor is evaluated on four whole-scene folds.
Actual naming beats it on all six primary fold means, but fold and deletion
reversals remain reported. Pure translation beats actual naming in both later
primary FLUX comparisons, with a Monet deletion and 256-pixel exceptions. The
evaluation-centered scalar worsens energy in all 60 original and 18 transfer
views; this is an algebraic feature comparison, not an internal model mechanism.
No new hypothesis tests or intervals are introduced.
