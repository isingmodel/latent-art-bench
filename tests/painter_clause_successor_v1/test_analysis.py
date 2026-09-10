"""Artificial-only arithmetic, randomization, complete-grid and gate qualification."""

import copy
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import binom

from latent_art_bench.painter_clause_successor_v1 import analysis, common
from latent_art_bench.painter_clause_validation_v1 import common as predecessor
from latent_art_bench.painter_distribution_study_v1.inference import paired_contributions
from latent_art_bench.painter_prompt_study_v1.randomization import randomization_pvalue

ROOT = Path(__file__).resolve().parents[2]


def synthetic_inputs(seed=752):
    """All references/scalers are invented; no retained feature file is read."""
    rng = np.random.default_rng(seed)
    result = dict(
        schema="painter-clause-successor-inputs/1",
        origin=dict(path="studies/painter_clause_validation_v1/inputs.json", sha256="a" * 64),
        targets={common.PAINTER_ID: dict(built=11 / 32, land=18 / 32, water=3 / 32)},
        reference={},
        scalers={},
    )
    for pipe in common.PIPELINES:
        result["reference"][pipe] = {
            common.PAINTER_ID: dict(
                ids=[f"artificial-reference-{i:02d}" for i in range(32)],
                n=32,
                values=rng.normal(size=(32, 31)).tolist(),
            )
        }
        result["scalers"][pipe] = {
            "scaler": dict(
                center=np.linspace(-0.1, 0.1, 31).tolist(),
                scale=np.linspace(0.8, 1.2, 31).tolist(),
            )
        }
    return result


@pytest.fixture(scope="module")
def artificial():
    rng = np.random.default_rng(753)
    requests, config, inputs = common.requests(ROOT), common.configuration(ROOT), synthetic_inputs()
    rows = []
    for request in requests:
        for pipe in common.PIPELINES:
            raw = rng.normal(size=31) + (0.7 if request["arm"] == "generic" else 0)
            scaler = inputs["scalers"][pipe]["scaler"]
            rows.append(
                dict(
                    {k: v for k, v in request.items() if k != "payload"},
                    image_id=request["request_id"],
                    pipeline=pipe,
                    status="measured",
                    values=raw.tolist(),
                    scaled=((raw - scaler["center"]) / scaler["scale"]).tolist(),
                )
            )
    receipt = dict(duration_contract_met=True, identity_contract_met=True, planned=96)
    return requests, rows, inputs, config, receipt


def run(data):
    requests, rows, inputs, config, receipt = data
    return analysis.analyze(requests, rows, inputs, config, collection_receipt=receipt)


@pytest.fixture(scope="module")
def complete(artificial):
    return run(artificial)


def direct_energy(reference, generated, weights):
    """Explicit double sums, independent of implementation's matrix products."""
    a = np.full(len(reference), 1 / len(reference))
    cross = sum(
        a[i] * weights[j] * np.linalg.norm(x - y)
        for i, x in enumerate(reference)
        for j, y in enumerate(generated)
    )
    rr = sum(
        a[i] * a[j] * np.linalg.norm(x - y)
        for i, x in enumerate(reference)
        for j, y in enumerate(reference)
    )
    gg = sum(
        weights[i] * weights[j] * np.linalg.norm(x - y)
        for i, x in enumerate(generated)
        for j, y in enumerate(generated)
    )
    return 2 * cross - rr - gg


def test_exact_prompts_routes_full_panel_and_disjoint_ids():
    current, old = common.requests(ROOT), predecessor.requests(ROOT)
    old_by_slot = {(r["template_id"], r["repetition"], r["arm"]): r for r in old}
    assert current == common.requests(ROOT)
    assert len(current) == 96
    assert Counter(r["arm"] for r in current) == {"generic": 48, "cezanne": 48}
    assert {r["template_id"] for r in current} == {r["template_id"] for r in old}
    assert "pcv_built04" in {r["template_id"] for r in current}
    assert not {r["request_id"] for r in current} & {r["request_id"] for r in old}
    for row in current:
        prior = old_by_slot[row["template_id"], row["repetition"], row["arm"]]
        assert row["payload"] == prior["payload"]
        assert row["route"] == "oauth_gpt_image_2"
        assert row["payload"]["model"] == "gpt-image-2"
        assert "muted, low-chroma" not in row["payload"]["prompt"]
        assert "vivid, high-chroma" not in row["payload"]["prompt"]
    slots, classes = analysis.validate_design(current, common.configuration(ROOT))
    assert len(slots) == 96 and Counter(classes.values()) == dict.fromkeys(common.CLASSES, 8)


