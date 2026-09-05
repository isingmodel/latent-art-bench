"""Read-only checks of prompt-study evidence, including bounded retained gzip responses."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path

from latent_art_bench.io import hash_file, read_json, read_jsonl
from latent_art_bench.painter_feature_generation_v2.artifacts import identifier
from latent_art_bench.painter_feature_generation_v2.features import NAMES

from . import generation, measurement
from .calibration_record import _verify_commit, validate_calibration
from .common import MANIFESTS, PACKAGE
from .design import validate_config
from .randomization_record import validate_randomization_calibration

GENERATION_STATUSES = {
    "generated",
    "not_attempted",
    "invalid_output",
    "refused",
    "authentication_blocked",
    "quota_or_rate_limited",
    "resource_ceiling",
    "outcome_uncertain",
    "transport_or_schema_failure",
}


def _calibration(root, calibration_id):
    calibration_id = identifier(calibration_id)
    decision = read_json(root / MANIFESTS / calibration_id / "decision.json")
    validator = (
        validate_randomization_calibration
        if decision.get("primary_estimator") == "paired_randomization"
        else validate_calibration
    )
    return validator(root, calibration_id)


class _Audit:
    def __init__(self, root, proxy_root):
        self.root = Path(root).resolve()
        self.proxy_root = None if proxy_root is None else Path(proxy_root).resolve()
        self.checks, self.failures, self.unverified_proxies = 0, [], []

    def require(self, condition, message):
        self.checks += 1
        if not condition:
            raise ValueError(message)

    def path(self, relative):
        relative = Path(relative)
        self.require(
            not relative.is_absolute() and ".." not in relative.parts, "nonportable evidence path"
        )
        path = (self.root / relative).resolve()
        path.relative_to(self.root)
        return path

    def check_hash(self, relative, expected):
        self.require(hash_file(self.path(relative)) == expected, f"changed bytes: {relative}")

    def current_bindings(self, records):
        self.require(len({r["path"] for r in records}) == len(records), "duplicate input binding")
        for row in records:
            self.check_hash(row["path"], row["sha256"])

    def source_bindings(self, commit, records, root=None):
        self.require(
            bool(records) and len({r["path"] for r in records}) == len(records),
            "missing or duplicate recorded-commit bindings",
        )
        _verify_commit(self.root if root is None else root, commit, records)
        self.checks += len(records)

    def guard(self, label, function):
        try:
            function()
        except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
            self.failures.append(f"{label}: {type(exc).__name__}: {exc}")

    def run(self, directory):
        run_id = directory.name
        relative = directory.relative_to(self.root)
        frozen = read_json(directory / "generation_freeze.json")
        self.require(frozen["run_id"] == run_id, "generation freeze identity changed")
        self.source_bindings(frozen["recorded_git_commit"], frozen["inputs"])
        config_path = frozen["config_path"]
        self.path(config_path)
        bound = {row["path"]: row["sha256"] for row in frozen["inputs"]}
        self.require(config_path in bound, "configuration source is absent from frozen inputs")
        committed_config = subprocess.run(
            ["git", "show", f"{frozen['recorded_git_commit']}:{config_path}"],
            cwd=self.root,
            capture_output=True,
            check=False,
        )
        self.require(
            committed_config.returncode == 0
            and json.loads(committed_config.stdout) == frozen["config"],
            "embedded configuration differs from its recorded-commit JSON",
        )
        self.require(bool(frozen["reference_inputs"]), "missing finite-reference bindings")
        self.require(
            all(bound.get(row["path"]) == row["sha256"] for row in frozen["reference_inputs"]),
            "finite reference inputs are missing from the frozen source bindings",
        )
        self.current_bindings(frozen["reference_inputs"])
        for name, key in (
            ("requests.jsonl", "requests_sha256"),
            ("prompts.json", "library_sha256"),
        ):
            self.check_hash(relative / name, frozen[key])
        requests = read_jsonl(directory / "requests.jsonl")
        self.require(
            requests
            == generation.request_grid(frozen["config"], read_json(directory / "prompts.json")),
            "frozen request grid changed",
        )
        self.require(frozen["requests"] == len(requests), "frozen request count changed")
        config = frozen["config"]
        validate_config(config, authorized=True)
        self.checks += 1
        calibration = _calibration(self.root, config["calibration_id"])
        calibration_path = MANIFESTS / config["calibration_id"] / "decision.json"
        calibration_records = [
            dict(path=calibration_path.as_posix(), sha256=hash_file(self.root / calibration_path)),
            *calibration["files"],
        ]
        self.require(
            all(bound.get(row["path"]) == row["sha256"] for row in calibration_records),
            "calibration decision or result files are missing from frozen source bindings",
        )
        self.require(
            config["repetitions"] in calibration["qualified_repetitions"]
            and config["primary_estimator"] == calibration["primary_estimator"]
            and config["simultaneous_alpha"] == calibration["simultaneous_alpha"],
            "run configuration lacks its recorded primary calibration",
        )
        self.require(
            calibration["uses_empirical_outcomes_for_tuning"] is False,
            "calibration used empirical outcomes for tuning",
        )
        proxy = frozen["proxy_source"]
        if self.proxy_root is None:
            self.unverified_proxies.append(
                dict(
                    run_id=run_id,
                    repository=proxy["repository"],
                    recorded_git_commit=proxy["recorded_git_commit"],
                )
            )
        else:
            self.source_bindings(proxy["recorded_git_commit"], proxy["files"], self.proxy_root)
        journal = generation._Journal(directory / "generation_events.jsonl")
        attempts, terminal = generation._state(journal.rows, requests)
        self.checks += 1
        self.require(
            list(attempts) == [r["request_id"] for r in requests[: len(attempts)]],
            "generation attempts do not follow the frozen prefix",
        )
        self.require(
            all(r["status"] in GENERATION_STATUSES for r in terminal.values()),
            "unrecognized generation status",
        )
        checked = set()
        for row in terminal.values():
            if "response_path" in row:
                key = tuple(
                    row[k]
                    for k in (
                        "response_path",
                        "response_sha256",
                        "stored_sha256",
                        "bytes",
                        "stored_bytes",
                    )
                )
                if key not in checked:
                    measurement._response_bytes(
                        self.root, run_id, row, config["maximum_response_bytes"]
                    )
                    checked.add(key)
                    self.checks += 1
        receipt_path = directory / "generation_receipt.json"
        outputs = None
        if (directory / "outputs.jsonl").exists():
            outputs = read_jsonl(directory / "outputs.jsonl")
            self.require(
                len(terminal) == len(requests)
                and outputs == [terminal.get(r["request_id"]) for r in requests],
                "terminal generation outputs differ from the ledger",
            )
        if receipt_path.exists():
            receipt = read_json(receipt_path)
            self.require(outputs is not None, "generation receipt has no terminal output file")
            for field, name in (
                ("freeze_sha256", "generation_freeze.json"),
                ("ledger_sha256", "generation_events.jsonl"),
                ("outputs_sha256", "outputs.jsonl"),
            ):
                self.check_hash(relative / name, receipt[field])
            self.require(
                receipt["run_id"] == run_id
                and receipt["terminal"] is True
                and receipt["expected_requests"] == len(requests)
                and receipt["terminal_requests"] == len(outputs)
                and receipt["image_attempts"] == len(attempts)
                and receipt["statuses"] == dict(Counter(r["status"] for r in outputs))
                and receipt["complete_generated_grid"]
                is all(r["status"] == "generated" for r in outputs),
                "terminal generation accounting differs from the ledger",
            )
            self.require(
                receipt["status"] in {"complete", "aborted"}
                and ((receipt["stopped_on"] is None) == (receipt["status"] == "complete")),
                "terminal generation stop accounting changed",
            )
        measurement_artifacts = any(
            (directory / name).exists()
            for name in (
                "measurement_events.jsonl",
                "measurement_receipt.json",
                "measured_features.jsonl",
                "analysis.json",
                "report_receipt.json",
            )
        )
        if measurement_artifacts:
            self.require(receipt_path.exists(), "measurement has no terminal generation receipt")
            self.measurement(directory, frozen, requests, outputs)

    def measurement(self, directory, frozen, requests, outputs):
        relative, run_id = directory.relative_to(self.root), directory.name
        journal = generation._Journal(directory / "measurement_events.jsonl")
        self.require(bool(journal.rows), "measurement lacks its source-binding event")
        start = journal.rows[0]
        self.require(
            start["kind"] == "stage_start"
            and start["run_id"] == run_id
            and start["short_side"] == 512
            and start["feature_names"] == list(NAMES),
            "measurement stage-start contract changed",
        )
        self.current_bindings(start["inputs"])
        expected_sources = {(relative / name).as_posix() for name in measurement.SOURCE_FILES}
        self.require(
            {r["path"] for r in start["inputs"]} == expected_sources,
            "measurement source inventory changed",
        )
        self.require(
            len(journal.rows) - 1 <= len(requests), "measurement exceeds frozen population"
        )
        measured = []
        for index, event in enumerate(journal.rows[1:]):
            self.require(event["kind"] == "terminal", "invalid measurement event")
            measurement._validate_row(event["row"], requests[index], outputs[index], run_id)
            self.checks += 1
            measured.append(event["row"])
        feature_path = directory / "measured_features.jsonl"
        if feature_path.exists():
            self.require(
                len(measured) == len(requests) and read_jsonl(feature_path) == measured,
                "terminal measured features differ from ledger",
            )
        receipt_path = directory / "measurement_receipt.json"
        if receipt_path.exists():
            receipt = read_json(receipt_path)
            self.current_bindings(receipt["inputs"])
            self.require(
                receipt["inputs"] == start["inputs"], "measurement receipt source set changed"
            )
            for field, name in (
                ("freeze_sha256", "generation_freeze.json"),
                ("generation_receipt_sha256", "generation_receipt.json"),
                ("outputs_sha256", "outputs.jsonl"),
                ("feature_file_sha256", "measured_features.jsonl"),
                ("ledger_sha256", "measurement_events.jsonl"),
            ):
                self.check_hash(relative / name, receipt[field])
            self.require(
                receipt["run_id"] == run_id
                and receipt["terminal"] is True
                and receipt["stage"] == "generated"
                and receipt["status"] == "complete"
                and receipt["short_side"] == 512
                and receipt["feature_names"] == list(NAMES)
                and receipt["expected_records"] == receipt["terminal_records"] == len(requests)
                and len(measured) == len(requests)
                and receipt["statuses"] == dict(Counter(r["status"] for r in measured))
                and receipt["complete_measured_grid"]
                is all(r["status"] == "measured" for r in measured),
                "terminal measurement accounting differs from ledger",
            )
        analysis_path = directory / "analysis.json"
        if analysis_path.exists():
            self.require(receipt_path.exists(), "analysis precedes terminal measurement")
            from .report import _validate

            result = read_json(analysis_path)
            self.current_bindings(result["inputs"])
            expected_inputs = {
                (relative / name).as_posix()
                for name in (
                    "generation_freeze.json",
                    "generation_receipt.json",
                    "outputs.jsonl",
                    "requests.jsonl",
                    "measurement_receipt.json",
                    "measured_features.jsonl",
                    "measurement_events.jsonl",
                )
            }
            if result["status"] == "complete":
                expected_inputs.update(row["path"] for row in frozen["reference_inputs"])
            expected_inputs.add(
                (MANIFESTS / frozen["config"]["calibration_id"] / "decision.json").as_posix()
            )
            self.require(
                {row["path"] for row in result["inputs"]} == expected_inputs,
                "analysis source inventory differs from the frozen analysis contract",
            )
            self.require(
                result["run_id"] == run_id
                and result["calibration_id"] == frozen["config"]["calibration_id"]
                and result["repetitions"] == frozen["config"]["repetitions"]
                and (result["status"] == "complete")
                is all(row["status"] == "measured" for row in measured),
                "analysis completeness or run identity changed",
            )
            _validate(result, run_id)
            self.checks += 1
            self.report(directory, frozen, result)
        elif (directory / "report_receipt.json").exists():
            raise ValueError("report receipt has no terminal analysis")

    def report(self, directory, frozen, result):
        receipt_path = directory / "report_receipt.json"
        if not receipt_path.exists():
            return
        relative, run_id = directory.relative_to(self.root), directory.name
        receipt = read_json(receipt_path)
        self.require(
            receipt["run_id"] == run_id and receipt["analysis_status"] == result["status"],
            "report receipt identity or status changed",
        )
        expected = {
            (relative / "analysis.json").as_posix(),
            (PACKAGE / "report.py").as_posix(),
            (relative / "generation_freeze.json").as_posix(),
        }
        self.require(
            len(receipt["inputs"]) == len(expected)
            and {r["path"] for r in receipt["inputs"]} == expected,
            "report input inventory changed",
        )
        code = [r for r in receipt["inputs"] if r["path"] == (PACKAGE / "report.py").as_posix()]
        self.require(
            receipt["recorded_git_commit"] == frozen["recorded_git_commit"]
            and code[0] in frozen["inputs"],
            "report renderer differs from the frozen source commit",
        )
        self.source_bindings(receipt["recorded_git_commit"], code)
        self.current_bindings([r for r in receipt["inputs"] if r not in code])
        self.current_bindings(receipt["files"])
        target = self.path(Path("reports/painter_prompt_study_v1") / run_id)
        actual = {p.relative_to(self.root).as_posix() for p in target.rglob("*") if p.is_file()}
        self.require(
            actual == {r["path"] for r in receipt["files"]} and bool(actual),
            "report file inventory differs from its receipt",
        )


def audit(root: Path, proxy_root: Path | None = None) -> dict:
    """Audit all new-study evidence without creating files or decoding artwork images."""
    verifier = _Audit(root, proxy_root)
    calibrations, runs = [], []
    for directory in sorted((verifier.root / MANIFESTS).glob("*")):
        if not directory.is_dir():
            continue
        if (directory / "decision.json").exists():
            calibrations.append(directory.name)
            verifier.guard(directory.name, lambda d=directory: _calibration(verifier.root, d.name))
            verifier.checks += 1
        elif (directory / "generation_freeze.json").exists():
            runs.append(directory.name)
            verifier.guard(directory.name, lambda d=directory: verifier.run(d))
        elif any(directory.iterdir()):
            verifier.failures.append(
                f"{directory.name}: orphan artifacts without a freeze or decision"
            )
    overall = (
        "FAIL"
        if verifier.failures
        else "pass_local_proxy_unverified"
        if verifier.unverified_proxies
        else "PASS"
    )
    return dict(
        overall=overall,
        checks=verifier.checks,
        failures=verifier.failures,
        calibrations=calibrations,
        runs=runs,
        unverified_external_proxy_sources=verifier.unverified_proxies,
        scope="read-only commit-bound sources, numeric evidence, ledgers, reports and gzip hashes",
    )
