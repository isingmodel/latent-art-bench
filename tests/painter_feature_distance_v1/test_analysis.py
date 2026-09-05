"""Small numeric populations exercise the distance explorer without reading any images."""

import copy
import hashlib
import json
from collections import Counter

import numpy as np
import pytest

from latent_art_bench.painter_feature_distance_v1 import analysis
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS
from latent_art_bench.painter_feature_generation_v2 import empirical, features
from latent_art_bench.painter_feature_generation_v2.artifacts import MANIFESTS, digest


def _generated_rows(blocks=1, alias="toy-service"):
    return [
        dict(
            image_id=f"{alias}-{block}-{condition}-{template}",
            stage="generated", status="measured", alias=alias,
            condition=condition, block=block, template_id=f"t{template:02}",
            values=[float(index + template / 16)] * 31,
            normalization={"short_side": 512},
        )
        for block in range(blocks)
        for index, condition in enumerate(analysis.CONDITIONS)
        for template in range(16)
    ]


def _source_tree(root, fault=None):
    """Write a minimal self-contained graph; faults precede outer file hash bindings."""
    method, experiment = "toy-method", "toy-experiment"
    directory = MANIFESTS / method
    hashes = {}

    def write(path, value, *, lines=False):
        path = directory / path
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        rendered = (
            "".join(json.dumps(row) + "\n" for row in value)
            if lines else json.dumps(value)
        )
        target.write_text(rendered)
        hashes[path.as_posix()] = hashlib.sha256(target.read_bytes()).hexdigest()
        return hashes[path.as_posix()]

    def bindings(paths):
        return [{"path": (directory / p).as_posix(),
                 "sha256": hashes[(directory / p).as_posix()]} for p in paths]

    frozen = dict(method_id=method, feature_names=list(features.NAMES), short_side=512,
                  experiment_ids=[experiment])
    if fault == "feature_order":
        frozen["feature_names"].reverse()
    frozen_hash = write("method_freeze.json", frozen)
    scaler = dict(
        center=[0.0] * 31, scale=[1.0] * 31,
        invalid_coordinates={family: [] for family in features.FAMILIES},
        development_counts={p: 10 for p in PAINTER_IDS},
        method_freeze_sha256=frozen_hash,
        development_feature_sha256="development-vectors",
    )
    if fault == "scaler_method":
        scaler["method_freeze_sha256"] = "different-freeze"
    if fault == "scaler_scale":
        scaler["scale"][0] = 0.0
    scaler_hash = write("scaler.json", scaler)
    write("development_receipt.json", dict(
        method_freeze_sha256=frozen_hash, feature_file_sha256="development-vectors",
        scaler_sha256=scaler_hash,
    ))
    real = {p: np.array([[i - 1.0] * 31, [i + 1.0] * 31])
            for i, p in enumerate(PAINTER_IDS)}
    confirmation = [
        dict(image_id=f"{p}-{i}", role="confirmation", painter_id=p, stage="confirmation",
             status="measured", values=values.tolist(), normalization={"short_side": 512})
        for p, matrix in real.items() for i, values in enumerate(matrix)
    ]
    generated = _generated_rows()
    for row in [*confirmation, *generated]:
        row["feature_sha256"] = digest(row["values"])
    if fault == "feature_digest":
        confirmation[0]["values"][0] += 1

    def stage(prefix, name, rows):
        file_hash = write(f"{prefix}{name}_features.jsonl", rows, lines=True)
        receipt = dict(
            stage=name, method_freeze_sha256=frozen_hash, feature_file_sha256=file_hash,
            terminal_records=len(rows), expected_records=len(rows),
            statuses=dict(Counter(row["status"] for row in rows)),
        )
        if name == "generated":
            receipt["experiment_id"] = experiment
        if name == "confirmation" and fault == "terminal_count":
            receipt["terminal_records"] -= 1
        if name == "confirmation" and fault == "status_accounting":
            receipt["statuses"] = {"measured": len(rows) - 1, "failed": 1}
        write(f"{prefix}{name}_receipt.json", receipt)

    stage("", "confirmation", confirmation)
    stage(f"experiments/{experiment}/", "generated", generated)
    write(f"../{experiment}/generation_receipt.json", dict(complete_generated_grid=True))
    comparison = empirical.finite_comparisons(
        real, empirical.generated_groups(generated, dict(center=[0.0] * 31, scale=[1.0] * 31))[
            "toy-service"
        ],
    )
    if fault == "endpoint":
        comparison["endpoints"][0]["estimate"] += 1
    if fault == "coordinate":
        comparison["coordinate_diagnostics"][0]["median_difference"] += 1
    if fault in {"real_counts", "generated_counts"}:
        comparison[fault][PAINTER_IDS[0]] += 1
    numeric_paths = ["scaler.json", "confirmation_features.jsonl",
                     f"experiments/{experiment}/generated_features.jsonl"]
    # Generation receipts use a normalized portable path, as real study bindings do.
    inputs = bindings(numeric_paths)
    inputs.append(dict(path=(MANIFESTS / experiment / "generation_receipt.json").as_posix(),
                       sha256=hashes[(directory / f"../{experiment}/generation_receipt.json")
                                     .as_posix()]))
    write("empirical_analysis.json", dict(method_id=method, inputs=inputs,
                                          comparisons={"toy-service": comparison}))
    write("report_receipt.json", dict(
        method_id=method,
        inputs=bindings(["method_freeze.json", "development_receipt.json",
                         "confirmation_receipt.json", "empirical_analysis.json"]),
        files=[dict(path="reports/toy.md", sha256="reported-document-hash")],
    ))
    return method


