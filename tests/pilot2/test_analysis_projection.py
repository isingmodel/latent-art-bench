from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

import numpy as np
import pytest

from latent_art_bench.io import stable_hash
from latent_art_bench.pilot2.analysis import (
    Pilot2AnalysisBindings,
    analyze_projected_pilot2,
    prepare_projected_analysis_inputs,
)
from latent_art_bench.pilot2.config import Pilot2Config
from latent_art_bench.pilot2.generation import (
    GenerationCell,
    build_generation_cells,
    generation_grid_sha256,
)
from latent_art_bench.pilot2.learned_formal import fit_train_only_pca
from latent_art_bench.schemas import PromptRecord

from .test_analysis_helpers import ARTISTS, CONTENT_IDS, POSITIONS


def _raw_real_atlas() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for artist_index, artist in enumerate(ARTISTS):
        for source_index, source in enumerate(("aic", "nga")):
            for rank in range(5):
                rows.append(
                    {
                        "canonical_work_id": f"{artist}-{source}-{rank}",
                        "artist_id": artist,
                        "source_id": source,
                        "split": "train" if rank < 3 else "held_out",
                        "status": "ok",
                        "vector": [
                            POSITIONS[artist] + source_index * 0.2 + rank * 0.03,
                            float((artist_index + 1) ** 2 + rank * 0.1),
                            float(source_index),
                            float(rank),
                        ],
                    }
                )
    return rows


def _frozen_pca(rows: List[Dict[str, Any]]) -> Any:
    train = sorted(
        (row for row in rows if row["split"] == "train"),
        key=lambda row: row["canonical_work_id"],
    )
    return fit_train_only_pca(
        np.asarray([row["vector"] for row in train], dtype=np.float64),
        [row["canonical_work_id"] for row in train],
    )


def _generation_cells() -> List[GenerationCell]:
    prompts: List[PromptRecord] = []
    for content in CONTENT_IDS:
        prompts.append(
            PromptRecord(
                prompt_id=f"{content}-control",
                content_id=content,
                template_id="control",
                prompt=f"A landscape for {content}, no text.",
                artist_free_control=True,
                test_only=True,
            )
        )
        for artist in ARTISTS:
            prompts.append(
                PromptRecord(
                    prompt_id=f"{content}-{artist}",
                    content_id=content,
                    template_id="named",
                    prompt=f"A landscape for {content} in the style of {artist}, no text.",
                    target_artist_id=artist,
                    target_artist_name=artist,
                    test_only=True,
                )
            )
    return build_generation_cells(prompts, repetitions=4)


def _completion(
    cells: Sequence[GenerationCell], *, failed_cap_cell_id: str | None = None
) -> Dict[str, Any]:
    dispositions = {
        cell.cell_id: (
            "failed_after_retry_cap"
            if cell.cell_id == failed_cap_cell_id
            else "succeeded"
        )
        for cell in cells
    }
    payload: Dict[str, Any] = {
        "schema_version": "pilot2-generation-completion-test-v1",
        "generation_grid_sha256": generation_grid_sha256(cells),
        "cell_dispositions": dict(sorted(dispositions.items())),
    }
    payload["report_sha256"] = stable_hash(payload)
    return payload


def _bindings(
    config: Pilot2Config,
    cells: Sequence[GenerationCell],
    completion: Dict[str, Any],
) -> Pilot2AnalysisBindings:
    return Pilot2AnalysisBindings(
        pilot2_config_sha256=config.content_hash(),
        protocol_document_sha256="1" * 64,
        prompt_manifest_sha256="2" * 64,
        qualification_result_sha256="3" * 64,
        qualification_contract_sha256="4" * 64,
        generation_gate_sha256="5" * 64,
        transport_conformance_sha256="6" * 64,
        generation_grid_sha256=generation_grid_sha256(cells),
        generation_completion_sha256=completion["report_sha256"],
    )


