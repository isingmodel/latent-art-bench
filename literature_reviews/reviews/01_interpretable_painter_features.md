# Interpretable coordinates for a painter feature

Review depth: methods/results for 39 primary studies and authoritative method sources

Question: which transparent image measurements could contribute to a painter-associated
distribution after reproduction and nuisance qualification?

## 1. Conclusion

No transparent coordinate is a painter feature by itself. The best-supported candidates form a
multitrait profile:

1. CIELAB moments/covariance and full local chromatic-distance distributions;
2. multiscale Fourier/wavelet energy and orientation structure;
3. tie-aware two-by-two ordinal-pattern probabilities and derived entropy/complexity;
4. PHOG-like gradient self-similarity, complexity, and anisotropy; and
5. coarse spatial maps of those same measurements.

Each is a descriptor of declared digital reproductions. It contributes to a painter feature only
if painter signal survives held-work, held-source, held-content, medium/date, and human construct
tests. Ordinary web RGB does not support literal pigment, binder, surface-relief, or physical
brushstroke claims.

## 2. Claim levels

| Level | Defensible statement | Required evidence |
|---|---|---|
| D0 | property of exact decoded bytes | formula/runtime identity |
| D1 | property of a declared digital reproduction | color/scale/crop/codec domain plus perturbation evidence |
| D2 | property of physical appearance/material | calibrated colorimetric, spectral, physical-scale, or topographic acquisition |
| D3 | painter-associated feature | D1/D2 reliability plus crossed held-work/source/content/medium/date and human validity |

The reviewed large catalog studies mostly support D0/D1 aggregate descriptions. Controlled
museum/topography studies show what D2 would require. D3 is the new study's task.

## 3. Color and local chromatic organization

### 3.1 Primary lineage

