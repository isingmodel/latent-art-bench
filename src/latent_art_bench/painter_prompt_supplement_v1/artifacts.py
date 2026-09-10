"""Commit-bound publication and numerical replay for the separate supplement."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

from latent_art_bench.io import canonical_json, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_distance_v1.analysis import load_source
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import empirical, features
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    bindings,
    digest,
    identifier,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1 import generation, reproduction
from latent_art_bench.painter_prompt_study_v1.calibration import wilson
from latent_art_bench.painter_prompt_study_v1.common import MANIFESTS as SOURCE_MANIFESTS
from latent_art_bench.painter_prompt_study_v1.common import committed
from latent_art_bench.painter_prompt_study_v1.prompts import METHOD_IDS

from . import validation

NAMESPACE = "painter_prompt_supplement_v1"
PACKAGE = Path("src/latent_art_bench") / NAMESPACE
MANIFESTS = Path("data/manifests") / NAMESPACE
REPORTS = Path("reports") / NAMESPACE
CONFIG = Path("configs") / NAMESPACE / "study.json"
PROTOCOL = Path("studies") / NAMESPACE / "PROTOCOL.md"


def _config(root):
    config = read_json(root / CONFIG)
    expected = dict(
        schema_version="painter-prompt-supplement/1.0",
        source_run_id="pps1-gpt-prompts-20260905",
        qualification_id="ppss1-qualification-20260905",
        repetitions=4,
        minimum_pairs_per_template=1,
        template_weighting="equal_template_then_equal_available_repetition",
        coordinate_quantiles="weighted_empirical_inverse_cdf_for_both_populations",
        family_size=48,
        alpha=0.05,
        permutation_seed=8755477342009039575,
        permutation_draws=99999,
        development_seed=20260910,
        validation_seed=20260911,
        trials_per_cell=2000,
        maximum_null_wilson_upper=0.065,
        new_provider_requests=0,
        new_feature_extraction=False,
        registration_status="specified_after_first_refusal_before_registered_feature_measurement",
    )
    if canonical_json(config) != canonical_json(expected):
        raise ValueError("supplement configuration differs from its fixed contract")
    return config


def _before_measurement(root, source_run_id):
    source = root / SOURCE_MANIFESTS / source_run_id
    if any(
        (source / name).exists()
        for name in (
            "measurement_events.jsonl",
            "measurement_receipt.json",
            "measured_features.jsonl",
        )
    ):
        raise ValueError("supplement qualification and freeze must precede source measurement")


def _source_paths(root, config):
    directory, freeze, _ = generation._load(root, config["source_run_id"])
    if freeze["config"]["maximum_requests"] != 1920:
        raise ValueError("supplement requires the approved 1920-request source design")
    paths = {Path(row["path"]) for row in freeze["inputs"]}
    paths.update({PROTOCOL, CONFIG})
    paths.update(path.relative_to(root) for path in (root / PACKAGE).glob("*.py"))
    paths.update(path.relative_to(root) for path in (root / "tests" / NAMESPACE).glob("*.py"))
    paths.update(
        (directory / name).relative_to(root)
        for name in ("generation_freeze.json", "prompts.json", "requests.jsonl")
    )
    return sorted(paths)


def _verify_commit(root, record, *, expected_paths=None, current=True):
    sources = record["inputs"]
    paths = [row["path"] for row in sources]
    if not paths or len(set(paths)) != len(paths):
        raise ValueError("source binding inventory is empty or duplicated")
    if expected_paths is not None and set(paths) != {Path(p).as_posix() for p in expected_paths}:
        raise ValueError("source binding inventory differs from mandatory inputs")
    for path in paths:
        relative = Path(path)
        if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != path:
            raise ValueError("nonportable source binding")
    if current:
        verify_bindings(root, sources)
    commit = record["recorded_git_commit"]
    if (
        not isinstance(commit, str)
        or len(commit) != 40
        or any(c not in "0123456789abcdef" for c in commit)
    ):
        raise ValueError("invalid recorded source commit")
    for source in sources:
        relative = Path(source["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("nonportable source binding")
        blob = subprocess.run(
            ["git", "show", f"{commit}:{relative.as_posix()}"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if blob.returncode or hashlib.sha256(blob.stdout).hexdigest() != source["sha256"]:
            raise ValueError(f"source does not verify at its recorded commit: {relative}")


def _verify_loaded(root, records):
    """Bind executing Python bytes, including an alternate --root checkout."""
    expected = {row["path"]: row["sha256"] for row in records}
    for path in expected:
        relative = Path(path)
        if relative.parts[:2] == ("src", "latent_art_bench") and relative.suffix == ".py":
            name = ".".join(relative.with_suffix("").parts[1:])
            if name.endswith(".__init__"):
                name = name.removesuffix(".__init__")
            if relative.parts[2] == NAMESPACE or name in sys.modules:
                module = importlib.import_module(name)
                loaded = getattr(module, "__file__", None)
                if (
                    loaded is None
                    or hashlib.sha256(Path(loaded).read_bytes()).hexdigest() != expected[path]
                ):
                    raise ValueError(f"executing module differs from bound source: {path}")


def _publication_commit(root, relative):
    """Find the first reachable commit retaining these exact published bytes."""
    relative = Path(relative)
    body = (root / relative).read_bytes()
    history = subprocess.run(
        ["git", "log", "--reverse", "--format=%H %ct", "--", relative.as_posix()],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    for line in history.stdout.splitlines():
        commit, seconds = line.split()
        blob = subprocess.run(
            ["git", "show", f"{commit}:{relative.as_posix()}"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if blob.returncode == 0 and blob.stdout == body:
            return commit, int(seconds)
    raise ValueError(f"publication is not committed with its present bytes: {relative}")


def _verify_publication(root, analysis_id, frozen):
    _, seconds = _publication_commit(root, MANIFESTS / analysis_id / "design_freeze.json")
    ledger = root / SOURCE_MANIFESTS / frozen["source_run_id"] / "measurement_events.jsonl"
    if ledger.exists():
        rows = generation._Journal(ledger).rows
        if not rows or rows[0]["kind"] != "stage_start":
            raise ValueError("source measurement start is missing or invalid")
        started = datetime.fromisoformat(rows[0]["at_utc"])
        if started.tzinfo is None or seconds + 1 > started.timestamp():
            raise ValueError("committed supplement publication must precede source measurement")


def _publish_immutable(path, value):
    """Publish a complete fsynced file atomically without replacing any bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".publish-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write((canonical_json(value) + "\n").encode())
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _qualification_content(config, oracles, development, checked):
    if oracles.get("overall") != "PASS" or oracles.get("empirical_outcomes_used") is not False:
        raise ValueError("independent supplement oracles did not pass")
    checks = oracles["checks"]
    if (
        len(checks) != len(validation.ORACLE_IDS)
        or {row["id"] for row in checks} != set(validation.ORACLE_IDS)
        or any(row["passed"] is not True for row in checks)
    ):
        raise ValueError("oracle inventory incomplete or failed")
    by_id = {row["id"]: row for row in checks}
    triplet = by_id["conditional_triplet_allocations"]
    if (
        oracles.get("seed") != config["development_seed"]
        or by_id["weighted_energy_swaps"]["assignments"] != 128
        or any(
            not 0 <= by_id[name]["maximum_absolute_error"] <= 1e-12
            for name in ("weighted_energy_swaps", "uniform_weight_reduction")
        )
        or by_id["ties_and_zero"]["pvalues"] != [1.0, 1.0]
        or triplet["full_triplet_allocations"] != 2592
        or triplet["conditioning_strata"] != 162
        or triplet["distinct_weight_support_patterns"] != 4
        or not 0 <= triplet["maximum_error"] <= 1e-12
        or not np.isfinite(triplet["maximum_conditional_cdf_minus_alpha"])
        or triplet["maximum_conditional_cdf_minus_alpha"] > 1e-12
        or triplet["unavailable_template_is_ineligible"] is not True
    ):
        raise ValueError("independent oracle numeric checks failed")
    required = {
        (case, dependence)
        for case in validation.CASE_IDS
        for dependence in validation.DEPENDENCE_IDS
    }
    for stored, seed in (
        (development, config["development_seed"]),
        (checked, config["validation_seed"]),
    ):
        if (
            stored["seed"] != seed
            or stored["trials_per_cell"] != config["trials_per_cell"]
            or stored["family_size"] != 48
            or stored["alpha"] != 0.05
            or stored["adjustment"] != "Holm"
            or stored["permutation_draws"] != 99999
            or stored["uses_empirical_outcomes_for_tuning"] is not False
            or len(stored["null_cells"]) != len(required)
            or {(c["case"], c["dependence"]) for c in stored["null_cells"]} != required
        ):
            raise ValueError("synthetic qualification inventory or fixed settings changed")
        for cell in stored["null_cells"]:
            count = cell["family_rejections"]
            if (
                type(count) is not int
                or not 0 <= count <= config["trials_per_cell"]
                or cell["trials"] != config["trials_per_cell"]
                or cell["family_size"] != 48
                or not np.allclose(
                    cell["family_rejection_wilson_95"],
                    wilson(count, config["trials_per_cell"]),
                    rtol=0,
                    atol=1e-14,
                )
                or cell["family_rejection_rate"] != count / config["trials_per_cell"]
            ):
                raise ValueError("synthetic qualification arithmetic differs")
    return all(
        c["family_rejection_wilson_95"][1] <= config["maximum_null_wilson_upper"]
        for batch in (development, checked)
        for c in batch["null_cells"]
    )


