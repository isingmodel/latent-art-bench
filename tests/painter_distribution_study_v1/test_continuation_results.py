import json

import pytest

from latent_art_bench.painter_distribution_study_v1 import continuation as p
from latent_art_bench.painter_distribution_study_v1 import continuation_results as r
from latent_art_bench.painter_distribution_study_v1 import parallel_collection as predecessor
from latent_art_bench.painter_distribution_study_v1 import study as s
from latent_art_bench.painter_feature_generation_v2.artifacts import append_event, bindings, publish


def setup(tmp_path, monkeypatch, *, duplicate=False):
    monkeypatch.setattr(p, "verify", lambda root: {})
    publish(tmp_path / p.DIRECTORY / "execution_freeze.json", {})
    path = tmp_path / s.DIRECTORY / "requests.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("".join(json.dumps(dict(request_id=f"slot{i}")) + "\n" for i in range(3)))
    for directory, rows in [
        (predecessor.DIRECTORY, [(0, "image_returned"), (2, "http_error")]),
        (p.DIRECTORY, [(0 if duplicate else 1, "image_returned")]),
    ]:
        for i, status in rows:
            append_event(
                tmp_path / directory / "slot_events.jsonl",
                dict(
                    request_id=f"slot{i}",
                    status=status,
                    initial_status=status,
                    selected_request_id=f"slot{i}" if status == "image_returned" else None,
                    selected_response=dict(request_id=f"slot{i}")
                    if status == "image_returned"
                    else None,
                ),
            )
        publish(
            tmp_path / directory / "generation_receipt.json",
            dict(
                run_id=directory.name,
                status="completed" if directory == p.DIRECTORY else "stopped_for_diagnosis",
                terminal_slots=len(rows),
                outputs=bindings(tmp_path, [directory / "slot_events.jsonl"]),
            ),
        )


def test_combined_view_preserves_refusal_and_frozen_inventory_order(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    receipt = r.combine(tmp_path)
    assert receipt["terminal_slots"] == 3
    assert receipt["dispositions"] == dict(image_returned=2, http_error=1)
    assert receipt["component_runs"][0]["status"] == "stopped_for_diagnosis"
    assert [row["request_id"] for row in r.inventory(tmp_path, "generated")] == ["slot0", "slot1"]
    assert r.combine(tmp_path) == receipt


def test_combined_view_rejects_duplicate_slots_instead_of_selecting_a_success(
    tmp_path, monkeypatch
):
    setup(tmp_path, monkeypatch, duplicate=True)
    with pytest.raises(ValueError, match="exact original inventory once"):
        r.combine(tmp_path)
