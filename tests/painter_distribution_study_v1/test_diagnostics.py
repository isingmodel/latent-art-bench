"""Exercise complete diagnostic data flow with synthetic work and scene identities."""

import numpy as np

from latent_art_bench.painter_distribution_study_v1 import diagnostics as d
from latent_art_bench.painter_distribution_study_v1.statistics import rng_for


def population():
    painters, frame = {}, {}
    rng = rng_for("synthetic-stage-a-integration")
    for painter in d.PAINTER_IDS:
        items, arrays = [], [rng.normal(size=(16, 31))]
        for i in range(16):
            image_id = f"{painter}-work-{i}"
            items.append(
                dict(
                    image_id=image_id,
                    domain="original",
                    alias="original",
                    method_id="original",
                    condition="original",
                    template_id="",
                    content_class=d.CLASSES[i % 4],
                )
            )
            frame[image_id] = dict(capture_workflow="unresolved", collections=["test-collection"])
        for alias in d.ALIASES:
            for method in d.METHOD_IDS:
                for condition in ("named", "artist_free"):
                    arrays.append(rng.normal(1, 0.5, size=(64, 31)))
                    for i in range(64):
                        prefix = painter if condition == "named" else "shared"
                        items.append(
                            dict(
                                image_id=f"{prefix}-{alias}-{method}-{condition}-{i}",
                                domain="generated",
                                alias=alias,
                                method_id=method,
                                condition=condition,
                                template_id=d.TEMPLATE_IDS[i % 16],
                                content_class=d.CLASSES[(i % 16) // 4],
                            )
                        )
        painters[painter] = dict(values=np.concatenate(arrays), items=items, reference_count=16)
    return painters, frame


def test_all_cells_controls_transfer_and_report_are_retained():
    painters, frame = population()
    data = d.compute(
        painters,
        frame,
        dict(
            seed="fixture",
            split_draws=2,
            classifier_baseline_draws=1,
            maximum_matched_group_size=8,
            transfer_folds=4,
        ),
    )
    assert len(data["cells"]) == 384
    assert len(data["reference_splits"]) == 32
    assert len(data["matched_comparisons"]) == 384
    assert len(data["classifiers"]) == 384
    assert len(data["predictions"]) == 3840
    assert len(data["transfer"]) == 64
    assert {r["condition"] for r in data["cells"]} == {"named", "artist_free"}
    assert all(0 <= r["balanced_accuracy"] <= 1 for r in data["transfer"])
    text = d.report_text(data)
    assert "|\n\n|" not in text
    assert "unresolved" in text
    assert "artist_free" in text
    for row in data["split_members"]:
        assert not set(row["left_ids"]) & set(row["right_ids"])
