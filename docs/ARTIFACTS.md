# Artifact retention

Keep material needed to understand, reproduce or audit a scientific result.
Use Git history for superseded editorial discussion. A file's age, extension or
ignored status alone does not determine whether it can be removed.

## Scientific evidence

Preserve the original paths and bytes of protocols, fixed plans, configurations,
bound source/tests, measured vectors, request ledgers, receipts, numerical
reports and their plots. These live chiefly in `studies/`, `configs/`,
`data/manifests/`, `src/`, `tests/` and `reports/`. The
[results index](../reports/README.md) and [analysis catalog](ANALYSES.md) provide
navigation without moving those dependencies.

Completed outputs may bind both code and prose. In `docs/`, the
[mechanism proposal](RESEARCH_IDEA_20260908.md) and
[methodology revision plan](reviews/20260907_methodology/REVIEW_AND_REVISION_PLAN.md)
are hash-bound inputs. The plan's three source reviews remain linked provenance.
The current diagnostic [analysis.json](../reports/painter_specificity_review_v1/analysis.json)
also binds its own source, plan and inputs. Do not rewrite these to make checks
pass. Scientific corrections belong in a separate result version.

Failures, exclusions and contrary findings remain part of the record. In
particular, the stopped specificity attempt, incomplete clause experiment,
failed map qualification and failed strict Ubuntu replay are retained. Earlier
release archives and publication receipts remain unchanged. Numerical replay
does not authenticate absent pixels or validate perceptual style.

## Unique local material

- `research_workspace/`: original image responses, generated images, failed
  requests, normalized reference displays, transport bodies and execution locks.
- `artifacts/models/` and `artifacts/sources/`: retained weights and source
  checkouts that Git does not back up.
- `tmp/pdfs/` and hash-bound calibration/qualification files under `tmp/`:
  some are scientific inputs despite their temporary-looking paths.
- User work, `.env` and other local configuration. The Korean manuscript and
  latest `critics/` reviews are outside the retired-document list.

The capture audit's original ignored `attempts.jsonl` remains unchanged. Its
committed [portable view](../data/manifests/painter_capture_audit_v1/pcav1-20260910/attempts.portable.json)
retains all 44 records and original line hashes; only `transport_source_path`
on lines 11 and 12 is normalized to a repository-relative path. Terminal
bindings still refer to the original ledger. The portable view is a disclosed
derivative, not a substitute for byte verification of the local original.

Create a checksum inventory and separate archive before migrating or removing
unique research bytes. Do not use broad cleanup commands such as `git clean -xfd`.
The two existing historical evidence acknowledgements must not be expanded to
conceal new missing files.

## Retired documentation

The 2026-09-13 cleanup removes superseded review rounds, the initial unbound
proposal, duplicate feature-distance guidance and redundant report/release prose.
Their necessary conclusions and navigation are consolidated in the current
docs and results index. Numerical JSON/CSV, figures, release receipts and bound
documents retain their original bytes and locations.

The previous tree is available at commit `cc764fe12bfbef3172edf0c56f3d5fc8cff423c2`:

```bash
git show cc764fe:docs/RESEARCH_PROPOSAL_20260906.md
git ls-tree -r --name-only cc764fe docs/reviews
```

Manuscript builds, rendered-page previews under `tmp/paper/`, test/lint caches,
bytecode and operating-system metadata are reproducible disposable state when
unused. Inspect exact targets before deleting them; do not extend this rule to
an entire ignored directory.
