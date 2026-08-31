# Development-pilot implementation status

## Current disposition

`pilot_3` now has an assembled prospective Freeze-A1 package. The authoritative finalist
metadata audit, corpus selection, source-held split, Phase-A measurement contract, and final
budget-constrained Phase-B estimation design are implemented. No Pilot 3 artwork byte,
transport-conformance request, or generated output has yet been opened; the applicable gates
remain closed until explicit freeze commits.

| `pilot_3` planning layer | Current status |
|---|---|
| Target | named artists; eras/movements are metadata only |
| Candidate decision | 9 prior-research candidates; 4 purposively advanced before fresh collection; no feasibility claim for the other 5 |
| Successor metadata audit | complete for the 4 finalists, 2 development sources, and 3 official external museum/provider blocks |
| Pilot 2 machine recovery | `pass`; counts, refusals, descriptive rows, qualification, and simulator inputs re-derived |
| Final generated design | 16 content blocks × 4 repetitions × (4 named + 1 shared control) = 320 `gpt-image-2` requests; estimation only |
| Real-corpus sample size | 52 selected: 32 training, 8 calibration, 12 sealed external; 25 metadata-only `not_selected` candidates; zero replacement-eligible reserves and no post-Freeze-A1 replacement |
| External design | complete Minneapolis, Dallas, and Toledo blocks; one work per artist per block; exact within-block `24^3 = 13,824` label assignments |
| Asset/claim boundary | exact official museum bytes; internal noncommercial research only; no redistribution, same-session, or cross-digitization claim |
| Generation gate | closed |
| Next authorized action | commit Freeze A1, then acquire/extract the 40 development works only |

The [Pilot 3 protocol](PILOT_3_PROTOCOL.md),
[planning report](../reports/pilot_3/PLANNING_REPORT.md), and
[planning index](../reports/pilot_3/planning_index.json) give the exact claim and I/O
boundaries. The assembled package does not authorize pixels until committed, and Freeze A1
does not authorize the external holdout or generation.

Development uses five works per artist from each of AIC and Met. The external holdout uses
official assets supplied by Minneapolis Institute of Art, Dallas Museum of Art, and Toledo
Museum of Art; Commons delivery is prohibited. Blocking controls holding institution and
official asset provider, but published metadata do not establish a common camera, operator,
capture date, or conservation-imaging session within a block.

## Final pilot_2 disposition

`pilot_2` completed its prospectively frozen generated-output phase and passed offline
verification. Its learned-formal calibration gate is `pass`, all 320 assigned cells are
terminal, and the registered analysis ran. The exact next-step decision is
**REDESIGN**.

| `pilot_2` layer | Final status |
|---|---|
| Learned-formal qualification | `pass` on the fixed development/calibration atlas |
| OAuth transport conformance | `pass` for exact requested-label acceptance and returned PNGs; no executed-model attestation |
| Generation | 320/320 terminal; 315 successes and 5 moderation refusals |
| Attempt accounting | 320 attempts; 320 observed exchanges; 0 retries, indeterminate sends, or technical failures |
| Learned-formal feature estimand | incomplete: 251/256 named/control pairs |
| Scientific execution | `complete`; this records execution/accounting, not hypothesis support |
| Registered hypotheses | both requested-label strata unsupported and all four primary tests not tested because each stratum is incomplete |
| Cross-label/model claim | none registered or supported |
| Next-step decision | **REDESIGN** |

The five refusals are final intention-to-request outcomes, not cells to replace or retry.
They comprise four `gpt-image-1` cells and one `gpt-image-2` cell. Consequently,
`gpt-image-1` has 124/128 complete named/control feature pairs and `gpt-image-2` has
127/128, for 251/256 overall. There are no missing successful features and no unresolved
ledger cells.

The available-pair values below are descriptive because the registered complete-grid
tests did not run. All AIC-only and NGA-only signs are positive, but that fact cannot
substitute for the absent familywise lower bounds and exact sign-flip tests.

