"""Export and replay the paper's retained numerical evidence without the media archive.

Export runs only in the maintainer's retained checkout. Check runs in a history-free
release tree and calls the unchanged scientific compute functions. No collection,
measurement, freeze, publication, or historical verification function is invoked by
check. This is numerical reproduction from measurements, not an independent study.
"""

from __future__ import annotations

import argparse
import copy
import csv
import gzip
import hashlib
import importlib
import importlib.metadata
import io
import json
import math
import os
import platform
import re
import runpy
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

NAMESPACE = "paper_reproducibility_v1"
DEFAULT_ID = "pprv1-20260910"
DATA = Path("data/manifests") / NAMESPACE
REPORTS = Path("reports") / NAMESPACE
ROOT = Path(__file__).resolve().parents[1]
STUDY1 = Path("data/manifests/painter_distribution_study_v1")
REVISION = Path("data/manifests/painter_distribution_revision_v1/pdrv1-numeric-20260907")
PALETTE = Path("data/manifests/painter_responsiveness_v2")
PALETTE_RUNS = ("prv2-oauth-recovery-20260908", "prv2-oauth-20260908")
PURE_KEYS = (
    "cells", "endpoints", "sensitivity_contrasts", "baselines", "coverage",
    "classifiers", "projections", "specificity", "availability",
)
EXPLORATORY_FIELDS = (
    "image_id", "domain", "alias", "method_id", "template_id", "block", "retried",
    "source_run_id",
)
DROP_FIELDS = {
    "source_response_path", "raw_path", "normalized_path", "path", "url", "uri",
    "event_sha256", "previous_sha256", "feature_sha256", "raw_sha256", "phash",
    "at_utc", "kind", "stage", "source_basis", "content_description",
    "visible_border_note", "scene_text", "fine_subject", "observed", "scaled",
}


def native(value):
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [native(v) for v in value]
    return value


