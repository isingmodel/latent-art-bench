# Agent handover — paper revision and clause validation

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
Round 1 averaged 8.2333; round 2 averaged 8.6889. See the [review record](reviews/20260910_substantive_revision/REVIEW.md)
for exact snapshots and scores. Do not inflate scores or claim the goal achieved
before the honest mean exceeds the threshold. All reviewers are operated by the
maintainer and have disclosed subsequent design/implementation involvement.
They are not independent human or institutional reviewers.

The current expansion uses no human ratings, learned features or paid calls.
Cumulative conservative OpenRouter accounting is $50.7219185 against the $75
ceiling, including the retained historical $5 reserve. Do not assign a monetary
value to OAuth subscription use.

| New scope | Source / qualification / freeze | State |
| --- | --- | --- |
| `painter_clause_validation_v1/pcvv1-20260910` | `dff2804` / `90a993f` / `79f28c1` | Permanently stopped: 211 images from 288 slots; one refusal, one unqualified server error, one cancellation before posting and 74 unattempted. Both primary comparisons and complete-grid secondary summaries are unavailable. |
| `painter_clause_successor_v1/pcsv1-20260910` | `07f8231` / `d5887f8` / `6effea1` | One final 96-output Cezanne/generic collection, running from a verified 167-input freeze. All 24 unchanged scenes, two repeats and fresh controls; alpha .025. |

The successor decision was committed at `f0ab2d4` after the initial Cezanne
refusal, before the later stop and before feature extraction. Its allocation
and threshold remain unchanged after Monet became unavailable. No observations
are pooled and no further cohort is planned if this successor fails or remains
unresolved. The HTTP 500 had a null error code and is outside the unchanged
numeric-code-match retry rule; never reclassify or retry it retrospectively.
The [terminal audit](reviews/20260910_substantive_revision/CLAUSE_TERMINAL_AUDIT_2.md)
records timing, accounting, response hashes and the inference restrictions.

Both live collectors are one-shot. Do not invoke collect again, resume, refill,
change bound source or replace failed slots. At most two requests are active,
recorded starts are five seconds apart, and blocks drain before the next.
The successor must become terminal before its feature extraction. Its three
pipelines and C/G energy/trace scope are fixed; it has no free arm, map/Q,
retrieval or secondary hypothesis tests. The stopped predecessor may be measured
after the successor freeze, preserving all 864 measurement-status rows and
unavailable endpoints. Each namespace provides `measure`, `check` and
`verify-responses`; the last checks private retained response hashes.

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
make figures-check
make paper
```

Terminal clause checks require their measurement receipts. Original local
workflow checks can require the retained private response archive; public
adapters have explicitly narrower numerical contracts. Do not repeat extraction
merely to verify a manuscript edit.

Six figures come from `paper/make_figures.py`, one from `paper/replay_palette.py`,
one from `paper/make_validation_figure.py`, and the ninth is copied from the
immutable geometry report. The older geometry-sensitivity figure uses “generic”
for short-scene named prompts; the manuscript labels that contrast correctly
without overwriting frozen evidence. New clause findings use a compact table.

The [original numerical release](https://github.com/isingmodel/latent-art-bench/releases/tag/pprv1-20260910)
(source `b2884c3`, public commit `2592dfb`) has 98 local/anonymous exact checks
and 98 hosted Ubuntu checks under its documented floating-point contract.
The [geometry addendum](https://github.com/isingmodel/latent-art-bench/releases/tag/ppgv1-20260910)
(source `5485e36`, public commit `7923049`) has exact fresh local/anonymous replay
of both namespaces and 95 tests. Preserve both archives, paper assets and the
original release's explicit erratum. Their sealed packagers must not be edited.

`tools/paper_clause_release.py` is the separate, currently unexported adapter
for both clause cohorts. It is being extended and requires its own final review,
real export, archive verification and anonymous replay before access is claimed.
See its [guide](../studies/paper_clause_reproducibility_v1/README.md).

Publication uses an explicit allowlist and sanitized history-free branch. Never
push the full local Git history. Exports exclude pixels, response bodies, proxy
snapshots, credentials, literature full text, weights and Korean drafts. Released
vectors permit numerical replay, not authentication or re-extraction of absent
pixels. Source URLs/license metadata do not grant image redistribution rights.

## Verification and preservation

Latest source qualification: Ruff passes, all 1,705 offline tests pass in 201.71
seconds, and the historical audit passes 2,902 checks. These checks precede the
current adapter extension; final checks must reflect its actual completed source.
The historical audit does not register the new namespaces, so run their own
replays as well. Before handoff after Python changes:

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
