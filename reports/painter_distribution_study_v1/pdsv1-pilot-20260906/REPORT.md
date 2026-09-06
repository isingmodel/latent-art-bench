# Technical pilot results

All 18 requests returned decodable images. The pilot is excluded from research outcomes and no fidelity features were extracted.

| Route | Images | Cost (USD) | Geometry | Encoding |
| --- | ---: | ---: | --- | --- |
| nano_banana_2 | 6/6 | 0.4104855 | {"1024x1024": 6} | {"JPEG": 6} |
| flux_2_max | 6/6 | 0.4200000 | {"1024x1024": 6} | {"PNG": 6} |
| oauth_gpt_image_2 | 6/6 | 0.0000000 | {"1402x1122": 1, "1403x1121": 2, "1397x1126": 1, "1398x1125": 2} | {"PNG": 6} |

Total pilot charge: **$0.8304855**. The remaining 576 paid research requests project to $39.8917 using each route's maximum observed pilot cost. Adding 25% headroom and the pilot gives **$50.6952**, below $75.

All three routes pass the prospective technical criterion. This qualifies transport and estimated affordability, not statistical power or painter fidelity.

Paid routes share observed 1024-square geometry, but JPEG/PNG differ. OAuth geometry and quality deviate; no fully matched rendering claim.
Retain the paid geometry comparison and separate OAuth service comparison. The main analysis must include common-JPEG and resize sensitivities; they cannot erase unknown capture or earlier encoding histories.

Google and BFL provider pins were requested with fallback disabled. The responses do not attest immutable model snapshots. All six OAuth responses reported low quality despite medium requests. No route was changed or retried.

Verification replays the raw-response hashes, costs and decoded container metadata. This is maintainer/LLM self-review, not institutional independence.

Recheck with `uv run --locked python -m latent_art_bench.painter_distribution_study_v1.pilot_summary check`.
