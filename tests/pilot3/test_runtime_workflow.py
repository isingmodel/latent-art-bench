from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from typer.testing import CliRunner

from latent_art_bench.io import hash_bytes, stable_hash
from latent_art_bench.pilot3 import execution
from latent_art_bench.pilot3.cli import app
from latent_art_bench.pilot3.qualification import (
    QualificationError,
    build_account_authorization_evidence,
    build_model_documentation_evidence,
    verify_account_authorization_evidence,
    verify_model_documentation_evidence,
)
from latent_art_bench.pilot3.transport import (
    EXPECTED_PILOT3_LAUNCHER_ENTRYPOINT,
    EXPECTED_PILOT3_OAUTH_FILE,
    EndpointProbeEvidence,
    OAuthProcessEvidence,
    Pilot3OAuthRuntimeFingerprint,
    Pilot3OAuthSourceSnapshot,
    Pilot3TransportConfig,
    RuntimeFingerprintError,
    verify_pilot3_production_runtime_fingerprint,
)


def _probe(url: str, summary: dict[str, object]) -> EndpointProbeEvidence:
    body = json.dumps(summary, sort_keys=True).encode()
    return EndpointProbeEvidence(
        url=url,
        http_status=200,
        response_body_sha256=hash_bytes(body),
        response_body_bytes=len(body),
        response_metadata={"content-type": "application/json"},
        parsed_summary=summary,
    )


def _production_fingerprint(
    config: Pilot3TransportConfig, *, launcher_models: list[str] | None = None
) -> Pilot3OAuthRuntimeFingerprint:
    source_payload: dict[str, Any] = {
        "schema_version": "pilot3-oauth-source-snapshot-v1",
        "checkout_path": str(config.checkout_path),
        "git_head": "1" * 40,
        "git_remote": "https://github.com/example/openai-oauth.git",
        "dirty": False,
        "relevant_roots": ["packages/openai-oauth/src/"],
        "files": [],
        "git_status_porcelain": "",
        "tracked_diff": "",
        "tracked_diff_sha256": hash_bytes(b""),
        "untracked_source_contents": {},
        "excluded_dirty_paths": [],
        "runtime_source_dirty_paths": [],
        "dirty_runtime_source_capture_complete": True,
    }
    source_payload["source_snapshot_sha256"] = stable_hash(source_payload)
    source = Pilot3OAuthSourceSnapshot.model_validate(source_payload)
    models = launcher_models or ["gpt-image-2"]
    process = OAuthProcessEvidence(
        pid=1234,
        cwd=str(config.checkout_path / "packages/openai-oauth"),
        cwd_inside_checkout=True,
        command_sanitized=(
            "bun ./src/cli.ts --host 127.0.0.1 --port 10533 "
            "--models gpt-image-2 --oauth-file <redacted>"
        ),
        command_sha256="2" * 64,
        executable_path="/example/bun",
        executable_sha256="3" * 64,
        runtime_version="1.3.14",
        launcher_contract_version="pilot3-openai-oauth-launcher-v1",
        launcher_entrypoint_path=str(
            (config.checkout_path / EXPECTED_PILOT3_LAUNCHER_ENTRYPOINT).resolve()
        ),
        launcher_host="127.0.0.1",
        launcher_port=10533,
        launcher_models=models,
        oauth_file_path_sha256=hashlib.sha256(
            str(EXPECTED_PILOT3_OAUTH_FILE).encode()
        ).hexdigest(),
        launcher_contract_valid=True,
    )
    health = _probe(config.health_url, {"ok": True})
    catalog = _probe(config.models_url, {"object": "list", "model_ids": ["gpt-image-2"]})
    payload: dict[str, Any] = {
        "schema_version": "pilot3-oauth-runtime-fingerprint-v1",
        "captured_at": "2026-09-01T00:00:00Z",
        "transport_config_sha256": config.config_sha256,
        "endpoint_url": config.endpoint_url,
        "frozen_requested_labels": ["gpt-image-2"],
        "executed_model_claims": False,
        "snapshot_identity_claims": False,
        "operational_model_estimand": "requested_model_label_accepted_by_oauth_endpoint",
        "source": source.model_dump(mode="json"),
        "process": process.model_dump(mode="json"),
        "health": health.model_dump(mode="json"),
        "model_catalog": catalog.model_dump(mode="json"),
        "health_ok": True,
        "model_catalog_contains_frozen_labels": True,
        "model_catalog_is_execution_attestation": False,
        "runtime_ready": True,
    }
    payload["fingerprint_sha256"] = stable_hash(payload)
    return Pilot3OAuthRuntimeFingerprint.model_validate(payload)


