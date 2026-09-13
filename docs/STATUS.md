# Current status — 2026-09-13

The project is in paper correction. The canonical English
[paper](../paper/paper.tex) and [PDF](../paper/paper.pdf) are on `main`, titled
**Artist-Name Responses beyond a Shared Painting Effect in Text-to-Image
Generation**. The current PDF has 23 pages. This documentation cleanup does not
run collection, measurement or new scientific analysis.

## Completed evidence

The primary experiment contains **1,008 generated images**: six models × 14
scenes × six prompt clauses × two repeats. All outputs were collected and
measured. Its four-painter reference panel contains 649 works: Monet 297,
Sisley 106, Pissarro 141 and Cézanne 105. Scaling uses a separate 221-work
development panel and all 31 interpretable features.

The [primary report](../reports/painter_specificity_v2/psv2-20260911/REPORT.md)
and separate [post-result diagnostics](../reports/painter_specificity_review_v1/REPORT.md)
support the following conclusions:

- All six models have positive reference-aligned artist-name responses under
  the declared simultaneous inference.
- FLUX.2 Max has the lowest estimated uncalibrated error, D = 0.801, and adjusted
  advantages over both GPT Image 2.5 variants. The other 13 model differences
  remain unresolved. No model is established to beat the D = 1 no-contrast
  benchmark.
- GPT Image 2 has the strongest corrected alignment and lowest estimated error
  after held-scene scalar calibration. That descriptive ordering has no added
  model-ranking tests and is not a ranking of perceptual artistic fidelity.
- Aggregate alignment conceals weak distinctions between nearby artists,
  especially Monet and Sisley. The scene-variation component of D can also
  penalize legitimate artist-by-content variation.
- Reference examples expose calibration strips and a title-class mismatch.
  Their prevalence and effect on the full reference target remain unmeasured.

The paper also retains the four-painter descriptive analysis, generic/palette
controls and the contrary prospective fixed-map result. Cohorts remain separate;
failed or incomplete experiments have not been repaired by pooling later data.
The [results index](../reports/README.md) links the supporting evidence.

Recorded cumulative paid accounting is **$112.293676** against the user's $120
ceiling. This includes the retained historical uncertainty reserve. Documentation
cleanup makes no paid requests and does not change the ledger.

## Outstanding review requests

The latest user-supplied reviews remain in `critics/review1.md`,
`critics/review2.md` and `critics/review3.md`. They assess the revised paper and
have not yet been implemented. Their actionable priorities are:

1. Quantify reference-region and content-label defects, including the development
   panel, and compare corrected targets with the original results in a separate
   sensitivity analysis.
2. Check shared-control noise in the generic/common cosine using cross-repeat
   products. The reviewers distinguish this secondary diagnostic from primary D.
3. Give coarse versus fine artist distinctions more emphasis; quantify the
   stability of calibrated model comparisons.
4. Establish an external interpretation of the feature measures and improve
   image-level reproducibility. Numerical replay alone does not validate style
   or constitute independent research replication.

These requests are a research backlog, not results of this cleanup. Human
ratings and learned-feature validation have not been performed. Internal LLM
review scores do not establish publication readiness.

## Reproducibility and verification

The last scientific revision was checked on 2026-09-12: numerical replay,
presentation replay, retained-image hashes, Ruff and the full offline suite
passed; the PDF compiled without warnings and was visually inspected. See
[the analysis catalog](ANALYSES.md) for checks appropriate to a new change.

Earlier versioned releases retain their own verification receipts. The fixed-map
release's strict Ubuntu replay failed; its separate diagnostic did not repair
that exact-comparison contract. The current six-model experiment and 23-page
paper are committed on `main` but do not yet have a dedicated versioned release
or an exact-pixel archive.

The 2026-09-13 documentation cleanup passed local-link checks, preserved-file
hash comparisons, `make evidence`, `make specificity-check`, `make review-check`
and `make figures-check`. It did not change the paper or scientific outputs;
the full Python test suite was not rerun for this documentation change.
