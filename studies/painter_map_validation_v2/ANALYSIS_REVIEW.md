# Precollection scientific analysis implementation review

2026-09-10. Scope: prospective `painter_map_validation_v2` observed-data analysis,
against the unchanged scientific and precision protocols. **No must-fix analysis
defect remains in this snapshot.** This is an arithmetic and analysis-contract
review, not permission to collect, a service-coverage certification, or a new
manuscript score. No new images, feature extraction, historical-law simulation,
or actual map-validation outcome was accessed or produced for this review.

The reviewer is a maintainer-run LLM agent, not an independent human or
institutional investigator. The reviewer authored the independent test file and
previously implemented the reused v1 numerical primitives, the v2 qualification
adapter, earlier variance/analysis modules and numerical release tools. The
current `analysis.py` and its original tests were authored by the coordinator.
The oracle below is separately expressed from the production contrast kernels;
this implementation involvement still limits institutional independence.

## Snapshot

The prospective analysis files were reviewed before their technical source
freeze; repository HEAD at inspection was
`dabc2f85f5f3eada7ea6fdcbb84181ae320953d1`. The following byte hashes, rather than
that pre-existing HEAD, identify the audited new source.

| File | SHA256 |
| --- | --- |
| `src/latent_art_bench/painter_map_validation_v2/analysis.py` | `7e06025be026312174a5335238233b42a3da2082ba88490e96b97d9316b64209` |
| `tests/painter_map_validation_v2/test_analysis.py` | `820a7542b6698bdfae7a85388d22bb6f0f2897a1f9d6bc15dbed41f2ce48f80e` |
| `tests/painter_map_validation_v2/test_analysis_oracle.py` | `ce96f59685efc8aebf14af3e26fa0d90e56d3c2c30697841ff5b350d9446c22a` |
| `studies/painter_map_validation_v2/PROTOCOL.md` | `d40f05a8714279ede08d395238739defda96d9a950e81f2b67d81d9caebca212` |
| `studies/painter_map_validation_v2/PRECISION_PROTOCOL.md` | `b9fd2ada9726b2ac0878f2e2bdd3caaefcbc5f8d42881fd6a07e8638ef719377` |
| `src/latent_art_bench/painter_map_validation_v1/precision.py` | `971d909e63346cea64a1b7dd7b695ec8c112dc16562230d9d5dd7d968bd0b44d` |

The current exact prospective assignment/configuration was used in wrapper
fixtures. Final `common.py`, workflow, collection and source-closure hashes are
left to the separate operational review because those files were still being
completed. This report does not substitute for their final review or source
binding.

## Independent arithmetic and gates

The oracle explicitly transforms every free vector under T1 and T2, constructs
weighted observed clouds, evaluates all three full V-energy terms and sums
ordered distinct-repeat residual inner products. For each deletion it physically
removes one paired F/N observation from only the affected scene, reconstructs
that scene's image weights and denominator, and recomputes the complete
components. It does not call the production support-table, contrast-statistic,
analytic-deletion, map or interval helpers for expected answers.

Three invented cases cover 2×10×2, 3×10×5 and the actual 12×10×31 dimensions,
including unequal scene weights, within-pair dependence, heteroscedastic draws
and 32 references in the full-size case. All 170 paired deletions agree. Maximum
absolute discrepancies across these cases were:

| Quantity | Maximum absolute discrepancy |
| --- | ---: |
| Four component point scores | 7.11e-15 |
| Two contrast points | 4.44e-15 |
| All deleted contrasts | 1.78e-14 |
| Two jackknife variances | 3.77e-15 |
| Interval bounds | 6.67e-15 |

An additional dyadic construction checks all 20 paired deletions with exactly
zero Q-contrast variance and positive energy variance. It withholds **both**
intervals while preserving finite component and contrast points. A separate
construction verifies negative Q and negative deltaQ without truncation, with
Q also checked against the sample-covariance correction identity.

The complete wrapper reproduces literal component points from wholly invented
measurements attached to the actual 240 prospective assignments. It preserves
water/built/land scene order, q_c/4 scene weights, q_c/40 image weights, all 120
pair identities and equal 1/32 reference weights. Missing a vector or a false
verified identity/timing eligibility gate prevents any numerical summary call;
all components, contrasts and intervals remain unavailable. Removing a terminal
row, changing one scaled value by one floating-point step, reversing feature
order or changing a measurement identity is rejected. Literal and internally
consistent receipt eligibility is required.

The review found one narrow row-identity issue: ordinary Python equality accepted
False as repetition 0 or 0.0 as sequence 0. The coordinator added exact-type
checks and two regression cases before the audited snapshot. Both now reject.

## Statistical interpretation and remaining boundaries

The observed draws are used only as an efficient distance-table lookup. No
finite-support truth function, new fitted law, map refit or evaluation centering
is invoked by observed-data analysis. The contrast is the complete empirical
finite-R10 energy difference; Q is the untruncated distinct-repeat residual
contrast. The paired within-scene deletion and factor 9/10 match the protocol,
with t(9,.9875), no map-label permutation and no additional hypothesis family.
The four components have no added intervals or tests.

The post-validation floating-point/ValueError handler records extreme finite
arithmetic failures as unavailable. Malformed input arrays are validated before
that handler. The audited normal and degenerate examples did not reveal a
masked arithmetic defect; this is not a proof against every programming error.

`analyze` consumes a **verified** collection-eligibility receipt. Its structural
input validation and stated origin hashes do not independently authenticate the
full scaler, reference and fitted-map bodies. The separate workflow must compare
the compact input object with `load_inputs(root)` and bind the exact source,
receipts and inputs; the operational implementer confirmed that bridge is part
of the planned freeze/verification path. Delivery, budget, service identity and
timing derivation remain the operational review's responsibility.

Correct arithmetic and proxy qualification do not prove coverage for the actual
service. The fixed-panel interpretation still assumes independent stationary
repeats, permits paired F/N dependence, conditions on historical maps/scaler/
references, and excludes their estimation uncertainty. It supplies no
scene-population, perception, capture or mechanism inference. All contrary,
uncertain, numerical-unavailable and incomplete outcomes remain reportable under
the frozen stopping rules.

## Validation

`uv run --locked pytest -q tests/painter_map_validation_v2/test_analysis.py
tests/painter_map_validation_v2/test_analysis_oracle.py` passed **46 tests**
(29 coordinator tests and 17 independent-oracle tests) in 1.10 seconds.
Scoped Ruff passed for these two files and `analysis.py`. The coordinator owns
the final whole-tree checks and separate technical freeze. This review creates
only its own test/report artifacts and changes no frozen scientific evidence.
