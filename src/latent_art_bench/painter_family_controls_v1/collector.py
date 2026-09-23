"""Offline qualification engine for the proposed family-control collection.

There is deliberately no live transport, credential lookup, URL fetch, or scheduler.
Only explicit simulation admits starts. A simulation ceiling is not authorization.
"""

from __future__ import annotations

import base64
import copy
import fcntl
import gzip
import hashlib
import io
import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Iterable, Optional

from PIL import Image

GIB = 1024**3
MIB = 1024**2
MAX_RESPONSE_BYTES = 64 * MIB
TECHNICAL_STATUSES = frozenset((429, 500, 502, 503, 504))
REFUSAL_CODES = frozenset(
    ("content_policy_violation", "moderation_blocked", "safety_violation",
     "image_generation_user_error", "invalid_prompt", "content_filter")
)


class CollectorError(RuntimeError):
    """A qualification invariant prevented an operation."""


class AdmissionDenied(CollectorError):
    pass


class AlreadyOwned(CollectorError):
    pass


def _money(value) -> Decimal:
    if isinstance(value, bool) or isinstance(value, float):
        raise ValueError("money requires Decimal, an integer, or an exact decimal string")
    try:
        result = Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("invalid charge") from exc
    if not result.is_finite() or result < 0:
        raise ValueError("charge must be finite and nonnegative")
    digits = result.as_tuple()
    if len(digits.digits) > 1000 or abs(digits.exponent) > 1000:
        raise ValueError("charge representation exceeds the supported exact range")
    return result


def _sum_money(*values):
    """Add validated amounts without ambient Decimal context rounding."""
    least_exponent = min(value.as_tuple().exponent for value in values)
    greatest_place = max(value.adjusted() for value in values)
    with localcontext() as context:
        context.prec = max(28, greatest_place - least_exponent + len(str(len(values))) + 2)
        return sum(values, Decimal(0))


def _utc(value) -> datetime:
    result = value if isinstance(value, datetime) else datetime.fromisoformat(
        str(value).replace("Z", "+00:00")
    )
    if result.tzinfo is None or result.utcoffset() != timedelta(0):
        raise ValueError("an explicit UTC timestamp is required")
    return result.astimezone(timezone.utc)


def _stamp(value) -> str:
    return _utc(value).isoformat().replace("+00:00", "Z")


