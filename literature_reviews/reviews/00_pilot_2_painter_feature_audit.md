# Pilot 2 audit: what “painter feature” must mean in the relaunch

Review type: internal historical-study audit against the new literature protocol

Evidence reviewed: frozen Pilot 2 protocol, qualification JSON, analysis JSON, result report,
sample-size sensitivity, and feature-method provenance

## 1. Intended scientific construct

Pilot 2 was explicit: “The target remains the artist, not the era or movement.” Its operational
feature was a deterministic project adaptation of Kim et al.'s A-vector. It asked whether adding a
painter's name to a content-matched generation request moved the output:

1. closer to that painter's held real-work centroid; and
2. closer to the painter than to one preregistered neighboring painter, beyond the same contrast
   for the painter-free control.

That is the correct lineage for the reboot. The desired object is not a generic list of painting
properties. It is a **painter-associated feature distribution across works** suitable for testing
target resemblance, specificity, and coverage.

## 2. What Pilot 2 did well

The following decisions remain scientifically useful:

- physical works, not patches, formed the real atlas;
- the target label was painter;
- painters were crossed with two sources (AIC and NGA);
- real transforms/PCA were fitted before generated outputs;
- training and held real works were separated;
- requested-label strata were not misrepresented as authoritative executed model identities;
- each named output was paired with an otherwise matched painter-free control;
- target improvement and target-versus-neighbor specificity were separate estimands;
- content block was the top-level generated sampling unit, so four repetitions did not inflate
  top-level \(n\);
- real works and content blocks were resampled at their appropriate levels;
- source-specific signs were required rather than allowing a pooled effect to hide reversal;
- refusals remained in the assignment ledger and were not replaced; and
- an incomplete estimand grid led to “not tested,” not opportunistic complete-case confirmation.

These are stronger foundations than unpaired image similarity, random image splits, or a single
FID-like score.

## 3. Why its measurement gate did not establish a painter feature

### 3.1 Real sample and representation

The atlas contained 40 works: four painters by two sources by five works. Twenty-four works (three
per painter-source cell) fitted a PCA of the 16,384-dimensional A-vector. The PCA retained 22 of
the maximum 23 components to reach 95% variance. This is almost full sample-rank retention, not a
stable low-dimensional estimate of painter structure.

The remaining 16 works supplied only four held works per painter. Generated outputs were compared
to centroids of those four works. Such centroids cannot describe multimodality by subject, career
phase, technique, or medium, and their sampling uncertainty is large.

### 3.2 Pooled painter-label and source-prediction diagnostics

The qualification gate technically passed its registered criteria, but the evidence is weak for
the broader construct:

| Diagnostic | Observed result | Painter-feature implication |
|---|---:|---|
| Four-painter pooled held balanced accuracy | 0.50 (chance 0.25; 16 works) | pooled artist-label predictability in the fixed atlas, but imprecise and uneven |
| Monet held recall | 0.25 | target painter often not identified |
| Pissarro held recall | 0.25 | target painter often not identified |
| AIC held balanced accuracy with pooled fit | 0.625 (8 works) | coarse source-stratum result |
| NGA held balanced accuracy with pooled fit | 0.375 (8 works) | coarse and close to chance |
| Source balanced accuracy | 0.8125 (16 works) | high acquisition-source predictability on a separate two-class task; raw BA is not ranked against the four-class painter task |
| Train NGA, test AIC painter accuracy | 0.25 | chance cross-source transfer |
| Train AIC, test NGA painter accuracy | 0.375 | weak cross-source transfer |

Balancing painter by source prevented perfect label-source aliasing, but it did not make the
representation source-invariant. A source-stratified permutation \(p=0.0216\) shows that the
registered pooled statistic was unusual under that shuffle scheme; it does not establish
reproduction reliability, content independence, or human painterly-style validity.

### 3.3 A-vector construct and artifact uncertainty

The Pilot 2 vector was an auditable, deterministic engineering adaptation: normalize to PNG,
force a 512 by 512 resize, derive a content-dependent seed, sample an SD2 VAE posterior, flatten,
and scale. It appropriately did not claim to reproduce Kim et al.'s unpublished random draw.

Scientifically, however:

- forced-square resizing changes composition;
- one arbitrary seeded posterior draw adds a model-specific realization that is not itself a
  painter construct;
- Kim's released code has an initialization defect and no complete reference artifact;
- the SD2 representation can contain object/content and web-training associations;
- no same-work independent-reproduction reliability was tested; and
- classification against four labels is not convergent/discriminant validation.

The A-vector is therefore a candidate learned coordinate, not the definition of painter feature.

## 4. What the generated estimands did and did not show

The frozen estimates were numerically positive in aggregate, but all four confirmatory rows were
not tested because five refused cells left the registered 256-pair feature grid incomplete. The
scientific conclusion is the registered one: no primary hypothesis was supported.

Even with a complete grid, centroid target improvement would measure proximity to a small
reference mean. It would not show that generated works cover the painter's oeuvre. A one-neighbor
difference-in-differences can also be positive when named and control outputs are both far outside
the real painter distribution.

The relaunch retains the paired logic while adding:

- absolute fit to the target distribution;
- one-versus-many matched hard-neighbor specificity;
- broad-negative calibration;
- bidirectional fidelity/precision and real-support coverage;
- within-painter contraction/expansion;
- content-by-painter interactions; and
- reference-distribution uncertainty.

## 5. Required definition for `painter_features_v1`

For painter \(a\), the target is not a vector \(\mu_a\) alone. It is a nuisance-qualified
distribution

\[
P_a(z \mid \text{content},\text{genre},\text{medium},\text{date},\text{source}),
\]

estimated across held-out physical works. Candidate coordinate \(z\) may contain interpretable
color/spatial/ordinal measurements, learned appearance coordinates, and contextual diagnostics,
but only gates can admit it to the painter profile.

The minimum gates are:

1. exact method/provenance identity;
2. deterministic or modeled stochastic repeatability;
3. controlled preprocessing robustness;
4. same-work independent-reproduction reliability;
5. leave-source-out painter specificity;
6. leave-content-family-out and matched-medium/date painter specificity;
7. source/content/metadata/artist-name shortcut probes;
8. content-controlled human convergent and discriminant validity; and
9. external-source confirmation.

Painter classification is one sensitivity analysis inside Gate 5. It is not the construct.

## 6. Historical boundary

This audit does not recalculate Pilot 2, fill its refused cells, revise its protocol, or relabel
its outcome. It uses the frozen negative and incomplete evidence to design a new prospective
measurement study. Pilot 2 remains a valid historical record of an engineering-qualified but
scientifically underqualified painter-feature path.
