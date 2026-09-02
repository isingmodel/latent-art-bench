# LatentArtBench

LatentArtBench is a research project for testing whether images generated with a painter's name
reproduce the measurable visual-feature distribution of that painter's authentic paintings. The
active study compares distributions under a common outdoor-place content frame; it does not treat
painter classification, centroid similarity, or one learned embedding as the answer.

> **Status — 2026-09-02:** [Painter Feature Generation v1 Protocol 2.0](studies/painter_feature_generation_v1/PROTOCOL.md)
> is the only active plan. The source frame is being rebuilt and no real work is admitted, no active
> image is downloaded, no generation is registered, and no generated-versus-real result exists.
> See [current status](docs/STATUS.md).

## Research design

The question is:

> When one frozen generative model is prompted with Monet, Sisley, Pissarro, or Cézanne, do its
> outputs reproduce that painter's real distribution of color, spatial/orientation, and digital
> texture organization under the same broad landscape subject matter?

The design uses:

- one physical painting as the real-data unit;
- authority-verified oil-on-canvas outdoor-place works with lawful, technically adequate images;
- at least three broad scene groups supported by all four painters, equally weighted;
- a deterministic 20% development / 20% qualification / 60% confirmation assignment within
  painter × scene × workflow, with previously exposed works restricted to development;
- four painter-name conditions plus a matched artist-free control;
- paired seeds, no rerolling, and complete attempt accounting;
- absolute distributional equivalence, all-neighbour specificity, control improvement, coverage,
  availability/adherence, and near-copy exclusion as separate required gates; and
- learned features such as Kim A/C, CSD, CLIP, FID/KID, and classifier accuracy as diagnostics only.

The previous 360-work-per-painter quota is retired. It had no literature or power basis and was
not supported by the current evidence. The new corpus is an exhaustive physical-work union with
actual unequal painter counts. “Enough data” is a
conjunction of common scene support, equal-scene ESS, work/source/capture influence, and registered
whole-decision simulation—not a target-count stopping rule.

## Current data evidence

| Evidence layer | Current result | What it does not mean |
|---|---:|---|
| material-constrained Wikidata seed | 3,190 item candidates / 3,364 Commons filenames | not authority-verified works |
| fixed-seed Commons audit | 3,367 rows; 2,029 metadata-qualified rows / 1,967 distinct item IDs | complete fixed-seed follow-up, not authority-verified works or full R0 |
| broad no-`P186` Wikidata census | 3,722 rows / 3,543 distinct item IDs / 3,718 filenames | complete discovery route, not authority or rights verification |
| broad-media follow-up R1 | 1 / 182 requests, terminal on HTTP 200 + `Retry-After: 5`; no manifest | terminal protocol evidence, not a completed media screen |
| separate direct official-source audit | 43 all-content candidates | not a reproducible complete source frame |
| active admitted/downloaded/confirmation/generated/result counts | all 0 | metadata discovery succeeded; acquisition and analysis remain gated |

The fixed-seed audit and broader discovery census are complete. The first broad-media follow-up
closed terminally without a partial result; it may not be retried or spliced. The next steps are a
separately reviewed retry design plus the remaining named source routes and authority/rights/work-
identity reconciliation. Image acquisition, blind coding, and confirmation remain later gates.

## Study disposition

| Study | Disposition | Canonical record |
|---|---|---|
| Painter Feature Generation v1 | active generated-versus-real study; Protocol 2.0; corpus NO-GO | [protocol](studies/painter_feature_generation_v1/PROTOCOL.md) |
| Painter Features v1 | historical real-only measurement precursor; frozen evidence | [overview](studies/painter_features_v1/README.md) |
| Pilot 3 | historical; Met R2 closed on terminal HTTP 403 | [status](docs/STATUS.md) |
| Pilot 2 | historical; requested grids incomplete, primary tests not run | [report](reports/pilot_2/REPORT.md) |
| Pilots 0–1 | historical qualification/engineering attempts | [documentation index](docs/INDEX.md) |

Historical protocols, ledgers, and hash-bound evidence retain their literal paths. They are not
alternative current plans and must not be rewritten merely to agree with the reboot.

## Start here

1. [Current status and boundary](docs/STATUS.md)
2. [Canonical Protocol 2.0](studies/painter_feature_generation_v1/PROTOCOL.md)
3. [Detailed Korean research and data report](reports/painter_feature_generation_v1/RESEARCH_PLAN_AND_DATA_REPORT_KO.md)
4. [Generated-versus-real literature review](literature_reviews/reviews/06_generated_vs_real_painter_fidelity.md)
5. [Literature package](literature_reviews/README.md)
6. [Documentation index](docs/INDEX.md)
7. [Artifact retention policy](docs/ARTIFACTS.md)

## Development setup

The project requires Python 3.9 or newer and `uv`.

```bash
uv sync --locked --extra dev --extra learned
uv run --locked ruff check .
uv run --locked pytest -q -m "not live"
```

The standard test command is offline. A registered `live` test or data request is not research
authorization; each active collection stage additionally requires its reviewed protocol freeze.

The historical `pilot2 verify` and `pilot3 verify` commands deliberately check older hash-bound
closures and are not general repository health checks.

## Repository map

| Path | Role |
|---|---|
| `studies/painter_feature_generation_v1/` | sole active research protocol |
| `literature_reviews/` | audited bibliography, searches, paper reviews, and method decisions |
| `reports/painter_feature_generation_v1/` | current Korean report and compact evidence |
| `configs/painter_feature_generation_v1/` | prospective collection contracts |
| `data/manifests/painter_feature_generation_v1/` | compact tracked request/candidate manifests |
| `research_workspace/painter_feature_generation_v1/` | ignored active raw responses and future image bytes |
| `src/latent_art_bench/` and `tests/` | shared measurement/collection tools and offline verification |
| `docs/` | mutable status/index plus fixed-path historical records |
| `artifacts/`, `outputs/` | mixed historical receipts and ignored research bytes |

Git intentionally excludes artwork, generated full-resolution images, model weights, feature arrays,
and some raw responses. Ignored research bytes may be unique evidence. Never use `git clean -xfd` or
broad recursive deletion under `artifacts/`, `data/`, or `outputs/`; follow the
[retention policy](docs/ARTIFACTS.md).

## Research boundary

External reference access, image acquisition, feature extraction, prompt/model freeze, generation,
and confirmation open only through the stages in Protocol 2.0. A failed source cannot be silently
replaced; a failed result cannot be rescued by changing the painter, feature, margin, prompt, or
denominator after protected data are seen.

## License

Code and documentation are released under the [MIT License](LICENSE). Artwork, model weights,
generated outputs, museum metadata, and third-party sources retain their own rights.
