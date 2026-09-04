from __future__ import annotations

import json
from pathlib import Path

from latent_art_bench.painter_feature_generation_v1 import scene_prescreen as sp

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_protocol_2_1_floor_arithmetic() -> None:
    floor = sp.per_painter_floor_2_1()
    assert floor["confirmation_works_needed_per_painter"] == 100
    assert floor["eligible_for_development_floor"] == 50
    assert floor["eligible_for_confirmation_and_ess_floor"] == 167
    assert floor["eligible_per_painter_primary"] == 167
    assert floor["eligible_per_painter_total"] == 179


def test_protocol_2_0_floor_arithmetic_is_kept_for_the_record() -> None:
    three = sp.per_cell_eligible_floor(3)
    four = sp.per_cell_eligible_floor(4)
    assert three["confirmation_works_needed_per_cell"] == 34
    assert three["eligible_per_cell"] == 57
    assert four["eligible_per_cell"] == 50
    totals = sp.floors()["protocol_2_0_by_retained_groups"]
    assert totals["G=3"]["eligible_per_painter_total"] == 3 * 57 + 12
    assert totals["G=4"]["eligible_per_painter_total"] == 4 * 50 + 12


def test_prescreen_runs_on_the_repository_manifests() -> None:
    result = sp.run(REPOSITORY_ROOT)
    assert result["protocol_id"] == "painter-feature-generation-v1/2.1"
    painters = result["broad_media_r2"]["per_painter"]
    assert set(painters) == set(sp.PAINTERS)
    assert painters["claude_monet"]["gate_pass_rows"] == 725
    assert painters["alfred_sisley"]["gate_pass_distinct_items"] == 287
    for bucket in painters.values():
        assert sum(bucket["disposition"].values()) == bucket["gate_pass_distinct_items"]
        assert bucket["eligible_with_collection_qid"] <= bucket["disposition"].get(
            "eligible_outdoor_place", 0
        )
    assert result["aic_r2"]["per_painter"]["claude_monet"]["screened_candidates"] == 33
    evaluation = result["evaluation_2_1"]
    assert set(evaluation["per_painter"]) == set(sp.PAINTERS)
    assert all(
        row["floor_including_auxiliary"] == 179 for row in evaluation["per_painter"].values()
    )
    tracked = json.loads((REPOSITORY_ROOT / sp.OUTPUT_JSON).read_text(encoding="utf-8"))
    assert tracked["evaluation_2_1"] == evaluation
    assert tracked["retention_under_2_0"] == result["retention_under_2_0"]
