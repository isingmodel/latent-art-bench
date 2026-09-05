import base64
import gzip
import hashlib
import importlib.metadata
import io
import json

import numpy as np
import pytest
from PIL import Image

from latent_art_bench.io import hash_file, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import digest, publish
from latent_art_bench.painter_prompt_study_v1 import generation, measurement
from latent_art_bench.painter_prompt_study_v1.common import MANIFESTS, WORKSPACE


def _journal(records):
    result = []
    for index, record in enumerate(records):
        row = dict(record, sequence=index, at_utc="fixture-time",
                   previous_sha256=result[-1]["event_sha256"] if result else None)
        row.pop("event_sha256", None)
        row["event_sha256"] = digest(row)
        result.append(row)
    return result


def _run(root, monkeypatch, statuses=("generated",), *, alpha_first=False, fault=None):
    """Tiny source graph; production source bindings, journals and image decoding remain real."""
    # These tiny read-only accounting fixtures are not a prospective qualified generation run.
    # Authorization, calibration and historical Git checks have separate offline tests.
    # Current config/source hashing, terminal journals, decoding and measurement stay real.
    monkeypatch.setattr(generation, "_validate_authorization", lambda *args: None)
    monkeypatch.setattr(generation, "_verify_commit", lambda *args: None)
    run_id = "measurement-fixture"
    directory = root / MANIFESTS / run_id
    directory.mkdir(parents=True)
    requests, events, outputs = [], [], []
    for index, status in enumerate(statuses):
        request = dict(sequence=index, request_id=f"q{index}", block=0, alias="gpt-image-1",
                       method_id="by_name", condition="claude_monet", template_id=f"W{index + 1}",
                       payload=dict(generation.RENDER))
        requests.append(request)
        output = dict(generation._identity(request), kind="terminal", status=status,
                      attempted=status != "not_attempted")
        if output["attempted"]:
            events.append(dict(kind="attempt", request_id=request["request_id"],
                               request_sha256=digest(request)))
        if status == "generated":
            if alpha_first and index == 0:
                image = Image.new("RGBA", (512, 512), (90, 160, 30, 127))
            else:
                pixels = np.random.default_rng(7).integers(0, 256, (512, 512, 3), dtype=np.uint8)
                image = Image.fromarray(pixels)
            encoded = io.BytesIO()
            image.save(encoded, format="PNG")
            image_bytes = encoded.getvalue()
            payload = {"data": [{"b64_json": base64.b64encode(image_bytes).decode()}]}
            body = json.dumps(payload).encode()
            if fault == "response_ceiling":
                body += b" " * (4 * 1024**2)
            compressed = gzip.compress(body, mtime=0)
            response_sha = hashlib.sha256(body).hexdigest()
            relative = WORKSPACE / run_id / "responses" / f"{response_sha}.json.gz"
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_bytes(compressed)
            output.update(response_path=relative.as_posix(), response_sha256=response_sha,
                          stored_sha256=hashlib.sha256(compressed).hexdigest(),
                          stored_bytes=len(compressed), bytes=len(body),
                          decoded_bytes=len(image_bytes),
                          sha256=hashlib.sha256(image_bytes).hexdigest())
            if fault == "image_hash":
                output["sha256"] = "different-image"
        events.append(output)
    events = _journal(events)
    outputs = [row for row in events if row["kind"] == "terminal"]
    publish(directory / "generation_events.jsonl", events, lines=True)
    publish(directory / "outputs.jsonl", outputs, lines=True)
    publish(directory / "requests.jsonl", requests, lines=True)
    publish(directory / "prompts.json", {"fixture": "numeric-free synthetic image grid"})
    (root / "bound.txt").write_text("fixed implementation fixture")
    config = dict(minimum_decoded_short_side=512, maximum_response_bytes=4 * 1024**2)
    config_path = "measurement-config.json"
    publish(root / config_path, config)
    freeze = dict(
        config_path=config_path, recorded_git_commit="uncommitted-accounting-fixture",
        run_id=run_id, requests_sha256=hash_file(directory / "requests.jsonl"),
        library_sha256=hash_file(directory / "prompts.json"),
        inputs=[dict(path="bound.txt", sha256=hash_file(root / "bound.txt")),
                dict(path=config_path, sha256=hash_file(root / config_path))],
        config=config,
        software={p: importlib.metadata.version(p) for p in ("httpx", "Pillow")},
    )
    publish(directory / "generation_freeze.json", freeze)
    receipt = dict(
        run_id=run_id, terminal=True,
        expected_requests=len(requests), terminal_requests=len(outputs),
        image_attempts=sum(row["attempted"] for row in outputs),
        statuses={s: statuses.count(s) for s in set(statuses)},
        complete_generated_grid=all(s == "generated" for s in statuses),
        freeze_sha256=hash_file(directory / "generation_freeze.json"),
        ledger_sha256=hash_file(directory / "generation_events.jsonl"),
        outputs_sha256=hash_file(directory / "outputs.jsonl"),
    )
    if fault == "terminal_count":
        receipt["terminal_requests"] -= 1
    publish(directory / "generation_receipt.json", receipt)
    monkeypatch.setattr(generation, "request_grid", lambda config, library: requests)
    return run_id, directory, outputs


