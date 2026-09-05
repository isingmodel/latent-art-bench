# Painter Feature Generation v2 — empirical comparison amendment 1.2

Issued 2026-09-05 after the maintainer instructed continued implementation of the analysis.
The immediate deliverable is an empirical analysis report, not a manuscript. This amendment
does not change any completed access experiment, running SD-Turbo generation, original-image
terminal acquisition, replacement rendering contract, physical-work roles, or feature formulas.

## Timing and estimands

The SD-Turbo run and replacement real-image acquisition have begun. Active painter-image features
and confirmation results have not been accessed. The preceding access experiment returned two
neutral synthetic images with requested-versus-returned settings mismatches; those responses were
decoded for transport diagnosis, not measured as painter evidence. They remain excluded here.

SD-Turbo retains its original 25-block, 2,000-request contract and 60-endpoint analysis. Add one
separately frozen **exploratory OAuth-service experiment**: two requested aliases, all 16 exact
v1 templates, five conditions, one repetition, 160 image requests total. This is a complete
prospective pilot, not a favourable prefix of a 4,000-request study. No repetition-based confidence
intervals, significance labels, or independent-model ranking may be attached to this pilot.

The OAuth estimand is the output of the specified dated service route under each **requested
alias**, not independently attested GPT-Image-1/GPT-Image-2 weights. Changing to this service-level
interpretation is explicit and prospective; it does not repair the failed size/quality contract
of the earlier access experiment. Its purpose is to measure the available service while retaining
the identity and control limitations needed to interpret any later paper.

## OAuth generation contract

Use the existing current-source, loopback-only openai-oauth instance at `127.0.0.1:10532`, with
its normal Codex OAuth credential handling. Bind its recorded source revision through the prior
access freeze, receipt, and offline diagnosis. No credential reads by this research client,
public paid-API fallback, service modification, reference images, or moderation override.

Request the exact registered painter and artist-free strings, `n=1`, `size=1024x1024`,
`quality=medium`, `output_format=png`, `background=opaque`. No seed is claimed or sent. Pair
the two aliases by template/condition, not latent randomness: hash-sort all 80 cells and alternate
the within-cell alias order by a fixed hash. Preserve this order, including failed requests.

Issue one request at a time, at least 15 seconds between starts. Timeout 240 seconds; response
ceiling 64 MiB; free-disk reserve 5 GiB. Preserve exact response bytes (or a flagged partial body
on interruption/ceiling), status, latency, allowlisted response headers, supplied strings, reported
model/quality/size/usage, decoded geometry/format, and image hash. Never follow output URLs or
redirects. Accept exactly one fully decodable JPEG/PNG/TIFF/WebP with native short side at least
512 for measurement; this is the service-output contract, not a claim that requested settings
were honored. Log every requested/returned mismatch and retain off-topic or duplicate outputs.

No generation request is automatically retried. Authentication or rate/quota failure closes the
pilot with all remaining requests explicitly unattempted; do not send into a known quota block.
Other failures remain failures. Interrupted requests with unknown outcomes are never rerolled.
Resumption may dispatch only never-attempted requests under the unchanged freeze; a terminal run
is permanently closed. Any deliberate retry of a terminal run needs a new ID and predecessor
evidence, never a top-up. A failed/partial grid receives availability reporting only, not a
silently reweighted comparison.

## Measurement and confirmation

Freeze the shared method after complete real-image acquisition and before feature extraction.
Bind both registered generation freezes and every method module used by the analysis. Development
scaling remains equal-painter, new-development-only median/IQR; historical development is not
used to fit it. Qualification is a diagnostic, not a pipeline selection loop.

Open real confirmation once only after development scaling, qualification, synthetic calibration,
and **both generation experiments' terminal dispositions** are committed. Complete SD-Turbo and
complete OAuth grids are assessed independently; an unavailable OAuth grid cannot prevent
reporting the unchanged SD-Turbo experiment, but must be reported as a failed empirical target.
Record access for every read and bind the opening to all experiment receipts and output manifests.
All experiments use the same successfully measured, finite confirmation work population.

All primary features use the frozen 512-pixel short side. For complete OAuth cells, report finite
empirical energy distance with both finite self terms (V-statistic), uniformly over the 16 fixed
templates. Report own-target, all three wrong-painter contrasts, artist-free contrast, and
coordinate medians/IQRs descriptively. This finite-sample statistic is not the SD-Turbo generator
U-estimator. Also give the SD-Turbo **finite descriptive** statistic in cross-service tables so
that a table never compares different estimators without labeling them. Different generated
sample sizes and the OAuth single repetition remain explicit limitations; do not rank winners.

Retain the original SD-Turbo 9,999 whole-block bootstrap and simultaneous 60-endpoint intervals.
Numerical calibration uses known finite synthetic generator populations (eight possible blocks,
16 templates, 31 coordinates), 100 trials per null/shift/dispersion scenario, 999 bootstrap draws
per trial, and fixed PCG64 seed 20260905. Evaluate all 60 endpoints jointly against exact finite
population truths. Report familywise coverage, zero-variance endpoints, bias, and Monte Carlo
uncertainty. Synthetic trials are method diagnostics, never empirical painter results. Poor
calibration is disclosed and downgrades inferential interpretation; it does not authorize retuning
after seeing the active result or treating nominal coverage as a verified guarantee.

## Robustness and reporting

Uniform 1% crop sensitivity uses both uncropped and cropped images at short side 496, so no
generated image is upsampled. Measure every successfully primary-measured real and generated
image under both branches; fit a separate 496-pixel uncropped new-development transform and
apply it unchanged to both branches. Report paired feature changes and finite-energy contrast
changes. This is a diagnostic, not an independent-capture calibration or another confirmatory test.

Report acquisition/measurement attrition by painter and fixed role; metadata content and collection
composition; ICC/profile, resolution and aspect-ratio distributions; feature discrepancies within
content/profile strata where supported (otherwise unresolved); exact-file duplicates and unvalidated
63-bit perceptual-hash near-neighbour diagnostics. Collections are not asserted capture workflows.
Report every invalid family, sparse stratum, incomplete grid and known exposure limitation.

The final report must distinguish completed estimates, exploratory service comparisons, nominal
uncertainty, failed gates, and unexecuted work. No result demonstrates equivalence without the
independent-capture qualification and justified margins that remain unavailable. No institutionally
independent review is claimed; all checks here are operator/LLM-assisted.
