# Prompt methods and feature distances from artists' paintings

This study compares generated-image distributions with the fixed original-painting reference for Monet, Sisley, Pissarro and Cézanne, separately in color, spatial structure and digital texture. It asks whether explicit style instructions and additional attention to broad visual aspects change those distances.

**Primary prompt inference is unavailable because the registered grid is incomplete.** No distance comparison, primary randomization test, selected complete-case analysis or inference plot is reported. Every planned condition and its terminal availability counts appear below.

## Population and availability

Run `pps1-gpt-prompts-20260905` registered **1,920 requests**: **1,918 generated images** and **1,918 measured images**. There are 4 repetition blocks, with all 16 original scene templates in every method × painter/artist-free × requested-service cell. The original by-name strings remain verbatim. Style instruction and style plus aspects each have their own artist-free control. No earlier generated images are pooled with these new draws.

| Requested service | Method | Condition | Planned | Generated | Measured | Normalization failures | Not generated |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gpt-image-1 | By name | Monet | 64 | 64 | 64 | 0 | 0 |
| gpt-image-1 | By name | Sisley | 64 | 64 | 64 | 0 | 0 |
| gpt-image-1 | By name | Pissarro | 64 | 63 | 63 | 0 | 1 |
| gpt-image-1 | By name | Cézanne | 64 | 63 | 63 | 0 | 1 |
| gpt-image-1 | By name | artist_free | 64 | 64 | 64 | 0 | 0 |
| gpt-image-1 | Style instruction | Monet | 64 | 64 | 64 | 0 | 0 |
| gpt-image-1 | Style instruction | Sisley | 64 | 64 | 64 | 0 | 0 |
| gpt-image-1 | Style instruction | Pissarro | 64 | 64 | 64 | 0 | 0 |
| gpt-image-1 | Style instruction | Cézanne | 64 | 64 | 64 | 0 | 0 |
| gpt-image-1 | Style instruction | artist_free | 64 | 64 | 64 | 0 | 0 |
| gpt-image-1 | Style + aspects | Monet | 64 | 64 | 64 | 0 | 0 |
| gpt-image-1 | Style + aspects | Sisley | 64 | 64 | 64 | 0 | 0 |
| gpt-image-1 | Style + aspects | Pissarro | 64 | 64 | 64 | 0 | 0 |
| gpt-image-1 | Style + aspects | Cézanne | 64 | 64 | 64 | 0 | 0 |
| gpt-image-1 | Style + aspects | artist_free | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | By name | Monet | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | By name | Sisley | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | By name | Pissarro | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | By name | Cézanne | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | By name | artist_free | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | Style instruction | Monet | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | Style instruction | Sisley | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | Style instruction | Pissarro | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | Style instruction | Cézanne | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | Style instruction | artist_free | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | Style + aspects | Monet | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | Style + aspects | Sisley | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | Style + aspects | Pissarro | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | Style + aspects | Cézanne | 64 | 64 | 64 | 0 | 0 |
| gpt-image-2 | Style + aspects | artist_free | 64 | 64 | 64 | 0 | 0 |

These counts distinguish generation availability from measurement success; every failure remains in the complete availability export and terminal ledgers.

[Template-level availability](template_availability.csv) retains every one of the 480 service × method × condition × template cells, including all failures and ungenerated dispositions.

The source method is `pfg2-method-20260905`. Its already exposed fixed reference contains 649 measured digital surrogates of Wikidata-declared outdoor-place paintings. These are not a new holdout or a probability sample of the artists' complete oeuvres. New prompt wording and inference were fixed before new generation, after the earlier reference and generated results were exposed.

The original 512-pixel normalization and all 31 raw features are reused. The unchanged scaler was fitted to 221 new-development paintings using equal painter weights: each coordinate subtracts its frozen median and divides by its frozen IQR. Color has 11 coordinates, spatial/orientation 8, and digital texture 12. Family magnitudes are not directly comparable and are never combined. No scaler is fitted to the new generated outputs.

## Distance and prompt-effect estimands

Finite empirical energy distances and randomized prompt comparisons were planned. They remain unavailable for this incomplete grid, and no corresponding numerical result tables or confidence intervals are emitted.

## Prospective randomization calibration

The frozen [calibration decision and numerical tables](../../../data/manifests/painter_prompt_study_v1/pps1-randomization-20260905/decision.json) record method qualification at one, two and four repetitions using synthetic contribution magnitudes and randomized assignment signs, without tuning on new empirical outcomes. The numerical tables include family error, sign-alignment power diagnostics and deliberately invalid persistent-sign stress. These are contribution-space simulations; they do not establish no interference in a remote service or guarantee power for real prompt effects. The small image budget limits precision and population generalization.

## Observed service behavior and interpretation limits

`gpt-image-1` and `gpt-image-2` are requested OAuth service aliases with no independently attested underlying model snapshots. Requested 1024×1024, medium, opaque PNG settings are distinct from reported quality and decoded geometry. The table records provider metadata, not visual-quality rankings; complete reported model/settings, geometry counts and latency summaries are retained in [service_diagnostics.json](service_diagnostics.json).

| Service | Method | Generation statuses | Reported quality counts | Distinct decoded sizes | Setting mismatch counts |
| --- | --- | --- | --- | --- | --- |
| gpt-image-1 | By name | {"generated":318,"refused":2} | {"None":2,"low":318} | 29 | {"decoded_size":318,"quality":318,"size":318} |
| gpt-image-1 | Style + aspects | {"generated":320} | {"low":317,"medium":3} | 32 | {"decoded_size":320,"quality":317,"size":320} |
| gpt-image-1 | Style instruction | {"generated":320} | {"low":316,"medium":4} | 29 | {"decoded_size":320,"quality":316,"size":320} |
| gpt-image-2 | By name | {"generated":320} | {"low":320} | 36 | {"decoded_size":320,"quality":320,"size":320} |
| gpt-image-2 | Style + aspects | {"generated":320} | {"low":319,"medium":1} | 31 | {"decoded_size":320,"quality":319,"size":320} |
| gpt-image-2 | Style instruction | {"generated":320} | {"low":316,"medium":4} | 31 | {"decoded_size":320,"quality":316,"size":320} |

Subject content, aspect ratio, color profiles, source workflows and digital reproduction may alter these measurements. The 31 features do not isolate content-free style, artistic quality, intention or physical brushwork. Independent capture calibration and a validated equivalence margin are absent. No comparison here establishes reproduction, authorship or broad model superiority.

Reviews were maintainer-run LLM subagent reviews, not institutionally independent reviews. No manuscript or artistic-quality winner is produced by this report.

## Complete exports and provenance

[availability.csv](availability.csv), [inputs.csv](inputs.csv), [template_availability.csv](template_availability.csv). CSV files retain full floating-point precision; nested counts remain JSON cells. No confidence-interval columns are manufactured. Figures are provided as PNG and SVG. The report command reads only numeric evidence and metadata.

The complete [analysis.json](../../../data/manifests/painter_prompt_study_v1/pps1-gpt-prompts-20260905/analysis.json) and [report receipt](../../../data/manifests/painter_prompt_study_v1/pps1-gpt-prompts-20260905/report_receipt.json) bind the source analysis, implementation and every report file by SHA-256. Existing reports are never overwritten.
