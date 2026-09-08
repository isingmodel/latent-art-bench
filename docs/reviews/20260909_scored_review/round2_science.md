# Round 2 scientific review — 9 September 2026

This is an internal maintainer-run LLM subagent review of the whole manuscript,
with emphasis on construct validity, alternative explanations and scientific
contribution. It is not independent human or institutional peer review. I did
not consult other reviewers or coordinate scores.

Reviewed TeX SHA-256:
`2d28cec5b0bf7e62cb8e76338b4c3b52809c63c0ab6e8bb9aba4dced9a931a52`.

Reviewed PDF SHA-256:
`48bb8772bd0bf8da48c621de1610ce8e7a29690c5aeeb9b6e330c803daf87666`.

The base remains the working revision following baseline `f0fe89a`; the changed
TeX and PDF above, not that earlier commit alone, identify this review. I read
`docs/STATUS.md`, then `docs/ARTIFACTS.md`, and inspected Git status. Existing
manuscript, figure and review changes were preserved. This is an editorial review,
not shared-primitive work, an active census or a new study. Only this review file
was written.

I read the complete revised TeX and bibliography, inspected PDF previews for all
requested pages 14–20 and the principal results/figures on pages 6–9 and 11, and
checked the newly presented controls against the retained records inspected in
round 1. I also checked the new simulation table against the published
`simulation.csv` and the direct Deliège primary source.

## Scores

Same equal-weight rubric: 5 means substantial unresolved defects; 7 means sound
but substantial revision needed; 8 means strong with limited revisions; 9 means
publication-ready as a carefully scoped empirical paper; 10 means exceptional.

| Aspect | Score / 10 | Assessment of this version |
| --- | ---: | --- |
| 1. Research question and contribution | 8.5 | A clear finite empirical result now leads: improved relative painter alignment accompanies contraction and residual neighborhood mismatch. The contribution is more than the general fact that evaluation metrics differ. |
| 2. Study design and controls | 8.0 | Common-scene randomized contrasts, identical artist-free payload controls, equal-class joint alignment and matched-real neighborhood queries now support the actual central question. Selected sparse panels, service-dependent rendering and the one-sentence/two-endpoint color design remain real limitations. |
| 3. Statistical validity | 8.5 | Inference families, sharp versus weak nulls, finite retrieval dependence, shared controls, effective degrees of freedom and proxy calibration are accurately separated. The small-repeat color intervals still rely on deployment assumptions that the simulation cannot establish. |
| 4. Evidence and robustness | 8.5 | Main-text controls now substantiate both relative alignment and residual original/generated mismatch. Representation reversals, saturation and individual cross-painter preference are retained. The evidence remains from the same finite images and correlated feature views, without capture-matched or independent-service replication. |
| 5. Interpretation and claim calibration | 9.0 | The body consistently distinguishes finite alignment from individual painter identification, descriptive retrieval from population improvement, and response experiments from mediation. Two small summary-phrase corrections remain below. No major inferential overclaim remains in the substantive analysis. |
| 6. Literature and positioning | 8.5 | The directly overlapping corpus-level expert evaluation is now acknowledged, and the Asperti comparison identifies the actual intervention-versus-representation distinction. The incremental contribution is credible and appropriately modest. |
| 7. Reproducibility and transparency | 8.5 | Exact local snapshot, retained tables, commands and distinct replay/access boundaries are stated truthfully. Public release of the compact scientific snapshot remains pending; raw media access is unavailable externally. |
| 8. Structure, writing and figures | 8.5 | Separate methods/results for each study create a clear reading sequence. The alignment table and scene-level interaction dots strengthen the presentation. The appendices are readable but repeat some panel/collection information already given in the main text. |

**Arithmetic mean: (8.5 + 8.0 + 8.5 + 8.5 + 9.0 + 8.5 + 8.5 + 8.5) / 8 = 8.50 / 10.**

