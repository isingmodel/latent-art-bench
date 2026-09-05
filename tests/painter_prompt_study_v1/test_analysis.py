"""Analytic point-distribution oracles and complete-grid checks for prompt effects."""

import copy

import numpy as np
import pytest

from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2.features import FAMILIES
from latent_art_bench.painter_prompt_study_v1 import analysis, generation
from latent_art_bench.painter_prompt_study_v1.prompts import CONDITIONS, METHOD_IDS, TEMPLATE_IDS


def numeric_grid(named, free=None):
    """Every template in a block is the same 31-dimensional point; no artwork is read."""
    repetitions = len(named["by_name"])
    free = free or {method: [5.0] * repetitions for method in METHOD_IDS}
    rows = []
    for alias in generation.ALIASES:
        for method in METHOD_IDS:
            for block in range(repetitions):
                for condition in CONDITIONS:
                    point = (
                        free[method][block] if condition == "artist_free" else named[method][block]
                    )
                    for template in TEMPLATE_IDS:
                        rows.append(
                            dict(
                                image_id=f"{alias}/{method}/{block}/{condition}/{template}",
                                alias=alias,
                                method_id=method,
                                block=block,
                                condition=condition,
                                template_id=template,
                                status="measured",
                                values=[point] * 31,
                                request_sequence=len(rows),
                            )
                        )
    real = {painter: np.zeros((index + 2, 31)) for index, painter in enumerate(PAINTER_IDS)}
    scaler = dict(center=[0.0] * 31, scale=[1.0] * 31)
    return real, rows, scaler


@pytest.fixture
def constant_grid():
    return numeric_grid(dict(by_name=[3.0], style_instruction=[2.0], style_aspects=[1.0]))


def dimension(family):
    section = FAMILIES[family]
    return section.stop - section.start


def test_complete_inventory_has_exact_finite_distances_and_randomization_pvalues(constant_grid):
    real, rows, scaler = constant_grid
    result = analysis.compute(real, rows, scaler, repetitions=1)
    assert {
        key: len(result[key])
        for key in (
            "distances",
            "absolute",
            "primary",
            "secondary",
            "coordinates",
            "scene_contributions",
            "time_diagnostics",
        )
    } == dict(
        distances=360,
        absolute=72,
        primary=48,
        secondary=72,
        coordinates=744,
        scene_contributions=48 * 16,
        time_diagnostics=48,
    )
    assert result["inference"]["family_size"] == result["inference"]["endpoint_count"] == 48
    assert result["inference"]["slot_pair_count"] == 16
    assert result["inference"]["alpha"] == 0.05
    assert result["inference"]["method"] == "paired_randomization"
    assert result["inference"]["confidence_intervals"] is False
    method_points = dict(by_name=3.0, style_instruction=2.0, style_aspects=1.0)
    for row in result["distances"]:
        point = 5.0 if row["condition"] == "artist_free" else method_points[row["method_id"]]
        assert row["distance"] == pytest.approx(2 * point * np.sqrt(dimension(row["family"])))
        assert row["generated_count"] == 16
        assert row["reference_count"] == len(real[row["painter_id"]])
    for row in result["absolute"]:
        expected = 2 * method_points[row["method_id"]] * np.sqrt(dimension(row["family"]))
        assert row["finite_distance"] == pytest.approx(expected)
        assert "paired_energy_estimate" not in row
    for row in result["primary"]:
        assert row["estimate"] == pytest.approx(-2 * np.sqrt(dimension(row["family"])))
        # Equal nonzero scene contributions have only two equally extreme sign assignments.
        assert row["raw_p"] == 2 / 65536
        assert row["holm_p"] == 48 * 2 / 65536 and row["reject_holm"]
        assert row["status"] == "conditional_randomization"
        assert row["method"] == "exact_paired_randomization"
        assert "lower" not in row and "upper" not in row
    for row in result["coordinates"]:
        assert row["median_difference"] == method_points[row["method_id"]]
        assert row["iqr_ratio"] is None
    for row in result["secondary"]:
        change = -4 if row["endpoint"] == "overall_transition" else -2
        assert row["estimate"] == pytest.approx(change * np.sqrt(dimension(row["family"])))


