from __future__ import annotations

import base64
import io
import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
from PIL import Image

from latent_art_bench.io import canonical_json, hash_file, read_jsonl, stable_hash
from latent_art_bench.pilot2.config import Pilot2GenerationConfig
from latent_art_bench.pilot2.generation import (
    MAX_PHYSICAL_POSTS_PER_CELL,
    AppendOnlyAttemptLedger,
    AppendOnlyPostIntentLedger,
    AppendOnlyRuntimeRevalidationLedger,
    GenerationAttempt,
    build_generation_cells,
    build_generation_schedule,
    generate_cell,
    generation_attempt_ledger_semantic_sha256,
    generation_completion_report,
    post_intent_ledger_semantic_sha256,
    reconcile_unmatched_post_intents,
    run_generation_grid,
    runtime_revalidation_ledger_semantic_sha256,
    select_conformance_cells,
    terminal_records_for_analysis,
    terminal_records_manifest_sha256,
    verified_attempt_receipt_manifest,
    verify_generation_runtime_revalidation_ledger,
    verify_post_intent_attempt_bijection,
    verify_successful_output_artifacts,
    verify_transport_conformance,
)
from latent_art_bench.pilot2.transport import (
    EndpointProbeEvidence,
    OAuthProcessEvidence,
    OAuthRuntimeFingerprint,
    OAuthRuntimeRevalidation,
    OAuthSourceSnapshot,
    OAuthTransportConfig,
    Pilot2OAuthTransport,
    RuntimeFingerprintError,
    SourceFileEvidence,
    canonical_image_request_bytes,
)
from latent_art_bench.schemas import PromptRecord


def _png(width: int = 512, height: int = 512) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (width, height), (12, 34, 56)).save(output, format="PNG")
    return output.getvalue()


def _success_response(width: int = 512, height: int = 512) -> httpx.Response:
    encoded = base64.b64encode(_png(width, height)).decode("ascii")
    return httpx.Response(
        200,
        headers={
            "content-type": "application/json",
            "x-request-id": "request-safe",
            "set-cookie": "must-not-be-recorded",
        },
        json={"data": [{"b64_json": encoded}], "usage": {"input_tokens": 3}},
    )


def _config(tmp_path: Path) -> OAuthTransportConfig:
    checkout = tmp_path / "openai-oauth"
    checkout.mkdir(exist_ok=True)
    return OAuthTransportConfig(
        base_url="http://127.0.0.1:19531/v1",
        checkout_path=checkout,
        required_checkout_path=checkout,
        timeout_seconds=5,
    )


def _post_intent_ledger(tmp_path: Path) -> AppendOnlyPostIntentLedger:
    return AppendOnlyPostIntentLedger(tmp_path / "post_intents.jsonl")


def _fingerprint(config: OAuthTransportConfig) -> OAuthRuntimeFingerprint:
    zero = "0" * 64
    one = "1" * 64
    source_payload = {
        "schema_version": "pilot2-oauth-source-snapshot-v1",
        "checkout_path": str(config.checkout_path),
        "git_head": "a" * 40,
        "git_remote": "https://example.test/openai-oauth.git",
        "dirty": True,
        "relevant_roots": ["packages/openai-oauth/src/"],
        "files": [
            SourceFileEvidence(
                path="packages/openai-oauth/src/images.ts",
                state="present",
                tracked_at_head=False,
                current_sha256=one,
                current_size_bytes=4,
            ).model_dump(mode="json")
        ],
        "git_status_porcelain": "?? packages/openai-oauth/src/images.ts\n",
        "tracked_diff": "",
        "tracked_diff_sha256": zero,
        "untracked_source_contents": {
            "packages/openai-oauth/src/images.ts": "test"
        },
        "excluded_dirty_paths": [],
        "runtime_source_dirty_paths": ["packages/openai-oauth/src/images.ts"],
        "dirty_runtime_source_capture_complete": True,
    }
    source_payload["source_snapshot_sha256"] = stable_hash(source_payload)
    source = OAuthSourceSnapshot.model_validate(source_payload)
    process = OAuthProcessEvidence(
        pid=123,
        cwd=str(config.checkout_path / "packages/openai-oauth"),
        cwd_inside_checkout=True,
        command_sanitized="bun src/cli.ts --oauth-file <redacted>",
        command_sha256=zero,
    )
    health = EndpointProbeEvidence(
        url=config.health_url,
        http_status=200,
        response_body_sha256=zero,
        response_body_bytes=11,
        response_metadata={"content-type": "application/json"},
        parsed_summary={"ok": True},
    )
    catalog = EndpointProbeEvidence(
        url=config.models_url,
        http_status=200,
        response_body_sha256=one,
        response_body_bytes=22,
        response_metadata={"content-type": "application/json"},
        parsed_summary={"model_ids": ["gpt-image-1", "gpt-image-2"]},
    )
    payload = {
        "captured_at": "2026-08-31T00:00:00Z",
        "endpoint_url": config.endpoint_url,
        "source": source.model_dump(mode="json"),
        "process": process.model_dump(mode="json"),
        "health": health.model_dump(mode="json"),
        "model_catalog": catalog.model_dump(mode="json"),
        "required_requested_labels": ["gpt-image-1", "gpt-image-2"],
        "health_ok": True,
        "model_catalog_contains_required_labels": True,
        "runtime_ready": True,
        "executed_model_claims": False,
        "operational_model_estimand": "requested_model_label_accepted_by_oauth_endpoint",
        "schema_version": "pilot2-oauth-runtime-fingerprint-v1",
    }
    provisional = OAuthRuntimeFingerprint.model_validate(
        {**payload, "fingerprint_sha256": zero}
    )
    payload["fingerprint_sha256"] = stable_hash(
        provisional.model_dump(mode="json", exclude={"fingerprint_sha256"})
    )
    return OAuthRuntimeFingerprint.model_validate(payload)