def _encoded(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sync_directory(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _mkdir_durable(path: Path) -> None:
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir()
        _sync_directory(directory.parent)


def _create_once(path: Path, content: bytes) -> None:
    # A crash-created partial file is retained and must never be overwritten.
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        _sync_directory(path.parent)


def actual_free_bytes(path: Path) -> int:
    """Actual filesystem free bytes; tests may inject a deterministic function."""
    return shutil.disk_usage(path).free


@dataclass(frozen=True)
class CollectorPolicy:
    cumulative_ceiling_usd: Decimal = Decimal("120")

    def __post_init__(self):
        object.__setattr__(self, "cumulative_ceiling_usd", _money(self.cumulative_ceiling_usd))

    @property
    def historical_usd(self):
        return Decimal("112.293676")

    @property
    def reservation_usd(self):
        return Decimal("5")

    @property
    def new_settled_stop_usd(self):
        return Decimal("220")


@dataclass(frozen=True)
class MockResponse:
    """In-memory response fixture. Cost normally comes from retained usage.cost.

    An explicit fixture charge requires nonempty billing_evidence, modeling a
    separately documented charge. An absent charge is never inferred to be zero.
    """

    status_code: Optional[int]
    body: object = b""
    charge_usd: Optional[Decimal] = None
    billing_evidence: Optional[str] = None
    transport_error: Optional[str] = None


class MockTransport:
    """Finite fixtures only; this object cannot acquire data from a service."""

    def __init__(self, responses: Iterable[MockResponse]):
        self.responses = iter(responses)
        self.requests = []

    def exchange(self, payload):
        self.requests.append(copy.deepcopy(payload))
        response = next(self.responses)
        if type(response) is not MockResponse:
            raise TypeError("only MockResponse fixtures are accepted")
        return response


class Collector:
    """Durable synchronous state machine, with no mechanism for live execution.

    Use with a context manager. start() records intent, finish() drains even
    after window cutoff or a pause. Recovery never resumes ambiguous attempts.
    """

    def __init__(
        self,
        run_dir,
        slots,
        *,
        simulation=False,
        policy=None,
        free_bytes: Callable[[Path], int] = actual_free_bytes,
        write_volumes=(),
    ):
        self.root = Path(run_dir).resolve()
        if any(part.startswith("painter_specificity_") for part in self.root.parts):
            raise CollectorError("the old collector namespaces are permanently excluded")
        if policy is not None and type(policy) is not CollectorPolicy:
            raise TypeError("policy must be the exact validated CollectorPolicy type")
        if type(simulation) is not bool:
            raise TypeError("simulation must be boolean")
        self._policy = copy.deepcopy(policy) if policy is not None else CollectorPolicy()
        self._simulation = simulation
        if not self.simulation and self.policy.cumulative_ceiling_usd != Decimal("120"):
            raise CollectorError("a changed ceiling is allowed only for offline simulation")
        self._slots = {}
        for original in slots:
            slot = copy.deepcopy(original)
            required = {"id", "model", "session", "scene", "arm", "window_start",
                        "window_end", "payload"}
            if not required <= slot.keys():
                raise ValueError("slot is missing required assignment fields")
            if not re.fullmatch(r"[A-Za-z0-9_.-]+", slot["id"]) or slot["id"] in self._slots:
                raise ValueError("slot IDs must be unique safe filenames")
            start, end = _utc(slot["window_start"]), _utc(slot["window_end"])
            if end - start != timedelta(hours=4):
                raise ValueError("each assigned dispatch window must be four hours")
            expected_model = ("openai/" + slot["model"] if slot["model"].startswith("gpt-image")
                              else slot["model"])
            if slot["payload"].get("model") != expected_model:
                raise ValueError("payload and assigned model disagree")
            route = slot["payload"].get("provider", {})
            if (not isinstance(route.get("only"), list) or len(route["only"]) != 1
                    or not isinstance(route["only"][0], str)
                    or route.get("allow_fallbacks") is not False):
                raise ValueError("payload requires one sole provider and disabled fallbacks")
            slot["window_start"], slot["window_end"] = _stamp(start), _stamp(end)
            self._slots[slot["id"]] = slot
        self.free_bytes = free_bytes
        _mkdir_durable(self.root)
        self.write_volumes = tuple(dict.fromkeys(
            [self.root, *(Path(path).resolve() for path in write_volumes)]
        ))
        self._lock = (self.root / "collector.lock").open("a+b")
        try:
            fcntl.flock(self._lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self._lock.close()
            raise AlreadyOwned("another process owns this run") from exc
        self._closed = False
        self._owned_attempts = set()
        self._events = []
        self._starts = {}
        self._ends = {}
        self._open = set()
        self._last_by_slot = {}
        self._slot_attempt_counts = {}
        self._settled = Decimal(0)
        self._unknown_ends = 0
        self._retry_count = 0
        self._latest_start = None
        self._technical_streak = 0
        self._pauses = []
        self.journal_corrupt = False
        try:
            if os.path.lexists(self.root / "terminal.json"):
                raise CollectorError("terminal collection is permanently closed")
            for directory in ("responses", "images"):
                destination = self.root / directory
                if destination.is_symlink():
                    raise CollectorError("artifact directories must not be symlinks")
                _mkdir_durable(destination)
            manifest = {
                "schema": "painter-family-controls-collector/2.0",
                "namespace": "painter_family_controls_v1", "simulation_only": self.simulation,
                "cumulative_ceiling_usd": str(self.policy.cumulative_ceiling_usd),
                "historical_usd": str(self.policy.historical_usd),
                "reservation_usd": str(self.policy.reservation_usd),
                "new_settled_stop_usd": str(self.policy.new_settled_stop_usd),
                "disk_floor_bytes": 5 * GIB,
                "active_storage_reservation_bytes": 256 * MIB,
                "max_response_bytes": MAX_RESPONSE_BYTES,
                "write_volumes": [str(path) for path in self.write_volumes],
                "slots": list(self._slots.values()),
            }
            self.manifest_hash = _sha(_encoded(manifest))
            manifest_path = self.root / "run.json"
            if manifest_path.exists():
                if manifest_path.read_bytes() != _encoded(manifest) + b"\n":
                    raise CollectorError("run assignments or policy changed on recovery")
            else:
                _create_once(manifest_path, _encoded(manifest) + b"\n")
            self.ledger = self.root / "events.jsonl"
            self._recover()
        except BaseException:
            self.close()
            raise

    @property
    def policy(self):
        return copy.deepcopy(self._policy)

    @property
    def simulation(self):
        return self._simulation

    @property
    def slots(self):
        return MappingProxyType(copy.deepcopy(self._slots))

    @property
    def events(self):
        return copy.deepcopy(self._events)

    @property
    def pauses(self):
        return list(self._pauses)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        if not self._closed:
            fcntl.flock(self._lock.fileno(), fcntl.LOCK_UN)
            self._lock.close()
            self._closed = True

    def _assert_owner(self):
        if self._closed:
            raise CollectorError("collector owner is closed")
        if os.path.lexists(self.root / "terminal.json"):
            raise CollectorError("terminal collection is permanently closed")

    def _append(self, event):
        self._assert_owner()
        if self.journal_corrupt:
            raise CollectorError("journal is damaged; preserve it for reconciliation")
        event = dict(event, manifest_sha256=self.manifest_hash, sequence=len(self._events),
                     previous_sha256=self._events[-1]["sha256"] if self._events else None)
        event["sha256"] = _sha(_encoded(event))
        try:
            with self.ledger.open("ab") as stream:
                stream.write(_encoded(event) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            _sync_directory(self.root)
        except OSError:
            self.journal_corrupt = True
            self._pauses.append("journal persistence failed; unknown durable state")
            raise
        self._events.append(event)
        self._index(event)
        return copy.deepcopy(event)

    def _index(self, event):
        if event["kind"] == "start":
            self._starts[event["attempt_id"]] = event
            self._open.add(event["attempt_id"])
            self._slot_attempt_counts[event["id"]] = event["attempt"]
            self._retry_count += event["attempt"] > 1
            self._latest_start = event
        elif event["kind"] == "end":
            self._ends[event["attempt_id"]] = event
            self._open.remove(event["attempt_id"])
            self._last_by_slot[event["id"]] = event
            self._technical_streak = (self._technical_streak + 1
                                      if event.get("technical_failure") else 0)
            if event["cost_usd"] is None:
                self._unknown_ends += 1
            else:
                self._settled = _sum_money(self._settled, _money(event["cost_usd"]))

    def _verify_retained(self, event):
        """A valid journal cannot substitute for missing or changed retained bytes."""
        archive = event["response"]
        if archive is not None:
            expected = f"responses/{event['attempt_id']}.json.gz"
            if archive["path"] != expected or type(archive["complete"]) is not bool:
                raise ValueError("invalid retained response reference")
            path = self.root / expected
            if path.is_symlink() or not path.resolve().is_relative_to(self.root):
                raise ValueError("retained response escaped the run")
            with gzip.open(path, "rb") as stream:
                body = stream.read(MAX_RESPONSE_BYTES + 1)
            if (len(body) > MAX_RESPONSE_BYTES or len(body) != archive["bytes"]
                    or _sha(body) != archive["sha256"]):
                raise ValueError("retained response differs from its receipt")
        images = event["images"]
        if not isinstance(images, list):
            raise ValueError("invalid image receipts")
        indexes = set()
        for image in images:
            index = image["index"]
            if type(index) is not int or index < 0 or index in indexes:
                raise ValueError("invalid image receipt index")
            indexes.add(index)
            expected = f"images/{event['attempt_id']}-{index}.original"
            path = self.root / expected
            if (image["path"] != expected or path.is_symlink()
                    or not path.resolve().is_relative_to(self.root)):
                raise ValueError("invalid retained original reference")
            with path.open("rb") as stream:
                raw = stream.read(MAX_RESPONSE_BYTES + 1)
            if (len(raw) > MAX_RESPONSE_BYTES or len(raw) != image["bytes"]
                    or _sha(raw) != image["sha256"]):
                raise ValueError("retained original differs from its receipt")
        if event["success"] and (archive is None or not archive["complete"]
                                 or len(images) != 1):
            raise ValueError("success lacks complete retained evidence")

    def _validate_replay(self, event):
        if event["manifest_sha256"] != self.manifest_hash:
            raise ValueError("event belongs to another manifest")
        if event["kind"] == "pause":
            if type(event["reason"]) is not str:
                raise ValueError("invalid pause reason")
            _utc(event["at"])
            return
        slot = self._slots[event["id"]]
        if event["kind"] == "start":
            attempt = self._slot_attempt_counts.get(event["id"], 0) + 1
            expected = {
                "attempt_id": f"{event['id']}-a{attempt}", "attempt": attempt,
                "session": slot["session"], "scene": slot["scene"], "arm": slot["arm"],
                "window_start": slot["window_start"], "window_end": slot["window_end"],
                "reservation_usd": "5", "simulation_only": True,
                "payload_sha256": _sha(_encoded(slot["payload"])),
            }
            if _encoded({key: event[key] for key in expected}) != _encoded(expected):
                raise ValueError("start is inconsistent with its frozen assignment")
            started = _utc(event["started_at"])
            if not _utc(slot["window_start"]) <= started < _utc(slot["window_end"]):
                raise ValueError("start is outside its frozen window")
            if (self._latest_start and started - _utc(self._latest_start["started_at"])
                    < timedelta(seconds=5)):
                raise ValueError("start violates global spacing")
            if attempt == 1:
                first = next(row["id"] for row in self._slots.values()
                             if row["session"] == slot["session"]
                             and not self._slot_attempt_counts.get(row["id"]))
                if first != event["id"]:
                    raise ValueError("start violates frozen first-dispatch order")
        elif event["kind"] == "end":
            start = self._starts[event["attempt_id"]]
            keys = ("id", "attempt_id", "attempt", "session", "window_start", "window_end")
            if (_encoded({key: event[key] for key in keys})
                    != _encoded({key: start[key] for key in keys})):
                raise ValueError("end does not match its durable intent")
            if _utc(event["ended_at"]) < _utc(start["started_at"]):
                raise ValueError("end precedes its start")
            if any(type(event[key]) is not bool for key in
                   ("success", "refusal", "retryable", "technical_failure")):
                raise ValueError("invalid end status schema")
            if event["status"] is not None and (type(event["status"]) is not int
                                                 or not 100 <= event["status"] <= 599):
                raise ValueError("invalid HTTP status")
            if (not isinstance(event["pause_reasons"], list)
                    or any(type(reason) is not str for reason in event["pause_reasons"])):
                raise ValueError("invalid diagnostic schema")
            self._verify_retained(event)

    def _recover(self):
        if self.ledger.exists():
            for line in self.ledger.read_bytes().splitlines(keepends=True):
                try:
                    event = json.loads(line)
                    saved_hash = event.pop("sha256")
                    expected_previous = self._events[-1]["sha256"] if self._events else None
                    if (not line.endswith(b"\n") or _sha(_encoded(event)) != saved_hash
                            or type(event["sequence"]) is not int
                            or event["sequence"] != len(self._events)
                            or event["previous_sha256"] != expected_previous):
                        raise ValueError("invalid event chain")
                    event["sha256"] = saved_hash
                    if event["kind"] not in ("start", "end", "pause"):
                        raise ValueError("unknown event")
                    if event["kind"] == "start":
                        if event["attempt_id"] in self._starts or event["id"] not in self._slots:
                            raise ValueError("duplicate or foreign start")
                    if event["kind"] == "end":
                        if (event["attempt_id"] not in self._starts
                                or event["attempt_id"] in self._ends):
                            raise ValueError("unmatched or duplicate end")
                        if event["cost_usd"] is not None:
                            _money(event["cost_usd"])
                    self._validate_replay(event)
                    self._events.append(event)
                    self._index(event)
                except (ValueError, TypeError, KeyError, OSError, EOFError, StopIteration):
                    self.journal_corrupt = True
                    self._pauses.append("damaged journal; accounting is indeterminate")
                    break
        self._pauses.extend(event["reason"] for event in self._events if event["kind"] == "pause")
        if self.open_attempts:
            self._pauses.append("unclosed crash intents require evidence reconciliation")
        if any(event["cost_usd"] is None for event in self._ends.values()):
            self._pauses.append("unknown charges retain reservations; reconciliation required")
        if any(event.get("pause_reasons") for event in self._ends.values()):
            self._pauses.append("retained diagnostic pause requires evidence reconciliation")

    @property
    def starts(self):
        return MappingProxyType(copy.deepcopy(self._starts))

    @property
    def ends(self):
        return MappingProxyType(copy.deepcopy(self._ends))

    @property
    def open_attempts(self):
        return set(self._open)

    @property
    def outstanding_count(self):
        return len(self._open) + self._unknown_ends

    @property
    def new_settled_usd(self):
        return self._settled

    @property
    def accounted_usd(self):
        return _sum_money(self.policy.historical_usd, self.new_settled_usd,
                          self.policy.reservation_usd * self.outstanding_count)

    def _disk_reasons(self, proposed_active, destination=None):
        required = 5 * GIB + 256 * MIB * proposed_active
        reasons = []
        paths = list(self.write_volumes)
        for directory in ("responses", "images"):
            artifact_dir = self.root / directory
            if artifact_dir.is_symlink():
                reasons.append("artifact directories must not be symlinks")
            paths.append(artifact_dir.resolve())
        if destination is not None:
            paths.append(destination.parent.resolve())
        for path in dict.fromkeys(paths):
            try:
                free = self.free_bytes(path)
                if isinstance(free, bool) or not isinstance(free, int) or free < required:
                    reasons.append(f"insufficient actual free bytes on {path}: need {required}")
            except OSError as exc:
                reasons.append(f"cannot inspect write volume {path}: {type(exc).__name__}")
        return reasons

    def _last(self, slot_id):
        return self._last_by_slot.get(slot_id)

    def admission(self, slot_id, now):
        """Return every current reason to deny this slot, without any writes."""
        self._assert_owner()
        moment = _utc(now)
        slot = self._slots[slot_id]
        reasons = []
        if not self.simulation:
            reasons.append("default deny: this engine supports offline simulation only")
        if self._pauses or self.journal_corrupt:
            reasons.append("collector is paused; evidence reconciliation is required")
        if not _utc(slot["window_start"]) <= moment < _utc(slot["window_end"]):
            reasons.append("outside assigned four-hour dispatch window")
        if len(self.open_attempts) >= 3:
            reasons.append("three active attempts already reserved")
        if any(self._starts[key]["id"] == slot_id for key in self._open):
            reasons.append("slot already has an open attempt")
        if (self._latest_start
                and (moment - _utc(self._latest_start["started_at"])).total_seconds() < 5):
            reasons.append("global starts must be at least five seconds apart")
        if (_sum_money(self.accounted_usd, self.policy.reservation_usd)
                >= self.policy.cumulative_ceiling_usd):
            reasons.append("reservation-inclusive cumulative ceiling must remain "
                           "strictly below cap")
        if self.new_settled_usd >= self.policy.new_settled_stop_usd:
            reasons.append("new-run settled operating stop reached")
        previous = self._last(slot_id)
        if not self._slot_attempt_counts.get(slot_id):
            earlier = next((row["id"] for row in self._slots.values()
                            if row["session"] == slot["session"]
                            and not self._slot_attempt_counts.get(row["id"])), None)
            if earlier != slot_id:
                reasons.append("first dispatch must follow frozen within-window order")
        if previous:
            if not previous["retryable"]:
                reasons.append("slot is complete or not eligible for technical retry")
            if previous["attempt"] >= 3:
                reasons.append("two retries per slot exhausted")
            if self._retry_count >= 96:
                reasons.append("96 global retries exhausted")
            delay = 20 if previous["attempt"] == 1 else 60
            if moment < _utc(previous["ended_at"]) + timedelta(seconds=delay):
                reasons.append(f"technical retry requires {delay}-second delay")
        reasons.extend(self._disk_reasons(self.outstanding_count + 1))
        return reasons

    def select(self, now):
        """First currently eligible frozen slot, keeping the original assignment order."""
        for slot in self._slots.values():
            previous = self._last(slot["id"])
            if previous and (not previous["retryable"] or previous["attempt"] >= 3):
                continue
            if not self.admission(slot["id"], now):
                return copy.deepcopy(slot)
        return None

    def start(self, slot_id, now):
        reasons = self.admission(slot_id, now)
        if reasons:
            raise AdmissionDenied("; ".join(reasons))
        slot = self._slots[slot_id]
        attempt = 1 + self._slot_attempt_counts.get(slot_id, 0)
        attempt_id = f"{slot_id}-a{attempt}"
        intent = self._append({
            "kind": "start", "id": slot_id, "attempt_id": attempt_id, "attempt": attempt,
            "session": slot["session"], "scene": slot["scene"], "arm": slot["arm"],
            "window_start": slot["window_start"], "window_end": slot["window_end"],
            "started_at": _stamp(now), "reservation_usd": "5", "simulation_only": True,
            "payload_sha256": _sha(_encoded(slot["payload"])),
        })
        self._owned_attempts.add(attempt_id)
        return intent

    def pause(self, reason, now):
        self._pauses.append(str(reason))
        return self._append({"kind": "pause", "at": _stamp(now), "reason": str(reason)})

    def _read_body(self, response):
        chunks = (response.body,) if isinstance(response.body, bytes) else response.body
        retained, length = [], 0
        issue = None
        try:
            for chunk in chunks:
                if not isinstance(chunk, bytes):
                    raise TypeError("fixture response chunks must be bytes")
                remaining = MAX_RESPONSE_BYTES - length
                retained.append(chunk[:remaining])
                length += min(len(chunk), remaining)
                if len(chunk) > remaining:
                    issue = "response exceeds 64 MiB; bounded partial response retained"
                    break
        except Exception as exc:
            issue = f"response stream failed: {type(exc).__name__}; partial response retained"
        return b"".join(retained), issue

    def _images(self, value, attempt_id):
        images, issues = [], []
        data = value.get("data", [])
        if not isinstance(data, list):
            return [], ["image data field is not a list"]
        if len(data) != 1:
            issues.append(f"expected one image; received {len(data)}")
        for index, record in enumerate(data):
            try:
                raw = base64.b64decode(record["b64_json"], validate=True)
                metadata = {"index": index, "sha256": _sha(raw), "bytes": len(raw)}
                # Preserve original decoded bytes even when image inspection fails.
                path = self.root / "images" / f"{attempt_id}-{index}.original"
                disk_issues = self._disk_reasons(self.outstanding_count, path)
                if disk_issues:
                    issues.extend(disk_issues)
                    continue
                _create_once(path, raw)
                metadata["path"] = str(path.relative_to(self.root))
                images.append(metadata)
                with Image.open(io.BytesIO(raw)) as image:
                    metadata.update(width=image.width, height=image.height,
                                    mime=Image.MIME.get(image.format), format=image.format)
                    image.verify()
                if (metadata["width"], metadata["height"]) != (1024, 1024):
                    issues.append("returned geometry differs from 1024 by 1024")
                else:
                    with Image.open(io.BytesIO(raw)) as decoded:
                        decoded.load()
                if metadata["mime"] is None:
                    issues.append("decoded media type is unavailable")
            except (ValueError, TypeError, KeyError, OSError, SyntaxError,
                    Image.DecompressionBombError) as exc:
                issues.append(f"image decode/archive failed: {type(exc).__name__}")
        return images, issues

    def _finish(self, attempt_id, response, now):
        """Retain a fixture completion under its original window, including stragglers."""
        self._assert_owner()
        if type(response) is not MockResponse:
            raise TypeError("only MockResponse fixtures are accepted")
        if attempt_id not in self._owned_attempts or attempt_id not in self.open_attempts:
            raise CollectorError("completion must match an attempt started by this owner")
        intent = self._starts[attempt_id]
        if _utc(now) < _utc(intent["started_at"]):
            raise ValueError("completion precedes its start")
        slot = self._slots[intent["id"]]
        body, body_issue = self._read_body(response)
        issues = [body_issue] if body_issue else []
        status = response.status_code
        if status is not None and (type(status) is not int or not 100 <= status <= 599):
            issues.append("invalid response status; expected an integer HTTP status or None")
            status = None
        value = {}
        try:
            value = json.loads(body, parse_float=Decimal,
                               parse_constant=lambda _: (_ for _ in ()).throw(
                                   ValueError("nonfinite JSON constant")))
            if not isinstance(value, dict):
                raise ValueError("response must be an object")
        except (ValueError, UnicodeError):
            value = {}
            issues.append("response is not a complete JSON object")
        cost, billing_source = None, None
        try:
            usage = value.get("usage", {})
            if not isinstance(usage, dict):
                raise ValueError("usage must be an object")
            if isinstance(usage, dict) and usage.get("cost") is not None:
                cost, billing_source = _money(usage["cost"]), "retained response usage.cost"
            if response.charge_usd is not None:
                if (type(response.billing_evidence) is not str
                        or not response.billing_evidence.strip()):
                    raise ValueError("explicit charge lacks billing evidence")
                fixture_cost = _money(response.charge_usd)
                if cost is not None and fixture_cost != cost:
                    raise ValueError("conflicting charge evidence")
                cost, billing_source = fixture_cost, response.billing_evidence
        except ValueError as exc:
            cost = None
            issues.append(str(exc))
        if cost is None:
            issues.append("unknown charge; retain the five-dollar reservation")
        elif cost > self.policy.reservation_usd:
            issues.append("charge exceeds five-dollar reservation")
        if response.transport_error:
            issues.append("transport error: " + str(response.transport_error))
        archive = None
        path = self.root / "responses" / f"{attempt_id}.json.gz"
        disk_issues = self._disk_reasons(self.outstanding_count, path)
        issues.extend(disk_issues)
        if not disk_issues:
            try:
                _create_once(path, gzip.compress(body, mtime=0))
                archive = {"path": str(path.relative_to(self.root)), "sha256": _sha(body),
                           "bytes": len(body), "complete": body_issue is None}
            except OSError as exc:
                issues.append(f"response archive failed: {type(exc).__name__}")
        error = value.get("error", {})
        if not isinstance(error, dict):
            issues.append("error must be an object")
        error_code = error.get("code") if isinstance(error, dict) else None
        if type(error_code) not in (str, int, type(None)):
            error_code = "malformed_error_code"
            issues.append("malformed error code")
        refusal_value = value.get("refusal", False)
        if type(refusal_value) is not bool:
            issues.append("refusal must be boolean")
            refusal_value = False
        refusal = error_code in REFUSAL_CODES or refusal_value
        if status == 200 and error and not refusal:
            issues.append("success status contains an error response")
        images = []
        reported = {key: value.get(key) if isinstance(value.get(key), (str, type(None)))
                    else str(value.get(key)) for key in ("model", "provider")}
        if archive and ("data" in value or (status == 200 and not refusal)):
            images, image_issues = self._images(value, attempt_id)
            issues.extend(image_issues)
        expected_provider = slot["payload"]["provider"]["only"][0]
        for key, expected in (("model", slot["payload"]["model"]),
                              ("provider", expected_provider)):
            if reported[key] is not None and reported[key] != expected:
                issues.append(f"contradictory echoed {key}")
        technical = not refusal and status != 200
        if technical and status not in TECHNICAL_STATUSES:
            issues.append("nonretryable technical failure requires diagnosis")
        if technical and self._technical_streak >= 2:
            issues.append("three consecutive technical failures")
        retryable = (technical and status in TECHNICAL_STATUSES
                     and cost is not None and not issues)
        result = self._append({
            "kind": "end", "id": intent["id"], "attempt_id": attempt_id,
            "attempt": intent["attempt"], "session": intent["session"],
            "window_start": intent["window_start"], "window_end": intent["window_end"],
            "ended_at": _stamp(now), "status": status,
            "success": status == 200 and not refusal and not issues,
            "refusal": refusal, "error_code": error_code, "retryable": retryable,
            "technical_failure": technical, "cost_usd": str(cost) if cost is not None else None,
            "billing_evidence": billing_source, "response": archive, "images": images,
            "reported": reported, "pause_reasons": issues,
        })
        self._owned_attempts.remove(attempt_id)
        self._pauses.extend(issues)
        return result

    def finish(self, attempt_id, response, now):
        """Drain a fixture; unexpected processing failure always stops new starts."""
        self._assert_owner()
        if type(response) is not MockResponse:
            raise TypeError("only MockResponse fixtures are accepted")
        if attempt_id not in self._owned_attempts or attempt_id not in self._open:
            raise CollectorError("completion must match an attempt started by this owner")
        if _utc(now) < _utc(self._starts[attempt_id]["started_at"]):
            raise ValueError("completion precedes its start")
        try:
            return self._finish(attempt_id, response, now)
        except Exception as exc:
            reason = "completion processing failed; retain reservation: " + type(exc).__name__
            self._pauses.append(reason)
            if not self.journal_corrupt:
                try:
                    self._append({"kind": "pause", "at": _stamp(now), "reason": reason})
                except Exception:
                    self.journal_corrupt = True
            raise

    def execute_one(self, slot_id, transport, *, started_at, ended_at):
        """Run a single in-memory fixture; no service transport can be passed here."""
        if type(transport) is not MockTransport:
            raise TypeError("only the finite built-in MockTransport is supported")
        intent = self.start(slot_id, started_at)
        try:
            response = transport.exchange(self._slots[slot_id]["payload"])
        except Exception as exc:
            response = MockResponse(None, transport_error=type(exc).__name__)
        return self.finish(intent["attempt_id"], response, ended_at)

    def close_terminal(self, now, reason="operator terminal closure"):
        """Permanently close a drained run with a complete slot-by-slot census."""
        self._assert_owner()
        if self._owned_attempts:
            raise CollectorError("drain owned active attempts before terminal closure")
        if self.journal_corrupt:
            raise CollectorError("cannot finalize a damaged journal")
        try:
            for event in self._ends.values():
                self._verify_retained(event)
        except (ValueError, TypeError, KeyError, OSError, EOFError) as exc:
            self.pause("retained evidence failed terminal verification", now)
            raise CollectorError("retained evidence failed terminal verification") from exc
        census = []
        for slot in self._slots.values():
            previous = self._last(slot["id"])
            if any(self._starts[key]["id"] == slot["id"] for key in self._open):
                state = "unclosed_intent_requires_reconciliation"
            elif previous and previous["success"]:
                state = "successful"
            elif previous and previous["cost_usd"] is None:
                state = "unknown_charge_requires_reconciliation"
            elif previous and previous["refusal"]:
                state = "content_refusal"
            elif previous:
                state = "failed"
            elif _utc(now) >= _utc(slot["window_end"]):
                state = "unstarted_window_expired"
            else:
                state = "unstarted_terminal_closure"
            census.append({"id": slot["id"], "session": slot["session"], "state": state})
        receipt = {
            "namespace": "painter_family_controls_v1", "simulation_only": self.simulation,
            "status": "complete" if all(r["state"] == "successful" for r in census)
            else "incomplete", "reason": reason, "ended_at": _stamp(now),
            "planned": len(census), "successful": sum(r["state"] == "successful" for r in census),
            "attempts": len(self._starts), "census": census,
            "historical_usd": str(self.policy.historical_usd),
            "new_settled_usd": str(self.new_settled_usd),
            "outstanding_reservations_usd": str(
                self.policy.reservation_usd * self.outstanding_count),
            "accounted_usd": str(self.accounted_usd), "manifest_sha256": self.manifest_hash,
            "ledger_sha256": _sha(self.ledger.read_bytes() if self.ledger.exists() else b""),
            "pause_reasons": list(self._pauses),
        }
        try:
            _create_once(self.root / "terminal.json", _encoded(receipt) + b"\n")
        except OSError:
            self._pauses.append("terminal archive failed; do not resume dispatch")
            if not os.path.lexists(self.root / "terminal.json"):
                self.pause("terminal archive failed; do not resume dispatch", now)
            raise
        return receipt
