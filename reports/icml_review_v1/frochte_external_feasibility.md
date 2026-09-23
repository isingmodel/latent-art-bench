# Frochte external-data feasibility

Date checked: 2026-09-19. This is an access/design feasibility check, not a new review or a change to any round-03 score. The completed contribution review remains unchanged.

## Decision

**No usable independent-data path was verified within the authorized scope.** The Frochte paper describes retained numerical arrays, but I found no study-specific public code repository, embedding download, row manifest, or data-license declaration in the primary paper or the author's publication entry. Consequently, exact archive sizes, schemas, checksums and access permissions cannot be verified. This is a bounded negative finding, not a claim that the author has no files or that no unlinked release exists.

The limitation is access and observation design, not the nominal space needed for a small embedding matrix. Published aggregate accuracy counts cannot reconstruct embeddings, held-subject folds, shared components, or the decisions made after a new mean translation.

## Access investigation

The checked version is [arXiv:2605.09030v2](https://arxiv.org/abs/2605.09030v2), revised July 5, 2026.

- The [primary HTML](https://arxiv.org/html/2605.09030v2) returned HTTP 200; the directly inspected body was **576,847 bytes**, SHA-256 `85249b1037a4983ccc01dfbaa4cc5768c5a6f893b630f49ef68e39a2ffad5a15`. Parsing its complete hyperlink list found only two scientific GitHub destinations: the third-party FLUX inference repository and PainterPalette. The other GitHub links belong to arXiv/LaTeXML tooling. No study-specific GitHub, Hugging Face, Zenodo, Figshare or OSF link was present.
- The [author's publication page](https://joerg.frochte.de/publications.html) returned HTTP 200; **146,890 bytes**, SHA-256 `616561e91a492ff5ee333e8b8b1c8e39cea8a64e1c7ce80510775dc8701e1c74`. The matching publication entry supplies the arXiv link and bibliographic record, without a code/data link.
- Two narrowly targeted searches used the exact arXiv identifier/title and author plus CSD. They did not identify a primary study release. The public [GitHub repository search for `2605.09030`](https://api.github.com/search/repositories?q=2605.09030) returned HTTP 200 and `total_count: 0` (55-byte JSON). This is not an exhaustive search of unindexed or differently named repositories.
- The arXiv page's generic “Code, Data, Media” toggles are discovery widgets, not verified artifact downloads. A third-party “reproduce paper” launcher is also not the author's retained dataset; it was not run.

## What the described observations would support

The following design facts come from [Sections 3 and 8 and Appendices E-F](https://arxiv.org/html/2605.09030v2). No corresponding raw payload was available for inspection.

| Cohort | Labels, pairing and repeats described | Fit to the requested test |
|---|---|---|
| Historical anchors | 1,799 artworks, 91 artist labels; 768-dimensional embeddings; attribution/license side arrays | Real-art labels, not prompt-name outcomes; cannot supply a naming intervention |
| Bare FLUX.1-dev | 15 artists, 22 neutral subjects, three seeds; `<subject>, art by <artist>` | Potential held-subject prompt-name observations, if complete vectors and subject/seed keys become accessible; no artist-free/generic-oil arms described |
| LoRA stress test | Eight artists; artist-specific adapters and anchor-derived captions; listed sample counts sum to 471 | Adapter/content changes confound a name-only intervention; no verified common-scene repeat manifest |
| Caption pretest | Two artists; 30 outputs per artist under full/stripped templates | Template comparison, not a generic-oil or artist-free naming control |

The bare-cohort text implies 990 outputs, but Table 19 displays 14 artist rows; Kyōsai appears separately in Table 20. A manifest is needed to resolve membership. Published tables contain counts, not query vectors or per-query decisions. Bare results use CSD positional interpolation at 336 pixels, unlike the manuscript's native 224-pixel CSD pipeline.

### Consequences for this manuscript

1. **Common/labeled gain relative to free or generic painting:** unavailable. Authentic-art embeddings alone lack the generated intervention arms. The bare-prompt cohort, even if released, has no documented matching baseline arm, so it cannot estimate the manuscript's named-minus-generic/free component fractions. A new baseline generation would exceed this task's authorized route.
2. **Repeat-corrected centered agreement:** potentially calculable from a complete crossed bare-prompt matrix with reference vectors, but seed numbers and source/encoder provenance would need verification. Reported top-1 counts do not suffice. The different CSD preprocessing must remain explicit rather than silently pooling results with the manuscript.
3. **Fixed-rule prompt-name recognition:** the bare cohort is the only described candidate with appropriate prompt-name labels and repeated subjects. Raw vectors, complete artist/subject/seed keys, and compatible reference embeddings would permit a separately predeclared held-subject evaluation. Existing published aggregate outcomes mean this would be an external-data analysis of an independently collected cohort, not a prospectively collected replication. None was performed here.
4. **LoRA and authentic-art classification:** substituting adapter identity or historical authorship for a name-only prompt label would change the question. These cohorts cannot be represented as a direct replication of the paper's controlled naming design.

## Actual linked resources: exact sizes and licenses

All sizes below are GitHub tree/blob byte sizes, not estimates. Only small metadata/source files and one CSV header were read; the data files were not downloaded.

### PainterPalette

[Repository](https://github.com/me9hanics/PainterPalette), inspected tree/commit `a1132c99c81a8460893479955bd4f020a600fa04`; recursive tree response was complete (`truncated: false`).

| File | Exact bytes | Inspection |
|---|---:|---|
| `README.md` | 29,268 | Read; describes one row per painter and biographical/style/relation attributes |
| `LICENSE` | 1,079 | Read; MIT project license, Hanics Mihály Péter |
| `NOTICE` | 278 | Read; project attribution |
| `PainterPalette.csv` | 2,736,640 | Header only; HTTP 206, `Content-Range: bytes 0-8191/2736640`; 385-byte first line read |
| `PainterPalette.xlsx` | 1,156,538 | Tree metadata only |
| `PainterPalette.sql` | 8,199,581 | Tree metadata only |

[Immutable README](https://github.com/me9hanics/PainterPalette/blob/a1132c99c81a8460893479955bd4f020a600fa04/README.md) and [license](https://github.com/me9hanics/PainterPalette/blob/a1132c99c81a8460893479955bd4f020a600fa04/LICENSE). The CSV header names artist, nationality, movement/styles, dates, locations and relationships. It contains no image embeddings, generation prompts, conditions, seed/repeat identifiers or generated-query labels. It can enrich artist metadata, but adds no appropriate generated observations for this test. Its MIT declaration is not a license for Frochte's separate unpublished arrays.

### FLUX

[Repository](https://github.com/black-forest-labs/flux), inspected complete tree `802fb4713906133fcbd0d8dc5351620ca4773036`. It identifies itself as the official FLUX.1 inference repository. Metadata lists `README.md` **6,722 bytes**, Apache-2.0 `LICENSE` **11,357 bytes**, and `model_licenses/LICENSE-FLUX1-dev` **18,621 bytes**. The model license is separate from the code license. No Frochte embedding or generation manifest appears in the inspected tree. No weights, generation code, dependencies or license acceptance flow were executed.

## Unknown archive sizes and license boundary

No URL for a Frochte NPZ or generated manifest was found, so its **actual compressed bytes, checksum, schema, sample identities and data license remain unknown**. The paper's arXiv non-exclusive distribution license does not establish a separate data-release license. The mention of captured source-license arrays is not a downloadable license inventory.

For capacity planning only, an uncompressed `float32` matrix with 1,799 rows and 768 columns would require **5,526,528 bytes**; the claimed 990 bare generations would require **3,041,280 bytes** per representation. These are arithmetic matrix sizes, not observed download sizes, and exclude labels, provenance and archive overhead. They suggest that compact vectors could fit the stated disk constraint if a proper release later becomes available; they do not establish access.

## Resource use and stopping point

- No new generation expenditure, image/checkpoint download, dependency installation, gated-terms acceptance, author contact, or external-volume use.
- Requests were restricted to primary HTML, author-publication metadata, exact-identifier discovery, linked repository metadata, small text files, and a bounded CSV header request.
- Directly fetched metadata/text bodies totaled under 1 MiB, excluding tool-managed web-search traffic. No scientific payload was retained or analyzed. This report is the only new persistent deliverable for the feasibility task.
- No new significance claim, retrospective score change, or credit for prospective work is warranted from this access check.

**Actionable conclusion:** stop this source path at present. Proceed only if an actual public, appropriately licensed compact release later supplies compatible reference/query vectors and the required prompt/subject/seed/condition manifest. No such artifact has been verified here.
