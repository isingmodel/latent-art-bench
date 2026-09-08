# Current status — 2026-09-08

The active follow-up is **computational painter responsiveness v2**, authorized by
the user's instruction to continue without human reference ratings. Its source and
192-slot design are committed and frozen. The first OAuth allocation is closed
after an unrecognized plain-text 503; a narrowly corrected replacement is being
prepared now.
The new experiment tests a measured service response; it does not claim human
perceptual resemblance or an identified internal model mechanism.

## Current execution

- Replacement: `prv2-oauth-recovery-20260908`; 192 fresh planned images, six fixed
  scenes, four style arms,
  two color instructions and four repeats. Free and generic controls are shared.
- Transport: source/process-verified local OAuth `gpt-image-2`, at most two calls
  in flight, starts at least five seconds apart, bounded technical retries.
- Original source commit: `d3bbe65`; design freeze commit: `491cc10`; 131 bound inputs.
  Its terminal run retained 49 images, one complete HTTP 503 and 142 never-started
  slots. A [prospective correction](../studies/painter_responsiveness_recovery_v1/PROTOCOL.md)
  qualifies only that exact error form for existing bounded retries. Prior outputs
  remain ancillary; successful images were not visually reviewed and scientific
  features were not extracted before the replacement decision.
- No OpenRouter requests or charges in this experiment. The prior conservative
  accounting remains $45.6819185 within the $75 ceiling; OAuth subscription usage
  is not assigned a monetary value.
- Generated feature measurement begins after terminal collection. Human ratings,
  new original-painting acquisition and learned features are outside this scope.

Do not edit frozen v2 source, tests, configuration or protocol while collection is
running. Do not launch a second collector. A stopped or completed allocation is
closed and cannot be resumed or refilled. See the
[implementation guide](../studies/painter_responsiveness_v2/README.md) and
[protocol](../studies/painter_responsiveness_v2/PROTOCOL.md).

## New retained-data finding

The [scene-retrieval report](../reports/painter_responsiveness_v2/prv2-oauth-20260908/diagnostics/REPORT.md)
is published. Painter naming reduces between-scene variation in all six historical
route/painter cells, but retrieval **improves in two and declines in four**.
FLUX/Monet improves from 44.4% to 59.7%, whereas Nano Banana 2/Cézanne declines from
66.7% to 41.7%. OAuth/Monet declines from 79.2% to 70.8%; OAuth/Cézanne from 83.3% to
69.4%. These are held-repetition, 24-scene nearest-centroid descriptions in the
fixed 31-feature space, not new significance tests or human scene-adherence scores.
Contraction alone therefore does not establish lost scene information.

The report includes all 450 comparisons across five feature views, three pipelines
and both 24-scene/within-class candidate controls. The sealed JSON retains exact
query/split identities and 25,920 predictions. A separate 5,000-trial-per-scenario
precision sensitivity uses historical OAuth residual proxies and hypothetical
interactions; it is not a human margin or a guarantee of future power.

## Preserved earlier work

| Item | State |
| --- | --- |
| Controlled study | 1,006 generated images, 70 Monet/Cézanne references and 221 development works; [report](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md) |
| Computational revision | Four feature views, variance decomposition, reference/scaler sensitivity and cross-route diagnostics; [report](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md) |
| Current manuscript | The earlier study's English paper, one TeX source and 11-page PDF; [guide](../paper/README.md) |
| Responsiveness v1 D0 | Six equal-brief diagnostics and original-reference chroma summaries; [report](../reports/painter_responsiveness_v1/prv1-diagnostic-20260908/REPORT.md) |
| Responsiveness v1 H0/R0 | Reference tasks prepared with zero human responses; closed FLUX preflight does not qualify its paid/human scope. This does not block the new computational OAuth scope. |

The original eight conditional randomization tests and all earlier evidence remain
unchanged. The v1 human/reference prerequisites were not retroactively waived or
fulfilled. Its source commit `79f3573`, D0/H0 freezes, reports, closed R0 receipt and
ignored displays remain preserved. Current manuscript claims have not been upgraded
with an unmeasured prospective result.

## Verification

The full v2 offline suite passed **1,112 tests**, including deterministic byte
replay and unavailable-primary output. The isolated recovery tests are additional.
Ruff passes. The retained-data analysis and all nine diagnostic report files
reproduce byte for byte. Both actual diagnostic plots and all six synthetic plot
types were visually checked. Three
maintainer-run LLM subagents reviewed methods, transport and rendering, with
coordinator checks; these are not independent human or institutional reviews.
See the [review record](reviews/20260908_computational_responsiveness/REVIEW.md).

The historical evidence audit passes **2,902 checks with zero failures**, retaining
only its two existing acknowledgements. This historical audit does not register v2;
its own offline numerical/report replay commands are separate. After terminal
publication, `make computational-responsiveness` verifies both new report bundles.
Current guidance is mutable; [ARTIFACTS.md](ARTIFACTS.md) governs retained evidence.
