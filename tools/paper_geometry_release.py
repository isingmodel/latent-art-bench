"""Build a local, history-free addendum for the two frozen naming analyses.

This tool never publishes, downloads, collects images, modifies a freeze, or
executes a scientific analysis. Binding hashes are checked even in draft mode.
Only the explicit release surface and the allowlisted transitive freeze graph
are copied; input ``origins`` are provenance, not instructions to copy history.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import re
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

NAMESPACES = ("painter_naming_geometry_v1", "painter_naming_centering_v1")
FIGURES = (
    "challenge_matrix.pdf", "color_responsiveness.pdf", "common_pca.pdf",
    "four_painter_distributions.pdf", "naming_geometry.pdf", "palette_blocks.pdf",
    "primary_comparison.pdf", "scene_retrieval.pdf", "variation_ratios.pdf",
)
CORE = frozenset({
    "LICENSE", "pyproject.toml", "uv.lock", "src/latent_art_bench/__init__.py",
    "paper/paper.tex", "paper/paper.pdf", "paper/references.bib",
    "tools/paper_geometry_release.py", "tests/test_geometry_release.py",
    *(f"paper/figures/{name}" for name in FIGURES),
})
GENERATED = frozenset({"README.md", "ADDENDUM_MANIFEST.json", "SHA256SUMS"})
SCHEMA = "painter-naming-addendum/1"
ROOT = Path(__file__).resolve().parents[1]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", value):
        raise ValueError("release/run ID must be a portable component")
    return value


def portable(value):
    """Reject ambiguous spellings as well as traversal, local, and private paths."""
    if not isinstance(value, str) or not value or not value.isascii():
        raise ValueError("path must be an ASCII portable relative path")
    parts = value.split("/")
    if any(not re.fullmatch(r"[A-Za-z0-9_.-]+", part) or part in (".", "..")
           for part in parts):
        raise ValueError("path must be a confined portable relative path")
    prohibited = re.compile(
        r"(^|[_.-])(git|hg|svn|history|raw|secrets?|credentials?|auth|tokens?|korean|ko)($|[_.-])"
        r"|^\.env($|\.)", re.IGNORECASE)
    if any(prohibited.search(part) for part in parts):
        raise ValueError("prohibited private, history, media, or Korean path")
    return PurePosixPath(value)


def allowed(value):
    path = portable(value)
    if value in CORE:
        return path
    p = path.parts
    valid = (
        len(p) == 4 and p[:2] == ("src", "latent_art_bench")
        and p[2] in NAMESPACES and p[3].endswith(".py")
    ) or (
        len(p) == 3 and p[0] == "tests" and p[1] in NAMESPACES
        and p[2].startswith("test_") and p[2].endswith(".py")
    ) or (
        len(p) == 3 and p[0] == "studies" and p[1] in NAMESPACES and p[2] == "PROTOCOL.md"
    ) or (
        len(p) == 5 and p[:2] == ("data", "manifests") and p[2] in NAMESPACES
        and p[4] in {"inputs.json", "freeze.json", "analysis.json", "receipt.json"}
    ) or (
        len(p) == 4 and p[0] == "reports" and p[1] in NAMESPACES
        and (p[3] == "REPORT.md" or p[1] == NAMESPACES[0] and p[3] == "naming_geometry.pdf")
    )
    if not valid:
        raise ValueError("path is outside the addendum allowlist")
    return path


def no_symlinks(path):
    """Check every component, including ancestors of a caller-supplied root."""
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError("symlink paths are prohibited")


def file_bytes(root, value):
    path = root / allowed(value)
    no_symlinks(path)
    if not path.is_file():
        raise ValueError(f"required regular file is missing: {value}")
    raw = path.read_bytes()
    screen(raw, path.suffix)
    return raw


def screen(raw, suffix):
    """Fail closed for compact-data credentials without displaying suspect bytes.

    Source tests may contain literal safety fixtures. Only data and publication
    text are screened here; source paths are separately strictly allowlisted.
    """
    if suffix not in {".json", ".md", ".tex", ".bib", ".toml", ".lock"}:
        return
    text = raw.decode("utf-8")
    patterns = (
        r"/(?:Users|home|private)/", r"[A-Za-z]:[\\/](?:Users|Windows)[\\/]",
        r"file://", r"data:image/", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"\bsk-[A-Za-z0-9_-]{24,}", r"\bAKIA[A-Z0-9]{16}\b",
        r"\bBearer\s+[A-Za-z0-9._-]{24,}", r"https?://[^\s/\"'<>:@]+:[^\s/\"'<>@]+@",
    )
    if any(re.search(pattern, text) for pattern in patterns):
        raise ValueError("release content contains a prohibited sensitive/local-path pattern")
    if suffix == ".json":
        def visit(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if re.search(r"password|api.?key|authorization|access.?token|refresh.?token",
                                 key, re.IGNORECASE):
                        raise ValueError("release JSON contains a sensitive field")
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)
        visit(json.loads(text))


def hash_mapping(value):
    if not isinstance(value, dict) or not value:
        raise ValueError("nonempty path/hash mapping required")
    for path, expected in value.items():
        allowed(path)
        if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("invalid SHA-256 binding")
    return value


def git_bytes(root, commit, path):
    try:
        return subprocess.check_output(
            ["git", "show", f"{commit}:{path}"], cwd=root, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as error:
        raise ValueError(f"release input is absent at required commit: {path}") from error


def gather(root, *, check_source_commits=False):
    """Verify both terminal runs and recursively collect their frozen dependencies."""
    root = Path(root).absolute()
    no_symlinks(root)
    files, freezes, active = {}, {}, set()

    def include(path, expected=None):
        raw = file_bytes(root, path)
        if expected is not None and digest(raw) != expected:
            raise ValueError(f"checksum mismatch: {path}")
        if path in files and files[path] != raw:
            raise ValueError("input changed during collection")
        files[path] = raw
        return raw

    def freeze(path):
        if path in active:
            raise ValueError("cyclic freeze binding")
        if path in freezes:
            return
        active.add(path)
        parts = allowed(path).parts
        if len(parts) != 5 or parts[-1] != "freeze.json":
            raise ValueError("invalid freeze path")
        name, run = parts[2:4]
        identifier(run)
        value = json.loads(include(path))
        commit = value.get("recorded_git_commit", "")
        if value.get("run_id") != run or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
            raise ValueError("freeze identity/source commit is invalid")
        bindings = hash_mapping(value.get("bindings"))
        required = {f"src/latent_art_bench/{name}/{p}.py"
                    for p in ("__init__", "__main__", "analysis")}
        required.update({f"studies/{name}/PROTOCOL.md", "pyproject.toml", "uv.lock"})
        if name == NAMESPACES[0]:
            required.add(f"data/manifests/{name}/{run}/inputs.json")
        has_tests = any(p.startswith(f"tests/{name}/") for p in bindings)
        if not required <= bindings.keys() or not has_tests:
            raise ValueError("freeze does not bind its required source/protocol/input/tests")
        for bound, expected in bindings.items():
            raw = include(bound, expected)
            if check_source_commits and git_bytes(root, commit, bound) != raw:
                raise ValueError(f"bound input differs from recorded source commit: {bound}")
            if PurePosixPath(bound).name == "freeze.json":
                freeze(bound)
        receipt_path = str(PurePosixPath(path).with_name("receipt.json"))
        receipt = json.loads(include(receipt_path))
        if (receipt.get("freeze_sha256") != digest(files[path])
                or receipt.get("recorded_git_commit") != commit
                or receipt.get("new_images") != 0):
            raise ValueError("terminal receipt does not match its freeze")
        outputs = hash_mapping(receipt.get("outputs"))
        required_outputs = {f"data/manifests/{name}/{run}/analysis.json",
                            f"reports/{name}/{run}/REPORT.md"}
        if name == NAMESPACES[0]:
            required_outputs.add(f"reports/{name}/{run}/naming_geometry.pdf")
        if outputs.keys() != required_outputs:
            raise ValueError("terminal output inventory differs from fixed release surface")
        for output, expected in outputs.items():
            include(output, expected)
        freezes[path] = {"sha256": digest(files[path]), "recorded_git_commit": commit}
        active.remove(path)

    for name in NAMESPACES:
        directory = root / "data/manifests" / name
        no_symlinks(directory)
        candidates = sorted(directory.glob("*/freeze.json"))
        if len(candidates) != 1:
            raise ValueError(f"exactly one frozen run is required for {name}")
        freeze(candidates[0].relative_to(root).as_posix())
    for path in sorted(CORE):
        include(path)
    manuscript = files["paper/paper.tex"].decode("utf-8")
    figures = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", manuscript)
    if set(figures) != set(FIGURES) or len(figures) != len(FIGURES):
        raise ValueError("English manuscript must use exactly the nine approved figures")
    return files, freezes


def readme(release_id, draft):
    status = "DRAFT FOR LOCAL QA; not a final release" if draft else "Final local build"
    return f"""# Painter naming geometry addendum: {release_id}

