"""Synthetic checks of exact-CDF correction and immutable, read-only publication."""

import copy
import json
import subprocess
from fractions import Fraction
from pathlib import Path

import pytest

from latent_art_bench import painter_responsiveness_quantiles_v1 as correction
from latent_art_bench.io import hash_file
from latent_art_bench.painter_feature_generation_v2.artifacts import publish
from latent_art_bench.painter_responsiveness_quantiles_v1 import (
    ORIGINAL,
    RUNS,
    correct,
    quantiles,
    weights,
)
from latent_art_bench.painter_responsiveness_v2 import analysis as original


@pytest.fixture
def result():
    generated, refs = [], []
    for pipeline in original.PIPELINES:
        for arm in original.ARMS:
            for i in range(48):
                generated.append(dict(request_id=f"{arm}-{i}", pipeline=pipeline, arm=arm,
                                      polarity="muted" if i < 24 else "vivid",
                                      content_class=original.CLASSES[i % 3], status="measured",
                                      value=i / 5))
        for painter in original.PAINTERS:
            for i in range(10):
                refs.append(dict(image_id=f"{painter}-{i}", painter_id=painter, pipeline=pipeline,
                                 content_class="built" if i < 2 else "land" if i < 5 else "water",
                                 value=float(i)))
    return dict(
        primary=dict(status="synthetic_unit_fixture", estimate=-0.2),
        arm_means=[1.2, 3.4], generated_chroma=generated, reference_chroma=refs,
        reference_context=original._reference_bridge(generated, refs),
    )


def test_exact_boundary_has_no_float_accumulation_or_tolerance():
    assert original._quantiles(list(range(48)), [1 / 48] * 48) == [4, 24, 43]
    assert quantiles(list(range(48)), [Fraction(1, 48)] * 48) == [4, 23, 43]
    assert original._quantiles(list(range(10)), [1 / 10] * 10) == [0, 4, 9]
    assert quantiles(list(range(10)), [Fraction(1, 10)] * 10) == [0, 4, 8]
    assert quantiles([7, 7, 7], [Fraction(1, 3)] * 3) == [7, 7, 7]


def test_exact_unequal_class_weights_and_missing_stratum():
    rows = [dict(content_class=c) for c in ("built", "land", "land", "water")]
    assert weights(rows, ("content_class",)) == [Fraction(1, 3), Fraction(1, 6),
                                               Fraction(1, 6), Fraction(1, 3)]
    assert weights(rows, ()) == [Fraction(1, 4)] * 4
    assert weights(rows[:-1], ("content_class",)) is None
    with pytest.raises(ValueError, match="undeclared"):
        weights(rows, ("unregistered",))


def test_corrects_quantiles_and_their_coverage_dependencies_without_other_changes(result):
    saved = copy.deepcopy(result)
    corrected, audit = correct(result)
    assert result == saved
    assert corrected["primary"] == result["primary"]
    assert corrected["arm_means"] == result["arm_means"]
    assert corrected["generated_chroma"] == result["generated_chroma"]
    assert all(a["wasserstein_1"] == b["wasserstein_1"] for a, b in zip(
        result["reference_context"]["comparisons"],
        corrected["reference_context"]["comparisons"], strict=True))
    assert all(a["generated_summary"]["weighted_mean"] == b["generated_summary"]["weighted_mean"]
               for a, b in zip(result["reference_context"]["comparisons"],
                               corrected["reference_context"]["comparisons"], strict=True))
    changed = next(r for r in audit["quantile_changes"] if r["kind"] == "generated_summary"
                   and r["polarity"] == "equal_polarity_mixture")
    assert changed["before"][1] == 4.8 and changed["corrected"][1] == 4.6
    coverage = next(r for r in audit["coverage_changes"]
                    if r["reference_weighting"] == "empirical_reference_mixture"
                    and r["polarity"] == "vivid"
                    and r["field"] == "generated_mass_in_reference_central80")
    assert coverage["before_exact_mass"] == "11/12"
    assert coverage["corrected_exact_mass"] == "17/24"
    assert coverage["corrected"] == 17 / 24
    assert len(coverage["removed_members"]) == 5 and coverage["added_members"] == []
    assert all(audit["unchanged"].values())
    json.dumps(audit, allow_nan=False)


