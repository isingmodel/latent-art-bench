# Novelty assessment and competing explanations

Search date: 2026-09-10/11. This is a scoped literature assessment, not proof that
no related result exists. Queries included artist-name prompting, prototype
similarity, generic painting, style homogenization, diffusion style similarity,
and the exact titles below. Primary papers and author project pages were used;
nonacademic search results were not treated as scientific evidence.

| Prior work | What is already established or studied | Consequence for this project |
|---|---|---|
| [Su et al., Identifying Prompted Artist Names from Generated Images (2025)](https://arxiv.org/abs/2507.18633), especially §§3.2–3.5 | Artist-name interventions, prompt complexity, several generators, real-artist prototypes and artist recognition. | Name substitution, artist classification and model comparison are not new contributions. Our target is recovery of relative reference-artist geometry after removing a common response, with a generic painting control. |
| [Somepalli et al., Investigating Style Similarity in Diffusion Models, ECCV 2024](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/08294.pdf) | Learned style descriptors, content/style separation, style retrieval and generator-specific artist imitation. | We cannot claim to invent style-sensitive measurement or diagnose training inclusion from these 31 features. We test an explicitly limited, interpretable target. |
| [Deliège et al., How Good Is the Machine at the Imitation Game? (2025)](https://doi.org/10.3390/jimaging11120429) | Historical/generated comparison, stereotyped imitation, shifts and dispersion, with expert ratings. | “Generated art is stereotyped” is not novel; our controlled decomposition must add evidence beyond that interpretation. We do not reproduce their perceptual validation. |
| [Fu et al., Artificial Intelligence and Misinformation in Art (2025)](https://arxiv.org/abs/2508.01408) | Real/AI painter attribution across a large WikiArt-derived corpus, using image captions to match generated content. | A common-scene design improves internal prompt comparisons but does not eliminate content differences from the historical reference panel. WikiArt and Wikimedia are different sources. |
| [Kim et al., Large-Scale Quantitative Analysis of Painting Arts (2014)](https://doi.org/10.1038/srep07370) | Interpretable color and brightness statistics; a painting/photo comparison and painting-filter controls. | Generic pictorial processing is an established alternative explanation. Its corpus was the Web Gallery of Art, so it does not validate Wikimedia capture quality. |
| [Kim et al., Context-Aware Multimodal AI Navigates Hidden Pathways in Five Centuries of Art Evolution (2026)](https://doi.org/10.1073/pnas.2517969123) | Formal/contextual latent representations of historical painting and contextual generative experiments. | Our question concerns controlled artist naming and recovery of reference differences, not reconstruction of art-historical evolution. Formal features alone cannot separate all contextual and stylistic influences. |

## Defensible contribution

The combination to test is: common scenes, four related painters, an explicit
generic painting arm, repeat-corrected reference contrast recovery, and model
comparisons on that shared target. We found close antecedents for every broad
motivation. We did not identify this exact combined estimand/design in the papers
examined, but will not describe it as a proven first. New model names alone do
not provide methodological novelty.

## Falsifiable explanations

1. **Shared painting response:** a generic painting clause reproduces the common
   component of naming. Test its direction/magnitude, while independently testing
   reference-aligned painter contrasts. A large shared fraction by itself is
   insufficient because the reference artists also share properties.
2. **Weak or exaggerated artist contrast:** generated painter differences point
   in the reference direction but have incorrect amplitude. The reference-aligned
   regression and amplitude component of corrected error quantify this account.
3. **Different painter contrasts:** painter names create distinct outputs whose
   differences are poorly aligned with the reference panel. The orthogonal error
   component distinguishes this from merely weak conditioning.
4. **Scene-dependent conditioning:** artist contrast recovery varies with the
   common scene. Compare scene-conditional and aggregated geometry and leave each
   scene out; do not treat individual features as independent experimental units.
5. **Concentrated conditional output distributions:** artist-specific mean
   differences can be recovered while within-artist variation remains too small.
   Report reference energy, trace and repeat variation alongside mean geometry.
6. **Measurement/reproduction effects:** aspect ratio, resolution, encoding and
   capture can create differences. A common-square remeasurement and feature-family
   analyses test some processing explanations. Existing capture evidence cannot
   resolve scanner/camera, conservation or material-surface effects.

Training frequency, filtering, memorization, preference optimization and inference
guidance are possible upstream causes but are not identified by these experiments.
No feature-only result will be described as proving one of those causes.
