from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

import numpy as np

from latent_art_bench.config import PilotConfig
from latent_art_bench.evaluation.learned_formal_v2 import (
    LearnedFormalV2Protocol,
    fit_real_pca,
    prepare_real_feature_rows,
    transform_with_pca,
)
from latent_art_bench.generation.attestation import validate_generation_call_identities
from latent_art_bench.generation.openai_images import (
    unique_successful_generation_calls_by_cell,
)
from latent_art_bench.io import stable_hash
from latent_art_bench.schemas import (
    AnalysisCell,
    AnalysisResult,
    CanonicalWorkRecord,
    FeatureRow,
    GenerationCallRecord,
    PromptRecord,
    ReproductionRecord,
    normalize_feature_measurement,
)


def validate_analysis_grid_provenance(
    config: PilotConfig,
    records: Iterable[AnalysisCell | AnalysisResult],
    qualification_identities: Mapping[str, tuple],
    feature_manifest_hashes: Mapping[str, tuple[str, str]],
    qualification_provenance: Mapping[str, tuple[str, Optional[str]]],
    generation_manifest_sha256: str,
    generation_attestation_sha256: str,
) -> None:
    """Fail closed unless records are the exact current 16-cell pilot grid."""

    rows = list(records)
    cell_ids = [row.cell_id for row in rows]
    if len(cell_ids) != len(set(cell_ids)):
        raise ValueError("analysis manifest contains duplicate cell identifiers")
    expected_grid = {
        (measurement, model, artist.artist_id)
        for measurement in config.measurements.required
        for model in config.generation.models
        for artist in config.corpus.selected_artists
    }
    if config.pilot_id == "pilot_1" and len(expected_grid) != 16:
        raise ValueError("pilot_1 requires an exact 16-cell analysis grid")
    observed_grid = [(row.measurement, row.model, row.target_artist_id) for row in rows]
    if len(set(observed_grid)) != len(observed_grid):
        raise ValueError("analysis manifest contains duplicate measurement/model/artist cells")
    if set(observed_grid) != expected_grid:
        missing = len(expected_grid - set(observed_grid))
        extra = len(set(observed_grid) - expected_grid)
        raise ValueError(
            f"analysis manifest is a selective or stale grid: missing={missing}, extra={extra}"
        )
    for row in rows:
        measurement = normalize_feature_measurement(row.feature_name)
        if measurement != row.measurement:
            raise ValueError(f"analysis measurement mismatch: {row.cell_id}")
        identity = qualification_identities.get(measurement)
        if identity is None:
            raise ValueError(f"analysis uses an unknown measurement: {measurement}")
        expected_real_hash, expected_generated_hash = feature_manifest_hashes[measurement]
        evidence_hash, qualified_pca_hash = qualification_provenance[measurement]
        mismatches = []
        if row.feature_version != identity[0]:
            mismatches.append("feature_version")
        if row.feature_config_hash != identity[1]:
            mismatches.append("feature_config_hash")
        if len(identity) >= 3 and row.qualification_contract_hash != identity[2]:
            mismatches.append("qualification_contract_hash")
        expected_values = {
            "qualification_evidence_artifact_sha256": evidence_hash,
            "real_feature_manifest_sha256": expected_real_hash,
            "generated_feature_manifest_sha256": expected_generated_hash,
            "generation_manifest_sha256": generation_manifest_sha256,
            "generation_attestation_sha256": generation_attestation_sha256,
            "qualified_reference_transform_state_sha256": qualified_pca_hash,
            "engineering_scope": "api_integration_test_only",
        }
        mismatches.extend(
            name
            for name, expected in expected_values.items()
            if getattr(row, name) != expected
        )
        if measurement == "learned_formal" and (
            row.reference_transform_state_sha256 != qualified_pca_hash
        ):
            mismatches.append("reference_transform_state_sha256")
        if mismatches:
            raise ValueError(
                f"analysis provenance is stale for {row.cell_id}: "
                + ", ".join(sorted(set(mismatches)))
            )


