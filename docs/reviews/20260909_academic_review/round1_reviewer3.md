# Academic manuscript review — round 1, reviewer 3

## Metadata and review scope

- **Title:** Painter Naming and the Distributional Gap Between Generated Images and Original Paintings.
- **Authors:** Anonymous authors; affiliations not specified.
- **Venue/status:** Local empirical manuscript; no publication venue selected and no acceptance recommendation calibrated to an assumed venue.
- **Year/domain/type:** 2026; computational art analysis and text-to-image evaluation; empirical computational study with exploratory and prospectively specified components.
- **Reviewed manuscript:** `paper/paper.tex`, all 1,275 lines, including every appendix; 23-page `paper/paper.pdf`.
- **TeX SHA-256:** `8466d0374936f884371b3acfcb73db8a7311f8a10bd16a0689ade4284cdd0b90`.
- **PDF SHA-256:** `040e3f054314d0f1e0213eeffb32325da10bd43fcc342b6abf41759d1f6190ee`.
- **Working revision:** `1fcbcc5860aff18549e72095526e4baed4b82128`; scientific snapshot named by the manuscript: `28a9eb6`.
- **Review date:** 9 September 2026.
- **Reviewer role:** Maintainer-run LLM subagent, not independent human or institutional peer review. Primary emphasis: narrative, claim audit, and reproducibility. All three fixed rubric aspects are scored independently below.

I read `docs/STATUS.md` and `docs/ARTIFACTS.md`, the supplied academic-paper-review skill and current rubric. I did not consult other reviewers' reports or earlier review files. Mandatory status/build documents contain historical review summaries; these were not used as scoring targets. Manuscript reading used consecutive complete source ranges to avoid truncated-output gaps. I rendered the reviewed PDF anew and visually inspected all 23 pages, including all six figures, table continuations, appendices, and references. The manuscript, Korean drafts, scientific inputs, and raw media were not edited.

## Executive assessment

This is a strong, carefully scoped computational account of how painter naming changes several different properties of generated image collections. The most persuasive result is the controlled Study 1 comparison: changing the name clause while holding scene text fixed lowers primary energy discrepancy in six cells, with four adjusted rejections, while aggregate contraction has different within-scene and retrieval consequences. The paper makes a useful empirical distinction between closeness to a reference panel and matching its variation. Its generic-style control in Study 2 also prevents a tempting but unsupported attribution of all named-versus-free chroma attenuation to artist identity.

The evidence remains narrower than a validated evaluation of artistic resemblance. Digital capture and rendering differences are entangled with the reference comparison, the feature geometry has no perceptual validation, and the small color experiment leaves its primary effects uncertain. These are substantive limits even though the paper describes them well. The contribution is a useful empirical application and diagnostic design, rather than a new distributional principle, validated style metric, or explanation of a model's internal behavior. Local reproducibility is substantially better than the external access currently available: the cited scientific release is pending, raw-response access has not been arranged, and the cited snapshot does not identify the current manuscript build by itself.

I recommend targeted revisions and a concrete reproducibility release before treating this as a fully accessible research contribution. I found no obvious fatal contradiction in the main reported numerical results, and no serious PDF layout defect. This is an assessment of the submitted empirical scope, not a publication-outcome prediction.

## Contributions and claim/evidence map

