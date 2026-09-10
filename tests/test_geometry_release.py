"""History-free addendum boundaries on small synthetic frozen studies only."""

import hashlib
import importlib.util
import json
import subprocess
import tarfile
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "paper_geometry_release",
    Path(__file__).resolve().parents[1] / "tools/paper_geometry_release.py")
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)
GEO, CENTER = release.NAMESPACES


def put(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else release.encoded(value)
    target.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def git(root, *args):
    return subprocess.check_output(
        ["git", *args], cwd=root, stderr=subprocess.DEVNULL).decode().strip()


def commit(root):
    git(root, "add", ".")
    git(root, "-c", "user.name=Local test", "-c", "user.email=test@example.invalid",
        "commit", "-qm", "synthetic fixture")
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def tree(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    git(root, "init", "-q")
    for path in release.CORE:
        raw = b"%PDF-synthetic\n" if path.endswith(".pdf") else b"synthetic public text\n"
        put(root, path, raw)
    put(root, "paper/paper.tex", "\n".join(
        f"\\includegraphics[width=\\linewidth]{{{name}}}" for name in release.FIGURES).encode())
    for name in release.NAMESPACES:
        for file in ("__init__", "__main__", "analysis"):
            put(root, f"src/latent_art_bench/{name}/{file}.py", b"# synthetic source\n")
        put(root, f"tests/{name}/test_analysis.py", b"# synthetic tests\n")
        put(root, f"studies/{name}/PROTOCOL.md", b"Synthetic protocol. No collection.\n")
    inputs = f"data/manifests/{GEO}/g1/inputs.json"
    put(root, inputs, {"values": [[1, 2]], "origins": {"historical/archive.json": "a" * 64}})
    source_commit = commit(root)

    def terminal(name, run, bound, source):
        directory = f"data/manifests/{name}/{run}"
        paths = [*bound, "pyproject.toml", "uv.lock"]
        paths += [f"src/latent_art_bench/{name}/{file}.py"
                  for file in ("__init__", "__main__", "analysis")]
        paths += [f"tests/{name}/test_analysis.py", f"studies/{name}/PROTOCOL.md"]
        freeze = dict(run_id=run, recorded_git_commit=source,
                      bindings={p: release.digest((root / p).read_bytes()) for p in paths})
        freeze_sha = put(root, f"{directory}/freeze.json", freeze)
        output_paths = [f"{directory}/analysis.json", f"reports/{name}/{run}/REPORT.md"]
        if name == GEO:
            output_paths.append(f"reports/{name}/{run}/naming_geometry.pdf")
        outputs = {}
        for path in output_paths:
            raw = {"synthetic": True} if path.endswith(".json") else b"Synthetic output\n"
            outputs[path] = put(root, path, raw)
        put(root, f"{directory}/receipt.json", dict(
            freeze_sha256=freeze_sha, recorded_git_commit=source, new_images=0, outputs=outputs))
        return directory

    geometry = terminal(GEO, "g1", [inputs], source_commit)
    previous = commit(root)
    terminal(CENTER, "c1", [f"{geometry}/{file}.json"
                            for file in ("inputs", "freeze", "analysis", "receipt")], previous)
    commit(root)
    return root


def build(tree, tmp_path, **kwargs):
    return release.build(tree, tmp_path / "exports", "test-addon", **kwargs)


def mutate_json(tree, path, mutate):
    value = json.loads((tree / path).read_bytes())
    mutate(value)
    put(tree, path, value)


def test_final_build_is_complete_history_free_deterministic_and_verifiable(tree, tmp_path):
    first = build(tree, tmp_path)
    stage = Path(first["stage"])
    assert release.verify(stage)["history_free"] is True
    manifest = json.loads((stage / "ADDENDUM_MANIFEST.json").read_bytes())
    assert manifest["draft"] is False
    assert len(manifest["freezes"]) == 2
    assert release.CORE <= manifest["files"].keys()
    assert f"reports/{GEO}/g1/naming_geometry.pdf" in manifest["files"]
    assert f"reports/{CENTER}/c1/REPORT.md" in manifest["files"]
    assert b"only" in (stage / "README.md").read_bytes()
    assert b"pprv1-20260910" in (stage / "README.md").read_bytes()
    assert b"uv sync --locked --extra analysis --extra dev" in (stage / "README.md").read_bytes()
    with tarfile.open(first["archive"]) as archive:
        assert all(member.isfile() and member.name.startswith("test-addon/")
                   for member in archive.getmembers())
        assert len(archive.getmembers()) == len(manifest["files"]) + 2
        assert not any(".git/" in member.name for member in archive.getmembers())
    second = release.build(tree, tmp_path / "other", "test-addon")
    assert Path(first["archive"]).read_bytes() == Path(second["archive"]).read_bytes()
    expected = release.digest(Path(first["archive"]).read_bytes())
    assert Path(first["checksum"]).read_text() == f"{expected}  test-addon.tar.gz\n"


def test_unlisted_history_raw_credentials_and_korean_files_are_not_copied(tree, tmp_path):
    for path in ("paper/paper_ko.tex", "historical/archive.json", ".env",
                 "data/raw/image.png", "notes/private.md"):
        put(tree, path, b"Do not include this file.\n")
    result = build(tree, tmp_path)
    stage = Path(result["stage"])
    assert not (stage / "paper/paper_ko.tex").exists()
    assert not (stage / "historical").exists()
    assert not (stage / ".git").exists()


@pytest.mark.parametrize("path", [
    "/absolute", "../escape", "a/../b", "a//b", "a/./b", "a\\b", "C:/data/file",
    "a/", ".git/config", "history/log", "data/raw/a.json", "paper/paper_ko.tex",
    "paper/한국어.tex", ".env", ".env.local", "data/api-token.json", "secrets.json",
])
def test_unsafe_paths_are_rejected(path):
    with pytest.raises(ValueError):
        release.portable(path)


@pytest.mark.parametrize("path", [
    "src/latent_art_bench/cli.py", "tools/paper_release.py", "paper/figures/extra.pdf",
    "data/manifests/painter_feature_generation_v1/run/analysis.json",
    f"data/manifests/{GEO}/g1/responses.json", f"reports/{CENTER}/c1/extra.pdf",
])
def test_allowlist_does_not_expand_to_historical_or_arbitrary_files(path):
    with pytest.raises(ValueError, match="allowlist"):
        release.allowed(path)


@pytest.mark.parametrize("path", [
    f"data/manifests/{GEO}/g1/inputs.json", f"data/manifests/{CENTER}/c1/analysis.json",
    f"reports/{GEO}/g1/REPORT.md", f"src/latent_art_bench/{GEO}/analysis.py",
])
def test_draft_never_skips_frozen_input_or_output_hashes(tree, tmp_path, path):
    with (tree / path).open("ab") as stream:
        stream.write(b" \n")
    with pytest.raises(ValueError, match="checksum"):
        build(tree, tmp_path, draft=True)
    assert not (tmp_path / "exports").exists()


@pytest.mark.parametrize("field,value", [
    ("freeze_sha256", "0" * 64), ("recorded_git_commit", "0" * 40), ("new_images", 1),
])
def test_terminal_receipt_identity_is_required(tree, tmp_path, field, value):
    mutate_json(tree, f"data/manifests/{CENTER}/c1/receipt.json",
                lambda row: row.update({field: value}))
    with pytest.raises(ValueError, match="receipt"):
        build(tree, tmp_path, draft=True)


def test_transitive_freeze_binding_must_match_even_when_other_files_are_intact(tree, tmp_path):
    mutate_json(tree, f"data/manifests/{CENTER}/c1/freeze.json", lambda row: row["bindings"].update(
        {f"data/manifests/{GEO}/g1/freeze.json": "0" * 64}))
    with pytest.raises(ValueError, match="checksum"):
        build(tree, tmp_path, draft=True)


def test_bound_private_path_is_rejected_without_creating_partial_release(tree, tmp_path):
    mutate_json(tree, f"data/manifests/{CENTER}/c1/freeze.json", lambda row: row["bindings"].update(
        {".env": "0" * 64}))
    with pytest.raises(ValueError, match="prohibited"):
        build(tree, tmp_path, draft=True)
    assert not (tmp_path / "exports").exists()


@pytest.mark.parametrize("field", ["inputs", "tests", "protocol"])
def test_freeze_cannot_omit_required_replay_inputs(tree, tmp_path, field):
    paths = {"inputs": f"data/manifests/{GEO}/g1/inputs.json",
             "tests": f"tests/{GEO}/test_analysis.py", "protocol": f"studies/{GEO}/PROTOCOL.md"}
    mutate_json(tree, f"data/manifests/{GEO}/g1/freeze.json",
                lambda row: row["bindings"].pop(paths[field]))
    with pytest.raises(ValueError, match="required source/protocol/input/tests"):
        build(tree, tmp_path, draft=True)


def test_receipt_cannot_add_an_unrelated_allowlisted_output(tree, tmp_path):
    mutate_json(tree, f"data/manifests/{CENTER}/c1/receipt.json", lambda row: row["outputs"].update(
        {"paper/paper.pdf": release.digest((tree / "paper/paper.pdf").read_bytes())}))
    with pytest.raises(ValueError, match="output inventory"):
        build(tree, tmp_path, draft=True)


@pytest.mark.parametrize("directory", [False, True])
def test_symlinked_file_or_parent_is_rejected(tree, tmp_path, directory):
    target = tree / "paper/figures" if directory else tree / "paper/paper.pdf"
    moved = tmp_path / "outside"
    target.rename(moved)
    target.symlink_to(moved, target_is_directory=directory)
    with pytest.raises(ValueError, match="symlink"):
        build(tree, tmp_path, draft=True)


@pytest.mark.parametrize("content", [
    {"access_token": "sensitive-fixture"}, {"value": "/home/example/private"},
    {"value": "data:image/png;base64,AAAA"}, {"url": "https://user:pass@example.invalid"},
])
def test_sensitive_json_fails_without_echoing_values(content):
    with pytest.raises(ValueError) as error:
        release.screen(release.encoded(content), ".json")
    assert "sensitive-fixture" not in str(error.value)
    assert "user:pass" not in str(error.value)


def test_final_build_requires_clean_included_files_but_draft_can_inspect_paper(tree, tmp_path):
    with (tree / "paper/paper.tex").open("ab") as stream:
        stream.write(b"% manuscript editing in progress\n")
    with pytest.raises(ValueError, match="not clean at HEAD"):
        build(tree, tmp_path)
    result = build(tree, tmp_path, draft=True)
    manifest = json.loads((Path(result["stage"]) / "ADDENDUM_MANIFEST.json").read_bytes())
    assert manifest["draft"] is True
    assert manifest["recorded_git_commit"] is None


def test_final_build_checks_original_source_commit_not_only_current_tree(tree, tmp_path):
    path = f"data/manifests/{CENTER}/c1/freeze.json"
    # This commit predates the predecessor's freeze/results, all locally intact.
    oldest = git(tree, "rev-list", "--max-parents=0", "HEAD")
    mutate_json(tree, path, lambda row: row.update(recorded_git_commit=oldest))
    mutate_json(tree, f"data/manifests/{CENTER}/c1/receipt.json", lambda row: row.update(
        recorded_git_commit=oldest, freeze_sha256=release.digest((tree / path).read_bytes())))
    commit(tree)
    with pytest.raises(ValueError, match="absent at required commit"):
        build(tree, tmp_path)


def test_existing_stage_archive_or_checksum_is_never_overwritten(tree, tmp_path):
    original = build(tree, tmp_path)
    before = {key: Path(original[key]).read_bytes() for key in ("archive", "checksum")}
    with pytest.raises(FileExistsError):
        build(tree, tmp_path)
    for key, raw in before.items():
        assert Path(original[key]).read_bytes() == raw


@pytest.mark.parametrize("damage", ["bytes", "extra", "symlink", "sums", "manifest"])
def test_extracted_verifier_rejects_tampering_without_git(tree, tmp_path, damage):
    stage = Path(build(tree, tmp_path)["stage"])
    assert not (stage / ".git").exists()
    if damage == "bytes":
        (stage / "paper/paper.pdf").write_bytes(b"changed")
    elif damage == "extra":
        (stage / "extra.txt").write_text("unlisted")
    elif damage == "symlink":
        (stage / "paper/paper.pdf").unlink()
        (stage / "paper/paper.pdf").symlink_to(tree / "paper/paper.pdf")
    elif damage == "sums":
        (stage / "SHA256SUMS").write_text("changed")
    else:
        mutate_json(stage, "ADDENDUM_MANIFEST.json", lambda row: row.update(schema="unknown"))
    with pytest.raises(ValueError):
        release.verify(stage)


def test_exact_nine_english_figures_are_required(tree, tmp_path):
    with (tree / "paper/paper.tex").open("ab") as stream:
        stream.write(b"\\includegraphics{unapproved.pdf}\n")
    with pytest.raises(ValueError, match="nine approved figures"):
        build(tree, tmp_path, draft=True)


def test_ambiguous_multiple_runs_fail_closed(tree, tmp_path):
    put(tree, f"data/manifests/{CENTER}/other/freeze.json", {})
    with pytest.raises(ValueError, match="exactly one frozen run"):
        build(tree, tmp_path, draft=True)
