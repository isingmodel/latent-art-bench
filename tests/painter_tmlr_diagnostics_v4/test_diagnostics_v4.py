"""Constructed-data checks for the fourth TMLR revision diagnostics."""

import numpy as np
import pytest

from latent_art_bench import painter_tmlr_diagnostics_v4 as diag


def constructed(class_means, scene_classes):
    """Generated arms equal to each scene's class means, identical in both repeats."""
    named = np.stack([class_means[c] for c in scene_classes])
    zeros = np.zeros((len(scene_classes), 2, 2, named.shape[-1]))
    repeated = np.broadcast_to(named[:, None], (len(scene_classes), 2, *named.shape[1:]))
    return np.concatenate([zeros, repeated], axis=2)


def refs_from(class_means, per_class=3):
    refs, labels = [], []
    classes = diag.review.CLASSES
    for a in range(4):
        rows, labs = [], []
        for c in range(len(classes)):
            rows += [class_means[c][a]] * per_class
            labs += [classes[c]] * per_class
        refs.append(np.array(rows))
        labels.append(np.array(labs))
    return refs, labels


def test_generator_matching_class_means_has_zero_class_error():
    rng = np.random.default_rng(3)
    class_means = rng.normal(size=(len(diag.review.CLASSES), 4, 3))
    scene_classes = [0, 1, 3, 0]
    refs, labels = refs_from(class_means)
    x = constructed(class_means, scene_classes)
    out = diag.content_agreement(x, refs, labels, list(range(4)), scene_classes, draws=50)
    assert out["class_d"] == pytest.approx(0, abs=1e-12)
    assert out["class_beta"] == pytest.approx(1)
    assert out["class_d_below_one"] == pytest.approx(1)


def test_identical_classes_make_class_and_pooled_targets_equal():
    rng = np.random.default_rng(4)
    base = rng.normal(size=(4, 3))
    class_means = np.broadcast_to(base, (len(diag.review.CLASSES), 4, 3)).copy()
    refs, labels = refs_from(class_means)
    x = rng.normal(size=(4, 2, 6, 3))
    out = diag.content_agreement(x, refs, labels, list(range(4)), [0, 1, 3, 0])
    assert out["class_d"] == pytest.approx(out["pooled_d"])
    assert out["class_vs_pooled"] == pytest.approx(0, abs=1e-12)
    assert out["class_h_over_h"] == pytest.approx(1)
