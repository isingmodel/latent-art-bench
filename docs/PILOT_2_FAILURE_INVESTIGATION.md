# pilot_2 failure investigation and redesign record

## Scope

This record explains why the earlier pilot could not support its intended inference, what was
verified against the cited papers and released code, and why the `pilot_2` corrections are
methodologically different from retrying until a favorable statistic appears. The real-image
calibration evidence was available during redesign. The generated-output phase remains
prospective and begins only after the frozen protocol commit.

## Image transport failures

The earlier local OAuth path accepted both requested labels but did not reliably honor an
explicit `1024x1024` request. The corrected `~/dev/openai-oauth` checkout was therefore tested
at a dedicated listener, separate from the older process. A captured runtime fingerprint binds
the listener PID, executable, working directory, checkout revision, relevant source-file
hashes, health response, model catalog, and endpoint behavior without storing credentials.

The common condition is now `size: auto`, `quality: low`, and PNG for both and only
`gpt-image-1` and `gpt-image-2`. This is an operational requested-label comparison: the OAuth
response does not attest which upstream model executed. The code revalidates the same process,
checkout, source snapshot, health endpoint, and two-label catalog before conformance and before
the full grid. It never silently falls back to another model or transport.

Every logical cell has at most ten identical physical sends. Only transport exceptions, HTTP
408/409/425/429, and HTTP 5xx are retryable. Refusals, other HTTP 4xx responses, malformed
successful responses, and ineligible decoded geometry are terminal. All sends enter an
append-only ledger; the tenth transient failure becomes an explicit retry-cap terminal outcome
for analysis rather than disappearing.

## Real-image acquisition failures

The deterministic 40-work atlas exposed five selected records that were not already present in
the prior local corpus. The two NGA images were acquired through the museum image service. The
three AIC IIIF URLs returned HTTP 403 to the command-line client even though the public artwork
pages could load the image assets. Those exact page assets were acquired through the browser
page context, then decoded, visually checked against the artwork page, hashed, and recorded
in the real-image manifest. No alternative artwork was substituted because of acquisition
difficulty.

## Learned-formal failure and paper/code reconciliation

Kim et al. describe an A-vector derived from the Stable Diffusion 2.0 VAE. Their released
extractor samples the posterior but does not publish an RNG realization for the paper's corpus.
It also resizes and rewrites using the input filename extension, which creates a codec-dependent
path when real inputs are JPEG and generated inputs are PNG. Consequently, exact recovery of an
unpublished stochastic realization is not a defensible claim.

`pilot_2` uses a project-defined harmonization that keeps the paper/code representation while
removing the origin-codec asymmetry: every origin first becomes a deterministic, metadata-free
sRGB PNG; the VAE input is resized with the pinned OpenCV operation; posterior sampling uses a
content-derived seed; and the resulting 16,384-value vector is content-addressed. Four
artist-stratified repeat probes must be bit-identical. PCA is fitted once on the 24 real training
works and its mean, basis, and state are frozen before generated images exist.

The first calibration design additionally required separate opposite-source refits: train on
one museum and test on the other. The AIC-held fold scored exactly chance (0.25). Treating that
as the generation gate was misaligned with the registered downstream analysis, which uses one
pooled PCA and one pooled set of artist centroids with source-stratified reference diagnostics.
It also tested a different transform in each fold on only eight held works.

The corrected gate does not discard the source issue or lower the threshold. It fits the single
downstream classifier on all 24 training works, tests it on all 16 held works, and then tests
that unchanged classifier separately on the eight AIC and eight NGA held works. All three must
beat four-class chance. The pooled constrained permutation test remains required. The old
opposite-source scores and pooled source-label predictability remain in the qualification
artifact as non-gating development diagnostics. Per-source `n=8` is explicitly too coarse for
a general domain-robustness claim.

The final real-only calibration result is:

- pooled held artist balanced accuracy: 0.500;
- unchanged pooled classifier on AIC held works: 0.625;
- unchanged pooled classifier on NGA held works: 0.375;
- constrained permutation: 215 exceedances in 9,999 draws, `p = 0.0216`;
- train-only PCA: 22 components, cumulative explained variance 0.9707404656;
- opposite-source development diagnostics: AIC 0.250, NGA 0.375;
- pooled source-label predictability diagnostic: 0.8125;
- deterministic repeat probes: four of four exact.

## Chromatic failure and paper reconciliation

Lee et al. define adjacent-pixel CIE Lab distances and the seamlessness statistic
`(sigma_d - mean_d) / (sigma_d + mean_d)`. Their Figure 1 demonstrates a mean-rescaled
distribution comparison for two example paintings. The paper does not establish the earlier
project-specific K-S margin, a corpus-wide collapse result, or an artist-classification gate.
Using those unreported criteria as if they came from the paper was therefore unsupported.

The corrected pilot keeps Lee's formula at one frozen 500-pixel long-side scale and adds a
fixed Hellinger-embedded histogram as descriptive secondary evidence. It reports real
artist-by-source summaries, requested-label named/control summaries, and per-artist matched
named-minus-control summaries. These values cannot open the generation gate, rescue the primary
analysis, or support a cross-label ranking.

## Prospective safeguards

The prompt text, artist roster, neighbors, 320 logical cells, deterministic 64-batch send
schedule, conformance cells, retries, preprocessing, PCA, estimands, bootstrap, exact sign-flip
test, and multiplicity decisions are all content-addressed before the first generated output.
Generated images are never selected by visual quality. A completed null or negative result is
a successful pilot execution; it does not authorize new prompts, more samples, exclusions, or
threshold changes.

Primary sources: Kim et al., *Scientific Reports* (2026), DOI
`10.1038/s41598-025-30166-1`; released code at
<https://github.com/aljinny/art-history>; Lee et al., *PLOS ONE* (2018), DOI
`10.1371/journal.pone.0204430`.
