# Current status — 2026-09-10

Work is on `codex/restore-four-artist-analysis`. The canonical English manuscript
is [paper/paper.tex](../paper/paper.tex). Read [ARTIFACTS.md](ARTIFACTS.md) for
retention rules, [AGENT_HANDOVER.md](AGENT_HANDOVER.md) for operational boundaries,
and [ANALYSES.md](ANALYSES.md) for computation and plotting commands.
No terminal study is reopened, and both user-owned Korean files remain untouched.

## Active paper-review goal

The user requests three skeptical reviews and substantive paper/analysis revision
until the unchanged nine-score average exceeds 9. Fixed aspects are scientific
rigor, contribution, and clarity/reproducibility, each scored 1–10.
[Round 1](reviews/20260910_substantive_revision/REVIEW.md) averaged **8.2333**;
round 2 averaged **8.6889**; round 3 averaged **8.9000**; round 4 averaged
**8.9333**. The target remains unmet. Three reviewers completed the committed
[39-page Round 4 snapshot](reviews/20260910_substantive_revision/ROUND4_SNAPSHOT.json).
All assigned scores are preserved in the linked review record. Current work
clarifies interpretation and diagnoses the Ubuntu failure in a distinct software
boundary, without reopening its closed strict attempt or changing scientific evidence.
Reviewers are maintainer-run LLM subagents with disclosed subsequent design,
implementation or writing involvement, not independent human/institutional reviewers.

The revision adds whole-scene moment maps, unchanged-map temporal transfer,
repeat-corrected conditional geometry and a separate evaluation-centering
comparison. These reuse retained measurements. Their complete numerical addendum
is already public. A prospective generic-clause follow-up is now complete and
integrated, with exact fresh local and anonymous public replay. All three
reviewers inspected the complete 35-page round-3 manuscript and all nine figures.
Their remaining presentation corrections are applied in the visually checked
published 36-page manuscript: comparison units/weights, exact abstract wording, larger
Figure 3 labels and a precise runtime pin. No new scientific score is assigned;
these corrections do not resolve the remaining design limits.
All four painters remain in the manuscript.

## Completed clause collection and analysis

| Cohort | Allocation and outcome | Inference |
| --- | --- | --- |
| [Original `pcvv1-20260910`](../reports/painter_clause_validation_v1/pcvv1-20260910/REPORT.md) | 288 slots; 211 images returned, one moderation refusal, one unqualified HTTP 500 error, one cancellation before posting and 74 unattempted; 62.97 minutes. All 864 measurement-status rows retained. | Permanently unavailable Monet/Cezanne primary comparisons and complete-grid secondary summaries. No complete-case estimates, refilling or pooling. |
| [Final successor `pcsv1-20260910`](../reports/painter_clause_successor_v1/pcsv1-20260910/REPORT.md) | 96/96 fresh Cezanne/generic outputs; 24 unchanged new scene briefs, two repeats per clause, 48 pairs; 45.5 minutes, no failures/retries. All 288 vectors measured. | Primary energy Cezanne−generic **−1.195419353**, raw **p=.00001**, rejects at fixed **alpha .025**. Generic/named energy 2.165789/.970369; named/generic trace .552327. |

The successor was fixed after the first refusal and before feature extraction
from the predecessor. Its allocation and threshold did not change when the
original Monet comparison also became unavailable. All briefs, including the
refused scene, remain. There is no further replacement cohort. Both collection
and measurement commands are one-shot and must not be invoked again.

Original source/qualification/freeze commits are `dff2804` / `90a993f` / `79f28c1`
(143 bindings); successor commits are `07f8231` / `d5887f8` / `6effea1` (167 bindings).
The new cohort uses OAuth only, with no additional paid cost. At most two
requests overlap; recorded starts are at least five seconds apart and each block
drains before the next. All successor outputs are nonsquare PNGs. Medium quality
is reported for 16 generic and six named outputs, low otherwise. These delivery
fields remain part of the service-response comparison.

The successor has one primary all-31-feature comparison and descriptive energy/
observed-trace summaries in three fixed pipelines. All three give lower energy
and trace for the named arm. It supplies no Monet comparison, artist-free control,
map evaluation, conditional-variance correction, retrieval or secondary tests.
No scene-population, perceptual or internal-mechanism claim follows.