def _raw_generated(
    cells: Sequence[GenerationCell], *, failed_cap_cell_id: str | None = None
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for cell in cells:
        row = cell.model_dump(mode="json")
        if cell.cell_id == failed_cap_cell_id:
            row.update(
                {
                    "outcome": "terminal_failure",
                    "terminal_disposition": "terminal_failure",
                    "retry_cap_exhausted": True,
                    "attempt_count": 10,
                }
            )
        else:
            artist_index = (
                0 if cell.artist_free_control else ARTISTS.index(cell.target_artist_id)
            )
            row.update(
                {
                    "outcome": "succeeded",
                    "generation_disposition": "succeeded",
                    "physical_attempt_count": 1,
                    "output_sha256": "7" * 64,
                    "derived_png_sha256": "8" * 64,
                    "raw_vector": (
                        [15.0, 5.0, 0.5, 2.0]
                        if cell.artist_free_control
                        else [
                            POSITIONS[cell.target_artist_id],
                            float((artist_index + 1) ** 2),
                            0.5,
                            2.0,
                        ]
                    ),
                }
            )
        rows.append(row)
    return rows


def _projected_fixture(
    *, failed_cap: bool = False
) -> Tuple[Pilot2Config, Any, List[GenerationCell], Dict[str, Any]]:
    config = Pilot2Config()
    real = _raw_real_atlas()
    cells = _generation_cells()
    failed_id = cells[0].cell_id if failed_cap else None
    completion = _completion(cells, failed_cap_cell_id=failed_id)
    projected = prepare_projected_analysis_inputs(
        _frozen_pca(real),
        real,
        _raw_generated(cells, failed_cap_cell_id=failed_id),
        bindings=_bindings(config, cells, completion),
        generation_cells=cells,
        generation_completion=completion,
    )
    return config, projected, cells, completion


def test_projection_bridge_uses_one_train_only_pca_and_binds_result() -> None:
    config, projected, _, _ = _projected_fixture()
    pca_state = projected.pca_state_sha256
    assert len(projected.real_observations) == 40
    assert len(projected.generated_observations) == 320
    assert {row.pca_state_sha256 for row in projected.real_observations} == {pca_state}
    assert {row.pca_state_sha256 for row in projected.generated_observations} == {
        pca_state
    }
    assert all(row.raw_feature_sha256 for row in projected.generated_observations)

    result = analyze_projected_pilot2(
        config,
        projected,
        content_ids=CONTENT_IDS,
        protocol_preconditions_met=True,
        bootstrap_draws=20,
    )
    assert result.itt.expected_cells == 320
    assert result.scientific_completion.status == "complete"
    assert result.projected_input_manifest_sha256 == projected.manifest_sha256


def test_projection_bridge_rejects_a_pca_fitted_on_the_wrong_real_works() -> None:
    config = Pilot2Config()
    real = _raw_real_atlas()
    wrong_rows = real[:24]
    wrong = fit_train_only_pca(
        np.asarray([row["vector"] for row in wrong_rows], dtype=np.float64),
        [row["canonical_work_id"] for row in wrong_rows],
    )
    cells = _generation_cells()
    completion = _completion(cells)
    with pytest.raises(ValueError, match="24 frozen training works"):
        prepare_projected_analysis_inputs(
            wrong,
            real,
            _raw_generated(cells),
            bindings=_bindings(config, cells, completion),
            generation_cells=cells,
            generation_completion=completion,
        )


def test_projected_manifest_and_config_tampering_are_rejected() -> None:
    config, projected, _, _ = _projected_fixture()
    stale = projected.model_copy(update={"manifest_sha256": "0" * 64})
    with pytest.raises(ValueError, match="manifest hash is stale"):
        analyze_projected_pilot2(
            config,
            stale,
            content_ids=CONTENT_IDS,
            protocol_preconditions_met=True,
            bootstrap_draws=5,
        )
    changed_config = config.model_copy(
        update={
            "generation": config.generation.model_copy(update={"timeout_seconds": 1.0})
        }
    )
    with pytest.raises(ValueError, match="config disagrees"):
        analyze_projected_pilot2(
            changed_config,
            projected,
            content_ids=CONTENT_IDS,
            protocol_preconditions_met=True,
            bootstrap_draws=5,
        )


def test_retry_cap_is_terminal_for_itt_without_changing_physical_ledger_status() -> None:
    config, projected, cells, completion = _projected_fixture(failed_cap=True)
    row = projected.generated_observations[0]
    assert row.cell_id == cells[0].cell_id
    assert completion["cell_dispositions"][row.cell_id] == "failed_after_retry_cap"
    assert row.generation_disposition == "failed_after_retry_cap"
    assert row.outcome == "terminal_failure"
    assert row.physical_attempt_count == 10
    result = analyze_projected_pilot2(
        config,
        projected,
        content_ids=CONTENT_IDS,
        protocol_preconditions_met=True,
        bootstrap_draws=5,
    )
    assert result.itt.failed_after_retry_cap_cells == 1
    assert result.itt.terminal_failure_cells == 1
    assert result.itt.retryable_failure_cells == 0
    assert result.scientific_completion.status == "complete"
