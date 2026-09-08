"""Qualify a prospective collection from actual reference and human decisions."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from pathlib import Path

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    publish,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import common, design, inference, workflow


def _verified_analysis(root, source_dir, source_freeze_sha256):
    path = source_dir / "analysis.json"
    receipt = read_json(root / source_dir / "analysis_receipt.json")
    if (hash_file(root / path) != receipt["analysis_sha256"]
            or receipt["freeze_sha256"] != source_freeze_sha256):
        raise ValueError("diagnostic analysis or source receipt changed")
    return read_json(root / path)


def qualify(reference, decision, simulation):
    """Check a responsible human's fixed decision against actual coded membership."""
    if (reference.get("status") != "ready_for_responsible_human_margin_decision"
            or reference.get("unresolved_work_ids") or reference.get("blocked_groups")):
        raise ValueError("independent reference judgments are incomplete or insufficient")
    if (decision.get("author_kind") != "responsible_human"
            or decision.get("actual_human_decision") is not True
            or not decision.get("responsible_human_id")
            or not decision.get("margin_rationale") or not decision.get("capture_limitations")
            or decision.get("decision") != "proceed"):
        raise ValueError("an actual responsible-human margin and target decision is required")
    groups = reference["groups"]
    target = sorted({work_id for group in groups for work_id in group["image_ids"]})
    if not target or sorted(decision.get("target_work_ids", [])) != target:
        raise ValueError("target must retain the complete qualified fine-content membership")
    for field in ("meaningful_margin_primary_iqr", "maximum_p90_halfwidth_primary_iqr",
                  "minimum_endpoint_power"):
        value = decision.get(field)
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError("positive finite human precision specification required: " + field)
    if decision["minimum_endpoint_power"] > 1:
        raise ValueError("minimum power cannot exceed one")
    human = decision.get("generated_image_assessment", {})
    if (human.get("status") != "feasible" or not human.get("recruitment")
            or not human.get("consent_and_storage_plan")
            or type(human.get("independent_rater_count")) is not int
            or human["independent_rater_count"] < 2
            or human.get("all_192_outputs_assigned") is not True):
        raise ValueError("generated-image human assessment is not demonstrably feasible")
    expected = [-decision["meaningful_margin_primary_iqr"]] * 2
    rows = [r for r in simulation["results"] if r["true_interactions"] == expected]
    if {r["scenario"] for r in rows} != {
        "empirical_proxy", "generic_noise_x1_5", "heteroskedastic_normal"
    } or len(rows) != 3:
        raise ValueError("precision qualification requires all three declared noise scenarios")
    precision_ok = all(
        min(bound[0] for bound in row["rejection_probability_mc95"])
        >= decision["minimum_endpoint_power"]
        and max(row["p90_family_interval_halfwidth"])
        <= decision["maximum_p90_halfwidth_primary_iqr"]
        and row["invalid_variance_trials"] == 0 for row in rows)
    return dict(
        reference=dict(status=reference["status"], independent_fine_content_coding=True,
                       target_frozen=True, responsible_human_range_accepted=True),
        human=dict(status="feasible"),
        precision=dict(margin_status="validated", decision="proceed" if precision_ok else "stop",
                       meaningful_margin_primary_iqr=decision["meaningful_margin_primary_iqr"],
                       qualification_rows=rows,
                       criterion="Lower Monte Carlo power bounds and p90 interval width "
                                 "must satisfy the human criteria in every declared scenario."),
    )


