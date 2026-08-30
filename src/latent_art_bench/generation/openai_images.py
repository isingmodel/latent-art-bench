from __future__ import annotations

import base64
import binascii
import io
import time
import uuid
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import urlsplit

import httpx
from PIL import Image

from latent_art_bench.config import GenerationConfig
from latent_art_bench.io import hash_bytes, utc_now
from latent_art_bench.schemas import (
    AllowedImageModel,
    GenerationCallRecord,
    PromptRecord,
)

ALLOWED_MODELS = frozenset({"gpt-image-1", "gpt-image-2"})
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


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
        if model not in ALLOWED_MODELS:
            raise ImageAdapterConfigurationError(f"model is not in the fixed allowlist: {model}")
        if model not in self.config.models:
            raise ImageAdapterConfigurationError(f"model is not enabled by pilot config: {model}")
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
            status="failed",
            qualification_bypass=qualification_bypass,
            started_at=started,
        )
        payload = {
            "model": model,
            "prompt": prompt.prompt,
            "n": 1,
            "size": self.config.size,
            "quality": self.config.quality,
            "output_format": self.config.output_format,
        }

        response: Optional[httpx.Response] = None
        try:
            for attempt in range(self.config.max_retries + 1):
                try:
                    response = self._client.post(self.endpoint, json=payload)
                except httpx.HTTPError as exc:
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
