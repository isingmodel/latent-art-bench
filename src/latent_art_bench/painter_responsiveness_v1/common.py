"""New-study paths, immutable publication and explicit execution gates."""

from __future__ import annotations

from pathlib import Path

from latent_art_bench.io import read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import identifier

NAMESPACE = "painter_responsiveness_v1"
PACKAGE = Path("src/latent_art_bench") / NAMESPACE
STUDIES = Path("studies") / NAMESPACE
CONFIG = Path("configs") / NAMESPACE / "study.json"
MANIFESTS = Path("data/manifests") / NAMESPACE
WORKSPACE = Path("research_workspace") / NAMESPACE
REPORTS = Path("reports") / NAMESPACE
DIAGNOSTIC_ID = "prv1-diagnostic-20260908"


def directory(run_id):
    return MANIFESTS / identifier(run_id)


def configuration(root):
    config = read_json(root / CONFIG)
    if (
        config["feature_index"] != 2
        or config["feature_name"] != "chroma_median"
        or config["primary_pipeline"] != "primary512"
        or config["repetitions"] != 4
        or len(config["templates"]) != 6
        or config["maximum_images"] != 192
        or set(config["style_clauses"]) != {"free", "generic", "monet", "cezanne"}
        or set(config["polarity_clauses"]) != {"muted", "vivid"}
    ):
        raise ValueError("configuration differs from the bounded responsiveness design")
    return config


def requests_from_schedule(schedule, config):
    templates = {r["template_id"]: r for r in config["templates"]}
    rows = []
    for row in schedule:
        template = templates[row["template_id"]]
        prompt = " ".join(filter(None, (
            config["base_prompt"], config["style_clauses"][row["arm"]],
            "Scene: " + template["scene_text"], config["polarity_clauses"][row["polarity"]],
            config["closing_prompt"],
        )))
        rows.append(dict(
            row, scene_text=template["scene_text"], content_class=template["content_class"],
            fine_subject=template["fine_subject"], route=config["route"],
            payload=dict(model=config["model"], prompt=prompt, n=1, aspect_ratio="1:1",
                         output_format="png", provider=dict(
                             only=[config["provider"]], allow_fallbacks=False)),
        ))
    return rows


def generation_gate(reference_validation, human_plan, precision, provider):
    """Missing evidence stays missing; task authorization cannot fabricate validation."""
    checks = {
        "reference_range_validated": (reference_validation.get("status")
            == "ready_for_responsible_human_margin_decision"
            and reference_validation.get("responsible_human_range_accepted") is True),
        "fine_content_independently_coded": reference_validation.get(
            "independent_fine_content_coding") is True,
        "reference_target_fixed": reference_validation.get("target_frozen") is True,
        "human_assessment_feasible": human_plan.get("status") == "feasible",
        "meaningful_margin_fixed": precision.get("margin_status") == "validated",
        "precision_accepted": precision.get("decision") == "proceed",
        "provider_contract_available": provider.get("contract_available") is True,
        "budget_available": provider.get("budget_available") is True,
    }
    return dict(
        status="ready" if all(checks.values()) else "not_ready", checks=checks,
        missing=[name for name, passed in checks.items() if not passed],
        task_authorized=True,
        claim="No causal or perceptual conclusion follows from gate availability.",
    )
