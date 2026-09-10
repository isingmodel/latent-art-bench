# Painter Feature Generation v2 — rendering transport correction 1.3

Issued 2026-09-05 before a new rendering-acquisition run and before active feature extraction.
The prior rendering run is terminal: 272 dispositions (78 acquired, 194 failed), plus one
interrupted request with unknown response. Its images, ledger, and terminal receipt stay intact.
This amendment fixes the collector, not the work frame or a statistical result.

## Verified cause

The previous collector incorrectly required `upload.wikimedia.org` and equality with imageinfo's
reported thumbnail dimensions. Wikimedia now advertises `thumb.wikimedia.org` for thumbnails;
originals remain on `upload.wikimedia.org`. See the provider's
[migration notice](https://phabricator.wikimedia.org/T434821).

[Imageinfo documentation](https://www.mediawiki.org/wiki/API:Imageinfo/en) explains that returned
thumbnail URLs may refer to a larger pregenerated size. The
[standard-size documentation](https://www.mediawiki.org/wiki/Common_thumbnail_sizes/en)
describes upward rounding. A recorded thumbnail URL can also identify the unscaled original.
Thus the collector's strict comparison rejected legitimate larger files and the new host.

## New, disjoint acquisition

Bind the predecessor's terminal receipt, ledger, images freeze, completed metadata receipt,
and full 1,193-row rendering manifest. Reuse that complete metadata evidence, not its image
successes. Bind the original unchanged work frame and a new complete request manifest. Fetch
every registered rendering under a new run ID and disjoint workspace, without splicing previous
downloaded bytes, changing roles, adding files, or substituting a failed URL.

Use each exact URL already supplied by the provider. Allow HTTPS port 443 on precisely
`upload.wikimedia.org` and `thumb.wikimedia.org`, with no user info, fragment, redirects, output
URL rewriting, or host substitution. A thumbnail path must be under `/wikipedia/commons/thumb/`;
a native original must be under `/wikipedia/commons/` on `upload.wikimedia.org`.

For a native original, verify its frozen original SHA-1 and original encoded dimensions.
For a thumbnail, parse the advertised pixel width from the already registered URL's final
`NNNpx-` segment (do not construct a URL), require that decoded width, and require height
compatible with the frozen source aspect ratio within max(2 pixels, 0.2% of expected height).
In both cases require full decode, JPEG/PNG/TIFF/WebP, and an actual short side of at least 1,024.
Retain reported and decoded dimensions separately, including differences. Unsupported formats
remain failures; do not convert them opportunistically. All provider files are digital surrogates,
not independent captures or adjudicated complete views.

Three attempts at most per exact image URL, only for transport errors, HTTP 429 or 5xx; respect
Retry-After, otherwise 5 then 15 seconds. One request at a time and at least one second between
items. Retain each full or flagged partial response, status, and hash. Maximum response 64 MiB;
free-disk reserve 5 GiB. An interrupted GET may consume its remaining registered attempts; never
retry a terminal work disposition. A terminal run is permanently closed. This is the last
defined acquisition contract, not permission to keep changing rules to hit a desired count.

The 512-pixel measurement scale, 496-pixel crop sensitivity, feature definitions, generated grids,
and analysis in amendments 1.0–1.2 are unchanged. Report all actual attrition and the acquisition
correction's timing. Checks are operator/LLM-assisted, not institutionally independent review.
