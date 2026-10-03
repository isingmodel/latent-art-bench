# Painter specificity v3: reference panels for two further painter groups

Version 1.0, 2026-10-02. Written before any image of the new painters was requested
and before any new generation. The four-painter study (`painter_specificity_v2`,
run `psv2-20260911`), its 649-work reference panel and its scaler are unchanged.

## Status and disclosure

This extension was added **after** the four-painter results and six rounds of
language-model review (`reports/tmlr_review_v1`), at the owner's instruction of
2026-10-02. The reviewers asked whether the shared fraction tracks how close the
painters are; one related group cannot answer that. The owner chose two further
groups from proposals based on the core reference papers:

- **Century group** (far apart, one painter per century, all known for outdoor
  scenes): Jacob van Ruisdael, Canaletto, Vincent van Gogh, Ernst Ludwig Kirchner.
- **Hudson River School** (closely related, a different tradition): Albert
  Bierstadt, Frederic Edwin Church, Thomas Cole, Asher Brown Durand.

The first proposal for the related group was four Russian landscape painters
(Shishkin, Levitan, Kuindzhi, Savrasov). A metadata-only feasibility count on
Wikidata (no pixels, recorded below) showed only 18–32 documented oil-on-canvas
works in a collection for Levitan, Kuindzhi and Savrasov, so the owner replaced
the group with the Hudson River School before any reference was acquired.

## Painters

| Group | Painter | Wikidata | Prompt name |
| --- | --- | --- | --- |
| Century | Jacob van Ruisdael | Q213612 | Jacob van Ruisdael |
| Century | Canaletto | Q182664 | Canaletto |
| Century | Vincent van Gogh | Q5582 | Vincent van Gogh |
| Century | Ernst Ludwig Kirchner | Q229272 | Ernst Ludwig Kirchner |
| Hudson River | Albert Bierstadt | Q77132 | Albert Bierstadt |
| Hudson River | Frederic Edwin Church | Q366212 | Frederic Edwin Church |
| Hudson River | Thomas Cole | Q334001 | Thomas Cole |
| Hudson River | Asher Brown Durand | Q391608 | Asher Brown Durand |

Reserves, used only under the floor rule below: Edvard Munch (Q41406) for
Kirchner; Jasper Francis Cropsey (Q1451318), then John Frederick Kensett
(Q982284), for a Hudson River painter. Reserves pass through census, metadata and
determination with the others, so a substitution needs no new census; their
images are acquired only if a substitution is triggered.

## Selection: the four-painter rules, with listed differences

The pipeline repeats `painter_feature_generation_v1` (discovery, metadata,
determination) and `painter_feature_generation_v2` (frame, renderings,
acquisition, measurement) in a new namespace.

1. **Discovery.** The same SPARQL query per creator: items with creator P170,
   instance of painting (Q3305213) and a Commons image (P18).
2. **Metadata.** Wikidata `wbgetentities` (claims, labels and descriptions, English
   with French fallback) and Commons `imageinfo` (size, MIME, SHA-1, licence
   fields), in batches of 40 at no less than 0.75 s apart.
3. **Determination.** The same seven gates in the same order; the first failure
   wins: single creator, painting, medium (oil paint **and** canvas), collection
   (P195 present), open rights, original short side at least 1024 pixels, and
   content (title lexicon). The largest qualifying file is the surrogate.
4. **Duplicates.** The same rule: records join only on the same QID or on one
   collection with one accession number.
5. **Rendering and acquisition.** The same Commons rendering request (a short side
   of at least 1536 pixels, widths in multiples of 512), the same current-rights,
   SHA-1 and size checks, the same allowed hosts, body inspection, three attempts,
   one-second spacing and content-addressed storage.
6. **Measurement.** `features.normalize(short_side=512)` and `features.extract`:
   the full view (primary) and the central 512 square (sensitivity), in the
   unchanged four-painter scaler (`pfg2-method-20260905/scaler.json`). Files that
   cannot be measured (transparency, unprofiled non-RGB colour) are recorded and
   excluded, as before.
7. **Embeddings.** CLIP ViT-L/14 and CSD at the revisions pinned by
   `painter_learned_audit_v1`, re-downloaded and hash-verified, with the same
   preprocessing, on full frames.

**Differences, and why:**

- **Content lexicon v3.** The original lexicon was written for French Impressionist
  titles (Seine, Pontoise, Sainte-Victoire). Version 3 keeps every original token
  and adds place and subject tokens for the new painters. The additions are chosen
  from the discovered titles (metadata only) before any pixel is requested, and are
  listed separately in the lexicon record.
