"""Read-only resource inspection; no live collection can be enabled here."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

from . import protocol as p

ROOT = Path(__file__).resolve().parents[3]
HISTORICAL = ROOT / "data/manifests/painter_specificity_v2/psv2-20260911"
LEDGER_SHA = "b131798cd2b803d6d60569def72700bb35daacdd2c5602e0dc854b7bd77a3ffd"
COLLECTION_SHA = "3491468b0dc6875d28e530595341d2a5a659a5aec175e5f6f7999f05b5851480"


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def storage_status(path, *, disk_usage=shutil.disk_usage):
    """Inspect the real volume of the nearest existing ancestor without writing."""
    requested = Path(path).expanduser().absolute()
    ancestor = requested
    while not ancestor.exists():
        if ancestor == ancestor.parent:
            raise ValueError("no existing storage ancestor")
        ancestor = ancestor.parent
    if not ancestor.is_dir():
        raise ValueError("destination or existing ancestor is not a directory")
    resolved = ancestor.resolve()
    usage = disk_usage(resolved)
    free = usage.free
    if not isinstance(free, int) or free < 0:
        raise ValueError("invalid actual free-byte observation")
    return dict(
        requested_path=str(requested), existing_ancestor=str(resolved),
        destination_exists=requested.is_dir(), writable=os.access(resolved, os.W_OK),
        device=os.stat(resolved).st_dev, free_bytes=free,
        initial_capacity_bytes=p.INITIAL_CAPACITY,
        meets_initial_capacity=free >= p.INITIAL_CAPACITY,
        meets_idle_collector_floor=free >= p.DISK_FLOOR,
        note="actual filesystem free bytes; no reservation, directory creation or write probe",
    )


def inspect(destination=None, start=None):
    """Report the existing unapproved state; no CLI override grants approval."""
    reasons = [
        "new collection is not authorized; proposed $350 ceiling is not operative",
        "current route availability and pricing have not been verified for a new run",
        "no complete precollection freeze for this run exists",
        "no live transport or execution command is implemented in this offline package",
    ]
    collection = json.loads((HISTORICAL / "collection.json").read_text())
    history_intact = (
        sha(HISTORICAL / "collection.json") == COLLECTION_SHA
        and sha(HISTORICAL / "attempts.jsonl") == LEDGER_SHA
        and collection["status"] == "completed"
        and str(collection["accounted_usd"]) == str(p.HISTORICAL_ACCOUNTED)
    )
    if not history_intact:
        reasons.append("historical terminal accounting or its binding changed")
    storage = storage_status(ROOT if destination is None else destination)
    if destination is None:
        reasons.append("no user-provided output/cache/temporary storage destination")
    if not storage["writable"] or not storage["meets_initial_capacity"]:
        reasons.append("destination lacks writable 40 GiB initial capacity")
    if not storage["meets_idle_collector_floor"]:
        reasons.append("actual free space is below the 5 GiB collector floor")
    normalized_start = None
    if start is None:
        reasons.append("absolute UTC session windows are not frozen")
    else:
        normalized_start = p.utc_datetime(start).isoformat()
    weight_paths = [
        ROOT / "artifacts/models/clip-vit-large-patch14/model.safetensors",
        ROOT / "artifacts/models/csd-vit-large/pytorch_model.bin",
    ]
    present = [str(path.relative_to(ROOT)) for path in weight_paths if path.is_file()]
    if len(present) != len(weight_paths):
        reasons.append("fixed extraction weights are not locally available; no download attempted")
    return dict(
        schema="painter-family-controls-readiness/1.0", ready_for_live_collection=False,
        namespace=p.NAMESPACE, operations="read-only; no network or new generation",
        historical_terminal_record_intact=history_intact,
        historical_accounted_usd=str(p.HISTORICAL_ACCOUNTED),
        approved_cumulative_ceiling_usd=str(p.CURRENT_CEILING),
        proposed_unapproved_ceiling_usd=str(p.PROPOSED_CEILING),
        planned_outputs=p.EXPECTED_OUTPUTS, proposed_start=normalized_start,
        storage=storage, present_weight_files=present, unresolved=reasons,
    )
