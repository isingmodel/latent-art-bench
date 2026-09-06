import json

import pytest

from latent_art_bench.io import hash_file, read_jsonl
from latent_art_bench.painter_distribution_study_v1 import recovery as p
from latent_art_bench.painter_distribution_study_v1 import recovery_results as r
from latent_art_bench.painter_distribution_study_v1 import study as s
from latent_art_bench.painter_distribution_study_v1 import transport as t
from latent_art_bench.painter_feature_generation_v2.artifacts import append_event, bindings, publish


def setup(root, monkeypatch, *, bad_authority=False, forbidden_duplicate=False):
    monkeypatch.setattr(p, "verify", lambda root: {})
    monkeypatch.setattr(
        p, "reserved_failure", lambda root, row: row["request_id"] == p.RECOVERY_SLOT
    )
    monkeypatch.setattr(
        p,
        "budget_state",
        lambda root: dict(
            attempts=4,
            paid_attempts=3,
            accounted_usd=5.14,
            provider_reported_usd=0.14,
            contingency_reserve_usd=5,
            missing_cost_failures=1,
            unresolved=0,
            uncertain=0,
        ),
    )
    publish(root / p.DIRECTORY / "execution_freeze.json", {})
    request_path = root / s.DIRECTORY / "requests.jsonl"
    request_path.parent.mkdir(parents=True)
    ids = ["slot0036", p.RECOVERY_SLOT, "slot0110"]
    request_path.write_text(
        "".join(
            json.dumps(dict(request_id=key, payload=dict(prompt="scene"))) + "\n" for key in ids
        )
    )
    for directory, key in zip(p.COMPONENTS, ids[:2]):
        append_event(
            root / directory / "slot_events.jsonl",
            dict(
                request_id=key,
                status="http_error",
                initial_status="http_error",
                selected_request_id=None,
                selected_response=None,
            ),
        )
    parent = append_event(
        root / p.predecessor.DIRECTORY / "generation_events.jsonl",
        dict(
            kind="terminal",
            request_id=p.RECOVERY_SLOT,
            route=s.ROUTES[1],
            status="http_error",
            complete=True,
            status_code=502,
            cost_usd=None,
        ),
    )
    child_dir = t.MANIFESTS / (p.RUN_ID + "-retry-" + p.RECOVERY_SLOT)
    child = append_event(
        root / child_dir / "generation_events.jsonl",
        dict(kind="terminal", request_id=p.RECOVERY_SLOT + "-retry1", status="image_returned"),
    )
    original = read_jsonl(request_path)[1]
    publish(
        root / child_dir / "retry_authority.json",
        dict(
            parent_run_id="wrong-parent" if bad_authority else p.predecessor.RUN_ID,
            predecessor_terminal_sha256=parent["event_sha256"],
            predecessor_terminal=parent,
            request=dict(
                original,
                request_id=p.RECOVERY_SLOT + "-retry1",
                predecessor_request_id=p.RECOVERY_SLOT,
            ),
            execution_freeze_sha256=hash_file(root / p.DIRECTORY / "execution_freeze.json"),
        ),
    )
    append_event(
        root / p.DIRECTORY / "slot_events.jsonl",
        dict(
            request_id=p.RECOVERY_SLOT,
            status="image_returned",
            initial_status="http_error",
            initial_terminal_sha256=parent["event_sha256"],
            retry_terminal_sha256=child["event_sha256"],
            selected_request_id=child["request_id"],
            selected_response=child,
        ),
    )
    append_event(
        root / p.DIRECTORY / "slot_events.jsonl",
        dict(
            request_id="slot0036" if forbidden_duplicate else "slot0110",
            status="image_returned",
            initial_status="image_returned",
            selected_request_id="slot0110",
            selected_response=dict(request_id="slot0110"),
        ),
    )
    for directory in (*p.COMPONENTS, p.DIRECTORY):
        paths = [directory / "slot_events.jsonl"]
        if directory == p.predecessor.DIRECTORY:
            paths.append(directory / "generation_events.jsonl")
        if directory == p.DIRECTORY:
            paths.extend(
                [child_dir / "generation_events.jsonl", child_dir / "retry_authority.json"]
            )
        publish(
            root / directory / "generation_receipt.json",
            dict(
                run_id=directory.name,
                status="completed" if directory == p.DIRECTORY else "stopped_for_diagnosis",
                terminal_slots=2 if directory == p.DIRECTORY else 1,
                outputs=bindings(root, paths),
            ),
        )


def test_combined_view_preserves_failure_and_applies_only_bound_retry(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch)
    before = hash_file(tmp_path / p.predecessor.DIRECTORY / "slot_events.jsonl")
    receipt = r.combine(tmp_path)
    assert receipt["terminal_slots"] == 3
    assert receipt["dispositions"] == dict(image_returned=2, http_error=1)
    assert [v["status"] for v in receipt["component_runs"]] == [
        "stopped_for_diagnosis",
        "stopped_for_diagnosis",
        "completed",
    ]
    images = r.inventory(tmp_path, "generated")
    assert [v["request_id"] for v in images] == [p.RECOVERY_SLOT, "slot0110"]
    assert not images[0]["initial_only_eligible"] and images[1]["initial_only_eligible"]
    assert before == hash_file(tmp_path / p.predecessor.DIRECTORY / "slot_events.jsonl")
    assert r.combine(tmp_path) == receipt


def test_retry_cannot_claim_a_different_parent_even_with_consistent_outer_hashes(
    tmp_path, monkeypatch
):
    setup(tmp_path, monkeypatch, bad_authority=True)
    with pytest.raises(ValueError, match="actual predecessor"):
        r.combine(tmp_path)


def test_no_successful_duplicate_can_replace_the_preserved_refusal(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, forbidden_duplicate=True)
    with pytest.raises(ValueError, match="unapproved duplicate"):
        r.combine(tmp_path)
