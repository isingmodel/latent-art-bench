"""Create-once prospective calibration decisions from retained synthetic experiments."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import tempfile
from pathlib import Path

from latent_art_bench.io import hash_file, utc_now
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, identifier, publish

from .calibration import SCENARIOS, normal_precision_plan, simulate, wilson
from .common import MANIFESTS, PACKAGE, committed

RECORDS = (
    ("development_original.json", 20260906, 1000, (5, 10, 25, 50), 0.05, None),
    ("development_conservative.json", 20260906, 1000, (10, 25, 50), 0.025, None),
    ("validation_coupled.json", 20260907, 2000, (10, 25, 50), 0.025, "shared_state"),
    ("validation_independent.json", 20260907, 2000, (10, 25, 50), 0.025, "independent_conditions"),
)
CODE_INPUTS = [
    PACKAGE / name
    for name in ("statistics.py", "calibration.py", "calibration_record.py", "common.py")
] + [
    Path("tests/painter_prompt_study_v1/test_statistics.py"),
    Path("tests/painter_prompt_study_v1/test_calibration_record.py"),
    Path("src/latent_art_bench/io.py"),
    Path("src/latent_art_bench/painter_feature_generation_v2/artifacts.py"),
    Path("pyproject.toml"),
    Path("uv.lock"),
]
CRITERION = (
    "For each repetition count, all four scenarios in BOTH unseen-seed validation "
    "constructions must have a Wilson 95% Monte Carlo lower bound >= 0.95 for joint "
    "coverage of all 48 adjacent prompt contrasts, with no missing or zero-variance endpoint. "
    "Intervals use prespecified paired_t and alpha=0.025. This is finite synthetic "
    "qualification, not a universal confidence guarantee."
)


def _close(first, second):
    return math.isclose(first, second, rel_tol=1e-10, abs_tol=1e-12)


def _endpoint_ids(inventory):
    return {
        (alias, painter, method, family)
        for alias in range(2)
        for painter in range(4)
        for method in ((1, 2) if inventory == "contrasts" else (0, 1, 2))
        for family in ("color", "spatial", "texture")
    }


def validate_document(document: dict, specification: tuple) -> dict:
    """Reject incomplete inventories; do not infer missing metadata for validation runs."""
    name, seed, trials, pair_counts, alpha, dependence = specification
    json.dumps(document, allow_nan=False)
    expected = dict(
        schema_version="painter-prompt-calibration/1.0",
        seed=seed,
        rng="PCG64",
        trials_per_cell=trials,
        pair_counts=list(pair_counts),
        source_states=16,
        templates=16,
        coordinates=31,
        aliases=2,
        methods=3,
        painters=4,
        requests_per_full_repetition=480,
        nominal_family_coverage=1 - alpha,
    )
    if any(document.get(key) != value for key, value in expected.items()):
        raise ValueError(f"unexpected synthetic design: {name}")
    # The two development outputs predate the explicit dependence metadata field.
    if document.get("dependence") != dependence:
        raise ValueError(f"unexpected synthetic dependence: {name}")
    expected_cells = {
        (scenario, inventory, method, pairs)
        for scenario in SCENARIOS
        for inventory in ("contrasts", "distances")
        for method in ("paired_t", "jackknife_t")
        for pairs in pair_counts
    }
    cells = {}
    for row in document["scenarios"]:
        key = row["scenario"], row["inventory"], row["method"], row["pairs"]
        if key in cells or key not in expected_cells:
            raise ValueError(f"duplicate or unexpected calibration cell: {name}")
        cells[key] = row
        endpoints = _endpoint_ids(row["inventory"])
        if (
            row["family_size"] != len(endpoints)
            or row["trials"] != trials
            or row["full_repetitions"] != 2 * row["pairs"]
            or row["requests"] != 960 * row["pairs"]
        ):
            raise ValueError(f"inconsistent calibration accounting: {name}")
        details = row["endpoint_truth_and_precision"]
        labels = {(r["alias"], r["painter"], r["method"], r["family"]) for r in details}
        if len(details) != len(endpoints) or labels != endpoints:
            raise ValueError(f"incomplete calibration endpoint inventory: {name}")
        if row["inventory"] == "contrasts" and any(
            r["baseline"] != r["method"] - 1 for r in details
        ):
            raise ValueError(f"calibration does not test adjacent prompt transitions: {name}")
        coverage = row["joint_coverage_nondegenerate"]
        successes = round(coverage * trials)
        if (
            not 0 <= coverage <= 1
            or not _close(successes / trials, coverage)
            or len(row["joint_coverage_mc_wilson_95"]) != 2
            or any(
                not _close(x, y)
                for x, y in zip(wilson(successes, trials), row["joint_coverage_mc_wilson_95"])
            )
        ):
            raise ValueError(f"invalid coverage/Monte Carlo interval: {name}")
        if (
            not 0 <= row["complete_inventory_coverage"] <= coverage
            or not 0 <= row["population_degenerate_endpoints"] <= len(endpoints)
            or not 0 <= row["trials_with_any_zero_sample_variance"] <= trials
        ):
            raise ValueError(f"invalid calibration degeneracy accounting: {name}")
        for detail in details:
            endpoint_coverage = detail["coverage"]
            if (
                not 0 <= endpoint_coverage <= 1
                or not _close(round(endpoint_coverage * trials) / trials, endpoint_coverage)
                or (
                    row["population_degenerate_endpoints"] == 0
                    and endpoint_coverage + 1e-12 < coverage
                )
            ):
                raise ValueError(f"endpoint/joint coverage accounting is inconsistent: {name}")
    if set(cells) != expected_cells:
        raise ValueError(f"incomplete calibration cell inventory: {name}")
    planned = normal_precision_plan(pair_counts=pair_counts, alpha=alpha)
    if document["normal_precision_plan"] != planned:
        raise ValueError(f"normal-theory planning table changed: {name}")
    return cells


def decision_fields(documents: list[dict]) -> dict:
    if len(documents) != len(RECORDS):
        raise ValueError("all four development and unseen-seed validation runs are required")
    cells = [validate_document(document, spec) for document, spec in zip(documents, RECORDS)]
    qualifications = []
    for pairs in (10, 25, 50):
        required = [
            cells[index][scenario, "contrasts", "paired_t", pairs]
            for index in (2, 3)
            for scenario in SCENARIOS
        ]
        passed = all(
            row["joint_coverage_mc_wilson_95"][0] >= 0.95
            and row["population_degenerate_endpoints"] == 0
            and row["trials_with_any_zero_sample_variance"] == 0
            and row["complete_inventory_coverage"] == row["joint_coverage_nondegenerate"]
            for row in required
        )
        qualifications.append(
            dict(
                repetitions=2 * pairs,
                pairs=pairs,
                qualified=passed,
                minimum_validation_joint_coverage=min(
                    r["complete_inventory_coverage"] for r in required
                ),
                minimum_validation_wilson_lower=min(
                    r["joint_coverage_mc_wilson_95"][0] for r in required
                ),
            )
        )
    return dict(
        primary_estimator="paired_t",
        simultaneous_alpha=0.025,
        primary_endpoints=48,
        primary_inventory="adjacent_prompt_transitions_1_minus_0_and_2_minus_1",
        qualified_repetitions=[r["repetitions"] for r in qualifications if r["qualified"]],
        qualification=qualifications,
        criterion=CRITERION,
        uses_empirical_outcomes_for_tuning=False,
        unqualified_scopes=[
            "absolute_distance_intervals",
            "jackknife_t_intervals",
            "matched_control_difference_in_differences_intervals",
        ],
        power_scope="normal IID pair contributions; marginal endpoint power, not joint power",
        power_and_precision=[
            r for r in documents[2]["normal_precision_plan"] if r["family_size"] == 48
        ],
    )


def _verify_commit(root: Path, commit: str, records: list[dict]) -> None:
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("invalid recorded calibration commit")
    for row in records:
        path = Path(row["path"])
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("nonportable calibration input")
        result = subprocess.run(
            ["git", "show", f"{commit}:{path.as_posix()}"], cwd=root, capture_output=True
        )
        if result.returncode or hashlib.sha256(result.stdout).hexdigest() != row["sha256"]:
            raise ValueError(f"commit-bound calibration code mismatch: {path}")


def publish_calibration(root: Path, calibration_id: str, source_paths: list[Path]) -> dict:
    root = root.resolve()
    directory = MANIFESTS / identifier(calibration_id)
    output = root / directory
    if output.exists():
        raise FileExistsError("calibration is immutable; choose a new calibration ID")
    if len(source_paths) != 4:
        raise ValueError("pass four files in development/development/validation/validation order")
    commit = committed(root, CODE_INPUTS)
    code = bindings(root, CODE_INPUTS)
    documents, originals = [], []
    for path in source_paths:
        path = (root / path).resolve()
        relative = path.relative_to(root)
        data = path.read_bytes()
        documents.append(json.loads(data))
        originals.append(dict(path=relative.as_posix(), sha256=hashlib.sha256(data).hexdigest()))
    fields = decision_fields(documents)
    _verify_commit(root, commit, code)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".calibration-", dir=output.parent) as temporary:
        staging = Path(temporary)
        files = []
        for document, specification in zip(documents, RECORDS):
            name = specification[0]
            publish(staging / name, document)
            files.append(dict(path=(directory / name).as_posix(), sha256=hash_file(staging / name)))
        decision = dict(
            fields,
            schema_version="painter-prompt-calibration-decision/1.0",
            calibration_id=calibration_id,
            recorded_git_commit=commit,
            inputs=code,
            files=files,
            original_source_inputs=originals,
            original_source_note="Original temporary byte hashes are provenance only; parsed JSON "
            "values are retained in the four bound published files.",
            prepared_at_utc=utc_now().isoformat(),
            reviewer_kind="maintainer_run_llm_subagent_not_institutionally_independent",
        )
        publish(staging / "decision.json", decision)
        output.mkdir()
        for path in staging.iterdir():
            path.rename(output / path.name)
    return decision


def validate_calibration(root: Path, calibration_id: str) -> dict:
    root = root.resolve()
    directory = MANIFESTS / identifier(calibration_id)
    decision = json.loads((root / directory / "decision.json").read_bytes())
    if (
        decision["schema_version"] != "painter-prompt-calibration-decision/1.0"
        or decision["calibration_id"] != calibration_id
    ):
        raise ValueError("calibration decision identity mismatch")
    expected = {(directory / specification[0]).as_posix() for specification in RECORDS}
    recorded = {r["path"]: r["sha256"] for r in decision["files"]}
    if set(recorded) != expected or len(decision["files"]) != len(expected):
        raise ValueError("calibration result file inventory mismatch")
    documents = []
    for specification in RECORDS:
        path = directory / specification[0]
        data = (root / path).read_bytes()
        if hashlib.sha256(data).hexdigest() != recorded[path.as_posix()]:
            raise ValueError("published synthetic result bytes changed")
        documents.append(json.loads(data))
    fields = decision_fields(documents)
    if any(decision.get(key) != value for key, value in fields.items()):
        raise ValueError("calibration qualification does not reproduce")
    if len(decision["inputs"]) != len(CODE_INPUTS) or {r["path"] for r in decision["inputs"]} != {
        p.as_posix() for p in CODE_INPUTS
    }:
        raise ValueError("calibration code input inventory mismatch")
    _verify_commit(root, decision["recorded_git_commit"], decision["inputs"])
    return decision


def _compare_reproduction(recorded, recomputed, path=()):
    """Compare every retained value; permit only documented newer metadata fields."""
    compared = 0
    if isinstance(recorded, dict):
        if not isinstance(recomputed, dict) or not set(recorded) <= set(recomputed):
            raise ValueError(f"missing reproduced calibration value at {path}")
        extras = set(recomputed) - set(recorded)
        allowed = set()
        if not path:
            allowed = {"dependence"}
            if "dependence" in extras and recomputed["dependence"] != "shared_state":
                raise ValueError("legacy development requires shared_state dependence")
        elif len(path) == 2 and path[0] == "scenarios":
            allowed = {"u_first_order_degenerate_endpoints"}
        elif (
            len(path) == 4 and path[0] == "scenarios" and path[2] == "endpoint_truth_and_precision"
        ):
            allowed = {"exact_pair_mean_sd", "exact_complete_u_sd"}
        if not extras <= allowed:
            raise ValueError(f"undocumented reproduced metadata at {path}: {extras - allowed}")
        return sum(
            _compare_reproduction(value, recomputed[key], (*path, key))
            for key, value in recorded.items()
        )
    if isinstance(recorded, list):
        if not isinstance(recomputed, list) or len(recorded) != len(recomputed):
            raise ValueError(f"changed reproduced calibration inventory at {path}")
        return sum(
            _compare_reproduction(a, b, (*path, i))
            for i, (a, b) in enumerate(zip(recorded, recomputed))
        )
    if type(recorded) in (int, float) and type(recomputed) in (int, float):
        equal = math.isclose(recorded, recomputed, rel_tol=1e-12, abs_tol=1e-12)
    else:
        equal = type(recorded) is type(recomputed) and recorded == recomputed
    if not equal:
        raise ValueError(f"reproduced calibration differs at {path}")
    compared += 1
    return compared


def reproduce_calibration(root: Path, calibration_id: str) -> dict:
    """Read-only replay of all four fixed candidate jobs, with no retuning or publication.

    Exploratory executions preceded their eventual source commit. This replay verifies
    retained values with the current implementation; it cannot create a contemporaneous
    source-commit history for those earlier executions.
    """
    root = root.resolve()
    decision = validate_calibration(root, calibration_id)
    results = []
    for name, seed, trials, pairs, alpha, dependence in RECORDS:
        recorded = json.loads((root / MANIFESTS / calibration_id / name).read_bytes())
        recomputed = simulate(
            trials=trials,
            pair_counts=pairs,
            seed=seed,
            states=16,
            alpha=alpha,
            dependence=dependence or "shared_state",
        )
        recomputed = json.loads(json.dumps(recomputed, allow_nan=False))
        count = _compare_reproduction(recorded, recomputed)
        results.append(dict(file=name, reproduced_values=count))
    return dict(
        overall="PASS",
        calibration_id=calibration_id,
        results=results,
        recorded_git_commit=decision["recorded_git_commit"],
        current_source_inputs=bindings(root, CODE_INPUTS),
        numeric_relative_and_absolute_tolerance=1e-12,
        permitted_new_metadata=[
            "dependence=shared_state",
            "u_first_order_degenerate_endpoints",
            "exact_pair_mean_sd",
            "exact_complete_u_sd",
        ],
        scope="All retained values replayed; no empirical outcomes and no evidence changes",
    )
