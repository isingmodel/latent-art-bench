import copy

import pytest

from latent_art_bench.painter_distribution_revision_v1.common import validate_rows
from latent_art_bench.painter_distribution_revision_v1.timing import group_records


def test_numeric_rows_reject_duplicates_and_nonfinite():
    row = dict(pipeline="primary512", image_id="work:one", status="measured",
               values=[0.0] * 31, scaled=[0.0] * 31)
    validate_rows([row], "test")
    with pytest.raises(ValueError, match="duplicate"):
        validate_rows([row, copy.deepcopy(row)], "test")
    row["scaled"][3] = float("nan")
    with pytest.raises(ValueError, match="invalid"):
        validate_rows([row], "test")


def test_boundary_membership_is_distinct_from_slow_same_component():
    requests, times = [], {}
    for brief, components, gap in (("one", ("a", "b"), 20), ("two", ("b", "b"), 150)):
        for i, condition in enumerate(("named", "artist_free")):
            key = f"{brief}{i}"
            requests.append(dict(route="test", painter_id="painter", brief_id=brief,
                                 repetition=0, request_id=key, condition=condition))
            seconds = i * gap
            times[key] = dict(started_at_utc=f"2026-09-07T00:{seconds//60:02d}:"
                                            f"{seconds%60:02d}+00:00",
                              component=components[i])
    result = group_records(requests, times)
    assert result[0]["crosses_component"] and not result[0]["gap_above_120_seconds"]
    assert not result[1]["crosses_component"] and result[1]["gap_above_120_seconds"]
    assert result[0]["condition_order"] == ["named", "artist_free"]