def _revalidation(
    config: OAuthTransportConfig, fingerprint: OAuthRuntimeFingerprint
) -> OAuthRuntimeRevalidation:
    checks = {"unit_test_runtime_is_frozen": True}
    payload = {
        "schema_version": "pilot2-oauth-runtime-revalidation-v1",
        "checked_at": datetime(2026, 8, 31, 0, 1, tzinfo=timezone.utc),
        "status": "pass",
        "persisted_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "endpoint_url": config.endpoint_url,
        "current_listener_pid": fingerprint.process.pid,
        "current_process_cwd": fingerprint.process.cwd,
        "current_source_snapshot_sha256": fingerprint.source.source_snapshot_sha256,
        "current_health_response_sha256": fingerprint.health.response_body_sha256,
        "current_model_catalog_response_sha256": (
            fingerprint.model_catalog.response_body_sha256
        ),
        "checks": checks,
    }
    provisional = OAuthRuntimeRevalidation.model_construct(
        **payload, revalidation_sha256="0" * 64
    )
    payload["revalidation_sha256"] = stable_hash(
        provisional.model_dump(mode="json", exclude={"revalidation_sha256"})
    )
    return OAuthRuntimeRevalidation.model_validate(payload)


def _control_prompt(prompt_id: str = "control-1") -> PromptRecord:
    return PromptRecord(
        prompt_id=prompt_id,
        content_id="content-1",
        template_id="template-1",
        prompt="A quiet riverside with three trees, no text.",
        artist_free_control=True,
        test_only=True,
    )


def _target_prompt(index: int = 1, content_id: str = "content-1") -> PromptRecord:
    return PromptRecord(
        prompt_id=f"target-{content_id}-{index}",
        content_id=content_id,
        template_id="template-1",
        prompt=f"A quiet riverside with three trees in the style of Artist {index}, no text.",
        target_artist_id=f"artist-{index}",
        target_artist_name=f"Artist {index}",
        artist_free_control=False,
        test_only=True,
    )


def _matched_prompts(content_id: str = "content-1") -> list[PromptRecord]:
    control = _control_prompt(prompt_id=f"control-{content_id}").model_copy(
        update={"content_id": content_id}
    )
    return [control, *[_target_prompt(index, content_id) for index in range(1, 5)]]


def test_canonical_request_is_exact_utf8_content() -> None:
    body = canonical_image_request_bytes("é and a river", "gpt-image-1")

    assert body == (
        '{"model":"gpt-image-1","n":1,"output_format":"png",'
        '"prompt":"é and a river","quality":"low","size":"auto"}'
    ).encode()
    with pytest.raises(ValueError, match="requested model"):
        canonical_image_request_bytes("test", "dall-e-3")  # type: ignore[arg-type]


def test_generation_config_freezes_schedule_contract_and_evidence_paths() -> None:
    config = Pilot2GenerationConfig()

    assert config.max_parallel == 4
    assert config.schedule_namespace == "pilot2-generation-order-v1"
    assert config.schedule_seed == 20260901
    assert config.generation_cells_manifest == "configs/pilot_2/generation_cells.jsonl"
    assert config.generation_schedule == "configs/pilot_2/generation_schedule.json"
    assert config.runtime_revalidation_ledger == (
        "reports/pilot_2/evidence/generation_runtime_revalidations.jsonl"
    )
    assert config.post_intent_ledger == (
        "artifacts/pilot_2/generation_post_intents.jsonl"
    )
    assert config.attempt_receipt_manifest == (
        "reports/pilot_2/evidence/generation_attempt_receipts.json"
    )


def test_transport_performs_one_post_and_sends_canonical_content(tmp_path: Path) -> None:
    config = _config(tmp_path)
    expected = canonical_image_request_bytes("A test", "gpt-image-2")
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return _success_response()

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with Pilot2OAuthTransport(config, client=client) as transport:
        exchange = transport.post_once(expected)
    client.close()

    assert len(requests) == 1
    assert requests[0].content == expected
    assert requests[0].headers["content-type"] == "application/json"
    assert exchange.http_status == 200
    assert exchange.response_body_sha256 is not None
    assert exchange.response_metadata == {
        "content-type": "application/json",
        "x-request-id": "request-safe",
    }


