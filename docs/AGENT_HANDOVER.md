# Agent handover: completed painter-feature analysis and research continuation

Prepared in English on 2026-09-05 at the user's request to hand the project to another agent.
This is a mutable orientation document, not a protocol, execution authorization, new analysis,
or replacement for sealed evidence. All repository paths below are relative to the repository
root unless they are Markdown links, which are relative to this document.

## 1. Executive handover

The requested empirical analysis is implemented, executed, and reported. It is not a proposal
waiting for its first images. The active implementation is **Painter Feature Generation v2** in
the Python package `latent_art_bench`; historical v1 code and evidence remain preserved.

The completed experiment compares a pinned local SD-Turbo baseline and two requested OAuth
service aliases, `gpt-image-1` and `gpt-image-2`, against measured digital surrogates of outdoor-place
paintings by Monet, Sisley, Pissarro, and Cézanne. It includes the entire registered generation
grids, reference acquisition and measurement attrition, interpretable feature comparisons,
SD-Turbo repeated-block uncertainty, synthetic calibration, and complete paired crop sensitivity.

The principal conclusion is **painter-feature reproduction is not demonstrated**. Some
painter-name conditions improve measured feature fit relative to the artist-free control, but
improvement, painter specificity, and equivalence are different properties. The report neither
ranks underlying models nor treats nominal confidence intervals as validated guarantees.

The user originally wanted eventual research-paper work, then explicitly narrowed the immediate
deliverable to an analysis report rather than a prototype manuscript. That report is complete.
A separate full Korean translation was subsequently requested and delivered. The present request
is for this handover, not authorization to start another generation run or draft a manuscript.

Start with these documents:

1. [Current status](STATUS.md), then [artifact retention policy](ARTIFACTS.md), as required by
   [AGENTS.md](../AGENTS.md).
2. [Completed English empirical report](../reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS.md).
3. [Korean companion translation](../reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS_KO.md).
4. [V2 operational workflow](V2_ANALYSIS_WORKFLOW.md).
5. The protocol sequence and evidence map below before proposing or executing an extension.

Do not begin by restarting a collector, rerunning `paper-study report`, rebuilding a frame,
resetting a lock, regenerating outputs, or cleaning ignored directories. Every current acquisition,
generation, measurement, and robustness run is terminal. There is no unfinished registered grid
to complete.

## 2. User intent and authority carried forward

The relevant conversation history, in order, was:

1. Understand the project and assess its status.
2. Complete the analysis implementation, with prospective improvements to rules/protocols if
   necessary, toward the eventual aim of a research paper.
3. Consider GPT Image services through the user's local `openai-oauth` setup in addition to
   SD-Turbo; defer a prototype paper and produce an analysis report for available generators.
4. Use the Codex authentication route for that API server and continue the analysis.
5. Translate the report into Korean in a separate Markdown file.
6. Produce a very detailed English handover for another agent.

Interpret these instructions together. The original paper ambition does not cancel the later
manuscript deferral. Permission to improve protocols did not permit retrospective changes to
already executed experiments, changing unfavorable results, unlimited paid usage, or bypassing
stage gates. The OAuth access and pilot were explicitly bounded, recorded experiments, not a
standing instruction to keep generating indefinitely.

The current task is **documentation-only work for the completed v2 study**. For the next task,
identify whether it is shared-primitive work, analysis of already exposed evidence, or a newly
versioned study. The distinction determines the applicable freezes and what can be claimed.

There is no unresolved question that prevents reading the reports, inspecting code, or running
offline checks. Before a material research expansion, obtain or establish the new scope: a
descriptive extension, better statistical calibration, new model/service experiments, independent
capture collection, or renewed manuscript drafting. Do not invent the user's choice.

## 3. Repository and working-tree snapshot

At preparation of this handover:

| Item | Observed state |
| --- | --- |
| Repository | `generative_art_diff` |
| Branch | `research/pfg-v2-paper` |
| HEAD | `39840bf0a7bcf263ba55136cfa333753b4efd754` |
| HEAD subject | `Publish completed empirical image-generation analysis and final project status` |
| Operating system / architecture | Darwin arm64 |
| Active locked Python environment | Python 3.13.11 |
| Project distribution / command | `latent-art-bench` / `latent-art-bench` |
| Current method ID | `pfg2-method-20260905` |
| Immediate deliverable | Completed analysis report, not manuscript |

The worktree was **not clean at the start of the handover task**. These changes belonged to the
completed translation task and must be preserved:

```text
 M docs/INDEX.md
?? reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS_KO.md
```

The index change adds the Korean companion link. This handover task adds
`docs/AGENT_HANDOVER.md` and its index link. No commit is created by the handover task. Reinspect
`git status --short --branch` when taking over; another user or agent may have added changes since
this snapshot. Do not assume that an untracked translation is disposable or that it exists in a
remote clone.

The original English report and its evidence receipt remain unchanged. Its SHA-256 is:

```text
2b65714a82447ad5db15441aebfef0637ee20635f354a19b351f8d9e2c44b636
```

The report receipt records input commit `a9f1f03f5139c731900ae2ad4d6a6b8997dc9530` and completion
time `2026-09-05T03:14:14.869633+00:00`. That input commit intentionally differs from the later
publication HEAD. A recording commit identifies the committed inputs available before the
new output was published; the new output need not already exist at that commit.

The Korean document is a human-readable companion translation, not a separately sealed empirical
result. Its prefatory note preserves the English original and linked evidence as authoritative.
Do not add it to an old receipt by changing the receipt or refreshing its hash.

## 4. Source-of-truth hierarchy and stale-document warnings

Use documents according to their purpose rather than treating every historical present-tense
sentence as current operational state.

