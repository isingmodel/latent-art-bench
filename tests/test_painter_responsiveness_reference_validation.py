"""Synthetic reference/task fixtures only; these are not collected human evidence."""

import copy

import pytest

from latent_art_bench.painter_responsiveness_v1 import human, reference_validation

SUBJECTS = (("water", "river_stream"), ("built", "buildings_street"),
            ("land", "fields_garden"))


def inputs(n=2):
    refs, works = [], []
    templates = [{"template_id": f"{b}{i}", "content_class": b, "fine_subject": f}
                 for b, f in SUBJECTS for i in range(2)]
    for painter in reference_validation.PAINTERS:
        for broad, fine in SUBJECTS:
            for i in range(n):
                ident = f"{painter}-{broad}-{i}"
                refs.append(dict(image_id=ident, image_path=f"not-opened/{ident}.png",
                                 painter_id=painter, painter_name=painter, content_class=broad))
                works.append(dict(
                    image_id=ident, painter_id=painter, content_class=broad,
                    raw_chroma={"primary512": 10.0 + i, "sensitivity256": 11.0 + i},
                    common_primary_scaled_chroma={"primary512": float(i),
                                                  "sensitivity256": 0.5 + i},
                    raw_pipeline_span=1.0, pipeline_span_primary_iqr_units=0.5,
                    capture_workflow="unresolved",
                ))
    package = human.make_tasks([], refs, 7)
    public, private = package["public"], package["private"]
    keys = {k["task_id"]: k for k in private["task_key"]}
    by_id = {w["image_id"]: w for w in works}
    assignments = {r: [t["task_id"] for t in public["tasks"]] for r in ("r1", "r2")}
    exports = []
    for rater in assignments:
        answers = []
        for task in public["tasks"]:
            work = by_id[keys[task["task_id"]]["image_id"]]
            broad = work["content_class"]
            fine = dict(SUBJECTS)[broad]
            annotation = task["kind"] == "reference_annotation"
            labels = {k: v[0] for k, v in human.ANNOTATION_OPTIONS.items()}
            labels.update(content_class=broad, fine_content=fine)
            answers.append(dict(task_id=task["task_id"], status="rated",
                                rating=None if annotation else 3 + int(work["image_id"][-1]),
                                annotations=labels if annotation else None))
        exports.append(dict(schema_version=1, package_id=public["package_id"], rater_id=rater,
                            phase="validation", respondent_kind="human", consent=True,
                            answers=answers))
    return dict(reference_chroma={"works": works}, public=public, private=private,
                rater_roles={"r1": "independent", "r2": "independent"},
                planned_templates=templates), exports, assignments


def summarized(args, exports, assignments):
    ratings = human.validate_ratings(args["public"], exports, assignments)
    return reference_validation.summarize(**args, ratings=ratings)


def test_zero_judgments_is_pending_with_all_planned_groups_and_missingness():
    args, _, assignments = inputs()
    result = summarized(args, [], assignments)
    assert result["status"] == "pending_human_reference_judgments"
    assert len(result["works"]) == 12 and len(result["groups"]) == 6
    assert len(result["blocked_groups"]) == 6 and len(result["unresolved_work_ids"]) == 12
    assert all(len(w["missing_assignments"]) == 4 for w in result["works"])
    assert not result["generation_authorized"] and result["meaningful_margin"] is None


def test_minimum_support_only_yields_human_decision_and_thin_finite_ranges():
    args, exports, assignments = inputs()
    result = summarized(args, exports, assignments)
    assert result["status"] == "ready_for_responsible_human_margin_decision"
    assert not result["generation_authorized"]
    assert result["unresolved_work_ids"] == [] and result["blocked_groups"] == []
    for group in result["groups"]:
        assert group["status"] == "thin_descriptive_support" and group["n_works"] == 2
        assert group["scaled_chroma_ranges"]["primary512"]["span"] == 1
        assert group["human_work_median_range"]["span"] == 1
        assert group["maximum_processing_span_primary_iqr"] == 0.5
    assert all(w["capture_workflow"] == "unresolved" for w in result["works"])


def test_maintainer_is_visible_but_cannot_supply_second_independent_judgment():
    args, exports, assignments = inputs()
    args["rater_roles"]["r2"] = "maintainer"
    result = summarized(args, exports, assignments)
    assert result["status"] == "blocked_reference"
    assert all(g["n_works"] == 0 for g in result["groups"])
    assert all(w["n_independent_vividness"] == 1 for w in result["works"])
    assert any(r["role"] == "maintainer" for r in result["works"][0]["judgments"])


def test_disagreement_is_not_majority_adjudicated_and_zero_span_not_invented():
    args, exports, assignments = inputs()
    annotation = next(a for a in exports[1]["answers"] if a["annotations"] is not None)
    task_id = annotation["task_id"]
    annotation["annotations"]["fine_content"] = "other"
    result = summarized(args, exports, assignments)
    disputed = [w for w in result["works"] if w["status"] == "disputed_independent_codes"]
    assert len(disputed) == 1 and result["status"] == "blocked_reference"
    assert any(r["task_id"] == task_id for r in disputed[0]["judgments"])
    thin = next(g for g in result["groups"] if g["n_works"] == 1)
    assert thin["raw_chroma_ranges"]["primary512"] is None
    assert thin["human_work_median_range"] is None


def test_unresolved_panel_work_blocks_selective_range_even_when_groups_have_two():
    args, exports, assignments = inputs(n=3)
    one_work = args["private"]["task_key"][0]["image_id"]
    omitted = {k["task_id"] for k in args["private"]["task_key"] if k["image_id"] == one_work}
    for response in exports:
        response["answers"] = [a for a in response["answers"] if a["task_id"] not in omitted]
    result = summarized(args, exports, assignments)
    assert all(g["n_works"] >= 2 for g in result["groups"])
    assert result["status"] == "blocked_reference" and result["blocked_groups"] == []
    assert result["unresolved_work_ids"] == [one_work]


def test_different_raters_cannot_supply_disjoint_unpaired_required_judgments():
    args, exports, assignments = inputs()
    for i, response in enumerate(exports):
        response["answers"] = [a for a in response["answers"]
                               if (a["annotations"] is not None) == bool(i)]
    result = summarized(args, exports, assignments)
    assert all(w["independent_complete_rater_ids"] == [] for w in result["works"])
    assert result["status"] == "blocked_reference"


def test_wrong_package_pilot_and_missing_task_membership_rejected():
    args, exports, assignments = inputs()
    ratings = human.validate_ratings(args["public"], exports, assignments)
    for bad_ratings in [dict(ratings, package_id="wrong"), dict(ratings, phase="usability_pilot")]:
        with pytest.raises(ValueError):
            reference_validation.summarize(**args, ratings=bad_ratings)
    malformed = copy.deepcopy(args)
    malformed["reference_chroma"]["works"].pop()
    with pytest.raises(ValueError, match="identity"):
        reference_validation.summarize(**malformed, ratings=ratings)
