# Research Roadmap

The roadmap is organized by evidence gates rather than fixed calendar dates. Timing and sample-size commitments will follow a resource audit and pilot variance estimates.

## Phase 0: Governance and reproducibility foundation

### Objectives

- finalize terminology and claims policy;
- establish repository, issue templates, and versioning rules;
- define rights-aware acquisition and release procedures;
- create canonical metadata and provenance schemas;
- register unresolved methodological decisions.

### Deliverables

- research proposal;
- benchmark specification;
- corpus and rights policy;
- validation protocol;
- initial reference implementation skeleton.

### Exit criterion

The project can trace every planned image, label, feature, and result to a versioned source and permitted use.

## Phase 1: Source-method replication

### Objectives

- implement all core feature families;
- reproduce representative image-level results;
- recover principal aggregate findings on comparable real corpora;
- document ambiguities in papers, supplements, and public code.

### Deliverables

- module-level replication reports;
- synthetic unit tests;
- source-faithful preprocessing configurations;
- pass, conditional-pass, or fail decisions.

### Exit criterion

Only features with interpretable functional replication advance to measurement calibration.

## Phase 2: Resolution and reproduction calibration

### Objectives

- assemble the multiple-reproduction calibration corpus;
- compute multiresolution feature-response curves;
- test compression, color-management, border, and aspect-ratio effects;
- estimate feature-specific reproduction noise floors.

### Deliverables

- reliability matrix by feature and resolution;
- canonical and multiscale analysis rules;
- reproduction-noise baselines;
- documented restrictions or exclusions.

### Exit criterion

Every retained feature has a justified preprocessing rule and a known domain of reliable inference.

## Phase 3: Real-art reference atlas

### Objectives

- curate the Western canonical discovery corpus;
- construct canonical-work-level splits;
- quantify era-, movement-, and artist-level signal;
- freeze validated transformations and reference distributions.

### Deliverables

- versioned discovery corpus manifest;
- held-out validity report;
- frozen reference atlas;
- paper-specific eligible views;
- evaluator cards documenting provenance and limits.

### Exit criterion

Every benchmark module demonstrates held-out real-group validity at the target level for which it will be used.

## Phase 4: Generator matrix and benchmark pilot

### Objectives

- freeze the initial open and closed model set;
- collect text-only and image-conditioned outputs;
- run the frozen benchmark without refitting;
- audit evaluator-family and memorization effects;
- estimate statistical power for the full comparison.

### Deliverables

- versioned generated corpus manifest;
- pilot style gap profiles;
- variance and power analysis;
- preregistered full-study analysis plan;
- any revised benchmark rules justified without reference to final model rankings.

### Exit criterion

The pilot supports identifiable model, target, and feature effects without unacceptable measurement or sampling ambiguity.

## Phase 5: Full discovery benchmark

### Objectives

- compare model families and conditioning modes;
- test semantic-formal asymmetry;
- test hierarchical degradation and prototype contraction;
- measure cross-feature coherence;
- quantify exposure and canon associations.

### Deliverables

- complete multidimensional benchmark profiles;
- uncertainty and robustness analyses;
- model and evaluator cards;
- manuscript for the generative-model benchmark.

### Exit criterion

All reported conclusions survive the preregistered held-out, preprocessing, and evaluator robustness analyses or are explicitly labeled conditional.

## Phase 6: External challenge evaluation

### Objectives

- apply the frozen benchmark to non-Western and long-tail targets;
- identify failures of generator knowledge, label ontology, corpus quality, and feature transferability;
- avoid treating the discovery taxonomy as a universal ontology.

### Deliverables

- challenge corpus manifest;
- target-level validity audit;
- comparative challenge report;
- revisions proposed for a later benchmark version, without retroactively changing the frozen discovery evaluation.

## Phase 7: Public release

### Objectives

- release validated code, manifests, evaluator configurations, and permitted derived data;
- archive a versioned release;
- publish reproducible examples and documentation;
- define maintenance and submission policies.

### Deliverables

- tagged benchmark release;
- public result schema;
- governance policy for adding models and targets.

## Deferred decisions

The following decisions should be made after the relevant pilot evidence is available:

- exact model roster and versions;
- artist and movement counts;
- minimum works per target;
- generation prompt matrix and repetition counts;
- reliability thresholds;
- dimensionality retained in learned feature spaces;
- aggregate score, weights, and leaderboard policy;
- cadence for adding models and external submissions.
