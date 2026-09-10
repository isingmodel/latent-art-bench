"""Separate numerical-only fixed-map v2 release; never collect or measure images.

Only local export reads the retained operational workflow. Public verification is
stdlib-only and public replay calls numerical functions without formal writers.
The earlier published exporter is an unchanged stdlib helper dependency.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib
import importlib.util
import io
import json
import os
import re
import sys
import tarfile
from pathlib import Path

HELPER = "tools/paper_map_release.py"
HELPER_SHA256 = "e8f1a0d17d291554b6c2b3dee1477d5f37c2742a9adc1d7d5af118bd9cfb5ad8"
_helper_path = Path(__file__).absolute().with_name("paper_map_release.py")
if any(p.is_symlink() for p in (_helper_path, *_helper_path.parents)):
    raise ValueError("symlink helper dependency prohibited")
if hashlib.sha256(_helper_path.read_bytes()).hexdigest() != HELPER_SHA256:
    raise ValueError("immutable helper dependency hash differs")
_spec = importlib.util.spec_from_file_location("_sealed_map_release_helpers", _helper_path)
base = importlib.util.module_from_spec(_spec)
_bytecode_flag = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    _spec.loader.exec_module(base)
finally:
    sys.dont_write_bytecode = _bytecode_flag

STUDY = "painter_map_validation_v2"
RUN = "pmv2-20260910"
RELEASE_ID = "pmv2r-20260910"
NAMESPACE = "paper_map_validation_reproducibility_v2"
DESIGN = f"studies/{STUDY}"
ORIGINAL = f"data/manifests/{STUDY}/{RUN}"
REPORT = f"reports/{STUDY}/{RUN}"
QUALIFICATION = f"{DESIGN}/pmvqv2-20260910"
EXPORT = f"data/manifests/{NAMESPACE}/{RELEASE_ID}"
TOOL = "tools/paper_map_validation_release.py"
MANIFEST = "MAP_VALIDATION_RELEASE_MANIFEST.json"
SCHEMA = "painter-map-validation-numerical-release/2"

# Fixed import closure of analysis/common/precision; operational files are kept
# for inspection only. Their private runtime dependency closure is not exported.
MODULES = {
    "": ("__init__", "io"),
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
    "painter_prompt_study_v1": (
        "__init__",
        "calibration",
        "calibration_record",
        "common",
        "randomization",
        "statistics",
    ),
    "painter_map_validation_v1": ("__init__", "precision"),
    STUDY: (
        "__init__",
        "analysis",
        "common",
        "precision",
        "collection",
        "workflow",
        "metadata",
        "__main__",
    ),
}
SOURCES = frozenset(
    "/".join(p for p in ("src/latent_art_bench", package, name + ".py") if p)
    for package, names in MODULES.items()
    for name in names
)
CORE = frozenset(
    {
        *SOURCES,
        "LICENSE",
        "pyproject.toml",
        "uv.lock",
        HELPER,
        TOOL,
        "tests/test_paper_map_validation_release.py",
        "tests/painter_map_validation_v1/test_precision.py",
        *(
            f"tests/{STUDY}/{n}"
            for n in ("test_analysis.py", "test_analysis_oracle.py", "test_precision.py")
        ),
        *(
            f"{DESIGN}/{n}"
            for n in (
                "PROTOCOL.md",
                "TECHNICAL_PROTOCOL.md",
                "DECISION.md",
                "PRECISION_PROTOCOL.md",
                "PRECISION_REVIEW.md",
                "ANALYSIS_REVIEW.md",
                "OPERATIONAL_REVIEW.md",
                "PRECOLLECTION_REVIEW.md",
                "study.json",
                "scenes.json",
                "inputs.json",
                "qualification.json",
            )
        ),
        *(f"{QUALIFICATION}/{n}" for n in ("RUN.json", "precision.json", "PRECISION.md")),
        *(f"{base.RESULT}/{n}" for n in ("RUN.json", "precision.json", "PRECISION.md")),
        f"{base.STUDY}/PRECISION_PROTOCOL.md",
        f"{base.GEOMETRY}/inputs.json",
        f"{base.GEOMETRY}/analysis.json",
    }
)
UNBOUND = frozenset({"LICENSE", HELPER, TOOL, "tests/test_paper_map_validation_release.py"})
OUTPUTS = frozenset(
    {
        f"{ORIGINAL}/planned_requests.jsonl",
        f"{ORIGINAL}/measurement_receipt.json",
        f"{REPORT}/analysis.json",
        f"{REPORT}/REPORT.md",
    }
)
EXPORTS = frozenset({f"{EXPORT}/inputs.json", f"{EXPORT}/export_manifest.json"})
GENERATED = frozenset({"README.md", MANIFEST, "SHA256SUMS"})
ROW_FIELDS = (
    "request_id",
    "sequence",
    "experiment",
    "route",
    "template_id",
    "content_class",
    "repetition",
    "arm",
    "painter_id",
    "block_id",
    "block_order",
    "within_block",
    "pipeline",
    "status",
    "feature_names",
    "values",
    "scaled",
)
REASONS = (
    "collection_stopped",
    "identity_contract_unverified",
    "duration_contract_failed",
    "admission_timing_contract_failed",
    "incomplete_delivery_grid",
    "unresolved_paid_accounting",
    "terminal_budget_exceeded",
)


def read(root, path):
    return json.loads(public_bytes(root, path))


def public_bytes(root, path):
    raw = base.file_bytes(root, path)
    if path.endswith(".jsonl"):
        for line in raw.splitlines():
            base.screen(line, ".json")
    return raw


def collection_projection(receipt):
    result = {k: receipt[k] for k in ("analysis_eligible", "analysis_unavailability_reasons")}
    reasons = result["analysis_unavailability_reasons"]
    if (
        type(result["analysis_eligible"]) is not bool
        or not isinstance(reasons, list)
        or any(r not in REASONS for r in reasons)
        or reasons != [r for r in REASONS if r in reasons]
        or result["analysis_eligible"] != (not reasons)
    ):
        raise ValueError("exact attested collection eligibility and ordered reasons required")
    return result


def project_rows(rows):
    return [{key: row[key] for key in ROW_FIELDS} for row in rows]


def numerical_modules(root):
    base.require_local_modules(root)
    sys.path.insert(0, str(Path(root) / "src"))
    importlib.invalidate_caches()
    modules = tuple(
        importlib.import_module(f"latent_art_bench.{STUDY}.{name}")
        for name in ("analysis", "common", "precision")
    )
    base.require_local_modules(root)
    return modules


def observed_replay(root, bundle):
    analysis, common, _ = numerical_modules(root)
    requests = [
        json.loads(line)
        for line in base.file_bytes(root, f"{ORIGINAL}/planned_requests.jsonl").splitlines()
    ]
    inputs = read(root, f"{DESIGN}/inputs.json")
    if base.encoded(inputs) != base.encoded(analysis.load_inputs(root)):
        raise ValueError("compact input bodies differ from immutable numerical origins")
    if set(bundle) != {"schema", "run_id", "rows", "collection_attestation"} or (
        bundle["schema"] != "painter-map-validation-public-inputs/2" or bundle["run_id"] != RUN
    ):
        raise ValueError("unexpected compact numerical payload")
    if any(set(row) != set(ROW_FIELDS) for row in bundle["rows"]):
        raise ValueError("exact projected measurement fields required")
    if bundle["collection_attestation"] != collection_projection(bundle["collection_attestation"]):
        raise ValueError("unexpected collection attestation fields")
    result = analysis.analyze(
        requests,
        bundle["rows"],
        inputs,
        common.configuration(root),
        collection_receipt=bundle["collection_attestation"],
    )
    return result, analysis.report_text


def terminal_inputs(root):
    """Local-only receipt/body/budget checks; never extraction or a formal writer."""
    numerical_modules(root)
    workflow = importlib.import_module(f"latent_art_bench.{STUDY}.workflow")
    freeze, requests, _, _, collection = workflow.collection_inputs(root, RUN)
    measurement = read(root, f"{ORIGINAL}/measurement_receipt.json")
    expected = {
        f"{ORIGINAL}/measurements.jsonl",
        f"{REPORT}/analysis.json",
        f"{REPORT}/REPORT.md",
        f"research_workspace/{STUDY}/{RUN}/measurement_started.json",
    }
    bindings = base.binding_map(measurement["outputs"])
    if (
        measurement.get("schema") != "painter-map-validation-measurement/2"
        or measurement.get("run_id") != RUN
        or bindings.keys() != expected
        or measurement["collection_receipt_sha256"]
        != base.digest(base.file_bytes(root, f"{ORIGINAL}/collection_receipt.json", public=False))
    ):
        raise ValueError("terminal measurement receipt chain or exact inventory differs")
    for path, sha in bindings.items():
        if base.digest(base.file_bytes(root, path, public=False)) != sha:
            raise ValueError("terminal measurement output hash differs")
    rows = [
        json.loads(line)
        for line in base.file_bytes(
            root, f"{ORIGINAL}/measurements.jsonl", public=False
        ).splitlines()
    ]
    if len(rows) != 240 or len(requests) != 240:
        raise ValueError("complete allocated terminal status inventory required")
    return freeze, requests, rows, collection


def export(root):
    """Create one compact public input after local terminal checks and exact replay."""
    root = Path(root).absolute()
    if (root / EXPORT).exists() or (root / EXPORT).is_symlink():
        raise FileExistsError("preserve existing create-once numerical export")
    freeze, requests, rows, collection = terminal_inputs(root)
    files = {p: public_bytes(root, p) for p in sorted(CORE | OUTPUTS)}
    frozen = base.binding_map(freeze["inputs"])
    if not CORE - UNBOUND <= frozen.keys():
        raise ValueError("public scientific core is absent from the frozen inventory")
    for path in CORE - UNBOUND:
        if (
            base.digest(files[path]) != frozen[path]
            or base.git_bytes(root, freeze["recorded_git_commit"], path) != files[path]
        ):
            raise ValueError("frozen scientific source or commit differs")
    if requests != [
        json.loads(line) for line in files[f"{ORIGINAL}/planned_requests.jsonl"].splitlines()
    ]:
        raise ValueError("terminal assigned requests differ from retained original bytes")
    bundle = dict(
        schema="painter-map-validation-public-inputs/2",
        run_id=RUN,
        rows=project_rows(rows),
        collection_attestation=collection_projection(collection),
    )
    raw = base.encoded(bundle)
    base.screen(raw, ".json")
    actual, renderer = observed_replay(root, bundle)
    if (
        base.encoded(actual) != base.encoded(json.loads(files[f"{REPORT}/analysis.json"]))
        or renderer(actual).encode() != files[f"{REPORT}/REPORT.md"]
    ):
        raise ValueError("compact projection fails exact unchanged analysis/report replay")
    fingerprints = {
        f"{ORIGINAL}/{name}"
        for name in ("freeze.json", "collection_receipt.json", "measurements.jsonl")
    } | OUTPUTS
    descriptor = dict(
        schema="painter-map-validation-export/2",
        release_id=RELEASE_ID,
        run_id=RUN,
        study_source_commit=freeze["recorded_git_commit"],
        qualified_source_commit=freeze["qualified_source_commit"],
        freeze_environment=freeze["environment"],
        frozen_input_bindings=frozen,
        original_terminal_hashes={
            p: base.digest(base.file_bytes(root, p, public=False)) for p in sorted(fingerprints)
        },
        omitted_binding_bodies=sorted(set(frozen) - set(files)),
        private_collection_budget_and_acquisition="locally verified; public attestation only",
        files={p: base.digest(value) for p, value in sorted(files.items())},
        projected_input_sha256=base.digest(raw),
        export_source_commit=base.clean_sources(root, files),
    )
    encoded = base.encoded(descriptor)
    base.screen(encoded, ".json")
    if base.clean_sources(root, files) != descriptor["export_source_commit"]:
        raise ValueError("source changed before export")
    base.write_new(root / EXPORT / "inputs.json", raw)
    base.write_new(root / EXPORT / "export_manifest.json", encoded)
    gather(root)
    if base.clean_sources(root, files) != descriptor["export_source_commit"]:
        raise ValueError("source changed during export; preserve create-once outputs")
    return dict(status="exported", release_id=RELEASE_ID, rows=240)


def validate_qualification(files):
    """Stdlib lineage checks; omitted bodies are fingerprints, never public claims."""
    base.validate_science(files)
    runs = []
    for folder, schema in (
        (base.RESULT, "painter-map-precision-run/1"),
        (QUALIFICATION, "painter-map-precision-v2-run/1"),
    ):
        run, result = (json.loads(files[f"{folder}/{n}"]) for n in ("RUN.json", "precision.json"))
        if run.get("schema") != schema or any(result.get(k) != v for k, v in run.items()):
            raise ValueError("qualification RUN/result provenance differs")
        bindings = base.binding_map(run["source_bindings"])
        expected = base.INCLUDED_BOUND | base.OMITTED
        if folder == QUALIFICATION:
            expected = expected | {
                f"src/latent_art_bench/{STUDY}/precision.py",
                f"src/latent_art_bench/{STUDY}/__init__.py",
                f"tests/{STUDY}/test_precision.py",
                f"{DESIGN}/DECISION.md",
                f"{DESIGN}/PRECISION_PROTOCOL.md",
                *(f"{base.RESULT}/{n}" for n in ("RUN.json", "precision.json", "PRECISION.md")),
            }
        if set(bindings) != expected or not re.fullmatch(
            r"[0-9a-f]{40}", str(run["source_commit"])
        ):
            raise ValueError("qualification source identity or exact binding inventory differs")
        for p, sha in bindings.items():
            if p in files and base.digest(files[p]) != sha:
                raise ValueError("included qualification source/input binding differs")
        runs.append((run, result))
    previous, current = runs
    lineage = current[0]["predecessor"]
    if (
        lineage["source_commit"] != previous[0]["source_commit"]
        or lineage["decision"] != "stop_inferential_proposal"
        or base.binding_map(lineage["artifacts"])
        != {
            f"{base.RESULT}/{n}": base.digest(files[f"{base.RESULT}/{n}"])
            for n in ("RUN.json", "precision.json", "PRECISION.md")
        }
        or current[0]["cross_version_confidence_claim"] is not False
        or previous[1]["qualification"]["decision"] != "stop_inferential_proposal"
    ):
        raise ValueError("retained failed predecessor lineage differs")
    q = current[1]["qualification"]
    cells = [(r["R"], r["shape"], r["mean"], r["regime"]) for r in q["records"]]
    expected_cells = {
        (10, sh, m, rg)
        for sh in ("gaussian_shaped", "t5_shaped", "lognormal_shaped")
        for m in ("T1", "midpoint", "T2")
        for rg in ("baseline", "high_positive", "low_negative")
    }
    if (
        len(cells) != 27
        or set(cells) != expected_cells
        or any(type(r["trials"]) is not int or r["trials"] != 10000 for r in q["records"])
        or q["decision"] != "qualified_proxy_only"
        or type(q["selected_R"]) is not int
        or q["selected_R"] != 10
        or type(q["selected_outputs"]) is not int
        or q["selected_outputs"] != 240
    ):
        raise ValueError("complete passing R10 qualification required")
    return current[1]


def gather(root):
    files = {p: public_bytes(root, p) for p in sorted(CORE | OUTPUTS | EXPORTS)}
    descriptor = json.loads(files[f"{EXPORT}/export_manifest.json"])
    if set(descriptor) != {
        "schema",
        "release_id",
        "run_id",
        "study_source_commit",
        "qualified_source_commit",
        "freeze_environment",
        "frozen_input_bindings",
        "original_terminal_hashes",
        "omitted_binding_bodies",
        "private_collection_budget_and_acquisition",
        "files",
        "projected_input_sha256",
        "export_source_commit",
    } or (
        descriptor.get("schema") != "painter-map-validation-export/2"
        or descriptor.get("release_id") != RELEASE_ID
        or descriptor.get("run_id") != RUN
    ):
        raise ValueError("fixed export identity required")
    for key in ("study_source_commit", "qualified_source_commit", "export_source_commit"):
        if not re.fullmatch(r"[0-9a-f]{40}", str(descriptor.get(key))):
            raise ValueError("missing committed export/source identity")
    if descriptor["private_collection_budget_and_acquisition"] != (
        "locally verified; public attestation only"
    ):
        raise ValueError("private collection verification scope differs")
    environment = descriptor["freeze_environment"]
    if set(environment) != {
        "python",
        "numpy",
        "scipy",
        "Pillow",
        "httpx",
        "PyWavelets",
        "scikit-image",
    } or any(not isinstance(value, str) or not value for value in environment.values()):
        raise ValueError("exact public frozen-runtime fields required")
    original = {p: files[p] for p in CORE | OUTPUTS}
    if descriptor["files"] != {p: base.digest(v) for p, v in original.items()} or (
        descriptor["projected_input_sha256"] != base.digest(files[f"{EXPORT}/inputs.json"])
    ):
        raise ValueError("exact exported source/output inventory or input digest differs")
    frozen = descriptor["frozen_input_bindings"]
    base.binding_map([dict(path=p, sha256=s) for p, s in frozen.items()])
    if (
        not CORE - UNBOUND <= frozen.keys()
        or any(frozen[p] != base.digest(files[p]) for p in CORE - UNBOUND)
        or descriptor["omitted_binding_bodies"] != sorted(set(frozen) - set(original))
    ):
        raise ValueError("frozen scientific bytes or stated omissions differ")
    qualified = json.loads(files[f"{DESIGN}/qualification.json"])
    if (
        qualified.get("schema") != "painter-map-validation-qualification/2"
        or qualified.get("qualified") is not True
        or qualified.get("source_commit") != descriptor["qualified_source_commit"]
    ):
        raise ValueError("operational qualification source identity differs")
    qualified_bindings = base.binding_map(qualified["source_bindings"])
    if not (CORE - UNBOUND - {f"{DESIGN}/qualification.json"}) <= qualified_bindings.keys():
        raise ValueError("operational qualification omits public scientific source")
    for records in (
        qualified["source_bindings"],
        *(
            json.loads(files[f"{folder}/RUN.json"])["source_bindings"]
            for folder in (base.RESULT, QUALIFICATION)
        ),
    ):
        bound = base.binding_map(records)
        if any(frozen.get(path) != sha for path, sha in bound.items()):
            raise ValueError("transitive source-binding fingerprints disagree")
    terminal = descriptor["original_terminal_hashes"]
    required = OUTPUTS | {
        f"{ORIGINAL}/{n}" for n in ("freeze.json", "collection_receipt.json", "measurements.jsonl")
    }
    if set(terminal) != required:
        raise ValueError("exact terminal provenance inventory required")
    base.binding_map([dict(path=p, sha256=s) for p, s in terminal.items()])
    if any(terminal[p] != base.digest(files[p]) for p in OUTPUTS):
        raise ValueError("original public output binding differs")
    measured = json.loads(files[f"{ORIGINAL}/measurement_receipt.json"])
    bindings = base.binding_map(measured["outputs"])
    marker = f"research_workspace/{STUDY}/{RUN}/measurement_started.json"
    if (
        measured["schema"] != "painter-map-validation-measurement/2"
        or measured["run_id"] != RUN
        or measured["collection_receipt_sha256"] != terminal[f"{ORIGINAL}/collection_receipt.json"]
        or set(bindings)
        != {
            marker,
            f"{ORIGINAL}/measurements.jsonl",
            f"{REPORT}/analysis.json",
            f"{REPORT}/REPORT.md",
        }
        or any(bindings[p] != terminal[p] for p in bindings if p != marker)
    ):
        raise ValueError("original measurement receipt provenance differs")
    validate_qualification(files)
    return files, descriptor


def readme(draft):
    return f"""# Prospective fixed-map numerical replay: {RELEASE_ID}

