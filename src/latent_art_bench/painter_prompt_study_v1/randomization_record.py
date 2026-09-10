"""Immutable, source-bound qualification records for the small randomization study."""

from __future__ import annotations

import hashlib
import json
import math
import tempfile
from pathlib import Path

from latent_art_bench.io import hash_file, utc_now
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, identifier, publish

from .calibration import wilson
from .calibration_record import _verify_commit
from .common import MANIFESTS, PACKAGE, committed
from .randomization import DEPENDENCE, DRAW_COUNT, REPETITIONS, SCENARIOS

RECORDS = (("development.json", 20260908), ("validation.json", 20260909))
CODE_INPUTS = (
    [
        PACKAGE / name
        for name in (
            "randomization.py",
            "randomization_record.py",
            "calibration.py",
            "calibration_record.py",
            "statistics.py",
            "common.py",
        )
    ]
    + [
        Path("tests/painter_prompt_study_v1") / name
        for name in (
            "test_randomization.py",
            "test_randomization_record.py",
        )
    ]
    + [
        Path(name)
        for name in (
            "src/latent_art_bench/io.py",
            "src/latent_art_bench/painter_feature_generation_v2/artifacts.py",
            "pyproject.toml",
            "uv.lock",
        )
    ]
)


def _validate_document(document, seed):
    json.dumps(document, allow_nan=False)
    expected = dict(
        schema_version="painter-prompt-randomization-calibration/1.0",
        seed=seed,
        rng="PCG64",
        trials_per_cell=2000,
        repetitions=[1, 2, 4],
        endpoints=48,
        alpha=0.05,
        adjustment="Holm",
        monte_carlo_draws=DRAW_COUNT,
        exact_max_pairs=16,
        uses_empirical_outcomes_for_tuning=False,
    )
    if any(document.get(key) != value for key, value in expected.items()):
        raise ValueError("unexpected prospective randomization calibration design")
    expected_null = {(r, s, d) for r in REPETITIONS for s in SCENARIOS for d in DEPENDENCE}
    observed = [(r["repetitions"], r["scenario"], r["dependence"]) for r in document["null_cells"]]
    if len(observed) != len(expected_null) or set(observed) != expected_null:
        raise ValueError("incomplete randomization null inventory")
    power_keys = [
        (r["repetitions"], r["positive_sign_probability"]) for r in document["power_diagnostics"]
    ]
    if len(power_keys) != 9 or set(power_keys) != {
        (r, p) for r in REPETITIONS for p in (0.65, 0.8, 0.95)
    }:
        raise ValueError("incomplete synthetic power diagnostic inventory")
    invalid = document["invalid_persistent_sign_stress"]
    if len(invalid) != 3 or {r["repetitions"] for r in invalid} != set(REPETITIONS):
        raise ValueError("incomplete invalid-dependence stress inventory")
    for row in [*document["null_cells"], *document["power_diagnostics"], *invalid]:
        n, successes = row["trials"], row["family_rejections"]
        if (
            n != 2000
            or type(successes) is not int
            or not 0 <= successes <= n
            or row["endpoints"] != 48
            or row["matched_scenes"] != 16 * row["repetitions"]
            or row["family_rejection_rate"] != successes / n
            or not 0 <= row["mean_rejected_endpoints"] <= 48
            or row["exact_enumeration"] is not (row["repetitions"] == 1)
            or row["monte_carlo_draws"] != (0 if row["repetitions"] == 1 else DRAW_COUNT)
            or len(row["family_rejection_wilson_95"]) != 2
            or any(
                not math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-12)
                for x, y in zip(wilson(successes, n), row["family_rejection_wilson_95"])
            )
        ):
            raise ValueError("inconsistent synthetic randomization accounting")


