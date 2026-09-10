# Prospective R10 qualification review

2026-09-10. Maintainer-run LLM reviewer 2, not an institutionally independent
investigator. Earlier implementation involvement includes geometry primitives,
centering and clause collection/workflows. I reviewed the v1 precision method and
its terminal result, but did not implement this v2 wrapper. The redesign and this
review know the v1 simulation failure; neither is outcome-blind to that history.
No paper score or live-collection permission is assigned.

**Conclusion:** no must-fix mathematical, lineage or execution-gate defect was
identified. The sole formal R10 assessment can proceed after the parent completes
validation and commits the reviewed source. A pass would qualify only the stated
proxy calculation; a failure must stop this single additional assessment under
DECISION's no-further-successor commitment.

## Examined snapshot

| File | SHA256 |
| --- | --- |
| `studies/painter_map_validation_v2/DECISION.md` | `5734a1331fb80e1ce5b423cfe8e03d23e8982ca01e6d55fd6ef622f5e5c0d3cb` |
| `studies/painter_map_validation_v2/PRECISION_PROTOCOL.md` | `b9fd2ada9726b2ac0878f2e2bdd3caaefcbc5f8d42881fd6a07e8638ef719377` |
| `src/latent_art_bench/painter_map_validation_v2/precision.py` | `0ed0cd14e5e2c925f63311136eb8ba7960ee50e12ac5b8c81dda263c84602c7a` |
| `src/latent_art_bench/painter_map_validation_v2/__init__.py` | `ca187b0bac15fb697372b37585dc86f9ba6dcc3c6cccf76173237f5fe1904040` |
| `tests/painter_map_validation_v2/test_precision.py` | `c35cbe32cb3133ac1dc71109ecd8aa24504b879097da57b815ea56b7e52c0297` |

I read the complete decision, protocol, source and tests. Imported v1 primitive
source remains SHA256
`971d909e63346cea64a1b7dd7b695ec8c112dc16562230d9d5dd7d968bd0b44d`.
No v1 source, global setting, protocol or terminal value is changed.

## Numerical and decision contracts

The wrapper evaluates **only R=10**, 240 hypothetical outputs and all **27**
predeclared laws, 10,000 trials each. It directly calls immutable v1 support,
simulation, exact-truth, interval and input functions. It does not copy/refit
numerical methods or re-evaluate the old three-allocation grid. Support seeds
remain `[2026091061,shape]`; trial seeds are exactly
`[2026091062,shape,mean,regime,10]`. The fixed inputs, full map, scaler, reference,
class masses, proxy means, covariance/whitening and within-pair coupling are
unchanged. The new scene briefs are not used in these historical proxy laws.

At R10 each paired deletion leaves nine repeats in one scene with its scene
weight preserved. The jackknife factor is 9/10 and critical value
`t(9,.9875)=2.6850108468164575`. Both endpoints retain the same approximate
Bonferroni interval procedure and unavailable-family treatment. This does not
turn the approximation into an exact service-coverage theorem.

The expected empirical V-energy target explicitly changes to **finite R10**:
its within-scene self-diagonal correction uses 1/10. Q's conditional-mean target
is unchanged while its sampling variance changes with R. This distinction is
correct in the decision, protocol and generated report; neither hypothetical
energy target is pooled with a new empirical cohort.

Coverage retains the one-sided CP tail **.05/81** and **.94** floor. The first
passing count remains 9476/10000 (bound .9400194393238092; 9475 gives
.9399130369867008). Every one of the 27 coverage cells must pass; every one of
nine baseline cells must meet median half-width E≤.25 and Q≤1.0. Stress widths
are reported, not silently made precision gates. Missing, duplicate or unplanned
cells and malformed widths are rejected. No alternative allocation, seed,
critical value or post-result fallback is selected. The protocol explicitly
avoids a combined 95% Monte Carlo claim across the old and new versions.

## Predecessor and execution gates

Read-only `read_previous` verified the exact three retained v1 output hashes,
shared provenance, all **12** original source/input bindings against source
commit `eb70ab8c30019b4b283366c170f8bdaf1405a023` and current bytes, and the full
unchanged stopped allocation decision. It did not rerun old simulations.

The new formal entry point binds **20 files**: the 12 old bindings, three failed
outputs and five new source/init/test/decision/protocol files. Working and staged
bytes must match recorded HEAD. A create-once RUN with runtime/source/predecessor
identity is written before simulation. Current source, HEAD/index and predecessor
are rechecked afterward; interrupted/existing output directories cannot be
reused. Pure numerical functions are deliberately separate from these orchestration
gates; the formal assessment must use the reviewed module entry point after the
parent's commit, not an unrecorded call to its numerical function.

## Artificial checks and review limits

My focused command passed **12 tests in 0.91s**:
`uv run --locked pytest -q tests/painter_map_validation_v2/test_precision.py`.
Scoped Ruff passed. Tests use invented numerical data or stub numerical execution
when checking all 27 orchestration seeds and create-once behavior. Their only
actual historical read verifies the retained predecessor, without sampling R10.

Separately, my existing independent direct-cloud oracle checked six invented
R10 cases and **180 literal paired deletions**, point estimates, jackknife
variances and exact truths, including positive scales below and above one.
Maximum absolute discrepancy was **2.7977620220553945e-14**. No historical R10
scenario, simulation or qualification was run by this reviewer. The implementer
also reports artificial-only checks, and `pmvqv2-20260910/` was absent at inspection.
These observations do not constitute proof that arbitrary unrecorded execution
is impossible; the approved entry point makes the intended formal run recordable
before calculation.

The design is openly informed by v1's failure. Its finite historical proxy laws
remain bounded, estimated and conditional on fixed inputs; stationarity,
independent repeats, future scene geometry, service noise, capture and perception
remain unverified. No collector is implemented or authorized by this review.
Fresh budget/metadata and a separately tested, frozen collection/measurement/
analysis contract are still required if the parent-recorded qualification passes.
