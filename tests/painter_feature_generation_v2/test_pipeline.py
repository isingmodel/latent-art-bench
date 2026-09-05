from pathlib import Path

import pytest

from latent_art_bench.io import hash_file
from latent_art_bench.painter_feature_generation_v2 import pipeline
from latent_art_bench.painter_feature_generation_v2.artifacts import MANIFESTS, publish


def fixture(tmp_path):
    base = tmp_path / MANIFESTS / "method"
    frozen = dict(inputs=[], experiment_ids=["generation"], calibration_id="calibration")
    publish(base / "method_freeze.json", frozen)
    publish(base / "scaler.json", dict(center=[0] * 31, scale=[1] * 31))
    for stage in ("development", "qualification"):
        path = base / f"{stage}_features.jsonl"
        publish(path, [dict(image_id="one", status="measured")], lines=True)
        publish(
            base / f"{stage}_receipt.json",
            dict(
                stage=stage,
                expected_records=1,
                terminal_records=1,
                statuses=dict(measured=1),
                feature_file_sha256=hash_file(path),
                scaler_sha256=hash_file(base / "scaler.json"),
            ),
        )
    generation = tmp_path / MANIFESTS / "generation"
    publish(generation / "outputs.jsonl", [dict(status="generated")], lines=True)
    publish(generation / "generation_freeze.json", dict(inputs=[]))
    publish(tmp_path / MANIFESTS / "calibration" / "calibration.json", dict(status="diagnostic"))
    return base, frozen, generation


def test_confirmation_cannot_open_before_every_generation_is_terminal(tmp_path, monkeypatch):
    base, frozen, generation = fixture(tmp_path)
    monkeypatch.setattr(pipeline, "_committed", lambda *_: "a" * 40)
    publish(
        generation / "generation_receipt.json",
        dict(
            expected_requests=2,
            terminal_requests=1,
            outputs_sha256=hash_file(generation / "outputs.jsonl"),
            complete_generated_grid=False,
        ),
    )
    with pytest.raises(ValueError, match="complete terminal accounting"):
        pipeline.open_confirmation(tmp_path, "method", frozen)
    assert not (base / "confirmation_opening.json").exists()


def test_confirmation_requires_one_complete_grid_and_exact_qualification(tmp_path, monkeypatch):
    base, frozen, generation = fixture(tmp_path)
    monkeypatch.setattr(pipeline, "_committed", lambda *_: "a" * 40)
    publish(
        generation / "generation_receipt.json",
        dict(
            expected_requests=1,
            terminal_requests=1,
            outputs_sha256=hash_file(generation / "outputs.jsonl"),
            complete_generated_grid=False,
        ),
    )
    with pytest.raises(ValueError, match="no complete generated grid"):
        pipeline.open_confirmation(tmp_path, "method", frozen)
    (base / "qualification_features.jsonl").write_text("changed")
    with pytest.raises(ValueError, match="bytes changed"):
        pipeline.open_confirmation(tmp_path, "method", frozen)


def test_confirmation_opening_is_one_time_and_commit_gated(tmp_path, monkeypatch):
    base, frozen, generation = fixture(tmp_path)
    publish(
        generation / "generation_receipt.json",
        dict(
            expected_requests=1,
            terminal_requests=1,
            outputs_sha256=hash_file(generation / "outputs.jsonl"),
            complete_generated_grid=True,
        ),
    )
    with pytest.raises(ValueError, match="commit the exact"):
        pipeline.open_confirmation(tmp_path, "method", frozen)
    monkeypatch.setattr(pipeline, "_committed", lambda *_: "a" * 40)
    pipeline.open_confirmation(tmp_path, "method", frozen)
    opening = (base / "confirmation_opening.json").read_bytes()
    pipeline.open_confirmation(tmp_path, "method", frozen)
    assert (base / "confirmation_opening.json").read_bytes() == opening
    (generation / "outputs.jsonl").write_text("tampered")
    with pytest.raises(ValueError, match="bound input changed"):
        pipeline.open_confirmation(tmp_path, "method", frozen)


def test_method_requires_committed_inputs(tmp_path):
    path = Path("method.py")
    (tmp_path / path).write_text("fixture")
    with pytest.raises(ValueError, match="commit the exact"):
        pipeline._committed(tmp_path, [path])
