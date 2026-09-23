"""Constructed-array tests only: this module never reads retained study data."""

import numpy as np
import pytest

from latent_art_bench.painter_prototype_transfer_v1 import evaluate_model

RULES = ("reference_baseline", "common_translation", "generated_prototype")


def _unit(values):
    values = np.asarray(values, dtype=float)
    return values / np.linalg.norm(values, axis=-1, keepdims=True)


def _synthetic_inputs():
    rng = np.random.default_rng(742)
    named = _unit(rng.normal(size=(4, 2, 4, 5)))
    prototypes = _unit(rng.normal(size=(4, 5))) * np.array([0.4, 0.6, 0.8, 0.9])[:, None]
    return named, prototypes


def _oracle(named, prototypes):
    """Direct loops implement the three planned scores, independently of the API."""
    scores = {rule: np.empty((*named.shape[:3], 4)) for rule in RULES}
    norms = {rule: np.empty(named.shape[:3]) for rule in RULES}
    reference_unit = prototypes / np.linalg.norm(prototypes, axis=1)[:, None]
    translations = []
    generated_norms = []
    for held_out in range(len(named)):
        train = np.concatenate([named[:held_out], named[held_out + 1 :]], axis=0)
        translation = prototypes.mean(axis=0) - train.mean(axis=(0, 1, 2))
        generated = train.mean(axis=(0, 1))
        generated_norms.append(np.linalg.norm(generated, axis=1))
        generated_unit = generated / np.linalg.norm(generated, axis=1)[:, None]
        translations.append(translation)
        for repeat in range(2):
            for painter in range(4):
                query = named[held_out, repeat, painter]
                for rule, vector, targets in (
                    ("reference_baseline", query, reference_unit),
                    ("common_translation", query + translation, reference_unit),
                    ("generated_prototype", query, generated_unit),
                ):
                    scores[rule][held_out, repeat, painter] = targets @ vector
                    norms[rule][held_out, repeat, painter] = np.linalg.norm(vector)
    return scores, norms, np.asarray(translations), np.asarray(generated_norms)


def _assert_rule_accounting(actual, scores, norms):
    scenes = scores.shape[0]
    truth = np.broadcast_to(np.arange(4), (scenes, 2, 4))
    predicted = np.argmax(scores, axis=-1)
    correct = predicted == truth
    confusion = np.zeros((4, 4), dtype=int)
    np.add.at(confusion, (truth.ravel(), predicted.ravel()), 1)
    margins = np.empty((scenes, 2, 4))
    for painter in range(4):
        incorrect = np.delete(scores[:, :, painter, :], painter, axis=-1)
        margins[:, :, painter] = scores[:, :, painter, painter] - incorrect.max(axis=-1)
    ties = np.sum(scores == scores.max(axis=-1, keepdims=True), axis=-1) > 1
    np.testing.assert_array_equal(actual["predictions"], predicted)
    np.testing.assert_array_equal(actual["confusion_counts"], confusion)
    np.testing.assert_allclose(actual["per_painter_recall"], correct.mean(axis=(0, 1)))
    np.testing.assert_allclose(actual["scene_accuracy"], correct.mean(axis=(1, 2)))
    np.testing.assert_allclose(actual["margins"], margins, atol=1e-14)
    np.testing.assert_allclose(actual["query_norms"], norms, atol=1e-14)
    assert actual["macro_accuracy"] == pytest.approx(correct.mean())
    assert actual["micro_accuracy"] == pytest.approx(correct.mean())
    assert actual["tie_counts"]["total"] == int(ties.sum())
    np.testing.assert_array_equal(actual["tie_counts"]["per_scene"], ties.sum(axis=(1, 2)))
    zero_queries = norms == 0
    np.testing.assert_array_equal(actual["zero_queries"], zero_queries)
    assert actual["zero_query_counts"]["total"] == int(zero_queries.sum())
    np.testing.assert_array_equal(
        actual["zero_query_counts"]["per_scene"], zero_queries.sum(axis=(1, 2))
    )
    assert confusion.sum() == scenes * 8
    np.testing.assert_array_equal(confusion.sum(axis=1), np.full(4, scenes * 2))


