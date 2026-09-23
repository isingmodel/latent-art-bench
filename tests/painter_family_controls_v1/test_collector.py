"""Constructed offline qualification: no credentials, service calls, or new data."""

import base64
import gzip
import io
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from PIL import Image

from latent_art_bench.painter_family_controls_v1 import collector as c

T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)


def at(seconds=0):
    return T0 + timedelta(seconds=seconds)


def slots(count=4):
    return [dict(id=f"slot-{i}", model="mock/model", provider="mock-provider", session=0,
                 scene=f"scene-{i}", arm="generic", window_start=T0.isoformat(),
                 window_end=(T0 + timedelta(hours=4)).isoformat(),
                 payload={"model": "mock/model", "provider": {"only": ["mock-provider"],
                                                              "allow_fallbacks": False},
                          "prompt": "fixed exact fixture"}) for i in range(count)]


@pytest.fixture(scope="module")
def png():
    stream = io.BytesIO()
    Image.new("RGB", (1024, 1024), "white").save(stream, format="PNG")
    return stream.getvalue()


def response(png=None, *, status=200, cost="0.05", code=None, **extra):
    value = {}
    if cost is not None:
        value["usage"] = {"cost": cost}
    if png is not None:
        value["data"] = [{"b64_json": base64.b64encode(png).decode()}]
    if code is not None:
        value["error"] = {"code": code}
    value.update(extra)
    return c.MockResponse(status, json.dumps(value).encode())


def engine(tmp_path, *, count=4, ceiling="350", **kwargs):
    return c.Collector(tmp_path, slots(count), simulation=True,
                       policy=c.CollectorPolicy(Decimal(ceiling)),
                       free_bytes=kwargs.pop("free_bytes", lambda _: 50 * c.GIB), **kwargs)


def complete(run, index, fixture, start=0, end=None):
    intent = run.start(f"slot-{index}", at(start))
    return run.finish(intent["attempt_id"], fixture, at(start + 1 if end is None else end))


def test_default_denies_and_current_ceiling_never_becomes_proposal(tmp_path):
    with c.Collector(tmp_path, slots(), free_bytes=lambda _: 50 * c.GIB) as run:
        assert run.policy.cumulative_ceiling_usd == Decimal("120")
        assert run.accounted_usd == Decimal("112.293676")
        with pytest.raises(c.AdmissionDenied, match="default deny"):
            run.start("slot-0", T0)
        assert not run.events
    with pytest.raises(c.CollectorError, match="offline simulation"):
        c.Collector(tmp_path / "other", slots(), policy=c.CollectorPolicy(Decimal("350")))


def test_current_budget_allows_only_one_reservation_and_strict_boundary(tmp_path):
    with engine(tmp_path / "current", ceiling="120") as run:
        run.start("slot-0", at())
        assert run.accounted_usd == Decimal("117.293676")
        with pytest.raises(c.AdmissionDenied, match="cumulative ceiling"):
            run.start("slot-1", at(5))
    with engine(tmp_path / "boundary", ceiling="117.293676") as run:
        with pytest.raises(c.AdmissionDenied, match="strictly below"):
            run.start("slot-0", at())
    with pytest.raises(ValueError, match="exact decimal"):
        c.CollectorPolicy(120.0)


def test_start_window_spacing_concurrency_and_late_drain(tmp_path, png):
    with engine(tmp_path) as run:
        with pytest.raises(c.AdmissionDenied, match="outside assigned"):
            run.start("slot-0", at(-1))
        first = run.start("slot-0", at(14389))
        with pytest.raises(c.AdmissionDenied, match="five seconds"):
            run.start("slot-1", at(14393))
        second = run.start("slot-1", at(14394))
        third = run.start("slot-2", at(14399))
        with pytest.raises(c.AdmissionDenied, match="three active"):
            run.start("slot-3", at(14404))
        late = run.finish(first["attempt_id"], response(png), at(14500))
        assert late["success"] and late["session"] == 0
        assert late["window_end"] == "2030-01-01T04:00:00Z"
        run.finish(second["attempt_id"], response(png), at(14501))
        run.finish(third["attempt_id"], response(png), at(14502))
        with pytest.raises(c.AdmissionDenied, match="outside assigned"):
            run.start("slot-3", at(14503))
        receipt = run.close_terminal(at(14504))
        assert receipt["status"] == "incomplete" and receipt["successful"] == 3
        assert receipt["census"][-1]["state"] == "unstarted_window_expired"


