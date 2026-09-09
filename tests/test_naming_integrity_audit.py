"""Artificial metadata fixtures only; no live or retained outcome access."""

import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "naming_integrity_audit", Path(__file__).parents[1] / "tools/audit_naming_replication.py"
)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_duplicate_hashes_count_physical_returns_and_cross_cohorts():
    images = [dict(request_id="a", image_sha256="same"),
              dict(request_id="b", image_sha256="same"),
              dict(request_id="c", image_sha256="different")]
    old = {"study1": [dict(image_id="old", image_sha256="same")],
           "study2": [dict(image_id="old2", image_sha256="other")]}
    result = audit.duplicates(images, old)
    assert result["compared_images"] == 3 and result["unique_hash_and_shape_keys"] == 2
    assert len(result["within_new_duplicate_groups"]) == 1
    assert result["cross_cohort"]["study1"]["matched_new_images"] == 2
    assert result["cross_cohort"]["study2"]["matched_new_images"] == 0


def test_normalized_array_duplicates_require_both_hash_and_shape():
    common = dict(normalized_sha256="same", normalized_width=512, normalized_height=626)
    images = [dict(request_id="a", **common), dict(request_id="b", **common),
              dict(request_id="c", normalized_sha256="same",
                   normalized_width=626, normalized_height=512)]
    old = {"study1": [dict(image_id="old", **common)]}
    result = audit.duplicates(images, old, normalized=True)
    assert result["compared_images"] == 3 and result["unique_hash_and_shape_keys"] == 2
    assert result["cross_cohort"]["study1"]["matched_new_images"] == 2
    assert len(result["within_new_duplicate_groups"]) == 1


def test_complete_delivery_profiles_keep_requested_absence_and_reported_quality():
    requests = [dict(request_id="a", experiment="palette", arm="free", polarity="muted",
                     payload=dict(size="1024x1024", quality="medium")),
                dict(request_id="b", experiment="palette", arm="free", polarity="vivid",
                     payload=dict(size="1024x1024", quality="medium")),
                dict(request_id="c", experiment="naming", arm="free", polarity=None,
                     payload=dict(aspect_ratio="1:1"))]
    slots = [dict(request_id="a", status="image_returned", observed=dict(
        width=1387, height=1134, format="PNG", mode="RGB", reported=dict(quality="low"))),
        dict(request_id="b", status="refused", observed=None),
        dict(request_id="c", status="image_returned", observed=dict(
            width=1024, height=1024, format="PNG", mode="RGB", reported=dict(quality=None)))]
    result = audit.delivery_counts(requests, slots)
    naming, palette = result
    assert naming["profiles"][0]["requested"]["quality"] is None
    assert "quality" not in naming["profiles"][0]["requested_fields_present"]
    assert palette["planned"] == 2 and len(palette["profiles"]) == 2
    success = next(r for r in palette["profiles"] if r["status"] == "image_returned")
    assert success["requested"]["quality"] == "medium"
    assert success["reported"]["quality"] == "low"
    assert success["decoded"]["width"] == 1387
    assert next(r for r in palette["profiles"] if r["status"] == "refused")["reported"] is None


def timeline(starts, ends, tickets=None):
    tickets = tickets or list(range(len(starts)))
    base = datetime(2026, 9, 10, tzinfo=UTC)
    ledger = []
    for i, (start, end) in enumerate(zip(starts, ends, strict=True)):
        identity = dict(request_id=str(i), attempt=1, slot_sequence=i, route="route")
        ledger.append((start, dict(identity, kind="attempt", dispatch_ticket=tickets[i])))
        stamp = (base + timedelta(seconds=start)).isoformat()
        ledger.append((end, dict(identity, kind="terminal", post_started=True,
                                  transport_started_monotonic=start,
                                  latency_seconds=end - start, status="image_returned",
                                  post_started_at_utc=stamp)))
    # Completions before new admission if times happen to coincide.
    return [r for _, r in sorted(ledger, key=lambda x: (x[0], x[1]["kind"] == "attempt"))]


CONFIG = dict(minimum_start_interval_seconds=5, maximum_in_flight=2)
RECEIPT = dict(elapsed_seconds=100, duration_contract_met=True,
               ended_at_utc="2026-09-10T00:01:40+00:00")


def test_time_uses_actual_admission_not_ledger_completion_order():
    result = audit.timing_summary(timeline([0, 5, 10], [9, 8, 12]), CONFIG, RECEIPT)
    assert result["admitted_start_spacing_seconds"]["minimum"] == 5
    assert result["maximum_timed_operations"] == 2
    assert result["maximum_outstanding_ledger_intents"] == 2
    assert result["dispatch_ticket_order_preserved"]
    assert not result["spacing_below_configured_minimum"]


def test_timing_reports_spacing_order_concurrency_without_filtering():
    result = audit.timing_summary(timeline([0, 4, 6], [20, 20, 20], [1, 0, 2]), CONFIG, RECEIPT)
    assert len(result["spacing_below_configured_minimum"]) == 2
    assert not result["dispatch_ticket_order_preserved"]
    assert result["maximum_timed_operations"] == 3
    assert result["timed_posts"] == 3


def test_cancelled_and_unknown_posts_never_receive_invented_timing():
    ledger = [dict(kind="attempt", request_id="a", attempt=1, dispatch_ticket=0),
              dict(kind="terminal", request_id="a", attempt=1, post_started=False),
              dict(kind="attempt", request_id="b", attempt=1, dispatch_ticket=1),
              dict(kind="terminal", request_id="b", attempt=1, status="outcome_uncertain")]
    result = audit.timing_summary(ledger, CONFIG, RECEIPT)
    assert result["timed_posts"] == 0
    assert len(result["cancelled_before_post"]) == len(result["missing_timing"]) == 1
    assert result["admitted_start_spacing_seconds"]["minimum"] is None
    assert result["dispatch_ticket_order_preserved"] is None
    assert not result["timing_complete"]


def test_two_receipts_required_before_any_new_outcome_reader(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("new outcome reader was called before receipts")

    monkeypatch.setattr(audit.workflow, "collection_inputs", forbidden)
    with pytest.raises(ValueError, match="both terminal"):
        audit.audit(tmp_path)
    directory = tmp_path / audit.common.directory(audit.common.RUN_ID)
    directory.mkdir(parents=True)
    (directory / "collection_receipt.json").write_text("{}")
    with pytest.raises(ValueError, match="both terminal"):
        audit.audit(tmp_path)
