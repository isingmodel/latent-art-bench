import copy

import numpy as np
import pytest

from latent_art_bench.io import hash_file
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import empirical, robustness
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    MANIFESTS,
    WORKSPACE,
    digest,
    publish,
)


def scaler():
    return dict(center=[0.0] * 31, scale=[1.0] * 31)


def generated_rows():
    return [
        dict(
            image_id=f"{a}-{p}-{t}",
            status="measured",
            values=[float(i)] * 31,
            alias=a,
            domain="generated",
            condition=p,
            block=0,
            template_id=f"t{t}",
        )
        for a in ("gpt-image-1", "gpt-image-2")
        for i, p in enumerate((*PAINTER_IDS, "artist_free"))
        for t in range(16)
    ]


def test_all_finite_endpoints_have_correct_contrast_sign():
    real = {p: np.full((3, 31), float(i)) for i, p in enumerate(PAINTER_IDS)}
    generated = dict(real, artist_free=np.full((16, 31), 10.0))
    result = empirical.finite_comparisons(real, generated)
    assert len(result["endpoints"]) == 60
    assert len(result["coordinate_diagnostics"]) == 124
    assert result["confidence_intervals"] is None
    for row in result["endpoints"]:
        assert row["estimate"] == 0 if row["endpoint"] == "target_fit" else row["estimate"] < 0


def test_aliases_are_kept_separate_and_grids_must_match():
    rows = generated_rows()
    groups = empirical.generated_groups(rows, scaler())
    assert set(groups) == {"gpt-image-1", "gpt-image-2"}
    assert all(g[PAINTER_IDS[0]].shape == (16, 31) for g in groups.values())
    rows[0]["template_id"] = "foreign-template"
    with pytest.raises(ValueError, match="complete condition"):
        empirical.generated_groups(rows, scaler())


@pytest.mark.parametrize("mutation", ["failure", "missing", "duplicate"])
def test_incomplete_generated_grids_never_become_fidelity_results(mutation):
    rows = generated_rows()
    if mutation == "failure":
        rows[0]["status"] = "failed"
    elif mutation == "missing":
        rows.pop()
    else:
        rows.append(rows[0])
    with pytest.raises(ValueError):
        empirical.generated_groups(rows, scaler())


def test_copy_exact_match_is_not_confused_with_nearest_perceptual_hash():
    references = [
        dict(image_id="exact", raw_sha256="A", phash="ffffffffffffffff"),
        dict(image_id="near", raw_sha256="B", phash="0"),
    ]
    generated = [dict(image_id="g", raw_sha256="A", phash="0")]
    candidate = empirical.copy_diagnostics(references, generated)["candidates"][0]
    assert candidate["nearest_phash_reference"] == "near"
    assert candidate["exact_file_references"] == ["exact"]


def test_recorded_content_class_is_used_and_small_strata_stay_unresolved():
    frame, rows = [], []
    for painter in PAINTER_IDS:
        for i in range(11):
            key = f"{painter}-{i}"
            frame.append(dict(work_id=key, content_class="water" if i < 10 else "land"))
            rows.append(
                dict(
                    image_id=key,
                    painter_id=painter,
                    values=[0.0] * 31,
                    normalization=dict(color_profile="missing_assumed_srgb"),
                )
            )
    generated = {"alias": {p: np.zeros((16, 31)) for p in PAINTER_IDS}}
    result = empirical.stratified_distances(frame, rows, generated, scaler())
    water = [r for r in result if r["stratum"] == "water"]
    assert len(water) == 4 and all("families" in r for r in water)
    land = [r for r in result if r["stratum"] == "land"]
    assert all(r["status"] == "sparse_unresolved" and "families" not in r for r in land)
    assert not any(r["stratum"] == "unknown" for r in result)


def test_service_diagnostic_uses_actual_collector_fields():
    result = empirical.service_diagnostics(
        [
            dict(
                alias="gpt-image-2",
                status="generated",
                reported=dict(model=None, quality="low"),
                decoded_size="1254x1254",
                latency_seconds=3,
                requested_returned_mismatches=["quality", "decoded_size"],
            )
        ]
    )["gpt-image-2"]
    assert result["decoded_sizes"] == {"1254x1254": 1}
    assert result["setting_mismatches"] == {"quality": 1, "decoded_size": 1}
    assert result["reported_settings"]["model"] == {"None": 1}


