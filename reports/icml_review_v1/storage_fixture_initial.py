"""Explicit supplemental offline fixture; never part of vanilla ``make check``.

Run only the two named historical test modules, with ``-p storage_fixture`` and
``--storage-fixture-receipt PATH``. Frozen tests and production guards stay intact.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import platform
import shutil
import socket
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FAKE_FREE = 10 * 1024**3
SCOPES = {
    "tests/painter_naming_replication_v1/test_replication.py": (
        "input_root",
        "latent_art_bench.painter_naming_replication_v1.collection",
    ),
    "tests/painter_map_validation_v2/test_operations.py": (
        "cohort",
        "latent_art_bench.painter_map_validation_v2.collection",
    ),
}
BOUND_PATHS = [
    *SCOPES,
    "src/latent_art_bench/painter_naming_replication_v1/collection.py",
    "src/latent_art_bench/painter_naming_replication_v1/common.py",
    "src/latent_art_bench/painter_map_validation_v2/collection.py",
    "src/latent_art_bench/painter_map_validation_v2/common.py",
    "reports/icml_review_v1/storage_fixture.py",
    "reports/icml_review_v1/validation_environment_first.json",
    "pytest-paper.ini",
    "uv.lock",
]
STATE = {"tests": {}, "resource_observations": [], "network_calls_blocked": 0}


def hashes():
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in BOUND_PATHS}


def pytest_addoption(parser):
    parser.addoption("--storage-fixture-receipt", required=True)


def pytest_configure(config):
    destination = Path(config.getoption("--storage-fixture-receipt")).resolve()
    if destination.exists():
        raise pytest.UsageError("supplemental receipt already exists; never overwrite it")
    STATE.update(
        destination=str(destination),
        start_utc=datetime.now(timezone.utc).isoformat(),
        invocation=list(config.invocation_params.args),
        python=platform.python_version(),
        real_workspace_disk_before=shutil.disk_usage(ROOT)._asdict(),
        sha256_before=hashes(),
        selected_modules=list(SCOPES),
        fake_free_bytes=FAKE_FREE,
    )


def pytest_collection_modifyitems(items):
    for item in items:
        try:
            relative = str(Path(item.path).resolve().relative_to(ROOT))
        except ValueError as exc:
            raise pytest.UsageError("storage fixture only allows its two named modules") from exc
        if relative not in SCOPES or item.get_closest_marker("live"):
            raise pytest.UsageError("storage fixture only allows its two named offline modules")


@pytest.fixture(autouse=True)
def supplemental_no_real_network(monkeypatch):
    """All network I/O is forbidden in this explicitly selected pytest process."""

    def prohibited(*args, **kwargs):
        STATE["network_calls_blocked"] += 1
        raise AssertionError("supplemental storage run prohibits all real network I/O")

    monkeypatch.setattr(socket, "create_connection", prohibited)
    monkeypatch.setattr(socket, "getaddrinfo", prohibited)
    monkeypatch.setattr(socket.socket, "connect", prohibited)
    monkeypatch.setattr(socket.socket, "connect_ex", prohibited)
    monkeypatch.setattr(socket.socket, "sendto", prohibited)


class ScopedShutil:
    """Delegate unchanged operations; fake only this collector's exact tmp root."""

    def __init__(self, original, root, observation):
        self.original = original
        self.root = root
        self.observation = observation

    def __getattr__(self, name):
        return getattr(self.original, name)

    def disk_usage(self, path):
        actual = self.original.disk_usage(path)
        if Path(path).resolve() == self.root:
            self.observation["fake_disk_queries"] += 1
            # Keep the public named-tuple shape and a consistent total/used/free.
            total = max(actual.total, FAKE_FREE)
            return type(actual)(total, total - FAKE_FREE, FAKE_FREE)
        self.observation["real_disk_queries_outside_scope"] += 1
        return actual


@pytest.fixture(autouse=True)
def supplemental_sufficient_storage(request, monkeypatch):
    relative = str(Path(request.node.path).resolve().relative_to(ROOT))
    fixture, module_name = SCOPES[relative]
    if fixture not in request.fixturenames:
        yield
        return
    root = request.getfixturevalue("tmp_path").resolve()
    if root == ROOT or ROOT in root.parents:
        raise AssertionError("synthetic root must be outside the real workspace")
    module = importlib.import_module(module_name)
    observation = {
        "nodeid": request.node.nodeid,
        "temporary_root": str(root),
        "real_disk_before": shutil.disk_usage(root)._asdict(),
        "fake_disk_queries": 0,
        "real_disk_queries_outside_scope": 0,
    }
    STATE["resource_observations"].append(observation)
    proxy = ScopedShutil(module.shutil, root, observation)
    assert proxy.disk_usage(ROOT) == shutil.disk_usage(ROOT)
    # Assign a collector-local proxy, not shutil.disk_usage process-wide. Existing
    # per-test monkeypatches (including free=0) can replace proxy.disk_usage.
    monkeypatch.setattr(module, "shutil", proxy)
    yield
    observation["collection_receipts"] = []
    for path in sorted(root.rglob("collection_receipt.json")):
        receipt = json.loads(path.read_text())
        observation["collection_receipts"].append(
            {
                "relative_path": str(path.relative_to(root)),
                **{
                    key: receipt.get(key)
                    for key in ("status", "reason", "attempts", "posted_attempts", "slot_counts")
                },
            }
        )


def pytest_runtest_logreport(report):
    STATE["tests"].setdefault(report.nodeid, {})[report.when] = report.outcome


def pytest_sessionfinish(session, exitstatus):
    STATE.update(
        end_utc=datetime.now(timezone.utc).isoformat(),
        pytest_exitstatus=int(exitstatus),
        real_workspace_disk_after=shutil.disk_usage(ROOT)._asdict(),
        sha256_after=hashes(),
    )
    unchanged = STATE["sha256_before"] == STATE["sha256_after"]
    STATE["bound_bytes_unchanged"] = unchanged
    STATE["passed"] = sum(v.get("call") == "passed" for v in STATE["tests"].values())
    STATE["failed_or_error"] = sum("failed" in v.values() for v in STATE["tests"].values())
    storage_node = (
        "tests/painter_map_validation_v2/test_operations.py::"
        "test_storage_stop_is_terminal_without_network"
    )
    STATE["zero_storage_override_verified"] = any(
        row["nodeid"] == storage_node
        and any(
            receipt["reason"] == "storage_reserve" and receipt["attempts"] == 0
            for receipt in row.get("collection_receipts", [])
        )
        for row in STATE["resource_observations"]
    )
    STATE["claim"] = (
        "Supplemental offline verification with a declared sufficient-storage fixture; "
        "this is not a vanilla make check pass."
    )
    if (
        not unchanged
        or STATE["network_calls_blocked"]
        or not STATE["zero_storage_override_verified"]
    ):
        session.exitstatus = 1
    STATE["effective_exitstatus"] = int(session.exitstatus)
    with Path(STATE["destination"]).open("x") as handle:
        json.dump(STATE, handle, indent=2, sort_keys=True)
        handle.write("\n")
