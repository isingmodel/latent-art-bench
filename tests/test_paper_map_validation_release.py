"""Synthetic terminal release tests; no new outcomes or formal qualification.

Known qualification records are copied unchanged, never re-simulated here. The
isolated replay tests replace only qualification computation with a sentinel;
the observed numerical analysis, fixed-input checks and package imports are real.
Actual 27-cell fresh replay remains a separate release-acceptance action.
"""

import copy
import importlib.util
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from latent_art_bench.painter_map_validation_v2 import analysis, common

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "map_validation_release", ROOT / "tools/paper_map_validation_release.py"
)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


def put(root, relative, raw):
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


@pytest.fixture
def synthetic_source(tmp_path, monkeypatch):
    return make_source(tmp_path, monkeypatch)


def make_source(tmp_path, monkeypatch):
    """Real numerical code/fixed inputs, artificial 240 observations and receipts."""
    source = tmp_path / "source"
    source.mkdir()
    for relative in release.CORE:
        path = ROOT / relative
        raw = (
            path.read_bytes()
            if path.is_file()
            else (b"{}\n" if relative.endswith(".json") else b"# Artificial pending review\n")
        )
        put(source, relative, raw)
    inputs = analysis.load_inputs(ROOT)
    put(source, f"{release.DESIGN}/inputs.json", release.base.encoded(inputs))
    config = common.configuration(ROOT)
    requests = common.build_plan(ROOT, config)
    rng = np.random.default_rng(823093)
    rows = []
    for request in requests:
        raw = rng.normal(size=31)
        rows.append(
            dict(
                {key: request[key] for key in ("request_id", *analysis.IDENTITY_FIELDS)},
                pipeline="primary512",
                status="measured",
                feature_names=list(analysis.NAMES),
                values=raw.tolist(),
                scaled=(
                    (raw - np.asarray(inputs["scaler"]["center"]))
                    / np.asarray(inputs["scaler"]["scale"])
                ).tolist(),
                observed=dict(width=1024, height=1024, private_provider_field="omitted"),
                source_response_path="research_workspace/private-responses/not-exported.json.gz",
            )
        )
    omitted = "studies/painter_map_validation_v2/private-preflight-note.md"
    put(source, omitted, b"Private current credit balance 123.456789 USD\n")
    git(source, "init")
    git(source, "config", "user.email", "test@example.invalid")
    git(source, "config", "user.name", "Test")
    git(source, "add", ".")
    git(source, "commit", "-m", "artificial source")
    commit = git(source, "rev-parse", "HEAD")
    qualified = json.loads((source / release.DESIGN / "qualification.json").read_text())
    fingerprints = release.base.binding_map(qualified["source_bindings"])
    fingerprints.update(
        {
            p: release.base.digest((source / p).read_bytes())
            for p in (release.CORE - release.UNBOUND) | {omitted}
        }
    )
    freeze = dict(
        recorded_git_commit=commit,
        qualified_source_commit=qualified["source_commit"],
        environment=dict(python="3.13.11", numpy=np.__version__, scipy="test-runtime"),
        inputs=[dict(path=p, sha256=sha) for p, sha in sorted(fingerprints.items())],
    )
    freeze["environment"].update(
        {k: "test-runtime" for k in ("Pillow", "httpx", "PyWavelets", "scikit-image")}
    )
    receipt = dict(
        schema="painter-map-validation-collection/2",
        run_id=release.RUN,
        analysis_eligible=True,
        analysis_unavailability_reasons=[],
        available_at_dispatch_usd="123.456789",
        budget=dict(private_account_value="excluded"),
    )

    def terminal(root):
        assert Path(root) == source
        return freeze, requests, rows, receipt

    def replay(root, bundle):
        value = analysis.analyze(
            requests,
            bundle["rows"],
            inputs,
            config,
            collection_receipt=bundle["collection_attestation"],
        )
        return value, analysis.report_text

    monkeypatch.setattr(release, "terminal_inputs", terminal)
    monkeypatch.setattr(release, "observed_replay", replay)
    return SimpleNamespace(
        root=source,
        requests=requests,
        rows=rows,
        inputs=inputs,
        config=config,
        freeze=freeze,
        receipt=receipt,
    )