| Document or record | Role and caution |
| --- | --- |
| `AGENTS.md` | Repository working rules, preservation requirements, stage boundaries, and validation commands |
| `docs/STATUS.md`, current v2 section | Mutable operational status; the later historical v1 section is explicitly historical |
| `docs/ARTIFACTS.md` | Retention and evidence policy; read its historical v1 descriptions within that scope |
| `studies/painter_feature_generation_v2/PROTOCOL.md` | Frozen v2 baseline, protocol ID `painter-feature-generation-v2/1.0`; its opening progress language describes issuance time |
| V2 amendments `PROTOCOL_1.1.md`, `PROTOCOL_1.2.md`, `PROTOCOL_1.3.md` | Specific prospective changes; read together with the baseline, not as permission to rewrite it |
| Stage freezes, manifests, ledgers, and receipts | Authority for the exact runs that occurred, including failures and completion conditions |
| `reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS.md` | Completed sealed empirical interpretation and tables |
| `reports/painter_feature_generation_v2/AVAILABLE_IMAGE_MODELS.md` | Earlier access-stage snapshot; its header explicitly supersedes old operational statements with the empirical report |
| `docs/V2_ANALYSIS_WORKFLOW.md` | Operational explanation and command routing; examples are not execution authorization |
| `docs/ARCHITECTURE.md` | Primarily historical v1 architecture; its opening R0-only/no-image description is no longer a description of the whole package |
| Root README and CLI help/docstrings | Contain historical v1 wording below current entry points; the actual CLI registers v2 commands |
| This handover | Navigation, verified snapshot, and recommendations; cannot override a protocol or receipt |

In particular, do not infer from the historical access report that SD-Turbo is still running,
that rendering acquisition has not started, or that the painter comparison is unexecuted.
Likewise, the historical v1 “zero images” statements do not describe v2.

The v1 canonical protocol remains `PROTOCOL_2.1.md` read with amendments 2.2/2.3 for its historical
study. V1 `PROTOCOL.md` is the frozen Protocol 2.0 text. The names are easy to confuse with v2's
own `PROTOCOL.md`, which is version 1.0. Never edit either frozen baseline to make the version
numbers or tense look more consistent.

## 5. Non-negotiable evidence and safety boundaries

### 5.1 Preserve what actually ran

- Never rewrite, reorder, truncate, move, or cosmetically regenerate frozen protocols, freezes,
  terminal receipts, hash-bound manifests, or append-only ledgers.
- A terminal run is closed permanently. A retry is a new ID, disjoint output/workspace paths,
  and explicit binding to the predecessor's terminal evidence. Successful prefixes are not
  spliced into a replacement run.
- Terminal collector code, configs, adapters, and their frozen tests remain evidence of what
  ran. Commit-bound verification does not grant permission to refactor them casually.
- Never refresh a recorded evidence hash to make a mismatch pass. Investigate the mismatch.
- Do not extend the v1 evidence acknowledgement file. Its two exceptions cover exact historical
  input hashes that were replaced before ever being committed, not future mistakes.
- Do not remove an execution lock because it looks empty or stale. A zero-byte one-shot marker
  may itself be material evidence.
- Do not relabel existing confirmation works as newly unexposed. Confirmation was opened once;
  a new filename or method ID cannot undo that exposure.

### 5.2 Keep scope and access explicit

- No external-holdout access, new acquisition, feature extraction, live generation transport,
  or image generation follows merely from a handover or an available CLI command.
- Standard tests stay offline. `live` tests require explicit user authorization and exclusion
  from the ordinary suite.
- A failed or partial generation grid receives availability reporting, not a favorable-prefix
  fidelity result. Keep refusals, failures, duplicates, and off-topic outputs in accounting.
- Do not aesthetically select, reroll, or quietly replace generated images.
- Do not initiate paid API use or rented compute without a specified spending authorization.
- Do not expose authentication tokens, copy them into this repository, add them to localhost
  client headers, or include them in logs/handover documents.
- Reviews so far were operator/LLM-assisted. Historical “neutral independent review” records
  refer to maintainer-run LLM subagents, not institutionally independent review.

### 5.3 Preserve ignored bytes and git history

The v2 ignored workspace held approximately **7.8G**, v1 workspace **133M**, and `artifacts/`
**433M** according to `du -sh` during this task. These are rounded filesystem measurements,
not archive manifests or byte-exact evidence totals.

Preserve these boundaries:

- `research_workspace/painter_feature_generation_v2/`: generated images, acquired originals and
  renderings, raw HTTP bodies, metadata responses, model weights, and stage runtime evidence.
- `research_workspace/painter_feature_generation_v1/`: historical raw responses and one-shot locks.
- `artifacts/`: retained models/source inputs described in the artifact policy.
- `tmp/pdfs/`: retained literature inputs where present; do not mistake them for report outputs.

`git clone`, a branch, or a tag alone does not preserve the ignored evidence. A machine handoff
needs both the relevant git history and a separate checksum-verified archive of ignored bytes.
Do not use `git clean -xfd`, broad recursive deletion, `git reset --hard`, or a checkout operation
that discards user changes. No cleanup or migration was performed for this handover.

## 6. Scientific question and exact scope of the completed study

The research construct is **Wikidata-declared outdoor-place digital-surrogate feature
reproduction**. The four painters are Monet, Sisley, Pissarro, and Cézanne. The analysis asks how
the feature distributions of painter-name image generation compare with the corresponding
recorded reference paintings, with other painters, and with an artist-free prompt control.

It is not a painter classifier, authorship detector, subjective aesthetic benchmark, claim about
physical brushwork, or probability-sampled study of each painter's full oeuvre. Attribution,
object type, medium/support, content, and collection come from recorded metadata, not a new
institutional catalogue verification or expert visual adjudication.

V2 made the following prospective changes relative to the stricter v1 plan:

- Used the already recorded 1,193 admitted work identities as a closed finite frame rather than
  continually extending a museum-source union.
- Kept deterministic exposure handling and fixed roles, but allocated new roles within painter
  rather than within many small painter × workflow cells.
- Retained independent captures, qualified margins, and workflow concerns as requirements for
  a positive reproduction claim, without pretending they were prerequisites already satisfied
  for a descriptive comparison.