## Main retained scientific evidence

| Analysis | Finding and scope |
| --- | --- |
| [Four-painter exploration](../reports/painter_distribution_exploration_v1/REPORT.md) | 649 references (Monet 297, Sisley 106, Pissarro 141, Cezanne 105), 1,536 named and 384 free outputs. All 24 full-feature trace ratios .206–.376; RBF balanced accuracy .940–.983. Two later retries complete descriptive coverage without restoring original full-grid inference. |
| [Four-painter controls](../reports/painter_distribution_study_v1/pdsv1-diagnostics-20260906/REPORT.md) | Generated/reference energy exceeds matched-size real/real medians for every painter. Pooled named energy is below its free median only for Sisley; this uses different panels/prompts from controlled Study 1. |
| [Study 1](../reports/painter_distribution_study_v1/pdsv1-analysis-20260907/REPORT.md) | 1,006 outputs, three services, 38 Monet/32 Cezanne references and a separate 221-work scaler. Six primary named/free energy changes are negative; four reject in the original eight-test family. |
| [Palette experiment](../reports/painter_responsiveness_v2/prv2-oauth-recovery-20260908/experiment/REPORT.md) | Sole primary 192-image run, six scenes/four repeats/four arms/two palettes. Both named-minus-generic response interactions unresolved. The 49-image predecessor remains ancillary. |
| [Measurement challenges](../reports/painter_measurement_validation_v1/pmvv1-20260910/REPORT.md) | 1,076 retained images and 1,706 vectors. Ten reference conditions characterize cross-family/processing responses. All eight common-square contrast signs and four original Holm rejections persist. This is computational characterization, not capture/perceptual validation. |
| [Temporal follow-up](../reports/painter_naming_replication_v1/pnrv1-20260910/REPORT.md) | 72 FLUX naming and 192 OAuth palette outputs, all returned in 64.3 minutes. FLUX energy changes −.695108/−.952024 reject in a separate four-test family; both palette interactions remain unresolved. Same templates, references and investigators. |
| [Moment-map geometry](../reports/painter_naming_geometry_v1/pngv1-20260910/REPORT.md) | Actual naming beats translation/scaling in six primary held-scene averages. Translation alone beats naming in both later primary FLUX views, with reported representation/deletion exceptions. Adding scale lowers conditional-mean mismatch in all six cells but raises reference energy in five. |
| [Evaluation centering](../reports/painter_naming_centering_v1/pncv1-20260910/REPORT.md) | At a common evaluation mean, the fitted scalar raises energy in all 60 original and 18 later views. This diagnostic does not test an internal mechanism or support an independent-repeat correction for the adapted map. |

## Public access and verification

| Numerical package | Verified access |
| --- | --- |
| [Original release `pprv1-20260910`](../reports/paper_reproducibility_v1/pprv1-20260910/REPORT.md) | 98 exact fresh local/anonymous checks; 98 hosted Ubuntu checks under the recorded floating-point contract. Seven Ubuntu figures match bytewise; the challenge PDF has platform-dependent bytes. Source `b2884c3`, public commit `2592dfb`. |
| [Geometry addendum `ppgv1-20260910`](../reports/paper_geometry_reproducibility_v1/ppgv1-20260910/REPORT.md) | Exact fresh local/anonymous replay of both namespaces and 95 tests. Source `5485e36`, public commit `7923049`; immutable 34-page manuscript and nine figures. |
| [Clause addendum `pcrv1-20260910`](../reports/paper_clause_reproducibility_v1/pcrv1-20260910/REPORT.md) | Public: 85 files, exact fresh local/anonymous replay of both separate cohorts, 152 tests and eight explicit maintainer-only skips in each environment. Archive SHA256 `6038da2d…bf23e40`, public commit `866fc27`. The final 36-page paper and 16-file source bundle are separately published; fresh compilation matches all page text/pixels, and anonymous downloads match all asset hashes. |
| [Failed precision qualification `pmrv1-20260910`](../reports/paper_map_reproducibility_v1/pmrv1-20260910/REPORT.md) | Public: 18 files, all 81 cells reproduce exactly in fresh local and anonymous-download environments; 73 tests in each. Archive SHA256 `00e82c31…62cd9f`, public root commit `3d70c37`. Same Mac; exact reconstructed support hashes constrain portability. V2 and manuscript assets are outside this release. |
| [Prospective fixed-map release `pmv2r-20260910`](../reports/paper_map_validation_reproducibility_v2/pmv2r-20260910/REPORT.md) | Public: 74 files, exact fresh local/anonymous replay of all 27 qualification cells and observed E/Q analysis, 75 tests in each. Archive SHA256 `8688085f…defb4eb6`, public root `f38da21`. [Single Ubuntu attempt](../reports/paper_map_validation_reproducibility_v2/pmv2r-20260910/HOSTED_REPORT.md) fails qualification comparison before observed replay; 75 tests and inventories pass. Current paper assets are not yet published. |

