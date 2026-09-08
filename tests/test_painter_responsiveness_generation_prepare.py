"""Scientific prerequisites cannot be replaced by authorization or ready booleans."""

import copy
import json
from pathlib import Path

import httpx
import pytest

from latent_art_bench.io import hash_file
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, publish
from latent_art_bench.painter_responsiveness_v1 import (
    common,
    generation_prepare,
    human_package,
    inference,
    preflight,
)


def evidence():
    reference = dict(status="ready_for_responsible_human_margin_decision",
                     unresolved_work_ids=[], blocked_groups=[],
                     groups=[dict(image_ids=["w1", "w2"])])
    decision = dict(author_kind="responsible_human", actual_human_decision=True,
                    responsible_human_id="synthetic-test-human", margin_rationale="Test only.",
                    capture_limitations="Unresolved capture ancestry.", decision="proceed",
                    target_work_ids=["w1", "w2"], meaningful_margin_primary_iqr=1,
                    maximum_p90_halfwidth_primary_iqr=0.5, minimum_endpoint_power=0.8,
                    generated_image_assessment=dict(
                        status="feasible", recruitment="Synthetic test only.",
                        consent_and_storage_plan="Synthetic test only.",
                        independent_rater_count=2, all_192_outputs_assigned=True))
    rows = [dict(scenario=name, true_interactions=[-1, -1],
                 rejection_probability_mc95=[[0.85, 0.95], [0.85, 0.95]],
                 p90_family_interval_halfwidth=[0.4, 0.4], invalid_variance_trials=0)
            for name in ("empirical_proxy", "generic_noise_x1_5", "heteroskedastic_normal")]
    return reference, decision, dict(results=rows)


def test_actual_reference_and_human_decision_are_distinct_prerequisites():
    reference, decision, simulation = evidence()
    qualified = generation_prepare.qualify(reference, decision, simulation)
    assert qualified["reference"]["status"] == reference["status"]
    assert qualified["precision"]["decision"] == "proceed"
    assert common.generation_gate(
        qualified["reference"], qualified["human"], qualified["precision"],
        dict(contract_available=True, budget_available=True))["status"] == "ready"
    reference["unresolved_work_ids"] = ["unrated"]
    with pytest.raises(ValueError, match="incomplete"):
        generation_prepare.qualify(reference, decision, simulation)


@pytest.mark.parametrize("field,value", [
    ("author_kind", "maintainer_llm"), ("actual_human_decision", False),
    ("target_work_ids", ["w1"]), ("meaningful_margin_primary_iqr", float("nan")),
    ("meaningful_margin_primary_iqr", True), ("minimum_endpoint_power", 1.01),
    ("generated_image_assessment", {"status": "feasible"}),
])
def test_fabricated_or_selectively_changed_prerequisites_rejected(field, value):
    reference, decision, simulation = evidence()
    decision[field] = value
    with pytest.raises(ValueError):
        generation_prepare.qualify(reference, decision, simulation)


def test_worst_declared_noise_scenario_and_mc_uncertainty_cannot_be_dropped():
    reference, decision, simulation = evidence()
    simulation["results"][2]["rejection_probability_mc95"][0][0] = 0.79
    assert generation_prepare.qualify(reference, decision, simulation)[
        "precision"]["decision"] == "stop"
    selected = copy.deepcopy(simulation)
    selected["results"].pop()
    with pytest.raises(ValueError, match="all three"):
        generation_prepare.qualify(reference, decision, selected)


