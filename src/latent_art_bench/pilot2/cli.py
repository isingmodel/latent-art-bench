"""Reproducible, fail-closed orchestration for the prospective pilot_2 study.

Only the ``conform`` and ``generate`` commands can send image requests.  Both
require the explicit ``--execute`` flag, a current qualification contract, and
the pinned localhost OAuth runtime.  Every other command is offline.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Type, TypeVar

import numpy as np
import typer
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from latent_art_bench.features.learned_formal import learned_formal_vector_sha256
from latent_art_bench.features.learned_pipeline import load_configured_vae
from latent_art_bench.io import (
    canonical_json,
    hash_bytes,
    hash_file,
    read_json,
    read_jsonl,
    stable_hash,
    write_json,
    write_jsonl,
)
from latent_art_bench.pilot2.analysis import (
    Pilot2AnalysisBindings,
    Pilot2AnalysisResult,
    Pilot2ChromaticSecondaryResult,
    Pilot2ProjectedAnalysisInputs,
    analyze_projected_pilot2,
    assemble_generation_analysis_rows,
    grid_spec_from_config,
    prepare_projected_analysis_inputs,
    summarize_chromatic_secondary,
)
from latent_art_bench.pilot2.chromatic import (
    Pilot2ChromaticFeature,
    extract_chromatic_secondary,
    formula_probe_evidence,
)
from latent_art_bench.pilot2.config import Pilot2Config, load_pilot2_config
from latent_art_bench.pilot2.contracts import (
    pilot2_generation_gate,
    pilot2_qualification_contract,
    require_pilot2_generation_gate,
)
from latent_art_bench.pilot2.corpus import (
    build_pilot2_atlas,
    validate_pilot2_acquired_images,
    validate_pilot2_atlas,
)
from latent_art_bench.pilot2.design import build_sample_size_sensitivity
from latent_art_bench.pilot2.generation import (
    AppendOnlyAttemptLedger,
    AppendOnlyPostIntentLedger,
    AppendOnlyRuntimeRevalidationLedger,
    GenerationAttempt,
    GenerationCell,
    GenerationSchedule,
    TerminalGenerationRecord,
    TransportConformanceFailure,
    build_generation_cells,
    build_generation_schedule,
    generation_attempt_ledger_semantic_sha256,
    generation_completion_report,
    generation_grid_sha256,
    post_intent_ledger_semantic_sha256,
    run_generation_grid,
    run_transport_conformance,
    runtime_revalidation_ledger_semantic_sha256,
    select_conformance_cells,
    terminal_records_for_analysis,
    terminal_records_manifest_sha256,
    verified_attempt_receipt_manifest,
    verify_generation_runtime_revalidation_ledger,
    verify_post_intent_attempt_bijection,
    verify_successful_output_artifacts,
    verify_transport_conformance,
)
from latent_art_bench.pilot2.learned_formal import (
    build_determinism_probe,
    extract_harmonized_learned_formal,
    feature_from_extraction,
    fit_train_only_pca,
)
from latent_art_bench.pilot2.preprocessing import (
    preprocess_acquired_image,
    preprocess_common_png,
)
from latent_art_bench.pilot2.qualification import (
    qualification_card_from_result,
    qualification_result_sha256,
    qualify_learned_formal,
)
from latent_art_bench.pilot2.reporting import (
    Pilot2ArtifactIndex,
    artifact_index_data,
    write_pilot2_report,
)
from latent_art_bench.pilot2.schemas import (
    Pilot2AcquiredImage,
    Pilot2AtlasWork,
    Pilot2DerivedInput,
    Pilot2DeterminismProbe,
    Pilot2Feature,
    Pilot2LearnedQualificationResult,
    Pilot2QualificationCard,
)
from latent_art_bench.pilot2.transport import (
    OAuthRuntimeFingerprint,
    OAuthRuntimeRevalidation,
    OAuthSourceSnapshot,
    OAuthTransportConfig,
    Pilot2OAuthTransport,
    verify_oauth_runtime_fingerprint,
    verify_oauth_source_snapshot,
)
from latent_art_bench.schemas import PromptRecord

app = typer.Typer(
    name="pilot2",
    no_args_is_help=True,
    help="Run the frozen pilot_2 requested-label study through local openai-oauth.",
)

DEFAULT_CONFIG = Path("configs/pilot_2/pilot.yaml")
DEFAULT_REAL_DERIVED = Path("artifacts/pilot_2/real_derived_inputs.jsonl")
DEFAULT_REAL_FEATURES = Path("artifacts/pilot_2/real_learned_features.jsonl")
DEFAULT_REAL_CHROMATIC = Path("artifacts/pilot_2/real_chromatic_features.jsonl")
DEFAULT_DETERMINISM = Path("artifacts/pilot_2/determinism_probes.jsonl")
DEFAULT_QUALIFICATION_CONTRACT = Path("reports/pilot_2/evidence/qualification_contract.json")
DEFAULT_GENERATION_GATE = Path("reports/pilot_2/evidence/generation_gate.json")
DEFAULT_CHROMATIC_FORMULA_PROBES = Path("reports/pilot_2/evidence/chromatic_formula_probes.json")
DEFAULT_ATTEMPT_LEDGER = Path("artifacts/pilot_2/generation_attempts.jsonl")
DEFAULT_CONFORMANCE = Path("reports/pilot_2/evidence/transport_conformance.json")
DEFAULT_COMPLETION = Path("reports/pilot_2/evidence/generation_completion.json")
DEFAULT_TERMINAL_RECORDS = Path("artifacts/pilot_2/generation_terminal.jsonl")
DEFAULT_SUCCESSFUL_OUTPUT_MANIFEST = Path(
    "reports/pilot_2/evidence/successful_output_manifest.json"
)
DEFAULT_GENERATED_DERIVED = Path("artifacts/pilot_2/generated_derived_inputs.jsonl")
DEFAULT_GENERATED_FEATURES = Path("artifacts/pilot_2/generated_learned_features.jsonl")
DEFAULT_GENERATED_CHROMATIC = Path("artifacts/pilot_2/generated_chromatic_features.jsonl")
DEFAULT_PROJECTED_INPUTS = Path("reports/pilot_2/evidence/projected_analysis_inputs.json")
DEFAULT_ANALYSIS = Path("reports/pilot_2/analysis.json")
DEFAULT_CHROMATIC_ANALYSIS = Path("reports/pilot_2/chromatic_secondary.json")
DEFAULT_REPORT_DIR = Path("reports/pilot_2")

T = TypeVar("T", bound=BaseModel)


@dataclass(frozen=True)
class Pilot2Context:
    root: Path
    config_path: Path
    config: Pilot2Config

    def resolve(self, value: str | Path) -> Path:
        path = Path(value).expanduser()
        return path.resolve() if path.is_absolute() else (self.root / path).resolve()


class GeneratedLearnedFeature(BaseModel):
    """Raw generated A-vector with complete transport/preprocessing bindings."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    record_type: str = "pilot2_generated_learned_feature"
    schema_version: str = "2.0"
    feature_id: str
    cell_id: str
    generation_cell_identity_sha256: str
    prompt_id: str
    content_id: str
    requested_model_label: str
    repetition: int
    target_artist_id: Optional[str] = None
    artist_free_control: bool
    source_output_sha256: str
    derived_png_sha256: str
    feature_version: str
    feature_config_sha256: str
    vector_sha256: str
    vector: List[float]
    extraction_metadata: Dict[str, Any]
    status: str = "ok"

    @field_validator(
        "generation_cell_identity_sha256",
        "source_output_sha256",
        "derived_png_sha256",
        "feature_config_sha256",
        "vector_sha256",
    )
    @classmethod
    def valid_hash(cls, value: str) -> str:
        if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
            raise ValueError("generated feature identities must be lowercase SHA-256 values")
        return value

    @model_validator(mode="after")
    def coherent_feature(self) -> "GeneratedLearnedFeature":
        if self.record_type != "pilot2_generated_learned_feature" or self.schema_version != "2.0":
            raise ValueError("generated feature schema identity is stale")
        if self.status != "ok":
            raise ValueError("generated feature manifests contain successful rows only")
        if not self.vector or any(not math.isfinite(value) for value in self.vector):
            raise ValueError("generated feature vectors must be finite and non-empty")
        if learned_formal_vector_sha256(self.vector) != self.vector_sha256:
            raise ValueError("generated feature vector hash is stale")
        if self.artist_free_control != (self.target_artist_id is None):
            raise ValueError("generated feature target/control identity is inconsistent")
        payload = _generated_feature_identity_payload(self)
        if self.feature_id != f"pilot2-generated-feature-{stable_hash(payload)[:24]}":
            raise ValueError("generated feature id does not bind its extraction inputs")
        return self


def _generated_feature_identity_payload(
    value: GeneratedLearnedFeature | Mapping[str, Any],
) -> Dict[str, Any]:
    payload = value.model_dump(mode="json") if isinstance(value, BaseModel) else dict(value)
    payload.pop("feature_id", None)
    payload.pop("record_type", None)
    payload.pop("schema_version", None)
    payload.pop("vector", None)
    payload.pop("status", None)
    return payload


def _context(root: Path, config_path: Path) -> Pilot2Context:
    resolved_root = Path(root).expanduser().resolve()
    resolved_config = Path(config_path).expanduser()
    if not resolved_config.is_absolute():
        resolved_config = resolved_root / resolved_config
    if not resolved_config.is_file():
        raise FileNotFoundError(f"missing pilot_2 config: {resolved_config}")
    return Pilot2Context(
        root=resolved_root,
        config_path=resolved_config.resolve(),
        config=load_pilot2_config(resolved_config),
    )


def _load_models(path: Path, model: Type[T]) -> List[T]:
    if not path.is_file():
        raise FileNotFoundError(path)
    return [model.model_validate(row) for row in read_jsonl(path)]


