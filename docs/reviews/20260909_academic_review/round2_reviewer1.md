# Academic review — round 2, reviewer 1

## Metadata and scope

- **Title:** Painter Naming and the Distributional Gap Between Generated Images and Original Paintings.
- **Authors:** Anonymous authors; no affiliations supplied.
- **Status / venue:** Local empirical manuscript; no selected publication venue is assumed.
- **Domain / year:** Computational art and text-to-image evaluation, 2026.
- **Review date:** 10 September 2026, Asia/Seoul.
- **Source:** Complete current `paper/paper.tex`, all 1,385 lines including appendices, and the 25-page PDF.
- **Source SHA-256:** `83deb0b17af76c82d6a9899edaee9359a128ef0c31832746771fd87acda5539d`.
- **PDF SHA-256:** `d4f731b6487a932543b943f93b5cbb95b47126cff581f3bd5f8785c0f9f2ac4c`.
- **Rubric:** The same three fixed 1–10 criteria in `RUBRIC.md`; no criteria or weights changed.
- **Disclosure:** This is a maintainer-run LLM revision assessment, not neutral external peer review or independent human validation. Between rounds I supplied a read-only derivation and grouping/order check for the requested block display. Another maintainer-run LLM implemented the replay; I inspected and tested that implementation here. I did not edit the manuscript, frozen evidence or my round 1 review, and did not consult the other reviewers' assessments or the coordinator's score aggregate.

I reread the entire manuscript in consecutive untruncated segments. I visually inspected PDF pages 1–8 as assigned and additionally page 23 containing the new block figure. These pages have readable figures, tables and text without clipping or overlap. I read all of `paper/replay_palette.py`, its tests, the relevant frozen schedule validator, and the feature implementation cited by the new appendix. The coordinator reports 1,149 passing offline tests, passing Ruff and 2,902 historical evidence checks with zero failures; I did not duplicate those full checks. My independently executed checks are listed below.

## Executive assessment

The revision is clearer and easier to reproduce numerically. The main-text coverage table now shows an important part of the observed response: naming increases median reference-neighborhood coverage in five comparisons and ties in one, while all named medians remain below matched real medians at k=3. That makes the simultaneous reduction in spread more informative than an account focusing only on the remaining coverage gap. The expanded feature appendix also explains consequential measurement choices, and the new compact-input replay offers a working path to check Study 2's estimates without the private image archive.

The underlying scientific assessment remains similar to round 1. Study 1 supports conditional prompt effects in its fixed feature geometry, and the variance/retrieval examples demonstrate that aggregate contraction has no single implication for scene distinguishability. Study 2's estimates remain unresolved relative to the generic clause. Its new block display makes the observed variance more inspectable but cannot establish repeat-error independence, service stability or perceptual validity. The selected reference panels, unresolved capture and geometry differences, single generic wording and limited service replication still constrain significance and transfer. No blocking scientific, arithmetic or replay defect was identified.

## Principal claims and evidence

| Claim | Current evidence | Assessment |
| --- | --- | --- |
| All four exploratory generated collections differ from their references. | Section 4, Figure 1, Tables 2–3 and Appendix B: all 24 trace ratios below one, strong held-scene/disjoint-work discrimination, and matched-size energy gaps. | **Strong descriptive support** for these digital collections. It does not isolate stylistic causes or establish capture-source transfer. |
| Naming lowers primary reference discrepancy. | Section 5.3, Figure 2 and Table 4: six negative point estimates and four Holm-adjusted conditional sharp-null rejections. | **Strong conditional evidence** for four comparisons; negative but unresolved estimates for two. The paired statistic and inferential family remain unchanged. |
| Naming improves joint relative alignment and usually increases neighborhood coverage despite contraction. | Section 5.4, Tables 5–6, Appendix D: negative alignment changes on all services; k=3 coverage increases in five comparisons and ties in one. | **Moderate descriptive evidence.** The newly displayed coverage values agree with retained `heldout_real_controls.csv`. Sparse equal-weight strata and k-dependent neighborhoods remain relevant. |
| Total contraction does not determine repeat variation or retrieval. | Sections 5.5–5.6, Figures 3–4: OAuth/Cézanne within-scene ratio 1.139; FLUX/Monet retrieval 44.4% to 59.7% despite contraction. | **Strong finite-set counterexamples**, without new-scene inference or a semantic-adherence claim. |
| Additional painter-minus-generic chroma-response effects remain unresolved. | Section 6.3, Figure 5 and Appendix E: −.284 and −.018 with both simultaneous intervals including zero. | **Correct model-conditional conclusion.** Independent calculations and the new replay agree; small-sample assumptions remain unvalidated for the delivered service. |
| Block variability contributes unevenly to the reported precision. | Appendix E.1 and Figure 7: all 24 block contrasts per painter, Monet 17 negative, largest variance shares 25.7% and 44.5%. | **Correct new presentation of retained observations.** The figure supports inspection of variation, not an independence test or a new confirmatory result. |