def test_single_owner_persistent_lock_and_unclosed_start_recovery(tmp_path):
    with engine(tmp_path) as run:
        run.start("slot-0", at())
        with pytest.raises(c.AlreadyOwned):
            engine(tmp_path)
    assert (tmp_path / "collector.lock").exists()
    with engine(tmp_path) as recovered:
        assert recovered.outstanding_count == 1
        assert recovered.accounted_usd == Decimal("117.293676")
        assert recovered.pauses
        with pytest.raises(c.AdmissionDenied, match="paused"):
            recovered.start("slot-1", at(100))
        with pytest.raises(c.CollectorError, match="this owner"):
            recovered.finish("slot-0-a1", response(status=429), at(101))
        receipt = recovered.close_terminal(at(14401))
        assert receipt["outstanding_reservations_usd"] == "5"
        assert receipt["census"][0]["state"] == "unclosed_intent_requires_reconciliation"


@pytest.mark.parametrize("status", [429, 500, 400, None])
def test_unknown_error_charge_stays_reserved_never_zero_or_auto_retry(tmp_path, status):
    with engine(tmp_path) as run:
        result = complete(run, 0, response(status=status, cost=None, code="error"))
        assert result["cost_usd"] is None and not result["retryable"]
        assert run.accounted_usd == Decimal("117.293676")
    with engine(tmp_path) as recovered:
        assert recovered.outstanding_count == 1
        assert recovered.accounted_usd == Decimal("117.293676")
        assert recovered.select(at(100)) is None
        assert "unknown_charge" in recovered.close_terminal(at(101))["census"][0]["state"]


def test_known_zero_requires_evidence_and_retry_delays_survive_recovery(tmp_path):
    fixture = response(status=429, cost="0", code="rate_limit")
    with engine(tmp_path) as run:
        result = complete(run, 0, fixture)
        assert result["retryable"] and result["cost_usd"] == "0"
        assert run.outstanding_count == 0
    with engine(tmp_path) as recovered:
        assert not recovered.pauses
        with pytest.raises(c.AdmissionDenied, match="20-second"):
            recovered.start("slot-0", at(20))
        second = recovered.start("slot-0", at(21))
        recovered.finish(second["attempt_id"], fixture, at(22))
        with pytest.raises(c.AdmissionDenied, match="60-second"):
            recovered.start("slot-0", at(81))
        third = recovered.start("slot-0", at(82))
        last = recovered.finish(third["attempt_id"], fixture, at(83))
        assert "three consecutive technical failures" in last["pause_reasons"]
        with pytest.raises(c.AdmissionDenied, match="two retries"):
            recovered.start("slot-0", at(150))


def test_retry_cannot_cross_assigned_window(tmp_path):
    with engine(tmp_path) as run:
        complete(run, 0, response(status=503, cost="0"), start=14390)
        with pytest.raises(c.AdmissionDenied, match="outside assigned"):
            run.start("slot-0", at(14411))


def test_global_retry_cap_is_96_with_successes_resetting_failure_streak(tmp_path, png):
    with engine(tmp_path, count=50) as run:
        failure = response(status=502, cost="0")
        for index in range(48):
            start = index * 90
            complete(run, index, failure, start=start)
            complete(run, index, failure, start=start + 21)
            complete(run, index, response(png, cost="0"), start=start + 82)
        assert sum(e["attempt"] > 1 for e in run.starts.values()) == 96
        complete(run, 48, failure, start=4320)
        with pytest.raises(c.AdmissionDenied, match="96 global retries"):
            run.start("slot-48", at(4341))
        assert not run.pauses


@pytest.mark.parametrize("status", [200, 400, 429, 500])
def test_content_refusals_never_retry(tmp_path, status):
    with engine(tmp_path) as run:
        result = complete(run, 0, response(status=status, cost="0",
                                           code="content_policy_violation"))
        assert result["refusal"] and not result["retryable"] and not result["success"]
        assert not run.pauses
        with pytest.raises(c.AdmissionDenied, match="not eligible"):
            run.start("slot-0", at(100))


