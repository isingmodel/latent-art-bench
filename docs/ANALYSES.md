# Analysis and plotting catalog

This catalog maps each result to the code that computes it, the builder that
presents it and the command that replays it. The [results index](../reports/README.md)
links the reports themselves. Run commands from the repository root with the
recorded Python 3.13.11 runtime and locked environment. All commands are offline
checks or manuscript builds; none acquires or generates images.

## Data flow

```text
studies/ + configs/            fixed protocols, plans and executed settings
data/manifests/                compact vectors, requests, hashes and receipts
reports/*/embeddings_*.npz     retained CLIP/CSD vectors (learned audit)
    |
    +-- painter_specificity_measurement_v1/workflow.py
    |     corrected reader: 649 references + 1,008 generated images
    |     painter_specificity_v2/analysis.py: primary slopes and model comparisons
    |
    +-- post-result diagnostics      painter_specificity_review_v1/v2, reference_quality_v1
    +-- retrospective extensions     review_v3, request_timing, learned_audit,
    |                                prototype_transfer, repeat_covariance,
    |                                cross_cohort, selective_attribution
    v
reports/<study>/                 hash-bound numerical results; originals never rewritten
    |
    +-- paper/tmlr/build_assets.py
          -> paper/tmlr/main.tex -> output/pdf/latent_art_bench_tmlr.pdf (TMLR submission)
```

The 31 feature definitions are in
[features.py](../src/latent_art_bench/painter_feature_generation_v2/features.py);
221 separate development works scale them. Older modules remain because later
analyses import their measurement, randomization and provenance primitives and
completed studies bind their paths. Collection code documents execution; no
Make target calls it.

| Location | Responsibility |
| --- | --- |
| [src/latent_art_bench/](../src/latent_art_bench/) | Versioned scientific calculation, data readers and historical collectors |
| [studies/](../studies/), [configs/](../configs/README.md) | Protocols, fixed plans and configurations |
| [data/manifests/](../data/manifests/) | Measurements, assignments, provenance and result bindings |
| [reports/](../reports/README.md) | Numerical outputs, report plots, release receipts and review records |
| [paper/](../paper/README.md) | Manuscripts and presentation builders |
| [scripts/](../scripts/), [tools/](../tools/) | Record audits, pixel-inventory checks, historical collectors and release adapters |
| [tests/](../tests/README.md) | Offline scientific and integrity checks |
| `research_workspace/` (ignored) | Raw artwork, generated images and transport records |

## Primary six-model experiment

Inputs are under
[data/manifests/painter_specificity_v2/psv2-20260911](../data/manifests/painter_specificity_v2/psv2-20260911/).
The [protocol](../studies/painter_specificity_v2/PROTOCOL.md) defines the 1,008-image
design; the [reader correction](../studies/painter_specificity_measurement_v1/CORRECTION.md)
selects the intended 649 measured references; the
[content-weighting protocol](../studies/painter_specificity_reference_v1/PROTOCOL.md)
defines the reference sensitivity.

| Calculation | Source | Check |
| --- | --- | --- |
| Artist contrasts, corrected error and paired model regressions | [analysis.py](../src/latent_art_bench/painter_specificity_v2/analysis.py), [workflow.py](../src/latent_art_bench/painter_specificity_measurement_v1/workflow.py) | `make specificity-check` (full/square × pooled/content-weighted) |
| Terminal report, accounting and raw-byte identity | [report.py](../src/latent_art_bench/painter_specificity_measurement_v1/report.py) | `make specificity-audit`; needs local responses/images |
| Scene decomposition, calibration, artist pairs, reference controls | [painter_specificity_review_v1.py](../src/latent_art_bench/painter_specificity_review_v1.py), [plan](../studies/painter_specificity_review_v1/PLAN.md) | `make review-check` |
| Shared-control correction, sampling-integrated controls, stability | [painter_specificity_review_v2.py](../src/latent_art_bench/painter_specificity_review_v2.py) | `make review-check` |
| Source-region, development-scaler and visual-label sensitivity | [painter_reference_quality_v1.py](../src/latent_art_bench/painter_reference_quality_v1.py), [plan](../studies/painter_reference_quality_v1/PLAN.md) | `make reference-quality-check`; `make reference-quality-images-check` re-extracts 131 crops |

```bash
uv run --locked python -m latent_art_bench.painter_specificity_measurement_v1.workflow analyze --check
# Add --square, --reference, or both for the other three saved views.
```

