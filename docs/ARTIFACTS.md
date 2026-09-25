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

Git does not back up these files. Some are referenced by committed records.

| Location | Contents |
| --- | --- |
| `research_workspace/` (22 GB) | Original responses, generated images, failed requests, reference displays, transport bodies and locks; the SD-Turbo and six-model pixel checks read it |
| `artifacts/` | Retained model weights and source checkouts |
| `output/pdf/` | `latent_art_bench_icml.pdf` (identical to the round-04 reviewed PDF) and `latent_art_bench_korean.pdf` (hash recorded by the 2026-09-19 and 2026-09-21 review reports) |
| `output/artifacts/` | The final numerical bundle and two candidate archives, each bound by a record in [numeric_bundle_v1/](../reports/icml_review_v1/numeric_bundle_v1/README.md) |
| `reports/icml_review_v1/*/input/`, `post_round_*/`, `resume_2026-09-21/before_revision/` | Exact reviewed PDFs and figure copies, ignored by the PDF rule |
| `reports/paper_editorial_review_v1/*_review_*/` | Editorial CLI traces and runners, listed with digests in the [archive guide](../reports/paper_editorial_review_v1/ARCHIVE.md) |
| `tmp/pdfs/`, `tmp/paper/`, calibration files under `tmp/` | Hash-bound inputs and frozen reviewed manuscript snapshots despite the temporary-looking path |

Before migrating or removing unique bytes, create a checksum inventory and a
separate archive. Never run broad cleanup such as `git clean -xfd`.

### Local inventory, 2026-09-23

`tmp/` holds 9.2 GB. About 1.6 GB is 2026-09-10 clause-release test and review
staging (`tmp/paper-clause-adapter-*`, `tmp/paper-clause-combined-*`) that no
tracked file references. QA render folders (`tmp/*-qa`, `tmp/r3_contribution_render`)
and dated 2026-09-05 to 09-08 logs are also unreferenced. They were **not deleted**:
an unreferenced path can still hold the only copy of an intermediate, and
deletion needs an inventory and the user's approval. Test caches, `__pycache__`
and `.DS_Store` files are disposable.

## Retired documentation

Superseded navigation documents are retired to Git history; the records they
summarize stay in place.

| Cleanup | Change | Previous tree |
| --- | --- | --- |
| 2026-09-13 | Removed superseded review rounds, the initial unbound proposal, duplicate feature-distance guidance and redundant report/release prose | `cc764fe` |
| 2026-09-23 | Merged `docs/ARCHITECTURE.md` into the [analysis catalog](ANALYSES.md); renamed `docs/INDEX.md` to [docs/README.md](README.md); rewrote the navigation documents for the ICML-era state | `aae2314` |

```bash
git show cc764fe:docs/RESEARCH_PROPOSAL_20260906.md
git show aae2314:docs/ARCHITECTURE.md
```

Manuscript build folders, page previews under `tmp/paper/`, test/lint caches,
bytecode and operating-system metadata are disposable when unused. Inspect the
exact target first, and keep the frozen reviewed snapshots under `tmp/paper/`.
`tmp/paper/icml-resume-build/` holds the build that produced the round-04 reviewed
PDF; `tmp/paper/icml-build/` receives fresh builds and still holds a round-03-era
build. `make icml-format-check` reads either one.