| Requested label | Complete pairs | Target improvement | Specificity DiD | Registered test | Support |
|---|---:|---:|---:|---|---|
| `gpt-image-1` | 124/128 | `8.6492391997` | `5.6107138440` | `not_tested_incomplete_feature_grid` | unsupported |
| `gpt-image-2` | 127/128 | `9.9262685683` | `6.5012713053` | `not_tested_incomplete_feature_grid` | unsupported |

These are separate operational requested-label strata. The local OAuth facade does not
provide authoritative upstream executed-model identity, and no cross-label superiority
estimand was registered. The learned-formal qualification pass is a measurement
precondition; it is not evidence that either generated-output hypothesis passed.

Authoritative `pilot_2` records are the [final report](../reports/pilot_2/REPORT.md),
[frozen protocol](PILOT_2_PROTOCOL.md),
[pilot_2 failure investigation](PILOT_2_FAILURE_INVESTIGATION.md), and
[artifact index](../reports/pilot_2/artifact_index.json). Principal content identities
are:

- protocol document: `9237aad13aaa18a6b6c661d5d3d4e97457cbd7950eccf5ff3733c8ecd1af46cf`;
- qualification result: `7e2734c403399e544595e4c88f361ad82398a88a57657f938cb40e30502a7842`;
- generation completion: `85446d312fe673e528736277d8aeef86936c2f2fbcc4b42130473d4b532b2f29`;
- requested-label analysis: `a7fb58770ced0315a5963f1cd9606d91dd10ec30a324196af7720da85b82025c`;
- chromatic secondary: `e459dcec8e92ba566df6b4d4e19ccc761b3deb7e8fabf3c62d12f98d89f97977`;
- artifact-index payload: `846b14b1c7cda5428a9010d7efe682f26c8db0587dba7d2b812403fb5173e026`.

A separate [post-result visual-QC manifest](../reports/pilot_2/visual_qc/manifest.json)
covers all 320 cells in 16 deterministic sheets (315 thumbnails and five refusal
placeholders). Its semantic SHA-256 is
`6f883b3942af51afae2def871692014b295c9a39357f7b5a449d1c4e7a7f8457`.
This audit is explicitly post hoc, selection-free, non-gating, and outside the frozen
analysis artifact index.

The `pilot_2` artifact index contains 36 records. Full offline `pilot2 verify` requires
the retained local attempt ledger, feature manifests, derived inputs, generated PNGs, and
model/source artifacts. The compact committed report and index preserve their identities,
but a clean checkout cannot recompute or byte-verify ignored artifacts that are absent.

“Complete” means the frozen study was executed and accounted for. It does not mean the
256-pair feature estimand was complete or that a hypothesis was supported. An unsupported
result here is not proof that artist conditioning is absent.

## Historical pilot_1 disposition

`pilot_0` followed its frozen failure path. The separately versioned `pilot_1` redesign
produced two `fail` cards, so its scientific gate remained closed. The following sections
retain that historical record; none of its failed cards is changed by the later
`pilot_2` qualification.

### Frozen artist-level corpus

The target is the artist, not an era or movement. Era and movement labels remain
cross-classified metadata because an era is too heterogeneous to substitute for an
artist-level target and would change the estimand from target-versus-neighbor
specificity. The roster was selected from the prior museum-source and common-genre
research, without using generated outputs or favorable feature separation.

| Artist | Frozen neighbor | Canonical works |
|---|---|---:|
| Claude Monet | Alfred Sisley | 30 |
| Alfred Sisley | Claude Monet | 21 |
| Camille Pissarro | Paul Cezanne | 30 |
| Paul Cezanne | Camille Pissarro | 27 |

The shared view is landscape/outdoor-place scenes. The corpus contains 108 canonical
works, split into 76 training and 32 held-out works, with 119 reproductions. Eleven
alternate files represent only seven independent physical works.

### Final pilot_1 qualification

#### Chromatic v2: fail

The scalar Lee seamlessness formula passed its synthetic probes, but this was not enough
to recover the paper's defining empirical behavior. The full mean-rescaled chromatic-
distance distribution collapse was ineligible: all 108 primaries lack a clear border
review, the schema lacks explicit partial-image and serious-damage review fields, none
of the 108 files supports the paper's 3000 px maximum without upsampling, and 17 of 108
exceeded the project's distributional K-S margin on at least one available branch.

