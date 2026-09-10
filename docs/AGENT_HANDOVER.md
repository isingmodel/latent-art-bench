# Agent handover — paper revision and fixed-map validation

Read [STATUS.md](STATUS.md), then [ARTIFACTS.md](ARTIFACTS.md), inspect
`git status --short --branch`, and follow [AGENTS.md](../AGENTS.md).
This document is mutable orientation; immutable scientific records stay at their
original paths. The canonical English manuscript is [paper/paper.tex](../paper/paper.tex).
The [paper guide](../paper/README.md) covers compilation and visual inspection;
[ANALYSES.md](ANALYSES.md) maps computation and plotting for each study.

## Active goal and current boundary

The user requests three skeptical LLM reviews using the DeerFlow academic-paper-
review skill, substantive paper/analysis revisions and a nine-score mean above 9.
The fixed aspects are rigor, contribution and clarity/reproducibility, each 1–10.
Round 1 averaged 8.2333; round 2 averaged 8.6889; round 3 averaged 8.9000.
The requested threshold remains unmet. All three round-3 reviewers inspected
the complete 35-page manuscript and nine figures; subsequent presentation fixes
do not constitute a new scored review. See the [review record](reviews/20260910_substantive_revision/REVIEW.md)
for exact snapshots and scores. Do not inflate scores or claim the goal achieved
before the honest mean exceeds the threshold. All reviewers are operated by the
maintainer and have disclosed subsequent design/implementation involvement.
They are not independent human or institutional reviewers.

The current local English draft is 37 pages and unpublished. The latest published
manuscript is the 36-page clause-release version; earlier assets remain immutable.
The active fixed-map collection uses paid FLUX, without human ratings or learned
features. Its precollection conservative accounting baseline is $50.7219185
against the $75 ceiling, including the historical $5 reserve. There is no final
new cost yet; consult the [live ledger](../data/manifests/painter_map_validation_v2/pmv2-20260910/generation_events.jsonl)
for new charges and pending reservations. Do not assign a monetary value to OAuth
subscription use.

| New scope | Source / qualification / freeze | State |
| --- | --- | --- |
| `painter_clause_validation_v1/pcvv1-20260910` | `dff2804` / `90a993f` / `79f28c1` | Permanently stopped: 211 images from 288 slots; one refusal, one unqualified server error, one cancellation before posting and 74 unattempted. Both primary comparisons and complete-grid secondary summaries are unavailable. |
| `painter_clause_successor_v1/pcsv1-20260910` | `07f8231` / `d5887f8` / `6effea1` | Complete: all 96 outputs in 45.5 minutes, no retries. Primary Cezanne−generic energy −1.195419353, raw p=.00001, rejects at .025; observed trace ratio .552327. All 288 measurement rows available. |

The successor decision was committed at `f0ab2d4` after the initial Cezanne
refusal, before the later stop and before feature extraction. Its allocation
and threshold remain unchanged after Monet became unavailable. No observations
are pooled and no further clause replacement is allowed. The HTTP 500 had a null
error code and is outside the unchanged numeric-code-match retry rule; never reclassify or retry it retrospectively.
The [terminal audit](reviews/20260910_substantive_revision/CLAUSE_TERMINAL_AUDIT_2.md)
records timing, accounting, response hashes and the inference restrictions.

Both clause collectors are one-shot. Do not invoke collect again, resume, refill,
change bound source or replace failed slots. At most two requests are active,
recorded starts are five seconds apart, and blocks drain before the next.
Both collections and one-shot measurements are complete. Do not invoke measure again.
The successor's three
pipelines and C/G energy/trace scope are fixed; it has no free arm, map/Q,
retrieval or secondary hypothesis tests. The stopped predecessor retains all
864 measurement-status rows and unavailable endpoints. Use each namespace's
`check` and `verify-responses` commands for verification; the latter checks
private retained response hashes.

## Active fixed-map collection

