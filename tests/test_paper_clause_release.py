"""Synthetic numerical release safety and isolated replay; no service access."""

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
LOCAL_WORKFLOW = (
    ROOT / "src/latent_art_bench/painter_distribution_study_v1/measurement.py"
).is_file()
LOCAL_ONLY = pytest.mark.skipif(
    not LOCAL_WORKFLOW, reason="Maintainer-only terminal workflow dependencies are excluded"
)
SPEC = importlib.util.spec_from_file_location(
    "clause_release_adapter", ROOT / "tools/paper_clause_release.py"
)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


def _git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def _put(root, path, value, *, raw=False):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(value if raw else release.encoded(value))


def _terminal_records(root, requests, rows, inputs, config, collection):
    from latent_art_bench.painter_clause_validation_v1 import analysis

    collection = copy.deepcopy(collection)
    collection["freeze_sha256"] = release.digest(
        (root / f"{release.ORIGINAL}/freeze.json").read_bytes()
    )
    expected = analysis.analyze(requests, rows, inputs, config, collection_receipt=collection)
    _put(root, f"{release.ORIGINAL}/collection_receipt.json", collection)
    _put(root, f"{release.REPORT}/analysis.json", expected)
    _put(root, f"{release.REPORT}/REPORT.md", analysis.report_text(expected).encode(), raw=True)
    _put(
        root,
        f"{release.ORIGINAL}/measurements.jsonl",
        b"".join((json.dumps(r) + "\n").encode() for r in rows),
        raw=True,
    )
    marker = f"research_workspace/{release.STUDY}/{release.RUN}/measurement_started.json"
    _put(root, marker, dict(synthetic=True))
    measured_paths = [
        f"{release.ORIGINAL}/measurements.jsonl",
        f"{release.REPORT}/analysis.json",
        f"{release.REPORT}/REPORT.md",
        marker,
    ]
    _put(
        root,
        f"{release.ORIGINAL}/measurement_receipt.json",
        dict(
            schema="painter-clause-validation-measurement/1",
            run_id=release.RUN,
            collection_receipt_sha256=release.digest(
                (root / f"{release.ORIGINAL}/collection_receipt.json").read_bytes()
            ),
            outputs=[
                dict(path=p, sha256=release.digest((root / p).read_bytes())) for p in measured_paths
            ],
        ),
    )
    return collection, expected


