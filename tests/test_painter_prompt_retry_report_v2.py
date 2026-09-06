"""All model rows must share family bounds that include every data point."""

import pytest

from latent_art_bench import painter_prompt_retry_report_v2 as report


@pytest.mark.parametrize("larger_alias", report.retry.generation.ALIASES)
def test_shared_axes_include_larger_values_in_either_alias(larger_alias):
    data = {
        "absolute": [
            dict(
                alias=a,
                method_id=m,
                painter_id=p,
                family=f,
                distance=10 if a == larger_alias else 0.1,
            )
            for a in report.retry.generation.ALIASES
            for m in report.retry.METHOD_IDS
            for p in report.retry.PAINTER_IDS
            for f in report.retry.features.FAMILIES
        ]
    }
    fig = report.figure(data)
    try:
        for ax in fig.axes:
            low, high = ax.get_xlim()
            assert high == pytest.approx(10.8)
            for collection in ax.collections:
                assert all(low < x < high for x in collection.get_offsets()[:, 0])
    finally:
        report.retry.plt.close(fig)
