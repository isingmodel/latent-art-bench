# Painter responsiveness: implementation and continuation

This study tests whether a painter name attenuates a requested color change, and
whether that attenuation prevents reaching supported properties of original works.
Read the [protocol](PROTOCOL.md), [human codebook](HUMAN_CODEBOOK.md) and
[capture feasibility record](CAPTURE_FEASIBILITY.md). None of these documents is
an empirical demonstration of the proposed mechanism.

## Reproduce the completed diagnostic stage

From the repository root, using the retained local numeric evidence:

```bash
uv run --locked python -m latent_art_bench.painter_responsiveness_v1 check
```

The command recomputes the equal-brief diagnostics, shared-control power
simulation and all report tables/figures; it compares results and report bytes.
It makes no provider calls or new scientific feature measurements. The defaults
refer to `prv1-diagnostic-20260908`. The [published report](../../reports/painter_responsiveness_v1/prv1-diagnostic-20260908/REPORT.md)
contains the numerical results. Historical evidence integrity has a separate
`latent-art-bench verify-evidence` command; that historical audit does not itself
recompute or register this new study.

Source organization follows the scientific stages: `analysis.py` owns retained-data
diagnostics, `report.py` renders saved results, `design.py` generates the fixed
192-slot order, and `inference.py` owns factorial inference and precision simulation.
`workflow.py` publishes and replays D0. `preflight.py` is GET-only. `human.py`,
`human_package.py` and `reference_validation.py` prepare, bind and validate actual
human tasks. `generation_prepare.py`, `collection.py` and `measurement.py` implement
the gated prospective experiment, bounded collection and all-slot measurement.
Tests use synthetic data and mock transports; passing tests are not study results.

## Human reference validation

The local H0 preview is under
`research_workspace/painter_responsiveness_v1/prv1-diagnostic-20260908/human_reference_preview/index.html`.
Its exports are explicitly technical previews and cannot count as human validation.
The 70 displays preserve aspect ratio and use opaque filenames. Color is not
calibrated across participants' screens. No invitations are sent automatically.

An actual responsible human supplies a private JSON plan with these fields:
`responsible_human`, `recruitment`, `institutional_requirements`, `storage`,
`consent_text`, `phase`, `assignments` and `rater_roles`. `phase` is either
`usability_pilot` or `validation`; the two phases have separate retained paths.
Assignments map pseudonymous rater IDs to task-ID lists from the H0 freeze.
Roles map those same IDs to `independent` or `maintainer`. At least two independent
human raters must complete both annotation and vividness tasks for each reference
before reference qualification can pass. An initial maintainer pilot cannot
satisfy that requirement. Use the codebook to determine task scope and consent.
Do not commit names, contact details or free-text responses.

```bash
uv run --locked python -m latent_art_bench.painter_responsiveness_v1 human-session --plan <private-plan.json>
# Commit the session receipt before importing actual responses.
uv run --locked python -m latent_art_bench.painter_responsiveness_v1 import-ratings --phase validation --submissions <actual-export-1.json> <actual-export-2.json>
```

Imports are terminal snapshots; resolve incomplete submissions before importing.
Missing/disputed annotations stay visible. The summary establishes only candidate
empirical reference spans. It cannot establish a meaningful margin automatically.

## Prospective collection, after qualification

An externally authored, deidentified human decision must bind
`reference_validation_sha256` and `package_id`; declare `author_kind` as
`responsible_human`, `actual_human_decision` as true, and a pseudonymous
`responsible_human_id`; record `target_work_ids`, `margin_rationale`,
`capture_limitations`, and `decision`. These fields record actual human work;
they must never be filled by an agent to manufacture qualification.

The decision specifies positive `meaningful_margin_primary_iqr`,
`maximum_p90_halfwidth_primary_iqr`, and `minimum_endpoint_power` (at most one).
All three noise scenarios must satisfy the chosen criteria, using lower Monte
Carlo power bounds conditional on both painter interactions equaling the negative
margin. Partial-null results are reported separately; the gate does not guarantee
the same power when only one painter changes. `generated_image_assessment` records feasible status,
recruitment, a consent/storage plan, at least two independent raters and capacity
to assign all 192 outputs. Inspect `generation_prepare.qualify` for the exact
field contract. Precision can reject the design even after human validation.

The H0 freeze, preview receipt, session receipt and response receipt have explicit
commit/hash checks. Keep raw plans and exported responses under the ignored
workspace; commit only their compact deidentified scientific receipts.

The GET-only provider/budget preflight must be within 24 hours of preparation and
collection. A stale closed preflight requires a successor diagnostic/preflight
run; it is never overwritten. No automatic provider fallback is allowed.

```bash
# New diagnostic runs require committed source, then prepare, commit the freeze, build.
uv run --locked python -m latent_art_bench.painter_responsiveness_v1 preflight --live --run-id <qualified-diagnostic-id>
# Commit the deidentified decision and scientific qualification receipts first.
uv run --locked python -m latent_art_bench.painter_responsiveness_v1 generation-prepare --run-id <new-generation-id> --diagnostic-run-id <qualified-diagnostic-id> --decision <deidentified-decision.json>
# Commit generation_freeze.json and planned_requests.jsonl before any POST.
uv run --locked python -m latent_art_bench.painter_responsiveness_v1 collect --live --run-id <new-generation-id>
uv run --locked python -m latent_art_bench.painter_responsiveness_v1 measure --run-id <new-generation-id>
```

The namespace caps new spending at $20 within the existing $75 overall ceiling;
current credit and per-request reservations can impose a smaller limit. Starts
are spaced by at least five seconds, with at most two requests in flight. Only
qualifying technical failures receive one identical-payload retry, six retries
maximum. Every planned slot and attempt remains in the analysis. Any missing
primary measurement withholds primary inference. A stopped/interrupted run cannot
resume or silently refill missing slots; a successor needs new paths and evidence.

The CLI human workflow currently prepares and imports reference judgments.
`human.make_tasks` also supports generated-image vividness, adherence and painter
resemblance instruments, but collection-bound generated displays/sessions and their
interpretation remain a subsequent stage. The prospective measurement publisher
is create-once with integrity receipts; it does not yet expose a numeric replay
command. D0 does expose full numerical and report-byte replay. These implementation
limits must not be mistaken for completed human or causal validation.

The existing paper continues to describe the completed earlier study. Upgrade its
claims only after genuine results from the prospective and human stages exist.

## Implementation review

Three maintainer-run LLM subagents reviewed the numerical method, collection and
human-evidence handling; these were not institutionally independent reviews.
Revisions included exact H0/session/response hash verification, disjoint human
pilot and validation paths, rejection of existing report directories, fresh key
and credit evidence, recomputation of precision qualification, and separating the
interaction margin from the manipulation check. Collector tests exercise actual
thread overlap with mock transport, technical retries, unknown costs, interrupted
requests, time spacing and preserved missing slots. Measurement tests use synthetic
retained responses and mocked extraction; no test results stand in for real images
or actual human judgments. Current verification counts belong in
[STATUS.md](../../docs/STATUS.md), not in this prospective protocol bundle.