## Independent replay and evidence checks

Both commands succeeded without opening images or response bodies:

```text
make palette-check
uv run --locked python paper/replay_palette.py --check-figure paper/figures/palette_blocks.pdf
```

I also calculated the block contrasts independently from the primary512 CSV rows, grouping by the explicit scene/repetition identities rather than relying on the new script's output grouping. Each of the 24 blocks contains all eight arm/polarity cells, and repetitions are numbered 0–3 in the retained data. For each painter I used

`K = (named_vivid − named_muted) − (generic_vivid − generic_muted)`.

All **48 block values** match the replay. A separate join with `collection_slots.csv` and `transport_attempts.csv` confirms the plotted block order: each block occupies eight consecutive sequence positions, actual transport starts follow the planned sequence, and all calls in a block finish before the next block starts. The script intentionally reads the schedule rather than transport metadata; the transport check supports the manuscript's statement that the actual collection order matched that schedule.

Independent scalar calculations recover scene means, standard errors, Welch degrees of freedom, simultaneous intervals and variance shares. The checked primary results are:

| Painter | Estimate | SE | Welch df | Simultaneous interval | Holm p |
| --- | ---: | ---: | ---: | --- | ---: |
| Monet | −0.284367715 | 0.120841017 | 15.24594083 | [−0.584714607, 0.015979177] | 0.064857047 |
| Cézanne | −0.017720927 | 0.123342047 | 9.91481111 | [−0.343056397, 0.307614543] | 0.888636789 |

The retained shared-control off-diagonal covariance is `0.011200734497355182`. Monet's garden contribution is 25.6938% of estimated variance; Cézanne's fields contribution is 44.5287%. The new figure is byte-identical to the replay's rendering. These checks establish agreement from retained measurements, not independent image remeasurement or empirical coverage of the intervals.

The script's use of the unchanged inference routine is appropriate for a replay. Its hash checks protect the three compact inputs, and its validation rejects missing, duplicated, unmeasured, nonfinite or identity-mismatched chroma rows. The new tests include a separate scalar-statistics calculation and compact-only input setup. I found no reason to replace the frozen inference or introduce another testing family.

## Assessment of prior findings

| Round 1 finding | Current disposition | What changed and what remains |
| --- | --- | --- |
| W1: measurement geometry and domain comparability | **Substantive limitation remains.** | Feature choices are now more inspectable, but no construct validation, capture common support or independent reference adjudication was added. Texture sensitivity and the NB2/Monet exception remain. |
| W2: Study 2 small-sample error model | **Presentation request addressed; design limitation remains.** | Figure 7 shows all blocks, and variance shares make concentration visible. This supplies useful inspection material but does not establish independent stable repeat errors across service collections. |
| W3: selected painters, scenes and wording constrain reach | **Remains.** | The new exploratory prompt construction explains the different controls particularly well. Neither painter transfer nor a general naming-versus-generic language effect has been tested. |
| W4: external reproducibility unfinished | **Partially addressed.** | The compact-input numerical replay works without raw responses. Public archival release and raw-media access remain pending, so outside access is still incomplete. |
| W5: feature definitions too abbreviated | **Addressed for this manuscript.** | Appendix A.1 gives the important thresholds, bins, scales and transform choices, and Appendix G identifies the exact implementation and scaler. Checked details agree with the implementation. Boundary constants can reasonably remain in the named versioned code. |

## Specific strengths

