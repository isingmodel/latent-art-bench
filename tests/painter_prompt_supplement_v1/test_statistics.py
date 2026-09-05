"""Independent finite-distribution and support oracles; no image or service operations."""

import copy
import itertools

import numpy as np
import pytest

from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import features
from latent_art_bench.painter_feature_generation_v2.statistics import finite_energy
from latent_art_bench.painter_prompt_study_v1 import randomization
from latent_art_bench.painter_prompt_study_v1.generation import ALIASES
from latent_art_bench.painter_prompt_study_v1.prompts import CONDITIONS, METHOD_IDS, TEMPLATE_IDS
from latent_art_bench.painter_prompt_supplement_v1 import statistics as stats


def grid(repetitions=1):
    rows = []
    for block in range(repetitions):
        for template in TEMPLATE_IDS:
            for condition in CONDITIONS:
                for alias in ALIASES:
                    for index, method in enumerate(METHOD_IDS):
                        request_id = f"{alias}/{method}/{condition}/{block}/{template}"
                        value = 5.0 if condition == "artist_free" else 3.0 - index
                        rows.append(
                            dict(
                                alias=alias,
                                method_id=method,
                                condition=condition,
                                block=block,
                                template_id=template,
                                request_id=request_id,
                                image_id=request_id,
                                request_sequence=len(rows),
                                status="measured",
                                values=[value] * 31,
                            )
                        )
    real = {p: np.zeros((i + 2, 31)) for i, p in enumerate(PAINTER_IDS)}
    scaler = dict(center=[0.0] * 31, scale=[1.0] * 31)
    return real, rows, scaler


def missing(row, status="not_generated"):
    row["status"] = status
    row.pop("values")


def selected(rows, *, method="by_name", condition=PAINTER_IDS[0], alias=ALIASES[0]):
    return [
        r
        for r in rows
        if (r["alias"], r["method_id"], r["condition"]) == (alias, method, condition)
    ]


def test_weighted_energy_hand_oracle_and_uniform_reduction():
    reference = np.zeros((3, 1))
    generated = np.array([[1.0], [3.0]])
    # 2 E|Y|=3 and E|Y-Y'|=.75, including both ordered off-diagonal terms.
    assert stats.weighted_energy(reference, generated, [0.75, 0.25]) == pytest.approx(2.25)
    assert stats.weighted_energy(reference, generated, [0.5, 0.5]) == finite_energy(
        reference, generated
    )
    assert stats.weighted_energy(reference, generated, [1, 0]) == 2


def test_weighted_coefficients_match_every_complementary_swap_by_integer_replication():
    reference = np.array([[0.0, 1.0], [2.0, 0.0], [1.0, 4.0]])
    before = np.array([[1.0, 0.0], [3.0, 4.0], [2.0, 1.0]])
    after = np.array([[2.0, 0.0], [0.0, 1.0], [1.0, 5.0]])
    weights = np.array([0.25, 0.25, 0.5])
    coefficients = stats.paired_energy_contributions(reference, before, after, weights)
    for swaps in itertools.product((False, True), repeat=3):
        swaps = np.array(swaps)
        first = np.where(swaps[:, None], after, before)
        second = np.where(swaps[:, None], before, after)
        # Replication gives the weighted empirical probability distribution independently.
        expected = finite_energy(reference, np.repeat(second, [1, 1, 2], axis=0)) - finite_energy(
            reference, np.repeat(first, [1, 1, 2], axis=0)
        )
        assert np.dot(1 - 2 * swaps, coefficients) == pytest.approx(expected, abs=1e-12)
    uniform = np.full(3, 1 / 3)
    assert stats.paired_energy_contributions(reference, before, after, uniform) == pytest.approx(
        randomization.paired_energy_contributions(reference, before, after)
    )


