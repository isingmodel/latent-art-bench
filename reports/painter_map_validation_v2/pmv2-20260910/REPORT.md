# Prospective fixed-map comparison on twelve new scene briefs

Run `pmv2-20260910`; status **approximate_simultaneous_intervals**.
240 allocated images, 120 pairs, ten repetitions per scene; FLUX/Cezanne, primary512 and all 31 unchanged features.
Terminal measurement counts: `{"measured": 240}`.
Unavailability reasons: `[]`.

| Endpoint | T2−T1 | Approximate simultaneous 95% interval | Direction |
| --- | ---: | --- | --- |
| deltaE | -0.390186879 | [-0.509032897, -0.271340860] | negative |
| deltaQ | -5.046510453 | [-7.879516972, -2.213503934] | negative |

Joint interpretation: `resolved_other_ordering`.

Component point values (interpretation aids; no component inference):
`{"Q_T1": 6.949537455161918, "Q_T2": 1.90302700221359, "energy_T1": 1.6706635369007783, "energy_T2": 1.2804766583666742}`.

E uses unsquared standardized distance and targets expected finite-R10 empirical V-energy. Q uses squared standardized coordinates and the distinct-repeat correction for conditional scene means; negative values are retained.

The paired within-scene delete-one jackknife preserves each scene's weight. Both intervals use t(9,.9875), with a nominal simultaneous 95% target. Nonpositive/nonfinite variance withholds both intervals. Incomplete or ineligible collection withholds all scientific summaries.

Conditional on the old maps/scaler/references and these authored scenes. Approximate intervals assume independent stationary repeats; proxy qualification does not establish actual service coverage. No perceptual, capture, scene-population or internal-mechanism inference.

Maintainer-run LLM design, implementation and review; not an independent human or institutional replication. Numerical replay does not authenticate absent image acquisition.
