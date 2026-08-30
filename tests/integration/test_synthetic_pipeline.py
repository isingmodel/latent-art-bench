from pathlib import Path

from latent_art_bench.features.chromatic import extract_chromatic_features
from latent_art_bench.io import hash_file
from latent_art_bench.manifests import validate_records
from latent_art_bench.preprocessing.pipeline import preprocess_reproductions
from latent_art_bench.preprocessing.synthetic import write_synthetic_images
from latent_art_bench.schemas import ReproductionRecord


def test_synthetic_manifest_pipeline_is_deterministic(tmp_path: Path, pilot_config) -> None:
    sources = write_synthetic_images(tmp_path / "sources", size=32, seed=41)
    reproductions = [
        ReproductionRecord(
            reproduction_id=f"reproduction-{name}",
            canonical_work_id=f"work-{name}",
            source_id="synthetic-v1",
            local_path=str(path),
            sha256=hash_file(path),
            split="train",
        )
        for name, path in sorted(sources.items())
    ]
    assert validate_records(reproductions, root=tmp_path, check_files=True) == {
        "reproduction": 5
    }

    first_views = preprocess_reproductions(
        reproductions, pilot_config.preprocessing, tmp_path, tmp_path / "derived"
    )
    second_views = preprocess_reproductions(
        reproductions, pilot_config.preprocessing, tmp_path, tmp_path / "derived"
    )
    assert [row.output_sha256 for row in first_views] == [
        row.output_sha256 for row in second_views
    ]
    assert [row.derived_view_id for row in first_views] == [
        row.derived_view_id for row in second_views
    ]

    first_features = extract_chromatic_features(
        first_views, pilot_config.measurements.chromatic, tmp_path
    )
    second_features = extract_chromatic_features(
        second_views, pilot_config.measurements.chromatic, tmp_path
    )
    assert [row.model_dump(mode="json") for row in first_features] == [
        row.model_dump(mode="json") for row in second_features
    ]