@pytest.fixture(scope="module")
def synthetic_export(tmp_path_factory):
    """Fresh artificial references/training/outcomes, with the actual frozen design."""
    from latent_art_bench.painter_clause_validation_v1 import analysis, common
    from latent_art_bench.painter_naming_geometry_v1.geometry import fit_map

    root = tmp_path_factory.mktemp("clause-maintainer")
    for path in release.CORE:
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
    rng = np.random.default_rng(94122)
    inputs = dict(
        schema="painter-clause-validation-inputs/1",
        targets={},
        reference={},
        original={},
        maps={},
        scalers={},
    )
    counts = {
        "claude_monet": dict(water=21, built=4, land=13),
        "paul_cezanne": dict(water=3, built=11, land=18),
    }
    for pipeline in common.PIPELINES:
        inputs["reference"][pipeline], inputs["maps"][pipeline] = {}, {}
        inputs["original"][pipeline] = {"oauth_gpt_image_2": {}}
        inputs["scalers"][pipeline] = dict(scaler=dict(center=[0.0] * 31, scale=[1.0] * 31))
        for painter, masses in counts.items():
            count = sum(masses.values())
            inputs["targets"][painter] = {key: value / count for key, value in masses.items()}
            inputs["reference"][pipeline][painter] = dict(
                ids=[f"synthetic-{painter}-{i}" for i in range(count)],
                values=rng.normal(size=(count, 31)).tolist(),
            )
            free = rng.normal(size=(24, 3, 31))
            named = 0.7 * free + 0.3
            classes = [c for c in common.CLASSES for _ in range(8)]
            inputs["original"][pipeline]["oauth_gpt_image_2"][painter] = dict(
                scene_ids=[f"old-synthetic-{i}" for i in range(24)],
                classes=classes,
                repeat_ids=[0, 1, 2],
                free=free.tolist(),
                named=named.tolist(),
            )
            weights = np.repeat([inputs["targets"][painter][c] / 24 for c in classes], 3)
            inputs["maps"][pipeline][painter] = fit_map(
                free.reshape(-1, 31), named.reshape(-1, 31), weights
            )
    _put(root, f"{release.DESIGN}/inputs.json", inputs)
    config, requests = common.configuration(root), common.requests(root)
    rows = []
    for request in requests:
        for pipeline in common.PIPELINES:
            x = rng.normal(size=31).tolist()
            rows.append(
                dict(
                    {key: value for key, value in request.items() if key != "payload"},
                    pipeline=pipeline,
                    status="measured",
                    values=x,
                    scaled=x,
                    source_response_path="/private/omitted-response.json",
                    response_headers={"authorization": "omitted"},
                    observed=dict(
                        width=768,
                        height=1024,
                        format="PNG",
                        reported=dict(quality="low"),
                        image_sha256="a" * 64,
                    ),
                )
            )
    complete_rows = copy.deepcopy(rows)
    # Missing all three pipelines for one generic output must withhold both endpoints.
    missing = next(r["request_id"] for r in requests if r["arm"] == "generic")
    for row in rows:
        if row["request_id"] == missing:
            row.update(status="refused", values=None, scaled=None, observed=None)
    collection = dict(
        schema="painter-clause-validation-collection/1",
        run_id=release.RUN,
        planned=288,
        duration_contract_met=True,
        identity_contract_met=True,
        status="complete",
        reason=None,
        budget=dict(accounted_usd=50.7219185),
        outputs=[
            dict(
                path=f"research_workspace/{release.STUDY}/{release.RUN}/collection_started.json",
                sha256="b" * 64,
            )
        ],
    )
    expected = analysis.analyze(requests, rows, inputs, config, collection_receipt=collection)
    _put(root, f"{release.ORIGINAL}/collection_receipt.json", collection)
    _put(root, f"{release.ORIGINAL}/measurement_receipt.json", {"synthetic": True})
    _put(root, f"{release.REPORT}/analysis.json", expected)
    _put(root, f"{release.REPORT}/REPORT.md", analysis.report_text(expected).encode(), raw=True)
    _put(
        root,
        f"{release.ORIGINAL}/planned_requests.jsonl",
        b"".join((json.dumps(r) + "\n").encode() for r in requests),
        raw=True,
    )
    _put(
        root,
        f"{release.ORIGINAL}/measurements.jsonl",
        b"".join((json.dumps(r) + "\n").encode() for r in rows),
        raw=True,
    )
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "Offline Fixture")
    _git(root, "config", "user.email", "offline@example.invalid")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "synthetic sources and results")
    commit = _git(root, "rev-parse", "HEAD")
    frozen = {
        p: release.digest((root / p).read_bytes()) for p in release.CORE - release.NOT_FREEZE_BOUND
    }
    freeze = dict(
        inputs=[dict(path=p, sha256=s) for p, s in frozen.items()],
        recorded_git_commit=commit,
        qualified_source_commit=commit,
        proxy_snapshot={"private_example": "/private/excluded/proxy"},
        environment={"python": sys.version.split()[0]},
    )
    _put(root, f"{release.ORIGINAL}/freeze.json", freeze)
    collection, expected = _terminal_records(root, requests, rows, inputs, config, collection)
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "synthetic terminal receipt bindings")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            release, "terminal_inputs", lambda selected: (freeze, requests, rows, collection)
        )
        result = release.export(root, "synthetic-clause")
    assert result["rows"] == 864
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "create-once synthetic export")
    return SimpleNamespace(
        root=root,
        release_id="synthetic-clause",
        expected=expected,
        rows=rows,
        requests=requests,
        collection=collection,
        freeze=freeze,
        complete_rows=complete_rows,
        inputs=inputs,
        config=config,
    )


@pytest.fixture(scope="module")
def built_template(synthetic_export, tmp_path_factory):
    output = tmp_path_factory.mktemp("clause-built-template")
    value = release.build(synthetic_export.root, output, synthetic_export.release_id)
    return Path(value["stage"])


@pytest.fixture
def stage(built_template, tmp_path):
    target = tmp_path / built_template.name
    shutil.copytree(built_template, target)
    for suffix in (".tar.gz", ".tar.gz.sha256"):
        shutil.copyfile(built_template.with_suffix(suffix), target.with_suffix(suffix))
    return target


@pytest.mark.parametrize(
    "path",
    [
        "/absolute",
        "../outside",
        "a/../b",
        "a//b",
        "a/./b",
        "a\\b",
        ".git/config",
        ".env",
        "a/.env.local",
        "raw/images.json",
        "paper/paper_ko.tex",
        "한국어.md",
    ],
)
def test_rejects_unsafe_or_private_paths(path):
    with pytest.raises(ValueError):
        release.portable(path)


@pytest.mark.parametrize(
    "value",
    [
        {"path": "/Users/example/image.png"},
        {"api_key": "placeholder"},
        {"nested": {"refresh_token": "placeholder"}},
        {"url": "https://name:secret@example.invalid"},
        {"data": [{"b64_json": "pixels"}]},
        {"message": "Bearer " + "x" * 30},
    ],
)
def test_sensitive_metadata_rejected_without_echo(value):
    with pytest.raises(ValueError) as error:
        release.screen(release.encoded(value), ".json")
    assert "placeholder" not in str(error.value)


