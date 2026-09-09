# Academic manuscript review — round 2, reviewer 3

## Metadata, independence and scope

- **Title:** Painter Naming and the Distributional Gap Between Generated Images and Original Paintings.
- **Authors:** Anonymous authors; affiliations unspecified.
- **Status/year/domain:** Local 2026 empirical manuscript in computational art analysis and text-to-image evaluation. No selected publication venue.
- **Reviewed source:** Entire `paper/paper.tex`, all 1,385 lines including appendices.
- **TeX SHA-256:** `83deb0b17af76c82d6a9899edaee9359a128ef0c31832746771fd87acda5539d`.
- **Reviewed PDF:** 25 pages, seven figures.
- **PDF SHA-256:** `d4f731b6487a932543b943f93b5cbb95b47126cff581f3bd5f8785c0f9f2ac4c`.
- **Review date:** 10 September 2026 KST, continuing the review cycle begun on 9 September.
- **Rubric:** The same three aspects and anchors in `RUBRIC.md`; all three are independently scored below.

**Disclosure:** I am a maintainer-run LLM subagent. Between rounds I implemented `paper/replay_palette.py` and its new tests at the coordinator's request, including the ordered-block figure and descriptive variance-share output. This round is consequently a maintainer-run LLM revision assessment involving implementation assistance, not a neutral independent external review. The coordinator and reviewer 1 were assigned separate checks of that implementation. I have not read their review reports, the coordinator's aggregate assessment, or their scores. Technical messages about request ordering and independently calculated block quantities were exchanged during implementation; this is disclosed collaboration, not independent evidence from another study.

I re-read the complete revised source in consecutive ranges and inspected every rendered PDF page. Pages 17–25 received direct page-level inspection, particularly the added specification, Appendix E and Figure 7. Main-text pages were additionally inspected in contact sheets. No paper, code, figure, frozen input, or earlier review was changed during this assessment.

## Executive assessment

The revision improves the paper's explanation and auditability while leaving its substantive scientific limits essentially unchanged. The added named/free/real coverage table corrects an incomplete presentation of the prompt effect: naming generally increases reference-neighborhood coverage even while the generated distribution contracts. The manuscript now lets the reader assess both improvement and remaining discrepancy together. Explicit development-painter counts, exact exploratory prompt/control construction, the expanded feature specification, and the corrected Deliège comparison also improve interpretation.

The new compact replay removes a real practical obstacle for one clearly bounded task: a reader with the code and three compact inputs can recompute Study 2's primary estimates and intervals without possessing the response archive. That is actual computational utility, beyond a promise of future access. It is not public release, transport verification, image remeasurement, validation of the feature geometry, or independent replication. Figure 7 helps the reader see the block variation underlying the six scene means, but cannot verify repeat independence or improve the primary confidence intervals.

My assessment remains that this is a strong, bounded empirical study with a moderate contribution. I raise only clarity/reproducibility. The unchanged scientific-rigor and contribution scores reflect the unchanged acquisition, measurement validity, precision, transfer, and public-access evidence. No venue recommendation is inferred from the scores.

## Claim/evidence map

