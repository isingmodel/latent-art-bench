# Current status — 2026-09-23

LatentArtBench asks whether painter-name prompts recover differences between
painters or mainly produce a shared painting-like appearance. The primary
six-model experiment was collected and measured on 2026-09-11. Everything added
since then is **retrospective analysis of retained data**: no images have been
generated or acquired, and no paid request has been made. Recorded cumulative
paid accounting is **$112.293676**, under the user's ceiling of strictly below $120.

Work stopped on 2026-09-21 after the ICML draft reached the user's replacement
review target. Resuming scientific work or revising a manuscript needs a new
instruction from the user.

## Manuscripts

| Manuscript | Source and output | Content | Last assessment |
| --- | --- | --- | --- |
| ICML-format draft (8 main pages, 60 total) | [paper/icml.tex](../paper/icml.tex) → `output/pdf/latent_art_bench_icml.pdf` (local only, not in Git) | Most complete: primary results plus every retrospective extension below | Round-04 AI scientific review **6, 6, 4** (mean 5.33) on PDF `3fbf2daf…`; live sources are identical to the reviewed input |
| Full-length paper (23 pages) | [paper/paper.tex](../paper/paper.tex) → [paper/paper.pdf](../paper/paper.pdf) | 2026-09-15 final editorial update; primary results, diagnostics and source-quality audit, without the ICML-era extensions | Unscored after its final update; the last scored snapshot (`_04`) received 8.0625 (Claude Code / Opus 5) and 8.8125 (Astra / xhigh) on the editorial rubric |
| Korean translation (26 pages) | [paper/latent_art_bench_korean.tex](../paper/latent_art_bench_korean.tex) → `output/pdf/latent_art_bench_korean.pdf` (local only) | Translation of the full-length paper at commit `f9e3935` | Not reviewed; PDF SHA-256 `096db88b…` matches the 2026-09-21 record |

All scores are internal language-model assessments of exact PDF snapshots, not
human evaluation, conference decisions or evidence of scientific validity. The
[ICML review record](../reports/icml_review_v1/README.md) and the
[editorial review record](../reports/paper_editorial_review_v1/README.md) keep
every review, including low scores.

## Primary experiment

Six requested configurations (GPT Image 1, GPT Image 2, GPT Image 2.5 Flare,
GPT Image 2.5 Sunburst, Nano Banana 2 and FLUX.2 Max) × 14 scenes × six prompt
clauses × two repeats = **1,008 images**. The 649-work reference panel
(Monet 297, Sisley 106, Pissarro 141, Cézanne 105) is compared in 31 color,
spatial and texture features; a separate 221-work panel scales them.

- All six aggregate reference-aligned slopes are positive under the declared
  simultaneous procedure, including the source-correction sensitivities.
- FLUX.2 Max has the lowest uncalibrated error point estimate (D = 0.801;
  0.832 with corrected source regions; 0.872 with corrected regions and scaler).
  Its adjusted advantage over Sunburst does not survive source correction; the
  Flare comparison stays separated. No model is shown to beat the D = 1
  no-contrast benchmark before calibration.
- GPT Image 2 has the lowest held-scene calibrated error estimate.
- Alignment is uneven across artist pairs, especially Monet–Sisley.
- An assistant audit covers all 870 reference/development sources; 131 cropped
  images were re-measured. Its labels are not independent ground truth.

Reports: [primary](../reports/painter_specificity_v2/psv2-20260911/REPORT.md),
[diagnostics](../reports/painter_specificity_review_v1/REPORT.md),
[follow-up diagnostics](../reports/painter_specificity_review_v2/REPORT.md),
[source quality](../reports/painter_reference_quality_v1/REPORT.md).

## Retrospective extensions, 2026-09-18 to 2026-09-21

Each has its own plan in `studies/`, source module, tests and hash-bound
analysis. None collects new observations; all reuse previously exposed data.