def test_greater_than_reservation_pauses_and_settles_exactly(tmp_path):
    with engine(tmp_path) as run:
        result = complete(run, 0, response(status=429, cost="5.000001"))
        assert result["cost_usd"] == "5.000001"
        assert run.accounted_usd == Decimal("117.293677")
        assert "charge exceeds five-dollar reservation" in result["pause_reasons"]


def test_new_settled_operating_stop_only_reachable_under_simulated_ceiling(tmp_path):
    with engine(tmp_path, count=45) as run:
        for index in range(44):
            complete(run, index, response(status=400, cost="5", code="content_filter"),
                     start=index * 5)
        assert run.new_settled_usd == Decimal("220")
        assert run.accounted_usd == Decimal("332.293676")
        with pytest.raises(c.AdmissionDenied, match="operating stop"):
            run.start("slot-44", at(220))


@pytest.mark.parametrize("free", [0, 5 * c.GIB, 5 * c.GIB + 256 * c.MIB - 1])
def test_actual_free_bytes_required_not_nominal_capacity(tmp_path, free):
    with engine(tmp_path, free_bytes=lambda _: free) as run:
        with pytest.raises(c.AdmissionDenied, match="actual free bytes"):
            run.start("slot-0", at())
        assert not run.starts


def test_every_write_volume_and_active_storage_reservation(tmp_path):
    extra = tmp_path / "another-volume"
    extra.mkdir()
    queried = []

    def disk(path):
        queried.append(path)
        return 0 if path == extra else 50 * c.GIB

    with engine(tmp_path / "run", free_bytes=disk, write_volumes=[extra]) as run:
        assert any(str(extra) in reason for reason in run.admission("slot-0", at()))
        assert extra in queried and run.root in queried
    free = 5 * c.GIB + 256 * c.MIB
    with engine(tmp_path / "active", free_bytes=lambda _: free) as run:
        run.start("slot-0", at())
        with pytest.raises(c.AdmissionDenied, match="actual free bytes"):
            run.start("slot-1", at(5))


def test_original_bytes_mime_gzip_and_fsync_are_retained(tmp_path, png, monkeypatch):
    calls = []
    original_fsync = os.fsync

    def synced(fd):
        calls.append(fd)
        return original_fsync(fd)

    monkeypatch.setattr(c.os, "fsync", synced)
    with engine(tmp_path) as run:
        fixture = response(png)
        intent = run.start("slot-0", at())
        assert json.loads(run.ledger.read_text().splitlines()[0])["kind"] == "start"
        assert calls
        result = run.finish(intent["attempt_id"], fixture, at(1))
        assert result["success"] and result["reported"] == {"model": None, "provider": None}
        assert gzip.decompress((tmp_path / result["response"]["path"]).read_bytes()) == fixture.body
        image = result["images"][0]
        assert image["mime"] == "image/png" and image["width"] == image["height"] == 1024
        assert (tmp_path / image["path"]).read_bytes() == png
        assert len(calls) >= 8


@pytest.mark.parametrize("field,echo", [("model", "other/model"), ("provider", "other")])
def test_contradictory_echo_preserves_images_then_pauses(tmp_path, png, field, echo):
    with engine(tmp_path) as run:
        result = complete(run, 0, response(png, **{field: echo}))
        assert result["response"] and result["images"] and not result["success"]
        assert f"contradictory echoed {field}" in run.pauses


def test_wrong_geometry_and_count_preserved_without_replacement(tmp_path, png):
    stream = io.BytesIO()
    Image.new("RGB", (512, 256)).save(stream, format="JPEG")
    data = [{"b64_json": base64.b64encode(raw).decode()} for raw in (png, stream.getvalue())]
    with engine(tmp_path) as run:
        result = complete(run, 0, response(data=data))
        assert len(result["images"]) == 2 and not result["success"]
        assert result["images"][1]["mime"] == "image/jpeg"
        assert result["images"][1]["width"] == 512
        assert any("expected one image" in reason for reason in run.pauses)
        assert any("geometry" in reason for reason in run.pauses)


def test_invalid_image_bytes_are_archived_before_inspection(tmp_path):
    with engine(tmp_path) as run:
        result = complete(run, 0, response(b"not an image"))
        assert (tmp_path / result["images"][0]["path"]).read_bytes() == b"not an image"
        assert not result["success"] and run.pauses


