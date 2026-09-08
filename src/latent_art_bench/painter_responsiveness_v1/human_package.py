"""Bind and prepare local blinded previews of the already exposed reference panel."""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
from PIL import Image

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_distribution_revision_v1 import common as retained
from latent_art_bench.painter_feature_generation_v2 import features
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    confined,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1.common import committed

from . import common, human
from .workflow import verify

PAINTER_NAMES = {"claude_monet": "Claude Monet", "paul_cezanne": "Paul Cézanne"}


def prepare(root, run_id):
    """Create the H0 task and exact-source freeze; do not open pixels."""
    verify(root, run_id)
    directory = root / common.directory(run_id)
    panel = read_jsonl(root / retained.MAIN / "reference_panel.jsonl")
    rows = []
    for item in panel:
        path = (root / item["response_path"]).resolve()
        path.relative_to((root / "research_workspace").resolve())
        if hash_file(path) != item["response_sha256"]:
            raise ValueError("reference image bytes differ from the retained source")
        rows.append(dict(image_id=item["work_id"], image_path=item["response_path"],
                         painter_id=item["painter_id"],
                         painter_name=PAINTER_NAMES[item["painter_id"]],
                         content_class=item["content_class"]))
    tasks = human.make_tasks([], rows, common.configuration(root)["seed"])
    freeze = dict(
        run_id=run_id, source_freeze_sha256=hash_file(directory / "freeze.json"),
        recorded_git_commit=committed(root, [common.directory(run_id) / "freeze.json"]),
        inputs=bindings(root, [Path(r["image_path"]) for r in rows]),
        display="Fixed primary512 normalization, aspect preserved, metadata-free RGB PNG.",
        authority="PROTOCOL.md H0: previously exposed 70 references, no new eligibility decision.",
        new_source_images=0, new_human_ratings=0, tasks=tasks,
    )
    publish(directory / "human_freeze.json", freeze)
    return dict(status="prepared", references=len(rows), tasks=len(tasks["public"]["tasks"]),
                next="Commit the H0 freeze before preparing display pixels.")


def _human_freeze(root, run_id):
    verify(root, run_id)
    directory = root / common.directory(run_id)
    relative_freeze = common.directory(run_id) / "human_freeze.json"
    freeze = read_json(root / relative_freeze)
    committed(root, [relative_freeze])
    verify_bindings(root, freeze["inputs"])
    if (freeze["run_id"] != run_id
            or freeze["source_freeze_sha256"] != hash_file(directory / "freeze.json")):
        raise ValueError("human/source freeze mismatch")
    tasks = freeze["tasks"]
    if tasks["public"]["package_id"] != tasks["private"]["package_id"]:
        raise ValueError("public/private human package mismatch")
    assets = tasks["private"]["assets"]
    if {a["source_path"] for a in assets} != {r["path"] for r in freeze["inputs"]}:
        raise ValueError("human assets do not match the exact-source freeze")
    for asset in assets:
        confined(root, asset["source_path"], common.WORKSPACE.parent)
        if not re.fullmatch(r"assets/[0-9a-f]{32}\.png", asset["public_path"]):
            raise ValueError("display assets require opaque confined PNG paths")
    return freeze


def _preview(root, run_id):
    freeze = _human_freeze(root, run_id)
    directory = root / common.directory(run_id)
    preview = read_json(directory / "human_preview_receipt.json")
    committed(root, [common.directory(run_id) / "human_preview_receipt.json"])
    if (preview.get("phase") != "technical_preview"
            or preview["freeze_sha256"] != hash_file(directory / "human_freeze.json")):
        raise ValueError("human preview does not match its committed H0 freeze")
    verify_bindings(root, preview["outputs"])
    return freeze, preview


def phase_directory(run_id, phase):
    common.directory(run_id)  # Validate the run component before returning an ignored path.
    if phase not in {"usability_pilot", "validation"}:
        raise ValueError("a declared human phase is required")
    return common.WORKSPACE / run_id / "human_sessions" / phase


