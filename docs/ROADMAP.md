# Development roadmap after the pilot_1 failure

## Final pilot_1 disposition

`pilot_1` is complete as an engineering exercise and failed as a scientific pilot. Both
real-only measurement cards are `fail`, the scientific gate is closed, and
`scientific_claims_enabled` is false. Neither card has a supported scientific scope.

| Measurement | Final status | Decisive failures |
|---|---|---|
| Chromatic | `fail` | Lee full-distribution behavior not recovered on eligible inputs; 0/108 primaries border-clear; Q85 and same-work interval bounds exceeded their margins; not every held-source fold passed |
| Learned formal | `fail` | PCA retained `0.6152142296` rather than `0.95`; same-work interval upper bound `1.1001825090` exceeded `1.0`; all 108 inputs met the released source's strict area rule but only 107/108 met its aspect rule; artist-by-source coverage was incomplete |

A separate engineering traversal was completed to prove that the implementation and
provenance paths work. It requested only `gpt-image-1` and `gpt-image-2` through
`~/dev/openai-oauth`, retained 41 attempts for 40 resolved cells, and recorded 0 of 40
exact `1024x1024` response-size matches. The local service routed to the ChatGPT Codex
backend rather than the public `api.openai.com` Images API. Its records prove the
requested labels and returned files, but not the executed backend model identity.

The final analysis contains 16 named-artist cells and 64 matched artist-free pairs. It
exists only because generated-feature preparation and analysis used explicit test-only
bypasses. All 16 specificity reference-resampling ranges include zero. The ranges omit
generator and prompt-cluster uncertainty and are not inferential confidence intervals.

Authoritative results: [final report](../reports/pilot_1/REPORT.md),
[evidence anchor](../reports/pilot_1/EVIDENCE.md), and
[failure investigation](FAILURE_INVESTIGATION.md).

The clean-checkout record is intentionally compact. Raw real and generated media,
model/source checkouts, derived views, and high-dimensional vectors remain ignored local
artifacts. Their hashes and provenance are anchored, but only the committed report and
evidence snapshots are present for direct byte verification in a clean checkout.

## Target selection: artists, not eras

The research target remains the artist. Era and movement are retained as metadata,
stratification variables, and possible future cross-classified covariates; they are not
substitutes for the target label. “Impressionism,” for example, spans heterogeneous
artists, phases, media, and institutions, so using it as the target would erase the
artist-versus-neighbor estimand rather than strengthen it.

The candidate decision remains the one established by the previous museum-source and
common-genre research:

- Claude Monet paired with Alfred Sisley;
- Camille Pissarro paired with Paul Cezanne;
- landscape/outdoor-place scenes as the common content domain;
- 108 canonical works, 119 reproductions, 76 training works, and 32 held-out works.

These artists were selected from metadata, source overlap, rights, and genre support,
not from generated outputs or favorable measurement results. A future larger roster
must be selected prospectively by the same principle.

## Completed work packages

| Package | Engineering result | Scientific result |
|---|---|---|
| WP0: contract | versioned configs, schemas, prompts, split, and analysis rules | development estimand frozen |
| WP1: substrate | locked environment, CLI, provenance, leakage guards, and tests | reproducible implementation |
| WP2: real corpus | AIC, CMA, Met, and NGA acquisition/audit; 108 works | artist-by-source graph proved inadequate for clean inference |
| WP3: preprocessing | content-addressed deterministic views | source domains and codec crossing remain inadequate |
| WP4: measurements | Lee scalar path and Kim A-vector path implemented | paper-level chromatic behavior and final learned gate not qualified |
| WP5: qualification | durable evidence and cards | both `fail`; scientific gate closed |
| WP6-WP7: generation and reporting | attested engineering grid, features, cells, analysis, report | no scientific model comparison |

Failure is the output of the completed pilot, not unfinished work. Blindly adding retries
cannot repair missing source-behavior tests, input ineligibility, an unattained PCA
target, absent artist-by-source cells, a codec confound, unverified executed-model
identity, or a systematic requested-size mismatch.

## Locked final-artifact sequence