def test_production_commands_are_exposed() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in (
        "authorize-transport",
        "capture-oauth-runtime",
        "qualify-transport",
        "run-generation",
    ):
        assert command in result.stdout


def test_strict_authorization_documentation_and_launcher_contract() -> None:
    config = Pilot3TransportConfig()
    fingerprint = _production_fingerprint(config)
    verify_pilot3_production_runtime_fingerprint(fingerprint, config=config)

    authorization = build_account_authorization_evidence(config)
    assert authorization.user_allowed_image_model_family == (
        "gpt-image-1",
        "gpt-image-2",
    )
    assert authorization.scheduled_requested_labels == ("gpt-image-2",)
    verify_account_authorization_evidence(
        authorization.model_dump(mode="json"), config
    )
    tampered_authorization = authorization.model_dump(mode="json")
    tampered_authorization["direct_api_allowed"] = True
    tampered_authorization["evidence_sha256"] = stable_hash(
        {k: v for k, v in tampered_authorization.items() if k != "evidence_sha256"}
    )
    with pytest.raises((QualificationError, ValueError)):
        verify_account_authorization_evidence(tampered_authorization, config)

    documentation = build_model_documentation_evidence(config, fingerprint)
    assert documentation.documentation_accessed_date == "2026-09-01"
    assert documentation.endpoint_accepted_image_aliases == (
        "gpt-image-1",
        "gpt-image-2",
    )
    assert documentation.models_flag_is_endpoint_allowlist is False
    assert documentation.pilot3_client_canonical_allowed_labels == ("gpt-image-2",)
    verify_model_documentation_evidence(
        documentation.model_dump(mode="json"), config, fingerprint
    )
    with pytest.raises(RuntimeFingerprintError):
        verify_pilot3_production_runtime_fingerprint(
            _production_fingerprint(config, launcher_models=["gpt-image-1"]),
            config=config,
        )


def test_authorization_writer_is_offline_and_refuses_divergence(tmp_path: Path) -> None:
    result = execution.write_qualification_authorization(tmp_path)
    path = tmp_path / execution.CANONICAL_PATHS["account_authorization"]
    assert json.loads(path.read_text()) == result
    path.write_text('{"tampered":true}\n', encoding="utf-8")
    with pytest.raises(execution.Pilot3ExecutionError, match="differs"):
        execution.write_qualification_authorization(tmp_path)


def test_qualification_closed_gate_never_constructs_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for key in ("a_vector_external", "account_authorization", "model_documentation"):
        path = tmp_path / execution.CANONICAL_PATHS[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(execution, "_load_runtime_fingerprint", lambda _root: object())
    monkeypatch.setattr(
        execution, "_verify_strict_qualification_evidence", lambda *_args: ({}, {})
    )
    monkeypatch.setattr(
        execution,
        "verify_transport_qualification_window",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            execution.Pilot3ExecutionError("closed committed gate")
        ),
    )

    class ForbiddenTransport:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            raise AssertionError("closed gate constructed a network transport")

    monkeypatch.setattr(execution, "Pilot3OAuthTransport", ForbiddenTransport)
    with pytest.raises(execution.Pilot3ExecutionError, match="closed committed gate"):
        execution.run_canonical_transport_qualification(tmp_path)


class _FakeTransport:
    enters = 0

    def __init__(self, config: object) -> None:
        self.config = config

    def __enter__(self) -> "_FakeTransport":
        type(self).enters += 1
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class _FakeContext:
    def model_dump(self, *, mode: str) -> dict[str, str]:
        assert mode == "json"
        return {"context": "frozen"}


