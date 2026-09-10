# Fixed-map offline precision qualification

Finite-support historical proxies; no new image outcomes or service-coverage guarantee.
Maintainer-run LLM design/implementation/review; not independent human investigators.
Source commit: `eb70ab8c30019b4b283366c170f8bdaf1405a023`.
Coverage gates all 27 laws; width gates only nine baseline laws per allocation.
Unavailable intervals count as coverage misses and infinite widths.
Decision: **stop_inferential_proposal**; selected outputs: None.

| R | Noise | Mean | Regime | Joint coverage | CP lower | Median E/Q half-width | Unavailable |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4 | gaussian_shaped | T1 | baseline | 0.99980 | 0.99882 | [0.16374080203075997, 2.0929497960648904] | 0 |
| 6 | gaussian_shaped | T1 | baseline | 0.99370 | 0.99071 | [0.10142549444427895, 1.1293609579362889] | 0 |
| 8 | gaussian_shaped | T1 | baseline | 0.98910 | 0.98532 | [0.07886391794040026, 0.8313773677690206] | 0 |
| 4 | gaussian_shaped | T1 | high_positive | 0.99930 | 0.99797 | [0.2926466549553821, 5.173760269042751] | 0 |
| 6 | gaussian_shaped | T1 | high_positive | 0.99600 | 0.99352 | [0.17798788139287622, 2.459410794969423] | 0 |
| 8 | gaussian_shaped | T1 | high_positive | 0.99010 | 0.98648 | [0.1372656987625327, 1.6778449381723342] | 0 |
| 4 | gaussian_shaped | T1 | low_negative | 0.99860 | 0.99693 | [0.08940672274761989, 1.1911579175059392] | 0 |
| 6 | gaussian_shaped | T1 | low_negative | 0.99170 | 0.98834 | [0.05569615556440235, 0.6974108260998273] | 0 |
| 8 | gaussian_shaped | T1 | low_negative | 0.98460 | 0.98021 | [0.04331287500771604, 0.5315044441797558] | 0 |
| 4 | gaussian_shaped | midpoint | baseline | 0.99940 | 0.99813 | [0.16486083773002347, 2.246373438178838] | 0 |
| 6 | gaussian_shaped | midpoint | baseline | 0.99430 | 0.99143 | [0.1020619417188235, 1.2402777852632605] | 0 |
| 8 | gaussian_shaped | midpoint | baseline | 0.98710 | 0.98303 | [0.07871071457478201, 0.9216842188060432] | 0 |
| 4 | gaussian_shaped | midpoint | high_positive | 0.99900 | 0.99751 | [0.29363238097561883, 5.314731647587024] | 0 |
| 6 | gaussian_shaped | midpoint | high_positive | 0.99410 | 0.99119 | [0.17798969068153553, 2.600876603560531] | 0 |
| 8 | gaussian_shaped | midpoint | high_positive | 0.99050 | 0.98694 | [0.13713761800224944, 1.795432148992643] | 0 |
| 4 | gaussian_shaped | midpoint | low_negative | 0.99750 | 0.99544 | [0.0891629642091479, 1.3067881839659732] | 0 |
| 6 | gaussian_shaped | midpoint | low_negative | 0.99030 | 0.98671 | [0.05591166633569897, 0.7790116041815338] | 0 |
| 8 | gaussian_shaped | midpoint | low_negative | 0.98340 | 0.97886 | [0.04336883077500561, 0.5999958511154082] | 0 |
| 4 | gaussian_shaped | T2 | baseline | 0.99950 | 0.99829 | [0.16494624847806272, 2.428168810369779] | 0 |
| 6 | gaussian_shaped | T2 | baseline | 0.99390 | 0.99095 | [0.10164264103180651, 1.3645340063696842] | 0 |
| 8 | gaussian_shaped | T2 | baseline | 0.98670 | 0.98258 | [0.07910011867474218, 1.0189782480276501] | 0 |
| 4 | gaussian_shaped | T2 | high_positive | 0.99940 | 0.99813 | [0.2934035432532745, 5.506786715297812] | 0 |
| 6 | gaussian_shaped | T2 | high_positive | 0.99580 | 0.99327 | [0.17806117632478535, 2.784234143922221] | 0 |
| 8 | gaussian_shaped | T2 | high_positive | 0.98870 | 0.98486 | [0.13704065709151858, 1.973954297923237] | 0 |
| 4 | gaussian_shaped | T2 | low_negative | 0.99770 | 0.99570 | [0.08967010876562098, 1.4491109154499753] | 0 |
| 6 | gaussian_shaped | T2 | low_negative | 0.98940 | 0.98567 | [0.05577985277332349, 0.8623711862807562] | 0 |
| 8 | gaussian_shaped | T2 | low_negative | 0.98370 | 0.97919 | [0.04348949072957985, 0.6660308258003227] | 0 |
| 4 | t5_shaped | T1 | baseline | 0.99950 | 0.99829 | [0.17196891431686692, 2.132779622354116] | 0 |
| 6 | t5_shaped | T1 | baseline | 0.99440 | 0.99155 | [0.10598716216166293, 1.1610754356883473] | 0 |
| 8 | t5_shaped | T1 | baseline | 0.99000 | 0.98636 | [0.0819749097413301, 0.854531810083033] | 0 |
| 4 | t5_shaped | T1 | high_positive | 0.99930 | 0.99797 | [0.32805166102355365, 5.009610344708051] | 0 |
| 6 | t5_shaped | T1 | high_positive | 0.99480 | 0.99204 | [0.19833042373334167, 2.467945650791864] | 0 |
| 8 | t5_shaped | T1 | high_positive | 0.98890 | 0.98509 | [0.1523420616088317, 1.6769616069967188] | 0 |
| 4 | t5_shaped | T1 | low_negative | 0.99910 | 0.99766 | [0.08999729840193987, 1.1729960309884617] | 0 |
| 6 | t5_shaped | T1 | low_negative | 0.99280 | 0.98964 | [0.05597858395803042, 0.6992954417927819] | 0 |
| 8 | t5_shaped | T1 | low_negative | 0.98590 | 0.98167 | [0.04355612217380636, 0.5379787105496221] | 0 |
| 4 | t5_shaped | midpoint | baseline | 0.99960 | 0.99846 | [0.17214495868664964, 2.2780197725874913] | 0 |
| 6 | t5_shaped | midpoint | baseline | 0.99400 | 0.99107 | [0.10607758983210547, 1.2680962781293232] | 0 |
| 8 | t5_shaped | midpoint | baseline | 0.98810 | 0.98418 | [0.08216620778686018, 0.9447851660800726] | 0 |
| 4 | t5_shaped | midpoint | high_positive | 0.99810 | 0.99624 | [0.3282081338457967, 5.181098299799961] | 0 |
| 6 | t5_shaped | midpoint | high_positive | 0.99460 | 0.99180 | [0.19869773377291855, 2.592873345127239] | 0 |
| 8 | t5_shaped | midpoint | high_positive | 0.98910 | 0.98532 | [0.1526846056952466, 1.801999259860425] | 0 |
| 4 | t5_shaped | midpoint | low_negative | 0.99850 | 0.99679 | [0.08981388583216593, 1.2997676515353263] | 0 |
| 6 | t5_shaped | midpoint | low_negative | 0.99240 | 0.98917 | [0.0560190827082742, 0.7817922044968035] | 0 |
| 8 | t5_shaped | midpoint | low_negative | 0.98510 | 0.98077 | [0.04363150201361437, 0.6015173476547948] | 0 |
| 4 | t5_shaped | T2 | baseline | 0.99960 | 0.99846 | [0.17258073511656316, 2.4580235944587616] | 0 |
| 6 | t5_shaped | T2 | baseline | 0.99360 | 0.99059 | [0.1060758360576409, 1.3832708643814988] | 0 |
| 8 | t5_shaped | T2 | baseline | 0.98660 | 0.98247 | [0.08219815288792601, 1.0402864375675982] | 0 |
| 4 | t5_shaped | T2 | high_positive | 0.99800 | 0.99610 | [0.32736888219066707, 5.390509539929905] | 0 |
| 6 | t5_shaped | T2 | high_positive | 0.99410 | 0.99119 | [0.1979348490839741, 2.745428333399806] | 0 |
| 8 | t5_shaped | T2 | high_positive | 0.98950 | 0.98578 | [0.15246468850269002, 1.9579042992108617] | 0 |
| 4 | t5_shaped | T2 | low_negative | 0.99830 | 0.99651 | [0.09016249999979933, 1.4285513251161128] | 0 |
| 6 | t5_shaped | T2 | low_negative | 0.99090 | 0.98741 | [0.055558025539408015, 0.8604754057331243] | 0 |
| 8 | t5_shaped | T2 | low_negative | 0.98500 | 0.98066 | [0.043504119024797304, 0.6682866431523266] | 0 |
| 4 | lognormal_shaped | T1 | baseline | 0.99800 | 0.99610 | [0.1840699229566184, 1.9628223343327356] | 0 |
| 6 | lognormal_shaped | T1 | baseline | 0.99330 | 0.99023 | [0.11259258550748227, 1.0686066131210836] | 0 |
| 8 | lognormal_shaped | T1 | baseline | 0.98750 | 0.98349 | [0.08737349703591607, 0.7890838331699279] | 0 |
| 4 | lognormal_shaped | T1 | high_positive | 0.99820 | 0.99638 | [0.36357771596206134, 4.562924751711872] | 0 |
| 6 | lognormal_shaped | T1 | high_positive | 0.99240 | 0.98917 | [0.21924534113842475, 2.286098494142428] | 0 |
| 8 | lognormal_shaped | T1 | high_positive | 0.98960 | 0.98590 | [0.16847775999480927, 1.5726799813561283] | 0 |
| 4 | lognormal_shaped | T1 | low_negative | 0.99750 | 0.99544 | [0.09070728198707798, 1.0953124891135273] | 0 |
| 6 | lognormal_shaped | T1 | low_negative | 0.98950 | 0.98578 | [0.05569625329080266, 0.6502264275162136] | 0 |
| 8 | lognormal_shaped | T1 | low_negative | 0.98310 | 0.97852 | [0.04311961038948527, 0.5005941286605995] | 0 |
| 4 | lognormal_shaped | midpoint | baseline | 0.99870 | 0.99707 | [0.18386831460564712, 2.094136364799162] | 0 |
| 6 | lognormal_shaped | midpoint | baseline | 0.99350 | 0.99047 | [0.1129072935577286, 1.1665681886841524] | 0 |
| 8 | lognormal_shaped | midpoint | baseline | 0.98380 | 0.97931 | [0.08711588864092523, 0.8683881573876364] | 0 |
| 4 | lognormal_shaped | midpoint | high_positive | 0.99800 | 0.99610 | [0.36095890863673197, 4.692262694251999] | 0 |
| 6 | lognormal_shaped | midpoint | high_positive | 0.99380 | 0.99083 | [0.22022530425198758, 2.4007599807521287] | 0 |
| 8 | lognormal_shaped | midpoint | high_positive | 0.98660 | 0.98247 | [0.16925604488023488, 1.6731989794338782] | 0 |
| 4 | lognormal_shaped | midpoint | low_negative | 0.99690 | 0.99466 | [0.09098721725705919, 1.1991593682819586] | 0 |
| 6 | lognormal_shaped | midpoint | low_negative | 0.98980 | 0.98613 | [0.055873817710303066, 0.7282719450406878] | 0 |
| 8 | lognormal_shaped | midpoint | low_negative | 0.98140 | 0.97662 | [0.04303480666725759, 0.558911893178691] | 0 |
| 4 | lognormal_shaped | T2 | baseline | 0.99790 | 0.99597 | [0.1844241650592246, 2.2614049483178547] | 0 |
| 6 | lognormal_shaped | T2 | baseline | 0.99290 | 0.98976 | [0.11257614596280012, 1.2745852520859873] | 0 |
| 8 | lognormal_shaped | T2 | baseline | 0.98420 | 0.97976 | [0.08732776536646009, 0.9610434896528317] | 0 |
| 4 | lognormal_shaped | T2 | high_positive | 0.99780 | 0.99584 | [0.3616784124723883, 4.915181164814195] | 0 |
| 6 | lognormal_shaped | T2 | high_positive | 0.99140 | 0.98799 | [0.2190500423683857, 2.5390998953801773] | 0 |
| 8 | lognormal_shaped | T2 | high_positive | 0.98410 | 0.97964 | [0.16870348421765252, 1.8156686155502089] | 0 |
| 4 | lognormal_shaped | T2 | low_negative | 0.99720 | 0.99505 | [0.09116156272558879, 1.3227301676032528] | 0 |
| 6 | lognormal_shaped | T2 | low_negative | 0.98710 | 0.98303 | [0.05576223901433875, 0.8028855567523651] | 0 |
| 8 | lognormal_shaped | T2 | low_negative | 0.98370 | 0.97919 | [0.0432125749736091, 0.6243456608481028] | 0 |

Passing concerns only these discrete proxy laws and fixed numerical tolerances;
it opens no generation gate and guarantees neither actual precision nor coverage.
The V-energy target is finite-R; Q targets conditional scene-mean mismatch.
No reference, scene-population, latent-style or perceptual uncertainty is included.