1. **A controlled prompt intervention with an appropriate distribution statistic.** Sections 5.1–5.3 and Appendix C preserve fixed scenes, randomized condition positions, common pair weights, the complete energy statistic and the original eight-test family. The result concerns an actual prompt contrast rather than uncontrolled corpus selection.
2. **Complementary controls and summaries produce a more informative result.** Sections 4 and 5.4 use sample-size baselines, own/cross-painter contrasts and matched held-out real coverage. Table 6 now shows that contraction can coexist with improved neighborhood occupation, so coverage is compared both against artist-free outputs and against references.
3. **Repeated scenes expose heterogeneous responses.** Figures 3–4 separate aggregate spread, repeat variation and scene retrieval. These contrasts support concrete conclusions that a single fidelity or variance number cannot supply.
4. **The uncertainty is now easier to inspect and calculate.** Appendix E.1 retains every block, while the compact replay reproduces the estimates and intervals from recorded chroma values. This is a functional improvement in numerical reproducibility, not simply a promise or a limitation statement.

## Remaining weaknesses and limitations

### W1. The measured gap still lacks validated artistic interpretation

Sections 3, 5.7 and 7.2 concern a fixed hand-selected metric whose dimensions have unequal and correlated contributions. The additional feature details explain the computation but do not establish the scientific importance of a unit in each coordinate. Texture remains influential, and one proximity direction changes under a non-texture view. Domain geometry and unknown reference capture also remain alternative sources of the gap. These facts limit what one learns about artistic resemblance even though the finite digital comparisons are correctly calculated.

**Needed improvement:** Independently selected/adjudicated references, capture and geometry common support where possible, and validation against relevant perceptual or visual criteria. This requires new research; merely adding another representation would not automatically establish ground truth.

### W2. Study 2 precision remains dependent on sparse repeat information and one collection

Appendix E estimates each scene's variance from four blocks and conditions on six fixed scenes. Figure 7 makes the variability visible, including the concentrated Cézanne variance, but it cannot establish independent or stable errors. The proxy simulation evaluates the stated procedure under its simulated conditions, not the service's realized dependence or tail behavior. Monet remains near a processing-sensitive rejection boundary and neither primary result establishes equivalence.

**Needed improvement:** Separate collection periods and more repetitions for precision, followed by new scenes or services for transfer. The present primary results should remain as reported; selecting blocks, treating 192 images as independent interaction observations or adding a low-powered independence test would not resolve the issue.

### W3. The empirical contribution remains bounded and largely incremental

The controlled painter pair was chosen after exploration, the reference panels are small and selected, and the exploratory named/free ordering differs from the controlled study. Study 2 tests one generic sentence and two extreme palette instructions. The work provides useful examples of how established distributional measures respond to controlled prompts, but it does not establish a general naming principle or explain Study 1 contraction. The better presentation of retained coverage results strengthens the account without proving broader transfer.

**Needed improvement:** A prospectively selected extension across painters/scenes and several generic phrasings if artist identity is the next target. Intermediate palette levels are needed only for a claim about response gain or saturation, not as a prerequisite for the present two-instruction estimand.

### W4. Public reproducibility is still incomplete

Data and code availability and Appendix G distinguish the older scientific snapshot from the current presentation scripts correctly. However, the archival release is still pending, and pixel access has not been arranged. The working compact replay is valuable preparation for external numerical checking; until the required materials are actually accessible, it is not equivalent to completed public reproducibility.

**Needed improvement:** Publish an immutable redistributable scientific snapshot together with the current manuscript/replay revision, then verify the numerical workflow from an external checkout. A separate restricted-input access process is needed for any offered image-level reproduction. This is a release task, not a new empirical experiment.

## Qualitative methodological assessment

| Criterion | Round 2 assessment |
| --- | --- |
| Soundness | Coherent calculations and estimands; no numerical contradiction found. New block values and feature descriptions agree with the retained inputs and implementation. |
| Experimental design | Strong within-inventory prompt comparisons and useful controls; source/domain comparability, selected references and independent service replication remain limited. |
| Statistical reasoning | Original randomization and multiplicity structure preserved. Study 2 shared-control covariance and stratified Welch intervals reproduce, but model validity for the actual service remains an assumption. |
| Measurement validity | Detailed and reproducible computational definitions; no new evidence of perceptual validity or capture invariance. |
| Reproducibility | Materially improved local numerical workflow. Public availability and pixel remeasurement remain distinct unfinished levels. |
| Scalability | No central scaling claim. The computations are suitable for the studied sample sizes, so quadratic distance/kernel costs are not a material objection here. |

