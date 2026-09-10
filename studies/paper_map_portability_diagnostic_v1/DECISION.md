# Diagnose the failed public map replay

10 September 2026. Scope: software diagnosis using already public numerical
inputs, under the active paper/analysis revision and public-reproducibility goal.
This is not a new scientific study, allocation qualification or image census.

## Problem and preserved predecessor

The original strict Ubuntu run [34474649751, attempt 1](https://github.com/isingmodel/latent-art-bench/actions/runs/34474649751)
failed before observed E/Q replay. Its checker raises a generic exception after
comparing the reconstructed 27-cell qualification object, without retaining that
object or the differing field. The complete log therefore cannot identify the
cause. The original run, workflow commit `f38da21b7ea1c49b5cb5c1678a8410c65df19733`,
archive and comparison contract remain unchanged and closed.

This separate diagnostic is `pmpdv1-20260910` under
`paper_map_portability_diagnostic_v1`. It uses the unchanged `pmv2r-20260910`
archive, SHA-256
`8688085fe001e6b45ca34f6d39a5979e3e762a2678cd5ecb8169a698defb4eb6`.
The archive contains 74 regular files; the frozen public checker SHA-256 is
`a97ee3fa87a219949c5695f5949cdda9704e8124ba9ebae6649d97fb21779015`.
No new scientific or public-replay tolerance is selected here.

## Diagnostic operations

1. Verify the complete immutable archive and module bindings before numerical
   imports, using the unchanged public verifier.
2. Call the original qualification computation in memory once. Save its complete
   reconstructed object outside the extracted archive. Compare every leaf using
   the original comparator: floating-point absolute/relative tolerance 1e-10;
   exact identities, counts, seeds, decisions and reconstructed support hashes.
   Also expose exact floating discrepancies without treating them as failures
   when the existing contract tolerates them. Retain all mismatches, not just
   the first one.
3. Separately invoke the original observed-analysis replay even if qualification
   differs. Save that result and report outside the archive. Report exact parity
   with the published observed result/report. Any additional descriptive float
   comparison is explicitly separate from the unchanged exact observed contract;
   it cannot convert a failed exact check into a pass.
4. Record input/module/script fingerprints, runtime versions and numerical
   backend information, and verify all 74 archive files again. Record exceptions
   and unreached steps without silently substituting an output.

The tool is read-only with respect to its archive and writes only to a new
diagnostic directory. It does not call formal qualification writers, collectors,
image decoders or feature extraction, nor change any retained result, map, proxy
law, seed, allocation, report or hash. Scientific endpoint analysis is replayed
unchanged, not replaced by an alternative estimator.

## Execution and interpretation

Comparator tests run offline. One local diagnostic establishes the diagnostic's
behavior on the known runtime. One separately named hosted diagnostic uses a new
sanitized public branch and disjoint run/output paths on Ubuntu 24.04 with the
same pinned Python/dependency versions as the failed predecessor. Its workflow
may use the existing registered dispatch entry point on that new branch; it does
not rerun or amend the predecessor's attempt or branch. Only already-public
archive data and the allowlisted diagnostic source/workflow are published.

Successful diagnostic completion means that the comparisons were recorded. It
does not mean that the original strict replay passed, that the reconstructed
support laws are byte-identical, or that actual-service uncertainty/capture
validity has been established. No cause is assumed before the actual differences
are inspected. In particular, floating support hashes are a possible failure
site, not the presumed sole explanation.

Any remedy must be proposed separately after diagnosis, with its numerical
contract stated explicitly and without changing this diagnostic or the failed
predecessor. No additional image sampling or scientific allocation assessment
is authorized by this software work. The analysis and all reviews remain
maintainer-run LLM work, not replication by independent investigators.
