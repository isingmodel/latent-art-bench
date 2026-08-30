# Initial Implementation Plan

> Implementation note (2026-08-29): the repository now contains the WP0/WP1 substrate, the exact chromatic implementation, synthetic tests, qualification cards, and a test-only image adapter. At the user's direction, that adapter is hard-limited to `gpt-image-1` and `gpt-image-2` through a loopback OpenAI-compatible endpoint. This is an engineering exception for API tests, not a change to the scientific design: WP5 remains closed, unqualified live calls require an explicit test-only bypass, and their outputs cannot be reported as pilot evidence.

This plan covers implementation only through the first reproducible development-pilot results. It is not a full benchmark, publication, hosting, or long-term maintenance plan. The project will stop and re-plan after the pilot report because corpus availability, measurement reliability, variance, and generation cost are not yet known.

## Pilot question

> Can one interpretable image measurement and one frozen learned-formal measurement be implemented faithfully, calibrated on real artworks, and used to estimate artist target gap and specificity in a small controlled generation pilot?

The pilot is artist-level only. Movement remains metadata. Its results describe one corpus, one prompt protocol, one generator checkpoint, and two qualified feature spaces; they do not support general model rankings or claims about artists as a population.

## Conditional stopping path

```text
pilot contract and engineering foundation
    -> real-corpus feasibility
    -> real-only measurement qualification
         -> fail: publish a measurement-feasibility report and stop
         -> pass: freeze the evaluators and prompt protocol
                    -> run one-generator development pilot
                    -> publish the pilot report and stop
```

“Stop” means make an explicit go, narrow, or redesign decision before planning further work. It does not mean force a failed measurement through the pipeline.

## Provisional pilot scope

- four public-domain artists arranged as two defensible neighbor pairs;
- one shared, sufficiently populated genre across the selected artists;
- an audit target of roughly 30–50 independent canonical works per artist, not a final inferential threshold;
- an audit target of roughly 15–20 same-work reproduction pairs across the pilot corpus;
- one interpretable measurement: normalized adjacent-pixel chromatic-distance distribution and seamlessness;
- one frozen learned-formal evaluator selected in a short code and checkpoint feasibility spike;
- one reproducible open-weight text-to-image generator with a fixed checkpoint;
- shared content prompts within the common genre and artist-free controls;
- two outputs: calibrated target gap and target-versus-neighbor specificity margin;
- no aggregate score, movement inference, prototype-contraction claim, cross-layer coherence claim, human study, closed-model comparison, or leaderboard.

The work-count targets are planning estimates. The real-data audit determines whether the four-artist design is viable before any generator is installed or run.

## Implementation principles

1. **Real data first.** No generation begins before both pilot measurements pass or conditionally pass their real-only gates.
2. **One configuration drives every run.** Corpus version, preprocessing, features, splits, prompts, checkpoints, seeds, and analysis rules are captured in a versioned configuration.
3. **Manifests are the source of truth.** Images remain local when rights require it; every input and derived artifact is addressed by identifiers and hashes.
4. **Fit and transform remain separate.** Anything learned or standardized is fitted on real training works and then frozen.
5. **Scripts produce results.** Notebooks may explore but are not the only execution path for a reported artifact.
6. **Failure is an output.** Failed replications, source confounding, generation refusals, and technical errors remain visible.
7. **Avoid premature infrastructure.** Do not add dashboards, distributed execution, DVC, MLflow, submission services, or a plugin framework for this pilot.

## Intended repository shape

```text
pyproject.toml
src/latent_art_bench/
  cli.py
  schemas.py
  data/
  preprocessing/
  features/
  evaluation/
  reporting/
configs/pilot_0/
tests/unit/
tests/integration/
reports/pilot_0/
```

Large images, model weights, caches, and derived arrays stay in ignored local directories. The repository retains small schemas, configurations, synthetic-fixture generators, tests, aggregate tables, and reports that are lawful to redistribute.

## Work packages

