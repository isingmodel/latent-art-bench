# Academic review — round 1, reviewer 2

## Manuscript and review metadata

- **Title:** Painter Naming and the Distributional Gap Between Generated Images and Original Paintings
- **Authors:** Anonymous authors; affiliations are not specified.
- **Status:** Local empirical manuscript, 2026; no target venue supplied.
- **Domain:** Computational art analysis and evaluation of text-to-image services.
- **Manuscript:** `paper/paper.tex`, all 1,275 lines, including every appendix and the bibliography.
- **SHA-256 reviewed:** `8466d0374936f884371b3acfcb73db8a7311f8a10bd16a0689ade4284cdd0b90`.
- **Review date:** 9 September 2026.
- **Review identity:** Maintainer-run LLM subagent review, with primary emphasis on contribution, significance and nearest literature. This is not independent human or institutional peer review, editorial acceptance, or a prediction of publication outcome.
- **Rubric:** The fixed three-aspect rubric in `RUBRIC.md`, adapting the supplied academic-paper-review skill. No other reviewer files or older scored review documents were consulted.

## Executive assessment

This is a solid, carefully bounded empirical study with a useful controlled-prompt contribution. Its strongest evidence is that adding a painter clause changes reference proximity and the organization of generated variation under fixed scene descriptions. The within/between-scene decomposition and the FLUX/Monet retrieval example provide substantive information that a single distance or variance measure would conceal. Study 2 makes a useful control comparison: a generic painting-style clause can also attenuate the measured palette response, while additional named-clause effects remain unresolved.

The contribution is **moderate** rather than a new general principle of distributional evaluation. Distinguishing location, dispersion, coverage and perceptual resemblance has close precedents, and the present study neither validates the artistic meaning of its geometry nor identifies the origin of the gap. This does not invalidate the stated finite-panel question. It does materially limit the result's significance for art evaluation and for decisions about imitation quality. A particularly useful result already present in the retained tables is underdeveloped in the manuscript: at the displayed coverage scale, naming improves coverage in five cells and leaves it unchanged in one, despite contraction. Reporting this joint change would strengthen the paper's actual contribution without a new experiment.

The numerical narrative is generally consistent with the retained reports, and I found no blocking contradiction in the principal claims. The main concerns are limited construct and capture validation, the narrow scope of the controlled evidence, incomplete presentation of the coverage contrast, and unavailable external access to the scientific snapshot and raw inputs. I recommend revision around these issues, without treating a larger or different study as a prerequisite for reporting the valid finite-panel results.

## Contribution and nearest-literature positioning

The manuscript makes three useful empirical additions: a randomized naming comparison across three requested services; decomposition and held-repetition retrieval under the same scene design; and a separate generic-controlled palette experiment. Its four-painter corpus adds descriptive breadth, but does not itself identify the naming effect. The main innovation lies in combining established measurements with a repeated prompt intervention, not in inventing the distance, coverage concept or distinction between feature similarity and style.

**Deliège et al. (2025) is the closest distributional style comparison.** I read its materials, expert-rating protocol, RRMap construction, discussion and conclusion through the Europe PMC full-text XML. It uses 300 Midjourney v6 images, grouped for evaluation, and historical reference intervals elicited from three experts' knowledge, rather than an explicit sampled historical-image panel. It already compares shifts, relative dispersion and overlap. The manuscript's fixed references and repeated scene-matched naming intervention therefore provide the relevant distinction. Section 2's description is broadly fair, but “historical and ... generated corpora” obscures how the historical baseline was obtained. Specify that difference directly. This is complementary evidence, not an objective replacement for expert assessment. [Deliège et al., primary article](https://doi.org/10.3390/jimaging11120429); [full-text XML accessed](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12734345/fullTextXML).

**Kim et al. (2026) is related but addresses another estimand.** The retained published text compares autoencoder and CLIP representations of historical artworks and applies later-period contextual keywords to existing paintings in image-to-image generation. The manuscript correctly distinguishes its text-only fixed-scene intervention. Kim's work is not a direct baseline for a painter-naming energy effect, and matching its scale or latent-space machinery is not necessary here. Its relevance is the distinction between semantic context and image statistics, reinforcing why the present low-level feature geometry is only one measurement view. [Kim et al., published article](https://doi.org/10.1073/pnas.2517969123).

**Asperti (2026) already studies human/generated separation and its interpretation.** The accessible preprint examines CLIP geometry using image transformations, interpretable descriptors and inversion. Its author reports low visual salience for some embedding displacements and acknowledges remaining generator signatures. Thus, domain separation and caution about perceptual interpretation are not new contributions here. The present paper contributes a prompt intervention rather than that preprint's investigation of the embedding gap. Its citation is appropriately described as a preprint; the paper should not borrow its proposed explanation as validation of these 31 features. [Asperti, version 1, especially §§3 and 10](https://arxiv.org/html/2608.25609v1).

