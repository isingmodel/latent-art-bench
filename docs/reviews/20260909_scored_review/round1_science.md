# Round 1 scientific review — 9 September 2026

Reviewer role: skeptical scientific reviewer, emphasizing construct validity,
alternative explanations and contribution while reviewing the whole manuscript.
This is an internal maintainer-run LLM subagent review, not independent human or
institutional peer review. I did not consult other reviewers or prior editorial
review conclusions.

Reviewed baseline commit: `f0fe89a`.

Reviewed `paper/paper.tex` SHA-256:
`a86ab853dddedcbf45c8d944aef3a4bc9871f022e583b2a7830c69ddfba25a17`.

Scope: editable manuscript review, not shared-primitive work, an active census,
or a new scientific study. I read `docs/STATUS.md`, then `docs/ARTIFACTS.md`, and
inspected Git status before review. The initial working tree was clean. I read
the complete TeX and bibliography, the controlled-study and retained-data
revision reports, the computational responsiveness synthesis and primary report,
and selected underlying CSV records. I inspected the existing current manuscript
page previews containing all five figures. Scientific evidence and manuscript
files were not edited.

## Scores

Scores use the specified equal-weight rubric: 5 means substantial unresolved
defects; 7 means sound but substantial revision needed; 8 means strong with
limited revisions; 9 means publication-ready as a carefully scoped empirical
paper; 10 means exceptional. Half-points are allowed.

| Aspect | Score / 10 | Reason |
| --- | ---: | --- |
| 1. Research question and contribution | 7.5 | The controlled painter-name comparison is useful, but the main narrative underuses its painter-specific original/generated evidence and foregrounds several already-known distinctions between metrics. |
| 2. Study design and controls | 7.0 | Shared scenes, randomized order, complete retention and a generic-clause control are strengths. Sparse selected references, one generic wording, two palette endpoints, only six follow-up scenes, and treatment-dependent delivery limit the scientific alternatives the design can distinguish. |
| 3. Statistical validity | 8.0 | The two test families and descriptive follow-ups are separated correctly; the energy swap identity, missingness scope and approximate Study 2 inference are stated carefully. Four repeats per scene and service stability assumptions remain meaningful limits on the color intervals. |
| 4. Evidence and robustness | 7.5 | Extensive retained sensitivities expose genuine reversals and counterexamples. Most reuse the same observations and representation family, while common capture/geometry and content differences remain unresolved. Existing matched reference controls are not adequately used in the manuscript. |
| 5. Interpretation and claim calibration | 8.5 | The manuscript avoids equating features with style, non-rejection with equivalence, or retrieval with adherence. The single generic-clause result and the forced color mixture still receive more general rhetorical weight than their designs warrant. |
| 6. Literature and positioning | 7.0 | Relevant primary work is cited accurately at a high level, but the closest distribution/representation paper receives only one sentence. The precise empirical increment over that work and existing fidelity/diversity evaluation needs development. |
| 7. Reproducibility and transparency | 8.5 | Compact vectors, fixed memberships, full tables, provenance and explicit replay limits are strong. The paper's availability statement still depends on an unspecified accompanying repository and separately retained response archive rather than a concrete public release/access route. |
| 8. Structure, writing and figures | 8.0 | Clear prose, readable vector figures and unusually careful captions. The paper would be more coherent if substantive original/generated controls appeared centrally and the color-mixture lesson occupied less space. |

**Arithmetic mean: (7.5 + 7.0 + 8.0 + 7.5 + 8.5 + 7.0 + 8.5 + 8.0) / 8 = 7.75 / 10.**

Recommendation: substantive focused revision. I do not currently score this as
publication-ready. The problem is not a discovered false primary result, and
new human ratings are not required to make a defensible computational paper.
The current evidence can support a more interesting and more clearly positioned
empirical contribution than the present emphasis communicates.

## Major findings

### 1. Put the empirical painter-specific result at the center of the contribution

