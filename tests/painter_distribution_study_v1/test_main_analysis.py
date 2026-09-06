from pathlib import Path

import numpy as np
import pytest

from latent_art_bench.io import read_json
from latent_art_bench.painter_distribution_study_v1 import analysis as a
from latent_art_bench.painter_distribution_study_v1 import study as s


def fixture():
    config = read_json(Path.cwd() / s.CONFIG)
    rng = np.random.default_rng(11)
    real = []
    for painter in s.PAINTERS:
        for c, n in zip(s.CLASSES, (3, 11, 18)):
            for i in range(n):
                real.append(
                    dict(
                        image_id=f"{painter}/{c}/{i}",
                        painter_id=painter,
                        content_class=c,
                        scaled=rng.normal(size=31).tolist(),
                        mixed_uncertain=False,
                        native_short_side=1200,
                    )
                )
    generated = [
        dict(
            r,
            image_id=r["request_id"],
            scaled=rng.normal(size=31).tolist(),
            initial_only_eligible=True,
        )
        for r in s.request_inventory(config)
    ]
    target = {p: a.mass([r for r in real if r["painter_id"] == p]) for p in s.PAINTERS}
    return config, real, generated, target


def test_primary_weights_match_original_content_and_reject_missing_support():
    _, real, generated, target = fixture()
    ref = [r for r in real if r["painter_id"] == s.PAINTERS[0]]
    gen = [
        r
        for r in generated
        if r["painter_id"] == s.PAINTERS[0]
        and r["route"] == s.ROUTES[0]
        and r["condition"] == "named"
    ]
    wr, wg = a.weights(ref, target[s.PAINTERS[0]]), a.weights(gen, target[s.PAINTERS[0]])
    assert np.allclose(wr, 1 / 32)
    for c in s.CLASSES:
        assert sum(w for r, w in zip(gen, wg) if r["content_class"] == c) == pytest.approx(
            target[s.PAINTERS[0]][c]
        )
    with pytest.raises(ValueError, match="support"):
        a.weights([r for r in gen if r["content_class"] != "water"], target[s.PAINTERS[0]])


def test_matched_contrast_uses_common_pairs_and_retains_unavailable_family_member():
    config, real, generated, target = fixture()
    painter, route = s.PAINTERS[0], s.ROUTES[0]
    ref = [r for r in real if r["painter_id"] == painter]
    filtered = [
        r
        for r in generated
        if not (
            r["route"] == route
            and r["painter_id"] == painter
            and r["condition"] == "named"
            and r["brief_id"] == "water01"
        )
    ]
    result = a.paired(
        ref,
        filtered,
        target[painter],
        route,
        painter,
        "artist_free",
        "named",
        config,
        0,
        run_test=False,
    )
    assert result["pairs"] == 69 and len(result["excluded_pairs"]) == 3
    ids = {r["image_id"]: r for r in filtered}
    before = [ids[c["before_image_id"]] for c in result["contributions"]]
    after = [ids[c["after_image_id"]] for c in result["contributions"]]
    wr, wg = a.weights(ref, target[painter]), a.weights(before, target[painter])
    direct = a.energy(a.values(ref), a.values(after), wr, wg) - a.energy(
        a.values(ref), a.values(before), wr, wg
    )
    assert result["estimate"] == pytest.approx(direct, abs=1e-12)
    unavailable = a.paired(
        ref, [], target[painter], route, painter, "artist_free", "named", config, 0
    )
    assert unavailable["raw_p"] == 1 and unavailable["status"] == "unavailable"


def test_classifier_holds_out_whole_briefs_and_original_works_with_sparse_water_support():
    _, real, generated, target = fixture()
    painter = s.PAINTERS[0]
    ref = [r for r in real if r["painter_id"] == painter]
    gen = [
        r
        for r in generated
        if r["painter_id"] == painter and r["route"] == s.ROUTES[0] and r["condition"] == "named"
    ]
    result = a.classify(ref, gen, target[painter], "brief", "rbf")
    assert result["status"] == "available" and len(result["predictions"]) == 104
    lookup = {r["image_id"]: r["brief_id"] for r in gen}
    for fold in result["memberships"]:
        assert not set(fold["train_image_ids"]) & set(fold["test_image_ids"])
        assert not {lookup[i] for i in fold["train_image_ids"] if i in lookup} & {
            lookup[i] for i in fold["test_image_ids"] if i in lookup
        }
    assert (
        a.weighted_metrics(
            np.array([-1, 1]), np.array([0, 2]), np.array([0.5, 0.5]), np.array([0.5, 0.5])
        )["auc"]
        == 0.75
    )


def test_baseline_and_empty_cells_do_not_invent_results():
    _, real, generated, target = fixture()
    ref = [r for r in real if r["painter_id"] == s.PAINTERS[0]]
    gen = [r for r in generated if r["painter_id"] == s.PAINTERS[0]]
    result = a.baseline(ref, gen, target[s.PAINTERS[0]], np.random.default_rng(1), draws=3)
    assert result["class_counts"] == dict(water=1, built=5, land=9)
    assert len(result["real_real_energy"]) == 3
    assert all(
        r["status"] == "unavailable" for r in a.cell_summaries(ref, [], target[s.PAINTERS[0]], {})
    )


def test_full_primary_analysis_has_all_endpoints_and_no_fitted_outcome_scaler():
    config, real, generated, targets = fixture()
    real = [dict(r, values=r["scaled"], pipeline="primary512", status="measured") for r in real]
    generated = [
        dict(r, values=r["scaled"], pipeline="primary512", status="measured") for r in generated
    ]
    scalers = dict(
        primary512=dict(status="available", scaler=dict(center=[0] * 31, scale=[1] * 31)),
        resolution256=dict(status="unavailable"),
        jpeg90_512=dict(status="unavailable"),
    )
    result = a.compute(
        real, generated, scalers, targets, config, baseline_draws=2, coverage_draws=2
    )
    assert len(result["cells"]) == 336 and len(result["endpoints"]) == 8
    assert len(result["classifiers"]) == 56 and len(result["sensitivity_contrasts"]) == 256
    assert all(r["pairs"] == 72 for r in result["endpoints"])
    assert all(r["holm_p"] >= r["raw_p"] for r in result["endpoints"])
    assert all(r["status"] == "available" for r in result["classifiers"])
    assert all(v["status"] == "available" for v in result["projections"].values())