def test_projection_drops_private_fields_but_preserves_missingness_delivery(synthetic_export):
    bundle = release.read(
        synthetic_export.root, f"{release.DATA}/{synthetic_export.release_id}/inputs.json"
    )
    assert bundle["requests"] == synthetic_export.requests
    assert bundle["collection"] == synthetic_export.collection
    assert len(bundle["rows"]) == 864
    assert sum(row["status"] == "refused" for row in bundle["rows"]) == 3
    assert all(set(row) == set(release.ROW_FIELDS) | {"observed"} for row in bundle["rows"])
    text = release.encoded(bundle).decode()
    assert "omitted-response" not in text and "response_headers" not in text
    assert "image_sha256" not in text and "768" in text
    assert all(
        row["status"] == "withheld_incomplete_allocated_grid"
        for row in synthetic_export.expected["primary"]
    )


def test_build_exact_allowlist_history_free_deterministic_archive(stage, synthetic_export):
    result = release.verify(stage)
    assert result["raw_response_authentication"] is False
    files = {p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()}
    assert (
        files
        == release.CORE
        | release.ORIGINAL_OUTPUTS
        | release.export_paths(synthetic_export.release_id)
        | release.GENERATED
    )
    archive = stage.with_suffix(".tar.gz")
    with tarfile.open(archive) as tar:
        assert all(r.isfile() and r.mode == 0o644 and r.mtime == 0 for r in tar.getmembers())
        assert {r.name for r in tar.getmembers()} == {f"{stage.name}/{p}" for p in files}
    descriptor = release.read(stage, f"{release.DATA}/{stage.name}/export_manifest.json")
    assert "proxy_snapshot" not in descriptor
    assert len(descriptor["private_proxy_snapshot_sha256"]) == 64
    assert not any("/private/" in p for p in files)
    assert not (stage / "paper").exists() and not (stage / ".git").exists()


def test_create_once_export_and_build(synthetic_export, tmp_path):
    with pytest.raises(FileExistsError):
        release.export(synthetic_export.root, synthetic_export.release_id)
    release.build(synthetic_export.root, tmp_path, synthetic_export.release_id)
    with pytest.raises(FileExistsError):
        release.build(synthetic_export.root, tmp_path, synthetic_export.release_id)


def test_verify_detects_payload_tampering(stage):
    path = stage / f"{release.DESIGN}/scenes.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="hash differs"):
        release.verify(stage)


@pytest.mark.parametrize("extra", ["extra.txt", ".env", ".git/config", "paper/paper_ko.tex"])
def test_verify_rejects_unlisted_files(stage, extra):
    _put(stage, extra, b"excluded", raw=True)
    with pytest.raises(ValueError, match="unlisted"):
        release.verify(stage)


def test_verify_rejects_symlink_payload_and_parent(stage, tmp_path):
    path = stage / "LICENSE"
    data = path.read_bytes()
    path.unlink()
    external = tmp_path / "outside-license"
    external.write_bytes(data)
    path.symlink_to(external)
    with pytest.raises(ValueError, match="symlink"):
        release.verify(stage)
    linked = tmp_path / "linked-stage"
    linked.symlink_to(stage, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        release.verify(linked)


def test_gather_cannot_expand_export_allowlist(stage):
    path = stage / f"{release.DATA}/{stage.name}/export_manifest.json"
    value = json.loads(path.read_text())
    value["files"]["unlisted.json"] = "a" * 64
    path.write_bytes(release.encoded(value))
    with pytest.raises(ValueError, match="allowlist"):
        release.gather(stage, stage.name)


def test_final_build_requires_committed_export_and_index_bytes(synthetic_export, tmp_path):
    root = tmp_path / "maintainer"
    shutil.copytree(synthetic_export.root, root)
    path = root / f"{release.DATA}/{synthetic_export.release_id}/export_manifest.json"
    original = path.read_bytes()
    path.write_bytes(original + b" ")
    with pytest.raises(ValueError, match="working/index"):
        release.build(root, tmp_path / "out1", synthetic_export.release_id)
    _git(root, "add", str(path.relative_to(root)))
    path.write_bytes(original)
    with pytest.raises(ValueError, match="working/index"):
        release.build(root, tmp_path / "out2", synthetic_export.release_id)


def test_draft_still_checks_scientific_hashes(synthetic_export, tmp_path):
    root = tmp_path / "maintainer"
    shutil.copytree(synthetic_export.root, root)
    path = root / f"{release.DESIGN}/inputs.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="hash differs"):
        release.build(root, tmp_path / "out", synthetic_export.release_id, draft=True)


def test_check_rejects_cached_foreign_source(stage, monkeypatch):
    monkeypatch.setitem(sys.modules, "latent_art_bench.foreign", SimpleNamespace(__file__=__file__))
    with pytest.raises(ValueError, match="outside the release"):
        release.check(stage)


def _isolated_check(stage, tmp_path):
    script = """
import importlib.util, json, pathlib, sys
root = pathlib.Path(sys.argv[1])
def guard(event, args):
    if event.startswith("socket.") or event == "subprocess.Popen":
        raise RuntimeError("public replay attempted network or subprocess")
sys.addaudithook(guard)
spec = importlib.util.spec_from_file_location(
    "public_adapter", root / "tools/paper_clause_release.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
result = module.check(root)
for name, value in sys.modules.items():
    if name == "latent_art_bench" or name.startswith("latent_art_bench."):
        assert pathlib.Path(value.__file__).resolve().is_relative_to((root / "src").resolve()), name
assert "latent_art_bench.painter_clause_validation_v1.workflow" not in sys.modules
assert "latent_art_bench.painter_clause_validation_v1.collection" not in sys.modules
print(json.dumps(result))
"""
    environment = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(stage)],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value["status"] == "exact_numeric_and_report_replay"
    assert (value["planned"], value["primary_endpoints"], value["views"]) == (288, 2, 6)
    assert value["raw_response_authentication"] is False
    assert not (stage / ".git").exists() and not (stage / "research_workspace").exists()
    return value