def test_response_size_limit_preserves_bounded_partial_bytes(tmp_path):
    with engine(tmp_path) as run:
        fixture = c.MockResponse(200, [b"x" * c.MIB] * 65)
        result = complete(run, 0, fixture)
        assert result["response"]["bytes"] == 64 * c.MIB
        assert result["response"]["complete"] is False
        assert result["cost_usd"] is None and run.outstanding_count == 1
        assert any("exceeds 64 MiB" in reason for reason in run.pauses)
        archived = gzip.decompress((tmp_path / result["response"]["path"]).read_bytes())
        assert len(archived) == 64 * c.MIB


def test_partial_stream_retained_and_not_retried(tmp_path):
    def stream():
        yield b'{"partial":'
        raise OSError("mock interrupted stream")

    with engine(tmp_path) as run:
        result = complete(run, 0, c.MockResponse(503, stream()))
        assert result["response"]["complete"] is False and not result["retryable"]
        assert result["cost_usd"] is None
        archived = (tmp_path / result["response"]["path"]).read_bytes()
        assert gzip.decompress(archived) == b'{"partial":'


def test_archive_collision_never_overwrites_crash_partial_and_keeps_charge(tmp_path, png):
    with engine(tmp_path) as run:
        crash_path = tmp_path / "responses/slot-0-a1.json.gz"
        crash_path.write_bytes(b"crash partial")
        result = complete(run, 0, response(png))
        assert crash_path.read_bytes() == b"crash partial"
        assert result["cost_usd"] == "0.05" and result["response"] is None
        assert not result["success"] and run.pauses


def test_space_lost_during_response_records_known_charge_and_pauses(tmp_path, png):
    available = [50 * c.GIB]
    with engine(tmp_path, free_bytes=lambda _: available[0]) as run:
        intent = run.start("slot-0", at())
        available[0] = 0
        result = run.finish(intent["attempt_id"], response(png), at(1))
        assert result["cost_usd"] == "0.05" and result["response"] is None
        assert not result["success"] and run.pauses


def test_terminal_is_create_once_permanent_and_blocks_all_starts(tmp_path, png):
    with engine(tmp_path, count=1) as run:
        complete(run, 0, response(png))
        receipt = run.close_terminal(at(2))
        assert receipt["status"] == "complete" and receipt["simulation_only"]
        saved = (tmp_path / "terminal.json").read_bytes()
        with pytest.raises(c.CollectorError, match="permanently closed"):
            run.close_terminal(at(3))
        assert (tmp_path / "terminal.json").read_bytes() == saved
    with pytest.raises(c.CollectorError, match="permanently closed"):
        engine(tmp_path, count=1)


def test_terminal_archive_failure_persists_pause_before_retry(tmp_path, monkeypatch):
    original = c._create_once

    def failed(path, data):
        if path.name == "terminal.json":
            raise OSError("mock disk error")
        return original(path, data)

    with engine(tmp_path) as run:
        monkeypatch.setattr(c, "_create_once", failed)
        with pytest.raises(OSError):
            run.close_terminal(at())
        assert run.pauses
        assert run.events[-1]["kind"] == "pause"
    monkeypatch.setattr(c, "_create_once", original)
    with engine(tmp_path) as recovered:
        with pytest.raises(c.AdmissionDenied, match="paused"):
            recovered.start("slot-0", at(5))


def test_partial_terminal_after_crash_is_permanently_closed(tmp_path):
    with engine(tmp_path):
        (tmp_path / "terminal.json").write_bytes(b'{"partial":')
    with pytest.raises(c.CollectorError, match="permanently closed"):
        engine(tmp_path)


def test_torn_journal_is_preserved_paused_and_accounting_indeterminate(tmp_path):
    with engine(tmp_path) as run:
        run.start("slot-0", at())
    with (tmp_path / "events.jsonl").open("ab") as stream:
        stream.write(b'{"kind":"end"')
    original = (tmp_path / "events.jsonl").read_bytes()
    with engine(tmp_path) as recovered:
        assert recovered.journal_corrupt and recovered.outstanding_count == 1
        assert recovered.select(at(10)) is None
        with pytest.raises(c.CollectorError, match="damaged journal"):
            recovered.close_terminal(at(11))
    assert (tmp_path / "events.jsonl").read_bytes() == original


