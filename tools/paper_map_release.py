"""Allowlisted numerical replay of one terminal fixed-map qualification.

No collection, extraction, qualification writer, publication or history export.
Public verify is stdlib-only. Public check recomputes the immutable numerical
qualification in memory; it never invokes the study's create-once build().
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib
import io
import json
import math
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath

STUDY = "studies/painter_map_validation_v1"
RESULT = f"{STUDY}/pmvqv1-20260910"
SCIENCE = "src/latent_art_bench/painter_map_validation_v1"
GEOMETRY = "data/manifests/painter_naming_geometry_v1/pngv1-20260910"
TOOL = "tools/paper_map_release.py"
SCHEMA = "paper-map-numerical-release/1"
MANIFEST = "MAP_RELEASE_MANIFEST.json"
OMITTED = frozenset({f"{STUDY}/DESIGN.md", f"{GEOMETRY}/freeze.json", f"{GEOMETRY}/receipt.json"})
INCLUDED_BOUND = frozenset(
    {
        f"{SCIENCE}/precision.py",
        f"{SCIENCE}/__init__.py",
        "src/latent_art_bench/__init__.py",
        "tests/painter_map_validation_v1/test_precision.py",
        f"{STUDY}/PRECISION_PROTOCOL.md",
        f"{GEOMETRY}/inputs.json",
        f"{GEOMETRY}/analysis.json",
        "pyproject.toml",
        "uv.lock",
    }
)
CORE = INCLUDED_BOUND | frozenset(
    {
        "LICENSE",
        TOOL,
        "tests/test_paper_map_release.py",
        f"{RESULT}/RUN.json",
        f"{RESULT}/precision.json",
        f"{RESULT}/PRECISION.md",
    }
)
TOLERANCE = 1e-10


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode()


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", value):
        raise ValueError("portable release identifier required")
    return value


def portable(value):
    if not isinstance(value, str) or not value or not value.isascii():
        raise ValueError("ASCII relative path required")
    parts = value.split("/")
    if any(not re.fullmatch(r"[A-Za-z0-9_.-]+", p) or p in (".", "..") for p in parts):
        raise ValueError("unsafe relative path")
    banned = (
        r"(^|[_.-])(git|hg|svn|history|raw|secrets?|credentials?|auth|tokens?|korean|ko)($|[_.-])"
    )
    if any(re.search(banned, p, re.I) or re.match(r"^\.env($|\.)", p, re.I) for p in parts):
        raise ValueError("private/history/raw/Korean path prohibited")
    return PurePosixPath(value)


def no_symlinks(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("symlink prohibited")


def screen(raw, suffix):
    if suffix not in {".json", ".md", ".toml", ".lock"}:
        return
    text = raw.decode("utf-8")
    patterns = (
        r"/(?:Users|home|private)/",
        r"[A-Za-z]:[\\/](?:Users|Windows)[\\/]",
        r"file://",
        r"data:image/",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"\bsk-[A-Za-z0-9_-]{24,}",
        r"\bAKIA[A-Z0-9]{16}\b",
        r"\bBearer\s+[A-Za-z0-9._-]{24,}",
        r"https?://[^\s/\"'<>:@]+:[^\s/\"'<>@]+@",
    )
    if any(re.search(pattern, text) for pattern in patterns):
        raise ValueError("sensitive content or absolute local path rejected")
    if suffix == ".json":

        def visit(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if re.search(
                        r"password|api.?key|authorization|access.?token|refresh.?token|b64_json",
                        key,
                        re.I,
                    ):
                        raise ValueError("sensitive JSON field rejected")
                    visit(child)
            elif isinstance(value, list):
                for child in value:
                    visit(child)

        visit(json.loads(text))


def file_bytes(root, relative, *, public=True):
    path = Path(root) / portable(relative)
    no_symlinks(path)
    if not path.is_file():
        raise ValueError(f"required regular file absent: {relative}")
    raw = path.read_bytes()
    if public:
        screen(raw, PurePosixPath(relative).suffix)
    return raw


def binding_map(records):
    result = {}
    if not isinstance(records, list):
        raise ValueError("binding records required")
    for row in records:
        if set(row) != {"path", "sha256"}:
            raise ValueError("exact binding fields required")
        path, sha = row["path"], row["sha256"]
        portable(path)
        if path in result or not re.fullmatch(r"[0-9a-f]{64}", str(sha)):
            raise ValueError("duplicate/invalid binding")
        result[path] = sha
    return result


def validate_science(files):
    run = json.loads(files[f"{RESULT}/RUN.json"])
    result = json.loads(files[f"{RESULT}/precision.json"])
    if set(run) != {"schema", "source_commit", "source_bindings", "environment"}:
        raise ValueError("unexpected qualification provenance fields")
    if run["schema"] != "painter-map-precision-run/1" or not re.fullmatch(
        r"[0-9a-f]{40}", str(run["source_commit"])
    ):
        raise ValueError("invalid qualification source identity")
    if set(result) != set(run) | {"proxy_scene_ids", "qualification"}:
        raise ValueError("unexpected numerical result fields")
    if any(result[k] != v for k, v in run.items()):
        raise ValueError("RUN/result provenance disagreement")
    bindings = binding_map(run["source_bindings"])
    if set(bindings) != INCLUDED_BOUND | OMITTED:
        raise ValueError("qualification binding inventory differs")
    if any(digest(files[p]) != bindings[p] for p in INCLUDED_BOUND):
        raise ValueError("included scientific source/input binding mismatch")
    q = result["qualification"]
    if (
        q.get("decision") != "stop_inferential_proposal"
        or q.get("selected_R") is not None
        or q.get("selected_outputs") is not None
    ):
        raise ValueError("this addendum retains the terminal failed proposal only")
    cells = {(r["R"], r["shape"], r["mean"], r["regime"]) for r in q["records"]}
    expected = {
        (r, sh, m, rg)
        for r in (4, 6, 8)
        for sh in ("gaussian_shaped", "t5_shaped", "lognormal_shaped")
        for m in ("T1", "midpoint", "T2")
        for rg in ("baseline", "high_positive", "low_negative")
    }
    if (
        len(q["records"]) != 81
        or cells != expected
        or any(row["trials"] != 10000 for row in q["records"])
    ):
        raise ValueError("complete 81-cell 10000-trial qualification required")
    return run, result


def git_bytes(root, revision, path):
    result = subprocess.run(["git", "show", f"{revision}:{path}"], cwd=root, capture_output=True)
    if result.returncode:
        raise ValueError(f"file missing at required commit: {path}")
    return result.stdout


def clean_sources(root, files):
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    for p, raw in files.items():
        if git_bytes(root, commit, p) != raw or git_bytes(root, "", p) != raw:
            raise ValueError(f"commit working/index bytes before final build: {p}")
    return commit


def gather(root, *, local=False):
    files = {p: file_bytes(root, p) for p in sorted(CORE)}
    run, result = validate_science(files)
    if local:
        for p, sha in binding_map(run["source_bindings"]).items():
            # Omitted private documents are verified locally, never screened into payload.
            raw = files[p] if p in files else file_bytes(root, p, public=False)
            if digest(raw) != sha or git_bytes(root, run["source_commit"], p) != raw:
                raise ValueError(f"historical source binding mismatch: {p}")
    return files, run, result


def readme(release_id, draft):
    return f"""# Terminal fixed-map precision replay: {release_id}

