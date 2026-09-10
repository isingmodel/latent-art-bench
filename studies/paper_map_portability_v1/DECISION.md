# An additive portable replay of fixed numerical inputs

10 September 2026. Software scope `paper_map_portability_v1/pmprv1-20260910`.
This decision follows the separately retained
[diagnostic](../paper_map_portability_diagnostic_v1/DECISION.md), not a new
experiment, scientific estimator or allocation qualification.

## Observed problem

The original strict Ubuntu attempt remains failed. A subsequent diagnostic
[run 34479252271](https://github.com/isingmodel/latent-art-bench/actions/runs/34479252271)
reproduces qualification-comparison failure with the unchanged public archive.
Its 27 failing leaves are precisely the 27 reconstructed support hashes. The
other 211 differing qualification floats have maximum absolute difference
3.552713678800501e-15 and satisfy the original 1e-10 absolute/relative tolerance.
All other leaves, including seeds, counts, identities and decisions, agree.

The diagnostic separately reaches the observed analysis. Its 156 differing
floats have maximum absolute difference 2.6645352591003757e-15; all other fields
agree. The exact JSON and report checks fail. The report differs only in the
full-precision component-point JSON line; the numerical table and interpretation
are unchanged. These facts describe the new diagnostic, not a recovered output
from the older run, whose reconstructed object was not retained.

## Separate contract

The unchanged `pmv2r-20260910` archive and all historical source/results remain
authoritative. This sidecar adds a different reproduction route and never makes
the old exact route pass retroactively.

1. On the already verified Mac runtime, reconstruct each of the 27 historical
   64-point joint supports with the unchanged scenario constructor. Serialize
   free then named arrays as little-endian float64, each with shape
   `(12, 64, 31)`. **Every concatenated byte hash must equal its pre-data retained
   support hash.** A mismatch stops export; no hash is refreshed. Export calls
   no Monte Carlo simulation, formal writer, generation or feature extraction.
2. Bind the binary supports, exact cell order/identities, archived sources,
   reference/map/proxy inputs and fixed simulation settings in a compact manifest.
   The binary is a reproduction input recovered from already bound supports,
   not a newly fitted law. Store large bytes in the ignored reproduction workspace
   and distribute a separate allowlisted sidecar.
3. Portable replay reads these exact arrays, constructs the original distance
   tables and calls the unchanged simulation primitive with the same R10,
   10,000 trials per cell, seeds and allocation-decision function. It never
   substitutes platform-reconstructed supports for the supplied inputs.
4. All structural fields, identities, counts, seeds, decisions and support hashes
   must match exactly. Qualification floats retain the original
   `math.isclose(rel_tol=1e-10, abs_tol=1e-10)` contract; nonfinite values fail.
5. Observed analysis uses the unchanged public replay function. **This separate
   route applies the same 1e-10 floating contract to the full observed numerical
   object**, with all nonfloating fields exact. This extends the previous
   observed contract, which required byte-exact JSON; it does not modify it.
   The tolerance already used by the project is retained, rather than estimated
   from this discrepancy or from an inferential threshold.
6. Retain exact/tolerant comparisons, every differing numerical leaf, the actual
   rendered report and its diff. Re-rendering the stored object must reproduce
   the stored report exactly, binding the formatter. Exact equality of the actual
   rendered report remains separately reported; floating-object equivalence
   cannot be described as byte-exact report reproduction.

The new route does not independently reproduce support construction on Linux.
It supplies those original finite inputs exactly and replays the subsequent
computation. No support reconstruction or new empirical endpoint is added to
the portable check.

## Verification and limits

Artificial tests cover support layout/hash/identity checks, immutable-input
guards, comparator and decision semantics, and exact versus tolerant report
claims. Export and replay use new directories, preserving any failure in place.
Fresh local and separate Ubuntu replay must bind their actual source/runtime and
complete outputs before success is reported. A public sidecar never includes
private image pixels, provider responses, credentials or repository history.

This remedy targets numerical portability only. It does not change measured
vectors, maps, scientific targets, intervals, inferential decisions or manuscript
numbers. It does not qualify actual service-error laws, recover capture ancestry,
authenticate missing pixels, or constitute replication by independent
investigators. All implementation and review remain maintainer-run LLM work.
