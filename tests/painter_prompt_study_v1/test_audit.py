"""Read-only audits detect retained-byte and accounting faults without provider access."""

import gzip
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_feature_generation_v2.artifacts import bindings, digest, publish
from latent_art_bench.painter_feature_generation_v2.features import NAMES
from latent_art_bench.painter_prompt_study_v1 import audit, generation, measurement, report
from latent_art_bench.painter_prompt_study_v1.common import MANIFESTS, PACKAGE, WORKSPACE
from latent_art_bench.painter_prompt_study_v1.prompts import METHOD_IDS


def _git(root, *arguments):
    return (
        subprocess.check_output(["git", *arguments], cwd=root, stderr=subprocess.DEVNULL)
        .decode()
        .strip()
    )


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    root, run_id = tmp_path, "audit-run"
    directory = root / MANIFESTS / run_id
    directory.mkdir(parents=True)
    calpath = MANIFESTS / "synthetic-calibration" / "decision.json"
    for path, content in (
        (Path("source.py"), "initial source"),
        (Path("reference.json"), '{"reference": true}'),
        (PACKAGE / "report.py", "renderer fixture"),
        (Path("proxy.py"), "proxy source"),
        (calpath, '{"primary_estimator":"paired_randomization"}'),
    ):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(content)
    settings = dict(
        repetitions=4,
        aliases=list(generation.ALIASES),
        method_ids=list(METHOD_IDS),
        maximum_requests=1920,
        approved_maximum_requests=1920,
        authorization="authorized synthetic fixture only",
        paid_fallback=False,
        base_url=generation.BASE,
        order_salt="synthetic-audit-order",
        order_seed=123,
        permutation_seed=321,
        permutation_draws=99999,
        multiplicity="holm",
        maximum_response_bytes=generation.MAX_RESPONSE_BYTES,
        max_runtime_bytes=1024**3,
        reserve_disk_bytes=generation.RESERVE_DISK_BYTES,
        timeout_seconds=240,
        minimum_start_interval_seconds=15,
        minimum_decoded_short_side=512,
        primary_estimator="paired_randomization",
        simultaneous_alpha=0.05,
        calibration_id="synthetic-calibration",
        **generation.RENDER,
    )
    config_path = Path("configs/painter_prompt_study_v1/audit.json")
    (root / config_path).parent.mkdir(parents=True)
    (root / config_path).write_text(json.dumps(settings))
    _git(root, "init")
    _git(root, "add", ".")
    _git(
        root,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "-c",
        "core.hooksPath=/dev/null",
        "commit",
        "--no-gpg-sign",
        "-m",
        "source inputs",
    )
    commit = _git(root, "rev-parse", "HEAD")
    requests = [
        dict(
            sequence=i,
            request_id=f"q{i}",
            block=0,
            alias="gpt-image-1",
            method_id="by_name",
            condition="claude_monet",
            template_id=f"W{i + 1}",
            payload=dict(generation.RENDER),
        )
        for i in range(2)
    ]
    # Full 1,920-cell grid construction has separate tests; audit faults use two literal requests.
    monkeypatch.setattr(generation, "request_grid", lambda config, library: requests)
    # Full report roster validation runs in test_end_to_end; this focused retained-
    # evidence fixture deliberately has only two requests, both refused.
    monkeypatch.setattr(report, "_validate", lambda result, run_id: None)
    monkeypatch.setattr(
        audit,
        "validate_randomization_calibration",
        lambda *args: dict(
            qualified_repetitions=[1, 2, 4],
            primary_estimator="paired_randomization",
            simultaneous_alpha=0.05,
            uses_empirical_outcomes_for_tuning=False,
            files=[],
        ),
    )
    publish(directory / "prompts.json", {"fixture": "two requests"})
    publish(directory / "requests.jsonl", requests, lines=True)
    frozen = dict(
        run_id=run_id,
        config=settings,
        config_path=config_path.as_posix(),
        recorded_git_commit=commit,
        requests=len(requests),
        inputs=bindings(
            root,
            [
                Path("source.py"),
                Path("reference.json"),
                PACKAGE / "report.py",
                calpath,
                config_path,
            ],
        ),
        reference_inputs=bindings(root, [Path("reference.json")]),
        requests_sha256=hash_file(directory / "requests.jsonl"),
        library_sha256=hash_file(directory / "prompts.json"),
        proxy_source=dict(
            repository="proxy-fixture",
            recorded_git_commit=commit,
            files=bindings(root, [Path("proxy.py")]),
        ),
    )
    publish(directory / "generation_freeze.json", frozen)
    return root, directory, frozen, requests