def finish_terminal(source, state="complete"):
    if state == "missing":
        source.rows[-1].update(status="normalization_failed", values=None, scaled=None)
    elif state == "identity":
        source.receipt.update(
            analysis_eligible=False,
            analysis_unavailability_reasons=["identity_contract_unverified"],
        )
    root = source.root
    directory, report = release.ORIGINAL, release.REPORT
    put(root, f"{directory}/freeze.json", release.base.encoded(source.freeze))
    put(root, f"{directory}/collection_receipt.json", release.base.encoded(source.receipt))
    put(
        root,
        f"{directory}/planned_requests.jsonl",
        b"".join((json.dumps(row, sort_keys=True) + "\n").encode() for row in source.requests),
    )
    put(
        root,
        f"{directory}/measurements.jsonl",
        b"".join((json.dumps(row, sort_keys=True) + "\n").encode() for row in source.rows),
    )
    value = analysis.analyze(
        source.requests,
        source.rows,
        source.inputs,
        source.config,
        collection_receipt=source.receipt,
    )
    put(root, f"{report}/analysis.json", release.base.encoded(value))
    put(root, f"{report}/REPORT.md", analysis.report_text(value).encode())
    marker = f"research_workspace/{release.STUDY}/{release.RUN}/measurement_started.json"
    put(root, marker, b'{"one_shot":true}\n')
    receipt = dict(
        schema="painter-map-validation-measurement/2",
        run_id=release.RUN,
        collection_receipt_sha256=release.base.digest(
            (root / directory / "collection_receipt.json").read_bytes()
        ),
        outputs=[
            dict(path=p, sha256=release.base.digest((root / p).read_bytes()))
            for p in (
                f"{directory}/measurements.jsonl",
                f"{report}/analysis.json",
                f"{report}/REPORT.md",
                marker,
            )
        ],
    )
    put(root, f"{directory}/measurement_receipt.json", release.base.encoded(receipt))
    git(root, "add", ".")
    git(root, "commit", "-m", "artificial terminal result")
    return value


def staged(source, tmp_path, state="complete"):
    expected = finish_terminal(source, state)
    release.export(source.root)
    git(source.root, "add", ".")
    git(source.root, "commit", "-m", "artificial compact export")
    result = release.build(source.root, tmp_path / "output")
    return Path(result["stage"]), result, expected


@pytest.fixture(scope="module")
def complete_stage(tmp_path_factory):
    directory = tmp_path_factory.mktemp("map-release-complete")
    with pytest.MonkeyPatch.context() as patch:
        source = make_source(directory, patch)
        stage, _, _ = staged(source, directory)
    return stage


def test_create_once_explicit_payload_and_private_projection(synthetic_source, tmp_path):
    stage, result, _ = staged(synthetic_source, tmp_path)
    expected_files = release.CORE | release.OUTPUTS | release.EXPORTS | release.GENERATED
    assert release.verify(stage)["files"] == len(expected_files)
    with tarfile.open(result["archive"]) as tar:
        members = tar.getmembers()
        assert all(m.isfile() and m.mode == 0o644 and m.mtime == 0 for m in members)
        assert {m.name for m in members} == {f"{release.RELEASE_ID}/{p}" for p in expected_files}
    for private in (
        f"{release.ORIGINAL}/collection_receipt.json",
        f"{release.ORIGINAL}/measurements.jsonl",
        f"{release.ORIGINAL}/freeze.json",
        "studies/painter_map_validation_v1/DESIGN.md",
    ):
        assert not (stage / private).exists()
    payload = release.read(stage, f"{release.EXPORT}/inputs.json")
    assert len(payload["rows"]) == 240
    assert payload["collection_attestation"] == dict(
        analysis_eligible=True, analysis_unavailability_reasons=[]
    )
    assert all(set(row) == set(release.ROW_FIELDS) for row in payload["rows"])
    bytes_ = b"".join(p.read_bytes() for p in stage.rglob("*") if p.is_file() and p.suffix != ".py")
    assert b"123.456789" not in bytes_ and b"private_provider_field" not in bytes_
    with pytest.raises(FileExistsError):
        release.export(synthetic_source.root)
    with pytest.raises(FileExistsError):
        release.build(synthetic_source.root, tmp_path / "output")
    archive = Path(result["archive"])
    assert Path(result["checksum"]).read_text() == (
        f"{release.base.digest(archive.read_bytes())}  {archive.name}\n"
    )


