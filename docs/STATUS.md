# Current status — 2026-10-03

LatentArtBench asks what a painter's name adds to a text-to-image prompt: a change shared by
all painter names, or differences that match the differences between the painters. The first
six-model experiment (four Impressionists) was collected on 2026-09-11. On 2026-10-02/03 the user
approved a **second collection** with two further painter groups (`painter_specificity_v3`),
collected on 2026-10-03.

**Spending.** Recorded charges: $112.293676 before the second collection, plus $72.93 in it, about
**$185.22** in total. The second collection's accounting closes at $195.22 because two gateway
errors without a reported charge keep their $5 reservations. The user set its cumulative ceiling
at $200 and raised it to $220 during collection (`psv3-r1/ceiling_amendment.json`). No further
paid request is authorized.

On 2026-09-30 the user retargeted the paper to **TMLR**. On 2026-10-02/03 the user asked for more
painters, chose the groups, and asked to generate the images and update the whole analysis and
paper; the user approved committing the work ("Commit everything").

## Manuscripts

| Manuscript | Source | State |
| --- | --- | --- |
| **TMLR submission** (lead) | [paper/tmlr/main.tex](../paper/tmlr/main.tex) → `output/pdf/latent_art_bench_tmlr.pdf` (local, not in Git) | *Proximity Is Not Specificity: What Painter Names Add in Text-to-Image Generation.* 38 pages. Anonymous, official TMLR style. Every table and figure except one image panel is generated, and all 225 quoted numbers are checked in their sentences (`make tmlr-check`). Revised on 2026-10-03 for the second collection. Six earlier subagent review rounds ([reports/tmlr_review_v1](../reports/tmlr_review_v1/README.md)) ended at minor revision without passing the rubric. A new round of the revision ([reports/tmlr_review_v2](../reports/tmlr_review_v2/README.md), round 1) gave three minor revisions without a pass: the closeness claim is too strong, and four factual errors were confirmed. The revision it calls for has not been made |
| Korean translation of the TMLR manuscript | [paper/tmlr_ko/main.tex](../paper/tmlr_ko/main.tex) → `output/pdf/latent_art_bench_tmlr_korean.pdf` (local, not in Git) | 39-page translation of the current sources, made by an AI assistant at the user's request and updated on 2026-10-03; not yet read by the user. `make tmlr-ko-check` verifies its numbers against the English text |
| Full-length paper | [paper/archive/full_length_2026-09-15/](../paper/archive/full_length_2026-09-15/) | Frozen 23-page version of 2026-09-15 |
| Korean translation of the full-length paper | same folder | Frozen 26-page translation of the full-length paper (the user's work) |
| ICML-format draft | [reports/icml_review_v1/round_04/input/](../reports/icml_review_v1/round_04/input/) | Retired on 2026-10-01 |

All review scores are internal language-model assessments of exact PDF snapshots, not human
evaluation, journal decisions or evidence of scientific validity.

## Main findings (TMLR manuscript)

**First collection.** Six configurations (GPT Image 1, GPT Image 2, GPT Image 2.5 Flare and
Sunburst, Nano Banana 2, FLUX.2 Max) × 14 scenes × six clauses × two repeats = 1,008 images,
against 649 reference reproductions of Monet, Sisley, Pissarro and Cézanne.

- Beyond a generic oil-painting clause, 66.7–88.4% of the squared change the names add is shared
  by all four names; a faithful imitator would share 84.8–95.2%.
- In CLIP and CSD the shared term supplies most of the proximity gain (54.2–83.8%) and drives the
  differences between configurations.
- By direction (alignment ratio) GPT Image 2 is best in all three representations; the error D
  ranks configurations differently per representation.

**Second collection** ([protocol](../studies/painter_specificity_v3/PROTOCOL.md),
[report](../reports/painter_specificity_v3/REPORT.md)). The same six configurations and 14 scenes,
ten clauses (no clause, generic, eight names), two repeats: 1,678 of 1,680 images (two safety
refusals). Groups: a **century group** (Jacob van Ruisdael, Canaletto, Vincent van Gogh, Ernst
Ludwig Kirchner) and the **Hudson River School** (Albert Bierstadt, Frederic Edwin Church, Thomas
Cole, Asher Brown Durand), with 788 reference works chosen by the four-painter rules.

- Both prespecified tests are supported in every representation. H1: the century group's shared
  fraction is 72.7 points lower (17.7–29.5% against 89.4–98.6%; 95% interval 62.6–76.5). H2: across
  the 28 painter pairs, name distance tracks reference distance (Spearman 0.85 / 0.86 / 0.92 in
  features / CLIP / CSD; exact p < 0.001).
- Generators reproduce the century painters' differences in direction and near their size
  (β 0.84–1.29, recognition 72–90%), the Impressionists' in part, and the Hudson River painters'
  barely (β about 0, recognition 29–50%). The shared term carries 93–98% of the proximity gain for
  the Hudson River School but 7–49% for the century group.
- Identical no-clause and generic requests did not change between the two collections beyond
  repeat noise.
- Caveats: closeness is confounded with how familiar the names are; the Hudson River panels are
  small (36–92 works); the second collection was added after the first results (its tests were
  fixed beforehand).

## Analyses added on 2026-10-01 to 2026-10-03

| Analysis | Result |
| --- | --- |
| [TMLR diagnostics v1–v5](../docs/ANALYSES.md) | Benchmarks, intervals, genuine-painting controls, content-matched targets, direction-only agreement for the first collection (post-result plans) |
| [Painter specificity v3](../reports/painter_specificity_v3/REPORT.md) | Prespecified analysis of the second collection: H1 and H2, per-group estimators, drift |
| [TMLR diagnostics v6](../reports/painter_tmlr_diagnostics_v6/REPORT.md) | Shared-fraction intervals, recognition and proximity for the two groups (plan fixed before measurement) |

## Decisions waiting for the user

1. **Revision after review.** Round 1 of the second review series
   ([triage](../reports/tmlr_review_v2/round_01/triage.md)) found the second collection's closeness
   claim too strong. By the faithful benchmark, closeness accounts for about 31 of the 72.7 points.
   The Impressionists and the Hudson River School are equally close, yet 21 points apart. "Near their
   size" for the century group holds only along the reference pattern. The round also confirmed
   four factual errors and found prespecified v6 readouts unreported. All of this needs text and
   table edits only; reporting H2 within pair types would need a short plan first.
2. **Submission.** Whether and when to submit to TMLR. The main text is now longer than 12 pages,
   so declare a long submission or move material to the appendix. Build the anonymous supplement
   with `SUPPLEMENT_IDENTIFIERS='<names>|<handles>|<email fragments>' uv run --locked python paper/tmlr/make_supplement.py`
   (100 files, about 70 MiB, scanned for identifiers).
3. **Anonymity and the public repository.** The GitHub repository carries the sources under the
   author's name; consider making it private during review.
4. **Generated images.** Whether to release the 2,686 generated images of both collections.
5. **AI-use statement.** Confirm or edit the manuscript's statement.
6. **Optional evidence.** A fictitious-name or group-clause control would separate movement toward
   a group from a generic artist-name effect; a less famous distant group, or a famous related
   group, would separate closeness from familiarity. Each needs a new budget.

## Verification

See [tests/README.md](../tests/README.md#verification-history) for the latest record of check
targets after the 2026-10-03 revision.
