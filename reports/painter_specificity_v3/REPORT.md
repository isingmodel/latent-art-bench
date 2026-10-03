# Painter specificity v3: two further painter groups

Prespecified analysis (`studies/painter_specificity_v3/PROTOCOL.md`),
written once by
`python -m latent_art_bench.painter_specificity_v3.report analyze`.

## hand31

- H1 closeness (century minus Hudson shared fraction): -0.727, 95% [-0.765, -0.626], supported: True
- H2 dose-response (Mantel Spearman, noise-corrected references): 0.849, exact p 0.00027, supported: True

| Group | Configuration | Shared | Faithful | Exact | beta | D | Alignment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Century group | GPT Image 1 | 0.295 | 0.676 | 0.518 | 1.279 | 1.576 | 0.723 |
| Century group | GPT Image 2 | 0.185 | 0.533 | 0.316 | 1.139 | 0.943 | 0.764 |
| Century group | GPT Image 2.5 Flare | 0.189 | 0.668 | 0.348 | 1.292 | 0.994 | 0.805 |
| Century group | GPT Image 2.5 Sunburst | 0.236 | 0.678 | 0.419 | 1.245 | 1.117 | 0.771 |
| Century group | Nano Banana 2 | 0.216 | 0.754 | 0.350 | 1.038 | 1.133 | 0.698 |
| Century group | FLUX.2 Max | 0.177 | 0.450 | 0.223 | 0.840 | 0.728 | 0.708 |
| Hudson River School | GPT Image 1 | 0.957 | 0.902 | 0.834 | -0.014 | 1.249 | -0.029 |
| Hudson River School | GPT Image 2 | 0.986 | 0.925 | 0.874 | 0.044 | 1.032 | 0.127 |
| Hudson River School | GPT Image 2.5 Flare | 0.938 | 0.960 | 0.873 | -0.012 | 1.633 | -0.015 |
| Hudson River School | GPT Image 2.5 Sunburst | 0.935 | 0.962 | 0.862 | 0.113 | 1.258 | 0.162 |
| Hudson River School | Nano Banana 2 | 0.951 | 0.970 | 0.868 | 0.198 | 1.259 | 0.244 |
| Hudson River School | FLUX.2 Max | 0.894 | 0.894 | 0.460 | 0.119 | 0.977 | 0.257 |

## hand31_square

- H1 closeness (century minus Hudson shared fraction): -0.727, 95% [-0.765, -0.626], supported: True
- H2 dose-response (Mantel Spearman, noise-corrected references): 0.849, exact p 0.00107, supported: True

| Group | Configuration | Shared | Faithful | Exact | beta | D | Alignment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Century group | GPT Image 1 | 0.295 | 0.662 | 0.508 | 1.256 | 1.498 | 0.724 |
| Century group | GPT Image 2 | 0.185 | 0.510 | 0.308 | 1.133 | 0.866 | 0.776 |
| Century group | GPT Image 2.5 Flare | 0.189 | 0.652 | 0.339 | 1.284 | 0.908 | 0.816 |
| Century group | GPT Image 2.5 Sunburst | 0.236 | 0.662 | 0.410 | 1.243 | 1.017 | 0.786 |
| Century group | Nano Banana 2 | 0.216 | 0.742 | 0.341 | 1.052 | 1.017 | 0.722 |
| Century group | FLUX.2 Max | 0.177 | 0.412 | 0.216 | 0.828 | 0.694 | 0.713 |
| Hudson River School | GPT Image 1 | 0.957 | 0.857 | 0.811 | -0.014 | 1.217 | -0.032 |
| Hudson River School | GPT Image 2 | 0.986 | 0.906 | 0.855 | 0.029 | 1.045 | 0.091 |
| Hudson River School | GPT Image 2.5 Flare | 0.938 | 0.949 | 0.854 | 0.004 | 1.512 | 0.006 |
| Hudson River School | GPT Image 2.5 Sunburst | 0.935 | 0.952 | 0.842 | 0.084 | 1.246 | 0.130 |
| Hudson River School | Nano Banana 2 | 0.951 | 0.962 | 0.849 | 0.218 | 1.123 | 0.291 |
| Hudson River School | FLUX.2 Max | 0.894 | 0.842 | 0.421 | 0.097 | 0.990 | 0.227 |

