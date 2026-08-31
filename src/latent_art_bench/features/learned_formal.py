from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import io
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Literal, Optional, Tuple

import numpy as np
import PIL
from PIL import Image
from PIL import features as pillow_features

from latent_art_bench.io import hash_file

SOURCE_REPOSITORY = "https://github.com/aljinny/art-history"
SOURCE_REVISION = "7da12358cf34dad2184f357a048c2cf114b3c4e0"
MODEL_REPOSITORY = "stabilityai/stable-diffusion-2-base"
INPUT_SIZE = (512, 512)
LATENT_SHAPE = (4, 64, 64)
LATENT_SCALE = 0.18215
FLATTEN_ORDER = "C"
SOURCE_FILE_FEATURE_VERSION = "kim2026-sd20-a-vector-source-file-seeded-sample-v2"
IN_MEMORY_FEATURE_VERSION = "kim2026-sd20-a-vector-seeded-sample-v1"

SamplingPolicy = Literal["seeded_posterior_sample", "posterior_mode"]
SOURCE_REPLICATION_POLICY: SamplingPolicy = "seeded_posterior_sample"
DETERMINISTIC_BENCHMARK_POLICY: SamplingPolicy = "posterior_mode"


class LearnedFormalError(RuntimeError):
    pass


class OptionalDependencyError(LearnedFormalError):
    pass


class ProvenanceVerificationError(LearnedFormalError):
    pass


class LatentContractError(LearnedFormalError):
    pass


def _is_lower_hex(value: str, length: int) -> bool:
    return len(value) == length and all(character in "0123456789abcdef" for character in value)


@dataclass(frozen=True)
class LearnedFormalPins:
    """Immutable identities required before loading the local SD2-base VAE snapshot."""

    model_revision: str
    config_sha256: str
    weights_sha256: str
    source_repository: str = SOURCE_REPOSITORY
    source_revision: str = SOURCE_REVISION
    model_repository: str = MODEL_REPOSITORY

    def __post_init__(self) -> None:
        for name, value in (
            ("source_revision", self.source_revision),
            ("model_revision", self.model_revision),
        ):
            if not _is_lower_hex(value, 40):
                raise ValueError(f"{name} must be an immutable 40-character lowercase Git SHA")
        for name, value in (
            ("config_sha256", self.config_sha256),
            ("weights_sha256", self.weights_sha256),
        ):
            if not _is_lower_hex(value, 64):
                raise ValueError(f"{name} must be a 64-character lowercase SHA-256")
        if not self.source_repository.strip() or not self.model_repository.strip():
            raise ValueError("repository identities must not be blank")


@dataclass(frozen=True)
class ArtifactVerification:
    pins: LearnedFormalPins
    config_path: str
    weights_path: str
    source_checkout: Optional[str]
    source_checkout_verified: bool

    def metadata(self) -> Dict[str, object]:
        return {
            "source_repository": self.pins.source_repository,
            "source_revision": self.pins.source_revision,
            "source_checkout_verified": self.source_checkout_verified,
            "model_repository": self.pins.model_repository,
            "model_revision": self.pins.model_revision,
            "config_sha256": self.pins.config_sha256,
            "weights_sha256": self.pins.weights_sha256,
            "artifacts_verified": True,
        }


@dataclass(frozen=True)
class LoadedSD2VAE:
    vae: Any
    verification: ArtifactVerification


@dataclass(frozen=True)
class LearnedFormalResult:
    vector: np.ndarray
    metadata: Dict[str, object]


@dataclass(frozen=True)
class SourceFilePreparation:
    rgb: np.ndarray
    source_sha256: str
    source_extension: str
    intermediate_payload_sha256: str
    opencv_version: str
    opencv_build_sha256: str
    pillow_version: str


def _optional_module(name: str, purpose: str) -> Any:
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise OptionalDependencyError(
            f"{name} is required for {purpose}; install it in the isolated learned-formal "
            "environment"
        ) from exc


