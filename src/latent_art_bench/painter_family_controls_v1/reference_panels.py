"""Offline, hash-anchored raw reference means from the retained learned audit.

Only existing embedding archives and provenance records are read. No image,
checkpoint, inference, network operation or prospective outcome is needed.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .protocol import ARTISTS
from .transport_artifact import ANCHOR, ANCHOR_SHA, LEARNED, ROOT, file_sha, verify_bindings

ENCODERS = ("clip", "csd")
PANEL_IDS = (
    "primary_original",
    "primary_audited_region",
    "development_original",
    "development_audited_region",
)
REFERENCE_COUNTS = {"reference": (297, 106, 141, 105), "development": (101, 36, 48, 36)}
AUDITED_COUNTS = {"reference": (41, 23, 13, 13), "development": (17, 7, 11, 6)}
SCHEMA = "painter-family-reference-panels-candidate/1.0"
IMPLEMENTATION_FILES = (
    "src/latent_art_bench/painter_family_controls_v1/reference_panels.py",
    "src/latent_art_bench/painter_family_controls_v1/protocol.py",
    "src/latent_art_bench/painter_family_controls_v1/transport_artifact.py",
    "src/latent_art_bench/painter_family_controls_v1/analysis.py",
)


def _box(row):
    value = row.get("box")
    if (
        not isinstance(value, list)
        or len(value) != 4
        or any(type(x) not in (int, float) for x in value)
    ):
        raise ValueError("reference crop box must contain four numeric coordinates")
    left, top, right, bottom = value
    if not 0 <= left < right <= 1 or not 0 <= top < bottom <= 1:
        raise ValueError("reference crop box is invalid")
    return value


def reference_panels(rows, embeddings):
    """Assemble all four fixed targets, retaining each selected row's identity.

    An audited target replaces an original with its already declared audited row;
    an original without an audited row remains original. Means are never normalized.
    The pure adapter is for supplied arrays; provenance authentication is performed
    by ``prepare``/``load_prepared`` before calling it on retained observations.
    """
    values = np.asarray(embeddings, dtype=np.float64)
    if (
        values.ndim != 2
        or values.shape[0] != len(rows)
        or values.shape[1] < 1
        or not np.isfinite(values).all()
        or np.any(np.abs(np.linalg.norm(values, axis=1) - 1) > 1e-4)
    ):
        raise ValueError("embedding rows must match the manifest and be finite unit vectors")
    lookup = {}
    for index, row in enumerate(rows):
        if not isinstance(row.get("id"), str) or not row["id"]:
            raise ValueError("each reference or generated row requires an identity")
        key = (row["id"], row.get("view"))
        if key in lookup:
            raise ValueError("duplicate retained image/view identity")
        if row.get("role") not in ("generated", "reference", "development"):
            raise ValueError("unknown retained image role")
        if row.get("view") not in ("original", "audited_region"):
            raise ValueError("unknown retained image view")
        if row["role"] == "generated" and row["view"] != "original":
            raise ValueError("generated images cannot acquire reference crops")
        lookup[key] = index

    for row in rows:
        if row["role"] == "generated":
            continue
        if row.get("painter") not in ARTISTS:
            raise ValueError("unknown reference painter")
        if (
            not isinstance(row.get("path"), str)
            or not row["path"]
            or not isinstance(row.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
        ):
            raise ValueError("reference source path and SHA-256 identity are required")
        box = _box(row)
        if row["view"] == "original":
            if box != [0, 0, 1, 1]:
                raise ValueError("original reference must retain the original source box")
        else:
            index = lookup.get((row["id"], "original"))
            if index is None or box == [0, 0, 1, 1]:
                raise ValueError("audited row must declare a changed region of an original")
            original = rows[index]
            if any(
                row.get(key) != original.get(key) for key in ("role", "painter", "path", "sha256")
            ):
                raise ValueError("audited row differs from its original source identity")

    result = {}
    for role, panel in (("reference", "primary"), ("development", "development")):
        originals = [row for row in rows if row["role"] == role and row["view"] == "original"]
        counts = Counter(row["painter"] for row in originals)
        crops = Counter(
            row["painter"]
            for row in rows
            if row["role"] == role and row["view"] == "audited_region"
        )
        if tuple(counts[p] for p in ARTISTS) != REFERENCE_COUNTS[role]:
            raise ValueError("fixed reference/development painter census changed")
        if tuple(crops[p] for p in ARTISTS) != AUDITED_COUNTS[role]:
            raise ValueError("fixed audited-region painter census changed")
        for view in ("original", "audited_region"):
            memberships, means, replacements = [], [], []
            for painter in ARTISTS:
                members, selected, replacement_count = [], [], 0
                for original in (row for row in originals if row["painter"] == painter):
                    original_index = lookup[(original["id"], "original")]
                    index = lookup.get((original["id"], view), original_index)
                    row = rows[index]
                    replacement_count += row["view"] == "audited_region"
                    selected.append(index)
                    members.append(
                        dict(
                            id=row["id"],
                            painter=painter,
                            original_row_index=original_index,
                            selected_row_index=index,
                            selected_view=row["view"],
                            source_path=row["path"],
                            source_sha256=row["sha256"],
                            box=row["box"],
                        )
                    )
                memberships.append(members)
                means.append(values[selected].mean(axis=0).tolist())
                replacements.append(replacement_count)
            panel_id = f"{panel}_{view}"
            result[panel_id] = dict(
                panel_id=panel_id,
                source_role=role,
                reference_view=view,
                painter_order=list(ARTISTS),
                counts=list(REFERENCE_COUNTS[role]),
                total=sum(REFERENCE_COUNTS[role]),
                audited_replacements_by_painter=replacements,
                original_rows_by_painter=[
                    n - c for n, c in zip(REFERENCE_COUNTS[role], replacements)
                ],
                memberships=memberships,
                reference_means=means,
                mean_convention="raw arithmetic mean of unit image embeddings; no renormalization",
            )
    return result


def _read(path):
    return json.loads(Path(path).read_text())


def _retained(root):
    """Authenticate the full retained provenance chain before reading any NPZ."""
    root = Path(root)
    verify_bindings({ANCHOR: ANCHOR_SHA}, root=root)
    anchor = _read(root / ANCHOR)
    verify_bindings(anchor["bindings"], root=root)
    bindings = {ANCHOR: ANCHOR_SHA, **anchor["bindings"]}
    inputs = _read(root / LEARNED / "inputs.json")
    adapter = _read(root / LEARNED / "csd_adapter_inputs_v2.json")
    for extra in (inputs["bindings"], adapter["bindings"]):
        verify_bindings(extra, root=root)
        for path, digest in extra.items():
            if path in bindings and bindings[path] != digest:
                raise ValueError("conflicting retained hash anchors")
            bindings[path] = digest
    if len(inputs["rows"]) != 2009 or set(inputs["models"]) != set(ENCODERS):
        raise ValueError("retained row or fixed encoder census changed")
    panels, contracts = {}, {}
    for encoder in ENCODERS:
        relative = f"{LEARNED}/embeddings_{encoder}.npz"
        receipt = _read(root / LEARNED / f"extraction_{encoder}.json")
        if (
            receipt["input_sha256"] != bindings[f"{LEARNED}/inputs.json"]
            or receipt["embeddings_sha256"] != bindings[relative]
            or receipt["model"] != inputs["models"][encoder]
            or receipt["shape"] != [2009, 768]
            or receipt["dtype"] != "float32"
        ):
            raise ValueError("retained extraction receipt disagrees with anchored inputs")
        with np.load(root / relative, allow_pickle=False) as archive:
            if archive.files != ["embeddings"]:
                raise ValueError("unexpected retained embedding archive members")
            values = archive["embeddings"]
            if values.shape != (2009, 768) or values.dtype != np.float32:
                raise ValueError("retained embedding shape or dtype changed")
            panels[encoder] = reference_panels(inputs["rows"], values)
        contracts[encoder] = dict(
            model=receipt["model"],
            processor=receipt["processor"],
            extraction_receipt=f"{LEARNED}/extraction_{encoder}.json",
            extraction_receipt_sha256=bindings[f"{LEARNED}/extraction_{encoder}.json"],
            embeddings_sha256=bindings[relative],
            input_sha256=receipt["input_sha256"],
            unit_norm_tolerance=1e-4,
            feature_dimension=768,
        )
    return bindings, panels, contracts


def prepare(output, *, root=ROOT):
    """Create an old-input-only candidate; never authorizes or freezes collection."""
    root, output = Path(root), Path(output)
    bindings, panels, contracts = _retained(root)
    bindings.update({relative: file_sha(root / relative) for relative in IMPLEMENTATION_FILES})
    record = dict(
        schema=SCHEMA,
        status="old-input candidate; not a complete prospective study freeze",
        created_utc=datetime.now(timezone.utc).isoformat(),
        new_observations=0,
        live_authorization=False,
        bindings=bindings,
        painter_order=list(ARTISTS),
        panel_order=list(PANEL_IDS),
        encoder_order=list(ENCODERS),
        encoder_contracts=contracts,
        panels=panels,
        source_census=dict(
            original_primary=649,
            original_development=221,
            audited_primary_replacements=90,
            audited_development_replacements=41,
            retained_embedding_rows=2009,
            retained_generated_rows=1008,
        ),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        stream.write(json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return file_sha(output)


def load_prepared(path, *, expected_sha256, root=ROOT):
    """Require an externally frozen digest and recheck sources and raw means.

    ``root`` may be a relocated evidence bundle preserving the bound relative
    paths. Missing source records fail closed; no public weights or pixels are read.
    """
    if (
        not isinstance(expected_sha256, str)
        or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)
        or file_sha(path) != expected_sha256
    ):
        raise ValueError("reference artifact differs from externally bound identity")
    record = _read(path)
    if (
        record.get("schema") != SCHEMA
        or record.get("painter_order") != list(ARTISTS)
        or record.get("panel_order") != list(PANEL_IDS)
        or record.get("encoder_order") != list(ENCODERS)
        or record.get("new_observations") != 0
        or record.get("live_authorization") is not False
        or record.get("bindings", {}).get(ANCHOR) != ANCHOR_SHA
    ):
        raise ValueError("reference artifact schema, anchor or axes changed")
    bindings, panels, contracts = _retained(root)
    stored = record["bindings"]
    required = set(bindings) | set(IMPLEMENTATION_FILES)
    if set(stored) != required or any(stored[key] != value for key, value in bindings.items()):
        raise ValueError("reference artifact source bindings are incomplete or changed")
    verify_bindings(stored, root=root)
    if record["panels"] != panels or record["encoder_contracts"] != contracts:
        raise ValueError("reference artifact differs from retained means, membership or encoders")
    return record