def _relative(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _require_file_hash(path: Path, expected: Optional[str], label: str) -> str:
    if expected is None:
        raise RuntimeError(f"pilot_2 config lacks the {label} SHA-256 pin")
    if not path.is_file():
        raise FileNotFoundError(f"missing pinned {label}: {path}")
    observed = hash_file(path)
    if observed != expected:
        raise RuntimeError(f"{label} SHA-256 mismatch: expected {expected}, found {observed}")
    return observed


def _preprocessing_config_sha256(config: Pilot2Config) -> str:
    return stable_hash(config.preprocessing.model_dump(mode="json"))


def _validate_derived_preprocessing(
    rows: Sequence[Pilot2DerivedInput],
    config: Pilot2Config,
    *,
    label: str,
) -> None:
    expected = _preprocessing_config_sha256(config)
    stale: List[str] = []
    for row in rows:
        identity = stable_hash(
            {
                "source_record_id": row.source_record_id,
                "source_sha256": row.source_sha256,
                "output_sha256": row.output_sha256,
                "preprocessing_config_sha256": row.preprocessing_config_sha256,
            }
        )
        if (
            row.preprocessing_config_sha256 != expected
            or row.derived_input_id != f"pilot2-input-{identity[:24]}"
        ):
            stale.append(row.source_record_id)
    if stale:
        raise ValueError(
            f"{label} derived inputs use a non-frozen preprocessing config: "
            + ", ".join(sorted(stale))
        )


def _expected_extraction_metadata(
    config: Pilot2Config, derived: Pilot2DerivedInput
) -> Dict[str, Any]:
    """Exact generated A-vector metadata inherited from the qualified extractor."""

    return {
        "feature_version": config.learned_formal.feature_version,
        "pilot2_representation_role": "harmonized_png_seeded_a_vector",
        "upstream_extractor_feature_version": (
            "kim2026-sd20-a-vector-source-file-seeded-sample-v2"
        ),
        "representation_role": "source_replication_seeded_posterior_sample",
        "policy": "seeded_posterior_sample",
        "seed_strategy": "sha256_of_resized_rgb_plus_base_seed",
        "base_seed": config.learned_formal.base_seed,
        "source_input_role": "original_reproduction_file",
        "source_preprocessing_policy": (
            "opencv_imread_resize_imwrite_same_extension_then_pillow_rgb"
        ),
        "source_file_sha256": derived.output_sha256,
        "source_extension": ".png",
        "intermediate_encoding": "png",
        "common_derived_png_sha256": derived.output_sha256,
        "acquired_source_sha256": derived.source_sha256,
        "acquired_source_record_id": derived.source_record_id,
        "acquired_source_width": derived.source_width,
        "acquired_source_height": derived.source_height,
        "acquired_source_decoded_format": derived.source_decoded_format,
        "common_preprocessing_config_sha256": _preprocessing_config_sha256(config),
        "input_size": [512, 512],
        "input_color_order": "RGB",
        "input_tensor_range": [-1.0, 1.0],
        "resize_library": "opencv",
        "resize_interpolation": "INTER_LANCZOS4",
        "latent_shape": [4, 64, 64],
        "latent_scale": 0.18215,
        "latent_scale_application": "explicit_after_encode",
        "flatten_order": "C",
        "vector_length": config.learned_formal.raw_dimension,
        "dtype": "float32",
        "source_repository": config.learned_formal.source_repository,
        "source_revision": config.learned_formal.source_revision,
        "model_repository": config.learned_formal.model_repository,
        "model_revision": config.learned_formal.model_revision,
        "config_sha256": config.learned_formal.model_config_sha256,
        "weights_sha256": config.learned_formal.model_weights_sha256,
        "device": config.learned_formal.device,
        "opencv_version": config.learned_formal.opencv_version,
        "opencv_build_sha256": config.learned_formal.opencv_build_sha256,
        "pillow_version": config.learned_formal.pillow_version,
        "jpeg_codec_version": config.learned_formal.jpeg_codec_version,
        "python_version": config.learned_formal.python_version,
        "platform_system": config.learned_formal.platform_system,
        "platform_release": config.learned_formal.platform_release,
        "platform_machine": config.learned_formal.platform_machine,
        "numpy_version": config.learned_formal.numpy_version,
        "torch_version": config.learned_formal.torch_version,
        "diffusers_version": config.learned_formal.diffusers_version,
        "torch_mps_built": config.learned_formal.torch_mps_built,
        "torch_mps_available": config.learned_formal.torch_mps_available,
        "source_checkout_verified": True,
        "artifacts_verified": True,
    }


def _validate_generated_extraction_provenance(
    feature: GeneratedLearnedFeature,
    derived: Pilot2DerivedInput,
    config: Pilot2Config,
) -> None:
    metadata = feature.extraction_metadata
    expected = _expected_extraction_metadata(config, derived)
    mismatches = [
        key for key, expected_value in expected.items() if metadata.get(key) != expected_value
    ]
    for key in ("seed_basis_sha256", "intermediate_payload_sha256"):
        value = metadata.get(key)
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            mismatches.append(key)
    if metadata.get("vector_sha256") != feature.vector_sha256:
        mismatches.append("vector_sha256")
    seed_basis = metadata.get("seed_basis_sha256")
    if isinstance(seed_basis, str) and len(seed_basis) == 64:
        seed_digest = hashlib.sha256()
        seed_digest.update(b"latent-art-bench:kim2026-a-vector-seed:v1\0")
        seed_digest.update(config.learned_formal.base_seed.to_bytes(8, "big"))
        try:
            seed_digest.update(bytes.fromhex(seed_basis))
            expected_seed = int.from_bytes(seed_digest.digest()[:8], "big") & ((1 << 63) - 1)
        except ValueError:
            expected_seed = None
        if metadata.get("seed") != expected_seed:
            mismatches.append("seed")
    if mismatches:
        raise ValueError(
            f"generated extraction provenance is stale for {feature.cell_id}: "
            + ", ".join(sorted(set(mismatches)))
        )


def _json_bytes(value: Any) -> bytes:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return (
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True, default=str) + "\n"
    ).encode("utf-8")


def _jsonl_bytes(rows: Iterable[Any]) -> bytes:
    lines: List[str] = []
    for row in rows:
        if isinstance(row, BaseModel):
            row = row.model_dump(mode="json")
        lines.append(canonical_json(row))
    return ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8")


def _assert_rendered_pin(payload: bytes, expected: Optional[str], label: str) -> str:
    observed = hash_bytes(payload)
    if expected is not None and observed != expected:
        raise RuntimeError(
            f"prospective {label} bytes disagree with config pin: "
            f"expected {expected}, found {observed}"
        )
    return observed


def _load_atlas(ctx: Pilot2Context, *, require_pin: bool = True) -> List[Pilot2AtlasWork]:
    path = ctx.resolve(ctx.config.corpus.atlas_manifest)
    if require_pin:
        _require_file_hash(path, ctx.config.corpus.atlas_manifest_sha256, "atlas manifest")
    rows = _load_models(path, Pilot2AtlasWork)
    validate_pilot2_atlas(rows, ctx.config.corpus)
    return rows


def _load_acquired(
    ctx: Pilot2Context,
    atlas: Sequence[Pilot2AtlasWork],
    *,
    require_pin: bool = True,
) -> List[Pilot2AcquiredImage]:
    path = ctx.resolve(ctx.config.corpus.real_image_manifest)
    if require_pin:
        _require_file_hash(
            path,
            ctx.config.corpus.real_image_manifest_sha256,
            "real-image manifest",
        )
    rows = _load_models(path, Pilot2AcquiredImage)
    validate_pilot2_acquired_images(rows, atlas, root=ctx.root)
    return rows


def _load_prompts(ctx: Pilot2Context, *, require_pin: bool = True) -> List[PromptRecord]:
    path = ctx.resolve(ctx.config.generation.prompt_manifest)
    if require_pin:
        _require_file_hash(
            path,
            ctx.config.generation.prompt_manifest_sha256,
            "prompt manifest",
        )
    rows = _load_models(path, PromptRecord)
    if len(rows) != 40 or any(row.test_only for row in rows):
        raise ValueError("pilot_2 requires exactly 40 non-test frozen prompts")
    grid_spec_from_config(ctx.config, prompt_records=rows)
    return rows


def _load_generation_plan(
    ctx: Pilot2Context,
    prompts: Optional[Sequence[PromptRecord]] = None,
    *,
    require_pins: bool = True,
) -> tuple[List[GenerationCell], GenerationSchedule]:
    prompt_rows = list(prompts) if prompts is not None else _load_prompts(ctx)
    cell_path = ctx.resolve(ctx.config.generation.generation_cells_manifest)
    schedule_path = ctx.resolve(ctx.config.generation.generation_schedule)
    if require_pins:
        _require_file_hash(
            cell_path,
            ctx.config.generation.generation_cells_manifest_sha256,
            "generation-cells manifest",
        )
        _require_file_hash(
            schedule_path,
            ctx.config.generation.generation_schedule_sha256,
            "generation schedule",
        )
    cells = _load_models(cell_path, GenerationCell)
    schedule = GenerationSchedule.model_validate(read_json(schedule_path))
    expected_cells = build_generation_cells(
        prompt_rows, repetitions=ctx.config.generation.repetitions
    )
    expected_schedule = build_generation_schedule(expected_cells)
    if [row.model_dump(mode="json") for row in cells] != [
        row.model_dump(mode="json") for row in expected_cells
    ]:
        raise RuntimeError("generation cells disagree with the frozen prompt expansion")
    if schedule.model_dump(mode="json") != expected_schedule.model_dump(mode="json"):
        raise RuntimeError("generation schedule disagrees with the frozen schedule")
    if len(cells) != ctx.config.generation.logical_cell_count:
        raise RuntimeError("generation plan is not the exact configured 320-cell grid")
    return cells, schedule


def _validate_static_manifests(ctx: Pilot2Context, *, require_plan: bool = True) -> Dict[str, Any]:
    config = ctx.config
    _require_file_hash(
        ctx.resolve(config.protocol_document),
        config.protocol_document_sha256,
        "protocol document",
    )
    _require_file_hash(
        ctx.resolve(config.learned_formal.model_verification_report),
        config.learned_formal.model_verification_report_sha256,
        "VAE model-verification report",
    )
    atlas = _load_atlas(ctx)
    expected_atlas = build_pilot2_atlas(ctx.resolve(config.corpus.candidate_audit), config.corpus)
    if [row.model_dump(mode="json") for row in atlas] != [
        row.model_dump(mode="json") for row in expected_atlas
    ]:
        raise RuntimeError("persisted atlas is not the deterministic candidate selection")
    acquired = _load_acquired(ctx, atlas)
    prompts = _load_prompts(ctx)
    design_path, design = _validate_design_sensitivity(ctx)
    formula_path = ctx.resolve(DEFAULT_CHROMATIC_FORMULA_PROBES)
    formula = formula_probe_evidence()
    if read_json(formula_path) != formula:
        raise RuntimeError("chromatic formula-probe evidence is stale")
    cells: List[GenerationCell] = []
    schedule: Optional[GenerationSchedule] = None
    if require_plan:
        cells, schedule = _load_generation_plan(ctx, prompts)

    fingerprint_path = ctx.resolve(config.generation.transport_fingerprint)
    source_path = ctx.resolve(config.generation.transport_source_snapshot)
    _require_file_hash(
        fingerprint_path,
        config.generation.transport_fingerprint_sha256,
        "OAuth runtime fingerprint",
    )
    _require_file_hash(
        source_path,
        config.generation.transport_source_snapshot_sha256,
        "OAuth source snapshot",
    )
    fingerprint = OAuthRuntimeFingerprint.model_validate(read_json(fingerprint_path))
    source = OAuthSourceSnapshot.model_validate(read_json(source_path))
    verify_oauth_runtime_fingerprint(fingerprint)
    verify_oauth_source_snapshot(source)
    if source.model_dump(mode="json") != fingerprint.source.model_dump(mode="json"):
        raise RuntimeError("standalone OAuth source snapshot disagrees with the fingerprint")
    if fingerprint.endpoint_url != f"{config.generation.base_url}/images/generations":
        raise RuntimeError("OAuth fingerprint endpoint disagrees with pilot_2 config")
    return {
        "status": "pass",
        "atlas_work_count": len(atlas),
        "acquired_image_count": len(acquired),
        "prompt_count": len(prompts),
        "generation_cell_count": len(cells) if require_plan else None,
        "generation_schedule_sha256": schedule.schedule_sha256 if schedule else None,
        "sample_size_sensitivity_file_sha256": hash_file(design_path),
        "sample_size_sensitivity_sha256": design["evidence_sha256"],
        "chromatic_formula_probes_sha256": formula["evidence_sha256"],
        "oauth_runtime_fingerprint_sha256": fingerprint.fingerprint_sha256,
        "executed_model_claims": False,
    }


