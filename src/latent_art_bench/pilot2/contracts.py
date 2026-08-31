"""Content-addressed qualification contract and fail-closed pilot_2 gate."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from latent_art_bench.io import hash_file, read_json, read_jsonl, stable_hash
from latent_art_bench.pilot2.config import Pilot2Config
from latent_art_bench.pilot2.corpus import (
    acquired_image_manifest_sha256,
    atlas_manifest_sha256,
    validate_pilot2_acquired_images,
)
from latent_art_bench.pilot2.design import build_sample_size_sensitivity
from latent_art_bench.pilot2.generation import (
    GenerationCell,
    GenerationSchedule,
    build_generation_cells,
    build_generation_schedule,
)
from latent_art_bench.pilot2.qualification import qualification_result_sha256
from latent_art_bench.pilot2.schemas import (
    Pilot2AcquiredImage,
    Pilot2AtlasWork,
    Pilot2Feature,
    Pilot2LearnedQualificationResult,
)
from latent_art_bench.schemas import PromptRecord

_PILOT2_PROSPECTIVE_CODE = (
    "src/latent_art_bench/io.py",
    "src/latent_art_bench/config.py",
    "src/latent_art_bench/schemas.py",
    "src/latent_art_bench/features/chromatic.py",
    "src/latent_art_bench/features/learned_formal.py",
    "src/latent_art_bench/features/learned_pipeline.py",
    "src/latent_art_bench/cli.py",
    "src/latent_art_bench/pilot2/__init__.py",
    "src/latent_art_bench/pilot2/config.py",
    "src/latent_art_bench/pilot2/schemas.py",
    "src/latent_art_bench/pilot2/corpus.py",
    "src/latent_art_bench/pilot2/preprocessing.py",
    "src/latent_art_bench/pilot2/learned_formal.py",
    "src/latent_art_bench/pilot2/qualification.py",
    "src/latent_art_bench/pilot2/contracts.py",
    "src/latent_art_bench/pilot2/transport.py",
    "src/latent_art_bench/pilot2/generation.py",
    "src/latent_art_bench/pilot2/chromatic.py",
    "src/latent_art_bench/pilot2/design.py",
    "src/latent_art_bench/pilot2/analysis.py",
    "src/latent_art_bench/pilot2/reporting.py",
    "src/latent_art_bench/pilot2/cli.py",
)


def pilot2_code_closure(root: Path) -> Dict[str, str]:
    """Hash every project source file that can alter the prospective pilot run."""

    root = Path(root).resolve()
    closure: Dict[str, str] = {}
    for relative in _PILOT2_PROSPECTIVE_CODE:
        path = root / relative
        if not path.is_file():
            raise RuntimeError(f"pilot_2 code-closure file is missing: {relative}")
        closure[relative] = hash_file(path)
    return closure


def feature_manifest_sha256(rows: Sequence[Pilot2Feature]) -> str:
    return stable_hash(
        [
            row.model_dump(mode="json")
            for row in sorted(rows, key=lambda item: item.canonical_work_id)
        ]
    )


def pilot2_qualification_contract(
    config: Pilot2Config,
    root: Path,
    atlas: Sequence[Pilot2AtlasWork],
    acquired_images: Sequence[Pilot2AcquiredImage],
    features: Sequence[Pilot2Feature],
) -> Tuple[str, Dict[str, object]]:
    """Bind config, atlas, features, full prospective code, and dependency lock."""

    root = Path(root).resolve()
    candidate_path = root / config.corpus.candidate_audit
    if not candidate_path.is_file():
        raise FileNotFoundError(f"missing frozen pilot_2 candidate audit: {candidate_path}")

    def pinned_file(relative: str, expected: Optional[str], label: str) -> str:
        if expected is None:
            raise RuntimeError(f"pilot_2 config lacks the {label} SHA-256 pin")
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"missing pinned pilot_2 {label}: {path}")
        observed = hash_file(path)
        if observed != expected:
            raise RuntimeError(
                f"pilot_2 {label} SHA-256 mismatch: expected {expected}, found {observed}"
            )
        return observed

    pinned_artifacts = {
        "protocol_document": pinned_file(
            config.protocol_document,
            config.protocol_document_sha256,
            "protocol document",
        ),
        "atlas_manifest": pinned_file(
            config.corpus.atlas_manifest,
            config.corpus.atlas_manifest_sha256,
            "atlas manifest",
        ),
        "real_image_manifest": pinned_file(
            config.corpus.real_image_manifest,
            config.corpus.real_image_manifest_sha256,
            "real-image manifest",
        ),
        "prompt_manifest": pinned_file(
            config.generation.prompt_manifest,
            config.generation.prompt_manifest_sha256,
            "prompt manifest",
        ),
        "generation_cells_manifest": pinned_file(
            config.generation.generation_cells_manifest,
            config.generation.generation_cells_manifest_sha256,
            "generation-cells manifest",
        ),
        "generation_schedule": pinned_file(
            config.generation.generation_schedule,
            config.generation.generation_schedule_sha256,
            "generation schedule",
        ),
        "sample_size_sensitivity": pinned_file(
            config.design.sensitivity_artifact,
            config.design.sensitivity_artifact_sha256,
            "sample-size sensitivity",
        ),
        "transport_fingerprint": pinned_file(
            config.generation.transport_fingerprint,
            config.generation.transport_fingerprint_sha256,
            "transport fingerprint",
        ),
        "transport_source_snapshot": pinned_file(
            config.generation.transport_source_snapshot,
            config.generation.transport_source_snapshot_sha256,
            "transport source snapshot",
        ),
        "model_verification_report": pinned_file(
            config.learned_formal.model_verification_report,
            config.learned_formal.model_verification_report_sha256,
            "VAE model verification report",
        ),
    }
    persisted_atlas = [
        Pilot2AtlasWork.model_validate(row)
        for row in read_jsonl(root / config.corpus.atlas_manifest)
    ]
    if atlas_manifest_sha256(persisted_atlas) != atlas_manifest_sha256(atlas):
        raise RuntimeError("in-memory atlas disagrees with its pinned manifest")
    persisted_acquired = [
        Pilot2AcquiredImage.model_validate(row)
        for row in read_jsonl(root / config.corpus.real_image_manifest)
    ]
    if acquired_image_manifest_sha256(
        persisted_acquired
    ) != acquired_image_manifest_sha256(acquired_images):
        raise RuntimeError("in-memory acquired images disagree with their pinned manifest")
    validate_pilot2_acquired_images(acquired_images, atlas, root=root)

    prompts = [
        PromptRecord.model_validate(row)
        for row in read_jsonl(root / config.generation.prompt_manifest)
    ]
    expected_cells = build_generation_cells(
        prompts, repetitions=config.generation.repetitions
    )
    persisted_cells = [
        GenerationCell.model_validate(row)
        for row in read_jsonl(root / config.generation.generation_cells_manifest)
    ]
    if [row.model_dump(mode="json") for row in persisted_cells] != [
        row.model_dump(mode="json") for row in expected_cells
    ]:
        raise RuntimeError(
            "persisted generation cells disagree with the frozen prompt expansion"
        )
    expected_schedule = build_generation_schedule(expected_cells)
    persisted_schedule = GenerationSchedule.model_validate(
        read_json(root / config.generation.generation_schedule)
    )
    if persisted_schedule.model_dump(mode="json") != expected_schedule.model_dump(
        mode="json"
    ):
        raise RuntimeError(
            "persisted generation schedule disagrees with the frozen cell schedule"
        )
    persisted_design = read_json(root / config.design.sensitivity_artifact)
    expected_design = build_sample_size_sensitivity(
        draws=config.design.simulation_draws,
        seed=config.design.simulation_seed,
    )
    if persisted_design != expected_design:
        raise RuntimeError(
            "persisted sample-size sensitivity disagrees with the frozen design"
        )
    closure = pilot2_code_closure(root)
    payload: Dict[str, object] = {
        "schema_version": "2.0",
        "pilot_id": "pilot_2",
        "measurement": "learned_formal",
        "resolved_config": config.model_dump(mode="json"),
        "resolved_config_sha256": config.content_hash(),
        "candidate_audit_path": config.corpus.candidate_audit,
        "candidate_audit_sha256": hash_file(candidate_path),
        "atlas_manifest_sha256": atlas_manifest_sha256(atlas),
        "acquired_image_manifest_sha256": acquired_image_manifest_sha256(
            acquired_images
        ),
        "feature_manifest_sha256": feature_manifest_sha256(features),
        "pinned_artifact_sha256": pinned_artifacts,
        "full_checkpoint_sha256": config.learned_formal.full_checkpoint_sha256,
        "qualification_code_closure": closure,
        "qualification_implementation_sha256": stable_hash(closure),
        "dependency_lock_sha256": hash_file(root / "uv.lock"),
        "project_configuration_sha256": hash_file(root / "pyproject.toml"),
    }
    return stable_hash(payload), payload


def pilot2_generation_gate(
    result: Pilot2LearnedQualificationResult,
    config: Pilot2Config,
    *,
    expected_contract_sha256: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """Unlock only for the exact primary result; chromatic is non-gating."""

    reasons: List[str] = []
    expected_feature_hash = stable_hash(config.learned_formal.model_dump(mode="json"))
    if result.status != "pass":
        reasons.append("learned_formal_status_is_not_pass")
    if not result.checks or not all(result.checks.values()):
        reasons.append("learned_formal_required_checks_did_not_all_pass")
    if result.measurement != "learned_formal":
        reasons.append("unexpected_primary_measurement")
    if result.feature_version != config.learned_formal.feature_version:
        reasons.append("feature_version_mismatch")
    if result.feature_config_sha256 != expected_feature_hash:
        reasons.append("feature_config_mismatch")
    if result.qualification_config_sha256 != expected_feature_hash:
        reasons.append("qualification_config_mismatch")
    if result.result_sha256 != qualification_result_sha256(result):
        reasons.append("qualification_result_self_hash_is_stale")
    if result.qualification_contract_sha256 is None:
        reasons.append("qualification_contract_is_missing")
    if expected_contract_sha256 is None:
        reasons.append("expected_qualification_contract_was_not_supplied")
    elif result.qualification_contract_sha256 != expected_contract_sha256:
        reasons.append("qualification_contract_mismatch")
    return not reasons, reasons


def require_pilot2_generation_gate(
    result: Pilot2LearnedQualificationResult,
    config: Pilot2Config,
    *,
    expected_contract_sha256: Optional[str] = None,
) -> None:
    allowed, reasons = pilot2_generation_gate(
        result,
        config,
        expected_contract_sha256=expected_contract_sha256,
    )
    if not allowed:
        raise RuntimeError("pilot_2 generation is locked: " + ", ".join(reasons))