The [v1 planning qualification](../studies/painter_map_validation_v1/pmvqv1-20260910/PRECISION.md)
is terminal: all 81 proxy coverage checks passed, but R4/R6/R8 each failed the
baseline conditional-residual width gate. No allocation was selected or collected.
Its [public release](../reports/paper_map_reproducibility_v1/pmrv1-20260910/REPORT.md)
contains 18 files, with exact fresh local/anonymous replay of all 81 cells and
73 tests in each recorded environment. It preserves a failed planning decision,
not new image evidence. V1 remains stopped.

One separately declared [R10 redesign](../studies/painter_map_validation_v2/DECISION.md)
passed its single 27-cell qualification. The one-shot `pmv2-20260910` collection
is now active: twelve fixed new scenes, ten repeats and free/named FLUX/Cezanne
arms, for 240 outputs. Operational source `765c5f7`, qualification `aaf431a` and
freeze `c68c235` bind the exact source, reviewed protocols and assignments.
At most two attempts overlap, recorded starts are at least five seconds apart,
and each pair drains before the next. The fixed historical maps, primary512
31-feature pipeline, development scaler and references remain unchanged.

Do not invoke collection again, resume, refill, replace failed slots or change
bound source. Feature extraction must wait for terminal closure. A permanently unavailable
required slot stops the cohort; there is no replacement. Both points and all
component scores require the complete eligible 240-vector grid after terminal
measurement. Qualification does not establish actual service coverage or
independent stationary repeats. The [technical contract](../studies/painter_map_validation_v2/TECHNICAL_PROTOCOL.md)
fixes conditional budget forecasts, $5 liabilities, retry limits and stop/drain
rules; no top-up or reserve reduction is authorized. No new E/Q result exists yet.

The reviewed public adapter, `tools/paper_map_validation_release.py`, is committed
at `916f5c5`; its 29 synthetic tests passed in 155.56 seconds. The
[adapter audit](reviews/20260910_substantive_revision/MAP_VALIDATION_RELEASE_AUDIT_2.md)
records independent synthetic extraction, stdlib verification and observed-vector
replay. Actual terminal export, complete fresh 27-cell replay and public acceptance
remain pending. This is separate from the already public failed-v1 package.

## Completed scientific additions

The four-painter exploration remains in the paper: 649 references, 1,536 named
images and 384 artist-free controls. Study 1 separately uses 1,006 images,
38 Monet/32 Cezanne references and the unchanged 221-work development scaler.
Study 2 has one 192-image primary palette run; its 49-image predecessor remains
ancillary. Two late exploratory retries do not restore its original full-grid
inference. Never pool cohorts to change denominators or eligibility.

| Completed namespace / run | Source / freeze | Main contribution |
| --- | --- | --- |
| `painter_measurement_validation_v1/pmvv1-20260910` | `f3bc9b6` / `f2ab8de` | Ten reference-image challenges and common-square measurements for all Study 1 outputs. Processing sensitivities are characterized, not perceptual or independent-capture validity. |
| `painter_naming_replication_v1/pnrv1-20260910` | `88cd185` / `2de6bc4` | 72 FLUX naming and 192 OAuth palette outputs; both naming directions recur, both palette interactions remain unresolved in the separate four-test family. |
| `painter_naming_geometry_v1/pngv1-20260910` | `459c6a8` / `8facfa3` | Whole-scene moment-map evaluation, unchanged-map transfer to later FLUX, repeat-corrected variance and conditional-mean mismatch. |
| `painter_naming_centering_v1/pncv1-20260910` | `c390eef` / `45e3ce9` | Evaluation-centering isolates the fitted scalar at a common mean; reference energy worsens in all 60 original and 18 later views. |

Adding scale improves corrected prediction of named scene means in all six
primary cells while worsening reference proximity in five. Translation alone
beats actual naming in both later primary FLUX comparisons, with recorded
representation exceptions. These post-result diagnostic observations do not
identify an internal generative mechanism. The evaluation-centered map induces
repeat dependence, so do not apply the independent-repeat Q correction to it.
The failed prospective clause cohort supplies no new-scene map validation.

## Reproduction and public access

