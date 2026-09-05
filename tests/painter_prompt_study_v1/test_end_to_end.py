"""One full offline R=4 grid connects all production stages and their evidence audit.

Transport and feature extraction are synthetic oracles. Calibration qualification and
the old numeric-reference loader are stubbed explicitly; no real study bytes are read.
"""

import base64
import hashlib
import importlib.metadata
import io
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import httpx
import numpy as np
import pytest
from PIL import Image

from latent_art_bench.io import hash_file, read_jsonl
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, digest, publish
from latent_art_bench.painter_prompt_study_v1 import (
    analysis,
    audit,
    generation,
    measurement,
    randomization,
    randomization_record,
    report,
    reproduction,
)
from latent_art_bench.painter_prompt_study_v1.common import MANIFESTS, PACKAGE, WORKSPACE
from latent_art_bench.painter_prompt_study_v1.prompts import METHOD_IDS, TEMPLATE_IDS, build_library

ROOT = Path(__file__).resolve().parents[2]


def test_complete_mocked_grid_flows_through_generation_measurement_analysis_report_and_audit(
    tmp_path, monkeypatch
):
    run_id, calibration_id = "offline-complete", "offline-calibration"
    source_id = "offline-reference"
    directory = tmp_path / MANIFESTS / run_id
    directory.mkdir(parents=True)
    config = dict(
        repetitions=4,
        aliases=list(generation.ALIASES),
        method_ids=list(METHOD_IDS),
        maximum_requests=1920,
        base_url=generation.BASE,
        order_seed=20260905,
        maximum_response_bytes=generation.MAX_RESPONSE_BYTES,
        max_runtime_bytes=1024**3,
        reserve_disk_bytes=generation.RESERVE_DISK_BYTES,
        timeout_seconds=240,
        minimum_start_interval_seconds=15,
        minimum_decoded_short_side=512,
        primary_estimator="paired_randomization",
        simultaneous_alpha=0.05,
        calibration_id=calibration_id,
        permutation_seed=20260905,
        permutation_draws=99999,
        multiplicity="holm",
        approved_maximum_requests=1920,
        authorization="Offline mock-transport fixture only",
        paid_fallback=False,
        **generation.RENDER,
    )
    config_path = Path("configs/painter_prompt_study_v1/offline.json")
    publish(tmp_path / config_path, config)
    library = build_library(ROOT)  # Frozen text metadata only, never artwork pixels.
    requests = generation.request_grid(config, library)
    publish(directory / "prompts.json", library)
    publish(directory / "requests.jsonl", requests, lines=True)
    confirmation = Path("data/manifests/painter_feature_generation_v2") / source_id
    confirmation /= "confirmation_features.jsonl"
    counts = dict(zip(PAINTER_IDS, [297, 106, 141, 105]))
    references = [
        dict(
            image_id=f"{p}-{i}",
            painter_id=p,
            status="measured",
            raw_sha256=digest([p, i]),
            phash="ffffffffffffffff",
            values=[j + (i % 5) / 10] * 31,
        )
        for j, p in enumerate(PAINTER_IDS)
        for i in range(counts[p])
    ]
    publish(tmp_path / confirmation, references, lines=True)
    reference_inputs = bindings(tmp_path, [confirmation])
    real = {
        p: np.array([r["values"] for r in references if r["painter_id"] == p]) for p in PAINTER_IDS
    }
    development_counts = dict(zip(PAINTER_IDS, [55, 55, 55, 56]))
    scaler = dict(center=[0.0] * 31, scale=[1.0] * 31)
    source = dict(inputs=reference_inputs, scaler_development_counts=development_counts)
    monkeypatch.setattr(
        analysis, "load_source", lambda root, method: (real, {}, {}, scaler, {}, source)
    )
    decision = dict(
        qualified_repetitions=[4],
        primary_estimator="paired_randomization",
        simultaneous_alpha=0.05,
        uses_empirical_outcomes_for_tuning=False,
        files=[],
    )
    decision_path = MANIFESTS / calibration_id / "decision.json"
    publish(tmp_path / decision_path, decision)
    monkeypatch.setattr(audit, "validate_randomization_calibration", lambda root, name: decision)
    monkeypatch.setattr(
        randomization_record, "validate_randomization_calibration", lambda root, name: decision
    )
    implementation_paths = []
    for module in (analysis, randomization, report, reproduction):
        implementation = PACKAGE / Path(module.__file__).name
        (tmp_path / implementation).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / implementation).write_bytes(Path(module.__file__).read_bytes())
        implementation_paths.append(implementation)
    (tmp_path / "proxy.txt").write_text("offline proxy source fixture")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    committed_paths = [
        *implementation_paths,
        confirmation,
        decision_path,
        config_path,
        Path("proxy.txt"),
    ]
    subprocess.run(["git", "add", *map(str, committed_paths)], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "Freeze offline pipeline fixture",
        ],
        cwd=tmp_path,
        check=True,
    )
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    frozen = dict(
        run_id=run_id,
        config=config,
        config_path=config_path.as_posix(),
        requests=len(requests),
        source_method_id=source_id,
        reference_inputs=reference_inputs,
        inputs=bindings(tmp_path, committed_paths),
        recorded_git_commit=commit,
        requests_sha256=hash_file(directory / "requests.jsonl"),
        library_sha256=hash_file(directory / "prompts.json"),
        software={p: importlib.metadata.version(p) for p in ("httpx", "Pillow")},
        proxy_source=dict(
            repository="offline-proxy",
            recorded_git_commit=commit,
            files=bindings(tmp_path, [Path("proxy.txt")]),
        ),
    )
    publish(directory / "generation_freeze.json", frozen)
    monkeypatch.setattr(
        generation.shutil, "disk_usage", lambda _: SimpleNamespace(free=100 * 1024**3)
    )
    encoded = io.BytesIO()
    Image.new("RGB", (512, 512), "#abcdef").save(encoded, format="PNG")
    image_bytes = encoded.getvalue()
    body = json.dumps(
        dict(
            data=[dict(b64_json=base64.b64encode(image_bytes).decode())],
            quality="low",
            size="512x512",
        )
    ).encode()
    seen = []

    def transport(request):
        assert str(request.url) == generation.BASE + "/v1/images/generations"
        seen.append(json.loads(request.content))
        return httpx.Response(
            200, stream=httpx.ByteStream(body), headers={"content-type": "application/json"}
        )

    transport = httpx.MockTransport(transport)
    first = generation.execute(
        tmp_path, run_id, transport=transport, sleep=lambda _: None, max_new_requests=7
    )
    assert first["terminal"] is False and first["image_attempts"] == 7
    generated = generation.execute(tmp_path, run_id, transport=transport, sleep=lambda _: None)
    assert generated["statuses"] == {"generated": 1920}
    assert seen == [r["payload"] for r in requests]
    called = []

    def numeric_oracle(item, short_side):
        assert short_side == 512 and Path(item["path"]).is_file()
        assert Path(item["path"]).is_relative_to(tmp_path / WORKSPACE / run_id)
        assert item["raw_sha256"] == hashlib.sha256(image_bytes).hexdigest()
        called.append(item["request_id"])
        painter = PAINTER_IDS.index(item["condition"]) if item["condition"] in PAINTER_IDS else 4
        method = METHOD_IDS.index(item["method_id"])
        offset = 2 - method * (0.3 + 0.02 * item["block"]) + 0.1 * item["block"]
        value = painter + offset + TEMPLATE_IDS.index(item["template_id"]) / 100
        values = [value] * 31
        return dict(
            status="measured",
            values=values,
            feature_sha256=digest(values),
            raw_sha256=item["raw_sha256"],
            normalization={"short_side": 512},
            phash="0000000000000000",
        )

    monkeypatch.setattr(measurement.pipeline, "measure_one", numeric_oracle)
    measured = measurement.measure(tmp_path, run_id)
    assert measured["complete_measured_grid"] and measured["statuses"] == {"measured": 1920}
    assert called == [r["request_id"] for r in requests]
    result = analysis.analyze(tmp_path, run_id)
    assert result["status"] == "complete"
    assert len(result["primary"]) == 48 and len(result["absolute"]) == 72
    assert len(result["distances"]) == 360 and len(result["coordinates"]) == 744
    assert (
        len(result["template_availability"]) == 480
        and len(result["scene_contributions"]) == 48 * 64
    )
    assert all(row["estimate"] < 0 for row in result["primary"])
    receipt = report.execute(tmp_path, run_id)
    assert receipt["analysis_status"] == "complete" and receipt["recorded_git_commit"] == commit
    checked = audit.audit(tmp_path, proxy_root=tmp_path)
    assert checked["overall"] == "PASS", checked["failures"]
    assert checked["checks"] > 1920
    assert len(read_jsonl(directory / "measured_features.jsonl")) == 1920
    assert len(list((tmp_path / WORKSPACE / run_id / "responses").glob("*.gz"))) == 1
    assert not list((tmp_path / WORKSPACE / run_id / "measurement_tmp").iterdir())
    assert hash_file(tmp_path / confirmation) == reference_inputs[0]["sha256"]

    # Replay performs all finite matrices, 48 permutation tests, Holm adjustment and report
    # rendering again. It must not decode/extract images, append ledgers or rewrite outputs.
    monkeypatch.setattr(measurement, "_response_bytes", lambda *args: pytest.fail("image access"))
    monkeypatch.setattr(measurement, "decode", lambda *args: pytest.fail("image decoding"))
    monkeypatch.setattr(
        measurement.pipeline, "measure_one", lambda *args: pytest.fail("feature extraction")
    )
    before_replay = {
        p.relative_to(tmp_path): hash_file(p) for p in tmp_path.rglob("*") if p.is_file()
    }
    replayed = reproduction.reproduce(tmp_path, run_id)
    assert replayed["status"] == "PASS" and replayed["primary_endpoints"] == 48
    assert replayed["report_files"] == len(receipt["files"]) and replayed["read_only"]
    assert replayed["normalized_analysis_fields"] == ["completed_at_utc"]
    assert before_replay == {
        p.relative_to(tmp_path): hash_file(p) for p in tmp_path.rglob("*") if p.is_file()
    }
    retained_analysis = directory / "analysis.json"
    original_bytes = retained_analysis.read_bytes()
    tampered = json.loads(original_bytes)
    tampered["secondary"][0]["estimate"] += 0.125
    retained_analysis.write_text(json.dumps(tampered))  # This temporary synthetic fixture only.
    with pytest.raises(ValueError, match="recomputed analysis differs"):
        reproduction.reproduce(tmp_path, run_id)
    retained_analysis.write_bytes(original_bytes)
    assert before_replay == {
        p.relative_to(tmp_path): hash_file(p) for p in tmp_path.rglob("*") if p.is_file()
    }