def test_full_matrix_has_analytic_distances_and_directional_contrasts():
    offsets = dict(zip(PAINTER_IDS, [0.0, 10.0, 20.0, 30.0]))
    real = {p: np.full((i + 2, 31), offset)
            for i, (p, offset) in enumerate(offsets.items())}
    conditions = dict(offsets, artist_free=5.0)
    conditions[PAINTER_IDS[-1]] = 10.0  # Deliberately closer to the wrong painter.
    generated = {"toy-service": {p: np.full((16, 31), v) for p, v in conditions.items()}}
    distances, contrasts = analysis.distance_tables(real, generated)
    assert len(distances) == 3 * 5 * 4
    assert len(contrasts) == 3 * 4
    assert len({(r["condition"], r["painter_id"], r["family"]) for r in distances}) == 60
    for row in distances:
        dimension = len(features.FAMILY_NAMES[row["family"]])
        expected = 2 * abs(conditions[row["condition"]] - offsets[row["painter_id"]])
        assert row["distance"] == pytest.approx(expected * np.sqrt(dimension))
        assert row["reference_count"] == len(real[row["painter_id"]])
        assert row["generated_count"] == 16
    for row in contrasts:
        assert row["control_difference"] == pytest.approx(
            row["target_distance"] - row["artist_free_distance"])
        if row["painter_id"] == PAINTER_IDS[-1]:
            assert row["nearest_other_painter"] == PAINTER_IDS[1]
            assert row["specificity_margin"] > 0
        else:
            assert row["control_difference"] < 0
            assert row["specificity_margin"] < 0


def test_same_medians_do_not_erase_distributional_spread_distance():
    real = {p: np.array([[-1.0] * 31, [1.0] * 31]) for p in PAINTER_IDS}
    generated = {"toy-service": {p: np.zeros((16, 31)) for p in analysis.CONDITIONS}}
    distances, _ = analysis.distance_tables(real, generated)
    # Both medians are zero. Cross mean = sqrt(D), reference self mean = sqrt(D).
    for row in distances:
        assert row["distance"] == pytest.approx(np.sqrt(len(features.FAMILY_NAMES[row["family"]])))