**Distributional evaluation supplies the methodological foundation.** The reference-neighborhood coverage definition in §5.2 is essentially Naeem et al.'s coverage construction, applied here with matched generated/real queries and a small fixed reference panel. Those matched controls are a useful application choice. The manuscript should cite the source at the definition and identify the adaptation. The general need to distinguish fidelity and diversity is established; the contribution is the observed joint behavior under naming. [Naeem et al., §3.2–3.3 and Eq. 5](https://proceedings.mlr.press/v119/naeem20a/naeem20a.pdf).

The cited preprocessing literature is relevant: the primary CVPR abstract for Parmar et al. specifically identifies resizing and compression as sources of metric variation. The manuscript's three-pipeline sensitivity is consequently useful but cannot remove unknown historical capture differences. I could access that abstract and proceedings record, but the full PDF fetch was denied, so I make no detailed claim about its experiments. [Parmar et al., official proceedings record](https://openaccess.thecvf.com/content/CVPR2022/html/Parmar_On_Aliased_Resizing_and_Surprising_Subtleties_in_GAN_Evaluation_CVPR_2022_paper.html).

## Principal claim/evidence map

| Claim | Evidence and location | Assessment |
|---|---|---|
| Four-painter generated collections have less spread and are distinguishable from the references. | §4; Tables 2–3 and Appendix B; trace ratios .206–.376 and RBF balanced accuracy .940–.983; retained exploration report. | **Strong for the observed image domains.** All 24 cells are reported. Content and capture differences prevent an artistic interpretation of the separation. |
| Naming improves primary reference proximity. | §5.3, Figure 2 and Table 4; six negative estimates, four adjusted rejections in the fixed eight-test family; retained original endpoint table. | **Strong for the specified conditional prompt tests.** OAuth results remain inconclusive; neither the tests nor the selected panels support an oeuvre-wide claim. |
| Naming improves joint relative painter alignment. | §5.4, Table 5, Eq. 4; negative named-minus-free changes in all 36 service/view/pipeline combinations. | **Moderate descriptive evidence.** The statistic is joint, with no dedicated uncertainty assessment; NB2/Monet remains individually closer to the other panel. |
| Named outputs retain reference-coverage gaps. | §5.4 and Appendix D.1; matched anchor/query design, three neighborhood sizes; real medians exceed named medians at k=3. | **Strong as a scale-specific finite-panel description.** At k=5 one comparison saturates. The omission of artist-free values from the displayed table leaves the naming-induced coverage change unnecessarily unclear. |
| Aggregate contraction does not determine repetition variability or retrieval. | §§5.5–5.6, Figures 3–4; OAuth/Cézanne within-scene ratio 1.139 and FLUX/Monet retrieval 44.4%→59.7%; retained retrieval report. | **Strong descriptive counterexamples.** They establish coexistence in this data, not semantic adherence or future-scene performance. |
| Additional painter-specific chroma attenuation beyond the tested generic clause is unresolved. | §6.3, Figure 5 and Appendix E; simultaneous intervals [−.585,.016] and [−.343,.308]; retained primary experiment report. | **Supported under the stated approximate error model.** Neither equivalence nor a mechanism is established; the small effective degrees of freedom and fixed scene set constrain precision and transfer. |
| Generic painting-style wording can reduce the measured response relative to the artist-free condition. | §6.3; secondary contrast −.853, nominal interval [−1.136,−.570]. | **Moderate, secondary evidence for this wording and delivered service.** It is an informative control finding, not a general effect of generic wording. |

## Specific strengths

### S1. A prompt intervention that resolves an ambiguity in corpus comparisons

Section 5 holds the scene and closing instructions fixed, changes the painter clause, randomizes order within assigned groups, and evaluates the complete prespecified eight-test family. This supports a much more specific conclusion than a generated-versus-original scatter plot. Its value comes from the design and the observed contrast, not merely from labelling the study prespecified.

### S2. Complementary diagnostics reveal substantively different behaviors

The energy-term example in §5.3 shows that the smaller within-generated distance actually opposes the energy improvement. Sections 5.5–5.6 then show that contraction can coexist with increased repeat variability or improved retrieval. These are useful observations for anyone evaluating generated collections; they prevent a distance improvement or a variance reduction from being mistaken for a complete evaluation.

### S3. Matched real-query coverage offers a meaningful empirical reference

The disjoint-anchor/real-query construction in Appendix D.1 matches query counts and class proportions for generated and real data. This is more informative than comparing an arbitrary generated sample's coverage with one or assuming coverage must equal one. The k=1/3/5 results make the scale dependence assessable.

### S4. The generic clause changes what the palette experiment can establish

