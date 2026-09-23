# Held-scene prompted-name transfer: design audit

**2026-09-19 KST. Design QA only; corrected before outcomes.** This audit now follows [the actual transfer PLAN](../../studies/painter_prototype_transfer_v1/PLAN.md). No translated predictions, accuracies, or future outcome files were computed or inspected. Original prototype confusions were already known when this proposal arose.

## Verdict

**Sound for a fixed retrospective decision diagnostic under the original PLAN.** Matching the actual source and target mixture means while classifying against normalized prototype directions is coherent. Held-scene accuracy against known prompt labels is an externally specified success criterion, so a gain is not guaranteed by that mean-matching objective. The pooled translation cannot learn which generated cluster corresponds to which artist: permuting training artist labels leaves it unchanged. This supplies useful out-of-fold decision evidence on the retained panel.

It does **not** supply fresh independent validation data. Previously inspected confusions informed the choice of diagnostic, including observations later called held out. Record the specification before translated outcomes, but describe it as a retrospective extension with out-of-fold fitting, not preregistration or an untouched confirmatory test.

## Freeze the exact algorithms

Let \(z_{sra}\) be a retained unit generated embedding for scene \(s\), repeat \(r\), and prompted artist \(a\). For each encoder/reference target, form the **unnormalized** real-art centroids \(\mu_a\), each a mean of unit artwork embeddings. Classification uses their normalized directions \(u_a=\mu_a/\|\mu_a\|\). Translation targets the equal-painter mean of \(\mu_a\), not of \(u_a\); do not weight painters by artwork counts.

For each held scene \(h\), model, and encoder:

\[
\bar\mu=\tfrac14\sum_a\mu_a,\qquad
m_{-h}=\tfrac1{13\cdot2\cdot4}\sum_{s\ne h,r,a}z_{sra},\qquad
t_{-h}=\bar\mu-m_{-h}.
\]

**Do not normalize either pooled mean or the translation.** Fix its scale to exactly one. The transformed training mixture satisfies \(m_{-h}+t_{-h}=\bar\mu\) exactly. Normalizing the individual reference centroids before forming this target would change the method and would no longer match the actual equal-painter reference mixture mean.

| Method | Held-scene prediction | Information fitted on the other 13 scenes |
|---|---|---|
| Reference baseline | \(\arg\max_a z^\top u_a\) | None; fixed real references |
| Common translation | \(\arg\max_a (z+t_{-h})^\top u_a\) | Balanced pooled named-arm mean; artist correspondence unused |
| Generated-centroid context | \(\arg\max_a z^\top q_{a,-h}\), where \(q_{a,-h}\) normalizes \(\tfrac1{26}\sum_{s\ne h,r}z_{sra}\) | Artist-labeled generated examples |

Each fold fits on **104 named images** and evaluates **eight**; each model/encoder evaluates 112 images across 14 folds. There are 12 model/encoder combinations, but the two encoders reuse the same images. A complete balanced pool makes translation label-blind in its arithmetic; selecting named arms and establishing balance still uses experimental metadata. This is target-domain calibration, not a zero-shot procedure applicable to an arbitrary unlabeled mixture.

Use the existing fixed artist order and tie rule; report exact ties. Dot-product scores avoid unnecessary query renormalization and equal cosine decisions whenever \(z+t\ne0\). If a translated query is exactly zero, report it and apply the explicitly declared linear-score tie rule; do not call its cosine defined. Any zero-norm reference or generated centroid makes that method/fold undefined; do not silently discard a class.

## Exact interpretation: useful thresholds, unchanged centered geometry

For nonzero translated queries,

\[
\arg\max_a\cos(z+t,u_a)
=\arg\max_a\{z^\top u_a+t^\top u_a\}.
\]

The method adds a **class-specific intercept**, fixed for all eight held-scene images. It is **not** ordinary joint centering around the mean of the normalized classification prototypes: generally \(\bar\mu\ne\tfrac14\sum_a u_a\). The earlier audit's centered-unit-prototype Euclidean equivalence therefore does not apply to this chosen rule.

An accuracy improvement would show that a pooled offset adjustment usefully changes decision thresholds for prompted-name identification. Within a fold, each pairwise class margin changes by a constant, so ordering images by that margin is unchanged. Artist differences, artist-centered beta/Q/D, and artist-centered repeat contrasts are unchanged by the common translation before any query normalization. Accuracy can change because the final argmax decision is nonlinear.

