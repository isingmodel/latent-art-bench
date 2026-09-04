from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from latent_art_bench.io import canonical_json
from latent_art_bench.painter_feature_generation_v1 import exposure_denylist as dl

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _history_available() -> bool:
    if shutil.which("git") is None or not (REPOSITORY_ROOT / ".git").exists():
        return False
    for _, commit, path, _, _ in dl.SOURCES:
        probe = subprocess.run(
            ["git", "-C", str(REPOSITORY_ROOT), "cat-file", "-e", f"{commit}:{path}"],
            capture_output=True,
        )
        if probe.returncode != 0:
            return False
    return True


pytestmark = pytest.mark.skipif(not _history_available(), reason="pinned git history is required")


def test_work_id_resolution_covers_every_source_shape() -> None:
    assert dl._work_id_from_row({"physical_work_id": "work-aic-16633"}) == "work-aic-16633"
    assert dl._work_id_from_row({"canonical_work_id": "work-nga-46653"}) == "work-nga-46653"
    assert dl._work_id_from_row({"physical_work_id": "aic:16633"}) == "work-aic-16633"
    assert (
        dl._work_id_from_row({"canonical_object_url": "https://www.nga.gov/artworks/155712"})
        == "work-nga-155712"
    )
    assert dl._work_id_from_row({"title": "no identifier"}) is None


def test_rebuild_is_deterministic_and_matches_the_tracked_file() -> None:
    built = dl.build(REPOSITORY_ROOT)
    expected = "".join(canonical_json(row) + "\n" for row in built["rows"])
    tracked = REPOSITORY_ROOT / dl.OUTPUT_PATH
    assert tracked.is_file(), "run scripts/build_pfg_v1_exposure_denylist.py"
    assert tracked.read_text(encoding="utf-8") == expected


def test_every_historical_pixel_exposure_is_denylisted() -> None:
    rows = dl.load(REPOSITORY_ROOT)
    by_id = {row["physical_work_id"]: row for row in rows}
    base = (
        subprocess.run(
            ["git", "-C", str(REPOSITORY_ROOT), "show", f"{dl.SOURCES[0][1]}:{dl.SOURCES[0][2]}"],
            capture_output=True,
            check=True,
        )
        .stdout.decode()
        .splitlines()
    )
    for line in base:
        if line.strip():
            work_id = json.loads(line)["physical_work_id"]
            assert by_id[work_id]["denylisted"] is True
            assert by_id[work_id]["allowed_role"] == "development_only"
    assert all(row["denylisted"] == row["pixel_exposed"] for row in rows)
    assert all(row["artist_id"] in (None, *dl.PANEL) for row in rows)


def test_receipt_records_every_source_blob() -> None:
    receipt = json.loads((REPOSITORY_ROOT / dl.RECEIPT_PATH).read_text(encoding="utf-8"))
    assert [row["source"] for row in receipt["sources"]] == [row[0] for row in dl.SOURCES]
    assert all(len(row["blob_sha256"]) == 64 for row in receipt["sources"])
    assert receipt["counts"]["denylisted"] >= 118
