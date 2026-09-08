"""Synthetic rendering preserves memberships and replays byte-for-byte."""

import csv

import numpy as np

from latent_art_bench.painter_feature_generation_v2.features import NAMES
from latent_art_bench.painter_responsiveness_v1.analysis import _summarize_scope
from latent_art_bench.painter_responsiveness_v1.report import render


def result_fixture():
    before = np.zeros((2, 3, 31))
    before[:, :, 0] = [[1, -1, 0], [-1, 1, 0]]
    after = before / 2
    briefs = []
    for i, name in enumerate(("a", "b")):
        briefs.append(dict(
            brief_id=name, content_class="water", repetitions=[0, 1, 2],
            before_image_ids=[f"free:{name}:{r}" for r in range(3)],
            after_image_ids=[f"named:{name}:{r}" for r in range(3)],
            before_mean=before[i].mean(axis=0).tolist(),
            after_mean=after[i].mean(axis=0).tolist(),
            mean_displacement=(after[i] - before[i]).mean(axis=0).tolist(),
            squared_mean_displacement=0, cross_repeat_displacement_products=[],
        ))
    groups = []
    for pipeline in ("primary512", "resolution256", "jpeg90_512"):
        groups.append(dict(
            painter_id="claude_monet", level="broad_content", label="water", pipeline=pipeline,
            n_reference=1, image_ids=["reference:a"],
            raw=dict(minimum=1., q25=1., median=1., q75=1., maximum=1.),
        ))
    diagnostic = dict(
        feature_names=list(NAMES), cells=[dict(
            cell_id="synthetic", route="flux_2_max", painter_id="claude_monet", briefs=briefs,
            scopes=[_summarize_scope(before, after, ["a", "b"], "all_briefs")],
        )],
        reference_chroma=dict(
            fine_content_feasibility=dict(status="unavailable", reason="Synthetic pending."),
            subject_label_inventory=[], groups=groups,
            works=[dict(image_id="reference:a", painter_id="claude_monet",
                        pipeline_span_primary_iqr_units=0.25)],
        ),
        service_quality=dict(interpretation="Successful outcomes only.", groups=[]),
    )
    return dict(diagnostics=diagnostic, simulation={},
                gates=dict(status="not_ready", missing=["human_assessment_feasible"],
                           checks=dict(human_assessment_feasible=False)))


def test_report_replays_all_bytes_and_retains_exact_memberships(tmp_path):
    result = result_fixture()
    first, second = tmp_path / "first", tmp_path / "second"
    paths = render(result, first)
    assert render(result, second) == paths
    assert set(paths) == {p.relative_to(first).as_posix() for p in first.rglob("*") if p.is_file()}
    assert all((first / p).read_bytes() == (second / p).read_bytes() for p in paths)
    with (first / "brief_memberships.csv").open() as source:
        memberships = list(csv.DictReader(source))
    assert len(memberships) == 12
    assert {r["image_id"] for r in memberships} == {
        f"{condition}:{brief}:{r}" for condition in ("free", "named")
        for brief in ("a", "b") for r in range(3)
    }
    with (first / "brief_coordinates.csv").open() as source:
        coordinates = list(csv.DictReader(source))
    assert len(coordinates) == 62
    assert {r["feature"] for r in coordinates} == set(NAMES)
    markdown = (first / "REPORT.md").read_text()
    assert "**Generation gate: `not_ready`" in markdown
    assert "`human_assessment_feasible`" in markdown
    assert "not a variance constrained to be nonnegative" in markdown