def test_recovery_rejects_changed_assignments_and_simulation_policy(tmp_path):
    with engine(tmp_path):
        pass
    changed = slots()
    changed[0]["payload"]["prompt"] = "changed"
    with pytest.raises(c.CollectorError, match="changed on recovery"):
        c.Collector(tmp_path, changed, simulation=True,
                    policy=c.CollectorPolicy(Decimal("350")), free_bytes=lambda _: 50 * c.GIB)


def test_finite_mock_transport_exact_payload_and_no_arbitrary_adapter(tmp_path, png):
    with engine(tmp_path) as run:
        fixture = c.MockTransport([response(png)])
        result = run.execute_one("slot-0", fixture, started_at=at(), ended_at=at(1))
        assert result["success"] and fixture.requests == [slots()[0]["payload"]]
        with pytest.raises(TypeError, match="finite built-in MockTransport"):
            run.execute_one("slot-1", lambda _: None, started_at=at(5), ended_at=at(6))


def test_explicit_charge_evidence_missing_or_conflicting_stays_unknown(tmp_path):
    with engine(tmp_path) as run:
        intent = run.start("slot-0", at())
        fixture = c.MockResponse(429, b"{}", charge_usd=Decimal("0"))
        result = run.finish(intent["attempt_id"], fixture, at(1))
        assert result["cost_usd"] is None and run.outstanding_count == 1
    with engine(tmp_path / "conflict") as run:
        fixture = c.MockResponse(429, b'{"usage":{"cost":0.01}}',
                                 charge_usd=Decimal("0"), billing_evidence="mock billing record")
        result = complete(run, 0, fixture)
        assert result["cost_usd"] is None and run.outstanding_count == 1


def test_old_namespaces_are_excluded(tmp_path):
    with pytest.raises(c.CollectorError, match="old collector namespaces"):
        engine(tmp_path / "painter_specificity_v2")


def test_actual_protocol_slots_and_exact_requested_route(tmp_path, png):
    from latent_art_bench.painter_family_controls_v1.protocol import assignments

    all_slots = assignments(T0)
    sample = next(slot for slot in all_slots if slot["model"].startswith("gpt-image"))
    with c.Collector(tmp_path, [sample], simulation=True,
                     policy=c.CollectorPolicy(Decimal("350")),
                     free_bytes=lambda _: 50 * c.GIB) as run:
        fixture = c.MockTransport([response(png, model=sample["payload"]["model"],
                                             provider=sample["payload"]["provider"]["only"][0])])
        result = run.execute_one(sample["id"], fixture, started_at=at(), ended_at=at(1))
        assert result["success"]
        assert fixture.requests == [sample["payload"]]


def test_provider_fallback_or_multiple_routes_are_rejected(tmp_path):
    sample = slots()
    sample[0]["payload"]["provider"]["allow_fallbacks"] = True
    with pytest.raises(ValueError, match="sole provider"):
        c.Collector(tmp_path, sample)


def test_abrupt_process_exit_releases_owner_but_preserves_durable_intent(tmp_path):
    script = """
import json, os, sys
from decimal import Decimal
from latent_art_bench.painter_family_controls_v1.collector import Collector, CollectorPolicy, GIB
run = Collector(sys.argv[1], json.loads(sys.argv[2]), simulation=True,
                policy=CollectorPolicy(Decimal('350')), free_bytes=lambda _: 50 * GIB)
run.start('slot-0', '2030-01-01T00:00:00Z')
os._exit(17)
"""
    child = subprocess.run([sys.executable, "-c", script, str(tmp_path), json.dumps(slots())],
                           check=False, capture_output=True, text=True)
    assert child.returncode == 17, child.stderr
    with engine(tmp_path) as recovered:
        assert recovered.outstanding_count == 1
        assert recovered.accounted_usd == Decimal("117.293676")
        assert recovered.select(at(5)) is None


def test_intent_persistence_failure_cannot_dispatch_fixture(tmp_path, png, monkeypatch):
    with engine(tmp_path) as run:
        fixture = c.MockTransport([response(png)])

        def failed(_fd):
            raise OSError("mock fsync failure")

        monkeypatch.setattr(c.os, "fsync", failed)
        with pytest.raises(OSError, match="fsync failure"):
            run.execute_one("slot-0", fixture, started_at=at(), ended_at=at(1))
        assert fixture.requests == []
        assert run.journal_corrupt and run.pauses


