# Painter Feature Generation v2 — acquisition amendment 1.1

Issued 2026-09-05. Amends only §4 of v2 Protocol 1.0. No hypotheses, prompt strings, generator
settings, roles, feature formulas, scaling, or statistical endpoints change. The 1.0 text and
all existing freezes remain unchanged.

## Timing and reason

The original-image acquisition was stopped because multiple selected Commons originals exceeded
its prospectively frozen 64 MiB file ceiling. The terminal receipt and partial ledger remain at
`data/manifests/painter_feature_generation_v2/pfg2-acquisition-20260905/`. This is a resource
limitation, not evidence that the corresponding works are ineligible. Excluding the largest scans
would introduce an avoidable source-dependent loss.

The registered SD-Turbo run had already begun when this amendment was written. No generated image
had been visually inspected, and no active real/generated feature or statistical result had been
calculated. Original images had been decoded only for integrity and dimensions by the acquisition
code. This timing is disclosed; the amendment is prospective for the replacement acquisition, not
claimed to precede all generation.

## Replacement acquisition of the same work frame

Use a new acquisition ID, disjoint workspace and output paths, binding the predecessor's freeze,
final ledger hash, and terminal receipt. The entire 1,193-work role manifest remains fixed. Do not
splice original-run successes into this run, add works, change roles, or select by measured features.

Before image transport, request Commons imageinfo for every selected filename, in deterministic
batches grouped by a requested rendering width. The width targets at least 1,536 pixels on the
short side, rounded upward to a multiple of 512 and capped at the recorded native width. Original
files with a native short side between 1,024 and 1,535 remain valid without upsampling.

Imageinfo must report the same original SHA-1 and original dimensions as the frozen v1 snapshot,
an allowed open licence without a usage restriction, and a delivered rendering with a short side
of at least 1,024. Use its exact `thumburl`, or its exact original URL when the provider returns
the original at the requested width. No URL is invented or inferred from a filename. Retain each
metadata response and the derivative-to-original linkage.

Fetch every qualifying rendering once under the same three-attempt transport policy. Record the
rendering's SHA-256, dimensions, byte length, ICC status, and the source-original SHA-1. Do not
compare a derivative's SHA-1 to the original's SHA-1: that would confuse capture lineage with file
identity. Verify actual delivered dimensions against the imageinfo rendering receipt.

The source-native 1,024-pixel floor, no-upsampling analysis at 512 pixels, all previously assigned
roles, complete attempt retention, and resource reserve remain unchanged. Failures are retained;
the finite measured frame and all attrition are reported. Commons rendering can alter codecs,
profiles, or fine texture, and is explicitly part of this paper's digital-surrogate construct.
It is not an independently captured image or a pixel-identical copy of the native original.
