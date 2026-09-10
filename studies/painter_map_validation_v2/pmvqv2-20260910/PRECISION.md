# R10 fixed-map precision qualification v2

V2 is one R10/240-output pre-data redesign informed by retained failed v1 simulations.
V1 remains stopped. This record does not combine Monte Carlo confidence across versions.
E targets the expected finite-R10 V contrast; Q keeps its conditional-mean target.
The .05/81 lower-bound tail, .94 coverage floor and .25/1.0 baseline half-width limits
are unchanged. No fallback, additional allocation or live gate follows from this record.

Finite-support historical proxies; no new image outcomes or service-coverage guarantee.
Maintainer-run LLM design/implementation/review; not independent human investigators.
Source commit: `6956feccb4a1c6f65de1a07ba0eeab856882b012`.
Coverage gates all 27 laws; width gates only nine baseline laws per allocation.
Unavailable intervals count as coverage misses and infinite widths.
Decision: **qualified_proxy_only**; selected outputs: 240.

| R | Noise | Mean | Regime | Joint coverage | CP lower | Median E/Q half-width | Unavailable |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | gaussian_shaped | T1 | baseline | 0.98520 | 0.98088 | [0.06666736942830939, 0.6809294470716923] | 0 |
| 10 | gaussian_shaped | T1 | high_positive | 0.98740 | 0.98338 | [0.11545520348137714, 1.295951244461555] | 0 |
| 10 | gaussian_shaped | T1 | low_negative | 0.97830 | 0.97318 | [0.03673969870497948, 0.4458423502023209] | 0 |
| 10 | gaussian_shaped | midpoint | baseline | 0.98150 | 0.97673 | [0.06677773374992516, 0.7606944228444401] | 0 |
| 10 | gaussian_shaped | midpoint | high_positive | 0.98500 | 0.98066 | [0.11500083680802174, 1.4126695440134658] | 0 |
| 10 | gaussian_shaped | midpoint | low_negative | 0.98100 | 0.97618 | [0.036873024777352506, 0.503787883950555] | 0 |
| 10 | gaussian_shaped | T2 | baseline | 0.98400 | 0.97953 | [0.0665151530298016, 0.8455411307229246] | 0 |
| 10 | gaussian_shaped | T2 | high_positive | 0.98340 | 0.97886 | [0.11532434414546933, 1.571290124497681] | 0 |
| 10 | gaussian_shaped | T2 | low_negative | 0.97930 | 0.97429 | [0.03677022189428601, 0.5636820022969471] | 0 |
| 10 | t5_shaped | T1 | baseline | 0.98180 | 0.97707 | [0.06915386524569676, 0.6981774814901252] | 0 |
| 10 | t5_shaped | T1 | high_positive | 0.98700 | 0.98292 | [0.12791131529577576, 1.3087321907199265] | 0 |
| 10 | t5_shaped | T1 | low_negative | 0.97780 | 0.97263 | [0.03684305331827323, 0.45001021747770964] | 0 |
| 10 | t5_shaped | midpoint | baseline | 0.97950 | 0.97451 | [0.06914065163137637, 0.7794371988964549] | 0 |
| 10 | t5_shaped | midpoint | high_positive | 0.98550 | 0.98122 | [0.1281255728552045, 1.4289392530554201] | 0 |
| 10 | t5_shaped | midpoint | low_negative | 0.98100 | 0.97618 | [0.03682095814511287, 0.5059226451378174] | 0 |
| 10 | t5_shaped | T2 | baseline | 0.98250 | 0.97785 | [0.06920164800010237, 0.8625931605203183] | 0 |
| 10 | t5_shaped | T2 | high_positive | 0.98600 | 0.98179 | [0.12824967058032208, 1.5786039818370194] | 0 |
| 10 | t5_shaped | T2 | low_negative | 0.98130 | 0.97651 | [0.0369211239618317, 0.5649132361562551] | 0 |
| 10 | lognormal_shaped | T1 | baseline | 0.98320 | 0.97863 | [0.07334985246242898, 0.6458620701476605] | 0 |
| 10 | lognormal_shaped | T1 | high_positive | 0.98610 | 0.98190 | [0.14206499979830914, 1.2307796270542333] | 0 |
| 10 | lognormal_shaped | T1 | low_negative | 0.97880 | 0.97374 | [0.03645241829334532, 0.4205421743955895] | 0 |
| 10 | lognormal_shaped | midpoint | baseline | 0.98130 | 0.97651 | [0.07347000271977107, 0.7193215984875949] | 0 |
| 10 | lognormal_shaped | midpoint | high_positive | 0.98270 | 0.97807 | [0.1421192917111413, 1.3277951863472008] | 0 |
| 10 | lognormal_shaped | midpoint | low_negative | 0.97770 | 0.97252 | [0.03641979016158953, 0.47170335516032535] | 0 |
| 10 | lognormal_shaped | T2 | baseline | 0.97850 | 0.97340 | [0.0734413066999686, 0.7992758805001015] | 0 |
| 10 | lognormal_shaped | T2 | high_positive | 0.97910 | 0.97407 | [0.14220566347605526, 1.464400522714257] | 0 |
| 10 | lognormal_shaped | T2 | low_negative | 0.97600 | 0.97065 | [0.0365119235477893, 0.5272093014711641] | 0 |

Passing concerns only these discrete proxy laws and fixed numerical tolerances;
it opens no generation gate and guarantees neither actual precision nor coverage.
The V-energy target is finite-R; Q targets conditional scene-mean mismatch.
No reference, scene-population, latent-style or perceptual uncertainty is included.
