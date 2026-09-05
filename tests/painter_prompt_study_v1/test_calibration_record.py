"""Calibration receipts cannot qualify missing, relabeled, or inconsistent experiments."""

import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from latent_art_bench.painter_prompt_study_v1 import calibration_record as record
from latent_art_bench.painter_prompt_study_v1.calibration import SCENARIOS, normal_precision_plan


def _documents():
    documents = []
    for name, seed, trials, pairs, alpha, dependence in record.RECORDS:
        rows = []
        for scenario in SCENARIOS:
            for inventory in ("contrasts", "distances"):
                details = [
                    dict(
                        alias=a,
                        painter=p,
                        method=m,
                        family=f,
                        truth=0.0,
                        baseline=m - 1,
                        coverage=0.98,
                    )
                    for a, p, m, f in sorted(record._endpoint_ids(inventory))
                ]
                for method in ("paired_t", "jackknife_t"):
                    for pair_count in pairs:
                        rows.append(
                            dict(
                                scenario=scenario,
                                inventory=inventory,
                                method=method,
                                pairs=pair_count,
                                full_repetitions=2 * pair_count,
                                requests=960 * pair_count,
                                family_size=len(details),
                                trials=trials,
                                endpoint_truth_and_precision=copy.deepcopy(details),
                                joint_coverage_nondegenerate=0.98,
                                complete_inventory_coverage=0.98,
                                joint_coverage_mc_wilson_95=record.wilson(
                                    round(0.98 * trials), trials
                                ),
                                population_degenerate_endpoints=0,
                                trials_with_any_zero_sample_variance=0,
                            )
                        )
        document = dict(
            schema_version="painter-prompt-calibration/1.0",
            seed=seed,
            rng="PCG64",
            trials_per_cell=trials,
            pair_counts=list(pairs),
            source_states=16,
            templates=16,
            coordinates=31,
            aliases=2,
            methods=3,
            painters=4,
            requests_per_full_repetition=480,
            nominal_family_coverage=1 - alpha,
            scenarios=rows,
            normal_precision_plan=normal_precision_plan(pair_counts=pairs, alpha=alpha),
        )
        if dependence is not None:
            document["dependence"] = dependence
        documents.append(document)
    return documents


@pytest.fixture(scope="module")
def documents():
    return _documents()


def test_complete_independent_validation_qualifies_only_the_primary_inventory(documents):
    result = record.decision_fields(documents)
    assert result["qualified_repetitions"] == [20, 50, 100]
    assert result["simultaneous_alpha"] == 0.025
    assert result["primary_endpoints"] == 48
    assert result["uses_empirical_outcomes_for_tuning"] is False
    assert "absolute_distance_intervals" in result["unqualified_scopes"]
    assert len(result["power_and_precision"]) == 9


def test_one_failed_validation_cell_disqualifies_its_repetition_count(documents):
    changed = copy.deepcopy(documents)
    row = next(
        r
        for r in changed[3]["scenarios"]
        if r["scenario"] == "rare_outlier"
        and r["inventory"] == "contrasts"
        and r["method"] == "paired_t"
        and r["pairs"] == 25
    )
    row.update(
        joint_coverage_nondegenerate=0.93,
        complete_inventory_coverage=0.93,
        joint_coverage_mc_wilson_95=record.wilson(1860, 2000),
    )
    assert record.decision_fields(changed)["qualified_repetitions"] == [20, 100]


@pytest.mark.parametrize(
    "fault",
    [
        "seed",
        "dependence",
        "missing_cell",
        "duplicate_cell",
        "missing_endpoint",
        "nonadjacent",
        "trials",
        "wilson",
        "power",
        "endpoint_coverage",
    ],
)
def test_incomplete_or_relabeled_evaluation_cannot_be_blessed(documents, fault):
    changed = copy.deepcopy(documents)
    validation = changed[2]
    if fault == "seed":
        validation["seed"] = 20260906
    elif fault == "dependence":
        del validation["dependence"]
    elif fault == "missing_cell":
        validation["scenarios"].pop()
    elif fault == "duplicate_cell":
        validation["scenarios"].append(validation["scenarios"][0])
    elif fault == "missing_endpoint":
        validation["scenarios"][0]["endpoint_truth_and_precision"].pop()
    elif fault == "nonadjacent":
        row = next(r for r in validation["scenarios"] if r["inventory"] == "contrasts")
        row["endpoint_truth_and_precision"][0]["baseline"] = 99
    elif fault == "trials":
        validation["scenarios"][0]["trials"] = 1000
    elif fault == "wilson":
        validation["scenarios"][0]["joint_coverage_mc_wilson_95"][0] = 1.0
    elif fault == "endpoint_coverage":
        validation["scenarios"][0]["endpoint_truth_and_precision"][0]["coverage"] = 0.50
    else:
        validation["normal_precision_plan"][0]["normal_theory_marginal_power"] = 0.99
    with pytest.raises(ValueError):
        record.decision_fields(changed)


