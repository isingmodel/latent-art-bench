"""Synthetic metadata and byte fixtures; never decode pixels or call providers."""

import json

import pytest

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, publish
from latent_art_bench.painter_responsiveness_v1 import common, human, human_package

RUN = "test-human"
SUBJECTS = [("water", "river_stream"), ("built", "buildings_street"),
            ("land", "fields_garden")]


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    monkeypatch.setattr(human_package, "verify", lambda *_: {})
    monkeypatch.setattr(human_package, "committed", lambda *_: "test-commit")
    monkeypatch.setattr(human_package.features, "normalize", lambda *_a, **_k: pytest.fail(
        "this suite must not access image pixels"))
    config = dict(seed=7, templates=[dict(template_id=f"{b}{i}", content_class=b, fine_subject=f)
                                    for b, f in SUBJECTS for i in range(2)])
    monkeypatch.setattr(common, "configuration", lambda _: config)
    directory = tmp_path / common.directory(RUN)
    publish(directory / "freeze.json", {"test_only": True})
    panel, works = [], []
    for i, painter in enumerate(human_package.PAINTER_NAMES):
        source = common.WORKSPACE / f"synthetic-reference-{i}.bin"
        (tmp_path / source).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / source).write_bytes(f"not an image {i}".encode())
        panel.append(dict(work_id=f"work-{i}", painter_id=painter, content_class="land",
                          response_path=str(source), response_sha256=hash_file(tmp_path / source)))
        works.append(dict(image_id=f"work-{i}", painter_id=painter, content_class="land",
                          raw_chroma={"primary512": 10.0 + i},
                          common_primary_scaled_chroma={"primary512": float(i)},
                          raw_pipeline_span=0.0, pipeline_span_primary_iqr_units=0.0,
                          capture_workflow="unresolved"))
    publish(tmp_path / human_package.retained.MAIN / "reference_panel.jsonl", panel, lines=True)
    assert human_package.prepare(tmp_path, RUN)["references"] == 2
    freeze = read_json(directory / "human_freeze.json")
    preview = tmp_path / common.WORKSPACE / RUN / "human_reference_preview"
    human.write_interface(freeze["tasks"]["public"], preview)
    for asset in freeze["tasks"]["private"]["assets"]:
        destination = preview / asset["public_path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(b"opaque synthetic display bytes, never decoded")
    publish(directory / "human_preview_receipt.json", dict(
        phase="technical_preview",
        freeze_sha256=hash_file(directory / "human_freeze.json"),
        outputs=bindings(tmp_path, [p.relative_to(tmp_path) for p in preview.rglob("*")
                                   if p.is_file()])))
    publish(directory / "analysis.json", {"diagnostics": {"reference_chroma": {"works": works}}})
    publish(directory / "analysis_receipt.json", dict(
        analysis_sha256=hash_file(directory / "analysis.json"),
        freeze_sha256=hash_file(directory / "freeze.json")))
    return tmp_path, freeze


def session(prepared, phase="validation", *, bad_code=False):
    root, freeze = prepared
    raters = ["r1", "r2"] if not bad_code else ["person@example.org"]
    plan = dict(responsible_human="Private responsible-person name", recruitment="Recorded plan",
                institutional_requirements="Recorded determination", storage="Private storage",
                consent_text="Supplied participant information.", phase=phase,
                assignments={r: [t["task_id"] for t in freeze["tasks"]["public"]["tasks"]]
                             for r in raters}, rater_roles={r: "independent" for r in raters})
    source = root / f"submitted-plan-{phase}.json"
    source.write_text(json.dumps(plan, indent=1))
    result = human_package.create_session(root, RUN, source)
    return result, plan, source


def submissions(prepared, plan):
    root, freeze = prepared
    paths = []
    for rater in plan["assignments"]:
        answers = []
        for task in freeze["tasks"]["public"]["tasks"]:
            annotation = task["kind"] == "reference_annotation"
            labels = {k: v[0] for k, v in human.ANNOTATION_OPTIONS.items()}
            labels.update(content_class="land", fine_content="fields_garden")
            answers.append(dict(task_id=task["task_id"], status="rated", notes="private-note",
                                rating=None if annotation else 4,
                                annotations=labels if annotation else None))
        value = dict(schema_version=1, package_id=freeze["tasks"]["public"]["package_id"],
                     rater_id=rater, phase=plan["phase"], respondent_kind="human", consent=True,
                     answers=answers)
        path = root / f"submitted-{plan['phase']}-{rater}.json"
        path.write_text(json.dumps(value, indent=3) + "\n")
        paths.append(path)
    return paths


def test_sessions_have_disjoint_phase_paths_and_retain_exact_private_plan(prepared):
    root, _ = prepared
    for phase in ("usability_pilot", "validation"):
        result, _, original = session(prepared, phase)
        assert result["phase"] == phase
        retained = root / human_package.phase_directory(RUN, phase) / "plan.json"
        assert retained.read_bytes() == original.read_bytes()
        receipt = human_package.verify_session(root, RUN, phase=phase)
        assert "Private responsible-person name" not in json.dumps(receipt)
        assert receipt["phase"] == phase
    with pytest.raises(ValueError, match="terminal"):
        session(prepared)


def test_changed_h0_freeze_cannot_reuse_old_preview(prepared):
    root, _ = prepared
    path = root / common.directory(RUN) / "human_freeze.json"
    value = read_json(path)
    value["display"] = "changed after preview"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="H0 freeze"):
        session(prepared)


