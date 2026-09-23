"""Bind supplied raw 31-feature rows to terminal pixels and the retained scaler.

No feature extraction, model execution, request or fitting occurs. Artifact
identity and declared method provenance do not prove that supplied raw numbers
were produced by that extractor: execution receipts/replay remain separate.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import numpy as np

from latent_art_bench.painter_feature_generation_v2.features import NAMES

from . import feature_census as fc
from . import protocol as p
from .transport_artifact import ROOT, file_sha

METHOD_BASE = "data/manifests/painter_feature_generation_v2/pfg2-method-20260905"
METHOD_FREEZE = METHOD_BASE + "/method_freeze.json"
DEVELOPMENT_RECEIPT = METHOD_BASE + "/development_receipt.json"
SCALER = METHOD_BASE + "/scaler.json"
HISTORICAL_BINDINGS = {
    METHOD_FREEZE: "0c254c629b37803c7e99f2c61485f6086f593f98cd8bc26b78a5c498f2b29200",
    DEVELOPMENT_RECEIPT: "5a724637bbf4ff1e424be0259e53ceb47c4926dba926defcff2609c7057b1b1c",
    SCALER: "71f511235081dfc1e9846976320c69477bcbd04dd43fc9a2e271f7b0375497b9",
}
METHOD_SOURCES = (
    "src/latent_art_bench/painter_feature_generation_v2/features.py",
    "src/latent_art_bench/painter_feature_generation_v2/statistics.py",
    "src/latent_art_bench/painter_feature_generation_v2/pipeline.py",
)


def _scaler_arrays(scaler):
    """Validate retained coordinates explicitly even after authenticating bytes."""
    arrays = []
    for key in ("center", "scale"):
        values = scaler.get(key)
        if (not isinstance(values, list) or len(values) != 31
                or any(type(value) not in (int, float) for value in values)):
            raise ValueError("retained scaler needs 31 numeric center/scale coordinates")
        array = np.asarray(values, dtype=float)
        if not np.isfinite(array).all():
            raise ValueError("retained scaler coordinates must be finite")
        arrays.append(array)
    if np.any(arrays[1] <= 0):
        raise ValueError("retained development IQR scales must be positive")
    return tuple(arrays)


def _historical_contract(root):
    root = Path(root).resolve()
    records = {
        path: fc._json(fc._bound_bytes(fc._inside(root, path), expected))
        for path, expected in HISTORICAL_BINDINGS.items()
    }
    frozen, development, scaler = (
        records[path] for path in (METHOD_FREEZE, DEVELOPMENT_RECEIPT, SCALER)
    )
    if (frozen["feature_names"] != list(NAMES) or len(NAMES) != 31
            or type(frozen["short_side"]) is not int or frozen["short_side"] != 512
            or frozen["method_id"] != "pfg2-method-20260905"):
        raise ValueError("historical measurement names or 512-short-side contract changed")
    if (development["stage"] != "development"
            or development["method_freeze_sha256"] != HISTORICAL_BINDINGS[METHOD_FREEZE]
            or development["scaler_sha256"] != HISTORICAL_BINDINGS[SCALER]
            or scaler["method_freeze_sha256"] != HISTORICAL_BINDINGS[METHOD_FREEZE]
            or scaler["development_feature_sha256"] != development["feature_file_sha256"]
            or scaler["quantile_rule"] != "equal_painter_weighted_empirical_inverse_cdf"
            or set(scaler["development_counts"]) != set(p.ARTISTS)
            or any(type(n) is not int or n <= 0 for n in scaler["development_counts"].values())
            or scaler["invalid_coordinates"] != {"color": [], "spatial": [], "texture": []}):
        raise ValueError("historical development-only scaler ancestry changed")
    source_bindings = {item["path"]: item["sha256"] for item in frozen["inputs"]}
    if len(source_bindings) != len(frozen["inputs"]):
        raise ValueError("duplicate historical method source binding")
    bindings = dict(HISTORICAL_BINDINGS)
    for source in METHOD_SOURCES:
        expected = source_bindings[source]
        fc._bound_bytes(fc._inside(root, source), expected)
        bindings[source] = expected
    center, scale = _scaler_arrays(scaler)
    contract = dict(
        name="historical31_original512",
        feature_dimension=31,
        feature_names=list(NAMES),
        normalize=dict(
            callable="latent_art_bench.painter_feature_generation_v2.features.normalize",
            short_side=512, crop_fraction=0.0,
            view="original full frame; no extra crop",
            exif_orientation="transpose using retained normalize implementation",
            color="retained embedded-profile to sRGB; missing profile assumes sRGB",
            resize="retained half-up geometry and Lanczos; never upsample",
            alpha="retained opaque-only admission",
        ),
        extract=dict(callable="latent_art_bench.painter_feature_generation_v2.features.extract",
                     output="raw 31-vector in fixed NAMES order"),
        standardization=dict(
            formula="(raw_features - retained center) / retained scale",
            scaler_path=SCALER, scaler_sha256=HISTORICAL_BINDINGS[SCALER],
            fitting_population="retained historical development only",
            new_fitting=False, unit_normalization=False,
            quantile_rule=scaler["quantile_rule"],
        ),
        historical_bindings=bindings,
        development_receipt=DEVELOPMENT_RECEIPT,
        extraction_execution_authenticated_by_loader=False,
    )
    return contract, center, scale


def _manifest(evidence, contract):
    return dict(
        schema="painter-family-raw31-feature-inputs/1.0", namespace=p.NAMESPACE,
        simulation_only=evidence["simulation_only"],
        terminal_record_hashes=evidence["record_hashes"],
        collector_manifest_sha256=evidence["collector_manifest_sha256"],
        measurement=contract, rows=evidence["images"], missing=evidence["missing"],
        window_times=evidence["window_times"],
    )


def feature_manifest(census: fc.TerminalCensus, *, root=ROOT):
    """Describe the exact terminal originals and retained method, without extraction."""
    fc.revalidate_census(census)
    contract, _, _ = _historical_contract(root)
    return _manifest(census.evidence, contract)


def _strings(values, label):
    if values.ndim != 1 or values.dtype.kind not in ("U", "S"):
        raise ValueError(f"{label} must be an explicit one-dimensional string array")
    if values.dtype.kind == "S":
        try:
            return [value.decode("utf-8", errors="strict") for value in values.tolist()]
        except UnicodeDecodeError as exc:
            raise ValueError(f"{label} must contain valid UTF-8 strings") from exc
    return values.tolist()


def _cell(row):
    if (row["model"] not in p.MODELS or row["arm"] not in p.ARMS
            or type(row["session"]) is not int or not 0 <= row["session"] < 8
            or type(row["scene"]) is not int or not 0 <= row["scene"] < 12):
        raise ValueError("raw feature row has invalid fixed-design cell indices")
    model = p.MODELS.index(row["model"])
    scene_id = p.SCENES[row["scene"]][0]
    expected_id = f"pfam1-s{row['session']:02d}-m{model:02d}-{scene_id}-{row['arm']}"
    if (row["id"] != expected_id or row["scene_id"] != scene_id
            or row["view"] != "original" or row["box"] != [0, 0, 1, 1]
            or not isinstance(row["sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])):
        raise ValueError("raw feature row identity or original full-frame view changed")
    if (row["attempt_id"] not in [f"{expected_id}-a{i}" for i in (1, 2, 3)]
            or row["path"] != f"images/{row['attempt_id']}-0.original"):
        raise ValueError("raw feature row is not bound to its exact original attempt")
    return model, row["session"], row["scene"], p.ARMS.index(row["arm"])


def load_feature_census(
    census: fc.TerminalCensus, manifest_path, raw_npz_path, *,
    expected_manifest_sha256, expected_raw_sha256, root=ROOT,
):
    """Validate supplied raw rows, apply the retained scaler, and map fixed cells.

    Terminal records and pixels are rechecked at consumption. Successful cells
    require finite raw vectors; failed extraction cannot be silently recoded as
    collector missingness. An execution receipt or replay is still necessary to
    establish that raw values were actually calculated from their bound pixels.
    """
    fc.revalidate_census(census)
    evidence = census.evidence
    contract, center, scale = _historical_contract(root)
    manifest = fc._json(fc._bound_bytes(manifest_path, expected_manifest_sha256))
    if p.canonical_sha(manifest) != p.canonical_sha(_manifest(evidence, contract)):
        raise ValueError("raw feature membership, timings or historical method contract changed")
    raw_bytes = fc._bound_bytes(raw_npz_path, expected_raw_sha256)
    with np.load(io.BytesIO(raw_bytes), allow_pickle=False) as archive:
        if (len(archive.files) != 3
                or set(archive.files) != {"raw_features", "ids", "feature_names"}):
            raise ValueError("raw archive must contain only raw_features, ids and feature_names")
        raw, ids, names = archive["raw_features"], archive["ids"], archive["feature_names"]
    rows = manifest["rows"]
    if _strings(ids, "row IDs") != [row["id"] for row in rows]:
        raise ValueError("raw feature row IDs differ from bound terminal image order")
    if _strings(names, "feature names") != list(NAMES):
        raise ValueError("raw feature names differ from fixed historical NAMES order")
    if (raw.shape != (len(rows), 31) or raw.dtype.kind != "f"
            or not np.isfinite(raw).all()):
        raise ValueError("one finite floating 31-vector is required per successful original")
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            standardized = (raw.astype(np.float64) - center) / scale
    except FloatingPointError as exc:
        raise ValueError("raw features overflow the retained scaler") from exc
    if not np.isfinite(standardized).all():
        raise ValueError("standardized historical features must remain finite")
    generated = np.full((6, 8, 12, 8, 31), np.nan)
    observed = np.zeros((6, 8, 12, 8), dtype=bool)
    for row, vector in zip(rows, standardized):
        cell = _cell(row)
        if observed[cell]:
            raise ValueError("more than one raw feature row maps to a fixed cell")
        if file_sha(fc._inside(census.run_dir, row["path"])) != row["sha256"]:
            raise ValueError("original pixels changed after terminal verification")
        generated[cell], observed[cell] = vector, True
    if int(observed.sum()) + len(manifest["missing"]) != p.EXPECTED_OUTPUTS:
        raise ValueError("raw feature cells do not complete the terminal missingness census")
    return dict(
        generated=generated, observed=observed, window_times=manifest["window_times"],
        simulation_only=manifest["simulation_only"], missing=manifest["missing"],
        model_order=p.MODELS, arm_order=p.ARMS, feature_names=NAMES,
        provenance=dict(
            schema="painter-family-raw31-bound-load/1.0",
            manifest_sha256=expected_manifest_sha256, raw_features_sha256=expected_raw_sha256,
            terminal_record_hashes=manifest["terminal_record_hashes"],
            collector_manifest_sha256=manifest["collector_manifest_sha256"],
            measurement_contract=contract,
            original_pixels_rechecked=True,
            extraction_execution_authenticated=False,
            extraction_execution_receipt_or_replay_required=True,
            limitation=("External hashes bind the supplied raw numbers and declared method; "
                        "they do not prove extractor execution on those original pixels."),
        ),
    )
