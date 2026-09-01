# Pilot 3 R2: Official Met `primaryImage` protocol

## Status and scope

This is a prospective replacement for only the closed Freeze-A1 Met digital-asset
path. It does not reopen, amend, retry, or reinterpret that path. The Wikimedia
Commons request, terminal, and raw payload recorded by
`met_asset_provider_incident.json` remain quarantined evidence and can never satisfy an
R2 gate.

R2 preserves the twenty previously frozen physical works: exact Met object ID,
accession, artist authority ID, artist, and development partition. It assigns the
digital reproduction of each work a new `met-r2-primaryimage-{objectID}` asset ID in
the `pilot3-met-r2-official-primaryimage` namespace. There are no reserves or
replacements.

The implementation is isolated in `src/latent_art_bench/pilot3/met_r2.py`.

## Prospective order of operations

1. Commit this protocol document and its isolated implementation. Build
   `met_r2_authorization.json` offline with `build_offline_authorization` or
   `write_offline_authorization`. This verifies the exact self-hashed provider incident
   and exact hash-pinned real split and records hashes of both protocol implementation
   files. It does not open metadata or image URLs.
2. Review and commit the authorization. Metadata capture rejects an untracked, dirty,
   or implementation-stale closure before invoking its injected requester.
3. Call `capture_official_metadata` with a requester that performs a single GET with
   redirects disabled. Exactly one fixed endpoint is allowed per object:
   `https://collectionapi.metmuseum.org/public/collection/v1/objects/{objectID}`.
   A self-hashed start is appended and fsynced before every requester invocation. The
   exact response bytes are written to an R2-only content-addressed store before the
   terminal is appended.
4. Call `freeze_metadata_targets`. It succeeds only when all twenty terminals are
   eligible and deterministically writes the target JSONL plus a self-hashed metadata
   freeze. Review and commit the compact authorization, metadata journal, target
   manifest, and freeze. Raw metadata CAS is ignored by Git but is hash-bound by the
   committed artifacts and revalidated locally before the image gate opens.
5. Build and commit the exact-member normalization-scope authorization. It binds all
   twenty frozen R2 asset IDs and URLs and authorizes normalization only; it opens no
   network or feature gate. Image acquisition refuses to run without it.
6. Call `acquire_official_images` with a requester that performs a single GET with
   redirects disabled. It verifies the whole committed-and-clean metadata closure
   before the first invocation. The only URL for a target is the exact committed
   `primary_image_url` on `images.metmuseum.org`.
7. R2 observes dimensions from that first image response. It never requests another
   derivative based on geometry. Only a decoded JPEG satisfying the unchanged Kim
   predicates is eligible: width greater than 410, height greater than 410,
   long-to-short aspect ratio below 2, and area greater than `410 * 410`.
8. Individual success terminals are evidence, not admissions. The compact acquisition
   manifest is materialized atomically only after all twenty fixed assets pass. A
   failure leaves no partially eligible cohort.

The authorization and metadata freeze are deterministic and contain no live wall-clock
field. Git commits provide the prospective chronology. Metadata and image execution each
hold a nonblocking process lock across verification, durable start, and transport, so two
local runners cannot duplicate a one-shot request.

## Fixed selection policy

The provider-wide selection field is `primaryImage`. `primaryImageSmall` and
`additionalImages` may occur in the official API response but are never read as image
candidates or copied into the target manifest. Search endpoints, Wikimedia Commons,
cross-provider redirects, alternate derivatives, fallbacks, work substitution, and
post-response URL choice are forbidden.

Identity eligibility requires the exact object ID, exact accession, and exact Met
artist constituent ID from the frozen physical-work binding. `artistDisplayName` must
be present, but the authority ID is the exact identity check because display spelling
can differ from the study's canonical artist spelling. `isPublicDomain` must be the
JSON boolean `true` and `primaryImage` must be a nonempty HTTPS URL whose host is
exactly `images.metmuseum.org`.

All twenty `primaryImage` URLs must be distinct. After transport, all twenty raw JPEG
hashes must also be distinct; any duplicate mapping or repeated payload closes the whole
cohort before an acquisition manifest can exist.

## Failure and recovery semantics

There is one scheduled metadata request and one scheduled image request per fixed
asset. Starts and terminals form separately self-hashed, append-only chains. A dangling
start is not replayed because the process cannot prove whether a response was observed.
A terminal transport or protocol failure closes the R2 cohort. No code path retries by
switching fields, derivatives, hosts, providers, or works.

A completed success prefix can be verified and resumed at the next untouched target.
Re-running a fully completed cohort performs verification only and does not invoke the
requester again. Every compact journal lives directly under `artifacts/pilot_3/` so it
can be committed; large metadata and image response bytes remain in the ignored
`artifacts/pilot_3/met_r2/` CAS.

## Test boundary

`tests/pilot3/test_met_r2.py` uses only injected in-memory responses. It checks the
incident binding, exact cohort, durable pre-request starts, deterministic self-hashes,
identity and public-domain failures, lack of fallback from an empty `primaryImage`,
search/redirect rejection, the pre-image commit gate, JPEG and Kim predicates,
cross-provider rejection, all-twenty atomic admission, and verification-only reruns.
The test suite performs no network access.