def build_analysis_cells(
    config: PilotConfig,
    real_features: Iterable[FeatureRow],
    generated_features: Iterable[FeatureRow],
    canonical: Sequence[CanonicalWorkRecord],
    reproductions: Sequence[ReproductionRecord],
    prompts: Sequence[PromptRecord],
    generation_calls: Sequence[GenerationCallRecord],
    measurement: str,
    *,
    qualification_contract_hash: Optional[str] = None,
    qualification_evidence_artifact_sha256: Optional[str] = None,
    real_feature_manifest_sha256: Optional[str] = None,
    generated_feature_manifest_sha256: Optional[str] = None,
    generation_manifest_sha256: Optional[str] = None,
    generation_attestation_sha256: Optional[str] = None,
    qualified_reference_transform_state_sha256: Optional[str] = None,
    learned_protocol: Optional[LearnedFormalV2Protocol] = None,
) -> List[AnalysisCell]:
    """Join frozen real references to generated target cells without visual selection."""

    real_rows = list(real_features)
    generated_rows = list(generated_features)
    if not real_rows or not generated_rows:
        raise ValueError("analysis cells require real and generated feature rows")
    if config.pilot_id == "pilot_1" and qualification_contract_hash is None:
        raise ValueError("pilot_1 analysis cells require a qualification contract hash")
    provenance_hashes = {
        "qualification evidence artifact": qualification_evidence_artifact_sha256,
        "real feature manifest": real_feature_manifest_sha256,
        "generated feature manifest": generated_feature_manifest_sha256,
        "generation manifest": generation_manifest_sha256,
        "generation attestation": generation_attestation_sha256,
    }
    if config.pilot_id == "pilot_1":
        missing = sorted(name for name, value in provenance_hashes.items() if value is None)
        if missing:
            raise ValueError(
                "pilot_1 analysis cells lack provenance hashes: " + ", ".join(missing)
            )
    expected_version, expected_hash = config.measurement_identities()[measurement]
    all_rows = real_rows + generated_rows
    if any(
        row.feature_version != expected_version or row.feature_config_hash != expected_hash
        for row in all_rows
    ):
        raise ValueError(f"{measurement} feature identity does not match the config")
    if any(row.origin != "real" for row in real_rows):
        raise ValueError("real feature input contains a non-real row")
    if any(row.origin != "generated" for row in generated_rows):
        raise ValueError("generated feature input contains a non-generated row")
    if any(normalize_feature_measurement(row.feature_name) != measurement for row in all_rows):
        raise ValueError(f"{measurement} input contains a different feature measurement")
    if len({row.feature_name for row in all_rows}) != 1:
        raise ValueError(f"{measurement} inputs do not share one persisted feature name")

    canonical_by_id = {row.canonical_work_id: row for row in canonical}
    if len(canonical_by_id) != len(canonical):
        raise ValueError("canonical work identifiers must be unique")
    reproduction_by_id = {row.reproduction_id: row for row in reproductions}
    if len(reproduction_by_id) != len(reproductions):
        raise ValueError("real reproduction identifiers must be unique")
    real_by_reproduction = {row.reproduction_id: row for row in real_rows}
    if len(real_by_reproduction) != len(real_rows):
        raise ValueError("real features contain duplicate reproduction identifiers")
    if set(real_by_reproduction) != set(reproduction_by_id):
        raise ValueError("real features must cover the frozen reproduction manifest exactly")
    for reproduction in reproductions:
        work = canonical_by_id.get(reproduction.canonical_work_id)
        if work is None:
            raise ValueError(
                f"reproduction {reproduction.reproduction_id} references an unknown work"
            )
        feature = real_by_reproduction[reproduction.reproduction_id]
        if reproduction.split != work.split or feature.split != work.split:
            raise ValueError(
                f"real feature {feature.feature_id} disagrees with its canonical split"
            )
        if feature.canonical_work_id != work.canonical_work_id:
            raise ValueError(
                f"real feature {feature.feature_id} disagrees with its canonical work"
            )
        if feature.artist_id != work.artist_id:
            raise ValueError(
                f"real feature {feature.feature_id} disagrees with its canonical artist"
            )
        if feature.status != "ok":
            raise ValueError("analysis accepts only successful real feature rows")

    if measurement == "learned_formal":
        protocol = learned_protocol or LearnedFormalV2Protocol()
        prepared = prepare_real_feature_rows(canonical, reproductions, real_rows, protocol)
        primary_real = list(prepared.primary_rows)
    else:
        primary_real = [
            row
            for row in real_rows
            if reproduction_by_id[row.reproduction_id].source_id
            != "cma_alternate_capture"
        ]
    if len({row.canonical_work_id for row in primary_real}) != len(primary_real):
        raise ValueError("analysis requires one primary real feature per canonical work")
    if {row.canonical_work_id for row in primary_real} != set(canonical_by_id):
        raise ValueError("primary real features must cover the canonical manifest exactly")

    validate_generation_call_identities(
        generation_calls, prompts, config.generation
    )
    successful_by_cell = unique_successful_generation_calls_by_cell(
        generation_calls, include_qualification_bypass=True
    )
    expected_generation_cells = {
        (prompt.prompt_id, model, repetition)
        for prompt in prompts
        for model in config.generation.models
        for repetition in range(config.generation.repetitions)
    }
    if set(successful_by_cell) != expected_generation_cells:
        missing = len(expected_generation_cells - set(successful_by_cell))
        extra = len(set(successful_by_cell) - expected_generation_cells)
        raise ValueError(
            "successful generation calls do not match the frozen grid: "
            f"missing={missing}, extra={extra}"
        )
    prompt_by_id = {row.prompt_id: row for row in prompts}
    if len(prompt_by_id) != len(prompts):
        raise ValueError("prompt identifiers must be unique")
    preparation_bypasses = set()
    for row in generated_rows:
        if row.status != "ok" or row.model is None or row.prompt_id is None:
            raise ValueError("every generated feature row must be complete and status=ok")
        if row.repetition is None:
            raise ValueError("every generated feature row must record its repetition")
        cell = (row.prompt_id, row.model, row.repetition)
        call = successful_by_cell.get(cell)
        if call is None:
            raise ValueError(f"generated feature lacks an attested successful call: {cell}")
        prompt = prompt_by_id[row.prompt_id]
        expected_metadata = {
            "engineering_scope": "api_integration_test_only",
            "generation_attestation_sha256": generation_attestation_sha256,
            "generation_manifest_sha256": generation_manifest_sha256,
            "generation_request_identity_sha256": call.request_identity_sha256,
            "generation_call_id": call.call_id,
            "generation_output_sha256": call.output_sha256,
        }
        mismatches = [
            name
            for name, value in expected_metadata.items()
            if row.extraction_metadata.get(name) != value
        ]
        bypass = row.extraction_metadata.get("preparation_qualification_bypass")
        if not isinstance(bypass, bool):
            mismatches.append("preparation_qualification_bypass")
        else:
            preparation_bypasses.add(bypass)
        if row.reproduction_id != f"generated-{call.call_id}":
            mismatches.append("reproduction_id")
        if row.canonical_work_id != f"generated-work-{call.call_id}":
            mismatches.append("canonical_work_id")
        if row.artist_id != prompt.target_artist_id:
            mismatches.append("artist_id")
        if mismatches:
            raise ValueError(
                f"generated feature provenance mismatch for {row.feature_id}: "
                + ", ".join(sorted(set(mismatches)))
            )
    if len(preparation_bypasses) != 1:
        raise ValueError("generated rows mix qualification-bypass preparation states")
    preparation_qualification_bypass = next(iter(preparation_bypasses))

    feature_ids = [row.feature_id for row in all_rows]
    if len(feature_ids) != len(set(feature_ids)):
        raise ValueError("analysis feature identifiers must be unique across both manifests")
    raw_vectors: Dict[str, np.ndarray] = {
        row.feature_id: np.asarray(row.vector, dtype=np.float64) for row in all_rows
    }
    if measurement == "learned_formal":
        train = [row for row in primary_real if row.split == "train"]
        matrix = np.asarray([raw_vectors[row.feature_id] for row in train])
        state = fit_real_pca(
            matrix,
            [row.canonical_work_id for row in train],
            [row.reproduction_id for row in train],
            [reproduction_by_id[row.reproduction_id].source_id for row in train],
            protocol,
        )
        projected = transform_with_pca(
            np.asarray([raw_vectors[row.feature_id] for row in all_rows]), state
        )
        vectors = {row.feature_id: projected[index] for index, row in enumerate(all_rows)}
        transform_state_sha256 = state.evidence.state_sha256
        if qualified_reference_transform_state_sha256 is None:
            raise ValueError("learned-formal analysis lacks the qualified PCA state")
        if transform_state_sha256 != qualified_reference_transform_state_sha256:
            raise ValueError(
                "learned-formal analysis PCA does not match qualification evidence"
            )
    elif measurement == "chromatic":
        if qualified_reference_transform_state_sha256 is not None:
            raise ValueError("chromatic analysis cannot declare a qualified PCA state")
        vectors = raw_vectors
        transform_state_sha256 = stable_hash(
            {
                "transform": "identity",
                "feature_version": expected_version,
                "feature_config_hash": expected_hash,
            }
        )
    else:
        raise ValueError(f"unsupported pilot measurement: {measurement}")

    expected_generated_cells = {
        (prompt.prompt_id, model, repetition)
        for prompt in prompts
        for model in config.generation.models
        for repetition in range(config.generation.repetitions)
    }
    observed_generated_cells = []
    for row in generated_rows:
        observed_generated_cells.append((row.prompt_id, row.model, row.repetition))
    if len(set(observed_generated_cells)) != len(observed_generated_cells):
        raise ValueError("generated features contain duplicate frozen cells")
    if set(observed_generated_cells) != expected_generated_cells:
        missing = len(expected_generated_cells - set(observed_generated_cells))
        extra = len(set(observed_generated_cells) - expected_generated_cells)
        raise ValueError(
            f"generated features do not match the frozen grid: missing={missing}, extra={extra}"
        )
    artists = {row.artist_id: row for row in config.corpus.selected_artists}
    real_train: Mapping[str, List[np.ndarray]] = defaultdict(list)
    real_held: Mapping[str, List[np.ndarray]] = defaultdict(list)
    for row in primary_real:
        target = real_train if row.split == "train" else real_held
        target[str(row.artist_id)].append(vectors[row.feature_id])

    generated_by_cell: Mapping[tuple, List[np.ndarray]] = defaultdict(list)
    for row in sorted(
        generated_rows,
        key=lambda item: (
            str(item.model),
            str(item.artist_id),
            str(item.prompt_id),
            item.repetition or 0,
        ),
    ):
        prompt = prompt_by_id.get(row.prompt_id)
        if prompt is None:
            raise ValueError(f"generated feature references unknown prompt: {row.prompt_id}")
        if prompt.artist_free_control:
            continue
        if row.artist_id != prompt.target_artist_id:
            raise ValueError(f"generated feature target disagrees with {row.prompt_id}")
        generated_by_cell[(row.model, str(row.artist_id))].append(vectors[row.feature_id])

    outputs: List[AnalysisCell] = []
    feature_name = real_rows[0].feature_name
    for model in config.generation.models:
        for artist_id in sorted(artists):
            generated = generated_by_cell.get((model, artist_id), [])
            if not generated:
                raise ValueError(f"no generated {measurement} rows for {model}/{artist_id}")
            neighbor_id = artists[artist_id].neighbor_artist_id
            outputs.append(
                AnalysisCell(
                    cell_id=f"{config.pilot_id}-{measurement}-{model}-{artist_id}",
                    target_artist_id=artist_id,
                    model=model,
                    measurement=measurement,
                    feature_name=feature_name,
                    feature_version=expected_version,
                    feature_config_hash=expected_hash,
                    qualification_contract_hash=qualification_contract_hash,
                    qualification_evidence_artifact_sha256=str(
                        qualification_evidence_artifact_sha256
                    ),
                    real_feature_manifest_sha256=str(real_feature_manifest_sha256),
                    generated_feature_manifest_sha256=str(
                        generated_feature_manifest_sha256
                    ),
                    generation_manifest_sha256=str(generation_manifest_sha256),
                    generation_attestation_sha256=str(generation_attestation_sha256),
                    reference_transform_state_sha256=transform_state_sha256,
                    qualified_reference_transform_state_sha256=(
                        qualified_reference_transform_state_sha256
                    ),
                    engineering_scope="api_integration_test_only",
                    preparation_qualification_bypass=(
                        preparation_qualification_bypass
                    ),
                    target_train_vectors=[value.tolist() for value in real_train[artist_id]],
                    target_held_out_vectors=[value.tolist() for value in real_held[artist_id]],
                    generated_vectors=[value.tolist() for value in generated],
                    neighbor_vectors={
                        neighbor_id: [value.tolist() for value in real_held[neighbor_id]]
                    },
                )
            )
    return outputs
