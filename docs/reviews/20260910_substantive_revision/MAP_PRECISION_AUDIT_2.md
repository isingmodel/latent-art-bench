# Fixed-map precision qualification: independent implementation audit

2026-09-10. Reviewer 2 is a maintainer-run LLM subagent, not an institutionally
independent investigator. Prior implementation involvement includes geometry
primitives, the centering analysis, and clause collection/workflow code. I did
not implement this precision module. This is a prospective method/code review,
not a paper score or a review blinded to earlier study results.

**Conclusion:** no remaining must-fix arithmetic or qualification-gate defect was
identified in the snapshot below. The specified offline qualification can proceed
after the parent commits its complete bound source. This conclusion neither
opens a collection gate nor predicts that an allocation will qualify.

## Examined snapshot

| File | SHA256 |
| --- | --- |
| `studies/painter_map_validation_v1/PRECISION_PROTOCOL.md` | `3d0a7ca0e97e303317324f4b0c929aa35ce7dba91be4103c4032ed9aa7fdb4de` |
| `src/latent_art_bench/painter_map_validation_v1/precision.py` | `971d909e63346cea64a1b7dd7b695ec8c112dc16562230d9d5dd7d968bd0b44d` |
| `tests/painter_map_validation_v1/test_precision.py` | `53f97071e45dc1976090a39214cf425d06ac2bb45710c3416e76d28e2e2ef1d0` |
| Independent artificial oracle, `tmp/paper/map_precision_audit_2.py` | `980b25263449d6058d9f0583a0fa9c763cef44a9193a924b06e35f76579b1bc5` |

I read the complete protocol, module and tests, checked the fixed input/map and
source-binding contracts, and reviewed DESIGN. The formal output directory
`studies/painter_map_validation_v1/pmvqv1-20260910/` did not exist at final inspection.
No formal historical-proxy grid, image generation, extraction, or live request
was executed by this reviewer.

## Mathematics and implementation

The energy target is correctly the **finite-R expected empirical V-energy
contrast**, not population-mixture energy. Its exact support truth subtracts
`(1-a) sum_j w_j^2 D_jj/R` from the independent-draw mixture expression. Same-scene
support pairs include all ordered atom pairs; sample self diagonals are zero.
The reference-within term cancels, and the positive isotropic map reduces the
within-generated contrast to `(1-a)` times the original free distances.

Q is the untruncated weighted distinct-repeat residual inner-product contrast.
Fixed affine maps commute with expectation, giving the stated difference of
squared conditional mean residuals. Within-pair F/N dependence is allowed;
independence across repeated pairs is needed for that interpretation. The exact
finite-support Q variance has the correct first-order and degenerate-kernel
terms and is an audit, not a replacement interval chosen after qualification.

The optimized paired deletion preserves each scene mass, renormalizes only the
affected scene, and adjusts its Q denominator. It agrees with literal recomputation
of unequal-size scene clouds. The jackknife uses the original point estimate and
centers deletions separately within each scene. The protocol correctly describes
the Student-t construction as approximate: R−1 degrees of freedom are not an
established conservative bound, and the jackknife variance is not generally
unbiased. The method needs the planned coverage qualification even when its
arithmetic is correct.

The covariance construction now preserves the complete historical within-arm
31×31 covariance in each constructed law. It does not preserve historical joint
F/N covariance; rho is explicitly a mixing coefficient rather than an exact
correlation. The support is finite and bounded after whitening, including its
“t5-shaped” and “lognormal-shaped” variants. Shared codebook values do not induce
cross-scene dependence when atom draws are independent.

## Coverage, width and provenance gates

The 27-law × 3-allocation grid is fixed, with 10,000 independent trial draws per
cell. Each hit requires both intervals to cover their exact truths. The
Clopper–Pearson tail `.05/81` controls the stated family of Monte Carlo lower-bound
claims without requiring independence between cells. The first passing count is
9,476: lower bound `.9400194393238092`; 9,475 gives `.9399130369867008` and fails.
This tests a **.94 coverage floor** for a nominal .95 interval candidate; it does
not prove .95 coverage.

Selection requires all 27 coverage cells and all nine baseline precision cells
for an allocation. The width limits are **median half-widths** E≤.25 and Q≤1
(full lengths .5 and 2), informed by the scale of existing results before formal
qualification. Stress widths are reported but cannot establish an upper bound on
service uncertainty. No passing allocation means stop this inferential proposal,
without tuning methods, scenarios, seeds or thresholds to its output.

Zero/nonfinite interval families count as coverage failures with infinite widths;
trials are not dropped. Malformed inputs fail. Aggregate overflow is reported as
unavailable rather than trimming numerical trials. Exact two-component width
shape and complete fixed grid checks prevent vacuous qualification.

The official build entry point checks working and staged bound bytes against
HEAD, writes a create-once RUN record before simulation, records input/source
hashes and runtime versions, and rechecks source identity before writing results.
It binds the numerical inputs, predecessor freeze/receipt, protocol/design,
implementation/tests, package initializers, and dependency lock/config. Direct
pure numerical functions intentionally do not perform these orchestration gates;
the formal invocation must remain the committed module entry point.

## Independent offline evidence

* Literal mapped-cloud energy, explicit residual pair sums, every paired deletion,
  and stratified jackknife variance matched the optimized code across invented
  supports with J=2/3/4, D=2/5, R=3/4/6/8 and several batch sizes: maximum absolute
  error `4.107825191113079e-15`. Nonuniform reference weights also agreed with the
  equivalent duplicated-reference construction.
* Exhaustive 16/64/256-state artificial sampling laws at R=2/3/4 independently
  verified exact E/Q truths and Q sampling variance: maximum absolute discrepancy
  `3.469446951953614e-16` against the production exact-truth calculation.
* Nine artificial shape/regime constructions verified both full arm covariance
  matrices (18 comparisons); maximum covariance error `1.509903313490213e-14`.
  Midpoint Q truth was zero through `3.6469850576981155e-15`.
* `uv run --locked pytest -q tests/painter_map_validation_v1/test_precision.py`:
  **42 passed in 1.00s**. Scoped Ruff passed. The parent owns the integration/full
  suite; I did not duplicate it or execute the formal 810,000-trial grid.

Issues resolved before formal execution were loss of cross-feature covariance in
an earlier draft, aborting rather than counting nonfinite interval trials,
nonfinite aggregate serialization, possible incomplete width vectors, ambiguity
between width and half-width, and overly literal interpretation of rho. These
were contract/correctness clarifications without examination of formal proxy or
new image outcomes.

## Material limits and handoff

Qualification is scientifically defensible as a bounded prospective check of one
candidate interval under specified proxy laws. Even a pass will not establish
coverage for actual service data: historical R=3 covariance and scene means are
estimated, future scene geometry may differ, interarm dependence is constructed,
and stationarity, cross-repeat independence, tails and delivery selection remain
unverified. Randomized collection order does not prove those assumptions. The
fixed scenes, references, map and scaler define the target; no scene-population,
reference-sampling, perceptual or oeuvre-level uncertainty is covered. The two
endpoints also retain their different targets, including finite-R dependence of E.

The Arvesen citation is used only as an asymptotic motivation; this audit did not
verify the full cited theorem text. Its arithmetic conclusions rest on direct
derivation and independent finite-law checks, not a claim of exact t coverage.

Next safe step: parent commits the reviewed source/contract, runs the single
create-once offline qualification, preserves all results including a failure, and
reviews its complete grid before deciding whether to write or authorize any
collection implementation. No method changes or fresh output fallback are
implied by this review.