def _terminal(prepared, *, measured=False, reported=False):
    root, directory, frozen, requests = prepared
    run_id = directory.name
    body = b'{"error":{"code":"moderation_blocked"}}'
    raw_sha = hashlib.sha256(body).hexdigest()
    compressed = gzip.compress(body, mtime=0)
    response_path = WORKSPACE / run_id / "responses" / f"{raw_sha}.json.gz"
    (root / response_path).parent.mkdir(parents=True)
    (root / response_path).write_bytes(compressed)
    journal = generation._Journal(directory / "generation_events.jsonl")
    terminal = {}
    for request in requests:
        journal.append(
            dict(kind="attempt", request_id=request["request_id"], request_sha256=digest(request))
        )
        row = journal.append(
            dict(
                generation._identity(request),
                kind="terminal",
                status="refused",
                attempted=True,
                response_path=response_path.as_posix(),
                response_sha256=raw_sha,
                stored_sha256=hashlib.sha256(compressed).hexdigest(),
                bytes=len(body),
                stored_bytes=len(compressed),
            )
        )
        terminal[request["request_id"]] = row
    generation._finish(directory, frozen, requests, terminal, None)
    if not measured:
        return response_path
    sources = bindings(
        root, [(directory.relative_to(root) / name) for name in measurement.SOURCE_FILES]
    )
    journal = generation._Journal(directory / "measurement_events.jsonl")
    journal.append(
        dict(
            kind="stage_start",
            run_id=run_id,
            inputs=sources,
            short_side=512,
            feature_names=list(NAMES),
        )
    )
    rows = []
    for request in requests:
        row = dict(
            measurement._identity(request, terminal[request["request_id"]], run_id),
            status="not_generated",
        )
        journal.append(dict(kind="terminal", row=row))
        rows.append(row)
    publish(directory / "measured_features.jsonl", rows, lines=True)
    receipt = dict(
        run_id=run_id,
        stage="generated",
        terminal=True,
        status="complete",
        expected_records=len(rows),
        terminal_records=len(rows),
        statuses=dict(Counter(r["status"] for r in rows)),
        complete_measured_grid=False,
        short_side=512,
        feature_names=list(NAMES),
        inputs=sources,
        freeze_sha256=hash_file(directory / "generation_freeze.json"),
        generation_receipt_sha256=hash_file(directory / "generation_receipt.json"),
        outputs_sha256=hash_file(directory / "outputs.jsonl"),
        feature_file_sha256=hash_file(directory / "measured_features.jsonl"),
        ledger_sha256=hash_file(directory / "measurement_events.jsonl"),
    )
    publish(directory / "measurement_receipt.json", receipt)
    if reported:
        relative = directory.relative_to(root)
        result = dict(
            schema_version="painter-prompt-analysis/1.0",
            run_id=run_id,
            calibration_id="synthetic-calibration",
            repetitions=4,
            status="unavailable_incomplete_grid",
            aliases=["gpt-image-1"],
            methods=["by_name"],
            painters=["claude_monet"],
            availability=[
                dict(
                    alias="gpt-image-1",
                    method_id="by_name",
                    condition=p,
                    expected=2 if p == "claude_monet" else 0,
                    statuses={"not_generated": 2 if p == "claude_monet" else 0},
                )
                for p in ["claude_monet", "artist_free"]
            ],
            inputs=bindings(
                root,
                [
                    relative / name
                    for name in (
                        "generation_freeze.json",
                        "generation_receipt.json",
                        "outputs.jsonl",
                        "requests.jsonl",
                        "measurement_receipt.json",
                        "measured_features.jsonl",
                        "measurement_events.jsonl",
                    )
                ]
                + [MANIFESTS / "synthetic-calibration" / "decision.json"],
            ),
        )
        publish(directory / "analysis.json", result)
        report_path = Path("reports/painter_prompt_study_v1") / run_id / "REPORT.md"
        (root / report_path).parent.mkdir(parents=True)
        (root / report_path).write_text("No numeric inference for this refused fixture.\n")
        publish(
            directory / "report_receipt.json",
            dict(
                run_id=run_id,
                analysis_status=result["status"],
                recorded_git_commit=frozen["recorded_git_commit"],
                inputs=bindings(
                    root,
                    [
                        relative / "analysis.json",
                        relative / "generation_freeze.json",
                        PACKAGE / "report.py",
                    ],
                ),
                files=bindings(root, [report_path]),
            ),
        )
    return response_path


