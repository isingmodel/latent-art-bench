# Current status — 2026-10-01

LatentArtBench asks what a painter's name adds to a text-to-image prompt: a change shared by
all painter names, or differences that match the differences between the painters. The primary
six-model experiment was collected and measured on 2026-09-11. Everything since is
**retrospective analysis of retained data**: no images have been generated or acquired, and no
paid request has been made. Recorded cumulative paid accounting is **$112.293676**, under the
user's ceiling of strictly below $120.

On 2026-09-30 the user retargeted the paper to **TMLR**, retired the ICML draft, asked for the
`paper/` folder to be cleaned, and asked for subagent reviews with revision until the review
rubric passes.

## Manuscripts

| Manuscript | Source | State |
| --- | --- | --- |
| **TMLR submission** (lead) | [paper/tmlr/main.tex](../paper/tmlr/main.tex) → `output/pdf/latent_art_bench_tmlr.pdf` (local, not in Git) | *Proximity Is Not Specificity: What Four Painter Names Add in Text-to-Image Generation.* Anonymous, official TMLR style. Every table and figure except one image panel is generated, and all quoted numbers are checked (`make tmlr-check`). Six subagent review rounds ([reports/tmlr_review_v1](../reports/tmlr_review_v1/README.md)): all three reviewers at minor revision from round 2 on; the rubric (both criteria *yes* from all three, no factual error) was not met by round 6, the last allowed. The current sources include an unreviewed final revision addressing round 6 |
| Korean translation of the TMLR manuscript | [paper/tmlr_ko/main.tex](../paper/tmlr_ko/main.tex) → `output/pdf/latent_art_bench_tmlr_korean.pdf` (local, not in Git) | 33-page translation of the current TMLR sources, made by an AI assistant on 2026-10-01 at the user's request and not yet read by the user. Same tables and figures; `make tmlr-ko-check` verifies that its numbers match the English text. Labels inside figures and prompt texts stay in English |
| Full-length paper | [paper/archive/full_length_2026-09-15/](../paper/archive/full_length_2026-09-15/) | Frozen 23-page version of 2026-09-15 |
| Korean translation of the full-length paper | same folder | Frozen 26-page translation of the full-length paper (the user's work) |
| ICML-format draft | [reports/icml_review_v1/round_04/input/](../reports/icml_review_v1/round_04/input/) | Retired on 2026-10-01; round-04 AI review 6, 6, 4 |

All review scores are internal language-model assessments of exact PDF snapshots, not human
evaluation, journal decisions or evidence of scientific validity.

## Main findings (TMLR manuscript)

Six configurations (GPT Image 1, GPT Image 2, GPT Image 2.5 Flare and Sunburst, Nano Banana 2,
FLUX.2 Max) × 14 scenes × six clauses × two repeats = **1,008 images**, compared with 649
reference reproductions of Monet, Sisley, Pissarro and Cézanne in 31 color, spatial and texture
features and in CLIP and CSD embeddings.

- Beyond a generic oil-painting clause, 66.7–88.4% of the squared change the names add is shared
  by all four names. This is **not** by itself a lack of specificity: a faithful imitator starting
  from the same generic outputs would share 84.8–95.2%, and a generator with exact reference
  painter differences 57.6–84.2%.
- In CLIP and CSD, the shared change supplies 73.2–83.8% and 54.2–79.7% of the gain in mean
  similarity to the prompted painter's works, within −2.8 to +6.5 points of a faithful imitator
  (scene interval above 50% in 11 of 12 configuration–encoder pairs), and differences in gain
  between configurations follow the shared term (CLIP: identical ranking; CSD: r = 0.95).
  Proximity gain mostly measures shared movement.
- Specificity is read from the between-name differences, separating direction from size. By
  direction (alignment ratio), every configuration aligns positively and GPT Image 2 is best in
  all three representations, consistent with recognition. The error D, which also penalizes size,
  ranks them differently per representation: in the 31 features GPT Image 1, Flare and Sunburst
  are above a no-distinction generator (97–98% of their error off the reference pattern); in CLIP
  GPT Image 1 is lowest; in CSD four errors are resolved below 1 and none above. Content-matched targets leave
  the embedding orderings unchanged. The 31 features separate genuine Monet and Sisley works
  poorly. Genuine paintings sampled with distinct works score below every configuration on
  average in all three representations.
- Proximity, agreement and recognition favor different configurations, even within CLIP alone.
  Texture is less shared than color (99.7% of paired resamples); texture versus spatial is
  unresolved.
- A separate 2,000-image SD-Turbo collection is majority-shared overall but not in texture.

## Analyses added on 2026-10-01

| Analysis | Result |
| --- | --- |
| [TMLR diagnostics v1](../reports/painter_tmlr_diagnostics_v1/REPORT.md) | Faithful-imitation benchmark, direction of the shared change, feature-family and weighting sensitivity, readout stability |
| [TMLR diagnostics v2](../reports/painter_tmlr_diagnostics_v2/REPORT.md) | Exact-differences benchmark, scene and reference intervals, pair intervals, joint resampling of D, 31-feature separability, SD-Turbo benchmarks |
| [TMLR diagnostics v3](../reports/painter_tmlr_diagnostics_v3/REPORT.md) | Genuine-painting controls with distinct works in all three representations (the earlier control drew with replacement), CLIP/CSD agreement intervals, normalized-prototype shares, paired feature-family contrasts |
| [TMLR diagnostics v4](../reports/painter_tmlr_diagnostics_v4/REPORT.md) | CLIP/CSD agreement against content-matched class targets: errors change by at most 0.037, orderings unchanged |
| [TMLR diagnostics v5](../reports/painter_tmlr_diagnostics_v5/REPORT.md) | Direction-only agreement: GPT Image 2 best in all three representations; error split along/off the reference pattern; embedding Student intervals and repeat-dependence thresholds; proximity correlations with intervals; configuration distinctness |

All five plans record the values that review subagents had computed before the analyses ran.

## Decisions waiting for the user

1. **Submission.** Whether and when to submit to TMLR through OpenReview. The main text is
   about 13.3 pages, so declare a long submission or cut about a page. Build the anonymous
   supplementary archive with
   `SUPPLEMENT_IDENTIFIERS='<names>|<handles>|<email fragments>' uv run --locked python paper/tmlr/make_supplement.py`
   (about 54 MiB). The packager is no longer included in the archive, and it refuses to write if
   any file, decompressed `.gz`, PDF or the written zip contains an identifier.
2. **Anonymity and the public repository.** The GitHub repository contains the manuscript sources
   under the author's name; TMLR forbids linking the submission to named versions. Consider making
   the repository private during review.
3. **Generated images.** Whether to release the 1,008 images (anonymized host now, or on
   acceptance). Reviewers asked for this.
4. **AI-use statement.** The manuscript states that AI assistants were used for code, the
   reference-source audit and editing, and that the authors checked all results; confirm or edit.
5. **Optional evidence.** A human check of the 131 AI-proposed crops and of a sample of the 230
   AI content-label disagreements; a prospective control with stylistically distant painters, a
   fictitious name or a group clause, and a time-separated third repeat (the unapproved
   family-control plan would need a budget above $120).
6. **Another review round.** The final revision after round 6 is unreviewed; a seventh round would
   need the rubric's six-round limit lifted.

## Verification

On 2026-10-01, all 22 offline check targets gave identical results before and after removing the
ICML sources and cleaning `paper/`. After the final (post-round-6) revision, `make check` passes
(1,251 + 141 tests), as do `evidence`, `retrospective-check` (including diagnostics v3–v5),
`extensions-check`, `artifact-check`, `figures-check`, `paper-archive` and `tmlr-check` (29
generated files, 183 claims, each checked in its sentence context). The supplement rebuilds at
72 files, 54.4 MiB, with no identifier found by the packager's scan or an independent re-scan.