def test_truncated_jpeg_is_retained_but_not_counted_as_success(tmp_path):
    stream = io.BytesIO()
    Image.new("RGB", (1024, 1024), "white").save(stream, format="JPEG")
    truncated = stream.getvalue()[:-20]
    with pytest.raises(OSError), Image.open(io.BytesIO(truncated)) as image:
        image.load()
    with engine(tmp_path) as run:
        result = complete(run, 0, response(truncated))
        assert not result["success"] and run.pauses
        assert result["cost_usd"] == "0.05" and not run.outstanding_count
        assert (tmp_path / result["images"][0]["path"]).read_bytes() == truncated


def test_bad_png_crc_settles_known_charge_and_persistently_pauses(tmp_path, png):
    damaged = bytearray(png)
    position = 8
    while position < len(damaged):
        size = int.from_bytes(damaged[position:position + 4], "big")
        if damaged[position + 4:position + 8] == b"IDAT":
            damaged[position + 8 + size] ^= 1
            break
        position += size + 12
    else:
        raise AssertionError("fixture requires an IDAT chunk")
    with engine(tmp_path) as run:
        result = complete(run, 0, response(damaged))
        assert not result["success"] and run.pauses
        assert result["cost_usd"] == "0.05" and not run.outstanding_count
        assert any("SyntaxError" in reason for reason in run.pauses)
        with pytest.raises(c.AdmissionDenied, match="paused"):
            run.start("slot-1", at(5))
    with engine(tmp_path) as recovered:
        assert not recovered.journal_corrupt and recovered.pauses
        assert recovered.new_settled_usd == Decimal("0.05")


@pytest.mark.parametrize("status", [200.0, True, float("nan"), float("inf"), "200", 99, 600])
def test_invalid_status_cannot_break_durable_completion_or_enable_starts(tmp_path, png, status):
    with engine(tmp_path) as run:
        result = complete(run, 0, response(png, status=status))
        assert result["status"] is None and not result["success"]
        assert result["cost_usd"] == "0.05" and not run.outstanding_count
        assert run.pauses
        with pytest.raises(c.AdmissionDenied, match="paused"):
            run.start("slot-1", at(5))
    with engine(tmp_path) as recovered:
        assert not recovered.journal_corrupt and recovered.pauses


@pytest.mark.parametrize("refusal", ["false", "true", 0, 1, None, [], {}])
def test_invalid_refusal_does_not_silently_consume_slot_as_content_refusal(tmp_path, refusal):
    with engine(tmp_path) as run:
        result = complete(run, 0, response(refusal=refusal))
        assert not result["refusal"] and not result["success"]
        assert "refusal must be boolean" in run.pauses


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_json_is_preserved_paused_and_keeps_reservation(tmp_path, constant):
    body = ('{"usage":{"cost":"0"},"refusal":' + constant + '}').encode()
    with engine(tmp_path) as run:
        result = complete(run, 0, c.MockResponse(200, body))
        assert not result["refusal"] and not result["success"]
        assert result["cost_usd"] is None and run.outstanding_count == 1
        assert run.pauses and gzip.decompress(
            (tmp_path / result["response"]["path"]).read_bytes()) == body


def test_unexpected_completion_exception_persistently_pauses(tmp_path, png, monkeypatch):
    def broken(*_args):
        raise RuntimeError("constructed internal decode failure")

    with engine(tmp_path) as run:
        monkeypatch.setattr(run, "_images", broken)
        with pytest.raises(RuntimeError, match="constructed internal"):
            complete(run, 0, response(png))
        assert run.outstanding_count == 1 and run.pauses
        assert run.events[-1]["kind"] == "pause"
        with pytest.raises(c.AdmissionDenied, match="paused"):
            run.start("slot-1", at(5))
    with engine(tmp_path) as recovered:
        assert recovered.outstanding_count == 1 and recovered.pauses