## clip

- H1 closeness (century minus Hudson shared fraction): -0.401, 95% [-0.414, -0.373], supported: True
- H2 dose-response (Mantel Spearman, noise-corrected references): 0.861, exact p 0.00037, supported: True

| Group | Configuration | Shared | Faithful | Exact | beta | D | Alignment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Century group | GPT Image 1 | 0.470 | 0.646 | 0.400 | 0.577 | 0.855 | 0.574 |
| Century group | GPT Image 2 | 0.479 | 0.686 | 0.478 | 0.695 | 0.893 | 0.613 |
| Century group | GPT Image 2.5 Flare | 0.518 | 0.711 | 0.481 | 0.572 | 1.039 | 0.526 |
| Century group | GPT Image 2.5 Sunburst | 0.520 | 0.716 | 0.523 | 0.674 | 0.979 | 0.585 |
| Century group | Nano Banana 2 | 0.607 | 0.743 | 0.563 | 0.621 | 0.860 | 0.592 |
| Century group | FLUX.2 Max | 0.539 | 0.709 | 0.512 | 0.627 | 0.887 | 0.587 |
| Hudson River School | GPT Image 1 | 0.975 | 0.921 | 0.832 | 0.136 | 1.019 | 0.252 |
| Hudson River School | GPT Image 2 | 0.981 | 0.923 | 0.821 | 0.095 | 1.013 | 0.211 |
| Hudson River School | GPT Image 2.5 Flare | 0.897 | 0.932 | 0.836 | 0.253 | 1.444 | 0.259 |
| Hudson River School | GPT Image 2.5 Sunburst | 0.886 | 0.936 | 0.847 | 0.306 | 1.508 | 0.289 |
| Hudson River School | Nano Banana 2 | 0.874 | 0.941 | 0.812 | 0.395 | 1.243 | 0.389 |
| Hudson River School | FLUX.2 Max | 0.930 | 0.928 | 0.744 | 0.177 | 1.193 | 0.239 |

## csd

- H1 closeness (century minus Hudson shared fraction): -0.474, 95% [-0.489, -0.449], supported: True
- H2 dose-response (Mantel Spearman, noise-corrected references): 0.923, exact p 0.00055, supported: True

| Group | Configuration | Shared | Faithful | Exact | beta | D | Alignment |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Century group | GPT Image 1 | 0.462 | 0.662 | 0.492 | 0.751 | 0.742 | 0.673 |
| Century group | GPT Image 2 | 0.406 | 0.628 | 0.496 | 0.948 | 0.669 | 0.758 |
| Century group | GPT Image 2.5 Flare | 0.443 | 0.692 | 0.502 | 0.830 | 0.769 | 0.694 |
| Century group | GPT Image 2.5 Sunburst | 0.442 | 0.686 | 0.530 | 0.927 | 0.722 | 0.738 |
| Century group | Nano Banana 2 | 0.554 | 0.706 | 0.569 | 0.739 | 0.714 | 0.677 |
| Century group | FLUX.2 Max | 0.517 | 0.636 | 0.515 | 0.754 | 0.608 | 0.714 |
| Hudson River School | GPT Image 1 | 0.973 | 0.932 | 0.904 | 0.124 | 1.084 | 0.215 |
| Hudson River School | GPT Image 2 | 0.983 | 0.936 | 0.894 | 0.112 | 1.018 | 0.227 |
| Hudson River School | GPT Image 2.5 Flare | 0.932 | 0.953 | 0.897 | 0.188 | 1.453 | 0.207 |
| Hudson River School | GPT Image 2.5 Sunburst | 0.923 | 0.954 | 0.899 | 0.301 | 1.366 | 0.306 |
| Hudson River School | Nano Banana 2 | 0.923 | 0.954 | 0.878 | 0.377 | 1.148 | 0.397 |
| Hudson River School | FLUX.2 Max | 0.932 | 0.921 | 0.763 | 0.203 | 0.938 | 0.346 |