**Do not identify this offset with the previously estimated shared naming effect.** It aligns pooled named-generated and real-reference means; it contains generator/domain and average-content differences as well as any shared style response. Free/generic arms never enter its fit. Consequently, success would not establish that removing a causal named-minus-generic component improves decisions, nor that the centered diagnostic itself learned or repaired artist-specific geometry.

## Leakage controls and fair reporting

- Exclude the held scene jointly across all four artists and both repeats. Do not split the two repeats across fit/test. Fit separately for every model/encoder; never include held-scene embeddings in its pooled mean or labeled centroids.
- Keep encoder weights, source preprocessing, and artist order fixed. The PLAN's main target is the 649-work original-view panel; all original/audited-region × primary/development reference targets are required sensitivities. Thus report all 12 model/encoder combinations under each of four reference targets, without selecting by accuracy. Those targets reuse generated observations, and generated-centroid predictions should be identical across reference targets.
- Record scale one, all six models, both encoders, all scenes, and all three methods before translated results. No fitting an extra intercept, class prior, scale, artist permutation, or favorable subset against held-scene labels.
- Reference classification has no generated-domain adaptation; translation uses an unlabeled balanced generated pool; generated centroids use class labels. State these different information budgets. The supervised centroid result is context for generated-domain identifiability, not a like-for-like zero-shot contest or evidence of alignment with real artwork.
- Report macro accuracy (equal to micro accuracy in this complete balanced panel), per-artist recall, full confusions, paired per-scene accuracy changes, and corrected-versus-harmed prediction counts. Show all 12 combinations, including null or adverse changes. Average gains alone can hide transfer of errors between painters.
- Treat the results descriptively. Fourteen overlapping training folds, shared reference prototypes, and two encoders on identical images are not independent replications. Ordinary image-wise binomial/McNemar inference or unqualified fold-wise standard errors would overstate independence. A bootstrap of fixed out-of-fold predictions also omits refitting uncertainty.

## What this can and cannot establish

**Can:** demonstrate whether one untuned, label-blind pooled adjustment improves the practical task of recovering known prompt clauses on held-out content scenes; distinguish zero-shot reference failure from recoverable decision bias and supervised generated-domain separability.

**Cannot:** establish artistic fidelity, human expert agreement, unknown-artist attribution, new-service replication, causally isolated naming gains, improved pairwise discrimination, or generalization beyond this fixed four-artist/14-scene experiment. A null result does not refute the mathematical common-translation invariance; an improvement does not validate every diagnostic claim.

Before execution, meaningful constructed checks should verify: held-scene perturbations cannot change its fitted translation/centroids; permuting training class assignments cannot change translation but can change labeled centroids; dot and cosine decisions agree off degeneracies; known common-offset toy data behave as specified; and axis/count checks preserve 104 fit versus eight test images. In particular, the correction must be zero when the training mixture equals \(\bar\mu\), even when individual real-centroid norms are below one; this catches accidental substitution of the rejected target. Bind the new plan, code, input hashes, and exact prediction rows in separate versioned outputs. No numerical execution was performed for this audit.

## Correction history: rejected alternative, before outcomes

The [earlier audit](held_scene_transfer_design_audit_normalized_alternative.md) introduced \(t_{\mathrm{alt}}=\tfrac14\sum_a u_a-m_{-h}\), although the root PLAN already specified \(\bar\mu-m_{-h}\). That was an unrequested design change and is preserved verbatim for provenance, not adopted as a second tested candidate. Root rejected it before translated outcomes to retain actual source/target mean matching in the unit-image embedding space. Both rules are mathematically possible, but answer different calibration choices; no performance evidence favored either.

The difference is the reference-only vector \(t_{\mathrm{alt}}-t=\tfrac14\sum_a u_a-\bar\mu\), which generally changes class intercepts. This audit withdraws its earlier normalized-target requirement and centered-unit-prototype equivalence. The original rule remains sound for the limited prompted-name decision test; all retrospective, leakage, geometry, and fidelity qualifications above remain.

Audited PLAN SHA-256: `c7f02a6d65910bc6c8e1a1e79bac0f6c16143d0ba4176e69dc4455d3bf89e459`.
Archived earlier audit SHA-256: `4d5632c85fd0d188a4d1a627be1ab47dd23224821c31e4d93cd71d823be957d9`.
