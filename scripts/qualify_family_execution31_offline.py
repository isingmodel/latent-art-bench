"""Run real historical31 extraction/replay on three synthetic collector images.

Extraction and replay use different Python child processes. The generated
fixtures are retained in a compressed archive for reproduction, not used as
scientific study observations. No learned checkpoint or service is contacted.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import socket
import subprocess
import sys
import tarfile
import tempfile
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageCms

from latent_art_bench.painter_family_controls_v1 import execution31 as e
from latent_art_bench.painter_family_controls_v1 import feature_census as fc
from latent_art_bench.painter_family_controls_v1 import protocol as p
from latent_art_bench.painter_family_controls_v1.collector import (
    Collector,
    CollectorPolicy,
    MockResponse,
    MockTransport,
)
from latent_art_bench.painter_family_controls_v1.transport_artifact import ROOT, file_sha

CHILD = """
import runpy, socket, sys
def forbidden(*args, **kwargs):
    raise AssertionError('offline extraction qualification prohibits network')
socket.socket.connect = forbidden
socket.socket.connect_ex = forbidden
socket.socket.sendto = forbidden
socket.getaddrinfo = forbidden
sys.argv = ['execution31', *sys.argv[1:]]
runpy.run_module('latent_art_bench.painter_family_controls_v1.execution31', run_name='__main__')
"""


def image_bytes(index):
    y, x = np.indices((1024, 1024))
    values = np.stack((x % 256, y % 256, ((x // 16 + y // 16) % 2) * 255), axis=-1)
    image = Image.fromarray(np.roll(values.astype(np.uint8), index, axis=2))
    stream = io.BytesIO()
    if index == 0:
        image.save(stream, format="PNG")
    elif index == 1:
        profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        image.save(stream, format="PNG", icc_profile=profile)
    else:
        exif = Image.Exif()
        exif[274] = 6
        image.save(stream, format="JPEG", quality=93, exif=exif)
    return stream.getvalue()


def child(operation, run_dir, extracted, hashes, receipt=None):
    args = [sys.executable, "-c", CHILD, operation, "--run", str(run_dir),
            "--run-sha256", hashes["run.json"], "--events-sha256", hashes["events.jsonl"],
            "--terminal-sha256", hashes["terminal.json"], "--output", str(extracted),
            "--allow-simulation"]
    if receipt is not None:
        args.extend(["--receipt-sha256", receipt])
    completed = subprocess.run(args, check=True, capture_output=True, text=True, cwd=ROOT)
    return json.loads(completed.stdout)


def run(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="family-real31-", dir=ROOT / "tmp/paper") as tmp:
        scratch = Path(tmp)
        run_dir, extracted = scratch / "collector", scratch / "extracted"
        start = p.utc_datetime("2000-01-01T00:00:00Z")
        slots = p.assignments(start)
        with Collector(run_dir, slots, simulation=True,
                       policy=CollectorPolicy(Decimal("350")),
                       free_bytes=lambda _: 100 * 1024**3) as collector:
            for i, slot in enumerate(slots[:3]):
                body = json.dumps({"usage": {"cost": "0.01"}, "data": [
                    {"b64_json": base64.b64encode(image_bytes(i)).decode()}
                ]}).encode()
                collector.execute_one(
                    slot["id"], MockTransport([MockResponse(200, body)]),
                    started_at=start + timedelta(seconds=i * 5),
                    ended_at=start + timedelta(seconds=i * 5 + 1),
                )
            collector.close_terminal(start + timedelta(seconds=15), "three synthetic images")
        hashes = {name: file_sha(run_dir / name) for name in fc.RECORD_FILES}
        extraction = child("extract", run_dir, extracted, hashes)
        receipt_sha = extraction["receipt_sha256"]
        receipt = fc._json(fc._bound_bytes(extracted / "execution.json", receipt_sha))
        replay = child("replay", run_dir, extracted, hashes, receipt_sha)
        assert replay["status"] == "all_rows_recomputed_exactly"
        assert replay["rows_recomputed"] == 3
        assert replay["simulation_only"] is True
        assert replay["replay_pid"] != receipt["producer_pid"]
        assert replay["raw31_extraction_reproduced"] is True
        assert replay["learned_extraction_reproduced"] is False
        assert {r["normalization"]["color_profile"] for r in receipt["rows"]} == {
            "missing_assumed_srgb", "embedded_to_srgb"}
        assert len({r["raw_vector_sha256"] for r in receipt["rows"]}) == 3
        (output / "execution.json").write_bytes((extracted / "execution.json").read_bytes())
        (output / "replay.json").write_bytes(e._json_bytes(replay))
        retained = {str(path.relative_to(scratch)): file_sha(path)
                    for path in sorted(scratch.rglob("*")) if path.is_file()}
        archive_path = output / "synthetic_fixture.tar.gz"
        with tarfile.open(archive_path, "w:gz") as archive:
            for relative in retained:
                archive.add(scratch / relative, arcname=relative)
        result = dict(
            status="passed", simulation_only=True,
            raw31_extractor_executed=True, raw31_rows_recomputed_exactly=3,
            separate_extraction_and_replay_processes=True, learned_encoders_executed=0,
            scientific_new_observations=0, new_paid_calls=0,
            fixture_successes=3, fixture_missing_slots=4605,
            synthetic_pixel_variants=["RGB PNG", "embedded-sRGB PNG", "EXIF-rotated JPEG"],
            receipt_sha256=receipt_sha, replay_sha256=file_sha(output / "replay.json"),
            fixture_archive_sha256=file_sha(archive_path), retained_fixture_files=retained,
            terminal_record_hashes=hashes,
            source_bindings={**receipt["implementation_bindings"],
                             str(Path(__file__).resolve().relative_to(ROOT)): file_sha(__file__)},
            scope="actual raw31 execution qualification on synthetic pixels only",
            full_study_execution_authenticated=False,
        )
    result["temporary_fixture_directory_removed"] = not scratch.exists()
    (output / "result.json").write_bytes(e._json_bytes(result))
    print(json.dumps({key: result[key] for key in (
        "status", "raw31_rows_recomputed_exactly", "new_paid_calls",
        "full_study_execution_authenticated")}))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    def forbidden(*args, **kwargs):
        raise AssertionError("offline extraction qualification prohibits network")
    with patch.object(socket.socket, "connect", forbidden), \
         patch.object(socket.socket, "connect_ex", forbidden), \
         patch.object(socket.socket, "sendto", forbidden), \
         patch.object(socket, "getaddrinfo", forbidden):
        run(args.output)


if __name__ == "__main__":
    main()
