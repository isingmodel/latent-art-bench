import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from latent_art_bench.io import stable_hash
from latent_art_bench.painter_feature_generation_v1.panel import ID_NAME_PAIRS
from latent_art_bench.painter_prompt_study_v1 import prompts

ROOT = Path(__file__).resolve().parents[2]


def _source():
    return json.loads((ROOT / prompts.SOURCE_PATH).read_bytes())


def _write_source(root, source):
    path = root / prompts.SOURCE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(source, ensure_ascii=False), encoding="utf-8")


def test_original_baseline_remains_byte_exact_in_every_cell():
    source = _source()
    library = prompts.build_library(ROOT)
    baseline = [row for row in library["prompts"] if row["method_id"] == "by_name"]
    assert len(baseline) == 80
    lookup = {row["template_id"]: row for row in source["templates"]}
    for row in baseline:
        template = lookup[row["template_id"]]
        if row["condition"] == "artist_free":
            expected, expected_hash = template["artist_free_prompt"], template["artist_free_sha256"]
        else:
            named = template["named_prompts"][row["condition"]]
            expected, expected_hash = named["prompt"], named["sha256"]
        assert row["prompt"].encode("utf-8") == expected.encode("utf-8")
        assert row["prompt_sha256"] == expected_hash
        assert row["scene_group"] == template["scene_group"]


def test_new_treatments_keep_every_scene_with_exact_matched_control_wording():
    library = prompts.build_library(ROOT)
    lookup = {row["template_id"]: row["artist_free_prompt"] for row in _source()["templates"]}
    names = dict(ID_NAME_PAIRS)
    expected_aspects = (
        " Attend to color relationships, the organization of forms, and the handling of painted"
        " marks; retain the stated scene."
    )
    for row in library["prompts"]:
        if row["method_id"] == "by_name":
            continue
        condition = row["condition"]
        suffix = (
            " Render this scene in a coherent painting style."
            if condition == "artist_free"
            else f" Render this scene in the painting style of {names[condition]}."
        )
        expected = lookup[row["template_id"]] + suffix
        if row["method_id"] == "style_aspects":
            expected += expected_aspects
        assert row["prompt"] == expected
        mentioned = [p for p, n in ID_NAME_PAIRS if n in row["prompt"]]
        assert mentioned == ([] if condition == "artist_free" else [condition])


def test_three_method_grid_is_complete_distinct_and_deterministic(tmp_path):
    library = prompts.build_library(ROOT)
    records = library["prompts"]
    assert library["method_ids"] == ["by_name", "style_instruction", "style_aspects"]
    assert len(records) == len({row["prompt"] for row in records}) == 240
    assert {(r["method_id"], r["condition"], r["template_id"]) for r in records} == {
        (method, condition, template)
        for method in prompts.METHOD_IDS
        for condition in prompts.CONDITIONS
        for template in prompts.TEMPLATE_IDS
    }
    assert set(Counter((r["method_id"], r["condition"]) for r in records).values()) == {16}
    for row in records:
        assert row["prompt_sha256"] == hashlib.sha256(row["prompt"].encode("utf-8")).hexdigest()
    assert library["strings_sha256"] == stable_hash([row["prompt"] for row in records])
    assert library == prompts.build_library(ROOT)
    _write_source(tmp_path, _source())
    copied = prompts.build_library(tmp_path)
    assert copied["prompts"] == records
    assert copied["strings_sha256"] == library["strings_sha256"]
    assert copied["source"]["sha256"] != library["source"]["sha256"]  # Exact source bytes bound.
    assert copied["source"]["path"] == prompts.SOURCE_PATH.as_posix()
    assert not Path(copied["source"]["path"]).is_absolute()
    assert "already exposed" in library["exposure_disclosure"]
    assert all(row["control_rationale"] for row in library["methods"])


@pytest.mark.parametrize("fault", [
    "missing_template", "reordered_templates", "scene_group", "missing_painter",
    "artist_free_hash", "named_hash", "rewritten_named_prompt", "complete_strings_hash",
])
def test_source_integrity_failure_prevents_prompt_construction(tmp_path, fault):
    source = _source()
    template = source["templates"][0]
    named = template["named_prompts"][prompts.CONDITIONS[0]]
    if fault == "missing_template":
        source["templates"].pop()
    elif fault == "reordered_templates":
        source["templates"].reverse()
    elif fault == "scene_group":
        template["scene_group"] = "route_organized"
    elif fault == "missing_painter":
        template["named_prompts"].pop(prompts.CONDITIONS[0])
    elif fault == "artist_free_hash":
        template["artist_free_sha256"] = "incorrect"
    elif fault == "named_hash":
        named["sha256"] = "incorrect"
    elif fault == "rewritten_named_prompt":
        named["prompt"] += " Bright blue sky."
        named["sha256"] = hashlib.sha256(named["prompt"].encode("utf-8")).hexdigest()
    else:
        source["strings_sha256"] = "incorrect"
    _write_source(tmp_path, source)
    with pytest.raises(ValueError):
        prompts.build_library(tmp_path)
