from pathlib import Path

import numpy as np
import pytest

from latent_art_bench.painter_distribution_exploration_v1 import analysis, report
from latent_art_bench.painter_prompt_study_v1.prompts import METHOD_IDS, TEMPLATE_IDS


def fixture_painter():
    rng = np.random.default_rng(981)
    items = [
        dict(
            image_id=f"work:{i}",
            domain="original",
            alias="original",
            method_id="original",
            template_id="",
            block=-1,
            retried=False,
            source_run_id="reference",
        )
        for i in range(32)
    ]
    for alias in report.ALIASES:
        for method in METHOD_IDS:
            items.extend(
                dict(
                    image_id=f"{alias}/{method}/{t}/{b}",
                    domain="generated",
                    alias=alias,
                    method_id=method,
                    template_id=t,
                    block=b,
                    retried=(t == TEMPLATE_IDS[0] and b == 0 and method == "by_name"),
                    source_run_id="source",
                )
                for t in TEMPLATE_IDS
                for b in range(4)
            )
    return {
        report.PAINTER_IDS[0]: dict(
            values=rng.normal(size=(416, 31)), items=items, reference_count=32
        )
    }


def test_compute_preserves_inventory_and_scene_groups():
    data = analysis.compute(fixture_painter())
    assert len(data["projections"]) == 5
    assert len(data["points"]) == 416 * 5
    assert len(data["separability"]) == 60
    assert len(data["predictions"]) == 96 * 6 * 2
    for method in METHOD_IDS:
        for alias in report.ALIASES:
            rows = [
                r
                for r in data["predictions"]
                if r["split"] == "scene" and r["method_id"] == method and r["alias"] == alias
            ]
            assert len({r["image_id"] for r in rows}) == 96
            for template in TEMPLATE_IDS:
                generated = [r for r in rows if r["template_id"] == template]
                assert len(generated) == 4
                assert len({r["fold"] for r in generated}) == 1
    for fit in data["projections"]:
        assert len(fit["feature_names"]) == len(fit["center"])


def test_shared_scatter_bounds_retain_outliers_from_other_methods():
    fit = dict(explained_variance_ratio=[0.5, 0.3])
    points = [
        dict(
            domain="original", alias="original", method_id="original", pc1=0, pc2=0, retried=False
        ),
        dict(
            domain="generated",
            alias=report.ALIASES[0],
            method_id="by_name",
            pc1=1,
            pc2=2,
            retried=False,
        ),
        dict(
            domain="generated",
            alias=report.ALIASES[1],
            method_id="style_aspects",
            pc1=100,
            pc2=-100,
            retried=True,
        ),
    ]
    fig, axes = report.plt.subplots(1, 2)
    for ax, method in zip(axes, ("by_name", "style_aspects")):
        report.scatter(ax, fit, points, method, report.ALIASES)
        assert ax.get_xlim()[1] > 100
        assert ax.get_ylim()[0] < -100
    assert axes[0].get_xlim() == axes[1].get_xlim()
    assert axes[0].get_ylim() == axes[1].get_ylim()
    report.plt.close(fig)


def test_build_never_overwrites_existing_evidence(tmp_path):
    (tmp_path / "existing").mkdir()
    marker = tmp_path / "existing" / "REPORT.md"
    marker.write_text("preserve")
    with pytest.raises(FileExistsError, match="immutable"):
        report.build(tmp_path, Path("existing"))
    assert marker.read_text() == "preserve"


def test_save_is_byte_deterministic(tmp_path):
    (tmp_path / "plots").mkdir()
    with report.plt.rc_context({**report.STYLE, "svg.hashsalt": report.NAMESPACE}):
        for name in ("first", "second"):
            fig, ax = report.plt.subplots()
            ax.scatter([0, 1], [2, 3])
            report.save(fig, tmp_path, name)
    for suffix in ("png", "svg"):
        assert (tmp_path / "plots" / f"first.{suffix}").read_bytes() == (
            tmp_path / "plots" / f"second.{suffix}"
        ).read_bytes()