def encoded(value, *, pretty=False, ordered=False):
    return (json.dumps(native(value), ensure_ascii=False, allow_nan=False,
                       sort_keys=not ordered, indent=2 if pretty else None,
                       separators=None if pretty else (",", ":")) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(encoded(value))


def close_values(actual, expected, *, tolerance=1e-10):
    """Compare every leaf; retain exact identities, structure, integers and decisions."""
    if isinstance(expected, dict):
        return (isinstance(actual, dict) and actual.keys() == expected.keys()
                and all(close_values(actual[k], v,
                                     tolerance=(0 if re.search(r"^p_|_p$|p_value|pvalue", k)
                                                else tolerance))
                        for k, v in expected.items()))
    if isinstance(expected, list):
        return (isinstance(actual, list) and len(actual) == len(expected)
                and all(close_values(a, b, tolerance=tolerance)
                        for a, b in zip(actual, expected, strict=True)))
    if type(expected) is float and type(actual) in (float, int):
        return math.isclose(actual, expected, abs_tol=tolerance, rel_tol=tolerance)
    return type(actual) is type(expected) and actual == expected


def csv_values(raw):
    def value(text):
        if not text:
            return text
        try:
            return json.loads(text)
        except (ValueError, TypeError):
            return text
    return [{key: value(item) for key, item in row.items()}
            for row in csv.DictReader(io.StringIO(raw.decode()))]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_new(path, value, *, ordered=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(encoded(value, ordered=ordered))


def identifier(value):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}", value):
        raise ValueError("release ID must be a portable component")
    return value


def portable(value):
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not path.parts or "\\" in str(value):
        raise ValueError("release paths must be confined portable relative paths")
    return path


def sanitize(value):
    """Remove unused transport/path metadata; preserve numerical labels and order."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key == "payload":
                # Existing metric code accepts this exact canonical payload hash.
                raw = json.dumps(item, sort_keys=True, separators=(",", ":"), allow_nan=False)
                result["payload_sha256"] = sha(raw.encode())
            elif key not in DROP_FIELDS and not key.endswith("_path"):
                result[key] = sanitize(item)
        return result
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    return native(value)


def screen_numerical(value):
    """Fail closed without printing a suspect value or credential."""
    text = encoded(value).decode()
    patterns = (
        r"/(?:Users|home|private)/", r"[A-Za-z]:\\\\(?:Users|Windows|Program Files)\\\\",
        r"file://", r"data:image/",
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"\bsk-[A-Za-z0-9_-]{24,}", r"\bAKIA[A-Z0-9]{16}\b",
        r"\bBearer\s+[A-Za-z0-9._-]{24,}",
        r"https?://[^\s/\"'<>:@]+:[^\s/\"'<>@]+@",
    )
    if any(re.search(pattern, text) for pattern in patterns):
        raise ValueError("public numerical export contains a prohibited sensitive/path pattern")
    def visit(item):
        if isinstance(item, dict):
            for key, child in item.items():
                if re.search(r"password|api.?key|authorization|access.?token|refresh.?token", key,
                             re.IGNORECASE):
                    raise ValueError("public numerical export contains a sensitive field name")
                visit(child)
        elif isinstance(item, list):
            for child in item:
                visit(child)
        elif isinstance(item, str) and re.match(r"^[A-Za-z]:[\\/]", item):
            raise ValueError("public numerical export contains an absolute local path")
    visit(value)


def coverage():
    return [
        dict(id="exploration", scope="sec:four-painter; tab:four-painter; tab:four-cells; "
             "fig:four-painter",
             mode="recomputed_from_vectors", details="All 24 full-feature cells, PCA fits, "
             "all feature-family classifier predictions, spreads and scene/block folds."),
        dict(id="stage_a", scope="tab:four-baseline",
             mode="recomputed_from_vectors", details="Four-painter matched reference/free/named "
             "controls, 128 saved-seed draws, content and classifier/transfer diagnostics."),
        dict(id="study1", scope="sec:controlled; app:inference; tab:contrasts",
             mode="recomputed_from_vectors", details="Complete original eight-test family, "
             "weights, randomization seeds, all pipelines, baselines, coverage and classifiers."),
        dict(id="revision", scope="tab:alignment; tab:coverage-main; tab:coverage_sensitivity; "
             "app:diagnostics; app:sensitivity",
             mode="recomputed_from_vectors", details="Full revision computation: representation, "
             "coverage, alignment, scaler/reference and timing sensitivities."),
        dict(id="retrieval", scope="fig:retrieval",
             mode="recomputed_from_vectors", details="All 450 condition comparisons plus "
             "query/split/prediction identities and processing views."),
        dict(id="palette", scope="fig:response; fig:response-blocks; app:response; "
             "app:mixture; tab:chroma",
             mode="recomputed_from_vectors", details="192-image primary and separate 49-image "
             "ancillary cohort, all coordinates, shared controls, sensitivities, reference "
             "comparisons and exact-rational quantile correction."),
        dict(id="calibration", scope="tab:calibration",
             mode="recomputed_from_vectors", details="Retained noise pools and full original "
             "5,000-trial calibration/effect grid with unchanged seeds."),
        dict(id="figures", scope="All seven manuscript figures",
             mode="rendered_from_saved_tables_with_numeric_bridges", details="Six figures use "
             "hash-checked saved CSV/JSON; the seventh recomputes palette block contrasts. "
             "Numerical analysis bridges are checked separately; PDF bytes are checked."),
        dict(id="design_and_acquisition", scope="tab:design; app:features; app:prompt",
             mode="recorded_metadata_only", details="Counts, prompts, feature definitions and "
             "transport history are retained descriptions. This package does not re-acquire "
             "artwork, regenerate images, re-extract features, audit private responses or "
             "establish perceptual validity/independent replication."),
    ]


def export_inputs(root, release_id):
    """Read retained numerical loaders, never edit their evidence or execute transport."""
    from latent_art_bench.painter_distribution_revision_v1 import common
    from latent_art_bench.painter_distribution_study_v1 import diagnostics as stage_a
    from latent_art_bench.painter_responsiveness_v2 import common as palette_common

    target = root / DATA / release_id
    if target.exists():
        raise FileExistsError("release input namespace exists; select a new release ID")
    bundle = common.load(root)
    painters, frame, stage_sources = stage_a.inputs(root)
    source_paths = {Path(row["path"]) for row in stage_sources} | set(common.INPUT_PATHS)
    source_paths |= {stage_a.CONFIG, palette_common.CONFIG}
    expected_objects = {}
    required_frame = {r["image_id"] for p in painters.values()
                      for r in p["items"][:p["reference_count"]]}
    catalog = []
    for key in sorted(required_frame):
        item = frame[key]
        surrogate = item["surrogate"]
        catalog.append(dict(
            cohort="four_painter_reference", work_id=key, painter_id=item["painter_id"],
            source_record_urls=item["object_urls"], source_image_url=surrogate["url"],
            origin_urls=surrogate["origin_urls"], file_sha1=surrogate["expected_sha1"],
            recorded_license=surrogate["licence"], commons_filename=surrogate["commons_filename"],
        ))
    delivery_path = STUDY1 / "pdsv1-reference-delivery-r2-20260906/deliveries.jsonl"
    deliveries = {r["work_id"]: r for r in rows(root / delivery_path)}
    for item in bundle["reference"]:
        if item["pipeline"] != "primary512":
            continue
        delivery = deliveries[item["image_id"]]
        catalog.append(dict(
            cohort="controlled_reference", work_id=item["image_id"],
            painter_id=item["painter_id"], source_record_urls=delivery["authority_urls"],
            source_image_url=delivery["delivery_url"], parent_source_url=delivery["url"],
            file_sha256=item["raw_sha256"], parent_file_sha1=delivery["expected_sha1"],
            recorded_license=delivery["license"], license_url=delivery["license_url"],
            rights_page=delivery["rights_page"], commons_filename=delivery["commons_filename"],
        ))
    frame = {key: {k: frame[key][k] for k in ("capture_workflow", "collections")}
             for key in sorted(required_frame)}
    # The public bundle keeps raw numerical coordinates and the original scalers.
    compact = {key: sanitize(bundle[key]) for key in (
        "reference", "generated", "development", "requests", "timings", "targets",
        "scalers", "config",
    )}
    compact["terminals"] = {
        key: {"status": row["status"], "status_code": row["status_code"],
              "cost_usd": row["cost_usd"],
              "observed": {"reported": {"quality": (row.get("observed") or {}).get(
                  "reported", {}).get("quality")}}}
        for key, row in bundle["terminals"].items()
    }
    palette = {}
    expected = {}
    for run in PALETTE_RUNS:
        directory = PALETTE / run
        files = [directory / name for name in (
            "planned_requests.jsonl", "generated_features.jsonl", "analysis.json")]
        source_paths.update(files)
        palette[run] = dict(requests=sanitize(rows(root / files[0])),
                            features=sanitize(rows(root / files[1])))
        original = read(root / files[2])
        expected_objects[run] = {key: value for key, value in original.items()
                                 if key != "collection"}
        expected[run] = digest(expected_objects[run])
    old_path = STUDY1 / "pdsv1-analysis-20260907/analysis.json"
    old = read(root / old_path)
    expected_objects["study1"] = {key: old[key] for key in PURE_KEYS}
    expected_objects["revision"] = read(root / REVISION / "analysis.json")
    expected.update({key: digest(expected_objects[key]) for key in ("study1", "revision")})
    diagnostic_path = PALETTE / "prv2-oauth-20260908/diagnostics.json"
    diagnostic = read(root / diagnostic_path)
    expected.update({key: digest(diagnostic[key])
                     for key in ("diagnostics", "retained_noise", "simulation")})
    expected_objects.update({key: diagnostic[key]
                             for key in ("diagnostics", "retained_noise", "simulation")})
    from latent_art_bench.painter_responsiveness_quantiles_v1 import correct
    for run in PALETTE_RUNS:
        corrected, _ = correct(read(root / PALETTE / run / "analysis.json"))
        expected_objects[run + ":quantiles"] = {
            key: value for key, value in corrected.items() if key != "collection"}
        expected[run + ":quantiles"] = digest(expected_objects[run + ":quantiles"])
    source_paths.update({old_path, REVISION / "analysis.json", diagnostic_path})
    exported = dict(
        schema="paper-reproducibility-inputs/1", study1=compact,
        stage_a=dict(painters=native(painters), frame=frame, config=read(root / stage_a.CONFIG)),
        palette=palette, palette_config=palette_common.configuration(root), extensions=[],
    )
    screen_numerical(exported)
    screen_numerical(catalog)
    screen_numerical(expected_objects)
    output_hashes = {}
    for directory, names in (
        (Path("reports/painter_distribution_exploration_v1"),
         ("points.csv", "separability.csv", "predictions.csv", "spread.csv", "projections.json")),
        (Path("reports/painter_distribution_study_v1/pdsv1-diagnostics-20260906"),
         tuple(p.name for p in (root / "reports/painter_distribution_study_v1/"
                               "pdsv1-diagnostics-20260906").glob("*")
               if p.suffix in (".csv", ".json"))),
    ):
        for name in names:
            path = directory / name
            source_paths.add(path)
            output_hashes[path.as_posix()] = sha((root / path).read_bytes())
    provenance = []
    for relative in sorted(source_paths):
        portable(relative)
        path = root / relative
        provenance.append(dict(path=relative.as_posix(), sha256=sha(path.read_bytes()),
                               bytes=path.stat().st_size, included_as_original=False))
    manifest = dict(
        schema="paper-reproducibility-export/1", release_id=release_id,
        source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root,
                                               text=True).strip(),
        source_commit_scope="Original local checkout provenance; this does not assert that "
                            "the original commit or private archive is publicly available.",
        input_sha256=sha(encoded(exported, ordered=True)), expected=expected,
        original_numeric_output_hashes=output_hashes, sources=provenance,
        transformations=[
            "Retain input row order, image/request identities, coordinate values, scalers, "
            "treatment labels, design weights, seeds, folds and computational nuisance labels.",
            "Omit unused path/response/ledger metadata; replace submitted payload with its "
            "canonical SHA256 accepted by the unchanged alignment implementation.",
            "Omit duplicate development-scaled coordinates and recompute them with the "
            "unchanged transform before analysis. Exploration retains its original scaled "
            "31-coordinate matrix. All quantities originate in retained measurements.",
            "Recompute Study 1 before the revision; pass its recomputed cells/endpoints to "
            "the unchanged revision consistency checks instead of copying old outputs.",
        ],
        coverage=coverage(),
        environment=runtime(),
    )
    write_new(target / "inputs.json", exported, ordered=True)
    write_new(target / "source_catalog.json", dict(
        scope="Recorded source links, licenses and file identities; URLs are not a guarantee "
              "of present availability or permission to redistribute images. Images are absent.",
        records=catalog))
    expected_path = root / REPORTS / release_id / "expected_outputs.json.gz"
    expected_path.parent.mkdir(parents=True, exist_ok=True)
    with expected_path.open("xb") as handle:
        handle.write(gzip.compress(encoded(expected_objects), mtime=0))
    manifest["expected_outputs_sha256"] = sha(expected_path.read_bytes())
    write_new(target / "export_manifest.json", manifest)
    return dict(status="exported", release_id=release_id,
                input_bytes=(target / "inputs.json").stat().st_size,
                original_sources=len(provenance))


def runtime():
    import pywt
    return dict(python=platform.python_version(), platform=platform.platform(),
                module_versions={"pywt": pywt.__version__},
                version_convention="Named distributions use importlib.metadata.version; "
                                   "module_versions preserves any distinct module-level string.",
                **{name: importlib.metadata.version(name) for name in
                   ("numpy", "scipy", "matplotlib", "Pillow", "PyWavelets", "scikit-image")})


def restored_bundle(value):
    import numpy as np

    from latent_art_bench.painter_feature_generation_v2.statistics import transform
    result = copy.deepcopy(value)
    for domain in ("reference", "generated", "development"):
        for row in result[domain]:
            row["stage"] = domain
            row["scaled"] = transform(np.asarray(row["values"]),
                                      result["scalers"][row["pipeline"]]["scaler"]).tolist()
    return result


def export_measurement(root, release_id):
    """Add completed challenge vectors without changing the base numerical export."""
    read(root / DATA / release_id / "export_manifest.json")
    namespace = "painter_measurement_validation_v1"
    source = Path("data/manifests") / namespace / "pmvv1-20260910"
    receipt = read(root / source / "run_receipt.json")
    if receipt.get("status") != "complete" or receipt.get("feature_vectors") != 1706:
        raise ValueError("measurement extension requires the completed 1706-vector receipt")
    for row in receipt["outputs"]:
        if sha((root / portable(row["path"])).read_bytes()) != row["sha256"]:
            raise ValueError("measurement receipt output differs")
    measured = rows(root / source / "features.jsonl")
    retained = [{key: row[key] for key in (
        "image_id", "painter_id", "stage", "condition", "raw_sha256", "window", "transform",
        "values",
    )} for row in measured]
    if len(retained) != 1706:
        raise ValueError("measurement row count differs")
    expected = read(root / source / "analysis.json")
    screen_numerical(retained)
    screen_numerical(expected)
    input_path = DATA / release_id / "measurement_validation.json"
    expected_path = REPORTS / release_id / "measurement_validation_expected.json.gz"
    descriptor_path = DATA / release_id / "measurement_extension.json"
    if any((root / p).exists() for p in (input_path, expected_path, descriptor_path)):
        raise FileExistsError("measurement extension already exists")
    write_new(root / input_path, retained, ordered=True)
    with (root / expected_path).open("xb") as handle:
        handle.write(gzip.compress(encoded(expected), mtime=0))
    source_paths = [source / name for name in
                    ("features.jsonl", "analysis.json", "run_receipt.json", "freeze.json")]
    source_paths += [Path("studies") / namespace / "PROTOCOL.md"]
    descriptor = dict(
        component="measurement", input_path=input_path.as_posix(),
        input_sha256=sha((root / input_path).read_bytes()),
        expected_path=expected_path.as_posix(),
        expected_file_sha256=sha((root / expected_path).read_bytes()),
        expected_numeric_sha256=digest(expected),
        sources=[dict(path=p.as_posix(), sha256=sha((root / p).read_bytes()))
                 for p in source_paths],
        public_design_files=[(source / "freeze.json").as_posix(),
                             (source / "run_receipt.json").as_posix(),
                             (Path("studies") / namespace / "PROTOCOL.md").as_posix()],
        coverage=dict(id="measurement", scope="painter_measurement_validation_v1: challenge; "
                      "geometry; primary_replay_exact",
                      mode="recomputed_from_new_measurements", details="All 1706 retained vectors, "
                      "700 reference challenges, 1076 square-window baselines; unchanged "
                      "pipeline.compute with recomputed Study 1 inputs. This numerical release "
                      "does not itself reopen pixels or establish independent captures."),
    )
    write_new(root / descriptor_path, descriptor)
    return dict(status="measurement_extension_exported", rows=len(retained))


def export_replication(root, release_id):
    """Add a terminal fresh collection, preserving any withheld-claim decisions."""
    from latent_art_bench.painter_naming_replication_v1 import common, workflow

    read(root / DATA / release_id / "export_manifest.json")
    source = common.directory(common.RUN_ID)
    receipt = read(root / source / "measurement_receipt.json")
    for row in receipt["outputs"]:
        if sha((root / portable(row["path"])).read_bytes()) != row["sha256"]:
            raise ValueError("replication measurement receipt output differs")
    collection = read(root / source / "collection_receipt.json")
    for row in collection["outputs"]:
        if sha((root / portable(row["path"])).read_bytes()) != row["sha256"]:
            raise ValueError("replication collection output differs")
    if sha((root / source / "collection_receipt.json").read_bytes()) != receipt[
        "collection_receipt_sha256"
    ]:
        raise ValueError("replication collection receipt differs")
    requests = rows(root / source / "planned_requests.jsonl")
    measured = rows(root / source / "measurements.jsonl")
    if len(measured) != 3 * len(requests):
        raise ValueError("replication must retain every allocated slot/pipeline status")
    delivery = delivery_metadata(requests, rows(root / source / "slot_outcomes.jsonl"),
                                 rows(root / source / "generation_events.jsonl"))
    payload = dict(requests=sanitize(requests), rows=sanitize(measured),
                   config=read(root / common.CONFIG), historical=workflow._historical(root),
                   collection=collection, delivery_metadata=delivery)
    report = common.REPORTS / common.RUN_ID / "analysis.json"
    expected = read(root / report)
    screen_numerical(payload)
    screen_numerical(expected)
    input_path = DATA / release_id / "replication_inputs.json"
    expected_path = REPORTS / release_id / "replication_expected.json.gz"
    descriptor_path = DATA / release_id / "replication_extension.json"
    if any((root / p).exists() for p in (input_path, expected_path, descriptor_path)):
        raise FileExistsError("replication extension already exists")
    write_new(root / input_path, payload, ordered=True)
    with (root / expected_path).open("xb") as handle:
        handle.write(gzip.compress(encoded(expected), mtime=0))
    sources = [source / name for name in ("planned_requests.jsonl", "measurements.jsonl",
                                         "measurement_receipt.json", "collection_receipt.json",
                                         "freeze.json", "slot_outcomes.jsonl",
                                         "generation_events.jsonl")]
    sources += [report, common.CONFIG, common.STUDIES / "PROTOCOL.md",
                common.OLD_NAMING, common.OLD_PALETTE]
    descriptor = dict(
        component="replication", input_path=input_path.as_posix(),
        input_sha256=sha((root / input_path).read_bytes()),
        expected_path=expected_path.as_posix(),
        expected_file_sha256=sha((root / expected_path).read_bytes()),
        expected_numeric_sha256=digest(expected),
        sources=[dict(path=p.as_posix(), sha256=sha((root / p).read_bytes())) for p in sources],
        public_design_files=[common.CONFIG.as_posix(), (common.STUDIES / "PROTOCOL.md").as_posix(),
                             (source / "freeze.json").as_posix(),
                             (source / "collection_receipt.json").as_posix(),
                             (source / "measurement_receipt.json").as_posix()],
        coverage=dict(id="replication", scope="painter_naming_replication_v1: primary; "
                      "distributions; palette; naming_contributions",
                      mode="recomputed_from_new_collection_measurements",
                      details="Unchanged analysis.analyze plus apply_collection_scope. "
                      "Every allocated slot/pipeline, missing outcome and duration-based "
                      "withheld-claim decision is retained. Historical comparison rows and "
                      "collection receipt are recorded metadata, not newly inferred results. "
                      "The allowlisted delivery table preserves all slots and attempts, actual "
                      "recorded UTC, delivered dimensions/format and reported quality with nulls "
                      "for absent fields; it does not authenticate service transport. "
                      "A maintainer-run new generation cohort is not an independent investigator "
                      "or an independent image-capture replication."),
    )
    write_new(root / descriptor_path, descriptor)
    return dict(status="replication_extension_exported", requests=len(requests), rows=len(measured))


def delivery_metadata(requests, slots, events):
    """Retain delivery facts without copying responses or inferring requested settings."""
    if [r["request_id"] for r in requests] != [r["request_id"] for r in slots]:
        raise ValueError("delivery metadata must retain every allocated slot in order")

    def observed(value):
        value = value or {}
        return {**{key: value.get(key) for key in
                   ("image_sha256", "width", "height", "format", "mode")},
                "reported_quality": (value.get("reported") or {}).get("quality")}

    slot_rows = [{**{key: row.get(key) for key in
                    ("request_id", "sequence", "status", "selected_attempt")},
                  **observed(row.get("observed"))} for row in slots]
    attempt_rows = [{**{key: row.get(key) for key in
                       ("request_id", "attempt", "kind", "at_utc", "status", "status_code",
                        "post_started", "post_started_at_utc", "latency_seconds")},
                     **observed(row.get("observed"))} for row in events]
    valid_ids = {row["request_id"] for row in requests}
    if any(row["request_id"] not in valid_ids for row in attempt_rows):
        raise ValueError("delivery attempt has an unallocated identity")
    return dict(scope="Recorded metadata only. Actual delivery is never imputed from requested "
                "settings. Missing fields remain null; intent and terminal UTC are preserved. "
                "This table does not authenticate provider transport or re-open image pixels.",
                slots=slot_rows, attempt_events=attempt_rows)


def current_coverage(entries, *, challenge_figure=False):
    """Describe added displays without rewriting the create-once core export."""
    result = copy.deepcopy(entries)
    if challenge_figure:
        item = next(row for row in result if row["id"] == "figures")
        item.update(scope="All eight manuscript figures", details="Six figures use hash-checked "
                    "saved CSV/JSON; palette blocks are recomputed; fig:challenges "
                    "uses the saved challenge matrix whose frozen numerical computation is "
                    "replayed by the measurement extension. Numeric bridges and PDF bytes "
                    "are checked separately.")
    return result


def assert_digest(value, expected, label, *, reference=None, portable_numeric=False):
    actual = digest(value)
    if actual != expected and not (portable_numeric and reference is not None
                                   and close_values(native(value), reference)):
        raise ValueError(f"numerical replay differs from retained result: {label}")
    return dict(component=label, status=("exact_numeric_match" if actual == expected
                                        else "within_1e-10_absolute_and_relative_tolerance"),
                sha256=actual, retained_sha256=expected)


def table_bridges(root, name, value, *, portable_numeric=False):
    """Re-render numerical display tables with their original writers, without plots."""
    from latent_art_bench.painter_distribution_revision_v1 import report as revised_report
    from latent_art_bench.painter_distribution_study_v1 import main_report
    from latent_art_bench.painter_responsiveness_v2 import report as palette_report

    tables = {}
    writer = palette_report._csv
    if name in {"study1", "revision"}:
        # Those two report entry points read the sort-key JSON publication first.
        value = json.loads(encoded(value))
    if name == "study1":
        directory = Path("reports/painter_distribution_study_v1/pdsv1-analysis-20260907")
        writer = main_report.write_table
        tables = {key: value[key] for key in main_report.TABLES if key in value}
        tables["projection_points"] = [
            dict(painter_id=painter, basis=basis, **row)
            for painter, projection in value["projections"].items()
            for basis, fitted in projection.get("bases", {}).items() for row in fitted["points"]]
    elif name == "revision":
        directory = Path("reports/painter_distribution_revision_v1/pdrv1-numeric-20260907")
        writer, tables = revised_report._csv, revised_report._tables(value)
    elif name in {"retrieval", "simulation", "retained_noise"}:
        directory = Path("reports/painter_responsiveness_v2/prv2-oauth-20260908/diagnostics")
        if name == "retrieval":
            tables = {"retrieval_comparisons": value["cells"]}
        elif name == "simulation":
            tables = {"simulation": value["results"]}
        else:
            tables = {"noise_groups": value["groups"], "noise_marginal_variances":
                      [dict(arm=k, variance=v) for k, v in value["marginal_variances"].items()]}
    elif name in PALETTE_RUNS:
        directory = Path("reports/painter_responsiveness_v2") / name / "experiment"
        primary = value["primary"]
        tables = {"generated_chroma": value["generated_chroma"],
                  "reference_chroma": value["reference_chroma"],
                  "availability": primary["availability"], "cell_means": primary["cells"],
                  "arm_means": primary["arm_means"], "primary": primary.get("primary") or [],
                  "responses": primary.get("responses", []),
                  "generic_minus_free": primary.get("generic_minus_free", []),
                  "secondary_named_minus_free": primary.get("secondary_named_minus_free", [])}
    else:
        return []
    checks = []
    with tempfile.TemporaryDirectory(dir=root) as temp:
        for key, rows_ in tables.items():
            path = Path(temp) / (key + ".csv")
            writer(path, rows_)
            raw = path.read_bytes()
            relative = directory / path.name
            retained = (root / relative).read_bytes()
            same = raw == retained
            if not same and not (portable_numeric and
                                 close_values(csv_values(raw), csv_values(retained))):
                raise ValueError("computed result differs from manuscript display table: "
                                 + relative.as_posix())
            checks.append(dict(component=relative.as_posix(),
                               status="exact_computed_display_match" if same else
                               "computed_display_within_1e-10_absolute_and_relative_tolerance",
                               sha256=sha(raw), retained_sha256=sha(retained)))
    return checks


def check_numeric(root, release_id, *, components=None, output=None, portable_numeric=False):
    import numpy as np

    from latent_art_bench.painter_distribution_exploration_v1 import analysis as exploration
    from latent_art_bench.painter_distribution_exploration_v1 import report as exploration_report
    from latent_art_bench.painter_distribution_revision_v1 import analysis as revision
    from latent_art_bench.painter_distribution_study_v1 import analysis as study1
    from latent_art_bench.painter_distribution_study_v1 import diagnostics as stage_a
    from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
    from latent_art_bench.painter_feature_generation_v2.statistics import transform
    from latent_art_bench.painter_responsiveness_quantiles_v1 import correct
    from latent_art_bench.painter_responsiveness_v1 import inference
    from latent_art_bench.painter_responsiveness_v2 import analysis as palette_analysis
    from latent_art_bench.painter_responsiveness_v2 import diagnostics as retrieval

    directory = root / DATA / release_id
    manifest = read(directory / "export_manifest.json")
    raw = (directory / "inputs.json").read_bytes()
    if sha(raw) != manifest["input_sha256"]:
        raise ValueError("compact input bytes differ from the export manifest")
    data = json.loads(raw)
    expected_raw = (root / REPORTS / release_id / "expected_outputs.json.gz").read_bytes()
    if sha(expected_raw) != manifest["expected_outputs_sha256"]:
        raise ValueError("expected-result bytes differ from the export manifest")
    references = json.loads(gzip.decompress(expected_raw))
    screen_numerical(data)
    selected = set(components or ("study1", "revision", "retrieval", "palette", "calibration",
                                  "exploration", "stage_a", "figures"))
    measurement_path = directory / "measurement_extension.json"
    replication_path = directory / "replication_extension.json"
    if components is None and measurement_path.exists():
        selected.add("measurement")
    if components is None and replication_path.exists():
        selected.add("replication")
    if selected - {"study1", "revision", "retrieval", "palette", "calibration",
                   "exploration", "stage_a", "figures", "measurement", "replication"}:
        raise ValueError("unknown numerical replay component")
    checks = []
    bundle = restored_bundle(data["study1"])

    def checked(name, value, expected_name=None):
        key = expected_name or name
        checks.append(assert_digest(value, manifest["expected"][key], name,
                                    reference=references[key], portable_numeric=portable_numeric))
        match_status = checks[-1]["status"]
        checks.extend(table_bridges(root, name, value, portable_numeric=portable_numeric))
        if output:
            write_new(output / (name.replace(":", "-") + ".json"), value)
        print(json.dumps(dict(component=name, status=match_status)), flush=True)

    if selected & {"study1", "revision", "measurement"}:
        primary = native(study1.compute(bundle["reference"], bundle["generated"], bundle["scalers"],
                                        bundle["targets"], bundle["config"]))
        checked("study1", primary)
        bundle["old_analysis"] = primary
    if "revision" in selected:
        checked("revision", revision.compute(bundle))
    if "measurement" in selected:
        from latent_art_bench.painter_measurement_validation_v1.pipeline import compute
        extension = read(measurement_path)
        raw = (root / portable(extension["input_path"])).read_bytes()
        expected_raw = (root / portable(extension["expected_path"])).read_bytes()
        if (sha(raw) != extension["input_sha256"]
                or sha(expected_raw) != extension["expected_file_sha256"]):
            raise ValueError("measurement extension checksum differs")
        result = native(compute(json.loads(raw), bundle))
        checks.append(assert_digest(result, extension["expected_numeric_sha256"], "measurement",
                                    reference=json.loads(gzip.decompress(expected_raw)),
                                    portable_numeric=portable_numeric))
        if output:
            write_new(output / "measurement.json", result)
        manifest["coverage"] = [*manifest["coverage"], extension["coverage"]]
        print(json.dumps(dict(component="measurement", status=checks[-1]["status"])), flush=True)
    if "replication" in selected:
        from latent_art_bench.painter_naming_replication_v1.analysis import analyze
        from latent_art_bench.painter_naming_replication_v1.workflow import apply_collection_scope
        extension = read(replication_path)
        raw = (root / portable(extension["input_path"])).read_bytes()
        expected_raw = (root / portable(extension["expected_path"])).read_bytes()
        if (sha(raw) != extension["input_sha256"]
                or sha(expected_raw) != extension["expected_file_sha256"]):
            raise ValueError("replication extension checksum differs")
        inputs = json.loads(raw)
        for row in inputs["rows"]:
            row["scaled"] = (transform(np.asarray(row["values"]),
                                       bundle["scalers"][row["pipeline"]]["scaler"]).tolist()
                             if row.get("values") is not None else None)
        result = native(analyze(inputs["requests"], inputs["rows"], bundle["reference"],
                                inputs["config"]))
        result["historical"] = inputs["historical"]
        result = apply_collection_scope(result, inputs["collection"])
        checks.append(assert_digest(result, extension["expected_numeric_sha256"], "replication",
                                    reference=json.loads(gzip.decompress(expected_raw)),
                                    portable_numeric=portable_numeric))
        if output:
            write_new(output / "replication.json", result)
        manifest["coverage"] = [*manifest["coverage"], extension["coverage"]]
        print(json.dumps(dict(component="replication", status=checks[-1]["status"])), flush=True)
    if "retrieval" in selected:
        checked("retrieval", retrieval.analyze(bundle), "diagnostics")
    if "palette" in selected:
        for run, value in data["palette"].items():
            feature_rows = copy.deepcopy(value["features"])
            for row in feature_rows:
                row["scaled"] = (transform(np.asarray(row["values"]),
                                           bundle["scalers"][row["pipeline"]]["scaler"]).tolist()
                                 if row["values"] is not None else None)
            result = palette_analysis.analyze(value["requests"], feature_rows,
                                              bundle["reference"], data["palette_config"])
            checked(run, result)
            corrected, _ = correct(result)
            checked(run + ":quantiles", corrected)
    if "calibration" in selected:
        config = data["palette_config"]
        noise = inference.retained_noise(bundle["generated"], route=config["route"])
        noise["assumptions"] = [s.replace("generic-clause FLUX data", "generic-clause OAuth data")
                                for s in noise["assumptions"]]
        checked("retained_noise", noise)
        effects = [[0, 0]] + [[-d, -d] for d in config["hypothetical_effect_grid"]]
        effects += [[-0.5, 0], [0, -0.5]]
        checked("simulation", inference.simulate_design(
            noise, seed=config["simulation_seed"], trials=config["simulation_trials"],
            effects=effects, repetitions=config["repetitions"], alpha=config["alpha"]))
    painters = {key: data["stage_a"]["painters"][key] for key in PAINTER_IDS}
    for value in painters.values():
        value["values"] = np.asarray(value["values"])

    def report_check(relative, raw):
        expected = manifest["original_numeric_output_hashes"][relative]
        if sha(raw) != expected:
            retained = (root / relative).read_bytes()
            if sha(retained) != expected:
                raise ValueError("retained numeric table checksum differs: " + relative)
            decode = csv_values if relative.endswith(".csv") else json.loads
            if not portable_numeric or not close_values(decode(raw), decode(retained)):
                raise ValueError("numerical report replay differs: " + relative)
        checks.append(dict(component=relative,
                           status="exact_report_match" if sha(raw) == expected else
                           "within_1e-10_absolute_and_relative_tolerance", sha256=sha(raw),
                           retained_sha256=expected))

    if "exploration" in selected:
        original = {}
        for key, value in painters.items():
            n = value["reference_count"]
            original[key] = dict(reference_count=n, values=value["values"][:n + 384],
                                 items=[{k: row[k] for k in EXPLORATORY_FIELDS}
                                        for row in value["items"][:n + 384]])
        result = exploration.compute(original)
        for name in ("points", "separability", "predictions", "spread"):
            report_check(f"reports/painter_distribution_exploration_v1/{name}.csv",
                         exploration_report._csv(result[name]).encode())
        report_check("reports/painter_distribution_exploration_v1/projections.json",
                     encoded(result["projections"], pretty=True))
        print('{"component":"exploration","status":"exact_report_match"}', flush=True)
    if "stage_a" in selected:
        result = stage_a.compute(painters, data["stage_a"]["frame"], data["stage_a"]["config"])
        with tempfile.TemporaryDirectory(dir=root) as temp:
            for name, value in result.items():
                suffix = ".json" if name in {"capture_inventory", "split_members"} else ".csv"
                if suffix == ".json":
                    raw = encoded(value, pretty=True)
                else:
                    target = Path(temp) / (name + suffix)
                    stage_a.csv_write(target, value)
                    raw = target.read_bytes()
                report_check("reports/painter_distribution_study_v1/"
                             f"pdsv1-diagnostics-20260906/{name}{suffix}", raw)
        print('{"component":"stage_a","status":"exact_report_match"}', flush=True)
    if "figures" in selected:
        with tempfile.TemporaryDirectory(dir=root) as temp:
            target = Path(temp)
            scripts = (
                ("make_figures.py", ["--output-dir", str(target)]),
                ("replay_palette.py", ["--figure", str(target / "palette_blocks.pdf")]),
            )
            for script, arguments in scripts:
                old_argv = sys.argv
                try:
                    sys.argv = [script, *arguments]
                    import matplotlib as mpl
                    with mpl.rc_context(mpl.rcParamsDefault):
                        runpy.run_path(str(root / "paper" / script), run_name="__main__")
                finally:
                    sys.argv = old_argv
            challenge = root / "paper/figures/challenge_matrix.pdf"
            if challenge.exists():
                from latent_art_bench.painter_measurement_validation_v1.report import figures
                extension = read(measurement_path)
                source = next(row for row in extension["sources"]
                              if row["path"].endswith("/analysis.json"))
                raw = (root / portable(source["path"])).read_bytes()
                if sha(raw) != source["sha256"]:
                    raise ValueError("challenge figure input differs from its frozen analysis")
                with tempfile.TemporaryDirectory(dir=root) as validation_temp:
                    with mpl.rc_context(mpl.rcParamsDefault):
                        figures(Path(validation_temp), json.loads(raw))
                    shutil.copyfile(Path(validation_temp) / challenge.name, target / challenge.name)
            generated = sorted(target.glob("*.pdf"))
            expected_figures = {p.name for p in (root / "paper/figures").glob("*.pdf")}
            if {p.name for p in generated} != expected_figures:
                raise ValueError("regenerated manuscript figure inventory differs")
            for path in generated:
                same = path.read_bytes() == (root / "paper/figures" / path.name).read_bytes()
                if not same and not portable_numeric:
                    raise ValueError("figure byte replay differs: " + path.name)
                checks.append(dict(component="figures/" + path.name,
                                   status="exact_pdf_match" if same else
                                   "rendered_from_verified_inputs_platform_bytes_differ",
                                   sha256=sha(path.read_bytes())))
    return dict(status="partial_verified" if components else "verified", release_id=release_id,
                selected_components=sorted(selected), checks=checks, environment=runtime(),
                coverage=current_coverage(manifest["coverage"], challenge_figure=(
                    root / "paper/figures/challenge_matrix.pdf").exists()),
                new_images=0, feature_extraction=False,
                external_replication=False)


def file_inventory(root):
    return [dict(path=p.relative_to(root).as_posix(), bytes=p.stat().st_size,
                 sha256=sha(p.read_bytes()))
            for p in sorted(root.rglob("*")) if p.is_file() and not p.is_symlink()]


def build(root, release_id, destination, *, draft=False):
    """Stage only explicit scientific inputs and source; never copy working-tree/history."""
    if destination.exists():
        raise FileExistsError("staging destination exists; select a new empty destination")
    data_dir = DATA / release_id
    exports = read(root / data_dir / "export_manifest.json")
    sources = runpy.run_path(str(root / "paper/make_figures.py"))["SOURCES"]
    inputs = runpy.run_path(str(root / "paper/replay_palette.py"))["INPUTS"]
    allowlist = {Path(p) for p in set(sources) | set(inputs)}
    allowlist |= {data_dir / "inputs.json", data_dir / "export_manifest.json",
                  data_dir / "source_catalog.json",
                  REPORTS / release_id / "expected_outputs.json.gz",
                  Path("LICENSE"), Path("pyproject.toml"), Path("uv.lock"), Path("pytest.ini"),
                  Path("tools/paper_release.py"), Path("tests/test_paper_release.py"),
                  Path("paper/paper.tex"), Path("paper/paper.pdf"), Path("paper/references.bib"),
                  Path("paper/make_figures.py"), Path("paper/replay_palette.py"),
                  Path("studies") / NAMESPACE / "README.md"}
    allowlist |= {p.relative_to(root) for p in (root / "src/latent_art_bench").rglob("*.py")}
    allowlist |= {p.relative_to(root) for p in (root / "paper/figures").glob("*.pdf")}
    allowlist |= {Path(p) for p in exports["original_numeric_output_hashes"]}
    display_directories = (
        "reports/painter_distribution_study_v1/pdsv1-analysis-20260907",
        "reports/painter_distribution_revision_v1/pdrv1-numeric-20260907",
        "reports/painter_responsiveness_v2/prv2-oauth-20260908/diagnostics",
        *(f"reports/painter_responsiveness_v2/{run}/experiment" for run in PALETTE_RUNS),
    )
    for relative in display_directories:
        allowlist |= {p.relative_to(root) for p in (root / relative).glob("*.csv")
                      if p.name not in {"actual_slot_times.csv", "transport_events.csv",
                                        "transport_attempts.csv", "transport_summary.csv",
                                        "collection_slots.csv"}}
    for name in ("measurement", "replication"):
        extension_path = data_dir / (name + "_extension.json")
        if (root / extension_path).exists():
            extension = read(root / extension_path)
            allowlist |= {extension_path, portable(extension["input_path"]),
                          portable(extension["expected_path"])}
            allowlist |= {portable(p) for p in extension["public_design_files"]}
            exports["coverage"] = [*exports["coverage"], extension["coverage"]]
    if (root / "paper/figures/challenge_matrix.pdf").exists():
        allowlist |= {Path("paper/make_validation_figure.py"),
                      Path("data/manifests/painter_measurement_validation_v1/"
                           "pmvv1-20260910/analysis.json")}
        exports["coverage"] = current_coverage(exports["coverage"], challenge_figure=True)
    allowlist |= {Path("studies") / p for p in (
        "painter_distribution_exploration_v1/METHODS.md",
        "painter_distribution_study_v1/PROTOCOL.md",
        "painter_distribution_study_v1/MAIN.md",
        "painter_distribution_study_v1/INFERENCE.md",
        "painter_distribution_study_v1/DIAGNOSTICS.md",
        "painter_distribution_revision_v1/PROTOCOL.md",
        "painter_responsiveness_v2/PROTOCOL.md",
        "painter_responsiveness_recovery_v1/PROTOCOL.md",
        "painter_feature_generation_v2/PROTOCOL.md",
        "painter_feature_generation_v2/PROTOCOL_1.3.md",
    )}
    allowlist |= {Path("configs/painter_distribution_study_v1/research.json"),
                  Path("configs/painter_responsiveness_v2/study.json")}
    # The coverage table is not a plotting dependency, but must be directly accessible.
    allowlist.add(Path("reports/painter_distribution_revision_v1/"
                       "pdrv1-numeric-20260907/heldout_real_controls.csv"))
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    if not draft:
        for relative in sorted(allowlist):
            retained = subprocess.run(["git", "show", f"{commit}:{relative.as_posix()}"],
                                      cwd=root, capture_output=True)
            if retained.returncode or retained.stdout != (root / relative).read_bytes():
                raise ValueError("final build input is not bound to HEAD: " + str(relative))
    for relative in sorted(allowlist):
        portable(relative)
        source = root / relative
        if (source.is_symlink() or not source.is_file()
                or not source.resolve().is_relative_to(root.resolve())):
            raise ValueError("allowlisted source is absent or a symlink: " + str(relative))
        if relative.suffix in {".md", ".tex", ".bib", ".csv", ".json", ".jsonl"}:
            screen_numerical({"file_text": source.read_text(encoding="utf-8")})
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (destination / "README.md").write_text(release_readme(release_id), encoding="utf-8")
    workflow = destination / ".github/workflows/reproduce.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(ci_workflow(release_id), encoding="utf-8")
    (destination / "NUMERICAL_DATA_LICENSE.md").write_text(
        "# Numerical export license and media boundary\n\n"
        "The repository MIT license applies to the project software and author-produced "
        "numerical exports in this archive. Retain LICENSE when redistributing them.\n\n"
        "No original artwork, generated image pixels, third-party article text, model "
        "weights or provider response bodies are distributed. No license to those absent "
        "materials, or to an artist's name or work, is granted by this numerical release. "
        "Artist identifiers and collection groups are retained scientific labels.\n",
        encoding="utf-8")
    (destination / "CITATION.cff").write_text(
        'cff-version: 1.2.0\nmessage: "Please cite the accompanying manuscript and this release."\n'
        'title: "Painter Naming and the Distributional Gap Between Generated Images and '
        'Original Paintings: numerical reproduction package"\n'
        'authors:\n  - name: "LatentArtBench contributors"\n'
        f'version: "{release_id}"\ndate-released: "2026-09-10"\n'
        'url: "https://github.com/isingmodel/latent-art-bench"\nlicense: MIT\n', encoding="utf-8")
    write_new(destination / "COVERAGE.json", exports["coverage"])
    inventory = file_inventory(destination)
    manifest = dict(schema="paper-reproducibility-release/1", release_id=release_id,
                    input_export_source_commit=exports["source_commit"],
                    original_source_commit_scope=exports["source_commit_scope"],
                    build_source_commit=commit if not draft else None,
                    build_source_commit_verified=not draft,
                    build_source_commit_scope="All copied original inputs match this local commit "
                    "in a final build. The history-free public branch has a different commit ID.",
                    publication_status="draft_uncommitted" if draft else "prepared_not_published",
                    publication_status_scope="Status at artifact build time. Subsequent public "
                    "access and download-verification receipts are recorded separately at "
                    f"https://github.com/isingmodel/latent-art-bench/releases/tag/{release_id}.",
                    files=inventory,
                    excluded=["Git history", "raw media", "response bodies", "credentials",
                              "local configuration", "Korean user drafts", "literature PDFs"],
                    coverage=exports["coverage"])
    write_new(destination / "RELEASE_MANIFEST.json", manifest)
    manifest_hash = sha((destination / "RELEASE_MANIFEST.json").read_bytes())
    (destination / "SHA256SUMS").write_text(
        "".join(f"{row['sha256']}  {row['path']}\n" for row in
                [*inventory, dict(path="RELEASE_MANIFEST.json", sha256=manifest_hash)]),
        encoding="utf-8")
    verify_package(destination)
    archive = destination.with_suffix(".tar.gz")
    if archive.exists():
        raise FileExistsError("archive exists; do not overwrite a release candidate")
    with tarfile.open(archive, "w:gz", format=tarfile.PAX_FORMAT) as tar:
        for path in sorted(destination.rglob("*")):
            if not path.is_file():
                continue
            archive_name = f"{release_id}/{path.relative_to(destination)}"
            info = tar.gettarinfo(str(path), arcname=archive_name)
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.mtime = 0
            info.mode = 0o644
            with path.open("rb") as handle:
                tar.addfile(info, handle)
    return dict(status=manifest["publication_status"], release_id=release_id, files=len(inventory),
                archive_bytes=archive.stat().st_size, archive_sha256=sha(archive.read_bytes()))


def verify_package(root):
    manifest = read(root / "RELEASE_MANIFEST.json")
    seen = set()
    for row in manifest["files"]:
        relative = portable(row["path"])
        if str(relative) in seen:
            raise ValueError("duplicate manifest path")
        seen.add(str(relative))
        path = root / relative
        if (path.is_symlink() or not path.is_file()
                or not path.resolve().is_relative_to(root.resolve())
                or sha(path.read_bytes()) != row["sha256"]):
            raise ValueError("release checksum differs: " + str(relative))
    if (root / ".git").exists():
        raise ValueError("release verification requires a history-free extracted archive")
    return manifest


def restrict_runtime(root):
    """One-way audit hook: block network/processes and reads outside release/runtime roots."""
    roots = [root.resolve(), Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve()]
    # A source-installed Python can keep its standard library beside its prefix.
    roots.append(Path(os.__file__).resolve().parent)
    counters = dict(network_attempts=0, subprocess_attempts=0, outside_file_attempts=0,
                    blocked_file_basenames=[],
                    checked_file_opens=0)
    def audit(event, args):
        if event in {"socket.__new__", "socket.connect", "socket.connect_ex", "socket.sendto",
                     "socket.sendmsg", "socket.getaddrinfo"}:
            counters["network_attempts"] += 1
            raise PermissionError("network access is prohibited during numerical replay")
        if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.spawn"}:
            counters["subprocess_attempts"] += 1
            raise PermissionError("subprocesses are prohibited during numerical replay")
        if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(args[0])).resolve()
            if str(path) == os.devnull:
                return
            counters["checked_file_opens"] += 1
            if not any(path.is_relative_to(base) for base in roots):
                counters["outside_file_attempts"] += 1
                if path.name not in counters["blocked_file_basenames"]:
                    counters["blocked_file_basenames"].append(path.name)
                raise PermissionError("file access outside the release/runtime roots is prohibited")
    sys.addaudithook(audit)
    return counters


def release_readme(release_id):
    return f"""# Public numerical reproduction package

Painter Naming and the Distributional Gap Between Generated Images and Original Paintings.

This history-free package reproduces computations from retained numerical measurements.
It does not regenerate images, extract image features, validate perception, audit the
private transport archive, or establish independently collected replication.
`COVERAGE.json` maps every manuscript result family to its actual replay scope.

Use the tested Python 3.13.11 and uv 0.9.28, then run from this extracted directory:

```sh
uv sync --locked --extra analysis --python 3.13.11
uv run --locked python tools/paper_release.py check --release-id {release_id} --isolated
```

The full check recomputes the original statistical functions and compares their results
with hash-bound retained outputs. It checks every included manuscript figure PDF.
Exact float/PDF byte comparisons may expose platform differences: the receipts record
the numerical runtime. A failure must be investigated; do not change a bound hash or relax
a scientific test to make it pass. Hosted CI uses `--portable-numeric`, a prospectively
fixed 1e-10 absolute/relative tolerance for finite floating results, with exact structures,
identities, counts, seeds, decisions and p-values. Figure byte differences on that path
are reported as platform differences, not falsely called byte-identical reproduction.
Dependencies may be downloaded during installation. During numerical analysis, a Python
audit-hook guard blocks socket creation/use, subprocesses and file access outside this
tree/Python runtime. This is an ordinary Python I/O guard, not an OS sandbox or a
hostile-code containment boundary. Blocked attempts are retained in the check receipt.

The checker prints a result per computation and writes its receipt under
`reports/paper_reproducibility_v1/{release_id}/`. Use `--components study1,palette` for
an explicitly partial check or `--output .replayed-results` to inspect recomputed JSON.
Full exploration and Stage A checks may take several minutes.

The original local source commit in the manifest is provenance metadata, not a claim
that the old commit or private archive is publicly available. `RELEASE_MANIFEST.json`
and `SHA256SUMS` enumerate the exact files. Release source copies preserve the original
scientific implementations. See `NUMERICAL_DATA_LICENSE.md`, `LICENSE` and `CITATION.cff`.

The included design contracts and local Git freezes document prospective local
procedures; they are not registrations in an independent preregistration registry.
`data/manifests/paper_reproducibility_v1/{release_id}/source_catalog.json` supplies
recorded source URLs, work IDs, file identities and license metadata. These links
are not guarantees of current image access or permission to redistribute pixels.

Publication and anonymous-download verification are recorded separately on the
[versioned release](https://github.com/isingmodel/latent-art-bench/releases/tag/{release_id}).
The manifest's preparation status describes artifact build time, not current public
access. This archive does not by itself establish that publication or hosted verification
has occurred; consult the versioned release and its separate verification receipt.
"""


def ci_workflow(release_id):
    return f"""name: Public numerical reproduction
on:
  push:
    branches: [codex/paper-reproducibility-v1]
  workflow_dispatch:
permissions:
  contents: read
jobs:
  reproduce:
    runs-on: ubuntu-latest
    timeout-minutes: 90
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          persist-credentials: false
      - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
        with:
          python-version: '3.13.11'
      - name: Install uv
        run: python -m pip install uv==0.9.28
      - name: Extract tracked release tree without Git history
        run: |
          mkdir "$RUNNER_TEMP/public-replay"
          git archive HEAD | tar -x -C "$RUNNER_TEMP/public-replay"
      - name: Install locked numerical dependencies
        working-directory: ${{{{ runner.temp }}}}/public-replay
        run: uv sync --locked --extra analysis
      - name: Verify public numerical results
        working-directory: ${{{{ runner.temp }}}}/public-replay
        env:
          MPLCONFIGDIR: ${{{{ runner.temp }}}}/public-replay/.replay-matplotlib
        run: >-
          uv run --locked python tools/paper_release.py check
          --release-id {release_id} --isolated --portable-numeric
      - name: Retain hosted verification receipt
        uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: public-numerical-verification
          path: ${{{{ runner.temp }}}}/public-replay/reports/**/verification.json
          if-no-files-found: error
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("export", "export-measurement", "export-replication",
                                             "build", "check", "verify"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--release-id", default=DEFAULT_ID, type=identifier)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--components", help="Explicit comma-separated partial replay")
    parser.add_argument("--output", type=Path, help="New directory for recomputed JSON results")
    parser.add_argument("--isolated", action="store_true")
    parser.add_argument("--portable-numeric", action="store_true")
    parser.add_argument("--draft", action="store_true",
                        help="Stage an explicitly uncommitted draft")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "export":
        result = export_inputs(root, args.release_id)
    elif args.command == "export-measurement":
        result = export_measurement(root, args.release_id)
    elif args.command == "export-replication":
        result = export_replication(root, args.release_id)
    elif args.command == "build":
        if args.destination is None:
            parser.error("build requires a new --destination")
        result = build(root, args.release_id, args.destination.resolve(), draft=args.draft)
    elif args.command == "verify":
        value = verify_package(root)
        result = dict(status="checksums_verified", files=len(value["files"]))
    else:
        if args.isolated:
            verify_package(root)
            os.environ["MPLCONFIGDIR"] = str(root / ".replay-matplotlib")
            # Initialize font/runtime discovery before prohibiting subprocesses.
            import matplotlib.pyplot  # noqa: F401
            runtime()  # Cache platform discovery before subprocesses are prohibited.
            counters = restrict_runtime(root)
        else:
            counters = None
        started = time.monotonic()
        result = check_numeric(root, args.release_id,
                               components=args.components.split(",") if args.components else None,
                               output=args.output.resolve() if args.output else None,
                               portable_numeric=args.portable_numeric)
        result.update(elapsed_seconds=time.monotonic() - started,
                      isolated=bool(args.isolated), runtime_access=counters)
        receipt_name = ("partial_" + sha(args.components.encode())[:10] + ".json"
                        if args.components else "verification.json")
        receipt = root / REPORTS / args.release_id / receipt_name
        write_new(receipt, result)
        result = {key: result[key] for key in (
            "status", "release_id", "selected_components", "elapsed_seconds", "isolated",
            "runtime_access",
        )} | dict(checks=len(result["checks"]), receipt=receipt.relative_to(root).as_posix())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
