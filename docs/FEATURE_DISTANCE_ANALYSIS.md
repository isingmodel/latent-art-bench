# Feature-distance analysis

The main deliverable measures how generated-image feature distributions differ from the recorded
paintings of Monet, Sisley, Pissarro, and Cézanne. It uses the existing v2 images' **already measured
31 interpretable coordinates**. The user selected this scope on 2026-09-05: existing data, existing
features, reproducible analysis commands, and a report with comparison plots.

This is a new versioned **descriptive analysis of exposed numeric evidence**, implemented under
`src/latent_art_bench/painter_feature_distance_v1/`. It is not an acquisition census, a new
generation experiment, a prospective confirmation test, or a rerun of a terminal v2 stage.
The source v1/v2 evidence and their reports remain unchanged.

## Inputs and measures

- Source method: `pfg2-method-20260905`, with 649 measured confirmation paintings: Monet 297,
  Sisley 106, Pissarro 141, Cézanne 105. The four failed confirmation measurements remain in source
  accounting and contribute no fabricated vectors.
- Generated samples: all 2,000 SD-Turbo outputs and all 160 GPT service outputs. SD-Turbo has 400
  images per condition; each GPT alias has 16. The five conditions are four painter-name prompts
  and an artist-free control, using the original 16 templates.
- Representation: 11 color, eight spatial/orientation, and 12 digital-texture features. The existing
  512-pixel image normalization and frozen common equal-painter median/IQR scaler are reused.
  The scaler was fitted on 221 new-development paintings; it is never refitted on this analysis.
- Primary measure: the finite empirical energy V-statistic, using Euclidean distance within each
  feature family:

  `2 mean(distance(real, generated)) − mean(distance(real, real)) − mean(distance(generated, generated))`.

  Both within-set terms include diagonals. Each painting and each generated image retains equal
  mass within its respective set. Lower values mean closer measured distributions. Different
  feature families have different dimensions and scales; they are not added into a single score.
- Contrasts: own-target minus artist-free distance; own-target minus the nearest other painter's
  distance. Negative values favor naming the painter and favor the intended reference, respectively.
- Coordinate diagnostics: generated-minus-reference median difference, in frozen development-IQR
  units, and generated/reference IQR ratio for all 31 coordinates. An undefined ratio is blank/null.
- Reference-to-reference distances provide finite context. These are distances between different
  artists' recorded populations, not independent-capture calibration or equivalence thresholds.

The full matrix contains **180 rows**: three services × three families × five generated conditions
× four reference painters. There are 36 target/control/specificity summaries and 372 coordinate
diagnostics. All 180 existing endpoint values and all 372 existing coordinate diagnostics are
recomputed and checked against the sealed empirical result before publication.

## Sample-count sensitivity

The pooled distances use every generated output. A separate exploratory view computes own-target
and paired artist-free contrasts for **every original SD-Turbo repetition block**, each containing
all 16 templates and all five conditions. Each GPT alias contributes its one existing block.
This produces 324 painter/family/block rows: `(25 + 1 + 1) × 4 × 3`.

The plot shows each service's median and observed minimum–maximum target-distance range at 16
images per condition. GPT points have one observation, not zero estimated uncertainty. Paired
contrasts are computed within each block and retained in the CSV. There is no selected block,
random subsampling, bootstrap, new seed, or image generation. Ranges are not confidence intervals
or bias corrections. They reflect both sample-count dependence and variation across observed
generator blocks. Matching counts/template mix does not match output geometry or service settings.

## Commands

Run from the repository root with the locked environment. Keep both extras so environment
synchronization preserves existing generation dependencies, even though these commands do not
generate images.

```bash
# Create a fresh report bundle; the directory must not already exist.
uv run --locked --extra analysis --extra learned latent-art-bench feature-distances build \
  --output reports/painter_feature_distance_v1

# Verify and reproduce the delivered bundle without changing it.
uv run --locked --extra analysis --extra learned latent-art-bench feature-distances check \
  --output reports/painter_feature_distance_v1

# Independently create the same numeric results, tables, prose and plots in a new location.
uv run --locked --extra analysis --extra learned latent-art-bench feature-distances build \
  --output tmp/feature-distance-reproduction

uv run --locked --extra analysis --extra learned latent-art-bench feature-distances -- --help
```

`--root` is a global option and precedes `build` or `check`; `--method-id` is a build option and
defaults to `pfg2-method-20260905`. The source adapter supports the sealed v2 four-painter,
31-coordinate, complete-template-grid contract. An arbitrary folder of images or new feature
representation requires a separately specified adapter/design; this command never silently
reinterprets those inputs. Output directories must be beneath the repository's `reports/` or `tmp/`.

## Outputs and verification

[The report](../reports/painter_feature_distance_v1/REPORT.md) leads with absolute target distances,
then full distance matrices, painter-name/control and specificity contrasts, all-coordinate median
diagnostics, and sample-count sensitivity. Every plot is also available as an SVG for export.
JSON and six CSV tables retain full floating-point values; displayed tables use rounded values.

The bundle contains `analysis.json`, `distances.csv`, `contrasts.csv`, `coordinates.csv`,
`reference_distances.csv`, `block_distances.csv`, `block_summary.csv`, `REPORT.md`, `plots/`, and
`provenance.json`. Provenance records the consumed source hashes, implementation/lockfile hashes,
runtime versions, and every output hash. It is a derived-report manifest, not a new study freeze
or a claim of independent review. It does not refresh any existing evidence hash.

The reader verifies direct report/empirical bindings, feature file and vector hashes, scaler
provenance, stage and experiment identities, terminal accounting, feature order, finite values,
and complete generated grids. It reads compact numeric artifacts only: no raw image bytes,
normalization/extraction, provider calls, proxy changes, or access-ledger appends. Historical code
bindings are checked by the existing commit-aware evidence audits, not by demanding that historical
source code match the current working tree.

`check` verifies source/code/output hashes, recomputes the numeric analysis, and re-renders tables,
Markdown and figures in temporary storage. It requires byte-identical reproduction. Use the
recorded implementation and locked runtime; graphics-library/font changes may change figure bytes
without changing the science. A mismatch is investigated, not repaired by changing a stored hash.

## Interpretation limits

The reference consists of Wikidata-declared outdoor-place painting surrogates, not new museum
authentication or a probability sample of each artist's oeuvre. Content, capture workflow,
profiles and geometry remain possible confounders. GPT labels identify requested service aliases
on the recorded route; underlying snapshots are unverified and returned size/quality differ from
requested controls. The one-repetition GPT pilot does not estimate repeat-generation uncertainty.

This analysis reports distances and differences, with no overall model ranking, significance labels,
equivalence threshold, or reproduction verdict. The original SD-Turbo intervals remain in the
sealed report and are exploratory because synthetic shift coverage was 0.86. Independent captures
and qualified margins would be needed for equivalence; their absence does not block descriptive
distance measurement. Existing crop/source sensitivities remain linked evidence, not retuned tests.