## Literature positioning

This reassessment uses the primary-source reading completed in round 1; the revised contribution does not require a new literature claim. The corrected Deliège comparison agrees with its methods: the historical ranges are expert characterizations, not estimates from a fixed displayed historical-image corpus. This makes the present finite-reference, repeated-scene design a useful difference. [Deliège et al., primary article text](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12734345/fullTextXML).

The coverage construction and broader need for multiple distributional summaries are established methods. Their attribution is now directly attached to the coverage definition. [Naeem et al., PMLR paper](https://proceedings.mlr.press/v119/naeem20a/naeem20a.pdf). The preprocessing sensitivities remain motivated by evidence that resizing and compression affect generative evaluation, but common re-encoding cannot undo unknown historical capture. [Parmar et al., primary preprint v1](https://arxiv.org/html/2104.11222v1). The distinction between feature displacement and visual resemblance also remains relevant to the interpretation of the present representation. [Asperti, primary preprint v1](https://arxiv.org/html/2608.25609v1).

Access limitations are unchanged: the initial PMC browser page required verification and some publisher/PDF requests failed; Deliège's methods and discussion were retrieved through Europe PMC XML. Parmar's v1 preprint, not every change in the final CVPR version, was read. No claims here rely only on search snippets.

## Genuine remaining questions

1. Which immutable release will contain both the scientific snapshot and these later presentation/replay files, and can a fresh external checkout reproduce the two primary intervals without access to the response archive?
2. What independent validation would justify transferring this 31-coordinate metric to an artistic-resemblance claim, rather than treating it as a fixed digital measurement system?
3. If the next study targets general painter naming, how will painters, scenes and generic phrasings be selected prospectively, and over what service-collection periods will the result be expected to hold?

## Scores and reasons for changes

| Fixed aspect | Round 1 | Round 2 | Reason |
| --- | ---: | ---: | --- |
| Scientific rigor | 7.8 | **7.8** | The controlled design, measurements, retained primary inference and substantive assumptions are unchanged. Better inspection of the same variance does not add evidence of independence, construct validity or reference comparability. The checked new presentation is sound but does not remove those limits. |
| Contribution and significance | 7.2 | **7.2** | The controlled empirical account remains useful and moderately original. More explicit coverage comparisons improve its interpretation, but the general metrics are established and no additional validation, transfer experiment or explanation has been demonstrated. |
| Clarity and reproducibility | 8.0 | **8.4** | The feature definitions are materially more implementable, the coverage comparison is now complete in the main text, and a working compact-input replay makes the uncertainty calculations independently checkable from retained measurements. The block plot adds inspectable observations rather than another assertion. The gain is for these concrete capabilities, not compliance or additional caveats. Public access remains too incomplete for an exceptional score. |

**Reviewer mean: 7.8000 / 10**, compared with **7.6667 / 10** in round 1.

**Confidence:** High for the complete manuscript reading and computations checked; moderate for novelty across the entire computational-art literature and for unknown backend dependence. **Contribution level:** Moderate. **Overall assessment:** A solid empirical paper with an improved, useful reproduction package; no venue-specific acceptance prediction is made.

## Actionable residual defects versus future research

I found **no remaining blocking manuscript or replay defect** in the reviewed scientific claims. An initially stale `paper/README.md` was updated before this review was finalized. I inspected the correction: it now identifies 25 pages and seven figures, documents `make palette-check` and its three compact inputs, and distinguishes numerical reproduction, archive checks and public availability. That minor handoff issue is resolved without changing the scored manuscript or the scores above.

The remaining priorities are:

1. **Release:** Make the compact scientific snapshot and current presentation scripts externally accessible and check a fresh-checkout reproduction. This is the largest remaining reproducibility improvement available without new observations.
2. **New research:** Validate the representation and improve reference/capture comparability before advancing an artistic-resemblance interpretation.
3. **New research:** Collect independent service periods and prospectively selected extensions to address precision, wording and transfer.

Further editorial polishing alone should not be expected to raise the rigor or contribution scores materially. The current narrow computational conclusions can stand without replacing their unresolved results or reopening terminal collections.