- Retained all 16 exact prompt templates, all five conditions, and all three feature families.
- Used a 512-pixel common short side compatible with the native local generator, while preserving
  the 1,024-pixel real-image acquisition floor.
- Disclosed single-operator/LLM assistance and all known limitations.

Amendment 1.1 replaced oversized-original acquisition with registered Commons renderings of the
same work frame. Amendment 1.2 added the explicit single-repetition OAuth service pilot and
specified the final report, shared method, calibration, and robustness rules. Amendment 1.3
corrected the rendering transport assumptions in a new disjoint acquisition. Their timing relative
to already started generation is disclosed in the amendments; do not claim all amendments
preceded every generation request.

## 7. Completed corpus and measurement accounting

### 7.1 Fixed roles and finite reference

The frame is derived from the v1 R1 determination, not a rerun of the original metadata census.
Identity merging uses explicit, unambiguous links rather than image similarity. Historical
exposure matching placed 91 records in development-only; 14 denylist records lacked crosswalk
identifiers. Nonmatching is not proof of no operator exposure or no model training overlap.

New role assignment sorts work IDs within painter by SHA-256 of canonical JSON
`["pfg-v2/1.0-role", work_id]`, then assigns modulo-five **ranks** 0/1/2–4 to
development/qualification/confirmation. Do not substitute digest modulo five or shuffle roles.
Acquisition or measurement losses never trigger reassignment.

| Role | Fixed frame | Acquired | Successfully measured |
| --- | --- | --- | --- |
| New development | 222 | 221 | 221 |
| Historical development | 91 | 91 | 91 |
| Qualification | 222 | 220 | 219 |
| Confirmation | 658 | 653 | 649 |
| Total | 1,193 | 1,185 | 1,180 |

| Painter | Confirmation assigned | Confirmation acquired | Confirmation measured |
| --- | --- | --- | --- |
| Monet | 303 | 299 | 297 |
| Sisley | 107 | 106 | 106 |
| Pissarro | 142 | 142 | 141 |
| Cézanne | 106 | 106 | 105 |
| Total | 658 | 653 | 649 |

The report's reference population is the **649 successfully measured confirmation works**, not
all 658 assigned works and not all 1,180 measured images. Each reference work has equal mass.
Historical development is measured for diagnostics but excluded from fitting the scaler.
Qualification is diagnostic; it is not evidence of successful independent-capture calibration.

### 7.2 Acquisition sequence and failures

| ID | Final state and purpose |
| --- | --- |
| `pfg2-acquisition-20260905` | Original-image run terminal-aborted under the 64 MiB resource contract; 41 terminal dispositions, 33 acquired and eight failed |
| `pfg2-renderings-20260905` | Complete rendering metadata: 191 requests, all 1,193 works registered; first image collector terminal with 272 dispositions, 78 acquired, 194 failed, and one interrupted request |
| `pfg2-renderings-r2-20260905` | Corrected whole-frame acquisition complete: 1,185 acquired, six below the fixed short-side floor, two unsupported formats |

The first rendering collector rejected valid provider behavior: the new `thumb.wikimedia.org`
host and larger standard-size thumbnails inconsistent with its exact-dimension assumption.
The successor used the complete predecessor metadata, not earlier downloaded image successes.
No new works, lowered floor, opportunistic conversions, or alternative URLs were introduced.

Actual acquisition failures by role were one unsupported Monet development image, two undersized
Monet qualification images, four undersized Monet confirmation images, and one unsupported Sisley
confirmation image. All are retained in the fixed accounting.

Measurement then failed on four unprofiled non-RGB images: two Monet confirmation, one Pissarro
confirmation, and one Cézanne qualification. One Cézanne confirmation image failed because of
nonopaque alpha. These five failures explain 1,185 acquired versus 1,180 measured.

## 8. Generation, service identity, and authentication history

### 8.1 SD-Turbo baseline

- ID: `pfg2-sd-turbo-20260905`.
- Model: `stabilityai/sd-turbo`, revision `b261bac6fd2cf515557d5d0707481eafa0485ec2`.
- Frozen config: `configs/painter_feature_generation_v2/sd_turbo.json`.
- Local FP16 / Apple MPS; 512×512; one inference step; guidance 0; no negative prompt.
- 25 paired repetition blocks × 16 exact templates × five conditions = **2,000 requests**.
- All 2,000 generated and measured successfully; **400 images per condition**.
- Seeds are paired across conditions within template/block. The checkpoint and settings are
  recorded; bit-identical reproducibility on different hardware is not asserted.
- Model choice was based on available local compute before active outcome inspection, not an
  empirical finding that this is a leading contemporary generator.

### 8.2 Neutral access experiment: separate from painter evidence

- ID: `pfg2-image-access-20260905`.
- One neutral red-circle request per alias, two requests total, no painter prompts.
- Requested 1024×1024 / medium / PNG / opaque; both responses were HTTP 200 and decodable PNG.
- Both decoded as 1254×1254 with reported quality `low`, with no returned model snapshot.
- The strict original receipt records `invalid_output` and zero contract-compliant images.
- Separate offline `response_diagnostics.json` records two decodable images and explains why
  transport success did not satisfy the original contract. The receipt was not rewritten.
- These two images do not enter the empirical painter grid or its 2,160 generated-image total.

### 8.3 Complete OAuth painter pilot

- ID: `pfg2-oauth-pilot-20260905`.
- Frozen config: `configs/painter_feature_generation_v2/oauth_pilot.json`.
- Two requested aliases × 16 templates × five conditions × one repetition = **160 requests**.
- All 160 generated and measured successfully: 80 per alias, **16 images per condition**.
- No seeds, no automatic generation retries, no rerolls, and no aesthetic selection.
- The pilot was prospectively defined as the output of each requested alias on a dated service
  route, not as verified independently identified model weights.
- The measurement acceptance contract was a fully decodable allowed-format image with short
  side at least 512. Requested/returned mismatches were retained separately. This contract did
  not retrospectively convert the earlier neutral access failures into successes.

