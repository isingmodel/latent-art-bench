"""Exercise terminal→feature bindings→all reports using explicitly invented fixtures.

No encoder or31-feature extractor executes. Successful loading cannot establish
execution provenance; that boundary stays false in the saved report. The four
mock completions and4,604 missing slots are not prospective observations.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import io
import json
import socket
import tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

from latent_art_bench.painter_family_controls_v1 import feature_census as fc
from latent_art_bench.painter_family_controls_v1 import measurement31 as m31
from latent_art_bench.painter_family_controls_v1 import protocol as p
from latent_art_bench.painter_family_controls_v1.collector import (
    Collector,
    CollectorPolicy,
    MockResponse,
    MockTransport,
)
from latent_art_bench.painter_family_controls_v1.reporting import analyze_census
from latent_art_bench.painter_family_controls_v1.transport_artifact import ROOT, file_sha

REFERENCE = ROOT / "reports/painter_family_controls_v1/reference_panels_candidate_v1.json"
REFERENCE_SHA = "0e3cf3628118324c7526a9a01e3fa9195ee1ace55ea401fa569c595696bcbd82"
TRANSPORT = ROOT / "reports/painter_family_controls_v1/old_transport_candidate_v1.json"
TRANSPORT_SHA = "fd6e80de75b7578059ecaee602b4ea5fc9e74f06d7711e52e8bd532cddbabac2"


def reject_network(*args, **kwargs):
    raise AssertionError("offline reporting qualification prohibits network")


def run(output):
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="family-report-", dir=ROOT / "tmp/paper") as tmp:
        scratch = Path(tmp)
        start = p.utc_datetime("2000-01-01T00:00:00Z")
        slots = p.assignments(start)
        pixels = io.BytesIO()
        Image.new("RGB", (1024, 1024), (20, 40, 60)).save(pixels, format="PNG")
        body = json.dumps({"usage": {"cost": "0.01"}, "data": [
            {"b64_json": base64.b64encode(pixels.getvalue()).decode()}
        ]}).encode()
        run_dir = scratch / "collector"
        with Collector(run_dir, slots, simulation=True,
                       policy=CollectorPolicy(Decimal("350")),
                       free_bytes=lambda path: 100 * 1024**3) as collector:
            for index, slot in enumerate(slots[:4]):
                collector.execute_one(
                    slot["id"], MockTransport([MockResponse(200, body)]),
                    started_at=start + timedelta(seconds=index * 5),
                    ended_at=start + timedelta(seconds=index * 5 + 1),
                )
            collector.close_terminal(start + timedelta(seconds=20), "partial fixture census")
        hashes = {name: file_sha(run_dir / name) for name in fc.RECORD_FILES}
        census = fc.load_terminal_census(run_dir, expected_hashes=hashes, allow_simulation=True)
        ids = np.array([row["id"] for row in census.evidence["images"]])
        learned_specs = {}
        for encoder in ("clip", "csd"):
            manifest = scratch / f"{encoder}_inputs.json"
            manifest.write_text(json.dumps(fc.feature_manifest(census, encoder), sort_keys=True))
            values = np.zeros((len(ids), 768), dtype=np.float32)
            values[:, 0] = 1
            embeddings = scratch / f"{encoder}.npz"
            np.savez_compressed(embeddings, embeddings=values, ids=ids)
            learned_specs[encoder] = dict(
                manifest_path=manifest, embeddings_path=embeddings,
                expected_manifest_sha256=file_sha(manifest),
                expected_embeddings_sha256=file_sha(embeddings),
            )
        raw_manifest = scratch / "raw31_inputs.json"
        raw_manifest.write_text(json.dumps(m31.feature_manifest(census), sort_keys=True))
        _, center, _ = m31._historical_contract(ROOT)
        raw = scratch / "raw31.npz"
        np.savez_compressed(raw, raw_features=np.tile(center, (len(ids), 1)), ids=ids,
                            feature_names=np.array(m31.NAMES))
        raw_spec = dict(manifest_path=raw_manifest, raw_npz_path=raw,
                        expected_manifest_sha256=file_sha(raw_manifest),
                        expected_raw_sha256=file_sha(raw))
        kwargs = dict(reference_path=REFERENCE, expected_reference_sha256=REFERENCE_SHA,
                      transport_path=TRANSPORT, expected_transport_sha256=TRANSPORT_SHA)
        try:
            analyze_census(census, learned_specs, raw_spec, **kwargs)
        except ValueError as error:
            assert "simulation analysis" in str(error)
        else:
            raise AssertionError("simulation analysis lacked explicit opt-in")
        report = analyze_census(census, learned_specs, raw_spec, allow_simulation=True, **kwargs)
        assert report["simulation_only"] is True
        assert report["status"] == "simulation_only_not_scientific_evidence"
        assert report["primary"]["primary_family_size"] == 12
        assert all(not model["primary_complete"] for model in report["primary"]["models"])
        assert len(report["secondary_embeddings"]) == 7
        assert set(report["frozen_transport"]) == {"clip", "csd"}
        assert len(report["secondary_features"]["models"]) == 6
        assert report["provenance"]["actual_extractor_execution_authenticated"] is False
        encoded = json.dumps(report, sort_keys=True, allow_nan=False).encode()
        (output / "combined_fixture_report.json.gz").write_bytes(gzip.compress(encoded, mtime=0))
        paths = [*(run_dir / name for name in fc.RECORD_FILES), raw_manifest, raw]
        for spec in learned_specs.values():
            paths.extend([spec["manifest_path"], spec["embeddings_path"]])
        retained = {}
        for path in paths:
            target = output / (path.name + ".gz")
            target.write_bytes(gzip.compress(path.read_bytes(), mtime=0))
            retained[target.name] = dict(sha256=file_sha(target), original_sha256=file_sha(path))
        result = dict(
            status="passed",
            scope="partial fixture census through all bound feature/report adapters",
            simulation_only=True, fixture_completed_slots=4, fixture_missing_slots=4604,
            scientific_new_observations=0, new_paid_calls=0, encoders_executed=0,
            raw31_extractor_executed=False, representations_used=["clip", "csd", "historical31"],
            primary_reports=1, primary_family_size=12, secondary_embedding_reports=7,
            frozen_transport_reports=2, secondary31_models=6,
            incomplete_primary_decisions_suppressed=True, default_simulation_denied=True,
            actual_extractor_execution_authenticated=False,
            combined_report_sha256=file_sha(output / "combined_fixture_report.json.gz"),
            reference_candidate_sha256=REFERENCE_SHA, transport_candidate_sha256=TRANSPORT_SHA,
            retained_fixture_artifacts=retained,
            source_bindings={str(path.relative_to(ROOT)): file_sha(path) for path in
                             [Path(__file__), *sorted((ROOT / "src/latent_art_bench/"
                                                      "painter_family_controls_v1").glob("*.py"))]},
        )
    result["temporary_fixture_directory_removed"] = not scratch.exists()
    (output / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: result[key] for key in (
        "status", "fixture_completed_slots", "fixture_missing_slots",
        "new_paid_calls", "actual_extractor_execution_authenticated",
    )}))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with patch.object(socket.socket, "connect", reject_network), \
         patch.object(socket.socket, "connect_ex", reject_network), \
         patch.object(socket.socket, "sendto", reject_network), \
         patch.object(socket, "getaddrinfo", reject_network):
        run(args.output)


if __name__ == "__main__":
    main()