The Introduction's three questions and final contribution paragraph
(`paper/paper.tex:67–91`) frame the paper around separating proximity, variation,
retrieval and responsiveness. Those distinctions are sound, but the facts that
covariance trace does not determine classification accuracy and that fidelity
and diversity are distinct are not by themselves substantial new scientific
findings. The FLUX/Monet counterexample is an informative demonstration in this
particular experiment; it should not have to carry most of the novelty.

The relative own/cross-painter interaction in Appendix D
(`paper/paper.tex:764–790`) addresses a more substantive alternative explanation:
whether both names simply move outputs toward one generic painting region.
Equal-class weighting removes the two reference panels' different broad-class
mixtures, while the double contrast cancels the within-reference and
within-generated energy terms. Its named-minus-free changes are -0.956 for NB2,
-1.707 for FLUX, and -1.758 for OAuth; all 36 service/view/pipeline changes are
negative. The artist-free paired labels have verified identical payloads and
near-zero empirical interactions. These are useful descriptive controls for a
paper about painter naming relative to actual reference collections.

Move a compact version into the main results and connect it explicitly to the
research question. It supports improved **joint relative alignment of the two
named collections with their assigned panels**, beyond a shared generic movement.
It does not establish six individually correct painter matches. In the primary
equal-class matrix, NB2/Monet energy is 3.687 to Monet and 3.488 to Cézanne. The
joint interaction is negative despite this individual cross-painter preference.
Keep this counterexample visible when stating the stronger central result.

Evidence: `specificity_interactions.csv`, `specificity_matrices.csv` and
`identical_payload_placebos.csv` in
`reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/`.

**Fix type:** editorial use of already published analysis. A new confirmatory
specificity test or a painter-population claim would require a new prospective
study; neither is necessary for the recommended descriptive statement.

### 2. The forced palette mixture is a weak central explanation of the original/generated gap

Section 4.6 and its Discussion continuation (`paper/paper.tex:551–612`) correctly
say that the 50/50 muted/vivid mixture is designed. Nevertheless, the extended
lesson that close means and broad ranges can mask different mass allocation
risks giving a largely design-induced phenomenon the weight of a discovery
about ordinary painter-conditioned generation. Extreme palette prompts are
expected to place observations on opposite sides of a reference center. No
intermediate instructions, unconstrained color control in Study 2, or response
curve can show whether the resulting gap is difficult to bridge.

The body already contains the right caveats; adding more caveats is not the
solution. Keep this as a short descriptive illustration, and use an existing
Study 1 original/generated control to substantiate the residual distributional
gap under the paper's ordinary detailed prompts.

The retained matched-anchor, held-out-real coverage results are one option.
At k=3, named generated coverage medians are:

| Painter | NB2 | FLUX | OAuth | Held-out real queries |
| --- | ---: | ---: | ---: | ---: |
| Monet | .500 | .833 | .500 | .944 |
| Cézanne | .400 | .800 | .533 | .933 |

These use identical anchors and matched class counts for disjoint real and
generated queries, with reduced query sizes 18/15. They offer a direct finite-panel
comparison that the current manuscript relegates to a final availability sentence.
They show why improved energy does not alone establish matching neighborhood
occupancy. Include k=1/3/5 sensitivity and the important saturation limitation:
FLUX/Cézanne reaches 1.0 for both generated and real median coverage at k=5.
The 100 fixed draws reuse the finite reference panel; their ranges are not
population confidence intervals. These results remain about digital feature
neighborhoods and do not remove capture or geometry differences.

Evidence: `heldout_real_controls.csv`, `heldout_reference_designs.csv`,
`heldout_real_draws.csv` and `coverage_summary.csv` in the revision bundle.

A still smaller addition would explain the saved energy terms: for FLUX/Monet,
twice the cross-domain mean distance falls from 15.831 to 12.421, while the
within-generated mean distance falls from 6.906 to 4.120. The latter change
opposes improvement because it is subtracted in energy. Thus the lower energy
is not mechanically obtained merely by reducing within-generated distances.
The current paragraph at lines 425–428 states dependence without making this
useful directional point. These terms are already in `metric_cells.csv`.

