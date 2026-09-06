import csv
import json

from latent_art_bench.io import hash_file
from latent_art_bench.painter_distribution_study_v1 import main_report as r
from latent_art_bench.painter_distribution_study_v1 import study as s


def fixture():
    data = {name: [] for name in r.TABLES}
    data["projections"] = {}
    data["generation_accounting"] = dict(
        status="stopped_for_diagnosis",
        terminal_slots=2,
        dispositions=dict(image_returned=2),
        budget=dict(accounted_usd=1.25, attempts=20, paid_attempts=14, unresolved=0, uncertain=0),
    )
    for painter in s.PAINTERS:
        points = [
            dict(
                image_id=f"{painter}:real:{i}",
                route="original",
                condition="original",
                content_class="water",
                pc1=float(i),
                pc2=float(-i),
            )
            for i in range(2)
        ]
        for route, condition in r.CELLS:
            label = dict(
                pipeline="primary512", painter_id=painter, route=route, condition=condition
            )
            data["cells"].append(
                dict(
                    label,
                    feature_set="all31",
                    weighting="reference_content",
                    status="available",
                    n_original=2,
                    n_generated=2,
                    energy_distance=0.123456789012345,
                    population_variance_ratio=0.5,
                    squared_iqr_sum_ratio=0.4,
                )
            )
            data["baselines"].append(
                dict(
                    label,
                    status="available",
                    real_real_energy=[0.1, 0.2],
                    original_generated_energy=[0.3, 0.4],
                )
            )
            points.extend(
                dict(
                    image_id=f"{painter}:{route}:{condition}:{i}",
                    route=route,
                    condition=condition,
                    content_class="water",
                    pc1=float(i + 0.5),
                    pc2=float(i + 0.25),
                )
                for i in range(2)
            )
        data["projections"][painter] = dict(
            status="available",
            bases={
                basis: dict(fit=dict(explained_variance_ratio=[0.4, 0.2]), points=points)
                for basis in ("balanced_joint", "original_only")
            },
        )
    data["endpoints"] = [
        dict(
            endpoint_index=0,
            painter_id=s.PAINTERS[0],
            route=s.ROUTES[0],
            before="artist_free",
            after="named",
            pairs=0,
            status="unavailable",
            raw_p=1.0,
            holm_p=1.0,
        )
    ]
    return data


def test_render_is_byte_reproducible_and_preserves_unavailable_and_precision(tmp_path):
    data = fixture()
    first, second = tmp_path / "first", tmp_path / "second"
    r.render(data, first)
    r.render(data, second)
    files = sorted(p.name for p in first.iterdir())
    assert len(files) == 22
    assert all(hash_file(first / name) == hash_file(second / name) for name in files)
    rows = list(csv.DictReader((first / "cells.csv").open()))
    assert float(rows[0]["energy_distance"]) == 0.123456789012345
    endpoints = list(csv.DictReader((first / "endpoints.csv").open()))
    assert endpoints[0]["status"] == "unavailable" and endpoints[0]["raw_p"] == "1.0"
    report = (first / "REPORT.md").read_text()
    assert "stopped_for_diagnosis" in report and "Terminal slots: 2/1,008" in report
    assert "not confidence intervals" in report
    coordinates = list(csv.DictReader((first / "projection_points.csv").open()))
    assert len(coordinates) == 2 * 2 * (2 + 2 * len(r.CELLS))


def test_scatter_keeps_all_points_and_common_painter_limits(tmp_path, monkeypatch):
    data = fixture()
    captured = []
    monkeypatch.setattr(r, "save", lambda fig, output, name: captured.append(fig))
    r.scatter_plot(data, tmp_path, "balanced_joint")
    fig = captured[0]
    for painter_index in range(2):
        axes = fig.axes[painter_index * 3 : (painter_index + 1) * 3]
        assert len({ax.get_xlim() for ax in axes}) == 1
        assert len({ax.get_ylim() for ax in axes}) == 1
        for ax, route in zip(axes, s.ROUTES):
            assert sum(len(c.get_offsets()) for c in ax.collections) == 2 + 2 * len(
                s.conditions(route)
            )
    r.plt.close(fig)


def test_nested_table_fields_remain_machine_readable(tmp_path):
    nested = [dict(image_id="a", fold=2)]
    path = tmp_path / "predictions.csv"
    r.write_table(path, [dict(predictions=nested, estimate=None)])
    row = next(csv.DictReader(path.open()))
    assert json.loads(row["predictions"]) == nested and row["estimate"] == ""
