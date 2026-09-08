"""Fixed computational study identities and exact prospective request inventory."""

from pathlib import Path

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_revision_v1 import common as retained
from latent_art_bench.painter_distribution_study_v1 import transport
from latent_art_bench.painter_feature_generation_v2.artifacts import identifier
from latent_art_bench.painter_responsiveness_v1 import design

NAMESPACE = "painter_responsiveness_v2"
PACKAGE = Path("src/latent_art_bench") / NAMESPACE
MANIFESTS = Path("data/manifests") / NAMESPACE
WORKSPACE = Path("research_workspace") / NAMESPACE
REPORTS = Path("reports") / NAMESPACE
STUDIES = Path("studies") / NAMESPACE
CONFIG = Path("configs") / NAMESPACE / "study.json"
RUN_ID = "prv2-oauth-20260908"


def directory(run_id):
    return MANIFESTS / identifier(run_id)


def configuration(root):
    c = read_json(root / CONFIG)
    scaler = read_json(root / retained.MAIN / "scalers.json")["primary512"]["scaler"]
    if (c["route"] != "oauth_gpt_image_2" or c["model"] != "gpt-image-2"
            or c["repetitions"] != 4 or len(c["templates"]) != 6
            or c["maximum_images"] != 192 or c["feature_index"] != 2
            or c["feature_name"] != "chroma_median" or c["primary_pipeline"] != "primary512"
            or c["primary_chroma_center"] != scaler["center"][2]
            or c["primary_chroma_scale"] != scaler["scale"][2]
            or c["maximum_new_openrouter_spend_usd"] != 0
            or c["requested_rendering"] != dict(size="1024x1024", quality="medium",
                                                output_format="png", background="opaque")):
        raise ValueError("configuration differs from the fixed computational-only design")
    return c


def requests(config):
    templates = {t["template_id"]: t for t in config["templates"]}
    schedule = design.make_schedule(templates, seed=config["seed"],
                                    repetitions=config["repetitions"])
    result = []
    for row in schedule:
        template = templates[row["template_id"]]
        prompt = " ".join(filter(None, (
            config["base_prompt"], config["style_clauses"][row["arm"]],
            "Scene: " + template["scene_text"], config["polarity_clauses"][row["polarity"]],
            config["closing_prompt"],
        )))
        result.append(dict(row,
            request_id=row["request_id"].replace("prv1:", "prv2:", 1),
            block_id=row["block_id"].replace("prv1:", "prv2:", 1),
            scene_text=template["scene_text"], content_class=template["content_class"],
            fine_subject=template["fine_subject"], route=config["route"],
            payload=transport.payload(config["route"], prompt)))
    design.validate_schedule(result)
    return result