The shared generic controls in §6 separate the additional effect of the tested name clause from the response under one other style phrase. The positive arm responses and smaller generic response provide actual evidence that named/free comparisons alone can attribute too much to painter naming. This is a meaningful design improvement even though the primary named/generic interactions are unresolved.

### S5. The records support unusually specific local checking

The full source, compact numeric tables, scene memberships, frozen test identities, and reported formulas permit close local scrutiny. The main figures are legible, use common axes where comparison requires them, and visibly distinguish descriptive quantities from uncertainty intervals. This is a local reproducibility strength with a real external-access limit, rather than proof of public reproducibility.

## Weaknesses and residual limitations

### W1. The measurement remains a weak bridge from the finite feature question to painter resemblance

The low-level representation is useful but not validated against artistic judgments or an independent image representation. Texture supplies almost half the reference trace; some features are correlated summaries; NB2/Monet reverses its proximity change in one no-texture view (§5.7). Geometry perfectly separates the paid-service/reference domains, and historical capture workflows are unknown (§7.2 and Appendix D.4). These facts do not invalidate a prompt effect on the measured output, but they substantially restrict the importance of a “distributional gap” for artistic resemblance. Additional prose cannot solve this limitation. Retained-data revisions should keep result summaries tied to measured domains; perceptual or capture validation requires a new study.

### W2. The empirical advance is useful but narrower than the broad evaluation lesson

Sections 1 and 7 emphasize why smaller distance does not establish distribution matching. That principle is already supported by the cited distributional-evaluation literature, while Deliège already studies shifts, dispersion and overlap for painter/style imitation. The novel material is the particular controlled intervention and its heterogeneous joint consequences. Make that distinction more explicit and sharpen the historical-baseline comparison with Deliège. There is no need to manufacture a new general principle or add a large benchmark to justify this empirical application.

### W3. The paper omits an informative existing coverage comparison

Section 5.4 and Appendix D.1 display named versus real coverage but not artist-free coverage. This weakens a paper whose contribution is how proximity, spread and coverage change together. The retained `heldout_real_controls.csv` shows that, at k=3, naming raises median coverage in five cells and ties in OAuth/Monet: Monet NB2 .278→.500, FLUX .556→.833, OAuth .500→.500; Cézanne NB2 .200→.400, FLUX .467→.800, OAuth .467→.533. All remain below the matched-real medians. Reporting these values would show that contraction can accompany *improved coverage with a residual deficit*, a more informative result than the residual deficit alone. This is a presentation omission, not evidence that the existing claim is numerically false. Keep it descriptive and specific to the matched k=3 construction.

### W4. The controlled scope and Study 2 precision limit substantive transfer

The controlled painters were selected after exploration, the reference panels are small and uneven, and the scenes are fixed. The exploratory named/free ordering differs from the controlled ordering (§7.1), demonstrating that prompt/reference/service context matters. Study 2 adds one service, six new scenes, one generic phrase and four repetitions; its intervals permit meaningful changes in either direction for Cézanne and substantial attenuation for Monet. It therefore adds a limited instruction-response finding rather than resolving the broader third research question. This is an appropriate study to report, but not an established explanation of the contraction or a general conclusion about painter-name responsiveness. Larger scope and better precision require a new versioned study, not retrospective expansion of the current inferential family.

### W5. External reproducibility is not yet available at the advertised scientific snapshot

The availability statement and Appendix G identify a local snapshot whose archival release is pending. Full checked replay needs raw response bytes, and remeasurement needs media to which external access is not arranged. The detailed local record does not let a reader independently execute those steps now. Release of the compact snapshot and a clearly runnable vector/table analysis path would materially improve the paper; raw-media access and licensing may require a separate release arrangement. The manuscript accurately states this limitation, but disclosure does not remove its effect on the reproducibility score.

## Qualitative methodology assessment

| Criterion | Assessment |
|---|---|
| Soundness | The principal inferential and descriptive estimands are defined coherently. The paired energy identity includes the within-generated term, avoiding a misleading mean-distance surrogate. No principal numerical contradiction was found. |
| Measurement | A fixed development-only scale avoids fitting the representation to the controlled outcome. The interpretability and multiple views are useful; dependence on digital texture and unmeasured capture differences remain substantial. |
| Experimental design | Study 1's fixed-scene paired intervention is strong for its conditional question. Study 2 adds a relevant active wording control. Painter, scene and service selection limit transfer, and variable delivery settings are part of the treatment rather than isolated nuisances. |
| Statistical reasoning | Multiplicity families, complete pairs and the two different inference frameworks are handled explicitly. Study 2 relies on unverified independent/stable repeat errors and modest effective degrees of freedom. Descriptive diagnostics should remain descriptive. |
| Reference comparisons | Count/class-matched real queries and equal-class joint alignment improve the analysis. Sparse strata and unknown capture processes still constrain painter-level interpretation. Showing the omitted free coverage arm is a feasible improvement. |
| Reproducibility | Strong local traceability and readable formulas; external execution and remeasurement remain blocked by release/access status. The review did not rerun full pixel extraction or reconstruct remote service behavior. |
| Scale and cost | The computations are plausible and adequate for the finite panels. Mutable service identifiers and a short collection window matter more than algorithmic scalability for the present question. A much larger benchmark is not required to validate the observed finite-panel differences. |