| Alias | Actual geometry | Reported quality | Returned model identity |
| --- | --- | --- | --- |
| `gpt-image-1` | 19 sizes; most frequent 1402×1122, 29/80; 80/80 landscape | `low` for all 80 | Absent for all 80 |
| `gpt-image-2` | 16 sizes; most frequent 1402×1122, 25/80; 79/80 landscape | `low` for all 80 | Absent for all 80 |

Do not substitute the neutral access probe's 1254-square dimensions for this grid's dimensions.
Do not use the response's `low` metadata as an aesthetic rating. Different aliases and different
file hashes do not establish different underlying model snapshots.

### 8.4 Local OAuth history and safe continuation

The access-stage investigation located the separate checkout at `dev/openai-oauth` under the
user's home directory, rather than the initially suggested home-level `openai-oauth` location.
The exact proxy source revision recorded in the access freeze is
`0a664bcc8e09649fcdd558e0bfbdd6447b85bca2`; selected source-file hashes are also retained there.

Recorded findings on 2026-09-05:

- The original port-10531 process predated an authentication/image source update and returned an
  expired-token error. A fresh current-source client authenticated with the configured Codex
  credentials. A stale running process was the supported operational explanation; its in-memory
  token was not inspected.
- A separate current-source instance on `http://127.0.0.1:10532` handled the recorded experiments.
  The original service and its replay state were not restarted or modified.
- The research client relied on the proxy's normal credential handling. It did not print/copy
  tokens or forward a token in a localhost client header.
- Source inspection and the proxy's then-passing offline forwarding tests supported that the
  requested `medium` and `1024x1024` values were sent unchanged. The upstream reason for the
  returned mismatch is unknown.
- This was a community-maintained Codex OAuth route, not proof of public API-key route semantics,
  unlimited subscription quota, or current model entitlement.

**These are recorded historical findings, not a fresh authentication or process-health test.**
No proxy was contacted, restarted, modified, or newly authenticated while preparing this handover.
No assumption is made that either listener is still running when another agent takes over.

If a later authorized experiment needs transport work, read the proxy's current README and
relevant local source first, compare them with the recorded provenance, and keep all credentials
outside the research repository. A source/route change needs fresh provenance and a new bounded
experiment contract. Do not test by rerunning either terminal study. Do not silently switch to
paid public API calls or claim a model snapshot merely because a model catalog lists an alias.

## 9. Implemented measurement and statistical contracts

### 9.1 Normalization and feature families

All real and generated images use the same frozen implementation:

1. Full decode, with truncation and incompatible image states rejected.
2. EXIF orientation applied; valid ICC converted to sRGB using perceptual intent; missing ICC
   assumed sRGB with an explicit flag; incompatible unprofiled non-RGB images rejected.
3. Nonopaque alpha rejected; original aspect ratio retained; Lanczos downsampling without
   upsampling to the **explicit frozen short side of 512**.
4. Float64 feature calculations, specified sRGB linearization and D65/2-degree Lab conversion.
5. Common equal-painter weighted median/IQR transform fitted on the **221 new-development**
   works only. All 31 IQRs were valid; no coordinates were dropped.

The low-level `features.normalize` function has a default short side of 1024. Do not mistake that
library default for the experiment's actual 512-pixel contract; the pipeline passes the frozen
value explicitly.

The exact 31 coordinate names, in registered family order, are:

| Family | Coordinates |
| --- | --- |
| Color, 11 | `lightness_median`, `lightness_iqr`, `chroma_median`, `chroma_iqr`, `chromatic_fraction`, `hue_concentration`, `hue_entropy`, `deltae_01`, `deltae_04`, `deltae_16`, `deltae_slope` |
| Spatial/orientation, 8 | `spectral_slope`, `spectral_residual`, `spectral_anisotropy`, `orientation_entropy`, `horizontal_vertical_balance`, `gradient_median`, `gradient_iqr`, `quadrant_jsd` |
| Digital texture, 12 | `wavelet_energy_1`, `wavelet_energy_2`, `wavelet_energy_3`, `wavelet_energy_4`, `wavelet_slope`, `wavelet_curvature`, `lbp_entropy_8`, `lbp_entropy_16`, `lbp_entropy_32`, `local_cv_01`, `local_cv_04`, `local_cv_16` |

Formula details are in the v2 baseline protocol and `features.py`: CIEDE2000 neighbor distances,
windowed spectral summaries, Scharr orientation/gradient summaries, stationary db2 wavelets,
uniform local binary patterns, and local coefficient-of-variation summaries. No learned evaluator
is the primary feature representation. The `learned` environment extra supplies generation
dependencies; its name does not mean the study's primary outcome is a learned embedding score.

### 9.2 Three different comparisons

For each painter × feature family, retain:

- **Target fit:** generated named-painter distribution versus that painter's real reference.
- **Specificity:** own-target distance minus distance to each of the three other real painters.
  Negative values favor the designated painter over that particular other painter.
- **Control improvement:** named-painter distance minus the artist-free distribution's distance
  to the same real target. Negative values favor naming the painter.

These produce 4 painters × 3 families × (1 + 3 + 1) = **60 endpoints** per comparison design.
Coordinate median differences and IQR ratios are separate descriptive diagnostics: **124
coordinate records per service**, four painters × 31 coordinates. They are not thresholded into
a reproduction label.

### 9.3 Finite V-statistic versus repeated generator U-estimator

The cross-service tables use finite energy distance:

```text
2 × mean cross-set distance − mean real-within-set distance − mean generated-within-set distance
```

Both finite within-set terms include diagonals. This is a V-statistic of the observed finite
sets, not an estimate with the same interpretation as the repeated generator analysis. Smaller
distance means closer measured feature distributions. Distances from different-dimensional
feature families are not directly comparable. Unequal generated sample sizes affect these
statistics; 16 versus 400 images per condition does not support an unqualified model ranking.