**Fix type:** editorial selection from existing evidence. Claims about attainable
palette support, natural output densities, or the cause of the original/generated
gap require new data and should remain outside the current paper.

### 3. The design identifies service-and-wording effects, with residual artistic alternatives

The paper states its limitations unusually well, but they are still limitations
of the scientific contribution, not issues resolved by disclosure. Study 1
identifies a finite prompt intervention under the declared sharp null. It does
not separate painter style from scene-content changes induced by the name, or
from rendering choices. Equal broad-class weighting cannot accomplish this.
The 17 uncertain/mixed annotations, intended rather than verified generated
classes, and sparse Monet-built/Cézanne-water strata matter directly to the
original/generated interpretation (`paper/paper.tex:128–175`). Under the
equal-class specificity weighting, reference effective sample sizes are only
about 24.0 and 18.8, respectively; the three/four-work strata acquire one-third
of the reference mass.

Study 2 improves on an artist-free-only comparison, but its control changes a
complete sentence. “Traditional landscape-painting” is a substantive aesthetic
instruction, not a semantically neutral placeholder. The secondary -0.853
interaction is evidence about that sentence, not all generic painting language.
In addition, arm-associated delivered quality (10/4/3/1 medium-quality images)
and geometry leave a semantic-clause effect at fixed rendering unidentified.
The current decision to retain all outputs and target delivered-service response
is defensible; filtering low-quality outputs after treatment is not the fix.

The manuscript should state the positive surviving claim compactly at the start
of the Discussion: names alter the finite delivered feature distributions and
their joint relative panel alignment; the single generic clause also alters
the two-level chroma response. The causal pathway through content, rendering or
style remains unresolved. Change the Section 4.5 heading and general references
to “generic painting language” to “the tested generic clause” where feasible.

**Fix type:** editorial calibration for the current paper. New generic wordings,
intermediate palette instructions, independently coded/generated content and
matched capture/rendering support would require a new prospective scope. I am
not making any of these prerequisites for the narrower empirical paper.

### 4. Position the paper against the closest representation work, not only its headline

The one-sentence treatment of Asperti (2026) at `paper/paper.tex:112–117` is too
thin for the nearest conceptual neighbor. Its primary abstract describes not
just CLIP separation but interpretable statistical representations, multiscale
structure, and inversion results in which strong embedding movement can have
low human perceptual salience. That is directly relevant to this manuscript's
measurement and interpretation choices. The useful distinction is the present
randomized painter-clause comparison with repeated common scenes and a finite
reference panel, plus the controlled color follow-up—not merely that one paper
uses CLIP and the other uses 31 features.

