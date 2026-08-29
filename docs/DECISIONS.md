# Project Decisions

This file records decisions that define the current research scope. Items may change only through a documented revision.

## Confirmed decisions

1. The project will be developed as a benchmark-oriented research program.
2. The primary target is artist- and movement-level latent style fidelity, with era and work levels retained as hierarchical contexts.
3. All visual feature gaps supported by the source-paper lineage will be considered, subject to paper-specific eligibility and validation gates.
4. Text-only and image-conditioned generation will be evaluated as separate conditions.
5. Multiple generator families will be compared, including reproducible open-weight and closed multimodal systems.
6. The initial discovery corpus will focus on Western canonical painting, reflecting the domain of the source methods and available reference data.
7. Non-Western and long-tail targets will form a separate external challenge corpus.
8. Corpus design is treated as a primary experimental variable rather than a neutral implementation detail.
9. The source papers' domains and inclusion rules will be followed through paper-specific corpus views rather than one imposed genre taxonomy.
10. Functional replication on real artworks is a mandatory gate before generated-image evaluation.
11. Functional replication emphasizes recovery of defining behavior and major directions rather than exact numerical identity when original files are unavailable.
12. Resolution, resampling, compression, color management, and alternative digital reproductions will be explicitly calibrated.
13. The evaluation will be automated; human expert or crowd ratings are outside the current scope.
14. “Style understanding” will be used only as an operational shorthand for measured latent style fidelity, not as a claim about human-like understanding or aesthetic essence.
15. A multidimensional diagnostic profile will be retained. The choice between an aggregate score, a leaderboard, or profile-only reporting is deferred.
16. Public project documents will be written in English.

## Open strategic decisions

- final benchmark name and branding;
- exact target roster and minimum corpus sizes;
- generator and evaluator versions at preregistration;
- formal exposure-proxy construction;
- aggregate scoring and leaderboard policy;
- long-term model-submission governance;
- archival and dataset hosting arrangements.

## Decision rule

Implementation details should not be fixed before the evidence they depend on exists. In particular, sampling counts, prompt grids, and score weights will follow pilot variance, corpus availability, rights review, and validation results.