The earlier complete Python verification passed **1,800 tests in 272.96 seconds**.
The new map-validation namespace separately passes **110 offline tests in 28.12 seconds**,
including independent numerical-oracle and complete artificial transport checks.
Whole-tree Ruff is clean. After the separate public adapter was finalized, the
full offline suite passed **1,939 tests in 478.30 seconds**. This resolves the four
provisional adapter-test failures in the earlier 1,929-pass run; those failures
were outside the frozen collection source. The reviewed adapter at `916f5c5`
also passes all 29 scoped synthetic tests, with a separate
[packaging audit](reviews/20260910_substantive_revision/MAP_VALIDATION_RELEASE_AUDIT_2.md).
Actual export and complete fresh local/anonymous replay now pass all 27
qualification cells, exact observed analysis/report and 75 public tests each.
The single strict Ubuntu attempt fails the qualification comparison before
observed replay; all 75 tests and both inventory checks pass there. Its differing
numerical field is unknown. No rerun or tolerance/source change was made.
The earlier exact replay of all nine active manuscript figures is
unchanged. Historical evidence audit at `bd3c9ca`: **2,902 checks, zero failures**, with the same two old
acknowledgements. Both geometry namespaces replay exactly. The historical audit
does not register the new namespaces; each requires its own numerical check.

All public packages use explicit allowlists and history-free branches. Never
push the full local history or overwrite earlier archives/paper assets. Numeric
replay does not re-extract absent pixels or independently authenticate acquisition.
Original raw artwork, generated pixels, response bodies, proxy snapshots,
credentials, literature full text, weights and Korean drafts are excluded.

## Accounting and remaining boundaries

The pre-map-validation conservative OpenRouter baseline is **$50.7219185** against the
user's **$75** ceiling, including a retained historical $5 reserve. The temporal
FLUX collection added $5.04; both clause cohorts add zero paid cost. No monetary
value is assigned to OAuth subscription use. No further clause generation is planned.

The distinct FLUX/Cezanne map-validation proposal on 12 new scenes has stopped
before collection. Its fixed [offline qualification](../studies/painter_map_validation_v1/pmvqv1-20260910/PRECISION.md)
evaluated 96, 144 and 192 outputs (4, 6 and 8 repeats). All 81 proxy coverage
checks passed, but every allocation failed the baseline conditional-residual
precision criterion. At eight repeats, two of nine baseline Q median
half-widths were 1.018978 and 1.040286 against the fixed maximum 1.0; all energy
width checks passed. No interval was unavailable. Source commit `eb70ab8`;
810,000 simulated trials, no new images and no paid generation. No allocation
is selected, and this inferential proposal will not be collected or tuned after
failure. It cannot restore either unavailable clause endpoint, reuse their slots
or pool cohorts.
A bounded metadata-only preflight at 08:16 UTC on 10 September records
**$19.2726443 actual OpenRouter credits** and the unchanged `flux.2-max`
provider quote of **$0.07 per output megapixel**. This is separate from the
$24.2780815 project ceiling headroom. No new images or paid requests were made.
The create-once receipt is under
`data/manifests/painter_map_validation_v1/metadata/pmv-feasibility-20260910a/`;
source commit `c262d98`. The current 39-page working manuscript also includes an
analytically checked fixed-center convexity observation and the terminal capture
audit's limitation, without new vector evaluation or a new score. Its changed
pages compile cleanly and pass visual inspection; the earlier public assets
remain unchanged.

