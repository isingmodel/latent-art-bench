# Development-pilot implementation status

The roadmap has been completed through its defined stop path. “Complete” here means that each gate reached an evidence-backed outcome; it does not mean that failed measurements were forced through to a scientific generator comparison.

| Work package | Engineering result | Scientific result |
|---|---|---|
| WP0: pilot contract | Frozen in `configs/pilot_0/pilot.yaml` | Monet–Sisley and Pissarro–Cézanne; shared landscape/outdoor-place scene |
| WP1: reproducible substrate | Config-driven CLI, strict records, provenance, leakage guards, deterministic fixtures, and tests | Passed on synthetic fixtures |
| WP2: real corpus | Official AIC, CMA, Met, and NGA audit/adapters; rights and hash manifests; browser-assisted AIC CDN fallback | 108 canonical works, 119 reproductions, 11 accepted same-work pairs; reproduction scope is narrower than planned |
| WP3: preprocessing | EXIF, ICC-to-sRGB, alpha handling, aspect-preserving Lanczos, lossless content addressing | 119/119 inputs reproduced with exact output-pixel identity |
| WP4: measurements | Lee et al. chromatic measurement implemented and evaluated; frozen Kim et al. A-vector feasibility spike closed | Chromatic source behavior recovered; learned-formal evaluator failed reproducibility prerequisites |
| WP5: real-only qualification | Computed reproduction, perturbation, held-out artist, source prediction, and leave-source-out diagnostics | Chromatic `fail` on frozen JPEG stability; learned-formal `fail`; scientific gate closed |
| WP6: generation freeze | Scientific branch not opened. Test adapter remains hard-limited to `gpt-image-1` and `gpt-image-2` on loopback | Ten bypassed API-test calls succeeded; not benchmark evidence |
| WP7: reporting | Human-readable report, machine-readable evidence, resolved config, call accounting, and decision memo | Decision: stop before scientific generation and redesign the learned/stability contract |

## Frozen corpus

| Artist | Neighbor | Canonical works |
|---|---|---:|
| Claude Monet | Alfred Sisley | 30 |
| Alfred Sisley | Claude Monet | 21 |
| Camille Pissarro | Paul Cézanne | 30 |
| Paul Cézanne | Camille Pissarro | 27 |

The selection rule used museum metadata only. Movement labels remain metadata; they were not used as the target. Primary sources overlap across artists, and all selected assets have an explicit public-domain/open-access basis. Images and derived arrays remain ignored local data; portable manifests, hashes, source URLs, aggregate evidence, and reports are tracked.

## Qualification outcome

The chromatic feature recovered its preregistered delta, exponential, heavy-tail, and scale-invariance behaviors. On the real corpus, held-out artist balanced accuracy was `0.3507`, held-out source balanced accuracy was `0.1896`, and leave-source-out train artist balanced accuracy was `0.4050`. Median same-work reproduction distance was `0.5730` of median within-artist held-out distance.

Exact preprocessing pixels were deterministic for 119/119 reproductions. Resolution drift at a 256-pixel long side was `0.4937` of the within-artist median, inside the frozen `0.5` margin. JPEG-quality-85 drift was `0.6928`, outside that margin. The chromatic card is therefore `fail`, despite passing its other checks.

The learned-formal card is `fail`: the frozen upstream script is not runnable as released, the audited code revision has no reusable license, the exact checkpoint bytes are unavailable, and no reference vector exists for source-faithful verification. The roadmap forbids replacing it after viewing the corpus.

## GPT Image API test

The local `~/dev/openai-oauth` proxy passed health and model-discovery checks. Five matched landscape prompts—four artist targets plus one artist-free control—were sent once to each allowed model. All five `gpt-image-1` and all five `gpt-image-2` calls succeeded without retry, produced valid PNG files, and recorded content hashes and actual dimensions. These ten calls used the explicit unqualified-test bypass and cannot change the scientific stop decision.

See `reports/pilot_0/API_SMOKE.md`, `reports/pilot_0/evidence/chromatic_qualification.json`, and `reports/pilot_0/DECISION.md` for the durable evidence.
