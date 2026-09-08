"""Synthetic metadata/response tests; no artwork or provider access."""

import copy
import json

import pytest

from latent_art_bench.painter_responsiveness_v1 import human


def package():
    images = [{"image_id": f"private-image-{i}", "image_path": f"ignored/{i}.jpg",
               "scene_text": "A country road beside trees.", "arm": f"secret-arm-{i}",
               "polarity": "secret-polarity"} for i in range(4)]
    refs = [{"image_id": f"work-{p}-{c}", "image_path": f"references/{p}/{c}.jpg",
             "painter_id": p, "painter_name": name, "content_class": c}
            for p, name in [("p1", "First Painter"), ("p2", "Second Painter")]
            for c in ["water", "built", "land"]]
    return human.make_tasks(images, refs, 901)


def export(public, ids, *, phase="validation"):
    return {"schema_version": 1, "package_id": public["package_id"], "rater_id": "r01",
            "phase": phase, "respondent_kind": "human", "consent": True,
            "answers": [{"task_id": i, "status": "rated", "rating": 4} for i in ids]}


def scalar_ids(public):
    return [t["task_id"] for t in public["tasks"] if t["kind"] == "vividness"]


def test_blinding_task_separation_and_reproducibility():
    result = package()
    assert result == package()
    public, private = result["public"], result["private"]
    encoded = json.dumps(public)
    for forbidden in ["private-image", "ignored/", "secret-arm", "secret-polarity", "work-p1"]:
        assert forbidden not in encoded
    assert len(public["tasks"]) == 28  # 4 * (vividness + adherence + 2 painters) + 6 * 2
    assert len(private["task_key"]) == 28
    for task in public["tasks"]:
        assert task["image"].startswith("assets/") and task["image"].endswith(".png")
        assert ("scene_text" in task) == (task["kind"] == "adherence")
        assert ("references" in task) == (task["kind"] == "resemblance")
    for panel in private["reference_panels"].values():
        assert len(panel["image_ids"]) == 3
        assert panel["selection"] == "one_per_prior_broad_class"
        assert panel["human_content_validation"] == "pending"


def test_seed_changes_opaque_ids_and_plans_do_not_read_paths():
    image = {"image_id": "x", "image_path": "not-present/x.bin", "scene_text": "A road.",
             "arm": "named", "polarity": "vivid"}
    first = human.make_tasks([image], [], 1)
    second = human.make_tasks([image], [], 2)
    assert first["public"]["package_id"] != second["public"]["package_id"]
    assert first["private"]["assets"][0]["source_path"] == "not-present/x.bin"


@pytest.mark.parametrize("path", ["../outside.jpg", "/absolute.jpg", "https://x/y", "C:\\x", "."])
def test_nonportable_or_remote_paths_rejected(path):
    with pytest.raises(ValueError, match="relative"):
        human.make_tasks([{"image_id": "x", "image_path": path}], [], 1)


def test_duplicate_sources_and_incomplete_reference_support():
    ref = {"image_id": "r", "image_path": "r.png", "painter_id": "p",
           "painter_name": "Painter", "content_class": "land"}
    result = human.make_tasks([], [ref], 1)
    assert result["private"]["reference_panels"]["p"]["selection"] == "incomplete_class_support"
    with pytest.raises(ValueError, match="duplicate"):
        human.make_tasks([], [ref, ref], 1)
    duplicate = dict(ref, image_id="second", image_path="./r.png")
    with pytest.raises(ValueError, match="duplicate"):
        human.make_tasks([], [ref, duplicate], 1)


def test_package_binds_private_treatment_join_and_is_input_order_invariant():
    image = {"image_id": "x", "image_path": "x.png", "scene_text": "A road.",
             "arm": "free", "polarity": "vivid"}
    other = dict(image, image_id="y", image_path="y.png")
    first = human.make_tasks([image, other], [], 5)
    assert first == human.make_tasks([other, image], [], 5)
    other["arm"] = "named"
    changed = human.make_tasks([image, other], [], 5)
    assert first["public"]["tasks"] == changed["public"]["tasks"]
    assert first["public"]["package_id"] != changed["public"]["package_id"]


def test_pending_partial_ties_and_display_failure_stay_distinct():
    public = package()["public"]
    ids = scalar_ids(public)
    assignment = {"r01": ids, "r02": ids[:1]}
    result = human.validate_ratings(public, [], assignment)
    assert result["status"] == "pending" and result["n_ratings"] == 0
    assert result["n_missing"] == 5
    response = export(public, ids[:3])
    response["answers"][1].update(status="cannot_judge", rating=None)
    response["answers"][2].update(status="display_failure", rating=None)
    result = human.validate_ratings(public, [response], assignment)
    assert result["status"] == "partial"
    assert [result[k] for k in ("n_ratings", "n_cannot_judge", "n_display_failure")] == [1, 1, 1]
    assert result["n_missing"] == 2 and result["n_submitted_raters"] == 1