def _real_inputs(
    ctx: Pilot2Context,
    *,
    derived_path: Path = DEFAULT_REAL_DERIVED,
    feature_path: Path = DEFAULT_REAL_FEATURES,
    probe_path: Path = DEFAULT_DETERMINISM,
) -> tuple[
    List[Pilot2AtlasWork],
    List[Pilot2AcquiredImage],
    List[Pilot2DerivedInput],
    List[Pilot2Feature],
    List[Pilot2DeterminismProbe],
]:
    atlas = _load_atlas(ctx)
    acquired = _load_acquired(ctx, atlas)
    derived = _load_models(ctx.resolve(derived_path), Pilot2DerivedInput)
    _validate_derived_preprocessing(derived, ctx.config, label="real")
    features = _load_models(ctx.resolve(feature_path), Pilot2Feature)
    probes = _load_models(ctx.resolve(probe_path), Pilot2DeterminismProbe)
    if len(derived) != 40 or {row.source_record_id for row in derived} != {
        row.canonical_work_id for row in atlas
    }:
        raise ValueError("real derived inputs do not cover the exact 40-work atlas")
    for row in derived:
        path = Path(row.output_path)
        if not path.is_absolute():
            path = ctx.root / path
        if not path.is_file() or hash_file(path) != row.output_sha256:
            raise RuntimeError(f"real derived PNG is missing or stale: {row.source_record_id}")
    return atlas, acquired, derived, features, probes


def _qualification_context(
    ctx: Pilot2Context,
    *,
    require_gate: bool,
) -> tuple[Pilot2LearnedQualificationResult, str, Dict[str, Any]]:
    atlas, acquired, _, features, _ = _real_inputs(ctx)
    contract_sha, contract = pilot2_qualification_contract(
        ctx.config, ctx.root, atlas, acquired, features
    )
    contract_path = ctx.resolve(DEFAULT_QUALIFICATION_CONTRACT)
    if not contract_path.is_file() or read_json(contract_path) != contract:
        raise RuntimeError("persisted qualification contract is missing or stale")
    result_path = ctx.resolve(ctx.config.qualification_artifacts.learned_result)
    result = Pilot2LearnedQualificationResult.model_validate(read_json(result_path))
    if result.result_sha256 != qualification_result_sha256(result):
        raise RuntimeError("qualification result self-hash is stale")
    if result.qualification_contract_sha256 != contract_sha:
        raise RuntimeError("qualification result binds a stale contract")
    allowed, reasons = pilot2_generation_gate(
        result, ctx.config, expected_contract_sha256=contract_sha
    )
    gate_payload: Dict[str, Any] = {
        "record_type": "pilot2_generation_gate",
        "schema_version": "2.0",
        "status": "pass" if allowed else "fail",
        "pilot2_config_sha256": ctx.config.content_hash(),
        "qualification_result_sha256": result.result_sha256,
        "qualification_contract_sha256": contract_sha,
        "reasons": reasons,
        "chromatic_can_open_or_close_gate": False,
    }
    gate_payload["gate_sha256"] = stable_hash(gate_payload)
    gate_path = ctx.resolve(DEFAULT_GENERATION_GATE)
    if require_gate:
        if not gate_path.is_file() or read_json(gate_path) != gate_payload:
            raise RuntimeError("persisted generation-gate artifact is missing or stale")
        require_pilot2_generation_gate(result, ctx.config, expected_contract_sha256=contract_sha)
    return result, contract_sha, gate_payload


def _load_runtime(ctx: Pilot2Context) -> tuple[OAuthTransportConfig, OAuthRuntimeFingerprint]:
    _validate_static_manifests(ctx, require_plan=True)
    _qualification_context(ctx, require_gate=True)
    fingerprint_path = ctx.resolve(ctx.config.generation.transport_fingerprint)
    fingerprint = OAuthRuntimeFingerprint.model_validate(read_json(fingerprint_path))
    checkout = (Path.home() / "dev" / "openai-oauth").resolve()
    transport_config = OAuthTransportConfig(
        base_url=ctx.config.generation.base_url,
        checkout_path=checkout,
        required_checkout_path=checkout,
        timeout_seconds=ctx.config.generation.timeout_seconds,
    )
    if transport_config.endpoint_url != fingerprint.endpoint_url:
        raise RuntimeError("configured transport endpoint disagrees with fingerprint")
    return transport_config, fingerprint


def _self_hashed_json(path: Path, field: str) -> Dict[str, Any]:
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise ValueError(f"expected a JSON object: {path}")
    recorded = payload.get(field)
    if not isinstance(recorded, str):
        raise ValueError(f"{path} lacks {field}")
    unsigned = {key: value for key, value in payload.items() if key != field}
    if stable_hash(unsigned) != recorded:
        raise ValueError(f"{path} has a stale {field}")
    return payload


def _validate_design_sensitivity(ctx: Pilot2Context) -> tuple[Path, Dict[str, Any]]:
    """Recompute the pinned prospective design evidence instead of trusting bytes."""

    path = ctx.resolve(ctx.config.design.sensitivity_artifact)
    _require_file_hash(
        path,
        ctx.config.design.sensitivity_artifact_sha256,
        "sample-size sensitivity artifact",
    )
    expected = build_sample_size_sensitivity(
        draws=ctx.config.design.simulation_draws,
        seed=ctx.config.design.simulation_seed,
    )
    persisted = read_json(path)
    if persisted != expected:
        raise RuntimeError(
            "sample-size sensitivity artifact is not the deterministic frozen design"
        )
    if (
        persisted.get("design_version") != ctx.config.design.design_version
        or persisted.get("frozen_design", {}).get("content_block_count")
        != ctx.config.design.top_level_block_count
        or persisted.get("frozen_design", {}).get("repetitions_per_block")
        != ctx.config.design.repetitions_per_block
        or persisted.get("simulation", {}).get("standardized_effect_grid")
        != ctx.config.design.standardized_effects
    ):
        raise RuntimeError("sample-size sensitivity artifact disagrees with config")
    return path, expected


def _validate_embedded_schedule(
    completion: Mapping[str, Any],
    schedule: GenerationSchedule,
    *,
    expected_max_parallel: int,
) -> None:
    """Require the executed envelope to contain the exact prospective schedule."""

    if expected_max_parallel != 4 or schedule.max_parallel != 4:
        raise RuntimeError("pilot_2 execution requires frozen max_parallel=4")
    if completion.get("max_parallel") != expected_max_parallel:
        raise RuntimeError("completion evidence records a non-frozen parallelism")
    if completion.get("generation_schedule_sha256") != schedule.schedule_sha256:
        raise RuntimeError("completion evidence binds a different schedule identity")
    if completion.get("generation_schedule") != schedule.model_dump(mode="json"):
        raise RuntimeError("completion evidence embeds a different generation schedule")


def _validate_execution_envelope(
    completion: Mapping[str, Any],
    *,
    cells: Sequence[GenerationCell],
    attempts: Sequence[GenerationAttempt],
    schedule: GenerationSchedule,
    post_intent_ledger_path: Path,
    runtime_ledger_path: Path,
    base_completion: Mapping[str, Any],
    base_conformance: Mapping[str, Any],
    fingerprint: OAuthRuntimeFingerprint,
    expected_max_parallel: int,
) -> OAuthRuntimeRevalidation:
    """Bind the enriched completion record to ledger, schedule, and OAuth runtime."""

    if completion.get("completion_report_without_conformance_sha256") != base_completion.get(
        "report_sha256"
    ) or any(
        completion.get(key) != value
        for key, value in base_completion.items()
        if key != "report_sha256"
    ):
        raise RuntimeError("completion evidence disagrees with the immutable attempt ledger")
    _validate_embedded_schedule(completion, schedule, expected_max_parallel=expected_max_parallel)
    if completion.get("transport_conformance") != dict(base_conformance):
        raise RuntimeError("completion embeds stale transport-conformance evidence")

    post_intent_ledger_path = post_intent_ledger_path.resolve()
    post_intents = AppendOnlyPostIntentLedger(post_intent_ledger_path).rows()
    verify_post_intent_attempt_bijection(post_intents, attempts, cells)
    if (
        completion.get("post_intent_count") != len(post_intents)
        or completion.get("post_intent_ledger_semantic_sha256")
        != post_intent_ledger_semantic_sha256(post_intents)
        or completion.get("post_intent_ledger_file_sha256") != hash_file(post_intent_ledger_path)
        or Path(str(completion.get("post_intent_ledger_path"))).resolve() != post_intent_ledger_path
    ):
        raise RuntimeError("completion post-intent ledger is stale")

    runtime_ledger_path = runtime_ledger_path.resolve()
    runtime_records = AppendOnlyRuntimeRevalidationLedger(runtime_ledger_path).rows()
    verify_generation_runtime_revalidation_ledger(
        runtime_records,
        attempts,
        cells,
        schedule,
        require_completed_generation=True,
    )
    raw_records = [record.model_dump(mode="json") for record in runtime_records]
    if (
        completion.get("oauth_runtime_revalidation_records") != raw_records
        or completion.get("oauth_runtime_revalidation_count") != len(raw_records)
        or completion.get("oauth_runtime_revalidation_records_sha256") != stable_hash(raw_records)
        or completion.get("oauth_runtime_revalidation_ledger_semantic_sha256")
        != runtime_revalidation_ledger_semantic_sha256(runtime_records)
        or completion.get("oauth_runtime_revalidation_ledger_file_sha256")
        != hash_file(runtime_ledger_path)
        or Path(str(completion.get("oauth_runtime_revalidation_ledger_path"))).resolve()
        != runtime_ledger_path
    ):
        raise RuntimeError("completion OAuth runtime revalidation ledger is stale")

    invocation_id = completion.get("current_execution_invocation_id")
    if not isinstance(invocation_id, str) or not invocation_id:
        raise RuntimeError("completion lacks its execution invocation identity")
    current_records = [
        record for record in runtime_records if record.invocation_id == invocation_id
    ]
    expected_current_phases = [
        ("start_before_conformance", None),
        *[
            (
                (
                    "after_conformance_before_batch"
                    if batch_rank == 1
                    else "batch_boundary_before_batch"
                ),
                batch_rank,
            )
            for batch_rank in range(1, schedule.batch_count + 1)
        ],
        ("end_after_all_batches", None),
    ]
    if (
        len(current_records) != len(expected_current_phases)
        or runtime_records[-len(current_records) :] != current_records
        or [(record.phase, record.batch_rank) for record in current_records]
        != expected_current_phases
        or [record.invocation_sequence for record in current_records]
        != list(range(1, len(current_records) + 1))
    ):
        raise RuntimeError("completion current runtime invocation is incomplete")

    for record in runtime_records:
        evidence = record.evidence
        if (
            evidence.persisted_fingerprint_sha256 != fingerprint.fingerprint_sha256
            or evidence.endpoint_url != fingerprint.endpoint_url
            or evidence.current_listener_pid != fingerprint.process.pid
            or Path(evidence.current_process_cwd).resolve()
            != Path(fingerprint.process.cwd).resolve()
            or evidence.current_source_snapshot_sha256 != fingerprint.source.source_snapshot_sha256
        ):
            raise RuntimeError("completion runtime revalidation does not bind the fingerprint")

    post_conformance = current_records[1].evidence
    final_revalidation = current_records[-1].evidence
    if (
        completion.get("oauth_runtime_revalidation") != post_conformance.model_dump(mode="json")
        or completion.get("oauth_runtime_revalidation_sha256")
        != post_conformance.revalidation_sha256
        or completion.get("final_oauth_runtime_revalidation_sha256")
        != final_revalidation.revalidation_sha256
    ):
        raise RuntimeError("completion OAuth runtime revalidation identities are stale")
    return post_conformance


def _require_exact_primary_result(
    persisted: Pilot2AnalysisResult, recomputed: Pilot2AnalysisResult
) -> None:
    """Prevent report rendering from trusting a merely self-consistent stale result."""

    if persisted.model_dump(mode="json") != recomputed.model_dump(mode="json"):
        raise RuntimeError("persisted primary analysis is stale")


