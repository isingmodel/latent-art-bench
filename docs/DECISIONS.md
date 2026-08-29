# Project Decisions

This file records decisions that define the current research scope. Items may change only through a documented revision.

## Confirmed decisions

1. The project will be developed as a benchmark-oriented research program.
2. The umbrella construct is artist-distribution fidelity. Formal style, contextual or iconographic fidelity, coverage, and cross-layer coherence are distinct subconstructs and must not be collapsed without validation.
3. The long-term program may qualify all feature families supported by the source-paper lineage, but the first benchmark study will use a small preregistered core. Additional modules must earn inclusion independently.
4. The first generative benchmark is text-only. Image-conditioned generation is a later, separately identified task rather than a directly comparable condition.
5. Multiple generator families will be compared, including reproducible open-weight and closed multimodal systems.
6. The initial discovery corpus will focus on Western canonical painting, reflecting the domain of the source methods and available reference data.
7. Non-Western and long-tail targets will form an external-validity and ontology-transfer corpus. It is a stress test of both generator and benchmark and will not be folded into a universal leaderboard.
8. Corpus design is treated as a primary experimental variable rather than a neutral implementation detail.
9. The source papers' domains and inclusion rules will be followed through paper-specific corpus views rather than one imposed genre taxonomy.
10. Functional replication on real artworks is a mandatory gate before generated-image evaluation.
11. Functional replication emphasizes recovery of defining behavior and major directions rather than exact numerical identity when original files are unavailable.
12. Resolution, resampling, compression, color management, and alternative digital reproductions will be explicitly calibrated.
13. The released benchmark will be automated. A limited blinded human study is permitted only for construct qualification and metric selection; it is not an aesthetic-quality leaderboard.
14. “Style understanding” is not a benchmark output. “Perceptual style fidelity” may be used only for measurements that pass the human qualification protocol; otherwise reports must name the measured feature space.
15. A multidimensional diagnostic profile will be retained. The choice between an aggregate score, a leaderboard, or profile-only reporting is deferred.
16. Public project documents will be written in English.
17. Generated distributions are conditional on generator version, prompt distribution, conditioning mode, seed or repetition policy, and output-selection policy. These factors are part of the estimand, not incidental metadata.
18. Era, movement, artist, genre, medium, and artist phase are cross-classified variables unless a particular corpus view justifies a nested relation. Work-level similarity belongs to an instance-reconstruction or memorization track.
19. Target specificity and prototype contraction are the primary scientific questions for the first generative benchmark. Cross-layer incoherence is secondary.
20. Exposure analyses are associational and must use the term “exposure proxy”; causal training-exposure claims are not supported for closed models.
21. Reproduction-pair calibration estimates variable surrogate error but does not remove common acquisition-domain bias. Source prediction, leave-source-out validation, and born-digital controls are required for source-sensitive features.
22. Review recommendations are adopted only when they improve identification, validity, or feasible inference. Expensive controls and additional modules may be deferred when a simpler negative control addresses the same immediate risk.
23. The first implementation cycle is a development pilot, not the benchmark. It stops after a reproducible initial-results report and decision memo.
24. The development pilot is artist-level only: four provisional public-domain artists, two neighbor pairs, one shared genre, and one fixed open-weight generator.
25. The pilot qualifies exactly two measurements before generation: normalized chromatic-distance/seamlessness and one frozen learned-formal evaluator selected before corpus results are inspected.
26. Pilot inference is limited to calibrated target gap and target-versus-neighbor specificity. Prototype contraction, coverage, coherence, movement inference, and evaluator-family robustness are deferred until initial variance and corpus support are known.
27. Generator integration cannot begin until the two measurements pass or conditionally pass real-only replication, stability, nuisance, and held-out validity gates.

## Open strategic decisions

- final benchmark name and branding;
- exact target roster and minimum corpus sizes;
- generator and evaluator versions at preregistration;
- formal exposure-proxy construction;
- aggregate scoring and leaderboard policy;
- long-term model-submission governance;
- archival and dataset hosting arrangements;
- final size of the human qualification subset;
- which optional feature modules advance beyond the core benchmark;
- exact four-artist development roster and shared genre;
- learned-formal checkpoint and source implementation for the development pilot;

## Decision rule

Implementation details should not be fixed before the evidence they depend on exists, but design variables that define the estimand must be specified before the benchmark pilot. Sampling counts will follow a calibration pilot and power simulation. Prompt families, primary endpoints, exclusion rules, and test-set seals must be frozen before any benchmark-pilot model comparison. Aggregate score weights, if ever used, require a separate justification and benchmark version.

## Disposition of external critiques

The reviews in `critics/01.md` and `critics/02.md` are treated as adversarial evidence, not as a specification.

### Adopted

- separate formal style, contextual fidelity, coverage, and coherence;
- make the prompt distribution and conditioning mode part of the estimand;
- narrow the initial study to text-only generation, 8–12 provisional artists, three measurement layers, and two co-primary endpoints;
- use cross-classified art-historical labels, source and acquisition controls, equal-sample comparisons, and associational exposure language;
- treat non-Western and long-tail work as ontology transfer rather than a universal leaderboard split.

### Adopted with limits

- Human judgment qualifies narrow perceptual claims but is not a universal ground truth or a gate for every physical observable.
- Full print-and-recapture experiments are optional unless simpler source and born-digital controls expose a material unresolved bias.
- The broader method library is retained, but optional modules cannot delay or rescue the initial study.
- The program may yield multiple studies, but no fixed paper count is required.

### Not accepted as stated

- Artist classification is not proof of style, but remains useful evidence of group signal after nuisance and construct checks.
- Non-Western evaluation is redesigned rather than removed.
- The provisional project name is retained; “latent” refers to the learned-representation lineage, not every handcrafted observable.

The governing rule is to narrow the study when a measurement fails, not add metrics, prompts, artists, or evaluators after seeing final rankings.