def test_unsafe_asset_path_fails_before_pixel_access(prepared):
    root, _ = prepared
    path = root / common.directory(RUN) / "human_freeze.json"
    value = read_json(path)
    value["tasks"]["private"]["assets"][0]["public_path"] = "../private.json"
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="confined"):
        human_package.materialize(root, RUN)


def test_contact_like_participant_codes_rejected_before_session_creation(prepared):
    with pytest.raises(ValueError, match="opaque"):
        session(prepared, bad_code=True)


def test_tampered_retained_plan_is_rejected(prepared):
    root, _ = prepared
    session(prepared)
    plan = root / human_package.phase_directory(RUN, "validation") / "plan.json"
    plan.write_bytes(plan.read_bytes() + b" ")
    with pytest.raises(ValueError, match="plan changed"):
        human_package.verify_session(root, RUN)


def test_validation_import_retains_exports_and_hashes_all_private_provenance(prepared):
    root, _ = prepared
    _, plan, _ = session(prepared)
    paths = submissions(prepared, plan)
    result = human_package.import_ratings(root, RUN, paths)
    assert result["status"] == "blocked_reference"  # only one synthetic work per painter
    receipt = human_package.verify_ratings(root, RUN)
    retained = root / human_package.phase_directory(RUN, "validation")
    for i, source in enumerate(paths):
        copied = retained / "submitted_exports" / f"{i:04d}.json"
        assert copied.read_bytes() == source.read_bytes()
    bound_paths = {r["path"] for r in receipt["inputs"]}
    assert str((retained / "validated_ratings.json").relative_to(root)) in bound_paths
    assert str((retained / "plan.json").relative_to(root)) in bound_paths
    public = (root / common.directory(RUN) / "reference_validation.json").read_text()
    assert "private-note" not in public and "Private responsible-person name" not in public
    with pytest.raises(ValueError, match="terminal"):
        human_package.import_ratings(root, RUN, paths)
    raw = retained / "submitted_exports" / "0000.json"
    raw.write_bytes(raw.read_bytes() + b" ")
    with pytest.raises(ValueError, match="bound input changed"):
        human_package.verify_ratings(root, RUN)


def test_pilot_snapshot_cannot_replace_or_block_later_validation(prepared):
    root, _ = prepared
    _, pilot_plan, _ = session(prepared, "usability_pilot")
    result = human_package.import_ratings(root, RUN, submissions(prepared, pilot_plan),
                                         phase="usability_pilot")
    assert result["status"] == "usability_pilot_only"
    assert not (root / common.directory(RUN) / "reference_validation.json").exists()
    receipt = human_package.verify_ratings(root, RUN, phase="usability_pilot")
    assert receipt["phase"] == "usability_pilot"
    _, validation_plan, _ = session(prepared)
    result = human_package.import_ratings(root, RUN, submissions(prepared, validation_plan))
    assert result["phase"] == "validation"


def test_import_refuses_changed_numeric_input_before_publishing_responses(prepared):
    root, _ = prepared
    _, plan, _ = session(prepared)
    path = root / common.directory(RUN) / "analysis.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="analysis receipt"):
        human_package.import_ratings(root, RUN, submissions(prepared, plan))
    assert not (root / human_package.phase_directory(RUN, "validation")
                / "validated_ratings.json").exists()
