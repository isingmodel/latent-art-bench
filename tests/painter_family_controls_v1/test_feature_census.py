"""Constructed terminal artifacts only; no learned encoder or service is run."""

import base64
import copy
import gzip
import io
import json
from datetime import timedelta
from decimal import Decimal

import numpy as np
import pytest
from PIL import Image

from latent_art_bench.painter_family_controls_v1 import protocol as p
from latent_art_bench.painter_family_controls_v1.collector import (
    Collector,
    CollectorPolicy,
    MockResponse,
    MockTransport,
)
from latent_art_bench.painter_family_controls_v1.feature_census import (
    RECORD_FILES,
    TerminalCensus,
    feature_manifest,
    load_embedding_census,
    load_terminal_census,
)
from latent_art_bench.painter_family_controls_v1.transport_artifact import file_sha


@pytest.fixture
def run(tmp_path):
    root = tmp_path / "collector"
    start = p.utc_datetime("2000-01-01T00:00:00Z")
    slots = p.assignments(start)
    buffer = io.BytesIO()
    Image.new("RGB", (1024, 1024), (20, 40, 60)).save(buffer, format="PNG")
    body = json.dumps({"usage": {"cost": "0.01"}, "data": [
        {"b64_json": base64.b64encode(buffer.getvalue()).decode()}
    ]}).encode()
    with Collector(root, slots, simulation=True, policy=CollectorPolicy(Decimal("350")),
                   free_bytes=lambda path: 100 * 1024**3) as collector:
        for index, slot in enumerate(slots[:4]):
            collector.execute_one(slot["id"], MockTransport([MockResponse(200, body)]),
                                  started_at=start + timedelta(seconds=5 * index),
                                  ended_at=start + timedelta(seconds=5 * index + 1))
        collector.close_terminal(start + timedelta(seconds=20), "constructed partial census")
    hashes = {name: file_sha(root / name) for name in RECORD_FILES}
    return root, hashes, slots


def load(run):
    root, hashes, _ = run
    return load_terminal_census(root, expected_hashes=hashes, allow_simulation=True)


def feature_files(tmp_path, census):
    manifest = feature_manifest(census, "csd")
    path = tmp_path / "features.json"
    path.write_text(json.dumps(manifest, sort_keys=True))
    values = np.zeros((len(manifest["rows"]), 768), dtype=np.float32)
    values[:, 0] = 1
    ids = np.array([row["id"] for row in manifest["rows"]])
    npz = tmp_path / "embeddings.npz"
    np.savez_compressed(npz, embeddings=values, ids=ids)
    return path, npz, values, ids


def test_terminal_requires_external_binding_and_explicit_simulation(run):
    root, hashes, _ = run
    with pytest.raises(ValueError, match="simulation receipts"):
        load_terminal_census(root, expected_hashes=hashes)
    with pytest.raises(ValueError, match="bind run.json"):
        load_terminal_census(root, expected_hashes={})
    changed = dict(hashes, **{"terminal.json": "0" * 64})
    with pytest.raises(ValueError, match="externally bound"):
        load_terminal_census(root, expected_hashes=changed, allow_simulation=True)


def test_all_assignments_missingness_timestamps_and_successful_image_identity(run):
    census = load(run)
    evidence = census.evidence
    assert evidence["planned"] == 4608
    assert len(evidence["images"]) == 4
    assert len(evidence["missing"]) == 4604
    assert len(evidence["window_times"][0]["attempts"]) == 4
    assert all(not window["attempts"] for window in evidence["window_times"][1:])
    assert evidence["simulation_only"] is True
    assert evidence["images"][0]["id"] == run[2][0]["id"]
    evidence["images"][0]["model"] = "mutated"
    assert census.evidence["images"][0]["model"] != "mutated"


def test_census_embedding_axes_and_missing_values_are_fixed(run, tmp_path):
    census = load(run)
    manifest, npz, _, _ = feature_files(tmp_path, census)
    result = load_embedding_census(census, manifest, npz,
                                  expected_manifest_sha256=file_sha(manifest),
                                  expected_embeddings_sha256=file_sha(npz))
    assert result["simulation_only"] is True
    assert result["generated"].shape == (6, 8, 12, 8, 768)
    assert result["observed"].sum() == 4
    assert np.isnan(result["generated"][~result["observed"]]).all()
    for row in run[2][:4]:
        cell = (p.MODELS.index(row["model"]), row["session"], row["scene"],
                p.ARMS.index(row["arm"]))
        assert result["generated"][cell][0] == 1