def test_transport_does_not_hide_a_retry(tmp_path: Path) -> None:
    config = _config(tmp_path)
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadError("one physical failure", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    exchange = transport.post_once(canonical_image_request_bytes("test", "gpt-image-1"))
    client.close()

    assert calls == 1
    assert exchange.http_status is None
    assert exchange.transport_error_kind == "ReadError"


def test_retry_attempts_are_distinct_immutable_rows(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells = build_generation_cells([_control_prompt()], repetitions=1)
    cell = cells[0]
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls < 3:
            return httpx.Response(
                503,
                headers={"content-type": "application/json"},
                json={"error": {"type": "upstream_error", "message": "later"}},
            )
        return _success_response()

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    sleeps: list[float] = []
    result = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=_post_intent_ledger(tmp_path),
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=sleeps.append,
    )
    client.close()

    attempts = ledger.rows()
    intents = _post_intent_ledger(tmp_path).rows()
    assert result.outcome == "succeeded"
    assert calls == 3
    assert sleeps == [1.0, 2.0]
    assert [row.attempt_number for row in attempts] == [1, 2, 3]
    assert [row.outcome for row in attempts] == [
        "retryable_failure",
        "retryable_failure",
        "succeeded",
    ]
    assert all(row.response_body_sha256 for row in attempts)
    assert len({row.attempt_id for row in attempts}) == 3
    assert len(intents) == len(attempts) == calls
    assert [intent.attempt_id for intent in intents] == [
        attempt.attempt_id for attempt in attempts
    ]
    assert [attempt.post_intent_sequence for attempt in attempts] == [1, 2, 3]
    assert post_intent_ledger_semantic_sha256(intents) != (
        post_intent_ledger_semantic_sha256(list(reversed(intents)))
    )
    verify_post_intent_attempt_bijection(intents, attempts, cells)
    receipts = verified_attempt_receipt_manifest(ledger, attempts)
    assert receipts["attempt_receipt_count"] == len(attempts)
    assert receipts["contains_raw_response_body"] is False
    assert receipts["attempt_receipt_manifest_sha256"] == stable_hash(
        {
            key: value
            for key, value in receipts.items()
            if key != "attempt_receipt_manifest_sha256"
        }
    )
    assert result.canonical_request_utf8.encode() == canonical_image_request_bytes(
        cell.prompt_text, cell.requested_model_label
    )
    assert result.actual_width == 512 and result.actual_height == 512
    assert result.decoded_output_sha256 == result.output_sha256
    assert result.decoded_output_byte_count == len(_png())
    assert result.exact_dimensions_claimed is False
    assert Path(result.output_path or "").name.startswith(result.output_sha256 or "missing")
    with pytest.raises(ValueError, match="already exists"):
        ledger.append(result)
    repeated = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=_post_intent_ledger(tmp_path),
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=sleeps.append,
    )
    assert repeated.attempt_id == result.attempt_id
    assert calls == 3