{"Draft local QA bundle." if draft else "Final local build; publication is separate."}
This separate release preserves the failed v1 qualification and the single
passing R10 redesign. It replays all 27 new qualification cells and the two
observed endpoint/component results, including any unavailable family.

```sh
python tools/paper_map_validation_release.py verify --root .
uv sync --locked --python 3.13.11 --extra analysis --extra dev
uv run --locked python tools/paper_map_validation_release.py check --root .
uv run --locked pytest -q --import-mode=importlib tests/test_paper_map_validation_release.py \\
  tests/painter_map_validation_v2/test_analysis.py \\
  tests/painter_map_validation_v2/test_analysis_oracle.py
```

Verify is stdlib-only and checks exact inventory before installation. Check calls
unchanged numerical functions in memory, never the qualification build writer,
collector, extractor, private workflow, network or Git. Installation may download
dependencies; optional tests use temporary Git fixtures. The public CLI above is
the supported entry point. Collection/workflow/metadata source is for inspection;
its private runtime dependencies are deliberately absent. Other included tests
record qualification provenance and are not all standalone public test commands.

Qualification floating leaves use 1e-10 absolute/relative tolerance; identities,
counts, seeds, decisions and support hashes are exact. Reconstructed support
hashes cover floating-array bytes and can restrict replay to matching numerical
arithmetic/platform even when other floats satisfy tolerance. Observed analysis
and its report must replay exactly. The descriptor records the frozen runtime;
Python 3.13.11 is the recorded interpreter. Source or numerical mismatches fail;
no retained result is overwritten or repaired.

