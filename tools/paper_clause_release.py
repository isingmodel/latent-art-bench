"""Additive, history-free numerical release of the prospective clause study.

Only export touches retained maintainer workflow metadata. Public verify is
stdlib-only; public check calls unchanged analysis/report functions. Neither
command acquires images, extracts features, authenticates responses, or publishes.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath

STUDY = "painter_clause_validation_v1"
NAMESPACE = "paper_clause_reproducibility_v1"
RUN = "pcvv1-20260910"
DATA = f"data/manifests/{NAMESPACE}"
ORIGINAL = f"data/manifests/{STUDY}/{RUN}"
REPORT = f"reports/{STUDY}/{RUN}"
DESIGN = f"studies/{STUDY}"
SCHEMA = "painter-clause-numerical-release/1"
ROOT = Path(__file__).resolve().parents[1]

# Actual import closure of unchanged analysis/common plus source kept for review.
# Transport helpers are inert imports; public replay never calls them.
MODULES = {
    "": ("__init__", "io"),
    STUDY: ("__init__", "__main__", "analysis", "common", "collection", "workflow", "precision"),
    "painter_distribution_exploration_v1": ("__init__", "statistics"),
    "painter_distribution_study_v1": (
        "__init__",
        "discovery",
        "inference",
        "reference_delivery",
        "references",
        "statistics",
        "study",
        "transport",
    ),
    "painter_feature_generation_v1": ("__init__", "panel"),
    "painter_feature_generation_v2": ("__init__", "artifacts", "features", "statistics"),
    "painter_naming_geometry_v1": ("__init__", "geometry", "variance"),
    "painter_prompt_study_v1": (
        "__init__",
        "calibration",
        "calibration_record",
        "common",
        "randomization",
        "statistics",
    ),
}
SOURCES = frozenset(
    "/".join(p for p in ("src/latent_art_bench", package, name + ".py") if p)
    for package, names in MODULES.items()
    for name in names
)
DESIGN_NAMES = (
    "PROTOCOL.md",
    "study.json",
    "scenes.json",
    "inputs.json",
    "qualification.json",
    "precision.json",
    "PRECISION.md",
    "PRECOLLECTION_REVIEW.md",
    "PRECOLLECTION_METHOD_REVIEW.md",
    "PRECOLLECTION_IMPLEMENTATION_REVIEW.md",
    "SCIENTIFIC_IMPLEMENTATION_REVIEW.md",
)
CORE = frozenset(
    {
        "LICENSE",
        "pyproject.toml",
        "uv.lock",
        "tools/paper_clause_release.py",
        "tests/test_paper_clause_release.py",
        f"studies/{NAMESPACE}/README.md",
        f"tests/{STUDY}/test_analysis.py",
        f"tests/{STUDY}/test_precision.py",
        "configs/painter_distribution_study_v1/research.json",
        "configs/painter_responsiveness_v2/study.json",
        *(f"{DESIGN}/{name}" for name in DESIGN_NAMES),
        *SOURCES,
    }
)
ORIGINAL_OUTPUTS = frozenset(
    {
        f"{ORIGINAL}/collection_receipt.json",
        f"{ORIGINAL}/measurement_receipt.json",
        f"{REPORT}/analysis.json",
        f"{REPORT}/REPORT.md",
    }
)
# These inert package initializers were outside the scientific freeze's inventory.
# They remain bound to the export and final build source commit.
NOT_FREEZE_BOUND = frozenset(
    {
        "src/latent_art_bench/__init__.py",
        "src/latent_art_bench/painter_feature_generation_v1/__init__.py",
        "LICENSE",
        "tools/paper_clause_release.py",
        "tests/test_paper_clause_release.py",
        f"studies/{NAMESPACE}/README.md",
    }
)
GENERATED = {"README.md", "CLAUSE_RELEASE_MANIFEST.json", "SHA256SUMS"}
ROW_FIELDS = (
    "request_id",
    "sequence",
    "experiment",
    "route",
    "template_id",
    "content_class",
    "repetition",
    "arm",
    "polarity",
    "block_id",
    "block_order",
    "within_block",
    "pipeline",
    "status",
    "values",
    "scaled",
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
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
        raise ValueError("private, history, raw, or Korean path is prohibited")
    return PurePosixPath(value)


def no_symlinks(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("symlink path is prohibited")


def screen(raw, suffix):
    if suffix not in {".json", ".jsonl", ".md", ".toml", ".lock"}:
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


def read_bytes(root, relative):
    path = root / portable(relative)
    no_symlinks(path)
    if not path.is_file():
        raise ValueError(f"required regular file absent: {relative}")
    return path.read_bytes()


def public_bytes(root, relative):
    raw = read_bytes(root, relative)
    screen(raw, PurePosixPath(relative).suffix)
    return raw


def read(root, relative):
    return json.loads(read_bytes(root, relative))


def records_map(records):
    if not isinstance(records, list) or not records:
        raise ValueError("nonempty hash-binding records required")
    result = {}
    for row in records:
        path, sha = row["path"], row["sha256"]
        portable(path)
        if path in result or not re.fullmatch(r"[0-9a-f]{64}", str(sha)):
            raise ValueError("duplicate or invalid hash binding")
        result[path] = sha
    return result


def git_bytes(root, revision, path):
    result = subprocess.run(["git", "show", f"{revision}:{path}"], cwd=root, capture_output=True)
    if result.returncode:
        raise ValueError(f"input absent at required source revision: {path}")
    return result.stdout


def clean_sources(root, files):
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    for path, raw in files.items():
        if git_bytes(root, commit, path) != raw or git_bytes(root, "", path) != raw:
            raise ValueError(f"commit exact working/index bytes first: {path}")
    return commit


def project_rows(rows):
    result = []
    for row in rows:
        selected = {key: row[key] for key in ROW_FIELDS}
        observed = row.get("observed")
        selected["observed"] = (
            None
            if observed is None
            else {
                **{key: observed[key] for key in ("width", "height", "format")},
                "reported": {"quality": observed.get("reported", {}).get("quality")},
            }
        )
        result.append(selected)
    return result


def scientific_result(root, bundle):
    # Deliberately do not import workflow, collection, or the old project CLI.
    sys.path.insert(0, str(root / "src"))
    from latent_art_bench.painter_clause_validation_v1 import analysis, common

    requests = common.requests(root)
    config = common.configuration(root)
    if bundle["requests"] != requests:
        raise ValueError("exported assignment/payloads differ from the fixed design")
    return analysis.analyze(
        requests,
        bundle["rows"],
        read(root, f"{DESIGN}/inputs.json"),
        config,
        collection_receipt=bundle["collection"],
    ), analysis.report_text


def require_local_modules(root):
    """Do not let an editable install or cached foreign module mask copied source."""
    boundary = (root / "src").resolve()
    for name, module in tuple(sys.modules.items()):
        if name == "latent_art_bench" or name.startswith("latent_art_bench."):
            location = getattr(module, "__file__", None)
            if location is None or not Path(location).resolve().is_relative_to(boundary):
                raise ValueError("cached scientific module is outside the release source tree")


def terminal_inputs(root):
    """Local only: verify terminal bindings without reading any raw response body."""
    from latent_art_bench.painter_clause_validation_v1 import workflow

    freeze, requests, _, _, collection = workflow.collection_inputs(root, RUN)
    receipt = read(root, f"{ORIGINAL}/measurement_receipt.json")
    expected_paths = {
        f"{ORIGINAL}/measurements.jsonl",
        f"{REPORT}/analysis.json",
        f"{REPORT}/REPORT.md",
        f"research_workspace/{STUDY}/{RUN}/measurement_started.json",
    }
    outputs = records_map(receipt["outputs"])
    if (
        receipt.get("schema") != "painter-clause-validation-measurement/1"
        or receipt.get("run_id") != RUN
        or outputs.keys() != expected_paths
        or receipt["collection_receipt_sha256"]
        != digest(read_bytes(root, f"{ORIGINAL}/collection_receipt.json"))
    ):
        raise ValueError("terminal measurement receipt identity or output inventory differs")
    for path, expected in outputs.items():
        if digest(read_bytes(root, path)) != expected:
            raise ValueError("terminal measurement output hash differs")
    rows = [
        json.loads(line) for line in read_bytes(root, f"{ORIGINAL}/measurements.jsonl").splitlines()
    ]
    if len(requests) != 288 or len(rows) != 864:
        raise ValueError("every allocated request and pipeline status is required")
    return freeze, requests, rows, collection


def export_paths(release_id):
    identifier(release_id)
    return {f"{DATA}/{release_id}/{name}" for name in ("inputs.json", "export_manifest.json")}


def write_new(path, raw):
    no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def export(root, release_id):
    """Create a numerical projection once, after committed terminal results exist."""
    root = Path(root).absolute()
    no_symlinks(root)
    paths = export_paths(release_id)
    if any((root / p).exists() or (root / p).is_symlink() for p in paths):
        raise FileExistsError("retain existing create-once numerical export")
    freeze, requests, rows, collection = terminal_inputs(root)
    frozen = records_map(freeze["inputs"])
    originals = {p: public_bytes(root, p) for p in sorted(CORE | ORIGINAL_OUTPUTS)}
    if not (CORE - NOT_FREEZE_BOUND) <= frozen.keys():
        raise ValueError("scientific release source/design is missing from the study freeze")
    for path in CORE - NOT_FREEZE_BOUND:
        if digest(originals[path]) != frozen[path]:
            raise ValueError("frozen source/design differs from copied bytes")
        if git_bytes(root, freeze["recorded_git_commit"], path) != originals[path]:
            raise ValueError("frozen source commit differs")
    commit = clean_sources(root, originals)
    bundle = dict(
        schema="painter-clause-compact-inputs/1",
        run_id=RUN,
        requests=requests,
        rows=project_rows(rows),
        collection=collection,
    )
    raw = encoded(bundle)
    screen(raw, ".json")
    actual, render = scientific_result(root, bundle)
    expected = json.loads(originals[f"{REPORT}/analysis.json"])
    if (
        encoded(actual) != encoded(expected)
        or render(actual).encode() != originals[f"{REPORT}/REPORT.md"]
    ):
        raise ValueError("compact projection fails exact original numerical/report replay")
    source_paths = {
        f"{ORIGINAL}/{name}"
        for name in (
            "freeze.json",
            "planned_requests.jsonl",
            "measurements.jsonl",
            "collection_receipt.json",
            "measurement_receipt.json",
        )
    } | {f"{REPORT}/analysis.json", f"{REPORT}/REPORT.md"}
    provenance = dict(
        schema="painter-clause-export/1",
        release_id=release_id,
        run_id=RUN,
        export_source_commit=commit,
        study_source_commit=freeze["recorded_git_commit"],
        qualified_source_commit=freeze["qualified_source_commit"],
        original_freeze_sha256=digest(read_bytes(root, f"{ORIGINAL}/freeze.json")),
        private_proxy_snapshot_sha256=digest(encoded(freeze["proxy_snapshot"])),
        freeze_environment=freeze["environment"],
        frozen_input_bindings=frozen,
        original_terminal_hashes={p: digest(read_bytes(root, p)) for p in sorted(source_paths)},
        files={
            **{p: digest(b) for p, b in originals.items()},
            f"{DATA}/{release_id}/inputs.json": digest(raw),
        },
        expected_numeric_sha256=digest(encoded(expected)),
        transformation="Project measurement rows onto the explicit consumed identity, numeric "
        "and delivery fields; preserve assignment and collection metadata verbatim.",
        coverage="Exact unchanged clause-v1 primary, all secondary summaries and report; "
        "no private response authentication, extraction or historical-result replay.",
    )
    manifest = encoded(provenance)
    screen(manifest, ".json")
    if clean_sources(root, originals) != commit:
        raise ValueError("source changed during export")
    write_new(root / f"{DATA}/{release_id}/inputs.json", raw)
    write_new(root / f"{DATA}/{release_id}/export_manifest.json", manifest)
    return dict(status="exported", release_id=release_id, requests=len(requests), rows=len(rows))


def gather(root, release_id):
    paths = CORE | ORIGINAL_OUTPUTS | export_paths(release_id)
    files = {p: public_bytes(root, p) for p in sorted(paths)}
    manifest_path = f"{DATA}/{release_id}/export_manifest.json"
    descriptor = json.loads(files[manifest_path])
    if (
        descriptor.get("schema") != "painter-clause-export/1"
        or descriptor.get("release_id") != release_id
        or descriptor.get("run_id") != RUN
        or set(descriptor.get("files", {})) != paths - {manifest_path}
    ):
        raise ValueError("export descriptor identity or exact allowlist differs")
    for path, sha in descriptor["files"].items():
        if digest(files[path]) != sha:
            raise ValueError(f"export payload hash differs: {path}")
    for field in ("export_source_commit", "study_source_commit", "qualified_source_commit"):
        if not re.fullmatch(r"[0-9a-f]{40}", str(descriptor.get(field))):
            raise ValueError("source commit identity missing")
    frozen = descriptor.get("frozen_input_bindings", {})
    if not (CORE - NOT_FREEZE_BOUND) <= frozen.keys():
        raise ValueError("public provenance omits scientific bindings")
    for path in CORE - NOT_FREEZE_BOUND:
        if frozen[path] != digest(files[path]):
            raise ValueError("public scientific source differs from frozen provenance")
    if (
        descriptor["original_terminal_hashes"][f"{ORIGINAL}/freeze.json"]
        != descriptor["original_freeze_sha256"]
    ):
        raise ValueError("freeze provenance hash mismatch")
    for path in ORIGINAL_OUTPUTS:
        if descriptor["original_terminal_hashes"][path] != digest(files[path]):
            raise ValueError("original terminal output provenance mismatch")
    collection = json.loads(files[f"{ORIGINAL}/collection_receipt.json"])
    measurement = json.loads(files[f"{ORIGINAL}/measurement_receipt.json"])
    measured_outputs = records_map(measurement["outputs"])
    required_outputs = {
        f"{ORIGINAL}/measurements.jsonl",
        f"{REPORT}/analysis.json",
        f"{REPORT}/REPORT.md",
        f"research_workspace/{STUDY}/{RUN}/measurement_started.json",
    }
    if (
        collection.get("freeze_sha256") != descriptor["original_freeze_sha256"]
        or measurement.get("collection_receipt_sha256")
        != digest(files[f"{ORIGINAL}/collection_receipt.json"])
        or measured_outputs.keys() != required_outputs
    ):
        raise ValueError("public terminal receipt chain differs")
    for path in required_outputs - {f"research_workspace/{STUDY}/{RUN}/measurement_started.json"}:
        if measured_outputs[path] != descriptor["original_terminal_hashes"][path]:
            raise ValueError("public measurement provenance differs")
    return files, descriptor


def checksum_text(files):
    return "".join(f"{digest(raw)}  {path}\n" for path, raw in sorted(files.items())).encode()


def readme(release_id, draft):
    return f"""# Prospective painter-clause numerical addendum: {release_id}

