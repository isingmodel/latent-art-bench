# Kim A/C, learned art representations, and painter-associated distributions

Review depth: full text, supplement, exact released source, and primary-method comparison

Question: when can a pretrained or learned image representation contribute to a reproducible
painter-associated distribution across works, and which claims remain unsupported?

## 1. Finding

A learned image vector is not itself a painter feature. It is a coordinate system in which a
painter-associated distribution may or may not be estimable. For painter $a$, the scientific
object is

\[
P_a\{f(X)\mid\text{phase, genre/content, medium, date, source/digitization}\},
\]

with uncertainty across physical works and digital reproductions. The encoder $f$ earns a
place in that profile only after artist-label predictability survives source, content, phase,
reproduction, and training-data shortcut tests and supports the declared painter-level claim.

The reviewed evidence does not justify calling any single pretrained latent *the* painter-style
representation:

- Kim's A-vector is a sampled Stable Diffusion 2.0 VAE reconstruction latent. It preserves
  color, composition, content, spatial layout, resizing artifacts, and acquisition-domain signal.
- Kim's C-vector is a LAION-trained CLIP representation with strong semantic, iconographic,
  chronology, artist-association, and possible exact-work exposure signal.
- CSD is directly optimized using caption-derived artist, medium, and movement tags. It is a
  promising painter-association candidate, but not a content-free or training-independent style
  instrument; its official repository also reports a current checkpoint/paper discrepancy.
- Artist classification, retrieval, or prompted-name recovery establishes label-associated
  signal. It does not establish within-painter coverage, source invariance, or painterly-form
  construct validity.

The prospective disposition is therefore a **profile with separately validated representation
families**, not a single learned score. Kim A remains a historical appearance coordinate; Kim C
remains a semantic/contextual diagnostic; CSD and ALADIN are secondary painter-specificity
candidates; memorization and prompt alignment remain separate audit layers.

## 2. Construct and naming discipline

| Object | Defensible name | What it can show after validation | What it cannot show by architecture alone |
|---|---|---|---|
| SD2 first-stage latent | Kim A-vector or SD2 VAE latent | model-specific appearance/reconstruction regularities | formal style, painter intention, or source invariance |
| CLIP image feature | Kim C-vector or CLIP image embedding | semantic/contextual and web-associated visual regularities | pure context, pure form, or absence of training overlap |
| CSD feature | CSD embedding plus exact readout | caption-supervised artist/medium/movement-associated similarity | calibrated painter fidelity from raw cosine |
| ALADIN feature | ALADIN fine-grained appearance embedding | retrieval similarity learned from weak style groupings | historical-painting validity or painter coverage |
| classifier output | held-work painter prediction | discriminant label signal in the tested label set | unique painter style or a complete oeuvre signature |
| painter prototype | mean/medoid in a declared space | central tendency of the sampled reference works | multimodality, phases, rare modes, or coverage |
| painter feature | qualified distribution across works | target fit, specificity, and coverage under a stated domain | an intrinsic timeless essence of a painter |

“Style” is especially hazardous because papers use it for Gram correlations, normalization
parameters, web tags, artist labels, movement labels, visual resemblance, or generated prompt
effects. This review uses each representation's exact technical name until human and nuisance
qualification supports a narrower perceptual claim.

## 3. Kim et al. 2026: paper, supplement, and exact source audit

### 3.1 Citation and source identity

