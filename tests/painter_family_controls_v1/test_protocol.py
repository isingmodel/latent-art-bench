"""Exact-design and fail-closed checks; never contacts a service."""

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from latent_art_bench.painter_family_controls_v1 import preflight
from latent_art_bench.painter_family_controls_v1 import protocol as p

START = "2026-10-01T00:00:00+00:00"  # Synthetic fixture; not a scheduled collection.


def test_complete_balanced_panel_and_exact_cell_census():
    rows = p.assignments(START)
    assert len(rows) == 4608 == len({r["id"] for r in rows})
    assert len({(r["model"], r["session"], r["scene"], r["arm"]) for r in rows}) == 4608
    assert Counter(r["model"] for r in rows) == dict.fromkeys(p.MODELS, 768)
    assert Counter(r["arm"] for r in rows) == dict.fromkeys(p.ARMS, 576)
    assert Counter(r["session"] for r in rows) == dict.fromkeys(range(8), 576)
    assert Counter(r["scene_id"][0] for r in rows) == dict.fromkeys("WBLM", 1152)
    p.verify_assignments(rows, START)


def test_global_interleaving_and_deterministic_order():
    rows = p.assignments(START)
    assert rows == p.assignments("2026-10-01T09:00:00+09:00")
    for session in range(8):
        group = rows[session * 576:(session + 1) * 576]
        assert [r["session_order"] for r in group] == list(range(576))
        assert len({r["model"] for r in group[:20]}) > 1
        assert len({r["scene"] for r in group[:20]}) > 1
        assert len({r["arm"] for r in group[:20]}) > 1
        begin = datetime.fromisoformat(group[0]["window_start"])
        end = datetime.fromisoformat(group[0]["window_end"])
        assert (end - begin).total_seconds() == 4 * 3600
        assert (begin - datetime.fromisoformat(START)).total_seconds() == (
            p.SESSION_OFFSETS_HOURS[session] * 3600)


@pytest.mark.parametrize("mutation", ["drop", "duplicate", "swap", "payload", "window",
                                     "boolean_for_integer", "float_for_integer"])
def test_membership_order_payload_and_window_changes_are_rejected(mutation):
    rows = p.assignments(START)
    if mutation == "drop":
        rows.pop()
    elif mutation == "duplicate":
        rows[-1] = rows[0]
    elif mutation == "swap":
        rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "payload":
        rows[0]["payload"]["prompt"] += " better art"
    elif mutation == "boolean_for_integer":
        rows[0]["payload"]["n"] = True
    elif mutation == "float_for_integer":
        rows[0]["session"] = float(rows[0]["session"])
    else:
        rows[0]["window_end"] = rows[0]["window_start"]
    with pytest.raises(ValueError, match="changed"):
        p.verify_assignments(rows, START)


def test_exact_proposal_text_and_historical_route_contract():
    proposal = (Path(__file__).resolve().parents[2]
                / "reports/icml_review_v1/prospective_controls_v2.md").read_text()
    for _, scene in p.SCENES:
        assert scene in proposal
    for suffix in p.SUFFIXES.values():
        assert suffix in proposal
    for model in p.MODELS:
        for arm in p.ARMS:
            payload = p.payload(model, 0, arm)
            assert payload["prompt"] == p.SCENES[0][1] + " " + p.SUFFIXES[arm]
            assert payload["n"] == 1 and payload["aspect_ratio"] == "1:1"
            assert payload["provider"]["allow_fallbacks"] is False
            assert len(payload["provider"]["only"]) == 1
            assert "seed" not in payload and "image" not in payload
        if model.startswith("gpt-image"):
            assert payload["model"] == "openai/" + model
            assert payload["quality"] == "medium" and payload["background"] == "opaque"
        elif model.startswith("google/"):
            assert payload["resolution"] == "1K"
        else:
            assert payload["output_format"] == "png"


@pytest.mark.parametrize("bad", ["2026-10-01", datetime(2026, 10, 1),
                               "2026-10-01T00:00:00.1Z", "bad"])
def test_ambiguous_or_fractional_start_rejected(bad):
    with pytest.raises(ValueError):
        p.assignments(bad)


def test_timezone_normalized_without_changing_instant():
    assert p.utc_datetime("2026-10-01T09:00:00+09:00") == datetime(
        2026, 10, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize("free,capacity,floor", [(0, False, False),
        (5 * 1024**3, False, True), (40 * 1024**3 - 1, False, True),
        (40 * 1024**3, True, True)])
def test_real_byte_thresholds_not_nominal_capacity(tmp_path, free, capacity, floor):
    result = preflight.storage_status(tmp_path / "does-not-exist",
                                      disk_usage=lambda _: SimpleNamespace(free=free))
    assert result["meets_initial_capacity"] is capacity
    assert result["meets_idle_collector_floor"] is floor
    assert not (tmp_path / "does-not-exist").exists()


def test_file_destination_is_rejected(tmp_path):
    path = tmp_path / "file"
    path.write_text("not a directory")
    with pytest.raises(ValueError, match="directory"):
        preflight.storage_status(path)


def test_proposal_is_not_authorization():
    record = p.design_record()
    assert record["current_approved_cumulative_ceiling_usd"] == "120"
    assert record["proposed_unapproved_ceiling_usd"] == "350"
    assert record["network_transport_available"] is False
    assert "draft" in record["status"]


def test_preflight_remains_blocked_even_with_a_proposed_time(tmp_path):
    result = preflight.inspect(tmp_path, START)
    assert result["ready_for_live_collection"] is False
    assert result["historical_terminal_record_intact"] is True
    assert any("not authorized" in r for r in result["unresolved"])
    assert any("no live transport" in r for r in result["unresolved"])