{"DRAFT local QA artifact." if draft else "Final local build; publication is a separate action."}
This standalone package replays only painter_clause_validation_v1 from retained
compact vectors, using unchanged qualified analysis and report functions. The
original pprv1-20260910 and naming-geometry releases remain necessary to reproduce
historical results. No original release is modified or replaced. Paper assets
are separate and are not needed for this numerical replay.

Verify before installing, then run the dedicated adapter (not the study CLI):

```sh
python tools/paper_clause_release.py verify --root .
uv sync --locked --python 3.13.11 --extra analysis --extra dev
uv run --locked python tools/paper_clause_release.py check --root .
uv run --locked pytest -q --import-mode=importlib tests/test_paper_clause_release.py \\
  tests/painter_clause_validation_v1/test_analysis.py \\
  tests/painter_clause_validation_v1/test_precision.py
```

The optional tests also require a Git executable for temporary provenance
fixtures; maintainer-only terminal-workflow tests are explicitly skipped in this
compact package. Public verify/check require neither Git nor its history.

The descriptor's freeze_environment records the study runtime. Python 3.13.11
matches its recorded interpreter. Installation may download dependencies.
Public verify uses only Python's standard library. Public check performs local
numerical computation: no Git, proxy,
network, response bodies, feature extraction, or image files are required.
The extra collection/workflow source is provided for inspection, not as a
supported generation entry point in this numerical package.

