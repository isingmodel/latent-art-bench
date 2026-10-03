# Readouts requested by review of the second collection (diagnostics v7)

Plan: `studies/painter_tmlr_diagnostics_v7/PLAN.md`.

## clip

- H2 across (16 pairs): mean Spearman 0.758, by configuration [0.821, 0.7, 0.794, 0.838, 0.682, 0.715]
- H2 all (28 pairs): mean Spearman 0.861, by configuration [0.876, 0.841, 0.875, 0.876, 0.86, 0.839]
- H2 within_century (6 pairs): mean Spearman 0.733, by configuration [0.771, 0.657, 0.771, 0.771, 0.771, 0.657]
- H2 within_hudson (6 pairs): mean Spearman 0.486, by configuration [-0.257, 0.371, 0.771, 0.6, 0.829, 0.6]
- century - Hudson: observed -40.1, faithful -22.9 [-23.5, -20.4], excess -17.3 [-19.2, -15.7] points

## csd

- H2 across (16 pairs): mean Spearman 0.847, by configuration [0.856, 0.879, 0.85, 0.859, 0.8, 0.835]
- H2 all (28 pairs): mean Spearman 0.923, by configuration [0.932, 0.933, 0.918, 0.926, 0.909, 0.92]
- H2 within_century (6 pairs): mean Spearman 0.876, by configuration [0.943, 0.886, 0.886, 0.886, 0.771, 0.886]
- H2 within_hudson (6 pairs): mean Spearman 0.267, by configuration [0.257, 0.314, 0.486, -0.257, 0.6, 0.2]
- century - Hudson: observed -47.4, faithful -27.3 [-28.5, -25.0], excess -20.0 [-21.7, -18.7] points

## hand31

- H2 across (16 pairs): mean Spearman 0.740, by configuration [0.588, 0.9, 0.788, 0.688, 0.879, 0.597]
- H2 all (28 pairs): mean Spearman 0.849, by configuration [0.82, 0.916, 0.86, 0.82, 0.902, 0.774]
- H2 within_century (6 pairs): mean Spearman 0.781, by configuration [0.714, 0.943, 0.829, 0.943, 0.714, 0.543]
- H2 within_hudson (6 pairs): mean Spearman 0.086, by configuration [0.486, 0.143, -0.257, -0.657, 0.486, 0.314]
- century - Hudson: observed -72.7, faithful -30.9 [-32.9, -26.6], excess -41.8 [-47.2, -34.9] points
- Impressionists - Hudson: observed -21.4, faithful -3.7 points; H 5.92 vs 6.24
- H1 resamples with N+B <= 0: {'century': [0, 0, 0, 0, 0, 0], 'hudson': [0, 0, 0, 0, 0, 90]}; fraction outside [0, 1]: {'century': [0, 0, 0, 0, 0, 150], 'hudson': [60, 11, 0, 0, 91, 237]}
