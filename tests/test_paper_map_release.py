"""Synthetic archive/provenance/replay tests; no scientific qualification writer."""

import copy
import importlib.util
import json
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "map_release_adapter", ROOT / "tools/paper_map_release.py"
)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


def put(root, path, raw):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, text=True).strip()


def artificial_qualification():
    records = [
        dict(
            R=r,
            shape=sh,
            mean=m,
            regime=rg,
            trials=10000,
            median_half_width=[0.1, 2.0],
            joint_covered=9900,
            coverage_lower=0.98,
            truth=dict(estimate=[0.3, -1.2]),
        )
        for r in (4, 6, 8)
        for sh in ("gaussian_shaped", "t5_shaped", "lognormal_shaped")
        for m in ("T1", "midpoint", "T2")
        for rg in ("baseline", "high_positive", "low_negative")
    ]
    return dict(
        records=records,
        decision="stop_inferential_proposal",
        selected_R=None,
        selected_outputs=None,
        allocations=[dict(R=r, qualified=False) for r in (4, 6, 8)],
    )


@pytest.fixture
def source(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    for p in release.CORE | release.OMITTED:
        if p.startswith(release.RESULT + "/"):
            continue
        raw = b"{}\n" if p.endswith(".json") else b"# Synthetic fixture\n"
        if p in (release.TOOL, "tests/test_paper_map_release.py"):
            raw = (ROOT / p).read_bytes()
        put(root, p, raw)
    q = artificial_qualification()
    put(root, f"{release.GEOMETRY}/inputs.json", release.encoded(dict(qualification=q)))
    code = f'''import json
from pathlib import Path

def load_proxy(root):
    return json.loads((Path(root)/"{release.GEOMETRY}/inputs.json").read_text())

def qualify(proxy):
    return proxy["qualification"]

def report(value):
    return "Synthetic terminal report\\n"

def build(root):
    raise AssertionError("scientific writer must never be called")
'''
    put(root, f"{release.SCIENCE}/precision.py", code.encode())
    put(root, f"{release.STUDY}/DESIGN.md", b"Private current credit balance $123.45\n")
    put(root, f"{release.GEOMETRY}/freeze.json", b'{"api_key":"private-fixture"}\n')
    git(root, "init")
    git(root, "config", "user.email", "test@example.invalid")
    git(root, "config", "user.name", "Test")
    git(root, "add", ".")
    git(root, "commit", "-m", "synthetic source")
    source_commit = git(root, "rev-parse", "HEAD")
    run = dict(
        schema="painter-map-precision-run/1",
        source_commit=source_commit,
        source_bindings=[
            dict(path=p, sha256=release.digest((root / p).read_bytes()))
            for p in sorted(release.INCLUDED_BOUND | release.OMITTED)
        ],
        environment=dict(python="3.13.11", numpy="synthetic", scipy="synthetic"),
    )
    put(root, f"{release.RESULT}/RUN.json", release.encoded(run))
    put(
        root,
        f"{release.RESULT}/precision.json",
        release.encoded(dict(run, proxy_scene_ids=["synthetic"], qualification=q)),
    )
    put(root, f"{release.RESULT}/PRECISION.md", b"Synthetic terminal report\n")
    git(root, "add", ".")
    git(root, "commit", "-m", "synthetic terminal result")
    return root


def bundle(source, tmp_path, name="pmrv1-test"):
    return release.build(source, tmp_path / "output", name)


@pytest.mark.parametrize(
    "path",
    [
        "/tmp/x",
        "../x",
        "a/../../x",
        "a//b",
        "a/./b",
        ".env",
        ".env.old",
        ".git/config",
        "raw/images",
        "x/paper_ko.tex",
        "x/credentials.json",
        "한글.tex",
        "a\\b",
    ],
)
def test_unsafe_paths_rejected(path):
    with pytest.raises(ValueError):
        release.portable(path)


@pytest.mark.parametrize(
    "value",
    [
        {"api_key": "x"},
        {"location": "/Users/person/file"},
        {"secret": "Bearer " + "x" * 30},
        {"x": "data:image/png;base64,a"},
    ],
)
def test_sensitive_metadata_rejected(value):
    with pytest.raises(ValueError):
        release.screen(release.encoded(value), ".json")


def test_final_bundle_exact_inventory_omissions_and_create_once(source, tmp_path):
    result = bundle(source, tmp_path)
    stage = Path(result["stage"])
    assert result["payload_files"] == 18
    assert release.verify(stage)["files"] == 18
    for path in release.OMITTED:
        assert not (stage / path).exists()
    raw = b"".join(p.read_bytes() for p in stage.rglob("*") if p.is_file())
    assert (source / f"{release.STUDY}/DESIGN.md").read_bytes() not in raw
    assert (source / f"{release.GEOMETRY}/freeze.json").read_bytes() not in raw
    with tarfile.open(result["archive"]) as tar:
        members = tar.getmembers()
        assert len(members) == 18 and all(m.isfile() for m in members)
        assert all(m.mode == 0o644 and m.mtime == 0 for m in members)
        assert all(m.name.startswith("pmrv1-test/") for m in members)
    archive = Path(result["archive"])
    assert (
        Path(result["checksum"]).read_text()
        == f"{release.digest(archive.read_bytes())}  {archive.name}\n"
    )
    with pytest.raises(FileExistsError):
        bundle(source, tmp_path)


def test_dirty_build_and_historical_binding_mutation_rejected(source, tmp_path):
    (source / "LICENSE").write_text("new bytes")
    with pytest.raises(ValueError, match="commit working"):
        bundle(source, tmp_path)
    (source / f"{release.STUDY}/DESIGN.md").write_text("changed private bytes")
    with pytest.raises(ValueError, match="historical source"):
        release.build(source, tmp_path / "draft", "draft", draft=True)


def test_symlink_source_and_output_rejected(source, tmp_path):
    target = source / "LICENSE"
    raw = target.read_bytes()
    external = tmp_path / "external"
    external.write_bytes(raw)
    target.unlink()
    target.symlink_to(external)
    with pytest.raises(ValueError, match="symlink"):
        bundle(source, tmp_path)
    target.unlink()
    target.write_bytes(raw)
    linked = tmp_path / "linked"
    linked.symlink_to(source, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        release.build(source, linked, "bad")


@pytest.mark.parametrize("mutation", ["extra", "tamper", "missing", "symlink"])
def test_verify_rejects_unlisted_changed_missing_and_symlink_files(source, tmp_path, mutation):
    result = bundle(source, tmp_path)
    stage = Path(result["stage"])
    if mutation == "extra":
        (stage / "unexpected.txt").write_text("extra")
    elif mutation == "tamper":
        (stage / f"{release.GEOMETRY}/inputs.json").write_text("{}")
    elif mutation == "missing":
        (stage / "LICENSE").unlink()
    else:
        (stage / "unlisted").symlink_to(tmp_path)
    with pytest.raises(ValueError):
        release.verify(stage)


def test_binding_inventory_duplicate_omitted_and_report_identity_rejected(source):
    files, _, _ = release.gather(source)
    original = json.loads(files[f"{release.RESULT}/RUN.json"])
    for records in (original["source_bindings"][:-1], original["source_bindings"] * 2):
        changed = dict(original, source_bindings=records)
        bad = dict(files)
        bad[f"{release.RESULT}/RUN.json"] = release.encoded(changed)
        value = json.loads(bad[f"{release.RESULT}/precision.json"])
        value.update(changed)
        bad[f"{release.RESULT}/precision.json"] = release.encoded(value)
        with pytest.raises(ValueError):
            release.validate_science(bad)


def test_complete_comparison_exact_discrete_leaves_and_float_contract():
    expected = artificial_qualification()
    small = copy.deepcopy(expected)
    small["records"][-1]["truth"]["estimate"][0] += 1e-12
    assert release.compare(small, expected)
    small["records"][-1]["truth"]["estimate"][0] += 1e-7
    assert not release.compare(small, expected)
    for path, value in [("joint_covered", 9900.0), ("trials", True), ("mean", "different")]:
        bad = copy.deepcopy(expected)
        bad["records"][-1][path] = value
        assert not release.compare(bad, expected)
    for actual in (float("nan"), float("inf"), True):
        assert not release.compare(actual, 1.0)
    assert not release.compare({}, expected)


def isolated(stage, command):
    return subprocess.run(
        [sys.executable, "-I", "-c", command, str(stage)], capture_output=True, text=True
    )


def test_stdlib_verify_and_isolated_public_replay_without_private_state(source, tmp_path):
    result = bundle(source, tmp_path)
    stage = Path(result["stage"])
    code = """import importlib.util,sys
sys.dont_write_bytecode=True
from pathlib import Path
root=Path(sys.argv[1])
def audit(event,args):
    if event.startswith('socket.') or event=='subprocess.Popen':
        raise AssertionError('public replay cannot use network or subprocess')
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=str(args[0])
        if '/.git/' in p or p.endswith('/DESIGN.md') or '/painter_map_validation_v1/metadata/' in p:
            raise AssertionError('private operational state must not be read')
sys.addaudithook(audit)
spec=importlib.util.spec_from_file_location('adapter',root/'tools/paper_map_release.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.verify(root)
assert 'numpy' not in sys.modules and 'scipy' not in sys.modules
result=m.check(root)
assert result['cells']==81 and result['exact_values']
assert result['decision']=='stop_inferential_proposal'
for name,mod in sys.modules.copy().items():
    if name=='latent_art_bench' or name.startswith('latent_art_bench.'):
        assert Path(mod.__file__).resolve().is_relative_to(root/'src')
print('isolated replay passed')
"""
    before_install = subprocess.run(
        [sys.executable, "-I", "-S", str(stage / release.TOOL), "verify", "--root", str(stage)],
        capture_output=True,
        text=True,
    )
    assert before_install.returncode == 0, before_install.stderr
    assert json.loads(before_install.stdout)["files"] == 18
    value = isolated(stage, code)
    assert value.returncode == 0, value.stderr
    assert "isolated replay passed" in value.stdout
    # Numeric replay must not create, replace or alter the retained scientific result.
    assert (stage / f"{release.RESULT}/precision.json").read_bytes() == (
        source / f"{release.RESULT}/precision.json"
    ).read_bytes()


def test_cached_external_scientific_module_rejected(tmp_path, monkeypatch):
    from types import SimpleNamespace

    monkeypatch.setitem(sys.modules, "latent_art_bench.outside", SimpleNamespace(__file__=__file__))
    with pytest.raises(ValueError, match="cached scientific"):
        release.require_local_modules(tmp_path)


@pytest.mark.parametrize("mutation", ["working", "head"])
def test_build_rechecks_source_after_writing_and_preserves_failed_output(
    source, tmp_path, monkeypatch, mutation
):
    original_write = release.write_new
    changed = []

    def mutate(path, raw):
        original_write(path, raw)
        if path.suffix == ".sha256" and not changed:
            changed.append(True)
            if mutation == "working":
                (source / "LICENSE").write_text("changed during writing")
            else:
                (source / "unrelated.txt").write_text("new commit")
                git(source, "add", ".")
                git(source, "commit", "-m", "concurrent artificial commit")

    monkeypatch.setattr(release, "write_new", mutate)
    with pytest.raises(ValueError, match="source changed"):
        bundle(source, tmp_path)
    assert (tmp_path / "output/pmrv1-test.tar.gz").is_file()
    with pytest.raises(FileExistsError):
        bundle(source, tmp_path)


def test_public_check_reverifies_inventory_after_numeric_work(source, tmp_path):
    stage = Path(bundle(source, tmp_path)["stage"])
    code = """import importlib.util,sys
sys.dont_write_bytecode=True
from pathlib import Path
root=Path(sys.argv[1]);sys.path.insert(0,str(root/'src'))
from latent_art_bench.painter_map_validation_v1 import precision
original=precision.qualify
def changed(proxy):
    (root/'unexpected.txt').write_text('mutation during replay')
    return original(proxy)
precision.qualify=changed
spec=importlib.util.spec_from_file_location('adapter',root/'tools/paper_map_release.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
try:
    m.check(root)
except ValueError as exc:
    assert 'unlisted' in str(exc)
else:
    raise AssertionError('post-replay verification must reject mutation')
"""
    value = isolated(stage, code)
    assert value.returncode == 0, value.stderr