Every allocated slot/pipeline status, both primary tests, their withholding,
all secondary summaries, delivery metadata and the report are checked exactly.
No numerical tolerance or post-result correction is introduced. Cross-platform
floating differences fail exact replay and must be reported, not normalized away.

The export descriptor binds source commits, original terminal hashes and the
explicit projection. The original private freeze/proxy content is omitted;
its fingerprints and safe source bindings are provenance only. Collection and
measurement receipt path/hash metadata are retained verbatim where safe; absent
referenced workspaces are intentionally not copied or traversed by public check.
Checksums authenticate bytes relative to a trusted release checksum, not absent
raw responses or paintings. Code/numerical-export licensing grants no rights to
absent underlying artwork. No perceptual validity, independent capture, stable
remote checkpoint or independent-investigator claim follows from replay.

Only explicit allowlisted files are present. No Git history, media, credentials,
local proxy state, model weights, source checkouts or Korean drafts are included.
Reviews and implementation were maintainer-run LLM work with disclosed assistance.
""".encode()


def build(root, output_root, release_id, *, draft=False):
    root, output_root = Path(root).absolute(), Path(output_root).absolute()
    identifier(release_id)
    no_symlinks(root)
    no_symlinks(output_root)
    stage, archive = output_root / release_id, output_root / f"{release_id}.tar.gz"
    checksum = output_root / f"{release_id}.tar.gz.sha256"
    if any(p.exists() or p.is_symlink() for p in (stage, archive, checksum)):
        raise FileExistsError("create-once staging/archive/checksum already exists")
    files, descriptor = gather(root, release_id)
    commit = None if draft else clean_sources(root, files)
    if not draft:
        for p in CORE - NOT_FREEZE_BOUND:
            if git_bytes(root, descriptor["study_source_commit"], p) != files[p]:
                raise ValueError("copied scientific source differs from study commit")
    files["README.md"] = readme(release_id, draft)
    files["CLAUSE_RELEASE_MANIFEST.json"] = encoded(
        dict(
            schema=SCHEMA,
            release_id=release_id,
            draft=draft,
            build_source_commit=commit,
            export_source_commit=descriptor["export_source_commit"],
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
    return dict(
        status="built",
        draft=draft,
        stage=str(stage),
        archive=str(archive),
        checksum=str(checksum),
        payload_files=len(files),
    )


def verify(root, *, runtime=False):
    """Stdlib package integrity check; no source import, Git or external state."""
    root = Path(root).absolute()
    no_symlinks(root)
    manifest = read(root, "CLAUSE_RELEASE_MANIFEST.json")
    if manifest.get("schema") != SCHEMA or type(manifest.get("draft")) is not bool:
        raise ValueError("invalid release manifest")
    if (manifest["draft"] and manifest.get("build_source_commit") is not None) or (
        not manifest["draft"]
        and not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("build_source_commit")))
    ):
        raise ValueError("final/draft source provenance is invalid")
    release_id = identifier(manifest.get("release_id"))
    files, descriptor = gather(root, release_id)
    files["README.md"] = public_bytes(root, "README.md")
    if (
        set(manifest.get("files", {})) != files.keys()
        or any(manifest["files"][p] != digest(raw) for p, raw in files.items())
        or manifest.get("export_source_commit") != descriptor["export_source_commit"]
    ):
        raise ValueError("release payload inventory/hash mismatch")
    files["CLAUSE_RELEASE_MANIFEST.json"] = read_bytes(root, "CLAUSE_RELEASE_MANIFEST.json")
    if read_bytes(root, "SHA256SUMS") != checksum_text(files):
        raise ValueError("release SHA256SUMS mismatch")
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
        observed.update((parent / name).relative_to(root).as_posix() for name in names)
    if observed != files.keys() | {"SHA256SUMS"}:
        raise ValueError("unlisted or missing release files")
    return dict(
        status="verified",
        release_id=release_id,
        payload_files=len(observed),
        runtime_directories_ignored=runtime,
        raw_response_authentication=False,
    )


def check(root):
    root = Path(root).absolute()
    verified = verify(root, runtime=True)
    release_id = verified["release_id"]
    descriptor = read(root, f"{DATA}/{release_id}/export_manifest.json")
    bundle = read(root, f"{DATA}/{release_id}/inputs.json")
    if bundle.get("schema") != "painter-clause-compact-inputs/1" or bundle.get("run_id") != RUN:
        raise ValueError("unknown compact input identity")
    if bundle["collection"] != read(root, f"{ORIGINAL}/collection_receipt.json"):
        raise ValueError("compact collection metadata differs from original receipt")
    require_local_modules(root)
    actual, render = scientific_result(root, bundle)
    require_local_modules(root)
    expected = read(root, f"{REPORT}/analysis.json")
    if digest(encoded(expected)) != descriptor["expected_numeric_sha256"] or encoded(
        actual
    ) != encoded(expected):
        raise ValueError("exact primary/secondary numerical replay differs")
    if render(actual).encode() != read_bytes(root, f"{REPORT}/REPORT.md"):
        raise ValueError("exact report replay differs")
    return dict(
        status="exact_numeric_and_report_replay",
        release_id=release_id,
        primary_endpoints=len(actual["primary"]),
        views=len(actual["views"]),
        planned=actual["planned"],
        raw_response_authentication=False,
        numerical_sha256=digest(encoded(actual)),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for command in ("export", "build", "verify", "check"):
        action = sub.add_parser(command)
        action.add_argument(
            "--root", type=Path, default=ROOT if command == "export" else Path.cwd()
        )
        if command in ("export", "build"):
            action.add_argument("--release-id", required=True)
        if command == "build":
            action.add_argument("--output-root", required=True, type=Path)
            action.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    if args.action == "export":
        result = export(args.root, args.release_id)
    elif args.action == "build":
        result = build(args.root, args.output_root, args.release_id, draft=args.draft)
    elif args.action == "verify":
        result = verify(args.root)
    else:
        result = check(args.root)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