def _patch_generation_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    global_stop: bool = False,
) -> SimpleNamespace:
    stop_path = tmp_path / "artifacts/pilot_3/global-stop.jsonl"
    if global_stop:
        stop_path.parent.mkdir(parents=True, exist_ok=True)
        stop_path.write_text("stopped\n", encoding="utf-8")
    stop = SimpleNamespace(path=stop_path)
    runtime = ([object()], object(), object(), object(), object(), object(), object(), stop)
    monkeypatch.setattr(execution, "verify_generation_gate", lambda *_a, **_k: {})
    monkeypatch.setattr(execution, "_production_generation_runtime", lambda _r: runtime)
    monkeypatch.setattr(
        execution, "_load_or_persist_generation_context", lambda *_a, **_k: _FakeContext()
    )
    monkeypatch.setattr(execution, "generation_execution_gate", lambda _r: object())
    monkeypatch.setattr(execution, "generation_request_gate", lambda _r: object())
    monkeypatch.setattr(execution, "Pilot3OAuthTransport", _FakeTransport)
    monkeypatch.setattr(
        execution,
        "verify_generation_execution",
        lambda report, **_kwargs: dict(report),
    )
    return stop


def _execution_report() -> dict[str, object]:
    return {
        "status": "complete",
        "execution_gate_context": {"context": "frozen"},
        "attempt_count": 320,
        "global_stop_triggered": False,
        "report_sha256": "a" * 64,
    }


def test_generation_persists_once_and_resume_is_offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _FakeTransport.enters = 0
    _patch_generation_runtime(tmp_path, monkeypatch)
    calls: list[int] = []

    def run(*_args: object, **kwargs: object) -> dict[str, object]:
        calls.append(1)
        assert kwargs["execution_context"].model_dump(mode="json") == {
            "context": "frozen"
        }
        assert kwargs["execution_gate"] is not None
        assert kwargs["request_gate"] is not None
        return _execution_report()

    monkeypatch.setattr(execution, "run_generation_grid", run)
    first = execution.run_canonical_generation_grid(tmp_path)
    assert first == _execution_report()
    report_path = tmp_path / execution.CANONICAL_PATHS["generation_execution"]
    assert json.loads(report_path.read_text()) == first
    assert calls == [1] and _FakeTransport.enters == 1

    second = execution.run_canonical_generation_grid(tmp_path)
    assert second == first
    assert calls == [1] and _FakeTransport.enters == 1

    divergent = dict(first)
    divergent["execution_gate_context"] = {"context": "tampered"}
    report_path.write_text(json.dumps(divergent) + "\n", encoding="utf-8")
    with pytest.raises(execution.Pilot3ExecutionError, match="durable execution context"):
        execution.run_canonical_generation_grid(tmp_path)
    assert calls == [1] and _FakeTransport.enters == 1


def test_global_stop_crash_reconstructs_without_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _FakeTransport.enters = 0
    _patch_generation_runtime(tmp_path, monkeypatch, global_stop=True)
    expected = {
        **_execution_report(),
        "status": "global_stop_complete",
        "global_stop_triggered": True,
    }
    reconstruction_calls: list[int] = []

    def reconstruct(*_args: object, **_kwargs: object) -> dict[str, object]:
        reconstruction_calls.append(1)
        return expected

    monkeypatch.setattr(execution, "reconstruct_generation_execution_report", reconstruct)
    monkeypatch.setattr(
        execution,
        "run_generation_grid",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("global-stop recovery attempted generation")
        ),
    )
    assert execution.run_canonical_generation_grid(tmp_path) == expected
    assert reconstruction_calls == [1]
    assert _FakeTransport.enters == 0


def test_generation_lock_rejects_concurrent_runner(tmp_path: Path) -> None:
    lock = tmp_path / execution.CANONICAL_PATHS["generation_execution_lock"]
    with execution._exclusive_workflow_lock(lock, label="Pilot-3 generation"):
        with pytest.raises(execution.Pilot3ExecutionError, match="holds the run lock"):
            execution.run_canonical_generation_grid(tmp_path)
