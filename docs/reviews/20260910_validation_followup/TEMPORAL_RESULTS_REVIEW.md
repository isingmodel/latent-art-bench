# Temporal results review — 10 September 2026

Run: `painter_naming_replication_v1/pnrv1-20260910`. Reviewer 1 is a
maintainer-run LLM agent who previously cross-reviewed the collector and wrote
the descriptive metadata audit. This is not external human or institutionally
independent peer review. The calculations below independently reconstruct the
results from retained vectors and assignments; no raw pixels were reopened and
no new inferential claim or score is introduced.

## Verification and disposition

No numerical, assignment or analysis-gating defect was found. All 264 assigned
images returned, with 264 measurements under each of three pipelines: 792 vectors
in total. All original request identities, arms, polarities, scenes, repetitions,
block positions and sequences agree with the primary measurement records.
Primary scaled coordinates reproduce exactly from the unscaled vectors and
unchanged development scaler. All frozen input and terminal collection/measurement
output hashes checked here agree with their bindings.

For each naming comparison I calculated the weighted V-energy directly from
distance matrices, then reconstructed each of the 24 coefficients by taking half
the change caused by swapping that pair alone. This is separate from the frozen
pooled-contribution implementation. Estimates and contributions agree within
2e-14. Independently generating the 99,999 fixed-seed sign assignments reproduces
the tail counts (one for Monet, zero for Cézanne), hence raw p-values .00002 and
.00001 with the plus-one correction.

For palette inference I reconstructed all 24 two-endpoint block interactions
from feature coordinate 2, using six scenes and four repetitions per scene.
Own calculations of within-scene sample covariance, covariance divided by
6²×4, Welch degrees of freedom, t tests and 98.75% marginal intervals agree with
the saved results within 2e-13. Applying Holm to the four reconstructed raw
p-values reproduces every top-level decision. Shared generic covariance is
0.00450553138; the two variance estimates are 0.01235125341 and 0.01057966534.

## Four primary endpoints

| Endpoint | Estimate | Raw p | Holm p, four tests | Interval |
| --- | ---: | ---: | ---: | --- |
| FLUX naming / Monet | −0.6951079233 | .000020 | .000060 | None specified |
| FLUX naming / Cézanne | −0.9520240321 | .000010 | .000040 | None specified |
| Palette named−generic / Monet | −0.1586478932 | .1744219243 | .3488438485 | [−.4749549337, .1576591473] |
| Palette named−generic / Cézanne | .0367407968 | .7268407457 | .7268407457 | [−.2625398377, .3360214313] |

The two palette intervals are 98.75% marginal intervals allocated within the
four-test family, not joint intervals for all four effects. Their standard
errors are .1111361931 and .1028575002; effective degrees of freedom are
14.635366 and 12.626095. The 192 palette images are not 192 independent
interaction observations.

Both naming effects satisfy the prospectively defined directional-replication
rule. Monet's artist-free and named V-energies are 2.265630 and 1.570522;
Cézanne's are 1.772275 and .820251. The same 24 free images enter both comparisons,
with painter-specific reference-content weights. There are 22 negative paired
contributions for Monet and 24 for Cézanne; those are descriptive signs, not
separate tests of individual images.

Both palette interactions remain unresolved. Monet has four negative and two
positive scene estimates, with 15/24 negative block interactions; its earlier
six scene estimates were all negative. Cézanne has one negative and five positive
scene estimates, with 11/24 negative blocks. These summaries do not establish a
between-collection difference or an absence of an additional naming effect.

The fixed control manipulation operates in all four arms: mean vivid-minus-muted
responses are 3.441692, 2.550630, 2.391982 and 2.587371 for free, generic, Monet
and Cézanne, with nominal intervals above zero. The secondary generic-minus-free
estimate is −.891062, nominal 95% interval [−1.077861, −.704262]. This repeats
the direction of the earlier secondary generic-clause response, but does not
turn the two unresolved primary named-minus-generic interactions into discoveries.

## Correct historical comparison

Original Study 1 FLUX effects were −.624646630 and −.895593477, each with
72 pairs and Holm p=.00008 in an eight-test family. The successor has 24 pairs
per painter and shared free controls. Changed finite-sample V-energy behavior,
dependence and collection conditions prevent attributing the modest magnitude
differences solely to time. One new FLUX output per arm/scene supplies no new
within-prompt variation estimate.

Original Study 2 effects were −.284367715 and −.017720927. Its historical
intervals [−.584714607, .015979177] and [−.343056397, .307614543] were 97.5%
marginal intervals forming an approximate 95% two-effect family; historical
Holm p-values were .064857047 and .888636789. The new primary p-values belong
only to the successor's four-test family. Do not compare old/new significance
levels as effect changes, mix the families, or interpret interval overlap as
effect equality. Neither collection establishes palette equivalence.

## Delivery, timing and duplicate checks