- **No role split.** In the four-painter panel, one work in five fitted the scaler
  and one in five was held for qualification. Nothing is fitted on the new
  references (the scaler and every method are fixed), so every admitted work is a
  reference work.
- **No exposure denylist.** No work by these painters was used before.
- **Bindings without commits.** Each stage binds its inputs by SHA-256. The owner
  commits the records; stages do not require a clean Git tree.
- **User agent** `LatentArtBench/0.3 research (painter specificity v3 references)`.

## Floor and substitution

A painter needs at least **60 measured reference works** (full view). Below that:
Kirchner is replaced by Munch; a Hudson River painter by Cropsey, then Kensett. A
shortfall for van Ruisdael, Canaletto or van Gogh, or of a reserve, goes to the
owner before the generation protocol is frozen. The floor is lower than the
four-painter minimum (105, Cézanne) and is reported with each group; the
stratified reference resampling of the analysis shows its effect.

## Visual audit

As in the four-painter primary analysis, the primary reference vectors use full
frames and title-derived content classes. A visual audit of frames and crops, if
done, is a sensitivity analysis, recorded with the tool that produced it.

## Predictions recorded before generation

After measurement and before the generation protocol is frozen, the reference
record states, for each group: the reference spread H, and the faithful benchmark
N*/(N*+H) for each configuration, computed with the generic-arm outputs of
`psv2-20260911` (the new collection will have its own generic arm). These are the
predictions the new collection tests.

## Feasibility count (metadata only, 2026-10-02)

Wikidata items with an image, a single creator and a collection, by medium
statement. Non-evidentiary; the census below supersedes these numbers.

| Painter | Oil | Oil on canvas |
| --- | --- | --- |
| Jacob van Ruisdael | 436 | 256 |
| Canaletto | 374 | 338 |
| Vincent van Gogh | 859 | 810 |
| Ernst Ludwig Kirchner | 210 | 201 |
| Albert Bierstadt | 230 | 155 |
| Frederic Edwin Church | 131 | 95 |
| Thomas Cole | 125 | 100 |
| Asher Brown Durand | 172 | 170 |
| Ivan Shishkin (dropped group) | 218 | 178 |
| Isaac Levitan (dropped group) | 23 | 18 |
| Arkhip Kuindzhi (dropped group) | 47 | 32 |
| Alexei Savrasov (dropped group) | 20 | 18 |
| Alfred Sisley (four-painter panel, for scale) | 421 | 415 |

## Records

- Code: `src/latent_art_bench/painter_specificity_v3/`
- Records: `data/manifests/painter_specificity_v3/<run>/`
- Raw responses and pixels (not tracked): `research_workspace/painter_specificity_v3/<run>/`

## Amendment 1 (2026-10-03, before any image was requested)

**Floor and reserves withdrawn.** After the metadata census, a dry pass of the
seven gates with lexicon v3 (no record; metadata only) gave these works per
painter: van Ruisdael 123, Canaletto 158, van Gogh 255, Kirchner 43; Bierstadt 92,
Church 47, Cole 36, Durand 38. Three Hudson River painters, both Hudson reserves
(Cropsey 44, Kensett 50) and Kirchner fall below the 60-work floor; relaxing the
medium and size gates would not lift Durand (58) or Kirchner (49) above it. The
owner instructed: "same with other already analyzed painters". The new panels are
therefore treated exactly like the four-painter panel: the same gates, no minimum
count and no substitution. All eight painters stay. Reserves are not acquired.

Small panels make reference means noisier, and the noise inflates the reference
spread H. As for the four painters, the analysis reports stratified reference
resampling; it also reports H corrected for this noise.

**Lexicon v3 additions** were fixed from the discovered titles before this
amendment and are listed in `content_lexicon.json` of the run.

## Amendment 2 (2026-10-03, during image acquisition)

**Thumbnail sizes.** Commons now serves only standard thumbnail widths, so the
`imageinfo` request rounded the four-painter rule's widths (a 1,536-pixel short
side in multiples of 512) up to 1,280, 1,920 or 3,840 pixels, or returned the
original when it was smaller. Every image is still resized to a 512-pixel short
side for measurement.

**User agent.** After 38 images, the upload server answered HTTP 429 roughly every
twenty requests and asked for a ten-minute wait. The stage was stopped between
requests and resumed from its event ledger. The user agent now carries the project
URL, as the four-painter pipeline's did and as Wikimedia's robot policy asks. Only
`USER_AGENT` changed in `references.py` (SHA-256 `c2193db55f9d…` before,
`892e1b6d1884…` after); the census, metadata, determination, frame and rendering
receipts bind the earlier version.