@pytest.mark.parametrize("tamper", ["ids", "norm", "dimension", "image", "manifest", "npz_hash"])
def test_extraction_input_or_vector_mutations_are_rejected(run, tmp_path, tamper):
    census = load(run)
    manifest, npz, values, ids = feature_files(tmp_path, census)
    manifest_sha, npz_sha = file_sha(manifest), file_sha(npz)
    if tamper == "ids":
        np.savez_compressed(npz, embeddings=values, ids=ids[::-1])
        npz_sha = file_sha(npz)
    elif tamper == "norm":
        values[0] *= 0.5
        np.savez_compressed(npz, embeddings=values, ids=ids)
        npz_sha = file_sha(npz)
    elif tamper == "dimension":
        np.savez_compressed(npz, embeddings=values[:, :767], ids=ids)
        npz_sha = file_sha(npz)
    elif tamper == "image":
        (census.run_dir / census.evidence["images"][0]["path"]).write_bytes(b"changed")
    elif tamper == "manifest":
        data = json.loads(manifest.read_text())
        data["encoder"]["processor"]["crop_offset"] = "different preprocessing"
        manifest.write_text(json.dumps(data))
        manifest_sha = file_sha(manifest)
    else:
        npz_sha = "0" * 64
    with pytest.raises(ValueError):
        load_embedding_census(census, manifest, npz,
                              expected_manifest_sha256=manifest_sha,
                              expected_embeddings_sha256=npz_sha)


@pytest.mark.parametrize("artifact", ["image", "response"])
def test_terminal_loader_verifies_retained_bytes(run, artifact):
    root, _, _ = run
    directory, pattern = (("images", "*.original") if artifact == "image"
                          else ("responses", "*.gz"))
    path = next((root / directory).glob(pattern))
    path.write_bytes(b"corrupted")
    with pytest.raises((ValueError, OSError)):
        load(run)


def rebind_journal(root, events, terminal):
    previous = None
    for index, event in enumerate(events):
        event.pop("sha256", None)
        event.update(sequence=index, previous_sha256=previous)
        event["sha256"] = p.canonical_sha(event)
        previous = event["sha256"]
    (root / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    terminal["ledger_sha256"] = file_sha(root / "events.jsonl")
    (root / "terminal.json").write_text(json.dumps(terminal))
    return {name: file_sha(root / name) for name in RECORD_FILES}


@pytest.mark.parametrize("geometry", [False, True])
def test_coherently_rehashed_receipts_still_require_real_image_response_identity(run, geometry):
    root, _, slots = run
    events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
    end = events[1]
    buffer = io.BytesIO()
    Image.new("RGB", (2, 3) if geometry else (1024, 1024), "red").save(buffer, format="PNG")
    raw = buffer.getvalue()
    image_path = root / end["images"][0]["path"]
    image_path.write_bytes(raw)
    end["images"][0].update(sha256=file_sha(image_path), bytes=len(raw))
    if geometry:
        # Even a matching raw response does not make a false1024x1024 receipt valid.
        response_path = root / end["response"]["path"]
        body = json.loads(gzip.decompress(response_path.read_bytes()))
        body["data"][0]["b64_json"] = base64.b64encode(raw).decode()
        encoded = json.dumps(body).encode()
        response_path.write_bytes(gzip.compress(encoded))
        import hashlib
        end["response"].update(sha256=hashlib.sha256(encoded).hexdigest(), bytes=len(encoded))
    terminal = json.loads((root / "terminal.json").read_text())
    hashes = rebind_journal(root, events, terminal)
    with pytest.raises(ValueError, match="actual decoded|raw response image"):
        load_terminal_census(root, expected_hashes=hashes, allow_simulation=True)


def test_terminal_closure_cannot_precede_any_retained_completion(run):
    root, hashes, _ = run
    terminal = json.loads((root / "terminal.json").read_text())
    terminal["ended_at"] = "2000-01-01T00:00:00Z"
    (root / "terminal.json").write_text(json.dumps(terminal))
    hashes["terminal.json"] = file_sha(root / "terminal.json")
    with pytest.raises(ValueError, match="closure precedes"):
        load(run)


def test_rehashed_post_success_retry_cannot_replace_the_original(run):
    root, _, _ = run
    events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
    retry = copy.deepcopy(events[0])
    retry.update(attempt=2, attempt_id=retry["id"] + "-a2", started_at="2000-01-01T00:00:25Z")
    events.append(retry)
    terminal = json.loads((root / "terminal.json").read_text())
    terminal["ended_at"] = "2000-01-01T00:00:30Z"
    hashes = rebind_journal(root, events, terminal)
    with pytest.raises(ValueError, match="eligible earlier technical failure"):
        load_terminal_census(root, expected_hashes=hashes, allow_simulation=True)


def test_constructed_dataclass_cannot_remove_simulation_identity(run):
    census = load(run)
    forged = census.evidence
    forged["simulation_only"] = False
    detached = TerminalCensus(census.run_dir, json.dumps(forged))
    with pytest.raises(ValueError, match="simulation receipts|detached census"):
        feature_manifest(detached, "csd")
