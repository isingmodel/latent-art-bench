import copy
import csv
import json
import os
import subprocess
from pathlib import Path

import pytest
from PIL import Image

from latent_art_bench.io import hash_file
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import features
from latent_art_bench.painter_feature_generation_v2.artifacts import publish
from latent_art_bench.painter_prompt_study_v1 import report
from latent_art_bench.painter_prompt_study_v1.common import MANIFESTS, PACKAGE
from latent_art_bench.painter_prompt_study_v1.prompts import CONDITIONS, METHOD_IDS, TEMPLATE_IDS


def _result(complete=True):
    aliases = ["gpt-image-1", "gpt-image-2"]
    result = dict(
        schema_version="painter-prompt-analysis/1.0",
        run_id="fixture-report",
        source_method_id="pfg2-method-20260905",
        calibration_id="fixture-calibration",
        repetitions=4,
        status="complete" if complete else "unavailable_incomplete_grid",
        aliases=aliases,
        methods=list(METHOD_IDS),
        painters=list(PAINTER_IDS),
        families={k: list(v) for k, v in features.FAMILY_NAMES.items()},
        availability=[
            dict(
                alias=a,
                method_id=m,
                condition=c,
                expected=64,
                statuses={"measured": 64}
                if complete
                else {"measured": 2, "failed": 1, "not_generated": 61},
            )
            for a in aliases
            for m in METHOD_IDS
            for c in CONDITIONS
        ],
        service_diagnostics={
            f"{a}/{m}": {
                a: dict(
                    statuses={"generated": 320}
                    if complete
                    else {"generated": 15, "not_attempted": 305},
                    reported_settings={"quality": {"low": 320}, "model": {"None": 320}},
                    decoded_sizes={"1400x1120": 320},
                    setting_mismatches={"quality": 320, "decoded_size": 320},
                )
            }
            for a in aliases
            for m in METHOD_IDS
        },
        copy_diagnostics={"status": "uncalibrated_screen", "candidates": []},
        inputs=[],
    )
    result["template_availability"] = [
        dict(
            alias=row["alias"],
            method_id=row["method_id"],
            condition=row["condition"],
            template_id=template,
            expected=4,
            statuses={"measured": 4}
            if complete
            else (
                {"measured": 2, "failed": 1, "not_generated": 1} if i == 0 else {"not_generated": 4}
            ),
        )
        for row in result["availability"]
        for i, template in enumerate(TEMPLATE_IDS)
    ]
    if not complete:
        return result
    result.update(
        reference_counts=dict(zip(PAINTER_IDS, [297, 106, 141, 105])),
        scaler_development_counts=dict(zip(PAINTER_IDS, [55, 55, 55, 56])),
        inference=dict(
            alpha=0.05,
            family_size=48,
            slot_pair_count=64,
            method="paired_randomization",
            multiplicity="Holm",
            confidence_intervals=False,
        ),
        absolute=[],
        primary=[],
        secondary=[],
        coordinates=[],
        distances=[],
        scene_contributions=[],
        time_diagnostics=[],
    )
    for a in aliases:
        for p in PAINTER_IDS:
            for f in features.FAMILIES:
                for i, m in enumerate(METHOD_IDS):
                    label = dict(alias=a, painter_id=p, family=f, method_id=m)
                    result["absolute"].append(dict(label, finite_distance=3.125 - i))
                    for condition in CONDITIONS:
                        result["distances"].append(
                            dict(label, condition=condition, distance=3.125 - i)
                        )
                    for coordinate in features.FAMILY_NAMES[f]:
                        result["coordinates"].append(
                            dict(
                                label,
                                coordinate=coordinate,
                                median_difference=0.0123456789012345,
                                iqr_ratio=None,
                            )
                        )
                for before, after in report.TRANSITIONS:
                    label = dict(alias=a, painter_id=p, family=f, before=before, after=after)
                    result["primary"].append(
                        dict(
                            label,
                            estimate=-1,
                            raw_p=0.0001,
                            holm_p=0.0048,
                            status="conditional_randomization",
                        )
                    )
                    result["secondary"].append(
                        dict(label, endpoint="control_adjusted_transition", estimate=-0.75)
                    )
                    result["scene_contributions"] += [
                        dict(
                            label,
                            block=b,
                            template_id=t,
                            before_request_sequence=(b * 16 + i) * 3,
                            after_request_sequence=(b * 16 + i) * 3 + 1,
                            order_sequence=(b * 16 + i) * 3,
                            contribution=-1 / 64,
                        )
                        for b in range(4)
                        for i, t in enumerate(TEMPLATE_IDS)
                    ]
                    result["time_diagnostics"].append(
                        dict(
                            label,
                            first_half_mean=-1 / 64,
                            second_half_mean=-1 / 64,
                            contribution_sd=0,
                        )
                    )
                result["secondary"].append(
                    dict(
                        alias=a,
                        painter_id=p,
                        family=f,
                        before="by_name",
                        after="style_aspects",
                        endpoint="overall_transition",
                        estimate=-2,
                    )
                )
    return result