def _bind_attempt_and_terminal_manifests(
    report: Mapping[str, Any],
    *,
    ledger_path: Path,
    attempts: Sequence[GenerationAttempt],
    terminal_path: Path,
    terminal_records: Sequence[TerminalGenerationRecord],
    attempt_receipt_path: Path,
    attempt_receipt_manifest: Mapping[str, Any],
    successful_output_path: Path,
    successful_output_manifest: Mapping[str, Any],
) -> Dict[str, Any]:
    """Add byte-level and canonical semantic bindings to completion evidence."""

    if not all(
        path.is_file()
        for path in (
            ledger_path,
            terminal_path,
            attempt_receipt_path,
            successful_output_path,
        )
    ):
        raise FileNotFoundError(
            "attempt, terminal, receipt, and successful-output manifests must exist before binding"
        )
    attempt_semantic = generation_attempt_ledger_semantic_sha256(attempts)
    terminal_semantic = terminal_records_manifest_sha256(terminal_records)
    if report.get("attempt_ledger_semantic_sha256") != attempt_semantic:
        raise RuntimeError("completion carries a stale attempt-ledger semantic hash")
    receipt_semantic = attempt_receipt_manifest.get("attempt_receipt_manifest_sha256")
    receipt_unsigned = {
        key: value
        for key, value in attempt_receipt_manifest.items()
        if key != "attempt_receipt_manifest_sha256"
    }
    if (
        receipt_semantic != stable_hash(receipt_unsigned)
        or report.get("attempt_receipt_manifest_sha256") != receipt_semantic
        or report.get("attempt_receipt_count")
        != attempt_receipt_manifest.get("attempt_receipt_count")
        or read_json(attempt_receipt_path) != dict(attempt_receipt_manifest)
    ):
        raise RuntimeError("completion carries stale attempt-receipt evidence")
    successful_semantic = successful_output_manifest.get("successful_output_manifest_sha256")
    successful_unsigned = {
        key: value
        for key, value in successful_output_manifest.items()
        if key != "successful_output_manifest_sha256"
    }
    if (
        successful_semantic != stable_hash(successful_unsigned)
        or report.get("successful_output_manifest_sha256") != successful_semantic
        or report.get("successful_output_count")
        != successful_output_manifest.get("successful_output_count")
        or read_json(successful_output_path) != dict(successful_output_manifest)
    ):
        raise RuntimeError("completion carries stale successful-output evidence")
    payload = dict(report)
    prior_report_sha = payload.pop("report_sha256", None)
    if not isinstance(prior_report_sha, str) or stable_hash(payload) != prior_report_sha:
        raise RuntimeError("generation completion has a stale pre-manifest self-hash")
    payload.update(
        {
            "completion_without_file_manifest_bindings_sha256": prior_report_sha,
            "attempt_ledger_file_sha256": hash_file(ledger_path),
            "terminal_records_file_sha256": hash_file(terminal_path),
            "terminal_records_manifest_sha256": terminal_semantic,
            "attempt_receipt_manifest_file_sha256": hash_file(attempt_receipt_path),
            "attempt_receipt_manifest_path": str(attempt_receipt_path.resolve()),
            "successful_output_manifest_file_sha256": hash_file(successful_output_path),
        }
    )
    payload["report_sha256"] = stable_hash(payload)
    return payload


def _validate_attempt_and_terminal_manifests(
    completion: Mapping[str, Any],
    *,
    ledger_path: Path,
    attempts: Sequence[GenerationAttempt],
    terminal_path: Path,
    terminal_records: Sequence[TerminalGenerationRecord],
    attempt_receipt_path: Path,
    attempt_receipt_manifest: Mapping[str, Any],
    successful_output_path: Path,
    successful_output_manifest: Mapping[str, Any],
) -> None:
    """Verify exact JSONL bytes and canonical rows against final completion."""

    persisted_terminal = _load_models(terminal_path, TerminalGenerationRecord)
    if [row.model_dump(mode="json") for row in persisted_terminal] != [
        row.model_dump(mode="json") for row in terminal_records
    ]:
        raise RuntimeError("terminal-record manifest disagrees with the attempt ledger")
    persisted_receipts = read_json(attempt_receipt_path)
    if persisted_receipts != dict(attempt_receipt_manifest):
        raise RuntimeError("attempt-receipt manifest disagrees with durable attempt sidecars")
    receipt_semantic = attempt_receipt_manifest.get("attempt_receipt_manifest_sha256")
    receipt_unsigned = {
        key: value
        for key, value in attempt_receipt_manifest.items()
        if key != "attempt_receipt_manifest_sha256"
    }
    if receipt_semantic != stable_hash(receipt_unsigned):
        raise RuntimeError("attempt-receipt manifest self-binding is stale")
    persisted_successful = read_json(successful_output_path)
    if persisted_successful != dict(successful_output_manifest):
        raise RuntimeError("successful-output manifest disagrees with verified original outputs")
    successful_semantic = successful_output_manifest.get("successful_output_manifest_sha256")
    successful_unsigned = {
        key: value
        for key, value in successful_output_manifest.items()
        if key != "successful_output_manifest_sha256"
    }
    if successful_semantic != stable_hash(successful_unsigned):
        raise RuntimeError("successful-output manifest self-binding is stale")

    pre_file_payload = dict(completion)
    pre_file_payload.pop("report_sha256", None)
    prior_sha = pre_file_payload.pop("completion_without_file_manifest_bindings_sha256", None)
    for key in (
        "attempt_ledger_file_sha256",
        "terminal_records_file_sha256",
        "terminal_records_manifest_sha256",
        "attempt_receipt_manifest_file_sha256",
        "attempt_receipt_manifest_path",
        "successful_output_manifest_file_sha256",
    ):
        pre_file_payload.pop(key, None)
    if not isinstance(prior_sha, str) or stable_hash(pre_file_payload) != prior_sha:
        raise RuntimeError("completion pre-file evidence chain is stale")

    checks = {
        "attempt-ledger file": (
            completion.get("attempt_ledger_file_sha256"),
            hash_file(ledger_path),
        ),
        "attempt-ledger semantic": (
            completion.get("attempt_ledger_semantic_sha256"),
            generation_attempt_ledger_semantic_sha256(attempts),
        ),
        "terminal-record file": (
            completion.get("terminal_records_file_sha256"),
            hash_file(terminal_path),
        ),
        "terminal-record semantic": (
            completion.get("terminal_records_manifest_sha256"),
            terminal_records_manifest_sha256(persisted_terminal),
        ),
        "attempt-receipt file": (
            completion.get("attempt_receipt_manifest_file_sha256"),
            hash_file(attempt_receipt_path),
        ),
        "attempt-receipt semantic": (
            completion.get("attempt_receipt_manifest_sha256"),
            receipt_semantic,
        ),
        "attempt-receipt count": (
            completion.get("attempt_receipt_count"),
            attempt_receipt_manifest.get("attempt_receipt_count"),
        ),
        "attempt-receipt path": (
            Path(str(completion.get("attempt_receipt_manifest_path"))).resolve(),
            attempt_receipt_path.resolve(),
        ),
        "successful-output file": (
            completion.get("successful_output_manifest_file_sha256"),
            hash_file(successful_output_path),
        ),
        "successful-output semantic": (
            completion.get("successful_output_manifest_sha256"),
            successful_semantic,
        ),
        "successful-output count": (
            completion.get("successful_output_count"),
            successful_output_manifest.get("successful_output_count"),
        ),
    }
    stale = [label for label, (recorded, observed) in checks.items() if recorded != observed]
    if stale:
        raise RuntimeError("stale generation evidence: " + ", ".join(stale))


def _make_generated_feature(
    cell: GenerationCell,
    source_output_sha256: str,
    derived: Pilot2DerivedInput,
    vector: Sequence[float],
    metadata: Mapping[str, Any],
    config: Pilot2Config,
) -> GeneratedLearnedFeature:
    payload: Dict[str, Any] = {
        "cell_id": cell.cell_id,
        "generation_cell_identity_sha256": cell.cell_identity_sha256,
        "prompt_id": cell.prompt_id,
        "content_id": cell.content_id,
        "requested_model_label": cell.requested_model_label,
        "repetition": cell.repetition,
        "target_artist_id": cell.target_artist_id,
        "artist_free_control": cell.artist_free_control,
        "source_output_sha256": source_output_sha256,
        "derived_png_sha256": derived.output_sha256,
        "feature_version": config.learned_formal.feature_version,
        "feature_config_sha256": stable_hash(config.learned_formal.model_dump(mode="json")),
        "vector_sha256": learned_formal_vector_sha256(vector),
        "vector": [float(value) for value in vector],
        "extraction_metadata": dict(metadata),
    }
    identity = stable_hash(_generated_feature_identity_payload(payload))
    return GeneratedLearnedFeature(
        feature_id=f"pilot2-generated-feature-{identity[:24]}", **payload
    )


@app.command("validate-manifests")
def validate_manifests_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config", help="pilot_2 YAML."),
) -> None:
    """Validate every frozen, pinned manifest without network access."""

    ctx = _context(root, config_path)
    typer.echo(json.dumps(_validate_static_manifests(ctx), indent=2, sort_keys=True))


@app.command("freeze-manifests")
def freeze_manifests_command(
    root: Path = typer.Option(Path("."), "--root", help="Repository root."),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config", help="pilot_2 YAML."),
) -> None:
    """Rebuild the deterministic atlas, generation cells, and schedule offline."""

    ctx = _context(root, config_path)
    config = ctx.config
    atlas = build_pilot2_atlas(ctx.resolve(config.corpus.candidate_audit), config.corpus)
    acquired = _load_models(ctx.resolve(config.corpus.real_image_manifest), Pilot2AcquiredImage)
    validate_pilot2_acquired_images(acquired, atlas, root=ctx.root)
    prompts = _load_prompts(ctx, require_pin=config.generation.prompt_manifest_sha256 is not None)
    cells = build_generation_cells(prompts, repetitions=config.generation.repetitions)
    schedule = build_generation_schedule(cells)
    sensitivity = build_sample_size_sensitivity(
        draws=config.design.simulation_draws,
        seed=config.design.simulation_seed,
    )
    formula = formula_probe_evidence()

    atlas_bytes = _jsonl_bytes(atlas)
    cell_bytes = _jsonl_bytes(cells)
    schedule_bytes = _json_bytes(schedule)
    pins = {
        "atlas_manifest_sha256": _assert_rendered_pin(
            atlas_bytes, config.corpus.atlas_manifest_sha256, "atlas manifest"
        ),
        "generation_cells_manifest_sha256": _assert_rendered_pin(
            cell_bytes,
            config.generation.generation_cells_manifest_sha256,
            "generation-cells manifest",
        ),
        "generation_schedule_sha256": _assert_rendered_pin(
            schedule_bytes,
            config.generation.generation_schedule_sha256,
            "generation schedule",
        ),
        "sample_size_sensitivity_artifact_sha256": _assert_rendered_pin(
            _json_bytes(sensitivity),
            config.design.sensitivity_artifact_sha256,
            "sample-size sensitivity artifact",
        ),
    }
    write_jsonl(ctx.resolve(config.corpus.atlas_manifest), atlas)
    write_jsonl(ctx.resolve(config.generation.generation_cells_manifest), cells)
    write_json(ctx.resolve(config.generation.generation_schedule), schedule)
    write_json(ctx.resolve(config.design.sensitivity_artifact), sensitivity)
    write_json(ctx.resolve(DEFAULT_CHROMATIC_FORMULA_PROBES), formula)
    typer.echo(json.dumps({"status": "frozen", **pins}, indent=2, sort_keys=True))