def qualify(root: Path, qualification_id: str):
    config = _config(root)
    if identifier(qualification_id) != config["qualification_id"]:
        raise ValueError("qualification identifier differs from config")
    _before_measurement(root, config["source_run_id"])
    target = root / MANIFESTS / qualification_id
    if target.exists():
        raise FileExistsError("qualification records are immutable")
    paths = _source_paths(root, config)
    commit = committed(root, paths)
    inputs = bindings(root, paths)
    _verify_loaded(root, inputs)
    oracles = validation.validate_oracles()
    development = validation.simulate(config["development_seed"], config["trials_per_cell"])
    checked = validation.simulate(config["validation_seed"], config["trials_per_cell"])
    qualified = _qualification_content(config, oracles, development, checked)
    _before_measurement(root, config["source_run_id"])
    results = dict(oracles=oracles, development=development, validation=checked)
    files = [
        dict(
            path=(MANIFESTS / qualification_id / f"{name}.json").as_posix(),
            sha256=hashlib.sha256((canonical_json(value) + "\n").encode()).hexdigest(),
        )
        for name, value in sorted(results.items())
    ]
    decision = dict(
        schema_version="painter-prompt-supplement-qualification/1.0",
        qualification_id=qualification_id,
        qualified=qualified,
        recorded_git_commit=commit,
        inputs=inputs,
        files=files,
        criterion=validation.CRITERION,
        reviewer_kind="maintainer_run_llm_subagent_not_institutionally_independent",
        created_at_utc=utc_now().isoformat(),
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    with stage_lock(root / "tmp" / NAMESPACE / f"{qualification_id}.writer.lock"):
        if target.exists():
            raise FileExistsError("qualification records are immutable")
        with tempfile.TemporaryDirectory(prefix=".qualification-", dir=target.parent) as temporary:
            stage = Path(temporary) / "record"
            for name, value in results.items():
                _publish_immutable(stage / f"{name}.json", value)
            _publish_immutable(stage / "decision.json", decision)
            _before_measurement(root, config["source_run_id"])
            _verify_commit(root, decision, expected_paths=paths)
            stage.rename(target)
    return decision


def check_qualification(root, qualification_id, *, replay=False):
    config = _config(root)
    if identifier(qualification_id) != config["qualification_id"]:
        raise ValueError("unknown qualification record")
    directory = root / MANIFESTS / qualification_id
    if (
        directory.is_symlink()
        or {p.name for p in directory.iterdir()}
        != {"decision.json", "oracles.json", "development.json", "validation.json"}
        or any(p.is_symlink() for p in directory.iterdir())
    ):
        raise ValueError("qualification directory inventory differs")
    record = read_json(directory / "decision.json")
    _verify_commit(root, record, expected_paths=_source_paths(root, config))
    _verify_loaded(root, record["inputs"])
    if (
        record["qualification_id"] != qualification_id
        or record["criterion"] != validation.CRITERION
    ):
        raise ValueError("qualification identity or criterion changed")
    expected = bindings(
        root,
        [
            (MANIFESTS / qualification_id / f"{name}.json")
            for name in ("oracles", "development", "validation")
        ],
    )
    if record["files"] != expected:
        raise ValueError("qualification files or inventory changed")
    oracles, development, checked = [
        read_json(directory / f"{name}.json") for name in ("oracles", "development", "validation")
    ]
    passed = _qualification_content(config, oracles, development, checked)
    if record["qualified"] is not passed or not passed:
        raise ValueError("supplement qualification is unavailable or failed")
    if replay:
        rebuilt = [
            validation.validate_oracles(),
            validation.simulate(config["development_seed"], config["trials_per_cell"]),
            validation.simulate(config["validation_seed"], config["trials_per_cell"]),
        ]
        if any(
            canonical_json(a) != canonical_json(b)
            for a, b in zip((oracles, development, checked), rebuilt)
        ):
            raise ValueError("qualification does not numerically reproduce")
    return record


def prepare(root, analysis_id):
    identifier(analysis_id)
    config = _config(root)
    _before_measurement(root, config["source_run_id"])
    target = root / MANIFESTS / analysis_id
    if target.exists():
        raise FileExistsError("supplement analysis IDs are never replaced")
    qualification = check_qualification(root, config["qualification_id"])
    qroot = MANIFESTS / config["qualification_id"]
    paths = _source_paths(root, config) + [qroot / "decision.json"]
    paths += [Path(row["path"]) for row in qualification["files"]]
    commit = committed(root, paths)
    ledger = SOURCE_MANIFESTS / config["source_run_id"] / "generation_events.jsonl"
    body = (root / ledger).read_bytes()
    body = body[: body.rfind(b"\n") + 1]
    if not body:
        raise ValueError("known source request outcomes are required")
    terminals = [
        row for line in body.splitlines() if (row := json.loads(line))["kind"] == "terminal"
    ]
    if not any(row["status"] == "refused" for row in terminals):
        raise ValueError("supplement trigger is the recorded refusal, not favorable feature values")
    freeze = dict(
        schema_version="painter-prompt-supplement-freeze/1.0",
        analysis_id=analysis_id,
        source_run_id=config["source_run_id"],
        config=config,
        recorded_git_commit=commit,
        inputs=bindings(root, paths),
        generation_prefix=dict(
            path=ledger.as_posix(),
            bytes=len(body),
            sha256=hashlib.sha256(body).hexdigest(),
            terminal_statuses=dict(Counter(r["status"] for r in terminals)),
        ),
        registered_measurement_absent=True,
        registration_status=config["registration_status"],
        created_at_utc=utc_now().isoformat(),
    )
    _before_measurement(root, config["source_run_id"])
    _verify_prefix(body, freeze["generation_prefix"]["terminal_statuses"])
    _publish_immutable(target / "design_freeze.json", freeze)
    return freeze


def _freeze(root, analysis_id):
    directory = root / MANIFESTS / identifier(analysis_id)
    frozen = read_json(directory / "design_freeze.json")
    config = _config(root)
    qroot = MANIFESTS / config["qualification_id"]
    paths = _source_paths(root, config) + [
        qroot / f"{name}.json" for name in ("decision", "oracles", "development", "validation")
    ]
    _verify_commit(root, frozen, expected_paths=paths)
    _verify_loaded(root, frozen["inputs"])
    if (
        frozen["analysis_id"] != analysis_id
        or frozen["config"] != _config(root)
        or frozen["source_run_id"] != frozen["config"]["source_run_id"]
        or frozen["registered_measurement_absent"] is not True
    ):
        raise ValueError("supplement freeze identity or fixed contract differs")
    prefix = frozen["generation_prefix"]
    if (
        prefix["path"]
        != (SOURCE_MANIFESTS / frozen["source_run_id"] / "generation_events.jsonl").as_posix()
    ):
        raise ValueError("source generation prefix is misdirected")
    with (root / prefix["path"]).open("rb") as handle:
        body = handle.read(prefix["bytes"])
    if len(body) != prefix["bytes"] or hashlib.sha256(body).hexdigest() != prefix["sha256"]:
        raise ValueError("source generation prefix changed")
    _verify_prefix(body, prefix["terminal_statuses"])
    check_qualification(root, frozen["config"]["qualification_id"])
    _verify_publication(root, analysis_id, frozen)
    return directory, frozen


def _verify_prefix(body, statuses):
    if not body or not body.endswith(b"\n"):
        raise ValueError("source generation prefix is incomplete")
    previous, counts = None, Counter()
    for index, line in enumerate(body.splitlines()):
        row = json.loads(line)
        bound = row.pop("event_sha256")
        if row["sequence"] != index or row["previous_sha256"] != previous or digest(row) != bound:
            raise ValueError("source generation prefix event chain changed")
        if row["kind"] == "terminal":
            counts[row["status"]] += 1
        previous = bound
    if dict(counts) != statuses or counts["refused"] < 1:
        raise ValueError("source generation prefix refusal trigger or counts changed")


def result(root, analysis_id):
    from .statistics import compute

    directory, frozen = _freeze(root, analysis_id)
    config = frozen["config"]
    source_id = frozen["source_run_id"]
    reproduction.reproduce(root, source_id)
    source = root / SOURCE_MANIFESTS / source_id
    original = read_json(source / "analysis.json")
    if original["status"] != "unavailable_incomplete_grid":
        raise ValueError("this supplement requires the original unavailable-primary source result")
    rows = read_jsonl(source / "measured_features.jsonl")
    real, _, _, scaler, _, reference = load_source(root, original["source_method_id"])
    source_freeze = read_json(source / "generation_freeze.json")
    if reference["inputs"] != source_freeze["reference_inputs"]:
        raise ValueError("supplement fixed painting reference differs from the original freeze")
    computed = compute(
        real,
        rows,
        scaler,
        config["repetitions"],
        permutation_seed=config["permutation_seed"],
        permutation_draws=config["permutation_draws"],
    )
    reference_path = next(
        Path(row["path"])
        for row in reference["inputs"]
        if Path(row["path"]).name == "confirmation_features.jsonl"
    )
    reference_rows = [
        row for row in read_jsonl(root / reference_path) if row["status"] == "measured"
    ]
    copy = empirical.copy_diagnostics(
        reference_rows, [row for row in rows if row["status"] == "measured"]
    )
    copy["scope"] = "649 exposed confirmation references and successful measurements only"
    paths = [
        Path(row["path"]) for row in frozen["inputs"] + original["inputs"] + reference["inputs"]
    ]
    paths += [MANIFESTS / analysis_id / "design_freeze.json"]
    paths += [
        SOURCE_MANIFESTS / source_id / name
        for name in ("analysis.json", "report_receipt.json", "generation_events.jsonl")
    ]
    return dict(
        **computed,
        schema_version="painter-prompt-supplement-analysis/1.0",
        analysis_id=analysis_id,
        source_run_id=source_id,
        registered_primary_status=original["status"],
        registration_status=frozen["registration_status"],
        source_method_id=original["source_method_id"],
        repetitions=config["repetitions"],
        aliases=list(generation.ALIASES),
        methods=list(METHOD_IDS),
        painters=list(PAINTER_IDS),
        families={key: list(value) for key, value in features.FAMILY_NAMES.items()},
        reference_counts={painter: len(values) for painter, values in real.items()},
        scaler_development_counts=reference["scaler_development_counts"],
        availability=original["availability"],
        template_availability=original["template_availability"],
        service_diagnostics=original["service_diagnostics"],
        copy_diagnostics=copy,
        qualification=read_json(root / MANIFESTS / config["qualification_id"] / "decision.json"),
        recorded_git_commit=frozen["recorded_git_commit"],
        inputs=bindings(root, paths),
        completed_at_utc=utc_now().isoformat(),
    )


def build(root, analysis_id):
    from .report import write_bundle

    directory, frozen = _freeze(root, analysis_id)
    with stage_lock(root / "tmp" / NAMESPACE / f"{analysis_id}.writer.lock"):
        if (directory / "report_receipt.json").exists():
            raise FileExistsError("supplement report is terminal; use check")
        target = root / REPORTS / analysis_id
        computed = result(root, analysis_id)
        analysis_path = directory / "analysis.json"
        if analysis_path.exists():
            stored = read_json(analysis_path)
            computed["completed_at_utc"] = stored["completed_at_utc"]
            if canonical_json(stored) != canonical_json(computed):
                raise ValueError("unreceipted supplement numeric result differs from replay")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".supplement-", dir=target.parent) as temporary:
            output = Path(temporary) / "bundle"
            write_bundle(json.loads(canonical_json(computed)), output)
            if target.exists() and _bundle_bytes(target) != _bundle_bytes(output):
                raise ValueError("unreceipted supplement report differs from replay")
            if not analysis_path.exists():
                _publish_immutable(analysis_path, computed)
            if not target.exists():
                output.rename(target)
        receipt = dict(
            schema_version="painter-prompt-supplement-report/1.0",
            analysis_id=analysis_id,
            source_run_id=frozen["source_run_id"],
            registered_primary_status=computed["registered_primary_status"],
            recorded_git_commit=frozen["recorded_git_commit"],
            inputs=bindings(
                root,
                [
                    MANIFESTS / analysis_id / "analysis.json",
                    MANIFESTS / analysis_id / "design_freeze.json",
                ],
            ),
            files=bindings(root, [p.relative_to(root) for p in target.rglob("*") if p.is_file()]),
            completed_at_utc=utc_now().isoformat(),
        )
        _publish_immutable(directory / "report_receipt.json", receipt)
    return receipt


