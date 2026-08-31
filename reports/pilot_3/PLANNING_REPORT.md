# Pilot 3 planning and Freeze-A1 report

## Outcome

The final metadata-only redesign fixes four artists: Alfred Sisley, Camille Pissarro, Paul
Cezanne, and Pierre-Auguste Renoir. No Pilot 3 artwork bytes, external features, transport-
qualification request, or generated output have been opened. The applicable development,
external, and generation gates remain closed until their explicit prospective commits.

The finite roster and reciprocal Sisley--Renoir and Pissarro--Cezanne neighbor pairs were
chosen before fresh Pilot 3 pixels or feature outcomes. The design makes no feasibility claim
for the five earlier candidates that were not advanced.

## Real-corpus freeze

The real corpus contains 52 selected physical works. The manifest also retains 25
metadata-only candidates as `not_selected`; zero works are replacement-eligible reserves:

- 40 development works in a four-artist × two-source × five-work grid;
- 32 development-training works and eight development-calibration works from AIC and Met; and
- 12 sealed external works in three complete one-work-per-artist museum/provider blocks from
  Minneapolis Institute of Art, Dallas Museum of Art, and Toledo Museum of Art.

Every selected row binds an exact official museum image asset. Wikimedia Commons is not an
image-delivery source or fallback. After Freeze A1, no selected work or external block may be
replaced; a metadata, rights, acquisition, corruption, input-domain, or provenance failure
closes the affected Pilot 3 path and requires a new untouched protocol.

The source images are limited to internal noncommercial scholarly research and are not
redistributed. Institution/provider blocking does not assert that the four works in a block
share a camera, operator, capture date, calibration, or conservation-imaging session.

## External randomization and claim boundary

The external analysis preserves holding institution and official asset provider as blocks.
It permutes the four artist labels independently within each complete block, giving `4! = 24`
assignments per block and an exact exhaustive space of `24^3 = 13,824` assignments. A global
12-row shuffle or Monte Carlo substitute is not the frozen test.

Phase A freezes the harmonized Kim A-vector used by the project: exact pinned SD2 VAE weights,
content-derived posterior seeds, 16,384-dimensional vectors, development-training-only PCA to
95% variance subject to the rank cap, nearest frozen artist centroids, and target-versus-
neighbor distance margins. The external gate requires above-chance balanced accuracy, every
artist recall at least 0.20, a positive mean neighbor margin, and both one-sided exact tests to
pass Holm familywise alpha 0.05.

Any pass qualifies only A-vector proximity conditional on the exact frozen official museum
bytes and preprocessing contract. It does not establish same-camera/session behavior, cross-
digitization robustness, artist or style fidelity, or authorship.

## Generated-study resolution

The Phase-B design remains a budget-constrained estimation pilot rather than a power claim:

- four named artists and one shared artist-free control;
- 16 frozen outdoor-place content blocks;
- four nested repetitions;
- one primary analytic requested label, `gpt-image-2`; and
- exactly 320 primary analytic calls after every gate passes.

The transport recognizes only `gpt-image-1` and `gpt-image-2`, and every request must traverse
the pinned `/Users/fred/dev/openai-oauth` route. `gpt-image-1` is historical development
evidence, not a second prospective Pilot 3 analytic stratum. No direct-API, browser, dated-
snapshot, alternate-model, or silent fallback is permitted. The study makes no 80%-power or
authoritative executed-model claim.

## Next authorized step

After the complete Freeze-A1 closure is committed, only the 40 development artworks may be
acquired and extracted. The eight exact repeat probes and calibration gate must pass before a
separate Freeze-A2 commit can unseal the three external museum blocks in one receipt-bound
transaction. Transport qualification and the 320 analytic generation calls remain prohibited
until the external validation passes and Freeze B is committed.

## Reproduce and verify the offline bundle

```bash
uv run --locked latent-art-bench pilot3 plan --root .
uv run --locked latent-art-bench pilot3 verify --root .
```

The self-hashed planning index and evidence artifacts must be regenerated from the reconciled
configs, manifests, implementations, tests, source snapshots, and protocol; narrative edits do
not manually mutate their hashes.