@app.command("preprocess-real")
def preprocess_real_command(
    root: Path = typer.Option(Path("."), "--root"),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    output_manifest: Path = typer.Option(DEFAULT_REAL_DERIVED, "--output-manifest"),
    output_dir: Path = typer.Option(Path("artifacts/pilot_2/real_common"), "--output-dir"),
) -> None:
    """Normalize all 40 acquired references into the common lossless PNG domain."""

    ctx = _context(root, config_path)
    atlas = _load_atlas(ctx)
    acquired = _load_acquired(ctx, atlas)
    acquired_by_work = {row.canonical_work_id: row for row in acquired}
    rows = [
        preprocess_acquired_image(
            acquired_by_work[work.canonical_work_id],
            ctx.root,
            ctx.resolve(output_dir),
            ctx.config.preprocessing,
        )
        for work in sorted(atlas, key=lambda row: row.canonical_work_id)
    ]
    write_jsonl(ctx.resolve(output_manifest), rows)
    typer.echo(f"wrote {len(rows)} normalized real inputs to {ctx.resolve(output_manifest)}")


@app.command("extract-real")
def extract_real_command(
    root: Path = typer.Option(Path("."), "--root"),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    derived_manifest: Path = typer.Option(DEFAULT_REAL_DERIVED, "--derived-manifest"),
    feature_manifest: Path = typer.Option(DEFAULT_REAL_FEATURES, "--feature-manifest"),
    chromatic_manifest: Path = typer.Option(DEFAULT_REAL_CHROMATIC, "--chromatic-manifest"),
    determinism_manifest: Path = typer.Option(DEFAULT_DETERMINISM, "--determinism-manifest"),
) -> None:
    """Extract all real A-vectors, secondary chromatic features, and repeat probes."""

    ctx = _context(root, config_path)
    atlas = _load_atlas(ctx)
    acquired = _load_acquired(ctx, atlas)
    derived = _load_models(ctx.resolve(derived_manifest), Pilot2DerivedInput)
    if len(derived) != 40:
        raise ValueError("real extraction requires exactly 40 derived inputs")
    _validate_derived_preprocessing(derived, ctx.config, label="real")
    derived_by_work = {row.source_record_id: row for row in derived}
    if set(derived_by_work) != {row.canonical_work_id for row in atlas}:
        raise ValueError("derived inputs do not cover the exact real atlas")
    atlas_rows = sorted(atlas, key=lambda row: row.canonical_work_id)

    typer.echo("loading the pinned local SD2 VAE; no image API call is made")
    loaded = load_configured_vae(ctx.config.learned_formal, ctx.root)
    features: List[Pilot2Feature] = []
    results: Dict[str, Any] = {}
    chromatic: List[Pilot2ChromaticFeature] = []
    for index, work in enumerate(atlas_rows, start=1):
        row = derived_by_work[work.canonical_work_id]
        result = extract_harmonized_learned_formal(
            row, loaded, ctx.config.learned_formal, device=ctx.config.learned_formal.device
        )
        results[work.canonical_work_id] = result
        features.append(feature_from_extraction(work, row, result, ctx.config.learned_formal))
        chromatic.append(
            extract_chromatic_secondary(
                Path(row.output_path),
                work.canonical_work_id,
                expected_sha256=row.output_sha256,
            )
        )
        if index == 1 or index % 5 == 0 or index == len(atlas_rows):
            typer.echo(f"real feature extraction {index}/{len(atlas_rows)}")

    probe_works = [
        min(
            (work for work in atlas_rows if work.artist_id == artist_id and work.split == "train"),
            key=lambda work: work.canonical_work_id,
        )
        for artist_id in sorted(ctx.config.corpus.artist_ids)
    ]
    probes: List[Pilot2DeterminismProbe] = []
    for work in probe_works:
        repeated = extract_harmonized_learned_formal(
            derived_by_work[work.canonical_work_id],
            loaded,
            ctx.config.learned_formal,
            device=ctx.config.learned_formal.device,
        )
        probes.append(build_determinism_probe(work, results[work.canonical_work_id], repeated))

    # Validate all extraction-to-acquisition bindings before publishing any manifest.
    qualify_learned_formal(
        features,
        atlas_rows,
        acquired,
        ctx.config,
        probes,
        qualification_contract_sha256=None,
    )
    write_jsonl(ctx.resolve(feature_manifest), features)
    write_jsonl(ctx.resolve(chromatic_manifest), chromatic)
    write_jsonl(ctx.resolve(determinism_manifest), probes)
    typer.echo(f"wrote {len(features)} real A-vectors and {len(probes)} repeat probes")


@app.command("qualify-real")
def qualify_real_command(
    root: Path = typer.Option(Path("."), "--root"),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
) -> None:
    """Run the frozen real-only primary qualification and write its gate artifacts."""

    ctx = _context(root, config_path)
    _validate_static_manifests(ctx, require_plan=True)
    atlas, acquired, _, features, probes = _real_inputs(ctx)
    contract_sha, contract = pilot2_qualification_contract(
        ctx.config, ctx.root, atlas, acquired, features
    )
    contract_path = ctx.resolve(DEFAULT_QUALIFICATION_CONTRACT)
    write_json(contract_path, contract)
    result = qualify_learned_formal(
        features,
        atlas,
        acquired,
        ctx.config,
        probes,
        qualification_contract_sha256=contract_sha,
    )
    result_path = ctx.resolve(ctx.config.qualification_artifacts.learned_result)
    write_json(result_path, result)
    card = qualification_card_from_result(
        result,
        _relative(result_path, ctx.root),
        hash_file(result_path),
    )
    card_path = ctx.resolve(ctx.config.qualification_artifacts.learned_card)
    write_json(card_path, card)
    allowed, reasons = pilot2_generation_gate(
        result, ctx.config, expected_contract_sha256=contract_sha
    )
    gate: Dict[str, Any] = {
        "record_type": "pilot2_generation_gate",
        "schema_version": "2.0",
        "status": "pass" if allowed else "fail",
        "pilot2_config_sha256": ctx.config.content_hash(),
        "qualification_result_sha256": result.result_sha256,
        "qualification_contract_sha256": contract_sha,
        "reasons": reasons,
        "chromatic_can_open_or_close_gate": False,
    }
    gate["gate_sha256"] = stable_hash(gate)
    write_json(ctx.resolve(DEFAULT_GENERATION_GATE), gate)
    typer.echo(
        json.dumps(
            {
                "status": result.status,
                "qualification_result_sha256": result.result_sha256,
                "qualification_contract_sha256": contract_sha,
                "generation_gate_sha256": gate["gate_sha256"],
                "reasons": result.reasons,
            },
            indent=2,
            sort_keys=True,
        )
    )
    if not allowed:
        raise typer.Exit(code=2)


