# Reviewer 3 — substantive revision, round 2

## Metadata and review provenance

- **Paper:** *Painter Naming and the Distributional Gap Between Generated Images and Original Paintings*.
- **Authors:** Anonymous authors; affiliations are not supplied.
- **Status/year:** Local English manuscript revision, reviewed 10 September 2026; no venue has been selected.
- **Domain/type:** Empirical computational evaluation of text-to-image prompting and digital painting distributions.
- **Snapshot:** Entire 1,871-line manuscript, all appendices, bibliography, all 36 PDF pages and all nine figures. TeX SHA-256: `8973d78ceb7d4f81a05010e118454eabc210ecdaa4885ad85eec1e3e41cff0e5`. PDF SHA-256: `ca291f0e0b04ebfa740240d697be89bbe78cfdaecae5b47b61f06acb636d3b9b`. Both hashes were checked before and after reading.
- **Criteria:** The user-requested [DeerFlow academic-paper-review skill](https://github.com/bytedance/deer-flow/blob/main/skills/public/academic-paper-review/SKILL.md), locally retained with SHA-256 `a0285baaeacc916bf45751c06db37745b195ddd4ec30e271ec1472f6cd48e8aa`, and the unchanged [three-aspect rubric](../20260909_academic_review/RUBRIC.md), SHA-256 `e381b14bd5b76d973139877eafba1325d7e9d4921aef0bbd28217be6bd46b6f8`.
- **Relationship to the project:** This is a maintainer-run LLM subagent review, not independent human or institutional peer review. Before the new analyses, I supplied literature and article-structure advice, proposed a generated-only held-scene moment benchmark, and identified the mean-offset ambiguity that motivated the centering successor. I subsequently advised on interpretation. I did not implement either study, edit analysis source, choose observed numerical results, or edit the manuscript. This methodological involvement limits the independence of this reassessment and is disclosed rather than treated as external validation.
- **Review boundary:** Mandatory status and artifact instructions were read, and the shared working tree was inspected. I did not consult the other reviewers' new reports or scores. The mandatory status contains earlier aggregate scores; they are not evidence for this assessment. The previous public numerical release and corrected r1 manuscript remain distinct from this local revision. A pending add-on is not credited as an already published artifact.

## Executive assessment

The revision now has a coherent empirical contribution. Its strongest result is the disagreement between two explicitly evaluated targets: adding the fitted scalar improves prediction of actual named scene means in all six primary cells, while making the transformed artist-free cloud farther from the painting panel in five. The held-scene and later-cohort comparisons make this more useful than simply observing that naming and contraction coexist. The subsequent evaluation-centered map adds a real geometric control: its comparison with translation changes spread at a matched weighted mean and still worsens energy in every specified original and later view. These are additional measurements with outcomes that were not determined by the explanatory wording.

The appropriate contribution remains a strong, bounded empirical diagnostic rather than a new general evaluation principle or an identified explanation of model behavior. Conditional and marginal evaluation can disagree in established literature. Here the useful addition is a concrete repeated-prompt demonstration, with fitted benchmarks, a temporal contrast, a controlled centering comparison, and a correction for finite repeats. The later translation result depends on representation, the new analyses were developed after outcomes were available, and the conditional-mean interpretation needs error assumptions that cannot be established from three repeats. Those limits affect scientific reach even though most finite-cloud comparisons are directly verifiable.

I found no fatal scientific defect in the stated finite-panel conclusion. I recommend the focused reporting/access corrections below before calling the revision complete. I do not recommend adding another large retained-vector analysis solely to improve review scores. No additional human ratings, image generation, acquisition or feature extraction is needed to correct the identified manuscript defects.

## Claim–evidence map

| Claim | Evidence and location | Assessment |
| --- | --- | --- |
| Generated/reference collections differ across all four painters, and named clouds have lower spread. | Section 4, Figure 1, Tables 2–3 and Appendix B: all 24 trace ratios are .206–.376; RBF balanced accuracy is .940–.983; matched-size reference/reference medians are much lower than generated/reference medians. | **Strong for the recorded collections.** Content, capture and service differences prevent stylistic or oeuvre-wide interpretation. Only Sisley's pooled exploratory named median improves over its free control; this contrary ordering remains visible. |
| Adding a painter clause improves primary reference proximity in the controlled cohorts. | Section 5.3, Figure 2, Table 4: all six naming contrasts are negative, with four Holm rejections in the original eight-test family. | **Strong conditional evidence.** Pair-swap inference incorporates the full energy statistic and conditions on the fixed panel and assignments. It still requires the stated no-interference assumption. The OAuth non-rejections remain unresolved. |
| Actual naming is closer than the fitted translation/scale benchmark on original held-out data. | Section 6.2, Figure 3A and Table 17: all six primary fold-averaged residuals and all 60 view-level averages are negative. Individual folds reverse in five cells; OAuth/Cézanne's delete-one mean range crosses zero. | **Strong descriptive support for the averages, not uniform scene/fold superiority or rejection of a composite model class.** The main results paragraph states this correctly; abbreviated summaries should retain the averaging qualification. |
| A translation fitted to the original FLUX cohort can transfer better than actual naming in reference energy. | Section 6.3, Figure 3B: later primary translation energies 1.470/.736 versus actual named 1.571/.820. Translation wins in 15 of 18 views, with all three 256-pixel Monet views reversing. | **Moderate transfer evidence with strong finite-cohort arithmetic.** Maps are unchanged, but the diagnostic is post-result and the later cohort reuses the templates and references. This is not an unexposed new-scene validation. |
| The fitted scalar can worsen reference proximity even after matching the transformed means. | Section 6.4, Equation 7 and Table 7; centering report: centered-minus-translation energy is positive in all 60 original and 18 later views. Later primary increases are .591 and .254. | **Strong geometric comparison.** The added map isolates a scalar change at the specified common mean. It adapts to evaluation-free data and does not isolate an internal generative cause, an optimum scalar, or a unique causal decomposition. |
| Better prediction of named conditional means need not improve painting-reference proximity. | Section 7.2 and Table 9: shift/scale has lower corrected conditional-mean residual than shift in all six primary cells; its reference energy is higher in five. | **Strong descriptive target disagreement under the correction's assumptions.** The two targets use different units and are not combined into one score. The result is not merely inferred from aggregate contraction. |
| Corrected scene variance contracts, while retrieval can improve or decline; a scalar signal/noise ratio does not explain every retrieval change. | Equation 8, Table 8 and Figure 5: corrected between-scene ratios are below one under both weightings. FLUX/Monet retrieval rises 44.4% to 59.7% despite an equal-scene named/free ratio of corrected signal/noise of .937. | **Strong observed retrieval result; moderate latent-component interpretation.** The paper correctly distinguishes equal-scene .937 from reference-weighted 1.107. Corrected estimates require stable independent errors; traces do not measure directional or local decision geometry. |
| More reference-neighborhood hits need not mean lower reference energy. | Section 6.5: later primary shift/scale occupancy .605/.750 exceeds actual naming .526/.719 despite worse energy. | **Strong finite-panel counterexample.** It is not proof of a metric defect or a representation-invariant advantage; the paper acknowledges view reversals and distinguishes this design from matched-real coverage. |
| Additional painter-name attenuation beyond a generic clause remains unresolved in both palette collections. | Section 8, Figure 6, Appendix E and Table 16: both original and both later intervals cross zero; the original and new inferential families are distinct. | **Supported.** Secondary generic-minus-free effects cannot identify a painter-name mechanism or convert non-rejection into equivalence. Six fixed scenes and two palette extremes limit precision and explanation. |
| Computational challenges and numerical replay support a limited measurement interpretation. | Section 9, Figure 7, Appendices G–K and the preceding public-release report. | **Strong for measured processing responses and the established numerical replay scope.** Nonselective responses, absent pixels and unavailable capture authentication remain consequential. The new central analyses are locally traceable but are not yet identified by a public add-on in this frozen manuscript. |

## Specific strengths

### S1. The new benchmark separates scientifically different targets

Section 6 and Table 9 ask both whether a transformation predicts the named output distribution and whether its outputs approach the painting references. These questions can now be compared using the same retained observations rather than through disconnected summaries. In particular, the six-versus-five ordering is a concrete result that would be useful to another evaluator deciding what a distributional improvement establishes. This is the main reason the contribution score increases.

### S2. Whole-scene fitting addresses a real optimistic-comparison risk

The maps use generated training observations, and the evaluation scenes are excluded completely. Reference vectors do not fit the means or scalar; only the fixed reference-derived content masses enter the weighting. Separate evaluation of each fold avoids introducing map-estimation variation by concatenating differently transformed clouds. Section 6.1 and Appendix J also explain why these 18-query energies cannot replace the original 72-query estimates. The plotted opposite-sign folds and the weak OAuth/Cézanne residual prevent the average result from hiding instability.

### S3. The centering successor resolves an actual ambiguity

The original-map difference included a center change proportional to the mismatch between training-free and evaluation-free means. Equation 7 removes that ambiguity for the specified comparison. The .591/.254 increases at the common mean, and the separate old-center offsets, are informative outcomes rather than a new label for the old result. The text correctly avoids applying the independent-repeat conditional correction to this evaluation-dependent map. The inclusion of the adaptation and path-dependence qualifications makes the comparison technically interpretable.

### S4. Finite-repeat correction improves the substance of the conditional analysis

The earlier observed between-scene component mixed true scene-mean variation with repeat noise. Equation 8 and Appendix J now state the relevant expectation and subtract the estimated noise contribution. The cross-repeat residual calculation also removes the diagonal noise term from held-scene prediction. Negative values are retained, and training-parameter uncertainty is not falsely claimed to have been removed. The equal-scene versus reference-content distinction is particularly important for the FLUX/Monet retrieval example.

### S5. The scientific record remains broader than the favorable main comparison

The revised article retains Monet, Sisley, Pissarro and Cézanne, all eight original primary tests, the four later endpoints, both unresolved palette findings, missingness, feature-view reversals and capture limitations. It distinguishes exploratory naming contrasts from the later controlled intervention. The resulting conclusion does not silently substitute the favorable Monet/Cézanne experiment for the four-painter descriptive result.

### S6. The figures expose relevant variation and use clear denominators

All nine figures are readable in the rendered PDF. Figure 3 shows individual folds as well as averages, Figure 5 identifies held-repetition query counts, and Figure 7 displays cross-family processing responses rather than only favorable diagonal comparisons. Tables 7–9 make the new center, correction and target comparisons inspectable. The original numerical release provides actual public replay for its stated scope, not just an unverified promise of code.

## Weaknesses and residual limitations

### W1. The conceptual contribution is useful but still an application of established distinctions

**Where:** Introduction, Section 2, Sections 6–7 and Discussion. The paper now accurately acknowledges prior conditional evaluation and complexity/diversity work. The headline distinction between proximity and conditional organization is therefore not itself novel. The new value is the measured behavior of a particular fitted benchmark on these painting comparisons. The manuscript supplies an instructive empirical case, but does not yet establish when another evaluator should expect translation, scale or actual naming to win.

**Impact and response:** This is a genuine significance limit, not a demand for a different paper. Foreground Table 9's target disagreement and the matched-mean comparison as the concrete contribution. Avoid making the broad principle carry novelty that belongs to the bounded experiment. Better wording alone cannot turn it into a new general theory.

### W2. The empirical benchmark has a narrow and outcome-exposed validation domain

**Where:** Sections 5.6, 6.1–6.4 and 10.2. The original held-out scenes are part of a previously inspected 24-scene set, and the later cohort reuses those scene templates and exposed references. Map classes and the centering diagnostic were selected after preceding outcomes were known. Held-scene computation reduces direct fitting optimism, but does not make this a prospectively selected benchmark tested on untouched scenes. Its descriptive residuals also have substantial fold variation, and the temporal translation ordering changes in the 256-pixel Monet views.

**Impact and response:** The fixed-cloud comparisons remain valid; the limitation concerns reliability outside this selection and the strength of a predictive account. Keep transfer described as a post-result fixed-map diagnostic of a later cohort. An independently specified new-scene evaluation would add information that more overlapping retained-data views cannot. It is a future study, not a prerequisite for accurately reporting the present counterexample.

### W3. Corrected conditional organization depends on unverified repeat-error structure

**Where:** Equation 8, Table 8, Table 9 and Appendix J. Three repetitions provide an estimate of scene noise, but do not establish stable independent errors across repeats and scenes. Shared service state could affect both the noise subtraction and the conditional-mean residual. The later FLUX cohort has no repeated outputs with which to assess the corrected quantities independently. A ratio near one, such as .937, is also an estimated scalar summary rather than calibrated evidence against every signal/noise account.

**Impact and response:** The observed coexistence of contraction and changed retrieval is secure; inference about underlying conditional means is more assumption-dependent. Retain that distinction. Existing per-fold corrected differences can show where Table 9's mean ordering comes from, but additional precision machinery should not be presented as verification of service independence. A repeated new cohort would address a different uncertainty from feature-view sensitivity.

### W4. The reference target and geometry limit the practical interpretation of a benchmark win

**Where:** Sections 3, 5.1, 9 and 10.2. The 70-work panel is selected, broad content labels are maintainer-LLM annotations, and texture contributes nearly half of primary reference trace. Common-square comparisons change visible content and do not remove unknown photographic differences. A translated feature cloud need not correspond to feasible images, and a lower energy score has no validated perceptual unit.

**Impact and response:** This limits what the useful comparison can recommend about image generation or painting fidelity. It does not invalidate the explicitly defined digital-feature target. The no-LBP and no-texture views are meaningful checks, but are not independent measurement validation. Preserve the present bounded interpretation; do not add unsupported artistic claims to strengthen significance.

### W5. Several fixable reporting and access defects remain in the frozen revision

**Where and fixes:**

1. **Original Study 2 delivery metadata was lost during condensation.** Appendix E.2 ends with all 192 requests succeeding but no longer reports that all were nonsquare PNGs or that 174 reported low and 18 medium quality. The later collection still says “As in Study 2” and reports its own arm counts. Restore the original delivery and arm-quality summary from its retained report. Condition-dependent delivery is part of the paper's service-response estimand, so this is more than cosmetic history.
2. **Abbreviated held-scene claims overstate the granularity.** The introduction, Discussion 10.1 and conclusion say that actual naming outperforms the map “on” the original held-out scenes. Section 6.2 is precise that these are six fold-averaged wins, with opposite-sign folds. Use “in all six primary held-scene averages” in the summaries too. This is a small correction, not a reversal of the result.
3. **New-analysis access is underspecified.** Data availability calls the new study “the moment-map diagnostic” but supplies neither its exact namespace/run identifiers nor the corresponding replay entry point. Appendix K describes the preceding release only. Name both versioned studies and give a portable reproduction route for the files accompanying this revision. An additive public archive should only be cited after its access and replay have been verified; the unchanged old archive must not be described as containing the new results.

These can be fixed with retained documentation and release work. They do not require changing frozen evidence or collecting images.

## Literature positioning

The three nearest methodological references are now cited fairly. I reopened their primary sources for this round and checked the new bibliography entries. My earlier art-literature reading also informed the assessment of Section 2; this round's targeted recheck focused on the newly central evaluation claims.

- **Benny et al., IJCV 2021, Sections 3.1–3.3 and Theorem 2:** establishes the need for conditional evaluation and separates class-mean from within-class aspects. The revised paper treats this as prior conceptual groundwork, without importing its FID theorem into energy discrepancy or presenting the finite-repeat correction as that theorem. The contribution here is a concrete benchmark and empirical target disagreement. [Primary article](https://link.springer.com/article/10.1007/s11263-020-01424-w).
- **Zhang et al., arXiv:2510.19557v1, Sections 3–4:** already finds that greater prompt specificity can reduce conditional diversity while improving reference-based distribution measures. Thus coexistence of lower diversity and better proximity is insufficient novelty. This paper's scene-fixed painter clause, generated-only held-scene maps and center-controlled reference comparison offer a distinct empirical test. The bibliography correctly identifies the 2025 v1 record. [Primary full text](https://arxiv.org/html/2510.19557v1).
- **Khayatkhoei and AbdAlmageed, ICML 2023, Sections 3–5:** analyzes neighborhood-measure asymmetry and explicitly connects its complement recall to coverage. It is relevant to interpreting radial transformations and occupied neighborhoods. The revised manuscript correctly does not claim that their asymptotic construction proves a distortion in this finite, correlated 31-dimensional panel. [Primary paper](https://proceedings.mlr.press/v202/khayatkhoei23a/khayatkhoei23a.pdf).

The primary HTML articles and conference PDF were accessible. I have not performed an exhaustive systematic literature search or established priority against every related study. No conclusion relies on search-result snippets alone. I found no remaining obvious mischaracterization of these closest sources.

## Prioritized actions and what would add evidence

1. **Complete the reporting/access corrections in W5.** Restore Study 2 delivery details, qualify the held-scene summaries, and identify the exact new analysis/replay artifacts. Keep the preceding public release immutable.
2. **Make the new scientific center easier to find.** Add a concise discussion sentence explicitly connecting Table 9's opposite map orderings to the matched-mean result. The abstract already mentions the target disagreement, but Discussion 10.1 emphasizes actual-versus-map proximity and retrieval more than the direct comparison of prediction targets. This is a clarity improvement, not additional scientific evidence.
3. **Remove avoidable PDF whitespace.** Page 34 contains only four lines and the remainder is blank; inspect the long `samepage` span through Appendices H–K when correcting pagination. No clipped equations, unreadable figures, missing citations or overlapped tables were found. This is a minor layout issue, not a statistical concern.
4. **Do not add a new broad analysis by default.** The previously important retained-data question—whether scale or the old center accounts for the transfer penalty—has now been answered by the centering successor. Its stable fixed-mean penalty is actual added evidence. Reporting the already retained per-fold differences underlying Table 9 could compactly expose the stability of that particular target disagreement, if desired, without new tests or scalar selection. It would not establish new-scene generalization or verify repeat independence.
5. **For a future increase in scientific reach, test a fixed diagnostic on new scenes.** A separately specified scene panel and independent captures would discriminate stability of the empirical result from dependence on these templates and reproductions. Intermediate palette instructions address a different unresolved response-function question. These are future studies outside this retained-data revision, not requests to reopen terminal collections.

## Verification performed and limits

- Read the complete TeX, appendices and bibliography; inspected all 36 rendered pages, then each of the nine figure pages individually. The supplied PDF and TeX hashes remained unchanged throughout this review.
- Read the new centering protocol and complete report, the prior geometry protocol/report and relevant bound numerical results, and the preceding public-reproducibility report. The geometry and centering result/report hashes match their receipts. Geometry source binding: `459c6a88a10a209ba22619dc38d616588da8817c`; centering source binding: `c390eef639ef8770230243bf5989ef93c84ec8d6`.
- Ran `uv run --locked pytest -q tests/painter_naming_geometry_v1 tests/painter_naming_centering_v1 -m 'not live'`: **95 passed in 3.46 seconds**. This checks the relevant existing offline suite without implementation edits. Passing tests is not independent verification of service assumptions or of absent source pixels.
- I did not implement or perform a fresh independent reconstruction of the new algorithms, rerun image extraction, access image services, authenticate acquisitions, or publish the new add-on. Existing public reproduction is credited for its verified predecessor scope; new public access is not assumed from local files.
- The review changes documentation only. It does not alter frozen protocols, manifests, reports, user-owned Korean manuscripts or the public archive.

## Scores under the unchanged rubric

| Aspect | Score / 10 | Justification and change from my round 1 |
| --- | ---: | --- |
| **Scientific rigor** | **8.8** | Up from 8.4. Whole-scene fitted comparisons, unchanged-map transfer, the explicit common-mean scalar control and finite-repeat correction improve the evidence supporting the central interpretation. The score does not reward the number of views or caveats. Outcome-exposed diagnostic selection, unverified error structure and representation/reference dependence remain substantive limits. |
| **Contribution and significance** | **8.3** | Up from 7.4. Table 9's direct target disagreement and Table 7's geometric control convert the earlier collection of descriptive findings into a useful evaluation case. They are new empirical evidence. Conditional-versus-marginal distinctions themselves are established, and the paper does not yet give a broadly validated prediction of when these outcomes occur. It is strong empirical work with limited reach, not a new general principle. |
| **Clarity and reproducibility** | **8.8** | Up from 8.7. The new central question, readable benchmark figure, corrected-variance table and explicit units/fold definitions improve coherence. This modest increase is offset by the omitted delivery summary, compressed fold-average wording, incomplete new-analysis access instructions and avoidable blank page. The verified old public release is substantive credit; the pending add-on is not. |

**Arithmetic mean: 8.6333/10.** These scores assess the frozen round-2 manuscript and have not been adjusted to meet a target. Corrections made after this snapshot require their own identified record; this review must not be rewritten to imply that they were already present.

**Overall recommendation:** Strong empirical manuscript with focused reporting/access revisions; no fatal flaw identified for its stated computational scope. This is not an editorial acceptance decision or a prediction for an unspecified venue.

**Contribution level:** Useful and substantive empirical advance within a narrow domain; moderate general significance.

**Confidence:** High for claim/text correspondence, the principal algebraic distinctions and figure inspection; moderate for the latent conditional-mean interpretation and literature-wide novelty. My methodological advice and the absence of an independent implementation reconstruction are material review limitations.