| Claim | Evidence location | Support and limits |
| --- | --- | --- |
| Four-painter generated collections differ from references and have lower full-feature spread. | Section 4, Figure 1, Tables 2–3, Appendix B/Table 7; exploration report. | **Strong for these finite measured collections.** All 24 trace ratios are .206–.376 and RBF balanced accuracies .940–.983. Matched-size reference baselines address count differences. Post-result construction, capture differences, and unverified scene content prevent an artistic or population interpretation. |
| Adding the painter clause improves primary feature proximity in Study 1. | Sections 5.1–5.3, Figure 2, Table 4, Appendix C; controlled report and inference code. | **Strong, conditional support.** All six estimates are negative; four survive the eight-test adjustment. Randomized positions support the sharp-null test under no interference and the fixed availability/retry policy. This is neither an oeuvre-wide effect nor an effect at fixed delivered rendering. |
| Naming improves joint relative painter alignment. | Section 5.4, Equation 4, Table 5, Appendix D.2. | **Moderate descriptive support.** The double contrast changes by −.956, −1.707 and −1.758 and remains negative across the stated views. Equal-class weighting addresses coarse mixture differences, but sparse reference strata and no uncertainty assessment limit strength. NB2/Monet remaining closer to Cézanne correctly rules out the stronger individual-own-painter claim. |
| Better proximity coexists with incomplete reference coverage. | Section 5.4 and Appendix D.1/Table 8. | **Moderate, scale-specific support.** At k=3 all named medians fall below matched real-query medians. Shared anchors and class-matched counts are meaningful controls. Reused small panels and k-dependent saturation do not establish a calibrated amount of missing artistic diversity. |
| Total contraction does not identify within-scene stability or retrieval change. | Sections 5.5–5.6, Figures 3–4, Equation 3; retained-data diagnostic. | **Strong as a descriptive counterexample.** OAuth/Cézanne contracts while within-scene trace increases; FLUX/Monet contracts while retrieval improves. The exact decomposition and scale-invariance argument are appropriate. The retrieval findings do not estimate semantic adherence or new-scene accuracy. |
| Additional named-minus-generic chroma-response effects remain unresolved. | Sections 6.2–6.3, Figure 5, Appendix E; primary CSV and shared-control inference source. | **Strong support for the reported estimate/uncertainty statement.** The CSV agrees with −.284 and −.018 and simultaneous intervals crossing zero. Four repeat contrasts per scene, approximate t inference, and effective df of 15.25/9.91 limit what the experiment resolves. |
| A generic clause also attenuates chroma response compared with artist-free wording. | Section 6.3; secondary nominal interval −1.136 to −.570. | **Moderate support for this specified secondary wording contrast.** It does not establish a universal generic-language effect or uniquely identify an artist-identity mechanism. |
| Computational evidence can be reproduced from retained records. | Data/code availability, Appendix G, `paper/README.md`, Makefile and replay source. | **Strong local traceability, incomplete external reproducibility.** Six figures replayed exactly here and inspected inference tests passed. Public snapshot release and archive access remain pending. Current manuscript reconstruction additionally needs its later presentation revision. |

## Specific strengths

### S1. The controlled contrast has a clearly defined intervention and inferential unit

Section 5 holds scene text fixed while adding the painter clause, preserves repeated descriptions, and reports the entire original eight-test family, including the two short-scene contrasts and two nonrejecting naming cells. Appendix C retains the within-generated energy terms in the swap statistic instead of treating energy as a mean-distance score. This is substantive design strength, not merely cautious reporting.

### S2. The paper uses informative controls for finite-sample distribution comparisons

Table 3 uses matched-size original/original splits; Section 5.4 compares generated and held-out real queries against the same anchors; and equal-class alignment separates a joint painter contrast from reference class proportions. These controls eliminate specific simpler explanations, including unequal counts and coarse class mixtures, without pretending to solve capture or content matching.

### S3. Variation and retrieval provide concrete counterexamples to a simplistic contraction account

Figures 3–4 are not redundant repetitions of the energy comparison. OAuth/Cézanne's increased within-description spread and FLUX/Monet's improved retrieval locate distinct behaviors concealed by total trace. The paper explains why uniform scaling leaves retrieval invariant and why estimated scene means still contain generation noise. This is the most useful conceptual contribution grounded in observed results.

### S4. The generic control changes the interpretation of Study 2

The four-arm design in Section 6 shows why named-minus-free alone is insufficient. The additional named-versus-generic effects are small or uncertain relative to the broader positive palette response, while the generic clause itself attenuates the response. Shared controls are correctly reused in the covariance calculation rather than counted as independent extra observations.

### S5. Most presentation choices make scientific scope visible

Table 1 distinguishes exploratory, prospective descriptive, post-result and primary analyses; the text defines proximity, spread and contraction; figures use consistent colors and distinguish estimates from reference lines. Figure 5 shows every scene-specific interaction as well as the pooled family intervals. Visual inspection found readable figures and tables, complete labels, no clipping, and no misleading claim that PCA overlap establishes equality.

### S6. The retained local package is unusually traceable

