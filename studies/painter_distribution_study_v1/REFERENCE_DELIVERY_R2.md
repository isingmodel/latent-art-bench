# Reference delivery successor R2 — 2026-09-06

This is a prospective delivery amendment for the same candidate paintings. The
original acquisition `pdsv1-reference-candidates-20260906` is permanently terminal:
97 attempts, five acquired originals, 92 HTTP 429 responses and 15 unattempted
candidates. The operator stopped its process between completed requests after
observing repeated rate limits. This overrides its full-inventory stopping rule
to respect the provider. Every attempt has a terminal response; no ledger or
expected hash was changed. The first collector lacked a stop-on-429 guard and
continued too long before operator intervention. Preserve that implementation as
the record of what ran; this successor fixes the operational policy prospectively.

Wikimedia's response specifically asks for a less disruptive approach or standard
thumbnail sizes. Its [current documentation](https://www.mediawiki.org/wiki/Common_thumbnail_sizes/en)
lists standard widths, explains restrictions on direct nonstandard requests, and
recommends the imageinfo API. Follow that supported delivery method after at least
ten minutes from the predecessor's last response. Do not change client identity,
credentials or network origin to bypass a rate limit.

The completed metadata census contains four fresh imageinfo responses for 71 of
the original 112 candidates, requested at supported widths of 960, 1280 or 1920.
Every returned parent SHA-1 agrees with the preserved original image identity.
Choose the largest supported width no larger than native width or 1920, requiring
a resulting short side of at least 512. For four JPEGs where imageinfo returns an
unscaled original at native width, use the next smaller supported width. Construct
that standard thumbnail URL from the verified parent's Commons hash-directory and
filename and the currently observed `thumb.wikimedia.org` delivery host. Preserve
whether the URL was returned or derived. No source image identity is replaced.

The immutable successor delivery manifest contains **38 Monet and 33 Cézanne**
works. The other 41 candidates cannot meet both the supported-thumbnail and
nonupsampling 512-pixel requirements and remain explicit delivery omissions.
This revises the 48-per-painter feasibility target before new feature measurement;
the final study uses the eligible available panel with its exact counts, not a
pretended 48-work panel. Original acquisition outcomes did not select these 71:
the rule uses only pre-acquisition native dimensions and current metadata. The
five already downloaded originals remain preserved and outside this derivative
panel unless they also have a qualifying standard thumbnail. Multiple surrogates
still count as one physical work.

Commit this contract, implementation/tests, the predecessor's terminal receipt
and the metadata terminal evidence before preparing the successor freeze. Commit
that freeze and the exact delivery/omission manifests before any image GET. The
successor binds every predecessor record it consumes and all four raw metadata
responses. Its run ID and all runtime/ledger paths are disjoint.

Exactly one GET per eligible derivative, at most 71 new artwork files. Along with
the five acquired originals this is at most 76 new artwork files, within the
umbrella 208-file limit. One serial writer, ten seconds between requests, a
90-second timeout, 16 MiB response bound and 5 GiB free-space reserve apply. No
redirects or automatic retries. Store selected response headers including
Retry-After; fsync intents before transport and retain every complete or partial
body. Stop and close the whole run on the first 403, 429, 503 or incomplete response,
recording the unattempted suffix. A closed successor can never resume in place.

Check decoded geometry against the declared nonupsampled delivery dimensions.
Retain the original expected SHA-1 as parent provenance, plus the newly received
derivative's separate SHA-256. A resampled derivative is not expected to share
the parent byte hash; no original hash is refreshed. Preserve source processing
history explicitly. This stage acquires image bytes and checks containers only;
it does not compute fidelity features. The visual rubric and later main-study
freeze required by `REFERENCES.md` remain in force.

The resulting reference panel has Wikimedia resampling/encoding in its history.
The study must disclose this and include native-size and symmetric processing
sensitivities. These are not independent capture events, nor a demonstrated
capture-matched comparison with generated images.