| Check | Exact final result | Disposition |
|---|---:|---|
| Formula behavior | verified | necessary but insufficient |
| Lee input eligibility | 0/108 border-clear primaries | failed |
| Full normalized-distribution collapse | `ineligible` | failed source-behavior recovery |
| Held-out artist balanced accuracy | `0.3506944444` | narrowly above the aggregate floor |
| Held-out source balanced accuracy | `0.2416666667` | diagnostic only |
| Leave-source-out artist balanced accuracy | pooled `0.3369674185` | not every fold passed |
| Direct 400/500 ratio, 95% interval | `0.0819375820`, `[0.0580938772, 0.1279254608]` | isolated supported sensitivity |
| Direct 256/500 ratio, 95% interval | `0.2604446675`, `[0.1718565735, 0.3900617693]` | isolated supported sensitivity |
| Q95 4:4:4 ratio, 95% interval | `0.0558064356`, `[0.0414253939, 0.0804704261]` | isolated supported sensitivity |
| Q85 4:2:0 ratio, 95% interval | `0.4325558376`, `[0.2634302557, 0.6231027032]` | failed; upper bound exceeds `0.5` |
| Same-work reproduction ratio, 95% interval | `0.5882766278`, `[0.2433774343, 1.8285907947]` | failed; upper bound exceeds `1.0` |

The per-artist recall was Sisley `0.8333`, Monet `0.4444`, Pissarro `0.0`, and
Cezanne `0.125`. The leave-source-out folds were AIC `0.3277`, CMA `0.0`, Met `0.2`,
and NGA `0.3729`; a favorable pooled value cannot hide the failed folds. The final
qualification-card supported scope is empty.

#### Learned-formal v2: fail

The clean-room source-compatible extractor produced 119 finite 16,384-value A-vectors.
The recovered full `512-base-ema.ckpt` and pinned Diffusers VAE agree bit-for-bit for all
248 mapped tensors: 83,653,863 float32 values and 334,615,452 logical bytes. This verifies
the two recovered containers, not the authors' unpublished A-vectors, RNG state, or the
identity of the exact checkpoint used in the paper.

| Check | Exact final result | Disposition |
|---|---:|---|
| Determinism probes | 4/4 byte- and metadata-exact | repaired seeded policy verified |
| Held-out artist balanced accuracy | `0.53125` | diagnostic only |
| Held-out source balanced accuracy | `0.5375` | diagnostic only |
| Nested leave-source-out artist balanced accuracy | `0.4126566416` | pooled diagnostic only |
| Primary PCA | 32 components; `0.6152142296` retained variance | failed the frozen `0.95` target |
| Same-work reproduction ratio, 95% interval | `0.7423170871`, `[0.5108065957, 1.1001825090]` | failed; upper bound exceeds `1.0` |
| Kim released-source native-area domain | 108/108 primaries eligible | passed strict `width * height > 410 * 410` screen |
| Kim aspect-ratio domain | 107/108 primaries eligible | failed |
| Artist-by-source split coverage | incomplete | failed source-confounding control |

`reproduction-cma-136510-primary` is 900 x 419 (aspect ratio 2.148), outside Kim et
al.'s strict `< 2` domain. Missing cells include Sisley-CMA training, Monet-CMA training,
and Monet-Met in both splits. The final qualification-card supported scope is empty.

The implementation now pins the observed Python, platform, Torch, Diffusers, NumPy,
OpenCV, Pillow, JPEG, and MPS environment. This improves reproducibility but does not
repair the failed scientific design.

#### Unresolved learned-feature codec confound

All 119 real inputs are JPEG, while all 40 generated outputs are PNG. The recovered Kim
source path writes the 512 x 512 intermediate with the source extension, so origin and
intermediate codec are perfectly associated:

```text
real image      -> JPEG intermediate -> VAE
generated image -> PNG intermediate  -> VAE
```

The source-faithful path is valid for source-method replication, but it is not an
unconfounded real-versus-generated comparison. A future scientific run must cross codec
with origin and use the same lossless primary intermediate for both origins.

