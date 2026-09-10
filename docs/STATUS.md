# Current status — 2026-09-11

Work is on `codex/restore-four-artist-analysis`. The canonical English source is
[paper/paper.tex](../paper/paper.tex). Read [ARTIFACTS.md](ARTIFACTS.md) for retention,
[AGENT_HANDOVER.md](AGENT_HANDOVER.md) for operational boundaries and
[ANALYSES.md](ANALYSES.md) for computation and plotting commands. User-owned Korean
files and ignored research bytes remain untouched.

## Active: artist specificity across six generators

The research question is whether painter names recover artist-specific variation
beyond a shared painting appearance. The user authorized the new experiment,
proxy explanations, model regressions and a focused English manuscript. The
constraints are four painters, the existing 31 features, no human ratings, and
cumulative conservative paid accounting **strictly below $120**. Do not query
remaining credit balances.

The [fixed allocation](../studies/painter_specificity_v2/PROTOCOL.md) contains
**1,008 images: six models × 14 scenes × six clauses × two repeats**. The models
are GPT Image 1, GPT Image 2, GPT Image 2.5 Flare, GPT Image 2.5 Sunburst,
Nano Banana 2 and FLUX.2 Max. The four OpenAI configurations use medium quality.
The collector is running with at most three requests overlapping and five seconds
between starts. Do not start another collector or measure an incomplete panel.
A separate postprocessing worker waits for terminal closure, then measures,
replays four numerical views, audits raw bytes and renders figures.

Baseline accounting is **$68.50735**, including all technical probes and the
historical $5 reserve. The fixed allocation forecasts approximately $112
cumulative; admission also reserves $5 per active request. Progress-log accounting
therefore includes temporary reservations and is not settled expenditure.
The terminal receipt will establish the final total.

The scientific inputs are 649 measured reference works (297 Monet, 106 Sisley,
141 Pissarro, 105 Cézanne) and a separate 221-work development scaler. The primary
endpoint is repeat-corrected error in scene-conditional artist contrasts.
The fixed family contains six reference-aligned slopes and 15 paired model
contrasts. Absolute error, full-distribution summaries, feature families and
processing/reference sensitivities are descriptive.

Use the [corrected measurement entry point](../studies/painter_specificity_measurement_v1/CORRECTION.md)
for extraction and all replay commands. It selects the intended 649 valid works
from a historical manifest that also preserves four older measurement failures.
The frozen predecessor readers remain unchanged. An additional
[reference-content sensitivity](../studies/painter_specificity_reference_v1/PROTOCOL.md)
was declared before inspecting new outcomes and gives four coarse content classes
equal weight within each painter.

The manuscript source has been rewritten around this design; its empirical
results and conclusions remain explicitly pending. **The current `paper/paper.pdf`
is still the preceding completed manuscript.** The plotting and table templates
were committed before inspecting experimental feature outcomes. Synthetic layout
previews under `tmp/paper/` are marked and are not experimental results.

## Closed predecessor and preserved historical boundaries

The [first specificity attempt](../studies/painter_specificity_v1/TERMINATION.md)
closed permanently after 31 returned images, before feature measurement. Negative
controls showed that its upstream interface returned images for invented model
identifiers. Acceptance cannot establish distinct variant selection; this does
not prove that all valid identifiers select one model. The local adapter adds
name forwarding, while the successor uses explicit documented paid routes.
Do not measure, resume or pool the first attempt.

All earlier censuses and publication bundles remain terminal. In particular:

- The incomplete 288-slot generic-clause cohort retains 211 images and unavailable
  primary comparisons. Its separate 96-image Cézanne/generic successor is complete;
  its energy change is −1.195419353 at the fixed alpha .025.
- The prospective 240-image fixed-map comparison is complete. Translation/scaling
  improves both reference energy and conditional prediction error, contrary to the
  earlier opposing ordering. Preserve that result and its unmet observed precision
  target; no extra sampling or retroactive qualification is authorized.
- The capture audit found zero qualified independent-capture pairs after 15 metadata
  requests across five works. Capture acquisition and measurement remain closed.
- The strict Ubuntu replay of the earlier map package failed support hashes.
  The separate diagnostic found numerical differences below 4e−15 and unchanged
  displayed results; it did not turn the strict attempt into a success. The portable
  successor proposal remains deferred.

The previous paper-review iteration stopped at the user's revised condition:
round 4's mean **8.9333** exceeded round 3's **8.9000**. The original above-9
threshold was not reached. No fifth review or continued score optimization belongs
to that closed iteration. Reviews were maintainer-run LLM subagents, not independent
human or institutional review. See [the record](reviews/20260910_substantive_revision/REVIEW.md).
The [previous 39-page paper assets](../reports/paper_map_validation_reproducibility_v2/pmv2r-20260910/PAPER_ASSETS.md)
and all older releases remain unchanged; the new manuscript is not yet published.

## Verification and next handoff

The new implementation passes Ruff and **1,943 retained offline tests** in
476.14 seconds. Routine `make check` selects **822** of these; 14 new cases protect
the new numerical, routing and membership contracts. No plotting/formatting tests
were added. [Test scope](../tests/README.md) explains the earlier retirement.
The most recent historical evidence audit passes **2,902 checks with zero failures**
and the same two existing acknowledgements. New specificity namespaces require
separate numerical and raw-byte checks; the historical audit does not cover them.

After terminal collection and automatic postprocessing: inspect the actual results,
complete the paper, build and inspect every PDF page, run the four exact numerical
replays and raw-byte/presentation checks, then update this status and the handover.
Do not restart a terminal collector or overwrite a measurement receipt.
No independent-investigator replication, human style validation, independently
captured reference panel or learned-feature validation has been performed.