def test_prepared_run_audits_without_creating_journals_and_marks_missing_proxy(prepared):
    root, _, _, _ = prepared
    before = {p: hash_file(p) for p in root.rglob("*") if p.is_file()}
    result = audit.audit(root)
    assert result["overall"] == "pass_local_proxy_unverified"
    assert not result["failures"]
    assert result["unverified_external_proxy_sources"][0]["run_id"] == "audit-run"
    assert audit.audit(root, proxy_root=root)["overall"] == "PASS"
    assert before == {p: hash_file(p) for p in root.rglob("*") if p.is_file()}


def test_historical_source_edits_do_not_hide_changed_live_reference_bytes(prepared):
    root, _, _, _ = prepared
    (root / "source.py").write_text("later shared implementation")
    assert audit.audit(root, proxy_root=root)["overall"] == "PASS"
    (root / "reference.json").write_text("changed numeric evidence")
    result = audit.audit(root, proxy_root=root)
    assert result["overall"] == "FAIL"
    assert "changed bytes: reference.json" in result["failures"][0]


@pytest.mark.parametrize(
    "fault",
    [
        "gzip",
        "generation_count",
        "measurement_count",
        "report_file",
        "request_hash",
        "authorization",
    ],
)
def test_full_retained_graph_detects_material_faults(prepared, fault):
    root, directory, _, _ = prepared
    response = _terminal(prepared, measured=True, reported=True)
    initial = audit.audit(root, proxy_root=root)
    assert initial["overall"] == "PASS", initial
    if fault == "gzip":
        (root / response).write_bytes(b"changed compressed response")
    elif fault == "report_file":
        path = root / "reports/painter_prompt_study_v1/audit-run/REPORT.md"
        path.write_text("changed report")
    else:
        name = (
            "generation_receipt.json"
            if fault == "generation_count"
            else "measurement_receipt.json"
            if fault == "measurement_count"
            else "generation_freeze.json"
        )
        path = directory / name
        row = read_json(path)
        if fault == "generation_count":
            row["image_attempts"] -= 1
        elif fault == "measurement_count":
            row["terminal_records"] -= 1
        elif fault == "request_hash":
            row["requests_sha256"] = "wrong"
        else:
            row["config"]["approved_maximum_requests"] = 0
        path.write_text(json.dumps(row))
    result = audit.audit(root, proxy_root=root)
    assert result["overall"] == "FAIL"
    assert result["failures"]


def test_unknown_orphan_artifact_directory_is_not_a_successful_empty_audit(tmp_path):
    path = tmp_path / MANIFESTS / "orphan" / "outputs.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text("{}\n")
    result = audit.audit(tmp_path)
    assert result["overall"] == "FAIL"
    assert "orphan" in result["failures"][0]


@pytest.mark.parametrize("fault", ["config_path", "embedded_config", "reference", "calibration"])
def test_every_frozen_scientific_input_is_bound_to_its_committed_source(prepared, fault):
    root, directory, frozen, _ = prepared
    assert audit.audit(root, proxy_root=root)["overall"] == "PASS"
    if fault == "config_path":
        frozen["config_path"] = "configs/unbound.json"
    elif fault == "embedded_config":
        frozen["config"]["permutation_seed"] += 1
    else:
        remove = (
            "reference.json"
            if fault == "reference"
            else (MANIFESTS / "synthetic-calibration" / "decision.json").as_posix()
        )
        frozen["inputs"] = [r for r in frozen["inputs"] if r["path"] != remove]
    (directory / "generation_freeze.json").write_text(json.dumps(frozen))
    result = audit.audit(root, proxy_root=root)
    assert result["overall"] == "FAIL", result


def test_qualified_calibration_result_files_must_also_be_frozen(prepared, monkeypatch):
    root, _, _, _ = prepared
    monkeypatch.setattr(
        audit,
        "validate_randomization_calibration",
        lambda *args: dict(
            qualified_repetitions=[1, 2, 4],
            primary_estimator="paired_randomization",
            simultaneous_alpha=0.05,
            uses_empirical_outcomes_for_tuning=False,
            files=[dict(path="missing_validation.json", sha256="0" * 64)],
        ),
    )
    result = audit.audit(root, proxy_root=root)
    assert result["overall"] == "FAIL"
    assert "calibration decision or result files" in result["failures"][0]