## Scores under the fixed rubric

| Aspect | Score / 10 | Reason |
|---|---:|---|
| Scientific rigor | **8.0** | Strong conditional design, correct separation of estimands and inference, and meaningful retained-data checks. Measurement/capture ambiguity and Study 2's small-sample service assumptions remain substantive limitations even for interpreting this bounded computational contribution. |
| Contribution and significance | **7.3** | A solid controlled empirical application with useful scene-structure and generic-control findings. The overarching distributional lesson is established, the mechanism and perceptual importance remain open, and transfer beyond these prompts and panels is untested. The available coverage improvement result is not yet developed in the manuscript. |
| Clarity and reproducibility | **8.0** | Coherent narrative, precise main definitions, readable figures and extensive local evidence. Coverage reporting and nearest-work distinction can be sharper; public availability of the cited scientific snapshot and raw inputs remains materially incomplete. |

**Equal-weight reviewer mean: 7.7667/10.** These scores recognize the actual empirical evidence. They do not award points for candor alone or assume an unstated venue standard.

**Confidence:** High in the manuscript-level claim assessment and the bounded literature distinctions; moderate in the numerical implementation and broader literature completeness. I read the complete manuscript source and bibliography, inspected all six figures in the retained current page renders, and checked the relevant exploration, revision, retrieval and primary palette reports. The two relevant offline inference/analysis test modules passed: **19 tests**. I did not conduct a full replay, inspect every raw response, validate expert judgments, or reproduce all related papers. The literature search was targeted rather than systematic. Kim was read in its retained published text; Asperti and Naeem in accessible primary full-text material; Deliège via primary full-text XML after publisher/PMC access failures; Parmar only at its official abstract/proceedings record.

## Questions for the authors

1. Do the authors intend the claimed joint-change contribution to include change in coverage under naming? If so, why are the available artist-free matched-coverage values absent from the displayed comparison?
2. Can the two painter-specific own-minus-cross margins from the existing alignment matrix be summarized alongside the joint interaction? This would clarify whether each name moves relatively toward its own panel, while preserving the separate question of which panel remains absolutely nearer.
3. What externally runnable analysis bundle will accompany the paper: compact-vector calculations and figure rebuilding, or also integrity-checked raw-response replay? The availability statement should match the actual release when it occurs.

## Prioritized actions

### Feasible from retained evidence and editorial revision

1. **Show artist-free, named and real matched coverage together at k=3**, preserving k=1/5 sensitivity. State the five improvements and one tie as correlated finite-panel descriptions, without adding significance tests or a claim of distribution matching.
2. **Sharpen the contribution relative to the nearest work.** Explain Deliège's knowledge-based historical reference and credit the existing coverage definition at its first use. Lead with the controlled repeated-scene intervention and observed joint outcomes.
3. **Make the painter-alignment interpretation easy to inspect.** If space permits, add the existing per-painter own/cross margins to the appendix; retain the joint nature of the main statistic and its current inferential status.
4. **Keep the synthesis at the level the evidence supports.** The paper is a feature-space account of specified service outputs. Its palette experiment adds a control result and unresolved interaction estimates; it does not explain Study 1's contraction.

### Requiring public release or a new study

1. **Release the scientific snapshot and a documented compact-data replay path.** Separately resolve whether raw media can be accessed for remeasurement; do not promise exact regeneration from mutable service aliases.
2. **For stronger claims about painter resemblance, prospectively validate the measurements** using independent judgments and a reference/capture design with appropriate common support. This would add evidence, not merely another disclaimer or another encoder treated as ground truth.
3. **For claims about general naming-specific responsiveness, use a new fixed design** with multiple generic phrasings, additional scenes/services and, if response shape is the target, intermediate palette levels. Do not expand or retrospectively reinterpret the closed primary cohorts.

## Minor issues

- The coverage attribution belongs near its definition, not only in the broad related-work paragraph.
- The phrase “historical ... corpora” in the Deliège comparison should distinguish explicit observed image samples from experts' knowledge-based ranges.
- No major figure-legibility problem was found in the six inspected figures. The exploratory legend's model-like labels are adequately qualified as requested aliases in the text; preserve that qualification.