def test_compact_input_lineage_preserves_full_reference_and_scaler_objects():
    # Only retained reference/scaler inputs are read, never prospective outcomes.
    old_bytes = (ROOT / predecessor.INPUTS).read_bytes()
    old = json.loads(old_bytes)
    current = json.loads((ROOT / common.INPUTS).read_bytes())
    assert current["origin"] == dict(
        path=predecessor.INPUTS.as_posix(),
        sha256=hashlib.sha256(old_bytes).hexdigest(),
    )
    assert current["targets"] == {common.PAINTER_ID: old["targets"][common.PAINTER_ID]}
    assert current["scalers"] == old["scalers"]
    for pipe in common.PIPELINES:
        assert current["reference"][pipe] == {
            common.PAINTER_ID: old["reference"][pipe][common.PAINTER_ID]
        }
    analysis.validate_inputs(current)


def test_primary_direct_energy_and_single_fixed_family(artificial, complete):
    assert len(complete["primary"]) == 1 and len(complete["views"]) == 3
    assert complete["measured_by_pipeline"] == dict.fromkeys(common.PIPELINES, 96)
    row, view = complete["primary"][0], complete["views"][0]
    assert view["pipeline"] == "primary512"
    weights = np.array(view["generated_weights"])
    classes = view["scene_classes"]
    assert weights.tolist() == [analysis.TARGET[c] / 16 for c in classes for _ in range(2)]
    assert weights.sum() == 1
    refs = np.array(artificial[2]["reference"]["primary512"][common.PAINTER_ID]["values"])
    indexed = {(r["request_id"], r["pipeline"]): r for r in artificial[1]}
    energies = {}
    for arm in common.ARMS:
        y = np.array(
            [indexed[i, "primary512"]["scaled"] for i in view["arms"][arm]["generated_ids"]]
        )
        energies[arm] = direct_energy(refs, y, weights)
        assert view["arms"][arm]["energy_distance"] == pytest.approx(energies[arm], abs=1e-12)
    assert row["estimate"] == pytest.approx(energies["cezanne"] - energies["generic"], abs=1e-12)
    assert sum(row["contributions"]) == pytest.approx(row["estimate"])
    assert len(row["contributions"]) == row["pairs"] == 48
    assert row["ordered_pairs"] == sorted(row["ordered_pairs"])
    assert row["status"] == "available" and row["alpha"] == 0.025
    assert row["reject"] == (row["raw_p"] <= 0.025)
    assert "holm_p" not in row and "interval" not in row
    test = row["randomization"]
    assert test["permutations"] == 99999 and test["seed"] == 2026091052
    assert row["raw_p"] == (test["exceedances"] + 1) / 100000


def test_monte_carlo_exact_48_pair_replay(complete):
    row = complete["primary"][0]
    values = np.array(row["contributions"])
    rng = np.random.default_rng(2026091052)
    threshold = abs(values.sum()) - 32 * np.finfo(float).eps * np.abs(values).sum()
    exceedances = 0
    # Same frozen draw stream, explicit row sums instead of the tested einsum.
    for start in range(0, 99999, 4096):
        signs = 2 * rng.integers(0, 2, size=(min(4096, 99999 - start), 48), dtype=np.int8) - 1
        exceedances += int((np.abs((signs * values).sum(axis=1)) >= threshold).sum())
    assert row["raw_p"] == (1 + exceedances) / 100000


