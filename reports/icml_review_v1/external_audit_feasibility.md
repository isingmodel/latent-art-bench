# External broader-panel audit: feasibility

**Checked 2026-09-19 KST. Feasibility research only; no scientific score or recommendation is revised.**

## Decision

**A new, independent named-versus-control decomposition is not presently executable from the verified public numeric releases under the stated constraints.** Su et al. provide relevant controlled experiments, but the discoverable standalone arrays are real-art prototypes, not generated-image observations. Their aggregate similarity table cannot replace the missing per-condition vectors or sufficient cross-products. The official CSD release does not fill that gap. This is a finding about the public artifacts inspected, not proof that the authors lack unreleased embeddings or that archives contain no additional files.

No images, image archives, checkpoints, parquet payloads, or paid services were downloaded or used. Only public pages, API metadata, small source files, and unauthenticated HEAD requests were read. Dataset conditions were not accepted, and no author was contacted.

## 1. Su et al.: relevant design, insufficient released observations

The [paper, Sections 3.1–3.5](https://arxiv.org/html/2507.18633v1#S3) describes 110 artists, 500 simple and 1,000 complex content templates. Open-weight generators use two seeds per artist/template, with ten for SDXL complex prompts. Section 3.5 explicitly compares artist-named images against images with the artist removed, holding prompt content and seed fixed. This is relevant to a name-versus-content contrast. It does not establish a separately standardized generic-art instruction such as the current study's generic arm. Midjourney is observational rather than a matched intervention.

The compact numeric evidence already available is [Table 1](https://arxiv.org/html/2507.18633v1#S3.T1):

| Generator | Mean CLIP similarity, content-only vs named: simple | Complex |
|---|---:|---:|
| SDXL | 0.571 | 0.738 |
| PixArt-Σ | 0.632 | 0.816 |
| SD1.5 | 0.520 | 0.643 |

These are published summary results, not a newly executed independent audit. They omit artist/scene/seed-specific vectors, reference cross-products, off-diagonal relationships, and repeat structure needed for shared/specific energy or scene-influence calculations. Extracting or algebraically transforming the six means would not supply those missing observations.

## 2. Exact discoverable numeric artifacts

The author's [project page](https://graceduansu.github.io/IdentifyingPromptedArtists/) links [GitHub](https://github.com/graceduansu/IdentifyingPromptedArtists) and the [CMU dataset](https://huggingface.co/datasets/cmu-gil/PromptedArtistIdentificationDataset). Inspected revisions were:

- GitHub: `5179627e4f458848f78186d1e869e921404504fa`.
- Dataset: `4a95615b9f46bf8aa2041cccc1ef4a5169afebbf`.

The complete paginated [dataset file-tree API](https://huggingface.co/api/datasets/cmu-gil/PromptedArtistIdentificationDataset/tree/main?recursive=true&expand=false) listed **2,803 files / 2,885,451,236,431 bytes**: 2,591 image-oriented archives, 127 text files, 72 CSVs, four `.npy` files, three model `.safetensors`, three YAMLs, and three other files. All four arrays are below; no standalone generated CLIP/CSD embeddings, embedding-chunk `.pkl` files, prediction outputs, or control-named artifacts were found in that inventory. Nested archive contents were not inspected.

| Exact array | Bytes verified in API | Expected shape, not header-verified |
|---|---:|---|
| [LAION train prototype](https://huggingface.co/datasets/cmu-gil/PromptedArtistIdentificationDataset/blob/4a95615b9f46bf8aa2041cccc1ef4a5169afebbf/dataset_laion/prototype-train_imgs-clip_vit_large-oneprocess.npy) | 409,728 | 100 × 1,024 float32 |
| [LAION test-source prototype](https://huggingface.co/datasets/cmu-gil/PromptedArtistIdentificationDataset/blob/4a95615b9f46bf8aa2041cccc1ef4a5169afebbf/dataset_laion/prototype-test_source_real_artist_imgs-clip_vit_large-oneprocess.npy) | 41,088 | 10 × 1,024 float32 |
| [JourneyDB-associated LAION train prototype](https://huggingface.co/datasets/cmu-gil/PromptedArtistIdentificationDataset/blob/4a95615b9f46bf8aa2041cccc1ef4a5169afebbf/dataset_laion_for_journeydb/prototype-train_imgs-clip_vit_large-oneprocess.npy) | 139,392 | 34 × 1,024 float32 |
| [JourneyDB-associated LAION test-source prototype](https://huggingface.co/datasets/cmu-gil/PromptedArtistIdentificationDataset/blob/4a95615b9f46bf8aa2041cccc1ef4a5169afebbf/dataset_laion_for_journeydb/prototype-test_source_real_artist_imgs-clip_vit_large-oneprocess.npy) | 389,248 | 95 × 1,024 float32 |

Total: **979,456 bytes**. Shapes are inferred from source dtype/dimension and file sizes assuming a 128-byte NumPy header; the payloads/headers were not accessible in this unauthenticated check. Do not treat inferred row counts or label order as independently validated.

The [prototype downloader](https://github.com/graceduansu/IdentifyingPromptedArtists/blob/5179627e4f458848f78186d1e869e921404504fa/scripts/download_prototypes.py) explicitly downloads only these two real-art directories. The [computation code](https://github.com/graceduansu/IdentifyingPromptedArtists/blob/5179627e4f458848f78186d1e869e921404504fa/utils/compute_prototype.py) removes CLIP's visual projection, uses float32, asserts 1,024 features for ViT-L/14, and averages artwork features by artist. These are not unit-normalized projected 768-dimensional CLIP means, nor CSD outputs. A raw mean cannot reconstruct the mean of individually normalized projected images. They are not a drop-in substitute for the current study's reference vectors and contain no generated/control observations or repeat variability.

The [evaluation instructions](https://github.com/graceduansu/IdentifyingPromptedArtists/blob/5179627e4f458848f78186d1e869e921404504fa/README_evaluation.md) tell users to run feature extraction and prediction themselves into local `RESULTS/` files before bootstrapping. The [embedding writer](https://github.com/graceduansu/IdentifyingPromptedArtists/blob/5179627e4f458848f78186d1e869e921404504fa/search/embeddings.py) would create `embeddings_*.pkl`; none were listed in the public release. The [GitHub releases endpoint](https://api.github.com/repos/graceduansu/IdentifyingPromptedArtists/releases) was empty.

## 3. Pairing metadata and access limits

The [dataset card](https://huggingface.co/datasets/cmu-gil/PromptedArtistIdentificationDataset#data-fields) documents artist labels, all artist names, source model, prompt/template ID, full prompt text, subject, and seed, with separate training, seen-artist testing, held-out query, and held-out support splits. These fields could support content/seed joins if row-level named and removed-name observations and vectors were supplied. It also mentions `prompt_type` including “style-only”; that description alone does not demonstrate a matched artist-free or generic arm.

Both code and dataset declare **CC-BY-NC-SA-4.0** ([code license](https://github.com/graceduansu/IdentifyingPromptedArtists/blob/5179627e4f458848f78186d1e869e921404504fa/LICENSE.md)). Dataset access is gated for research/noncommercial use. Unauthenticated HEAD requests for both LAION arrays, the small prompt-type map, and artist list returned **HTTP 401 / GatedRepo**. Consequently actual CSV condition values, row labels, array headers, and control membership remain unverified; access approval alone would not establish that missing generated embeddings exist.

The advertised full corpus is about 2.9 TB, and the sample is 17 GB. The separate [sample-viewer inventory](https://huggingface.co/api/datasets/cmu-gil/PromptedArtistIdentificationDataset-ViewSamples/tree/main?recursive=true&expand=false) contains image parquet shards rather than an advertised numeric-feature bundle; even its smallest shard is 75,419,824 bytes. Neither image download route meets this task's constraints. The three trained classifier/prototype-network weights are approximately 1.21 GB each and are models, not observations.

## 4. CSD does not supply the missing paired panel

| Official material | Verified metadata and relevance |
|---|---|
| [CSD repository tree](https://api.github.com/repos/learn2phoenix/CSD/git/trees/main?recursive=1), revision `3a9df32605b869eceb704897839be80977a9f1ea` | `embeddings/.gitkeep` is zero bytes; no released feature arrays were found. [GitHub releases](https://api.github.com/repos/learn2phoenix/CSD/releases) is empty. Repository license: MIT. |
| [ContraStyles](https://huggingface.co/datasets/tomg-group-umd/ContraStyles) / [schema API](https://datasets-server.huggingface.co/info?dataset=tomg-group-umd%2FContraStyles) | `train.parquet`: 103,357,623 bytes, 497,901 rows × six string columns (`key`, `url`, `caption`, `md5`, `merged_tags`, `tags`). No embedding, condition, scene, repeat, or matched-control fields. Card license: CC-BY-4.0. Payload not downloaded. |
| [CSD-ViT-L file metadata](https://huggingface.co/api/models/tomg-group-umd/CSD-ViT-L/tree/main?recursive=true&expand=false) | Card/config plus 2,438,228,893-byte model weights; no per-image outputs. Card license: CC-BY-4.0. |
| [400-artist list](https://github.com/learn2phoenix/CSD/blob/3a9df32605b869eceb704897839be80977a9f1ea/artists_400.txt) | 5,422 bytes and 400 unique names; no scene/control/repeat measurements. |

The [authors' similarity-computation guidance](https://github.com/learn2phoenix/CSD/issues/5#issuecomment-2093777153) asks users to collect real paintings and generate images before extracting/comparing features. It does not offer the proposed matched numeric panel. CSD's artwork/style corpus is useful for learning a representation, but it is not a controlled generated-image experiment.

## 5. What would make an independent audit possible

A compact author release could make this feasible without any new generation or image downloads. It would need:

1. Per-image CLIP/CSD vectors for a declared multi-artist, multi-content subset, with named and matching removed-name conditions, at least two seed/repeat observations, and explicit missingness.
2. A row manifest linking generator/version, full condition text, artist, content/template, seed/repeat, split, and image identity. A generic-art baseline would require its own actual condition; removing a name cannot be relabeled as that intervention.
3. Compatible real-art reference means or vectors, artist row maps, encoder/checkpoint and preprocessing definitions, normalization conventions, and license/access terms. Alternatively, sufficiently detailed per-scene/per-repeat Gram matrices could support a specified cross-product analysis, but summary means or classifications alone cannot.

Before seeing numerical outcomes, an external analysis should fix artist/scene selection and estimands. Its population would still be the released artists, prompts, and older generators; it would not by itself validate the present six services. Reference-only prototypes could enable a narrower reference-geometry calculation after access and coordinate checks, but would not evaluate naming response.

**Scope of negative finding:** all three pages of official Su dataset metadata were inspected (949,631 response bytes total), along with its complete GitHub tree, download/evaluation/extraction code, linked sample metadata, paper and site, and the official CSD materials above. No standalone artifact meeting the paired-feature requirements was verified. The remaining actionable dependency is release or provision of those compact observations, not a paid generation call or an unreported reanalysis of published averages.
