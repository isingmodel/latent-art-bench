"""Bind terminal collector evidence to fixed learned-feature axes, without inference.

All three collector-file hashes and both feature-artifact hashes must come from
an external receipt. Simulation inputs are denied by default and stay labeled
when explicitly inspected. This module has no service call or model download.
"""

from __future__ import annotations

import base64
import copy
import gzip
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np
from PIL import Image

from . import protocol as p
from .transport_artifact import ANCHOR, ANCHOR_SHA, ROOT, file_sha, verify_bindings

RECORD_FILES = ("run.json", "events.jsonl", "terminal.json")


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def reject(value):
        raise ValueError("nonfinite JSON constant: " + value)
    return json.loads(data, object_pairs_hook=unique, parse_constant=reject)


def _bound_bytes(path, expected):
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("an external SHA-256 binding is required")
    value = Path(path).read_bytes()
    if _digest(value) != expected:
        raise ValueError("file differs from externally bound identity: " + str(path))
    return value


def _time(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("recorded timestamp must include a timezone")
    return result.astimezone(timezone.utc)


@dataclass(frozen=True)
class TerminalCensus:
    """Detached JSON evidence; properties return copies, not mutable backing state."""

    run_dir: Path
    evidence_json: str

    @property
    def evidence(self):
        return _json(self.evidence_json)


def _inside(root, relative):
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        raise ValueError("retained artifact escapes the collector directory")
    return path


def load_terminal_census(run_dir, *, expected_hashes, allow_simulation=False):
    """Read a permanently closed full design, including explicit missing slots.

    This verifies evidence identity and census consistency. Collector safety
    qualification remains separate; a hash is not financial authorization.
    """
    root = Path(run_dir).resolve()
    if set(expected_hashes) != set(RECORD_FILES):
        raise ValueError("bind run.json, events.jsonl and terminal.json explicitly")
    bodies = {name: _bound_bytes(_inside(root, name), expected_hashes[name])
              for name in RECORD_FILES}
    manifest, terminal = (_json(bodies[name]) for name in ("run.json", "terminal.json"))
    if manifest.get("schema") != "painter-family-controls-collector/2.0":
        raise ValueError("unsupported collector manifest")
    simulation = manifest.get("simulation_only")
    if type(simulation) is not bool or terminal.get("simulation_only") is not simulation:
        raise ValueError("simulation identity is absent or contradictory")
    if simulation and allow_simulation is not True:
        raise ValueError("simulation receipts cannot be treated as scientific observations")
    if manifest.get("namespace") != p.NAMESPACE or terminal.get("namespace") != p.NAMESPACE:
        raise ValueError("foreign collection namespace")
    slots = manifest["slots"]
    if len(slots) != p.EXPECTED_OUTPUTS:
        raise ValueError("the terminal manifest must retain all 4608 assignments")
    normalized = copy.deepcopy(slots)
    for slot in normalized:
        for key in ("window_start", "window_end"):
            slot[key] = p.utc_datetime(slot[key]).isoformat()
    p.verify_assignments(normalized, normalized[0]["window_start"])
    manifest_hash = p.canonical_sha(manifest)
    if (terminal["manifest_sha256"] != manifest_hash
            or terminal["ledger_sha256"] != _digest(bodies["events.jsonl"])):
        raise ValueError("terminal receipt does not bind its manifest and ledger")
    by_id = {slot["id"]: slot for slot in slots}
    starts, ends, last, known_costs = {}, {}, {}, []
    active, started_slots, attempts_by_slot = set(), set(), {}
    latest_start, paused, retry_count = None, False, 0
    terminal_time = _time(terminal["ended_at"])
    previous_hash = None
    window_attempts = [[] for _ in range(8)]
    for sequence, line in enumerate(bodies["events.jsonl"].splitlines(keepends=True)):
        event = _json(line)
        saved = event.pop("sha256")
        if (not line.endswith(b"\n") or p.canonical_sha(event) != saved
                or type(event["sequence"]) is not int or event["sequence"] != sequence
                or event["previous_sha256"] != previous_hash
                or event["manifest_sha256"] != manifest_hash):
            raise ValueError("event chain or manifest binding changed")
        previous_hash = saved
        if event["kind"] == "pause":
            if _time(event["at"]) > terminal_time:
                raise ValueError("terminal closure precedes a retained event")
            paused = True
            continue
        slot = by_id[event["id"]]
        if event["kind"] == "start":
            attempt_id = event["attempt_id"]
            if (attempt_id in starts or type(event["attempt"]) is not int
                    or not 1 <= event["attempt"] <= 3
                    or event["attempt"] != attempts_by_slot.get(slot["id"], 0) + 1
                    or attempt_id != f"{slot['id']}-a{event['attempt']}"
                    or event["payload_sha256"] != p.canonical_sha(slot["payload"])
                    or event["simulation_only"] is not simulation):
                raise ValueError("duplicate, foreign or mislabeled request intent")
            if (paused or len(active) >= 3
                    or any(starts[key]["id"] == slot["id"] for key in active)):
                raise ValueError("start violates retained pause or active-request state")
            started_at = _time(event["started_at"])
            if started_at > terminal_time:
                raise ValueError("terminal closure precedes a retained start")
            if latest_start is not None and (started_at - latest_start).total_seconds() < 5:
                raise ValueError("start violates fixed global spacing")
            if event["attempt"] == 1:
                first = next(row["id"] for row in slots if row["session"] == slot["session"]
                             and row["id"] not in started_slots)
                if first != slot["id"]:
                    raise ValueError("start changes frozen within-window order")
            else:
                previous = last.get(slot["id"])
                delay = 20 if event["attempt"] == 2 else 60
                if (previous is None or previous["success"] or previous["refusal"]
                        or previous["retryable"] is not True
                        or previous["cost_usd"] is None or previous["pause_reasons"]
                        or previous["status"] not in (429, 500, 502, 503, 504)
                        or (started_at - _time(previous["ended_at"])).total_seconds() < delay):
                    raise ValueError("retry lacks eligible earlier technical failure")
                retry_count += 1
                if retry_count > 96:
                    raise ValueError("global retry limit exceeded")
            for key in ("session", "scene", "arm", "window_start", "window_end"):
                if p.canonical_sha(event[key]) != p.canonical_sha(slot[key]):
                    raise ValueError("request intent differs from assignment")
            if not _time(slot["window_start"]) <= _time(event["started_at"]) < _time(
                slot["window_end"]
            ):
                raise ValueError("request was started outside its assigned window")
            starts[attempt_id] = event
            active.add(attempt_id)
            started_slots.add(slot["id"])
            attempts_by_slot[slot["id"]] = event["attempt"]
            latest_start = started_at
            window_attempts[slot["session"]].append(attempt_id)
        elif event["kind"] == "end":
            attempt_id = event["attempt_id"]
            if attempt_id not in starts or attempt_id in ends:
                raise ValueError("end lacks one unique earlier intent")
            intent = starts[attempt_id]
            for key in ("id", "attempt", "session", "window_start", "window_end"):
                if p.canonical_sha(event[key]) != p.canonical_sha(intent[key]):
                    raise ValueError("completion differs from its request intent")
            if _time(event["ended_at"]) < _time(intent["started_at"]):
                raise ValueError("completion precedes start")
            if _time(event["ended_at"]) > terminal_time:
                raise ValueError("terminal closure precedes a retained completion")
            if type(event["success"]) is not bool or type(event["refusal"]) is not bool:
                raise ValueError("invalid completion status type")
            if event["cost_usd"] is not None:
                if type(event["cost_usd"]) is not str:
                    raise ValueError("charge must retain its exact decimal string")
                charge = Decimal(event["cost_usd"])
                if not charge.is_finite() or charge < 0:
                    raise ValueError("invalid retained charge")
                known_costs.append(charge)
            ends[attempt_id] = event
            active.remove(attempt_id)
            last[event["id"]] = event
            paused = paused or bool(event["pause_reasons"]) or event["cost_usd"] is None
        else:
            raise ValueError("unknown event kind")
    open_attempts = set(starts) - set(ends)
    uncertain = len(open_attempts) + sum(e["cost_usd"] is None for e in ends.values())
    with localcontext() as context:
        context.prec = 4096
        settled = sum(known_costs, Decimal(0))
        outstanding = p.RESERVATION * uncertain
        accounted = p.HISTORICAL_ACCOUNTED + settled + outstanding
    if (Decimal(terminal["historical_usd"]) != p.HISTORICAL_ACCOUNTED
            or Decimal(terminal["new_settled_usd"]) != settled
            or Decimal(terminal["outstanding_reservations_usd"]) != outstanding
            or Decimal(terminal["accounted_usd"]) != accounted):
        raise ValueError("terminal accounting differs from retained attempts")
    census = terminal["census"]
    if (len(census) != 4608 or len({row["id"] for row in census}) != 4608
            or {row["id"] for row in census} != set(by_id)):
        raise ValueError("terminal missingness census changed")
    reported = {row["id"]: row for row in census}
    images, missing = [], []
    for slot in slots:
        outcome = last.get(slot["id"])
        if any(starts[key]["id"] == slot["id"] for key in open_attempts):
            state = "unclosed_intent_requires_reconciliation"
        elif outcome and outcome["success"]:
            state = "successful"
        elif outcome and outcome["cost_usd"] is None:
            state = "unknown_charge_requires_reconciliation"
        elif outcome and outcome["refusal"]:
            state = "content_refusal"
        elif outcome:
            state = "failed"
        elif _time(terminal["ended_at"]) >= _time(slot["window_end"]):
            state = "unstarted_window_expired"
        else:
            state = "unstarted_terminal_closure"
        expected_state = dict(id=slot["id"], session=slot["session"], state=state)
        if p.canonical_sha(reported[slot["id"]]) != p.canonical_sha(expected_state):
            raise ValueError("terminal state disagrees with retained attempt history")
        identity = {key: slot[key] for key in
                    ("id", "model", "session", "scene", "scene_id", "arm")}
        if state != "successful":
            missing.append(dict(identity, state=state))
            continue
        if (type(outcome["status"]) is not int or outcome["status"] != 200
                or outcome["refusal"] or outcome["pause_reasons"]
                or outcome["cost_usd"] is None or len(outcome["images"]) != 1
                or outcome["response"] is None or outcome["response"]["complete"] is not True):
            raise ValueError("successful observation lacks complete evidence")
        receipt = outcome["images"][0]
        for key in ("width", "height"):
            if type(receipt[key]) is not int or receipt[key] != 1024:
                raise ValueError("successful observation has unexpected image geometry")
        relative = f"images/{outcome['attempt_id']}-0.original"
        if receipt["path"] != relative or receipt["index"] != 0:
            raise ValueError("original image receipt points to another attempt")
        raw = _bound_bytes(_inside(root, relative), receipt["sha256"])
        if len(raw) != receipt["bytes"]:
            raise ValueError("original byte count changed")
        response = outcome["response"]
        response_path = f"responses/{outcome['attempt_id']}.json.gz"
        if response["path"] != response_path:
            raise ValueError("raw response points to another attempt")
        with gzip.open(_inside(root, response_path), "rb") as stream:
            body = stream.read(64 * 1024**2 + 1)
        if (len(body) > 64 * 1024**2 or len(body) != response["bytes"]
                or _digest(body) != response["sha256"]):
            raise ValueError("retained raw response changed")
        # Hashes alone do not establish the relation between two retained files.
        # Verify the response actually contains this original and decode geometry.
        response_value = _json(body)
        data = response_value.get("data")
        if not isinstance(data, list) or len(data) != 1:
            raise ValueError("successful raw response does not contain one original")
        try:
            returned = base64.b64decode(data[0]["b64_json"], validate=True)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("raw response image is not valid inline base64") from exc
        if returned != raw:
            raise ValueError("retained original differs from its raw response image")
        with Image.open(io.BytesIO(raw)) as image:
            image.load()
            if (image.size != (1024, 1024) or Image.MIME.get(image.format) != receipt["mime"]
                    or image.format != receipt["format"]):
                raise ValueError("actual decoded original differs from its image receipt")
        images.append(dict(identity, attempt_id=outcome["attempt_id"], path=relative,
                           sha256=receipt["sha256"], view="original", box=[0, 0, 1, 1]))
    if (terminal["planned"] != 4608 or terminal["successful"] != len(images)
            or terminal["attempts"] != len(starts)
            or terminal["status"] != ("complete" if len(images) == 4608 else "incomplete")):
        raise ValueError("terminal summary differs from its complete fixed census")
    times = []
    for window, ids in enumerate(window_attempts):
        assigned = next(slot for slot in slots if slot["session"] == window)
        times.append(dict(
            window=window, assigned_start=assigned["window_start"],
            assigned_end=assigned["window_end"],
            attempts=[dict(id=starts[key]["id"], attempt_id=key,
                           started_at=starts[key]["started_at"],
                           ended_at=ends[key]["ended_at"] if key in ends else None)
                      for key in ids],
        ))
    evidence = dict(schema="painter-family-terminal-feature-census/1.0", namespace=p.NAMESPACE,
                    simulation_only=simulation, record_hashes=dict(expected_hashes),
                    collector_manifest_sha256=manifest_hash, images=images,
                    missing=missing, window_times=times, planned=4608)
    return TerminalCensus(root, json.dumps(evidence, sort_keys=True, allow_nan=False))


def revalidate_census(census):
    """Reject forged detached state, including flipping a simulation into observations."""
    evidence = census.evidence
    verified = load_terminal_census(
        census.run_dir, expected_hashes=evidence["record_hashes"],
        allow_simulation=evidence["simulation_only"] is True,
    )
    if p.canonical_sha(evidence) != p.canonical_sha(verified.evidence):
        raise ValueError("detached census differs from its bound collector evidence")
    return verified


def encoder_contract(encoder, *, root=ROOT):
    if encoder not in ("clip", "csd"):
        raise ValueError("only the two already fixed learned encoders are supported")
    verify_bindings({ANCHOR: ANCHOR_SHA}, root=root)
    anchor = _json((Path(root) / ANCHOR).read_bytes())
    path = f"reports/painter_learned_audit_v1/extraction_{encoder}.json"
    receipt = _json(_bound_bytes(Path(root) / path, anchor["bindings"][path]))
    return dict(name=encoder, feature_dimension=768, model=receipt["model"],
                processor=receipt["processor"], retained_extraction_receipt=path,
                retained_extraction_sha256=anchor["bindings"][path],
                generated_view="original full frame; native encoder preprocessing unchanged",
                embedding_normalization="unit L2; no later implicit normalization")


def feature_manifest(census, encoder, *, root=ROOT):
    """Describe inputs for post-terminal extraction; does not load encoder weights."""
    evidence = revalidate_census(census).evidence
    return dict(schema="painter-family-learned-feature-inputs/1.0", namespace=p.NAMESPACE,
                simulation_only=evidence["simulation_only"],
                terminal_record_hashes=evidence["record_hashes"],
                collector_manifest_sha256=evidence["collector_manifest_sha256"],
                encoder=encoder_contract(encoder, root=root), rows=evidence["images"],
                missing=evidence["missing"], window_times=evidence["window_times"])


def load_embedding_census(census, manifest_path, embeddings_path, *,
                          expected_manifest_sha256, expected_embeddings_sha256, root=ROOT):
    """Bind each vector to its exact successful image and the original design cell."""
    manifest = _json(_bound_bytes(manifest_path, expected_manifest_sha256))
    encoder = manifest["encoder"]["name"]
    if p.canonical_sha(manifest) != p.canonical_sha(feature_manifest(census, encoder, root=root)):
        raise ValueError("feature input membership, timing or measurement contract changed")
    vector_bytes = _bound_bytes(embeddings_path, expected_embeddings_sha256)
    with np.load(io.BytesIO(vector_bytes), allow_pickle=False) as archive:
        if set(archive.files) != {"embeddings", "ids"}:
            raise ValueError("embedding archive must contain vectors and explicit row IDs")
        values, ids = archive["embeddings"], archive["ids"]
    rows = manifest["rows"]
    if (ids.dtype.kind not in ("U", "S") or ids.ndim != 1
            or ids.tolist() != [row["id"] for row in rows]):
        raise ValueError("embedding row IDs differ from bound image order")
    if (values.shape != (len(rows), 768) or values.dtype.kind != "f"
            or not np.isfinite(values).all()
            or np.any(np.abs(np.linalg.norm(values, axis=1) - 1) > 1e-4)):
        raise ValueError("expected finite unit embeddings for every successful original")
    generated = np.full((6, 8, 12, 8, 768), np.nan)
    observed = np.zeros((6, 8, 12, 8), dtype=bool)
    for row, vector in zip(rows, values):
        # Recheck pixels at consumption time, not just at earlier census loading.
        if file_sha(_inside(census.run_dir, row["path"])) != row["sha256"]:
            raise ValueError("original changed after census verification")
        cell = (p.MODELS.index(row["model"]), row["session"], row["scene"],
                p.ARMS.index(row["arm"]))
        if observed[cell]:
            raise ValueError("more than one embedding maps to the same fixed cell")
        generated[cell], observed[cell] = vector, True
    return dict(generated=generated, observed=observed, window_times=manifest["window_times"],
                encoder=encoder, simulation_only=manifest["simulation_only"],
                missing=manifest["missing"], manifest_sha256=expected_manifest_sha256,
                embeddings_sha256=expected_embeddings_sha256,
                model_order=p.MODELS, arm_order=p.ARMS)
