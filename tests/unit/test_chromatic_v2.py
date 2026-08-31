from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image, ImageCms
from pydantic import ValidationError

from latent_art_bench.evaluation.chromatic_v2 import (
    BootstrapRatioEvidence,
    ChromaticV2Protocol,
    aggregate_lee_resolution_collapse,
    assess_lee_input_eligibility,
    build_chromatic_v2_probe,
    decide_chromatic_v2_scope,
    group_reproduction_alternates,
    nested_leave_source_out_artist_accuracy,
    stratified_bootstrap_ratio,
    two_sample_ecdf_ks_distance,
)
from latent_art_bench.features.chromatic import chromatic_summary
from latent_art_bench.io import hash_file
from latent_art_bench.schemas import CanonicalWorkRecord, ReproductionRecord


def _pattern(width: int, height: int) -> Image.Image:
    y, x = np.indices((height, width), dtype=np.uint32)
    rgb = np.stack(
        (
            (x * 13 + y * 3) % 256,
            (x * 5 + y * 11) % 256,
            ((x // 7) * 19 + (y // 5) * 23) % 256,
        ),
        axis=2,
    ).astype(np.uint8)
    return Image.fromarray(rgb)


def _record(path: Path, reproduction_id: str = "repro-1") -> ReproductionRecord:
    with Image.open(path) as image:
        width, height = image.size
    return ReproductionRecord(
        reproduction_id=reproduction_id,
        canonical_work_id="work-1",
        source_id="museum",
        local_path=str(path),
        sha256=hash_file(path),
        native_width=width,
        native_height=height,
        split="train",
    )


def _v2_chromatic(pilot_config):
    return pilot_config.measurements.chromatic.model_copy(
        update={"vector_representation": "seamlessness"}
    )


def _canonical() -> CanonicalWorkRecord:
    return CanonicalWorkRecord(
        canonical_work_id="work-1",
        artist_id="artist-1",
        artist_name="Artist One",
        title="Landscape",
        genre="landscape_and_outdoor_place_scene",
        medium="Oil on canvas",
        attribution_status="confirmed",
        public_domain_status="confirmed",
    )


def test_protocol_freezes_q85_420_500_and_half_margin() -> None:
    protocol = ChromaticV2Protocol(bootstrap_draws=100)
    assert protocol.matched_input_long_side == 1024
    assert protocol.canonical_long_side == 500
    assert protocol.direct_resolution_long_sides == (500, 400, 256)
    assert protocol.paper_figure_resolution_long_sides == (
        500,
        1000,
        1500,
        2000,
        2500,
        3000,
    )
    assert protocol.distribution_collapse_statistic == "two_sample_ecdf_ks"
    assert protocol.distribution_collapse_ks_max == 0.05
    assert protocol.distribution_collapse_aggregation == (
        "every_eligible_image_and_resolution_pair"
    )
    assert protocol.jpeg_quality == 85
    assert protocol.jpeg_subsampling == 2
    assert protocol.sensitivity_jpeg_quality == 95
    assert protocol.sensitivity_jpeg_subsampling == 0
    assert protocol.perturbation_ratio_max == 0.5
    assert protocol.random_seed == 20260830

    with pytest.raises(ValidationError):
        ChromaticV2Protocol(perturbation_ratio_max=0.6)
    with pytest.raises(ValidationError):
        ChromaticV2Protocol(jpeg_quality=95)
    with pytest.raises(ValidationError):
        ChromaticV2Protocol(sensitivity_jpeg_subsampling=2)
    with pytest.raises(ValidationError):
        ChromaticV2Protocol(direct_resolution_long_sides=(500, 256, 400))
    with pytest.raises(ValidationError):
        ChromaticV2Protocol(distribution_collapse_ks_max=0.10)
    with pytest.raises(ValidationError):
        ChromaticV2Protocol(paper_figure_resolution_long_sides=(500, 1000, 1500, 2000, 2500, 2500))


def test_probe_uses_independent_source_branches_and_records_codec_provenance(
    tmp_path: Path, pilot_config
) -> None:
    path = tmp_path / "large.png"
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    _pattern(1200, 1600).save(path, format="PNG", icc_profile=profile)
    record = _record(path)
    protocol = ChromaticV2Protocol(bootstrap_draws=100)

    probe = build_chromatic_v2_probe(
        record,
        _v2_chromatic(pilot_config),
        pilot_config.preprocessing,
        tmp_path,
        protocol,
    )

    assert probe.observed_source_sha256 == record.sha256
    assert probe.codec_probe_eligible is True
    assert max(probe.matched_input_width, probe.matched_input_height) == 1024
    assert probe.matched_input_parent_pixel_sha256 == probe.normalized_pixel_sha256
    assert probe.jpeg_quality == 85
    assert probe.jpeg_subsampling == 2
    assert probe.jpeg_payload_sha256 is not None
    assert probe.lossless_processing_deterministic is True
    assert probe.lossless_repeat_normalized_pixel_sha256 == probe.normalized_pixel_sha256
    assert (
        probe.lossless_repeat_canonical_pixel_sha256
        == probe.direct_resolution_branches["500"].pixel_sha256
    )
    assert probe.codec_lossless_control is not None
    assert probe.codec_q85_420_treatment is not None
    assert probe.sensitivity_jpeg_quality == 95
    assert probe.sensitivity_jpeg_subsampling == 0
    assert probe.sensitivity_jpeg_payload_sha256 is not None
    assert probe.codec_q95_444_sensitivity is not None
    assert max(probe.codec_lossless_control.width, probe.codec_lossless_control.height) == 500
    assert (
        max(
            probe.codec_q85_420_treatment.width,
            probe.codec_q85_420_treatment.height,
        )
        == 500
    )
    assert (
        probe.codec_lossless_control.branch_parent_pixel_sha256 == probe.matched_input_pixel_sha256
    )
    assert (
        probe.codec_q85_420_treatment.branch_parent_pixel_sha256 == probe.matched_input_pixel_sha256
    )
    assert (
        probe.codec_q95_444_sensitivity.branch_parent_pixel_sha256
        == probe.matched_input_pixel_sha256
    )

    for requested in (500, 400, 256):
        branch = probe.direct_resolution_branches[str(requested)]
        assert branch.branch_parent_pixel_sha256 == probe.normalized_pixel_sha256
        assert branch.exact_requested_resolution is True
        assert max(branch.width, branch.height) == requested
        assert len(branch.primary_vector) == 1
        assert branch.primary_vector[0] == pytest.approx(branch.scalars["seamlessness"])
        assert len(branch.diagnostic_histogram) == 11
        assert branch.mean_rescaling_defined is True
        assert len(branch.mean_rescaled_distribution_sha256) == 64

    assert [pair.comparison_long_side for pair in probe.resolution_distribution_pairs] == [400, 256]
    for pair in probe.resolution_distribution_pairs:
        assert pair.reference_long_side == 500
        assert pair.statistic == "two_sample_ecdf_ks"
        assert pair.threshold == 0.05
        assert pair.independently_derived_from_shared_source is True
        assert pair.exact_requested_resolutions is True
        assert pair.ks_distance is not None
        assert (
            pair.reference_mean_rescaled_distribution_sha256
            == probe.direct_resolution_branches[
                str(pair.reference_long_side)
            ].mean_rescaled_distribution_sha256
        )
        assert (
            pair.comparison_mean_rescaled_distribution_sha256
            == probe.direct_resolution_branches[
                str(pair.comparison_long_side)
            ].mean_rescaled_distribution_sha256
        )

    repeated = build_chromatic_v2_probe(
        record,
        _v2_chromatic(pilot_config),
        pilot_config.preprocessing,
        tmp_path,
        protocol,
    )
    assert repeated.provenance_sha256 == probe.provenance_sha256
    assert repeated.jpeg_payload_sha256 == probe.jpeg_payload_sha256


def test_probe_applies_exif_before_branching_and_never_upsamples(
    tmp_path: Path, pilot_config
) -> None:
    path = tmp_path / "oriented.jpg"
    exif = Image.Exif()
    exif[274] = 6
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    _pattern(700, 900).save(
        path,
        format="JPEG",
        quality=95,
        subsampling=0,
        exif=exif,
        icc_profile=profile,
    )

    probe = build_chromatic_v2_probe(
        _record(path, "repro-oriented"),
        _v2_chromatic(pilot_config),
        pilot_config.preprocessing,
        tmp_path,
        ChromaticV2Protocol(bootstrap_draws=100),
    )

    assert (probe.encoded_width, probe.encoded_height) == (700, 900)
    assert (probe.normalized_width, probe.normalized_height) == (900, 700)
    assert probe.codec_probe_eligible is False
    assert "below the frozen 1024-pixel matched input" in probe.codec_ineligibility_reason
    assert probe.matched_input_pixel_sha256 is None
    assert probe.jpeg_payload_sha256 is None
    assert probe.lossless_processing_deterministic is True
    assert probe.codec_lossless_control is None
    assert probe.codec_q85_420_treatment is None
    assert probe.codec_q95_444_sensitivity is None
    assert probe.direct_resolution_branches["500"].exact_requested_resolution is True
    assert (
        max(
            probe.direct_resolution_branches["500"].width,
            probe.direct_resolution_branches["500"].height,
        )
        == 500
    )


def test_probe_rejects_histogram_as_a_v2_primary_feature(tmp_path: Path, pilot_config) -> None:
    path = tmp_path / "histogram-input.png"
    _pattern(600, 500).save(path, format="PNG")

    with pytest.raises(ValueError, match="vector_representation='seamlessness'"):
        build_chromatic_v2_probe(
            _record(path, "repro-histogram"),
            pilot_config.measurements.chromatic,
            pilot_config.preprocessing,
            tmp_path,
            ChromaticV2Protocol(bootstrap_draws=100),
        )


def test_full_ecdf_ks_detects_shape_difference_hidden_by_scalar_s(
    pilot_config,
) -> None:
    # Both distributions have mean=2 and population std=1, hence the same
    # coefficient of variation and seamlessness S.  Their complete empirical
    # distributions are nevertheless different.
    first = np.tile(np.asarray([1.0, 1.0, 3.0, 3.0]), 100)
    root_two = np.sqrt(2.0)
    second = np.tile(np.asarray([2.0 - root_two, 2.0, 2.0, 2.0 + root_two]), 100)
    config = _v2_chromatic(pilot_config)

    first_summary = chromatic_summary(first, config)
    second_summary = chromatic_summary(second, config)
    assert first_summary["scalars"]["seamlessness"] == pytest.approx(
        second_summary["scalars"]["seamlessness"], abs=1e-15
    )
    assert two_sample_ecdf_ks_distance(first / first.mean(), second / second.mean()) > 0.05


def test_lee_domain_gate_does_not_infer_missing_visual_reviews(tmp_path: Path) -> None:
    path = tmp_path / "painting.png"
    _pattern(640, 512).save(path)
    record = _record(path).model_copy(update={"border_status": "none"})

    evidence = assess_lee_input_eligibility([_canonical()], [record])

    assert evidence.painting_metadata_eligible_count == 1
    assert evidence.border_clear_count == 1
    assert evidence.paper_domain_review_complete is False
    assert evidence.missing_review_fields == [
        "partial_image_status",
        "serious_damage_status",
    ]
    assert evidence.supported is False
    assert "manifest schema has no explicit review" in evidence.reason


def test_resolution_collapse_reports_adapted_branch_and_domain_ineligibility(
    tmp_path: Path, pilot_config
) -> None:
    path = tmp_path / "painting.png"
    _pattern(900, 700).save(path)
    record = _record(path).model_copy(update={"border_status": "none"})
    protocol = ChromaticV2Protocol(bootstrap_draws=100)
    probe = build_chromatic_v2_probe(
        record,
        _v2_chromatic(pilot_config),
        pilot_config.preprocessing,
        tmp_path,
        protocol,
    )
    eligibility = assess_lee_input_eligibility([_canonical()], [record])

    evidence = aggregate_lee_resolution_collapse([probe], [record], eligibility, protocol)

    assert evidence.evaluated_resolution_long_sides == [500, 400, 256]
    assert evidence.paper_figure_resolution_long_sides == [
        500,
        1000,
        1500,
        2000,
        2500,
        3000,
    ]
    assert evidence.exact_paper_resolution_set is False
    assert evidence.primary_native_supporting_paper_resolution_set_count == 0
    assert evidence.paper_domain_eligible_image_count == 0
    assert evidence.raw_pair_count == 2
    assert evidence.raw_defined_ks_count == 2
    assert evidence.raw_ks_minimum is not None
    assert evidence.raw_ks_median is not None
    assert evidence.raw_ks_maximum is not None
    assert evidence.raw_diagnostic_pass_fraction in {0.0, 1.0}
    assert evidence.supported is False
    assert "do not reproduce Lee et al. Figure 1" in evidence.reason

    mismatched_record = record.model_copy(update={"reproduction_id": "different-id"})
    with pytest.raises(ValueError, match="exactly the primary corpus"):
        aggregate_lee_resolution_collapse([probe], [mismatched_record], eligibility, protocol)


def test_alternate_images_collapse_to_independent_canonical_works() -> None:
    groups = group_reproduction_alternates(
        distances=[1.0, 9.0, 3.0, 5.0, 2.0],
        canonical_work_ids=["work-a", "work-a", "work-a", "work-a", "work-b"],
        artist_ids=["artist-a", "artist-a", "artist-a", "artist-a", "artist-b"],
        reproduction_ids=["a1", "a2", "a3", "a4", "b1"],
    )

    assert len(groups) == 2
    assert groups[0].canonical_work_id == "work-a"
    assert groups[0].alternate_image_count == 4
    assert groups[0].independent_work_distance == pytest.approx(4.0)
    assert groups[1].alternate_image_count == 1
    assert groups[1].independent_work_distance == pytest.approx(2.0)


def test_nested_source_folds_fit_standardization_without_held_source() -> None:
    matrix = np.asarray(
        [
            [0.0, 0.0],
            [10.0, 10.0],
            [100.0, 0.0],
            [110.0, 10.0],
            [200.0, 0.0],
            [210.0, 10.0],
        ]
    )
    artists = ["a", "b", "a", "b", "a", "b"]
    sources = ["s1", "s1", "s2", "s2", "s3", "s3"]
    works = [f"work-{index}" for index in range(6)]

    result = nested_leave_source_out_artist_accuracy(matrix, artists, sources, works)

    assert len(result.folds) == 3
    assert result.balanced_accuracy == pytest.approx(1.0)
    for fold in result.folds:
        assert fold.held_out_source_id not in fold.fit_source_ids
        assert fold.held_out_source_id not in fold.standardizer.fit_source_ids
        fit_indices = [
            index for index, source in enumerate(sources) if source != fold.held_out_source_id
        ]
        assert fold.standardizer.mean == pytest.approx(matrix[fit_indices].mean(axis=0))
        assert set(fold.fit_work_ids).isdisjoint(fold.test_work_ids)


def test_bootstrap_requires_the_upper_bound_to_clear_the_frozen_threshold() -> None:
    supported = stratified_bootstrap_ratio(
        numerator_values=[1.0, 1.0, 1.0, 1.0],
        numerator_artist_ids=["a", "a", "b", "b"],
        denominator_values=[3.0, 3.0, 3.0, 3.0],
        denominator_artist_ids=["a", "a", "b", "b"],
        metric="codec",
        numerator_unit="primary_work",
        draws=200,
        seed=7,
    )
    unsupported = stratified_bootstrap_ratio(
        numerator_values=[2.0, 2.0, 2.0, 2.0],
        numerator_artist_ids=["a", "a", "b", "b"],
        denominator_values=[3.0, 3.0, 3.0, 3.0],
        denominator_artist_ids=["a", "a", "b", "b"],
        metric="codec",
        numerator_unit="primary_work",
        draws=200,
        seed=7,
    )

    assert supported.point_ratio == pytest.approx(1.0 / 3.0)
    assert supported.confidence_upper == pytest.approx(1.0 / 3.0)
    assert supported.supported is True
    assert unsupported.point_ratio == pytest.approx(2.0 / 3.0)
    assert unsupported.confidence_upper == pytest.approx(2.0 / 3.0)
    assert unsupported.supported is False

    repeated = stratified_bootstrap_ratio(
        numerator_values=[1.0, 1.0, 1.0, 1.0],
        numerator_artist_ids=["a", "a", "b", "b"],
        denominator_values=[3.0, 3.0, 3.0, 3.0],
        denominator_artist_ids=["a", "a", "b", "b"],
        metric="codec",
        numerator_unit="primary_work",
        draws=200,
        seed=7,
    )
    assert repeated == supported


def test_scope_narrows_to_exact_lossless_files_without_hiding_failed_probes() -> None:
    def ratio(metric: str, supported: bool) -> BootstrapRatioEvidence:
        return BootstrapRatioEvidence(
            metric=metric,
            numerator_unit="canonical_work",
            numerator_count=7,
            denominator_count=32,
            numerator_median=0.4,
            denominator_median=1.0,
            point_ratio=0.4,
            confidence_level=0.95,
            confidence_lower=0.2,
            confidence_upper=0.4 if supported else 1.2,
            bootstrap_draws=2_000,
            threshold=0.5,
            supported=supported,
        )

    q85 = ratio("q85_diagnostic", False)
    reproduction = ratio("reproduction_generalization", False)
    decision = decide_chromatic_v2_scope(
        source_behavior_recovered=True,
        artist_signal_valid=True,
        source_confounding_controlled=True,
        lossless_processing_deterministic=True,
        codec_q85_diagnostic=q85,
        codec_q95_sensitivity=ratio("q95_sensitivity", True),
        reproduction_generalization=reproduction,
        direct_resolution_stability={
            "400": ratio("direct_400", True),
            "256": ratio("direct_256", True),
        },
    )

    assert q85.supported is False
    assert reproduction.supported is False
    assert decision.status == "fail"
    assert not any(
        "exact versioned primary digital reproductions only" in item
        for item in decision.supported_scope
    )
    assert any("native-to-400" in item for item in decision.supported_scope)
    assert any("Q85 4:2:0" in item for item in decision.unsupported_conditions)
    assert any("reproduction generalization" in item for item in decision.unsupported_conditions)

    failed_resolution = decide_chromatic_v2_scope(
        source_behavior_recovered=True,
        artist_signal_valid=True,
        source_confounding_controlled=True,
        lossless_processing_deterministic=True,
        codec_q85_diagnostic=q85,
        codec_q95_sensitivity=ratio("q95_sensitivity", True),
        reproduction_generalization=reproduction,
        direct_resolution_stability={"400": ratio("direct_400", False)},
    )
    assert failed_resolution.status == "fail"