def test_fresh_public_replay_uses_only_copied_source_without_network_or_git(stage, tmp_path):
    _isolated_check(stage, tmp_path)


def test_complete_primary_contributions_pvalues_holm_replay_in_isolation(
    synthetic_export, tmp_path, monkeypatch
):
    root = tmp_path / "complete-maintainer"
    shutil.copytree(synthetic_export.root, root)
    collection, expected = _terminal_records(
        root,
        synthetic_export.requests,
        synthetic_export.complete_rows,
        synthetic_export.inputs,
        synthetic_export.config,
        synthetic_export.collection,
    )
    assert all(
        row["status"] == "available"
        and len(row["contributions"]) == 72
        and row["raw_p"] is not None
        and row["holm_p"] is not None
        for row in expected["primary"]
    )
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "complete artificial terminal results")
    monkeypatch.setattr(
        release,
        "terminal_inputs",
        lambda selected: (
            synthetic_export.freeze,
            synthetic_export.requests,
            synthetic_export.complete_rows,
            collection,
        ),
    )
    release.export(root, "complete-synthetic")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "complete artificial numerical export")
    built = release.build(root, tmp_path / "complete-package", "complete-synthetic")
    checked = _isolated_check(Path(built["stage"]), tmp_path)
    assert checked["numerical_sha256"] == release.digest(release.encoded(expected))


def test_stdlib_verify_before_install(stage, tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            str(stage / "tools/paper_clause_release.py"),
            "verify",
            "--root",
            str(stage),
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "verified"


@LOCAL_ONLY
def test_terminal_export_refuses_pending_study_without_creating_output(tmp_path):
    with pytest.raises((ValueError, FileNotFoundError)):
        release.export(tmp_path, "not-terminal")
    assert not (tmp_path / release.DATA).exists()


@pytest.mark.parametrize("mutation", [None, "missing_output", "altered_binding", "collection_hash"])
@LOCAL_ONLY
def test_terminal_input_receipt_inventory_and_hashes(
    synthetic_export, tmp_path, monkeypatch, mutation
):
    from latent_art_bench.painter_clause_validation_v1 import workflow

    root = tmp_path / "local-terminal"
    shutil.copytree(synthetic_export.root, root)
    monkeypatch.setattr(
        workflow,
        "collection_inputs",
        lambda selected, run: (
            synthetic_export.freeze,
            synthetic_export.requests,
            [],
            {},
            synthetic_export.collection,
        ),
    )
    path = root / f"{release.ORIGINAL}/measurement_receipt.json"
    receipt = json.loads(path.read_text())
    if mutation == "missing_output":
        receipt["outputs"].pop()
    elif mutation == "altered_binding":
        receipt["outputs"][0]["sha256"] = "0" * 64
    elif mutation == "collection_hash":
        receipt["collection_receipt_sha256"] = "0" * 64
    path.write_bytes(release.encoded(receipt))
    if mutation is None:
        assert len(release.terminal_inputs(root)[2]) == 864
    else:
        with pytest.raises(ValueError, match="receipt|output hash"):
            release.terminal_inputs(root)


def test_row_projection_is_exactly_consumed_fields(synthetic_export):
    rows = copy.deepcopy(synthetic_export.rows)
    before = copy.deepcopy(release.project_rows(rows))
    rows[0]["ignored_extra"] = {"secret": "not exported"}
    assert release.project_rows(rows) == before
    rows[0]["scaled"][0] += 1
    assert release.project_rows(rows) != before