def materialize(root, run_id):
    """Display normalization only, under the committed H0 exact-source freeze."""
    freeze = _human_freeze(root, run_id)
    directory = root / common.directory(run_id)
    relative_freeze = common.directory(run_id) / "human_freeze.json"
    output = root / common.WORKSPACE / run_id / "human_reference_preview"
    with stage_lock(root / common.WORKSPACE / ".human-preview.lock"):
        if output.exists() or (directory / "human_preview_receipt.json").exists():
            raise ValueError("human preview is terminal; never replace its displays in place")
        tasks = freeze["tasks"]
        human.write_interface(tasks["public"], output)
        for asset in tasks["private"]["assets"]:
            original = root / asset["source_path"]
            rgb = features.normalize(original, short_side=512).rgb
            pixels = np.floor(np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
            destination = output / asset["public_path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(pixels).save(destination, format="PNG", optimize=False)
        receipt = dict(
            freeze_sha256=hash_file(root / relative_freeze), phase="technical_preview",
            images=len(tasks["private"]["assets"]), new_measurements=0, human_ratings=0,
            outputs=bindings(root, [p.relative_to(root) for p in output.rglob("*")
                                    if p.is_file()]),
            display_limit="Browser/display color is not calibrated by this package.",
        )
        publish(directory / "human_preview_receipt.json", receipt)
        return dict(status="prepared", phase="technical_preview", images=receipt["images"],
                    page=str((output / "index.html").relative_to(root)),
                    ratings="No human responses exist; technical exports cannot be validation.")


def create_session(root, run_id, plan_path):
    """Create one session per phase from a responsible human's recorded plan."""
    freeze, _ = _preview(root, run_id)
    plan_bytes = Path(plan_path).read_bytes()
    plan = json.loads(plan_bytes)
    required = ("responsible_human", "recruitment", "institutional_requirements", "storage",
                "consent_text", "phase", "assignments", "rater_roles")
    if not isinstance(plan, dict) or any(not plan.get(k) for k in required):
        raise ValueError("a real responsible-human/rater/consent plan is required")
    phase = plan["phase"]
    relative_session = phase_directory(run_id, phase)
    confined(root, relative_session, common.WORKSPACE)
    if set(plan["assignments"]) != set(plan["rater_roles"]):
        raise ValueError("rater assignments and role declarations must agree")
    if any(role not in {"maintainer", "independent"} for role in plan["rater_roles"].values()):
        raise ValueError("declare each human rater as maintainer or independent")
    if any(not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", rater) for rater in plan["assignments"]):
        raise ValueError("participant codes must be opaque portable identifiers, not contacts")
    directory = root / common.directory(run_id)
    receipt_path = directory / f"human_session_{phase}_receipt.json"
    destination = root / relative_session / "public"
    with stage_lock(root / common.WORKSPACE / ".human-session.lock"):
        if (root / relative_session).exists() or receipt_path.exists():
            raise ValueError("session is terminal; never change assigned tasks in place")
        public = freeze["tasks"]["public"]
        human.write_interface(public, destination, plan["assignments"], phase=phase,
                              consent_text=plan["consent_text"])
        original = root / common.WORKSPACE / run_id / "human_reference_preview"
        for asset in freeze["tasks"]["private"]["assets"]:
            target = destination / asset["public_path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write((original / asset["public_path"]).read_bytes())
        # Exact submitted plan bytes and any identifying details remain ignored.
        retained_plan = root / relative_session / "plan.json"
        with retained_plan.open("xb") as handle:
            handle.write(plan_bytes)
        publish(receipt_path, dict(
            phase=phase, human_freeze_sha256=hash_file(directory / "human_freeze.json"),
            preview_receipt_sha256=hash_file(directory / "human_preview_receipt.json"),
            source_plan_sha256=hash_file(retained_plan),
            retained_plan_sha256=hash_file(retained_plan),
            package_id=public["package_id"], rater_count=len(plan["assignments"]),
            outputs=bindings(root, [p.relative_to(root) for p in destination.rglob("*")
                                   if p.is_file()]),
        ))
    return dict(status="prepared", phase=phase,
                page=str((destination / "index.html").relative_to(root)))


def verify_session(root, run_id, *, phase="validation"):
    freeze, _ = _preview(root, run_id)
    directory = root / common.directory(run_id)
    relative_receipt = common.directory(run_id) / f"human_session_{phase}_receipt.json"
    session_path = root / phase_directory(run_id, phase)
    session = read_json(root / relative_receipt)
    committed(root, [relative_receipt])
    if (session["phase"] != phase
            or session["human_freeze_sha256"] != hash_file(directory / "human_freeze.json")
            or session["preview_receipt_sha256"]
            != hash_file(directory / "human_preview_receipt.json")
            or session["package_id"] != freeze["tasks"]["public"]["package_id"]):
        raise ValueError("human session/H0 freeze chain mismatch")
    if hash_file(session_path / "plan.json") != session["retained_plan_sha256"]:
        raise ValueError("registered human plan changed")
    verify_bindings(root, session["outputs"])
    return session


def import_ratings(root, run_id, submission_paths, *, phase="validation"):
    """Publish one terminal response snapshot per phase; partial imports stay partial."""
    from .reference_validation import summarize

    verify_session(root, run_id, phase=phase)
    directory = root / common.directory(run_id)
    relative_session = phase_directory(run_id, phase)
    session_path = root / relative_session
    plan = read_json(session_path / "plan.json")
    if plan["phase"] != phase:
        raise ValueError("registered plan phase differs from requested import phase")
    freeze = read_json(directory / "human_freeze.json")
    raw = [Path(p).read_bytes() for p in submission_paths]
    submissions = [json.loads(data) for data in raw]
    validated = human.validate_ratings(freeze["tasks"]["public"], submissions,
                                       plan["assignments"], phase=phase)
    receipt_path = directory / f"human_ratings_{phase}_receipt.json"
    validated_path = session_path / "validated_ratings.json"
    reference_path = directory / "reference_validation.json"
    result = None
    if phase == "validation":
        analysis_receipt = read_json(directory / "analysis_receipt.json")
        if (analysis_receipt["analysis_sha256"] != hash_file(directory / "analysis.json")
                or analysis_receipt["freeze_sha256"] != hash_file(directory / "freeze.json")):
            raise ValueError("human reference diagnostics differ from the analysis receipt")
        diagnostic = read_json(directory / "analysis.json")["diagnostics"]
        result = summarize(diagnostic["reference_chroma"], freeze["tasks"]["public"],
                           freeze["tasks"]["private"], validated, plan["rater_roles"],
                           common.configuration(root)["templates"])
    with stage_lock(root / common.WORKSPACE / ".human-import.lock"):
        if (receipt_path.exists() or validated_path.exists()
                or (session_path / "submitted_exports").exists()
                or (phase == "validation" and reference_path.exists())):
            raise ValueError("ratings import is terminal; never replace response evidence")
        source_paths = [common.directory(run_id) / name for name in
                        ("freeze.json", "human_freeze.json", "human_preview_receipt.json",
                         f"human_session_{phase}_receipt.json")]
        source_paths.append(relative_session / "plan.json")
        for index, data in enumerate(raw):
            relative_export = relative_session / "submitted_exports" / f"{index:04d}.json"
            target = root / relative_export
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as handle:
                handle.write(data)
            source_paths.append(relative_export)
        publish(validated_path, validated)
        source_paths.append(validated_path.relative_to(root))
        receipt = dict(phase=phase, package_id=freeze["tasks"]["public"]["package_id"],
                       human_freeze_sha256=hash_file(directory / "human_freeze.json"),
                       session_receipt_sha256=hash_file(
                           directory / f"human_session_{phase}_receipt.json"),
                       submitted_exports=len(raw), ratings=validated["n_ratings"],
                       missing=validated["n_missing"], generation_authorized=False)
        if result is not None:
            private_result = session_path / "reference_validation_private.json"
            publish(private_result, result)
            public_result = dict(result, works=[
                {key: value for key, value in work.items() if key != "judgments"}
                for work in result["works"]])
            publish(reference_path, public_result)
            source_paths.extend([private_result.relative_to(root),
                                 common.directory(run_id) / "analysis.json",
                                 common.directory(run_id) / "analysis_receipt.json"])
            receipt.update(status=result["status"],
                           reference_validation_sha256=hash_file(reference_path))
        else:
            receipt.update(status="usability_pilot_only")
        receipt["inputs"] = bindings(root, source_paths)
        publish(receipt_path, receipt)
    return dict(status=receipt["status"], phase=phase, ratings=validated["n_ratings"],
                missing=validated["n_missing"], generation_authorized=False)


def verify_ratings(root, run_id, *, phase="validation"):
    """Verify retained exact exports, plan, session and derived-summary provenance."""
    session = verify_session(root, run_id, phase=phase)
    directory = root / common.directory(run_id)
    relative = common.directory(run_id) / f"human_ratings_{phase}_receipt.json"
    receipt = read_json(root / relative)
    committed(root, [relative])
    if (receipt["phase"] != phase or receipt["package_id"] != session["package_id"]
            or receipt["human_freeze_sha256"] != hash_file(directory / "human_freeze.json")
            or receipt["session_receipt_sha256"]
            != hash_file(directory / f"human_session_{phase}_receipt.json")):
        raise ValueError("human rating/session/H0 chain mismatch")
    verify_bindings(root, receipt["inputs"])
    if phase == "validation" and receipt["reference_validation_sha256"] != hash_file(
        directory / "reference_validation.json"
    ):
        raise ValueError("reference validation summary changed")
    return receipt
