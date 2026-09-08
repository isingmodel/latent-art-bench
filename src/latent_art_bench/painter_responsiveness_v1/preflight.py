"""Bounded GET-only provider/budget check; credentials are never persisted."""

from __future__ import annotations

import json
import math

import httpx

from latent_art_bench.io import hash_file, utc_now
from latent_art_bench.painter_distribution_study_v1.discovery import (
    account_projection,
    key_from_env,
)
from latent_art_bench.painter_distribution_study_v1.immediate import budget_state
from latent_art_bench.painter_feature_generation_v2.artifacts import publish, stage_lock

from . import common

ORIGIN = "https://openrouter.ai"
ENDPOINT_PATH = "/api/v1/images/models/black-forest-labs/flux.2-max/endpoints"
MAX_BYTES = 2 * 1024**2


def inspect_contract(value, config):
    result = dict(contract_available=False, model=config["model"],
                  provider=config["provider"], price_per_image_usd=None)
    if not isinstance(value, dict):
        return dict(result, reason="invalid_model_inventory")
    data = value.get("data", value)
    if not isinstance(data, dict):
        return dict(result, reason="invalid_model_inventory")
    endpoints = data.get("endpoints", [])
    if not isinstance(endpoints, list) or any(not isinstance(e, dict) for e in endpoints):
        return dict(result, reason="invalid_endpoint_inventory")
    candidates = [e for e in endpoints if e.get("provider_tag") == config["provider"]]
    if data.get("id") != config["model"] or len(candidates) != 1:
        return dict(result, reason="exact_model_provider_not_available")
    endpoint = candidates[0]
    parameters = endpoint.get("supported_parameters", {})
    if not isinstance(parameters, dict):
        return dict(result, reason="invalid_parameter_inventory", endpoint=endpoint)
    expected = (("aspect_ratio", "1:1"), ("output_format", "png"))
    if not all(isinstance(parameters.get(k), dict)
               and isinstance(parameters[k].get("values"), list)
               and v in parameters[k]["values"] for k, v in expected):
        return dict(result, reason="square_png_contract_not_supported", endpoint=endpoint)
    # No guessed megapixel rounding or token pricing is used to approve dispatch.
    prices = endpoint.get("pricing", [])
    if not isinstance(prices, list) or any(not isinstance(p, dict) for p in prices):
        return dict(result, reason="invalid_price_inventory", endpoint=endpoint)
    output = [p for p in prices if p.get("billable") == "output_image"]
    if (len(prices) != 1 or len(output) != 1 or output[0].get("unit") != "image"
            or output[0].get("variant") not in (None, "")):
        return dict(result, reason="pricing_requires_explicit_contract_review", endpoint=endpoint)
    cost = output[0].get("cost_usd")
    if isinstance(cost, bool) or not isinstance(cost, (float, int)) or not math.isfinite(cost):
        return dict(result, reason="invalid_unit_cost", endpoint=endpoint)
    if cost <= 0 or cost > config["request_reservation_usd"]:
        return dict(result, reason="unit_cost_outside_reservation", endpoint=endpoint)
    return dict(result, contract_available=True, price_per_image_usd=float(cost),
                endpoint=endpoint, reason="pinned_provider_contract_available")


