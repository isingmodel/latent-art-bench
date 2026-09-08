# Independent-capture feasibility: four retained works

Metadata-only check performed on 2026-09-08 by a maintainer-run LLM agent.
**No independently documented capture pair was verified in this bounded check.**
Two individual photographs have useful camera/author metadata, but neither has a
verified independent counterpart. This does not establish that no suitable pair
exists elsewhere among the 70 retained works.

## Scope and decision rule

The work identities were selected only from the existing
`data/manifests/painter_distribution_study_v1/pdsv1-main-20260906/reference_panel.jsonl`.
Titles, accession numbers, Commons description pages and authority links came from
the existing R2 delivery inventory. Four works with plausible museum/visitor-photo
routes were checked using primary museum pages and Commons metadata/file histories.
No artwork image bytes were downloaded, opened, rendered or measured. No broader
painting frame was collected, and no existing evidence was changed.

A second website, upload date, resolution, crop or encoding is insufficient.
A qualifying pair needs evidence of distinct photographic/scan events for the same
physical work, with identities and image ancestry checked. Capture dates must be
distinguished from artwork dates, uploads and later editing timestamps. Metadata
claims remain claims; the inspected pages do not independently validate their EXIF.

## 1. Monet, Ice Floes at Twilight — `wikidata:Q67609602`

Accession 154 / 154/GZ, Museum Langmatt. The retained
[Commons description](https://commons.wikimedia.org/wiki/File:La_D%C3%A9b%C3%A2cle_de_la_Seine_-_Claude_Monet_-_Museum_Langmatt-8639_(without_frame).jpg)
credits Raimond Spekking and records a Canon EOS 5D Mark IV capture on
26 April 2025 at 14:53. Its 3 May 2025 file-history entry explicitly describes a
crop of the corresponding framed photograph. That source and the crop are one
capture, not a pair. The page's EXIF usage text names Spekking and CC BY-SA 4.0;
the reproduction also carries public-domain-art tags. Those displayed notices do
not replace a future rights/attribution check.

The [official museum object page](https://www.langmatt.ch/en/collection/claude-monet-ice-floes-at-twilight-1893)
confirms title, 1893, medium and dimensions, but the accessible page and its HTML
metadata provide no second capture author/date. The page's author meta field is
Museum Langmatt, which identifies the page publisher rather than a photographer.

**Decision: unresolved pair.** One retained capture is documented; the museum
image cannot be assumed independent merely because it has another delivery URL.

## 2. Monet, The Cabin at Sainte-Adresse — `wikidata:Q50700359`

Accession 1990-0045, Musée d'Art et d'Histoire de Genève. The retained
[museum-derived Commons file](https://commons.wikimedia.org/wiki/File:La_Cabane_de_Sainte-Adresse_(1867)_Claude_Monet_-_Mus%C3%A9e_d%27Art_et_d%27Histoire_de_Gen%C3%A8ve_(W_94).jpg)
explicitly cites the [MAH object page](https://www.mahmah.ch/collection/oeuvres/la-cabane-de-sainte-adresse/1990-0045)
as its source. Its displayed file history has one upload, 2 February 2024 by
Shooting4truth. No capture author/date is supplied. The displayed JPEG comment
records gd-jpeg/IJG encoding at quality 85; that is processing information.
The page carries public-domain-art reproduction notices.

A linked [visitor photograph](https://commons.wikimedia.org/wiki/File:Claude_monet,_la_cabene_de_saint-adresse,_1867.JPG)
identifies the same work/accession, own work by Sailko, and a capture on
20 May 2014 at 10:58:25. EXIF identifies a Canon PowerShot G12, ISO 800 and
1/30-second exposure. The page specifies CC BY 3.0. Its 2016 crop and subsequent
reversion are derivative/version history, not independent captures.

**Decision: promising but unresolved pair.** The museum-derived upload is later
than the visitor capture, so chronology does not rule out shared ancestry. It
does not document a distinct museum photographer, capture date, negative or plate
identifier. The official MAH page was not text-readable through the inspected
browser result; no undocumented museum provenance is inferred. A museum attestation
of its master image's origin would be useful before authorizing a paired probe.

## 3. Monet, Weeping Willow — `wikidata:Q105099583`

Accession 5078, Musée Marmottan Monet. The retained
[Commons description](https://commons.wikimedia.org/wiki/File:Weeping_Willow_by_Claude_Monet,_Mus%C3%A9e_Marmottan_Monet_5078.JPG)
lists an own-work source, but its photograph subsection uses the painting's
1918–1919 date and names Claude Monet as author. Its upload history names Wmpearl
on 14 July 2019. These fields do not establish a camera event or a second capture.
The [museum notice](https://www.marmottan.fr/notice/5078/) was inaccessible through
the inspected browser result.

**Decision: unresolved.** Artwork dates and upload dates must not become invented
capture dates; a displayed own-work label alone is insufficient for a pair.

## 4. Cézanne, A Copse — `wikidata:Q64366377`

Accession 4845.1, Honolulu Museum of Art. The retained
[Commons description and history](https://commons.wikimedia.org/wiki/File:Paul_C%C3%A9zanne_-_%27Un_Clos%27_(%27A_Close%27),_c._1890.JPG)
currently lists own work. Its earlier 25 March 2009 upload entry cites Honolulu
Academy of Arts; the larger current file was uploaded on 25 March 2016. Both
entries name uploader Hiart. No distinct capture author/date or documented
independent scan event was established. The [recorded museum object route](https://honolulumuseum.org/collections/35087/)
and [alternate recorded route](https://www.honolulumuseum.org/art/5382) were not
accessible in the inspected browser results.

**Decision: unresolved.** Changing file size, upload date and source-description
text does not establish a new capture. This work remains useful to investigate
because its omission changes the existing OAuth Cézanne energy-contrast direction;
that influence does not validate any candidate image replacement.

## Consequence for the successor

Keep independent capture validation pending. The Cabin and Ice Floes cases offer
specific provenance questions, rather than a general request for more images.
No image acquisition or paired feature comparison is authorized by these notes.
A successor capture probe would need exact master/version identities, provenance,
rights and processing rules fixed before accessing additional image bytes.
Neither a new crop nor a museum-hosted copy should satisfy that gate by itself.