def test_foreign_hashed_journal_cannot_be_replayed_in_another_manifest(tmp_path, png):
    source, destination = tmp_path / "source", tmp_path / "destination"
    with engine(source) as run:
        complete(run, 0, response(png))
    changed = slots()
    changed[0]["payload"]["prompt"] = "different frozen prompt"
    kwargs = dict(simulation=True, policy=c.CollectorPolicy("350"),
                  free_bytes=lambda _: 50 * c.GIB)
    with c.Collector(destination, changed, **kwargs):
        pass
    (destination / "events.jsonl").write_bytes((source / "events.jsonl").read_bytes())
    with c.Collector(destination, changed, **kwargs) as recovered:
        assert recovered.journal_corrupt and recovered.pauses
        assert recovered.select(at(5)) is None
        with pytest.raises(c.CollectorError, match="damaged journal"):
            recovered.close_terminal(at(6))


@pytest.mark.parametrize("artifact,mutation", [("image", "remove"), ("image", "change"),
                                              ("response", "remove"), ("response", "change")])
def test_recovery_verifies_retained_originals_and_response_bytes(tmp_path, png, artifact, mutation):
    with engine(tmp_path) as run:
        result = complete(run, 0, response(png))
    path = tmp_path / (result["images"][0]["path"] if artifact == "image"
                       else result["response"]["path"])
    if mutation == "remove":
        path.unlink()
    else:
        path.write_bytes(b"changed" if artifact == "image" else gzip.compress(b"{}"))
    with engine(tmp_path) as recovered:
        assert recovered.journal_corrupt and recovered.pauses
        assert recovered.select(at(5)) is None


def test_public_assignment_event_and_policy_views_cannot_mutate_frozen_state(tmp_path, png):
    with engine(tmp_path) as run:
        run.slots["slot-0"]["payload"]["prompt"] = "mutated view"
        object.__setattr__(run.policy, "cumulative_ceiling_usd", Decimal("999"))
        fixture = c.MockTransport([response(png)])
        result = run.execute_one("slot-0", fixture, started_at=at(), ended_at=at(1))
        result["success"] = False
        run.events[0]["started_at"] = at(999).isoformat()
        run.starts["slot-0-a1"]["started_at"] = at(999).isoformat()
        run.ends["slot-0-a1"]["success"] = False
        assert fixture.requests == [slots()[0]["payload"]]
        assert run.policy.cumulative_ceiling_usd == Decimal("350")
        assert run.ends["slot-0-a1"]["success"] is True
        assert run.starts["slot-0-a1"]["started_at"] == "2030-01-01T00:00:00Z"
        run.pause("persistent", at(2))
        run.pauses.clear()
        assert run.pauses == ["persistent"]


def test_returned_intent_cannot_change_completion_window(tmp_path, png):
    with engine(tmp_path) as run:
        intent = run.start("slot-0", at())
        intent["window_end"] = "2030-01-02T04:00:00Z"
        intent["session"] = 99
        result = run.finish("slot-0-a1", response(png), at(1))
        assert result["window_end"] == "2030-01-01T04:00:00Z"
        assert result["session"] == 0


def test_only_exact_policy_type_is_accepted(tmp_path):
    from types import SimpleNamespace

    class Alternate(c.CollectorPolicy):
        @property
        def reservation_usd(self):
            return Decimal("0")

    for policy in (False, True, {}, SimpleNamespace(cumulative_ceiling_usd=Decimal("350")),
                   Alternate("350")):
        with pytest.raises(TypeError, match="exact validated CollectorPolicy"):
            c.Collector(tmp_path, slots(), simulation=True, policy=policy)
    assert not tmp_path.joinpath("run.json").exists()


def test_space_loss_after_raw_response_stops_each_original_write(tmp_path, png, monkeypatch):
    free = [50 * c.GIB]
    original = c._create_once

    def drop_space(path, content):
        original(path, content)
        if path.name.endswith(".json.gz"):
            free[0] = 0

    with engine(tmp_path, free_bytes=lambda _: free[0]) as run:
        monkeypatch.setattr(c, "_create_once", drop_space)
        result = complete(run, 0, response(png))
        assert not result["success"] and result["response"] and not result["images"]
        assert result["cost_usd"] == "0.05" and run.pauses
        assert list((tmp_path / "images").iterdir()) == []