@pytest.mark.parametrize("state", ["complete", "missing", "identity"])
def test_isolated_stdlib_verify_and_real_observed_replay(synthetic_source, tmp_path, state):
    stage, _, expected = staged(synthetic_source, tmp_path, state)
    before = subprocess.run(
        [sys.executable, "-I", "-S", str(stage / release.TOOL), "verify", "--root", str(stage)],
        capture_output=True,
        text=True,
    )
    assert before.returncode == 0, before.stderr
    assert json.loads(before.stdout)["files"] == len(
        release.CORE | release.OUTPUTS | release.EXPORTS | release.GENERATED
    )
    code = """import importlib.util,sys,json
from pathlib import Path
root=Path(sys.argv[1]);sys.dont_write_bytecode=True
def audit(event,args):
    if event.startswith('socket.') or event=='subprocess.Popen':
        raise AssertionError('public check must not use network or subprocess')
    if event=='open' and isinstance(args[0],(str,bytes)):
        name=str(args[0])
        if (any(part in name for part in (
                '/.git/', '/painter_map_validation_v2/metadata/', '/research_workspace/'))
                or name.endswith('/DESIGN.md')):
            raise AssertionError('private runtime state must remain absent')
sys.addaudithook(audit)
spec=importlib.util.spec_from_file_location('adapter',root/'tools/paper_map_validation_release.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.verify(root)
assert 'numpy' not in sys.modules and 'scipy' not in sys.modules
sys.path.insert(0,str(root/'src'))
from latent_art_bench.painter_map_validation_v2 import precision
# This test verifies integration only: never execute another formal 270k trials.
sentinel=object()
precision.v1.load_proxy=lambda path: sentinel
def qualification(proxy):
    assert proxy is sentinel
    return json.loads((root/m.QUALIFICATION/'precision.json').read_text())['qualification']
precision.qualify=qualification
def forbidden(*args,**kwargs):
    raise AssertionError('formal writer/old private provenance path forbidden')
precision.build=forbidden;precision.read_previous=forbidden;precision.v1.build=forbidden
result=m.check(root)
assert result['qualification_cells']==27 and result['qualification_exact']
assert result['observed_exact'] and not result['private_collection_authenticated']
assert not result['scientific_outputs_written']
for name,mod in sys.modules.copy().items():
    if name=='latent_art_bench' or name.startswith('latent_art_bench.'):
        assert Path(mod.__file__).resolve().is_relative_to(root/'src')
assert 'latent_art_bench.painter_map_validation_v2.workflow' not in sys.modules
assert 'latent_art_bench.painter_map_validation_v2.collection' not in sys.modules
print(json.dumps(result))
"""
    run = subprocess.run(
        [sys.executable, "-I", "-c", code, str(stage)], capture_output=True, text=True
    )
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)["observed_status"] == expected["status"]
    assert release.read(stage, f"{release.REPORT}/analysis.json") == expected


@pytest.mark.parametrize("mutation", ["extra", "missing", "tamper", "symlink"])
def test_exact_inventory_rejects_drift(complete_stage, tmp_path, mutation):
    stage = tmp_path / "stage"
    shutil.copytree(complete_stage, stage)
    if mutation == "extra":
        (stage / "extra.txt").write_text("unlisted")
    elif mutation == "missing":
        (stage / "LICENSE").unlink()
    elif mutation == "tamper":
        (stage / release.EXPORT / "inputs.json").write_text("{}")
    else:
        (stage / "unsafe").symlink_to(tmp_path)
    with pytest.raises(ValueError):
        release.verify(stage)


@pytest.mark.parametrize("private", ["/tmp/file", "../file", ".env", ".git/config", "paper_ko.tex"])
def test_private_and_unsafe_paths_rejected(private):
    with pytest.raises(ValueError):
        release.base.portable(private)


