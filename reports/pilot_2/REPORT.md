# pilot_2 requested-label analysis

## Scope

This report estimates effects of sending requests bearing the labels `gpt-image-1` and `gpt-image-2` through the frozen OAuth transport. The labels define separate operational strata. They are not authoritative executed-backend identities, no cross-label superiority estimand was registered, and this report does not rank the labels.

Named prompts are compared with their matched artist-free control within the same content block, requested-label stratum, and repetition. Positive target improvement means the name moved the generated feature toward the target's held-out real works. Positive specificity difference-in-differences means that the target-versus-neighbor contrast improved beyond the matched control.

## Completion and hypothesis support

- Scientific execution status: **complete**.
- Exact 320-cell assignment grid accounted for: **true**.
- Complete 256-pair feature estimand grid: **false**.
- All four label-by-estimand hypotheses supported: **false**.

Completion records whether the frozen study was carried through and accounted for. It does not imply that any hypothesis was supported. Terminal refusals and failures can complete the assignment ledger while preventing a complete feature estimand.

Recorded completion qualifications:
- terminal refusals, failures, or missing features prevent a complete feature estimand

## Intention-to-treat accounting

Requested label | Expected cells | Succeeded | Refused | Terminal failed | Retry-cap failed | Still retryable | Missing | Complete named/control pairs
--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---:
`gpt-image-1` | 160 | 156 | 4 | 0 | 0 | 0 | 0 | 124/128
`gpt-image-2` | 160 | 159 | 1 | 0 | 0 | 0 | 0 | 127/128

Across all assignments: 5 refused cells, 0 terminal failures (0 after the fixed retry cap), 0 missing cells, and 0 successful cells without an analyzable projected feature. These outcomes are retained in the ITT accounting and are not silently removed.

## Primary requested-label-stratum estimates

Requested label | Estimand | Estimate | 95% cluster interval | Familywise lower bound | AIC-only | NGA-only | Exact block sign-flip p | Holm-adjusted p | Decision
--- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---
`gpt-image-1` | Target improvement | 8.649239 | — | — | 5.968121 | 9.542978 | — | 1.000000 | not supported
`gpt-image-1` | Artist-vs-neighbor specificity DiD | 5.610714 | — | — | 6.756036 | 2.506050 | — | 1.000000 | not supported
`gpt-image-2` | Target improvement | 9.926269 | — | — | 7.635423 | 10.092928 | — | 1.000000 | not supported
`gpt-image-2` | Artist-vs-neighbor specificity DiD | 6.501271 | — | — | 7.868489 | 2.962764 | — | 1.000000 | not supported

The interval is the deterministic two-stage cluster bootstrap: real works are resampled within artist-by-source cells, then the eight content blocks and repetitions are resampled while every named/control pair is preserved. The run uses 10,000 draws and seed `20260901`. Exact one-sided inference flips the signs of the eight block estimates; Holm correction covers the fixed family of two requested-label strata by two primary estimands. AIC-only and NGA-only signs must both be positive for support. The support decision uses the one-sided Bonferroni familywise lower bound at quantile `0.0125`, not the descriptive two-sided 95% interval.

## Secondary per-artist estimates

