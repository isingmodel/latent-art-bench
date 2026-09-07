import json

import pytest

from latent_art_bench.io import hash_file
from latent_art_bench.painter_distribution_study_v1 import immediate as p
from latent_art_bench.painter_distribution_study_v1 import immediate_results as r
from latent_art_bench.painter_distribution_study_v1 import study as s
from latent_art_bench.painter_feature_generation_v2.artifacts import append_event, bindings, publish


def test_four_components_keep_previous_retry_and_reject_duplicates(tmp_path, monkeypatch):
    prior = [
        dict(
            request_id="old",
            status="image_returned",
            initial_status="http_error",
            selected_request_id="old-retry1",
            selected_response={},
        )
    ]
    monkeypatch.setattr(r.predecessor_results, "component_slots", lambda root: prior)
    monkeypatch.setattr(p, "verify", lambda root: {})
    monkeypatch.setattr(p, "budget_state", lambda root: dict(unresolved=0, uncertain=0))
    path = tmp_path / s.DIRECTORY / "requests.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("".join(json.dumps(dict(request_id=k)) + "\n" for k in ("old", "new")))
    ledger = tmp_path / p.DIRECTORY / "slot_events.jsonl"
    append_event(
        ledger,
        dict(
            request_id="new",
            status="image_returned",
            initial_status="image_returned",
            selected_request_id="new",
            selected_response={},
        ),
    )
    publish(tmp_path / p.DIRECTORY / "execution_freeze.json", {})
    for directory in (*p.COMPONENTS, p.DIRECTORY):
        publish(
            tmp_path / directory / "generation_receipt.json",
            dict(
                run_id=directory.name,
                status="completed" if directory == p.DIRECTORY else "closed",
                terminal_slots=1,
                outputs=bindings(tmp_path, [p.DIRECTORY / "slot_events.jsonl"])
                if directory == p.DIRECTORY
                else [],
            ),
        )
    before = hash_file(ledger)
    combined = r.combine(tmp_path)
    assert len(combined["component_runs"]) == 4 and combined["terminal_slots"] == 2
    assert r.inventory(tmp_path, "generated")[0]["initial_only_eligible"] is False
    assert r.combine(tmp_path) == combined and hash_file(ledger) == before
    append_event(ledger, dict(request_id="old", status="image_returned"))
    with pytest.raises(ValueError, match="must not repeat"):
        r.component_slots(tmp_path)


def test_selection_uses_only_unattempted_future_batches(tmp_path, monkeypatch):
    requests = [dict(request_id=f"slot{i:04d}", window=i // 126) for i in range(1008)]
    slots = [
        dict(row, status="http_error" if row["request_id"] == "slot0036" else "image_returned")
        for row in requests[:504]
    ]
    monkeypatch.setattr(p.predecessor_results, "component_slots", lambda root: slots)
    path = tmp_path / s.DIRECTORY / "requests.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in requests))
    publish(
        tmp_path / p.predecessor.DIRECTORY / "generation_receipt.json",
        dict(
            status="superseded_by_user_schedule_change",
            terminal_slots=405,
            unresolved_slot_ids=[],
            outputs=[],
        ),
    )
    assert p.remaining_requests(tmp_path) == requests[504:]
    slots[0]["request_id"] = "slot0900"
    with pytest.raises(ValueError, match="inventory differs"):
        p.remaining_requests(tmp_path)
