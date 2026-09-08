# Exact weighted empirical quantile corrigendum

Issued 2026-09-08 after a descriptive CDF boundary error was identified in the
completed computational responsiveness analysis. This is a numerical correction
scope, not another experiment or a replacement of the primary outcome. It covers
the closed `prv2-oauth-recovery-20260908` primary collection and the closed,
incomplete `prv2-oauth-20260908` ancillary collection. All existing sources,
protocols, features, results and plots remain unchanged at their frozen paths.

## Error and intended statistic

The original helper accumulated binary floating weights and selected the first
value whose normalized cumulative weight reached the requested quantile. At exact
CDF boundaries, rounding could incorrectly select the next order statistic. For
48 equally weighted values 0 through 47, the helper returned median 24, whereas
the declared generalized inverse empirical CDF gives 23. This can visibly move a
mixture median across the gap between muted and vivid outputs.

Reconstruct exact positive rational weights from the unchanged memberships:

- Empirical reference mixture: each of N paintings has weight 1/N.
- Equal broad-class references and single-polarity generated groups: each member
  of class c has weight 1/(3 n_c).
- Equal-polarity generated mixtures: each member of class/polarity stratum c,p has
  weight 1/(6 n_cp).

Keep the existing broad classes, selected available members and incomplete-stratum
rules. No member is added, excluded, reclassified or visually inspected. The values
are the unchanged saved chroma coordinates in their common primary-development
scale. Sort those values and accumulate exact fractions. For q = 1/10, 1/2 and
9/10, select the first value with cumulative mass at least q times total mass.
Ties share their observed value. No tolerance, smoothing or interpolation is used.

## Correction boundaries

First reproduce each original reference-context object from its saved numeric
members using its unchanged original helper. Then correct all affected reference
and generated quantile records, including shared summaries repeated under different
reference comparisons. Recompute both directions of central-80 inclusion when
their corrected range endpoints change accepted members. Use exact rational mass
for changed coverage values. If accepted membership is unchanged, retain the
original floating result exactly, avoiding unrelated last-bit summation changes.

Preserve primary inference, all means, Wasserstein distances, feature vectors,
availability and every other supplied result. A protected-result digest excludes
only the permitted quantile/coverage fields and must remain identical. Corrections
to medians cannot change central-80 coverage; changes to the 10th or 90th percentile
can, and the implementation tests that dependency with synthetic data.

## Publication and verification

Commit this source, tests and protocol and both original publication inputs before
preparing a create-once correction freeze. Bind exact input/source hashes, the
source Git commit and the rendering runtime. Commit the freeze before publishing.
The new namespace contains only affected-record tables, a complete correction
audit, a short report and corrected original-chroma-context PNG/SVG plots for each
collection. Reuse the frozen renderer with corrected numeric arguments; no earlier
plot is overwritten and the other experimental plots are not duplicated.

Replaying `check` must reproduce the corrected numeric audit and all nine report
files byte-for-byte. Hash verification detects altered original inputs or corrected
outputs. This task reads numeric JSON only and authorizes zero images, generation,
feature extraction, acquisition or human-rating activity. The scientific limits
of the original computational reference comparisons remain in force.
