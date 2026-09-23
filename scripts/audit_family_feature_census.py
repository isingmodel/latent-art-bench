"""Temporary constructed probes for the independent family feature-census audit."""

from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import shutil
import tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

import numpy as np
from PIL import Image

from latent_art_bench.painter_family_controls_v1 import feature_census as fc
from latent_art_bench.painter_family_controls_v1 import protocol as p
from latent_art_bench.painter_family_controls_v1.collector import (
    Collector,
    CollectorPolicy,
    MockResponse,
    MockTransport,
)
from latent_art_bench.painter_family_controls_v1.transport_artifact import file_sha


def fixture(root):
    start = p.utc_datetime("2000-01-01T00:00:00Z")
    slots = p.assignments(start)
    buffer = io.BytesIO()
    Image.new("RGB", (1024, 1024), (20, 40, 60)).save(buffer, format="PNG")
    body = json.dumps(
        {
            "usage": {"cost": "0.01"},
            "data": [{"b64_json": base64.b64encode(buffer.getvalue()).decode()}],
        }
    ).encode()
    with Collector(
        root,
        slots,
        simulation=True,
        policy=CollectorPolicy(Decimal("350")),
        free_bytes=lambda path: 100 * 1024**3,
    ) as collector:
        for index, slot in enumerate(slots[:4]):
            collector.execute_one(
                slot["id"],
                MockTransport([MockResponse(200, body)]),
                started_at=start + timedelta(seconds=5 * index),
                ended_at=start + timedelta(seconds=5 * index + 1),
            )
        collector.close_terminal(start + timedelta(seconds=20), "independent constructed audit")
    return slots


def hashes(root):
    return {name: file_sha(root / name) for name in fc.RECORD_FILES}


def read_events(root):
    return [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]


def rebind(root, events=None, terminal=None):
    manifest = json.loads((root / "run.json").read_text())
    manifest_sha = p.canonical_sha(manifest)
    events = read_events(root) if events is None else events
    previous, lines = None, []
    for sequence, event in enumerate(events):
        event.pop("sha256", None)
        event.update(sequence=sequence, previous_sha256=previous, manifest_sha256=manifest_sha)
        event["sha256"] = p.canonical_sha(event)
        previous = event["sha256"]
        lines.append(json.dumps(event, sort_keys=True, separators=(",", ":")))
    (root / "events.jsonl").write_text("\n".join(lines) + "\n")
    terminal = json.loads((root / "terminal.json").read_text()) if terminal is None else terminal
    terminal.update(manifest_sha256=manifest_sha, ledger_sha256=file_sha(root / "events.jsonl"))
    (root / "terminal.json").write_text(json.dumps(terminal))


def load(root):
    return fc.load_terminal_census(root, expected_hashes=hashes(root), allow_simulation=True)


def embeddings(root, census):
    manifest = fc.feature_manifest(census, "csd")
    path, npz = root / "features.json", root / "embeddings.npz"
    path.write_text(json.dumps(manifest))
    values = np.zeros((len(manifest["rows"]), 768), dtype=np.float32)
    values[:, 0] = 1
    ids = np.array([row["id"] for row in manifest["rows"]])
    np.savez_compressed(npz, embeddings=values, ids=ids)
    return path, npz, values, ids


def consume(census, manifest, npz):
    return fc.load_embedding_census(
        census,
        manifest,
        npz,
        expected_manifest_sha256=file_sha(manifest),
        expected_embeddings_sha256=file_sha(npz),
    )


def image_response_mismatch(root):
    events = read_events(root)
    success = next(event for event in events if event["kind"] == "end")
    receipt = success["images"][0]
    path = root / receipt["path"]
    # A valid but different PNG is now falsely attributed to the unchanged response.
    buffer = io.BytesIO()
    Image.new("RGB", (1024, 1024), (220, 140, 160)).save(buffer, format="PNG")
    path.write_bytes(buffer.getvalue())
    receipt.update(sha256=file_sha(path), bytes=path.stat().st_size)
    rebind(root, events)
    census = load(root)
    manifest, npz, _, _ = embeddings(root, census)
    result = consume(census, manifest, npz)
    return {
        "accepted_observations": int(result["observed"].sum()),
        "response_bytes_changed": False,
        "selected_image_bytes_changed": True,
    }


def claimed_geometry(root):
    events = read_events(root)
    success = next(event for event in events if event["kind"] == "end")
    receipt = success["images"][0]
    path = root / receipt["path"]
    buffer = io.BytesIO()
    Image.new("RGB", (2, 3), (220, 140, 160)).save(buffer, format="PNG")
    path.write_bytes(buffer.getvalue())
    receipt.update(sha256=file_sha(path), bytes=path.stat().st_size)
    rebind(root, events)
    return {
        "accepted_observations": len(load(root).evidence["images"]),
        "claimed_dimensions": [receipt["width"], receipt["height"]],
        "actual_dimensions": [2, 3],
    }