def _decision_fields(documents):
    if len(documents) != 2:
        raise ValueError("development and unseen-seed validation records are required")
    for document, (_, seed) in zip(documents, RECORDS):
        _validate_document(document, seed)
    qualification = []
    for repetitions in REPETITIONS:
        rows = [
            row
            for document in documents
            for row in document["null_cells"]
            if row["repetitions"] == repetitions
        ]
        upper = max(row["family_rejection_wilson_95"][1] for row in rows)
        qualification.append(
            dict(
                repetitions=repetitions,
                qualified=upper <= 0.065,
                maximum_development_or_validation_wilson_upper=upper,
            )
        )
    return dict(
        primary_estimator="paired_randomization",
        simultaneous_alpha=0.05,
        primary_endpoints=48,
        adjustment="Holm",
        permutation_draws=DRAW_COUNT,
        exact_max_pairs=16,
        qualified_repetitions=[row["repetitions"] for row in qualification if row["qualified"]],
        qualification=qualification,
        criterion="All 8 valid-null cells at a repetition count, in BOTH 2000-trial development "
        "and unseen-seed validation, have Wilson95 upper <=0.065. Prespecified "
        "diagnostic criterion; theory still requires the actual randomization null.",
        uses_empirical_outcomes_for_tuning=False,
        inference_scope="Conditional sharp no-effect/no-interference or joint paired-swap "
        "invariance; not a weak null of equal energy distances; no CIs.",
        simulation_scope=documents[1]["simulation_scope"],
        shortcut=documents[1]["shortcut"],
        power_scope=documents[1]["power_scope"],
        invalid_scope=documents[1]["invalid_scope"],
        limitations="Finite contribution-space constructions cannot establish service "
        "stationarity, absence of carryover, or actual generated-image power.",
    )


def publish_randomization_calibration(
    root: Path, calibration_id: str, source_paths: list[Path]
) -> dict:
    root = root.resolve()
    relative = MANIFESTS / identifier(calibration_id)
    output = root / relative
    if output.exists():
        raise FileExistsError("randomization calibration is immutable; choose a new ID")
    if len(source_paths) != 2:
        raise ValueError("pass development then unseen validation JSON")
    commit = committed(root, CODE_INPUTS)
    code = bindings(root, CODE_INPUTS)
    documents, originals = [], []
    for source in source_paths:
        path = (root / source).resolve()
        data = path.read_bytes()
        originals.append(
            dict(path=path.relative_to(root).as_posix(), sha256=hashlib.sha256(data).hexdigest())
        )
        documents.append(json.loads(data))
    fields = _decision_fields(documents)
    _verify_commit(root, commit, code)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".randomization-calibration-", dir=output.parent
    ) as temp:
        staging = Path(temp)
        files = []
        for document, (name, _) in zip(documents, RECORDS):
            publish(staging / name, document)
            files.append(dict(path=(relative / name).as_posix(), sha256=hash_file(staging / name)))
        decision = dict(
            fields,
            schema_version="painter-prompt-randomization-decision/1.0",
            calibration_id=calibration_id,
            recorded_git_commit=commit,
            inputs=code,
            files=files,
            original_source_inputs=originals,
            prepared_at_utc=utc_now().isoformat(),
        )
        publish(staging / "decision.json", decision)
        output.mkdir()
        for path in staging.iterdir():
            path.rename(output / path.name)
    return decision


def validate_randomization_calibration(root: Path, calibration_id: str) -> dict:
    root = root.resolve()
    relative = MANIFESTS / identifier(calibration_id)
    decision = json.loads((root / relative / "decision.json").read_bytes())
    if (
        decision["schema_version"] != "painter-prompt-randomization-decision/1.0"
        or decision["calibration_id"] != calibration_id
    ):
        raise ValueError("randomization calibration decision identity mismatch")
    expected = {(relative / name).as_posix() for name, _ in RECORDS}
    records = {r["path"]: r["sha256"] for r in decision["files"]}
    if set(records) != expected or len(decision["files"]) != len(expected):
        raise ValueError("randomization result inventory mismatch")
    documents = []
    for name, _ in RECORDS:
        path = relative / name
        if hash_file(root / path) != records[path.as_posix()]:
            raise ValueError("published randomization result bytes changed")
        documents.append(json.loads((root / path).read_bytes()))
    if any(decision.get(key) != value for key, value in _decision_fields(documents).items()):
        raise ValueError("randomization qualification does not reproduce")
    if len(decision["inputs"]) != len(CODE_INPUTS) or {r["path"] for r in decision["inputs"]} != {
        p.as_posix() for p in CODE_INPUTS
    }:
        raise ValueError("randomization code input inventory changed")
    _verify_commit(root, decision["recorded_git_commit"], decision["inputs"])
    return decision