Overall assessment: a strong, carefully scoped computational empirical paper
with limited final revisions. I have no unresolved major numerical or logical
objection to the central result as now bounded. The increase from 7.75 reflects
the substantive use of relevant existing controls and a better-supported
research question; it is not a reward for length, effort, or additional caveats.
The scores do not imply that the unchanged design now answers broader artistic
or mechanistic questions.

## What is substantively resolved

### The central original/generated contribution is now supported

The central claim in the Introduction, §3.3 and Discussion is materially better
supported than the round 1 emphasis. The three joint named-minus-free alignment
changes (-.956, -1.707 and -1.758) are correctly presented as descriptive
equal-class contrasts, with cancellation of within-distribution energy terms.
The main text retains the decisive interpretive exception: NB2/Monet is nearer
the Cézanne reference panel (3.488) than the Monet panel (3.687), even though the
joint pairing improves. That prevents a reader from translating the joint result
into six individually successful painter matches.

The identical artist-free payload check and near-zero free alignment are useful
collection controls. The Discussion's explicit statement that this does not
reject a stochastic common-response model is correct. The finite double contrast
is evidence of observed differential alignment, not a newly confirmed universal
painter-specific mechanism.

The matched-anchor reference coverage results add a directly relevant comparison
under Study 1's ordinary detailed prompts. They are no longer displaced by the
artificial muted/vivid mixture. Main-text k=3 medians match the retained records;
Appendix D.1 gives disjoint anchor/query construction, class counts, equal query
sizes and k=1/3/5 sensitivity. The FLUX/Cézanne k=5 equality is visible. These
controls make the residual finite distributional mismatch empirically informative
without converting it into a stylistic or oeuvre claim.

The FLUX/Monet energy-term example also answers an important measurement question:
the decrease in the subtracted within-generated distance opposes the observed
energy improvement. The lower energy therefore is not mechanically obtained by
that decrease alone. This clarifies the evidence without adding a new test.

### The second study has a defensible supporting role

Study 2 is now clearly a separate fixed-scene, two-palette experiment, not a
mediation analysis of Study 1. The text consistently identifies the specific
traditional-landscape sentence as the generic control. The body does not imply
that its -.853 secondary interaction represents all generic language or isolates
artist identity independently of wording and rendering.

The two primary interactions remain unresolved. SEs, effective degrees of
freedom and numerical scale context show what the intervals still allow. The
-.585 Monet endpoint is correctly interpreted as roughly 22% of the generic
point response only for scale context, not as a confidence interval for a ratio
or a perceptual threshold. All six scene estimates per painter are visible in
Figure 4. The three proxy-noise calibration rows match the existing simulation
table and are explicitly limited to their simulated assumptions.

The forced palette mixture is now an appendix illustration with a short main
reference. It is no longer asked to explain the original/generated discrepancy
under ordinary prompts. That resolves my principal objection to its former role.

### Positioning and access claims are more accurate

The Deliège comparison accurately acknowledges a direct precedent for corpus-level
style comparison using expert intervals and relative shift, dispersion and
overlap across five movements and ten painters. The new paragraph distinguishes
the current controlled painter-clause intervention and within/between-scene
decomposition without claiming to replace expert construct validation. I checked
this against the [primary Deliège et al. paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12734345/).

The expanded Asperti (2026) paragraph is consistent with the primary source
checked in round 1 and no longer reduces the neighboring work to a generic CLIP
detector. The separate contribution of common-scene prompt intervention is clear.

The availability statement names the repository and local snapshot, explicitly
says that public archival release is pending, and distinguishes numerical
rebuilding from raw-hash replay, image remeasurement and service regeneration.
This resolves the earlier ambiguity. It does not yet make the local snapshot
externally retrievable; that remains practical release work.

## Remaining findings

### Two concrete wording corrections