The figure builder checks eight input hashes, rebuilds figures from saved numerical outputs, and rejects changed inputs. I ran `make figures-check`, which verified all six PDFs byte for byte. I also ran the two targeted inference test modules, obtaining **18 passed**. Source inspection confirmed fixed-scene covariance, shared generic-control handling, and raw-response hash checks in computational replay. This supports local checking, while remaining distinct from release availability.

## Weaknesses and residual limitations

### W1. Measurement validity and domain differences restrict the substantive interpretation — major residual limitation

Section 7.2 and Appendix D.4 acknowledge that all 576 NB2/FLUX images are square and all 70 Study 1 references nonsquare, and that reference capture workflows are unknown. Texture contributes nearly half the reference trace, and NB2/Monet changes direction in a no-texture sensitivity. Thus much of the distributional signal may concern capture, framing, processing, or content rather than a painter's characteristic rendering. Removing an explicit aspect-ratio coordinate would not remove the influence of geometry on spatial and texture features.

The randomized naming contrast remains meaningful for the delivered service outcome, so this is not grounds to reject the finite-feature computation. It does limit the artistic and practical value of the measured improvement. The present evidence has no independent reference adjudication, human style calibration, or complementary learned representation. A matched-capture/geometry study and independent perceptual validation require a new study; more caveats cannot supply this missing evidence.

### W2. External reproduction cannot currently match the local audit — substantive access limitation

Data/code availability and Appendix G explicitly say that scientific snapshot `28a9eb6` is not archivally released and that external access to the required raw-response archive has not been arranged. The public repository landing page was accessible during review, but I did not establish public access to the named snapshot; the browser's landing-page response showed older project status and must not be treated as a current release check. A reader presently cannot rely on the advertised public link to execute the full verified pipeline or remeasure the images.

There is also a concrete revision ambiguity. Local `git show 28a9eb6:paper/make_figures.py` renders only three figures, while the reviewed paper has six. The snapshot Makefile lacks current `four-painter-analysis` and `figures-check` targets. This does not invalidate the scientific records, but it means the one named snapshot is insufficient to identify the manuscript's current presentation. Name both scientific and presentation revisions and provide the exact command/input mapping. Actual archival publication and a usable archive-access arrangement are release work, not an editorial fix.

### W3. Study 2 cannot resolve the added naming effect or its transfer — major residual limitation

Six fixed scenes and four repeats support only approximate conditional inference. Monet's family interval spans a potentially noticeable computational reduction through essentially zero; Cézanne's spans effects in either direction. Near-boundary processing sensitivity further limits decisiveness. A single generic phrase leaves artist identity entangled with other wording differences, while condition-associated quality delivery prevents an interpretation at common rendering quality.

The paper correctly reports an unresolved result and does not need a significant finding to be valid. Nevertheless, its narrower question remains only partially answered. The primary contribution from this study is estimation and control interpretation. New scenes, collection sessions, generic phrasings, and prospective precision goals would be needed to strengthen generality; retrospectively narrowing intervals or promoting JPEG sensitivity would not do so.

### W4. Novelty is useful but incremental

The broad lesson that proximity, spread and coverage need separate evaluation is established generative-evaluation practice, and prior artistic-imitation research already compares relative shifts and dispersion. This manuscript adds a concrete repeated-scene intervention and empirically heterogeneous retrieval behavior. It does not introduce a validated new metric, independently replicated law, or identified explanation of a generative model. The revised research narrative should keep its strongest distinction centered on the controlled joint analysis, rather than implying that the general location-versus-diversity distinction originates here.

### W5. The feature inventory is insufficient for standalone reimplementation — fixable from retained source

Appendix A.1 lists coordinate names but omits choices needed to reconstruct them: the chroma ≥5 mask and 1% minimum chromatic fraction, 24-bin weighted hue histogram, D65/2° Lab convention, relative color-distance lags, spectral frequency bins, db2 stationary-wavelet transform, uniform-LBP point/radius pairs, and local-window definitions. These choices exist in `painter_feature_generation_v2/features.py`, which is a strength of the package. Since the geometry drives every result and public access is pending, a compact parameter table plus exact source path/revision would materially improve reimplementation. This does not require feature remeasurement or alteration of a freeze.

### W6. The nearest art-comparison citation needs a factual wording correction — minor but consequential

