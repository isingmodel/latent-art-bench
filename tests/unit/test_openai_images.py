import base64
import io
import json
from pathlib import Path

import httpx
import pytest
from PIL import Image

from latent_art_bench.generation.openai_images import (
    ALLOWED_MODELS,
    ImageAdapterConfigurationError,
    OpenAIImageAdapter,
    attest_legacy_generation_call,
    generation_api_payload,
    generation_endpoint,
    generation_request_payload,
    generation_request_sha256,
    plan_generation_calls,
    unique_successful_generation_calls_by_cell,
)
from latent_art_bench.io import hash_file, write_jsonl
from latent_art_bench.manifests import validate_records
from latent_art_bench.schemas import PromptRecord, RunRecord


def encoded_png(size=(12, 7)) -> str:
    output = io.BytesIO()
    Image.new("RGB", size, (1, 2, 3)).save(output, format="PNG")
    return base64.b64encode(output.getvalue()).decode("ascii")


def prompt() -> PromptRecord:
    return PromptRecord(
        prompt_id="test-prompt",
        content_id="content",
        template_id="template",
        prompt="A tiny test image",
        artist_free_control=True,
        test_only=True,
    )


def test_adapter_allowlist_is_exact() -> None:
    assert ALLOWED_MODELS == {"gpt-image-1", "gpt-image-2"}


def test_adapter_records_requested_and_actual_dimensions(tmp_path: Path, pilot_config) -> None:
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "data": [{"b64_json": encoded_png(), "revised_prompt": "revised"}],
                "usage": {"x": 1},
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with OpenAIImageAdapter(
        pilot_config.generation, client=client, sleep=lambda _: None
    ) as adapter:
        result = adapter.generate(
            "run-1", prompt(), "gpt-image-2", 0, tmp_path, qualification_bypass=True
        )
    client.close()
    assert result.status == "succeeded"
    assert result.requested_size == "1024x1024"
    assert (result.actual_width, result.actual_height) == (12, 7)
    assert result.actual_format == "png"
    assert result.qualification_bypass is True
    assert requests[0]["model"] == "gpt-image-2"
    assert requests[0]["output_format"] == "png"
    assert "seed" not in requests[0]
    assert validate_records([result], root=tmp_path, check_files=True) == {
        "generation_call": 1
    }


