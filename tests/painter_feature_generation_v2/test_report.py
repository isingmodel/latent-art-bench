import numpy as np
import pytest

from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import empirical, report
from latent_art_bench.painter_feature_generation_v2.artifacts import MANIFESTS, publish


def test_report_renders_numbers_and_does_not_invent_a_model_ranking():
    real = {p: np.full((10, 31), i) for i, p in enumerate(PAINTER_IDS)}
    comparison = empirical.finite_comparisons(real, dict(real, artist_free=np.full((16, 31), 10)))
    comparison["copy_diagnostics"] = dict(generated_exact_duplicate_excess=0, candidates=[])
    meta = [
        dict(
            painter_id=p,
            role="confirmation",
            frame_count=10,
            acquired_count=10,
            measured_count=10,
            acquisition_failure_reasons={},
            profile_counts={"srgb": 10},
            measured_short_side_summary=[1024, 2048, 3000],
            measured_aspect_ratio_summary=[1, 1.5, 2],
            content_memberships={"water": 10},
        )
        for p in PAINTER_IDS
    ]
    text = report.render(
        "fixture",
        dict(
            comparisons={"gpt-image-2": comparison},
            generation={},
            metadata_diagnostics=dict(by_painter_and_role=meta),
            stratified_distances=[],
        ),
        dict(
            scenarios=[
                dict(
                    scenario="shift",
                    joint_coverage_nondegenerate_endpoints=0.86,
                    coverage_mc_wilson_95=[0.77, 0.91],
                    zero_variance_endpoint_counts=[0],
                )
            ]
        ),
        dict(status="complete_paired_features", expected_records=200),
        {
            "sd-fixture": dict(
                repetitions=25,
                simultaneous_endpoint_count=60,
                endpoints=[],
                qualification_diagnostics=[
                    dict(painter_id=p, family=f, finite_energy=0.1234)
                    for p in PAINTER_IDS
                    for f in ("color", "spatial", "texture")
                ],
            )
        },
    )
    assert "40 works: 40 acquired" in text
    assert "12/12" in text
    assert "0.8600" in text
    assert "Development-to-qualification" in text and "0.1234" in text
    assert "sd-fixture/analysis.json" in text
    assert "not demonstrated" in text
    assert "not significance tests or a ranking" in text
    assert "None means" not in text  # The literal metadata field is formatted as code.
    assert "`None` means no model identifier" in text
    assert "#" in text and "nan" not in text.lower()


def test_report_does_not_omit_registered_repeated_analysis(tmp_path):
    base = tmp_path / MANIFESTS / "method"
    publish(base / "method_freeze.json", dict(inputs=[]))
    publish(
        base / "empirical_analysis.json",
        dict(comparisons={"sd-turbo": dict(experiment_id="sd-run")}),
    )
    with pytest.raises(ValueError, match="repeated SD-Turbo analysis"):
        report.execute(tmp_path, "method")


def test_markdown_table_escapes_cells_and_has_commonmark_separation():
    rendered = report.table(["one"], [["a|b\nc"]])
    assert rendered.startswith("\n|")
    assert "a\\|b c" in rendered


def test_native_geometry_summary_preserves_counts_without_a_large_dictionary_cell():
    summary = report.geometry_summary({"1402x1122": 3, "1169x1346": 1})
    assert "2 sizes" in summary and "1402×1122 (3/4)" in summary
    assert "landscape 3/4" in summary
    assert report.geometry_summary({"unreported": 4}) == "unreported"