def _fixture(root, result):
    root.mkdir(parents=True, exist_ok=True)
    directory = root / MANIFESTS / result["run_id"]
    directory.mkdir(parents=True)
    source = root / "numeric-input.json"
    source.write_text('{"fixed": true}')
    result = copy.deepcopy(result)
    result["inputs"] = [dict(path="numeric-input.json", sha256=hash_file(source))]
    implementation = root / PACKAGE / "report.py"
    implementation.parent.mkdir(parents=True)
    implementation.write_bytes(Path(report.__file__).read_bytes())
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", (PACKAGE / "report.py").as_posix()], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "Freeze report fixture",
        ],
        cwd=root,
        check=True,
        env=dict(
            os.environ,
            GIT_AUTHOR_DATE="2026-09-05T00:00:00+0000",
            GIT_COMMITTER_DATE="2026-09-05T00:00:00+0000",
        ),
    )
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    publish(
        directory / "generation_freeze.json",
        dict(
            recorded_git_commit=commit,
            inputs=[
                dict(path=(PACKAGE / "report.py").as_posix(), sha256=hash_file(implementation))
            ],
        ),
    )
    freeze_relative = MANIFESTS / result["run_id"] / "generation_freeze.json"
    result["inputs"].append(
        dict(
            path=freeze_relative.as_posix(), sha256=hash_file(directory / "generation_freeze.json")
        )
    )
    publish(directory / "analysis.json", result)
    decision = root / MANIFESTS / result["calibration_id"] / "decision.json"
    publish(decision, {"synthetic_fixture": True})
    return directory