def test_measurement_emits_exact_raw_features_without_durable_decoded_images(tmp_path, monkeypatch):
    run_id, directory, outputs = _run(tmp_path, monkeypatch)
    before = {path: hash_file(path) for path in tmp_path.rglob("*") if path.is_file()}
    normalize = measurement.features.normalize
    accessed = []

    def spy(path, *args, **kwargs):
        accessed.append(path)
        assert path.is_relative_to(tmp_path / WORKSPACE / run_id / "measurement_tmp")
        return normalize(path, *args, **kwargs)

    monkeypatch.setattr(measurement.features, "normalize", spy)
    receipt = measurement.measure(tmp_path, run_id)
    rows = read_jsonl(directory / "measured_features.jsonl")
    assert receipt["complete_measured_grid"] is True
    assert receipt["statuses"] == {"measured": 1}
    assert len(rows) == len(accessed) == 1
    row = rows[0]
    assert row["image_id"] == row["request_id"] == "q0"
    assert row["method_id"] == "by_name" and row["alias"] == "gpt-image-1"
    assert row["source_output_sha256"] == digest(outputs[0])
    assert row["normalization"]["short_side"] == 512
    assert len(row["values"]) == 31 and np.isfinite(row["values"]).all()
    assert row["feature_sha256"] == digest(row["values"])
    assert receipt["feature_file_sha256"] == hash_file(directory / "measured_features.jsonl")
    assert all(hash_file(path) == sha for path, sha in before.items())
    assert all(not path.exists() for path in accessed)
    assert not list((tmp_path / WORKSPACE / run_id / "measurement_tmp").iterdir())
    assert not (tmp_path / "data/manifests/painter_feature_generation_v2").exists()
    with pytest.raises(FileExistsError, match="permanently terminal"):
        measurement.measure(tmp_path, run_id)


def test_failed_and_nongenerated_dispositions_are_retained_and_never_remeasured(
    tmp_path, monkeypatch
):
    run_id, directory, _ = _run(tmp_path, monkeypatch,
                                ("generated", "not_attempted", "generated"), alpha_first=True)
    first = measurement.measure(tmp_path, run_id, max_new_records=1)
    assert first["terminal"] is False and first["statuses"] == {"failed": 1}
    assert not (directory / "measured_features.jsonl").exists()
    original = measurement.pipeline.measure_one
    called = []

    def spy(item, *args):
        called.append(item["request_id"])
        return original(item, *args)

    monkeypatch.setattr(measurement.pipeline, "measure_one", spy)
    receipt = measurement.measure(tmp_path, run_id)
    assert called == ["q2"]
    assert receipt["statuses"] == {"failed": 1, "not_generated": 1, "measured": 1}
    assert receipt["complete_measured_grid"] is False
    rows = read_jsonl(directory / "measured_features.jsonl")
    assert [row["image_id"] for row in rows] == ["q0", "q1", "q2"]
    assert "nonopaque alpha" in rows[0]["error"]
    assert "values" not in rows[0] and "values" not in rows[1]


@pytest.mark.parametrize(("fault", "message"), [
    ("terminal_count", "terminal generation evidence"),
    ("image_hash", "decoded image hash"),
    ("response_ceiling", "frozen byte ceiling"),
    ("compressed_bytes", "compressed response changed"),
    ("freeze_input", "bound input changed"),
])
def test_source_tampering_and_resource_overflow_fail_before_feature_extraction(
    tmp_path, monkeypatch, fault, message
):
    run_id, directory, outputs = _run(tmp_path, monkeypatch, fault=fault)
    if fault == "compressed_bytes":
        (tmp_path / outputs[0]["response_path"]).write_bytes(b"tampered")
    elif fault == "freeze_input":
        (tmp_path / "bound.txt").write_text("changed")
    monkeypatch.setattr(measurement.pipeline, "measure_one",
                        lambda *args: pytest.fail("invalid evidence must not reach features"))
    with pytest.raises(ValueError, match=message):
        measurement.measure(tmp_path, run_id)
    assert not (directory / "measurement_receipt.json").exists()
    assert not (directory / "measured_features.jsonl").exists()


@pytest.mark.parametrize("fault", ["feature_digest", "wrong_identity"])
def test_resume_rejects_changed_prefix_even_with_a_consistent_event_chain(
    tmp_path, monkeypatch, fault
):
    run_id, directory, _ = _run(tmp_path, monkeypatch, ("generated", "generated"))
    measurement.measure(tmp_path, run_id, max_new_records=1)
    path = directory / "measurement_events.jsonl"
    rows = read_jsonl(path)
    if fault == "feature_digest":
        rows[1]["row"]["values"][0] += 1
    else:
        rows[1]["row"]["image_id"] = "a-different-image"
    # Only a temporary synthetic ledger is rewritten to test semantic validation after hashing.
    path.write_text("".join(json.dumps(row) + "\n" for row in _journal(rows)))
    monkeypatch.setattr(measurement.pipeline, "measure_one",
                        lambda *args: pytest.fail("changed prefix must never be skipped"))
    with pytest.raises(ValueError, match="feature digest|ordered source outputs"):
        measurement.measure(tmp_path, run_id)


def test_publication_interruption_resumes_without_reextracting_features(tmp_path, monkeypatch):
    run_id, directory, _ = _run(tmp_path, monkeypatch)
    original = measurement.publish

    def fail_receipt(path, *args, **kwargs):
        if path.name == "measurement_receipt.json":
            raise OSError("simulated publication interruption")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(measurement, "publish", fail_receipt)
    with pytest.raises(OSError, match="publication interruption"):
        measurement.measure(tmp_path, run_id)
    before = (directory / "measured_features.jsonl").read_bytes()
    monkeypatch.setattr(measurement, "publish", original)
    monkeypatch.setattr(measurement.pipeline, "measure_one",
                        lambda *args: pytest.fail("persisted terminal row must not be rerun"))
    assert measurement.measure(tmp_path, run_id)["complete_measured_grid"] is True
    assert (directory / "measured_features.jsonl").read_bytes() == before
