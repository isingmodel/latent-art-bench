"""Offline contract and credential handling tests; no provider calls."""

import copy
import json
from pathlib import Path

import httpx
import pytest

from latent_art_bench.painter_responsiveness_v1 import common, design, preflight, workflow

ROOT = Path(__file__).resolve().parents[1]


def test_prospective_payloads_hold_scene_and_polarity_fixed_across_name_clauses():
    config = common.configuration(ROOT)
    schedule = design.make_schedule([r["template_id"] for r in config["templates"]],
                                    seed=config["seed"])
    rows = common.requests_from_schedule(schedule, config)
    assert len(rows) == 192
    for row in rows:
        p = row["payload"]
        assert p["provider"] == {"only": ["black-forest-labs/us-3"], "allow_fallbacks": False}
        assert p["n"] == 1 and p["aspect_ratio"] == "1:1" and p["output_format"] == "png"
        assert row["scene_text"] in p["prompt"]
        assert config["polarity_clauses"][row["polarity"]] in p["prompt"]
        if row["arm"] in ("free", "generic"):
            assert all(name not in p["prompt"] for name in ("Monet", "Cezanne", "Cézanne"))


def test_missing_research_evidence_cannot_authorize_paid_collection():
    gate = common.generation_gate({}, {}, {}, {})
    assert gate["status"] == "not_ready" and len(gate["missing"]) == 8
    candidate = common.generation_gate(
        {"status": "ready_for_responsible_human_margin_decision",
         "independent_fine_content_coding": True, "target_frozen": True},
        {"status": "feasible"}, {"margin_status": "validated", "decision": "proceed"},
        {"contract_available": True, "budget_available": True})
    assert candidate["missing"] == ["reference_range_validated"]


def contract():
    return {"id": "black-forest-labs/flux.2-max", "endpoints": [{
        "provider_tag": "black-forest-labs/us-3",
        "supported_parameters": {
            "aspect_ratio": {"type": "enum", "values": ["1:1"]},
            "output_format": {"type": "enum", "values": ["png"]}},
        "pricing": [{"billable": "output_image", "unit": "image", "cost_usd": 0.07}]}]}


def test_provider_contract_cannot_silently_use_fallback_or_guessed_pricing():
    config = common.configuration(ROOT)
    good = preflight.inspect_contract(contract(), config)
    assert good["contract_available"] and good["price_per_image_usd"] == 0.07
    other = copy.deepcopy(contract())
    other["endpoints"][0]["provider_tag"] = "different"
    assert not preflight.inspect_contract(other, config)["contract_available"]
    other = copy.deepcopy(contract())
    other["endpoints"][0]["pricing"][0]["unit"] = "megapixel"
    assert not preflight.inspect_contract(other, config)["contract_available"]


def test_budget_uses_fresh_credit_and_conservative_prior_not_old_arithmetic_remainder():
    config = common.configuration(ROOT)
    c = preflight.inspect_contract(contract(), config)
    prior = {"accounted_usd": 45.6819185, "unresolved": 0, "uncertain": 0}
    good = preflight.inspect_budget(c, {"total_credits": 100, "total_usage": 50},
                                     {"limit": None}, prior, config)
    assert good["budget_available"]
    assert good["expected_plus_one_reservation_usd"] == pytest.approx(18.86)
    assert not preflight.inspect_budget(c, {}, {}, prior, config)["budget_available"]
    assert not preflight.inspect_budget(c, {"total_credits": 100, "total_usage": 99}, {},
                                       prior, config)["budget_available"]


def test_account_fetch_suppresses_identity_and_credentials_and_only_uses_get():
    calls = []

    def handler(request):
        calls.append(request)
        assert request.method == "GET"
        return httpx.Response(200, json={"data": {"total_credits": 100,
                                                 "total_usage": 30, "label": "private"}})

    value = preflight.fetch_metadata("/api/v1/credits", secret="test-only-secret",
                                     transport=httpx.MockTransport(handler))
    assert value["value"] == {"total_credits": 100, "total_usage": 30}
    assert len(calls) == 1
    assert "private" not in json.dumps(value)
    with pytest.raises(ValueError, match="undeclared"):
        preflight.fetch_metadata("/api/v1/images", transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError, match="echo suppressed"):
        preflight.fetch_metadata("/api/v1/key", secret="test-only-secret", transport=
                                httpx.MockTransport(lambda r: httpx.Response(
                                    200, text="test-only-secret")))


def test_freeze_includes_new_nested_inference_tests_and_old_input_contracts():
    paths = workflow.source_paths(ROOT)
    assert Path("tests/painter_responsiveness_v1/test_design_inference.py") in paths
    assert common.CONFIG in paths
    assert Path("src/latent_art_bench/painter_distribution_revision_v1/common.py") in paths