{status}. This history-free numerical addendum contains the English manuscript,
its nine figure PDFs, and both post-result naming analyses. It reruns only
`painter_naming_geometry_v1` and `painter_naming_centering_v1` from retained
compact measurements. It does not regenerate or independently measure images.

Historical paper results require the immutable predecessor release
[pprv1-20260910](https://github.com/isingmodel/latent-art-bench/releases/tag/pprv1-20260910).
This addendum supplements that release; it does not claim to replay every
historical paper result. Historical hashes and input `origins` are provenance;
their original archives are intentionally not copied here.

## Verify and replay

In a fresh extracted directory, verify the package before installing:

```sh
python tools/paper_geometry_release.py verify --root .
uv sync --locked --extra analysis --extra dev
uv run --locked python -m latent_art_bench.painter_naming_geometry_v1 verify
uv run --locked python -m latent_art_bench.painter_naming_centering_v1 verify
uv run --locked pytest -q --import-mode=importlib \\
  tests/painter_naming_geometry_v1 tests/painter_naming_centering_v1
```

Use the two module commands above; the original project-wide console command
depends on historical source outside this compact addendum. Installation may
download the locked software dependencies. Scientific replay reads local data
only and preserves the frozen inputs and terminal outputs. A TeX installation
is needed only to rebuild the manuscript PDF; its nine figures are included.

`ADDENDUM_MANIFEST.json` records every payload hash and source/freeze provenance;
`SHA256SUMS` also hashes that manifest. The external archive checksum authenticates
bytes relative to a trusted release checksum, not the underlying observations.
Git history, raw pixels, artwork, model weights, source checkouts, authentication
material, and Korean manuscript files are excluded. Capture validity and the
finite-panel, post-result scope remain as stated in the protocols and paper.
Reviews and implementation assistance were maintainer-run LLM work, not
institutionally independent review. No external publication is performed by
this local packaging tool.
""".encode()


def checksum_text(files):
    return "".join(f"{digest(raw)}  {path}\n" for path, raw in sorted(files.items())).encode()


def write_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    no_symlinks(path)
    with path.open("xb") as stream:
        stream.write(raw)


def build(root, output_root, release_id, *, draft=False):
    """Create one new staging tree/archive/checksum; never replace an existing artifact."""
    release_id = identifier(release_id)
    root, output_root = Path(root).absolute(), Path(output_root).absolute()
    no_symlinks(output_root)
    stage = output_root / release_id
    archive = output_root / f"{release_id}.tar.gz"
    checksum = output_root / f"{release_id}.tar.gz.sha256"
    for path in (stage, archive, checksum):
        if path.exists() or path.is_symlink():
            raise FileExistsError(f"create-once release target exists: {path.name}")
    files, freezes = gather(root, check_source_commits=not draft)
    commit = None
    if not draft:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                         text=True).strip()
        for path, raw in files.items():
            if git_bytes(root, commit, path) != raw:
                raise ValueError(f"release input is not clean at HEAD: {path}")
    files["README.md"] = readme(release_id, draft)
    manifest = dict(schema=SCHEMA, release_id=release_id, draft=draft,
                    recorded_git_commit=commit, freezes=freezes,
                    files={path: digest(raw) for path, raw in sorted(files.items())},
                    scope="Only geometry and centering replay; historical release required")
    files["ADDENDUM_MANIFEST.json"] = encoded(manifest)
    files["SHA256SUMS"] = checksum_text(files)
    stage.mkdir(parents=True)
    for path, raw in sorted(files.items()):
        write_new(stage / path, raw)
    verify(stage)
    with archive.open("xb") as stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as tar:
                for path, raw in sorted(files.items()):
                    entry = tarfile.TarInfo(f"{release_id}/{path}")
                    entry.size, entry.mode, entry.mtime = len(raw), 0o644, 0
                    tar.addfile(entry, io.BytesIO(raw))
    write_new(checksum, f"{digest(archive.read_bytes())}  {archive.name}\n".encode())
    return dict(status="built", draft=draft, stage=str(stage), archive=str(archive),
                checksum=str(checksum), payload_files=len(files))


def verify(root):
    """Validate an extracted package before environment installation, without Git."""
    root = Path(root).absolute()
    no_symlinks(root)
    manifest_path = root / "ADDENDUM_MANIFEST.json"
    no_symlinks(manifest_path)
    manifest = json.loads(manifest_path.read_bytes())
    if manifest.get("schema") != SCHEMA:
        raise ValueError("unknown addendum manifest schema")
    identifier(manifest.get("release_id"))
    expected = manifest.get("files")
    if not isinstance(expected, dict) or "README.md" not in expected:
        raise ValueError("invalid addendum payload inventory")
    files = {}
    for path, sha in expected.items():
        if path != "README.md":
            allowed(path)
        if path in GENERATED - {"README.md"} or not re.fullmatch(r"[0-9a-f]{64}", str(sha)):
            raise ValueError("invalid addendum payload binding")
        target = root / path
        no_symlinks(target)
        raw = target.read_bytes()
        if digest(raw) != sha:
            raise ValueError(f"package checksum mismatch: {path}")
        files[path] = raw
    files["ADDENDUM_MANIFEST.json"] = manifest_path.read_bytes()
    sum_path = root / "SHA256SUMS"
    no_symlinks(sum_path)
    if sum_path.read_bytes() != checksum_text(files):
        raise ValueError("SHA256SUMS differs from payload and manifest")
    observed = set()
    for path in root.rglob("*"):
        no_symlinks(path)
        if path.is_file():
            observed.add(path.relative_to(root).as_posix())
    if observed != files.keys() | {"SHA256SUMS"}:
        raise ValueError("unlisted or missing package files")
    gathered, freezes = gather(root)
    if set(gathered) != set(expected) - {"README.md"} or freezes != manifest.get("freezes"):
        raise ValueError("package inventory differs from transitive frozen release surface")
    return dict(status="verified", payload_files=len(observed), history_free=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    export = sub.add_parser("build")
    export.add_argument("--root", type=Path, default=ROOT)
    export.add_argument("--output-root", type=Path, required=True)
    export.add_argument("--release-id", required=True)
    export.add_argument("--draft", action="store_true", help="Skip Git checks for local QA only")
    check = sub.add_parser("verify")
    check.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = verify(args.root) if args.action == "verify" else build(
        args.root, args.output_root, args.release_id, draft=args.draft)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