### API-test boundary and completed traversal

The retained generation ledger has 41 attempt records for 40 resolved frozen cells: 20
successful files requested as `gpt-image-1`, 20 requested as `gpt-image-2`, and one
preserved `gpt-image-1` moderation refusal before the identical frozen cell succeeded on
explicit retry. The generation records themselves report zero qualification-bypass
calls.

Those names are requested labels only. `~/dev/openai-oauth` was launched without an
upstream override and routes its compatibility endpoint to the ChatGPT Codex backend,
not to the public `api.openai.com` Images API. The retained responses contain no
authoritative executed-model identity, so an image-1-versus-image-2 comparison is not
supported.

All 40 successful requests specified `1024x1024`; 0 of 40 returned files matched that
contract. Nine returned sizes were observed, with widths 1392-1412 px and heights
1114-1130 px. This 40-of-40 mismatch is systematic and is not a reason to keep retrying.

After the final cards failed, generated-feature preparation and analysis ran only with
the explicit `--allow-unqualified-test-preparation` and
`--allow-unqualified-test-analysis` flags. Provenance carries that bypass into every
downstream cell. The result set contains exactly 16 named-artist cells and 64 matched
artist-free pairs. They are engineering diagnostics, not scientific observations. All
16 specificity reference-resampling ranges include zero; those ranges resample only the
real reference side, hold the generated side fixed at `n=4`, and are not inferential
confidence intervals.

| Artist-free diagnostic | Requested label | Pairs | Median raw distance |
|---|---|---:|---:|
| Chromatic | `gpt-image-1` | 16 | `0.0587337` |
| Chromatic | `gpt-image-2` | 16 | `0.0797196` |
| Learned formal | `gpt-image-1` | 16 | `99.4847` |
| Learned formal | `gpt-image-2` | 16 | `96.8956` |

The exact per-cell target-gap and specificity values are reproduced, without promotion
to scientific results, in the [final report](../reports/pilot_1/REPORT.md#test-only-distribution-diagnostics).

### Work-package disposition

| Work package | Engineering disposition | Scientific disposition |
|---|---|---|
| WP0-WP3 | frozen contract, corpus, preprocessing, and provenance complete | development inputs only |
| WP4-WP5 | both measurement implementations and final evaluations complete | both cards `fail`; gate closed |
| WP6-WP7 | generation attested; test-only preparation, analysis, and report complete | not opened for scientific inference |

No scientific task remains inside `pilot_1`. Its next planned work was the separately
frozen `pilot_2` now summarized above; neither pilot permits another retry or retrospective
relabeling of its results. The next project-level action is the `pilot_2` **REDESIGN**
decision, not mutation of either completed ledger.

### Pilot_1 evidence identities

- Chromatic evidence SHA-256: `aab262dd6dcc7c5302df4947871448603c4424ad888c164ec91e38834f0f1aa4`
- Learned-formal evidence SHA-256: `eeadf841101eddda157447ee3cdff1770e7f46c94c930ffdbbae334ac97c5033`
- Generation attestation SHA-256: `477a3626013b3ee9140f76cfdbb76b6e996b6973222d6b3fcc72fed5fdf45764`
- Analysis-results SHA-256: `eb9cda2a8fcc4226b1798426635699a8bfbb6b70bd8c1f85823ff7e782129576`

The complete content-addressed ledger is in
[`reports/pilot_1/EVIDENCE.md`](../reports/pilot_1/EVIDENCE.md). The locked finalization
command sequence is documented in the [README](../README.md#development-pilot-commands).

### Pilot_1 clean-checkout verification boundary

The final artifact index records 196 entries and 46 run records. The repository commits
the compact qualification, model-verification, attestation, analysis, report, and index
snapshots. Raw museum images, all generated PNGs, model weights, the source checkout,
derived views, and high-dimensional feature/vector manifests remain ignored local files.
The evidence anchor records their identities and retention status, but a clean checkout
cannot byte-verify or recompute bytes that are not distributed. Public verification is
therefore limited to the committed compact snapshots and the internal hash links among
them.