{"Draft local QA bundle." if draft else "Final local build; publication is separate."}
The proposal stopped: all three allocations failed the baseline Q half-width
criterion. This numerical replay does not reopen it, authorize collection, or
establish service validation. No new images were generated for this qualification.

```sh
python tools/paper_map_release.py verify --root .
uv sync --locked --python 3.13.11 --extra analysis --extra dev
uv run --locked python tools/paper_map_release.py check --root .
uv run --locked pytest -q --import-mode=importlib tests/test_paper_map_release.py \\
  tests/painter_map_validation_v1/test_precision.py
```

The dedicated public check calls unchanged qualify(load_proxy(...)) in memory,
compares the complete 81-cell qualification, and never calls the create-once
study build command. It writes no scientific results. Public verify uses only
stdlib; check requires installed NumPy/SciPy but no Git, network, proxy, images,
credentials or current credit balance. Optional tests need Git for temporary
provenance fixtures. Installation may download dependencies. RUN.json records
the original interpreter/library/platform; use its Python 3.13.11 runtime.

Floating results use the existing 1e-10 absolute/relative comparison contract;
structures, integers, identities, seeds, hashes, nulls and decisions are exact.
Each support_sha256 hashes reconstructed floating-point array bytes. Exact support
hash equality can restrict replay to matching numerical arithmetic/platform even
when other floating values meet 1e-10; cross-platform portability is not promised.
No tolerance alters counts, stopping decisions or the retained original report.
The stored report is verified bytewise against the unchanged report renderer
applied to the stored result; computed qualification values are checked separately.
Source mismatches or changed Monte Carlo counts fail rather than being repaired.