Section 2 says Deliège et al. compare historical and generated “corpora” through expert ratings. Their Section 2.2.3 explicitly states that experts did not receive a particular historical selection: historical ratings came from their knowledge, with optional outside resources, while generated ratings used displayed groups of 20 images. Describe this asymmetry precisely. It also helps articulate this manuscript's distinct use of a fixed, explicitly enumerated reference panel without overstating either study.

## Qualitative methodological assessment

| Criterion | Assessment |
| --- | --- |
| Soundness | The finite weighted energy, trace decomposition, paired sharp-null calculation, and fixed-scene shared-control covariance are coherent. No obvious implementation/manuscript mismatch was found in the inspected components. Service interference/stability assumptions and measurement validity remain unresolved. |
| Experimental design | Fixed scene text, randomized within-block order, complete accounting, generic controls, and matched real-query baselines are meaningful strengths. Selected painters, coarse content annotations, unbalanced sparse reference strata, delivery differences and one short Study 2 collection limit interpretation. |
| Statistical reasoning | Appropriate distinction between conditional randomization and approximate model-based tests; correct multiplicity families; no equivalence claim from nonrejection. Post-result diagnostic multiplicity is not converted into confirmatory evidence. No uncertainty model is supplied for the promoted alignment result, and Study 2 precision is limited. |
| Reproducibility | Strong source/receipt/membership traceability and successful targeted local checks. Public snapshot/archive availability, a manuscript revision identifier and a fuller feature specification are still required for realistic independent reproduction. |
| Novelty and significance | A useful empirical synthesis and intervention design. Its contribution lies in concrete joint behaviors and controls, with moderate domain significance until the measurements' artistic relevance and transfer are established. |
| Computational practicality | Compact vectors make numerical analysis and figure replay practical. Integrity checks additionally depend on the retained media archive and exact runtime bindings. The work provides no evidence of collection-scale or cross-service operational stability beyond its observed runs, nor does it need a new scalable algorithm for its present scope. |

## Scores under the fixed three-aspect rubric

| Aspect | Score / 10 | Reason |
| --- | ---: | --- |
| Scientific rigor | **8.0** | Strong controlled design, correct distinctions among estimands, useful finite-sample controls, and credible inspected computations. The unknown capture/rendering contribution, unvalidated feature interpretation, and limited independent-repeat evidence in Study 2 remain substantive weaknesses. Clear acknowledgement limits claims but does not eliminate those weaknesses. |
| Contribution and significance | **7.4** | Solid empirical contribution from fixed-scene naming, distribution diagnostics, and the generic-control interpretation. The general principles and metrics are established; artistic relevance, wider transfer and a mechanism are not validated. The observed examples are useful without yet being an exceptional advance. |
| Clarity and reproducibility | **7.8** | Coherent 23-page narrative, unusually precise reporting, readable figures, detailed local records and successful figure/test checks. Public reproduction is incomplete, the named scientific snapshot does not specify the current manuscript build, key feature parameters are absent from the paper, and one nearest-literature description needs correction. |

**Reviewer mean:** (8.0 + 7.4 + 7.8) / 3 = **7.7333/10**.

These are baseline scores for the recorded hash, not a target, a venue acceptance score, or an endorsement of unperformed validation. Better prose alone would not substantially change the scientific-rigor or contribution scores.

## Genuine questions for the authors

1. Which exact presentation revision will accompany scientific snapshot `28a9eb6`, and which artifact will a reader check out to reproduce all six current figures and this PDF?
2. Can a redistributable vector-only numerical replay be provided with a clearly separated raw-integrity verification step, while preserving the existing complete checks? Which named analyses already work without the raw archive?
3. What practical access arrangement is intended for independent checking of retained response bytes and pixels? If none is feasible, which results can be independently recomputed from the public material alone?
4. Which research interpretation, if any, do the authors wish to attach to the effect sizes beyond changes in this fixed feature space? Answering this would determine the appropriate target for future calibration, rather than inviting a post-hoc perceptual threshold.
5. For a prospective follow-up, is priority given to resolving the finite-scene Monet interaction or to testing transfer across scenes, phrasings and service sessions? These are different allocation goals and cannot be substituted for one another by simply increasing repeats.

## Prioritized actions

### Feasible from retained evidence and editorial material