def test_block_tables_retain_every_template_and_pair_all_observed_blocks():
    scaler = dict(center=[0.0] * 31, scale=[1.0] * 31)
    real = {p: np.zeros((2, 31)) for p in PAINTER_IDS}
    rows = {"repeated": _generated_rows(25, "repeated"),
            "single": _generated_rows(1, "single")}
    for service_rows in rows.values():
        for row in service_rows:
            block = row["block"]
            own, free = (0, 0) if block < 8 else ((1, 4) if block < 17 else (10, 10))
            offset = free if row["condition"] == "artist_free" else own
            template = int(row["template_id"][1:])
            row["values"] = [offset + template / 16] * 31
    generated = empirical.generated_groups([r for group in rows.values() for r in group], scaler)
    distances, summaries = analysis.block_tables(real, generated, rows, scaler)
    assert len(distances) == (25 + 1) * 4 * 3
    assert len(summaries) == 2 * 4 * 3
    template_term = 15 / 16 - 255 / 768
    for row in distances:
        dimension = len(features.FAMILY_NAMES[row["family"]])
        own, free = (0, 0) if row["block"] < 8 else (
            (1, 4) if row["block"] < 17 else (10, 10))
        assert row["generated_count"] == 16
        assert row["distance"] == pytest.approx((2 * own + template_term) * np.sqrt(dimension))
        assert row["control_difference"] == pytest.approx(2 * (own - free) * np.sqrt(dimension))
    for row in summaries:
        assert row["blocks"] == (25 if row["service"] == "repeated" else 1)
        assert row["images_per_condition"] == 16
    chosen = [r for r in distances if r["service"] == "repeated"
              and r["painter_id"] == PAINTER_IDS[0] and r["family"] == "color"]
    assert {r["block"] for r in chosen} == set(range(25))
    assert np.median([r["control_difference"] for r in chosen]) == pytest.approx(0)
    assert np.median([r["distance"] for r in chosen]) - np.median(
        [r["artist_free_distance"] for r in chosen]) < 0
    broken = copy.deepcopy(rows)
    broken["repeated"][0]["template_id"] = "unpaired-template"
    with pytest.raises(ValueError, match="complete condition"):
        analysis.block_tables(real, generated, broken, scaler)


def test_sources_validate_exact_bytes_and_confine_paths(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    path = root / "values.json"
    path.write_text('{"value": 1}')
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    sources = analysis.Sources(root)
    assert sources.bound("values.json", {"values.json": sha}) == {"value": 1}
    assert sources.records() == [{"path": "values.json", "sha256": sha}]
    with pytest.raises(ValueError, match="source hash mismatch"):
        sources.read("values.json", "wrong-hash")
    with pytest.raises(ValueError, match="missing source binding"):
        sources.bound("values.json", {})
    with pytest.raises(ValueError, match="duplicate source binding"):
        analysis.binding_map(sources.records() * 2)
    path.write_text('{"value": 2}')
    with pytest.raises(ValueError, match="source changed while reading"):
        sources.read("values.json")
    outside = tmp_path / "outside.json"
    outside.write_text('{"value": 3}')
    (root / "escape.json").symlink_to(outside)
    for escaped in ("../outside.json", "escape.json", outside):
        with pytest.raises(ValueError):
            sources.read(escaped)
    assert sources.records() == [{"path": "values.json", "sha256": sha}]


def test_analyze_loads_sealed_numeric_fixture_with_all_distance_outputs(tmp_path):
    method = _source_tree(tmp_path)
    result = analysis.analyze(tmp_path, method)
    assert result["estimator"] == "finite_empirical_energy_V_statistic"
    assert result["confidence_intervals"] is None
    assert result["feature_names"] == list(features.NAMES)
    assert result["reference_counts"] == {p: 2 for p in PAINTER_IDS}
    assert result["generated_counts"] == {"toy-service": {p: 16 for p in analysis.CONDITIONS}}
    assert len(result["distances"]) == 60
    assert len(result["coordinates"]) == 124
    assert len(result["reference_distances"]) == 48
    assert len(result["block_distances"]) == len(result["block_summary"]) == 12
    for row in result["reference_distances"]:
        if row["first_painter"] == row["second_painter"]:
            assert row["distance"] == pytest.approx(0)
    assert all(".." not in r["path"] for r in result["source"]["inputs"])


@pytest.mark.parametrize(("fault", "message"), [
    ("feature_order", "unsupported source feature contract"),
    ("scaler_method", "scaler is not bound"),
    ("scaler_scale", "invalid development IQR"),
    ("feature_digest", "feature vector hash mismatch"),
    ("terminal_count", "measurement stage accounting mismatch"),
    ("status_accounting", "measurement stage accounting mismatch"),
])
def test_source_contract_rejects_internally_inconsistent_sealed_inputs(tmp_path, fault, message):
    method = _source_tree(tmp_path, fault)
    with pytest.raises(ValueError, match=message):
        analysis.analyze(tmp_path, method)


@pytest.mark.parametrize("fault", ["endpoint", "coordinate", "real_counts", "generated_counts"])
def test_analyze_rejects_disagreement_with_sealed_result(tmp_path, fault):
    method = _source_tree(tmp_path, fault)
    with pytest.raises(ValueError, match="differ.*sealed result"):
        analysis.analyze(tmp_path, method)