def test_complete_disposition_without_any_judgments_remains_pending():
    public = package()["public"]
    ids = scalar_ids(public)
    response = export(public, ids)
    for answer in response["answers"]:
        answer.update(status="cannot_judge", rating=None)
    result = human.validate_ratings(public, [response], {"r01": ids})
    assert result["status"] == "pending" and result["n_ratings"] == 0
    assert result["disposition_status"] == "complete" and result["n_missing"] == 0


@pytest.mark.parametrize("mutation", [
    {"respondent_kind": "synthetic"}, {"respondent_kind": "technical"},
    {"phase": "usability_pilot"}, {"phase": "technical_preview"},
    {"consent": False}, {"package_id": "wrong"}, {"rater_id": "unregistered"},
])
def test_nonhuman_unregistered_or_wrong_phase_never_imported(mutation):
    public = package()["public"]
    ids = scalar_ids(public)
    response = export(public, ids)
    response.update(mutation)
    with pytest.raises(ValueError):
        human.validate_ratings(public, [response], {"r01": ids})


@pytest.mark.parametrize("value", [0, 8, 1.5, True, "4", None])
def test_invalid_scalar_values_rejected(value):
    public = package()["public"]
    ids = scalar_ids(public)
    response = export(public, ids)
    response["answers"][0]["rating"] = value
    with pytest.raises(ValueError, match="integer"):
        human.validate_ratings(public, [response], {"r01": ids})


def test_duplicate_unknown_and_unassigned_tasks_rejected():
    public = package()["public"]
    ids = scalar_ids(public)
    response = export(public, ids)
    for answers in [response["answers"] * 2, [{"task_id": "unknown", "status": "rated"}],
                    response["answers"]]:
        changed = dict(response, answers=answers)
        with pytest.raises(ValueError):
            human.validate_ratings(public, [changed], {"r01": ids[:1]})
    with pytest.raises(ValueError, match="duplicate rater"):
        human.validate_ratings(public, [response, response], {"r01": ids})
    with pytest.raises(ValueError, match="assignment"):
        human.validate_ratings(public, [], {"r01": [ids[0], ids[0]]})


@pytest.mark.parametrize("part,value", [
    ("export", []), ("answer", None), ("rater_id", []), ("task_id", []),
    ("schema_version", True), ("status", []),
])
def test_malformed_json_records_fail_with_validation_error(part, value):
    public = package()["public"]
    ids = scalar_ids(public)
    response = export(public, ids)
    if part == "export":
        response = value
    elif part == "answer":
        response["answers"][0] = value
    elif part in {"task_id", "status"}:
        response["answers"][0][part] = value
    else:
        response[part] = value
    with pytest.raises(ValueError):
        human.validate_ratings(public, [response], {"r01": ids})


def test_unrecognized_export_and_task_fields_rejected():
    public = package()["public"]
    ids = scalar_ids(public)
    for at_top in (True, False):
        response = export(public, ids)
        target = response if at_top else response["answers"][0]
        target["synthetic_rating"] = True
        with pytest.raises(ValueError, match="unknown"):
            human.validate_ratings(public, [response], {"r01": ids})


def test_structured_reference_annotations_validate_without_fabricated_period():
    public = package()["public"]
    task = next(t for t in public["tasks"] if t["kind"] == "reference_annotation")
    response = export(public, [task["task_id"]])
    answer = response["answers"][0]
    answer.update(rating=None, annotations={k: v[-1] for k, v in human.ANNOTATION_OPTIONS.items()})
    result = human.validate_ratings(public, [response], {"r01": [task["task_id"]]})
    assert result["status"] == "complete"
    assert "period" not in answer["annotations"]
    answer["annotations"]["fine_content"] = "free-text-group"
    with pytest.raises(ValueError, match="annotation label"):
        human.validate_ratings(public, [response], {"r01": [task["task_id"]]})


def test_cannot_judge_cannot_smuggle_rating_or_annotation():
    public = package()["public"]
    ids = scalar_ids(public)
    response = export(public, ids)
    response["answers"][0]["status"] = "cannot_judge"
    with pytest.raises(ValueError, match="nonratings"):
        human.validate_ratings(public, [response], {"r01": ids})


def test_interface_is_public_only_local_create_once_and_defaults_technical(tmp_path):
    public = package()["public"]
    public = copy.deepcopy(public)
    public["tasks"][0]["question"] = "</script><script>bad()</script>"
    assert human.write_interface(public, tmp_path) == ["index.html"]
    text = (tmp_path / "index.html").read_text()
    assert "technical_preview" in text and "connect-src 'none'" in text
    assert "private-image" not in text and "ignored/" not in text
    assert "</script><script>bad()" not in text
    assert "fetch(" not in text and "XMLHttpRequest" not in text
    with pytest.raises(FileExistsError):
        human.write_interface(public, tmp_path)
    with pytest.raises(ValueError, match="assignments and consent"):
        human.write_interface(public, tmp_path / "other", phase="validation")


def test_human_interface_requires_registered_assignment_and_supplied_materials(tmp_path):
    public = package()["public"]
    human.write_interface(public, tmp_path, {"r01": scalar_ids(public)},
                          phase="usability_pilot", consent_text="Supplied pilot information.")
    text = (tmp_path / "index.html").read_text()
    assert "Supplied pilot information." in text
    assert '"phase": "usability_pilot"' in text
