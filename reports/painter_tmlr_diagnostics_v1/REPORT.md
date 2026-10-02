# TMLR revision diagnostics

Retrospective analysis under
[the plan](../../studies/painter_tmlr_diagnostics_v1/PLAN.md).
Descriptive only: no tests; deletion ranges and bootstrap frequencies describe
dependence on the 14 authored scenes.

## Shared fraction beyond the generic clause, 31 features

| Configuration | N/(N+B) | faithful | N/H | B/H | color | spatial | texture | equal family | covariance | within scene |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 1 | 0.713 | 0.952 | 5.262 | 2.116 | 0.838 | 0.777 | 0.486 | 0.724 | 0.722 | 0.710 |
| GPT Image 2 | 0.709 | 0.893 | 4.979 | 2.041 | 0.743 | 0.596 | 0.738 | 0.700 | 0.712 | 0.762 |
| GPT Image 2.5 Flare | 0.711 | 0.848 | 4.989 | 2.026 | 0.815 | 0.655 | 0.601 | 0.708 | 0.764 | 0.769 |
| GPT Image 2.5 Sunburst | 0.667 | 0.869 | 3.970 | 1.984 | 0.667 | 0.615 | 0.703 | 0.661 | 0.713 | 0.722 |
| Nano Banana 2 | 0.691 | 0.925 | 1.359 | 0.607 | 0.568 | 0.698 | 0.798 | 0.689 | 0.658 | 0.528 |
| FLUX.2 Max | 0.884 | 0.904 | 5.341 | 0.701 | 0.826 | 0.951 | 0.765 | 0.898 | 0.869 | 0.936 |

Exchangeable null: 0.25. Faithful: named means replaced by reference means,
generic mean kept; includes the reproduction/generation and content gaps.

## Direction and centroid proximity, 31 features

| Configuration | cosine(c, t) | projection | gain | shared part | between part |
| --- | ---: | ---: | ---: | ---: | ---: |
| GPT Image 1 | 0.852 | 0.441 | 17.490 | 17.844 | -0.354 |
| GPT Image 2 | 0.657 | 0.507 | 5.094 | 5.159 | -0.065 |
| GPT Image 2.5 Flare | 0.574 | 0.543 | 0.871 | 1.585 | -0.715 |
| GPT Image 2.5 Sunburst | 0.717 | 0.556 | 4.500 | 4.997 | -0.498 |
| Nano Banana 2 | 0.747 | 0.248 | 7.423 | 7.013 | 0.410 |
| FLUX.2 Max | 0.860 | 0.646 | 10.529 | 10.176 | 0.353 |

## CLIP

| Configuration | N/(N+B) | faithful | prototype faithful | cosine(c, t) | gain | gain shared | accuracy | D |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 1 | 0.761 | 0.861 | 0.713 | 0.742 | 0.0716 | 0.745 | 0.607 | 0.847 |
| GPT Image 2 | 0.766 | 0.871 | 0.760 | 0.735 | 0.0996 | 0.732 | 0.688 | 1.061 |
| GPT Image 2.5 Flare | 0.817 | 0.887 | 0.771 | 0.681 | 0.0913 | 0.788 | 0.598 | 1.057 |
| GPT Image 2.5 Sunburst | 0.776 | 0.889 | 0.776 | 0.720 | 0.1015 | 0.777 | 0.589 | 1.136 |
| Nano Banana 2 | 0.823 | 0.912 | 0.829 | 0.713 | 0.1121 | 0.838 | 0.518 | 1.078 |
| FLUX.2 Max | 0.808 | 0.885 | 0.807 | 0.606 | 0.0830 | 0.817 | 0.411 | 1.058 |

## CSD

| Configuration | N/(N+B) | faithful | prototype faithful | cosine(c, t) | gain | gain shared | accuracy | D |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT Image 1 | 0.765 | 0.892 | 0.704 | 0.743 | 0.2167 | 0.727 | 0.723 | 0.735 |
| GPT Image 2 | 0.688 | 0.824 | 0.483 | 0.663 | 0.1659 | 0.542 | 0.759 | 0.741 |
| GPT Image 2.5 Flare | 0.746 | 0.864 | 0.627 | 0.656 | 0.1866 | 0.650 | 0.625 | 0.819 |
| GPT Image 2.5 Sunburst | 0.699 | 0.869 | 0.654 | 0.718 | 0.2142 | 0.674 | 0.616 | 0.944 |
| Nano Banana 2 | 0.774 | 0.897 | 0.757 | 0.701 | 0.2101 | 0.797 | 0.509 | 0.999 |
| FLUX.2 Max | 0.751 | 0.877 | 0.710 | 0.726 | 0.2167 | 0.776 | 0.393 | 0.714 |

## Readout stability (scene bootstrap, best-configuration frequency)

- hand31 d (lower is better): GPT Image 1 0.000, GPT Image 2 0.001, GPT Image 2.5 Flare 0.000, GPT Image 2.5 Sunburst 0.000, Nano Banana 2 0.153, FLUX.2 Max 0.847
- clip gain (higher is better): GPT Image 1 0.000, GPT Image 2 0.046, GPT Image 2.5 Flare 0.000, GPT Image 2.5 Sunburst 0.095, Nano Banana 2 0.858, FLUX.2 Max 0.002
- clip gain_shared_fraction (higher is better): GPT Image 1 0.000, GPT Image 2 0.000, GPT Image 2.5 Flare 0.000, GPT Image 2.5 Sunburst 0.000, Nano Banana 2 0.855, FLUX.2 Max 0.145
- clip accuracy (higher is better): GPT Image 1 0.008, GPT Image 2 0.987, GPT Image 2.5 Flare 0.000, GPT Image 2.5 Sunburst 0.006, Nano Banana 2 0.000, FLUX.2 Max 0.000
- clip d (lower is better): GPT Image 1 0.993, GPT Image 2 0.006, GPT Image 2.5 Flare 0.000, GPT Image 2.5 Sunburst 0.000, Nano Banana 2 0.001, FLUX.2 Max 0.000
- csd gain (higher is better): GPT Image 1 0.262, GPT Image 2 0.000, GPT Image 2.5 Flare 0.000, GPT Image 2.5 Sunburst 0.255, Nano Banana 2 0.148, FLUX.2 Max 0.336
- csd gain_shared_fraction (higher is better): GPT Image 1 0.000, GPT Image 2 0.000, GPT Image 2.5 Flare 0.000, GPT Image 2.5 Sunburst 0.000, Nano Banana 2 0.888, FLUX.2 Max 0.112
- csd accuracy (higher is better): GPT Image 1 0.196, GPT Image 2 0.804, GPT Image 2.5 Flare 0.000, GPT Image 2.5 Sunburst 0.000, Nano Banana 2 0.000, FLUX.2 Max 0.000
- csd d (lower is better): GPT Image 1 0.268, GPT Image 2 0.260, GPT Image 2.5 Flare 0.000, GPT Image 2.5 Sunburst 0.000, Nano Banana 2 0.000, FLUX.2 Max 0.472