| Claim | Revised evidence | Assessment |
| --- | --- | --- |
| All four painters show lower generated full-feature spread and detectable collection differences. | Section 4; Figure 1; Tables 2–3 and 8. | **Strong for the observed feature collections.** The 24 trace and discrimination summaries are unchanged. Capture, geometry and content differences remain possible explanations; this is not a validated artistic-style distinction. |
| Naming lowers Study 1 primary energy discrepancy. | Sections 5.1–5.3; Figure 2; Table 4; Appendix C. | **Strong conditional evidence.** Six negative point contrasts and four Holm-adjusted rejections remain unchanged. The assignment-based interpretation still requires the stated no-interference and availability/retry assumptions. |
| Naming improves joint painter alignment. | Section 5.4; Equation 4; Table 5; Appendix D.2. | **Moderate descriptive evidence.** Equal-class double contrasts and robustness directions support a joint pairing improvement, not individual nearest-painter success or an independently estimated population effect. |
| Naming generally improves reference coverage while leaving a gap relative to real queries. | New Table 6 and corresponding abstract, Section 5.4, discussion and conclusion. | **Strong correspondence to saved descriptive summaries.** I checked the 12 named/free medians and real baselines against `heldout_real_controls.csv`: five increases, one tie, and every named median below the real median at k=3. Sensitivity to neighborhood size and reused finite panels remain. |
| Aggregate contraction does not determine scene distinguishability or within-scene spread. | Sections 5.5–5.6; Figures 3–4. | **Strong descriptive counterexamples.** Unchanged OAuth/Cézanne and FLUX/Monet results establish the claimed coexistence within these data, not a universal response law. |
| Study 2 leaves additional named-minus-generic effects unresolved. | Section 6.3; Figure 5; Appendix E; compact numerical replay. | **Strong support for the reported uncertainty statement.** The same −.284 and −.018 estimates and zero-crossing simultaneous intervals are reproduced. Approximate fixed-scene inference and limited repeats still constrain conclusions. |
| The apparent consistency of Monet scene means conceals mixed block signs and uneven uncertainty contributions. | New Appendix E.1 and Figure 7. | **Strong descriptive support.** All 24 blocks are displayed; 17 Monet blocks are negative, and the stated 25.7%/44.5% scene variance shares agree with the unchanged stratified variance calculation. No extra sign test, block deletion or independence claim is added. |
| Study 2 inference can be replayed without raw responses. | Data/code availability; Appendix G; `make palette-check`. | **Supported, narrowly.** Three pinned compact files suffice for calculation parity with the frozen inference primitive. The manuscript explicitly keeps source-response integrity and pixel remeasurement separate. External availability is still pending. |

## Strengths

1. **Controlled design and complete test reporting remain substantial strengths.** The original paired scene intervention, complete eight-test Study 1 family, Study 2 shared controls, and explicit conditional versus approximate inference retain the sound features identified in round 1. The revision does not replace nonrejecting results with a convenient sensitivity result.
2. **Coverage now has the relevant comparison in the main text.** Table 6 on page 10 gives artist-free, named and held-out-real medians side by side. This prevents readers from confusing a remaining absolute reference gap with a worsening under naming. It also makes the main empirical combination—lower spread, greater coverage and lower discrepancy—clearer.
3. **Methods now specify consequential measurement and prompting choices.** Section 3 identifies all development-painter counts and same-painter scaling. Appendix A.1 specifies the chroma mask, hue bins, CIEDE2000 lags, luminance, spectral window/bins, gradient histogram, wavelet family and LBP settings. Appendix A.3 differentiates the three exploratory control wordings from Study 1's intervention. The source paths in Appendix G make the remaining numerical constants traceable.
4. **The block display exposes the small experiment's actual unit of variation.** Figure 7 uses a common vertical scale, retains all points, distinguishes the six scenes, and shows collection-block order without fitting a smooth temporal curve. The caption's qualification is appropriate. The figure strengthens transparency without making the 192 images appear to be 192 independent interaction observations.
5. **The compact replay has a real, bounded use.** During implementation I verified the two saved primary rows exactly, checked the figure deterministically, and ran an isolated-root test containing only three compact data files. Input corruption, duplicate/missing/nonfinite outcomes, treatment mismatches, reordered schedules and parity failures are rejected. These checks establish a usable numerical route; they do not validate the upstream measurements.
6. **Literature positioning is more accurate.** Section 2 correctly distinguishes Deliège's knowledge-based historical ratings from this paper's explicit reference panel, and Section 5.2 directly credits the coverage construction to Naeem et al. The manuscript claims a controlled empirical characterization rather than a new metric.

## Weaknesses and residual limitations

### W1. Artistic measurement validity is still unestablished — substantive, unchanged

Section 7.2 and Appendix D.4 correctly retain the unknown capture workflows, square/nonsquare domain split, condition-associated delivery differences, and strong texture contribution. A better parameter specification makes the measurement reproducible; it does not establish what that geometry measures about artistic resemblance. There is still no independent content/reference adjudication, perceptual calibration, or complementary learned-feature validation. These limitations constrain practical significance even for an accurately computed finite-panel study.

