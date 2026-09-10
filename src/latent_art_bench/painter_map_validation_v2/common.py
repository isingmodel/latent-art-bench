"""The single prospective R10 allocation and disjoint operational paths."""

import json
from pathlib import Path

import numpy as np

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_study_v1.study import prompt
from latent_art_bench.painter_distribution_study_v1.transport import payload
from latent_art_bench.painter_feature_generation_v2.artifacts import identifier

NAMESPACE = "painter_map_validation_v2"
RUN_ID = "pmv2-20260910"
PACKAGE = Path("src/latent_art_bench") / NAMESPACE
STUDIES = Path("studies") / NAMESPACE
MANIFESTS = Path("data/manifests") / NAMESPACE
WORKSPACE = Path("research_workspace") / NAMESPACE
REPORTS = Path("reports") / NAMESPACE
CONFIG = STUDIES / "study.json"
SCENES = STUDIES / "scenes.json"
INPUTS = STUDIES / "inputs.json"
QUALIFICATION = STUDIES / "qualification.json"
PREFLIGHT_ID = "pmv2-prefreeze-20260910"
DISPATCH_ID = "pmv2-dispatch-20260910"
METADATA = MANIFESTS / "metadata" / PREFLIGHT_ID / "receipt.json"
ENDPOINT_METADATA = Path("studies/painter_naming_replication_v1/endpoint_metadata.json")
PREFLIGHT_SOURCE = Path("studies/painter_map_validation_v1/preflight.py")
BUDGET_RECEIPT = Path(
    "data/manifests/painter_naming_replication_v1/pnrv1-20260910/collection_receipt.json"
)
MAIN_RECEIPT = Path(
    "data/manifests/painter_distribution_study_v1/pdsv1-main-immediate-20260907/collection_receipt.json"
)
ZERO_PAID_RECEIPTS = (
    Path("data/manifests/painter_clause_validation_v1/pcvv1-20260910/collection_receipt.json"),
    Path("data/manifests/painter_clause_successor_v1/pcsv1-20260910/collection_receipt.json"),
)
ARMS = ("artist_free", "named")
CLASSES = ("water", "built", "land")
PIPELINES = ("primary512",)
PAINTER_ID = "paul_cezanne"
ROUTE = "flux_2_max"
MODEL = "black-forest-labs/flux.2-max"


def expected_config():
    return dict(
        schema="painter-map-validation/2",
        run_id=RUN_ID,
        assignment_seed=2026091071,
        repetitions=10,
        scenes_per_class=4,
        maximum_images=240,
        maximum_attempts=248,
        maximum_technical_retries=8,
        maximum_in_flight=2,
        minimum_start_interval_seconds=5,
        maximum_collection_seconds=86400,
        overall_spending_ceiling_usd=75,
        historical_accounted_usd=50.7219185,
        request_reservation_usd=5,
        planning_attempt_usd=0.075,
        minimum_free_bytes=5 * 1024**3,
    )


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def configuration(root):
    value = read_json(Path(root) / CONFIG)
    if canonical(value) != canonical(expected_config()):
        raise ValueError("configuration differs from the sole R10 allocation")
    return value


def directory(run_id):
    if identifier(run_id) != RUN_ID:
        raise ValueError("only the designated R10 collection is authorized")
    return MANIFESTS / run_id


def scenes(root):
    value = read_json(Path(root) / SCENES)
    briefs = value["briefs"]
    expected = [(f"pmv2_{c}{i:02d}", c) for c in CLASSES for i in range(1, 5)]
    if [(b["brief_id"], b["content_class"]) for b in briefs] != expected or any(
        set(b) != {"brief_id", "content_class", "detailed"}
        or not isinstance(b["detailed"], str)
        or not b["detailed"].strip()
        for b in briefs
    ):
        raise ValueError("the twelve fixed scene briefs are required")
    return briefs


def plan_from_scenes(briefs, config):
    if canonical(config) != canonical(expected_config()):
        raise ValueError("fixed prospective configuration required")
    rng = np.random.default_rng(config["assignment_seed"])
    blocks = []
    for brief in briefs:
        for repetition in range(config["repetitions"]):
            block_id = f"pmv2:{brief['brief_id']}:r{repetition:02d}"
            blocks.append(
                [
                    dict(
                        request_id=f"{block_id}:{arm}",
                        block_id=block_id,
                        experiment="map",
                        route=ROUTE,
                        template_id=brief["brief_id"],
                        content_class=brief["content_class"],
                        repetition=repetition,
                        arm=str(arm),
                        painter_id=PAINTER_ID,
                        payload=payload(ROUTE, prompt(brief, PAINTER_ID, str(arm))),
                    )
                    for arm in rng.permutation(ARMS)
                ]
            )
    result = []
    for order, index in enumerate(rng.permutation(len(blocks)), 1):
        for position, row in enumerate(blocks[index]):
            result.append(dict(row, sequence=len(result), block_order=order, within_block=position))
    return result


def build_plan(root, config=None):
    return plan_from_scenes(scenes(root), config or configuration(root))


requests = build_plan


def validate_design(requests, config):
    root = Path(__file__).resolve().parents[3]
    if len(requests) != 240 or canonical(requests) != canonical(build_plan(root, config)):
        raise ValueError("request identities, payloads or prospective pair order differ")
    return [requests[i : i + 2] for i in range(0, len(requests), 2)]


def binding_paths(root):
    from . import precision

    paths = {
        CONFIG,
        SCENES,
        INPUTS,
        QUALIFICATION,
        METADATA,
        METADATA.with_name("started.json"),
        ENDPOINT_METADATA,
        PREFLIGHT_SOURCE,
        BUDGET_RECEIPT,
        MAIN_RECEIPT,
        STUDIES / "PROTOCOL.md",
        STUDIES / "TECHNICAL_PROTOCOL.md",
        STUDIES / "DECISION.md",
        STUDIES / "PRECISION_PROTOCOL.md",
        STUDIES / "PRECISION_REVIEW.md",
        STUDIES / "OPERATIONAL_REVIEW.md",
        STUDIES / "PRECOLLECTION_REVIEW.md",
        STUDIES / "ANALYSIS_REVIEW.md",
        *precision.BINDINGS,
        *(precision.OUTPUT_PATH / n for n in ("RUN.json", "precision.json", "PRECISION.md")),
        *ZERO_PAID_RECEIPTS,
    }
    for namespace in (
        "painter_distribution_study_v1",
        "painter_naming_replication_v1",
        "painter_clause_validation_v1",
        "painter_clause_successor_v1",
    ):
        paths.update(
            p.relative_to(root)
            for p in (Path(root) / "data/manifests" / namespace).glob("*/generation_events.jsonl")
        )
    return sorted(paths)