def test_complete_report_renders_all_outputs_and_reproduces_bytes(tmp_path):
    result = _result()
    first, second = tmp_path / "first", tmp_path / "second"
    directory = _fixture(first, result)
    _fixture(second, result)
    receipt = report.execute(first, result["run_id"])
    other = report.execute(second, result["run_id"])
    assert receipt["files"] == other["files"]
    target = first / report.REPORTS / result["run_id"]
    markdown = (target / "REPORT.md").read_text()
    for phrase in (
        "Holm adjustment across all 48 primary endpoints",
        "sharp absence",
        "649 measured",
        "221 new-development",
        "not institutionally independent",
        "All 744 coordinate diagnostics",
        "all 360 generated-condition",
    ):
        assert phrase in markdown
    for name in report.NUMERIC_TABLES:
        with (target / f"{name}.csv").open() as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == len(result[name])
    with (target / "primary.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 48 and rows[0]["raw_p"] == "0.0001"
    assert "lower" not in rows[0] and "upper" not in rows[0]
    assert "0.0123456789012345" in (target / "coordinates.csv").read_text()
    assert len(list((target / "plots").iterdir())) == 6
    for path in (target / "plots").glob("*.png"):
        with Image.open(path) as image:
            assert min(image.size) > 1000
    assert all(hash_file(first / row["path"]) == row["sha256"] for row in receipt["files"])
    assert any(r["path"] == (PACKAGE / "report.py").as_posix() for r in receipt["inputs"])
    assert (directory / "report_receipt.json").exists()
    assert not list(first.rglob("*.image"))
    assert not list((first / report.REPORTS).glob(".report-*"))
    with pytest.raises(FileExistsError, match="already exists"):
        report.execute(first, result["run_id"])


def test_incomplete_report_has_all_availability_and_no_primary_tables_or_plots(
    tmp_path, monkeypatch
):
    result = _result(False)
    _fixture(tmp_path, result)
    monkeypatch.setattr(report, "_plots", lambda *args: pytest.fail("incomplete grid has no plots"))
    receipt = report.execute(tmp_path, result["run_id"])
    target = tmp_path / report.REPORTS / result["run_id"]
    markdown = (target / "REPORT.md").read_text()
    assert "Primary prompt inference is unavailable" in markdown
    assert "**1,920 requests**" in markdown and "**60 measured images**" in markdown
    assert "**90 generated images**" in markdown
    assert not (target / "plots").exists() and not (target / "primary.csv").exists()
    with (target / "availability.csv").open() as handle:
        availability = list(csv.DictReader(handle))
    assert len(availability) == 30
    assert all(
        json.loads(row["statuses"]) == {"measured": 2, "failed": 1, "not_generated": 61}
        for row in availability
    )
    assert receipt["analysis_status"] == "unavailable_incomplete_grid"


@pytest.mark.parametrize(
    "fault",
    [
        "source_hash",
        "missing_primary",
        "selected_incomplete",
        "missing_distance",
        "duplicated_coordinate",
        "missing_scene",
        "template_aggregate",
        "nonfinite_secondary",
        "reduced_planned_count",
        "holm_tamper",
        "inconsistent_effect",
    ],
)
def test_unverified_or_partial_numerical_results_never_publish(tmp_path, fault):
    result = _result(fault != "selected_incomplete")
    if fault == "missing_primary":
        result["primary"].pop()
    elif fault == "selected_incomplete":
        result["primary"] = [{"estimate": -1}]
    elif fault == "missing_distance":
        result["distances"].pop()
    elif fault == "duplicated_coordinate":
        result["coordinates"][-1] = result["coordinates"][0]
    elif fault == "missing_scene":
        result["scene_contributions"].pop()
    elif fault == "template_aggregate":
        result["template_availability"][0]["statuses"] = {"failed": 4}
    elif fault == "nonfinite_secondary":
        result["secondary"][0]["estimate"] = float("nan")
    elif fault == "reduced_planned_count":
        result["availability"][0].update(expected=2, statuses={"measured": 2})
    elif fault == "holm_tamper":
        result["primary"][0]["holm_p"] = 0.0001
    elif fault == "inconsistent_effect":
        result["primary"][0]["estimate"] = -999
    if fault == "nonfinite_secondary":
        with pytest.raises(ValueError, match="nonfinite"):
            report._validate(result, result["run_id"])
        return
    directory = _fixture(tmp_path, result)
    if fault == "source_hash":
        (tmp_path / "numeric-input.json").write_text("changed")
    with pytest.raises(ValueError):
        report.execute(tmp_path, result["run_id"])
    assert not (tmp_path / report.REPORTS / result["run_id"]).exists()
    assert not (directory / "report_receipt.json").exists()


def test_report_publication_recovers_exact_orphan_and_rejects_changed_bundle(tmp_path, monkeypatch):
    result = _result(False)
    directory = _fixture(tmp_path, result)
    original = report.publish

    def fail_receipt(path, *args, **kwargs):
        if path.name == "report_receipt.json":
            raise OSError("simulated interruption after report rename")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(report, "publish", fail_receipt)
    with pytest.raises(OSError, match="after report rename"):
        report.execute(tmp_path, result["run_id"])
    output = tmp_path / report.REPORTS / result["run_id"]
    marker = output / "REPORT.md"
    original_bytes = marker.read_bytes()
    assert not (directory / "report_receipt.json").exists()
    monkeypatch.setattr(report, "publish", original)
    marker.write_bytes(original_bytes + b"changed")
    with pytest.raises(ValueError, match="differs from complete source reproduction"):
        report.execute(tmp_path, result["run_id"])
    marker.write_bytes(original_bytes)  # Temporary synthetic fixture only.
    receipt = report.execute(tmp_path, result["run_id"])
    assert receipt["recorded_git_commit"]
    assert marker.read_bytes() == original_bytes