| ID | Work package | Depends on | Primary artifact | Gate |
|---|---|---|---|---|
| WP0 | Freeze the pilot contract | — | `pilot_0` configuration | Estimand-defining choices are explicit |
| WP1 | Build the reproducible substrate | WP0 | Package, CLI, schemas, tests | Synthetic dry run is deterministic |
| WP2 | Audit and ingest the real corpus | WP0, WP1 | Versioned real-work manifest | Four-artist corpus is viable and lawful |
| WP3 | Implement deterministic preprocessing | WP1, WP2 | Derived-view manifest | Pixel transforms are reproducible |
| WP4 | Implement the two measurements | WP1, WP3 | Feature tables and replication tests | Source behavior is recovered |
| WP5 | Run real-only qualification | WP2–WP4 | Measurement qualification report | Both measurements pass or conditionally pass |
| WP6 | Freeze the generated pilot | WP5 pass | Generator and prompt manifest | No result-dependent choices remain |
| WP7 | Run, analyze, and report the pilot | WP6 | Development-pilot report | Initial results and next decision are recorded |

### WP0: Freeze the pilot contract

Decide before implementation results are available:

- candidate artists, sources, common genre, and neighbor-pair rule;
- the exact paper, code revision, and mathematical definition for chromatic distance and seamlessness;
- the learned-formal checkpoint, license, preprocessing, layer, and pooling rule;
- canonical-work and reproduction identifiers;
- provisional resolution and perturbation grid;
- allowed pilot claims and explicit non-claims;
- the open-weight generator candidates and local hardware constraints, without installing or running the selected generator yet.

The learned evaluator receives a time-bounded feasibility spike. If its source implementation, weights, license, or preprocessing cannot be reproduced, record that result and stop at the real-only one-feature feasibility report rather than silently substituting another evaluator.

**Exit:** one reviewable configuration contains every choice that changes the pilot estimand. Values that legitimately depend on real-only variance are marked as pending with the milestone that will resolve them.

### WP1: Build the reproducible substrate

Implement a small Python package with a locked environment and a config-driven command line. Before generator qualification, the command surface should cover:

- `validate-manifest`;
- `preprocess`;
- `extract-features`;
- `qualify`;
- `report-pilot`.

Define schema-validated records for canonical works, reproductions, derived views, feature rows, generation calls, and runs. Each run records the Git revision, dependency lock, full configuration, input hashes, checkpoint hashes, random seeds where available, start and completion state, and failure reasons.

Unit tests generate solid fields, gradients, stripes, checkerboards, and noise in memory. An integration test takes a tiny synthetic manifest through preprocessing and a dummy feature twice and asserts identical hashes and outputs.

**Exit:** a fresh environment can execute the synthetic dry run from one documented command, and the test suite detects work-level split leakage and fit/transform misuse.

### WP2: Audit and ingest the real corpus

Audit more candidates than the final four without using feature separability or generator output as selection criteria. Record:

- canonical identity and attribution confidence;
- artist, date, genre, medium, and approximate phase;
- source institution, landing page, access date, and license;
- native dimensions, color profile, borders, file hash, and perceptual hash;
- same-work alternative reproductions;
- known source-by-artist and genre-by-artist confounding.

Ingest only the development slice after the rights review. Deduplicate before splitting and keep all reproductions of one canonical work in the same train or held-out partition, except for explicitly paired calibration analyses.

**Exit:** four artists form two defensible neighbor pairs, share a usable genre, have adequate independent works and overlapping sources, and have no unresolved high-risk duplicate leakage. If not, revise the roster and repeat WP2; do not weaken the split.

### WP3: Implement deterministic preprocessing

Build one documented image-loading path that handles orientation, embedded profiles, conversion to the project color space, alpha, borders, aspect ratio, and downsampling. Preserve native files and write content-addressed derived views plus provenance records.

Use a narrow calibration grid: a small set of supported downsampled resolutions, one fixed resampling path, lossless output, and one representative JPEG condition. Exact values are frozen in WP0. Upsampling is excluded from primary comparisons.

Synthetic tests check known colors, dimensions, aspect ratios, alpha behavior, and transform determinism. Manually inspect a small contact sheet only for pipeline defects, not for selecting favorable works.

**Exit:** repeated preprocessing is byte- or value-identical under the documented tolerance, and every derived view maps back to its source file and configuration.

### WP4: Implement the two measurements

#### Interpretable measurement

Implement source-faithful color-space conversion, horizontal and vertical adjacent-pixel distances, the source normalization, distribution summaries, and seamlessness. Test expected behavior on synthetic constant fields, hard splits, gradients, checkerboards, and noise. Recover a small preregistered set of image-level or aggregate behaviors from the source paper.

#### Learned-formal measurement

Wrap exactly one frozen checkpoint behind the same feature interface. Reproduce its documented preprocessing, layer extraction, pooling, and vector dimension. Verify checkpoint and output hashes, deterministic evaluation behavior, and strict real-train fitting for any subsequent standardization or dimensionality reduction.