The repeated SD-Turbo analysis keeps the real population fixed and uses a generator U-term that
excludes equal repetition-block pairs. It may yield negative estimates. All 9,999 bootstrap
replicates jointly resample whole repetition blocks across templates, conditions, families,
and endpoints. They do not bootstrap paintings to imply sampling from a painter's oeuvre.

Implementation detail worth preserving: bootstrap self-pair exclusion removes the same
**resampled position**, not all pairs that happen to originate from the same original block.
Conflating those cases changes the bootstrap when a block is sampled more than once.

Simultaneous intervals use a maximum absolute standardized deviation across the valid endpoint
set. Zero/nonfinite bootstrap variability makes an endpoint inconclusive. The GPT pilot has no
repetition-based intervals or significance labels because it has only one repetition.

### 9.4 Synthetic calibration and its failed coverage guarantee

Calibration ID: `pfg2-calibration-20260905`. The registered diagnostic uses eight possible
synthetic blocks, 16 templates, 31 coordinates, 25 sampled blocks per trial, 100 trials per
scenario, 999 bootstrap draws per trial, and fixed PCG64 seed 20260905. It evaluates exact known
finite-population truths, not painter results or mock transport fixtures as empirical evidence.

| Scenario | Joint coverage over nondegenerate endpoints | Wilson 95% Monte Carlo interval | Zero-variance endpoint count |
| --- | --- | --- | --- |
| Null | 1.00 | [0.9630, 1.0000] | 48 |
| Shift | 0.86 | [0.7786, 0.9147] | 0 |
| Dispersion | 0.96 | [0.9016, 0.9843] | 0 |

The null result excludes 48 endpoints lacking intervals; it is not simultaneous coverage of all
60 endpoints. The shift result prevents presenting nominal 95% intervals as demonstrated 95%
guarantees. These intervals are exploratory. No active-outcome retuning was performed to repair
the result. A new calibration investigation must preserve this record and distinguish method
development from already exposed empirical evidence.

## 10. Main results, robustness, and remaining scientific limitations

The following is a navigation summary; the sealed English report and numeric artifacts contain
the complete values, including all other-painter contrasts and uncertainty intervals.

| Service | Images per condition | Negative control contrasts, out of 12 | Color / spatial / texture counts | Own target closer than all three others, out of 12 |
| --- | --- | --- | --- | --- |
| `gpt-image-1` | 16 | 7 | 4/4, 1/4, 2/4 | 8 |
| `gpt-image-2` | 16 | 7 | 3/4, 2/4, 2/4 | 9 |
| `sd-turbo` | 400 | 10 | 3/4, 4/4, 3/4 | 4 |

These are descriptive sign counts, not statistical discoveries. More favorable control contrasts
can arise from a weaker artist-free baseline. In particular, do not turn SD-Turbo's 10/12 control
contrasts into a claim that it has the best absolute painter fit or strongest painter specificity.

### 10.1 Paired crop sensitivity is complete

- Both branches contain **3,340** successfully measured images: 1,180 real plus 2,160 generated.
- One branch is uncropped, the other uniformly cropped by 1% at each edge.
- Both branches are analyzed at short side **496**, using the same scaler fitted only on
  uncropped-496 new development. Neither branch upsamples SD-Turbo.
- All paired features completed, with no measurement failures or invalid scaler coordinates.
- No named-minus-control sign reversed: 0/12 per service, 0/36 overall.
- All target-fit, specificity, and paired feature changes remain in the robustness result, not
  just the convenient control-sign summary.
- Crops share the same capture. Their stability is **not** independent-capture qualification.

### 10.2 Source, content, and geometry remain confounded

The diagnostic contains 96 stratum records; six have fewer than ten works and remain unresolved.
Supported-stratum comparisons still use the full generated condition, not matched generated
subject matter, and cannot isolate style from content. Painter content mixes differ substantially.

Do not mix denominators in the report's source table: profile/geometry summaries describe
measured confirmation images, whereas “frame content composition” describes the fixed frame's
confirmation composition. Content labels are metadata memberships, not a new visual census.

Square SD-Turbo outputs and mostly landscape OAuth outputs are not geometry-matched. Preserving
aspect ratio and using a common short side does not remove this spatial/texture confound.
“Native” real dimensions refer to acquired Commons renderings, not necessarily the original
full-resolution photograph or physical canvas. Collection memberships are not established
independent capture workflows; Commons derivatives may alter fine texture and color profiles.

### 10.3 Copy screens are not proof of originality

All three services had zero exact generated-duplicate excess, zero recorded perceptual/exact
copy candidates, and zero exact real-file matches in the diagnostic. The search covers measured
development, qualification, and confirmation images, not every image ever used for training.
The 63-bit perceptual hash uses an unvalidated distance threshold of eight. It is a screen, not
copy adjudication, training-overlap exclusion, or a guarantee of originality. Duplicates retain
their full statistical multiplicity if present.

### 10.4 What remains before a stronger paper-level claim

The principal missing evidence is:

- Attested underlying OAuth model identity and controllable generation settings.
- Repeated GPT grids under a new bounded, prospective design.
- Better validated uncertainty, especially around degeneracy and the observed undercoverage.
- Genuine independent captures and prospectively justified equivalence margins.
- Better control or explicit restriction of subject matter, capture workflows, profiles,
  borders, native geometry/resolution, and possible training overlap.
- Appropriate external review if an independent-review claim is desired.

More generated images alone do not establish equivalence or solve model identity, reference
provenance, content confounding, or training overlap. A defensible descriptive paper may be
possible with explicit limitations, but manuscript drafting was deferred by the user and no such
manuscript has been produced.

## 11. Evidence map and artifact navigation

All IDs in this table have compact tracked artifacts below
`data/manifests/painter_feature_generation_v2/`. Large runtime bytes belong below the ignored
`research_workspace/painter_feature_generation_v2/` boundary, with exact paths in the manifests.