def test_weighted_sign_identity_for_every_two_position_assignment():
    rng = np.random.default_rng(754)
    ref, generic, named = rng.normal(size=(4, 2)), rng.normal(size=(5, 2)), rng.normal(size=(5, 2))
    weights = np.array([1, 3, 2, 7, 4]) / 17
    contributions = paired_contributions(ref, generic, named, pair_weights=weights)
    assignments = list(itertools.product((0, 1), repeat=5))
    direct = []
    for bits in assignments:
        flip = np.array(bits, dtype=bool)
        before = np.where(flip[:, None], named, generic)
        after = np.where(flip[:, None], generic, named)
        value = direct_energy(ref, after, weights) - direct_energy(ref, before, weights)
        assert value == pytest.approx((1 - 2 * flip) @ contributions, abs=1e-12)
        direct.append(value)
    # Each pair has two equiprobable positions. All 2^5 joint assignments occur
    # once in this exact design, including assignments with within-pair reversal.
    assert len(set(assignments)) == 32
    assert np.array(assignments).sum(axis=0).tolist() == [16] * 5
    tested = randomization_pvalue(contributions, seed=1)
    count = np.count_nonzero(np.abs(direct) >= abs(contributions.sum()) - 1e-12)
    assert tested["raw_p"] == count / 32


@pytest.mark.parametrize("kind", ["constant", "content_mass", "rare_large", "zero"])
def test_48_pair_sharp_null_exact_plus_one_rejection_probability(kind):
    """Exact finite null/MC law, not service power or validity of the prior trigger.

    Enumerate the integer-convolution distribution of 48 independent position
    signs. Conditional on a statistic, the 99,999 sampled signs give a binomial
    exceedance count. Thus the integration below is exact (up to floating point),
    avoiding a noisy repeated simulation or 2^48 brute-force enumeration.
    """
    magnitudes = dict(
        constant=[1] * 48,
        content_mass=[11] * 16 + [18] * 16 + [3] * 16,
        rare_large=[1] * 47 + [48],
        zero=[0] * 48,
    )[kind]
    counts = Counter({0: 1})
    for value in magnitudes:
        next_counts = Counter()
        for total, count in counts.items():
            next_counts[total - value] += count
            next_counts[total + value] += count
        counts = next_counts
    assert sum(counts.values()) == 2**48
    magnitudes_counts = Counter()
    for total, count in counts.items():
        magnitudes_counts[abs(total)] += count
    rejection_probability = 0
    tail_count = 0
    for magnitude in sorted(magnitudes_counts, reverse=True):
        count = magnitudes_counts[magnitude]
        tail_count += count
        # (1 + exceedances) / 100000 <= .025 iff exceedances <= 2499.
        rejection_probability += count / 2**48 * binom.cdf(2499, 99999, tail_count / 2**48)
    assert 0 <= rejection_probability <= 0.025 + 1e-12
    if kind == "zero":
        assert rejection_probability == 0
        assert randomization_pvalue(np.zeros(48), seed=2026091052)["raw_p"] == 1


def test_summary_hand_values_and_zero_denominators():
    ref, generated, weights = (
        np.array([[0.0], [2.0]]),
        np.array([[1.0], [3.0]]),
        np.array([0.25, 0.75]),
    )
    value = analysis.summary(ref, generated, weights)
    assert value["energy_distance"] == 1.75
    assert value["reference_trace"] == 1
    assert value["generated_trace"] == 0.75
    assert value["generated_reference_trace_ratio"] == 0.75
    zero = analysis.summary(np.zeros((2, 1)), generated, weights)
    assert zero["generated_reference_trace_ratio"] is None
    assert zero["reference_trace_ratio_status"] == "unavailable_zero_denominator"
    arms = {k: dict(status="descriptive", generated_trace=0) for k in common.ARMS}
    assert analysis.trace_ratio(arms) == dict(status="unavailable_zero_denominator", ratio=None)


