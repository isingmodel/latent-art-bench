# Round 3 → revision

Round 3 reviewed PDF `7da8263c…` (25 pages). Recommendations: methods **minor revision**,
empirical **minor revision**, editor **minor revision**. Criterion 1 (claims and evidence) was
*partially* for all three; criterion 2 (audience and clarity) *yes* for all three; desk-rejection
risk *low* for all three. The round does not pass the rubric.

**Prompt change disclosed.** Relative to round 2, the round-3 reviewer prompts added one
calibration clause. Methods and empirical: "answer criterion 1 with `yes` if every claim as worded
is supported, even if you can list minor wording improvements". Editor: "answer each criterion with
`yes` if the paper meets it as written, even if you can list minor improvements". The prompts also
listed the diagnostics-v2 plan among the supplementary material and gave the new page count. The
rubric itself did not change.

## New analysis

[`painter_tmlr_diagnostics_v3`](../../painter_tmlr_diagnostics_v3/REPORT.md), under a
[plan](../../../studies/painter_tmlr_diagnostics_v3/PLAN.md) that lists the values the round-3
reviewers had already computed. It recomputes the genuine-painting controls with two *distinct*
works per pseudo-repeat, in the 31 features, CLIP and CSD; adds scene, reference and joint
intervals for the embedding β and D; computes the normalized-prototype proximity shares; and adds
paired scene-bootstrap contrasts between feature families. Replayed by `make retrospective-check`;
3 constructed-data tests in the routine suite. The existing request-timing diagnostic
(`painter_request_timing_v1`) is now a manuscript input.

## Critical issues and responses

| Issue (reviewers) | Response |
| --- | --- |
| Genuine-painting control drew the two pseudo-repeats with replacement, contradicting its description; "FLUX.2 Max is close to the genuine level" unsupported (methods, empirical, editor) | Distinct-works control reported in all three representations (new Appendix Table: 31 features 0.125–0.328, embeddings 0.060–0.216, with 95% ranges and shares above 1); the earlier with-replacement values kept in a labelled column with the reason they were inflated; target noise explained analytically (≈ twice the 6.7% H correction for half-size targets); the FLUX.2 Max sentence removed; every configuration is far above the genuine means in every representation |
| "Three configurations are worse than no distinctions" stated without its representation; embedding D without intervals; GPT Image 1 fragile to multiplicity (all three) | Abstract, §1 and §5.3 scope the verdict to the 31 features; new main-text Table 4 gives CLIP and CSD β, D, scene intervals and joint P(D<1); text states the reversal (CLIP: GPT Image 1 lowest; CSD: all below 1, four intervals below 1); D-vs-1 labelled descriptive and outside the prespecified family; six-way Bonferroni interval for GPT Image 1 [0.935, 2.210] includes 1, Flare and Sunburst stay above |
| Representation validity: the 31 features separate the painters poorly (empirical, editor) | Separability (49.8% vs ~80%) moved to the Measurements paragraph; §5.3 declines an overall specificity ranking; recommendation 1 now starts with checking separability and calibrating D per representation; D>1 explained as over-sized, partly aligned differences (β/√Q 0.511–0.600) with the scale-mismatch reading and D_held as evidence |
| Premise thinly documented; analysed score differs from practice (editor, empirical) | Opening sentence narrowed to "often evaluated"; Verma et al. (CSD similarity used to decide imitation) and Su et al. (gain over the no-name image) added; §4.4 names the score as mean image-to-reference cosine, states that the identity holds for unit prototypes (shares change ≤ 0.5 points, new Appendix Table) and that raw proximity adds a further name-independent term |
| "Texture is the least shared family" not resolved against spatial (all three) | Paired contrasts reported: texture below color in 99.7% of resamples (−6.1 points [−13.5, −2.0]), below spatial in only 65.2%; bullet and §5.5 reworded; dropped draws stated |

## Minor changes

Abstract rewritten to state the argument before numbers, with fewer ranges; reading guide at the
start of §4; §5.1 heading reworded so it does not suggest a match with the faithful value; Table 1
now shows N/H and B/H (the direction block moved to a new appendix table) and §5.1 explains the
exact-differences comparison through B/H; §5.2 qualified (11 of 12 intervals above 50%; GPT Image 2
in CSD; Cézanne as low as 34.6%); within-CLIP readout contrast leads §5.4 and the intro bullet;
unadjusted nominal and bootstrap pairwise intervals reported (6 and 8 of 15 resolved); cropped-only
and refit source corrections separated; single-scene deletions and square windows added to the
sensitivity table; learned-setting and SD-Turbo family tables added; H correction applied to D and
the benchmarks (FLUX.2 Max 0.787; exact fractions 59.3–85.1%); repeat dependence stated to inflate
N and B; request timing (median 3.1 minutes between repeats; linear drift does not predict repeat
differences); exchangeable null as a ratio of expectations with mean zero; interval estimand
sentence rewritten; "about twice" corrected to squared size; Table 11 caption ½ fixed; "overlap and
do not add" removed; D_held comparators named; Appendix F defines the reference source and corrects
the class-score sentence; Flare and Sunburst described, Figure 2 labels explained; 230-of-870
content-label disagreement noted in §3; dual-use sentence in the broader impact statement;
identifier line breaks; Figure 3 tick and Figure 4 colorbar fixed; operational definition of
specificity in §4.3 and Limitations. The claim registry now anchors each of 141 numbers to its
sentence context.

## Not changed

No image release commitment in the manuscript, no human check of the AI crops, no HEIM citation
and no new generation (distant painters, fictitious name or group clause) — owner decisions or
optional suggestions, stated as limitations where relevant.
