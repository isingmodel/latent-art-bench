# Painter Features v1

Status: prospective design framework; not a preregistration or executable protocol; no artwork
acquisition or feature extraction authorized

Protocol family: `painter_features_v1`

This namespace relaunches LatentArtBench as a measurement study. It does not continue or
repair Pilots 0-3. Its target is the **painter feature** used in Pilot 2: a reproducible,
painter-associated distribution across multiple works, not a generic description of an
individual painting. Observable image coordinates are candidate ingredients only. They become
painter features only if they show painter specificity across held-out works while resisting
source, subject, genre, medium, date, and reproduction confounds.

The study deliberately avoids a single "style score." A painting can be similar to another in
palette, spatial organization, mark scale, depicted content, iconography, or a learned model's
representation while being dissimilar on the other dimensions. Calling all of these signals
"style" would hide the construct being measured.

## Research objectives

1. Estimate how much each candidate measurement changes across digital reproductions of the
   same physical work and across controlled preprocessing perturbations.
2. Estimate each painter's within-painter distribution and test whether between-painter signal
   remains after matching or adjusting for content, medium, date, and provider.
3. Qualify interpretable feature families for color/luminance, spatial structure, and ordinal
   complexity only when they contribute reproducible painter specificity beyond confounds.
4. Evaluate learned embeddings as model-dependent appearance or contextual diagnostics,
   including explicit tests for source, content, label, and training-data confounding.
5. Establish whether any qualified coordinates converge with human judgments under
   content-controlled tasks while remaining discriminant from source and subject matter.
6. Preserve Pilot 2's paired target-improvement and target-versus-neighbor specificity ideas,
   but compare later outputs to qualified painter distributions rather than fragile centroids.
7. Freeze a painter-feature profile and analysis plan before any generated-image comparison.

## Units and vocabulary

- **Physical work**: the underlying painting. This is the primary sampling unit for claims
  about paintings.
- **Digital reproduction**: one capture, scan, catalog derivative, or web delivery of a
  physical work. Reproductions are nested observations, not independent paintings.
- **Feature coordinate**: a defined numerical measurement with a stated input domain.
- **Feature family**: related coordinates that answer one construct question.
- **Painter feature**: a qualified distribution or model of feature coordinates for painter
  \(a\), conditional on the study's content, medium, period, and source design. It is not one
  painting, a centroid alone, or an artist-name classifier score.
- **Common support**: the connected, frozen set of joint content, medium, phase, and source cells
  in which the registered painter contrast is identified without extrapolation.
- **Source-faithful branch**: reported preprocessing reconstructed as closely as the available
  artifact contract permits. It is not called an exact replication when code, weights, hashes,
  environment, fixtures, or stochastic realization are missing.
- **Harmonized branch**: a common, color-aware, aspect-preserving pipeline used to test
  comparability.
- **Measurement qualification**: evidence that a coordinate is repeatable, robust enough for
  its intended estimand, and appropriately interpreted. Classification accuracy alone is not
  qualification.

## Documents

- [`MEASUREMENT_PROTOCOL.md`](MEASUREMENT_PROTOCOL.md) defines the observation model,
  preprocessing branches, candidate coordinates, provenance, and method-specific limits.
- [`VALIDATION_PROTOCOL.md`](VALIDATION_PROTOCOL.md) defines perturbation, reproduction,
  construct, human, and external-validation gates.
- [`ANALYSIS_AND_CLAIMS.md`](ANALYSIS_AND_CLAIMS.md) fixes the sampling units, estimands,
  inferential rules, multiplicity policy, and permitted language.
- [`../../literature_reviews/`](../../literature_reviews/) contains the review protocol,
  evidence matrix, critical reviews, and method decisions supporting this design.

## Present boundary

This design package performs no corpus download, provider access, sealed-holdout access,
feature extraction, model-weight download, or image generation. It specifies the scientific
architecture and failure conditions but is not yet prospectively executable. A later, separately
reviewed execution-freeze artifact must name the corpus, rights, providers, common-support table,
reproduction incidence/rank audit, sample-size simulations, estimators, exact artifacts, SESOIs,
experiment-wide decision tree, missingness scenarios, qualification thresholds, and terminal
actions; it must be committed before any of those operations begin.
