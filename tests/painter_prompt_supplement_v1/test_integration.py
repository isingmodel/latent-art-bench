"""Real numeric publication/replay with synthetic sealed-source boundary substitutes only."""

import csv
from collections import Counter
from pathlib import Path

import httpx
import numpy as np
import pytest

from latent_art_bench.io import canonical_json
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import empirical
from latent_art_bench.painter_prompt_study_v1 import generation, measurement
from latent_art_bench.painter_prompt_study_v1.prompts import CONDITIONS, METHOD_IDS, TEMPLATE_IDS
from latent_art_bench.painter_prompt_supplement_v1 import artifacts, report

from .test_artifacts import git, write_json
from .test_statistics import grid, missing


def _write_rows(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8")


def _availability(rows, *, per_template=False):
    result = []
    for alias in generation.ALIASES:
        for method in METHOD_IDS:
            for condition in CONDITIONS:
                for template in TEMPLATE_IDS if per_template else (None,):
                    selected = [
                        row
                        for row in rows
                        if (row["alias"], row["method_id"], row["condition"])
                        == (alias, method, condition)
                        and (template is None or row["template_id"] == template)
                    ]
                    entry = dict(
                        alias=alias,
                        method_id=method,
                        condition=condition,
                        expected=4 if per_template else 64,
                        statuses=dict(Counter(row["status"] for row in selected)),
                    )
                    if per_template:
                        entry["template_id"] = template
                    result.append(entry)
    return result


def test_one_refusal_real_statistics_publication_and_byte_replay(tmp_path, monkeypatch):
    """This tests composition; the original freeze/replay/reference loader have separate audits."""
    repo = Path(__file__).resolve().parents[2]
    config = artifacts._config(repo)
    analysis_id = "supplement-offline-integration"
    source_id = config["source_run_id"]
    source = artifacts.SOURCE_MANIFESTS / source_id
    method_id = "synthetic-reference-method"
    reference_dir = Path("data/manifests/painter_feature_generation_v2") / method_id
    directory = tmp_path / artifacts.MANIFESTS / analysis_id
    _, rows, scaler = grid(4)
    missing(rows[0])
    for row in rows[1:]:
        row["raw_sha256"] = artifacts.digest(["synthetic-generated", row["request_id"]])
        row["phash"] = row["raw_sha256"][:16]
    reference_counts = dict(zip(PAINTER_IDS, (297, 106, 141, 105)))
    reference_rows = [
        dict(
            image_id=f"synthetic-reference/{painter}/{index}",
            painter_id=painter,
            status="measured",
            values=[(index % 7) / 10 + coordinate / 50 for coordinate in range(31)],
            raw_sha256=artifacts.digest(["synthetic-reference", painter, index]),
            phash=artifacts.digest(["synthetic-reference", painter, index])[:16],
        )
        for painter, count in reference_counts.items()
        for index in range(count)
    ]
    # One exact synthetic duplicate exercises the real numeric copy screen without any pixels.
    for key in ("raw_sha256", "phash", "values"):
        reference_rows[0][key] = rows[1][key]
    real = {
        painter: np.array([row["values"] for row in reference_rows if row["painter_id"] == painter])
        for painter in PAINTER_IDS
    }
    _write_rows(tmp_path / reference_dir / "confirmation_features.jsonl", reference_rows)
    write_json(tmp_path / reference_dir / "scaler.json", scaler)
    reference = dict(
        inputs=artifacts.bindings(
            tmp_path,
            [reference_dir / "confirmation_features.jsonl", reference_dir / "scaler.json"],
        ),
        scaler_development_counts=dict(zip(PAINTER_IDS, (101, 36, 48, 36))),
    )
    _write_rows(tmp_path / source / "measured_features.jsonl", rows)
    outputs = [
        dict(
            request_id=row["request_id"],
            alias=row["alias"],
            method_id=row["method_id"],
            status="generated" if row["status"] == "measured" else "refused",
            reported=dict(quality="low", size="512x512"),
            decoded_size="512x512" if row["status"] == "measured" else "unreported",
        )
        for row in rows
    ]
    _write_rows(tmp_path / source / "outputs.jsonl", outputs)
    _write_rows(tmp_path / source / "generation_events.jsonl", outputs)
    write_json(
        tmp_path / source / "generation_freeze.json",
        dict(run_id=source_id, reference_inputs=reference["inputs"]),
    )
    write_json(
        tmp_path / source / "generation_receipt.json",
        dict(terminal=True, expected_requests=1920, statuses=dict(generated=1919, refused=1)),
    )
    write_json(
        tmp_path / source / "measurement_receipt.json",
        dict(
            terminal_records=1920,
            complete_measured_grid=False,
            statuses=dict(measured=1919, not_generated=1),
        ),
    )
    write_json(tmp_path / source / "report_receipt.json", dict(synthetic_sealed_source=True))
    source_paths = [path.relative_to(tmp_path) for path in (tmp_path / source).iterdir()]
    original = dict(
        status="unavailable_incomplete_grid",
        source_method_id=method_id,
        inputs=artifacts.bindings(tmp_path, source_paths),
        availability=_availability(rows),
        template_availability=_availability(rows, per_template=True),
        service_diagnostics={
            method: empirical.service_diagnostics([r for r in outputs if r["method_id"] == method])
            for method in METHOD_IDS
        },
    )
    write_json(tmp_path / source / "analysis.json", original)
    write_json(tmp_path / artifacts.CONFIG, config)
    qualification_path = artifacts.MANIFESTS / config["qualification_id"] / "decision.json"
    qualification = dict(
        qualification_id=config["qualification_id"],
        qualified=True,
        files=[],
        scope="Synthetic boundary substitute; qualification validity is tested separately.",
    )
    write_json(tmp_path / qualification_path, qualification)
    # A source-worker sentinel is intentionally outside the new report namespace.
    worker = tmp_path / "tmp" / source_id / "completion" / "worker.json"
    write_json(worker, dict(pid=12345, stage="synthetic terminal source"))
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Offline fixture")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "Synthetic sealed inputs")
    frozen = dict(
        analysis_id=analysis_id,
        source_run_id=source_id,
        config=config,
        recorded_git_commit=git(tmp_path, "rev-parse", "HEAD"),
        registration_status=config["registration_status"],
        inputs=artifacts.bindings(tmp_path, [artifacts.CONFIG, qualification_path]),
    )
    write_json(directory / "design_freeze.json", frozen)
    boundary_calls = Counter()

    def sealed_freeze(root, identifier):
        assert root == tmp_path and identifier == analysis_id
        boundary_calls["freeze"] += 1
        return directory, frozen

    def sealed_reproduction(root, identifier):
        assert root == tmp_path and identifier == source_id
        boundary_calls["reproduce"] += 1
        return dict(status="PASS", synthetic_sealed_source=True)

    def sealed_reference(root, identifier):
        assert root == tmp_path and identifier == method_id
        boundary_calls["reference"] += 1
        return real, {}, {}, scaler, {}, reference

    def forbidden(*args, **kwargs):
        pytest.fail("Numeric supplement attempted provider or image-measurement access")

    monkeypatch.setattr(artifacts, "_freeze", sealed_freeze)
    monkeypatch.setattr(artifacts.reproduction, "reproduce", sealed_reproduction)
    monkeypatch.setattr(artifacts, "load_source", sealed_reference)
    monkeypatch.setattr(generation, "execute", forbidden)
    monkeypatch.setattr(measurement, "measure", forbidden)
    monkeypatch.setattr(measurement, "_response_bytes", forbidden)
    monkeypatch.setattr(httpx, "Client", forbidden)
    source_before = artifacts.bindings(tmp_path, source_paths + [source / "analysis.json"])
    worker_before = worker.read_bytes()
    computed = artifacts.result(tmp_path, analysis_id)
    expected_counts = dict(
        distances=360,
        absolute=72,
        coordinates=744,
        exploratory_contrasts=48,
        pair_support=1024,
        scene_contributions=3072,
        secondary=72,
        time_diagnostics=48,
        availability=30,
        template_availability=480,
    )
    assert {name: len(computed[name]) for name in report.TABLES} == expected_counts
    assert computed["qualification"] == qualification
    assert computed["registered_primary_status"] == "unavailable_incomplete_grid"
    assert computed["source_method_id"] == method_id and computed["source_run_id"] == source_id
    assert computed["reference_counts"] == reference_counts
    assert computed["scaler_development_counts"] == reference["scaler_development_counts"]
    assert computed["service_diagnostics"] == original["service_diagnostics"]
    assert computed["inference"]["permutation_draws"] == 99999
    assert computed["inference"]["family_size"] == computed["inference"]["eligible_endpoints"] == 48
    assert Counter(row["pairs"] for row in computed["exploratory_contrasts"]) == {63: 3, 64: 45}
    assert sum(not row["included"] for row in computed["pair_support"]) == 1
    assert sum(row["contribution"] is None for row in computed["scene_contributions"]) == 3
    assert all(row["distance"] is not None for row in computed["distances"])
    assert computed["copy_diagnostics"]["searched_real_records"] == 649
    assert computed["copy_diagnostics"]["candidates"] == [
        dict(
            request_id=rows[1]["image_id"],
            nearest_phash_reference=reference_rows[0]["image_id"],
            phash_hamming_distance=0,
            exact_file_references=[reference_rows[0]["image_id"]],
        )
    ]
    bound_paths = {row["path"] for row in computed["inputs"]}
    assert {
        row["path"] for row in reference["inputs"] + original["inputs"] + frozen["inputs"]
    } <= bound_paths
    assert (source / "analysis.json").as_posix() in bound_paths
    assert (artifacts.MANIFESTS / analysis_id / "design_freeze.json").as_posix() in bound_paths

    receipt = artifacts.build(tmp_path, analysis_id)
    published = artifacts.read_json(directory / "analysis.json")
    computed["completed_at_utc"] = published["completed_at_utc"]
    assert canonical_json(published) == canonical_json(computed)
    assert len(receipt["files"]) == 18
    assert receipt["recorded_git_commit"] == frozen["recorded_git_commit"]
    target = tmp_path / artifacts.REPORTS / analysis_id
    for name, count in expected_counts.items():
        with (target / f"{name}.csv").open(newline="") as handle:
            assert len(list(csv.DictReader(handle))) == count
    assert sum(path.suffix == ".png" for path in target.rglob("*")) == 3
    assert sum(path.suffix == ".svg" for path in target.rglob("*")) == 3
    before_check = {
        path.relative_to(tmp_path): path.read_bytes()
        for parent in (directory, target)
        for path in parent.rglob("*")
        if path.is_file()
    }
    assert artifacts.check(tmp_path, analysis_id) == dict(
        status="PASS",
        analysis_id=analysis_id,
        numeric_reproduction=True,
        report_files=18,
        registered_primary_status="unavailable_incomplete_grid",
        image_access=False,
        provider_calls=0,
        ledger_writes=0,
    )
    assert before_check == {
        path.relative_to(tmp_path): path.read_bytes()
        for parent in (directory, target)
        for path in parent.rglob("*")
        if path.is_file()
    }
    assert artifacts.bindings(tmp_path, source_paths + [source / "analysis.json"]) == source_before
    assert worker.read_bytes() == worker_before
    assert boundary_calls["reproduce"] == boundary_calls["reference"] == 3
    assert not (tmp_path / "research_workspace").exists()