def inspect_budget(contract, credits, key, prior, config):
    total, usage = credits.get("total_credits"), credits.get("total_usage")
    account_available = None
    if all(type(x) in (int, float) and math.isfinite(x) and x >= 0 for x in (total, usage)):
        account_available = max(0.0, total - usage)
    key_remaining = key.get("limit_remaining")
    key_status, available = "unavailable", None
    if (type(key_remaining) in (int, float) and math.isfinite(key_remaining)
            and key_remaining >= 0):
        key_status = "finite"
        if account_available is not None:
            available = min(account_available, key_remaining)
    elif "limit" in key and key["limit"] is None and key_remaining is None:
        key_status, available = "explicitly_unlimited", account_available
    cost = contract.get("price_per_image_usd")
    valid_cost = type(cost) in (int, float) and math.isfinite(cost) and cost > 0
    expected = (cost * (config["maximum_images"] + config["maximum_technical_retries"])
                if valid_cost else None)
    prior_spend = prior["accounted_usd"]
    if (type(prior_spend) not in (int, float) or not math.isfinite(prior_spend)
            or prior_spend < 0):
        raise ValueError("invalid conservative prior accounting")
    cap = min(config["maximum_new_spend_usd"],
              config["overall_spending_ceiling_usd"] - prior_spend)
    # Keep an additional full in-flight reservation near the end of collection.
    need = None if expected is None else expected + config["request_reservation_usd"]
    prior_resolved = all(type(prior.get(field)) is int and prior[field] == 0
                         for field in ("unresolved", "uncertain"))
    ready = bool(contract["contract_available"] is True and available is not None
                 and need is not None and need <= cap and need <= available and prior_resolved)
    return dict(budget_available=ready, available_credit_usd=available,
                account_available_credit_usd=account_available, key_limit_status=key_status,
                existing_conservative_spend_usd=prior_spend, new_spend_cap_usd=cap,
                expected_images_and_retry_cost_usd=expected,
                expected_plus_one_reservation_usd=need, prior_accounting=prior,
                explanation="Fresh account numbers; estimates are not a bill guarantee.")


def _reject_nonfinite_json(_):
    raise ValueError("metadata contains a non-JSON numeric constant")


def fetch_metadata(path, *, secret=None, transport=None):
    if path not in (ENDPOINT_PATH, "/api/v1/credits", "/api/v1/key"):
        raise ValueError("undeclared metadata endpoint")
    headers = {"User-Agent": "LatentArtBench responsiveness research"}
    if secret:
        headers["Authorization"] = "Bearer " + secret
    try:
        with httpx.Client(transport=transport, follow_redirects=False,
                          trust_env=False, timeout=30) as client:
            with client.stream("GET", ORIGIN + path, headers=headers) as response:
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > MAX_BYTES:
                        return dict(status="unavailable", error="metadata_byte_bound_exceeded")
                    chunks.append(chunk)
                raw = b"".join(chunks)
                if secret and secret.encode() in raw:
                    raise ValueError("credential echo suppressed")
                if response.status_code != 200:
                    return dict(status="unavailable", http_status=response.status_code)
                try:
                    parsed = json.loads(raw, parse_constant=_reject_nonfinite_json)
                    if not isinstance(parsed, dict):
                        raise ValueError("expected metadata object")
                    if secret and not isinstance(parsed.get("data"), dict):
                        raise ValueError("expected account data object")
                    value = account_projection(raw) if secret else parsed
                    if not value:
                        raise ValueError("empty metadata projection")
                except (ValueError, TypeError, UnicodeError):
                    return dict(status="unavailable", error="malformed_metadata")
                return dict(status="available", http_status=200, value=value)
    except httpx.HTTPError as exc:
        return dict(status="unavailable", error=type(exc).__name__)


def build(root, run_id, *, transport=None):
    from .workflow import verify

    verify(root, run_id)
    config = common.configuration(root)
    target = root / common.directory(run_id) / "provider_preflight.json"
    with stage_lock(root / common.WORKSPACE / ".preflight.lock"):
        if target.exists():
            raise ValueError("preflight is terminal; use a successor run for another check")
        secret = key_from_env(root)
        model = fetch_metadata(ENDPOINT_PATH, transport=transport)
        credits = fetch_metadata("/api/v1/credits", secret=secret, transport=transport)
        key = fetch_metadata("/api/v1/key", secret=secret, transport=transport)
        contract = inspect_contract(model.get("value", {}), config)
        budget = inspect_budget(contract, credits.get("value", {}), key.get("value", {}),
                                budget_state(root), config)
        value = dict(checked_at_utc=utc_now().isoformat(), model_response=model,
                     account_projection=credits, key_projection=key, **contract, **budget,
                     source_urls=[ORIGIN + p for p in
                                  (ENDPOINT_PATH, "/api/v1/credits", "/api/v1/key")],
                     generation_calls=0,
                     freeze_sha256=hash_file(root / common.directory(run_id) / "freeze.json"))
        publish(target, value)
        return value
