# Held-scene prompted-name transfer: design audit

**2026-09-19 KST. Design QA only.** No translated predictions, accuracies, or future outcome files were computed or inspected. Existing analysis source and its recorded design were read; original prototype confusions were already known when this proposal arose.

## Verdict

**Proceed as a fixed retrospective decision diagnostic, with the definitions below.** Held-scene accuracy against known prompt labels is an externally specified success criterion, so a gain is not guaranteed by the fitting objective. The pooled translation cannot learn which generated cluster corresponds to which artist: permuting training artist labels leaves it unchanged. This supplies useful out-of-fold decision evidence on the retained panel.

It does **not** supply fresh independent validation data. Previously inspected confusions informed the choice of diagnostic, including observations later called held out. Record the specification before translated outcomes, but describe it as a retrospective extension with out-of-fold fitting, not preregistration or an untouched confirmatory test.

## Freeze the exact algorithms

Let \(z_{sra}\) be a retained unit generated embedding for scene \(s\), repeat \(r\), and prompted artist \(a\). For each encoder, form the real-art means \(v_a\), then **individually normalize** them to \(p_a=v_a/\|v_a\|\). Use equal painter weights, not artwork-count weights.

For each held scene \(h\), model, and encoder:

\[
\bar p=\tfrac14\sum_a p_a,\qquad
m_{-h}=\tfrac1{13\cdot2\cdot4}\sum_{s\ne h,r,a}z_{sra},\qquad
t_{-h}=\bar p-m_{-h}.
\]

**Do not normalize either pooled mean or the translation.** Fix its scale to exactly one. The target mean here is the mean of the same normalized prototypes used for classification, not the mean of the unnormalized real-art centroids. These alternatives produce different methods and must not be selected after results.

| Method | Held-scene prediction | Information fitted on the other 13 scenes |
|---|---|---|
| Reference baseline | \(\arg\max_a z^\top p_a\) | None; fixed real references |
| Common translation | \(\arg\max_a (z+t_{-h})^\top p_a\) | Balanced pooled named-arm mean; artist correspondence unused |
| Generated-centroid context | \(\arg\max_a z^\top q_{a,-h}\), where \(q_{a,-h}\) normalizes \(\tfrac1{26}\sum_{s\ne h,r}z_{sra}\) | Artist-labeled generated examples |

Each fold fits on **104 named images** and evaluates **eight**; each model/encoder evaluates 112 images across 14 folds. There are 12 model/encoder combinations, but the two encoders reuse the same images. A complete balanced pool makes translation label-blind in its arithmetic; selecting named arms and establishing balance still uses experimental metadata. This is target-domain calibration, not a zero-shot procedure applicable to an arbitrary unlabeled mixture.

Use the existing fixed artist order and tie rule; report exact ties. Dot-product scores avoid unnecessary query renormalization and equal cosine decisions whenever \(z+t\ne0\). If a translated query is exactly zero, report it and apply the explicitly declared linear-score tie rule; do not call its cosine defined. Any zero-norm reference or generated centroid makes that method/fold undefined; do not silently discard a class.

## Exact interpretation: useful thresholds, unchanged centered geometry

For nonzero translated queries,

\[
\arg\max_a\cos(z+t,p_a)
=\arg\max_a\{z^\top p_a+t^\top p_a\}.
\]

The method adds a **class-specific intercept**, fixed for all eight held-scene images. Equivalently it performs Euclidean nearest-prototype classification between \(z-m_{-h}\) and \(p_a-\bar p\); this does not mean renormalizing the centered prototypes.

An accuracy improvement would show that a pooled offset adjustment usefully changes decision thresholds for prompted-name identification. Within a fold, each pairwise class margin changes by a constant, so ordering images by that margin is unchanged. Artist differences, artist-centered beta/Q/D, and artist-centered repeat contrasts are unchanged by the common translation before any query normalization. Accuracy can change because the final argmax decision is nonlinear.

**Do not identify this offset with the previously estimated shared naming effect.** It aligns pooled named-generated and real-reference means; it contains generator/domain and average-content differences as well as any shared style response. Free/generic arms never enter its fit. Consequently, success would not establish that removing a causal named-minus-generic component improves decisions, nor that the centered diagnostic itself learned or repaired artist-specific geometry.

## Leakage controls and fair reporting

- Exclude the held scene jointly across all four artists and both repeats. Do not split the two repeats across fit/test. Fit separately for every model/encoder; never include held-scene embeddings in its pooled mean or labeled centroids.
- Keep encoder weights, source preprocessing, artist order, and the 649-work reference panel fixed. Primary view should follow the existing original-source learned-view definition. If the audited-region reference sensitivity is included, declare and report it for all combinations; do not select a view or development panel by accuracy.
- Record scale one, all six models, both encoders, all scenes, and all three methods before translated results. No fitting an extra intercept, class prior, scale, artist permutation, or favorable subset against held-scene labels.
- Reference classification has no generated-domain adaptation; translation uses an unlabeled balanced generated pool; generated centroids use class labels. State these different information budgets. The supervised centroid result is context for generated-domain identifiability, not a like-for-like zero-shot contest or evidence of alignment with real artwork.
- Report macro accuracy (equal to micro accuracy in this complete balanced panel), per-artist recall, full confusions, paired per-scene accuracy changes, and corrected-versus-harmed prediction counts. Show all 12 combinations, including null or adverse changes. Average gains alone can hide transfer of errors between painters.
- Treat the results descriptively. Fourteen overlapping training folds, shared reference prototypes, and two encoders on identical images are not independent replications. Ordinary image-wise binomial/McNemar inference or unqualified fold-wise standard errors would overstate independence. A bootstrap of fixed out-of-fold predictions also omits refitting uncertainty.

## What this can and cannot establish

**Can:** demonstrate whether one untuned, label-blind pooled adjustment improves the practical task of recovering known prompt clauses on held-out content scenes; distinguish zero-shot reference failure from recoverable decision bias and supervised generated-domain separability.

**Cannot:** establish artistic fidelity, human expert agreement, unknown-artist attribution, new-service replication, causally isolated naming gains, improved pairwise discrimination, or generalization beyond this fixed four-artist/14-scene experiment. A null result does not refute the mathematical common-translation invariance; an improvement does not validate every diagnostic claim.

Before execution, meaningful constructed checks should verify: held-scene perturbations cannot change its fitted translation/centroids; permuting training class assignments cannot change translation but can change labeled centroids; dot and cosine decisions agree off degeneracies; known common-offset toy data behave as specified; and axis/count checks preserve 104 fit versus eight test images. Bind the new plan, code, input hashes, and exact prediction rows in separate versioned outputs. No numerical execution was performed for this audit.