One [explicit prospective v2 redesign](../studies/painter_map_validation_v2/DECISION.md)
has passed its sole [offline qualification](../studies/painter_map_validation_v2/pmvqv2-20260910/PRECISION.md): R=10, or 240 outputs, with the same maps, interval,
historical proxy laws and precision thresholds. V1 remains stopped. The decision
records that v1's future-proposal clause and Protocol 2.1 section 15 permit a
separate version before new outcomes; the earlier broader interpretation was
corrected openly. Its finite-R energy target changes with R. All 27 coverage
checks and all nine baseline width checks passed in 270,000 simulated trials;
the minimum coverage lower bound is .97065 and the largest baseline Q median
half-width is .862593. There were no unavailable intervals. Source commit
`6956fec` precedes this single formal assessment. These are historical discrete
proxy calculations, not a service-coverage guarantee. There is no further
allocation assessment for this question in the revision.

The separately reviewed v2 collection is complete: **240/240 images**, no
failures or retries, **90.73 minutes**, and all collection eligibility checks
passed. It started at **10:11 UTC**. Source `765c5f7`, metadata/review source `c82e160`,
qualification commit `aaf431a` and freeze commit `c68c235` retain 188 bound inputs
and all 240 exact assignments. Both fresh two-GET metadata gates passed with the
unchanged endpoint and sufficient actual credits for the conditional $18.60
allowance. At most two requests overlapped, with five-second start spacing and
automatic financial serialization. The terminal ledger records **$16.80** in
new reported charges, **$67.5219185** in conservative project accounting, and no
new unknown charges, pending attempts or reserves. There is no replacement or
further collection. All 240 primary vectors are measured. Both fixed-map contrasts favor
translation/scaling: **deltaE −.390186879 [−.509032897, −.271340860]** and
**deltaQ −5.046510453 [−7.879516972, −2.213503934]**, using the qualified
approximate simultaneous interval procedure. The historical opposing ordering
does not transfer. The observed Q half-width 2.833 exceeds the proxy planning
criterion 1.0; proxy qualification did not guarantee achieved precision or coverage.
The [terminal audit](reviews/20260910_substantive_revision/MAP_VALIDATION_TERMINAL_AUDIT_2.md)
passes all 188 source bindings, 240 response/measurement records and exact
numerical replay, without feature re-extraction. Do not invoke collection or
measurement again.
The precollection [analysis](../studies/painter_map_validation_v2/ANALYSIS_REVIEW.md),
[operational](../studies/painter_map_validation_v2/OPERATIONAL_REVIEW.md) and
[coordinator](../studies/painter_map_validation_v2/PRECOLLECTION_REVIEW.md) reviews
remain source-bound. The working 39-page manuscript includes both allocation decisions, the interval
method and the contrary prospective result. All pages were rendered and inspected;
all nine figure replays pass. The final offline rerun with terminal records and public exports passed
**1,939 tests in 473.41 seconds**. Whole-tree Ruff and `git diff --check` pass.

A separate [stage R0 capture audit](../reports/painter_capture_audit_v1/pcav1-20260910/REPORT.md)
is terminal: **zero qualified pairs after 15 metadata requests across five
selected works**, with no images. New catalogue photographer/archive evidence
activated the two conditional candidates. All five capture-pair claims remain
unresolved; redirects, access denial and missing source ancestry are retained.
The original four-work audit is unchanged. A
[portable ledger view](../reports/painter_capture_audit_v1/pcav1-20260910/PORTABILITY.md)
preserves the complete event content while the original hash-bound ledger stays
local and unchanged. Capture acquisition and measurement remain closed.

Human style ratings, independently captured reproductions, learned-feature
validation and replication by separate investigators remain unperformed.
Service aliases are not independently attested checkpoints. The clause and fixed-map cohorts add new authored scenes for their separate
comparisons. Fixed-map transfer is now observed for one selected painter/service;
the earlier opposing energy/Q ordering does not recur. Protocol 2.1's broader reproduction gates are
unchanged and unqualified.

Historical review snapshots, prior manuscript corrections and exact verification
receipts remain linked from [INDEX.md](INDEX.md). Mutable status never replaces
immutable protocols, append-only ledgers or commit-bound evidence.
