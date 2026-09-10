# Fixed-map precision qualification: terminal result audit

2026-09-10. Maintainer-run LLM reviewer 2; not an independent human or
institutional investigator. I contributed earlier geometry/centering and clause
collector/workflow implementations, but did not implement this precision module.
This audit follows my pre-run mathematical/code review and is not blinded to the
terminal decision. No score is assigned.

**Finding:** `stop_inferential_proposal` is the correct frozen-contract decision.
The failure is insufficient baseline **Q precision** for the chosen interval
procedure and candidate allocations under the specified proxy laws. It is not a
coverage failure, missing/nonfinite-trial failure, or identified implementation
defect. This does not establish that fixed-map validation is scientifically
impossible or that a particular map succeeds or fails on new images. No allocation
is selected; this failed design must not be collected.

## Provenance and complete-grid checks

Source commit: `eb70ab8c30019b4b283366c170f8bdaf1405a023`.
The [frozen protocol](../../../studies/painter_map_validation_v1/PRECISION_PROTOCOL.md)
and all 12 RUN source bindings match their current bytes, staged bytes and source
commit blobs. Protocol SHA256 is
`3d0a7ca0e97e303317324f4b0c929aa35ce7dba91be4103c4032ed9aa7fdb4de`;
precision implementation SHA256 is
`971d909e63346cea64a1b7dd7b695ec8c112dc16562230d9d5dd7d968bd0b44d`.
These are the pre-run reviewed snapshots.

Terminal files under `studies/painter_map_validation_v1/pmvqv1-20260910/`:

| File | Bytes | SHA256 |
| --- | ---: | --- |
| `RUN.json` | 2,244 | `944a8ea098b55d8ccb12c66f8b55dd55582456b080e0c77139f8100f4d0589e8` |
| `precision.json` | 93,970 | `ca5da6798dfc4c6056de6250320d85d1c17dffe1a0d274788d3ac8091557598a` |
| `PRECISION.md` | 9,939 | `c65ec527fd67289baefa7f52207a85778b84e818015546f703c589994c703555` |

The numerical result embeds RUN's identical source/environment fields. The
recorded environment is Python 3.13.11, NumPy 2.5.2, SciPy 1.18.1 on macOS arm64.
I inspected all **81** records: exact 3 shapes × 3 mean positions × 3 regimes ×
R=4/6/8 inventory and order, 10,000 trials each (**810,000 recorded trials**),
output counts 24R, exact prescribed trial seeds, 27 support hashes stable across
their three allocations, finite diagnostics and count bounds. Every one of the
81 Markdown rows agrees with its JSON record. There are **zero unavailable
interval families and zero nonfinite-estimate trials**.

## Exact failure decomposition

Every allocation needs all 27 simultaneous-coverage cells to pass and all nine
baseline cells to have median **half-widths** E≤.25 and Q≤1.0. The thresholds
refer to full interval lengths .5 and 2. Stress widths are reported but not gated.

| R / outputs | Coverage cells passing | Smallest CP lower bound | Baseline E half-width range | Baseline Q half-width range | Failed baseline E / Q cells |
| --- | ---: | ---: | --- | --- | --- |
| 4 / 96 | 27/27 | .994660 | .163741–.184424 | 1.962822–2.458024 | 0/9 / 9/9 |
| 6 / 144 | 27/27 | .983034 | .101425–.112907 | 1.068607–1.383271 | 0/9 / 9/9 |
| 8 / 192 | 27/27 | .976622 | .078711–.087373 | .789084–1.040286 | 0/9 / 2/9 |

For R=8 the two failures are baseline named-mean=T2 cells:

* Gaussian-shaped: Q median half-width **1.0189782480276501**, 1.8978% above 1.
* t5-shaped: **1.0402864375675982**, 4.0286% above 1.

The corresponding lognormal-shaped/T2 cell passes at .9610434896528317.
The small excesses do not license rounding, rerunning for another median, omitting
cells, changing thresholds, or selecting R=8. Median Monte Carlo uncertainty was
not itself a gate; the committed rule uses these retained medians.

Observed joint coverage ranges from .9814 to .9998. I independently recalculated
all 81 one-sided Clopper–Pearson bounds with tail `.05/81` from their integer hit
counts: exact agreement with the JSON. Every bound exceeds the fixed .94 floor.
The high observed coverage is consistent with conservative intervals in these
laws, but does not make the failed width criterion optional. At R=8 the ungated
high-noise Q half-widths are 1.572680–1.973954; they are not the reason for the stop.

The three allocation records correctly have `coverage_pass=true`,
`baseline_width_pass=false`, `qualified=false`; `selected_R` and
`selected_outputs` are null. I reconstructed these decisions directly from all
retained cells without calling the production selection function.

## Defect assessment and limits

No numerical anomaly or contract mismatch was identified. Recorded E truths obey
the required affine dependence on 1/R through 4.44e−16; recorded Q truths are
unchanged across R, and their exact sampling variances obey the stated R law
through 1.67e−16. Empirical/exact Q variance ratios range .965322–1.030808; this is
a descriptive consistency check, not another qualification test. My pre-run
independent direct-cloud/paired-deletion oracle and finite-law exhaustive checks
already validated the arithmetic, with 42 focused tests passing on this source.
No additional test suite or formal Monte Carlo grid was run for this audit.

This is a substantive **precision-qualification failure of the prescribed
procedure/design under its proxies**, not evidence of a failed transport service
or a new biological/perceptual/style result. The proxies use uncertain historical
means/covariances, bounded artificial support and independent stationary draws;
passing coverage under them would not prove actual service coverage. Energy
retains its finite-R empirical target and Q its fixed-scene conditional-mean
mismatch target. The width thresholds are planning tolerances informed by old
result scales, not established meaningful-effect margins.

The terminal bundle contains aggregate simulation results, not every trial's
interval. Accordingly this audit verifies the complete aggregate inventory,
provenance, stated formulas, report consistency and gates; it does not independently
reconstruct the 810,000 medians/hit indicators. No frozen files, method, threshold,
seed, allocation or evidence were changed. Preserve the terminal failure and keep
this inferential proposal closed.
