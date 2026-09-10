# Agent handover — artist-specificity experiment and paper

Read [STATUS.md](STATUS.md), then [ARTIFACTS.md](ARTIFACTS.md), inspect
`git status --short --branch`, and preserve unrelated working-tree changes.
This document is mutable orientation; immutable scientific records stay at their
original paths. The canonical English manuscript is [paper/paper.tex](../paper/paper.tex).
The [paper guide](../paper/README.md) covers compilation and visual inspection;
[ANALYSES.md](ANALYSES.md) maps computation and plotting for each study.

Test maintenance after the previous paper closeout reduced routine coverage and
removed 41 unbound obsolete or formatting cases. The specificity extension adds
15 numerical, routing and membership cases: `make check` now selects 823, while
`make check-all` includes 1,121 additional historical cases (1,944 total).
See [test scope](../tests/README.md). The original `pytest.ini`, `pyproject.toml`,
bound tests and published evidence remain unchanged; routine selection lives in
`pytest-paper.ini`. Use an explicit `tests` argument for the full retained suite.

## Completed artist-specificity extension

The authorized painter-specificity extension and manuscript reframing are
complete. See the completed-results section of [STATUS.md](STATUS.md)
and [the new protocol](../studies/painter_specificity_v2/PROTOCOL.md). The prior
review stopping condition below applies to that old iteration. Do not resume its
collectors, portable replay proposal or score optimization. Keep new evidence in
`painter_specificity_v2`, retain all four artists, use English and keep cumulative
paid accounting below $120 without querying remaining credit balances.

The first specificity attempt is terminal after 31 outputs, before feature
measurement. Both upstream model-selection negative controls accepted invented
image-model IDs. Preserve that evidence and do not measure/pool it. The local
adapter adds model-name forwarding but does not verify upstream model selection.

The successor has **1,008 requests: six models × 14 scenes × six clauses × two
repeats**, with medium quality for all four OpenAI models on explicit paid routes.
Source commit `d223402`; exact assignment/freeze commit `c55fef6`. Collection is
complete: 1,008/1,008 outputs, no failures or retries, closed at 18:21:04 UTC on
10 September. Do not restart it. The append-only ledger and terminal
receipt are under `data/manifests/painter_specificity_v2/psv2-20260911/`;
raw bytes are under the corresponding ignored workspace. Baseline $68.50735
includes all eight paid probes and the historical $5 uncertainty reserve.
New charges total $43.786326; final cumulative accounting is $112.293676.
Never query remaining balances. Measurement is complete: 1,008 generated rows
and 649 reference-window rows, with full/square vectors and four numerical
analyses. Do not launch duplicate extraction or collection.

The completed 17-page manuscript presents the six-model results, three main
figures and all four painters. The central contrast is strong aligned response
without faithful reference geometry: GPT Image 2 has beta .999 but D 1.226;
FLUX has the smallest point D (.801), with adjusted advantages over both 2.5
variants and no resolved advantage over the other models. All 24 generated
clouds have lower total variance than the references. The terminal
[report](../reports/painter_specificity_v2/psv2-20260911/REPORT.md) contains exact
numbers and links to all eight new figures. The generic/palette controls and
contrary map-transfer result remain in the paper; neither establishes internal
training causation. The new addition has not been archived as a public release.

Use the [corrected reference reader](../studies/painter_specificity_measurement_v1/CORRECTION.md)
for all four replay views. Measurement itself is permanently closed. The historical manifest has
649 measured works and four old failures; the frozen original reader mistakenly
assumed it contained only valid records. The adapter preserves the intended panel
without editing frozen source or retrying an old failed image. Completed historical findings and their contrary fixed-map
transfer result remain, with operational details moved out of the main text.
The new reference-content sensitivity uses the four historical title-lexicon
classes inherited through the frame. Do not describe these as the later
controlled panel's separate three-class LLM visual annotations.
The user's Korean files remain untouched.

### Verification and immutable inputs

- `make specificity-check`: four exact numerical replays pass.
- `make specificity-audit`: terminal report and all 1,008 response/image hashes pass.
- `make figures-check`: all retained/new presentation artifacts and generated tables pass.
- Whole-tree Ruff and all 1,944 retained offline tests pass; routine selection is 823.
- Historical evidence audit: 2,902 checks, zero failures, the same two old acknowledgements.
- `make paper`: 17 pages, no TeX warnings; all pages and eight new figures visually checked.

