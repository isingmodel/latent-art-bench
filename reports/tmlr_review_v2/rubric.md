# TMLR-style review rubric, second record (AI reviewer simulation)

Frozen on 2026-10-03, before the first review of the TMLR manuscript revised for the second
collection (`paper/tmlr/main.tex` at commit `8ab2a67`). Every reviewer in this record is a
language-model subagent started fresh for one review. These reviews are an internal quality
screen, not TMLR decisions, and do not predict acceptance.

The first record ([`reports/tmlr_review_v1`](../tmlr_review_v1/README.md)) used its six allowed
rounds without passing. The manuscript was then extended with a second collection (two further
painter groups, `studies/painter_specificity_v3`), which the owner approved and paid for after
the first record closed. On 2026-10-03 the owner asked for a new review round of this revision.
This record keeps the first rubric's criteria, form, roles and pass criterion unchanged; the
differences are listed at the end.

## What reviewers judge

TMLR accepts a submission when both questions have a positive answer
([acceptance criteria](https://jmlr.org/tmlr/acceptance-criteria.html)):

1. **Claims and evidence.** Are the claims made in the submission supported by
   accurate and convincing evidence? Any gap between claims and evidence must be
   named, with what would close it (more evidence or narrower claims).
2. **Audience and clarity.** Would some individuals in TMLR's audience be
   interested in the findings, and does the paper communicate them clearly?
   Novelty or expected impact are not grounds for rejection at TMLR.

Reviewers also act as an action editor screening for **desk rejection**: out of
scope, format violations, poor quality, or a paper that reads as largely
machine-generated with low care (TMLR states such submissions are examined
closely).

## Review form

Each reviewer writes `reviewer_<role>.md` and `reviewer_<role>.json` in the round
folder, with: summary of contributions; strengths; weaknesses with page/section
locations; requested changes, each labelled *critical* (must change for
acceptance) or *minor*; answers to criteria 1 and 2 (`yes`, `partially`, `no`);
desk-rejection risk (`none`, `low`, `high`) with reason; recommendation
(`accept`, `minor revision`, `major revision`, `reject`); confidence 1–5; and the
SHA-256 of the PDF read.

Reviewers read the complete frozen PDF. They may inspect the supplementary
material a TMLR reviewer would receive: `paper/tmlr/` (sources, generated tables,
`build_assets.py`), the analysis outputs it reads under `reports/` and
`data/manifests/`, the protocols and plans under `studies/`, and `src/`. They must
not read earlier reviews of this or any other manuscript (`reports/tmlr_review_v1/`,
`reports/tmlr_review_v2/` other than their own round's input and their own output,
`reports/icml_review_v1/`, `reports/paper_editorial_review_v1/`, `critics/`),
status or handover documents under `docs/`, or any stated score target. They
must not modify any file other than their own two outputs.

## Roles

- **methods**: statistics and estimators; checks that every claim is supported
  and that numbers match the evidence; reproducibility.
- **empirical**: generative-model evaluation researcher; positioning against the
  literature, whether the experiments support the conclusions, alternative
  explanations.
- **editor**: TMLR action-editor view; desk-rejection screen, clarity for the
  intended audience, structure, length, figures and tables, format compliance.

## Pass criterion

A round passes when all three fresh reviewers of the same frozen PDF answer
`yes` to both criteria, recommend `accept` or `minor revision`, report
desk-rejection risk `none` or `low`, and no reviewer reports a factual error
that the revision author confirms. Minor requested changes from a passing round
are then applied without a new scored round, and the final manuscript is rebuilt
and re-checked.

Between rounds, revisions may change wording, structure, claims and presentation,
and may add analyses of already retained data. They may not add image
generation, paid requests or human evaluation. A new round uses three new
reviewers, and every earlier review stays in this record.

## Differences from the first rubric

1. **Round limit.** The first rubric allowed at most six rounds. In this record a round runs
   only when the owner asks for it, and each request is noted in the round's record.
2. **Earlier reviews.** Reviewers may read neither record's earlier reviews.
3. **Supplementary material.** It now includes the second collection's protocol, reference
   rules and records (`studies/painter_specificity_v3/`, `data/manifests/painter_specificity_v3/`)
   and the plan of its readouts (`studies/painter_tmlr_diagnostics_v6/`).