def test_all_secondary_traces_direct_and_narrow_scope(artificial, complete):
    indexed = {(r["request_id"], r["pipeline"]): r for r in artificial[1]}
    for view in complete["views"]:
        weights = np.array(view["generated_weights"])
        for arm in common.ARMS:
            cell = view["arms"][arm]
            y = np.array([indexed[i, view["pipeline"]]["scaled"] for i in cell["generated_ids"]])
            mean = sum(w * vector for w, vector in zip(weights, y, strict=True))
            trace = sum(
                w * np.dot(vector - mean, vector - mean)
                for w, vector in zip(weights, y, strict=True)
            )
            assert cell["generated_trace"] == pytest.approx(trace, abs=1e-12)
            assert (
                cell["generated_reference_trace_ratio"]
                == cell["generated_trace"] / cell["reference_trace"]
            )
        assert view["named_generic_trace_ratio"]["ratio"] == (
            view["arms"]["cezanne"]["generated_trace"] / view["arms"]["generic"]["generated_trace"]
        )
        assert (
            not {"maps", "retrieval", "variance", "conditional_residual", "contrasts"} & view.keys()
        )
    report = analysis.report_text(complete)
    for phrase in (
        "original Cezanne primary remains unavailable",
        "No non-rejection establishes",
        "conditional on the prior availability-triggered decision",
        "No further replacement",
    ):
        assert phrase in report


@pytest.mark.parametrize("arm", common.ARMS)
def test_missing_primary_cell_withholds_primary_without_complete_case_refill(artificial, arm):
    data = copy.deepcopy(artificial)
    row = next(r for r in data[1] if r["arm"] == arm and r["pipeline"] == "primary512")
    row.update(status="moderation_blocked", values=None, scaled=None)
    result = run(data)
    primary, view = result["primary"][0], result["views"][0]
    assert primary["status"] == "withheld_incomplete_allocated_grid"
    assert primary["estimate"] is primary["raw_p"] is None and not primary["reject"]
    assert "contributions" not in primary and "randomization" not in primary
    assert view["arms"][arm]["status"] == "withheld_incomplete_allocated_arm"
    assert view["arms"][next(a for a in common.ARMS if a != arm)]["status"] == "descriptive"
    assert view["named_generic_trace_ratio"]["ratio"] is None
    assert result["views"][1]["named_generic_trace_ratio"]["status"] == "descriptive"


def test_nonprimary_missingness_does_not_discard_primary(artificial, complete):
    data = copy.deepcopy(artificial)
    row = next(r for r in data[1] if r["pipeline"] == "resolution256")
    row.update(status="measurement_failed", values=None, scaled=None)
    assert run(data)["primary"] == complete["primary"]


def test_delivery_counts_once_without_affecting_numeric_selection(artificial, complete):
    data = copy.deepcopy(artificial)
    for row in data[1]:
        row["observed"] = dict(
            width=1536,
            height=1024,
            format="PNG",
            reported={"quality": "low"},
        )
    result = run(data)
    assert result["primary"] == complete["primary"]
    for arm in common.ARMS:
        assert result["delivery"][arm]["planned"] == 48
        assert result["delivery"][arm]["observed_outputs"] == 48
        assert result["delivery"][arm]["dimensions"] == {"1536x1024": 48}
        assert result["delivery"][arm]["reported_quality"] == {"low": 48}
    assert "no output is adjusted or excluded" in analysis.report_text(result)


@pytest.mark.parametrize(
    "receipt",
    [
        None,
        {},
        {"duration_contract_met": True, "identity_contract_met": True, "planned": 95},
        {"duration_contract_met": True, "identity_contract_met": True, "planned": 96.0},
        *[
            dict(duration_contract_met=x, identity_contract_met=True, planned=96)
            for x in (1, False, "true", None)
        ],
        *[
            dict(duration_contract_met=True, identity_contract_met=x, planned=96)
            for x in (1, False, "true", None)
        ],
    ],
)
def test_collection_gate_is_literal_and_preserves_only_complete_estimate(
    artificial, complete, receipt, monkeypatch
):
    def no_test(*args, **kwargs):
        pytest.fail("ineligible collection must not calculate an inferential p-value")

    monkeypatch.setattr(analysis, "randomization_pvalue", no_test)
    data = list(artificial)
    data[-1] = receipt
    endpoint = run(data)["primary"][0]
    assert endpoint["estimate"] == complete["primary"][0]["estimate"]
    assert endpoint["contributions"] == complete["primary"][0]["contributions"]
    assert endpoint["status"] == "withheld_collection_contract"
    assert endpoint["raw_p"] is None and not endpoint["reject"]
    assert "randomization" not in endpoint