def test_jsonl_secrets_are_screened(tmp_path):
    put(tmp_path, "planned.jsonl", b'{"payload":{"api_key":"private"}}\n')
    with pytest.raises(ValueError, match="sensitive"):
        release.public_bytes(tmp_path, "planned.jsonl")


@pytest.mark.parametrize(
    "mutation", ["flag_type", "unknown_reason", "duplicate_reason", "extra_field"]
)
def test_collection_attestation_strictness(mutation):
    receipt = dict(analysis_eligible=False, analysis_unavailability_reasons=["collection_stopped"])
    if mutation == "flag_type":
        receipt["analysis_eligible"] = 0
    elif mutation == "unknown_reason":
        receipt["analysis_unavailability_reasons"] = ["new_reason"]
    elif mutation == "duplicate_reason":
        receipt["analysis_unavailability_reasons"] *= 2
    else:
        receipt.update(available_at_dispatch_usd="123.456789")
        assert release.collection_projection(receipt) == {
            "analysis_eligible": False,
            "analysis_unavailability_reasons": ["collection_stopped"],
        }
        return
    with pytest.raises(ValueError):
        release.collection_projection(receipt)


def test_dirty_source_and_changed_frozen_bytes_rejected(synthetic_source):
    finish_terminal(synthetic_source)
    (synthetic_source.root / "LICENSE").write_text("uncommitted")
    with pytest.raises(ValueError, match="commit working"):
        release.export(synthetic_source.root)
    (synthetic_source.root / f"src/latent_art_bench/{release.STUDY}/analysis.py").write_text(
        "changed"
    )
    with pytest.raises(ValueError, match="frozen scientific"):
        release.export(synthetic_source.root)


def test_export_rejects_nonexact_compact_replay(synthetic_source, monkeypatch):
    finish_terminal(synthetic_source)
    original = release.observed_replay

    def wrong(root, bundle):
        value, report = original(root, bundle)
        value["primary"][0]["estimate"] += 1e-12
        return value, report

    monkeypatch.setattr(release, "observed_replay", wrong)
    with pytest.raises(ValueError, match="exact unchanged"):
        release.export(synthetic_source.root)
    assert not (synthetic_source.root / release.EXPORT).exists()


def test_terminal_measurement_receipt_inventory_and_collection_binding(
    synthetic_source,
    monkeypatch,
):
    finish_terminal(synthetic_source)
    # Call the real adapter gate with only the private workflow verifier stubbed.
    original = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(original)
    monkeypatch.setattr(original, "numerical_modules", lambda root: ())
    monkeypatch.setitem(
        sys.modules,
        f"latent_art_bench.{release.STUDY}.workflow",
        SimpleNamespace(
            collection_inputs=lambda root, run: (
                synthetic_source.freeze,
                synthetic_source.requests,
                [],
                {},
                synthetic_source.receipt,
            )
        ),
    )
    path = synthetic_source.root / release.ORIGINAL / "measurement_receipt.json"
    valid = json.loads(path.read_text())
    assert len(original.terminal_inputs(synthetic_source.root)[2]) == 240
    for mutation in ("empty", "missing", "duplicate", "collection_hash"):
        changed = copy.deepcopy(valid)
        if mutation == "empty":
            changed["outputs"] = []
        elif mutation == "missing":
            changed["outputs"].pop()
        elif mutation == "duplicate":
            changed["outputs"][-1] = changed["outputs"][0]
        else:
            changed["collection_receipt_sha256"] = "0" * 64
        path.write_bytes(release.base.encoded(changed))
        with pytest.raises(ValueError):
            original.terminal_inputs(synthetic_source.root)


def test_stdlib_lineage_rejects_altered_qualification_and_extra_private_descriptor(
    complete_stage,
    tmp_path,
):
    stage = tmp_path / "stage"
    shutil.copytree(complete_stage, stage)
    files, _ = release.gather(stage)
    changed = dict(files)
    path = f"{release.QUALIFICATION}/precision.json"
    value = json.loads(changed[path])
    value["qualification"]["records"].pop()
    changed[path] = release.base.encoded(value)
    with pytest.raises(ValueError, match="complete passing"):
        release.validate_qualification(changed)
    path = stage / release.EXPORT / "export_manifest.json"
    value = json.loads(path.read_text())
    value["available_at_dispatch_usd"] = "123.456789"
    path.write_bytes(release.base.encoded(value))
    with pytest.raises(ValueError, match="fixed export identity"):
        release.gather(stage)