def test_terminal_stage_verifies_bytes_accounting_and_statuses(tmp_path):
    path = tmp_path / "generated_features.jsonl"
    publish(path, [dict(image_id="a", status="measured")], lines=True)
    publish(
        tmp_path / "generated_receipt.json",
        dict(
            feature_file_sha256=hash_file(path),
            terminal_records=1,
            expected_records=2,
            statuses=dict(measured=1),
        ),
    )
    with pytest.raises(ValueError, match="count or identities"):
        empirical.load_stage(tmp_path, "generated")
    path.write_text("changed")
    with pytest.raises(ValueError, match="bytes changed"):
        empirical.load_stage(tmp_path, "generated")


def test_identical_crop_branches_have_zero_effect_and_keep_both_aliases():
    rows = generated_rows()
    rows += [
        dict(
            image_id=p,
            domain="real",
            role="confirmation",
            painter_id=p,
            values=[float(i)] * 31,
            status="measured",
        )
        for i, p in enumerate(PAINTER_IDS)
    ]
    result = robustness.paired_changes(rows, copy.deepcopy(rows), scaler())
    assert result["status"] == "complete_paired_features"
    assert set(result["endpoint_changes"]) == {"gpt-image-1", "gpt-image-2"}
    assert all(r["change"] == 0 for v in result["endpoint_changes"].values() for r in v)
    changed = copy.deepcopy(rows)
    changed[0]["status"] = "failed"
    assert robustness.paired_changes(rows, changed, scaler())["comparisons"] is None
    with pytest.raises(ValueError, match="same unique population"):
        robustness.paired_changes(rows, rows[:-1], scaler())


def test_full_robustness_execution_preserves_population_and_new_development_scaler(
    tmp_path, monkeypatch
):
    base = tmp_path / MANIFESTS / "method"
    publish(
        base / "method_freeze.json",
        dict(
            inputs=[],
            acquisition_id="acquisition",
            experiment_ids=["generation"],
            feature_workers=2,
        ),
    )
    publish(base / "confirmation_opening.json", dict(inputs=[]))
    acquisitions, outputs = [], []
    counter = 0

    def image_record(key):
        nonlocal counter
        counter += 1
        raw = tmp_path / WORKSPACE / "fixture" / str(counter)
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(str(counter).encode())
        return dict(
            image_id=key,
            raw_path=str(raw.relative_to(tmp_path)),
            raw_sha256=hash_file(raw),
            status="measured",
            values=[float(counter)] * 31,
        )

    def stage_receipt(directory, stage, rows):
        path = directory / f"{stage}_features.jsonl"
        publish(path, rows, lines=True)
        publish(
            directory / f"{stage}_receipt.json",
            dict(
                expected_records=len(rows),
                terminal_records=len(rows),
                feature_file_sha256=hash_file(path),
                statuses=dict(measured=len(rows)),
            ),
        )

    for stage, count in (("development", 10), ("qualification", 1), ("confirmation", 1)):
        rows = []
        for p in PAINTER_IDS:
            for i in range(count):
                row = dict(image_record(f"{stage}-{p}-{i}"), role=stage, painter_id=p)
                rows.append(row)
                acquisitions.append(dict(row, work_id=row["image_id"], status="acquired"))
        stage_receipt(base, stage, rows)
    publish(tmp_path / MANIFESTS / "acquisition" / "acquisitions.jsonl", acquisitions, lines=True)
    rows = []
    for row in generated_rows():
        source = image_record(row["image_id"])
        rows.append(dict(row, **{k: source[k] for k in ("raw_sha256", "values")}))
        outputs.append(
            dict(
                row,
                request_id=row["image_id"],
                image_path=source["raw_path"],
                sha256=source["raw_sha256"],
                status="generated",
            )
        )
    gen_dir = tmp_path / MANIFESTS / "generation"
    publish(gen_dir / "generation_receipt.json", dict(complete_generated_grid=True))
    publish(gen_dir / "outputs.jsonl", outputs, lines=True)
    stage_receipt(base / "experiments" / "generation", "generated", rows)
    measured = []

    def fake_measure(item, short_side, crop_fraction):
        measured.append((item["image_id"], short_side, crop_fraction))
        values = [float(int(item["raw_sha256"][:6], 16))] * 31
        return dict(
            {k: v for k, v in item.items() if k not in ("path", "raw_path")},
            values=values,
            feature_sha256=digest(values),
            status="measured",
        )

    monkeypatch.setattr(robustness, "measure_one", fake_measure)
    result = robustness.execute(tmp_path, "method")
    assert result["status"] == "complete_paired_features"
    assert len(measured) == 2 * (48 + 160)
    assert {x[1] for x in measured} == {496}
    assert {x[2] for x in measured} == {0, 0.01}
    assert all(r["change"] == 0 for v in result["endpoint_changes"].values() for r in v)
    with pytest.raises(FileExistsError, match="terminal"):
        robustness.execute(tmp_path, "method")
