# Retrospective SD-Turbo common-response audit

All 2,000 retained outputs, all four painters, all 16 fixed scenes and all 25 paired-seed blocks.
The control already requests oil painting. No shared-family control is present.
Previously analyzed pixels and historical references are reused. No prospective or independent replication is claimed.

| View | C | L | N | T | C/N | beta | Pooled D | Scene D |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all31 | 12.211777 | 6.81428856 | 19.0260655 | 5.39748843 | 0.641844577 | 0.61753264 | 0.916968523 | 1.6366323 |
| color | 2.75324197 | 2.03418125 | 4.78742322 | 0.719060728 | 0.575098931 | 0.632180399 | 0.692255148 | 0.884251602 |
| spatial | 7.47100258 | 1.33383112 | 8.80483371 | 6.13717146 | 0.848511492 | 0.310210442 | 1.26996497 | 3.53855496 |
| texture | 1.98753243 | 3.44627619 | 5.43380862 | -1.45874375 | 0.365771519 | 0.80492661 | 0.894718918 | 1.09123039 |

`analysis.json` retains both decomposition targets for every family, each scene, all six painter pairs, every delete-one-block result and finite sensitivity ranges.
Ratios with nonpositive N and alignment/error with zero reference energy are unavailable with reasons. Signed estimates and ratios outside [0,1] are retained.
The descriptive common-majority criterion is N > 0 and T > 0; it is not a significance test. No p-values or confidence intervals are supplied.

Replay: `uv run --locked python -m latent_art_bench.painter_cross_cohort_v1 check --execute-real --inputs-sha256 94413b3ee5bd689f60df35e7a8135f79eb929fd9dbee36bd450b47df4db0e693`.