def test_median_only_changes_leave_coverage_float_bytes_unchanged(result):
    result["reference_chroma"] = [r for r in result["reference_chroma"]
                                  if not r["image_id"].endswith("-9")]
    result["reference_context"] = original._reference_bridge(result["generated_chroma"],
                                                              result["reference_chroma"])
    corrected, audit = correct(result)
    for before, after in zip(result["reference_context"]["comparisons"],
                             corrected["reference_context"]["comparisons"], strict=True):
        for field in ("generated_mass_in_reference_central80",
                      "reference_mass_in_generated_central80"):
            if not any(row["field"] == field and all(row.get(k) == before.get(k)
                                                    for k in correction.KEYS)
                       for row in audit["coverage_changes"]):
                assert before[field] == after[field]


def test_unavailable_ancillary_strata_remain_unavailable(result):
    for row in result["generated_chroma"]:
        if row["arm"] == "monet" and row["content_class"] == "water":
            row.update(status="never_started", value=None)
    result["reference_context"] = original._reference_bridge(result["generated_chroma"],
                                                              result["reference_chroma"])
    corrected, _ = correct(result)
    assert all(r["status"] == "unavailable_stratum" and "generated_summary" not in r
               for r in corrected["reference_context"]["comparisons"] if r["arm"] == "monet")


def test_old_result_must_reproduce_before_correction(result):
    result["reference_context"]["comparisons"][0]["wasserstein_1"] += 0.01
    with pytest.raises(ValueError, match="does not reproduce"):
        correct(result)


@pytest.fixture
def publication(tmp_path, monkeypatch, result):
    paths = []
    for run in RUNS:
        directory = tmp_path / ORIGINAL / run
        publish(directory / "analysis.json", result)
        publish(directory / "analysis_receipt.json", dict(
            analysis_sha256=hash_file(directory / "analysis.json")))
        publish(directory / "collection_receipt.json", dict(terminal=True))
        publish(directory / "freeze.json", dict(scope="synthetic_fixture"))
        paths.extend(ORIGINAL / run / name for name in ("analysis.json", "analysis_receipt.json",
                                                       "collection_receipt.json", "freeze.json"))
    source = Path("fixture_source.txt")
    (tmp_path / source).write_text("frozen synthetic source")
    paths.append(source)
    monkeypatch.setattr(correction, "source_paths", lambda: sorted(paths))
    monkeypatch.setattr(correction, "committed", lambda root, paths: "a" * 40)
    monkeypatch.setattr(correction, "_commit_bindings", lambda root, freeze: None)
    return tmp_path


def test_create_once_numeric_and_plot_replay_and_input_immutability(publication):
    before = {p: hash_file(publication / p) for p in correction.source_paths()}
    assert correction.prepare(publication)["status"] == "prepared"
    assert correction.build(publication)["status"] == "published"
    assert correction.build(publication, check=True)["reports"] == 9
    assert {p: hash_file(publication / p) for p in correction.source_paths()} == before
    with pytest.raises(ValueError, match="already exists"):
        correction.prepare(publication)
    with pytest.raises(ValueError, match="terminal"):
        correction.build(publication)


def test_tampered_output_and_input_are_detected(publication):
    correction.prepare(publication)
    correction.build(publication)
    path = publication / correction.REPORTS / "REPORT.md"
    saved = path.read_bytes()
    path.write_bytes(saved + b"tampered")
    with pytest.raises(ValueError, match="bound input changed"):
        correction.build(publication, check=True)
    path.write_bytes(saved)
    (publication / "fixture_source.txt").write_text("changed source")
    with pytest.raises(ValueError, match="bound input changed"):
        correction.build(publication, check=True)


def test_terminal_receipt_mismatch_blocks_preparation(publication):
    path = publication / ORIGINAL / RUNS[0] / "analysis.json"
    path.write_text(path.read_text() + " ")
    with pytest.raises(ValueError, match="terminal publication receipt"):
        correction.prepare(publication)


def test_recorded_commit_must_contain_each_exact_bound_blob(tmp_path):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, check=True,
                              capture_output=True, text=True).stdout.strip()

    git("init")
    git("config", "user.name", "Offline Test")
    git("config", "user.email", "offline@example.invalid")
    path = tmp_path / "input.txt"
    path.write_text("exact source")
    git("add", "input.txt")
    git("commit", "-m", "Synthetic source binding")
    freeze = dict(recorded_git_commit=git("rev-parse", "HEAD"),
                  inputs=[dict(path="input.txt", sha256=hash_file(path))])
    correction._commit_bindings(tmp_path, freeze)
    freeze["inputs"][0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="recorded Git commit"):
        correction._commit_bindings(tmp_path, freeze)