| Analysis | Result |
| --- | --- |
| [Direct naming decomposition](../reports/painter_specificity_review_v3/report.md) | Common movement is 66.7–88.4% of named-minus-generic change (single-scene deletion 65.9–90.2%). Monet–Sisley alignment is most positive for GPT Image 2 and negative for Sunburst. |
| [Request timing](../reports/painter_request_timing_v1/REPORT.md) | A common linear drift model has negative held-out gain in every configuration (−0.72% to −3.38%); service independence is not established. |
| [Learned representations](../reports/painter_learned_audit_v1/REPORT.md) | CLIP and CSD on 2,009 same-image vectors: common movement supplies 73.2–83.8% (CLIP) and 54.2–79.7% (CSD) of named-minus-generic prototype gain; Monet–Sisley alignment turns positive in both. |
| [Held-scene prompt-name transfer](../reports/painter_prototype_transfer_v1/REPORT.md) | Common translation changes mean accuracy by +2.68 pp (CLIP) and +9.97 pp (CSD) on the primary target; centroids fitted to labeled generated images win all 12 primary combinations but use more information. |
| [Repeat covariance scenarios](../reports/painter_repeat_covariance_v1/REPORT.md) | Fixed hypothetical correlations; three model pairs change point order. Actual covariance is not identified and no interval is repaired. |
| [Separate SD-Turbo collection](../reports/painter_cross_cohort_v1/REPORT.md) | 2,000 retained images: 64.18% common change overall, but texture only 36.58%; pooled D 0.917 versus scene-wise D 1.637. |
| [Reference-calibrated abstention](../reports/painter_selective_attribution_v1/REPORT.md) | Primary CSD setting: accepted error falls 26.03 pp against unrestricted prediction but only 0.526 pp against matched-margin filtering. All eight settings fail the declared joint criterion. |

## Decisions waiting for the user

1. **ICML corrections.** The [round-04 report](../reports/icml_review_v1/review_report_2026-09-21.md)
   lists four corrections still present in the scored PDF: the Table 2 caption,
   the description of Frochte v2, selective-classification prior work (Jones
   et al.) and "an coverage-matched" in the conclusion. Applying them produces a
   new, unscored PDF.
2. **Which manuscript leads.** The full-length paper lacks the ICML-era
   extensions; the Korean translation follows the full-length paper.
3. **Prospective family controls.** The [plan](../studies/painter_family_controls_v1/PLAN.md)
   adds shared-family prompt controls: 4,608 new images (six configurations,
   12 scenes, eight arms, eight windows). Its collector and analysis pass offline
   qualification ([preparation record](../reports/painter_family_controls_v1/README.md)),
   but it needs about $200 at historical rates, a proposed $350 cumulative
   ceiling and at least 40 GiB of storage. None of these is approved and nothing
   has been collected.
4. **Public release.** The six-model experiment has no versioned public release
   and no public exact-pixel archive or verified recovery route. The local
   [numerical bundle](../reports/icml_review_v1/numeric_bundle_v1/README.md)
   replays 16 checks but contains no pixels.

## Outstanding review requests

The ICML scientific reviewers still ask for evidence the project does not have:
independent fresh observations, a shared-family prompt control, public access to
exact pixels and a broader painter scope than four related painters with finite
digital reference panels. Closed-service repeat dependence is unidentified, and
the SD-Turbo check reuses the historical target. There is no human evaluation or
perceptual validation; the user asked that none be added. Local hashes and
replay are not independent research replication.

## Verification

Recorded on 2026-09-23 during the documentation cleanup, which changed only
navigation documents and the Makefile:

- `make check`: Ruff passed; 1,251 routine tests and 110 SD-Turbo/selective tests
  passed. Before the Makefile fix, Ruff reported 324 findings, all in frozen audit
  scripts under `reports/` and one hash-bound ICML builder.
- `make check-all`: 2,482 tests passed.
- `make evidence`: 2,902 checks, 0 failed. `make editorial-check` passed.
- `make specificity-check`, `review-check`, `reference-quality-check`,
  `figures-check`, `icml-evidence-check` and `icml-extensions-check` replayed
  exactly; no tracked result or figure changed.
- The ICML format check passed on the reviewed build
  (`ICML_BUILD=tmp/paper/icml-resume-build`): 8 main pages, 60 total, PDF `3fbf2daf…`.
- The Korean translation compiled with Tectonic into a scratch folder.

Repeated on 2026-09-25 before committing the cleanup, with 9.7 GiB free: `make check`,
`make evidence`, every replay target above, `make editorial-check`,
`make icml-artifact-check` and the reviewed-build format check passed with no
tracked change. `make check-all` and the Korean build were not rerun. With less
than 5 GiB free, 10 mocked-collector tests stop at the storage reserve (see
[test scope](../tests/README.md)).

Earlier receipts: the [2026-09-15 full-length validation](../reports/paper_editorial_review_v1/final_update/VALIDATION.json)
and the [2026-09-21 ICML review verification](../reports/icml_review_v1/round_04/verification.json).
