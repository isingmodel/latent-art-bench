# Development-pilot implementation status

This status follows the stopping rules in `ROADMAP.md`. “Implemented” means executable code and synthetic or adapter tests exist; it does not mean a real-data scientific gate has passed.

| Work package | Engineering status | Scientific gate status |
|---|---|---|
| WP0: pilot contract | Implemented as `configs/pilot_0/pilot.yaml`, schema-validated manifests, exact chromatic definition, audit templates, and a frozen learned-source revision | Partial: artist roster, common genre, and real-only thresholds remain pending; learned checkpoint reproduction is unresolved |
| WP1: reproducible substrate | Implemented: locked `uv` environment, CLI, strict records, input/config/code hashes, dirty-tree flag, deterministic synthetic dry run, leakage guards, and real-only fit enforcement | Passed on synthetic fixtures, not a measurement qualification |
| WP2: real corpus | Audit and manifest templates implemented | Not run; no artwork corpus was supplied or fabricated |
| WP3: preprocessing | Deterministic EXIF, ICC-to-sRGB, alpha, aspect-preserving Lanczos downsampling, lossless content-addressed output, and provenance implemented | Real reproduction and perturbation checks pending |
| WP4: measurements | Lee et al. adjacent-pixel Delta E 1976 distribution and seamlessness implemented with source-behavior tests | Chromatic real-art replication pending; learned A-vector blocked by the documented feasibility findings |
| WP5: real-only qualification | Evidence schema, identity-locked cards, evidence-file hashing, source-confounding fields, and gate enforcement implemented | Closed: both committed cards are `pending` |
| WP6: generation freeze | Test-only adapter implemented with exact two-model allowlist, loopback restriction, retries/refusals, output hashes, actual dimensions, dry run, and bypass audit | Scientific generation remains closed; the adapter is an explicit engineering exception |
| WP7: analysis/reporting | Energy distance, deterministic equal-sample subsampling, real-only neighbor selection, calibrated target gap, specificity interval, call accounting, and decision reporting implemented | No pilot estimate is produced because WP5 is closed |

## Verified commands

The implementation passed:

- 34 unit and integration tests on Python 3.13;
- the same 34 tests in an isolated Python 3.9 environment;
- Ruff checks, dependency-lock validation, and whitespace/diff checks;
- a five-image deterministic synthetic run;
- a two-call dry-run containing only `gpt-image-1` and `gpt-image-2`;
- one live, neutral, explicitly bypassed API smoke call per allowed model through the local OAuth proxy.

The live calls succeeded without retry. Both requested `1024x1024` and returned valid `1329x1183` PNG files, demonstrating why requested and actual dimensions are separate fields. See [`reports/pilot_0/API_SMOKE.md`](../reports/pilot_0/API_SMOKE.md).

## Required next evidence

The next scientific action is not more generation. It is to complete the candidate-artist/source audit, ingest rights-reviewed real reproductions, resolve or formally fail the learned-formal checkpoint reproduction, run the real-only qualification protocol, and update the two qualification cards from hashed evidence artifacts. If either measurement fails, the roadmap requires a feasibility report and stop/redesign decision rather than bypassing the gate.
