"""Numeric-only render tests, including complete inventories with unavailable endpoints."""

import copy
import csv
import hashlib
import json

import numpy as np
import pytest

from latent_art_bench.painter_prompt_supplement_v1 import report, statistics


def _numeric_result(all_unavailable=False):
    rows = []
    for alias in report.ALIASES:
        for method_index, method in enumerate(report.METHODS):
            for condition in (*report.PAINTER_IDS, "artist_free"):
                for template_index, template in enumerate(report.TEMPLATES):
                    index = len(rows)
                    row = dict(
                        alias=alias,
                        method_id=method,
                        condition=condition,
                        template_id=template,
                        block=0,
                        request_sequence=index,
                        request_id=f"q{index}",
                        image_id=f"q{index}",
                        status="measured",
                        values=[
                            0.1 * method_index + 0.03 * template_index + 0.01 * feature
                            for feature in range(31)
                        ],
                    )
                    if index == 0 or all_unavailable:
                        row["status"] = "not_generated"
                        row.pop("values")
                    rows.append(row)
    real = {p: np.array([np.zeros(31), np.ones(31)]) for p in report.PAINTER_IDS}
    result = statistics.compute(
        real, rows, dict(center=[0.0] * 31, scale=[1.0] * 31), 1, permutation_seed=20260905
    )
    result.update(
        aliases=list(report.ALIASES),
        methods=list(report.METHODS),
        painters=list(report.PAINTER_IDS),
        families={f: list(names) for f, names in report.FAMILY_NAMES.items()},
        repetitions=1,
        analysis_id="supplement-fixture",
        source_run_id="source-fixture",
        registered_primary_status="unavailable_incomplete_grid",
        reference_counts=dict(zip(report.PAINTER_IDS, (297, 106, 141, 105))),
        scaler_development_counts=dict(zip(report.PAINTER_IDS, (101, 36, 48, 36))),
        service_diagnostics={"fixture": "RGB; requested aliases; snapshot unverified"},
        copy_diagnostics={"candidates": []},
        qualification={"scope": "synthetic-only fixture"},
        inputs=[dict(path="data/manifests/fixture.json", sha256="a" * 64)],
    )
    result["availability"] = [
        dict(
            alias=a,
            method_id=m,
            condition=c,
            expected=16,
            statuses={
                "measured": sum(
                    r["status"] == "measured"
                    for r in rows
                    if (r["alias"], r["method_id"], r["condition"]) == (a, m, c)
                ),
                "not_generated": sum(
                    r["status"] != "measured"
                    for r in rows
                    if (r["alias"], r["method_id"], r["condition"]) == (a, m, c)
                ),
            },
        )
        for a in report.ALIASES
        for m in report.METHODS
        for c in (*report.PAINTER_IDS, "artist_free")
    ]
    result["template_availability"] = [
        dict(
            alias=r["alias"],
            method_id=r["method_id"],
            condition=r["condition"],
            template_id=r["template_id"],
            expected=1,
            statuses={r["status"]: 1},
        )
        for r in rows
    ]
    return result


@pytest.fixture(scope="module")
def numeric_result():
    return _numeric_result()


def hashes(directory):
    return {
        p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in directory.rglob("*")
        if p.is_file()
    }


