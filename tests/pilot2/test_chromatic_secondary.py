from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from latent_art_bench.io import hash_bytes
from latent_art_bench.pilot2.chromatic import (
    FEATURE_VERSION,
    extract_chromatic_secondary,
    formula_probe_evidence,
)


def test_formula_probes_are_functional_not_a_false_figure1_claim() -> None:
    evidence = formula_probe_evidence()
    assert evidence["status"] == "pass"
    assert all(evidence["checks"].values())
    assert "not a corpus-wide replication" in evidence["claim_boundary"]


def test_secondary_feature_uses_fixed_500_lossless_input(tmp_path: Path) -> None:
    image = Image.new("RGB", (900, 600))
    for x in range(900):
        for y in range(600):
            image.putpixel((x, y), (x % 256, y % 256, (x + y) % 256))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", compress_level=9)
    payload = buffer.getvalue()
    path = tmp_path / "input.png"
    path.write_bytes(payload)

    feature = extract_chromatic_secondary(
        path,
        "fixture",
        expected_sha256=hash_bytes(payload),
    )

    assert feature.feature_version == FEATURE_VERSION
    assert feature.role == "secondary_descriptive"
    assert (feature.width, feature.height) == (500, 333)
    assert len(feature.vector) == 1 + 30
    assert -1.0 <= feature.scalars["seamlessness"] <= 1.0


def test_secondary_feature_upsamples_an_eligible_sub500_input(tmp_path: Path) -> None:
    image = Image.new("RGB", (413, 411))
    for x in range(413):
        for y in range(411):
            image.putpixel((x, y), (x % 256, y % 256, (2 * x + y) % 256))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", compress_level=9)
    payload = buffer.getvalue()
    path = tmp_path / "sub500.png"
    path.write_bytes(payload)

    feature = extract_chromatic_secondary(
        path,
        "sub500-fixture",
        expected_sha256=hash_bytes(payload),
    )

    assert (feature.width, feature.height) == (500, 498)
    assert max(feature.width, feature.height) == 500


def test_uniform_png_uses_registered_degenerate_limit(tmp_path: Path) -> None:
    image = Image.new("RGB", (512, 512), (37, 37, 37))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", compress_level=9)
    payload = buffer.getvalue()
    path = tmp_path / "uniform.png"
    path.write_bytes(payload)

    feature = extract_chromatic_secondary(
        path,
        "uniform-generated-cell",
        expected_sha256=hash_bytes(payload),
    )

    assert feature.scalars["degenerate"] == 1.0
    assert feature.scalars["seamlessness"] == -1.0
    assert feature.vector[0] == -1.0
    assert feature.vector[1] == 1.0
    assert all(value == 0.0 for value in feature.vector[2:])