### W2. The primary color experiment remains limited in precision and transfer — substantive, unchanged

The two primary intervals are unchanged. The new block plot exposes variation but supplies no new repeats, collection sessions, generic phrasings or scenes. Six scene means, four repeats each, one short service collection and approximate error assumptions still cannot resolve broader painter-specific attenuation. The single generic phrase remains a particular aesthetic instruction, and delivered rendering changes remain inside the service-level estimand. This is not remedied by displaying 17 negative blocks or by documenting model assumptions.

### W3. External reproducibility is still incomplete — substantive access limitation

Data/code availability continues to state that public archival release is pending and external raw-media access has not been arranged. The new replay can be executed by someone who receives the files, but this review has not established that an external reader can obtain the full reviewed package at a durable public revision. It also recomputes results from retained chroma values rather than independently remeasuring them. Actual release and an access arrangement remain necessary for the stronger reproducibility claim.

The distinction between scientific and presentation code is now explicit, addressing the principal wording defect from round 1. Before release, “with this revision” should resolve to a durable identifier for the complete current manuscript/build package. It does not yet do so in the manuscript itself.

### W4. Contribution remains useful and incremental — unchanged

Distributional proximity, spread and coverage are established evaluation distinctions. The scientific addition is the repeated-scene naming intervention and its observed joint behaviors, including heterogeneous retrieval and the generic-control result. The revision reveals these results better, but supplies no new validated metric, causal mechanism, independent replication or general principle. This is a reason to preserve the contribution score rather than award novelty credit for adding a tool.

### W5. A bounded layout defect remains; the build-guide defect was resolved

- **Build guide, resolved before finalizing this review:** The initial inspection found obsolete page/figure counts and missing compact-replay guidance in `paper/README.md`. I inspected the coordinator's subsequent update: it now states 25 pages/seven figures, names the three pinned input paths, documents `make palette-check`, and distinguishes numerical replay from archive/pixel verification and public availability. This concern is closed; the manuscript hashes above did not change.
- **Appendix E opening:** At the bottom of page 21, the heading and variable-definition paragraph are separated from the covariance formula at the top of page 22, splitting the explanatory sentence. Keep that opening unit together. I found no clipping, unreadable mathematical symbol, missing legend, or incorrect plotted axis. The similar ordinary paragraph continuations elsewhere are minor and do not justify wholesale reflow.

These are editorial/packaging matters, not grounds for changing scientific inference or commissioning additional analyses.

## Qualitative methodological assessment

| Criterion | Round 2 assessment |
| --- | --- |
| Soundness | The finite-feature estimands and original inference remain coherent. New descriptive calculations are tied to the existing fixed-scene estimator and do not alter it. Measurement validity and service assumptions remain unresolved. |
| Experimental design | Strong within-scene prompt controls and finite-sample reference baselines. Selected painters, coarse annotation, rendering differences, small reference strata, and one limited Study 2 collection remain material restrictions. |
| Statistical reasoning | Multiplicity and inferential units are clearly reported. New coverage comparisons and block quantities remain descriptive. No uncertainty is manufactured for alignment and no time-series or independence conclusion is extracted from Figure 7. |
| Clarity and traceability | Materially improved by Table 6, the parameter/prompt specification, explicit development composition, corrected literature and separation of scientific/presentation code. The build guide is now synchronized; the Appendix E break remains a minor defect. |
| Reproducibility | Better actual numerical replay from compact data, with strong input checks. Still conditional on receiving the package; it does not reproduce measurements or verify transport and does not establish public release. |
| Contribution and practicality | Useful empirical characterization and a modestly easier checking path. No new evidence for generality, artistic validity or mechanism has been added. |

## Fixed-aspect scores and change explanation

