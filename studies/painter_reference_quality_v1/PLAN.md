# Reference-quality sensitivity — 13 September 2026

This retrospective audit follows the user-supplied reviews and their assessment.
It is an assistant visual inspection of source reproductions, not a human
artist-resemblance study or an independent validation of artistic fidelity.
All original measurements, scalers, protocols and results remain unchanged.
No generated images are acquired or selected, and no paid requests are made.

Inspect all 649 measured confirmation/reference works and all 221 development
works. Bind each record to its retained work identity and raw SHA-256. Inspect
contact sheets, enlarging ambiguous examples. Record every work, including
unflagged ones. Decisions must use visible source content, never model scores.

Record clear calibration targets, photographic borders/margins, frames,
non-painting text/labels or surrounding capture backgrounds. A rectangular
painting-region box may exclude a visibly separate peripheral non-painting
region. Coordinates are fractions of the orientation-corrected source width
and height, in [left, top, right, bottom] order. Leave ambiguous boundaries
uncropped and explicitly flag uncertainty. Do not remove genuine dark edges,
artist signatures, depicted frames, or parts of the depicted composition.
Record a short reason for each correction. Original full-frame examples remain
in the manuscript to make the failure mode inspectable.

For each reference work, assess the broad visible organizing content: water
(river/lake/sea is a central organizing element), built place (buildings or a
settlement organize the composition), route (a path/road organizes an otherwise
open scene), or open/wooded land. If no single class is clear, mark mixed/unclear.
Compare with the recorded title class only after the visual decision. Change
only confident mismatches; retain original labels for mixed/unclear works.
These coarse assistant labels remain imperfect, not composition matching.
Development content labels are not used to fit scaling.

Re-extract the unchanged 31 features only for unambiguously cropped works.
Apply orientation and ICC handling as in the original normalization, then crop
before aspect-preserving Lanczos resize to a 512-pixel short side without
upsampling. Retain raw image bytes; store compact crop records and new vectors.
Reuse original vectors for unchanged works. Compare (1) cropped references with
original scaling, and (2) cropped references with scaling refitted on corrected
development vectors, transforming all generated vectors consistently. This
separates region changes from scale changes. Keep every painter and work.

Report defect prevalence by painter and panel, crop fractions, reference target
direction/magnitude changes, all six beta/D estimates, all 15 paired contrasts,
artist-pair slopes and held-scene scalar calibration. Separately compare the
original and revised content targets on the same 11 generated briefs. These are
descriptive sensitivities; the primary 21-comparison family is not redefined.
Preserve full results in the repository and add only a compact result and method
summary to the paper, replacing redundant prose so the paper does not lengthen.

Source/input hashes and exact replay commands accompany the new result. Local
raw-pixel availability does not constitute a public image archive. No public
release or recovery guarantee is claimed without separately verifying it.
