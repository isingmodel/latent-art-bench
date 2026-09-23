"""Exercise every proposed slot with in-memory fixtures and a synthetic clock.

This command is deliberately incapable of live collection. The fixture budget,
disk capacity, service echoes, images and time are synthetic. It retains an
audit ledger, then removes only its own temporary fixture response/image files.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import io
import json
import socket
import tempfile
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from latent_art_bench.painter_family_controls_v1 import protocol as p
from latent_art_bench.painter_family_controls_v1.collector import (
    Collector,
    CollectorError,
    CollectorPolicy,
    MockResponse,
    MockTransport,
)

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reject_network(*args, **kwargs):
    raise AssertionError("network is disabled for offline qualification")


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    code_paths = [Path(__file__), *sorted(
        (ROOT / "src/latent_art_bench/painter_family_controls_v1").glob("*.py")
    )]
    result = {
        "schema": "painter-family-controls-full-grid-qualification/1.0",
        "status": "running", "simulation_only": True,
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "new_paid_calls": 0, "new_observations": 0,
        "fixture_ceiling_usd": "350", "operative_approved_ceiling_usd": "120",
        "synthetic_free_bytes": 100 * 1024**3,
        "synthetic_cost_per_fixture_usd": "0.01",
        "source_bindings": {str(path.relative_to(ROOT)): digest(path) for path in code_paths},
        "limits": [
            "No current route, price, actual capacity or provider behavior is verified.",
            "This is a deterministic fixture census, not scientific evidence or permission.",
        ],
    }
    started = time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix="family-offline-", dir=ROOT / "tmp/paper") as tmp:
            scratch = Path(tmp)
            result["temporary_fixture_directory"] = str(scratch)
            run_dir = scratch / "run"
            try:
                fixed_start = datetime(2000, 1, 1, tzinfo=timezone.utc)
                slots = p.assignments(fixed_start)
                p.verify_assignments(slots, fixed_start)
                result["assignment_sha256"] = p.canonical_sha(slots)
                result["synthetic_window_origin"] = fixed_start.isoformat()
                buffer = io.BytesIO()
                Image.new("RGB", (1024, 1024), (80, 110, 140)).save(buffer, format="PNG")
                original = buffer.getvalue()
                encoded_image = base64.b64encode(original).decode()
                result["fixture_image_sha256"] = hashlib.sha256(original).hexdigest()
                result["fixture_image_bytes"] = len(original)
                kwargs = dict(simulation=True, policy=CollectorPolicy(Decimal("350")),
                              free_bytes=lambda path: 100 * 1024**3)
                windows, route_counts = {}, Counter()
                with Collector(run_dir, slots, **kwargs) as collector:
                    for index, slot in enumerate(slots):
                        now = p.utc_datetime(slot["window_start"]) + timedelta(
                            seconds=slot["session_order"] * 5
                        )
                        selected = collector.select(now)
                        assert selected["id"] == slot["id"], "scheduler changed frozen order"
                        payload = slot["payload"]
                        response_body = json.dumps({
                            "data": [{"b64_json": encoded_image}],
                            "usage": {"cost": "0.01"},
                            "model": payload["model"],
                            "provider": payload["provider"]["only"][0],
                        }, sort_keys=True).encode()
                        transport = MockTransport([MockResponse(200, response_body)])
                        receipt = collector.execute_one(
                            slot["id"], transport, started_at=now,
                            ended_at=now + timedelta(seconds=1),
                        )
                        assert transport.requests == [payload]
                        assert receipt["success"] and not receipt["pause_reasons"]
                        assert len(receipt["images"]) == 1
                        archived = run_dir / receipt["images"][0]["path"]
                        assert archived.read_bytes() == original
                        raw_archive = run_dir / receipt["response"]["path"]
                        assert gzip.decompress(raw_archive.read_bytes()) == response_body
                        assert collector.new_settled_usd == Decimal("0.01") * (index + 1)
                        assert collector.outstanding_count == 0
                        route_counts[payload["model"]] += 1
                        window = windows.setdefault(slot["session"], {
                            "count": 0, "first_started_at": now.isoformat(),
                        })
                        window["count"] += 1
                        window["last_completed_at"] = (now + timedelta(seconds=1)).isoformat()
                    assert len(collector.starts) == p.EXPECTED_OUTPUTS
                    assert len(collector.ends) == p.EXPECTED_OUTPUTS
                    assert not collector.pauses
                # Reopen a fully drained but nonterminal journal; this checks exact replay
                # of the whole census rather than relying only on in-memory accounting.
                with Collector(run_dir, slots, **kwargs) as recovered:
                    assert not recovered.pauses
                    assert recovered.new_settled_usd == Decimal("46.08")
                    assert recovered.accounted_usd == Decimal("158.373676")
                    terminal = recovered.close_terminal(
                        now + timedelta(seconds=2), "complete offline fixture census"
                    )
                assert terminal["status"] == "complete"
                assert terminal["planned"] == terminal["successful"] == 4608
                try:
                    Collector(run_dir, slots, **kwargs)
                except CollectorError as exc:
                    assert "terminal" in str(exc)
                else:
                    raise AssertionError("terminal run reopened")
                result.update(
                    status="passed", planned=4608, successful=4608,
                    starts=4608, ends=4608, route_counts=dict(route_counts),
                    windows=windows, fixture_accounted_usd=terminal["accounted_usd"],
                    full_journal_replay_passed=True, permanent_terminal_denial_passed=True,
                    original_bytes_and_raw_response_checks=4608,
                )
            finally:
                retained = {}
                for name in ("run.json", "events.jsonl", "terminal.json"):
                    path = run_dir / name
                    if path.exists():
                        target = output / (name + ".gz")
                        target.write_bytes(gzip.compress(path.read_bytes(), mtime=0))
                        retained[target.name] = {
                            "sha256": digest(target), "uncompressed_sha256": digest(path),
                            "uncompressed_bytes": path.stat().st_size,
                        }
                result["retained_simulation_records"] = retained
        result["temporary_fixture_directory_removed"] = not scratch.exists()
    except BaseException as exc:
        result.update(status="failed", error_type=type(exc).__name__, error=str(exc))
        raise
    finally:
        result["elapsed_seconds"] = time.monotonic() - started
        (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in (
        "status", "successful", "new_paid_calls", "elapsed_seconds"
    )}))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", required=True, type=Path,
                        help="new directory for simulation ledger and audit result")
    args = parser.parse_args()
    with patch.object(socket.socket, "connect", reject_network), \
         patch.object(socket.socket, "connect_ex", reject_network), \
         patch.object(socket.socket, "sendto", reject_network), \
         patch.object(socket, "getaddrinfo", reject_network):
        run(args.output)


if __name__ == "__main__":
    main()