def test_cached_foreign_scientific_module_rejected(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "latent_art_bench.outside", SimpleNamespace(__file__=__file__))
    with pytest.raises(ValueError, match="cached scientific"):
        release.numerical_modules(tmp_path)


@pytest.mark.parametrize("mutation", ["working_source", "private_terminal"])
def test_build_detects_late_mutation_and_preserves_failed_outputs(
    synthetic_source,
    tmp_path,
    monkeypatch,
    mutation,
):
    finish_terminal(synthetic_source)
    release.export(synthetic_source.root)
    git(synthetic_source.root, "add", ".")
    git(synthetic_source.root, "commit", "-m", "artificial exported inputs")
    original_write = release.base.write_new

    def write_then_mutate(path, raw):
        original_write(path, raw)
        if path.suffix == ".sha256":
            if mutation == "working_source":
                (synthetic_source.root / "LICENSE").write_text("concurrent source change")
            else:
                synthetic_source.receipt["analysis_eligible"] = False
                synthetic_source.receipt["analysis_unavailability_reasons"] = ["collection_stopped"]

    monkeypatch.setattr(release.base, "write_new", write_then_mutate)
    with pytest.raises(ValueError, match="source|terminal"):
        release.build(synthetic_source.root, tmp_path / "output")
    assert (tmp_path / "output" / f"{release.RELEASE_ID}.tar.gz").is_file()
    with pytest.raises(FileExistsError):
        release.build(synthetic_source.root, tmp_path / "output")


def test_public_check_reverifies_inventory_after_numerical_work(complete_stage, tmp_path):
    stage = tmp_path / "stage"
    shutil.copytree(complete_stage, stage)
    code = """import importlib.util,json,sys
from pathlib import Path
root=Path(sys.argv[1]);sys.dont_write_bytecode=True;sys.path.insert(0,str(root/'src'))
spec=importlib.util.spec_from_file_location('adapter',root/'tools/paper_map_validation_release.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
from latent_art_bench.painter_map_validation_v2 import precision
precision.v1.load_proxy=lambda root: None
def changed(proxy):
    (root/'unlisted.txt').write_text('mutation during numerical replay')
    return json.loads((root/m.QUALIFICATION/'precision.json').read_text())['qualification']
precision.qualify=changed
try:
    m.check(root)
except ValueError as exc:
    assert 'unlisted' in str(exc)
else:
    raise AssertionError('post-replay inventory check must reject mutation')
"""
    value = subprocess.run(
        [sys.executable, "-I", "-c", code, str(stage)], capture_output=True, text=True
    )
    assert value.returncode == 0, value.stderr


def test_public_runtime_cannot_include_private_account_fields(complete_stage, tmp_path):
    stage = tmp_path / "stage"
    shutil.copytree(complete_stage, stage)
    path = stage / release.EXPORT / "export_manifest.json"
    value = json.loads(path.read_text())
    value["freeze_environment"]["available_at_dispatch_usd"] = "123.456789"
    path.write_bytes(release.base.encoded(value))
    with pytest.raises(ValueError, match="runtime fields"):
        release.gather(stage)


@pytest.mark.parametrize("mutation", ["qualified_commit", "omitted_fingerprint"])
def test_transitive_provenance_cannot_disagree(complete_stage, tmp_path, mutation):
    stage = tmp_path / "stage"
    shutil.copytree(complete_stage, stage)
    path = stage / release.EXPORT / "export_manifest.json"
    value = json.loads(path.read_text())
    if mutation == "qualified_commit":
        value["qualified_source_commit"] = "0" * 40
    else:
        value["frozen_input_bindings"]["studies/painter_map_validation_v1/DESIGN.md"] = "0" * 64
    path.write_bytes(release.base.encoded(value))
    with pytest.raises(ValueError, match="qualification source|transitive"):
        release.gather(stage)
