from __future__ import annotations

import base64
import binascii
import io
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlsplit

import httpx
from PIL import Image

from latent_art_bench.config import GenerationConfig
from latent_art_bench.io import hash_bytes, hash_file, read_jsonl, stable_hash, utc_now
from latent_art_bench.schemas import (
    AllowedImageModel,
    GenerationCallRecord,
    PromptRecord,
    RunRecord,
)

ALLOWED_MODELS = frozenset({"gpt-image-1", "gpt-image-2"})
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
GENERATION_REQUEST_IDENTITY_VERSION = "generation-request-v1"

GenerationCell = Tuple[str, AllowedImageModel, int]


class ImageAdapterConfigurationError(ValueError):
    pass


def generation_endpoint(config: GenerationConfig) -> str:
    parsed = urlsplit(config.base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ImageAdapterConfigurationError("generation base_url must be an HTTP(S) URL")
    if config.require_loopback and parsed.hostname not in LOOPBACK_HOSTS:
        raise ImageAdapterConfigurationError(
            f"test-only OAuth adapter requires a loopback host, found {parsed.hostname!r}"
        )
    return f"{config.base_url.rstrip('/')}/{config.endpoint}"


def _validate_model(model: AllowedImageModel, config: GenerationConfig) -> None:
    if model not in ALLOWED_MODELS:
        raise ImageAdapterConfigurationError(
            f"model is not in the fixed allowlist: {model}"
        )
    if model not in config.models:
        raise ImageAdapterConfigurationError(
            f"model is not enabled by pilot config: {model}"
        )


def generation_api_payload(
    prompt: PromptRecord,
    model: AllowedImageModel,
    config: GenerationConfig,
) -> Dict[str, Any]:
    """Build the exact semantic JSON body sent to the image endpoint."""

    _validate_model(model, config)
    return {
        "model": model,
        "prompt": prompt.prompt,
        "n": 1,
        "size": config.size,
        "quality": config.quality,
        "output_format": config.output_format,
    }


def generation_request_payload(
    prompt: PromptRecord,
    model: AllowedImageModel,
    repetition: int,
    config: GenerationConfig,
) -> Dict[str, Any]:
    """Return the canonical retry-stable request identity payload.

    Run identifiers, call identifiers, timestamps, and retry counters are deliberately
    excluded so that every attempt for one frozen cell has the same identity. The full
    prompt record is included to bind both the exact text sent to the API and its frozen
    experimental annotations.
    """

    if repetition < 0 or repetition >= config.repetitions:
        raise ImageAdapterConfigurationError(
            f"repetition must be in [0, {config.repetitions}), found {repetition}"
        )
    return {
        "identity_version": GENERATION_REQUEST_IDENTITY_VERSION,
        "endpoint": generation_endpoint(config),
        "model": model,
        "repetition": repetition,
        "prompt_record": prompt.model_dump(mode="json"),
        "api_payload": generation_api_payload(prompt, model, config),
    }


def generation_request_sha256(
    prompt: PromptRecord,
    model: AllowedImageModel,
    repetition: int,
    config: GenerationConfig,
) -> str:
    """Hash a frozen image-generation cell independently of an individual attempt."""

    return stable_hash(generation_request_payload(prompt, model, repetition, config))


def generation_prompt_record_sha256(prompt: PromptRecord) -> str:
    return stable_hash(prompt.model_dump(mode="json"))


def generation_config_sha256(config: GenerationConfig) -> str:
    """Hash generation execution settings, excluding the sidecar attestation path."""

    return stable_hash(
        config.model_dump(mode="json", exclude={"manifest_attestation"}, exclude_none=True)
    )


def attest_legacy_generation_call(
    call: GenerationCallRecord,
    run: RunRecord,
    prompt_manifest: Path,
) -> str:
    """Recover a request identity for a pre-identity call using run provenance.

    The run identifier, resolved generation config, and prompt-manifest input hash must
    agree before an identity is reconstructed. This establishes compatibility with the
    frozen request contract; it cannot prove facts that were never recorded by the
    legacy run (for example, a separate wire-level request-body digest).
    """

    if call.run_id != run.run_id:
        raise ImageAdapterConfigurationError(
            f"legacy call run_id {call.run_id!r} does not match run {run.run_id!r}"
        )
    if run.command not in {"generate", "retry-generation-failures"}:
        raise ImageAdapterConfigurationError(
            f"run command {run.command!r} did not issue image-generation requests"
        )
    if not isinstance(run.resolved_config, dict) or not isinstance(
        run.resolved_config.get("generation"), dict
    ):
        raise ImageAdapterConfigurationError(
            "legacy run does not contain a resolved generation config"
        )
    try:
        config = GenerationConfig.model_validate(run.resolved_config["generation"])
    except ValueError as exc:
        raise ImageAdapterConfigurationError(
            f"legacy run resolved generation config is invalid: {exc}"
        ) from exc

    manifest_argument = run.arguments.get("prompt_manifest")
    recorded_hashes = []
    for recorded_path, recorded_hash in run.input_hashes.items():
        argument_match = isinstance(manifest_argument, str) and recorded_path == manifest_argument
        config_match = Path(recorded_path).as_posix().endswith(
            Path(config.prompt_manifest).as_posix()
        )
        if argument_match or config_match:
            recorded_hashes.append(recorded_hash)
    if len(set(recorded_hashes)) != 1:
        raise ImageAdapterConfigurationError(
            "legacy run does not identify exactly one prompt-manifest input hash"
        )
    recorded_prompt_manifest_sha256 = recorded_hashes[0]
    if len(recorded_prompt_manifest_sha256) != 64 or any(
        character not in "0123456789abcdef"
        for character in recorded_prompt_manifest_sha256
    ):
        raise ImageAdapterConfigurationError(
            "legacy run prompt-manifest sha256 is not 64 lowercase hexadecimal characters"
        )
    if hash_file(prompt_manifest) != recorded_prompt_manifest_sha256:
        raise ImageAdapterConfigurationError(
            "legacy run prompt-manifest hash does not match the supplied manifest"
        )

    prompts = [PromptRecord.model_validate(row) for row in read_jsonl(prompt_manifest)]
    matched_prompts = [prompt for prompt in prompts if prompt.prompt_id == call.prompt_id]
    if len(matched_prompts) != 1:
        raise ImageAdapterConfigurationError(
            f"legacy call prompt_id {call.prompt_id!r} resolves to "
            f"{len(matched_prompts)} prompt rows"
        )
    prompt = matched_prompts[0]
    expected = {
        "endpoint": generation_endpoint(config),
        "requested_size": config.size,
        "requested_quality": config.quality,
        "requested_output_format": config.output_format,
    }
    mismatches = [
        field
        for field, expected_value in expected.items()
        if getattr(call, field) != expected_value
    ]
    if call.model not in config.models or call.model not in ALLOWED_MODELS:
        mismatches.append("model")
    if call.repetition < 0 or call.repetition >= config.repetitions:
        mismatches.append("repetition")
    if mismatches:
        raise ImageAdapterConfigurationError(
            "legacy call is incompatible with the frozen request contract: "
            + ", ".join(sorted(set(mismatches)))
        )
    return generation_request_sha256(prompt, call.model, call.repetition, config)


def unique_successful_generation_calls_by_cell(
    calls: Iterable[GenerationCallRecord],
    *,
    include_qualification_bypass: bool = False,
) -> Dict[GenerationCell, GenerationCallRecord]:
    """Index successful calls while rejecting ambiguous duplicate cell outputs."""

    successful: Dict[GenerationCell, GenerationCallRecord] = {}
    for call in calls:
        if call.status != "succeeded":
            continue
        if call.qualification_bypass and not include_qualification_bypass:
            continue
        cell = (call.prompt_id, call.model, call.repetition)
        prior = successful.get(cell)
        if prior is not None:
            raise ValueError(
                "multiple successful generation calls exist for cell "
                f"{cell!r}: {prior.call_id!r}, {call.call_id!r}"
            )
        successful[cell] = call
    return successful


def _error_detail(response: httpx.Response) -> tuple:
    try:
        body = response.json()
    except ValueError:
        return "http_error", response.text[:1000]
    error = body.get("error", body) if isinstance(body, dict) else body
    if isinstance(error, dict):
        code = str(error.get("code") or error.get("type") or "http_error")
        message = str(error.get("message") or error)[:1000]
        return code, message
    return "http_error", str(error)[:1000]


def _is_refusal(code: str, message: str) -> bool:
    combined = f"{code} {message}".lower()
    return any(term in combined for term in ("moderation", "content_policy", "safety", "refusal"))


def _retry_delay(response: httpx.Response, retry_index: int) -> float:
    retry_after = response.headers.get("retry-after")
    if retry_after:
        try:
            return min(30.0, max(0.0, float(retry_after)))
        except ValueError:
            pass
    return min(8.0, float(2**retry_index))


def _planned_record(
    run_id: str,
    prompt: PromptRecord,
    model: AllowedImageModel,
    config: GenerationConfig,
    repetition: int,
    qualification_bypass: bool,
) -> GenerationCallRecord:
    now = utc_now()
    return GenerationCallRecord(
        call_id=f"call-{uuid.uuid4().hex}",
        run_id=run_id,
        prompt_id=prompt.prompt_id,
        model=model,
        endpoint=generation_endpoint(config),
        requested_size=config.size,
        requested_quality=config.quality,
        requested_output_format=config.output_format,
        repetition=repetition,
        prompt_record_sha256=generation_prompt_record_sha256(prompt),
        generation_config_sha256=generation_config_sha256(config),
        request_identity_sha256=generation_request_sha256(
            prompt, model, repetition, config
        ),
        request_identity_provenance="native_pre_request",
        status="planned",
        qualification_bypass=qualification_bypass,
        started_at=now,
        completed_at=now,
    )


def plan_generation_calls(
    run_id: str,
    prompts: Iterable[PromptRecord],
    models: Iterable[AllowedImageModel],
    config: GenerationConfig,
    qualification_bypass: bool,
) -> List[GenerationCallRecord]:
    rows: List[GenerationCallRecord] = []
    for prompt in prompts:
        for model in models:
            for repetition in range(config.repetitions):
                rows.append(
                    _planned_record(
                        run_id, prompt, model, config, repetition, qualification_bypass
                    )
                )
    return rows


class OpenAIImageAdapter:
    def __init__(
        self,
        config: GenerationConfig,
        client: Optional[httpx.Client] = None,
        sleep=time.sleep,
    ) -> None:
        self.config = config
        self.endpoint = generation_endpoint(config)
        self._client = client or httpx.Client(timeout=config.timeout_seconds)
        self._owns_client = client is None
        self._sleep = sleep

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "OpenAIImageAdapter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def generate(
        self,
        run_id: str,
        prompt: PromptRecord,
        model: AllowedImageModel,
        repetition: int,
        output_dir: Path,
        qualification_bypass: bool,
    ) -> GenerationCallRecord:
        generation_request_payload(prompt, model, repetition, self.config)
        started = utc_now()
        record = GenerationCallRecord(
            call_id=f"call-{uuid.uuid4().hex}",
            run_id=run_id,
            prompt_id=prompt.prompt_id,
            model=model,
            endpoint=self.endpoint,
            requested_size=self.config.size,
            requested_quality=self.config.quality,
            requested_output_format=self.config.output_format,
            repetition=repetition,
            prompt_record_sha256=generation_prompt_record_sha256(prompt),
            generation_config_sha256=generation_config_sha256(self.config),
            request_identity_sha256=generation_request_sha256(
                prompt, model, repetition, self.config
            ),
            request_identity_provenance="native_pre_request",
            status="failed",
            qualification_bypass=qualification_bypass,
            started_at=started,
        )
        payload = generation_api_payload(prompt, model, self.config)

        response: Optional[httpx.Response] = None
        try:
            for attempt in range(self.config.max_retries + 1):
                try:
                    response = self._client.post(self.endpoint, json=payload)
                except httpx.HTTPError as exc:
                    response = None
                    if attempt < self.config.max_retries:
                        record.retry_count += 1
                        self._sleep(min(8.0, float(2**attempt)))
                        continue
                    record.failure_kind = "transport_error"
                    record.failure_reason = str(exc)[:1000]
                    return self._finish(record)
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < self.config.max_retries:
                        record.retry_count += 1
                        self._sleep(_retry_delay(response, attempt))
                        continue
                break

            if response is None:
                record.failure_kind = "internal_error"
                record.failure_reason = "adapter did not receive a response"
                return self._finish(record)
            if not response.is_success:
                code, message = _error_detail(response)
                record.status = "refused" if _is_refusal(code, message) else "failed"
                record.failure_kind = code
                record.failure_reason = message
                return self._finish(record)

            try:
                body = response.json()
                item = body["data"][0]
                encoded = item["b64_json"]
                image_bytes = base64.b64decode(encoded, validate=True)
            except (ValueError, KeyError, IndexError, TypeError, binascii.Error) as exc:
                record.failure_kind = "invalid_response"
                record.failure_reason = f"missing or invalid data[0].b64_json: {exc}"
                return self._finish(record)

            try:
                with Image.open(io.BytesIO(image_bytes)) as image:
                    image.load()
                    actual_width, actual_height = image.size
                    actual_format = (image.format or "unknown").lower()
            except Exception as exc:
                record.failure_kind = "invalid_image"
                record.failure_reason = str(exc)[:1000]
                return self._finish(record)

            digest = hash_bytes(image_bytes)
            suffixes: Dict[str, str] = {"png": ".png", "jpeg": ".jpg", "webp": ".webp"}
            suffix = suffixes.get(actual_format, ".bin")
            path = output_dir / model / digest[:2] / f"{digest}{suffix}"
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists() and path.read_bytes() != image_bytes:
                record.failure_kind = "content_address_collision"
                record.failure_reason = str(path)
                return self._finish(record)
            if not path.exists():
                path.write_bytes(image_bytes)

            record.status = "succeeded"
            record.output_path = str(path)
            record.output_sha256 = digest
            record.actual_width = actual_width
            record.actual_height = actual_height
            record.actual_format = actual_format
            record.revised_prompt = item.get("revised_prompt")
            usage = body.get("usage", {})
            record.usage = usage if isinstance(usage, dict) else {"value": usage}
            return self._finish(record)
        except Exception as exc:
            record.failure_kind = "adapter_error"
            record.failure_reason = f"{type(exc).__name__}: {exc}"[:1000]
            return self._finish(record)

    @staticmethod
    def _finish(record: GenerationCallRecord) -> GenerationCallRecord:
        record.completed_at = utc_now()
        return record
