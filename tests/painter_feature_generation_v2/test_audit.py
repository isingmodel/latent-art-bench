import subprocess

from latent_art_bench.io import hash_file
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    WORKSPACE,
    append_event,
    publish,
)
from latent_art_bench.painter_feature_generation_v2.audit import audit


def test_raw_bytes_and_chain_are_both_audited(tmp_path):
    raw = tmp_path / WORKSPACE / "audit-fixture" / "raw" / "fixture"
    raw.parent.mkdir(parents=True)
    raw.write_bytes(b"response fixture")
    append_event(
        tmp_path / MANIFESTS / "audit-fixture" / "assessment_events.jsonl",
        dict(kind="response", raw_path=str(raw.relative_to(tmp_path)), raw_sha256=hash_file(raw)),
    )
    assert audit(tmp_path)["overall"] == "OK"
    raw.write_bytes(b"tampered")
    result = audit(tmp_path)
    assert result["overall"] == "FAIL"
    assert result["failed"] == 1


def test_bound_input_uses_recorded_commit(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    source = tmp_path / "method.txt"
    source.write_text("frozen code")
    expected = hash_file(source)
    subprocess.run(["git", "add", "method.txt"], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.test",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=tmp_path,
        check=True,
    )
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    publish(
        tmp_path / MANIFESTS / "audit-fixture" / "freeze.json",
        dict(recorded_git_commit=commit, inputs=[dict(path="method.txt", sha256=expected)]),
    )
    source.write_text("future implementation")
    assert audit(tmp_path)["overall"] == "OK"


def test_missing_and_outside_bound_input_fail_closed(tmp_path):
    publish(
        tmp_path / MANIFESTS / "audit-fixture" / "freeze.json",
        dict(inputs=[dict(path="../outside", sha256="0" * 64)]),
    )
    assert audit(tmp_path)["failed"] == 1


def test_invalid_recording_commit_is_not_excused_by_current_bytes(tmp_path):
    source = tmp_path / "method.txt"
    source.write_text("fixture")
    publish(
        tmp_path / MANIFESTS / "audit-fixture" / "freeze.json",
        dict(
            recorded_git_commit="0" * 40, inputs=[dict(path="method.txt", sha256=hash_file(source))]
        ),
    )
    assert audit(tmp_path)["failed"] == 1