def test_full_grid_reproduces_all_finite_distances_and_retains_every_inventory():
    real, rows, scaler = grid(4)
    result = stats.compute(real, rows, scaler, 4, permutation_seed=123)
    assert {
        k: len(result[k])
        for k in (
            "distances",
            "absolute",
            "coordinates",
            "exploratory_contrasts",
            "pair_support",
            "scene_contributions",
            "secondary",
            "time_diagnostics",
        )
    } == dict(
        distances=360,
        absolute=72,
        coordinates=744,
        exploratory_contrasts=48,
        pair_support=16 * 64,
        scene_contributions=48 * 64,
        secondary=72,
        time_diagnostics=48,
    )
    for row in result["distances"]:
        values = np.array(
            [
                r["values"]
                for r in selected(
                    rows, method=row["method_id"], condition=row["condition"], alias=row["alias"]
                )
            ]
        )
        section = features.FAMILIES[row["family"]]
        assert row["distance"] == pytest.approx(
            finite_energy(real[row["painter_id"]][:, section], values[:, section])
        )
        assert row["status"] == stats.AVAILABLE and row["generated_count"] == 64
    for row in result["exploratory_contrasts"]:
        section = features.FAMILIES[row["family"]]
        assert row["estimate"] == pytest.approx(-2 * np.sqrt(section.stop - section.start))
        assert row["estimate"] == pytest.approx(row["after_distance"] - row["before_distance"])
        assert row["pairs"] == 64 and row["status"] == stats.ELIGIBLE
        assert row["raw_p"] == row["holm_input"] == (row["exceedances"] + 1) / 100000
        assert "availability AND measured features" in row["null"]
        assert "lower" not in row and "upper" not in row
    assert all(r["included"] and r["weight"] == 1 / 64 for r in result["pair_support"])
    assert all(r["contribution"] is not None for r in result["scene_contributions"])
    for row in result["secondary"]:
        section = features.FAMILIES[row["family"]]
        change = -4 if row["endpoint"] == "overall_transition" else -2
        assert row["estimate"] == pytest.approx(change * np.sqrt(section.stop - section.start))
        assert row["support"] == "all_available_equal_template" and "raw_p" not in row


def test_one_missing_partner_changes_weights_and_keeps_all_available_support_separate():
    real, rows, scaler = grid(4)
    first = selected(rows)[0]
    missing(first)
    for row in selected(rows):
        if row["status"] == "measured" and row["template_id"] == first["template_id"]:
            row["values"] = [10.0] * 31
    partner = next(
        r
        for r in selected(rows, method="style_instruction")
        if r["block"] == first["block"] and r["template_id"] == first["template_id"]
    )
    partner["values"] = [50.0] * 31
    result = stats.compute(real, rows, scaler, 4, permutation_seed=12, permutation_draws=999)
    observed = [r for r in selected(rows) if r["status"] == "measured"]
    expanded = np.repeat(
        np.array([r["values"] for r in observed]),
        [4 if r["template_id"] == first["template_id"] else 3 for r in observed],
        axis=0,
    )
    for row in result["absolute"]:
        if (row["alias"], row["painter_id"], row["method_id"]) == (
            ALIASES[0],
            PAINTER_IDS[0],
            "by_name",
        ):
            section = features.FAMILIES[row["family"]]
            assert row["finite_distance"] == pytest.approx(
                finite_energy(real[PAINTER_IDS[0]][:, section], expanded[:, section])
            )
    support = [
        r
        for r in result["pair_support"]
        if r["alias"] == ALIASES[0]
        and r["painter_id"] == PAINTER_IDS[0]
        and r["before"] == "by_name"
    ]
    assert len(support) == 64 and sum(r["included"] for r in support) == 63
    assert sum(r["weight"] for r in support) == pytest.approx(1)
    for template in TEMPLATE_IDS:
        assert sum(r["weight"] for r in support if r["template_id"] == template) == pytest.approx(
            1 / 16
        )
    omitted = next(r for r in support if not r["included"])
    assert omitted["before_request_id"] == first["request_id"]
    assert omitted["after_request_id"] == partner["request_id"] and omitted["weight"] == 0
    for row in result["exploratory_contrasts"]:
        if (
            row["alias"] != ALIASES[0]
            or row["painter_id"] != PAINTER_IDS[0]
            or row["before"] != "by_name"
        ):
            continue
        own = [
            r
            for r in result["absolute"]
            if r["alias"] == row["alias"]
            and r["painter_id"] == row["painter_id"]
            and r["family"] == row["family"]
        ]
        all_available = {r["method_id"]: r["finite_distance"] for r in own}
        assert row["estimate"] != pytest.approx(
            all_available["style_instruction"] - all_available["by_name"]
        )
        assert row["pairs"] == 63
        contributions = [
            r
            for r in result["scene_contributions"]
            if all(r[k] == row[k] for k in ("alias", "painter_id", "family", "before", "after"))
        ]
        assert (
            len(contributions) == 64 and sum(r["contribution"] is None for r in contributions) == 1
        )
        assert sum(r["contribution"] or 0 for r in contributions) == pytest.approx(row["estimate"])


def test_inverse_cdf_uses_exact_mass_at_nonuniform_template_boundaries():
    real, rows, scaler = grid(4)
    target = selected(rows)
    value = 0
    for template, count in zip(TEMPLATE_IDS, [1, 2, 3, 4] * 4):
        for row in [r for r in target if r["template_id"] == template]:
            if row["block"] >= count:
                missing(row)
            else:
                row["values"] = [float(value)] * 31
                value += 1
    result = stats.compute(real, rows, scaler, 4, permutation_seed=123, permutation_draws=99)
    coordinates = [
        row
        for row in result["coordinates"]
        if (row["alias"], row["method_id"], row["painter_id"])
        == (ALIASES[0], "by_name", PAINTER_IDS[0])
    ]
    assert len(coordinates) == 31
    # Each four-template group holds exactly 1/4 probability: boundaries are 9, 19, 29.
    # Floating accumulation of 1/(16*m) used to move the median incorrectly to 20.
    for row in coordinates:
        assert row["generated_median"] == row["median_difference"] == 19
        assert row["generated_iqr"] == 20


