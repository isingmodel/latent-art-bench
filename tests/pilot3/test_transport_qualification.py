from __future__ import annotations

import base64
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pytest
from PIL import Image

from latent_art_bench.io import hash_bytes, stable_hash, write_json
from latent_art_bench.pilot3.qualification import (
    TRANSPORT_QUALIFICATION_NAMESPACE,
    TRANSPORT_QUALIFICATION_PROMPT,
    QualificationAttemptLedger,
    QualificationError,
    QualificationIntentLedger,
    QualificationWindowClosed,
    build_transport_qualification_report,
    run_neutral_transport_qualification,
    validate_transport_qualification_config,
    verify_transport_qualification_report,
)
from latent_art_bench.pilot3.transport import (
    EndpointProbeEvidence,
    OAuthProcessEvidence,
    Pilot3OAuthRuntimeFingerprint,
    Pilot3OAuthRuntimeRevalidation,
    Pilot3OAuthSourceSnapshot,
    Pilot3TransportConfig,
    TransportExchange,
    canonical_image_request_bytes,
)

NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)
CHECKOUT = (Path.home() / "dev" / "openai-oauth").resolve()


def _config() -> Pilot3TransportConfig:
    return Pilot3TransportConfig(
        checkout_path=CHECKOUT,
        required_checkout_path=CHECKOUT,
        frozen_requested_labels=("gpt-image-2",),
        execution_namespace=TRANSPORT_QUALIFICATION_NAMESPACE,
    )