Included source/protocol/numerical/result bytes are unchanged. RUN.json retains
all 12 source-binding fingerprints; nine bound files are included. DESIGN.md is
omitted because it contains private operational credit information; old geometry
freeze/receipt bodies are also omitted. Their hashes are provenance, not a public
check of absent bodies. The builder verifies all 12 locally against the recorded
source commit before export. No Git history, preflight records, metadata bodies,
raw pixels, .env, Korean drafts, artwork or capture-audit raw ledger is included.
Underlying image acquisition, capture ancestry and service identity are not
independently authenticated by these vectors or a checksum manifest. Earlier
immutable numerical packages remain necessary for their historical results.

This qualification uses discrete historical noise proxies, not verified current
service laws or new-scene outcomes. Passing coverage simulations did not overcome
the failed precision gate. No perceptual, independent-capture, scene-population
or internal-mechanism validation follows. Design, implementation and reviews were
maintainer-run LLM work with disclosed assistance, not independent human reviews.
""".encode()


def checksum_text(files):
    return "".join(f"{digest(raw)}  {p}\n" for p, raw in sorted(files.items())).encode()


def write_new(path, raw):
    no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)


def build(root, output_root, release_id, *, draft=False):
    root, output_root = Path(root).absolute(), Path(output_root).absolute()
    identifier(release_id)
    no_symlinks(root)
    no_symlinks(output_root)
    stage = output_root / release_id
    archive = output_root / f"{release_id}.tar.gz"
    checksum = output_root / f"{release_id}.tar.gz.sha256"
    if any(p.exists() or p.is_symlink() for p in (stage, archive, checksum)):
        raise FileExistsError("create-once stage/archive/checksum already exists")
    files, run, _ = gather(root, local=True)
    commit = None if draft else clean_sources(root, files)
    original_files = dict(files)
    files["README.md"] = readme(release_id, draft)
    files[MANIFEST] = encoded(
        dict(
            schema=SCHEMA,
            release_id=release_id,
            draft=draft,
            build_source_commit=commit,
            qualification_source_commit=run["source_commit"],
            omitted_bound_paths=sorted(OMITTED),
            files={p: digest(raw) for p, raw in sorted(files.items())},
        )
    )
    files["SHA256SUMS"] = checksum_text(files)
    stage.mkdir(parents=True)
    for p, raw in sorted(files.items()):
        write_new(stage / p, raw)
    verify(stage)
    with archive.open("xb") as handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as tar:
                for p, raw in sorted(files.items()):
                    item = tarfile.TarInfo(f"{release_id}/{p}")
                    item.size, item.mode, item.mtime = len(raw), 0o644, 0
                    tar.addfile(item, io.BytesIO(raw))
    write_new(checksum, f"{digest(archive.read_bytes())}  {archive.name}\n".encode())
    refreshed, _, _ = gather(root, local=True)
    if refreshed != original_files or (not draft and clean_sources(root, refreshed) != commit):
        raise ValueError("source changed during build; preserve the failed create-once outputs")
    verify(stage)
    return dict(
        stage=str(stage),
        archive=str(archive),
        checksum=str(checksum),
        draft=draft,
        payload_files=len(files),
    )


def verify(root, *, runtime=False):
    """Stdlib verification before installing/importing any scientific implementation."""
    root = Path(root).absolute()
    no_symlinks(root)
    manifest = json.loads(file_bytes(root, MANIFEST))
    if set(manifest) != {
        "schema",
        "release_id",
        "draft",
        "build_source_commit",
        "qualification_source_commit",
        "omitted_bound_paths",
        "files",
    }:
        raise ValueError("unexpected release manifest fields")
    if manifest["schema"] != SCHEMA or type(manifest["draft"]) is not bool:
        raise ValueError("invalid release manifest")
    identifier(manifest["release_id"])
    if (manifest["draft"] and manifest["build_source_commit"] is not None) or (
        not manifest["draft"]
        and not re.fullmatch(r"[0-9a-f]{40}", str(manifest["build_source_commit"]))
    ):
        raise ValueError("invalid final/draft source identity")
    files, run, _ = gather(root)
    if manifest["qualification_source_commit"] != run["source_commit"] or manifest[
        "omitted_bound_paths"
    ] != sorted(OMITTED):
        raise ValueError("qualification provenance/omissions differ")
    files["README.md"] = file_bytes(root, "README.md")
    if set(manifest["files"]) != files.keys() or any(
        manifest["files"][p] != digest(raw) for p, raw in files.items()
    ):
        raise ValueError("payload inventory/hash mismatch")
    files[MANIFEST] = file_bytes(root, MANIFEST)
    if file_bytes(root, "SHA256SUMS") != checksum_text(files):
        raise ValueError("SHA256SUMS mismatch")
    observed = set()
    for directory, directories, names in os.walk(root, followlinks=False):
        parent = Path(directory)
        if runtime:
            directories[:] = [
                d
                for d in directories
                if d not in {".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
            ]
        for name in directories + names:
            no_symlinks(parent / name)
        observed.update((parent / n).relative_to(root).as_posix() for n in names)
    if observed != files.keys() | {"SHA256SUMS"}:
        raise ValueError("unlisted/missing release files")
    return dict(
        status="verified",
        files=len(observed),
        qualification="terminal_failed",
        absent_pixels_authenticated=False,
    )


def compare(actual, expected):
    """Every leaf checked: only finite float results receive existing 1e-10 tolerance."""
    if isinstance(expected, dict):
        return (
            isinstance(actual, dict)
            and actual.keys() == expected.keys()
            and all(compare(actual[k], value) for k, value in expected.items())
        )
    if isinstance(expected, list):
        return (
            isinstance(actual, list)
            and len(actual) == len(expected)
            and all(compare(a, b) for a, b in zip(actual, expected))
        )
    if type(expected) is float and type(actual) in (float, int):
        return (
            math.isfinite(actual)
            and math.isfinite(expected)
            and math.isclose(actual, expected, rel_tol=TOLERANCE, abs_tol=TOLERANCE)
        )
    return type(actual) is type(expected) and actual == expected


def require_local_modules(root):
    source = (Path(root) / "src").resolve()
    for name, module in list(sys.modules.items()):
        if name == "latent_art_bench" or name.startswith("latent_art_bench."):
            origin = getattr(module, "__file__", None)
            if origin is None or not Path(origin).resolve().is_relative_to(source):
                raise ValueError(
                    "cached scientific module outside this package; use a fresh process"
                )


def check(root):
    root = Path(root).absolute()
    verify(root, runtime=True)
    original_manifest = file_bytes(root, MANIFEST)
    require_local_modules(root)
    sys.path.insert(0, str(root / "src"))
    importlib.invalidate_caches()
    precision = importlib.import_module("latent_art_bench.painter_map_validation_v1.precision")
    require_local_modules(root)
    expected = json.loads(file_bytes(root, f"{RESULT}/precision.json"))
    actual = precision.qualify(precision.load_proxy(root))
    require_local_modules(root)
    if not compare(actual, expected["qualification"]):
        raise ValueError(
            "complete qualification replay differs; retain terminal evidence unchanged"
        )
    if precision.report(expected).encode() != file_bytes(root, f"{RESULT}/PRECISION.md"):
        raise ValueError("stored report renderer replay differs")
    verify(root, runtime=True)
    if file_bytes(root, MANIFEST) != original_manifest:
        raise ValueError("package manifest changed during numerical replay")
    return dict(
        status="checked",
        cells=81,
        decision=actual["decision"],
        exact_values=(actual == expected["qualification"]),
        float_absolute_relative_tolerance=TOLERANCE,
        writes_scientific_outputs=False,
        service_validation=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("verify", "check", "build"):
        command = sub.add_parser(name)
        command.add_argument("--root", type=Path, default=Path.cwd())
        if name == "build":
            command.add_argument("--output-root", type=Path, required=True)
            command.add_argument("--release-id", required=True)
            command.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    if args.command == "build":
        result = build(args.root, args.output_root, args.release_id, draft=args.draft)
    else:
        result = {"verify": verify, "check": check}[args.command](args.root)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