The public check recomputes qualification, assignment/order, exact fixed-input
lineage, all 240 row identities/statuses, raw-vector-to-fixed-scaler equality,
complete-vector eligibility, and the observed points/deletions/intervals/report.
Here "raw vector" means 31 numeric features, not image pixels. The collection
eligibility flags/reasons are a projection of a locally verified private receipt:
budget, service identity, transport timing and acquisition remain **attestations**,
not independently recomputed public facts. Projected rows do not authenticate the
omitted full measurement or response bytes. Omitted source-binding/terminal hashes
are provenance fingerprints, not verified public contents. No private current
credit balance, metadata response body, image, credential, .env, history or Korean
draft is included. Numerical replay does not establish raw-pixel authenticity.

The earlier immutable packages are still required for their historical results.
This archive contains no manuscript assets and does not change any previous
release. Fixed-panel stationarity/independence assumptions and historical proxy
limitations remain; no guaranteed service coverage, perceptual, capture,
scene-population or mechanism validation follows. Maintainer-run LLM agents
designed, implemented and reviewed these studies; this is not independent-human
replication. No further collection or replacement is authorized by replay.
""".encode()


def build(root, output_root, *, draft=False):
    root, output_root = Path(root).absolute(), Path(output_root).absolute()
    base.no_symlinks(root)
    base.no_symlinks(output_root)
    stage, archive, checksum = (
        output_root / RELEASE_ID,
        output_root / f"{RELEASE_ID}.tar.gz",
        output_root / f"{RELEASE_ID}.tar.gz.sha256",
    )
    if any(p.exists() or p.is_symlink() for p in (stage, archive, checksum)):
        raise FileExistsError("preserve existing create-once stage/archive/checksum")
    files, descriptor = gather(root)
    # Recheck private terminal/source attestations at local build, without resampling.
    freeze, requests, rows, receipt = terminal_inputs(root)
    terminal_snapshot = base.encoded([freeze, requests, rows, receipt])
    if (
        base.binding_map(freeze["inputs"]) != descriptor["frozen_input_bindings"]
        or project_rows(rows) != json.loads(files[f"{EXPORT}/inputs.json"])["rows"]
        or collection_projection(receipt)
        != json.loads(files[f"{EXPORT}/inputs.json"])["collection_attestation"]
        or requests
        != [json.loads(line) for line in files[f"{ORIGINAL}/planned_requests.jsonl"].splitlines()]
    ):
        raise ValueError("local terminal state differs from export")
    commit = None if draft else base.clean_sources(root, files)
    original = files.copy()
    files["README.md"] = readme(draft)
    files[MANIFEST] = base.encoded(
        dict(
            schema=SCHEMA,
            release_id=RELEASE_ID,
            draft=draft,
            build_source_commit=commit,
            files={p: base.digest(raw) for p, raw in sorted(files.items())},
        )
    )
    files["SHA256SUMS"] = base.checksum_text(files)
    stage.mkdir(parents=True)
    for path, raw in sorted(files.items()):
        base.write_new(stage / path, raw)
    verify(stage)
    with archive.open("xb") as handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0) as zipped:
            with tarfile.open(fileobj=zipped, mode="w", format=tarfile.PAX_FORMAT) as tar:
                for path, raw in sorted(files.items()):
                    item = tarfile.TarInfo(f"{RELEASE_ID}/{path}")
                    item.size, item.mode, item.mtime = len(raw), 0o644, 0
                    tar.addfile(item, io.BytesIO(raw))
    base.write_new(checksum, f"{base.digest(archive.read_bytes())}  {archive.name}\n".encode())
    refreshed, _ = gather(root)
    if refreshed != original or (not draft and base.clean_sources(root, refreshed) != commit):
        raise ValueError("source changed during build; preserve failed create-once outputs")
    if base.encoded(list(terminal_inputs(root))) != terminal_snapshot:
        raise ValueError("private terminal state changed during build; preserve failed outputs")
    verify(stage)
    return dict(
        stage=str(stage),
        archive=str(archive),
        checksum=str(checksum),
        payload_files=len(files),
        draft=draft,
    )


def verify(root, *, runtime=False):
    root = Path(root).absolute()
    base.no_symlinks(root)
    manifest = read(root, MANIFEST)
    if (
        set(manifest) != {"schema", "release_id", "draft", "build_source_commit", "files"}
        or manifest["schema"] != SCHEMA
        or manifest["release_id"] != RELEASE_ID
        or type(manifest["draft"]) is not bool
        or (manifest["draft"] and manifest["build_source_commit"] is not None)
        or (
            not manifest["draft"]
            and not re.fullmatch(r"[0-9a-f]{40}", str(manifest["build_source_commit"]))
        )
    ):
        raise ValueError("fixed final/draft release manifest required")
    files, _ = gather(root)
    files["README.md"] = base.file_bytes(root, "README.md")
    if manifest["files"] != {p: base.digest(raw) for p, raw in files.items()}:
        raise ValueError("exact release inventory/hash differs")
    files[MANIFEST] = base.file_bytes(root, MANIFEST)
    if base.file_bytes(root, "SHA256SUMS") != base.checksum_text(files):
        raise ValueError("checksum manifest differs")
    observed = set()
    for directory, dirs, names in os.walk(root, followlinks=False):
        parent = Path(directory)
        if runtime:
            dirs[:] = [
                d for d in dirs if d not in {".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
            ]
        for name in dirs + names:
            base.no_symlinks(parent / name)
        observed.update((parent / n).relative_to(root).as_posix() for n in names)
    if observed != files.keys() | {"SHA256SUMS"}:
        raise ValueError("unlisted/missing release files")
    return dict(status="verified", files=len(observed), private_collection_authenticated=False)


def check(root):
    root = Path(root).absolute()
    verify(root, runtime=True)
    before = base.file_bytes(root, MANIFEST)
    _, _, precision = numerical_modules(root)
    expected_precision = read(root, f"{QUALIFICATION}/precision.json")
    actual_precision = precision.qualify(precision.v1.load_proxy(root))
    if not base.compare(actual_precision, expected_precision["qualification"]):
        raise ValueError("complete 27-cell numerical qualification replay differs")
    if precision.report(expected_precision).encode() != base.file_bytes(
        root, f"{QUALIFICATION}/PRECISION.md"
    ):
        raise ValueError("qualification report replay differs")
    actual, render = observed_replay(root, read(root, f"{EXPORT}/inputs.json"))
    expected = read(root, f"{REPORT}/analysis.json")
    if base.encoded(actual) != base.encoded(expected) or render(actual).encode() != base.file_bytes(
        root, f"{REPORT}/REPORT.md"
    ):
        raise ValueError("exact observed analysis/report replay differs")
    base.require_local_modules(root)
    verify(root, runtime=True)
    if base.file_bytes(root, MANIFEST) != before:
        raise ValueError("manifest changed during numerical replay")
    return dict(
        status="checked",
        qualification_cells=27,
        qualification_exact=(actual_precision == expected_precision["qualification"]),
        observed_exact=True,
        observed_status=actual["status"],
        private_collection_authenticated=False,
        scientific_outputs_written=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("export", "build", "verify", "check"):
        command = sub.add_parser(name)
        command.add_argument("--root", type=Path, default=Path.cwd())
        if name == "build":
            command.add_argument("--output-root", type=Path, required=True)
            command.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    result = (
        build(args.root, args.output_root, draft=args.draft)
        if args.command == "build"
        else {
            "export": export,
            "verify": verify,
            "check": check,
        }[args.command](args.root)
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
