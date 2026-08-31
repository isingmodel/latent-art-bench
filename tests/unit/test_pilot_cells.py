from pathlib import Path

import pytest

from latent_art_bench.config import load_config
from latent_art_bench.evaluation.pilot_cells import (
    build_analysis_cells,
    validate_analysis_grid_provenance,
)
from latent_art_bench.generation.openai_images import plan_generation_calls
from latent_art_bench.io import read_jsonl
from latent_art_bench.schemas import (
    AnalysisCell,
    CanonicalWorkRecord,
    FeatureRow,
    PromptRecord,
    ReproductionRecord,
)


def _feature(
    *,
    identifier: str,
    work_id: str,
    reproduction_id: str,
    artist_id: str,
    version: str,
    config_hash: str,
    value: float,
    split: str = "unassigned",
    origin: str = "real",
    model=None,
    prompt_id=None,
    repetition: int = 0,
    extraction_metadata=None,
) -> FeatureRow:
    return FeatureRow(
        feature_id=f"feature-{identifier}",
        derived_view_id=f"view-{identifier}",
        reproduction_id=reproduction_id,
        canonical_work_id=work_id,
        artist_id=artist_id,
        origin=origin,
        split=split,
        model=model,
        prompt_id=prompt_id,
        repetition=repetition if origin == "generated" else None,
        feature_name="chromatic_distance_seamlessness",
        feature_version=version,
        feature_config_hash=config_hash,
        vector=[value],
        scalars={"seamlessness": value},
        extraction_metadata=extraction_metadata or {},
        status="ok",
    )


@pytest.mark.parametrize("tamper_generated_provenance", [False, True])
@pytest.mark.parametrize("generation_bypass", [False, True])
def test_build_analysis_cells_uses_primary_real_and_excludes_controls(
    tamper_generated_provenance: bool,
    generation_bypass: bool,
) -> None:
    config = load_config(Path("configs/pilot_1/pilot.yaml"))
    version, config_hash = config.measurement_identities()["chromatic"]
    prompts = [
        PromptRecord.model_validate(row)
        for row in read_jsonl(Path(config.generation.prompt_manifest))
    ]
    real = []
    canonical = []
    reproductions = []
    for artist_index, artist in enumerate(config.corpus.selected_artists):
        for split_index, split in enumerate(("train", "held_out")):
            work_id = f"real-{artist.artist_id}-{split}"
            reproduction_id = f"reproduction-{work_id}"
            canonical.append(
                CanonicalWorkRecord(
                    canonical_work_id=work_id,
                    artist_id=artist.artist_id,
                    artist_name=artist.artist_name,
                    title=work_id,
                    attribution_status="confirmed",
                    public_domain_status="confirmed",
                    split=split,
                )
            )
            reproductions.append(
                ReproductionRecord(
                    reproduction_id=reproduction_id,
                    canonical_work_id=work_id,
                    source_id="aic",
                    local_path=f"ignored/{reproduction_id}.png",
                    split=split,
                )
            )
            real.append(
                _feature(
                    identifier=work_id,
                    work_id=work_id,
                    reproduction_id=reproduction_id,
                    artist_id=artist.artist_id,
                    version=version,
                    config_hash=config_hash,
                    value=float(artist_index + split_index / 10),
                    split=split,
                )
            )

    calls = [
        call.model_copy(
            update={
                "status": "succeeded",
                "output_path": f"ignored/{call.call_id}.png",
                "output_sha256": "e" * 64,
                "actual_width": 1024,
                "actual_height": 1024,
                "actual_format": "png",
            }
        )
        for call in plan_generation_calls(
            "run",
            prompts,
            config.generation.models,
            config.generation,
            generation_bypass,
        )
    ]
    prompt_by_id = {prompt.prompt_id: prompt for prompt in prompts}
    generated = []
    for call in calls:
        prompt = prompt_by_id[call.prompt_id]
        generated.append(
            _feature(
                identifier=call.call_id,
                work_id=f"generated-work-{call.call_id}",
                reproduction_id=f"generated-{call.call_id}",
                artist_id=str(prompt.target_artist_id or ""),
                version=version,
                config_hash=config_hash,
                value=(99.0 if prompt.artist_free_control else float(call.repetition)),
                origin="generated",
                model=call.model,
                prompt_id=call.prompt_id,
                repetition=call.repetition,
                extraction_metadata={
                    "engineering_scope": "api_integration_test_only",
                    "preparation_qualification_bypass": generation_bypass,
                    "generation_attestation_sha256": "a" * 64,
                    "generation_manifest_sha256": "b" * 64,
                    "generation_request_identity_sha256": (
                        call.request_identity_sha256
                    ),
                    "generation_call_id": call.call_id,
                    "generation_output_sha256": call.output_sha256,
                },
            ).model_copy(update={"artist_id": prompt.target_artist_id})
        )

    if tamper_generated_provenance:
        generated[0].extraction_metadata["generation_request_identity_sha256"] = "9" * 64
        with pytest.raises(ValueError, match="generation_request_identity_sha256"):
            build_analysis_cells(
                config,
                real,
                generated,
                canonical,
                reproductions,
                prompts,
                calls,
                "chromatic",
                qualification_contract_hash="c" * 64,
                qualification_evidence_artifact_sha256="d" * 64,
                real_feature_manifest_sha256="f" * 64,
                generated_feature_manifest_sha256="0" * 64,
                generation_manifest_sha256="b" * 64,
                generation_attestation_sha256="a" * 64,
            )
        return

    cells = build_analysis_cells(
        config,
        real,
        generated,
        canonical,
        reproductions,
        prompts,
        calls,
        "chromatic",
        qualification_contract_hash="c" * 64,
        qualification_evidence_artifact_sha256="d" * 64,
        real_feature_manifest_sha256="f" * 64,
        generated_feature_manifest_sha256="0" * 64,
        generation_manifest_sha256="b" * 64,
        generation_attestation_sha256="a" * 64,
    )

    assert len(cells) == 8
    assert {cell.model for cell in cells} == {"gpt-image-1", "gpt-image-2"}
    assert all(len(cell.generated_vectors) == 4 for cell in cells)
    assert all(len(cell.target_train_vectors) == 1 for cell in cells)
    assert all(len(cell.target_held_out_vectors) == 1 for cell in cells)
    assert all(len(cell.neighbor_vectors) == 1 for cell in cells)
    assert all(
        cell.preparation_qualification_bypass is generation_bypass for cell in cells
    )