| ID / location | Important compact files |
| --- | --- |
| `pfg2-frame-20260905/` | `frame.jsonl`, `frame_receipt.json` |
| `pfg2-acquisition-20260905/` | `acquisition_freeze.json`, `acquisition_events.jsonl`, `terminal_receipt.json` |
| `pfg2-renderings-20260905/` | Metadata requests/freeze/events/receipt, `renderings.jsonl`, `images_freeze.json`, `image_events.jsonl`, `terminal_receipt.json` |
| `pfg2-renderings-r2-20260905/` | `requests.jsonl`, `acquisition_freeze.json`, `acquisition_events.jsonl`, `acquisitions.jsonl`, `acquisition_receipt.json` |
| `pfg2-sd-turbo-20260905/` | `requests.jsonl`, `generation_freeze.json`, `generation_events.jsonl`, `outputs.jsonl`, `generation_receipt.json` |
| `pfg2-image-access-20260905/` | `assessment_freeze.json`, `requests.jsonl`, `assessment_events.jsonl`, `assessment_receipt.json`, `response_diagnostics.json` |
| `pfg2-oauth-pilot-20260905/` | `requests.jsonl`, `generation_freeze.json`, `generation_events.jsonl`, `outputs.jsonl`, `generation_receipt.json` |
| `pfg2-calibration-20260905/` | `calibration_freeze.json`, `calibration.json` |
| `model_sd_turbo.json` | Pinned local model evidence |

The shared method directory is the main entry point for numerical work:

```text
data/manifests/painter_feature_generation_v2/pfg2-method-20260905/
  method_freeze.json
  development_features.jsonl
  development_receipt.json
  scaler.json
  qualification_features.jsonl
  qualification_receipt.json
  confirmation_opening.json
  access_events.jsonl
  confirmation_features.jsonl
  confirmation_receipt.json
  empirical_analysis.json
  report_receipt.json
  experiments/
    pfg2-sd-turbo-20260905/
      generated_features.jsonl
      generated_receipt.json
      analysis.json
    pfg2-oauth-pilot-20260905/
      generated_features.jsonl
      generated_receipt.json
  robustness/
    uncropped_features.jsonl
    uncropped_receipt.json
    cropped_features.jsonl
    cropped_receipt.json
    scaler.json
    robustness_analysis.json
```

There is intentionally no repeated-block `analysis.json` for the single-repetition OAuth pilot.
Its finite results are in the shared `empirical_analysis.json`; absence of the repeated file is
not an unfinished job.

Useful direct links:

- [Method freeze](../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/method_freeze.json).
- [Primary finite empirical results](../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/empirical_analysis.json).
- [Repeated SD-Turbo results](../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/experiments/pfg2-sd-turbo-20260905/analysis.json).
- [Full paired crop result](../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/robustness/robustness_analysis.json).
- [Calibration result](../data/manifests/painter_feature_generation_v2/pfg2-calibration-20260905/calibration.json).
- [Report receipt](../data/manifests/painter_feature_generation_v2/pfg2-method-20260905/report_receipt.json).

The original v1 admitted frame comes from
`data/manifests/painter_feature_generation_v1/pfg_v1_r1_20260904_determination.jsonl` and its
`pfg_v1_r1_20260904_determination_receipt.json`. The exact prompt strings live in v1
`prompt_library.json`; do not paraphrase or translate them for a supposedly identical generation
experiment. The existing exposure denylist and content lexicon are also retained there.

## 12. Implementation map and tests

The installed entry point is `latent_art_bench.cli:app`. The outer Typer CLI forwards arguments
to the stage-specific parser. `paper-study` is the retained command name for v2, not a request
to write a paper. Importing the outer CLI does not eagerly load all analysis libraries.

Module paths in the table are relative to `src/latent_art_bench/painter_feature_generation_v2/`;
test paths are relative to `tests/painter_feature_generation_v2/`.

| Module | Responsibility | Main focused tests |
| --- | --- | --- |
| `corpus.py` | Frame reconciliation, exposure matching, fixed roles | `test_methods.py` |
| `artifacts.py` | Portable identifiers, path confinement, create-once publication, hash chains, OS locks | `test_methods.py`, pipeline/audit tests |
| `acquire.py` | Original-image acquisition contract and retained terminal run | `test_acquisition.py` |
| `renderings.py` | Rendering metadata and original rendering-image collector | `test_renderings.py` |
| `renderings_r2.py` | Corrected provider-host and actual-dimension acquisition | `test_renderings_r2.py` |
| `generate.py` | Pinned SD-Turbo model/download evidence, request grid, local generation | `test_generation.py` |
| `model_assessment.py` | Bounded neutral localhost access assessment | `test_model_assessment.py` |
| `assessment_diagnostics.py` | Offline interpretation of retained access responses | `test_assessment_diagnostics.py` |
| `oauth_generate.py` | Frozen full OAuth painter grid, mismatch and failure accounting | `test_oauth_generate.py` |
| `features.py` | Shared normalization and 31 interpretable coordinates | `test_methods.py` |
| `statistics.py` | Weighted scaler, finite energy, block estimator, simultaneous intervals | `test_methods.py`, `test_calibration.py` |
| `pipeline.py` | Method freeze, serialized measurement stages, one-time opening, access ledger, repeated analysis | `test_pipeline.py` |
| `empirical.py` | Common finite comparisons, source strata, service diagnostics, copy screens | `test_empirical.py` |
| `calibration.py` | Known-population simulation and recorded coverage diagnostics | `test_calibration.py` |
| `robustness.py` | Full paired 496-pixel branches, independent scaler, paired change summaries | `test_empirical.py`, `test_pipeline.py` |
| `report.py` | Deterministic English Markdown rendering and create-once report receipt | `test_report.py` |
| `audit.py` | Read-only v2 evidence graph verification, including retained runtime bytes | `test_audit.py` |
| `cli.py` | Explicit v2 stage parser and dispatch | Inspect alongside the package-level CLI |

Shared dependencies include `latent_art_bench/io.py`, v1 `panel.py`, the v1 prompt library, and
the v1 evidence machinery. Their names do not imply the v2 analysis is missing or independent of
all v1 primitives. The historical collector modules and adapters remain frozen evidence.