def _assert_paired_accounting(result, candidate):
    baseline = np.asarray(result["rules"]["reference_baseline"]["predictions"])
    predicted = np.asarray(result["rules"][candidate]["predictions"])
    truth = np.broadcast_to(np.arange(4), baseline.shape)
    before, after = baseline == truth, predicted == truth
    pair_name = "translation" if candidate == "common_translation" else candidate
    paired = result[f"paired_{pair_name}_vs_baseline"]
    difference = after.astype(float) - before.astype(float)
    assert paired["accuracy_difference"] == pytest.approx(difference.mean())
    assert paired["corrected_count"] == int(np.sum(~before & after))
    assert paired["newly_incorrect_count"] == int(np.sum(before & ~after))
    np.testing.assert_allclose(paired["scene_accuracy_difference"], difference.mean(axis=(1, 2)))


def test_all_fixed_rules_match_direct_scores_and_complete_accounting():
    named, prototypes = _synthetic_inputs()
    expected, norms, translations, generated_norms = _oracle(named, prototypes)
    result = evaluate_model(named, prototypes)
    assert set(result["rules"]) == set(RULES)
    assert len(result["folds"]) == len(named)
    for rule in RULES:
        _assert_rule_accounting(result["rules"][rule], expected[rule], norms[rule])
    for scene, fold in enumerate(result["folds"]):
        train_scenes = [index for index in range(len(named)) if index != scene]
        assert fold["held_out_scene"] == scene
        assert fold["train_scenes"] == train_scenes
        assert fold["training_image_count"] == len(train_scenes) * 8
        np.testing.assert_allclose(fold["training_mean"], named[train_scenes].mean(axis=(0, 1, 2)))
        np.testing.assert_allclose(fold["translation"], translations[scene], atol=1e-14)
        assert fold["translation_norm"] == pytest.approx(np.linalg.norm(translations[scene]))
        np.testing.assert_allclose(
            fold["reference_prototype_norms"], np.linalg.norm(prototypes, axis=1)
        )
        np.testing.assert_allclose(fold["generated_prototype_norms"], generated_norms[scene])
    _assert_paired_accounting(result, "common_translation")
    _assert_paired_accounting(result, "generated_prototype")


def test_both_held_out_repeats_are_excluded_from_fitted_quantities():
    named, prototypes = _synthetic_inputs()
    before = evaluate_model(named, prototypes)
    changed = named.copy()
    changed[0, 0] = _unit(np.arange(1, 21).reshape(4, 5))
    changed[0, 1] = _unit(-np.arange(21, 41).reshape(4, 5))
    after = evaluate_model(changed, prototypes)
    assert before["folds"][0] == after["folds"][0]
    expected, norms, _, _ = _oracle(changed, prototypes)
    for rule in RULES:
        _assert_rule_accounting(after["rules"][rule], expected[rule], norms[rule])


def test_translation_ignores_training_painter_label_permutations():
    named, prototypes = _synthetic_inputs()
    permuted = named.copy()
    for scene in range(1, len(named)):
        permuted[scene, 0] = named[scene, 0, [3, 1, 0, 2]]
        permuted[scene, 1] = named[scene, 1, [2, 0, 3, 1]]
    before = evaluate_model(named, prototypes)
    after = evaluate_model(permuted, prototypes)
    for key in ("translation", "training_mean", "translation_norm"):
        np.testing.assert_allclose(before["folds"][0][key], after["folds"][0][key], atol=1e-14)
    for key in ("predictions", "margins", "query_norms"):
        np.testing.assert_allclose(
            before["rules"]["common_translation"][key][0],
            after["rules"]["common_translation"][key][0],
            atol=1e-14,
        )
    # The supervised context is allowed to depend on these training labels.
    assert not np.allclose(
        before["folds"][0]["generated_prototype_norms"],
        after["folds"][0]["generated_prototype_norms"],
    )


