"""Prepare old-only parameters and require external hash identity when loading.

No prospective observation, feature extraction, service call or live freeze is
performed. Retained numerical inputs are anchored to the completed transfer audit.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .analysis import fit_transport_parameters
from .protocol import ARTISTS, MODELS

ROOT = Path(__file__).resolve().parents[3]
ANCHOR = "reports/painter_prototype_transfer_v1/inputs.json"
ANCHOR_SHA = "bdcf38bb09da53c890a1a62ce268c0336824ccadfb6ba90ee711bdaf1a6f1baf"
LEARNED = "reports/painter_learned_audit_v1"
REFERENCE_COUNTS = (297, 106, 141, 105)


def file_sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_bindings(bindings, *, root=ROOT):
    root = Path(root).resolve()
    for relative, expected in bindings.items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("invalid artifact binding")
        if file_sha(path) != expected:
            raise ValueError(f"bound file changed: {relative}")


def old_arrays(rows, embeddings):
    """Select exact old full-frame named cells and equal-painter reference means."""
    values = np.asarray(embeddings, dtype=float)
    if values.ndim != 2 or values.shape[0] != len(rows) or values.shape[1] < 1:
        raise ValueError("embedding rows must match the bound input manifest")
    if (not np.isfinite(values).all()
            or np.any(np.abs(np.linalg.norm(values, axis=1) - 1) > 1e-4)):
        raise ValueError("retained embeddings must be finite unit vectors")
    old = np.full((6, 14, 2, 4, values.shape[1]), np.nan)
    refs = {painter: [] for painter in ARTISTS}
    selected, reference_ids = [], set()
    for index, row in enumerate(rows):
        if row["view"] != "original":
            continue
        if row["role"] == "reference":
            painter = row["painter"]
            key = (painter, row["id"])
            if painter not in refs or key in reference_ids:
                raise ValueError("duplicate or unknown primary reference")
            reference_ids.add(key)
            refs[painter].append(values[index])
        elif row["role"] == "generated" and row["arm"] in ARTISTS:
            if (type(row["scene"]) is not int or not 0 <= row["scene"] < 14
                    or type(row["repeat"]) is not int or row["repeat"] not in (0, 1)):
                raise ValueError("invalid old scene or repeat identity")
            cell = (MODELS.index(row["model"]), row["scene"], row["repeat"],
                    ARTISTS.index(row["arm"]))
            if np.isfinite(old[cell]).any():
                raise ValueError("duplicate old named cell")
            old[cell] = values[index]
            selected.append(row["id"])
    if not np.isfinite(old).all() or len(set(selected)) != 672:
        raise ValueError("incomplete or duplicate 672-image old named census")
    if tuple(len(refs[painter]) for painter in ARTISTS) != REFERENCE_COUNTS:
        raise ValueError("primary reference census differs from the fixed 649 works")
    means = np.stack([np.mean(refs[painter], axis=0) for painter in ARTISTS])
    return old, means


def prepare(output, *, root=ROOT):
    """Write a create-once parameter candidate; it is not a study authorization."""
    root, output = Path(root), Path(output)
    verify_bindings({ANCHOR: ANCHOR_SHA}, root=root)
    anchor = json.loads((root / ANCHOR).read_text())
    verify_bindings(anchor["bindings"], root=root)
    inputs = json.loads((root / LEARNED / "inputs.json").read_text())
    if len(inputs["rows"]) != 2009:
        raise ValueError("retained learned manifest row count changed")
    bindings = {ANCHOR: ANCHOR_SHA}
    for relative in anchor["bindings"]:
        if relative.startswith(LEARNED + "/"):
            bindings[relative] = anchor["bindings"][relative]
    for relative in (
        "src/latent_art_bench/painter_family_controls_v1/analysis.py",
        "src/latent_art_bench/painter_family_controls_v1/protocol.py",
        "src/latent_art_bench/painter_family_controls_v1/transport_artifact.py",
        "uv.lock",
    ):
        bindings[relative] = file_sha(root / relative)
    parameters = {}
    for encoder in ("clip", "csd"):
        with np.load(root / LEARNED / f"embeddings_{encoder}.npz", allow_pickle=False) as archive:
            old, refs = old_arrays(inputs["rows"], archive["embeddings"])
        parameters[encoder] = fit_transport_parameters(old, refs, encoder=encoder)
    record = dict(
        schema="painter-family-old-transport-candidate/1.0",
        status="prepared from old observations only; not a complete precollection freeze",
        created_utc=datetime.now(timezone.utc).isoformat(),
        new_observations=0, live_authorization=False, bindings=bindings,
        model_order=MODELS, painter_order=ARTISTS, old_named_count=672,
        reference_counts=REFERENCE_COUNTS, encoder_contracts=inputs["models"],
        parameters=parameters,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        stream.write(json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return file_sha(output)


def load_prepared(path, *, expected_sha256, root=ROOT):
    """Expected digest must come from the caller's separately frozen study manifest."""
    if (not isinstance(expected_sha256, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)
            or file_sha(path) != expected_sha256):
        raise ValueError("parameter artifact differs from externally bound identity")
    record = json.loads(Path(path).read_text())
    if (record.get("schema") != "painter-family-old-transport-candidate/1.0"
            or record.get("bindings", {}).get(ANCHOR) != ANCHOR_SHA
            or tuple(record.get("model_order", ())) != MODELS
            or tuple(record.get("painter_order", ())) != ARTISTS):
        raise ValueError("parameter artifact schema, anchor or axes changed")
    verify_bindings(record["bindings"], root=root)
    return record
