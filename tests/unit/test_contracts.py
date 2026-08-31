import shutil
from pathlib import Path

import pytest

from latent_art_bench.evaluation.contracts import measurement_code_closure
from latent_art_bench.evaluation.qualification_orchestration import (
    load_exact_qualification_manifest,
)
from latent_art_bench.io import stable_hash, write_jsonl
from latent_art_bench.schemas import CanonicalWorkRecord, ReproductionRecord

ROOT = Path(__file__).resolve().parents[2]


def test_measurement_code_closure_excludes_unrelated_reporting_and_generation() -> None:
    chromatic = measurement_code_closure(ROOT, "chromatic")
    learned = measurement_code_closure(ROOT, "learned_formal")

    assert "src/latent_art_bench/evaluation/chromatic_v2.py" in chromatic
    assert "src/latent_art_bench/features/learned_formal.py" not in chromatic
    assert "src/latent_art_bench/evaluation/learned_formal_v2.py" in learned
    assert "src/latent_art_bench/features/chromatic.py" not in learned
    for closure in (chromatic, learned):
        assert (
            "src/latent_art_bench/evaluation/qualification_orchestration.py"
            in closure
        )
        assert "src/latent_art_bench/manifests.py" in closure
        assert "src/latent_art_bench/cli.py" not in closure
        assert "src/latent_art_bench/reporting/pilot.py" not in closure
        assert "src/latent_art_bench/generation/openai_images.py" not in closure
        assert all(len(digest) == 64 for digest in closure.values())


def test_orchestration_change_invalidates_each_measurement_closure(tmp_path: Path) -> None:
    baseline = {}
    for measurement in ("chromatic", "learned_formal"):
        closure = measurement_code_closure(ROOT, measurement)
        baseline[measurement] = stable_hash(closure)
        for relative in closure:
            destination = tmp_path / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)

    orchestration = (
        tmp_path
        / "src/latent_art_bench/evaluation/qualification_orchestration.py"
    )
    orchestration.write_text(
        orchestration.read_text(encoding="utf-8") + "\n# semantic change\n",
        encoding="utf-8",
    )

    for measurement in ("chromatic", "learned_formal"):
        assert stable_hash(measurement_code_closure(tmp_path, measurement)) != baseline[
            measurement
        ]


@pytest.mark.parametrize(
    "expected_type", [CanonicalWorkRecord, ReproductionRecord]
)
def test_qualification_manifest_loader_rejects_mixed_record_types(
    tmp_path: Path,
    expected_type: type[CanonicalWorkRecord] | type[ReproductionRecord],
) -> None:
    canonical = CanonicalWorkRecord(
        canonical_work_id="work_1",
        artist_id="artist_1",
        artist_name="Artist One",
        title="Work One",
        attribution_status="confirmed",
        public_domain_status="confirmed",
        split="train",
    )
    reproduction = ReproductionRecord(
        reproduction_id="reproduction_1",
        canonical_work_id="work_1",
        source_id="museum_1",
        local_path="data/reproduction_1.png",
        native_width=512,
        native_height=512,
        split="train",
    )
    manifest = tmp_path / "mixed.jsonl"
    write_jsonl(manifest, [canonical, reproduction])

    with pytest.raises(ValueError, match="must contain only"):
        load_exact_qualification_manifest(manifest, expected_type)


def test_qualification_manifest_loader_rejects_empty_input(tmp_path: Path) -> None:
    manifest = tmp_path / "empty.jsonl"
    write_jsonl(manifest, [])

    with pytest.raises(ValueError, match="manifest is empty"):
        load_exact_qualification_manifest(manifest, CanonicalWorkRecord)