1. **Avoid assigning causal consequences to contraction.** The abstract at
   `paper/paper.tex:34` says that the distributional changes have heterogeneous
   “consequences,” and the Conclusion at line 706 says that contraction has
   heterogeneous consequences for scene distinguishability. The body explicitly
   explains that contraction does not cause the observed retrieval outcome and
   that uniform rescaling preserves retrieval. Prefer “These changes are
   accompanied by heterogeneous changes in scene distinguishability” and
   “contraction coexists with heterogeneous scene-distinguishability changes.”
   This is a small but useful consistency fix, not a new objection to the data.

2. **Qualify the abstract's neighborhood-occupancy statement.** Lines 32–34
   summarize lower occupancy without the neighborhood setting. The main result
   is lower median matched coverage at k=3 (and k=1), while FLUX/Cézanne saturates
   at equality for k=5. Add “at k=3” or equivalent concise scope to the abstract.
   The main text and appendix already handle the sensitivity correctly.

### Substantive limitations that remain, without requiring a new study for this paper

The finite-panel target is scientifically defensible, but it does not establish
that the observed alignment reflects painter style rather than unmeasured
within-class subject matter, reproduction differences or prompt-associated
rendering. Sparse equal-class strata receive substantial mass: the documented
effective reference counts of about 24.0 and 18.8 are a useful reminder that the
nominal 70 works do not yield three large balanced classes per painter. No amount
of rephrasing can remove those alternatives.

The four-repeat follow-up remains a short single-service run. Its approximate
intervals assume stable independent repeat-block errors; randomized order,
complete retention and the proxy simulations make the analysis disciplined but
do not prove actual service independence. Two palette endpoints and one generic
sentence cannot distinguish response slope, saturation and wording effects.
The present manuscript correctly refrains from those conclusions.

The coverage controls, representation sensitivities and joint alignment reuse
the same generated images and selected reference panels. They address different
measurement questions but are not independent replication. The present claim
does not require calling them replication, and the manuscript no longer does so.

These are the main reasons I do not assign every design/evidence aspect 9 or 10.
They do not justify reopening terminal collection or adding post-result
confirmatory tests to the current manuscript. A broader claim would require a
new prospectively defined study, chosen for a specific scientific uncertainty.

### Presentation and release details

- The figures and requested final pages are readable. No clipped text, overlapping
  content or illegible table/figure labeling was apparent in the inspected
  previews. Figure 4's new gray scene estimates and blue family interval have
  distinct roles and a clear caption.
- Appendix A.1 repeats several main-method sentences almost verbatim. A light
  shortening is optional if a submission format imposes a length limit. The
  current 20-page document is understandable; extensive rewriting is unnecessary.
- Public archival release of the exact compact scientific snapshot should occur
  before representing the package as publicly available at submission. The
  current pending-release statement is truthful. No raw-artwork redistribution
  or new access promise should be invented to satisfy this review.

## Practical next step

Apply the two brief summary-wording corrections, verify the resulting TeX/PDF,
and finalize a concrete compact-data release plan consistent with the actual
access boundaries. Preserve the primary families and every unfavorable or
unresolved result. The manuscript's empirical core is now ready for an external
reader to assess on its stated scope; repeated major restructuring or additional
same-data hypothesis tests would not address the remaining design limitations.

The answer to the scientific question is **yes**: the existing data support an
interesting central original/generated distribution claim in the specified
feature space. Joint relative panel alignment can improve while the generated
collections contract and retain lower matched reference-neighborhood occupancy;
their repeated-scene responses are heterogeneous. The current manuscript now
shows the relevant retained evidence. New human ratings are unnecessary for that
claim. Perceptual fidelity, painter-population generalization and a mechanism for
the remaining gap still require different evidence.

## Verification boundary

Both reviewed file hashes were verified locally and match those supplied for this
round. I used the PDF skill for read-only visual inspection; no PDF was edited or
re-exported by this reviewer. The coordinator reports Ruff, a warning-free build,
and 1,135 offline tests passing in 115.43 seconds for this revision. I did not
rerun those completed checks, add tests, or conduct new scientific analyses.
No image acquisition, generation, feature extraction or human-rating collection
was performed.
