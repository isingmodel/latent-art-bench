# Reference candidate acquisition and content eligibility — 2026-09-06

This prospective Stage B contract selects reference candidates before downloading
their pixels and forbids extracting any of the 31 fidelity features at this stage.
The final panel, prompts, content weights and analysis must be frozen under Stage D
before measurement. The purpose is a fresh reference comparison with explicit
content coding, while preserving the earlier exposed-reference results.

## Feasibility and adaptation

The earlier 1,193-work frame and exposure denylist cover more than the 649 originals
in the latest analysis. Qualification and development records are also exposed.
Reusing a different role from that frame would not create an unmeasured reference.
The preserved broader Wikidata/Commons metadata contains additional oil-on-canvas
works that were not in that frame, often because the old 1,024-pixel cutoff or
place-name-based title coding excluded them. Their metadata has already been seen;
they are not described as wholly unseen works or a complete painter oeuvre.

Use the fixed original-media minimum of **512 native pixels on the short side**,
so primary 512 normalization never upsamples. This prospectively relaxes the old
1,024 requirement; the new analysis must include the ≥1,024-native subset as a
resolution sensitivity. Preserve the older reference results rather than replacing
their source frame. Do not count additional digital files as additional works.

The metadata screen found 134 Monet and 48 Cézanne candidates after the explicit
work-identity rules below. These are candidates, not pixel-validated admissions.
Acquire the first 64 Monet candidates in the fixed hash order and all 48 Cézanne
candidates. No more than 128 candidate files are authorized by this contract; the
actual immutable manifest determines the count. The umbrella limit of 208 new
artwork files still applies to all stages combined. Retain the initial 48-work-per-
painter target if it is feasible after technical/content checks; if fewer remain,
use all eligible works and report the unequal counts. No outcome-based top-up.

The initial 12 equally filled content strata are not established by this audit.
Do not force them by inventing content labels. The final contract will use the
supported visual content classes and a declared mixture, with 24 briefs per painter
if supported. A main-study uncertainty qualification must use the actual panel.

## Exact candidate screen and identity

Inputs are the preserved broad-media R2 candidate manifest, the 1,193-work v2 frame
and the historical exposure denylist. `references.py` is the executable screen:

1. Sole recorded creator is Monet or Cézanne; painting, oil paint and canvas claims
   must be present, with a collection identity. Require an accession or a specific
   Cézanne catalogue entry URL containing its numeric work ID. The latter allows
   a stable work identifier when museum accession metadata is absent. This is
   recorded Wikidata attribution/identity evidence, not a fresh independent museum
   authentication; linked catalogue pages were not all independently inspected.
2. The media record has an open-rights marker, supported raster MIME type, original
   native short side ≥512, original URL, filename and expected SHA-1. Preserve the
   exact license marker and source record hash. Rights metadata is a dated source
   assertion; it does not identify the original photographic workflow.
3. An accent-insensitive title screen requires an explicit outdoor/object noun and
   excludes obvious portraits, still lifes and figure-led subjects. Geographic names
   alone do not assign content. The explicit exception `Q3821663`, *The Hanged Man's
   House*, refers to a building despite the word “man.” The literal screen is fixed
   in code before acquisition; it locates candidates and is not final visual coding.
4. Exclude any match to the earlier frame/denylist on QID, collection/accession,
   work URL, Commons filename or image SHA-1 where recorded. Preserve work-ID query
   parameters and fragments in URLs; discard only `utm_*` tracking parameters.
   Title equality alone is never a physical-work identity rule. Repeated discoveries
   are collapsed using the same identity keys in stable QID/filename order.
5. Within painter, sort remaining candidates by SHA-256 of canonical JSON
   `["pdsv1-reference-candidates-20260906", item_qid]`; select at most 64. Publish
   every screening disposition and the exact candidate identities before acquisition.

This conservative screen also excludes denylist entries whose earlier exposure was
metadata-only. Absence from recorded identity indexes is not proof that nobody has
ever seen a work. The claim is a new numeric-reference panel under the recorded
project history, with residual identity limitations reported.

## Acquisition

Commit the implementation, tests, contract and source inputs. Prepare a create-once
freeze with the exact candidate and screening hashes; commit it and both manifests
before the first image GET. Use the frozen HTTPS original URLs on
`upload.wikimedia.org/wikipedia/commons/`, one request per selected work, serially
with two seconds between requests, 90-second timeout and 64 MiB response bound.
Retain at least 5 GiB plus that bound free before each request.

Fsync an attempt event before each GET and retain all received bytes under the new
ignored workspace, including error bodies and partial responses. No redirects,
automatic retry, alternate source, replacement or best-image selection. A terminal
response is recorded once. A crash with an unresolved intent prevents automatic
redispatch. The complete finite request inventory is the stopping rule; do not stop
when a favorable count is reached. Closed stages remain terminal permanently.

Successful admission to visual review requires HTTP 200, complete response,
matching expected image SHA-1, decodable supported raster and native short side
≥512. Record SHA-256, dimensions and format. A hash mismatch remains a failure;
do not refresh the expected hash. Do not normalize or extract fidelity features.

## Visual coding, before main analysis freeze

The maintainer LLM may inspect decodable candidates to code content eligibility.
This is one maintainer's annotation, not an independent human or expert review.
Ignore whether an image looks particularly characteristic, appealing or variable.
No distance, feature spread, model output or pilot image informs admission.

Admit outdoor-place paintings: landscape, waterscape, garden/park or exterior built
scene is the principal subject. Incidental small people are allowed; portraits,
figure-led/narrative scenes, still-life subjects and interior rooms are excluded.
Exclude an unresolved wrong-work identity or a photograph primarily of a frame,
wall or installation. Do not crop away frames or alter the source to rescue an
otherwise ineligible candidate. Preserve every decision and its short reason.

Code three broad classes from the visible organization, not the title:

- **water:** a substantial river, pond, coast or other water surface organizes the
  composition. A place name or tiny distant water patch is insufficient.
- **built:** architecture, streets or a built route organize the scene, when water
  is not the organizing surface. A small distant house alone is insufficient.
- **land:** vegetation, open ground, hills, mountains or exposed rock organize the
  scene, with neither water nor architecture organizing it.

Also record subject subcategory, near/mid/distant emphasis, open/enclosed setting,
and a plain content description. Mixed/uncertain cases retain that flag and reason;
they must not silently receive a confident label. Coding does not inspect feature
values. Final target weights, inclusion of ambiguous cases, 24 detailed briefs and
selection of at most 48 eligible works in the same hash order require a separate
main-study contract before feature extraction or research generation.

## Capture limitation

The bounded AIC, Met and NGA metadata audit has not established 12 independent
photographic capture pairs per painter. An alternate digital asset, its creation
timestamp or a second host does not prove an independent photograph. Consequently,
this stage makes no capture-equivalence claim. Any later official-source versus
Commons pair must be labeled a **same-work surrogate comparison** unless genuine
capture-event provenance is available. Controlled resizing/JPEG sensitivities can
test processing robustness, but cannot substitute for independent capture evidence.
