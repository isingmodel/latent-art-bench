from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from latent_art_bench.io import stable_hash
from latent_art_bench.pilot2.analysis import (
    chromatic_secondary_json_data,
    summarize_chromatic_secondary,
)
from latent_art_bench.pilot2.chromatic import (
    FEATURE_VERSION,
    LONG_SIDE,
    chromatic_config,
)
from latent_art_bench.pilot2.reporting import (
    render_chromatic_markdown,
    write_pilot2_report,
)

from .test_analysis_helpers import ARTISTS, synthetic_grid, synthetic_result
from .test_analysis_projection import _bindings, _completion, _generation_cells


def _derived(source_record_id: str, source_sha: str, output_sha: str) -> Dict[str, Any]:
    config_sha = "9" * 64
    identity = stable_hash(
        {
            "source_record_id": source_record_id,
            "source_sha256": source_sha,
            "output_sha256": output_sha,
            "preprocessing_config_sha256": config_sha,
        }
    )
    return {
        "derived_input_id": f"pilot2-input-{identity[:24]}",
        "source_record_id": source_record_id,
        "source_sha256": source_sha,
        "output_sha256": output_sha,
        "preprocessing_config_sha256": config_sha,
    }


def _feature(
    source_record_id: str,
    source_png_sha: str,
    seamlessness: float,
    histogram_bin: int,
) -> Dict[str, Any]:
    config_sha = stable_hash(
        chromatic_config().model_dump(mode="json", exclude_none=True)
    )
    root = [0.0] * 30
    root[histogram_bin] = 1.0
    identity = stable_hash(
        {
            "source_record_id": source_record_id,
            "source_png_sha256": source_png_sha,
            "feature_version": FEATURE_VERSION,
            "feature_config_sha256": config_sha,
            "analysis_long_side": LONG_SIDE,
        }
    )
    return {
        "record_id": f"pilot2-chromatic-{identity[:24]}",
        "source_record_id": source_record_id,
        "source_png_sha256": source_png_sha,
        "feature_version": FEATURE_VERSION,
        "feature_config_sha256": config_sha,
        "vector": [seamlessness, *root],
        "scalars": {"seamlessness": seamlessness},
    }


def _real_records() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for artist in ARTISTS:
        for source in ("aic", "nga"):
            for rank in range(5):
                work_id = f"{artist}-{source}-{rank}"
                source_sha = stable_hash({"raw-real": work_id})
                png_sha = stable_hash({"derived-real": work_id})
                rows.append(
                    {
                        "canonical_work_id": work_id,
                        "artist_id": artist,
                        "source_id": source,
                        "derived_input": _derived(work_id, source_sha, png_sha),
                        "feature": _feature(work_id, png_sha, 0.25, 1),
                    }
                )
    return rows


def _generated_records() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for cell in _generation_cells():
        output_sha = stable_hash({"generated-output": cell.cell_id})
        png_sha = stable_hash({"generated-derived": cell.cell_id})
        terminal: Dict[str, Any] = {
            "record_type": "pilot2_generation_terminal",
            "cell_id": cell.cell_id,
            "cell_identity_sha256": cell.cell_identity_sha256,
            "outcome": "succeeded",
            "output_sha256": output_sha,
            "executed_model_claims": False,
        }
        terminal["terminal_record_sha256"] = stable_hash(terminal)
        control = cell.artist_free_control
        rows.append(
            {
                "terminal_record": terminal,
                "derived_input": _derived(cell.cell_id, output_sha, png_sha),
                "feature": _feature(
                    cell.cell_id,
                    png_sha,
                    0.1 if control else 0.3,
                    0 if control else 1,
                ),
            }
        )
    return rows


def _summary() -> Any:
    cells = _generation_cells()
    completion = _completion(cells)
    from latent_art_bench.pilot2.config import Pilot2Config

    config = Pilot2Config()
    return summarize_chromatic_secondary(
        synthetic_grid(),
        _real_records(),
        _generated_records(),
        bindings=_bindings(config, cells, completion),
        generation_cells=cells,
        generation_completion=completion,
    )


def test_chromatic_secondary_is_executable_paired_and_non_gating() -> None:
    result = _summary()
    assert result.role == "secondary_descriptive_non_gating"
    assert result.can_open_or_close_generation_gate is False
    assert result.can_rescue_primary_analysis is False
    assert result.executed_model_claims is False
    assert result.observed_real_features == 40
    assert result.observed_generated_features == 320
    assert len(result.real_reference_summaries) == 8
    assert len(result.requested_label_summaries) == 2
    assert len(result.artist_pair_summaries) == 8
    for row in result.requested_label_summaries:
        assert row.named_feature_cells == 128
        assert row.control_feature_cells == 32
        assert row.complete_named_control_pairs == 128
        assert row.mean_named_seamlessness == pytest.approx(0.3)
        assert row.mean_control_seamlessness == pytest.approx(0.1)
        assert row.mean_paired_named_minus_control_seamlessness == pytest.approx(0.2)
        assert row.mean_paired_named_control_histogram_hellinger == pytest.approx(1.0)
    for row in result.artist_pair_summaries:
        assert row.complete_pairs == 32
        assert row.mean_named_to_real_artist_histogram_hellinger == pytest.approx(0.0)
        assert row.mean_control_to_real_artist_histogram_hellinger == pytest.approx(1.0)


def test_chromatic_json_markdown_and_report_artifact_are_bound(tmp_path: Path) -> None:
    chromatic = _summary()
    payload = chromatic_secondary_json_data(chromatic)
    markdown = render_chromatic_markdown(chromatic)
    assert payload["result_sha256"] == chromatic.result_sha256
    assert "descriptive only" in markdown
    assert "cannot open or close" in markdown
    assert "rank request labels" in markdown

    written = write_pilot2_report(
        synthetic_result(draws=5),
        tmp_path / "report",
        evidence_root=tmp_path,
        chromatic_secondary=chromatic,
    )
    assert written.chromatic_secondary_json is not None
    assert Path(written.chromatic_secondary_json).is_file()


def test_chromatic_provenance_tampering_is_rejected() -> None:
    cells = _generation_cells()
    completion = _completion(cells)
    from latent_art_bench.pilot2.config import Pilot2Config

    generated = _generated_records()
    generated[0]["derived_input"]["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="derived-input identity is stale"):
        summarize_chromatic_secondary(
            synthetic_grid(),
            _real_records(),
            generated,
            bindings=_bindings(Pilot2Config(), cells, completion),
            generation_cells=cells,
            generation_completion=completion,
        )
