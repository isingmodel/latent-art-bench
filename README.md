# LatentArtBench

> **Current implementation — 2026-09-05:**
> [Painter Feature Generation v2](studies/painter_feature_generation_v2/PROTOCOL.md) continues the
> study toward a comparative analysis. The immediate deliverable is the
> [available-image-model analysis report](reports/painter_feature_generation_v2/AVAILABLE_IMAGE_MODELS.md),
> not a prototype paper. Its 1,193-record frame has
> prospective roles (658 confirmation records); the 31-feature measurement and paired-block
> analysis code is implemented. SD-Turbo generation is running. Both GPT Image aliases return
> image bytes through the current Codex OAuth proxy, but returned settings differ from requests
> and model snapshots are not attested. Full painter-feature results remain pending. Use
> [current status](docs/STATUS.md) for operational guidance. The v1 overview below is historical.

Run the new pipeline with
`uv run --locked --extra analysis --extra learned latent-art-bench paper-study --help`.

Inspect the bounded GPT Image access tool with `latent-art-bench model-assessment --help`.
Completed experiments are immutable; do not rerun them in place.

LatentArtBench is a research project for testing whether images generated with a painter's name
reproduce the measurable visual-feature distribution of that painter's authentic paintings. The
active study compares distributions within a metadata-declared outdoor-place content frame; it
does not treat painter classification, centroid similarity, or one learned embedding as the answer.

> **Historical pre-determination overview (superseded):** [Painter Feature Generation v1 Protocol 2.1](studies/painter_feature_generation_v1/PROTOCOL_2.1.md)
> is the only active plan. It removes every human coding step from Protocol 2.0, whose text stays
> frozen at `PROTOCOL.md` as the authority for the censuses run under it. No real work is admitted,
> no active image is downloaded, no generation is registered, and no generated-versus-real result
> exists. A non-binding
> [corpus pre-screen](reports/painter_feature_generation_v1/SCENE_SUPPORT_PRESCREEN_KO.md) shows
> all four painters clear the 2.1 floor at the metadata upper bound, with Sisley the binding risk.
> See [current status](docs/STATUS.md).

## Research design

The question is:

> When one frozen generative model is prompted with Monet, Sisley, Pissarro, or Cézanne, do its
> outputs reproduce that painter's real distribution of color, spatial/orientation, and digital
> texture organization within the same outdoor-place subject domain?

The design uses:

- one physical painting as the real-data unit;
- authority-verified oil-on-canvas works whose metadata declares an outdoor place under a frozen
  lexicon, with lawful, technically adequate images and no human coding;
- uniform work weights within the outdoor-place domain and actual unequal painter counts;
- a deterministic 20% development / 20% qualification / 60% confirmation assignment within
  painter × workflow, with previously exposed works restricted to development;
- all 16 prompt templates under four painter-name conditions plus a matched artist-free control;
- paired seeds, no rerolling, and complete attempt accounting;
- absolute distributional equivalence, all-neighbour specificity, control improvement, coverage,
  availability, and near-copy exclusion as separate required gates, with prompt adherence as an
  automated diagnostic; and
- learned features such as Kim A/C, CSD, CLIP, FID/KID, and classifier accuracy as diagnostics only.

The previous 360-work-per-painter quota is retired. It had no literature or power basis and was
not supported by the current evidence. The corpus is an exhaustive physical-work union with
actual unequal painter counts. “Enough data” is a conjunction of at least 100 confirmation works
per painter, work/source/capture influence gates, the auxiliary capture panel, and registered
whole-decision simulation—not a target-count stopping rule.

## Current data evidence

| Evidence layer | Current result | What it does not mean |
|---|---:|---|
| material-constrained Wikidata seed | 3,190 item candidates / 3,364 Commons filenames | not authority-verified works |
| fixed-seed Commons audit | 3,367 rows; 2,029 metadata-qualified rows / 1,967 distinct item IDs | complete fixed-seed follow-up, not authority-verified works or full R0 |
| broad no-`P186` Wikidata census | 3,722 rows / 3,543 distinct item IDs / 3,718 filenames | complete discovery route, not authority or rights verification |
| broad-media follow-up R1 | 1 / 182 requests, terminal on a plural `errors:[maxlag]` HTTP 200 envelope; no manifest | terminal protocol evidence, not a completed media screen |
| broad-media follow-up R2 | 182 / 182 requests; 3,722 rows / 2,029 metadata-qualified rows | complete metadata screen, not authority verification or image acquisition |
| AIC route R1 | 1 / 4 requests, terminal on a string `classification_id`; no manifest | terminal protocol evidence, not a completed source route |
| AIC route R2 | 4 / 4 requests; 153 rows / 57 screened candidates | complete AIC route census, not authority verification or image acquisition |
| separate direct official-source audit | 43 all-content candidates | not a reproducible complete source frame |
| historical pixel-exposure denylist | 122 physical works, development-only | rebuilt from pinned git history; not yet frozen for M0 |
| corpus pre-screen (non-binding) | 2.1 floor 179 per painter; lexicon upper bounds Monet 529 / Sisley 193 / Pissarro 256 / Cézanne 200 | a metadata upper bound, not a protocol count; admits or excludes nothing |
| active admitted/downloaded/confirmation/generated/result counts | all 0 | metadata discovery succeeded; acquisition and analysis remain gated |