Each feature row includes work, reproduction, derived-view, feature-version, and configuration identifiers. Each measurement receives a machine-readable `pass`, `conditional_pass`, or `fail` card with evidence and supported scope.

**Exit:** both measurements recover their preregistered source or reference behavior. A failed measurement is not replaced after inspecting held-out artist or generated results.

### WP5: Run real-only qualification

Without any generated images, compute:

- same-file preprocessing drift;
- same-work reproduction distance;
- within-artist train-versus-held-out distance;
- target-versus-neighbor distance;
- source-prediction performance;
- leave-source-out artist signal;
- response across the narrow resolution and compression grid.

Fit learned transformations on real training works only. Use the development portion to set numerical reliability thresholds and practical equivalence margins, document them, and then evaluate the held-out real split. Estimate variance for generation repetitions and equal-sample comparisons.

**Gate:** proceed only if the interpretable and learned-formal measurements both pass or have clearly documented conditional domains compatible with the pilot corpus, and artist signal is not dominated by source. Otherwise produce the measurement-feasibility report and stop.

### WP6: Freeze the generated pilot

Only after WP5 passes, freeze:

- one generator checkpoint and inference environment;
- exact shared-content prompts within the common genre;
- no more than two templates per content and an artist-free control;
- seeds or repetition rules derived from WP5 variance;
- retry, refusal, failure, and output-selection rules;
- Energy distance as the pilot target-gap statistic;
- the target-minus-nearest-neighbor specificity formula and sign convention;
- equal-sample subsampling and the uncertainty hierarchy.

At this point, and not earlier, add the minimal generator adapter plus `generate` and `analyze-pilot` commands.

Outputs generated for the other artists already provide wrong-artist neighbor comparisons; do not add a redundant generation matrix. The result is explicitly a development estimate, not a sealed confirmatory benchmark.

**Exit:** the frozen configuration can be reviewed without generated images, and no manual visual-selection step exists.

### WP7: Run, analyze, and report the pilot

Run the fixed grid without visual curation. Apply only the frozen real-only preprocessing and measurements. Report:

- target gap and specificity with uncertainty;
- held-out real-real, target-neighbor, reproduction, preprocessing, and source baselines;
- per-cell request, success, refusal, retry, and failure counts;
- qualification cards and all conditional domains;
- sensitivity to the preregistered preprocessing conditions;
- variance and sample-size estimates for a possible next study.

Do not promote exploratory coverage, covariance, effective-rank, prototype-contraction, or coherence results to pilot conclusions. Four artists do not support a population-wide artist claim.

**Exit:** `reports/pilot_0/` contains a human-readable report, machine-readable tables, the resolved configuration, environment and run manifests, and a decision memo.

## Decision after the initial results

The decision memo selects exactly one path:

- **Go:** the corpus and two measurements are usable, and target-gap or specificity estimates justify planning a larger confirmatory study.
- **Narrow:** the pipeline works only for a restricted source, resolution, genre, artist pair, or feature; plan that restricted study explicitly.
- **Redesign:** data or measurement failures dominate; revise the corpus or construct before any more generation.
- **Stop:** the proposed comparison is not supportable with available data and measurements.

Only then should the project decide whether to add the second interpretable layer, contextual diagnostics, more artists, more generators, prototype contraction, human qualification, or a sealed confirmatory benchmark.

## Explicitly deferred

The following are intentionally not implementation work for this plan:

1. the full 8–12-artist roster;
2. multiple or closed generators;
3. movement-level inference;
4. contextual-evaluator and evaluator-family matrices;
5. coverage, effective rank, prototype contraction, tails, subclusters, and cross-layer coherence;
6. full perturbation sweeps, born-digital controls, or print-and-recapture experiments unless the source diagnostic triggers them;
7. human qualification, image conditioning, memorization, exposure proxies, and ontology transfer;
8. aggregate scores, leaderboards, submission governance, public hosting, or paper scheduling.

## First implementation batch

Begin with only these tasks:

1. add the Python package, dependency lock, test runner, and CLI skeleton;
2. define and test the canonical-work, reproduction, derived-view, and run schemas;
3. add synthetic-fixture generators and the deterministic preprocessing smoke test;
4. create the candidate-artist and source audit template;
5. write the exact chromatic-distance/seamlessness specification and source-replication test cases;
6. complete the learned-formal checkpoint feasibility spike.

Do not implement generator integration until WP5 has produced a pass decision.