@pytest.mark.parametrize(
    "field,value",
    [
        ("arm", "monet"),
        ("sequence", 99),
        ("sequence", True),
        ("repetition", 9),
        ("content_class", "new"),
        ("route", "flux_2_max"),
        ("within_block", 3),
    ],
)
def test_measurement_assignment_cannot_change(artificial, field, value):
    requests, rows, inputs, _, _ = copy.deepcopy(artificial)
    rows[0][field] = value
    with pytest.raises(ValueError, match="assigned request identity"):
        analysis.validate_measurements(requests, rows, inputs)


def test_missing_duplicate_unknown_and_nonfinite_measurements_rejected(artificial):
    requests, rows, inputs, _, _ = copy.deepcopy(artificial)
    with pytest.raises(ValueError, match="terminal accounting"):
        analysis.validate_measurements(requests, rows[:-1], inputs)
    with pytest.raises(ValueError, match="duplicate"):
        analysis.validate_measurements(requests, rows + [rows[0]], inputs)
    rows[0]["pipeline"] = "not_allocated"
    with pytest.raises(ValueError, match="unknown"):
        analysis.validate_measurements(requests, rows, inputs)
    rows[0]["pipeline"] = "primary512"
    rows[0]["values"][0] = float("nan")
    with pytest.raises(ValueError, match="finite numeric"):
        analysis.validate_measurements(requests, rows, inputs)


def test_scaled_values_are_exact_and_failed_rows_cannot_hide_vectors(artificial):
    requests, rows, inputs, _, _ = copy.deepcopy(artificial)
    rows[0]["scaled"][0] = np.nextafter(rows[0]["scaled"][0], np.inf)
    with pytest.raises(ValueError, match="changed scaler"):
        analysis.validate_measurements(requests, rows, inputs)
    rows[0]["status"] = "failed"
    with pytest.raises(ValueError, match="carries a measurement"):
        analysis.validate_measurements(requests, rows, inputs)


@pytest.mark.parametrize(
    "change",
    [
        "target",
        "origin",
        "reference_n",
        "duplicate_ref",
        "negative_scale",
        "nan",
        "bool",
        "extra_pipeline",
    ],
)
def test_input_contract_rejects_changed_numeric_specification(change):
    inputs = synthetic_inputs()
    ref = inputs["reference"]["primary512"][common.PAINTER_ID]
    if change == "target":
        inputs["targets"][common.PAINTER_ID]["built"] = 1 / 3
    elif change == "origin":
        inputs["origin"]["path"] = "other/inputs.json"
    elif change == "reference_n":
        ref["n"] = 31
    elif change == "duplicate_ref":
        ref["ids"][0] = ref["ids"][1]
    elif change == "negative_scale":
        inputs["scalers"]["primary512"]["scaler"]["scale"][0] = -1
    elif change == "nan":
        ref["values"][0][0] = float("nan")
    elif change == "bool":
        ref["values"] = [[False] * 31] * 32
    else:
        inputs["reference"]["extra"] = ref
    with pytest.raises(ValueError):
        analysis.validate_inputs(inputs)


@pytest.mark.parametrize("change", ["repeat", "class", "block", "position", "count", "alpha"])
def test_allocation_cannot_expand_refill_or_change_family(artificial, change):
    requests, _, _, config, _ = copy.deepcopy(artificial)
    if change == "repeat":
        requests[0]["repetition"] = 2
    elif change == "class":
        requests[0]["content_class"] = "new"
    elif change == "block":
        for row in requests[2:4]:
            row["block_id"] = requests[0]["block_id"]
    elif change == "position":
        requests[0]["within_block"] = 1
    elif change == "count":
        requests.pop()
    else:
        config["alpha"] = 0.05
    with pytest.raises(ValueError):
        analysis.validate_design(requests, config)
