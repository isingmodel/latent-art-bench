# pilot_0 report

This artifact is an API-integration development report, not a benchmark scorecard.
The configuration disables scientific claims and restricts generation to `gpt-image-1` and `gpt-image-2`.

## Frozen design

Common corpus view: `landscape_and_outdoor_place_scene`.

| Target artist | Frozen neighbor |
|---|---|
| Claude Monet | Alfred Sisley |
| Alfred Sisley | Claude Monet |
| Camille Pissarro | Paul Cezanne |
| Paul Cezanne | Camille Pissarro |

## Qualification

| Measurement | Status | Real works | Reproduction pairs |
|---|---|---:|---:|
| `chromatic` | `fail` | 108 | 11 |
| `learned_formal` | `fail` | 0 | 0 |

`chromatic` evidence:
- stability exceeded the frozen margin
- All transformations were fitted on one primary reproduction per real training work.
- Nearest-centroid checks are construct diagnostics, not artist-recognition claims.

`learned_formal` evidence:
- no independent real works were evaluated
- no same-work reproduction pairs were evaluated
- source behavior was not recovered
- stability exceeded the frozen margin
- held-out artist signal was not valid
- source confounding was not controlled
- The frozen upstream extractor is not runnable as released.
- The source repository has no reusable code license at the audited revision.
- The exact checkpoint bytes and an author-supplied reference vector are unavailable.
- The roadmap forbids substituting a different learned evaluator after corpus inspection.

Scientific-generation gate: `closed`.

## Generation accounting

- `gpt-image-1`: succeeded=5
- `gpt-image-2`: succeeded=5
- Calls using the explicit unqualified test bypass: 10

## Scientific pilot analysis

No target-gap or specificity result was computed because the qualification gate is closed. The API-test images are excluded from scientific analysis.

## Decision

Stop before scientific generation. Redesign the failed measurement contracts before gathering any additional benchmark outputs.
