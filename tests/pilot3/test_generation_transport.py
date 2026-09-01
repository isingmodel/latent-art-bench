from __future__ import annotations

import base64
import io
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

import httpx
import pytest
from PIL import Image
from pydantic import ValidationError

from latent_art_bench.io import hash_bytes, stable_hash
from latent_art_bench.pilot3.generation import (
    FIXED_RETRY_DELAYS_SECONDS,
    MAX_PHYSICAL_POSTS_PER_CELL,
    AppendOnlyAttemptLedger,
    AppendOnlyPostIntentLedger,
    AppendOnlyRuntimeRevalidationLedger,
    ExecutionGateClosed,
    GenerationGlobalStopDisposition,
    GenerationGlobalStopLedger,
    RequestGateClosed,
    adapt_t12_manifests_to_generation,
    build_generation_schedule,
    generate_cell,
    generation_completion_report,
    make_generation_cell,
    reconcile_unmatched_post_intents,
    run_generation_grid,
    select_runtime_image_preflight_cells,
    verified_attempt_receipt_manifest,
    verify_generation_execution,
)
from latent_art_bench.pilot3.transport import (
    EndpointProbeEvidence,
    OAuthProcessEvidence,
    Pilot3OAuthRuntimeFingerprint,
    Pilot3OAuthRuntimeRevalidation,
    Pilot3OAuthSourceSnapshot,
    Pilot3OAuthTransport,
    Pilot3TransportConfig,
    RuntimeFingerprintError,
    TransportConfigurationError,
    TransportExchange,
    canonical_image_request_bytes,
    validate_frozen_requested_labels,
    verify_pilot3_oauth_runtime_fingerprint,
)

NOW = datetime(2026, 9, 1, tzinfo=timezone.utc)


def _config(tmp_path: Path, labels: Sequence[str] = ("gpt-image-2",)) -> Pilot3TransportConfig:
    checkout = tmp_path / "openai-oauth"
    checkout.mkdir(exist_ok=True)
    return Pilot3TransportConfig(
        checkout_path=checkout,
        required_checkout_path=checkout,
        frozen_requested_labels=tuple(labels),
    )


