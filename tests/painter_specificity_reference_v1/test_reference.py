"""An oracle for class balance, independent of unequal work counts."""

import numpy as np
import pytest

from latent_art_bench.painter_specificity_reference_v1.analysis import CLASSES, class_means


def test_equal_class_target_removes_only_mixture_weights():
    labels = np.repeat(CLASSES, [9, 3, 2, 1])
    values = np.repeat(
        np.array([[0.0, 4.0], [2.0, 4.0], [6.0, 4.0], [8.0, 4.0]]), [9, 3, 2, 1], axis=0
    )
    assert not np.allclose(values.mean(axis=0), [4, 4])
    np.testing.assert_allclose(class_means(values, labels).mean(axis=0), [4, 4])
    np.testing.assert_allclose(class_means(values + 3, labels).mean(axis=0), [7, 7])


def test_missing_class_does_not_silently_change_target():
    with pytest.raises(ValueError, match="all four"):
        class_means(np.ones((3, 2)), CLASSES[:3])