def test_adapter_retries_only_retryable_status(tmp_path: Path, pilot_config) -> None:
    attempts = 0
    sleeps = []

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(
                429,
                headers={"retry-after": "0"},
                json={"error": {"message": "rate"}},
            )
        return httpx.Response(200, json={"data": [{"b64_json": encoded_png()}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = OpenAIImageAdapter(pilot_config.generation, client=client, sleep=sleeps.append)
    result = adapter.generate(
        "run-1", prompt(), "gpt-image-1", 0, tmp_path, qualification_bypass=True
    )
    client.close()
    assert result.status == "succeeded"
    assert result.retry_count == 1
    assert attempts == 2
    assert sleeps == [0.0]


def test_adapter_retries_http_transport_errors(tmp_path: Path, pilot_config) -> None:
    attempts = 0
    sleeps = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ConnectError("temporary connection failure", request=request)
        return httpx.Response(200, json={"data": [{"b64_json": encoded_png()}]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = OpenAIImageAdapter(pilot_config.generation, client=client, sleep=sleeps.append)
    result = adapter.generate(
        "run-1", prompt(), "gpt-image-1", 0, tmp_path, qualification_bypass=True
    )
    client.close()
    assert result.status == "succeeded"
    assert result.retry_count == 1
    assert attempts == 2
    assert sleeps == [1.0]


def test_adapter_records_exhausted_http_transport_error(
    tmp_path: Path, pilot_config
) -> None:
    attempts = 0
    sleeps = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        raise httpx.ReadError("connection dropped", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = OpenAIImageAdapter(pilot_config.generation, client=client, sleep=sleeps.append)
    result = adapter.generate(
        "run-1", prompt(), "gpt-image-1", 0, tmp_path, qualification_bypass=True
    )
    client.close()
    assert result.status == "failed"
    assert result.failure_kind == "transport_error"
    assert result.retry_count == pilot_config.generation.max_retries
    assert attempts == pilot_config.generation.max_retries + 1
    assert sleeps == [1.0, 2.0]


def test_moderation_error_is_not_retried(tmp_path: Path, pilot_config) -> None:
    attempts = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            400,
            json={"error": {"code": "content_policy_violation", "message": "blocked"}},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = OpenAIImageAdapter(pilot_config.generation, client=client, sleep=lambda _: None)
    result = adapter.generate(
        "run-1", prompt(), "gpt-image-1", 0, tmp_path, qualification_bypass=True
    )
    client.close()
    assert result.status == "refused"
    assert result.retry_count == 0
    assert attempts == 1


def test_non_loopback_endpoint_is_rejected(pilot_config) -> None:
    unsafe = pilot_config.generation.model_copy(update={"base_url": "https://api.example.test/v1"})
    with pytest.raises(ImageAdapterConfigurationError, match="loopback"):
        generation_endpoint(unsafe)


def test_runtime_model_allowlist_rejects_other_models(tmp_path: Path, pilot_config) -> None:
    client = httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(500)))
    adapter = OpenAIImageAdapter(pilot_config.generation, client=client, sleep=lambda _: None)
    with pytest.raises(ImageAdapterConfigurationError, match="allowlist"):
        adapter.generate("run-1", prompt(), "dall-e-3", 0, tmp_path, True)  # type: ignore[arg-type]
    client.close()


def test_request_identity_binds_exact_prompt_annotations_and_cell(pilot_config) -> None:
    record = prompt()
    api_payload = generation_api_payload(
        record, "gpt-image-1", pilot_config.generation
    )
    identity_payload = generation_request_payload(
        record, "gpt-image-1", 0, pilot_config.generation
    )

    assert api_payload["prompt"] == "A tiny test image"
    assert "seed" not in api_payload
    assert identity_payload["api_payload"] == api_payload
    assert identity_payload["prompt_record"] == record.model_dump(mode="json")
    identity = generation_request_sha256(
        record, "gpt-image-1", 0, pilot_config.generation
    )
    assert len(identity) == 64
    assert identity == generation_request_sha256(
        record, "gpt-image-1", 0, pilot_config.generation
    )
    changed_text = record.model_copy(update={"prompt": "A changed test image"})
    changed_annotation = record.model_copy(update={"content_id": "different-content"})
    assert identity != generation_request_sha256(
        changed_text, "gpt-image-1", 0, pilot_config.generation
    )
    assert identity != generation_request_sha256(
        changed_annotation, "gpt-image-1", 0, pilot_config.generation
    )
    assert identity != generation_request_sha256(
        record, "gpt-image-2", 0, pilot_config.generation
    )


def test_request_identity_rejects_out_of_range_repetition(pilot_config) -> None:
    with pytest.raises(ImageAdapterConfigurationError, match="repetition"):
        generation_request_sha256(
            prompt(),
            "gpt-image-1",
            pilot_config.generation.repetitions,
            pilot_config.generation,
        )


def test_legacy_call_attestation_uses_run_prompt_manifest_hash(
    tmp_path: Path, pilot_config
) -> None:
    prompt_manifest = tmp_path / "prompts.jsonl"
    write_jsonl(prompt_manifest, [prompt()])
    call = plan_generation_calls(
        "legacy-run",
        [prompt()],
        ["gpt-image-1"],
        pilot_config.generation,
        qualification_bypass=False,
    )[0]
    run = RunRecord(
        run_id="legacy-run",
        command="generate",
        arguments={"prompt_manifest": str(prompt_manifest)},
        status="complete",
        started_at=call.started_at,
        resolved_config=pilot_config.model_dump(mode="json"),
        input_hashes={str(prompt_manifest): hash_file(prompt_manifest)},
    )

    identity = attest_legacy_generation_call(
        call,
        run,
        prompt_manifest,
    )
    assert identity == generation_request_sha256(
        prompt(), "gpt-image-1", 0, pilot_config.generation
    )

    with pytest.raises(ImageAdapterConfigurationError, match="does not match"):
        attest_legacy_generation_call(
            call,
            run.model_copy(
                update={"input_hashes": {str(prompt_manifest): "0" * 64}}
            ),
            prompt_manifest,
        )
    incompatible = call.model_copy(update={"requested_quality": "high"})
    with pytest.raises(ImageAdapterConfigurationError, match="requested_quality"):
        attest_legacy_generation_call(
            incompatible,
            run,
            prompt_manifest,
        )


def test_unique_successful_calls_rejects_duplicate_frozen_cell(pilot_config) -> None:
    call = plan_generation_calls(
        "run-1",
        [prompt()],
        ["gpt-image-1"],
        pilot_config.generation,
        qualification_bypass=False,
    )[0].model_copy(update={"status": "succeeded"})
    duplicate = call.model_copy(update={"call_id": "second-success"})

    with pytest.raises(ValueError, match="multiple successful generation calls"):
        unique_successful_generation_calls_by_cell([call, duplicate])

    bypass = duplicate.model_copy(update={"qualification_bypass": True})
    assert unique_successful_generation_calls_by_cell([call, bypass]) == {
        ("test-prompt", "gpt-image-1", 0): call
    }