def test_clean_commit_is_required_before_any_publication(tmp_path, monkeypatch):
    def reject(*args):
        raise ValueError("commit exact prospective input first")

    monkeypatch.setattr(record, "committed", reject)
    with pytest.raises(ValueError, match="commit exact"):
        record.publish_calibration(tmp_path, "calibration", [Path("unused")] * 4)
    assert not (tmp_path / record.MANIFESTS).exists()


def test_publication_retains_all_results_and_refuses_overwrite(tmp_path, monkeypatch, documents):
    for path in record.CODE_INPUTS:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("committed fixture\n")
    sources = []
    for i, document in enumerate(documents):
        path = Path(f"source-{i}.json")
        (tmp_path / path).write_text(json.dumps(document))
        sources.append(path)
    monkeypatch.setattr(record, "committed", lambda *args: "a" * 40)
    monkeypatch.setattr(record, "_verify_commit", lambda *args: None)
    decision = record.publish_calibration(tmp_path, "calibration", sources)
    assert decision["qualified_repetitions"] == [20, 50, 100]
    assert len(decision["files"]) == 4
    assert record.validate_calibration(tmp_path, "calibration") == decision
    for specification, document in zip(record.RECORDS, documents):
        path = tmp_path / record.MANIFESTS / "calibration" / specification[0]
        assert json.loads(path.read_bytes()) == document
    with pytest.raises(FileExistsError):
        record.publish_calibration(tmp_path, "calibration", sources)
    path = tmp_path / record.MANIFESTS / "calibration" / "decision.json"
    changed = dict(decision, qualified_repetitions=[20, 50, 100, 200])
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="qualification does not reproduce"):
        record.validate_calibration(tmp_path, "calibration")


def test_commit_verification_uses_recorded_commit_not_working_tree(tmp_path, monkeypatch):
    data, calls = b"historical bytes", []

    def git(arguments, **kwargs):
        calls.append(arguments)
        return SimpleNamespace(returncode=0, stdout=data)

    monkeypatch.setattr(record.subprocess, "run", git)
    rows = [dict(path="source.py", sha256=hashlib.sha256(data).hexdigest())]
    record._verify_commit(tmp_path, "b" * 40, rows)
    assert calls == [["git", "show", "b" * 40 + ":source.py"]]
    with pytest.raises(ValueError, match="mismatch"):
        record._verify_commit(tmp_path, "b" * 40, [dict(path="source.py", sha256="wrong")])


def test_reproduction_allows_only_documented_extra_metadata_and_tiny_numeric_error():
    old = dict(scenarios=[dict(endpoint_truth_and_precision=[dict(truth=1.0)])])
    new = dict(
        dependence="shared_state",
        scenarios=[
            dict(
                u_first_order_degenerate_endpoints=0,
                endpoint_truth_and_precision=[
                    dict(truth=1.0 + 1e-13, exact_pair_mean_sd=2.0, exact_complete_u_sd=1.0)
                ],
            )
        ],
    )
    assert record._compare_reproduction(old, new) == 1
    new["surprise"] = "not permitted"
    with pytest.raises(ValueError, match="undocumented"):
        record._compare_reproduction(old, new)
    del new["surprise"]
    new["scenarios"][0]["endpoint_truth_and_precision"][0]["truth"] = 1.1
    with pytest.raises(ValueError, match="differs"):
        record._compare_reproduction(old, new)


def test_read_only_reproduction_replays_exact_four_fixed_jobs(tmp_path, monkeypatch, documents):
    directory = tmp_path / record.MANIFESTS / "candidate"
    directory.mkdir(parents=True)
    for (name, *_), document in zip(record.RECORDS, documents):
        (directory / name).write_text(json.dumps(document))
    monkeypatch.setattr(
        record, "validate_calibration", lambda *args: dict(recorded_git_commit="a" * 40)
    )
    monkeypatch.setattr(record, "bindings", lambda *args: [])
    jobs = []

    def replay(**kwargs):
        jobs.append(kwargs)
        return copy.deepcopy(documents[len(jobs) - 1])

    monkeypatch.setattr(record, "simulate", replay)
    before = {p: p.read_bytes() for p in directory.iterdir()}
    result = record.reproduce_calibration(tmp_path, "candidate")
    assert result["overall"] == "PASS"
    assert len(result["results"]) == 4
    assert [job["seed"] for job in jobs] == [20260906, 20260906, 20260907, 20260907]
    assert [job["trials"] for job in jobs] == [1000, 1000, 2000, 2000]
    assert [job["dependence"] for job in jobs] == ["shared_state"] * 3 + ["independent_conditions"]
    assert before == {p: p.read_bytes() for p in directory.iterdir()}