def verify_file_sha256(path: Path, expected_sha256: str, label: str) -> str:
    if not _is_lower_hex(expected_sha256, 64):
        raise ValueError("expected_sha256 must be a 64-character lowercase SHA-256")
    path = Path(path)
    if not path.is_file():
        raise ProvenanceVerificationError(f"missing pinned {label}: {path}")
    observed = hash_file(path)
    if observed != expected_sha256:
        raise ProvenanceVerificationError(
            f"{label} SHA-256 mismatch: expected {expected_sha256}, found {observed}"
        )
    return observed


def _normalized_repository(value: str) -> str:
    normalized = value.strip().rstrip("/")
    return normalized[:-4] if normalized.endswith(".git") else normalized


def verify_source_checkout(
    checkout: Path,
    expected_repository: str = SOURCE_REPOSITORY,
    expected_revision: str = SOURCE_REVISION,
    runner: Callable[..., Any] = subprocess.run,
) -> Tuple[str, str]:
    checkout = Path(checkout)
    if not checkout.is_dir():
        raise ProvenanceVerificationError(f"missing source checkout: {checkout}")
    try:
        revision_result = runner(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        repository_result = runner(
            ["git", "-C", str(checkout), "config", "--get", "remote.origin.url"],
            check=True,
            capture_output=True,
            text=True,
        )
        status_result = runner(
            [
                "git",
                "-C",
                str(checkout),
                "status",
                "--porcelain=v1",
                "--untracked-files=no",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ProvenanceVerificationError(
            f"cannot inspect source checkout {checkout}: {exc}"
        ) from exc
    observed_revision = revision_result.stdout.strip()
    observed_repository = repository_result.stdout.strip()
    if status_result.stdout.strip():
        raise ProvenanceVerificationError(
            f"source checkout has modified tracked files: {checkout}"
        )
    if observed_revision != expected_revision:
        raise ProvenanceVerificationError(
            "source revision mismatch: "
            f"expected {expected_revision}, found {observed_revision or '<empty>'}"
        )
    if _normalized_repository(observed_repository) != _normalized_repository(expected_repository):
        raise ProvenanceVerificationError(
            "source repository mismatch: "
            f"expected {expected_repository}, found {observed_repository or '<empty>'}"
        )
    return observed_repository, observed_revision


def verify_pinned_artifacts(
    pins: LearnedFormalPins,
    config_path: Path,
    weights_path: Path,
    source_checkout: Optional[Path] = None,
    runner: Callable[..., Any] = subprocess.run,
) -> ArtifactVerification:
    verify_file_sha256(config_path, pins.config_sha256, "SD2 VAE config")
    verify_file_sha256(weights_path, pins.weights_sha256, "SD2 VAE weights")
    source_verified = False
    if source_checkout is not None:
        verify_source_checkout(
            source_checkout,
            expected_repository=pins.source_repository,
            expected_revision=pins.source_revision,
            runner=runner,
        )
        source_verified = True
    return ArtifactVerification(
        pins=pins,
        config_path=str(Path(config_path).resolve()),
        weights_path=str(Path(weights_path).resolve()),
        source_checkout=str(Path(source_checkout).resolve()) if source_checkout else None,
        source_checkout_verified=source_verified,
    )


def load_pinned_sd2_vae(
    snapshot_dir: Path,
    pins: LearnedFormalPins,
    config_relative_path: Path = Path("vae/config.json"),
    weights_relative_path: Path = Path("vae/diffusion_pytorch_model.safetensors"),
    source_checkout: Optional[Path] = None,
    torch_module: Optional[Any] = None,
    diffusers_module: Optional[Any] = None,
) -> LoadedSD2VAE:
    """Verify a local immutable snapshot before allowing Diffusers to load it."""

    snapshot_dir = Path(snapshot_dir)
    config_path = snapshot_dir / config_relative_path
    weights_path = snapshot_dir / weights_relative_path
    verification = verify_pinned_artifacts(
        pins,
        config_path=config_path,
        weights_path=weights_path,
        source_checkout=source_checkout,
    )
    torch_module = torch_module or _optional_module("torch", "SD2 VAE inference")
    diffusers_module = diffusers_module or _optional_module("diffusers", "SD2 VAE loading")
    autoencoder = getattr(diffusers_module, "AutoencoderKL", None)
    if autoencoder is None:
        raise OptionalDependencyError("diffusers.AutoencoderKL is required for SD2 VAE loading")
    model_kwargs = {
        "local_files_only": True,
        "torch_dtype": torch_module.float32,
        "use_safetensors": weights_path.suffix == ".safetensors",
    }
    artifact_parent = config_relative_path.parent
    if artifact_parent != Path("."):
        model_kwargs["subfolder"] = str(artifact_parent)
    vae = autoencoder.from_pretrained(str(snapshot_dir), **model_kwargs)
    vae.to(device="cpu")
    vae.eval()
    return LoadedSD2VAE(vae=vae, verification=verification)


def _rgb_array(image: Any) -> np.ndarray:
    if isinstance(image, Image.Image):
        rgb = np.asarray(image.convert("RGB"), dtype=np.uint8)
    else:
        rgb = np.asarray(image)
        if rgb.ndim != 3 or rgb.shape[2] not in (3, 4):
            raise ValueError("learned-formal input must have shape H x W x 3 or H x W x 4")
        if rgb.dtype != np.uint8:
            if not np.issubdtype(rgb.dtype, np.number) or not np.isfinite(rgb).all():
                raise ValueError("learned-formal input must contain finite numeric values")
            if float(rgb.min()) < 0.0 or float(rgb.max()) > 255.0:
                raise ValueError("learned-formal input values must be in [0, 255]")
            rgb = np.rint(rgb).astype(np.uint8)
        if rgb.shape[2] == 4:
            rgb = np.asarray(Image.fromarray(rgb, mode="RGBA").convert("RGB"), dtype=np.uint8)
    return np.ascontiguousarray(rgb)


def resize_source_rgb(image: Any, cv2_module: Optional[Any] = None) -> np.ndarray:
    """Apply the paper/source 512-square OpenCV INTER_LANCZOS4 transform."""

    cv2_module = cv2_module or _optional_module("cv2", "Kim et al. source preprocessing")
    interpolation = getattr(cv2_module, "INTER_LANCZOS4", None)
    if interpolation is None:
        raise OptionalDependencyError("cv2.INTER_LANCZOS4 is required for source preprocessing")
    resized = cv2_module.resize(_rgb_array(image), INPUT_SIZE, interpolation=interpolation)
    resized = np.asarray(resized, dtype=np.uint8)
    if resized.shape != (INPUT_SIZE[1], INPUT_SIZE[0], 3):
        raise LatentContractError(f"OpenCV resize returned {resized.shape}; expected (512, 512, 3)")
    return np.ascontiguousarray(resized)


def prepare_source_file_rgb(
    path: Path, cv2_module: Optional[Any] = None
) -> SourceFilePreparation:
    """Reproduce the released cv2 resize/write then Pillow RGB-read path."""

    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"missing learned-formal source image: {path}")
    cv2_module = cv2_module or _optional_module(
        "cv2", "Kim et al. source-file preprocessing"
    )
    imread_color = getattr(cv2_module, "IMREAD_COLOR", 1)
    decoded = cv2_module.imread(str(path), imread_color)
    if decoded is None:
        raise LearnedFormalError(f"OpenCV could not decode source image: {path}")
    color_swap = getattr(cv2_module, "COLOR_RGB2BGR", None)
    if color_swap is None:
        raise OptionalDependencyError(
            "cv2.COLOR_RGB2BGR is required for source-file preprocessing"
        )
    interpolation = getattr(cv2_module, "INTER_LANCZOS4", None)
    if interpolation is None:
        raise OptionalDependencyError(
            "cv2.INTER_LANCZOS4 is required for source-file preprocessing"
        )

    # These two channel swaps deliberately mirror the released script around
    # cv2.resize. OpenCV decodes/writes BGR, while the intermediate array is RGB.
    rgb = cv2_module.cvtColor(np.asarray(decoded), color_swap)
    resized_rgb = cv2_module.resize(rgb, INPUT_SIZE, interpolation=interpolation)
    encoded_bgr = cv2_module.cvtColor(np.asarray(resized_rgb), color_swap)
    extension = path.suffix.lower()
    if extension == ".jpeg":
        extension = ".jpg"
    if extension not in {".jpg", ".png", ".webp"}:
        raise LearnedFormalError(
            f"unsupported source extension for released resize/write path: {path.suffix}"
        )
    success, encoded = cv2_module.imencode(extension, encoded_bgr)
    if not success:
        raise LearnedFormalError(
            f"OpenCV could not encode the resized {extension} intermediate for {path}"
        )
    payload = np.asarray(encoded, dtype=np.uint8).tobytes()
    opencv_version = str(getattr(cv2_module, "__version__", "unknown"))
    build_information = getattr(cv2_module, "getBuildInformation", None)
    if not callable(build_information):
        raise OptionalDependencyError(
            "cv2.getBuildInformation is required to bind the source preprocessing runtime"
        )
    opencv_build_sha256 = hashlib.sha256(
        str(build_information()).encode("utf-8")
    ).hexdigest()

    with Image.open(io.BytesIO(payload)) as image:
        image = image.convert("RGB")
        width, height = image.size
        width, height = (value - value % 64 for value in (width, height))
        image = image.resize((width, height), resample=Image.Resampling.LANCZOS)
        prepared = np.asarray(image, dtype=np.uint8)
    if prepared.shape != (INPUT_SIZE[1], INPUT_SIZE[0], 3):
        raise LatentContractError(
            f"source-file preprocessing returned {prepared.shape}; expected (512, 512, 3)"
        )
    return SourceFilePreparation(
        rgb=np.ascontiguousarray(prepared),
        source_sha256=hash_file(path),
        source_extension=extension,
        intermediate_payload_sha256=hashlib.sha256(payload).hexdigest(),
        opencv_version=opencv_version,
        opencv_build_sha256=opencv_build_sha256,
        pillow_version=PIL.__version__,
    )


def rgb_to_model_array(resized_rgb: np.ndarray) -> np.ndarray:
    rgb = np.asarray(resized_rgb)
    if rgb.shape != (INPUT_SIZE[1], INPUT_SIZE[0], 3) or rgb.dtype != np.uint8:
        raise ValueError("resized RGB input must be uint8 with shape (512, 512, 3)")
    chw = rgb.astype(np.float32).transpose(2, 0, 1)[None, ...]
    return np.ascontiguousarray(chw / np.float32(127.5) - np.float32(1.0))


def resized_content_sha256(resized_rgb: np.ndarray) -> str:
    rgb = np.asarray(resized_rgb)
    if rgb.shape != (INPUT_SIZE[1], INPUT_SIZE[0], 3) or rgb.dtype != np.uint8:
        raise ValueError("content hashing requires uint8 RGB with shape (512, 512, 3)")
    digest = hashlib.sha256()
    digest.update(b"latent-art-bench:sd2-source-rgb:512x512:v1\0")
    digest.update(np.ascontiguousarray(rgb).tobytes(order="C"))
    return digest.hexdigest()


def learned_formal_vector_sha256(values: Any) -> str:
    """Hash a learned-formal vector with an explicit float32 byte contract."""

    vector = np.asarray(values, dtype="<f4")
    digest = hashlib.sha256()
    digest.update(str(vector.shape).encode("ascii"))
    digest.update(b"\0float32-le\0C\0")
    digest.update(np.ascontiguousarray(vector).tobytes(order="C"))
    return digest.hexdigest()


def derive_content_seed(resized_rgb: np.ndarray, base_seed: int = 0) -> int:
    if base_seed < 0 or base_seed >= 2**63:
        raise ValueError("base_seed must be in [0, 2**63)")
    digest = hashlib.sha256()
    digest.update(b"latent-art-bench:kim2026-a-vector-seed:v1\0")
    digest.update(base_seed.to_bytes(8, "big", signed=False))
    digest.update(bytes.fromhex(resized_content_sha256(resized_rgb)))
    return int.from_bytes(digest.digest()[:8], "big", signed=False) & ((1 << 63) - 1)


def _resolve_device(torch_module: Any, requested: str) -> str:
    if requested != "auto":
        if requested not in {"cpu", "mps", "cuda"}:
            raise ValueError("device must be one of auto, cpu, mps, or cuda")
        return requested
    mps = getattr(getattr(torch_module, "backends", None), "mps", None)
    if mps is not None and callable(getattr(mps, "is_available", None)) and mps.is_available():
        return "mps"
    cuda = getattr(torch_module, "cuda", None)
    if cuda is not None and callable(getattr(cuda, "is_available", None)) and cuda.is_available():
        return "cuda"
    return "cpu"


def runtime_environment_metadata(torch_module: Any) -> Dict[str, object]:
    """Describe the numerical/codec runtime that can affect extracted A-vectors."""

    mps = getattr(getattr(torch_module, "backends", None), "mps", None)
    is_built = getattr(mps, "is_built", None)
    is_available = getattr(mps, "is_available", None)
    return {
        "python_version": platform.python_version(),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_machine": platform.machine(),
        "numpy_version": np.__version__,
        "torch_version": importlib.metadata.version("torch"),
        "diffusers_version": importlib.metadata.version("diffusers"),
        "jpeg_codec_version": pillow_features.version("jpg"),
        "torch_mps_built": bool(is_built()) if callable(is_built) else None,
        "torch_mps_available": (
            bool(is_available()) if callable(is_available) else None
        ),
    }


def _posterior_from_encoded(encoded: Any) -> Any:
    return getattr(encoded, "latent_dist", encoded)


def _posterior_mode(posterior: Any) -> Any:
    mode = getattr(posterior, "mode", None)
    if callable(mode):
        return mode()
    mean = getattr(posterior, "mean", None)
    if mean is None:
        raise LatentContractError("posterior_mode requires posterior.mode() or posterior.mean")
    return mean


def _seeded_posterior_sample(posterior: Any, seed: int, torch_module: Any) -> Any:
    mean = getattr(posterior, "mean", None)
    std = getattr(posterior, "std", None)
    if mean is None or std is None:
        raise LatentContractError("seeded sampling requires posterior.mean and posterior.std")
    generator = torch_module.Generator(device="cpu")
    generator.manual_seed(seed)
    noise = torch_module.randn(
        tuple(mean.shape),
        generator=generator,
        device="cpu",
        dtype=torch_module.float32,
    )
    noise = noise.to(device=mean.device, dtype=mean.dtype)
    return mean + std * noise


def scale_and_flatten_latent(latent: Any) -> np.ndarray:
    if hasattr(latent, "detach"):
        latent = latent.detach()
    if hasattr(latent, "to"):
        latent = latent.to(device="cpu")
    if hasattr(latent, "numpy"):
        latent = latent.numpy()
    array = np.asarray(latent, dtype=np.float32)
    if array.shape == (1, *LATENT_SHAPE):
        array = array[0]
    if array.shape != LATENT_SHAPE:
        raise LatentContractError(
            f"SD2 VAE latent has shape {array.shape}; expected {LATENT_SHAPE}"
        )
    scaled = np.ascontiguousarray(array * np.float32(LATENT_SCALE))
    vector = scaled.flatten(order=FLATTEN_ORDER)
    if vector.shape != (int(np.prod(LATENT_SHAPE)),) or not np.isfinite(vector).all():
        raise LatentContractError("learned-formal vector is malformed or non-finite")
    return vector


def extract_learned_formal(
    image: Any,
    loaded_vae: LoadedSD2VAE,
    policy: SamplingPolicy = SOURCE_REPLICATION_POLICY,
    seed: Optional[int] = None,
    base_seed: int = 0,
    device: str = "auto",
    torch_module: Optional[Any] = None,
    cv2_module: Optional[Any] = None,
) -> LearnedFormalResult:
    """Extract a Kim-style 16,384-value A-vector with an explicit latent policy."""

    if policy not in {SOURCE_REPLICATION_POLICY, DETERMINISTIC_BENCHMARK_POLICY}:
        raise ValueError(f"unsupported learned-formal policy: {policy}")
    torch_module = torch_module or _optional_module("torch", "SD2 VAE inference")
    resolved_device = _resolve_device(torch_module, device)
    if isinstance(image, (str, Path)):
        preparation = prepare_source_file_rgb(Path(image), cv2_module=cv2_module)
        resized = preparation.rgb
        preprocessing_metadata: Dict[str, object] = {
            "source_input_role": "original_reproduction_file",
            "source_preprocessing_policy": (
                "opencv_imread_resize_imwrite_same_extension_then_pillow_rgb"
            ),
            "source_file_sha256": preparation.source_sha256,
            "source_extension": preparation.source_extension,
            "intermediate_payload_sha256": preparation.intermediate_payload_sha256,
            "intermediate_encoding": preparation.source_extension.lstrip("."),
            "opencv_version": preparation.opencv_version,
            "opencv_build_sha256": preparation.opencv_build_sha256,
            "pillow_version": preparation.pillow_version,
        }
        source_file_contract = True
    else:
        resized = resize_source_rgb(image, cv2_module=cv2_module)
        preprocessing_metadata = {
            "source_input_role": "in_memory_rgb",
            "source_preprocessing_policy": "opencv_resize_without_file_roundtrip",
            "source_file_sha256": None,
            "source_extension": None,
            "intermediate_payload_sha256": None,
            "intermediate_encoding": None,
            "opencv_version": str(getattr(cv2_module, "__version__", "unknown")),
            "opencv_build_sha256": None,
            "pillow_version": PIL.__version__,
        }
        source_file_contract = False
    content_sha256 = resized_content_sha256(resized)
    model_array = rgb_to_model_array(resized)

    effective_seed: Optional[int] = None
    seed_strategy = "not_applicable"
    if policy == SOURCE_REPLICATION_POLICY:
        if seed is None:
            effective_seed = derive_content_seed(resized, base_seed=base_seed)
            seed_strategy = "sha256_of_resized_rgb_plus_base_seed"
        else:
            if seed < 0 or seed >= 2**63:
                raise ValueError("seed must be in [0, 2**63)")
            effective_seed = seed
            seed_strategy = "explicit"

    vae = loaded_vae.vae
    vae.to(device=resolved_device)
    vae.eval()
    tensor = torch_module.from_numpy(model_array)
    tensor = tensor.to(device=resolved_device, dtype=torch_module.float32)
    with torch_module.inference_mode():
        posterior = _posterior_from_encoded(vae.encode(tensor))
        if policy == SOURCE_REPLICATION_POLICY:
            assert effective_seed is not None
            latent = _seeded_posterior_sample(posterior, effective_seed, torch_module)
            role = "source_replication_seeded_posterior_sample"
            feature_version = (
                SOURCE_FILE_FEATURE_VERSION
                if source_file_contract
                else IN_MEMORY_FEATURE_VERSION
            )
        else:
            latent = _posterior_mode(posterior)
            role = "deterministic_benchmark_deviation_posterior_mode"
            feature_version = (
                "kim2026-sd20-a-vector-source-file-posterior-mode-v2"
                if source_file_contract
                else "kim2026-sd20-a-vector-posterior-mode-v1"
            )
    vector = scale_and_flatten_latent(latent)

    metadata: Dict[str, object] = {
        "feature_version": feature_version,
        "representation_role": role,
        "policy": policy,
        "seed": effective_seed,
        "seed_strategy": seed_strategy,
        "base_seed": base_seed if policy == SOURCE_REPLICATION_POLICY else None,
        "seed_basis_sha256": content_sha256,
        "input_size": list(INPUT_SIZE),
        "input_color_order": "RGB",
        "input_tensor_range": [-1.0, 1.0],
        "resize_library": "opencv",
        "resize_interpolation": "INTER_LANCZOS4",
        "latent_shape": list(LATENT_SHAPE),
        "latent_scale": LATENT_SCALE,
        "latent_scale_application": "explicit_after_encode",
        "flatten_order": FLATTEN_ORDER,
        "vector_length": int(vector.size),
        "device": resolved_device,
        "dtype": "float32",
        "vector_sha256": learned_formal_vector_sha256(vector),
        **runtime_environment_metadata(torch_module),
        **preprocessing_metadata,
        **loaded_vae.verification.metadata(),
    }
    return LearnedFormalResult(vector=vector, metadata=metadata)