The exact finalization sequence for the existing generation ledger is in the
[README](../README.md#development-pilot-commands). Its order is part of the contract:

1. verify every pinned VAE tensor against the recovered full checkpoint;
2. rerun the final chromatic and learned-formal evaluations;
3. write both failed qualification cards;
4. attest all generation attempts and output bytes against the current cards;
5. prepare generated features with `--allow-unqualified-test-preparation`;
6. build the exact two-measurement analysis grid;
7. analyze it with `--allow-unqualified-test-analysis`;
8. render the report and content-addressed evidence anchor.

The bypasses apply to generated-feature preparation and analysis, and their status is
carried into every downstream record. They do not turn failed qualification into a pass.

## Prospective pilot_2 roadmap

`pilot_2` must be a new protocol on new or sealed evidence. It must not reuse the
`pilot_1` label, relax a threshold after seeing a result, or retry until an interval
crosses a desired boundary.

### R1. Preregister immutable scientific boundaries

Before examining held-out features or generated outputs, commit and hash:

- hypotheses, estimands, margins, confidence level, multiplicity policy, and stopping
  rules;
- artist, source, genre, medium, phase, aspect, resolution, border, damage, crop, and
  rights eligibility rules;
- feature versions, checkpoint and source revisions, environment fingerprint,
  preprocessing, RNG policy, and schemas;
- PCA selection rule and permitted maximum dimension;
- prompts, artist-free controls, requested model labels, repetitions, and output policy;
- transport-conformance tests and the complete analysis implementation;
- a simulation-based sample-size decision.

Any estimand-changing alteration after unsealing creates a new pilot version.

**Exit:** an immutable protocol can be reviewed without access to held-out results.

### R2. Build a balanced artist-by-source corpus

Construct the artist-by-source table before feature extraction. Every retained source
must contain every artist in both training and held-out partitions, with equal planned
counts or prospectively fixed weights. Deduplicate at the physical-work level and keep
all captures of a work in one split outside the reproduction study.

If the four artists cannot populate a common source intersection, add sources or narrow
the source roster before unsealing. Never average over structurally absent cells.

**Exit:** every held-source fold and its training complement contains all target artists.

### R3. Enforce the source-paper input domains

Two reviewers must independently record frame, mat, caption, partial-image, damage,
painting/non-painting, crop, native dimensions, format, profile, and acquisition lineage,
with adjudication before inclusion. Unknown border or damage status is ineligible for the
Lee primary analysis.

For the Kim track, require aspect ratio `< 2` before square resizing. Record both the
paper's low-resolution description and the released source's area rule, and use their
prospectively selected intersection for the primary source-compatible domain.

**Exit:** every primary input has complete review fields and passes its paper-specific
eligibility contract.

### R4. Recover Lee et al.'s defining behavior

Preregister a distance between full mean-rescaled adjacent-pixel chromatic-distance
distributions over a fixed, paper-compatible resolution grid. Use eligible real images,
fixed antialiasing, and no upsampling. Keep scalar seamlessness formula probes as a
separate necessary unit test.

Report aggregate, per-artist, and per-source results. Every required held-source fold
must satisfy the frozen criterion; pooled performance cannot mask a failed fold.

**Exit:** both the scalar formula and the held-out full-distribution collapse rule pass.

### R5. Qualify the A-vector without origin-codec confounding

Use the pinned verified VAE and exact environment fingerprint. Keep the honest claim:
the deterministic posterior policy is a repaired, source-compatible A-vector, not the
authors' unpublished RNG realization.

Cross preprocessing codec with origin:

- primary: both real and generated decoded RGB use one pinned lossless intermediate;
- sensitivity: both origins use the same pinned JPEG library, quality, and subsampling;
- source replication: original-extension behavior is reported separately.

Fit centering and PCA only on real training primaries. Allow enough prospectively capped
components to reach the frozen 95% target, hash the selected basis before transformation,
and refit inside each source-held-out fold. Failure to reach 95% closes the gate.

**Exit:** eligibility, codec balance, determinism, PCA retention, reproduction stability,
and artist-by-source control all pass their frozen rules.

### R6. Expand independent reproduction calibration

Acquire independent digitizations with documented capture ancestry rather than multiple
derivatives of a museum master. Balance physical works across artist and source. Use the
physical work as the top-level bootstrap unit and determine the pair count by simulation
for the desired upper-bound precision.

**Exit:** the planned sample is complete and evaluated once; stopping does not depend on
whether the margin passes.

### R7. Require transport conformance before model claims

Before any scientific image generation, require a transport that preserves an
authoritative executed-model identifier, upstream request/response identity, exact wire
request body, and output dimensions. Validate the requested-size contract on a frozen
conformance set. A local compatibility catalog or forwarded request string is not proof
of the executed model.

If only the current OAuth facade is available, restrict the work to engineering tests
and make no comparison between requested labels.

**Exit:** model identity and request contract are independently verifiable for every
scientific call.

### R8. Freeze, generate, analyze, and report once

Only after both measurements and transport conformance pass, freeze the full artist,
content, control, model, and repetition grid. Use enough generated samples to model
generator and prompt-cluster variability. Analyze the complete frozen grid without
visual selection or selective cell omission.

Report target gap, specificity, controls, uncertainty at every sampling level, failures,
and sensitivity analyses. Do not infer an artist or model ordering when intervals overlap
the null or when any required measurement gate fails.

**Exit:** produce a new content-addressed report and select exactly one decision: go,
narrow, redesign, or stop.

## Explicitly outside pilot_2's core

Movement-level inference, broad era classification, prototype contraction, contextual
evaluator matrices, aggregate scores, leaderboards, human aesthetic rankings, exposure
causality, image conditioning, and public submission infrastructure remain separate
studies. None may be added post hoc to rescue a failed core measurement.
