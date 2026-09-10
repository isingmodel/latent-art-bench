# Actual clause addendum: fresh local replay

**Passed.** This is a fresh **local** extraction and installed-environment check
of the actual final `pcrv1-20260910` combined archive. It is not an anonymous
download, public-release verification or cross-platform reproduction.

The verifier is maintainer-run LLM Reviewer 2, who implemented both clause
collectors/workflows and related tests and earlier geometry/centering components.
The verifier reviewed but did not implement the public adapter. This execution
was separate from the build, on the same maintainer's machine; it is not
independent human or institutional verification. No source, scientific result,
archive or existing evidence was changed. No generation or image re-extraction
was performed.

## Exact artifact and environment

- Archive: `tmp/paper-clause-release/final-01/pcrv1-20260910.tar.gz`
- SHA256: `6038da2daed74e6ed4b509464dc6f1a4dae386e644d265235de982db4bf23e40`
- Size: **1,500,356 bytes**; **85 regular archive files**.
- Export source: `39a0bce028956f3ddf972f3dbaffe5171e0f6027`.
- Final build/export commit: `c73874e7157e61d406d376d05e6cb383ada5d38f`.
- Fresh extraction: `tmp/paper-clause-local-replay-20260910/fresh-01/pcrv1-20260910`.
- Platform: macOS 26.6.2, Darwin 25.6.0,
  arm64; Python **3.13.11**.
- The unchanged lockfile installed **44 packages** in a new `.venv`. Package
  versions and the uv/Git versions are recorded in `LOCAL_REPLAY.json`.

The archive checksum and sibling checksum file were checked before extraction.
All members had unique safe relative paths and were regular files, without
symlinks or hardlinks. Standard-library verification ran before the environment
was installed and verified all 85 files. The original final build stage was not
used as this execution environment.

## Executed commands and results

All commands ran in the fresh extraction directory. For pre-install verification,
the first command selects the already available Python 3.13.11 interpreter in
the retained checkout, with `-I -S` to disable user/site-package dependencies.
Installation, numerical replay and the four-path optional test command otherwise
match the archive README exactly.

```sh
../../../../.venv/bin/python -I -S tools/paper_clause_release.py verify --root .
uv sync --locked --python 3.13.11 --extra analysis --extra dev
uv run --locked python tools/paper_clause_release.py check --root .
uv run --locked pytest -q --import-mode=importlib tests/test_paper_clause_release.py tests/painter_clause_validation_v1/test_analysis.py tests/painter_clause_validation_v1/test_precision.py tests/painter_clause_successor_v1/test_analysis.py
```

| Step | Exit | Measured command seconds |
| --- | ---: | ---: |
| stdlib_verify_before_install | 0 | 0.285 |
| locked_fresh_environment_install | 0 | 0.548 |
| unchanged_public_numerical_report_replay | 0 | 23.192 |
| exact_readme_optional_four_path_tests | 0 | 74.436 |

The public check returns `exact_numeric_and_report_replay`. Each cohort remains
separate, with exact numerical JSON and Markdown replay:

| Cohort | Allocated slots / measurement-status rows | Primary state | Views | Numerical SHA256 |
| --- | ---: | --- | ---: | --- |
| Original `pcvv1-20260910` | 288 / 864 | Both comparisons withheld by the original collection contract | 6 | `5580d9699ce15b69a47556bf80d0fd0e986810cfd18f4f0da013c9b23a52a2b2` |
| Successor `pcsv1-20260910` | 96 / 288 | One available Cezanne/generic comparison | 3 | `00ab620f5c3e67b6fcac16cc8e4456504a3001e7a82a2524b8c58fcacfe9deb8` |

The original identity flag remains false and its unavailable endpoints are not
restored or pooled with the successor. Its retained Holm value 1 is unavailable
family bookkeeping, not a computed p-value. The successor retains its single
.025 threshold and its original result/report bytes.

The exact README optional test command passes: **152 passed, 8 explicitly
skipped in 72.76 seconds**. The eight skips are one pending-export case,
four original terminal-wrapper cases and three successor terminal-wrapper cases,
whose full maintainer workflow dependencies are intentionally excluded. Those
cases are not represented as passing public tests; their local qualification is
reported separately. Git is used by optional synthetic provenance fixtures.

After all commands, all **85 original archive payloads remain byte-identical**
in the extraction, and the archive hash and byte count still match. Runtime
installation/test caches are additional local files, not replacement payloads.
Detailed commands, exit codes, normalized stdout/stderr, platform versions,
source/provenance and both report hashes are in [LOCAL_REPLAY.json](LOCAL_REPLAY.json).

## Scope limits

This new environment used the existing host and local uv cache. No anonymous
network retrieval or separate operating-system verification was performed.
Dependency installation is separate from the local numerical replay. The
numerical package contains no private response/image workspace or Git history;
its replay does not re-extract or authenticate absent pixels, remote model
identity or acquisition provenance. Same-platform exactness does not establish
cross-platform floating-point equality, independent investigators or perceptual
validity. Publication and anonymous download/replay are separate coordinator
steps, with their own evidence records.
