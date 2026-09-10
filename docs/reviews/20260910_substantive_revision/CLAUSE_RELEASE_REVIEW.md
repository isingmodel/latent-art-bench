# Bounded review of the clause numerical exporter

Date: 2026-09-10. Reviewer: maintainer-run LLM subagent Reviewer 2.

## Conclusion and disclosure

No unresolved correctness, privacy or replay blocker remains in the reviewed
**provisional, synthetic-tested** exporter contract. This conclusion qualifies
the packaging implementation for subsequent real-data verification; it is not
verification of an actual scientific export or public release.

The actual OAuth collection was still running when this report was written.
**No real terminal export, final scientific archive, publication, anonymous
download/replay or cross-platform result check was performed in this review.**
The coordinating maintainer's full-suite run and final source commitment were
also pending. No manuscript score is assigned or changed.

I did not implement or edit the exporter, its tests or its guide. I reviewed
Reviewer 1's implementation and requested corrections. I previously implemented
the clause study's collector/workflow and parts of the geometry/centering
analyses, and helped repair its precollection gates. This is consequently not
an independent review of the whole scientific system. Both author and reviewer
are LLM agents operated by the same maintainer, not independent human or
institutional reviewers.

## Exact reviewed files

The hashes below identify the files present when this completed review was
persisted. No checks were rerun merely to write this report, and no scientific
source was altered.

| File | SHA-256 |
| --- | --- |
| `tools/paper_clause_release.py` | `699cb7e3a13c82a42357c79e58ad5b0336a0115070e109b687b316f0ff5e872f` |
| `tests/test_paper_clause_release.py` | `a13f8b1dde723800df4b4a817311081e9b97879dd3b9875987897a3b4b010c99` |
| `studies/paper_clause_reproducibility_v1/README.md` | `526a4ef735dca0ee2e47276e72b0fa9fc6c696d174c044d0e8ed5b854e3b29b5` |

## Contract examined

The local exporter first calls the unchanged sealed workflow to verify terminal
collection metadata, then verifies the measurement receipt, complete output
inventory and measurement/report hashes. It checks copied scientific
source/design against the recorded study freeze and commit; final exports and
builds require exact working-tree/index/HEAD bytes. Outputs are create-once.
The exporter performs no publication, generation or feature extraction.

The compact projection preserves all consumed assignment, numeric, status and
delivery fields. It drops response paths/headers and unconsumed image metadata
from measurement rows. Safe collection metadata remains verbatim because it
is part of the unchanged analysis output. Expected analysis JSON and report
must replay exactly through the unchanged `analysis.analyze` and `report_text`.
No numerical tolerance or rewritten scientific function is introduced.

The explicit allowlist contains the numeric import closure, selected additional
source for inspection, design/qualification/reviews, compact vectors and
results. Inert transport helpers imported by the unchanged common module are
included, but public replay never calls them. The full measurement/collection
dependency graph is intentionally omitted. Raw response/image bytes, proxy
contents, credentials, Git history, Korean drafts, manuscript files and other
unlisted files are excluded. Original private freeze/proxy hashes and relative
path/hash references are declared provenance; public replay does not traverse
the absent runtime workspace.

Public `verify` uses only the standard library before installation. Public
`check` verifies the package and runs numerical code without Git, proxy state,
network, response bodies or images. Checksums establish consistency relative
to a trusted archive checksum, not authenticity of absent observations. The
guide distinguishes the optional tests' Git-executable requirement and their
five maintainer-only skips from the Git-free primary replay command.

## Independent verification completed

- The 49 public source/design files required to match the scientific freeze
  were all present in that freeze and matched their recorded SHA-256 hashes.
  The static public surface contained 34 source files and 55 core files.
  Existing core content passed the privacy screen.
- A local exporter test run passed **40 tests in 28.29 seconds**, with Ruff
  clean. After the public/local test split, six targeted stdlib-verification,
  complete-primary and terminal-binding cases passed in **20.09 seconds**.
- I ran the exact three-path optional pytest command from the extracted
  synthetic stage in a fresh Python `-I` process, forcing staged source first:
  **96 passed, 5 intentionally skipped in 29.73 seconds**. A post-run assertion
  confirmed that every loaded `latent_art_bench` module came from that stage's
  `src` directory. The skips are the one pending-export case and four local
  terminal-workflow parameter cases, whose omitted dependencies are explicit.
- Isolated numerical-check tests covered both a complete 288-slot cohort,
  including both available primary contributions/p-values/Holm results, and a
  missing-generic cohort that withholds both primary tests. The six secondary
  views and report replay exactly in both cases.
- The isolated check subprocess rejected socket and subprocess audit events
  and asserted that neither the clause workflow nor collector was imported.
  Separate `-I -S` execution verified the package without site packages.
- Synthetic tests exercised explicit allowlists, path traversal, symlinks,
  credential fields, omitted private projection fields, extra files, modified
  data/bindings, create-once outputs, staged-index changes, draft hash checks,
  cached foreign scientific modules and terminal receipt/hash-chain failures.

These fixtures use artificial reference/training/outcome vectors and temporary
Git repositories. They use the real frozen design and unchanged analysis code,
but they are not observations from the running experiment. The test interpreter
and installed dependencies were already available locally; this was not a new
dependency installation or a public anonymous reproduction.

## Findings resolved during review

1. **Cached external source could mask packaged replay.** Merely prepending
   staged `src` to `sys.path` does not replace already-imported modules. Public
   check now rejects foreign cached scientific modules before and after replay,
   and isolated tests confirm the complete loaded-module origin set.
2. **The original synthetic fixture exercised only withholding.** Its missing
   generic observation withheld both primaries. A separate complete 288-slot
   fixture now checks exact available primary contributions, p-values and Holm
   results as well as all secondary output/report fields.
3. **The advertised standalone test command initially imported omitted local
   dependencies.** I reproduced a fresh staged workflow import failure for
   `painter_distribution_study_v1.measurement`. The implementation now clearly
   separates the five maintainer-only cases, retaining the minimal public
   dependency surface. The exact advertised three-path command subsequently
   passed in isolation as recorded above.
4. **Terminal gate checks needed direct adapter coverage.** Added tests exercise
   valid local terminal inputs, missing measurement outputs, changed output
   hashes and mismatched collection-receipt hashes. Public verification also
   checks the measurement-to-collection-to-original-freeze fingerprint chain
   and measured output provenance without attempting absent raw-file access.
5. **An initial test snapshot shared mutable numeric lists.** The first run had
   34 passes and one failed assertion because changing its source row also
   changed the test's saved projection. The test now makes an independent
   snapshot. Export serialization was unaffected; no scientific function was
   changed to accommodate that test.

## Remaining required work

After the real collection and measurement become terminal, export must pass
the actual sealed workflow/receipt checks, verify the real projected numbers
and report exactly, and bind the final source and export commits. The resulting
archive then needs fresh verification, installation and numerical replay, plus
the separately authorized public publication/download checks. A synthetic pass
cannot substitute for those steps or guarantee cross-platform floating-point
equality.

The separate terminal timing/identity/accounting audit remains pending the real
receipt. That audit will describe recorded collector admission spacing and
response intervals, not independently observed backend arrival times or backend
state. This packaging review makes no new claim about perceptual validity,
capture calibration, independent investigators or scientific effect sizes.
