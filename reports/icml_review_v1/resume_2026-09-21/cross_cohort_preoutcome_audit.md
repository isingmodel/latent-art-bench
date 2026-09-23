# Cross-cohort pre-outcome design and code audit

**Status: passed for the exact bound plan, implementation and constructed tests.**

This is a bounded independent method/code audit, not a scientific rating. The auditor did not load empirical feature arrays, execute real outcomes or inspect the new empirical findings.

## Initial findings and fixes

- Mandatory: the original plan did not fully define pairwise amplitude/error aggregation or family-specific denominators. The revised plan and code now specify mean-block-and-scene amplitude, mean-scene cross-block error and separate family/pair denominators. Zero denominators remain unavailable.
- Optional hardening adopted: analyze/check now require an external frozen-input SHA-256, in addition to the passing audit and explicit execution flag.
- Scope clarified: each deletion uses K=24 with fixed historical reference membership, means, scales and denominators.

## Verification

- 55 constructed tests passed; Ruff passed. Tests cover ordered-pair U, the two-repeat identity, within-block arm dependence, signed estimates, all-coordinate and family targets, all six pair formulas, deletions, invalid census rows, create-once behavior, execution gates and synthetic replay/tampering.
- A separate direct ordered-pair oracle passed 100 checks on constructed arrays, including all four coordinate families, all six pair amplitudes/errors, every K=24 deletion and negative/zero-denominator cases.
- Exact file bindings and the complete probe results are recorded in the adjacent JSON.

## Interpretation boundary

The independent-block expectation requires stable independent block errors; distinct deterministic seed streams motivate but do not establish that assumption. This retrospective separate collection retains the same exposed finite four-painter historical target. It cannot establish fresh confirmation, perceptual fidelity, broader painter generalization or closed-service independence.

No unresolved mandatory pre-outcome design/code finding remains. Empirical outcomes must be reported even if adverse or undefined.
