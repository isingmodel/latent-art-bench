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
    generation_endpoint,
)
from latent_art_bench.manifests import validate_records
from latent_art_bench.schemas import PromptRecord


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