def _source_snapshot(checkout: Path) -> Pilot3OAuthSourceSnapshot:
    payload = {
        "schema_version": "pilot3-oauth-source-snapshot-v1",
        "checkout_path": str(checkout.resolve()),
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
    source = _source_snapshot(config.checkout_path)
    process = OAuthProcessEvidence(
        pid=1234,
        cwd=str(config.checkout_path),
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
        {"object": "list", "model_ids": list(config.frozen_requested_labels)},
    )
    payload = {
        "schema_version": "pilot3-oauth-runtime-fingerprint-v1",
        "captured_at": NOW.isoformat().replace("+00:00", "Z"),
        "transport_config_sha256": config.config_sha256,
        "endpoint_url": config.endpoint_url,
        "frozen_requested_labels": list(config.frozen_requested_labels),
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
        "checked_at": NOW.isoformat().replace("+00:00", "Z"),
        "status": "pass",
        "persisted_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "transport_config_sha256": config.config_sha256,
        "endpoint_url": config.endpoint_url,
        "frozen_requested_labels": list(config.frozen_requested_labels),
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


def _png_bytes(size: tuple[int, int] = (512, 512), *, image_format: str = "PNG") -> bytes:
    handle = io.BytesIO()
    Image.new("RGB", size, (23, 45, 67)).save(handle, format=image_format)
    return handle.getvalue()


def _exchange(
    *,
    status: int = 200,
    body: bytes | None = None,
    image: bytes | None = None,
    transport_error: bool = False,
) -> TransportExchange:
    if transport_error:
        return TransportExchange(
            started_at=NOW,
            completed_at=NOW,
            transport_error_kind="ConnectError",
            transport_error_reason="connection reset",
            transport_error_retryable=True,
        )
    if body is None:
        encoded = base64.b64encode(image or _png_bytes()).decode()
        body = json.dumps({"data": [{"b64_json": encoded}], "usage": {"images": 1}}).encode()
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
        responder: Callable[[int, bytes], TransportExchange],
    ) -> None:
        self.config = config
        self._responder = responder
        self._lock = threading.Lock()
        self.requests: list[bytes] = []

    def post_once(self, canonical_request: bytes) -> TransportExchange:
        with self._lock:
            index = len(self.requests)
            self.requests.append(canonical_request)
        return self._responder(index, canonical_request)


def _cell(
    model: str = "gpt-image-2",
    *,
    prompt_id: str = "control-1",
    content_block_id: str = "block-1",
    control: bool = True,
    repetition: int = 0,
):
    return make_generation_cell(
        prompt_id=prompt_id,
        content_id=prompt_id,
        content_block_id=content_block_id,
        prompt_pair_id=f"pair-{prompt_id}",
        template_id="template-v1",
        prompt_text=f"A harmless geometric study {prompt_id}",
        artist_free_control=control,
        target_artist_id=None if control else "artist-1",
        target_artist_name=None if control else "Artist One",
        requested_model_label=model,  # type: ignore[arg-type]
        repetition=repetition,
    )


def _ledgers(tmp_path: Path):
    return (
        AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl"),
        AppendOnlyPostIntentLedger(tmp_path / "intents.jsonl"),
        AppendOnlyRuntimeRevalidationLedger(tmp_path / "runtime.jsonl"),
    )


def _global_stops(tmp_path: Path) -> GenerationGlobalStopLedger:
    return GenerationGlobalStopLedger(tmp_path / "global_stops.jsonl")


def _t12_plan(
    config: Pilot3TransportConfig,
    *,
    target_count: int = 0,
    max_parallel: int = 2,
    include_rows: bool = False,
):
    """Build a tiny canonical T12 fixture with a sequence-one control."""

    block_id = "block-1"
    pair_basis = stable_hash({"block": block_id, "template": "test"})
    prompt_rows: list[dict[str, object]] = []
    prompt_specs = [("control", None, None)] + [
        (f"target-{index}", f"artist-{index}", f"neighbor-{index}")
        for index in range(1, target_count + 1)
    ]
    for suffix, artist_id, neighbor_id in prompt_specs:
        control = artist_id is None
        prompt_id = f"p3-b01-{suffix}"
        prompt: dict[str, object] = {
            "record_type": "pilot3_prompt",
            "schema_version": "pilot3-prompt/1.0",
            "prompt_id": prompt_id,
            "content_block_id": block_id,
            "content_block_rank": 1,
            "condition": "artist_free_control" if control else "named_artist",
            "target_artist_id": artist_id,
            "target_artist_name": None if control else f"Artist {suffix.split('-')[-1]}",
            "neighbor_artist_id": neighbor_id,
            "paired_control_prompt_id": None if control else "p3-b01-control",
            "pair_basis_sha256": pair_basis,
            "prompt_text": f"A harmless original landscape study for {suffix}",
            "content_annotations": ["landscape", "test"],
            "visual_selection_allowed": False,
        }
        prompt["prompt_sha256"] = stable_hash(prompt)
        prompt_rows.append(prompt)

    schedule_rows: list[dict[str, object]] = []
    for prompt in prompt_rows:
        control = prompt["condition"] == "artist_free_control"
        request_id = f"p3-b01-r01-{str(prompt['prompt_id']).removeprefix('p3-b01-')}"
        body = json.loads(
            canonical_image_request_bytes(
                str(prompt["prompt_text"]),
                "gpt-image-2",
                frozen_requested_labels=config.frozen_requested_labels,
            )
        )
        row: dict[str, object] = {
            "record_type": "pilot3_scheduled_request",
            "schema_version": "pilot3-scheduled-request/1.0",
            "request_id": request_id,
            "prompt_id": prompt["prompt_id"],
            "prompt_sha256": prompt["prompt_sha256"],
            "content_block_id": block_id,
            "content_block_rank": 1,
            "condition": prompt["condition"],
            "target_artist_id": prompt["target_artist_id"],
            "neighbor_artist_id": prompt["neighbor_artist_id"],
            "paired_control_request_id": (
                None if control else "p3-b01-r01-control"
            ),
            "repetition": 1,
            "requested_model_label": "gpt-image-2",
            "transport": "~/dev/openai-oauth",
            "endpoint": "/v1/images/generations",
            "request_body": body,
            "semantic_request_sha256": stable_hash(body),
        }
        row["execution_order_sha256"] = stable_hash(
            {
                "namespace": "pilot3-assignment-order-v1",
                "seed": 20260903,
                "request_id": request_id,
                "semantic_request_sha256": row["semantic_request_sha256"],
            }
        )
        schedule_rows.append(row)
    schedule_rows = [schedule_rows[0], *sorted(
        schedule_rows[1:],
        key=lambda row: (row["execution_order_sha256"], row["request_id"]),
    )]
    for sequence, row in enumerate(schedule_rows, 1):
        row["sequence"] = sequence
        row["schedule_row_sha256"] = stable_hash(row)
    plan = adapt_t12_manifests_to_generation(
        prompt_rows,
        schedule_rows,
        transport_config=config,
        max_parallel=max_parallel,
    )
    if include_rows:
        return (*plan, prompt_rows, schedule_rows)
    return plan


def test_config_and_canonical_request_reject_snapshot_and_nonloopback(tmp_path: Path) -> None:
    config = _config(tmp_path, ("gpt-image-1", "gpt-image-2"))
    request = canonical_image_request_bytes(
        "  keep exact prompt whitespace  ",
        "gpt-image-2",
        frozen_requested_labels=config.frozen_requested_labels,
    )
    assert request == (
        b'{"model":"gpt-image-2","n":1,"output_format":"png",'
        b'"prompt":"  keep exact prompt whitespace  ","quality":"low","size":"auto"}'
    )
    with pytest.raises(TransportConfigurationError):
        canonical_image_request_bytes(  # type: ignore[arg-type]
            "prompt", "gpt-image-2-2026-04-21"
        )
    with pytest.raises(TransportConfigurationError):
        validate_frozen_requested_labels(("gpt-image-2", "gpt-image-1"))
    with pytest.raises(ValidationError):
        Pilot3TransportConfig(
            base_url="https://example.com/v1",
            dedicated_port=443,
            checkout_path=config.checkout_path,
            required_checkout_path=config.checkout_path,
        )


def test_transport_performs_exactly_one_post_and_preserves_safe_headers(tmp_path: Path) -> None:
    config = _config(tmp_path)
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            503,
            json={"error": {"code": "overloaded", "message": "later"}},
            headers={"x-request-id": "req-safe", "authorization": "secret"},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot3OAuthTransport(config, client=client)
    request = canonical_image_request_bytes(
        "harmless", "gpt-image-2", frozen_requested_labels=("gpt-image-2",)
    )
    exchange = transport.post_once(request)
    assert len(seen) == 1
    assert seen[0].url.path == "/v1/images/generations"
    assert seen[0].content == request
    assert exchange.http_status == 503
    assert exchange.response_metadata == {
        "content-type": "application/json",
        "x-request-id": "req-safe",
    }


def test_transport_loss_after_send_is_never_declared_retryable(tmp_path: Path) -> None:
    config = _config(tmp_path)
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        raise httpx.ReadError("connection lost after request began", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot3OAuthTransport(config, client=client)
    request = canonical_image_request_bytes(
        "harmless", "gpt-image-2", frozen_requested_labels=("gpt-image-2",)
    )
    exchange = transport.post_once(request)
    assert len(seen) == 1
    assert exchange.transport_error_kind == "ReadError"
    assert exchange.transport_error_retryable is False


def test_runtime_fingerprint_is_self_hashed_and_subset_bound(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    verify_pilot3_oauth_runtime_fingerprint(fingerprint, config=config)
    other = _config(tmp_path, ("gpt-image-1", "gpt-image-2"))
    with pytest.raises(RuntimeError, match="different transport config"):
        verify_pilot3_oauth_runtime_fingerprint(fingerprint, config=other)


def test_schedule_is_deterministic_bounded_and_marks_each_runtime_preflight_label(
    tmp_path: Path,
) -> None:
    labels = ("gpt-image-1", "gpt-image-2")
    cells = [
        _cell(label, prompt_id=f"control-{label}") for label in labels
    ] + [
        _cell(labels[index % 2], prompt_id=f"target-{index}", control=False)
        for index in range(5)
    ]
    first = build_generation_schedule(
        cells, frozen_requested_labels=labels, seed=42, max_parallel=3
    )
    second = build_generation_schedule(
        list(reversed(cells)), frozen_requested_labels=labels, seed=42, max_parallel=3
    )
    changed = build_generation_schedule(
        cells, frozen_requested_labels=labels, seed=43, max_parallel=3
    )
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert first.schedule_sha256 != changed.schedule_sha256
    assert [
        entry.runtime_image_preflight_rank
        for entry in first.entries
        if entry.runtime_image_preflight_rank is not None
    ] != []
    assert sorted(
        entry.runtime_image_preflight_rank
        for entry in first.entries
        if entry.runtime_image_preflight_rank is not None
    ) == [1, 2]
    assert max(
        sum(entry.batch_rank == rank for entry in first.entries)
        for rank in range(1, first.batch_count + 1)
    ) <= 3


def test_t12_adapter_preserves_exact_sequence_pairing_and_repetition(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    cells, schedule, prompts, rows = _t12_plan(
        config, target_count=2, include_rows=True
    )
    assert schedule.ordering_basis == "t12_canonical_sequence"
    assert [cell.source_sequence for cell in cells] == [1, 2, 3]
    assert [cell.source_request_id for cell in cells] == [
        row["request_id"] for row in rows
    ]
    assert all(cell.source_repetition == 1 and cell.repetition == 0 for cell in cells)
    assert cells[1].source_paired_control_request_id == cells[0].source_request_id
    assert cells[1].prompt_pair_id == cells[0].source_request_id
    assert cells[1].source_neighbor_artist_id == rows[1]["neighbor_artist_id"]
    assert [entry.source_sequence for entry in schedule.entries] == [1, 2, 3]
    assert select_runtime_image_preflight_cells(cells, ("gpt-image-2",))[0] is cells[0]

    with pytest.raises(ValueError, match="exact contiguous canonical sequence"):
        adapt_t12_manifests_to_generation(
            prompts,
            list(reversed(rows)),
            transport_config=config,
        )

    tampered = [dict(row) for row in rows]
    tampered[1]["paired_control_request_id"] = "missing-control"
    tampered[1].pop("schedule_row_sha256")
    tampered[1]["schedule_row_sha256"] = stable_hash(tampered[1])
    with pytest.raises(ValueError, match="paired control request does not exist"):
        adapt_t12_manifests_to_generation(
            prompts,
            tampered,
            transport_config=config,
        )


def test_success_is_content_addressed_receipted_and_idempotent(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = _cell()
    ledger, intents, _ = _ledgers(tmp_path)
    transport = FakeTransport(config, lambda _index, _request: _exchange())
    result = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intents,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        request_gate=lambda _context: True,
        runtime_revalidator=_revalidation,
        sleep=lambda _seconds: None,
    )
    assert result.outcome == "succeeded"
    assert result.actual_width == result.actual_height == 512
    assert result.actual_format == "png"
    assert Path(result.output_path or "").name == f"{result.output_sha256}.png"
    assert len(transport.requests) == 1
    intent = intents.rows()[0]
    assert (
        intent.pre_post_runtime_revalidation.persisted_fingerprint_sha256
        == fingerprint.fingerprint_sha256
    )
    assert (
        result.pre_post_runtime_revalidation.revalidation_sha256
        == intent.pre_post_runtime_revalidation.revalidation_sha256
    )
    receipt_manifest = verified_attempt_receipt_manifest(ledger)
    assert receipt_manifest["attempt_receipt_count"] == 1
    repeated = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intents,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        request_gate=lambda _context: True,
        runtime_revalidator=_revalidation,
        sleep=lambda _seconds: None,
    )
    assert repeated.attempt_id == result.attempt_id
    assert len(transport.requests) == 1

    tampered = intent.model_dump(mode="json")
    tampered["pre_post_runtime_revalidation"]["endpoint_url"] = (
        "http://127.0.0.1:10534/v1/images/generations"
    )
    with pytest.raises(ValidationError):
        type(intent).model_validate(tampered)


def test_direct_cell_has_no_ungated_post_fallback(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    ledger, intents, _ = _ledgers(tmp_path)
    transport = FakeTransport(config, lambda _index, _request: _exchange())
    with pytest.raises(RequestGateClosed):
        generate_cell(
            _cell(),
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intents,
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            request_gate=None,
            runtime_revalidator=_revalidation,
            sleep=lambda _seconds: None,
        )
    assert transport.requests == []
    assert intents.rows() == []
    assert ledger.rows() == []


def test_failed_per_post_runtime_revalidation_writes_no_intent_or_attempt(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    ledger, intents, _ = _ledgers(tmp_path)
    transport = FakeTransport(config, lambda _index, _request: _exchange())
    gate_calls: list[int] = []

    def fail_revalidation(*_args: object) -> Pilot3OAuthRuntimeRevalidation:
        raise RuntimeFingerprintError("live runtime changed")

    with pytest.raises(RuntimeFingerprintError, match="live runtime changed"):
        generate_cell(
            _cell(),
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intents,
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            request_gate=lambda _context: not gate_calls.append(1),
            runtime_revalidator=fail_revalidation,
            sleep=lambda _seconds: None,
        )
    assert gate_calls == []
    assert transport.requests == []
    assert intents.rows() == []
    assert ledger.rows() == []


def test_transient_failures_use_exact_fixed_waits_then_succeed(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = _cell()
    ledger, intents, _ = _ledgers(tmp_path)
    responses = [
        _exchange(transport_error=True),
        _exchange(
            status=429,
            body=json.dumps({"error": {"code": "rate_limit", "message": "later"}}).encode(),
        ),
        _exchange(),
    ]
    transport = FakeTransport(config, lambda index, _request: responses[index])
    waits: list[float] = []
    revalidation_calls: list[int] = []

    def revalidate_each_post(
        runtime_config: Pilot3TransportConfig,
        runtime_fingerprint: Pilot3OAuthRuntimeFingerprint,
    ) -> Pilot3OAuthRuntimeRevalidation:
        revalidation_calls.append(1)
        return _revalidation(runtime_config, runtime_fingerprint)

    result = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intents,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        request_gate=lambda _context: True,
        runtime_revalidator=revalidate_each_post,
        sleep=waits.append,
    )
    assert result.outcome == "succeeded"
    assert [row.retry_classification for row in ledger.rows()] == [
        "retryable_transport",
        "retryable_http_status",
        "not_retryable_success",
    ]
    assert waits == [1.0, 2.0]
    assert len(revalidation_calls) == 3
    assert len(intents.rows()) == 3
    assert all(
        row.pre_post_runtime_revalidation.persisted_fingerprint_sha256
        == fingerprint.fingerprint_sha256
        for row in intents.rows()
    )


def test_ambiguous_post_transport_loss_is_terminal_and_never_resent(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = _cell()
    ledger, intents, _ = _ledgers(tmp_path)
    exchange = TransportExchange(
        started_at=NOW,
        completed_at=NOW,
        transport_error_kind="ReadError",
        transport_error_reason="connection lost after request began",
        transport_error_retryable=False,
    )
    transport = FakeTransport(config, lambda _index, _request: exchange)
    result = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intents,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        request_gate=lambda _context: True,
        runtime_revalidator=_revalidation,
        sleep=lambda _seconds: pytest.fail("ambiguous POSTs must not retry"),
    )
    assert result.outcome == "terminal_failure"
    assert result.retry_classification == (
        "not_retryable_indeterminate_after_interruption"
    )
    assert result.failure_kind == "indeterminate_after_interruption"
    assert result.post_exchange_observed is False
    assert len(transport.requests) == 1
    assert len(intents.rows()) == 1
    assert len(ledger.rows()) == 1


def test_retry_cap_is_exactly_ten_and_completion_is_terminal(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = _cell()
    ledger, intents, _ = _ledgers(tmp_path)
    body = json.dumps({"error": {"code": "upstream", "message": "later"}}).encode()
    transport = FakeTransport(
        config, lambda _index, _request: _exchange(status=503, body=body)
    )
    waits: list[float] = []
    result = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intents,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        request_gate=lambda _context: True,
        runtime_revalidator=_revalidation,
        sleep=waits.append,
    )
    assert result.outcome == "retryable_failure"
    assert len(transport.requests) == MAX_PHYSICAL_POSTS_PER_CELL
    assert waits == list(FIXED_RETRY_DELAYS_SECONDS)
    completion = generation_completion_report(
        [cell], ledger.rows(), frozen_requested_labels=("gpt-image-2",)
    )
    assert completion["all_cells_terminal"] is True
    assert completion["cell_dispositions"][cell.cell_id] == "failed_after_retry_cap"


def test_refusal_and_other_4xx_are_terminal_and_never_retried(tmp_path: Path) -> None:
    for name, status, error, expected_outcome, expected_class in [
        (
            "refusal",
            429,
            {"code": "moderation_blocked", "message": "safety refusal Bearer abcdefghijklmnop"},
            "refused",
            "not_retryable_refusal",
        ),
        (
            "bad-request",
            400,
            {"code": "invalid_parameter", "message": "bad size"},
            "terminal_failure",
            "not_retryable_http_status",
        ),
    ]:
        case = tmp_path / name
        case.mkdir()
        config = _config(case)
        fingerprint = _fingerprint(config)
        ledger, intents, _ = _ledgers(case)
        body = json.dumps({"error": error}).encode()
        transport = FakeTransport(
            config, lambda _index, _request: _exchange(status=status, body=body)
        )
        result = generate_cell(
            _cell(),
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intents,
            fingerprint=fingerprint,
            output_dir=case / "outputs",
            request_gate=lambda _context: True,
            runtime_revalidator=_revalidation,
            sleep=lambda _seconds: pytest.fail("terminal errors must not retry"),
        )
        assert result.outcome == expected_outcome
        assert result.retry_classification == expected_class
        assert len(transport.requests) == 1
        assert "abcdefghijklmnop" not in (result.failure_reason or "")


def test_interruption_is_indeterminate_and_never_blindly_resent(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = _cell()
    ledger, intents, _ = _ledgers(tmp_path)

    def interrupt(_index: int, _request: bytes) -> TransportExchange:
        raise KeyboardInterrupt

    transport = FakeTransport(config, interrupt)
    with pytest.raises(KeyboardInterrupt):
        generate_cell(
            cell,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intents,
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            request_gate=lambda _context: True,
            runtime_revalidator=_revalidation,
            sleep=lambda _seconds: None,
        )
    assert len(intents.rows()) == 1
    assert ledger.rows() == []
    reconciled = reconcile_unmatched_post_intents(
        [cell], ledger, intents, fingerprint
    )
    assert len(reconciled) == 1
    assert reconciled[0].failure_kind == "indeterminate_after_interruption"
    assert reconciled[0].post_exchange_observed is False
    assert (
        reconciled[0].pre_post_runtime_revalidation.revalidation_sha256
        == intents.rows()[0].pre_post_runtime_revalidation.revalidation_sha256
    )
    repeated = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intents,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        request_gate=lambda _context: True,
        runtime_revalidator=_revalidation,
        sleep=lambda _seconds: None,
    )
    assert repeated.attempt_id == reconciled[0].attempt_id
    assert len(transport.requests) == 1


@pytest.mark.parametrize(
    ("image", "failure_kind"),
    [
        (_png_bytes((410, 410)), "ineligible_kim_geometry"),
        (_png_bytes((900, 400)), "ineligible_kim_geometry"),
        (_png_bytes((512, 512), image_format="JPEG"), "unexpected_output_format"),
    ],
)
def test_invalid_format_or_strict_kim_geometry_is_terminal(
    tmp_path: Path, image: bytes, failure_kind: str
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    ledger, intents, _ = _ledgers(tmp_path)
    transport = FakeTransport(
        config, lambda _index, _request: _exchange(image=image)
    )
    result = generate_cell(
        _cell(),
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intents,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        request_gate=lambda _context: True,
        runtime_revalidator=_revalidation,
        sleep=lambda _seconds: pytest.fail("invalid outputs must not retry"),
    )
    assert result.outcome == "terminal_failure"
    assert result.failure_kind == failure_kind
    assert len(transport.requests) == 1


def test_closed_gate_prevents_probe_write_and_post(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells, schedule = _t12_plan(config)
    ledger, intents, runtime = _ledgers(tmp_path)
    transport = FakeTransport(config, lambda _index, _request: _exchange())
    revalidation_calls: list[int] = []

    def should_not_revalidate(*_args):
        revalidation_calls.append(1)
        raise AssertionError("closed gate must prevent runtime probes")

    with pytest.raises(ExecutionGateClosed):
        run_generation_grid(
            cells,
            schedule=schedule,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intents,
            runtime_revalidation_ledger=runtime,
            global_stop_ledger=_global_stops(tmp_path),
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            execution_gate=lambda _context: False,
            request_gate=lambda _context: True,
            runtime_revalidator=should_not_revalidate,
        )
    assert transport.requests == []
    assert revalidation_calls == []
    assert not ledger.path.exists()
    assert not intents.path.exists()
    assert not runtime.path.exists()


def test_grid_runner_revalidates_batches_and_offline_verifier_passes(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells, schedule = _t12_plan(config, target_count=3, max_parallel=2)
    ledger, intents, runtime = _ledgers(tmp_path)
    transport = FakeTransport(config, lambda _index, _request: _exchange())
    gate_contexts = []
    report = run_generation_grid(
        cells,
        schedule=schedule,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intents,
        runtime_revalidation_ledger=runtime,
        global_stop_ledger=_global_stops(tmp_path),
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        execution_gate=lambda context: not gate_contexts.append(context),
        request_gate=lambda _context: True,
        sleep=lambda _seconds: None,
        runtime_revalidator=_revalidation,
    )
    assert report["status"] == "complete"
    assert report["generation_completion"]["all_cells_succeeded"] is True
    assert len(transport.requests) == len(cells)
    assert report["per_physical_post_runtime_revalidation_required"] is True
    assert report["pre_post_runtime_revalidation_count"] == len(transport.requests)
    assert all(
        intent.pre_post_runtime_revalidation.revalidation_sha256
        for intent in intents.rows()
    )
    assert len(gate_contexts) == 1
    assert runtime.rows()[0].phase == "start_before_runtime_image_preflight"
    assert runtime.rows()[-1].phase == "end_after_all_batches"
    verified = verify_generation_execution(
        report,
        cells=cells,
        schedule=schedule,
        config=config,
        fingerprint=fingerprint,
        ledger=ledger,
        post_intent_ledger=intents,
        runtime_revalidation_ledger=runtime,
        global_stop_ledger=_global_stops(tmp_path),
    )
    assert verified["report_sha256"] == report["report_sha256"]
    assert all(
        "pilot2" not in json.dumps(row.model_dump(mode="json"))
        for row in [*ledger.rows(), *intents.rows(), *runtime.rows()]
    )


def test_request_gate_fails_before_next_intent_after_between_request_mutation(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells, schedule = _t12_plan(config, target_count=2, max_parallel=2)
    ledger, intents, runtime = _ledgers(tmp_path)
    closure = {"committed_clean": True}

    def exchange(_index: int, _request: bytes) -> TransportExchange:
        closure["committed_clean"] = False
        return _exchange()

    contexts = []

    def request_gate(context) -> bool:
        contexts.append(context)
        return closure["committed_clean"]

    transport = FakeTransport(config, exchange)
    with pytest.raises(RequestGateClosed):
        run_generation_grid(
            cells,
            schedule=schedule,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intents,
            runtime_revalidation_ledger=runtime,
            global_stop_ledger=_global_stops(tmp_path),
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            execution_gate=lambda _context: True,
            request_gate=request_gate,
            sleep=lambda _seconds: None,
            runtime_revalidator=_revalidation,
        )
    assert len(transport.requests) == 1
    assert len(intents.rows()) == 1
    assert len(ledger.rows()) == 1
    assert len(contexts) == 2
    assert contexts[0].existing_post_intent_count == 0
    assert contexts[1].existing_post_intent_count == 1


def test_failed_runtime_image_preflight_stops_before_remaining_grid(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells, schedule = _t12_plan(config, target_count=3)
    ledger, intents, runtime = _ledgers(tmp_path)
    refusal = json.dumps(
        {"error": {"code": "moderation_blocked", "message": "refusal"}}
    ).encode()
    transport = FakeTransport(
        config, lambda _index, _request: _exchange(status=400, body=refusal)
    )
    global_stops = _global_stops(tmp_path)
    report = run_generation_grid(
        cells,
        schedule=schedule,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intents,
        runtime_revalidation_ledger=runtime,
        global_stop_ledger=global_stops,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        execution_gate=lambda _context: True,
        request_gate=lambda _context: True,
        sleep=lambda _seconds: None,
        runtime_revalidator=_revalidation,
    )
    assert report["status"] == "global_stop_complete"
    assert report["generation_completion"]["all_cells_terminal"] is True
    assert report["generation_completion"]["global_stop_disposition_count"] == 3
    assert (
        report["only_preflight_cell_posted_or_indeterminate_before_global_stop"]
        is True
    )
    assert len(global_stops.rows()) == 3
    assert all(row.physical_post_count == 0 for row in global_stops.rows())
    assert all(row.fake_attempt_row_created is False for row in global_stops.rows())
    stopped_requests = {row.source_request_id for row in global_stops.rows()}
    assert all(
        report["generation_completion"]["source_request_dispositions"][request_id]
        == "not_sent_global_stop"
        for request_id in stopped_requests
    )
    assert len(transport.requests) == 1
    assert ledger.rows()[0].cell_id == select_runtime_image_preflight_cells(
        cells, config.frozen_requested_labels
    )[0].cell_id
    verified = verify_generation_execution(
        report,
        cells=cells,
        schedule=schedule,
        config=config,
        fingerprint=fingerprint,
        ledger=ledger,
        post_intent_ledger=intents,
        runtime_revalidation_ledger=runtime,
        global_stop_ledger=global_stops,
    )
    assert verified == report
    with pytest.raises(RuntimeError, match="existing global-stop ledger"):
        run_generation_grid(
            cells,
            schedule=schedule,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intents,
            runtime_revalidation_ledger=runtime,
            global_stop_ledger=global_stops,
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            execution_gate=lambda _context: True,
            request_gate=lambda _context: True,
            sleep=lambda _seconds: None,
            runtime_revalidator=_revalidation,
        )
    assert len(transport.requests) == 1
    global_stops.path.write_text(
        global_stops.path.read_text(encoding="utf-8").replace(
            "not_sent_global_stop", "usable_image", 1
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="invalid global-stop ledger row"):
        global_stops.rows()


def test_failed_preflight_with_no_unsent_cells_still_seals_global_stop(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells, schedule = _t12_plan(config)
    ledger, intents, runtime = _ledgers(tmp_path)
    refusal = json.dumps(
        {"error": {"code": "moderation_blocked", "message": "refusal"}}
    ).encode()
    transport = FakeTransport(
        config, lambda _index, _request: _exchange(status=400, body=refusal)
    )
    global_stops = _global_stops(tmp_path)

    report = run_generation_grid(
        cells,
        schedule=schedule,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intents,
        runtime_revalidation_ledger=runtime,
        global_stop_ledger=global_stops,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        execution_gate=lambda _context: True,
        request_gate=lambda _context: True,
        sleep=lambda _seconds: None,
        runtime_revalidator=_revalidation,
    )

    assert report["status"] == "global_stop_complete"
    assert report["global_stop_triggered"] is True
    assert report["generation_completion"]["global_stop_triggered"] is True
    assert report["generation_completion"]["all_cells_terminal"] is True
    assert report["global_stop_disposition_count"] == 0
    assert global_stops.path.is_file()
    assert global_stops.path.read_bytes() == b""
    assert global_stops.rows() == []
    stopped_cell = cells[0]
    replacement_payload = {
        "record_type": "pilot3_generation_global_stop_disposition",
        "schema_version": "pilot3-generation-global-stop-disposition-v1",
        "stop_sequence": 1,
        "cell_id": stopped_cell.cell_id,
        "cell_identity_sha256": stopped_cell.cell_identity_sha256,
        "source_request_id": stopped_cell.source_request_id,
        "source_sequence": stopped_cell.source_sequence,
        "source_schedule_row_sha256": stopped_cell.source_schedule_row_sha256,
        "requested_model_label": stopped_cell.requested_model_label,
        "generation_grid_sha256": report["generation_grid_sha256"],
        "generation_schedule_sha256": schedule.schedule_sha256,
        "runtime_image_preflight_sha256": report[
            "runtime_image_preflight_sha256"
        ],
        "preflight_cell_id": stopped_cell.cell_id,
        "preflight_source_request_id": stopped_cell.source_request_id,
        "global_stop_reason": "runtime_image_preflight_failed",
        "terminal_category": "not_sent_global_stop",
        "physical_post_count": 0,
        "physical_post_may_have_executed": False,
        "post_intent_written": False,
        "fake_attempt_row_created": False,
        "attempts_at_stop_count": 1,
        "post_intents_at_stop_count": 1,
    }
    replacement = GenerationGlobalStopDisposition.model_validate(
        {
            **replacement_payload,
            "record_sha256": stable_hash(replacement_payload),
        }
    )
    with pytest.raises(RuntimeError, match="immutable once created"):
        global_stops.write_once([replacement])
    assert len(transport.requests) == 1
    assert len(intents.rows()) == 1
    assert len(ledger.rows()) == 1
    assert verify_generation_execution(
        report,
        cells=cells,
        schedule=schedule,
        config=config,
        fingerprint=fingerprint,
        ledger=ledger,
        post_intent_ledger=intents,
        runtime_revalidation_ledger=runtime,
        global_stop_ledger=global_stops,
    ) == report

    with pytest.raises(RuntimeError, match="existing global-stop ledger"):
        run_generation_grid(
            cells,
            schedule=schedule,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intents,
            runtime_revalidation_ledger=runtime,
            global_stop_ledger=global_stops,
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            execution_gate=lambda _context: True,
            request_gate=lambda _context: True,
            sleep=lambda _seconds: None,
            runtime_revalidator=_revalidation,
        )
    assert len(transport.requests) == 1


def test_interrupted_preflight_global_stop_never_claims_an_observed_post(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells, schedule = _t12_plan(config, target_count=1)
    ledger, intents, runtime = _ledgers(tmp_path)
    global_stops = _global_stops(tmp_path)

    def interrupt(_index: int, _request: bytes) -> TransportExchange:
        raise KeyboardInterrupt

    first_transport = FakeTransport(config, interrupt)
    with pytest.raises(KeyboardInterrupt):
        run_generation_grid(
            cells,
            schedule=schedule,
            transport=first_transport,
            ledger=ledger,
            post_intent_ledger=intents,
            runtime_revalidation_ledger=runtime,
            global_stop_ledger=global_stops,
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            execution_gate=lambda _context: True,
            request_gate=lambda _context: True,
            sleep=lambda _seconds: None,
            runtime_revalidator=_revalidation,
        )
    assert len(first_transport.requests) == 1
    assert len(intents.rows()) == 1
    assert ledger.rows() == []

    def unexpected_post(_index: int, _request: bytes) -> TransportExchange:
        pytest.fail("an indeterminate preflight intent must never be resent")

    resume_transport = FakeTransport(config, unexpected_post)
    report = run_generation_grid(
        cells,
        schedule=schedule,
        transport=resume_transport,
        ledger=ledger,
        post_intent_ledger=intents,
        runtime_revalidation_ledger=runtime,
        global_stop_ledger=global_stops,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        execution_gate=lambda _context: True,
        request_gate=lambda _context: True,
        sleep=lambda _seconds: None,
        runtime_revalidator=_revalidation,
    )

    assert resume_transport.requests == []
    assert report["status"] == "global_stop_complete"
    assert report["post_exchange_observed_cell_count"] == 0
    assert report["post_exchange_observed_cell_ids"] == []
    assert report["physical_post_or_indeterminate_cell_count"] == 1
    assert (
        report["only_preflight_cell_posted_or_indeterminate_before_global_stop"]
        is True
    )
    assert report["generation_completion"][
        "post_exchange_observed_attempt_count"
    ] == 0
    assert report["generation_completion"][
        "indeterminate_after_interruption_count"
    ] == 1
    assert len(global_stops.rows()) == 1
    assert len(ledger.rows()) == 1
    assert ledger.rows()[0].failure_kind == "indeterminate_after_interruption"
    assert verify_generation_execution(
        report,
        cells=cells,
        schedule=schedule,
        config=config,
        fingerprint=fingerprint,
        ledger=ledger,
        post_intent_ledger=intents,
        runtime_revalidation_ledger=runtime,
        global_stop_ledger=global_stops,
    ) == report


def test_tampered_attempt_receipt_is_rejected(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    ledger, intents, _ = _ledgers(tmp_path)
    transport = FakeTransport(config, lambda _index, _request: _exchange())
    result = generate_cell(
        _cell(),
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intents,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        request_gate=lambda _context: True,
        runtime_revalidator=_revalidation,
        sleep=lambda _seconds: None,
    )
    receipt = ledger.sidecar_dir / f"{result.attempt_id}.json"
    receipt.write_text(receipt.read_text().replace("succeeded", "refused", 1))
    with pytest.raises(ValueError, match="invalid attempt receipt"):
        ledger.verify_receipts()
