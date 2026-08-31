from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

from latent_art_bench.config import PilotConfig
from latent_art_bench.evaluation import vae_equivalence
from latent_art_bench.io import hash_file, read_json, stable_hash

_COMMON_QUALIFICATION_CODE = (
    "src/latent_art_bench/config.py",
    "src/latent_art_bench/evaluation/contracts.py",
    "src/latent_art_bench/evaluation/qualification.py",
    "src/latent_art_bench/evaluation/qualification_orchestration.py",
    "src/latent_art_bench/io.py",
    "src/latent_art_bench/manifests.py",
    "src/latent_art_bench/schemas.py",
)

_MEASUREMENT_CODE = {
    "chromatic": (
        "src/latent_art_bench/evaluation/chromatic_v2.py",
        "src/latent_art_bench/features/chromatic.py",
        "src/latent_art_bench/preprocessing/pipeline.py",
    ),
    "learned_formal": (
        "src/latent_art_bench/evaluation/distances.py",
        "src/latent_art_bench/evaluation/learned_formal_v2.py",
        "src/latent_art_bench/evaluation/vae_equivalence.py",
        "src/latent_art_bench/features/learned_formal.py",
        "src/latent_art_bench/features/learned_pipeline.py",
    ),
}


def measurement_code_closure(root: Path, measurement: str) -> Dict[str, str]:
    """Hash only source files that can change a measurement qualification result."""

    if measurement not in _MEASUREMENT_CODE:
        raise ValueError(f"unsupported qualification measurement: {measurement}")
    paths = sorted(set(_COMMON_QUALIFICATION_CODE + _MEASUREMENT_CODE[measurement]))
    closure: Dict[str, str] = {}
    for relative in paths:
        path = root / relative
        if not path.is_file():
            raise RuntimeError(f"qualification code-closure file is missing: {relative}")
        closure[relative] = hash_file(path)
    return closure


def qualification_contract(
    config: PilotConfig, measurement: str, root: Path
) -> Tuple[str, Dict[str, object]]:
    """Bind a pilot_1 card to data, config, code, and dependency identities."""

    if measurement not in config.measurements.required:
        raise ValueError(f"measurement is not required by {config.pilot_id}: {measurement}")
    root = root.resolve()
    canonical_path = root / config.corpus.canonical_manifest
    reproduction_path = root / config.corpus.reproduction_manifest
    observed_canonical = hash_file(canonical_path)
    observed_reproductions = hash_file(reproduction_path)
    if config.pilot_id == "pilot_1":
        if observed_canonical != config.corpus.canonical_manifest_sha256:
            raise RuntimeError("canonical manifest hash does not match the pilot_1 pin")
        if observed_reproductions != config.corpus.reproduction_manifest_sha256:
            raise RuntimeError("reproduction manifest hash does not match the pilot_1 pin")
    lock_path = root / "uv.lock"
    code_closure = measurement_code_closure(root, measurement)
    payload: Dict[str, object] = {
        "schema_version": "2.0",
        "pilot_id": config.pilot_id,
        "measurement": measurement,
        "resolved_config": config.model_dump(mode="json"),
        "canonical_manifest_sha256": observed_canonical,
        "reproduction_manifest_sha256": observed_reproductions,
        "measurement_code_closure": code_closure,
        "measurement_implementation_sha256": stable_hash(code_closure),
        "dependency_lock_sha256": hash_file(lock_path),
        "project_configuration_sha256": hash_file(root / "pyproject.toml"),
    }
    if measurement == "learned_formal":
        learned = config.measurements.learned_formal
        if learned.model_verification_report is None:
            raise RuntimeError("learned-formal qualification lacks model verification evidence")
        report_path = root / learned.model_verification_report
        report = read_json(report_path)
        if not isinstance(report, dict) or report.get("verification_status") != "pass":
            raise RuntimeError("learned-formal model verification did not pass")
        comparison = report.get("comparison", {})
        mapping = report.get("mapping", {})
        artifacts = report.get("artifacts", {})
        model = report.get("model", {})
        verifier = report.get("verifier", {})
        if (
            model.get("identity_profile") != "pinned_sd2_base"
            or model.get("revision") != learned.model_revision
            or comparison.get("mismatch_count") != 0
            or comparison.get("canonical_tensor_sets_equal") is not True
            or mapping.get("expected_tensor_count") != 248
            or comparison.get("exact_equal_count") != 248
        ):
            raise RuntimeError("learned-formal model verification is incomplete")
        if (
            artifacts.get("full_checkpoint", {}).get("sha256")
            != learned.full_checkpoint_sha256
            or artifacts.get("vae_weights", {}).get("sha256")
            != learned.model_weights_sha256
            or artifacts.get("vae_config", {}).get("sha256")
            != learned.model_config_sha256
        ):
            raise RuntimeError("learned-formal model verification artifact pins are stale")
        verifier_path = Path(str(vae_equivalence.__file__)).resolve()
        if (
            verifier.get("module")
            != "latent_art_bench.evaluation.vae_equivalence"
            or verifier.get("module_sha256") != hash_file(verifier_path)
        ):
            raise RuntimeError("learned-formal model verifier implementation is stale")
        payload["model_verification_report"] = str(report_path.relative_to(root))
        payload["model_verification_report_sha256"] = hash_file(report_path)
    return stable_hash(payload), payload


def expected_qualification_identities(
    config: PilotConfig, root: Path
) -> Dict[str, tuple]:
    identities = config.measurement_identities()
    if config.pilot_id != "pilot_1":
        return identities
    return {
        measurement: (
            *identities[measurement],
            qualification_contract(config, measurement, root)[0],
        )
        for measurement in config.measurements.required
    }