def _bundle_bytes(target):
    if target.is_symlink() or not target.is_dir() or any(p.is_symlink() for p in target.rglob("*")):
        raise ValueError("supplement bundle must be a regular directory")
    return {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}


def _report_receipt(root, analysis_id):
    directory, frozen = _freeze(root, analysis_id)
    receipt = read_json(directory / "report_receipt.json")
    expected = bindings(
        root,
        [MANIFESTS / analysis_id / "analysis.json", MANIFESTS / analysis_id / "design_freeze.json"],
    )
    if (
        receipt["inputs"] != expected
        or receipt["analysis_id"] != analysis_id
        or receipt["source_run_id"] != frozen["source_run_id"]
        or receipt["recorded_git_commit"] != frozen["recorded_git_commit"]
        or receipt["registered_primary_status"] != "unavailable_incomplete_grid"
    ):
        raise ValueError("supplement report receipt identity or inputs changed")
    target = root / REPORTS / analysis_id
    if target.is_symlink() or not target.is_dir() or any(p.is_symlink() for p in target.rglob("*")):
        raise ValueError("supplement bundle must be a regular directory")
    actual = bindings(root, [p.relative_to(root) for p in target.rglob("*") if p.is_file()])
    if receipt["files"] != actual:
        raise ValueError("supplement report inventory or bytes changed")
    verify_bindings(root, read_json(directory / "analysis.json")["inputs"])
    return receipt