### 12.1 Runtime behavior and continuation pitfalls

- `publish()` uses exclusive creation. Existing artifacts, even identical ones, are not
  overwritten. “File exists” is an intentional boundary, not a reason to delete the file.
- Stage locks use `fcntl.flock`; a crash releases the OS lock without deleting the lock file.
  A second active writer should fail rather than corrupt an append-only stage.
- Measurement uses three frozen worker threads with ordered main-thread writing. The access
  writer verifies the prior chain under the lock once and then fsyncs each appended event.
- Interrupted **nonterminal** stages may resume under unchanged registered inputs and accounting.
  This is different from retrying any of the now-terminal stages.
- Confirmation opening required committed development/scaler, qualification, calibration, and
  both generation experiments' terminal dispositions. Later access reads were logged. The final
  report binds the completed access ledger, so extending that ledger is not a harmless action.
- Some execution-time checks compare bound inputs with working-tree bytes, whereas evidence
  auditing can resolve recorded commits. An audit passing does not mean an old command is safe
  or meaningful to rerun against changed current code.
- `report.py` has a fixed `REPORT` path and refuses execution if the English report or receipt
  already exists. A new method ID alone does **not** create a new report destination.
- `pipeline.prepare` binds the current v2 protocol/config family and expects the existing artifact
  contracts. Do not assume the helpers are an arbitrary-model benchmark framework.
- `empirical.analyze` rejects duplicate service aliases across the experiments of one method.
  Adding another run with the same aliases requires an explicit new design, not list concatenation.
- `statistics.analyze` expects all five conditions with complete arrays of at least 25 blocks,
  16 templates, and 31 coordinates. It is not the correct entry point for the single-block GPT pilot.

Keep future changes small and versioned where required. Do not refactor the sealed pipeline into
a generalized experiment framework merely to make the project look more complete.

## 13. Environment, commands, and validation

Use `uv.lock`, not an unpinned package upgrade. The observed environment was Python 3.13.11 on
Darwin arm64. `pyproject.toml` declares Python >=3.9; that declaration is not evidence that all
supported Python versions or operating systems were tested during this work. Local generation
was configured for Apple MPS, and locking uses `fcntl`; portability requires its own checks.

The `analysis` extra supplies SciPy, scikit-image, PyWavelets, and plotting support. The `learned`
extra supplies Torch/diffusers and associated generation dependencies. Preserve both extras in
the shared environment commands below; an environment sync with a narrower extra set may remove
dependencies another process expects. No package or lockfile changes were made for this handover.

### 13.1 Safe orientation and offline validation

Run from the repository root:

```bash
git status --short --branch
git log -6 --oneline
uv run --locked --extra analysis --extra learned latent-art-bench paper-study -- --help
uv run --locked --extra analysis --extra learned ruff check .
uv run --locked --extra analysis --extra learned pytest -q -m "not live"
uv run --locked --extra analysis --extra learned latent-art-bench verify-evidence
uv run --locked --extra analysis --extra learned latent-art-bench paper-study audit
git diff --check
```

The extra `--` before detailed help forwards it past the outer CLI. The audits are read-only
checks of evidence and retained bytes. They are not acquisition, generation, or new feature
extraction. `uv run` can synchronize the local environment from the lockfile; the standard test
suite itself excludes live provider calls.

For a small report-focused check:

```bash
uv run --locked --extra analysis --extra learned pytest -q tests/painter_feature_generation_v2/test_report.py
```

Before handoff after Python changes, run Ruff and the full offline suite. Changes touching
manifests, research workspace, or freeze-bound material require evidence verification. Do not
run `pytest -m live`, a live assessment, or a generation command as an ordinary smoke test.

### 13.2 Results rechecked during this handover task

| Check | Observed result |
| --- | --- |
| Report-focused offline tests | 4 passed |
| Ruff | Passed |
| Full offline suite | 334 passed in 17.69 seconds |
| Historical v1 evidence audit | 2,902 checks, zero unacknowledged failures |
| V2 evidence audit | 15,809 checks, zero failures |
| Handover documentation checks | All 12 links resolve; role counts match source artifacts; original report hash unchanged; the read-only example reproduces the English report byte-for-byte |

The historical v1 audit still reports two explicitly acknowledged unrecoverable pre-repair
inputs: `federated_census.py` and its test file, at the exact hashes named in
`evidence_acknowledgements.json`. It may also report informational working-tree drift for shared
files whose recorded historical bytes are successfully found in git. Those are not new failures.
Neither informational drift nor an existing acknowledgement authorizes ignoring a new mismatch.

The preceding Korean translation task verified all 190 Markdown table rows cell by cell for
numeric values, signs, and missing-comparison dashes, as well as numeric-token counts, section
structure, shell commands, local links, and the original report hash. It also reran the v2 audit.
No scientific result was recomputed or changed to produce the translation.

### 13.3 Verify report reproduction without republishing it

For read-only renderer verification, use `report.render`, not `report.execute` or the CLI
`report` command. The following reads compact numeric artifacts and compares text in memory;
it does not read raw images, append access events, or overwrite the report:

```bash
uv run --locked --extra analysis --extra learned python - <<'PY'
from pathlib import Path
import json

from latent_art_bench.painter_feature_generation_v2 import report

base = Path("data/manifests/painter_feature_generation_v2")
method_id = "pfg2-method-20260905"
method = base / method_id

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

freeze = read(method / "method_freeze.json")
repeated = {}
for experiment_id in freeze["experiment_ids"]:
    path = method / "experiments" / experiment_id / "analysis.json"
    if path.exists():
        repeated[experiment_id] = read(path)

rendered = report.render(
    method_id,
    read(method / "empirical_analysis.json"),
    read(base / freeze["calibration_id"] / "calibration.json"),
    read(method / "robustness" / "robustness_analysis.json"),
    repeated,
)
original = Path("reports/painter_feature_generation_v2/EMPIRICAL_ANALYSIS.md")
assert rendered.encode("utf-8") == original.read_bytes()
print("English report matches the sealed numeric results byte-for-byte.")
PY
```

