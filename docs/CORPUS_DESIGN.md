# Corpus Design and Data Governance

## 1. Corpus architecture

LatentArtBench uses four linked corpora rather than one undifferentiated image collection.

| Corpus | Primary role | Core unit |
|---|---|---|
| Reproduction calibration corpus | Estimate digitization and preprocessing noise | Multiple files representing one physical work |
| Discovery corpus | Fit and validate the reference atlas | Western canonical real works |
| External challenge corpus | Test geographic, canon, and exposure generalization | Non-Western and long-tail real works |
| Generated corpus | Evaluate model and conditioning effects | Generated outputs nested within model and target |

All corpora share canonical identifiers and metadata conventions, but each source method operates on a paper-appropriate view.

## 2. Digital surrogates, not originals

Most computational art-history datasets contain digital surrogates of physical artworks. Differences can arise from photography, scanning, illumination, white balance, restoration state, cropping, framing, resampling, color profiles, compression, and website processing. Generated images are born digital and often lack these acquisition artifacts.

The benchmark therefore does not call a web image an “original.” It distinguishes:

- the physical work;
- a canonical intellectual identity for that work;
- one or more digital reproductions;
- derived standardized analysis views.

## 3. Reproduction calibration corpus

The calibration corpus should prioritize works for which at least two independently produced digital reproductions can be obtained, for example from a museum collection, a scholarly archive, and a general art platform.

Its purposes are to:

- estimate same-work reproduction distances in every feature family;
- identify features dominated by source-specific color or compression effects;
- test border, mat, and photographic-background removal;
- quantify the lower bound on interpretable real-versus-generated differences.

The calibration corpus should span different periods, palettes, surface organizations, aspect ratios, and image sources. It is not intended to estimate art-historical group distributions.

## 4. Discovery corpus

The initial discovery corpus focuses on Western canonical painting because the source studies and their metadata systems are predominantly grounded in that canon, and because sufficiently large artist-level samples are more readily available.

Selection should preserve a hierarchy:

\[
\text{era} \supset \text{movement} \supset \text{artist} \supset \text{work} \supset \text{digital reproduction}.
\]

Inclusion should be based on documented eligibility, image quality, metadata confidence, and the minimum number of independent works needed for held-out validation. An artist may be eligible for movement-level analysis while remaining ineligible for artist-level distribution estimation.

The discovery corpus is not presented as a universal history of art. It is a measurement-development set whose historical and geographic limitations must remain visible in every release.

## 5. External challenge corpus

The challenge corpus is held apart from discovery-stage evaluator fitting. It includes:

- non-Western artists, schools, and visual traditions;
- geographically underrepresented artists;
- long-tail artists with limited online representation;
- groups whose labels do not map cleanly onto Western movement taxonomies;
- optionally, contemporary digital and user-generated visual art.

The challenge stage evaluates both the generator and the benchmark representation. Poor performance may reveal inadequate model knowledge, inadequate reference data, inappropriate labels, or an observable that does not transfer beyond its original corpus.

## 6. Paper-specific views

The master metadata layer yields multiple eligible subsets:

| Method family | Primary corpus view |
|---|---|
| Large-scale color and brightness statistics | Broad painting corpus following the source inclusion rules |
| Seamlessness and chromatic-distance heterogeneity | Broad painting corpus with valid color reproduction |
| Color-interaction partitioning | Exact source examples for replication, then a documented extension set |
| Information-theoretic composition | Landscape paintings; abstract works may serve as an auxiliary comparison |
| Complexity-entropy analysis | Broad historical paintings and a contemporary user-generated-art view |
| Formal/contextual latent representations | Works with sufficiently reliable artist, period, and style labels |

Features are not forced onto images outside the domain in which their interpretation has been validated.

## 7. Metadata schema

The public metadata design should include, where available:

| Field | Description |
|---|---|
| `canonical_work_id` | Stable identity joining alternative reproductions |
| `reproduction_id` | Identifier for one digital file or source rendering |
| `artist_id` | Authority-linked artist identity |
| `artist_name` | Display name with controlled aliases stored separately |
| `title` | Source title plus normalized title if needed |
| `creation_date_start` / `creation_date_end` | Date interval rather than false precision |
| `era_id` | Project-controlled era label and provenance |
| `movement_id` | Source and harmonized style labels retained separately |
| `genre` | Source genre and paper-specific eligibility labels |
| `medium` | Physical medium when documented |
| `dimensions` | Physical dimensions when documented |
| `holding_institution` | Museum or collection authority |
| `source_url` | Landing page for the digital reproduction |
| `source_name` | Museum, archive, or platform |
| `license` | Rights statement for the digital asset |
| `accessed_at` | Acquisition date |
| `pixel_width` / `pixel_height` | Native file dimensions |
| `color_profile` | Embedded or inferred profile |
| `file_hash` | Integrity and exact-duplicate detection |
| `perceptual_hash` | Near-duplicate screening aid |
| `border_status` | Presence and treatment of frame or background |
| `split` | Train, validation, test, calibration, or challenge |
| `eligibility_flags` | Feature-module inclusion flags with reasons |

Labels inherited from source websites must retain provenance. A harmonized label must never silently overwrite the original label.

## 8. Deduplication and split policy

Splitting occurs at the canonical-work level, not the file level. All reproductions of the same physical work must remain in the same inferential partition except within the dedicated calibration design.

Near-duplicate detection should combine metadata, file hashes, perceptual hashes, local feature matches, and manual adjudication for ambiguous high-impact cases. Crops, color-shifted copies, and framed versions should not be allowed to leak across training and evaluation splits.

Any learned evaluator or dimensionality reduction is fitted on the real training split only. Held-out real works and all generated outputs remain unseen until the evaluator is frozen.

## 9. Exposure and canon variables

Exact training exposure is generally unobservable for closed models. The project may use preregistered proxies such as:

- frequency of artist and work names in publicly inspectable training indexes;
- number of accessible online reproductions;
- representation across major art platforms;
- encyclopedia and search-frequency measures;
- known inclusion in documented model-training sources.

These variables must be called exposure proxies, not ground-truth training counts. Fame, availability, canon status, and training exposure are correlated but conceptually distinct.

## 10. Image standardization and derived views

The project preserves native files where rights and storage rules permit, then creates versioned derived views. Standard operations include:

- decoding and conversion to a documented sRGB workflow;
- alpha handling;
- border and photographic-background treatment;
- aspect-preserving downsampling for the harmonized track;
- paper-specific resizing or quantization for replication;
- lossless storage of standardized derived views when permitted.

Primary harmonized comparisons use only downsampling to a common supported size. Upsampling is reserved for negative controls or model-required preprocessing and must be labeled.

## 11. Rights and public release

The public repository will not assume that an artwork in the public domain implies unrestricted rights in every digital reproduction. Releases should prioritize:

- source landing-page URLs;
- rights statements and license metadata;
- canonical IDs and hashes;
- acquisition scripts where permitted;
- non-reconstructive derived features;
- split manifests and provenance records.

Image files should be redistributed only when the digital asset license explicitly permits it. Terms of service, robots policies, attribution requirements, and jurisdiction-specific database rights must be reviewed before acquisition or release.

## 12. Versioning

Every corpus release should record:

- a semantic version;
- source access dates;
- acquisition and filtering code versions;
- additions, removals, and metadata corrections;
- split changes;
- known unresolved duplicates;
- rights-status changes;
- feature-module eligibility changes.

Benchmark papers must cite a fixed corpus release rather than a mutable web collection.