The fixed-seed audit, broader discovery census, separately reviewed broad-media R2 follow-up, and
the Art Institute of Chicago route are complete. Each R1 remains frozen terminal evidence and was
neither retried nor spliced: every R2 used a new census ID, disjoint paths, and its own complete
request frame. The next steps are the remaining named source routes — Europeana, NGA, Cleveland,
Yale, Getty, Minneapolis, Paris Musées, and POP/Joconde — and authority/rights/work-identity
reconciliation across their union. Image acquisition, blind coding, and confirmation remain later
gates.

## Study disposition

Painter Feature Generation v1 is the only study in this repository. Its canonical record is
[Protocol 2.1](studies/painter_feature_generation_v1/PROTOCOL_2.1.md); Protocol 2.0 stays frozen
at `PROTOCOL.md`. The corpus disposition is NO-GO past R0. Earlier exploratory attempts were
removed rather than carried as inactive namespaces.

The active study's own hash-bound evidence — freezes, reviews, authorizations, append-only request
ledgers, and published manifests — retains its literal paths and must not be rewritten, reordered,
truncated, moved, or regenerated for cosmetic cleanup.

## Start here

1. [Current status and boundary](docs/STATUS.md)
2. [Canonical Protocol 2.1](studies/painter_feature_generation_v1/PROTOCOL_2.1.md)
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
uv run --locked latent-art-bench verify-evidence
```

The standard test command is offline. The evidence audit verifies every freeze at the git commit
that recorded it, plus every hash-chained ledger and execution receipt; it never refreshes a hash. A registered `live` test or data request is not research
authorization; each active collection stage additionally requires its reviewed protocol freeze.

The `latent-art-bench` console script exposes the seven terminal collectors, the Cleveland route
on the shared engine, the evidence audit (`verify-evidence`), and the R0 artifact tools
(`prompt-library`, `content-lexicon`, `exposure-denylist`, `scene-prescreen`) as pass-through
subcommands. Preparing a census is not authorization to execute one.

## Repository map

| Path | Role |
|---|---|
| `studies/painter_feature_generation_v1/` | sole active research protocol |
| `literature_reviews/` | audited bibliography, searches, paper reviews, and method decisions |
| `reports/painter_feature_generation_v1/` | current Korean reports, the scene pre-screen, and compact evidence |
| `configs/painter_feature_generation_v1/` | prospective collection contracts |
| `data/manifests/painter_feature_generation_v1/` | compact tracked request/candidate manifests |
| `research_workspace/painter_feature_generation_v1/` | ignored active raw responses and future image bytes |
| `src/latent_art_bench/` and `tests/` | the census collectors, the shared census engine, the evidence audit, the R0 artifact tools, and offline verification |
| `docs/` | mutable status, index, architecture, and retention policy |
| `artifacts/` | ignored local research bytes retained outside git |

Git intentionally excludes artwork, generated full-resolution images, model weights, feature arrays,
and some raw responses. Ignored research bytes may be unique evidence. Never use `git clean -xfd` or
broad recursive deletion under `artifacts/`, `data/`, or `research_workspace/`; follow the
[retention policy](docs/ARTIFACTS.md).

## Research boundary

External reference access, image acquisition, feature extraction, prompt/model freeze, generation,
and confirmation open only through the stages in Protocol 2.1. A failed source cannot be silently
replaced; a failed result cannot be rescued by changing the painter, feature, margin, prompt, or
denominator after protected data are seen.

## License

Code and documentation are released under the [MIT License](LICENSE). Artwork, model weights,
generated outputs, museum metadata, and third-party sources retain their own rights.
