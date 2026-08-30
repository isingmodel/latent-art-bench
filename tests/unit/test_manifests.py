from pathlib import Path

import pytest

from latent_art_bench.manifests import validate_records
from latent_art_bench.schemas import CanonicalWorkRecord, ReproductionRecord


def work(work_id: str, split: str) -> CanonicalWorkRecord:
    return CanonicalWorkRecord(
        canonical_work_id=work_id,
        artist_id="artist-1",
        artist_name="Artist One",
        title=work_id,
        attribution_status="confirmed",
        public_domain_status="confirmed",
        split=split,
    )


def reproduction(reproduction_id: str, work_id: str, split: str, digest: str) -> ReproductionRecord:
    return ReproductionRecord(
        reproduction_id=reproduction_id,
        canonical_work_id=work_id,
        source_id="source-1",
        local_path="missing-for-schema-only.png",
        sha256=digest,
        split=split,
    )


def test_validation_detects_canonical_work_split_leakage(tmp_path: Path) -> None:
    records = [
        work("work-1", "train"),
        reproduction("repro-1", "work-1", "held_out", "a" * 64),
    ]
    with pytest.raises(ValueError, match="split leakage"):
        validate_records(records, root=tmp_path)


def test_validation_detects_byte_duplicate_across_works(tmp_path: Path) -> None:
    records = [
        work("work-1", "train"),
        work("work-2", "train"),
        reproduction("repro-1", "work-1", "train", "a" * 64),
        reproduction("repro-2", "work-2", "train", "a" * 64),
    ]
    with pytest.raises(ValueError, match="byte-identical"):
        validate_records(records, root=tmp_path)


def test_valid_work_and_reproduction_manifest(tmp_path: Path) -> None:
    records = [
        work("work-1", "train"),
        reproduction("repro-1", "work-1", "train", "a" * 64),
    ]
    assert validate_records(records, root=tmp_path) == {
        "canonical_work": 1,
        "reproduction": 1,
    }