Use Python 3.13.11 with the lockfile. These commands do not generate images:

```sh
make four-painter-analysis
make analysis
make palette-check
make validation-check
make replication-check
make geometry-check
make clause-check
make clause-successor-check
make figures-check
make paper
```

Terminal clause checks require their measurement receipts. Original local
workflow checks can require the retained private response archive; public
adapters have explicitly narrower numerical contracts. Do not repeat extraction
merely to verify a manuscript edit.

Six figures come from `paper/make_figures.py`, one from `paper/replay_palette.py`,
one from `paper/make_validation_figure.py`, and the ninth uses
`paper/make_geometry_figure.py` to display unchanged sealed geometry values in
larger stacked panels. The original numerical renderer and figure remain
unchanged. The older geometry-sensitivity figure uses “generic”
for short-scene named prompts; the manuscript labels that contrast correctly
without overwriting frozen evidence. New clause findings use a compact table.

The [original numerical release](https://github.com/isingmodel/latent-art-bench/releases/tag/pprv1-20260910)
(source `b2884c3`, public commit `2592dfb`) has 98 local/anonymous exact checks
and 98 hosted Ubuntu checks under its documented floating-point contract.
The [geometry addendum](https://github.com/isingmodel/latent-art-bench/releases/tag/ppgv1-20260910)
(source `5485e36`, public commit `7923049`) has exact fresh local/anonymous replay
of both namespaces and 95 tests. Preserve both archives, paper assets and the
original release's explicit erratum. Their sealed packagers must not be edited.

`tools/paper_clause_release.py` is the separately reviewed adapter for both
clause cohorts. The [published addendum](../reports/paper_clause_reproducibility_v1/pcrv1-20260910/REPORT.md)
passes exact fresh local and anonymous replay, each with 152 tests and eight
explicit maintainer-only skips. The archive has 85 files and SHA256
`6038da2daed74e6ed4b509464dc6f1a4dae386e644d265235de982db4bf23e40`.
Public root commit is `866fc27`; export/build source is `c73874e`. Preserve the
create-once export, archive and all earlier releases. The final 36-page English
paper and 16-file source bundle are published as separate additive assets from
`e81ea83`. Fresh compilation matches all page text/pixels; anonymous downloads
and presentation replay pass. Preserve these assets as well.
See its [guide](../studies/paper_clause_reproducibility_v1/README.md).

Publication uses an explicit allowlist and sanitized history-free branch. Never
push the full local Git history. Exports exclude pixels, response bodies, proxy
snapshots, credentials, literature full text, weights and Korean drafts. Released
vectors permit numerical replay, not authentication or re-extraction of absent
pixels. Source URLs/license metadata do not grant image redistribution rights.

## Verification and preservation

Read [STATUS.md](STATUS.md) for current test and evidence-audit results, including
the full-suite rerun after the final adapter changes. Do not carry an earlier
passing count forward as a claim about the current tree. The immutable
[presentation check](reviews/20260910_substantive_revision/FINAL_PRESENTATION_QA_3.md)
records the published 36-page version's TeX/PDF and nine-figure QA, not the current
37-page draft, and assigns no new scores. The historical evidence audit does not
register the new namespaces, so their own replays are also required. Before
handoff after Python changes:

```sh
uv run --locked ruff check .
uv run --locked pytest -q -m 'not live'
uv run --locked latent-art-bench verify-evidence
make geometry-check
make figures-check
git diff --check
```

Build the final PDF and inspect all pages and figures. Update STATUS, the review
aggregate, analysis catalog and release verification with actual outcomes.
Canonical Protocol 2.1's broader reproduction gates remain unqualified.

Never rewrite or refresh frozen evidence, ledgers, protocols, sources or hashes.
The two historical evidence acknowledgements must not be extended to hide drift.
Ignored `research_workspace/`, `artifacts/` and `tmp/pdfs/` may contain unique
bytes. No broad cleanup or `git clean -xfd`. User-owned `paper/paper_ko.tex` and
ignored `paper/paper_ko.pdf` must remain untouched, unstaged and unpublished.