def test_analysis_grid_provenance_normalizes_chromatic_feature_name_and_rejects_subset() -> None:
    config = load_config(Path("configs/pilot_1/pilot.yaml"))
    identities = {
        measurement: (*config.measurement_identities()[measurement], "c" * 64)
        for measurement in config.measurements.required
    }
    feature_hashes = {
        "chromatic": ("1" * 64, "2" * 64),
        "learned_formal": ("3" * 64, "4" * 64),
    }
    qualification = {
        "chromatic": ("5" * 64, None),
        "learned_formal": ("6" * 64, "7" * 64),
    }
    cells = []
    for measurement in config.measurements.required:
        version, feature_hash, contract_hash = identities[measurement]
        for model in config.generation.models:
            for artist in config.corpus.selected_artists:
                pca_hash = qualification[measurement][1]
                cells.append(
                    AnalysisCell(
                        cell_id=f"{measurement}-{model}-{artist.artist_id}",
                        target_artist_id=artist.artist_id,
                        model=model,
                        measurement=measurement,
                        feature_name=(
                            "chromatic_distance_seamlessness"
                            if measurement == "chromatic"
                            else "learned_formal"
                        ),
                        feature_version=version,
                        feature_config_hash=feature_hash,
                        qualification_contract_hash=contract_hash,
                        qualification_evidence_artifact_sha256=qualification[measurement][0],
                        real_feature_manifest_sha256=feature_hashes[measurement][0],
                        generated_feature_manifest_sha256=feature_hashes[measurement][1],
                        generation_manifest_sha256="8" * 64,
                        generation_attestation_sha256="9" * 64,
                        reference_transform_state_sha256=pca_hash or "a" * 64,
                        qualified_reference_transform_state_sha256=pca_hash,
                        target_train_vectors=[[0.0]],
                        target_held_out_vectors=[[0.1]],
                        generated_vectors=[[0.2]],
                        neighbor_vectors={"neighbor": [[1.0]]},
                    )
                )

    validate_analysis_grid_provenance(
        config,
        cells,
        identities,
        feature_hashes,
        qualification,
        "8" * 64,
        "9" * 64,
    )
    with pytest.raises(ValueError, match="selective or stale"):
        validate_analysis_grid_provenance(
            config,
            cells[:-1],
            identities,
            feature_hashes,
            qualification,
            "8" * 64,
            "9" * 64,
        )