The primary paper is Jin Kim, Byunghwee Lee, Taekho You, and Jinhyuk Yun, “Context-aware
multimodal AI navigates hidden pathways in five centuries of art evolution,” *Proceedings of the
National Academy of Sciences* 123(30), e2517969123 (2026),
[doi:10.1073/pnas.2517969123](https://doi.org/10.1073/pnas.2517969123), with the article and
supplement accessible through [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC13416963/).

The released repository was audited at the exact commit
[`7da12358cf34dad2184f357a048c2cf114b3c4e0`](https://github.com/aljinny/art-history/tree/7da12358cf34dad2184f357a048c2cf114b3c4e0).
The checkout names package versions but does not contain a complete environment lock, an explicit
license, the paper's extracted vector files, a checkpoint hash, or the posterior RNG realization.
Its A-vector script is not directly executable: model initialization is indented after a return,
module-level code refers to an undefined `model`, and author-local absolute paths remain.

These omissions set a hard reproducibility boundary. The project can build a source-faithful,
versioned **compatibility reconstruction**, but it cannot promise exact A- or C-vector
replication. Repairing the A script or supplying a model/checkpoint is an adaptation. The C
implementation remains provisional until the full artifact contract—resolved weights,
dependency versions, preprocessing behavior, reference fixture, and numeric tolerance—is
recovered. Compatibility outputs must never be described as the authors' unreleased vectors.

### 3.2 Corpus and eligibility domain

Kim et al. begin from ART500K, introduced by Mao, Cheung, and She in
[DeepArt](https://doi.org/10.1145/3123266.3123405). The final analysis uses 72,447 Western
paintings, 2,354 attributed painters, dates from 1500 to 1990, and 128 conventional style-period
labels. ART500K aggregates sources including Google Arts & Culture, WikiArt, and Web Gallery of
Art rather than constituting a controlled digitization corpus.

Important domain facts are:

- approximately one quarter of dates are approximate;
- date spans are assigned their last year and then floored to a decade;
- metadata filters use manually supplied words and ordered fields;
- the article's prose describes a 410 by 410 resolution rule, while the released notebook checks
  area `height * width > 410 * 410`;
- aspect ratios at least two are removed; and
- every retained image is then forced to 512 by 512.

No independent physical-work identifier, alternate-reproduction grouping, source-disjoint split,
crop/frame control, or training-overlap audit underlies the published representation analyses.

### 3.3 Published and released A- and C-vector contracts

| Dimension | A-vector | C-vector |
|---|---|---|
| Intended paper role | artistic/formal information | contextual/semantic information |
| Released model | Stable Diffusion 2.0 first-stage VAE | CLIP Interrogator `ViT-H-14/laion2b_s32b_b79k` |
| Input path | OpenCV-resized intermediate | original image opened through Pillow |
| Resize | forced 512 by 512, `INTER_LANCZOS4` | CLIP Interrogator/model-native path |
| Codec behavior | resized file written under original extension; JPEG is re-encoded, PNG remains PNG | original container path |
| Tensor/feature | sampled and scaled `4 x 64 x 64` posterior latent, C-order flatten | 1,024-dimensional CLIP image feature |
| Dimension | 16,384 | 1,024 |
| Stochasticity | posterior sample; paper RNG unpublished | deterministic under fixed software/model |
| Primary signal risks | color, content, layout, texture, warp, codec, VAE training domain | content, iconography, period, captions/web association, exact-work exposure |

The resizing script uses OpenCV, performs its particular channel conversions, resizes to a square,
and writes with the original extension. The extraction script reopens that file with Pillow,
converts to RGB, maps pixels to `[-1,1]`, calls `encode_first_stage` and
`get_first_stage_encoding`, then flattens the scaled posterior sample. The A-vector is therefore
a stochastic, lossy reconstruction code, not an invariance-engineered painter descriptor.

The C-vector script instantiates CLIP Interrogator with a LAION-2B-trained ViT-H/14 model and calls
`image_to_features` on the original image. A and C consequently differ in model objective,
training data, and preprocessing. Their contrast cannot be interpreted as a controlled
decomposition of the same pixels into form and context.

### 3.4 Published validation and its limits

| Published diagnostic | A-vector | C-vector | Interpretation boundary |
|---|---:|---:|---|
| Year regression (R^2), repeated random painting splits | 0.2024 | 0.8687 | chronology signal, not painter-form validity |
| Year Pearson correlation | 0.4505 | 0.9324 | same boundary |
| Ten-painter balanced accuracy | 0.3268 | 0.8226 | label-associated discrimination; artist/source/content overlap remains |
| Ten-style balanced accuracy | 0.2507 | 0.7495 | conventional label prediction, not construct isolation |
| Artist-disjoint year (R^2) | 0.189 | 0.850 | reduces direct artist leakage for year only |
| Artist-disjoint year correlation | 0.438 | 0.922 | does not address source, duplicate work, or encoder pretraining |

Kim et al. also report shorter within-painter and within-style distances, especially in C-space.
Those pairwise comparisons reuse each painting many times; the enormous pair count is not an
equivalent number of independent works. A p-value near zero under dependent pairs does not
establish practical separation or source-invariant painter specificity.

PCA examples associate A directions with brightness, blue/orange balance, composition, and
pattern, while C directions include people, abstraction, and related semantic content. These
examples are useful evidence that the spaces mix the claimed constructs; post-hoc visual
interpretation is not convergent validation. UMAP was separately fitted to A and C with
`n_neighbors=100`, `min_dist=0`, and `random_state=102`; those plots are visualizations, not
measurement spaces.

The paper's SynthCLIP sensitivity analysis reduces direct training on real photographs, but its
synthetic corpus was produced by a diffusion model trained on web imagery. It cannot rule out
indirect art-corpus knowledge. The generative century-shift experiment is likewise
evaluator-coupled: a C-based year predictor assesses images transformed by another component of
the same broad web-trained model ecosystem.

### 3.5 Painter-feature disposition

| Criterion | A-vector | C-vector |
|---|---|---|
| Painter specificity | pooled artist-label predictability; not content/source qualified | strong label predictability; semantic and training association are plausible causes |
| Within-painter coverage | not evaluated | not evaluated |
| Same-movement hard negatives | limited aggregate distance evidence | limited aggregate distance evidence |
| Source/digitization transfer | not established | not established |
| Content independence | not established; spatial reconstruction objective retains content | contradicted by semantic directions and CLIP objective |
| Pretraining leakage | possible through SD2 training and exact works | high concern through LAION/CLIP web training |
| Reboot role | `diagnostic_only` historical appearance coordinate | `diagnostic_only` semantic/contextual coordinate |

The [Pilot 2 audit](00_pilot_2_painter_feature_audit.md) supplies the decisive local evidence:
the harmonized A-vector reached only 0.50 held painter balanced accuracy, classified acquisition
source at 0.8125, and transferred across sources at only 0.25/0.375 balanced accuracy. Those
two balanced-accuracy values come from unlike four-class and two-class tasks and are not ranked
directly. Together with failed opposite-source transfer, the results do not invalidate the
representation for all purposes, but they reject it as the sole
painter feature for this corpus design. The positive result is limited to pooled artist-label
predictability within the fixed Pilot 2 atlas; it established no transferable painter feature.
Because the registered generator grids were incomplete and the primary tests were not run, it
also established no generated-output effect.

For any new A-vector study, use the posterior mean as the primary deterministic coordinate or
integrate repeated posterior draws and propagate encoder variance. A content-derived seed makes
one arbitrary draw reproducible; it does not make the draw uniquely meaningful. This branch is a
methodological adaptation. A separate compatibility branch should preserve every recoverable
published choice, record each repair, and stop short of an exact-replication claim.

## 4. CSD and the raw-cosine problem

### 4.1 Original method

Somepalli et al., “Investigating Style Similarity in Diffusion Models,” *ECCV 2024*,
[doi:10.1007/978-3-031-72848-8_9](https://doi.org/10.1007/978-3-031-72848-8_9),
[official paper](https://www.ecva.net/papers/eccv_2024/papers_ECCV/html/8294_ECCV_2024_paper.php),
[official repository](https://github.com/learn2phoenix/CSD), trains Contrastive Style Descriptors
from CLIP ViT-B/L initialization.

The training set is not WikiArt artist supervision. It begins from LAION-Aesthetics 6+, builds a
style vocabulary from prompt and CLIP-Interrogator terms, searches captions for artist, medium,
and movement tags, removes overly generic tags, removes unavailable images, and deduplicates with
SSCD. The final set contains 511,921 images and 3,840 multi-label tags. Training runs for 80,000
iterations with multi-label contrastive learning plus a style-preserving spatial
self-supervision term. Color jitter, blur, and grayscale are avoided so that color/texture cues
are not deliberately erased.

WikiArt evaluation contains 80,096 works, 1,119 painters, and 27 genres, divided randomly into
database and query works. Painter identity is explicitly a proxy rather than a gold-standard
style construct. The human test uses 30 untrained participants, three judgments per item, and a
four-way same-painter task. This supports constrained attribution resemblance, not full oeuvre
coverage or expert construct validity.

Generated-image validation assumes that the artist named in the prompt is the correct style
label. Simple prompts cover 400 artists with ten seeds; additional experiments use Lexica prompts
and a small set of content-controlled nouns. These designs measure prompted-name recoverability,
not absolute painter-distribution fidelity.

The repository currently warns that uploaded weights produce discrepancies from paper results.
Until a checkpoint hash reproduces a declared reference suite, CSD cannot be a frozen primary
evaluator.

### 4.2 CSD+ diagnostic

Jörg Frochte, “When Style Similarity Scores Fail: Diagnosing Raw CSD Cosine in Artist-Style
Evaluation,” [arXiv:2605.09030v2](https://arxiv.org/abs/2605.09030) (2026), evaluates 1,799
public-domain works by 91 painters. It defines a painter discrimination gap as within-painter
median similarity minus the strongest cross-painter median similarity.

Raw CSD cosine produced negative pairwise gaps for 23 of 91 painters, with two bootstrap intervals
fully below zero; pooled painter representations were negative for 15 of 91. CSLS with $k=15$
reduced pooled failures to four, and interpolation plus CSLS modestly improved pair AUC. Shared
traditions remained difficult across CSD, CLIP, SigLIP, and DINOv2.

This is strong evidence against treating raw cosine as calibrated. It is not yet validation of a
replacement:

- the paper is a preprint;
- CSLS depends on the candidate reference pool, so an image's score can change when unrelated
  painters are added;
- the artist set and movement mapping are curated and small;
- many individual negative gaps remain statistically uncertain; and
- the paper incorrectly says original CSD was fine-tuned on WikiArt painter labels, whereas the
  original training used caption-derived LAION style tags.

### 4.3 CSD disposition

| Question | Evidence | Disposition |
|---|---|---|
| Does CSD contain painter-label signal? | yes: WikiArt retrieval, constrained human matching, generated-prompt tests | retain as `secondary_candidate` |
| Is that signal formal rather than semantic/training-associated? | unresolved; painter/medium/movement caption tags directly supervise training | require content, source, and unseen-painter tests |
| Does raw cosine calibrate target specificity? | no; CSD+ finds negative gaps and local hubs | prohibit raw cosine as a primary score |
| Does CSD measure within-painter coverage? | no direct validation | require bidirectional set-level analysis |
| Is the public artifact frozen and reproduced? | no; repository reports checkpoint discrepancy | fail closed until reconciled |
| Can CSLS be used? | only as a declared candidate-pool-dependent sensitivity readout | never compare scores across different reference pools |

## 5. Related learned representations: evidence and disposition

| Source | Representation, data, and validation | Main threat to painter inference | Prospective disposition |
|---|---|---|---|
| [Gatys, Ecker & Bethge 2016](https://doi.org/10.1109/CVPR.2016.265) | ImageNet VGG-19 content activations plus layerwise Gram correlations; exemplar style-transfer evaluation | stationary feature correlations are called style but ignore oeuvre and spatial arrangement | `diagnostic_only` formal-texture baseline |
| [Li et al. 2017](https://doi.org/10.24963/ijcai.2017/310) | proves Gram matching equals MMD with a degree-two polynomial kernel | explains the chosen statistic; does not validate a painter construct | `background_only`, informs kernel language |
| [Karayev et al. 2014](https://doi.org/10.5244/C.28.122) | object-trained deep features predict 20 Flickr visual styles and 25 painting style/genre labels | label prediction can use objects, scenes, period, and source | `background_only`, shortcut warning |
| [Saleh & Elgammal 2016](https://doi.org/10.11588/dah.2016.2.23376) | fine-art artist/genre/style classification and metric retrieval | WikiArt labels and source/content/chronology are entangled | attribution baseline only |
| [Elgammal et al. 2018](https://doi.org/10.1609/aaai.v32i1.11894) | CNN representations and temporal manifolds over about 67,000 paintings | chronology and subject can create apparent historical structure | hypothesis-generating only |
| [Cetinic, Lipic & Grgic 2018](https://doi.org/10.1016/j.eswa.2018.07.026) | compares object-, scene-, and sentiment-initialized CNNs on five art tasks | upstream task substantially changes the art representation | mandates evaluator-family sensitivity |
| [DeepArt 2017](https://doi.org/10.1145/3123266.3123405) | ART500K and joint content/style triplet/ranking representation | joint by construction; aggregated-source labels and duplicates | corpus/provenance source, not validation |
| [OmniArt 2018](https://doi.org/10.1145/3273022) | more than two million records and metadata-rich artist/date/type/style benchmarks | museum/source imbalance, duplicates, ontology conflict | external corpus audit candidate |
| [SemArt 2018](https://openaccess.thecvf.com/content_eccv_2018_workshops/w13/html/Garcia_How_to_Read_Paintings_Semantic_Art_Understanding_with_Multi-Modal_Retrieval_ECCVW_2018_paper.html) | visual-text retrieval from WGA catalogue comments and attributes | text may directly reveal painter, date, and context | separate contextual layer |
| [Gairola, Shah & Narayanan 2020](https://doi.org/10.1109/WACV45572.2020.9093421) | compact embedding learned from pseudo-triplets constructed with VGG Gram similarity; six datasets | circularly distills Gram assumptions; style definition changes by dataset | `secondary_candidate` after nuisance tests |
| [ALADIN 2021](https://openaccess.thecvf.com/content/ICCV2021/html/Ruta_ALADIN_All_Layer_Adaptive_Instance_Normalization_for_Fine-Grained_Style_Similarity_ICCV_2021_paper.html) | all-layer AdaIN representation, weak grouping supervision, 2.62M-image BAM-FG retrieval | modern digital-art groupings can leak creator/content/platform | `secondary_candidate`; historical transfer required |
| [StyleBabel 2022](https://doi.org/10.1007/978-3-031-20074-8_13) | expert-led participatory style taxonomy and captions for about 135,000 digital artworks | modern digital-art and English-language domain | use vocabulary for human attribute validation |
| [Dumoulin, Shlens & Kudlur 2017](https://arxiv.org/abs/1610.07629) | conditional instance-normalization parameters encode styles in a multi-style generator | generation-control parameters lack independent similarity validation | exclude as painter metric |
| [Kotovenko et al. 2019](https://openaccess.thecvf.com/content_ICCV_2019/html/Kotovenko_Content_and_Style_Disentanglement_for_Artistic_Style_Transfer_ICCV_2019_paper.html) | triplet/fixpoint disentanglement over ten painters plus patch-level human/classifier tests | small style set; deception/preference is not oeuvre validity | adopt content-matched human-control ideas |
| [GOYA 2024](https://doi.org/10.3390/jimaging10070156) | CLIP transforms learned from Stable-Diffusion synthetic content-by-style pairs; evaluated on 81,445 WikiArt works | generator and CLIP priors define the separation; labels imperfect | `secondary_candidate` sensitivity only |
| [CSD 2024](https://doi.org/10.1007/978-3-031-72848-8_9) | CLIP fine-tuned on 511,921 images using caption-derived multi-label artist, medium, movement, and other style tags; WikiArt/prompt evaluation | noisy caption-derived tags rather than curated painter ground truth, source/pretraining overlap, artifact discrepancy | provisional `secondary_candidate` |
| [ArtSavant 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/63ef323523f3be8b58ed9277cc747485-Abstract-Conference.html) | CLIP-based DeepMatch and 260-tag TagMatch over 90,960 WikiArt works/372 painters; set-level generated tests | recognizability can rely on subject/source/era/CLIP exposure; random work split | adopt set voting, competitors, abstention; reject “recognizable = unique style” |
| [Su et al. 2025](https://arxiv.org/abs/2507.18633) | 1.95M generated images, 110 painters, complex/multiple-painter prompts and multiple generators | measures prompted-name recovery; strong generator-domain dependence | prompt-audit benchmark, not real-oeuvre metric |
| [DiffSim 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Song_DiffSim_Taming_Diffusion_Models_for_Evaluating_Visual_Similarity_ICCV_2025_paper.html) | aligned diffusion attention features; seven similarity benchmarks including synthetic Sref styles | diffusion-model-coupled and mixes subject/background/appearance | evaluator-family sensitivity only |

Two recurring results govern the reboot. First, an encoder's upstream objective determines the
meaning of its distances. Second, random held-image splits are insufficient when the same
painters, sources, web reproductions, and pretraining ecosystem occur on both sides.

## 6. Neural style-transfer and perceptual metrics

| Source | Actual construct | Painter-feature use |
|---|---|---|
| [ArtFID, Wright & Ommer 2022](https://arxiv.org/abs/2207.12280) | `(1 + mean LPIPS content loss) x (1 + art-feature FID)`; art encoder trained on 241,088 works/595 artists/109 styles; 13 NST methods and large AMT comparison | useful method-level NST benchmark; not target-painter specificity or coverage, and ordinary FID needs large sets |
| [LPIPS, Zhang et al. 2018](https://doi.org/10.1109/CVPR.2018.00068) | calibrated full-reference deep-feature distance from human distortion/restoration judgments | same-work reproduction and content-preservation control only |
| [DISTS, Ding et al. 2022](https://doi.org/10.1109/TPAMI.2020.3045810) | full-reference structure/texture image-quality similarity | digitization/perturbation control only |
| [DreamSim, Fu et al. 2023](https://papers.nips.cc/paper_files/paper/2023/hash/9f09f316a3eaf59d9ced5ffaefe97e0f-Abstract-Conference.html) | holistic human similarity learned from 477,964 judgments over synthetic triplets | useful competing perceptual evaluator; content- and generator-sensitive |
| [CLIPScore, Hessel et al. 2021](https://doi.org/10.18653/v1/2021.emnlp-main.595) | reference-free image-caption alignment validated on caption judgments | prompt/semantic alignment only; explicitly outside formal painter score |

Human agreement with a neural-style-transfer method ranking does not validate the same metric for
historical painter identification. Full-reference metrics are valuable for reproduction
reliability precisely because that is a different construct.

## 7. Memorization, copying, and training-set attribution are separate

A generated image may be near a painter distribution without copying a work; it may copy a local
motif while scoring poorly on an aggregate painter metric. These outcomes require distinct audit
tracks.

| Source | Method and validation | Allowed use | Prohibited inference |
|---|---|---|---|
| [SSCD, Pizzi et al. 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Pizzi_A_Self-Supervised_Descriptor_for_Image_Copy_Detection_CVPR_2022_paper.html) | self-supervised copy descriptor validated on DISC2021; aspect-preserved and square preprocessing variants | exact/near-copy retrieval with locally calibrated thresholds | style or painter similarity |
| [Somepalli et al. 2023](https://doi.org/10.1109/CVPR52729.2023.00586) | SSCD-based replication search across controlled data and a 12M-image LAION subset | generator replication audit | complete training-set prevalence or painter fidelity |
| [Carlini et al. 2023](https://www.usenix.org/conference/usenixsecurity23/presentation/carlini) | generate-and-filter extraction; more than 1,000 diffusion training examples recovered | establishes extraction risk and attack methodology | prevalence under ordinary prompts |
| [Somepalli et al. 2023, NeurIPS](https://papers.nips.cc/paper_files/paper/2023/hash/9521b6e7f33e039e7d92e23f5e37bbf4-Abstract-Conference.html) | shows caption/text conditioning contributes to copying beyond duplicates | artist-name/prompt risk interpretation | style similarity |
| [Wen et al. 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/993760d9b1d63a385611c7c9ef8f3ecb-Abstract-Conference.html) | first-step prediction magnitude and token attribution detect risky prompts | prompt-level memorization diagnostic | proof a painter was in training |
| [Chen et al. 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/498c7e2589cd2e5b9886d0ba9a5e6032-Abstract-Conference.html) | bright-ending attention localizes memorized patches | local-copy audit missed by global metrics | full-image style inference |
| [Wang et al. 2023](https://doi.org/10.1109/ICCV51070.2023.00661) | Attribution by Customization creates known-influence evaluation sets | benchmark attribution methods under known intervention | opaque base-model training attribution from similarity alone |

Every generated-painter analysis should therefore report nearest real-work copy evidence and local
patch evidence separately from painter-distribution results. Similarity alone cannot establish
causal training exposure, especially for closed models.

## 8. Distributional fidelity, specificity, and coverage

A painter prototype is insufficient even in a qualified representation. The generated and real
sets need distributional comparisons with sample-size and encoder sensitivity.

| Source | Contribution | Limitation and use |
|---|---|---|
| [FID, Heusel et al. 2017](https://papers.nips.cc/paper_files/paper/2017/hash/8a1d694707eb0fefe65871369074926d-Abstract.html) | Gaussian mean/covariance distance in Inception-v3 space | mixes fidelity/coverage, ImageNet semantics, Gaussian assumption, finite bias; reject as painter score |
| [KID, Bińkowski et al. 2018](https://openreview.net/forum?id=r1lUOzWCW) | unbiased polynomial-kernel MMD estimator | encoder/kernel-dependent; candidate statistic only after local qualification |
| [Sajjadi et al. 2018](https://papers.nips.cc/paper_files/paper/2018/hash/f7696a9b362ac5a51c3dc8f098b73923-Abstract.html) | distributional precision/recall separates quality and coverage | clustering sensitivity; essential conceptual split |
| [Kynkäänniemi et al. 2019](https://proceedings.neurips.cc/paper/2019/hash/0234c510bc6d908b28c70ff313743079-Abstract.html) | kNN-manifold precision and recall | sensitive to $k$, outliers, encoder, and sample size; use with calibration curves |
| [Naeem et al. 2020](https://proceedings.mlr.press/v119/naeem20a.html) | density and coverage correct several precision/recall failures | still neighborhood/feature dependent; strong candidate coverage diagnostic |
| [Chong & Forsyth 2020](https://doi.org/10.1109/CVPR42600.2020.00611) | exposes model-dependent finite-sample FID bias and proposes extrapolation | requires equal-sample and sample-size sensitivity analyses |
| [Stein et al. 2023](https://papers.nips.cc/paper_files/paper/2023/hash/0bc795afae289ed465a65a3b4b1f4eb7-Abstract-Conference.html) | 17 metrics across nine encoders versus a large human realism study | no universal metric; report evaluator disagreement rather than select favorable rankings |
| [CMMD, Jayasumana et al. 2024](https://openaccess.thecvf.com/content/CVPR2024/html/Jayasumana_Rethinking_FID_Towards_a_Better_Evaluation_Metric_for_Image_Generation_CVPR_2024_paper.html) | unbiased Gaussian-kernel MMD on CLIP features without Gaussian feature assumption | CLIP semantic/web bias remains; contextual distribution diagnostic only |

For a target painter $a$, the reboot keeps eight outcome families distinct. A canonical
painter-fidelity claim requires the first six to pass **conjunctively**:

1. **Absolute target fit/equivalence:** a prespecified two-sample discrepancy between generated
   $Q_a$ and held real $P_a$, judged against a frozen real-to-real reference scale and an
   equivalence or noninferiority margin. Failure to reject a difference is not evidence of fit.
2. **Hard-neighbor specificity:** the full target-versus-competitor margin vector for a
   prospectively selected set of same-movement, same-period, same-medium, content-matched painters,
   all evaluated on one panel-wide common support; the frozen worst and lower-quantile rules are
   binding rather than an average or favorable neighbor.
3. **Generated-to-real support:** precision and density must each meet independently frozen
   criteria.
4. **Real-to-generated support:** recall and coverage must each meet independently frozen criteria.
5. **Content coherence:** absolute fit, specificity, and support must meet a frozen cross-content
   robustness rule.
6. **Availability:** refusals and terminal failures must meet the frozen availability and
   missingness-robustness rule.
7. **Contraction:** generated versus real dispersion is mandatory but has no automatically
   favorable direction.
8. **Prompt-induced movement:** named versus painter-free paired change under fixed content,
   generator, prompt family, and seed policy is mandatory but cannot rescue a failed conjunct.

A positive prompt-induced centroid movement can coexist with poor absolute fit and severe mode
contraction. A positive one-neighbor margin can coexist with greater similarity to untested
painters. No single quantity may stand in for the others.

## 9. Specific prospective consequences

This section states learned-representation consequences only; the full sampling and inference
protocol belongs in the new study protocol.

### 9.1 Candidate admission

1. No learned representation is automatically primary because its title or training labels say
   “style.”
2. Kim A, Kim C, CSD, ALADIN, and one general perceptual/self-supervised comparator should be
   evaluated as separately versioned candidate modules. Kim A/C modules are compatibility
   reconstructions unless and until complete artifact contracts are recovered.
3. A candidate advances only if painter discrimination survives held physical works, held source,
   matched content/medium/date, and independent-reproduction tests.
4. Checkpoint, code revision, preprocessing, dtype, device, feature layer, normalization, distance,
   and any reference pool must be hashed and named.
5. CSD remains closed to primary use until the public checkpoint discrepancy is reconciled on a
   frozen reference fixture.

### 9.2 Preprocessing and stochasticity

1. Decode each source once to a common, metadata-free, lossless color-managed representation;
   then apply each encoder's frozen native transform.
2. Record whether native preprocessing crops, stretches, or pads. Run an aspect-preserving
   sensitivity branch whenever the original method forces a square.
3. Do not let real/generated origin determine codec or preprocessing path.
4. Use posterior mean for Kim A's primary deterministic candidate, or repeated posterior draws
   with variance propagation. Label either choice an adaptation. Preserve the recoverable
   historical seeded-sample path only as a named, versioned compatibility reconstruction; do not
   call it an exact replication.
5. Fit PCA, standardization, metric learning, CSLS reference pools, bandwidths, and thresholds on
   real development data only. UMAP/t-SNE never enters an estimand.

### 9.3 Painter specificity and leakage tests

1. Split by physical work; alternate reproductions remain in the same work group.
2. Require leave-source-out and sealed external-source transfer rather than source-stratified
   pooled accuracy alone.
3. Test same-painter versus same-movement hard negatives under matched genre, motif, period,
   medium, and source.
4. Include source, collection, codec, frame/border, genre, period, and subject prediction probes.
   A high nuisance score is evidence about the representation even when the corpus is balanced.
5. Audit exact and near-copy overlap with encoder pretraining where records permit; include unseen
   or low-exposure painters to test whether the readout generalizes beyond memorized names.
6. Use expert, content-matched triplets and interpretable attributes for convergent/discriminant
   validation. Untrained four-way attribution alone is insufficient.

### 9.4 Distribution and reporting

1. Model painter profiles across works and, where support permits, phase/genre/medium strata. Do
   not reduce the real oeuvre to one centroid.
2. Report target fit/equivalence; the full panel-wide hard-neighbor specificity vector; one
   simulation-selected primary support pair; the alternative neighborhood estimators as
   sensitivity; content coherence; availability; copying; contraction; and prompt movement
   separately. Any conjunctive decision is a prospectively simulated project rule, not a
   literature-validated universal metric. Contraction and prompt movement remain mandatory
   nongating outcomes.
3. Use work-, painter-, prompt-, and seed-level clustered or hierarchical uncertainty. Pairwise
   distances are not independent observations.
4. Report feature-family disagreement. A formal coordinate, CSD, and CLIP may disagree because
   they measure different regularities; disagreement is a result, not a reason to average them.
5. Keep semantic prompt alignment, exact/local copying, and training-exposure proxies outside the
   painter-formal profile.

## 10. Evidence grades and final decisions

Grades describe support for this project's proposed use, not general paper quality.

| Method/source | Grade for painter-feature use | Decision |
|---|---:|---|
| Kim A-vector | C | historical `diagnostic_only`; source/content qualification failed locally |
| Kim C-vector | C | contextual `diagnostic_only`; do not place in formal profile |
| CSD | B- concept / unresolved artifact | `secondary_candidate`, fail closed for primary use |
| CSD+ raw-cosine diagnosis | C, preprint | adopt warning; evaluate readouts prospectively |
| ALADIN | B- | `secondary_candidate` after historical-painting transfer |
| Gairola unsupervised style embedding | C+ | secondary Gram-derived comparator |
| GOYA | C+ | generator/CLIP-dependent sensitivity only |
| ArtSavant | B- for set recognition | adopt competitors, set aggregation, tags, and abstention; reject uniqueness inference |
| Su prompted-painter benchmark | B- for generator-domain recognition | prompt-condition diagnostic only |
| ArtFID | B for method-level neural style transfer | not a target-painter metric |
| SSCD | A- for copy detection in its validated domain | separate copy audit with local threshold calibration |
| density/coverage and precision/recall families | B as generic estimators | qualify in each candidate feature space |

No reviewed learned method receives an A-grade painter-feature disposition. The reboot's
scientific contribution is therefore not to select the most fashionable embedding. It is to
show which declared representations support painter-associated distributions after the sources
of easy recognition have been challenged, and to report where specificity, coverage, semantics,
and copying disagree.