def early_terminal(root):
    terminal = json.loads((root / "terminal.json").read_text())
    terminal["ended_at"] = "2000-01-01T00:00:00+00:00"
    rebind(root, terminal=terminal)
    return {
        "accepted_observations": len(load(root).evidence["images"]),
        "terminal_time": terminal["ended_at"],
        "latest_completion": "2000-01-01T00:00:16+00:00",
    }


def retry_after_success(root):
    events = read_events(root)
    start = copy.deepcopy(next(event for event in events if event["kind"] == "start"))
    end = copy.deepcopy(next(event for event in events if event["kind"] == "end"))
    original_attempt = start["attempt_id"]
    for event in (start, end):
        event.update(attempt=2, attempt_id=start["id"] + "-a2")
    start["started_at"] = "2000-01-01T00:00:30+00:00"
    end["ended_at"] = "2000-01-01T00:00:31+00:00"
    for receipt in (end["images"][0], end["response"]):
        old_path = root / receipt["path"]
        receipt["path"] = receipt["path"].replace(original_attempt, end["attempt_id"])
        shutil.copyfile(old_path, root / receipt["path"])
    terminal = json.loads((root / "terminal.json").read_text())
    terminal.update(
        attempts=5,
        new_settled_usd="0.05",
        accounted_usd=str(p.HISTORICAL_ACCOUNTED + Decimal("0.05")),
        ended_at="2000-01-01T00:00:35+00:00",
    )
    rebind(root, [*events, start, end], terminal)
    census = load(root)
    selected = next(row for row in census.evidence["images"] if row["id"] == start["id"])
    return {
        "selected_attempt": selected["attempt_id"],
        "earlier_successful_attempt": original_attempt,
    }


def fabricated_vectors(root):
    census = load(root)
    manifest, npz, values, ids = embeddings(root, census)
    values[:] = 0
    values[:, 501] = 1
    np.savez_compressed(npz, embeddings=values, ids=ids)
    result = consume(census, manifest, npz)
    return {"accepted_observations": int(result["observed"].sum()), "encoder_executed": False}


def forged_object(root):
    evidence = load(root).evidence
    evidence["simulation_only"] = False
    forged = fc.TerminalCensus(root.resolve(), json.dumps(evidence))
    manifest, npz, _, _ = embeddings(root, forged)
    result = consume(forged, manifest, npz)
    return {
        "simulation_only": result["simulation_only"],
        "on_disk_simulation_only": json.loads((root / "run.json").read_text())["simulation_only"],
    }


def altered_contract(root):
    census = load(root)
    manifest, npz, _, _ = embeddings(root, census)
    data = json.loads(manifest.read_text())
    data["encoder"]["processor"]["crop_offset"] = "unauthorized substitute"
    manifest.write_text(json.dumps(data))
    return consume(census, manifest, npz)


def reordered_vectors(root):
    census = load(root)
    manifest, npz, values, ids = embeddings(root, census)
    np.savez_compressed(npz, embeddings=values, ids=ids[::-1])
    return consume(census, manifest, npz)


def altered_assignment(root):
    manifest = json.loads((root / "run.json").read_text())
    manifest["slots"][0]["payload"]["prompt"] += " unauthorized suffix"
    (root / "run.json").write_text(json.dumps(manifest))
    rebind(root)
    return load(root)


def default_simulation(root):
    return fc.load_terminal_census(root, expected_hashes=hashes(root))


def stale_hash(root):
    expected = hashes(root)
    (root / "terminal.json").write_text((root / "terminal.json").read_text() + " ")
    return fc.load_terminal_census(root, expected_hashes=expected, allow_simulation=True)


def main():
    results = []
    for probe in (
        image_response_mismatch,
        claimed_geometry,
        early_terminal,
        retry_after_success,
        fabricated_vectors,
        forged_object,
        altered_contract,
        reordered_vectors,
        altered_assignment,
        default_simulation,
        stale_hash,
    ):
        with tempfile.TemporaryDirectory(prefix="family-census-independent-") as directory:
            root = Path(directory) / "run"
            fixture(root)
            try:
                details = probe(root)
                outcome = "accepted"
            except Exception as error:
                outcome, details = (
                    "rejected",
                    {"exception": type(error).__name__, "reason": str(error)},
                )
            results.append(dict(probe=probe.__name__, outcome=outcome, details=details))
    print(
        json.dumps(
            dict(
                status="constructed_offline_independent_probes",
                new_observations=0,
                implementation_sha256=file_sha(Path(fc.__file__)),
                script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                probes=results,
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
