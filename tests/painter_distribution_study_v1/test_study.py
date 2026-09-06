from collections import Counter, defaultdict
from pathlib import Path

import pytest

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_study_v1 import study as s


def test_full_grid_has_shared_content_randomized_condition_positions_and_distinct_windows():
    config = read_json(Path.cwd() / s.CONFIG)
    rows = s.request_inventory(config)
    assert rows == s.request_inventory(config)
    assert len(rows) == 1008
    assert Counter(r["route"] for r in rows) == dict(zip(s.ROUTES, (288, 288, 432)))
    groups, windows = defaultdict(list), defaultdict(set)
    for row in rows:
        groups[row["route"], row["painter_id"], row["brief_id"], row["repetition"]].append(row)
        windows[row["route"], row["painter_id"], row["brief_id"]].add(row["window"])
    assert all(len(w) == 3 for w in windows.values())
    assert all(
        {r["condition"] for r in group} == set(s.conditions(key[0]))
        for key, group in groups.items()
    )
    for group in groups.values():
        before = next(r for r in group if r["condition"] == "artist_free")
        after = next(r for r in group if r["condition"] == "named")
        assert (
            after["payload"]["prompt"].replace(
                f" In the style of {s.PAINTER_NAMES[after['painter_id']]}.", ""
            )
            == before["payload"]["prompt"]
        )
    free = defaultdict(set)
    for row in rows:
        if row["condition"] == "artist_free":
            free[row["brief_id"]].add(row["payload"]["prompt"])
    assert all(len(prompts) == 1 for prompts in free.values())
    first_conditions = Counter(group[0]["condition"] for group in groups.values())
    assert (
        first_conditions["named"]
        and first_conditions["artist_free"]
        and first_conditions["generic_named"]
    )


def test_modified_caps_or_inventory_are_rejected():
    config = read_json(Path.cwd() / s.CONFIG)
    config["maximum_retry_attempts"] = 25
    with pytest.raises(ValueError, match="bounded design"):
        s.request_inventory(config)