def qualification_fixture(tmp_path, monkeypatch):
    """Synthetic record chain; real simulation, mocked human receipt verification only."""
    reference, decision, _ = evidence()
    reference["package_id"] = "synthetic-qualified-package"
    source = common.directory("prv1-qualification-tests")
    publish(tmp_path / source / "freeze.json", dict(run_id="prv1-qualification-tests"))
    source_hash = hash_file(tmp_path / source / "freeze.json")
    reference_path = source / "reference_validation.json"
    publish(tmp_path / reference_path, reference)
    decision.update(reference_validation_sha256=hash_file(tmp_path / reference_path),
                    package_id=reference["package_id"])
    decision_path = Path("synthetic_decision.json")
    publish(tmp_path / decision_path, decision)
    noise = dict(pools={arm: [-0.02, 0, 0.02] for arm in ("free", "generic", "monet", "cezanne")})
    publish(tmp_path / source / "analysis.json", dict(retained_noise=noise))
    publish(tmp_path / source / "analysis_receipt.json", dict(
        analysis_sha256=hash_file(tmp_path / source / "analysis.json"),
        freeze_sha256=source_hash))
    receipt = dict(phase="validation", inputs=[],
                   reference_validation_sha256=hash_file(tmp_path / reference_path))
    publish(tmp_path / source / "human_ratings_validation_receipt.json", receipt)
    monkeypatch.setattr(human_package, "verify_ratings", lambda *_, **__: receipt)
    provider_path = source / "provider_preflight.json"
    provider = dict(contract_available=True, budget_available=True, freeze_sha256=source_hash,
                    existing_conservative_spend_usd=45.6819185)
    publish(tmp_path / provider_path, provider)
    config = dict(simulation_seed=811, simulation_trials=200, repetitions=4, alpha=0.05)
    simulation = inference.simulate_design(
        noise, seed=811, trials=200, effects=[[0, 0], [-1, -1], [-1, 0], [0, -1]])
    qualified = generation_prepare.qualify(reference, decision, simulation)
    paths = [p.relative_to(tmp_path) for p in (tmp_path / source).glob("*.json")]
    paths.append(decision_path)
    freeze = dict(
        diagnostic_run_id="prv1-qualification-tests", inputs=bindings(tmp_path, paths),
        decision_path=str(decision_path), provider_preflight_path=str(provider_path),
        meaningful_margin_primary_iqr=1, target_work_ids=["w1", "w2"], config=config,
        precision=qualified["precision"], source_freeze_sha256=source_hash,
        budget_baseline_usd=45.6819185, gates=common.generation_gate(
            qualified["reference"], qualified["human"], qualified["precision"], provider),
    )
    return freeze, provider


def test_generation_qualification_recomputes_precision_instead_of_trusting_frozen_numbers(
    tmp_path, monkeypatch,
):
    freeze, provider = qualification_fixture(tmp_path, monkeypatch)
    assert generation_prepare.verify_qualification(tmp_path, freeze) == provider
    freeze["precision"]["qualification_rows"][0]["rejection_probability_mc95"][0][0] = 0.999
    with pytest.raises(ValueError, match="precision qualification"):
        generation_prepare.verify_qualification(tmp_path, freeze)


@pytest.mark.parametrize("filename", ("analysis.json", "analysis_receipt.json"))
def test_generation_qualification_cannot_use_unbound_noise_or_its_receipt(
    tmp_path, monkeypatch, filename,
):
    freeze, _ = qualification_fixture(tmp_path, monkeypatch)
    freeze["inputs"] = [row for row in freeze["inputs"] if not row["path"].endswith(filename)]
    with pytest.raises(ValueError, match="must be bound"):
        generation_prepare.verify_qualification(tmp_path, freeze)


def test_generation_qualification_checks_diagnostic_analysis_receipt(tmp_path, monkeypatch):
    freeze, _ = qualification_fixture(tmp_path, monkeypatch)
    source = common.directory(freeze["diagnostic_run_id"])
    (tmp_path / source / "analysis.json").write_text('{"retained_noise":{"pools":{}}}')
    # Even if someone rebinds the changed analysis, its terminal receipt still contradicts it.
    freeze["inputs"] = bindings(tmp_path, [Path(row["path"]) for row in freeze["inputs"]])
    with pytest.raises(ValueError, match="diagnostic analysis"):
        generation_prepare.verify_qualification(tmp_path, freeze)