def test_retry_cap_is_exactly_ten_physical_posts(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = build_generation_cells([_control_prompt()], repetitions=1)[0]
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(429, json={"error": {"message": "rate limited"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    sleeps: list[float] = []
    result = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=_post_intent_ledger(tmp_path),
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=sleeps.append,
    )
    client.close()

    assert result.outcome == "retryable_failure"
    assert calls == MAX_PHYSICAL_POSTS_PER_CELL == 10
    attempts = ledger.rows()
    assert len(attempts) == 10
    assert sleeps == [1.0, 2.0, 4.0, 8.0, 8.0, 8.0, 8.0, 8.0, 8.0]
    cells = build_generation_cells([_control_prompt()], repetitions=1)
    report = generation_completion_report(cells, attempts)
    assert report["cell_dispositions"][cell.cell_id] == "failed_after_retry_cap"
    assert report["attempt_ledger_semantic_sha256"] == (
        generation_attempt_ledger_semantic_sha256(attempts)
    )
    assert generation_attempt_ledger_semantic_sha256(attempts) != (
        generation_attempt_ledger_semantic_sha256(list(reversed(attempts)))
    )

    tampered = list(attempts)
    first_payload = tampered[0].model_dump(mode="json")
    first_payload["failure_reason"] = "tampered retry detail with same disposition"
    tampered[0] = GenerationAttempt.model_validate(first_payload)
    tampered_report = generation_completion_report(cells, tampered)

    assert tampered_report["attempt_count"] == report["attempt_count"]
    assert tampered_report["disposition_counts"] == report["disposition_counts"]
    assert tampered_report["cell_dispositions"] == report["cell_dispositions"]
    assert (
        tampered_report["attempt_ledger_semantic_sha256"]
        != report["attempt_ledger_semantic_sha256"]
    )
    assert tampered_report["report_sha256"] != report["report_sha256"]


def test_unmatched_post_intent_is_terminalized_without_resend(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells = build_generation_cells([_control_prompt()], repetitions=1)
    interrupted_cell, other_cell = cells
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    intent_ledger = _post_intent_ledger(tmp_path)
    physical_posts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal physical_posts
        physical_posts += 1
        if physical_posts == 1:
            raise KeyboardInterrupt("simulated kill after durable intent")
        return _success_response()

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    with pytest.raises(KeyboardInterrupt, match="simulated kill"):
        generate_cell(
            interrupted_cell,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intent_ledger,
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            sleep=lambda _: None,
        )

    assert physical_posts == 1
    assert len(intent_ledger.rows()) == 1
    assert ledger.rows() == []
    verify_post_intent_attempt_bijection(
        intent_ledger.rows(), ledger.rows(), cells, allow_unmatched=True
    )

    reconciled = reconcile_unmatched_post_intents(
        cells, ledger, intent_ledger, fingerprint
    )
    assert len(reconciled) == 1
    indeterminate = reconciled[0]
    assert indeterminate.attempt_id == intent_ledger.rows()[0].attempt_id
    assert indeterminate.outcome == "terminal_failure"
    assert indeterminate.failure_kind == "indeterminate_after_interruption"
    assert indeterminate.retry_classification == (
        "not_retryable_indeterminate_after_interruption"
    )
    assert indeterminate.physical_post_may_have_executed is True
    assert indeterminate.post_exchange_observed is False
    assert indeterminate.response_body_sha256 is None
    assert indeterminate.request_label_accepted is False
    verify_post_intent_attempt_bijection(intent_ledger.rows(), ledger.rows(), cells)

    # Reconciliation and cell resume are idempotent and never blind-resend.
    assert reconcile_unmatched_post_intents(cells, ledger, intent_ledger, fingerprint) == []
    repeated = generate_cell(
        interrupted_cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intent_ledger,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: None,
    )
    assert repeated.attempt_id == indeterminate.attempt_id
    assert physical_posts == 1

    generate_cell(
        other_cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intent_ledger,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: None,
    )
    client.close()
    tampered_attempts = ledger.rows()
    tampered_payload = tampered_attempts[-1].model_dump(mode="json")
    tampered_payload["post_intent_sha256"] = "f" * 64
    tampered_attempts[-1] = GenerationAttempt.model_validate(tampered_payload)
    with pytest.raises(RuntimeError, match="disagrees with its durable post intent"):
        verify_post_intent_attempt_bijection(
            intent_ledger.rows(), tampered_attempts, cells
        )
    terminal = terminal_records_for_analysis(cells, ledger.rows())
    interrupted_terminal = next(
        row for row in terminal if row.cell_id == interrupted_cell.cell_id
    )
    assert interrupted_terminal.outcome == "terminal_failure"
    assert interrupted_terminal.failure_kind == "indeterminate_after_interruption"
    assert interrupted_terminal.source_post_exchange_observed is False
    assert physical_posts == 2


def test_resume_observes_remaining_fixed_delay_before_next_intent(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = build_generation_cells([_control_prompt()], repetitions=1)[0]
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(503, json={"error": {"message": "temporary"}})
        return _success_response()

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    intent_ledger = _post_intent_ledger(tmp_path)
    with pytest.raises(KeyboardInterrupt, match="between attempts"):
        generate_cell(
            cell,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intent_ledger,
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            sleep=lambda _: (_ for _ in ()).throw(
                KeyboardInterrupt("between attempts")
            ),
        )
    assert calls == len(ledger.rows()) == len(intent_ledger.rows()) == 1

    resumed_sleeps: list[float] = []
    result = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intent_ledger,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=resumed_sleeps.append,
    )
    client.close()
    assert result.outcome == "succeeded"
    assert calls == len(ledger.rows()) == len(intent_ledger.rows()) == 2
    assert len(resumed_sleeps) == 1
    assert 0 < resumed_sleeps[0] <= 1.0


def test_torn_attempt_tail_recovers_only_from_exact_intent_backed_sidecar(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells = build_generation_cells([_control_prompt()], repetitions=1)
    cell = cells[0]
    posts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal posts
        posts += 1
        return _success_response()

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    intent_ledger = _post_intent_ledger(tmp_path)
    original = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intent_ledger,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: None,
    )
    complete_bytes = ledger.path.read_bytes()
    torn_bytes = complete_bytes[:-25]
    ledger.path.write_bytes(torn_bytes)
    with pytest.raises(ValueError, match="invalid attempt row"):
        ledger.rows()

    recovered_ids = ledger.recover_from_sidecars(intent_ledger)
    assert recovered_ids == [original.attempt_id]
    assert ledger.rows() == [original]
    recovered_tail_paths = list(ledger.recovery_dir.glob("*.partial"))
    assert len(recovered_tail_paths) == 1
    ledger.verify_sidecars(ledger.rows())
    verify_post_intent_attempt_bijection(intent_ledger.rows(), ledger.rows(), cells)
    receipts = verified_attempt_receipt_manifest(ledger, ledger.rows())
    assert receipts["recovered_tail_count"] == 1
    assert receipts["recovered_tails"][0]["file_sha256"] == hash_file(
        recovered_tail_paths[0]
    )

    repeated = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intent_ledger,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: None,
    )
    client.close()
    assert repeated.attempt_id == original.attempt_id
    assert posts == 1

    recovered_tail_paths[0].write_bytes(b"tampered recovery evidence")
    with pytest.raises(RuntimeError, match="torn-tail evidence is stale"):
        verified_attempt_receipt_manifest(ledger, ledger.rows())


def test_receipt_recovers_crash_before_attempt_ledger_append_without_resend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = build_generation_cells([_control_prompt()], repetitions=1)[0]
    posts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal posts
        posts += 1
        return _success_response()

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    intent_ledger = _post_intent_ledger(tmp_path)
    original_write = ledger._write_attempt_sidecar

    def interrupt_after_receipt(
        attempt: GenerationAttempt, prior_attempts: list[GenerationAttempt]
    ) -> Path:
        original_write(attempt, prior_attempts)
        raise KeyboardInterrupt("crash after durable receipt")

    monkeypatch.setattr(ledger, "_write_attempt_sidecar", interrupt_after_receipt)
    with pytest.raises(KeyboardInterrupt, match="durable receipt"):
        generate_cell(
            cell,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intent_ledger,
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            sleep=lambda _: None,
        )
    assert posts == 1
    assert ledger.rows() == []
    sidecars = list(ledger.sidecar_dir.glob("*.json"))
    assert len(sidecars) == 1
    receipt = json.loads(sidecars[0].read_text(encoding="utf-8"))
    assert receipt["ledger_row_index"] == 0
    assert receipt["ledger_prefix_semantic_sha256"] == stable_hash([])
    with pytest.raises(
        RuntimeError, match="sidecars do not cover the exact ledger"
    ):
        ledger.append(GenerationAttempt.model_validate(receipt["attempt"]))
    assert ledger.rows() == []

    monkeypatch.setattr(ledger, "_write_attempt_sidecar", original_write)
    recovered = ledger.recover_from_sidecars(intent_ledger)
    assert len(recovered) == 1
    recovered_attempt = ledger.rows()[0]
    assert recovered == [recovered_attempt.attempt_id]
    repeated = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intent_ledger,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: None,
    )
    client.close()
    assert repeated.attempt_id == recovered_attempt.attempt_id
    assert posts == 1


def test_nonfinal_missing_receipt_backed_row_fails_closed(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells = build_generation_cells(_matched_prompts(), repetitions=1)[:2]
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: _success_response())
    )
    transport = Pilot2OAuthTransport(config, client=client)
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    intent_ledger = _post_intent_ledger(tmp_path)
    for cell in cells:
        generate_cell(
            cell,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intent_ledger,
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            sleep=lambda _: None,
        )
    client.close()
    attempts = ledger.rows()
    assert len(attempts) == 2

    # Preserve the later complete row while removing the first. Its receipt says
    # it extended a one-row prefix, so recovery cannot reinterpret it as row zero.
    ledger.path.write_text(
        canonical_json(attempts[1].model_dump(mode="json")) + "\n",
        encoding="utf-8",
    )
    damaged = ledger.path.read_bytes()
    with pytest.raises(RuntimeError, match="disagrees with ledger prefix"):
        ledger.recover_from_sidecars(intent_ledger)
    assert ledger.path.read_bytes() == damaged


@pytest.mark.parametrize("tamper", ["delete", "corrupt"])
def test_resume_checks_attempt_sidecars_before_any_new_post(
    tmp_path: Path, tamper: str
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells = build_generation_cells(_matched_prompts(), repetitions=1)
    posts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal posts
        posts += 1
        return _success_response()

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    intent_ledger = _post_intent_ledger(tmp_path)
    attempt = generate_cell(
        cells[0],
        transport=transport,
        ledger=ledger,
        post_intent_ledger=intent_ledger,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: None,
    )
    sidecar = ledger.sidecar_dir / f"{attempt.attempt_id}.json"
    if tamper == "delete":
        sidecar.unlink()
    else:
        sidecar.write_bytes(b"corrupt sidecar")

    with pytest.raises((RuntimeError, ValueError)):
        run_generation_grid(
            cells,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=intent_ledger,
            runtime_revalidation_ledger=AppendOnlyRuntimeRevalidationLedger(
                tmp_path / "runtime_revalidations.jsonl"
            ),
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            sleep=lambda _: None,
            max_parallel=4,
            runtime_revalidator=lambda cfg, frozen: _revalidation(cfg, frozen),
        )
    client.close()
    assert posts == 1


@pytest.mark.parametrize("tamper", ["delete", "corrupt"])
def test_successful_output_manifest_fails_closed_on_artifact_tamper(
    tmp_path: Path, tamper: str
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells = build_generation_cells([_control_prompt()], repetitions=1)
    cell = cells[0]
    client = httpx.Client(transport=httpx.MockTransport(lambda _: _success_response()))
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    attempt = generate_cell(
        cell,
        transport=Pilot2OAuthTransport(config, client=client),
        ledger=ledger,
        post_intent_ledger=_post_intent_ledger(tmp_path),
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: None,
    )
    client.close()
    attempts = ledger.rows()

    manifest = verify_successful_output_artifacts(cells, attempts)
    completion = generation_completion_report(cells, attempts)
    assert manifest["successful_output_count"] == 1
    assert manifest["contains_raw_image_bytes"] is False
    assert completion["successful_output_manifest_sha256"] == manifest[
        "successful_output_manifest_sha256"
    ]
    assert manifest["successful_output_manifest_sha256"] == stable_hash(
        {
            key: value
            for key, value in manifest.items()
            if key != "successful_output_manifest_sha256"
        }
    )

    output_path = Path(attempt.output_path or "")
    if tamper == "delete":
        output_path.unlink()
        expected = FileNotFoundError
    else:
        output_path.write_bytes(b"corrupted original PNG bytes")
        expected = RuntimeError
    with pytest.raises(expected):
        verify_successful_output_artifacts(cells, attempts)
    with pytest.raises(expected):
        generation_completion_report(cells, attempts)


def test_refusal_is_preserved_not_retried_and_secret_is_redacted(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = build_generation_cells([_control_prompt()], repetitions=1)[0]
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": "content_policy_violation",
                    "message": "blocked Bearer abcdefghijklmnopqrstuvwxyz",
                }
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    result = generate_cell(
        cell,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=_post_intent_ledger(tmp_path),
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: pytest.fail("refusal must not sleep/retry"),
    )
    client.close()

    assert calls == 1
    assert result.outcome == "refused"
    assert result.failure_kind == "content_policy_violation"
    assert result.failure_reason == "blocked <redacted-secret>"
    serialized = ledger.path.read_text()
    assert "abcdefghijklmnopqrstuvwxyz" not in serialized
    assert result.response_body_sha256 is not None


def test_successful_http_with_invalid_payload_is_terminal(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = build_generation_cells([_control_prompt()], repetitions=1)[0]
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, json={"data": []})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    result = generate_cell(
        cell,
        transport=transport,
        ledger=AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl"),
        post_intent_ledger=_post_intent_ledger(tmp_path),
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: pytest.fail("ambiguous successful response must not be retried"),
    )
    client.close()

    assert calls == 1
    assert result.outcome == "terminal_failure"
    assert result.request_label_accepted is True
    assert result.failure_kind == "invalid_response"


def test_decoded_nonimage_bytes_are_preserved_content_addressed(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = build_generation_cells([_control_prompt()], repetitions=1)[0]
    decoded = b"not an image but returned as base64"

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"data": [{"b64_json": base64.b64encode(decoded).decode("ascii")}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = generate_cell(
        cell,
        transport=Pilot2OAuthTransport(config, client=client),
        ledger=AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl"),
        post_intent_ledger=_post_intent_ledger(tmp_path),
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: None,
    )
    client.close()

    assert result.outcome == "terminal_failure"
    assert result.failure_kind == "invalid_image"
    assert result.decoded_output_byte_count == len(decoded)
    assert result.decoded_output_sha256 == result.output_sha256
    assert Path(result.output_path or "").read_bytes() == decoded
    assert Path(result.output_path or "").suffix == ".bin"


@pytest.mark.parametrize(
    ("width", "height", "reason_fragment"),
    [
        (410, 410, "area=168100"),
        (840, 420, "aspect_ratio=2"),
    ],
)
def test_decodable_png_outside_geometry_domain_is_terminal_without_retry(
    tmp_path: Path, width: int, height: int, reason_fragment: str
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = build_generation_cells([_control_prompt()], repetitions=1)[0]
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _success_response(width, height)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = generate_cell(
        cell,
        transport=Pilot2OAuthTransport(config, client=client),
        ledger=AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl"),
        post_intent_ledger=_post_intent_ledger(tmp_path),
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: pytest.fail("geometry failure must not retry"),
    )
    client.close()

    assert calls == 1
    assert result.outcome == "terminal_failure"
    assert result.failure_kind == "invalid_image_geometry"
    assert result.retry_classification == "not_retryable_invalid_image"
    assert reason_fragment in (result.failure_reason or "")
    assert result.output_path and Path(result.output_path).is_file()
    assert (result.actual_width, result.actual_height) == (width, height)


def test_geometry_domain_uses_strict_boundaries(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cell = build_generation_cells([_control_prompt()], repetitions=1)[0]
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: _success_response(411, 410))
    )
    result = generate_cell(
        cell,
        transport=Pilot2OAuthTransport(config, client=client),
        ledger=AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl"),
        post_intent_ledger=_post_intent_ledger(tmp_path),
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: None,
    )
    client.close()

    assert result.outcome == "succeeded"
    assert 411 * 410 > 410 * 410


def test_conformance_passes_without_executed_model_or_dimension_claim(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells = build_generation_cells([_control_prompt()], repetitions=1)
    client = httpx.Client(
        transport=httpx.MockTransport(lambda _: _success_response(512, 411))
    )
    transport = Pilot2OAuthTransport(config, client=client)
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    for cell in cells:
        generate_cell(
            cell,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=_post_intent_ledger(tmp_path),
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            sleep=lambda _: None,
        )
    client.close()

    report = verify_transport_conformance(cells, ledger.rows(), fingerprint)
    assert report["status"] == "pass"
    assert report["executed_model_claims"] is False
    assert report["exact_dimensions_claimed"] is False
    assert {evidence["observed_width"] for evidence in report["models"].values()} == {
        512
    }
    assert all(
        evidence["requested_label_accepted_by_endpoint"]
        for evidence in report["models"].values()
    )


def test_grid_reuses_control_cells_for_preflight_then_runs_parallel(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells = build_generation_cells(_matched_prompts(), repetitions=1)
    observed_prompts: list[str] = []
    observed_models: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        observed_prompts.append(body["prompt"])
        observed_models.append(body["model"])
        return _success_response()

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    runtime_ledger = AppendOnlyRuntimeRevalidationLedger(
        tmp_path / "runtime_revalidations.jsonl"
    )
    report = run_generation_grid(
        cells,
        transport=transport,
        ledger=ledger,
        post_intent_ledger=_post_intent_ledger(tmp_path),
        runtime_revalidation_ledger=runtime_ledger,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: None,
        max_parallel=4,
        runtime_revalidator=lambda cfg, frozen: _revalidation(cfg, frozen),
    )
    client.close()

    selected = select_conformance_cells(cells)
    assert [cell.requested_model_label for cell in selected] == [
        "gpt-image-1",
        "gpt-image-2",
    ]
    assert observed_prompts[:2] == [_control_prompt().prompt, _control_prompt().prompt]
    assert len(observed_prompts) == len(cells) == 10
    assert len(ledger.rows()) == 10
    concurrent_intents = _post_intent_ledger(tmp_path).rows()
    assert [intent.intent_sequence for intent in concurrent_intents] == list(
        range(1, len(cells) + 1)
    )
    verify_post_intent_attempt_bijection(concurrent_intents, ledger.rows(), cells)
    assert report["all_cells_succeeded"] is True
    assert report["transport_conformance"]["status"] == "pass"
    assert report["max_parallel"] == 4
    assert report["generation_schedule"]["batch_count"] == 2
    assert report["generation_schedule_sha256"] == report["generation_schedule"][
        "schedule_sha256"
    ]
    assert report["oauth_runtime_revalidation"]["status"] == "pass"
    assert report["oauth_runtime_revalidation_count"] == 4
    assert [
        record["phase"] for record in report["oauth_runtime_revalidation_records"]
    ] == [
        "start_before_conformance",
        "after_conformance_before_batch",
        "batch_boundary_before_batch",
        "end_after_all_batches",
    ]
    assert report["oauth_runtime_revalidation_records_sha256"] == stable_hash(
        report["oauth_runtime_revalidation_records"]
    )
    assert report["oauth_runtime_revalidation_ledger_semantic_sha256"] == (
        runtime_revalidation_ledger_semantic_sha256(runtime_ledger.rows())
    )
    assert report["oauth_runtime_revalidation_ledger_file_sha256"] == hash_file(
        runtime_ledger.path
    )
    assert report["post_intent_count"] == len(cells)
    assert report["post_intent_ledger_semantic_sha256"] == (
        post_intent_ledger_semantic_sha256(concurrent_intents)
    )
    assert report["post_intent_ledger_file_sha256"] == hash_file(
        _post_intent_ledger(tmp_path).path
    )
    assert report["attempt_receipt_count"] == len(cells)
    receipt_manifest = verified_attempt_receipt_manifest(ledger, ledger.rows())
    assert report["attempt_receipt_manifest_sha256"] == receipt_manifest[
        "attempt_receipt_manifest_sha256"
    ]
    # Parallel response completion may differ from intent order, but the ledger
    # lock freezes one exact, gap-free prefix position into every receipt.
    assert sorted(
        receipt["ledger_row_index"] for receipt in receipt_manifest["receipts"]
    ) == list(range(len(cells)))
    assert len(
        {
            receipt["ledger_prefix_semantic_sha256"]
            for receipt in receipt_manifest["receipts"]
        }
    ) == len(cells)
    assert observed_models[:2] == ["gpt-image-1", "gpt-image-2"]
    assert observed_models[2:] in (
        ["gpt-image-1"] * 4 + ["gpt-image-2"] * 4,
        ["gpt-image-2"] * 4 + ["gpt-image-1"] * 4,
    )


def test_generation_revalidates_runtime_at_batch_boundaries(tmp_path: Path) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells = build_generation_cells(_matched_prompts(), repetitions=1)
    physical_posts = 0
    revalidation_calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal physical_posts
        physical_posts += 1
        return _success_response()

    def changing_runtime(
        cfg: OAuthTransportConfig, frozen: OAuthRuntimeFingerprint
    ) -> OAuthRuntimeRevalidation:
        nonlocal revalidation_calls
        revalidation_calls += 1
        if revalidation_calls == 3:
            raise RuntimeFingerprintError(
                "OAuth listener PID/source changed at a batch boundary"
            )
        return _revalidation(cfg, frozen)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    runtime_ledger = AppendOnlyRuntimeRevalidationLedger(
        tmp_path / "runtime_revalidations.jsonl"
    )
    with pytest.raises(RuntimeFingerprintError, match="PID/source changed"):
        run_generation_grid(
            cells,
            transport=Pilot2OAuthTransport(config, client=client),
            ledger=ledger,
            post_intent_ledger=_post_intent_ledger(tmp_path),
            runtime_revalidation_ledger=runtime_ledger,
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            sleep=lambda _: None,
            max_parallel=4,
            runtime_revalidator=changing_runtime,
        )
    client.close()

    assert revalidation_calls == 3
    assert physical_posts == len(ledger.rows()) == 6
    interrupted_records = runtime_ledger.rows()
    assert [record.phase for record in interrupted_records] == [
        "start_before_conformance",
        "after_conformance_before_batch",
    ]
    schedule = build_generation_schedule(cells)
    verify_generation_runtime_revalidation_ledger(
        interrupted_records, ledger.rows(), cells, schedule
    )

    resumed_client = httpx.Client(transport=httpx.MockTransport(handler))
    resumed = run_generation_grid(
        cells,
        transport=Pilot2OAuthTransport(config, client=resumed_client),
        ledger=ledger,
        post_intent_ledger=_post_intent_ledger(tmp_path),
        runtime_revalidation_ledger=runtime_ledger,
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: None,
        max_parallel=4,
        runtime_revalidator=lambda cfg, frozen: _revalidation(cfg, frozen),
    )
    resumed_client.close()

    assert physical_posts == len(ledger.rows()) == len(cells) == 10
    assert resumed["all_cells_succeeded"] is True
    persisted_records = runtime_ledger.rows()
    assert len({record.invocation_id for record in persisted_records}) == 2
    assert resumed["oauth_runtime_revalidation_count"] == len(persisted_records) == 6
    verify_generation_runtime_revalidation_ledger(
        persisted_records,
        ledger.rows(),
        cells,
        schedule,
        require_completed_generation=True,
    )


def test_resume_rejects_attempts_when_runtime_journal_is_missing(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells = build_generation_cells(_matched_prompts(), repetitions=1)
    posts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal posts
        posts += 1
        return _success_response()

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    generate_cell(
        cells[0],
        transport=transport,
        ledger=ledger,
        post_intent_ledger=_post_intent_ledger(tmp_path),
        fingerprint=fingerprint,
        output_dir=tmp_path / "outputs",
        sleep=lambda _: None,
    )
    assert posts == 1

    with pytest.raises(RuntimeError, match="without persisted runtime"):
        run_generation_grid(
            cells,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=_post_intent_ledger(tmp_path),
            runtime_revalidation_ledger=AppendOnlyRuntimeRevalidationLedger(
                tmp_path / "missing_runtime_revalidations.jsonl"
            ),
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            sleep=lambda _: None,
            max_parallel=4,
            runtime_revalidator=lambda cfg, frozen: _revalidation(cfg, frozen),
        )
    client.close()
    assert posts == 1


def test_generation_schedule_is_set_deterministic_and_keeps_cells_unchanged() -> None:
    prompts = [*_matched_prompts("content-1"), *_matched_prompts("content-2")]
    cells = build_generation_cells(prompts, repetitions=2)
    identities_before = {cell.cell_id: cell.cell_identity_sha256 for cell in cells}

    schedule = build_generation_schedule(cells)
    reversed_schedule = build_generation_schedule(list(reversed(cells)))

    assert schedule.schedule_sha256 == reversed_schedule.schedule_sha256
    assert schedule.model_dump(mode="json") == reversed_schedule.model_dump(mode="json")
    assert schedule.namespace == "pilot2-generation-order-v1"
    assert schedule.seed == 20260901
    assert schedule.max_parallel == 4
    assert schedule.batch_count == 8
    assert schedule.cell_count == 40
    assert [entry.scheduled_cell_rank for entry in schedule.entries] == list(range(1, 41))
    assert sorted(
        entry.conformance_preflight_rank
        for entry in schedule.entries
        if entry.conformance_preflight_rank is not None
    ) == [1, 2]
    assert {cell.cell_id: cell.cell_identity_sha256 for cell in cells} == identities_before


def test_registered_prompt_manifest_has_frozen_320_cell_schedule() -> None:
    prompt_path = Path("configs/pilot_2/prompts.jsonl")
    prompts = [PromptRecord.model_validate(row) for row in read_jsonl(prompt_path)]
    cells = build_generation_cells(prompts, repetitions=4)
    schedule = build_generation_schedule(cells)

    assert hash_file(prompt_path) == (
        "4492121b4233d1b1fdadd5785a8164c7e1b5877de557893f4d8973b318b4af2b"
    )
    assert len(prompts) == 40
    assert len(cells) == 320
    assert schedule.batch_count == 64
    assert schedule.schedule_sha256 == (
        "89ad2446157f29b87cc5cef96cc8dc4698ab42f3db51a2ceaed97598148cbf41"
    )


def test_grid_fails_closed_before_first_post_when_live_revalidation_fails(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells = build_generation_cells(_matched_prompts(), repetitions=1)
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return _success_response()

    def reject_runtime(
        _: OAuthTransportConfig, __: OAuthRuntimeFingerprint
    ) -> OAuthRuntimeRevalidation:
        raise RuntimeFingerprintError("listener changed")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with pytest.raises(RuntimeFingerprintError, match="listener changed"):
        run_generation_grid(
            cells,
            transport=Pilot2OAuthTransport(config, client=client),
            ledger=AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl"),
            post_intent_ledger=_post_intent_ledger(tmp_path),
            runtime_revalidation_ledger=AppendOnlyRuntimeRevalidationLedger(
                tmp_path / "runtime_revalidations.jsonl"
            ),
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            sleep=lambda _: None,
            max_parallel=4,
            runtime_revalidator=reject_runtime,
        )
    client.close()
    assert calls == 0


def test_terminal_analysis_records_map_retry_cap_without_changing_ledger(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path)
    fingerprint = _fingerprint(config)
    cells = build_generation_cells([_control_prompt()], repetitions=1)

    def handler(request: httpx.Request) -> httpx.Response:
        model = json.loads(request.content)["model"]
        if model == "gpt-image-1":
            return httpx.Response(503, json={"error": {"message": "temporary"}})
        return httpx.Response(
            400,
            json={"error": {"code": "content_policy_violation", "message": "blocked"}},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    transport = Pilot2OAuthTransport(config, client=client)
    ledger = AppendOnlyAttemptLedger(tmp_path / "attempts.jsonl")
    for cell in cells:
        generate_cell(
            cell,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=_post_intent_ledger(tmp_path),
            fingerprint=fingerprint,
            output_dir=tmp_path / "outputs",
            sleep=lambda _: None,
        )
    client.close()
    ledger_before = ledger.path.read_bytes()
    attempts_before = ledger.rows()

    records = terminal_records_for_analysis(cells, attempts_before)

    assert ledger.path.read_bytes() == ledger_before
    assert ledger.rows() == attempts_before
    assert len(records) == len(cells) == 2
    by_model = {record.requested_model_label: record for record in records}
    exhausted = by_model["gpt-image-1"]
    assert exhausted.outcome == "terminal_failure"
    assert exhausted.terminal_disposition == "terminal_failure"
    assert exhausted.retry_cap_exhausted is True
    assert exhausted.attempt_count == 10
    assert exhausted.source_terminal_attempt_outcome == "retryable_failure"
    assert exhausted.failure_kind == "retry_cap_exhausted"
    assert len(exhausted.ledger_attempt_ids) == 10
    refusal = by_model["gpt-image-2"]
    assert refusal.outcome == "refused"
    assert refusal.retry_cap_exhausted is False
    assert refusal.attempt_count == 1

    tampered_attempts = list(attempts_before)
    tampered_payload = tampered_attempts[0].model_dump(mode="json")
    tampered_payload["failure_reason"] = "tampered non-terminal retry detail"
    tampered_attempts[0] = GenerationAttempt.model_validate(tampered_payload)
    tampered_records = terminal_records_for_analysis(cells, tampered_attempts)
    assert terminal_records_manifest_sha256(tampered_records) != (
        terminal_records_manifest_sha256(records)
    )
    assert terminal_records_manifest_sha256(list(reversed(records))) == (
        terminal_records_manifest_sha256(records)
    )


def test_terminal_analysis_records_reject_unresolved_cells() -> None:
    cells = build_generation_cells([_control_prompt()], repetitions=1)
    with pytest.raises(ValueError, match="unresolved cells"):
        terminal_records_for_analysis(cells, [])