def test_translation_is_identity_when_training_and_reference_means_match():
    prototypes = np.array([[0.6, 0, 0.8], [0, 0.6, 0.8], [-0.6, 0, 0.8], [0, -0.6, 0.8]])
    named = np.tile(prototypes, (3, 2, 1, 1))
    result = evaluate_model(named, prototypes)
    for fold in result["folds"]:
        np.testing.assert_allclose(fold["translation"], 0, atol=1e-14)
    baseline = result["rules"]["reference_baseline"]
    translated = result["rules"]["common_translation"]
    for key in ("predictions", "margins", "query_norms"):
        np.testing.assert_allclose(baseline[key], translated[key], atol=1e-14)
    assert translated["macro_accuracy"] == 1
    assert result["paired_translation_vs_baseline"]["accuracy_difference"] == 0


def test_fixed_translation_recovers_a_known_additive_offset():
    queries = np.array([[4 / 5, -3 / 5], [12 / 13, -5 / 13], [12 / 13, 5 / 13], [4 / 5, 3 / 5]])
    offset = np.array([0.7, 0.0])
    prototypes = queries - offset
    named = np.tile(queries, (3, 2, 1, 1))
    result = evaluate_model(named, prototypes)
    assert np.all(np.linalg.norm(prototypes, axis=1) < 1)
    for fold in result["folds"]:
        np.testing.assert_allclose(fold["translation"], -offset, atol=1e-14)
    assert result["rules"]["reference_baseline"]["macro_accuracy"] == pytest.approx(0.5)
    assert result["rules"]["common_translation"]["macro_accuracy"] == 1
    assert result["rules"]["generated_prototype"]["macro_accuracy"] == 1
    paired = result["paired_translation_vs_baseline"]
    assert paired["accuracy_difference"] == 0.5
    assert paired["corrected_count"] == 12
    assert paired["newly_incorrect_count"] == 0


def test_harmful_translation_is_retained_without_clipping_or_fallback():
    prototypes = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])
    named = np.tile(np.array([0.8, 0.6]), (3, 2, 4, 1))
    named[0] = prototypes
    result = evaluate_model(named, prototypes)
    np.testing.assert_allclose(result["folds"][0]["translation"], [-0.8, -0.6])
    assert result["rules"]["reference_baseline"]["macro_accuracy"] == pytest.approx(0.5)
    assert result["rules"]["common_translation"]["macro_accuracy"] == pytest.approx(1 / 3)
    paired = result["paired_translation_vs_baseline"]
    assert paired["accuracy_difference"] == pytest.approx(-1 / 6)
    assert paired["corrected_count"] == 0
    assert paired["newly_incorrect_count"] == 4
    np.testing.assert_allclose(paired["scene_accuracy_difference"], [-0.5, 0.0, 0.0])


def test_exact_ties_use_first_candidate_and_count_queries_once():
    prototypes = np.tile([1.0, 0.0], (4, 1))
    named = np.tile([0.6, 0.8], (3, 2, 4, 1))
    result = evaluate_model(named, prototypes)
    for rule in RULES:
        actual = result["rules"][rule]
        np.testing.assert_array_equal(actual["predictions"], np.zeros((3, 2, 4), dtype=int))
        np.testing.assert_array_equal(actual["confusion_counts"], [[6, 0, 0, 0]] * 4)
        np.testing.assert_array_equal(actual["per_painter_recall"], [1, 0, 0, 0])
        np.testing.assert_array_equal(actual["margins"], np.zeros((3, 2, 4)))
        assert actual["macro_accuracy"] == actual["micro_accuracy"] == 0.25
        assert actual["tie_counts"] == {"total": 24, "per_scene": [8, 8, 8]}


