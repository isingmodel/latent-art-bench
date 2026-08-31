from __future__ import annotations

import json
from pathlib import Path

import pytest

from latent_art_bench.io import hash_file
from latent_art_bench.pilot2.reporting import (
    artifact_index_data,
    json_data,
    render_analysis_markdown,
    write_pilot2_report,
)

from .test_analysis_helpers import synthetic_result


def test_json_and_markdown_are_operational_requested_label_views() -> None:
    result = synthetic_result(draws=40)
    payload = json_data(result)
    markdown = render_analysis_markdown(result)

    assert payload["analysis_scope"] == "requested_label_operational_effect"
    assert payload["executed_model_claims"] is False
    assert payload["cross_label_superiority_estimand"] is False
    assert "authoritative executed-backend identities" in markdown
    assert "does not rank the labels" in markdown
    assert "Scientific execution status: **complete**" in markdown
    assert "All four label-by-estimand hypotheses supported: **true**" in markdown
    assert "quantile `0.0125`" in markdown
    assert "outperforms" not in markdown.casefold()
    assert "better model" not in markdown.casefold()


def test_report_writer_emits_content_addressed_relative_artifact_index(
    tmp_path: Path,
) -> None:
    result = synthetic_result(draws=30)
    input_path = tmp_path / "evidence" / "qualification.json"
    input_path.parent.mkdir(parents=True)
    input_path.write_text('{"status":"pass"}\n', encoding="utf-8")
    output_dir = tmp_path / "reports" / "pilot_2"
    written = write_pilot2_report(
        result,
        output_dir,
        evidence_root=tmp_path,
        input_artifacts={"qualification": input_path},
    )

    analysis_path = Path(written.analysis_json)
    report_path = Path(written.report_markdown)
    index_path = Path(written.artifact_index)
    assert analysis_path.is_file()
    assert report_path.is_file()
    assert index_path.is_file()
    assert written.analysis_json_sha256 == hash_file(analysis_path)
    assert written.report_markdown_sha256 == hash_file(report_path)
    assert written.artifact_index_sha256 == hash_file(index_path)

    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert index["pilot_id"] == "pilot_2"
    assert index["executed_model_claims"] is False
    assert index["cross_label_superiority_estimand"] is False
    assert index["analysis_result_sha256"] == result.result_sha256
    by_role = {row["role"]: row for row in index["artifacts"]}
    assert set(by_role) == {"analysis_json", "qualification", "report_markdown"}
    assert by_role["analysis_json"]["path"] == "reports/pilot_2/analysis.json"
    assert by_role["qualification"]["path"] == "evidence/qualification.json"
    assert all(not row["path"].startswith("/") for row in index["artifacts"])


def test_artifact_index_rejects_external_and_missing_files(tmp_path: Path) -> None:
    result = synthetic_result(draws=10)
    outside = tmp_path.parent / "outside-pilot2-evidence.json"
    outside.write_text("{}\n", encoding="utf-8")
    try:
        with pytest.raises(ValueError, match="outside the declared evidence root"):
            artifact_index_data(
                result, {"outside": outside}, root=tmp_path
            )
    finally:
        outside.unlink()
    with pytest.raises(FileNotFoundError, match="missing pilot_2 artifact"):
        artifact_index_data(
            result, {"missing": tmp_path / "missing.json"}, root=tmp_path
        )


def test_reporting_rejects_a_stale_analysis_self_hash() -> None:
    result = synthetic_result(draws=10)
    stale = result.model_copy(update={"result_sha256": "0" * 64})
    with pytest.raises(ValueError, match="result hash is stale"):
        render_analysis_markdown(stale)