def check(root, analysis_id):
    from .report import write_bundle

    receipt = _report_receipt(root, analysis_id)
    stored = read_json(root / MANIFESTS / analysis_id / "analysis.json")
    rebuilt = result(root, analysis_id)
    rebuilt["completed_at_utc"] = stored["completed_at_utc"]
    if canonical_json(stored) != canonical_json(rebuilt):
        raise ValueError("supplement numeric result does not reproduce")
    with tempfile.TemporaryDirectory(prefix="supplement-replay-") as temporary:
        output = Path(temporary) / "bundle"
        write_bundle(json.loads(canonical_json(rebuilt)), output)
        target = root / REPORTS / analysis_id
        actual = _bundle_bytes(target)
        replayed = _bundle_bytes(output)
        if actual != replayed:
            raise ValueError("supplement report bytes do not reproduce")
    return dict(
        status="PASS",
        analysis_id=analysis_id,
        numeric_reproduction=True,
        report_files=len(receipt["files"]),
        registered_primary_status=stored["registered_primary_status"],
        image_access=False,
        provider_calls=0,
        ledger_writes=0,
    )


def audit(root):
    qualifications, analyses, failures = [], [], []
    for directory in sorted((root / MANIFESTS).glob("*")):
        if not directory.is_dir() or not any(
            (directory / name).is_file() for name in ("decision.json", "design_freeze.json")
        ):
            failures.append(
                dict(
                    path=directory.relative_to(root).as_posix(),
                    error="orphan supplement evidence without a decision or freeze",
                )
            )
    for target in sorted((root / REPORTS).glob("*")):
        if not (root / MANIFESTS / target.name / "design_freeze.json").is_file():
            failures.append(
                dict(
                    path=target.relative_to(root).as_posix(),
                    error="orphan report without a supplement freeze",
                )
            )
    for path in sorted((root / MANIFESTS).glob("*/decision.json")):
        try:
            check_qualification(root, path.parent.name)
            qualifications.append(path.parent.name)
        except (OSError, ValueError, KeyError) as error:
            failures.append(dict(path=path.relative_to(root).as_posix(), error=str(error)))
    for path in sorted((root / MANIFESTS).glob("*/design_freeze.json")):
        try:
            _freeze(root, path.parent.name)
            reported = (path.parent / "report_receipt.json").exists()
            if reported:
                _report_receipt(root, path.parent.name)
            elif (path.parent / "analysis.json").exists() or (
                root / REPORTS / path.parent.name
            ).exists():
                raise ValueError(
                    "unreceipted supplement artifacts require deterministic build recovery"
                )
            analyses.append(
                dict(analysis_id=path.parent.name, stage="reported" if reported else "prepared")
            )
        except (OSError, ValueError, KeyError) as error:
            failures.append(dict(path=path.relative_to(root).as_posix(), error=str(error)))
    return dict(
        overall="FAIL" if failures else "PASS",
        qualifications=qualifications,
        analyses=analyses,
        failures=failures,
        scope="Commit-bound supplement inputs, generation prefix and report hashes; "
        "check replays numerics.",
    )