def test_near_ties_are_not_counted_as_exact_ties():
    angle = 1e-5
    prototypes = np.array([[1, 0], [np.cos(angle), np.sin(angle)], [-1, 0], [0, -1]])
    named = np.tile([1.0, 0.0], (2, 2, 4, 1))
    result = evaluate_model(named, prototypes)
    assert result["rules"]["reference_baseline"]["tie_counts"] == {"total": 0, "per_scene": [0, 0]}


@pytest.mark.parametrize(
    "kind",
    ["one_scene", "one_repeat", "three_painters", "prototype_shape", "dimension_mismatch"],
)
def test_rejects_invalid_shapes(kind):
    named, prototypes = _synthetic_inputs()
    if kind == "one_scene":
        named = named[:1]
    elif kind == "one_repeat":
        named = named[:, :1]
    elif kind == "three_painters":
        named = named[:, :, :3]
    elif kind == "prototype_shape":
        prototypes = prototypes[:3]
    else:
        prototypes = prototypes[:, :-1]
    with pytest.raises(ValueError):
        evaluate_model(named, prototypes)


@pytest.mark.parametrize("bad_value", [np.nan, np.inf, -np.inf])
@pytest.mark.parametrize("input_name", ["named", "prototypes"])
def test_rejects_nonfinite_inputs(bad_value, input_name):
    named, prototypes = _synthetic_inputs()
    if input_name == "named":
        named[0, 0, 0, 0] = bad_value
    else:
        prototypes[0, 0] = bad_value
    with pytest.raises(ValueError):
        evaluate_model(named, prototypes)


@pytest.mark.parametrize("scale", [0.0, 0.5, 1.1])
def test_rejects_nonunit_generated_queries(scale):
    named, prototypes = _synthetic_inputs()
    named[0, 0, 0] *= scale
    with pytest.raises(ValueError):
        evaluate_model(named, prototypes)


def test_rejects_zero_reference_prototype():
    named, prototypes = _synthetic_inputs()
    prototypes[0] = 0
    with pytest.raises(ValueError):
        evaluate_model(named, prototypes)


def test_rejects_zero_generated_prototype():
    prototypes = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])
    named = np.tile(prototypes, (2, 2, 1, 1))
    named[1, 1] *= -1
    with pytest.raises(ValueError):
        evaluate_model(named, prototypes)


def test_retains_zero_translated_queries_as_counted_linear_score_ties():
    prototypes = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])
    named = np.tile([1.0, 0.0], (2, 2, 4, 1))
    result = evaluate_model(named, prototypes)
    translated = result["rules"]["common_translation"]
    np.testing.assert_array_equal(translated["scores"], np.zeros((2, 2, 4, 4)))
    np.testing.assert_array_equal(translated["predictions"], np.zeros((2, 2, 4), dtype=int))
    np.testing.assert_array_equal(translated["margins"], np.zeros((2, 2, 4)))
    np.testing.assert_array_equal(translated["query_norms"], np.zeros((2, 2, 4)))
    np.testing.assert_array_equal(translated["zero_queries"], np.ones((2, 2, 4), dtype=bool))
    np.testing.assert_array_equal(translated["confusion_counts"], [[4, 0, 0, 0]] * 4)
    assert translated["tie_counts"] == {"total": 16, "per_scene": [8, 8]}
    assert translated["zero_query_counts"] == {"total": 16, "per_scene": [8, 8]}
    assert translated["macro_accuracy"] == translated["micro_accuracy"] == 0.25
    for rule in ("reference_baseline", "generated_prototype"):
        assert result["rules"][rule]["zero_query_counts"] == {"total": 0, "per_scene": [0, 0]}
        np.testing.assert_array_equal(
            result["rules"][rule]["zero_queries"], np.zeros((2, 2, 4), dtype=bool)
        )