Post-result diagnostics do not extend the original 21-comparison family. The
first, stopped 31-output attempt remains excluded.

## Retrospective analyses

Added 2026-09-18 to 2026-09-21 for the (now retired) ICML draft; the TMLR
manuscript uses the direct-naming, learned, transfer, covariance and SD-Turbo
analyses. Each plan was fixed before
its new outcomes were inspected, but every analysis reuses previously exposed
data. Module paths are relative to `src/latent_art_bench/`.

| Analysis | Plan | Code | Report | Replay |
| --- | --- | --- | --- | --- |
| Direct named-minus-generic decomposition and scene stability | [plan](../studies/painter_specificity_review_v3/PLAN.md) | `painter_specificity_review_v3.py` | [report](../reports/painter_specificity_review_v3/report.md), [interpretation](../reports/painter_specificity_review_v3/interpretation.md) | `make retrospective-check` |
| Within-cell request timing | [plan](../studies/painter_request_timing_v1/PLAN.md) | `painter_request_timing_v1.py` | [report](../reports/painter_request_timing_v1/REPORT.md) | `make retrospective-check` |
| Same-image CLIP/CSD audit | [plan](../studies/painter_learned_audit_v1/PLAN.md) | `painter_learned_audit_v1.py` (extraction), `painter_learned_csd_v1.py` (CSD crop adapter), `painter_learned_analysis_v1.py` (analysis) | [report](../reports/painter_learned_audit_v1/REPORT.md) | `make retrospective-check`; re-extraction needs `--extra learned`, checkpoints and pixels |
| Held-scene prompt-name transfer | [plan](../studies/painter_prototype_transfer_v1/PLAN.md) | `painter_prototype_transfer_v1.py` | [report](../reports/painter_prototype_transfer_v1/REPORT.md) | `make retrospective-check` |
| Cross-repeat covariance scenarios | [plan](../studies/painter_repeat_covariance_v1/PLAN.md) | `painter_repeat_covariance_v1.py` | [report](../reports/painter_repeat_covariance_v1/REPORT.md) | `make retrospective-check` |
| Separate 2,000-image SD-Turbo collection | [plan](../studies/painter_cross_cohort_v1/PLAN.md) | `painter_cross_cohort_v1.py` | [report](../reports/painter_cross_cohort_v1/REPORT.md) | `make extensions-check`; verifies the 2,000 local pixel hashes |
| Reference-calibrated selective attribution | [plan](../studies/painter_selective_attribution_v1/PLAN.md) | `painter_selective_attribution_v1.py` | [report](../reports/painter_selective_attribution_v1/REPORT.md) | `make extensions-check` |
| TMLR revision diagnostics (2026-10-01): faithful-imitation benchmark, direction, feature families, readout stability | [plan](../studies/painter_tmlr_diagnostics_v1/PLAN.md) | `painter_tmlr_diagnostics_v1.py` | [report](../reports/painter_tmlr_diagnostics_v1/REPORT.md) | `make retrospective-check` |
| TMLR revision diagnostics v2 (2026-10-01): exact-differences benchmark, scene and reference intervals, joint resampling of D, 31-feature separability, SD-Turbo benchmarks | [plan](../studies/painter_tmlr_diagnostics_v2/PLAN.md) | `painter_tmlr_diagnostics_v2.py` | [report](../reports/painter_tmlr_diagnostics_v2/REPORT.md) | `make retrospective-check` |
| TMLR revision diagnostics v3 (2026-10-01): genuine-painting controls with distinct works (31 features, CLIP, CSD), embedding D intervals, normalized-prototype shares, paired feature-family contrasts | [plan](../studies/painter_tmlr_diagnostics_v3/PLAN.md) | `painter_tmlr_diagnostics_v3.py` | [report](../reports/painter_tmlr_diagnostics_v3/REPORT.md) | `make retrospective-check` |
| TMLR revision diagnostics v4 (2026-10-01): CLIP/CSD agreement against content-matched class targets | [plan](../studies/painter_tmlr_diagnostics_v4/PLAN.md) | `painter_tmlr_diagnostics_v4.py` | [report](../reports/painter_tmlr_diagnostics_v4/REPORT.md) | `make retrospective-check` |
| TMLR revision diagnostics v5 (2026-10-01): direction-only agreement and its stability, embedding error split and Student intervals, repeat dependence in the embeddings, proximity correlations across configurations, configuration distinctness, projection coordinates | [plan](../studies/painter_tmlr_diagnostics_v5/PLAN.md) | `painter_tmlr_diagnostics_v5.py` | [report](../reports/painter_tmlr_diagnostics_v5/REPORT.md) | `make retrospective-check` |
| Painter specificity v3 (2026-10-02/03): **prospective second collection** with a century group and the Hudson River School; reference panels (`refs-20261002`, 788 works, with two pre-request amendments), predictions, 1,680 requests (`psv3-r1`), and the prespecified tests H1 (closeness) and H2 (pairwise dose-response) | [references](../studies/painter_specificity_v3/REFERENCES.md), [protocol](../studies/painter_specificity_v3/PROTOCOL.md) | `painter_specificity_v3/` | [report](../reports/painter_specificity_v3/REPORT.md) | `make retrospective-check` |
| TMLR diagnostics v6 (2026-10-03): shared-fraction intervals, recognition and proximity for the two further groups; plan fixed before the second collection was measured | [plan](../studies/painter_tmlr_diagnostics_v6/PLAN.md) | `painter_tmlr_diagnostics_v6.py` | [report](../reports/painter_tmlr_diagnostics_v6/REPORT.md) | `make retrospective-check` |
| TMLR diagnostics v7 (2026-10-04): H2 by pair type, the closeness-only (faithful) contrast of H1 with intervals, matched closeness, census of the H1 resamples; planned after review round 1 of the second series, with its point values known | [plan](../studies/painter_tmlr_diagnostics_v7/PLAN.md) | `painter_tmlr_diagnostics_v7.py` | [report](../reports/painter_tmlr_diagnostics_v7/REPORT.md) | `make retrospective-check` |