1. **Resolve revision/replay identity.** State scientific snapshot and manuscript/presentation revision separately; map the current six figure outputs and replay commands to those revisions. Preserve historical source bindings rather than refreshing hashes.
2. **Expand the feature specification.** Add an economical parameter table or directly identified supplement covering the consequential thresholds, scales, transforms and normalization conventions already present in the retained implementation.
3. **Correct Deliège's comparison description.** Distinguish displayed generated sets from expert-knowledge historical ratings, then articulate the present paper's fixed-panel and repeated-scene differences.
4. **Make external reproducibility operationally explicit.** Document, for each current check, whether it needs only tracked vectors/tables, the response archive, or pixels. Keep the release status accurate. A vector-only check should be a clearly scoped additional analysis path, never a weakened replacement for the existing integrity audit.
5. **Consider one deterministic illustrative image panel if rights and retained-media use permit.** Selecting an already retained scene/repetition by a stated rule, showing all its relevant arms, and annotating measured coordinates would help readers understand what the abstract features describe. Treat it as illustration, not perceptual validation or selected evidence of style. This is optional and does not repair W1.

### Requiring a public release or new scientific study

1. **Release:** Archive the exact code, vectors, requests, memberships and numerical records used for the manuscript, with a durable revision identifier; provide an actual policy or facility for response/pixel access. A pending-release sentence is not equivalent to this deliverable.
2. **New validation study:** Match or vary capture/geometry deliberately and obtain independent content/style judgments tied to specific hypotheses about the feature measurements. Complementary learned features may probe representation dependence but would not substitute for human validation.
3. **New responsiveness study:** Prospectively choose a precision target, additional scenes, several generic clauses, and independent collection sessions. Intermediate palette levels are useful only if estimating slope or saturation is the stated goal. Keep the current terminal cohorts and primary results unchanged.

## Literature positioning and sources actually read

- [Deliège et al. (2025), institutional full-text PDF](https://orbi.uliege.be/bitstream/2268/338186/1/jimaging-11-00429.pdf): read the abstract, contributions, corpus/prompt design, expert-rating protocol, and discussion/conclusion. It already examines relative shift, dispersion and overlap using three experts, but historical ratings rely on their knowledge and generated sets contain 20 images per prompt. The current paper's fixed reference identities and repeated scene interventions are meaningful distinctions. The browser initially rejected the PDF's size and the publisher page returned HTTP 429; downloading the same institutional PDF succeeded. This assessment is based on that full-text access, not search snippets.
- [Naeem et al. (2020), primary PMLR paper](https://proceedings.mlr.press/v119/naeem20a/naeem20a.pdf): read Sections 1–3, including the real-neighborhood coverage definition and finite-sample behavior. This supports treating coverage and overall discrepancy as different diagnostics, and shows why the broad fidelity/diversity distinction is established prior art. It does not validate this manuscript's feature space or small fixed painter panels.
- [Parmar et al. (2022), author preprint full text, v3](https://arxiv.org/html/2104.11222): read the introduction and Sections 3.1–3.3 on resizing, quantization and compression. Their results establish that preprocessing can materially affect feature-based comparisons. The present sensitivity checks are relevant, but shared JPEG re-encoding cannot reconstruct unknown original capture histories.
- [Public project repository](https://github.com/isingmodel/latent-art-bench): landing page accessed to assess the availability claim. I did not verify an externally downloadable archive for `28a9eb6` or current raw-media access.

## Verification performed and review limits

Executed offline: the two inference test modules (18 passes), six-figure byte verification, source hash checks, and PDF rendering/visual inspection. Inspected the current figure source, relevant measurement/feature definitions, Study 2 covariance/contrast code and response-verification workflow, controlled/exploration reports, the primary interaction CSV, and the scientific-snapshot presentation files. The complete manuscript was read; targeted literature reading was not a systematic review of every bibliography item.

I did not rerun the full scientific replay, re-extract any features, inspect the raw artwork pixels, re-run the full test suite or historical evidence audit, independently recreate the complete mathematical implementation, or test a fresh external checkout. No Python behavior, manifest, or freeze-bound file was changed. Accordingly, successful targeted checks support the assessed components, not an unqualified certification of all measurements or public reproducibility. Review confidence is **high for manuscript clarity, scope and inspected local traceability**, and **moderate for complete scientific validity and literature exhaustiveness**.