def test_artifact_symlink_is_rejected_and_actual_subdirectory_is_checked(tmp_path, png):
    target = tmp_path / "other"
    target.mkdir()
    root = tmp_path / "run"
    root.mkdir()
    (root / "images").symlink_to(target, target_is_directory=True)
    with pytest.raises(c.CollectorError, match="symlinks"):
        engine(root)
    checked = []

    def free(path):
        checked.append(path)
        return 0 if path.name == "images" else 50 * c.GIB

    with engine(tmp_path / "separate", free_bytes=free) as run:
        with pytest.raises(c.AdmissionDenied, match="actual free bytes"):
            run.start("slot-0", at())
        assert run.root / "responses" in checked and run.root / "images" in checked


def test_direct_first_starts_obey_order_while_retries_can_interleave(tmp_path, png):
    with engine(tmp_path) as run:
        with pytest.raises(c.AdmissionDenied, match="frozen within-window order"):
            run.start("slot-3", at())
        complete(run, 0, response(status=429, cost="0"))
        complete(run, 1, response(png), start=5)
        retry = run.start("slot-0", at(21))
        run.finish(retry["attempt_id"], response(png), at(22))
        complete(run, 2, response(png), start=26)
        assert [event["id"] for event in run.starts.values()] == [
            "slot-0", "slot-1", "slot-0", "slot-2"]


def test_new_directory_ancestors_are_synced_before_first_intent(tmp_path, monkeypatch):
    synced = []
    original = c._sync_directory

    def observed(path):
        synced.append(path)
        original(path)

    monkeypatch.setattr(c, "_sync_directory", observed)
    root = tmp_path / "new-parent" / "new-run"
    with engine(root) as run:
        run.start("slot-0", at())
    assert tmp_path.resolve() in synced
    assert (tmp_path / "new-parent").resolve() in synced
    assert root.resolve() in synced


@pytest.mark.parametrize("cost", [True, float("nan"), float("inf"), "-0.1", "1e999999"])
def test_unsafe_observed_costs_preserve_reservation_and_pause(tmp_path, cost):
    with engine(tmp_path) as run:
        result = complete(run, 0, response(status=429, cost=cost))
        assert result["cost_usd"] is None and run.outstanding_count == 1
        assert not result["retryable"] and run.pauses


def test_high_precision_json_cost_is_summed_without_decimal_rounding(tmp_path):
    amount = "0.000000000000000000000000000000000001"
    fixture = c.MockResponse(429, ('{"usage":{"cost":' + amount + '}}').encode())
    with engine(tmp_path) as run:
        result = complete(run, 0, fixture)
        assert result["retryable"]
        assert str(run.accounted_usd) == "112.293676000000000000000000000000000001"


@pytest.mark.parametrize("field,value", [("window_end", "2030-01-02T04:00:00Z"),
                                       ("session", True), ("payload_sha256", "wrong"),
                                       ("attempt", True), ("sequence", False)])
def test_replay_rejects_assignment_or_schema_drift_even_with_rehashed_event(tmp_path, field, value):
    with engine(tmp_path) as run:
        run.start("slot-0", at())
    ledger = tmp_path / "events.jsonl"
    event = json.loads(ledger.read_bytes())
    event[field] = value
    event.pop("sha256")
    event["sha256"] = c._sha(c._encoded(event))
    ledger.write_bytes(c._encoded(event) + b"\n")
    with engine(tmp_path) as recovered:
        assert recovered.journal_corrupt and recovered.pauses
        assert recovered.select(at(5)) is None


def test_terminal_verifies_evidence_and_broken_symlink_is_permanent_barrier(tmp_path, png):
    with engine(tmp_path / "missing") as run:
        result = complete(run, 0, response(png))
        (run.root / result["images"][0]["path"]).unlink()
        with pytest.raises(c.CollectorError, match="terminal verification"):
            run.close_terminal(at(2))
        assert run.pauses
    root = tmp_path / "broken-terminal"
    with engine(root):
        (root / "terminal.json").symlink_to(root / "absent-file")
    with pytest.raises(c.CollectorError, match="permanently closed"):
        engine(root)


def test_error_envelope_with_200_status_is_retained_and_diagnosed(tmp_path, png):
    with engine(tmp_path) as run:
        result = complete(run, 0, response(png, code="server_error"))
        assert result["response"] and result["images"]
        assert not result["success"] and run.pauses


@pytest.mark.parametrize("ceiling", [True, False, "NaN", "Infinity", "-1", "1e999999"])
def test_unsafe_policy_ceiling_is_rejected(ceiling):
    with pytest.raises(ValueError):
        c.CollectorPolicy(ceiling)