The prospective [family-control study](../studies/painter_family_controls_v1/PLAN.md)
is implemented in `painter_family_controls_v1/` and qualified offline by
`scripts/qualify_family_*_offline.py`, `scripts/audit_family_*.py` and
`tests/painter_family_controls_v1`. It has no observations; see
[its preparation record](../reports/painter_family_controls_v1/README.md).

Independent audit and replay scripts for these analyses are frozen records in
[reports/icml_review_v1/](../reports/icml_review_v1/README.md). The local
[numerical bundle](../reports/icml_review_v1/numeric_bundle_v1/README.md), built by
`scripts/icml_numeric_bundle.py`, replays 16 fixed checks outside the checkout.

## Manuscript presentation

| Presentation | Builder | Check |
| --- | --- | --- |
| TMLR tables, component figure and every quoted number | [paper/tmlr/build_assets.py](../paper/tmlr/build_assets.py) | `make tmlr-check` |
| TMLR Figures 1 and 3 (example images, painter pairs) | Static copies with hashes in [paper/tmlr/figures/PROVENANCE.json](../paper/tmlr/figures/PROVENANCE.json) | `make tmlr-check` |
| Palette block display | [paper/replay_palette.py](../paper/replay_palette.py) | `make figures-check`, `make palette-check` |
| Frozen full-length paper and Korean translation | None (snapshot in `paper/archive/`) | `make paper-archive` recompiles them |

```bash
make tmlr-check           # TMLR assets, quoted numbers, style and figure hashes
make paper-tmlr           # Check assets and compile the TMLR submission
make paper-archive        # Recompile the frozen full-length paper and translation
make figures-check        # Palette figure against its replay
```

The earlier presentation builders (`make_specificity_figures.py`,
`make_specificity_tables.py`, `make_review_figures.py`, `make_example_figures.py`,
`make_figures.py`, `make_validation_figure.py`, `make_geometry_figure.py` and
the seven `make_icml_*.py` table builders) and their unused outputs were removed
from `paper/` on 2026-10-01. Records under `reports/` still name them; Git
history and `generative_art_diff_archive/2026-10-01/` keep them. The numerical
analyses they presented are unaffected and still replay.

## Supporting analyses

Package paths are relative to `src/latent_art_bench/`. Each namespace has its
protocol or methods in `studies/`, input bindings in `data/manifests/` or report
provenance, and outputs linked from the results index.