This equality check complements, rather than replaces, the commit-bound evidence audit. If a
future renderer version differs, investigate version provenance; do not overwrite the historical
report to make the check pass.

## 14. Recommended continuation plan, not yet authorized execution

The next agent should first read and verify, then agree on the next deliverable. The completed
analysis does not need more acquisition merely to become “finished.” Further work should address
a stated scientific limitation or communication need.

### Step A: Preserve and orient

1. Read status, artifacts, and agent instructions; inspect the current worktree.
2. Preserve the Korean translation and this handover, including any uncommitted index edits.
3. Read the English report and the prospective v2 amendment sequence.
4. Run the offline checks and inspect failures before changing anything.
5. Establish whether the next task is documentation, exposed-data exploration, method development,
   or a genuinely new experiment. Record that distinction in the work plan.

### Step B: Choose a bounded research extension

| Candidate direction | What it could resolve | Requirements before execution |
| --- | --- | --- |
| Improve interpretation/presentation of sealed results | Clearer narrative, evidence-linked tables or figures | User wants that deliverable; use numeric evidence, retain original report, label any new post-hoc analysis |
| Investigate uncertainty calibration | Diagnose shift undercoverage and degeneracy; compare justified procedures | New versioned synthetic-only work, explicit evaluation plan, no tuning on old painter outcomes, retain old calibration |
| Qualify a future GPT service route | Establish returned controls and model identity to the extent possible | Current local-source inspection, new bounded access protocol/ID/provenance, explicit live authorization and quota/cost constraints |
| Repeat GPT grids | Estimate service variability across scheduled repetitions | Prespecified repetitions/order/failure policy, complete grids, validated inferential plan, known exposure status, authorized resources |
| Independent-capture study | Support capture disturbance estimates and defensible equivalence margins | New provenance-backed capture selection, rights/access authorization, protected role/exposure plan, sufficient independent works |
| Draft a descriptive manuscript | Communicate completed findings with limitations | User reverses the manuscript deferral and specifies desired scope/venue; no stronger claims than the evidence permits |

A sensible scientific priority is to understand uncertainty calibration before scaling up an
inference-heavy generation study, while separately resolving route identity/control limitations.
This is a recommendation, not a decision already made by the user or a change to the old method.

### Step C: Register any new experiment before observing its outcomes

Define the new question and estimand, source/frame reuse, prior exposure, service/model identity,
parameters, prompt library, repetitions and pairing, complete request order, resource budget,
failure/resumption policy, measurements, diagnostics, and permissible claims. If external access
or spending is involved, resolve its authority first.

Use a new versioned namespace when existing sealed evidence would otherwise be mutated. A new
experiment ID may be sufficient only where the existing contracts genuinely support it; changing
the scientific method or report destination may require a new study/report implementation.
Bind predecessor evidence for a deliberate retry, commit exact clean bound inputs before freezing,
and keep all new runtime bytes under a clearly authorized ignored boundary.

Already opened v2 confirmation is **exposed reference data** for future method development.
Analyses designed after reading these results must be called exploratory or post-hoc unless a
genuinely independent prospective validation design is supplied. New IDs do not restore blindness.

### Step D: Execute only the authorized stages and hand off an auditable result

Keep all attempts and outcomes, report losses, never substitute a new scientific goal after a
technical failure, and stop a terminal run permanently. If a plan fails, diagnose why and pursue
the same stated goal under an explicitly new, justified contract where necessary.

At the end, deliver the requested artifact plus exact validation and limitations. Update
`docs/STATUS.md` if operational state changes and `docs/INDEX.md` if canonical documents are added
or retired. Keep mutable status separate from immutable evidence. Avoid creating redundant
progress files, duplicated protocols, or a manuscript the user did not ask for.

## 15. Common mistakes to avoid

1. Treating a historical R0-only architecture page as proof that v2 features/generation are absent.
2. Calling the current analysis incomplete because there is no manuscript or no repeated GPT file.
3. Using the 658 assigned confirmation count where the analysis uses 649 measured works.
4. Fitting the scaler on historical development, qualification, confirmation, or generated images.
5. Calling `qualification` successful independent-capture validation.
6. Comparing V- and U-estimator values as though they were identical statistics.
7. Calling nominal intervals validated despite 0.86 synthetic shift coverage.
8. Interpreting null coverage as covering all 60 endpoints when 48 had no intervals.
9. Ranking models by control-contrast sign counts or treating requested aliases as attested weights.
10. Claiming shared latent seeds for OAuth, or equating low metadata with measured low visual quality.
11. Treating common short-side normalization as native-resolution or aspect-ratio matching.
12. Treating uniform crops, duplicate files, different hosts, or multiple encodings as independent captures.
13. Using zero perceptual-hash candidates as proof of no copying or no training overlap.
14. Running the report writer again because the renderer can reproduce the text in memory.
15. Deleting a lock, a failed response, or ignored media to get past an intentional terminal guard.
16. Refreshing a hash or expanding acknowledgements to hide a new mismatch.
17. Reusing an exposed confirmation set while describing it as unopened validation.
18. Restarting the old proxy or spending on a new route merely because earlier calls were authorized.
19. Describing operator-run LLM reviews as institutionally independent.
20. Assuming a git-only handoff includes the local media, weights, or uncommitted Korean translation.

## 16. Suggested first message to the user after taking over

Adapt this to the next actual request; it is not a required script:

> I have read the completed v2 analysis and its evidence boundaries. The registered experiments
> and Korean translation are complete, and the existing runs will remain sealed. I will first
> verify the current worktree and offline checks, then identify the smallest next step toward
> your research goal. Any new generation, capture collection, or manuscript drafting will be
> scoped explicitly rather than treated as an in-place continuation of the closed experiment.

The essential handover is: **preserve the completed evidence, distinguish descriptive results
from reproduction claims, and make the next scientific question explicit before running more.**