@app.command("plan-generation")
def plan_generation_command(
    root: Path = typer.Option(Path("."), "--root"),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
) -> None:
    """Write the exact 320-cell plan and deterministic five-cell batch schedule offline."""

    ctx = _context(root, config_path)
    prompts = _load_prompts(ctx)
    cells = build_generation_cells(prompts, repetitions=ctx.config.generation.repetitions)
    schedule = build_generation_schedule(cells)
    cell_bytes = _jsonl_bytes(cells)
    schedule_bytes = _json_bytes(schedule)
    cell_file_sha = _assert_rendered_pin(
        cell_bytes,
        ctx.config.generation.generation_cells_manifest_sha256,
        "generation-cells manifest",
    )
    schedule_file_sha = _assert_rendered_pin(
        schedule_bytes,
        ctx.config.generation.generation_schedule_sha256,
        "generation schedule",
    )
    write_jsonl(ctx.resolve(ctx.config.generation.generation_cells_manifest), cells)
    write_json(ctx.resolve(ctx.config.generation.generation_schedule), schedule)
    typer.echo(
        json.dumps(
            {
                "status": "planned_offline_no_image_requests",
                "cell_count": len(cells),
                "generation_grid_sha256": generation_grid_sha256(cells),
                "generation_cells_file_sha256": cell_file_sha,
                "generation_schedule_file_sha256": schedule_file_sha,
                "generation_schedule_sha256": schedule.schedule_sha256,
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("conform")
def conform_command(
    execute: bool = typer.Option(
        False,
        "--execute",
        help="Required acknowledgement: send the two frozen conformance cells.",
    ),
    root: Path = typer.Option(Path("."), "--root"),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    ledger_path: Path = typer.Option(DEFAULT_ATTEMPT_LEDGER, "--ledger"),
    output_path: Path = typer.Option(DEFAULT_CONFORMANCE, "--output"),
) -> None:
    """Send only the two frozen in-grid conformance requests through local OAuth."""

    if not execute:
        raise typer.BadParameter(
            "conform can send image requests; rerun with --execute to acknowledge"
        )
    ctx = _context(root, config_path)
    cells, _ = _load_generation_plan(ctx)
    transport_config, fingerprint = _load_runtime(ctx)
    typer.echo(
        "sending the two frozen conformance cells through "
        f"{transport_config.endpoint_url}; the requested labels are operational strata"
    )
    ledger = AppendOnlyAttemptLedger(ctx.resolve(ledger_path))
    post_intent_ledger = AppendOnlyPostIntentLedger(
        ctx.resolve(ctx.config.generation.post_intent_ledger)
    )
    runtime_ledger = AppendOnlyRuntimeRevalidationLedger(
        ctx.resolve(ctx.config.generation.runtime_revalidation_ledger)
    )
    with Pilot2OAuthTransport(transport_config) as transport:
        report = run_transport_conformance(
            cells=cells,
            transport=transport,
            ledger=ledger,
            post_intent_ledger=post_intent_ledger,
            runtime_revalidation_ledger=runtime_ledger,
            fingerprint=fingerprint,
            output_dir=ctx.resolve(ctx.config.generation.output_dir),
        )
    attempts = ledger.rows()
    attempt_receipts = verified_attempt_receipt_manifest(ledger, attempts)
    attempt_receipt_path = ctx.resolve(ctx.config.generation.attempt_receipt_manifest)
    write_json(attempt_receipt_path, attempt_receipts)
    if (
        report.get("attempt_receipt_count") != attempt_receipts["attempt_receipt_count"]
        or report.get("attempt_receipt_manifest_sha256")
        != attempt_receipts["attempt_receipt_manifest_sha256"]
    ):
        raise RuntimeError("transport conformance carries stale attempt receipts")
    report_payload = dict(report)
    prior_report_sha = report_payload.pop("report_sha256", None)
    if not isinstance(prior_report_sha, str) or stable_hash(report_payload) != prior_report_sha:
        raise RuntimeError("transport conformance self-binding is stale")
    report_payload["conformance_without_receipt_file_binding_sha256"] = prior_report_sha
    report_payload["attempt_receipt_manifest_file_sha256"] = hash_file(attempt_receipt_path)
    report_payload["attempt_receipt_manifest_path"] = str(attempt_receipt_path.resolve())
    report_payload["report_sha256"] = stable_hash(report_payload)
    report = report_payload
    write_json(ctx.resolve(output_path), report)
    typer.echo(json.dumps(report, indent=2, sort_keys=True))
    if report["status"] != "pass":
        raise typer.Exit(code=2)


@app.command("generate")
def generate_command(
    execute: bool = typer.Option(
        False,
        "--execute",
        help="Required acknowledgement: resume/send the frozen 320-cell generation grid.",
    ),
    root: Path = typer.Option(Path("."), "--root"),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    ledger_path: Path = typer.Option(DEFAULT_ATTEMPT_LEDGER, "--ledger"),
    completion_path: Path = typer.Option(DEFAULT_COMPLETION, "--completion"),
    conformance_path: Path = typer.Option(DEFAULT_CONFORMANCE, "--conformance"),
    terminal_path: Path = typer.Option(DEFAULT_TERMINAL_RECORDS, "--terminal-records"),
    successful_output_path: Path = typer.Option(
        DEFAULT_SUCCESSFUL_OUTPUT_MANIFEST, "--successful-output-manifest"
    ),
) -> None:
    """Resume the append-only frozen schedule until every logical cell is terminal."""

    if not execute:
        raise typer.BadParameter(
            "generate can send image requests; rerun with --execute to acknowledge"
        )
    ctx = _context(root, config_path)
    cells, _ = _load_generation_plan(ctx)
    transport_config, fingerprint = _load_runtime(ctx)
    ledger = AppendOnlyAttemptLedger(ctx.resolve(ledger_path))
    post_intent_ledger = AppendOnlyPostIntentLedger(
        ctx.resolve(ctx.config.generation.post_intent_ledger)
    )
    runtime_ledger = AppendOnlyRuntimeRevalidationLedger(
        ctx.resolve(ctx.config.generation.runtime_revalidation_ledger)
    )
    typer.echo(
        "resuming the frozen 320-cell schedule through the pinned localhost OAuth; "
        "existing terminal ledger rows will not be sent again"
    )
    try:
        with Pilot2OAuthTransport(transport_config) as transport:
            report = run_generation_grid(
                cells,
                transport=transport,
                ledger=ledger,
                post_intent_ledger=post_intent_ledger,
                runtime_revalidation_ledger=runtime_ledger,
                fingerprint=fingerprint,
                output_dir=ctx.resolve(ctx.config.generation.output_dir),
                max_parallel=ctx.config.generation.max_parallel,
            )
    except TransportConformanceFailure as exc:
        write_json(ctx.resolve(conformance_path), exc.report)
        raise RuntimeError("transport conformance failed; full generation was not started") from exc

    conformance = dict(report["transport_conformance"])
    prior_sha = conformance.pop("report_sha256")
    conformance["conformance_without_revalidation_sha256"] = prior_sha
    conformance["oauth_runtime_revalidation"] = report["oauth_runtime_revalidation"]
    conformance["oauth_runtime_revalidation_sha256"] = report["oauth_runtime_revalidation_sha256"]
    conformance["report_sha256"] = stable_hash(conformance)
    attempts = ledger.rows()
    attempt_receipt_manifest = verified_attempt_receipt_manifest(ledger, attempts)
    resolved_attempt_receipt_path = ctx.resolve(ctx.config.generation.attempt_receipt_manifest)
    write_json(resolved_attempt_receipt_path, attempt_receipt_manifest)
    conformance_prior_sha = conformance.pop("report_sha256")
    conformance.update(
        {
            "conformance_without_receipt_file_binding_sha256": (conformance_prior_sha),
            "attempt_receipt_count": attempt_receipt_manifest["attempt_receipt_count"],
            "attempt_receipt_manifest_sha256": attempt_receipt_manifest[
                "attempt_receipt_manifest_sha256"
            ],
            "attempt_receipt_manifest_file_sha256": hash_file(resolved_attempt_receipt_path),
            "attempt_receipt_manifest_path": str(resolved_attempt_receipt_path.resolve()),
        }
    )
    conformance["report_sha256"] = stable_hash(conformance)
    write_json(ctx.resolve(conformance_path), conformance)
    successful_output_manifest = verify_successful_output_artifacts(
        cells,
        attempts,
        output_root=ctx.resolve(ctx.config.generation.output_dir),
    )
    resolved_successful_output_path = ctx.resolve(successful_output_path)
    write_json(resolved_successful_output_path, successful_output_manifest)
    if report["all_cells_terminal"]:
        terminal_records = terminal_records_for_analysis(cells, attempts)
        resolved_terminal_path = ctx.resolve(terminal_path)
        write_jsonl(resolved_terminal_path, terminal_records)
        report = _bind_attempt_and_terminal_manifests(
            report,
            ledger_path=ctx.resolve(ledger_path),
            attempts=attempts,
            terminal_path=resolved_terminal_path,
            terminal_records=terminal_records,
            attempt_receipt_path=resolved_attempt_receipt_path,
            attempt_receipt_manifest=attempt_receipt_manifest,
            successful_output_path=resolved_successful_output_path,
            successful_output_manifest=successful_output_manifest,
        )
    write_json(ctx.resolve(completion_path), report)
    typer.echo(
        json.dumps(
            {
                "all_cells_terminal": report["all_cells_terminal"],
                "attempt_count": report["attempt_count"],
                "disposition_counts": report["disposition_counts"],
                "report_sha256": report["report_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if not report["all_cells_terminal"]:
        raise typer.Exit(code=2)


@app.command("prepare-generated")
def prepare_generated_command(
    root: Path = typer.Option(Path("."), "--root"),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    ledger_path: Path = typer.Option(DEFAULT_ATTEMPT_LEDGER, "--ledger"),
    derived_manifest: Path = typer.Option(DEFAULT_GENERATED_DERIVED, "--derived-manifest"),
    feature_manifest: Path = typer.Option(DEFAULT_GENERATED_FEATURES, "--feature-manifest"),
    chromatic_manifest: Path = typer.Option(DEFAULT_GENERATED_CHROMATIC, "--chromatic-manifest"),
    output_dir: Path = typer.Option(Path("artifacts/pilot_2/generated_common"), "--output-dir"),
) -> None:
    """Normalize and extract features for every successful terminal output, offline."""

    ctx = _context(root, config_path)
    cells, schedule = _load_generation_plan(ctx)
    _qualification_context(ctx, require_gate=True)
    ledger = AppendOnlyAttemptLedger(ctx.resolve(ledger_path))
    post_intent_ledger = AppendOnlyPostIntentLedger(
        ctx.resolve(ctx.config.generation.post_intent_ledger)
    )
    ledger.recover_from_sidecars(post_intent_ledger)
    attempts = ledger.rows()
    ledger.verify_sidecars(attempts)
    base_completion = generation_completion_report(cells, attempts)
    completion = _self_hashed_json(ctx.resolve(DEFAULT_COMPLETION), "report_sha256")
    fingerprint = OAuthRuntimeFingerprint.model_validate(
        read_json(ctx.resolve(ctx.config.generation.transport_fingerprint))
    )
    _validate_execution_envelope(
        completion,
        cells=cells,
        attempts=attempts,
        schedule=schedule,
        post_intent_ledger_path=ctx.resolve(ctx.config.generation.post_intent_ledger),
        runtime_ledger_path=ctx.resolve(ctx.config.generation.runtime_revalidation_ledger),
        base_completion=base_completion,
        base_conformance=verify_transport_conformance(
            select_conformance_cells(cells), attempts, fingerprint
        ),
        fingerprint=fingerprint,
        expected_max_parallel=ctx.config.generation.max_parallel,
    )
    if not completion["all_cells_terminal"]:
        raise RuntimeError("generated feature preparation requires all 320 cells terminal")
    terminal = terminal_records_for_analysis(cells, attempts)
    attempt_receipt_manifest = verified_attempt_receipt_manifest(ledger, attempts)
    successful_output_manifest = verify_successful_output_artifacts(
        cells,
        attempts,
        output_root=ctx.resolve(ctx.config.generation.output_dir),
    )
    _validate_attempt_and_terminal_manifests(
        completion,
        ledger_path=ctx.resolve(ledger_path),
        attempts=attempts,
        terminal_path=ctx.resolve(DEFAULT_TERMINAL_RECORDS),
        terminal_records=terminal,
        attempt_receipt_path=ctx.resolve(ctx.config.generation.attempt_receipt_manifest),
        attempt_receipt_manifest=attempt_receipt_manifest,
        successful_output_path=ctx.resolve(DEFAULT_SUCCESSFUL_OUTPUT_MANIFEST),
        successful_output_manifest=successful_output_manifest,
    )
    successes = [row for row in terminal if row.outcome == "succeeded"]
    cell_by_id = {row.cell_id: row for row in cells}

    derived: List[Pilot2DerivedInput] = []
    for row in successes:
        assert row.output_path is not None and row.output_sha256 is not None
        derived.append(
            preprocess_common_png(
                Path(row.output_path),
                row.cell_id,
                ctx.resolve(output_dir),
                ctx.config.preprocessing,
                expected_source_sha256=row.output_sha256,
            )
        )
    derived_by_cell = {row.source_record_id: row for row in derived}
    generated: List[GeneratedLearnedFeature] = []
    chromatic: List[Pilot2ChromaticFeature] = []
    if successes:
        typer.echo(
            f"loading the pinned local SD2 VAE for {len(successes)} successful outputs; "
            "no image API call is made"
        )
        loaded = load_configured_vae(ctx.config.learned_formal, ctx.root)
        for index, terminal_row in enumerate(successes, start=1):
            cell = cell_by_id[terminal_row.cell_id]
            common = derived_by_cell[cell.cell_id]
            extraction = extract_harmonized_learned_formal(
                common,
                loaded,
                ctx.config.learned_formal,
                device=ctx.config.learned_formal.device,
            )
            assert terminal_row.output_sha256 is not None
            generated.append(
                _make_generated_feature(
                    cell,
                    terminal_row.output_sha256,
                    common,
                    extraction.vector,
                    extraction.metadata,
                    ctx.config,
                )
            )
            chromatic.append(
                extract_chromatic_secondary(
                    Path(common.output_path),
                    cell.cell_id,
                    expected_sha256=common.output_sha256,
                )
            )
            if index == 1 or index % 10 == 0 or index == len(successes):
                typer.echo(f"generated feature extraction {index}/{len(successes)}")
    write_jsonl(ctx.resolve(derived_manifest), derived)
    write_jsonl(ctx.resolve(feature_manifest), generated)
    write_jsonl(ctx.resolve(chromatic_manifest), chromatic)
    typer.echo(f"wrote {len(generated)} generated A-vectors and chromatic features")


def _analysis_inputs(
    ctx: Pilot2Context,
    *,
    ledger_path: Path,
    generated_feature_path: Path,
) -> tuple[
    Pilot2ProjectedAnalysisInputs,
    List[PromptRecord],
    Dict[str, Path],
]:
    design_path, _ = _validate_design_sensitivity(ctx)
    prompts = _load_prompts(ctx)
    cells, schedule = _load_generation_plan(ctx, prompts)
    result, contract_sha, gate = _qualification_context(ctx, require_gate=True)
    _, _, _, real_features, _ = _real_inputs(ctx)
    ordered_real = sorted(real_features, key=lambda row: row.canonical_work_id)
    train = [row for row in ordered_real if row.split == "train"]
    frozen_pca = fit_train_only_pca(
        np.asarray([row.vector for row in train], dtype=np.float64),
        [row.canonical_work_id for row in train],
        variance_target=ctx.config.learned_formal.pca_variance_target,
    )
    if frozen_pca.evidence.model_dump(mode="json") != result.pca.model_dump(mode="json"):
        raise RuntimeError("reconstructed train-only PCA disagrees with qualification")

    ledger = AppendOnlyAttemptLedger(ctx.resolve(ledger_path))
    post_intent_ledger = AppendOnlyPostIntentLedger(
        ctx.resolve(ctx.config.generation.post_intent_ledger)
    )
    ledger.recover_from_sidecars(post_intent_ledger)
    attempts = ledger.rows()
    ledger.verify_sidecars(attempts)
    attempt_receipt_manifest = verified_attempt_receipt_manifest(ledger, attempts)
    attempt_receipt_path = ctx.resolve(ctx.config.generation.attempt_receipt_manifest)
    cell_by_id = {row.cell_id: row for row in cells}
    fingerprint = OAuthRuntimeFingerprint.model_validate(
        read_json(ctx.resolve(ctx.config.generation.transport_fingerprint))
    )
    for attempt in attempts:
        cell = cell_by_id.get(attempt.cell_id)
        if cell is None or (
            attempt.cell_identity_sha256 != cell.cell_identity_sha256
            or attempt.requested_model_label != cell.requested_model_label
            or attempt.canonical_request_sha256 != cell.canonical_request_sha256
            or attempt.oauth_runtime_fingerprint_sha256 != fingerprint.fingerprint_sha256
            or attempt.endpoint != fingerprint.endpoint_url
        ):
            raise RuntimeError(
                f"generation attempt disagrees with its frozen cell/runtime: {attempt.cell_id}"
            )
    base_completion = generation_completion_report(cells, attempts)
    completion_path = ctx.resolve(DEFAULT_COMPLETION)
    completion = _self_hashed_json(completion_path, "report_sha256")
    base_conformance = verify_transport_conformance(
        select_conformance_cells(cells), attempts, fingerprint
    )
    execution_revalidation = _validate_execution_envelope(
        completion,
        cells=cells,
        attempts=attempts,
        schedule=schedule,
        post_intent_ledger_path=ctx.resolve(ctx.config.generation.post_intent_ledger),
        runtime_ledger_path=ctx.resolve(ctx.config.generation.runtime_revalidation_ledger),
        base_completion=base_completion,
        base_conformance=base_conformance,
        fingerprint=fingerprint,
        expected_max_parallel=ctx.config.generation.max_parallel,
    )
    if not completion.get("all_cells_terminal"):
        raise RuntimeError("analysis requires all frozen generation cells terminal")
    terminal_records = terminal_records_for_analysis(cells, attempts)
    successful_output_path = ctx.resolve(DEFAULT_SUCCESSFUL_OUTPUT_MANIFEST)
    successful_output_manifest = verify_successful_output_artifacts(
        cells,
        attempts,
        output_root=ctx.resolve(ctx.config.generation.output_dir),
    )
    _validate_attempt_and_terminal_manifests(
        completion,
        ledger_path=ctx.resolve(ledger_path),
        attempts=attempts,
        terminal_path=ctx.resolve(DEFAULT_TERMINAL_RECORDS),
        terminal_records=terminal_records,
        attempt_receipt_path=attempt_receipt_path,
        attempt_receipt_manifest=attempt_receipt_manifest,
        successful_output_path=successful_output_path,
        successful_output_manifest=successful_output_manifest,
    )

    generated_features = _load_models(ctx.resolve(generated_feature_path), GeneratedLearnedFeature)
    terminal_by_cell = {row.cell_id: row for row in terminal_records}
    successful_terminal = {
        cell_id: row for cell_id, row in terminal_by_cell.items() if row.outcome == "succeeded"
    }
    generated_derived = _load_models(ctx.resolve(DEFAULT_GENERATED_DERIVED), Pilot2DerivedInput)
    _validate_derived_preprocessing(generated_derived, ctx.config, label="generated")
    derived_by_cell = {row.source_record_id: row for row in generated_derived}
    feature_by_cell = {row.cell_id: row for row in generated_features}
    if (
        len(feature_by_cell) != len(generated_features)
        or len(derived_by_cell) != len(generated_derived)
        or set(feature_by_cell) != set(successful_terminal)
        or set(derived_by_cell) != set(successful_terminal)
    ):
        raise ValueError("generated learned manifests do not cover exactly the successful cells")
    expected_feature_config = stable_hash(ctx.config.learned_formal.model_dump(mode="json"))
    for cell_id, feature in feature_by_cell.items():
        terminal = successful_terminal[cell_id]
        derived = derived_by_cell[cell_id]
        if (
            feature.generation_cell_identity_sha256 != terminal.cell_identity_sha256
            or feature.source_output_sha256 != terminal.output_sha256
            or feature.derived_png_sha256 != derived.output_sha256
            or derived.source_sha256 != terminal.output_sha256
            or feature.feature_version != ctx.config.learned_formal.feature_version
            or feature.feature_config_sha256 != expected_feature_config
            or len(feature.vector) != ctx.config.learned_formal.raw_dimension
        ):
            raise ValueError(f"generated feature provenance is stale: {cell_id}")
        _validate_generated_extraction_provenance(feature, derived, ctx.config)
        derived_path = Path(derived.output_path)
        if not derived_path.is_absolute():
            derived_path = ctx.root / derived_path
        if not derived_path.is_file() or hash_file(derived_path) != derived.output_sha256:
            raise RuntimeError(f"generated normalized PNG is missing or stale: {cell_id}")
    vectors_by_cell = {row.cell_id: row.vector for row in generated_features}
    derived_hash_by_cell = {row.cell_id: row.derived_png_sha256 for row in generated_features}
    joined_rows, _ = assemble_generation_analysis_rows(
        cells,
        attempts,
        raw_generated_vectors_by_cell=vectors_by_cell,
        derived_png_sha256_by_cell=derived_hash_by_cell,
    )

    conformance_path = ctx.resolve(DEFAULT_CONFORMANCE)
    conformance = _self_hashed_json(conformance_path, "report_sha256")
    if conformance.get("status") != "pass":
        raise RuntimeError("transport conformance did not pass")
    if conformance.get("conformance_without_revalidation_sha256") != base_conformance.get(
        "report_sha256"
    ) or any(
        conformance.get(key) != value
        for key, value in base_conformance.items()
        if key != "report_sha256"
    ):
        raise RuntimeError("conformance evidence disagrees with the immutable attempt ledger")
    if (
        conformance.get("oauth_runtime_revalidation")
        != execution_revalidation.model_dump(mode="json")
        or conformance.get("oauth_runtime_revalidation_sha256")
        != execution_revalidation.revalidation_sha256
    ):
        raise RuntimeError("conformance and completion runtime revalidation disagree")
    conformance_pre_receipt = dict(conformance)
    conformance_pre_receipt.pop("report_sha256", None)
    conformance_prior_sha = conformance_pre_receipt.pop(
        "conformance_without_receipt_file_binding_sha256", None
    )
    for key in (
        "attempt_receipt_count",
        "attempt_receipt_manifest_sha256",
        "attempt_receipt_manifest_file_sha256",
        "attempt_receipt_manifest_path",
    ):
        conformance_pre_receipt.pop(key, None)
    if (
        not isinstance(conformance_prior_sha, str)
        or stable_hash(conformance_pre_receipt) != conformance_prior_sha
        or conformance.get("attempt_receipt_count")
        != attempt_receipt_manifest["attempt_receipt_count"]
        or conformance.get("attempt_receipt_manifest_sha256")
        != attempt_receipt_manifest["attempt_receipt_manifest_sha256"]
        or conformance.get("attempt_receipt_manifest_file_sha256")
        != hash_file(attempt_receipt_path)
        or Path(str(conformance.get("attempt_receipt_manifest_path"))).resolve()
        != attempt_receipt_path.resolve()
    ):
        raise RuntimeError("conformance attempt-receipt evidence is stale")
    bindings = Pilot2AnalysisBindings(
        pilot2_config_sha256=ctx.config.content_hash(),
        protocol_document_sha256=hash_file(ctx.resolve(ctx.config.protocol_document)),
        prompt_manifest_sha256=hash_file(ctx.resolve(ctx.config.generation.prompt_manifest)),
        qualification_result_sha256=result.result_sha256,
        qualification_contract_sha256=contract_sha,
        generation_gate_sha256=str(gate["gate_sha256"]),
        transport_conformance_sha256=str(conformance["report_sha256"]),
        generation_grid_sha256=generation_grid_sha256(cells),
        generation_completion_sha256=str(completion["report_sha256"]),
    )
    projected = prepare_projected_analysis_inputs(
        frozen_pca,
        ordered_real,
        joined_rows,
        bindings=bindings,
        generation_cells=cells,
        generation_completion=completion,
    )
    artifacts = {
        "pilot2_config": ctx.config_path,
        "protocol_document": ctx.resolve(ctx.config.protocol_document),
        "candidate_audit": ctx.resolve(ctx.config.corpus.candidate_audit),
        "atlas_manifest": ctx.resolve(ctx.config.corpus.atlas_manifest),
        "real_image_manifest": ctx.resolve(ctx.config.corpus.real_image_manifest),
        "prompt_manifest": ctx.resolve(ctx.config.generation.prompt_manifest),
        "generation_cells": ctx.resolve(ctx.config.generation.generation_cells_manifest),
        "generation_schedule": ctx.resolve(ctx.config.generation.generation_schedule),
        "oauth_runtime_fingerprint": ctx.resolve(ctx.config.generation.transport_fingerprint),
        "oauth_source_snapshot": ctx.resolve(ctx.config.generation.transport_source_snapshot),
        "vae_model_verification": ctx.resolve(ctx.config.learned_formal.model_verification_report),
        "real_derived_inputs": ctx.resolve(DEFAULT_REAL_DERIVED),
        "real_learned_features": ctx.resolve(DEFAULT_REAL_FEATURES),
        "real_chromatic_features": ctx.resolve(DEFAULT_REAL_CHROMATIC),
        "determinism_probes": ctx.resolve(DEFAULT_DETERMINISM),
        "qualification_result": ctx.resolve(ctx.config.qualification_artifacts.learned_result),
        "qualification_card": ctx.resolve(ctx.config.qualification_artifacts.learned_card),
        "qualification_contract": ctx.resolve(DEFAULT_QUALIFICATION_CONTRACT),
        "generation_gate": ctx.resolve(DEFAULT_GENERATION_GATE),
        "transport_conformance": conformance_path,
        "generation_completion": completion_path,
        "attempt_ledger": ctx.resolve(ledger_path),
        "generation_post_intents": ctx.resolve(ctx.config.generation.post_intent_ledger),
        "generation_attempt_receipts": attempt_receipt_path,
        "generation_terminal_records": ctx.resolve(DEFAULT_TERMINAL_RECORDS),
        "successful_output_manifest": successful_output_path,
        "generation_runtime_revalidations": ctx.resolve(
            ctx.config.generation.runtime_revalidation_ledger
        ),
        "sample_size_sensitivity": design_path,
        "chromatic_formula_probes": ctx.resolve(DEFAULT_CHROMATIC_FORMULA_PROBES),
        "generated_derived_inputs": ctx.resolve(DEFAULT_GENERATED_DERIVED),
        "generated_learned_features": ctx.resolve(generated_feature_path),
        "generated_chromatic_features": ctx.resolve(DEFAULT_GENERATED_CHROMATIC),
        "projected_analysis_inputs": ctx.resolve(DEFAULT_PROJECTED_INPUTS),
    }
    return projected, prompts, artifacts


def _chromatic_analysis(
    ctx: Pilot2Context,
    *,
    prompts: Sequence[PromptRecord],
    bindings: Pilot2AnalysisBindings,
    ledger_path: Path = DEFAULT_ATTEMPT_LEDGER,
    real_derived_path: Path = DEFAULT_REAL_DERIVED,
    real_feature_path: Path = DEFAULT_REAL_CHROMATIC,
    generated_derived_path: Path = DEFAULT_GENERATED_DERIVED,
    generated_feature_path: Path = DEFAULT_GENERATED_CHROMATIC,
) -> Pilot2ChromaticSecondaryResult:
    """Join and summarize the explicitly non-gating chromatic evidence."""

    atlas = _load_atlas(ctx)
    cells, _ = _load_generation_plan(ctx, prompts)
    grid = grid_spec_from_config(ctx.config, prompt_records=prompts)
    real_derived = _load_models(ctx.resolve(real_derived_path), Pilot2DerivedInput)
    _validate_derived_preprocessing(real_derived, ctx.config, label="real chromatic")
    real_features = _load_models(ctx.resolve(real_feature_path), Pilot2ChromaticFeature)
    real_derived_by_work = {row.source_record_id: row for row in real_derived}
    real_feature_by_work = {row.source_record_id: row for row in real_features}
    work_ids = {row.canonical_work_id for row in atlas}
    if set(real_derived_by_work) != work_ids or set(real_feature_by_work) != work_ids:
        raise ValueError("chromatic real manifests do not cover the exact 40-work atlas")
    real_records = [
        {
            "canonical_work_id": work.canonical_work_id,
            "artist_id": work.artist_id,
            "source_id": work.source_id,
            "derived_input": real_derived_by_work[work.canonical_work_id],
            "feature": real_feature_by_work[work.canonical_work_id],
        }
        for work in atlas
    ]

    attempts = AppendOnlyAttemptLedger(ctx.resolve(ledger_path)).rows()
    terminal = terminal_records_for_analysis(cells, attempts)
    successful = {row.cell_id: row for row in terminal if row.outcome == "succeeded"}
    generated_derived = _load_models(ctx.resolve(generated_derived_path), Pilot2DerivedInput)
    _validate_derived_preprocessing(generated_derived, ctx.config, label="generated chromatic")
    generated_features = _load_models(ctx.resolve(generated_feature_path), Pilot2ChromaticFeature)
    generated_derived_by_cell = {row.source_record_id: row for row in generated_derived}
    generated_feature_by_cell = {row.source_record_id: row for row in generated_features}
    if set(generated_derived_by_cell) != set(successful) or set(generated_feature_by_cell) != set(
        successful
    ):
        raise ValueError("chromatic generated manifests do not cover exactly the successful cells")
    generated_records = [
        {
            "terminal_record": successful[cell_id],
            "derived_input": generated_derived_by_cell[cell_id],
            "feature": generated_feature_by_cell[cell_id],
        }
        for cell_id in successful
    ]
    completion = _self_hashed_json(ctx.resolve(DEFAULT_COMPLETION), "report_sha256")
    return summarize_chromatic_secondary(
        grid,
        real_records,
        generated_records,
        bindings=bindings,
        generation_cells=cells,
        generation_completion=completion,
    )


@app.command("analyze")
def analyze_command(
    root: Path = typer.Option(Path("."), "--root"),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    ledger_path: Path = typer.Option(DEFAULT_ATTEMPT_LEDGER, "--ledger"),
    generated_feature_path: Path = typer.Option(DEFAULT_GENERATED_FEATURES, "--generated-features"),
    projected_path: Path = typer.Option(DEFAULT_PROJECTED_INPUTS, "--projected-inputs"),
    output_path: Path = typer.Option(DEFAULT_ANALYSIS, "--output"),
    chromatic_output_path: Path = typer.Option(DEFAULT_CHROMATIC_ANALYSIS, "--chromatic-output"),
) -> None:
    """Project with the qualified PCA and run the frozen requested-label analysis."""

    ctx = _context(root, config_path)
    projected, prompts, _ = _analysis_inputs(
        ctx,
        ledger_path=ledger_path,
        generated_feature_path=generated_feature_path,
    )
    write_json(ctx.resolve(projected_path), projected)
    result = analyze_projected_pilot2(
        ctx.config,
        projected,
        prompt_records=prompts,
        protocol_preconditions_met=True,
    )
    write_json(ctx.resolve(output_path), result)
    chromatic = _chromatic_analysis(
        ctx,
        prompts=prompts,
        bindings=projected.bindings,
        ledger_path=ledger_path,
    )
    write_json(ctx.resolve(chromatic_output_path), chromatic)
    typer.echo(
        json.dumps(
            {
                "scientific_completion": result.scientific_completion.status,
                "all_four_primary_hypotheses_supported": (
                    result.all_four_primary_hypotheses_supported
                ),
                "projected_input_manifest_sha256": projected.manifest_sha256,
                "analysis_result_sha256": result.result_sha256,
                "chromatic_result_sha256": chromatic.result_sha256,
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command("report")
def report_command(
    root: Path = typer.Option(Path("."), "--root"),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
    analysis_path: Path = typer.Option(DEFAULT_ANALYSIS, "--analysis"),
    output_dir: Path = typer.Option(DEFAULT_REPORT_DIR, "--output-dir"),
) -> None:
    """Render the content-addressed JSON/Markdown report and artifact index."""

    ctx = _context(root, config_path)
    result = Pilot2AnalysisResult.model_validate(read_json(ctx.resolve(analysis_path)))
    chromatic = Pilot2ChromaticSecondaryResult.model_validate(
        read_json(ctx.resolve(DEFAULT_CHROMATIC_ANALYSIS))
    )
    projected = Pilot2ProjectedAnalysisInputs.model_validate(
        read_json(ctx.resolve(DEFAULT_PROJECTED_INPUTS))
    )
    if result.projected_input_manifest_sha256 != projected.manifest_sha256:
        raise RuntimeError("analysis result binds a different projected-input artifact")
    recomputed_projected, prompts, artifacts = _analysis_inputs(
        ctx,
        ledger_path=DEFAULT_ATTEMPT_LEDGER,
        generated_feature_path=DEFAULT_GENERATED_FEATURES,
    )
    if projected.model_dump(mode="json") != recomputed_projected.model_dump(mode="json"):
        raise RuntimeError("persisted projected-input artifact is stale")
    recomputed_result = analyze_projected_pilot2(
        ctx.config,
        recomputed_projected,
        prompt_records=prompts,
        protocol_preconditions_met=True,
    )
    _require_exact_primary_result(result, recomputed_result)
    recomputed_chromatic = _chromatic_analysis(
        ctx,
        prompts=prompts,
        bindings=projected.bindings,
    )
    if chromatic.model_dump(mode="json") != recomputed_chromatic.model_dump(mode="json"):
        raise RuntimeError("persisted chromatic secondary analysis is stale")
    rendered = write_pilot2_report(
        result,
        ctx.resolve(output_dir),
        evidence_root=ctx.root,
        input_artifacts=artifacts,
        chromatic_secondary=chromatic,
    )
    typer.echo(rendered.model_dump_json(indent=2))


@app.command("verify")
def verify_command(
    root: Path = typer.Option(Path("."), "--root"),
    config_path: Path = typer.Option(DEFAULT_CONFIG, "--config"),
) -> None:
    """Verify the complete pilot_2 evidence graph without sending requests."""

    ctx = _context(root, config_path)
    static = _validate_static_manifests(ctx, require_plan=True)
    result, contract_sha, gate = _qualification_context(ctx, require_gate=True)
    card = Pilot2QualificationCard.model_validate(
        read_json(ctx.resolve(ctx.config.qualification_artifacts.learned_card))
    )
    result_path = ctx.resolve(ctx.config.qualification_artifacts.learned_result)
    if (
        card.qualification_result_sha256 != result.result_sha256
        or card.qualification_contract_sha256 != contract_sha
        or card.evidence_artifact_sha256 != hash_file(result_path)
        or ctx.resolve(card.evidence_artifact_path) != result_path
        or card.status != result.status
        or card.feature_version != result.feature_version
        or card.feature_config_sha256 != result.feature_config_sha256
        or card.input_feature_manifest_sha256 != result.input_feature_manifest_sha256
        or card.input_acquired_manifest_sha256 != result.input_acquired_manifest_sha256
        or card.reasons != result.reasons
    ):
        raise RuntimeError("qualification card is stale")
    projected, prompts, expected_input_artifacts = _analysis_inputs(
        ctx,
        ledger_path=DEFAULT_ATTEMPT_LEDGER,
        generated_feature_path=DEFAULT_GENERATED_FEATURES,
    )
    persisted_projected = Pilot2ProjectedAnalysisInputs.model_validate(
        read_json(ctx.resolve(DEFAULT_PROJECTED_INPUTS))
    )
    if persisted_projected.model_dump(mode="json") != projected.model_dump(mode="json"):
        raise RuntimeError("persisted projected-input artifact is stale")
    analysis = Pilot2AnalysisResult.model_validate(read_json(ctx.resolve(DEFAULT_ANALYSIS)))
    recomputed = analyze_projected_pilot2(
        ctx.config,
        projected,
        prompt_records=prompts,
        protocol_preconditions_met=True,
    )
    _require_exact_primary_result(analysis, recomputed)
    chromatic = Pilot2ChromaticSecondaryResult.model_validate(
        read_json(ctx.resolve(DEFAULT_CHROMATIC_ANALYSIS))
    )
    recomputed_chromatic = _chromatic_analysis(
        ctx,
        prompts=prompts,
        bindings=projected.bindings,
    )
    if chromatic.model_dump(mode="json") != recomputed_chromatic.model_dump(mode="json"):
        raise RuntimeError("persisted chromatic secondary analysis is stale")
    report_analysis = Pilot2AnalysisResult.model_validate(
        read_json(ctx.resolve(DEFAULT_REPORT_DIR / "analysis.json"))
    )
    report_chromatic = Pilot2ChromaticSecondaryResult.model_validate(
        read_json(ctx.resolve(DEFAULT_REPORT_DIR / "chromatic_secondary.json"))
    )
    if report_analysis != analysis or report_chromatic != chromatic:
        raise RuntimeError("rendered report data views are stale")
    report_markdown = ctx.resolve(DEFAULT_REPORT_DIR / "REPORT.md")
    if not report_markdown.is_file():
        raise FileNotFoundError(report_markdown)
    index = Pilot2ArtifactIndex.model_validate(
        read_json(ctx.resolve(DEFAULT_REPORT_DIR / "artifact_index.json"))
    )
    index_payload = index.model_dump(mode="json", exclude={"index_payload_sha256"})
    if (
        index.analysis_result_sha256 != analysis.result_sha256
        or stable_hash(index_payload) != index.index_payload_sha256
    ):
        raise RuntimeError("report artifact index self-binding is stale")
    expected_index = artifact_index_data(
        analysis,
        {
            **expected_input_artifacts,
            "analysis_json": ctx.resolve(DEFAULT_REPORT_DIR / "analysis.json"),
            "report_markdown": report_markdown,
            "chromatic_secondary_json": ctx.resolve(
                DEFAULT_REPORT_DIR / "chromatic_secondary.json"
            ),
        },
        root=ctx.root,
    )
    if index.model_dump(mode="json") != expected_index.model_dump(mode="json"):
        raise RuntimeError("report artifact index omits or misbinds required evidence")
    for artifact in index.artifacts:
        path = ctx.resolve(artifact.path)
        try:
            path.relative_to(ctx.root)
        except ValueError as exc:
            raise RuntimeError("report artifact index points outside the repository") from exc
        if (
            not path.is_file()
            or hash_file(path) != artifact.sha256
            or path.stat().st_size != artifact.size_bytes
        ):
            raise RuntimeError(f"indexed report artifact is missing or stale: {artifact.path}")
    typer.echo(
        json.dumps(
            {
                **static,
                "qualification_status": result.status,
                "generation_gate_sha256": gate["gate_sha256"],
                "projected_input_manifest_sha256": projected.manifest_sha256,
                "analysis_result_sha256": analysis.result_sha256,
                "chromatic_result_sha256": chromatic.result_sha256,
                "scientific_completion": analysis.scientific_completion.status,
                "verification": "pass_offline_no_image_requests",
            },
            indent=2,
            sort_keys=True,
        )
    )


__all__ = ["GeneratedLearnedFeature", "app"]