| Evidence | Numerical code | Report plotting | Replay |
| --- | --- | --- | --- |
| Four-painter distribution exploration | `painter_distribution_exploration_v1/{analysis,statistics}.py` | `report.py` in the same package | `make four-painter-analysis` |
| Earlier content/reference controls | `painter_distribution_study_v1/diagnostics.py` | Same module | Included in `make four-painter-analysis` |
| Completed-grid retry presentation | Original `painter_prompt_retry_v1.py` results | `painter_prompt_retry_report_v2.py` | Included in `make four-painter-analysis` |
| Controlled named/free comparisons | `painter_distribution_study_v1/{analysis,statistics,inference}.py` | `main_report.py` | `make analysis`; report bundle: `make plots` |
| Content, reference/scaler and timing diagnostics | `painter_distribution_revision_v1/{analysis,metrics,diagnostics,timing}.py` | `report.py`, checked by `report_publication.py` | Included in `make analysis` and `make plots` |
| Palette intervention and scene retrieval | `painter_responsiveness_v2/{analysis,diagnostics}.py` | `report.py` | `make computational-responsiveness`; compact primary only: `make palette-check` |
| Palette quantile correction | `painter_responsiveness_quantiles_v1.py` | Same module | Included in `make computational-responsiveness` |
| Processing challenges and common-square sensitivity | `painter_measurement_validation_v1/{pipeline,statistics}.py` | `report.py` | `make validation-check` |
| Separate temporal naming/palette replication | `painter_naming_replication_v1/{analysis,workflow}.py` | Analysis output | `make replication-check` |
| Held-scene moment maps and evaluation centering | `painter_naming_geometry_v1/`, `painter_naming_centering_v1/` | Geometry `report.py`; centering has no plot | `make geometry-check` |
| Incomplete clause experiment and separate successor | `painter_clause_validation_v1/analysis.py`, `painter_clause_successor_v1/analysis.py` | Numerical reports; manuscript tables | `make clause-check`, `make clause-successor-check` |
| Prospective fixed-map comparison | `painter_map_validation_v2/analysis.py` | Numerical report; manuscript table | `uv run --locked python -m latent_art_bench.painter_map_validation_v2 check` |

The four-painter exploration is descriptive and retains the two later retries;
it does not restore the incomplete prompt study's primary inference. The naming,
palette, temporal, clause and fixed-map panels remain separate. The fixed-map
result reverses the historical ordering on one endpoint and must stay visible.
Temporal replication was run by the same maintainer.

Some supporting checks authenticate local response hashes even though they
replay compact measurements: full palette and fixed-map checks need retained
responses; `make palette-check` is the numeric-only palette path.

## Earlier development and public releases

These records remain dependencies or context, without new primary claims.

| Scope | Source and result | Existing offline check |
| --- | --- | --- |
| Baseline 31-feature distances | [package](../src/latent_art_bench/painter_feature_distance_v1/), [report](../reports/painter_feature_distance_v1/REPORT.md) | `uv run --locked --extra analysis --extra learned latent-art-bench feature-distances check --output reports/painter_feature_distance_v1` |
| Original prompt grid, missingness supplement and retry | [study](../studies/painter_prompt_study_v1/), [supplement](../studies/painter_prompt_supplement_v1/), [retry](../studies/painter_prompt_retry_v1/) | Versioned CLI commands below |
| Earlier mechanism diagnostic | [package](../src/latent_art_bench/painter_responsiveness_v1/), [study guide](../studies/painter_responsiveness_v1/README.md) | `make responsiveness`; human validation was not performed |
| Corpus census and empirical feature baseline | [v1 study](../studies/painter_feature_generation_v1/README.md), [v2 study](../studies/painter_feature_generation_v2/) | `make evidence`; v2 integrity: `uv run --locked latent-art-bench paper-study audit` |
| Synthetic qualification and technical pilots | Protocols and receipts in their originating study/manifests | Consult the study guide; do not rerun create-once writers |

```bash
uv run --locked python -m latent_art_bench.painter_prompt_study_v1.cli check-run pps1-gpt-prompts-20260905
uv run --locked python -m latent_art_bench.painter_prompt_supplement_v1.cli check ppss1-missingness-20260905
uv run --locked python -m latent_art_bench.painter_prompt_retry_v1 check
```

Public adapters are `tools/paper_release.py`, `paper_geometry_release.py`,
`paper_clause_release.py`, `paper_map_release.py` and
`paper_map_validation_release.py`. Their guides and receipts are linked in the
[results index](../reports/README.md#historical-public-releases). Run them against
the matching extracted archive, not an unrelated tree. The separate
`paper_map_portability_diagnostic.py` records the strict Ubuntu mismatch; it does
not change the failed replay contract.

Evidence integrity, numerical equality, figure equality and measurement validity
are different checks. Investigate mismatches against recorded inputs; never
refresh a stored hash to hide drift.