Primary source checked: [Asperti (2026), arXiv:2608.25609](https://arxiv.org/abs/2608.25609).

The paper should also explain what the repeated intervention adds to the
individual-image survey design of AI-Pastiche and the original-caption-conditioned
attribution design of AI-WikiArt. The present descriptions are broadly accurate;
this is a positioning omission rather than a demonstrated citation error.
Primary sources checked:
[AI-Pastiche](https://www.mdpi.com/2504-2289/9/9/231) and
[Fu et al., methods §3.2](https://arxiv.org/html/2508.01408v1).

Finally, fidelity/diversity distinctions and neighborhood coverage already have
a substantial generative-model-evaluation basis. State that the contribution is
their controlled empirical application and the specific observed dissociations,
not introducing the need to separate those concepts.
Primary source checked: [Naeem et al. (2020)](https://proceedings.mlr.press/v119/naeem20a.html).

**Fix type:** editorial and literature synthesis. No new images, ratings or
scientific calculations are needed.

## Minor findings and confirmations

1. **Statistical statements are substantially correct as written.** The sharp-null
   family concerns prompt assignment, not original/generated population equality.
   The color family uses approximate fixed-scene inference and does not treat
   random dispatch as an exact weak-interaction test. The 49-image predecessor is
   correctly excluded from primary inference. I found no basis in the reviewed
   records to claim that a reported primary contrast or interval is wrong.

2. **The unresolved color result should remain numerical.** Report both intervals
   as now, including the small positive endpoints, without converting the two
   non-rejections into evidence that naming has no additional effect. No minimum
   relevant effect or equivalence margin has been validated. The JPEG Monet
   threshold crossing is correctly presented as sensitivity rather than a
   replacement primary result.

3. **Retrieval supports a finite counterexample, not a population improvement.**
   The held-out query is excluded from all centroids and the within-class control
   is useful. Overlapping training sets and only three repetitions mean the 72
   query outcomes are not 72 independent trials for naive binomial intervals.
   Retaining the descriptive presentation is appropriate. Uniform scaling leaves
   retrieval unchanged, as the paper correctly acknowledges.

4. **Figures are clear but distributional content could be stronger.** All five
   inspected figures are readable, use sensible comparison scales, and have
   informative captions. The Study 2 mean-only panel removes output variation
   visible in the already published arm-chroma plot. If the color section remains
   substantial, showing the retained individual values or scene means would help
   readers distinguish consistent shifts from extreme observations. It is not
   necessary to add another figure merely to show every retained diagnostic.

5. **A public release statement should name the actual access path.** Lines
   656–669 distinguish figure rebuilds from integrity-checked replay well, but
   “accompanying repository” and “retained separately” should resolve to a stable
   repository/archive and an explicit access status at submission. Do not imply
   that computational reproducibility guarantees service regeneration or access
   to all raw pixels. This is a release/editorial issue, not a request to expose
   nonredistributable artwork or private response material.

6. **The strongest sensitivity failure deserves continued prominence.**
   NB2/Monet's positive no-texture/256 energy change and its above-reference
   no-texture/512 trace ratio prevent a representation-independent result. Keep
   both in the main text even if the narrative is reorganized around specificity.

## Smallest defensible revision path

1. Rewrite the contribution paragraph and opening Discussion around the actual
   finite empirical pattern: primary proximity often improves, joint painter
   alignment strengthens, aggregate spread contracts, and residual reference
   neighborhood occupancy differs. Retain route/painter heterogeneity.
2. Promote the existing specificity contrast with its explicit joint-result
   limitation and the NB2/Monet exception. Add at most one compact use of the
   existing matched-real coverage or energy-term evidence; do not turn all
   diagnostic tables into main-text claims.
3. Keep retrieval as an observed counterexample and Study 2 as a scoped test of
   two named clauses versus the one specified generic sentence. Shorten the
   forced-mixture section and remove any suggestion that it explains the ordinary
   original/generated discrepancy.
4. Expand the closest-primary-literature comparison and make the release path
   concrete. Rebuild the existing presentation and verify its source values.
5. Do not add human ratings, new image collection, new primary tests or a new
   preferred feature space merely to improve review scores. Broader artistic,
   scene-population, mechanism or response-curve claims would require new evidence.

**Answer to the central question:** yes, the current data support an interesting
original/generated distribution paper when its target is the finite measured
digital panels and delivered services. The most useful story is an empirically
demonstrated combination of improved relative painter alignment, contraction,
remaining distributional mismatch and heterogeneous response consequences. They
do not support an oeuvre-wide or perceptual imitation claim, a universal loss of
scene information, or a demonstrated painter-specific color-attenuation mechanism.

## Verification performed

Smallest relevant offline tests run:

```text
uv run --locked pytest -q tests/painter_distribution_revision_v1/test_metrics.py tests/painter_responsiveness_v2/test_prv2_analysis.py -m 'not live'
27 passed in 1.22s
```

This review changes only its own Markdown report. It does not change Python
behavior or evidence-bound files, so I did not rerun the full suite or historical
evidence audit. No live generation, new image acquisition, feature extraction,
or human-rating collection was performed.