def test_missing_whole_template_stays_unavailable_and_holm_keeps_family_48():
    real, rows, scaler = grid()
    missing(selected(rows)[0], status="failed")
    result = stats.compute(real, rows, scaler, 1, permutation_seed=19)
    unavailable = [r for r in result["exploratory_contrasts"] if r["status"] == stats.UNAVAILABLE]
    assert len(unavailable) == 3 and result["inference"]["eligible_endpoints"] == 45
    assert len(result["exploratory_contrasts"]) == result["inference"]["family_size"] == 48
    for row in unavailable:
        assert row["pairs"] == 0 and row["both_measured_pairs"] == 15
        assert row["estimate"] is row["raw_p"] is row["holm_p"] is None
        assert row["holm_input"] == 1 and row["reject_holm"] is False
        assert row["missing_templates"] == [TEMPLATE_IDS[0]]
    assert sum(r["distance"] is None for r in result["distances"]) == 12
    assert sum(r["median_difference"] is None for r in result["coordinates"]) == 31
    assert sum(r["estimate"] is None for r in result["secondary"]) == 6
    for row in result["exploratory_contrasts"]:
        if row["status"] == stats.ELIGIBLE:
            assert row["raw_p"] == 2 / 65536
            assert row["holm_p"] == 48 * 2 / 65536


def test_quantile_rule_is_inverse_cdf_for_both_populations_and_scaler_applied_once():
    real, rows, scaler = grid()
    real = {p: np.tile(np.arange(4.0)[:, None], (1, 31)) for p in PAINTER_IDS}
    scaler.update(center=[10.0] * 31, scale=[2.0] * 31)
    for row in rows:
        row["values"] = [10 + 2 * TEMPLATE_IDS.index(row["template_id"])] * 31
    result = stats.compute(real, rows, scaler, 1, permutation_seed=4)
    assert result["inference"]["quantile_rule"] == stats.QUANTILE_RULE
    for row in result["coordinates"]:
        assert row["reference_median"] == 1 and row["reference_iqr"] == 2
        assert row["generated_median"] == 7 and row["generated_iqr"] == 8
        assert row["median_difference"] == 6 and row["iqr_ratio"] == 4
    assert all(
        r["estimate"] == 0 and r["raw_p"] == r["holm_p"] == 1
        for r in result["exploratory_contrasts"]
    )


def test_row_permutation_does_not_change_support_randomization_or_output_order():
    real, rows, scaler = grid()
    missing(selected(rows)[0])
    unchanged = copy.deepcopy((rows, scaler))
    expected = stats.compute(real, rows, scaler, 1, permutation_seed=4)
    assert (rows, scaler) == unchanged
    shuffled = copy.deepcopy(rows)
    np.random.default_rng(91).shuffle(shuffled)
    assert stats.compute(real, shuffled, scaler, 1, permutation_seed=4) == expected


@pytest.mark.parametrize(
    "weights", [[0.2, 0.2], [-0.1, 1.1], [0, 0], [np.nan, 1], [1], [[0.5, 0.5]]]
)
def test_invalid_probability_mass_is_rejected_without_normalization(weights):
    with pytest.raises(ValueError, match="weights"):
        stats.weighted_energy([[0]], [[1], [2]], weights)
    with pytest.raises(ValueError, match="weights"):
        stats.paired_energy_contributions([[0]], [[1], [2]], [[0], [1]], weights)


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "duplicate",
        "identity",
        "sequence",
        "alias",
        "method",
        "condition",
        "template",
        "block",
        "status",
        "nonfinite",
        "shape",
    ],
)
def test_foreign_or_malformed_terminal_grid_is_rejected(fault):
    real, rows, scaler = grid()
    if fault == "missing":
        rows.pop()
    elif fault == "duplicate":
        rows[0] = rows[1]
    elif fault == "identity":
        rows[0]["image_id"] = "other-request"
    elif fault == "sequence":
        rows[0]["request_sequence"] = rows[1]["request_sequence"]
    elif fault in {"alias", "method", "condition", "template"}:
        field = {"method": "method_id", "template": "template_id"}.get(fault, fault)
        rows[0][field] = "unregistered"
    elif fault == "block":
        rows[0]["block"] = 100
    elif fault == "status":
        rows[0]["status"] = "discarded_outlier"
    elif fault == "nonfinite":
        rows[0]["values"][0] = np.inf
    else:
        rows[0]["values"].pop()
    with pytest.raises(ValueError):
        stats.compute(real, rows, scaler, 1, permutation_seed=4)