def test_full_bundle_is_deterministic_and_retains_all_numeric_inventory(numeric_result, tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    before = copy.deepcopy(numeric_result)
    report.write_bundle(numeric_result, first)
    report.write_bundle(numeric_result, second)
    assert numeric_result == before
    assert hashes(first) == hashes(second)
    assert set(hashes(first)) == {
        "REPORT.md",
        "diagnostics.json",
        *(f"{name}.csv" for name in report.TABLES),
        *(
            f"plots/{name}.{extension}"
            for name in ("target_distances", "paired_transitions", "pair_availability")
            for extension in ("png", "svg")
        ),
    }
    for name in report.TABLES:
        with (first / f"{name}.csv").open(newline="", encoding="utf-8") as handle:
            exported = list(csv.DictReader(handle))
        assert len(exported) == len(numeric_result[name])
    with (first / "exploratory_contrasts.csv").open(newline="", encoding="utf-8") as handle:
        endpoints = list(csv.DictReader(handle))
    assert len(endpoints) == 48
    unavailable = [r for r in endpoints if r["status"] == "unavailable_missing_template"]
    assert len(unavailable) == 3
    assert all(r["raw_p"] == r["holm_p"] == "" and r["holm_input"] == "1.0" for r in unavailable)
    available = next(r for r in endpoints if r["raw_p"])
    original = next(
        r
        for r in numeric_result["exploratory_contrasts"]
        if all(
            str(r[k]) == available[k] for k in ("alias", "painter_id", "family", "before", "after")
        )
    )
    assert float(available["estimate"]) == original["estimate"]
    markdown = (first / "REPORT.md").read_text()
    assert "original registered primary analysis remains unavailable" in markdown
    assert "after the first service refusal and before new-image feature measurement" in markdown
    assert "paired supports and weights can differ" in markdown
    assert "does not isolate a feature change from an availability change" in markdown
    assert "weighted inverse empirical-CDF quantiles" in markdown
    assert "Cézanne" in markdown and "45 available; 3 unavailable; 48 retained" in markdown
    diagnostics = json.loads((first / "diagnostics.json").read_text())
    for key in ("qualification", "inputs", "service_diagnostics", "copy_diagnostics", "inference"):
        assert diagnostics[key] == numeric_result[key]
    for name in ("target_distances", "paired_transitions", "pair_availability"):
        assert (first / "plots" / f"{name}.png").read_bytes().startswith(b"\x89PNG")
        assert "<dc:date>" not in (first / "plots" / f"{name}.svg").read_text()


def test_markdown_escapes_nonascii_metadata_and_csv_preserves_exact_text(numeric_result):
    result = copy.deepcopy(numeric_result)
    result["source_run_id"] = "Échantillon|<script>\n[link](target)"
    markdown = report._markdown(result, report.TABLES)
    assert "Échantillon\\|&lt;script&gt; \\[link\\](target)" in markdown
    assert "<script>" not in markdown
    value = 'Cézanne | "quoted"\nsecond line'
    decoded = list(csv.DictReader(report._csv([dict(note=value)]).splitlines(keepends=True)))
    assert decoded == [dict(note=value)]


@pytest.mark.parametrize("table", report.TABLES)
def test_missing_rows_are_not_silently_omitted(numeric_result, tmp_path, table):
    result = copy.deepcopy(numeric_result)
    result[table].pop()
    with pytest.raises(ValueError, match="full .*inventory"):
        report.write_bundle(result, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_unavailable_placeholder_cannot_be_presented_as_observed_p(numeric_result, tmp_path):
    result = copy.deepcopy(numeric_result)
    row = next(
        r for r in result["exploratory_contrasts"] if r["status"] == "unavailable_missing_template"
    )
    row["raw_p"] = row["holm_p"] = 1.0
    with pytest.raises(ValueError, match="unavailable endpoint"):
        report.write_bundle(result, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_existing_outputs_are_retained_without_overwrite(numeric_result, tmp_path):
    (tmp_path / "REPORT.md").write_text("unique earlier artifact")
    with pytest.raises(FileExistsError, match="existing files are retained"):
        report.write_bundle(numeric_result, tmp_path)
    assert list(tmp_path.iterdir()) == [tmp_path / "REPORT.md"]
    assert (tmp_path / "REPORT.md").read_text() == "unique earlier artifact"


def test_completely_unavailable_results_render_plainly_without_empty_errorbars(tmp_path):
    result = _numeric_result(all_unavailable=True)
    report.write_bundle(result, tmp_path / "bundle")
    markdown = (tmp_path / "bundle" / "REPORT.md").read_text()
    assert "0 available; 48 unavailable; 48 retained" in markdown
    assert "check supplement-fixture" in markdown
    assert all(r["raw_p"] is None for r in result["exploratory_contrasts"])
    assert len(list((tmp_path / "bundle" / "plots").iterdir())) == 6


def test_target_scales_cover_both_aliases_within_each_family(numeric_result, monkeypatch):
    result = copy.deepcopy(numeric_result)
    for row in result["absolute"]:
        if row["alias"] == report.ALIASES[1]:
            row["finite_distance"] = 100.0
    limits = {}

    def inspect(fig, output, name):
        limits[name] = [axis.get_xlim() for axis in fig.axes]
        report.plt.close(fig)

    monkeypatch.setattr(report, "_save", inspect)
    with report.plt.rc_context(report.STYLE):
        report._plots(result, None)
    assert len(limits) == 3
    for family_index in range(3):
        first = limits["target_distances"][family_index]
        second = limits["target_distances"][family_index + 3]
        assert first == second and first[0] == 0 and first[1] > 100