@pytest.mark.parametrize("repetitions", [2, 4])
def test_pooled_finite_oracle_keeps_all_blocks_and_matched_free_change(repetitions):
    named = dict(
        by_name=[4.0, 7.0, 9.0, 12.0],
        style_instruction=[2.0, 3.0, 6.0, 8.0],
        style_aspects=[1.0, 2.0, 2.0, 6.0],
    )
    free = dict(
        by_name=[8.0, 9.0, 10.0, 11.0],
        style_instruction=[7.0, 7.0, 7.0, 8.0],
        style_aspects=[7.0, 8.0, 8.0, 9.0],
    )
    named = {k: v[:repetitions] for k, v in named.items()}
    free = {k: v[:repetitions] for k, v in free.items()}
    real, rows, scaler = numeric_grid(named, free)
    result = analysis.compute(real, rows, scaler, repetitions=repetitions)

    def distance(points):
        values = np.array(points)
        return 2 * values.mean() - np.abs(values[:, None] - values[None, :]).mean()

    def oracle(row, points):
        return (distance(points[row["after"]]) - distance(points[row["before"]])) * np.sqrt(
            dimension(row["family"])
        )

    for row in result["primary"]:
        assert row["estimate"] == pytest.approx(oracle(row, named))
        assert row["method"] == "monte_carlo_paired_randomization"
        assert row["permutations"] == 99999 and row["pairs"] == 16 * repetitions
        assert row["raw_p"] == (row["exceedances"] + 1) / 100000
        selected = [
            r
            for r in result["scene_contributions"]
            if all(r[k] == row[k] for k in ("alias", "painter_id", "family", "before", "after"))
        ]
        assert {(r["block"], r["template_id"]) for r in selected} == {
            (b, t) for b in range(repetitions) for t in TEMPLATE_IDS
        }
        assert sum(r["contribution"] for r in selected) == pytest.approx(row["estimate"])
        assert [r["order_sequence"] for r in selected] == sorted(
            r["order_sequence"] for r in selected
        )
        diagnostic = next(
            r
            for r in result["time_diagnostics"]
            if all(r[k] == row[k] for k in ("alias", "painter_id", "family", "before", "after"))
        )
        assert diagnostic["first_half_mean"] == pytest.approx(
            np.mean([r["contribution"] for r in selected[: 8 * repetitions]])
        )
    for row in result["secondary"]:
        value = oracle(row, named)
        if row["endpoint"] == "control_adjusted_transition":
            value -= oracle(row, free)
        assert row["estimate"] == pytest.approx(value)


def test_identical_methods_have_zero_effect_and_p_one_without_invented_interval():
    real, rows, scaler = numeric_grid({method: [3.0] for method in METHOD_IDS})
    result = analysis.compute(real, rows, scaler, repetitions=1)
    assert all(
        r["estimate"] == 0
        and r["raw_p"] == r["holm_p"] == 1
        and not r["reject_holm"]
        and r["zero_contributions"]
        for r in result["primary"]
    )


def test_row_order_does_not_change_pairing_or_reuse_old_generation(monkeypatch, constant_grid):
    real, rows, scaler = constant_grid
    monkeypatch.setattr(
        analysis,
        "load_source",
        lambda *args: pytest.fail("compute must not load prior generations"),
    )
    expected = analysis.compute(real, rows, scaler, repetitions=1)
    shuffled = copy.deepcopy(rows)
    np.random.default_rng(91).shuffle(shuffled)
    assert analysis.compute(real, shuffled, scaler, repetitions=1) == expected


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "extra_old_output",
        "duplicate_image",
        "failed",
        "unknown_alias",
        "unknown_method",
        "unknown_condition",
        "duplicate_template",
        "unknown_block",
        "nonfinite_feature",
    ],
)
def test_incomplete_or_foreign_grid_cannot_reach_primary_inference(constant_grid, fault):
    real, rows, scaler = constant_grid
    if fault == "missing":
        rows.pop()
    elif fault == "extra_old_output":
        rows.append(dict(rows[0], image_id="old-generation", alias="sd-turbo"))
    elif fault == "duplicate_image":
        rows[0]["image_id"] = rows[1]["image_id"]
    elif fault == "failed":
        rows[0]["status"] = "failed"
    elif fault == "unknown_alias":
        rows[0]["alias"] = "old-or-unregistered-service"
    elif fault == "unknown_method":
        rows[0]["method_id"] = "retrospectively-tuned-method"
    elif fault == "unknown_condition":
        rows[0]["condition"] = "unregistered-painter"
    elif fault == "duplicate_template":
        rows[0]["template_id"] = rows[1]["template_id"]
    elif fault == "unknown_block":
        rows[0]["block"] = 100
    else:
        rows[0]["values"][0] = float("nan")
    with pytest.raises(ValueError):
        analysis.compute(real, rows, scaler, repetitions=1)


def test_changed_template_inventory_is_rejected_even_when_counts_still_match(constant_grid):
    real, rows, scaler = constant_grid
    for row in rows:
        row["template_id"] = "changed-" + row["template_id"]
    with pytest.raises(ValueError):
        analysis.compute(real, rows, scaler, repetitions=1)


def test_nondefault_scaler_is_applied_once_to_new_raw_values(constant_grid):
    real, rows, scaler = constant_grid
    scaler["center"] = [10.0] * 31
    scaler["scale"] = [2.0] * 31
    # Reference arrays are already transformed by source loading. New rows remain raw until compute.
    for row in rows:
        row["values"] = [10 + 2 * value for value in row["values"]]
    result = analysis.compute(real, rows, scaler, repetitions=1)
    for row in result["primary"]:
        assert row["estimate"] == pytest.approx(-2 * np.sqrt(dimension(row["family"])))