Final layout fixes corrected inline math, placed the complete comparison tables
together and clarified the common-fraction denominator. Table-generation changes
only affect LaTeX float placement; numerical replay remains exact. Current-doc
relative links pass. The frozen report CSVs retain the standard CSV writer's
CRLF endings; an ordinary staged whitespace check flags those carriage returns.
The CRLF-aware check passes without changing any bound report byte:
`git -c core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol diff --check HEAD^ HEAD`.
The temporary keep-awake assertion
has been stopped; no collection or postprocessing process remains.

The terminal collection is committed at `3fe90d7`. Numerical source/freeze
identities remain `d223402` / `c55fef6`; reference weighting `fdb646a` / `ec63052`;
reader correction `86e1bd1` / `0017c26`. The create-once report binds its own source,
so do not edit `painter_specificity_measurement_v1/report.py` or overwrite the
report to change wording. Corrected membership excludes only the four historical
failed reference measurements. New primary re-extractions matched all 649 prior
vectors at 1e-10; development scaling uses 221 works, not all 312 manifest rows.

The local adapter in the separate `openai-oauth` repository adds the requested
2.5 names (`d0a390f`) and discloses unverified upstream selection (`50be88d`).
The new scientific comparison uses documented paid model routes. Its responses
omit model/quality echoes, so requested configurations are not checkpoint
attestation. No remaining-credit endpoint was queried. No image, feature or
result from the stopped 31-output attempt enters the successor.

## Closed iteration and current boundary

The original request used the DeerFlow academic-paper-review skill, three
skeptical LLM reviews, substantive revisions and a nine-score mean above 9.
The fixed aspects are rigor, contribution and clarity/reproducibility, each 1–10.
Round 1 averaged 8.2333; round 2 averaged 8.6889; round 3 averaged 8.9000;
round 4 averaged 8.9333. The original threshold remains unmet. The user's latest
instruction is to finish the current iteration and stop if the score increased;
the increase from round 3 meets that revised condition. No fifth review or new
research cycle is authorized by this closeout. All three reviewers
completed the [39-page Round 4 snapshot](reviews/20260910_substantive_revision/ROUND4_SNAPSHOT.json),
including all appendices and nine figures. Current wording corrections and a
separate Ubuntu diagnostic receive no automatic score increase. See the [review record](reviews/20260910_substantive_revision/REVIEW.md)
for exact snapshots and scores. Do not inflate scores or claim the original
above-9 threshold was reached. All reviewers are operated by the
maintainer and have disclosed subsequent design/implementation involvement.
They are not independent human or institutional reviewers.

The distinct portability diagnostic is complete; its [authenticated result](../reports/paper_map_portability_diagnostic_v1/pmpdv1-20260910/REPORT.md)
finds 27 qualification support-hash failures and floating differences below 4e-15.
The displayed scientific table is unchanged. The original exact route remains
failed. The separate [portable replay contract](../studies/paper_map_portability_v1/DECISION.md)
uses support bytes that must match every pre-data hash and applies the existing
1e-10 finite-float comparison to the observed object as a declared new contract.
The proposal is deferred at the user's stop instruction, before qualified
implementation, support export or replay. The unused agent draft was moved to
the ignored preparation directory; there is no active portable entry point.
Do not resume that proposal without a new user instruction or alter the frozen
exporters, completed diagnostic or scientific results.

The final 39-page English manuscript and 16-file source bundle are
[published and verified](../reports/paper_map_validation_reproducibility_v2/pmv2r-20260910/PAPER_ASSETS.md)
from source commit `2969a31`. Fresh compilation matches all page text/pixels;
anonymous asset hashes and presentation replay pass. Earlier assets remain
immutable. No publication or review work is pending for this iteration.
The fixed-map collection and measurement are terminal complete, using paid FLUX
without human ratings or learned features. New reported costs total $16.80;
conservative accounting is $67.5219185 against the $75 ceiling, including the
retained historical $5 reserve. No new unknown charges or pending attempts remain.
Do not assign a monetary value to OAuth subscription use.

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
change bound source or replace failed slots. At most two requests overlapped,
recorded starts are five seconds apart, and blocks drain before the next.
Both collections and one-shot measurements are complete. Do not invoke measure again.
The successor's three
pipelines and C/G energy/trace scope are fixed; it has no free arm, map/Q,
retrieval or secondary hypothesis tests. The stopped predecessor retains all
864 measurement-status rows and unavailable endpoints. Use each namespace's
`check` and `verify-responses` commands for verification; the latter checks
private retained response hashes.

