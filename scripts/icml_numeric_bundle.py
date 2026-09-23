"""Build and replay a local, portable numerical artifact without pixels or weights.

Discovery observes the fixed read-only commands below. It never invokes an
extractor, collector or network client. Original scientific code is copied
byte-for-byte and retains its existing input hashes and exact replay checks.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
import platform
import runpy
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "reports/icml_review_v1/numeric_bundle_v1"
MANIFEST = "numeric_bundle_manifest.json"
FROZEN = Path("reports/icml_review_v1/round_03")
COMMANDS = [
    ["-m", "latent_art_bench.painter_specificity_measurement_v1.workflow", "analyze", "--check"],
    ["-m", "latent_art_bench.painter_specificity_measurement_v1.workflow",
     "analyze", "--square", "--check"],
    ["-m", "latent_art_bench.painter_specificity_measurement_v1.workflow",
     "analyze", "--reference", "--check"],
    ["-m", "latent_art_bench.painter_specificity_measurement_v1.workflow",
     "analyze", "--reference", "--square", "--check"],
    ["-m", "latent_art_bench.painter_specificity_review_v1", "check"],
    ["-m", "latent_art_bench.painter_specificity_review_v2", "check"],
    ["-m", "latent_art_bench.painter_reference_quality_v1", "check"],
    ["-m", "latent_art_bench.painter_specificity_review_v3", "check"],
    ["-m", "latent_art_bench.painter_request_timing_v1", "check"],
    ["-m", "latent_art_bench.painter_learned_audit_v1", "check"],
    ["paper/make_icml_learned_tables.py", "--check"],
    ["paper/make_icml_learned_calibration_tables.py", "--check"],
    ["-m", "latent_art_bench.painter_prototype_transfer_v1", "check", "--execute-real"],
    ["paper/make_icml_transfer_tables.py", "--check"],
    ["-m", "latent_art_bench.painter_repeat_covariance_v1", "check", "--execute-real"],
    ["paper/make_icml_covariance_tables.py", "--check"],
]


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def safe_member(name):
    path = Path(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe archive path: {name}")
    if any(part.startswith(".") for part in path.parts):
        raise ValueError(f"hidden file not permitted: {name}")
    if path.parts[0] in {"research_workspace", "tmp", "output"}:
        raise ValueError(f"raw or output directory not permitted: {name}")
    if path == FROZEN / "input/manuscript.pdf":
        return path
    if path.suffix not in {".py", ".json", ".jsonl", ".npz", ".md", ".toml",
                           ".lock", ".ini", ".tex"} and path.name not in {"LICENSE"}:
        raise ValueError(f"unexpected numerical-artifact file: {name}")
    return path


def guarded_check(index, trace_path=None):
    """Deny network and writes; collect opened inputs for the selected command."""
    if not 0 <= index < len(COMMANDS):
        raise ValueError("unknown fixed replay command")
    opened = set()
    external = set()
    tracing = True
    runtime_roots = [Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()]
    system_metadata = {Path("/System/Library/CoreServices/SystemVersion.plist"),
                       Path("/etc/os-release").resolve(), Path("/usr/lib/os-release")}
    mutations = {"os.remove", "os.rename", "os.mkdir", "os.rmdir", "os.chmod",
                 "os.chown", "os.link", "os.symlink", "os.truncate", "os.utime",
                 "os.setxattr", "os.removexattr"}
    processes = {"subprocess.Popen", "os.system", "os.posix_spawn", "os.spawn",
                 "os.exec", "os.fork", "os.forkpty", "pty.spawn"}

    def audit(event, args):
        if not tracing:
            return
        if event.startswith("socket.") or event in processes | mutations:
            raise RuntimeError(f"mutating/network/process operation forbidden: {event}")
        if event != "open" or not tracing:
            return
        name, mode, flags = args
        if ((isinstance(mode, str) and any(c in mode for c in "wax+"))
                or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)):
            raise RuntimeError(f"write forbidden during numerical replay: {name}")
        if isinstance(name, int):
            return
        path = Path(name).resolve()
        if any(path.is_relative_to(prefix) for prefix in runtime_roots):
            external.add(str(path))
        elif path.is_relative_to(ROOT):
            if path.suffix == ".pyc":
                path = Path(importlib.util.source_from_cache(str(path)))
            if path.is_file():
                opened.add(str(path.relative_to(ROOT)))
        elif path in system_metadata:
            external.add(str(path))
        else:
            raise RuntimeError(f"read outside bundle/runtime forbidden: {path}")

    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT / "src"))
    sys.addaudithook(audit)
    command = COMMANDS[index]
    try:
        if command[0] == "-m":
            sys.argv = command[1:]
            runpy.run_module(command[1], run_name="__main__", alter_sys=True)
        else:
            sys.path.insert(0, str(ROOT / "paper"))
            sys.argv = command
            runpy.run_path(str(ROOT / command[0]), run_name="__main__")
    except SystemExit as exc:
        if exc.code not in (None, 0):
            raise
    finally:
        tracing = False
    result = dict(index=index, command=command, inputs=sorted(opened),
                  external_reads=sorted(external))
    if trace_path:
        write_new(trace_path, result)
    print(f"PASS {index + 1}/{len(COMMANDS)}: {' '.join(command)}", flush=True)


def child(index, trace_path=None):
    command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "one", str(index)]
    if trace_path:
        command.extend(["--trace", str(trace_path)])
    subprocess.run(command, cwd=ROOT, check=True)


def discover(finalize_only=False):
    if (RECORDS / "discovery.json").exists():
        raise FileExistsError("preserve the existing discovery record")
    RECORDS.mkdir(parents=True, exist_ok=True)
    if not finalize_only:
        for index in range(len(COMMANDS)):
            child(index, RECORDS / f"trace_{index:02d}.json")
    paths = {str(p.relative_to(ROOT)) for p in (ROOT / "src").rglob("*.py")}
    paths.update({"pyproject.toml", "uv.lock", "LICENSE", "README.md",
                  "scripts/icml_numeric_bundle.py"})
    for index in range(len(COMMANDS)):
        trace = read(RECORDS / f"trace_{index:02d}.json")
        if trace["command"] != COMMANDS[index] or trace["index"] != index:
            raise ValueError("unexpected successful discovery trace")
        paths.update(p for p in trace["inputs"] if not p.startswith(".venv/"))
    paths.update({"reports/icml_review_v1/artifact_inventory.json",
                  "reports/icml_review_v1/artifact_attribution.json"})
    frozen_evidence = read(ROOT / FROZEN / "evidence_manifest.json")
    for name, expected in frozen_evidence.items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"frozen round-03 evidence changed: {name}")
    paths.update(frozen_evidence)
    paths.update(str(FROZEN / name) for name in
                 ["evidence_manifest.json", "inputs.json", "input/manuscript.pdf"])
    files = []
    for name in sorted(paths):
        relative = safe_member(name)
        path = ROOT / relative
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"nonlocal source: {name}")
        files.append(dict(path=name, bytes=path.stat().st_size, sha256=sha(path)))
    write_new(RECORDS / "discovery.json", dict(
        schema="icml-numeric-discovery/1.0", commands=COMMANDS, files=files,
        total_bytes=sum(row["bytes"] for row in files),
        python=platform.python_version(), scope="numerical replay, not pixel re-extraction",
    ))


def add_bytes(archive, name, data):
    info = tarfile.TarInfo(name)
    info.size, info.mode, info.mtime = len(data), 0o644, 0
    archive.addfile(info, io.BytesIO(data))


def build(destination):
    discovery = read(RECORDS / "discovery.json")
    if discovery["commands"] != COMMANDS:
        raise ValueError("replay command inventory changed")
    files = discovery["files"]
    for row in files:
        path = ROOT / safe_member(row["path"])
        if path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise ValueError(f"input changed since discovery: {row['path']}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    # A conservative uncompressed upper bound leaves 512 MiB untouched. This
    # never changes the separate 5 GiB collector guard or permits collection.
    needed = discovery["total_bytes"] + 1024 * len(files) + 512 * 1024**2
    if shutil.disk_usage(destination.parent).free < needed:
        raise OSError("insufficient space for conservative numerical-bundle bound")
    notes = (RECORDS / "BUNDLE_README.md").read_bytes()
    manifest = dict(schema="icml-numeric-bundle/1.0", commands=COMMANDS,
                    files=files + [dict(path="NUMERIC_REPLAY.md", bytes=len(notes),
                                      sha256=hashlib.sha256(notes).hexdigest())],
                    source_discovery_sha256=sha(RECORDS / "discovery.json"),
                    scope="retained numerical results; no exact pixels or model weights")
    with destination.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            with tarfile.open(mode="w|", fileobj=compressed, format=tarfile.USTAR_FORMAT) as tar:
                for row in files:
                    path = ROOT / row["path"]
                    info = tarfile.TarInfo(row["path"])
                    info.size, info.mode, info.mtime = row["bytes"], 0o644, 0
                    with path.open("rb") as source:
                        tar.addfile(info, source)
                add_bytes(tar, "NUMERIC_REPLAY.md", notes)
                add_bytes(tar, MANIFEST,
                          (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
    write_new(RECORDS / "archive.json", dict(
        path=str(destination), bytes=destination.stat().st_size, sha256=sha(destination),
        file_count=len(manifest["files"]) + 1, uncompressed_payload_bytes=(
            discovery["total_bytes"] + len(notes)), status="local; not publicly released",
    ))


def verify():
    manifest = read(ROOT / MANIFEST)
    if manifest["commands"] != COMMANDS:
        raise ValueError("unexpected replay commands")
    names = [row["path"] for row in manifest["files"]]
    if len(names) != len(set(names)):
        raise ValueError("duplicate bundle path")
    for row in manifest["files"]:
        path = ROOT / safe_member(row["path"])
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"nonlocal bundle member: {row['path']}")
        if path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            raise ValueError(f"bundle input changed: {row['path']}")
    actual = {str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file()}
    if actual != set(names) | {MANIFEST}:
        raise ValueError("bundle contains missing or unlisted files")
    frozen_evidence = read(ROOT / FROZEN / "evidence_manifest.json")
    for name, expected in frozen_evidence.items():
        if name not in names or sha(ROOT / safe_member(name)) != expected:
            raise ValueError(f"frozen evidence differs: {name}")
    pdf_sha = read(ROOT / FROZEN / "inputs.json")["sha256"]["manuscript.pdf"]
    if sha(ROOT / FROZEN / "input/manuscript.pdf") != pdf_sha:
        raise ValueError("frozen reviewed PDF differs")
    print(f"Verified {len(names)} exact bundle inputs", flush=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    discovery = sub.add_parser("discover")
    discovery.add_argument("--finalize-only", action="store_true",
                           help="assemble existing successful traces without rerunning checks")
    one = sub.add_parser("one")
    one.add_argument("index", type=int)
    one.add_argument("--trace", type=Path)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("destination", type=Path)
    sub.add_parser("verify")
    sub.add_parser("run")
    args = parser.parse_args()
    if args.action == "discover":
        discover(args.finalize_only)
    elif args.action == "one":
        guarded_check(args.index, args.trace)
    elif args.action == "build":
        build(args.destination.resolve())
    else:
        verify()
        if args.action == "run":
            for index in range(len(COMMANDS)):
                child(index)
            verify()


if __name__ == "__main__":
    main()