Requested label | Artist | Estimand | Estimate | AIC-only | NGA-only | Complete pairs
--- | --- | --- | ---: | ---: | ---: | ---:
`gpt-image-1` | `alfred_sisley` | Target improvement | 13.541805 | 8.623339 | 16.634054 | 32/32
`gpt-image-1` | `alfred_sisley` | Artist-vs-neighbor specificity DiD | 8.729511 | 9.424969 | 7.340496 | 32/32
`gpt-image-1` | `camille_pissarro` | Target improvement | 14.374661 | 9.524331 | 15.397330 | 32/32
`gpt-image-1` | `camille_pissarro` | Artist-vs-neighbor specificity DiD | 15.603853 | 16.764231 | 8.402944 | 32/32
`gpt-image-1` | `claude_monet` | Target improvement | 1.780388 | -1.091486 | 4.555096 | 32/32
`gpt-image-1` | `claude_monet` | Artist-vs-neighbor specificity DiD | -6.943118 | -5.468762 | -7.475904 | 32/32
`gpt-image-1` | `paul_cezanne` | Target improvement | 4.364511 | 6.937470 | 0.448641 | 28/32
`gpt-image-1` | `paul_cezanne` | Artist-vs-neighbor specificity DiD | 4.972881 | 6.239086 | 1.649610 | 28/32
`gpt-image-2` | `alfred_sisley` | Target improvement | 15.066876 | 9.788119 | 18.505091 | 32/32
`gpt-image-2` | `alfred_sisley` | Artist-vs-neighbor specificity DiD | 9.428151 | 10.079392 | 8.216919 | 32/32
`gpt-image-2` | `camille_pissarro` | Target improvement | 14.942526 | 10.586336 | 15.622770 | 32/32
`gpt-image-2` | `camille_pissarro` | Artist-vs-neighbor specificity DiD | 14.524930 | 16.741159 | 7.139252 | 32/32
`gpt-image-2` | `claude_monet` | Target improvement | 3.071582 | 0.028915 | 5.594898 | 32/32
`gpt-image-2` | `claude_monet` | Artist-vs-neighbor specificity DiD | -6.853109 | -5.765331 | -7.220692 | 32/32
`gpt-image-2` | `paul_cezanne` | Target improvement | 6.517568 | 10.219058 | 0.344310 | 31/32
`gpt-image-2` | `paul_cezanne` | Artist-vs-neighbor specificity DiD | 8.982656 | 10.501000 | 3.739861 | 31/32

## Secondary chromatic description

This Lee-derived seamlessness and mean-rescaled-histogram view is descriptive only. It cannot open or close the generation gate, rescue the learned-formal primary analysis, support an executed-model claim, or rank request labels.

Requested label | Named features | Control features | Complete pairs | Mean named S | Mean control S | Paired named−control S | Paired histogram Hellinger
--- | ---: | ---: | ---: | ---: | ---: | ---: | ---:
`gpt-image-1` | 124/128 | 32/32 | 124/128 | -0.052651 | 0.030558 | -0.084732 | 0.093774
`gpt-image-2` | 127/128 | 32/32 | 127/128 | -0.048603 | 0.025855 | -0.074312 | 0.086227

Requested label | Artist | Complete pairs | Paired named−control S | Paired histogram Hellinger | Named→real-artist Hellinger | Control→real-artist Hellinger
--- | --- | ---: | ---: | ---: | ---: | ---:
`gpt-image-1` | `alfred_sisley` | 32/32 | -0.076212 | 0.081675 | 0.080337 | 0.088377
`gpt-image-1` | `camille_pissarro` | 32/32 | -0.102957 | 0.103092 | 0.062783 | 0.105280
`gpt-image-1` | `claude_monet` | 32/32 | -0.105876 | 0.104032 | 0.079626 | 0.145335
`gpt-image-1` | `paul_cezanne` | 28/32 | -0.049478 | 0.085228 | 0.069164 | 0.115185
`gpt-image-2` | `alfred_sisley` | 32/32 | -0.051853 | 0.069003 | 0.077763 | 0.080845
`gpt-image-2` | `camille_pissarro` | 32/32 | -0.107076 | 0.099608 | 0.060818 | 0.097400
`gpt-image-2` | `claude_monet` | 32/32 | -0.096092 | 0.094630 | 0.080613 | 0.136978
`gpt-image-2` | `paul_cezanne` | 31/32 | -0.041192 | 0.081522 | 0.065857 | 0.105643

Chromatic result SHA-256: `e459dcec8e92ba566df6b4d4e19ccc761b3deb7e8fabf3c62d12f98d89f97977`.

These preregistered per-artist values are descriptive secondary estimates. They carry no confidence interval, multiplicity adjustment, or separate hypothesis-support claim.

## Interpretation boundary

Any supported row applies only to outputs obtained after sending that request label through the pinned transport, the frozen prompts, and the frozen digital reference atlas. It is not evidence about an authoritative executed model, physical artworks, arbitrary digitizations, or a ranking between labels.

Analysis result SHA-256: `a7fb58770ced0315a5963f1cd9606d91dd10ec30a324196af7720da85b82025c`.