The descriptive integrity audit and separate direct set comparisons agree:
all 264 new encoded-image hashes are unique, and all 264 primary normalized
array hashes paired with their dimensions are unique. None matches the original
1,006 Study 1 or 192 primary Study 2 images. The ancillary 49-image predecessor
is outside this comparison. These findings exclude exact retained-byte and
same-shape normalized-array duplicates in the compared sets. They do not exclude
near-duplicates or establish independently sampled hidden model states.

All 72 FLUX outputs are 1024×1024 PNGs. FLUX quality is not requested or reported;
missing quality is not a measured quality category. OAuth requests specify
1024×1024, medium quality, opaque PNG, while all 192 delivered OAuth images are
nonsquare RGB PNGs. Their reported quality counts are:

| OAuth arm | Low | Medium | Total |
| --- | ---: | ---: | ---: |
| Free | 28 | 20 | 48 |
| Generic | 44 | 4 | 48 |
| Monet | 45 | 3 | 48 |
| Cézanne | 44 | 4 | 48 |
| All | 161 | 31 | 192 |

The medium total increases from 18 previously to 31, including free-arm counts
of 10 previously and 20 now. The 1536×1024 geometry occurs in 121 new images
versus 71 previously. All complete geometry/quality/polarity profiles remain in
`integrity_audit.json`. These changes matter for interpreting old/new comparisons
as delivered-service effects; they are not grounds for post-treatment exclusion
or adjustment.

First recorded pre-HTTP timestamp: 9 September 2026, 23:06:09.934950 UTC.
Terminal receipt: 10 September, 00:10:27.002717 UTC. The receipt elapsed time is
3,859.576712 seconds (64.3263 minutes), safely within the 24-hour contract.
All 264 initial positions and dispatch tickets retain order 0–263. Minimum,
median and maximum monotonic admission gaps are 5.000366, 14.901702 and
46.318923 seconds; the minimum pre-HTTP wall-clock gap is 5.000155 seconds.
Maximum timed-operation and outstanding-intent concurrency are both two, with
no missing timings, cancelled posts, failures or retries. These are local gate
and operation measurements, not observations of socket transmission or provider
execution order.

The receipt reports $5.04 new OpenRouter charges, no new pending/unknown costs
or reserves, and $50.7219185 conservative cumulative accounting including the
unchanged historical $5 reserve. Subscription usage has no assigned cash value.

## Interpretation and remaining limits

The study adds a separately collected, exactly nonduplicated set that supports
the two prespecified FLUX naming directions under the conditional randomization
null. It leaves the additional palette effects unresolved while again showing
a smaller response under the specific generic clause in secondary analysis.
The finite references, templates and evaluator remain exposed and shared with
the earlier work. Independent repeat-block errors and stable response
distributions remain assumptions for the approximate palette intervals;
monotonic pacing and unique hashes do not prove them. One interleaved collection
does not estimate variation over dates, independent services or investigators.

No frozen correction is requested. Manuscript integration should preserve the
historical/new denominators and multiplicity conventions, the changing delivered
geometry/quality mix, the limited meaning of exact-duplicate checks, and the
distinction between temporal directional replication and artistic validity.
Public package availability must be established separately from this local review.

## Exact reviewed identities

```text
c352a3bac3489784c987d65d0d3acd3f0c4141da61624abea06ca71ba8504054  studies/painter_naming_replication_v1/PROTOCOL.md
a6d2c535d9d554e1a0ea626c36dbaa91f4386d795f1dc781df7cb39c89313c32  src/latent_art_bench/painter_naming_replication_v1/analysis.py
859f789063d1d39f648096a9057376dcd0ace0f206f143fcd105313d3d7e26d7  data/manifests/painter_naming_replication_v1/pnrv1-20260910/freeze.json
b9a03e997aa085f418c912e18a58be4dea23c0608b6c15caebd98a9fc887f632  data/manifests/painter_naming_replication_v1/pnrv1-20260910/planned_requests.jsonl
6144b6d5d2847f9191c619b9b24764834f458bf52246ab55a0b03654381700bf  data/manifests/painter_naming_replication_v1/pnrv1-20260910/collection_receipt.json
bfad64b4dd76c102a43b37cadc24e90cf7c8c235f1201cb9ee8c924c096d83e4  data/manifests/painter_naming_replication_v1/pnrv1-20260910/measurement_receipt.json
9c4b1e4d95fbb62edb9f7ebbe87853a345bb7a027a20eff8baa87c945aaefd41  data/manifests/painter_naming_replication_v1/pnrv1-20260910/measurements.jsonl
e7da57c0b8942679a3ffaf3ce7740c0203cd9a7c3dbd50eaa2b64e5565b8e185  reports/painter_naming_replication_v1/pnrv1-20260910/analysis.json
d3cebfee59eb2a8827cb4d792d2046c9c7a071df239d96618832ed9cfbad97fb  reports/painter_naming_replication_v1/pnrv1-20260910/integrity_audit.json
```