def test_ready_flags_cannot_replace_actual_human_qualification(tmp_path, monkeypatch):
    freeze, _ = qualification_fixture(tmp_path, monkeypatch)
    assert freeze["gates"]["status"] == "ready"
    monkeypatch.setattr(human_package, "verify_ratings", lambda *_, **__: (
        _ for _ in ()).throw(ValueError("actual human rating chain missing")))
    with pytest.raises(ValueError, match="actual human rating chain"):
        generation_prepare.verify_qualification(tmp_path, freeze)


def test_ready_flags_are_reconstructed_from_actual_provider_evidence(tmp_path, monkeypatch):
    freeze, provider = qualification_fixture(tmp_path, monkeypatch)
    provider["budget_available"] = False
    path = tmp_path / freeze["provider_preflight_path"]
    path.write_text(json.dumps(provider))
    freeze["inputs"] = bindings(tmp_path, [Path(row["path"]) for row in freeze["inputs"]])
    with pytest.raises(ValueError, match="does not authorize"):
        generation_prepare.verify_qualification(tmp_path, freeze)


def budget_fixture():
    config = common.configuration(Path(__file__).resolve().parents[1])
    return (dict(contract_available=True, price_per_image_usd=0.07),
            dict(total_credits=100, total_usage=20),
            dict(accounted_usd=45.6819185, unresolved=0, uncertain=0), config)


def test_budget_requires_account_credit_and_explicit_key_limit_evidence():
    contract, credits, prior, config = budget_fixture()
    def check(account, key):
        return preflight.inspect_budget(contract, account, key, prior, config)

    assert check(credits, {"limit": None})["budget_available"]
    assert check(credits, {"limit_remaining": 30})["budget_available"]
    assert not check(credits, {})["budget_available"]
    assert not check({}, {"limit_remaining": 100})["budget_available"]
    assert not check(credits, {"limit_remaining": 1})["budget_available"]
    assert not check(credits, {"limit": None, "limit_remaining": -1})["budget_available"]


def test_budget_rejects_unresolved_and_unqualified_uncertain_historical_charges():
    contract, credits, prior, config = budget_fixture()
    for field in ("unresolved", "uncertain"):
        changed = dict(prior, **{field: 1})
        assert not preflight.inspect_budget(contract, credits, {"limit": None},
                                            changed, config)["budget_available"]
    # The recovery budget has already removed approved historical contingency from uncertain.
    prior.update(contingency_reserve_usd=10, missing_cost_failures=2)
    assert preflight.inspect_budget(contract, credits, {"limit": None}, prior, config)[
        "budget_available"]


@pytest.mark.parametrize("body", (b"not-json", b"[]", b'{"data":[]}', b'{"data":{}}',
                                  b'{"data":{"limit_remaining":NaN}}'))
def test_malformed_account_metadata_is_unavailable_not_an_unlimited_key(body):
    transport = httpx.MockTransport(lambda _: httpx.Response(200, content=body))
    result = preflight.fetch_metadata("/api/v1/key", secret="synthetic-secret", transport=transport)
    assert result == {"status": "unavailable", "error": "malformed_metadata"}


@pytest.mark.parametrize("inventory", (None, [], {"data": None}, {"endpoints": [None]},
                                       {"endpoints": {}}))
def test_malformed_provider_inventory_cannot_qualify(inventory):
    config = common.configuration(Path(__file__).resolve().parents[1])
    assert not preflight.inspect_contract(inventory, config)["contract_available"]


def test_additional_billable_components_require_contract_review():
    config = common.configuration(Path(__file__).resolve().parents[1])
    inventory = dict(id=config["model"], endpoints=[dict(
        provider_tag=config["provider"], supported_parameters={
            "aspect_ratio": {"values": ["1:1"]}, "output_format": {"values": ["png"]}},
        pricing=[dict(billable="output_image", unit="image", cost_usd=0.07)])])
    assert preflight.inspect_contract(inventory, config)["contract_available"]
    inventory["endpoints"][0]["pricing"].append(
        dict(billable="input_tokens", unit="token", cost_usd=0.0001))
    result = preflight.inspect_contract(inventory, config)
    assert not result["contract_available"]
    assert result["reason"] == "pricing_requires_explicit_contract_review"
