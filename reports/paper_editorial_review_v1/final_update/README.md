# Final editorial update and repository cleanup

On 2026-09-15 the user requested one last revision and repository cleanup,
keeping only `main`, then explicitly removed the manuscript length limit.
This update follows [paired evaluation 04](../paired_review_04/README.md).
The earlier 8.0625 Claude and 8.8125 Astra scores concern PDF
`4dd19f7d77d63eb17e7708d566607c3c001c7c8bc9afda84a5c297d93e7005b2`;
they do not grade this later manuscript. No new review or human evaluation was run.

## Accepted editorial changes

- The abstract identifies calibration's object as measured painter contrasts.
  Its length remains 151 words.
- Section 5.4 introduces scene-by-scene error, error after scene averaging and
  held-out calibrated error before explaining the changed model ordering.
- Table 3 now shows all six corrected shared/generic cosines and squared-size
  ratios. These are presentations of existing diagnostic records, explicitly
  labeled retrospective; the primary shared-change percentages are unchanged.
- Section 5.2 explains why a response common to the names need not equal the
  generic painting response. Their squared components cannot be attributed as
  independent contributions because the additional naming shift has a cross term
  with the generic shift.
- The conclusion specifies the artist-free baseline and includes the painting
  clause in the shared change. Main-text pointers identify the model-version
  verification limit and separate historical experiments.
- Repeated prose is reduced selectively. The figure overview/detail views,
  all four painters, inferential boundaries and source limitations remain.
  Removing an unnecessary forced page break improves the closing page flow.

The user removed the page cap; the revised PDF is 23 pages. Font size and margins
are unchanged. The extra explanations and table rows were not compressed to
preserve the earlier page count.

The host did not adopt suggestions that would call the whole common shift a
name effect, omit “squared” from the magnitude ratio, equate beta with the
between-name share, or collapse the model overviews without preserving their
different means and Cézanne positions. See the fact checks beside the raw `_04`
reviews. An additional read-only agent check verified all 12 new table cells
against the retained diagnostic JSON and checked the interpretation; it did not
assign editorial scores.

## Repository organization and preservation

The root, paper, report, status, handover and analysis guides now identify the
current entry points, image builders and historical records consistently.
`make editorial-check` runs the new portable archive audit without contacting
models. The [archive guide](../ARCHIVE.md) documents the preserved raw reviews,
hashes, arithmetic and optional verification of local snapshots.

All 99 original reviews and six completed external reviews remain. Narrow ignore
rules exclude bulky CLI transport traces and machine-local runners while leaving
their bytes intact. Frozen manuscript snapshots are explicitly protected by the
[artifact retention guide](../../../docs/ARTIFACTS.md). Scientific source,
protocols, measurements, results, image ledgers and retained pixels are unchanged.
Two historical unified-diff files retain their required blank context-line
spaces; exact-path `.gitattributes` rules exempt those spaces from trailing-space
checks without rewriting the archived patches.

Only `main` remains locally and on the remote. The remote already contained only
`main`; fetching with pruning removed nine obsolete local remote-tracking refs.
There were no secondary worktrees or unique branch work to discard.

[Final snapshot](FINAL_SNAPSHOT.json) binds the manuscript and presentation
sources. [Validation](VALIDATION.json) records final checks and their limits.
