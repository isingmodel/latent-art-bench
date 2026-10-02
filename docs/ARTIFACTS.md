# Artifact retention

Keep material needed to understand, reproduce or audit a scientific result.
A file's age, extension, location or ignored status does not decide whether it
can be removed; its bindings do. Use Git history for superseded navigation text.

## Scientific evidence

Preserve the original paths and bytes of protocols, fixed plans, configurations,
bound source/tests, measured vectors, request ledgers, receipts, numerical reports,
report plots and review records. These live chiefly in `studies/`, `configs/`,
`data/manifests/`, `src/`, `tests/` and `reports/`. The
[results index](../reports/README.md) and [analysis catalog](ANALYSES.md) provide
navigation without moving them. The [handover](AGENT_HANDOVER.md#what-must-not-change)
lists bound files that look editable and shows how to test a file for bindings.

Failures, exclusions and contrary findings are part of the record: the stopped
specificity attempt, incomplete clause experiment, failed map qualification,
failed strict Ubuntu replay and every low review score stay. Earlier release
archives and publication receipts remain unchanged. Numerical replay does not
authenticate absent pixels or validate perceptual style.

The capture audit's original ignored `attempts.jsonl` stays unchanged. Its
committed [portable view](../data/manifests/painter_capture_audit_v1/pcav1-20260910/attempts.portable.json)
retains all 44 records and original line hashes; only `transport_source_path` on
lines 11 and 12 is normalized. Terminal bindings still refer to the original.
The two acknowledged unrecoverable inputs in `evidence_acknowledgements.json`
must not be expanded to conceal new missing files.

## Unique local material

The frozen `reports/painter_prototype_transfer_v1/analysis.json` is 176,665,174
bytes and exceeds GitHub's ordinary Git file limit. Git stores its lossless
`analysis.json.gz` archive instead. Run `make restore-analysis` after cloning
to restore the ignored JSON at its original path. The helper verifies SHA-256
`e1d1fbb924feb797f67e0907677511ed7c745335a4f2827e99d2f286e6be5448`
and refuses to overwrite a differing local file. The archive preserves all
original observations, whitespace and frozen bindings. Numerical bundle tools
still package the restored original bytes; run the restore step before using them.

Git does not back up these files. Some are referenced by committed records.

| Location | Contents |
| --- | --- |
| `research_workspace/` (20 GB) | Original responses, generated images, failed requests, reference displays, transport bodies and locks; the SD-Turbo and six-model pixel checks read it. The SD-Turbo weights were deleted on 2026-09-27 (see below) |
| `artifacts/` | Retained model weights and source checkouts |
| `output/pdf/` | `latent_art_bench_tmlr.pdf` (current anonymous TMLR build; disposable) and `latent_art_bench_korean.pdf` (hash recorded by the 2026-09-19 and 2026-09-21 review reports) |
| `output/artifacts/` | The final numerical bundle and two candidate archives, each bound by a record in [numeric_bundle_v1/](../reports/icml_review_v1/numeric_bundle_v1/README.md) |
| `reports/icml_review_v1/*/input/`, `post_round_*/`, `resume_2026-09-21/before_revision/` | Exact reviewed PDFs and figure copies, ignored by the PDF rule |
| `reports/paper_editorial_review_v1/*_review_*/` | Editorial CLI traces and runners, listed with digests in the [archive guide](../reports/paper_editorial_review_v1/ARCHIVE.md) |
| `tmp/pdfs/`, calibration files under `tmp/` | Hash-bound inputs despite the temporary-looking path |

Before migrating or removing unique bytes, create a checksum inventory and a
separate archive. Never run broad cleanup such as `git clean -xfd`.

### Local inventory, 2026-09-27

`tmp/` holds 435 MB in 18 entries. Each is on the keep list above or is named by
path or SHA-256 in a record:

| Path under `tmp/` | Size | Why it stays |
| --- | --- | --- |
| `paper/` | 5 MB | Only `tmlr-build/`, the disposable output of `make paper-tmlr` |
| `pdfs/` | 347 MB | Reviewed PDFs and page renders whose digests the review records keep |
| `reference-quality/` | 70 MB | Source crops named in `reports/painter_reference_quality_v1/audit_*.json` |
| Calibration, randomization and supplement JSON files; `painter_prompt_supplement_v1/` | 5 MB | On the keep list above; `data/manifests/painter_prompt_study_v1/*/decision.json` names the calibration and randomization files, and the supplement package writes its locks in `painter_prompt_supplement_v1/` |
| `docs-cleanup/`, `editorial_r11_b.IKbcXX/`, `portable-review-audit-result.json`, `pps1-gpt-prompts-20260905/`, `ppss1-missingness-20260905/` | 9 MB | Digests in editorial records, or completion logs named by their run IDs |

On 2026-09-26, 50 unreferenced entries (1.6 GB) were packed into verified
lossless archives outside the repository, in the sibling folder
`generative_art_diff_archive/2026-09-26/`, and then removed. They were the
2026-09-10 clause test and review staging, QA render folders, the 2026-09-05 to
09-08 logs and other scratch. That folder's `README.md` summarizes each archive,
`MANIFEST.tsv` lists every file with its SHA-256, and `BINDING_TEST.tsv` records
why each `tmp/` entry was kept or archived. Git does not hold these archives.
To restore one, run this from that folder:

```bash
zstd -dc --long=27 X.tar.zst | tar -xf - -C /path/to/generative_art_diff
```

On 2026-09-27, at the owner's request, the following derived paper material and
model weights were deleted. None of it was generated result data.

- `tmp/paper/`: previews, page renders, review work folders, the round-03 and
  round-04 ICML builds, and logs.
- The six 2026-09-10 release folders (`tmp/paper-release/`,
  `tmp/paper-substantive-release/`, `tmp/paper-map-release/`,
  `tmp/paper-map-validation-release/`, `tmp/paper-clause-release/` and
  `tmp/paper-clause-local-replay-20260910/`). They held drafts, extracted bundles
  with their virtual environments, and QA renders.
- The SD-Turbo weights in `research_workspace/painter_feature_generation_v2/models/`.

Records under `studies/`, `data/manifests/` and `reports/` still name these paths
and digests; the files are gone. `generative_art_diff_archive/2026-09-27/` holds:

- `DELETED_MANIFEST.tsv`, which lists every deleted file with its SHA-256.
- A 58 MB lossless archive of the 1,121 files that existed nowhere else: paper
  drafts, LLM review requests and response streams, and release-draft records.
  Virtual environments, renders and byte copies of kept files were not archived.

Every offline check target gave the same result before and after the deletion.
The only exception is the format check of the deleted round-04 build. To
re-extract SD-Turbo features, download `stabilityai/sd-turbo` at revision
`b261bac6fd2cf515557d5d0707481eafa0485ec2` into the recorded `model_path`, then
verify it against the file digests in
[model_sd_turbo.json](../data/manifests/painter_feature_generation_v2/model_sd_turbo.json).

On 2026-10-01, when the user retargeted the paper to TMLR and asked for the ICML
templates to be removed, the live ICML draft sources in `paper/` (`icml.tex`, the
hand-written `icml_*` sections, `icml_references.bib`, `icml2026.sty`,
`icml2026.bst` and `icml_style/`), `scripts/check_icml_format.py`,
`output/pdf/latent_art_bench_icml.pdf` and `tmp/paper/icml-build/` were deleted.
Every deleted source is byte-identical to a tracked frozen copy in
`reports/icml_review_v1/round_04/input/`, and the reviewed PDF stays at
`reports/icml_review_v1/round_04/input/manuscript.pdf`. The untracked files and
the unbound checker were first copied to `generative_art_diff_archive/2026-10-01/`
with an `INVENTORY.sha256`.

The same day, at the owner's request to remove redundant files from `paper/`, the
folder was reorganized: the full-length paper and its Korean translation, with
their inputs and five figures, moved unchanged to
`paper/archive/full_length_2026-09-15/`; the two figures and the example-image
manifest used by the TMLR manuscript were copied to `paper/tmlr/figures/`; and
all presentation builders except `replay_palette.py` (14 files), the nine
generated `icml_*` tables and 18 unused figures were deleted. The presentation
checks that read them (`figures-check` except the palette figure, the builder
steps of `review-check`, `retrospective-check` and `extensions-check`,
`example-images-check` and `review-images-check`) were removed with them; the
analysis replays are unchanged. Records under `reports/` still name the deleted
paths. A complete copy of the previous `paper/` folder is in
`generative_art_diff_archive/2026-10-01/paper_before_cleanup/`, listed in
`PAPER_BEFORE_CLEANUP.sha256`, and Git history holds every tracked file. All
offline check targets were run before and after these changes; see
[STATUS.md](STATUS.md#verification).

Test caches, `__pycache__` and `.DS_Store` files are disposable.

## Retired documentation

Superseded navigation documents are retired to Git history; the records they
summarize stay in place.

| Cleanup | Change | Previous tree |
| --- | --- | --- |
| 2026-09-13 | Removed superseded review rounds, the initial unbound proposal, duplicate feature-distance guidance and redundant report/release prose | `cc764fe` |
| 2026-09-23 | Merged `docs/ARCHITECTURE.md` into the [analysis catalog](ANALYSES.md); renamed `docs/INDEX.md` to [docs/README.md](README.md); rewrote the navigation documents for the ICML-era state | `fb61bb5` |

```bash
git show cc764fe:docs/RESEARCH_PROPOSAL_20260906.md
git show fb61bb5:docs/ARCHITECTURE.md
```

Manuscript build folders, page previews under `tmp/paper/`, test/lint caches,
bytecode and operating-system metadata are disposable when unused. Inspect the
exact target first. `tmp/paper/tmlr-build/` receives TMLR builds. The reviewed
round-04 ICML PDF is preserved at
`reports/icml_review_v1/round_04/input/manuscript.pdf`, and each reviewed TMLR PDF
under `reports/tmlr_review_v1/round_*/input/`.
