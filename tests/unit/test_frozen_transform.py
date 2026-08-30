from typing import List

import numpy as np
import pytest

from latent_art_bench.evaluation.frozen_transform import (
    FitTransformViolation,
    RealOnlyStandardizer,
)
from latent_art_bench.schemas import FeatureRow


def feature(
    work_id: str,
    vector: List[float],
    origin: str = "real",
    split: str = "train",
) -> FeatureRow:
    return FeatureRow(
        feature_id=f"feature-{work_id}-{origin}-{split}",
        derived_view_id=f"view-{work_id}",
        reproduction_id=f"reproduction-{work_id}",
        canonical_work_id=work_id,
        origin=origin,
        split=split,
        feature_name="formal-test",
        feature_version="v1",
        feature_config_hash="config-hash",
        vector=vector,
        scalars={},
        status="ok",
    )


def test_standardizer_fits_real_training_works_then_freezes() -> None:
    transform = RealOnlyStandardizer()
    state = transform.fit([feature("work-1", [0.0, 2.0]), feature("work-2", [2.0, 2.0])])
    assert state.fit_canonical_work_ids == ["work-1", "work-2"]
    transformed = transform.transform([feature("generated-1", [1.0, 2.0], origin="generated")])
    assert transformed == pytest.approx(np.array([[0.0, 0.0]]))
    with pytest.raises(FitTransformViolation, match="already fitted"):
        transform.fit([feature("work-3", [3.0, 3.0])])


@pytest.mark.parametrize(
    "bad_row, message",
    [
        (feature("generated", [0.0], origin="generated"), "real works only"),
        (feature("held-out", [0.0], split="held_out"), "real-training works only"),
    ],
)
def test_standardizer_rejects_non_training_fit_data(bad_row: FeatureRow, message: str) -> None:
    with pytest.raises(FitTransformViolation, match=message):
        RealOnlyStandardizer().fit([bad_row])


def test_standardizer_rejects_multiple_reproductions_as_independent_works() -> None:
    first = feature("same-work", [0.0])
    second = first.model_copy(update={"feature_id": "second", "derived_view_id": "second-view"})
    with pytest.raises(FitTransformViolation, match="one row per canonical work"):
        RealOnlyStandardizer().fit([first, second])