def prepare(root, run_id, diagnostic_run_id, decision_path):
    """Create no collection freeze unless all prerequisites are genuine and bound."""
    if run_id == diagnostic_run_id:
        raise ValueError("generation requires a disjoint run identity")
    workflow.verify(root, diagnostic_run_id)
    source_dir = common.directory(diagnostic_run_id)
    decision_path = Path(decision_path).resolve().relative_to(root.resolve())
    decision = read_json(root / decision_path)
    reference_path = source_dir / "reference_validation.json"
    reference = read_json(root / reference_path)
    receipt_path = source_dir / "human_ratings_validation_receipt.json"
    from .human_package import verify_ratings

    receipt = verify_ratings(root, diagnostic_run_id, phase="validation")
    if (receipt.get("phase") != "validation"
            or receipt.get("reference_validation_sha256") != hash_file(root / reference_path)):
        raise ValueError("actual reference validation receipt required")
    verify_bindings(root, receipt["inputs"])
    if (decision.get("reference_validation_sha256") != hash_file(root / reference_path)
            or decision.get("package_id") != reference["package_id"]):
        raise ValueError("human decision does not bind these reference judgments")
    analysis_path = source_dir / "analysis.json"
    analysis = _verified_analysis(root, source_dir, hash_file(root / source_dir / "freeze.json"))
    config = common.configuration(root)
    margin = decision.get("meaningful_margin_primary_iqr")
    if type(margin) not in (int, float) or not math.isfinite(margin) or margin <= 0:
        raise ValueError("a positive human-defined margin must precede precision simulation")
    simulation = inference.simulate_design(
        analysis["retained_noise"], seed=config["simulation_seed"],
        trials=config["simulation_trials"], repetitions=config["repetitions"],
        effects=[[0, 0], [-margin, -margin], [-margin, 0], [0, -margin]], alpha=config["alpha"])
    qualified = qualify(reference, decision, simulation)
    provider_path = source_dir / "provider_preflight.json"
    provider = read_json(root / provider_path)
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(provider["checked_at_utc"])
           ).total_seconds()
    if not 0 <= age <= 24 * 3600:
        raise ValueError("provider/budget metadata must be no older than 24 hours")
    if provider["freeze_sha256"] != hash_file(root / source_dir / "freeze.json"):
        raise ValueError("provider metadata/source mismatch")
    gates = common.generation_gate(qualified["reference"], qualified["human"],
                                   qualified["precision"], provider)
    if gates["status"] != "ready":
        return dict(status="not_ready", run_id=run_id, gates=gates,
                    precision=qualified["precision"], generation_calls=0)
    from .collection import budget_state

    budget = budget_state(root)
    if budget["pending"] or budget["unknown_cost"]:
        raise ValueError("unresolved predecessor collection must be diagnosed before a successor")
    paths = set(workflow.source_paths(root)) | {
        source_dir / "freeze.json", source_dir / "analysis_receipt.json", analysis_path,
        reference_path, receipt_path, provider_path, decision_path,
    }
    commit = committed(root, sorted(paths))
    destination = root / common.directory(run_id)
    if destination.exists():
        raise ValueError("generation namespace already exists; use a new run identity")
    schedule = design.make_schedule([r["template_id"] for r in config["templates"]],
                                    seed=config["seed"], repetitions=config["repetitions"])
    publish(destination / "planned_requests.jsonl",
            common.requests_from_schedule(schedule, config), lines=True)
    freeze = dict(
        schema="painter-responsiveness-generation-freeze/1", run_id=run_id,
        diagnostic_run_id=diagnostic_run_id, recorded_git_commit=commit,
        source_freeze_sha256=hash_file(root / source_dir / "freeze.json"),
        config=config, inputs=bindings(root, sorted(paths)), gates=gates,
        requests_sha256=hash_file(destination / "planned_requests.jsonl"),
        meaningful_margin_primary_iqr=margin, precision=qualified["precision"],
        budget_baseline_usd=provider["existing_conservative_spend_usd"],
        prior_namespace_accounting=budget, target_work_ids=decision["target_work_ids"],
        decision_path=str(decision_path), provider_preflight_path=str(provider_path),
        claim="Prospective permission to test; no result or human perception established.",
    )
    publish(destination / "generation_freeze.json", freeze)
    return dict(status="prepared", run_id=run_id, generation_calls=0,
                next="Commit the generation freeze and request inventory before collect --live.")


def verify_qualification(root, freeze):
    """Recheck evidence, not merely a manually set ready flag, before using G0."""
    from .human_package import verify_ratings

    source_dir = common.directory(freeze["diagnostic_run_id"])
    verify_bindings(root, freeze["inputs"])
    receipt = verify_ratings(root, freeze["diagnostic_run_id"], phase="validation")
    reference_path = source_dir / "reference_validation.json"
    if receipt["reference_validation_sha256"] != hash_file(root / reference_path):
        raise ValueError("reference qualification changed")
    reference = read_json(root / reference_path)
    bound = {item["path"] for item in freeze["inputs"]}
    decision_path = freeze["decision_path"]
    provider_path = freeze["provider_preflight_path"]
    required = {str(reference_path), decision_path, provider_path,
                str(source_dir / "analysis.json"), str(source_dir / "analysis_receipt.json"),
                str(source_dir / "freeze.json"),
                str(source_dir / "human_ratings_validation_receipt.json")}
    if not required.issubset(bound):
        raise ValueError("generation qualification inputs must be bound")
    decision = read_json(root / decision_path)
    if (decision["reference_validation_sha256"] != hash_file(root / reference_path)
            or decision["package_id"] != reference["package_id"]
            or decision["meaningful_margin_primary_iqr"] != freeze["meaningful_margin_primary_iqr"]
            or decision["target_work_ids"] != freeze["target_work_ids"]):
        raise ValueError("generation decision/target mismatch")
    config = freeze["config"]
    analysis = _verified_analysis(root, source_dir, freeze["source_freeze_sha256"])
    margin = freeze["meaningful_margin_primary_iqr"]
    simulation = inference.simulate_design(
        analysis["retained_noise"], seed=config["simulation_seed"],
        trials=config["simulation_trials"], repetitions=config["repetitions"],
        effects=[[0, 0], [-margin, -margin], [-margin, 0], [0, -margin]], alpha=config["alpha"])
    qualified = qualify(reference, decision, simulation)
    if qualified["precision"] != freeze["precision"]:
        raise ValueError("frozen precision qualification differs from the human criteria")
    provider = read_json(root / provider_path)
    if (provider["freeze_sha256"] != freeze["source_freeze_sha256"]
            or provider["existing_conservative_spend_usd"] != freeze["budget_baseline_usd"]):
        raise ValueError("provider/budget qualification mismatch")
    gates = common.generation_gate(qualified["reference"], qualified["human"],
                                   qualified["precision"], provider)
    if gates != freeze["gates"] or gates["status"] != "ready":
        raise ValueError("actual qualification evidence does not authorize this generation")
    return provider