| Aspect | Round 1 | Round 2 | Explanation |
| --- | ---: | ---: | --- |
| Scientific rigor | 8.0 | **8.0** | Unchanged. The new coverage display and block diagnostics improve access to the evidence, but the principal design, feature validity, precision, error assumptions and population limits are unchanged. The replay checks calculation; it is not a new validation study. |
| Contribution and significance | 7.4 | **7.4** | Unchanged. The empirical argument is more legible, and prior work is more accurately positioned, but neither a new substantive result nor new artistic/causal validation has been supplied. Implementation effort is not novelty. |
| Clarity and reproducibility | 7.8 | **8.3** | **+0.5.** The revised manuscript now shows the relevant named/free/real coverage comparison, identifies consequential feature/prompt parameters and development composition, corrects the nearest literature description, distinguishes scientific from presentation files, and supplies a working archive-free numerical replay for Study 2. These are concrete improvements in interpretation and use. Pending public release, missing media access, the unspecified durable presentation revision and small handoff defects keep the score below the exceptional/only-minor-limitations anchor. |

**Reviewer mean:** (8.0 + 7.4 + 8.3) / 3 = **7.9000/10**, up from 7.7333.

The increase is confined to clarity/reproducibility and does not reward limitation statements as if they supplied missing data. A subsequent layout-only correction would resolve the remaining minor defect but would not, by itself, justify another score increase.

## Questions and prioritized actions

**Questions:** Which immutable public identifier will bind the complete current manuscript/build package to the scientific snapshot? Which portions of the raw-response archive and image data can external researchers actually access, and through what arrangement? For future validation, is the intended target reliable finite-feature computation, human artistic resemblance, or a transferable prompt-response effect? These targets need different evidence.

**Actions feasible from retained material:**

1. Preserve the now-synchronized build guide and its explicit separation of numerical, response-integrity and pixel-remeasurement tasks when preparing the release. No additional guide correction is required from this review.
2. Keep Appendix E's opening definitions and covariance equation together, then verify the affected pages without changing formulas or estimates.
3. Preserve the explicit descriptive labels on Figure 7 and the coverage table, and attach the eventual immutable presentation identifier when the package is released.

**Actions requiring release or new study:**

1. Publish the exact code/data/presentation snapshot and implement a usable external-access policy. No extra disclaimer substitutes for this release work.
2. For claims about artistic resemblance, conduct independent content/style validation and address capture/geometry effects with appropriate controlled evidence.
3. For transferable responsiveness claims, prospectively add scenes, alternative generic phrasings and separate service collections with a precision target. Do not reopen or refill the terminal cohorts.

## Primary literature and review limits

The targeted primary-source literature search/read from round 1 remains applicable; I did not conduct a new broad search for this revision. The following sources were actually read, and the revised claims were checked against that reading:

- [Deliège et al. (2025), institutional full-text PDF](https://orbi.uliege.be/bitstream/2268/338186/1/jimaging-11-00429.pdf), especially Section 2.2.3 and discussion: historical ranges rely on experts' knowledge, while generated ratings use shown sets. The revised Section 2 now represents this distinction accurately.
- [Naeem et al. (2020), PMLR primary paper](https://proceedings.mlr.press/v119/naeem20a/naeem20a.pdf), Sections 1–3: real-neighborhood coverage and the distinction between fidelity and diversity precede this manuscript. Direct attribution in Section 5.2 is appropriate.
- [Parmar et al. (2022), author preprint v3](https://arxiv.org/html/2104.11222), introduction and Sections 3.1–3.3: preprocessing choices can affect image-feature comparisons. The expanded specification aids reproducibility but does not resolve unknown capture histories.

I re-read the entire revised manuscript, checked all 25 rendered pages, compared the new coverage values with the saved source table, and checked the added feature/prompt description against retained implementations. During implementation between rounds I ran 14 new replay tests plus 15 existing design/inference tests (29 passing), Ruff for the new files, isolated compact-input replay and deterministic figure checking. Those are explicitly my implementation checks, not independent external validation. The coordinator reports Ruff, 1,149 offline tests and 2,902 historical evidence checks passing with zero audit failures; I did not independently repeat those checks. I did not inspect raw artwork, remeasure images, regenerate outputs, conduct new human assessment or establish a public release.

Confidence is **high for manuscript scope, the reported revision changes, numerical correspondence of the inspected additions and visual presentation**; **moderate for complete scientific validity and literature completeness**. Implementation involvement reduces the independence of this revision assessment and is not concealed by the separate checks requested from other maintainers.