## Completed fixed-map comparison

The [v1 planning qualification](../studies/painter_map_validation_v1/pmvqv1-20260910/PRECISION.md)
is terminal: all 81 proxy coverage checks passed, but R4/R6/R8 each failed the
baseline conditional-residual width gate. No allocation was selected or collected.
Its [public release](../reports/paper_map_reproducibility_v1/pmrv1-20260910/REPORT.md)
contains 18 files, with exact fresh local/anonymous replay of all 81 cells and
73 tests in each recorded environment. It preserves a failed planning decision,
not new image evidence. V1 remains stopped.

One separately declared [R10 redesign](../studies/painter_map_validation_v2/DECISION.md)
passed its single 27-cell qualification. The one-shot `pmv2-20260910` collection
returned all 240 images: twelve fixed new scenes, ten repeats and free/named
FLUX/Cezanne arms. All primary512 feature rows are measured. Operational source `765c5f7`, qualification `aaf431a` and
freeze `c68c235` bind the exact source, reviewed protocols and assignments.
At most two attempts overlap, recorded starts are at least five seconds apart,
and each pair drains before the next. The fixed historical maps, primary512
31-feature pipeline, development scaler and references remain unchanged.

Do not invoke collection again, resume, refill, replace failed slots or change
bound source. Do not invoke the completed one-shot measurement again. There is
no replacement or further allocation for this question. Both points and all
component scores require the complete eligible 240-vector grid after terminal
measurement. Qualification does not establish actual service coverage or
independent stationary repeats. The [technical contract](../studies/painter_map_validation_v2/TECHNICAL_PROTOCOL.md)
fixes conditional budget forecasts, $5 liabilities, retry limits and stop/drain
rules; no top-up or reserve reduction is authorized. The new E/Q differences
are −.390186879 and −5.046510453, with both approximate simultaneous intervals
wholly below zero: both targets favor translation/scaling. The historical
opposing ordering does not transfer. Observed Q half-width 2.833 exceeds the
proxy planning threshold 1.0; passed qualification is not achieved precision or
a coverage guarantee. The [terminal audit](reviews/20260910_substantive_revision/MAP_VALIDATION_TERMINAL_AUDIT_2.md)
passed all source, response and measurement checks and exact ordinary replay.

The reviewed public adapter, `tools/paper_map_validation_release.py`, is committed
at `916f5c5`; its 29 synthetic tests passed in 155.56 seconds. The
[adapter audit](reviews/20260910_substantive_revision/MAP_VALIDATION_RELEASE_AUDIT_2.md)
records independent synthetic extraction, stdlib verification and observed-vector
replay. Actual export and fresh local/anonymous replay now pass all 27 qualification
cells, exact observed E/Q/report and 75 tests each. The
[public package](../reports/paper_map_validation_reproducibility_v2/pmv2r-20260910/REPORT.md)
has 74 files and archive SHA256 `8688085fe001e6b45ca34f6d39a5979e3e762a2678cd5ecb8169a698defb4eb6`;
public root is `f38da21`, build source `bd3c9ca`. The
[single hosted Ubuntu attempt](../reports/paper_map_validation_reproducibility_v2/pmv2r-20260910/HOSTED_REPORT.md)
fails the qualification comparison before observed replay; all 75 tests and
inventories pass. Its reconstructed object was not retained. The subsequent
diagnostic records its own support-hash failures and floating differences below
4e-15; it cannot recover the earlier discarded object or identify a particular
backend operation as the cause. No rerun, source or tolerance change is allowed
for the original attempt. Earlier assets and failed-v1 records remain unchanged.

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
records the earlier 36-page version's TeX/PDF and nine-figure QA. The current
[39-page build/access record](../reports/paper_map_validation_reproducibility_v2/pmv2r-20260910/PAPER_ASSETS.md)
covers final publication and assigns no new scores. The final suite passes
1,970 offline tests in 499.08 seconds; Ruff is clean. The historical audit at
`be5cc37` passes 2,902 checks with zero failures and the same two old
acknowledgements. The historical evidence audit does not
register the new namespaces, so their own replays are also required. Before
handoff after Python changes:

```sh
uv run --locked ruff check .
uv run --locked pytest -q tests -m 'not live'
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