| Source | Method and corpus | Evidence useful here | Limitation and disposition |
|---|---|---|---|
| [Kim, Son & Jeong 2014](https://doi.org/10.1038/srep07370) | RGB rank use, RGB-cube color-gamut box counts, brightness roughness, weighted local entropy; 8,798 WGA works | large historical precedent; exact 500×500 Lanczos rule for entropy | single web source; period/source/content confounding; `secondary_candidate` |
| [Lee et al. 2018](https://doi.org/10.1371/journal.pone.0204430) | adjacent-pixel CIELAB \(\Delta E^*_{ab}\) distribution and mean-rescaled form; 179,853 works | complete distribution is interpretable; explicit source exclusions; two-work scale illustration | raw distance is resolution/color-pipeline dependent; scale collapse not corpus-wide; `core_candidate` after qualification |
| [Seo et al. 2018](https://doi.org/10.3938/NPSM.68.693) | recursive quasi-homogeneous regions and color interaction; three paintings | demonstrates spatial palette relations beyond a global histogram | sample of three and threshold sensitivity; `diagnostic_only` |
| [Montagner et al. 2016](https://doi.org/10.1364/JOSAA.33.00A170) | color statistics of paintings versus natural scenes | tests whether painters reproduce natural color statistics | category comparison is not painter validity; `background_only` |
| [Nascimento et al. 2017](https://doi.org/10.1016/j.visres.2016.11.006) | observers rotated 3D color gamuts of 10 paintings; 50 observers | original gamut orientation was perceptually meaningful | small work set; preference is not painter identity; supports gamut/covariance coordinates |
| [Nakauchi et al. 2022](https://doi.org/10.1038/s41598-022-08365-z) | hue rotation, spatial scrambling, calibrated/hyperspectral subset; cross-cultural observers | global chromatic composition retained perceptual information even with spatial rearrangement | limited painting/culture panel; supports color distribution, not quality |
| [Nakauchi & Tamura 2022](https://doi.org/10.1038/s41598-022-18847-9) | \(L^*,a^*,b^*\) means, variance, skewness, correlations; 1,200 paintings/4,800 variants/31,353 participants | strong direct evidence for first-through-third moments and covariance as preference-relevant | uncontrolled online displays and WikiArt source; aesthetic preference is not painterly manner; `secondary_candidate` |
| [Graham & Field 2008](https://doi.org/10.1068/p5971) | grayscale moments/sparseness with 140 consistently scanned works | unusually consistent acquisition; useful nuisance controls | provenance/content/medium still covary; not cultural or painter essence |

### 3.2 Retained color coordinates

The prospective profile retains:

- quantiles and first-through-third moments of \(L^*\), \(a^*\), \(b^*\), and chroma;
- \(L^*,a^*,b^*\) covariance/correlation and gamut principal axes;
- circular hue moments above a frozen low-chroma threshold;
- a fixed joint lightness/chroma/hue occupancy representation;
- Lee-source-faithful adjacent \(\Delta E^*_{ab}\) distributions, means, coefficient of variation,
  quantiles, direction contrast, and normalized shape; and
- CIEDE2000 as a technical sensitivity coordinate verified against [Sharma et al.'s test data](https://doi.org/10.1002/col.20070),
  not as a style score.

Color-harmony templates are not retained as primary. Their palette extraction and template
thresholds are unstable, and the observer literature validates organization/preferences rather
than a universal harmony score.

## 4. Multiscale texture, spatial frequency, and edges

### 4.1 Fourier and gradient evidence

| Source | Method/design | Decision-relevant result | Limitation |
|---|---|---|---|
| [Graham & Field 2007](https://doi.org/10.1163/156856807782753877) | amplitude-spectrum slopes, sparseness, filter responses; 124 paintings | paintings share some natural-scene regularities | reproduction and content remain entangled; naturalness is not quality |
| [Koch, Denzler & Redies 2010](https://doi.org/10.1371/journal.pone.0012268) | windowed 2D Fourier power, radial slope, 16-sector anisotropy; multiple art/photo sets | slope near \(1/f^2\) and relatively low anisotropy describe groups; matched landscapes partly control content | heavy overlap; authors caution these are neither necessary nor sufficient for aesthetics |
| [Braun et al. 2013](https://doi.org/10.3389/fpsyg.2013.00808) | 100,000-pixel PHOG; self-similarity, summed gradient strength, anisotropy | transparent multiscale edge profile distinguishes image groups on average | absolute values change with resolution and pyramid depth |
| [Redies & Groß 2013](https://doi.org/10.3389/fpsyg.2013.00831) | same paintings through museum, catalog, and other reproduction routes | frame inclusion affected measurements; reproduction groups showed no statistically significant aggregate difference | no equivalence or work-level repeatability test, so the null group result is not reproduction invariance |
| [Redies, Brachmann & Wagemans 2017](https://doi.org/10.1016/j.visres.2017.02.004) | pairwise relative edge-orientation entropy in >1,600 Western and other art sets | high relative-orientation entropy generalized across several cultural sets/content controls | group-level regularity, not painter specificity or composition quality |
| [Redies & Brachmann 2017](https://doi.org/10.3389/fnins.2017.00593) | Fourier slope, fractal dimension, edge entropies, self-similarity across traditional/bad/abstract art | demonstrates overlap and multi-coordinate character of image groups | aesthetic category/source labels are not construct ground truth |
| [Essock & Schweinhart 2016](https://doi.org/10.1177/0301006616633384) | ten artists painted one shared source scene; orientation by spatial frequency | unusually strong content control; painters changed orientation structure across scales | one scene and ten painters; medium/translation remains systematic |

### 4.2 Wavelet, local texture, and visible-stroke evidence

| Source | Method/design | Use | Boundary |
|---|---|---|---|
| [Lyu, Rockmore & Farid 2004](https://doi.org/10.1073/pnas.0406398101) | multiscale/multiorientation wavelet coefficient statistics on 13 Bruegel drawings split into patches | proves local multiscale texture can encode attribution signal | 13 drawings; patches are not independent works |
| [Hughes, Graham & Rockmore 2010](https://doi.org/10.1073/pnas.0910530107) | sparse coding of Bruegel patches | explicitly exposes scale/downsampling/physical-area dependence | small specialist drawing set |
| [Johnson et al. 2008](https://doi.org/10.1109/MSP.2008.923513) | Van Gogh museum challenge across wavelet, stroke, Gabor, and classifier approaches | field benchmark with high-resolution controlled scans | synthesis of heterogeneous methods; not one qualified estimator |
| [Li et al. 2012](https://doi.org/10.1109/TPAMI.2011.203) | visible stroke extraction at 196.3 pixels per painted inch, 16-bit scans; 45 paintings | strongest RGB evidence for length/width/orientation when physical scale is shared | specialized, cropped corpus; does not generalize to web JPEGs |
| [Lamberti et al. 2014](https://doi.org/10.1186/1687-5281-2014-53) | region-growing stroke extraction on five patches against three human annotators | small direct annotation check | insufficient for a primary endpoint |
| [Abry, Wendt & Jaffard 2013](https://doi.org/10.1016/j.sigpro.2012.01.016) | wavelet-leader multifractals on controlled replicas and 200-dpi Van Gogh set | scale-indexed controlled evidence; supports retaining curves/ranges | tiny samples/manual regions; needs physical sampling |
| [Qi, Taeb & Hughes 2013](https://doi.org/10.1016/j.sigpro.2012.09.025) | background selection plus wavelet-HMT Fisher distance for Impressionist attribution/dating | treats painter manner as a texture distribution and uses leave-one-out tests | small specialized sets and manual/background assumptions |
| [Wu et al. 2014](https://arxiv.org/abs/1401.6638) | dual-tree complex wavelet HMT plus probabilistic topics on five Giotto altarpiece panels | useful local stylistic-vocabulary hypothesis | one artwork complex; exploratory, not painter population validation |

### 4.3 Physical painter's-hand comparator

[Ji et al. 2021](https://doi.org/10.1186/s40494-021-00618-w) is the clearest controlled
“painter's hand” experiment: nine painters produced triplicate works with the same subject,
materials, tools, and palette; optical surface topography outperformed photographs under
subject/color shifts, and fine height scales were informative. [Bigerelle et al. 2023](https://doi.org/10.1088/2051-672X/acbe53)
separates micrometer-scale brush, canvas, and undulation regimes. These studies support a crucial
exclusion: arbitrary web RGB gradients cannot be called physical brushstroke width or topology.

The RGB protocol retains wavelet energy, Fourier/orientation, and gradient summaries under the
label *multiscale spatial structure*. Literal painter's-hand measurement requires a future
physical-scale/topographic modality.

## 5. Ordinal and information-theoretic complexity

| Source | Method/corpus | Evidence | Decision |
|---|---|---|---|
| [Sigaki, Perc & Ribeiro 2018](https://doi.org/10.1073/pnas.1800083115) | grayscale 2×2 ordinal patterns, normalized permutation entropy and Jensen–Shannon complexity; 137,364 WikiArt images | large-scale, low-dimensional local-order lineage | `core_candidate`; classification is only indirect validation |
| [Tarozo et al. 2025](https://doi.org/10.1093/pnasnexus/pgaf092) | 75 tie-aware 2×2 states, 11 interpretable groups, entropy/complexity/Fisher information | strongest transparent ordinal representation; published per-image data | exact ties react to codec/bit depth; random style splits are not painter/source-disjoint |
| [Silva et al. 2021](https://doi.org/10.1016/j.patcog.2021.107864) | Normalized Compression, BDM, quantization, local complexity, roughness; 4,266 paintings/91 painters | compares algorithmic/compression families and local fingerprints | compressor/file representation and source/content can identify labels; `secondary_candidate` |
| [Yang & Yang 2021](https://doi.org/10.3390/e23070883) | pixel and wavelet-energy entropy on 36,000 Eastern/Western works | supports multiscale/channel-specific entropy | region, period, medium, collection, and source confounded |
| [Papia et al. 2023](https://doi.org/10.1016/j.chaos.2023.113385) | entropy/complexity on 800 human and 800 AI images across genres | precedent for real/generated comparison | generator/export/web-source artifacts can identify source; `background_only` |
| [Kim, Lee & Lee 2025](https://doi.org/10.1038/s41598-025-04448-9) | entropy/complexity, ResNet, SIFT on 149,780 platform works | modern scale/source comparison | platform/export/category confounding; not historical painter validity |

The primary ordinal output should be the full 75-state distribution and 11 group rates, not only
two scalars. Exact-tie and noise-tolerant branches must be compared. Permutation entropy and
statistical complexity are local-order measures, not creativity or historical progress.

## 6. Composition and saliency

| Source | Evidence | Decision |
|---|---|---|
| [Lee et al. 2020](https://doi.org/10.1073/pnas.2011927117) | 14,912 landscapes; long side 400, aspect preserved, frame/background removal, 3-bit colors, recursive information partition; 86.8% dominant horizontal split | source-faithful replication for landscapes only; general corpus uses coarse spatial pyramids |
| [Fuchs et al. 2011](https://doi.org/10.1007/s12559-010-9062-3) | two 12-observer studies: classical bottom-up saliency predicted early fixations above chance/center baselines | saliency may mean predicted gaze propensity, not quality or intent |
| [Le Meur et al. 2020](https://doi.org/10.1371/journal.pone.0239980) | 150 paintings, 21 observers, >44,000 fixations; deep saliency outperformed handcrafted models | learned saliency mixes content, center prior, and low-level cues; use only with transparent comparator |
| [Amirshahi et al. 2014](https://doi.org/10.1163/22134913-00002024) | 727 paintings plus photo sets and 30 observers; rule-of-thirds score weakly related to aesthetics | reject as painter-quality/style endpoint |
| [McManus et al. 2011](https://doi.org/10.1068/i0445aap) | controlled tests did not support luminance-center-of-mass as Arnheim balance mechanism | center of mass is descriptive only |
| [Mather 2020](https://doi.org/10.3390/vision4010010) | 476 one-work-per-painter set; image-statistic relations to ratings differed strongly by genre | strong reason to stratify genre; not independent external validation |
| [Swartz et al. 2024](https://doi.org/10.1038/s41598-024-69689-6) | raw statistics explained limited beauty variance and natural-scene calibration did not improve prediction | rejects low-level features as beauty proxies |

Composition is therefore represented conservatively: aspect-preserved spatial pyramids of color,
edges, entropy, and saliency; no rule-of-thirds or balance score; and Lee's partition only in a
separate landscape-compatible branch.

## 7. Fractal evidence and falsification

[Taylor et al. 1999](https://doi.org/10.1038/20833) introduced the Pollock-fractal hypothesis.
[Taylor et al. 2007](https://doi.org/10.1016/j.patrec.2006.08.012) reported sample separation with
dimensional interplay, but [Jones-Smith & Mathur 2006](https://doi.org/10.1038/nature05398)
showed that limited-range apparent fractality is easy to obtain in freehand and synthetic patterns.
[Mureika et al. 2005](https://doi.org/10.1103/PhysRevE.72.046101) likewise found limited painter
discrimination in some multifractal components.

Consequently:

- no fractal authenticity or painter score is retained;
- any multiscale fit reports the scaling range, goodness-of-fit, residuals, competing models,
  threshold sensitivity, and physical/image scale; and
- the full response curve is preferred to a single exponent.

## 8. Prospective painter-feature decision

### Core candidates

- CIELAB moments/covariance/gamut and full adjacent-color-distance distributions;
- Fourier/wavelet energy curves, orientation entropy/anisotropy, and PHOG-like self-similarity;
- 75-state tie-aware ordinal-pattern profile with derived entropy/complexity; and
- coarse spatial maps of these quantities.

### Secondary or diagnostic

- compression/BDM;
- landscape-specific information partition;
- transparent and learned saliency in parallel;
- wavelet-HMT/multifractal descriptors in controlled physical-scale subsets; and
- historical source-faithful Kim 2014 measures.

### Rejected for ordinary RGB painter inference

- literal pigment, binder, impasto, topography, or brushstroke-width claims;
- color-harmony, rule-of-thirds, visual-balance, beauty, creativity, or quality scores;
- a single fractal dimension or Pollock-authentication shortcut; and
- artist classification accuracy as sufficient validity.

The feature family is deliberately plural. A painter's corpus may show stable color organization
but variable composition, or stable multiscale mark organization but changing subject matter.
The method must expose that structure rather than compress it into a flattering number.
