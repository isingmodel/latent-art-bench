# Current status — 2026-09-08

The earlier English manuscript is complete in [paper/](../paper/README.md).
The new **painter-responsiveness diagnostic stage is implemented and published**;
its prospective 192-image experiment is not executed or empirically qualified.
There is no active collector, web-preview server or scheduled continuation.

## Completed evidence

| Item | Current state |
| --- | --- |
| Controlled study | 1,006 generated images, 70 Monet/Cézanne references, 221 development works; [report](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md) |
| Computational revision | Four feature views, variation decomposition, reference/scaler sensitivity, painter interactions, coverage and cross-route diagnostics; [report](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md) |
| Current manuscript | One TeX source, 11-page PDF, three vector figures; [build guide](../paper/README.md) |
| Responsiveness D0 | Six equal-brief named/free comparisons, 31-coordinate diagnostics, all 70 reference chroma records, and 18 simulation settings; [report with 14 tables and three plot pairs](../reports/painter_responsiveness_v1/prv1-diagnostic-20260908/REPORT.md) |
| Reference H0 | 70 normalized, opaque-name displays and 140 blinded tasks prepared under a committed exact-source freeze; zero human responses |
| Provider R0 | Three GET-only requests completed; current contract/credit do not qualify generation; [receipt](../data/manifests/painter_responsiveness_v1/prv1-diagnostic-20260908/provider_preflight.json) |

The original eight conditional randomization tests remain unchanged. Revision and
D0 diagnostics are post-result descriptions, not new confirmatory test families.
All reviews have been maintainer-run LLM subagent reviews, with coordinator checks;
none is an independent human or institutional peer review.

## What the new diagnosis shows

With equal weights over the 24 fixed briefs, painter naming reduces variation
between brief means by **26.9%–66.4%** across all six route/painter cells. The signed
cross-repetition diagnostic has the same contraction direction in all six cells.
It requires unverified stable-service/independent-repeat assumptions to estimate
stable signal; it is not an identified latent variance or a new significance test.

OAuth/Cézanne is particularly informative: between-brief variation falls **45.6%**,
while within-brief variation falls only **2.0%** under these equal weights. The
previous reference-content-weighted analysis instead had a within-brief ratio of
1.139. These are different weighting targets, not interchangeable estimates. The
new result strengthens the motivation to test responses across scene briefs;
it does not establish that painter naming impairs human-perceived fidelity.

For reference median chroma, the maximum same-file processing span is **0.1105**
primary-development IQR units. This addresses the three tested processing pipelines,
not independent capture bias. A separate metadata check of four retained works
found no verified independent capture pair; see [capture feasibility](../studies/painter_responsiveness_v1/CAPTURE_FEASIBILITY.md).

At a hypothetical −0.5 interaction for both painters, the 192-image simulation
has endpoint power of **75.3%/80.4%** under historical residual proxies, but
**21.9%/23.0%** under the declared heterogeneous-noise stress scenario. These are
conditional simulation results, not guaranteed future power or meaningful margins.

## What remains before generation

The [implementation guide](../studies/painter_responsiveness_v1/README.md) and
[protocol](../studies/painter_responsiveness_v1/PROTOCOL.md) define the next stages.
Actual independent fine-content annotation and vividness ratings, a responsible
human's reference target and meaningful margin, acceptable precision, and a feasible
generated-image human assessment plan are still absent. The reference preview is
ready at `research_workspace/painter_responsiveness_v1/prv1-diagnostic-20260908/human_reference_preview/index.html`.
A technical preview or maintainer pilot cannot count as independent validation.
The question about recruiting real raters remains unanswered.

R0 at **2026-09-08 02:21 UTC** found **$9.3126443 available** to the current key.
The pinned FLUX endpoint exists and reports **$0.07 per megapixel**. The current
implementation deliberately does not treat that as a per-image quote, and its
pricing gate remains closed. Supported endpoint metadata does not fix output
resolution or billing rounding. A successor size/pricing contract must resolve
those before dispatch; this is not a provider-outage claim. At an *assumed* one
billed megapixel per output, 192 outputs would cost $13.44 before retries, exceeding
the current balance. That illustration is not an approved quotation. The user was
asked whether to replenish credits after scientific qualification.

The earlier conservative accounting remains **$45.6819185 of the $75 ceiling**,
including the historical $5 contingency. The new namespace caps additional spending
at $20, but that cap is not account credit. **Zero new generation calls, charges,
source acquisitions or scientific feature extractions** occurred in this task.
H0 only normalized previously exposed references for display.

Staggered generation, restricted technical retries, missing-slot preservation and
three-pipeline measurement are implemented and tested prospectively. The CLI human
workflow currently covers references; collection-bound generated-human sessions
remain subsequent work. Prospective measurement has create-once integrity receipts
but no numeric replay CLI yet. Neither limitation is hidden by a completed-stage
claim. The existing paper has not been upgraded with an unperformed causal result.

## Verification and evidence boundaries

Latest implementation checks: **Ruff passes; 1,042 offline tests pass** (96.44 s).
`make responsiveness` reproduces the numerical result and all **21 report files
byte-for-byte**. All three plot layouts and the local H0 task interface were
visually checked; the interface showed zero recorded responses. The historical
integrity audit passes **2,902 checks with zero failures**, retaining only its two
existing acknowledgements. That audit does not register this new namespace;
its explicit D0 replay and H0 hash checks are separate.

D0 binds **138 inputs** at source commit `79f3573`, with freeze commit `9636b5e`.
Numeric results and H0 task freeze were published at `bc21967`. Preserve these
sources/configs/reports, the closed R0 receipt and ignored display bytes. Do not
rewrite a freeze, reopen a terminal stage or silently switch provider/parameters.
Use successor scopes for scientific or transport corrections. Current guidance
is mutable; [ARTIFACTS.md](ARTIFACTS.md) governs retained evidence.