def _source_snapshot() -> Pilot3OAuthSourceSnapshot:
    payload = {
        "schema_version": "pilot3-oauth-source-snapshot-v1",
        "checkout_path": str(CHECKOUT),
        "git_head": "0" * 40,
        "git_remote": "https://example.invalid/openai-oauth",
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
    payload["source_snapshot_sha256"] = stable_hash(payload)
    return Pilot3OAuthSourceSnapshot.model_validate(payload)


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


def _fingerprint(config: Pilot3TransportConfig) -> Pilot3OAuthRuntimeFingerprint:
    source = _source_snapshot()
    process = OAuthProcessEvidence(
        pid=987,
        cwd=str(CHECKOUT),
        cwd_inside_checkout=True,
        command_sanitized="bun ./src/cli.ts --port 10533",
        command_sha256="1" * 64,
        executable_path="/example/bun",
        executable_sha256="2" * 64,
        runtime_version="1.3.14",
    )
    health = _probe(config.health_url, {"ok": True})
    catalog = _probe(
        config.models_url,
        {
            "object": "list",
            "model_ids": ["gpt-image-2"],
            "execution_attestation": False,
        },
    )
    payload = {
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


def _revalidation(
    config: Pilot3TransportConfig, fingerprint: Pilot3OAuthRuntimeFingerprint
) -> Pilot3OAuthRuntimeRevalidation:
    payload = {
        "schema_version": "pilot3-oauth-runtime-revalidation-v1",
        "checked_at": "2026-09-01T00:00:00Z",
        "status": "pass",
        "persisted_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "transport_config_sha256": config.config_sha256,
        "endpoint_url": config.endpoint_url,
        "frozen_requested_labels": ["gpt-image-2"],
        "current_listener_pid": fingerprint.process.pid,
        "current_process_cwd": fingerprint.process.cwd,
        "current_source_snapshot_sha256": fingerprint.source.source_snapshot_sha256,
        "current_health_response_sha256": fingerprint.health.response_body_sha256,
        "current_model_catalog_response_sha256": (
            fingerprint.model_catalog.response_body_sha256
        ),
        "checks": {"offline_fake_exact_match": True},
    }
    payload["revalidation_sha256"] = stable_hash(payload)
    return Pilot3OAuthRuntimeRevalidation.model_validate(payload)


def _png(size: tuple[int, int] = (512, 512)) -> bytes:
    handle = io.BytesIO()
    Image.new("RGB", size, (20, 40, 60)).save(handle, format="PNG")
    return handle.getvalue()


def _exchange(*, status: int = 200, image: bytes | None = None) -> TransportExchange:
    if status == 200:
        body = json.dumps(
            {"data": [{"b64_json": base64.b64encode(image or _png()).decode()}]}
        ).encode()
    else:
        body = json.dumps({"error": {"code": "overloaded", "message": "later"}}).encode()
    return TransportExchange(
        started_at=NOW,
        completed_at=NOW,
        http_status=status,
        response_body=body,
        response_body_sha256=hash_bytes(body),
        response_body_bytes=len(body),
        response_metadata={"content-type": "application/json"},
    )


class FakeTransport:
    def __init__(
        self,
        config: Pilot3TransportConfig,
        responder: Callable[[bytes], TransportExchange],
    ) -> None:
        self.config = config
        self.responder = responder
        self.requests: list[bytes] = []

    def post_once(self, request: bytes) -> TransportExchange:
        self.requests.append(request)
        return self.responder(request)


def _phase_a(path: Path, *, status: str = "pass") -> None:
    payload = {
        "record_type": "pilot3_a_vector_external_validation",
        "schema_version": "pilot3-a-vector-external-validation/1.0",
        "todo_id": "P3-T08",
        "status": status,
        "gate_checks": {"external_geometry": status == "pass"},
    }
    payload["result_sha256"] = stable_hash(payload)
    write_json(path, payload)


def _paths(tmp_path: Path) -> dict[str, Path]:
    values = {
        "phase": tmp_path / "phase_a.json",
        "authorization": tmp_path / "account_authorization.json",
        "documentation": tmp_path / "model_documentation.json",
        "freeze_b": tmp_path / "generation_gate.json",
        "intent": tmp_path / "qualification_intents.jsonl",
        "attempt": tmp_path / "qualification_attempts.jsonl",
        "output": tmp_path / "outputs",
        "artifact": tmp_path / "transport_qualification.json",
    }
    _phase_a(values["phase"])
    values["authorization"].write_text("authorized\n")
    values["documentation"].write_text("gpt-image-2 docs\n")
    return values


def _run_kwargs(tmp_path: Path, transport: FakeTransport) -> dict[str, object]:
    paths = _paths(tmp_path)
    fingerprint = _fingerprint(transport.config)
    return {
        "phase_a_result_path": paths["phase"],
        "account_authorization_evidence_path": paths["authorization"],
        "model_documentation_evidence_path": paths["documentation"],
        "freeze_b_generation_gate_path": paths["freeze_b"],
        "transport": transport,
        "fingerprint": fingerprint,
        "intent_ledger": QualificationIntentLedger(paths["intent"]),
        "attempt_ledger": QualificationAttemptLedger(paths["attempt"]),
        "output_root": paths["output"],
        "artifact_path": paths["artifact"],
        "authorization_gate": lambda _context: True,
        "runtime_revalidator": _revalidation,
    }


def test_qualification_reuses_exact_default_analytic_transport_config() -> None:
    analytic = Pilot3TransportConfig()
    qualification = _config()

    validate_transport_qualification_config(analytic)
    assert qualification.config_sha256 == analytic.config_sha256
    assert analytic.execution_namespace == "pilot3-generation-v1"
    assert analytic.endpoint_url == "http://127.0.0.1:10533/v1/images/generations"

    divergent = analytic.model_copy(
        update={"execution_namespace": "pilot3-transport-qualification-v1"}
    )
    with pytest.raises(QualificationError, match="frozen analytic namespace"):
        validate_transport_qualification_config(divergent)


def test_neutral_qualification_is_one_shot_separate_and_self_verified(
    tmp_path: Path,
) -> None:
    config = _config()
    transport = FakeTransport(config, lambda _request: _exchange())
    kwargs = _run_kwargs(tmp_path, transport)
    report = run_neutral_transport_qualification(**kwargs)  # type: ignore[arg-type]
    assert report["status"] == "pass"
    assert report["resolves_task_id"] == "P3-T11"
    assert report["outside_artist_content_grid"] is True
    assert report["analytic_grid_membership"] is False
    assert report["physical_post_count"] == 1
    assert report["retry_allowed"] is False
    assert report["requested_model_label"] == "gpt-image-2"
    assert report["dedicated_port"] == 10533
    assert report["transport"] == "~/dev/openai-oauth"
    assert report["execution_namespace"] == "pilot3-generation-v1"
    assert report["transport_config_sha256"] == config.config_sha256
    assert report["canonical_request_utf8"].encode() == transport.requests[0]
    assert report["canonical_request_byte_count"] == len(transport.requests[0])
    assert report["executed_model_claims"] is False
    assert report["output_hash_png_and_geometry_verified"] is True
    assert transport.requests == [
        canonical_image_request_bytes(
            TRANSPORT_QUALIFICATION_PROMPT,
            "gpt-image-2",
            frozen_requested_labels=("gpt-image-2",),
        )
    ]
    verify_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key
        in {
            "phase_a_result_path",
            "account_authorization_evidence_path",
            "model_documentation_evidence_path",
            "fingerprint",
            "intent_ledger",
            "attempt_ledger",
            "output_root",
        }
    }
    verify_kwargs["config"] = config
    assert verify_transport_qualification_report(
        report, **verify_kwargs  # type: ignore[arg-type]
    )["report_sha256"] == report["report_sha256"]
    with pytest.raises(QualificationWindowClosed, match="already consumed"):
        run_neutral_transport_qualification(**kwargs)  # type: ignore[arg-type]
    assert len(transport.requests) == 1


def test_phase_a_freeze_b_and_explicit_gate_close_before_any_probe_or_post(
    tmp_path: Path,
) -> None:
    config = _config()
    transport = FakeTransport(config, lambda _request: _exchange())
    kwargs = _run_kwargs(tmp_path, transport)
    calls: list[int] = []

    def probe(*_args: object) -> Pilot3OAuthRuntimeRevalidation:
        calls.append(1)
        raise AssertionError("closed window must prevent runtime probes")

    kwargs["authorization_gate"] = lambda _context: False
    kwargs["runtime_revalidator"] = probe
    with pytest.raises(QualificationWindowClosed, match="did not return True"):
        run_neutral_transport_qualification(**kwargs)  # type: ignore[arg-type]
    assert calls == [] and transport.requests == []
    assert not Path(kwargs["intent_ledger"].path).exists()  # type: ignore[union-attr]

    Path(kwargs["freeze_b_generation_gate_path"]).write_text("frozen\n")
    kwargs["authorization_gate"] = lambda _context: True
    with pytest.raises(QualificationWindowClosed, match="before the Freeze-B"):
        run_neutral_transport_qualification(**kwargs)  # type: ignore[arg-type]
    assert calls == [] and transport.requests == []

    Path(kwargs["freeze_b_generation_gate_path"]).unlink()
    _phase_a(Path(kwargs["phase_a_result_path"]), status="fail")
    with pytest.raises(QualificationWindowClosed, match="terminal P3-T08 pass"):
        run_neutral_transport_qualification(**kwargs)  # type: ignore[arg-type]
    assert calls == [] and transport.requests == []


def test_transient_http_failure_is_terminal_and_never_retried(tmp_path: Path) -> None:
    config = _config()
    transport = FakeTransport(config, lambda _request: _exchange(status=503))
    kwargs = _run_kwargs(tmp_path, transport)
    report = run_neutral_transport_qualification(**kwargs)  # type: ignore[arg-type]
    assert report["status"] == "fail"
    assert report["outcome"] == "http_failure"
    assert report["physical_post_count"] == 1
    assert len(transport.requests) == 1
    with pytest.raises(QualificationWindowClosed, match="already consumed"):
        run_neutral_transport_qualification(**kwargs)  # type: ignore[arg-type]
    assert len(transport.requests) == 1


def test_interruption_leaves_indeterminate_intent_and_prohibits_blind_resend(
    tmp_path: Path,
) -> None:
    config = _config()

    def interrupt(_request: bytes) -> TransportExchange:
        raise KeyboardInterrupt

    transport = FakeTransport(config, interrupt)
    kwargs = _run_kwargs(tmp_path, transport)
    with pytest.raises(KeyboardInterrupt):
        run_neutral_transport_qualification(**kwargs)  # type: ignore[arg-type]
    assert len(transport.requests) == 1
    intent_ledger = kwargs["intent_ledger"]
    attempt_ledger = kwargs["attempt_ledger"]
    assert intent_ledger.row() is not None  # type: ignore[union-attr]
    assert attempt_ledger.row() is None  # type: ignore[union-attr]
    with pytest.raises(QualificationWindowClosed, match="already consumed"):
        run_neutral_transport_qualification(**kwargs)  # type: ignore[arg-type]
    report = build_transport_qualification_report(
        phase_a_result_path=kwargs["phase_a_result_path"],  # type: ignore[arg-type]
        account_authorization_evidence_path=kwargs[
            "account_authorization_evidence_path"
        ],  # type: ignore[arg-type]
        model_documentation_evidence_path=kwargs[
            "model_documentation_evidence_path"
        ],  # type: ignore[arg-type]
        config=config,
        fingerprint=kwargs["fingerprint"],  # type: ignore[arg-type]
        intent_ledger=intent_ledger,  # type: ignore[arg-type]
        attempt_ledger=attempt_ledger,  # type: ignore[arg-type]
        output_root=kwargs["output_root"],  # type: ignore[arg-type]
    )
    assert report["status"] == "indeterminate"
    assert report["p3_t11_passes"] is False
    assert report["physical_post_count"] is None
    assert report["physical_post_or_indeterminate_count"] == 1
    assert len(transport.requests) == 1


def test_strict_geometry_failure_and_report_tampering_are_rejected(tmp_path: Path) -> None:
    config = _config()
    transport = FakeTransport(config, lambda _request: _exchange(image=_png((410, 410))))
    kwargs = _run_kwargs(tmp_path, transport)
    report = run_neutral_transport_qualification(**kwargs)  # type: ignore[arg-type]
    assert report["status"] == "fail"
    assert report["outcome"] == "ineligible_geometry"
    tampered = {**report, "status": "pass"}
    verify_kwargs = {
        key: value
        for key, value in kwargs.items()
        if key
        in {
            "phase_a_result_path",
            "account_authorization_evidence_path",
            "model_documentation_evidence_path",
            "fingerprint",
            "intent_ledger",
            "attempt_ledger",
            "output_root",
        }
    }
    verify_kwargs["config"] = config
    with pytest.raises(QualificationError, match="stale or tampered"):
        verify_transport_qualification_report(
            tampered, **verify_kwargs  # type: ignore[arg-type]
        )
