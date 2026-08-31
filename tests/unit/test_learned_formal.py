from __future__ import annotations

import hashlib
import io
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from latent_art_bench.features.learned_formal import (
    DETERMINISTIC_BENCHMARK_POLICY,
    INPUT_SIZE,
    LATENT_SCALE,
    LATENT_SHAPE,
    MODEL_REPOSITORY,
    SOURCE_FILE_FEATURE_VERSION,
    SOURCE_REPLICATION_POLICY,
    SOURCE_REPOSITORY,
    SOURCE_REVISION,
    ArtifactVerification,
    LatentContractError,
    LearnedFormalPins,
    LoadedSD2VAE,
    OptionalDependencyError,
    ProvenanceVerificationError,
    _optional_module,
    derive_content_seed,
    extract_learned_formal,
    load_pinned_sd2_vae,
    prepare_source_file_rgb,
    resize_source_rgb,
    rgb_to_model_array,
    scale_and_flatten_latent,
    verify_file_sha256,
    verify_pinned_artifacts,
    verify_source_checkout,
)


class FakeCV2:
    INTER_LANCZOS4 = 41

    def __init__(self) -> None:
        self.calls = []

    def resize(self, image, size, interpolation):
        self.calls.append((np.array(image, copy=True), size, interpolation))
        # A deterministic stand-in for OpenCV. It intentionally makes the
        # resized pixels depend on the input for content-derived seed tests.
        color = np.asarray(image, dtype=np.uint8)[0, 0, :3]
        return np.broadcast_to(color, (size[1], size[0], 3)).copy()


class FakeTensor:
    def __init__(self, values, device="cpu", dtype="float32") -> None:
        self.values = np.asarray(values, dtype=np.float32)
        self.device = device
        self.dtype = dtype

    @property
    def shape(self):
        return self.values.shape

    def to(self, device=None, dtype=None):
        if device is not None:
            self.device = device
        if dtype is not None:
            self.dtype = dtype
        return self

    def detach(self):
        return self

    def numpy(self):
        return np.array(self.values, copy=True)

    def __mul__(self, other):
        values = other.values if isinstance(other, FakeTensor) else other
        return FakeTensor(self.values * values, device=self.device, dtype=self.dtype)

    def __rmul__(self, other):
        return self * other

    def __add__(self, other):
        values = other.values if isinstance(other, FakeTensor) else other
        return FakeTensor(self.values + values, device=self.device, dtype=self.dtype)


class FakeGenerator:
    def __init__(self, device):
        assert device == "cpu"
        self.seed = None

    def manual_seed(self, seed):
        self.seed = seed
        return self


class FakeTorch:
    float32 = "float32"

    def __init__(self, mps_available=False) -> None:
        self.backends = SimpleNamespace(mps=SimpleNamespace(is_available=lambda: mps_available))
        self.cuda = SimpleNamespace(is_available=lambda: False)
        self.randn_devices = []

    def Generator(self, device):
        return FakeGenerator(device)

    def randn(self, shape, generator, device, dtype):
        assert device == "cpu"
        assert dtype == self.float32
        self.randn_devices.append(device)
        values = np.random.default_rng(generator.seed).standard_normal(shape).astype(np.float32)
        return FakeTensor(values, device=device, dtype=dtype)

    def from_numpy(self, values):
        return FakeTensor(values)

    @staticmethod
    def inference_mode():
        return nullcontext()


class FakePosterior:
    def __init__(self, mean, std) -> None:
        self.mean = FakeTensor(mean)
        self.std = FakeTensor(std)

    def mode(self):
        return self.mean


class FakeVAE:
    def __init__(self, posterior) -> None:
        self.posterior = posterior
        self.to_calls = []
        self.eval_count = 0
        self.last_input = None

    def to(self, **kwargs):
        self.to_calls.append(kwargs)
        return self

    def eval(self):
        self.eval_count += 1
        return self

    def encode(self, tensor):
        self.last_input = tensor
        self.posterior.mean.to(device=tensor.device, dtype=tensor.dtype)
        self.posterior.std.to(device=tensor.device, dtype=tensor.dtype)
        return SimpleNamespace(latent_dist=self.posterior)


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def pins(config=b"config", weights=b"weights") -> LearnedFormalPins:
    return LearnedFormalPins(
        model_revision="1" * 40,
        config_sha256=digest(config),
        weights_sha256=digest(weights),
    )


def loaded_fake(mean=None, std=None):
    mean = np.zeros((1, *LATENT_SHAPE), dtype=np.float32) if mean is None else mean
    std = np.ones((1, *LATENT_SHAPE), dtype=np.float32) if std is None else std
    fake_vae = FakeVAE(FakePosterior(mean, std))
    verification = ArtifactVerification(
        pins=pins(),
        config_path="/verified/vae/config.json",
        weights_path="/verified/vae/weights.safetensors",
        source_checkout=None,
        source_checkout_verified=False,
    )
    return LoadedSD2VAE(fake_vae, verification), fake_vae


def test_source_resize_forces_square_opencv_lanczos4() -> None:
    cv2 = FakeCV2()
    source = np.zeros((7, 11, 3), dtype=np.uint8)
    source[0, 0] = [3, 7, 11]

    resized = resize_source_rgb(source, cv2_module=cv2)

    assert resized.shape == (512, 512, 3)
    assert resized.dtype == np.uint8
    assert resized[400, 300].tolist() == [3, 7, 11]
    assert len(cv2.calls) == 1
    _, size, interpolation = cv2.calls[0]
    assert size == INPUT_SIZE
    assert interpolation == FakeCV2.INTER_LANCZOS4


def test_source_file_preprocessing_matches_released_file_roundtrip(
    tmp_path: Path,
) -> None:
    cv2 = pytest.importorskip("cv2")
    y, x = np.indices((73, 91), dtype=np.uint16)
    source = np.stack(
        ((x * 7 + y) % 256, (x + y * 9) % 256, (x * 3 + y * 5) % 256),
        axis=2,
    ).astype(np.uint8)
    path = tmp_path / "source.jpg"
    Image.fromarray(source).save(path, format="JPEG", quality=89)

    decoded = cv2.imread(str(path), cv2.IMREAD_COLOR)
    upstream_rgb = cv2.cvtColor(np.asarray(decoded), cv2.COLOR_RGB2BGR)
    upstream_resized = cv2.resize(
        upstream_rgb, INPUT_SIZE, interpolation=cv2.INTER_LANCZOS4
    )
    upstream_bgr = cv2.cvtColor(upstream_resized, cv2.COLOR_RGB2BGR)
    success, payload = cv2.imencode(".jpg", upstream_bgr)
    assert success
    with Image.open(io.BytesIO(np.asarray(payload).tobytes())) as reopened:
        expected = np.asarray(
            reopened.convert("RGB").resize(INPUT_SIZE, Image.Resampling.LANCZOS),
            dtype=np.uint8,
        )

    prepared = prepare_source_file_rgb(path, cv2_module=cv2)

    assert np.array_equal(prepared.rgb, expected)
    assert prepared.source_extension == ".jpg"
    assert len(prepared.source_sha256) == 64
    assert len(prepared.intermediate_payload_sha256) == 64


def test_path_extraction_records_original_file_contract(tmp_path: Path) -> None:
    cv2 = pytest.importorskip("cv2")
    path = tmp_path / "source.png"
    Image.new("RGB", (19, 11), (20, 40, 60)).save(path)
    loaded, _ = loaded_fake()

    result = extract_learned_formal(
        path,
        loaded,
        policy=SOURCE_REPLICATION_POLICY,
        base_seed=17,
        device="cpu",
        torch_module=FakeTorch(),
        cv2_module=cv2,
    )

    assert result.metadata["feature_version"] == SOURCE_FILE_FEATURE_VERSION
    assert result.metadata["source_input_role"] == "original_reproduction_file"
    assert result.metadata["source_preprocessing_policy"] == (
        "opencv_imread_resize_imwrite_same_extension_then_pillow_rgb"
    )
    assert result.metadata["source_extension"] == ".png"
    assert result.metadata["source_file_sha256"] is not None
    assert result.metadata["intermediate_payload_sha256"] is not None


def test_model_array_is_float32_chw_and_minus_one_to_one() -> None:
    rgb = np.zeros((512, 512, 3), dtype=np.uint8)
    rgb[0, 0] = [0, 127, 255]

    tensor = rgb_to_model_array(rgb)

    assert tensor.shape == (1, 3, 512, 512)
    assert tensor.dtype == np.float32
    assert tensor[0, 0, 0, 0] == -1.0
    assert tensor[0, 1, 0, 0] == pytest.approx(127 / 127.5 - 1.0)
    assert tensor[0, 2, 0, 0] == 1.0
    assert float(tensor.min()) >= -1.0
    assert float(tensor.max()) <= 1.0


def test_scale_and_flatten_is_explicit_float32_c_order() -> None:
    latent = np.arange(np.prod(LATENT_SHAPE), dtype=np.float32).reshape(LATENT_SHAPE)

    vector = scale_and_flatten_latent(latent)

    assert vector.shape == (16384,)
    assert vector.dtype == np.float32
    assert vector[:4] == pytest.approx(np.arange(4) * LATENT_SCALE)
    assert vector[-1] == pytest.approx((16384 - 1) * LATENT_SCALE)


def test_scale_and_flatten_rejects_a_non_sd2_latent_shape() -> None:
    with pytest.raises(LatentContractError, match="latent has shape"):
        scale_and_flatten_latent(np.zeros((4, 32, 32), dtype=np.float32))


def test_content_seed_is_stable_sensitive_and_namespaced() -> None:
    first = np.zeros((512, 512, 3), dtype=np.uint8)
    second = first.copy()
    second[0, 0, 0] = 1

    assert derive_content_seed(first, base_seed=9) == derive_content_seed(first, base_seed=9)
    assert derive_content_seed(first, base_seed=9) != derive_content_seed(second, base_seed=9)
    assert derive_content_seed(first, base_seed=9) != derive_content_seed(first, base_seed=10)
    assert 0 <= derive_content_seed(first) < 2**63


def test_seeded_sampling_is_reproducible_and_policy_is_recorded() -> None:
    loaded, vae = loaded_fake()
    torch = FakeTorch()
    cv2 = FakeCV2()
    image = np.zeros((2, 3, 3), dtype=np.uint8)
    image[0, 0] = [20, 40, 60]

    first = extract_learned_formal(
        image,
        loaded,
        policy=SOURCE_REPLICATION_POLICY,
        base_seed=17,
        device="cpu",
        torch_module=torch,
        cv2_module=cv2,
    )
    second = extract_learned_formal(
        image,
        loaded,
        policy=SOURCE_REPLICATION_POLICY,
        base_seed=17,
        device="cpu",
        torch_module=torch,
        cv2_module=cv2,
    )

    assert np.array_equal(first.vector, second.vector)
    assert first.metadata["seed"] == second.metadata["seed"]
    assert first.metadata["seed_strategy"] == "sha256_of_resized_rgb_plus_base_seed"
    assert first.metadata["feature_version"].endswith("seeded-sample-v1")
    assert first.metadata["representation_role"].startswith("source_replication")
    assert first.metadata["latent_scale"] == LATENT_SCALE
    assert first.metadata["flatten_order"] == "C"
    assert first.metadata["vector_length"] == 16384
    assert first.metadata["artifacts_verified"] is True
    assert first.metadata["source_revision"] == SOURCE_REVISION
    assert first.metadata["source_repository"] == SOURCE_REPOSITORY
    assert first.metadata["model_repository"] == MODEL_REPOSITORY
    assert vae.last_input.shape == (1, 3, 512, 512)
    assert vae.last_input.device == "cpu"
    assert vae.last_input.dtype == "float32"


def test_explicit_seed_changes_sample_but_not_content_identity() -> None:
    loaded, _ = loaded_fake()
    kwargs = {
        "loaded_vae": loaded,
        "policy": SOURCE_REPLICATION_POLICY,
        "device": "cpu",
        "torch_module": FakeTorch(),
        "cv2_module": FakeCV2(),
    }
    image = np.zeros((1, 1, 3), dtype=np.uint8)

    first = extract_learned_formal(image, seed=1, **kwargs)
    second = extract_learned_formal(image, seed=2, **kwargs)

    assert not np.array_equal(first.vector, second.vector)
    assert first.metadata["seed"] == 1
    assert second.metadata["seed"] == 2
    assert first.metadata["seed_strategy"] == "explicit"
    assert first.metadata["seed_basis_sha256"] == second.metadata["seed_basis_sha256"]


def test_auto_mps_keeps_float32_and_uses_cpu_seeded_noise() -> None:
    loaded, vae = loaded_fake()
    torch = FakeTorch(mps_available=True)

    result = extract_learned_formal(
        np.zeros((1, 1, 3), dtype=np.uint8),
        loaded,
        policy=SOURCE_REPLICATION_POLICY,
        seed=123,
        device="auto",
        torch_module=torch,
        cv2_module=FakeCV2(),
    )

    assert result.metadata["device"] == "mps"
    assert result.metadata["dtype"] == "float32"
    assert vae.to_calls[-1] == {"device": "mps"}
    assert vae.last_input.device == "mps"
    assert vae.last_input.dtype == "float32"
    assert torch.randn_devices == ["cpu"]


def test_posterior_mode_is_deterministic_and_labeled_as_deviation() -> None:
    mean = np.arange(16384, dtype=np.float32).reshape((1, *LATENT_SHAPE))
    loaded, _ = loaded_fake(mean=mean, std=np.full_like(mean, 1000.0))
    result = extract_learned_formal(
        np.zeros((1, 1, 3), dtype=np.uint8),
        loaded,
        policy=DETERMINISTIC_BENCHMARK_POLICY,
        device="cpu",
        torch_module=FakeTorch(),
        cv2_module=FakeCV2(),
    )

    assert result.vector[:4] == pytest.approx(np.arange(4) * LATENT_SCALE)
    assert result.metadata["seed"] is None
    assert result.metadata["seed_strategy"] == "not_applicable"
    assert result.metadata["feature_version"].endswith("posterior-mode-v1")
    assert result.metadata["representation_role"].startswith("deterministic_benchmark_deviation")


def test_hash_verification_accepts_exact_bytes_and_rejects_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "weights.bin"
    artifact.write_bytes(b"exact-weights")
    expected = digest(b"exact-weights")

    assert verify_file_sha256(artifact, expected, "weights") == expected
    with pytest.raises(ProvenanceVerificationError, match="SHA-256 mismatch"):
        verify_file_sha256(artifact, "0" * 64, "weights")


def test_pins_require_immutable_revisions_and_hashes() -> None:
    with pytest.raises(ValueError, match="model_revision"):
        LearnedFormalPins(
            model_revision="main",
            config_sha256="0" * 64,
            weights_sha256="1" * 64,
        )
    with pytest.raises(ValueError, match="config_sha256"):
        LearnedFormalPins(
            model_revision="0" * 40,
            config_sha256="not-a-hash",
            weights_sha256="1" * 64,
        )


def test_source_checkout_verifies_remote_and_revision(tmp_path: Path) -> None:
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        if "rev-parse" in command:
            return SimpleNamespace(stdout=SOURCE_REVISION + "\n")
        if "status" in command:
            return SimpleNamespace(stdout="")
        return SimpleNamespace(stdout=SOURCE_REPOSITORY + ".git\n")

    repository, revision = verify_source_checkout(tmp_path, runner=runner)

    assert repository.endswith(".git")
    assert revision == SOURCE_REVISION
    assert len(calls) == 3
    assert all(call[1]["check"] is True for call in calls)


def test_source_checkout_rejects_modified_tracked_files(tmp_path: Path) -> None:
    def runner(command, **_kwargs):
        if "rev-parse" in command:
            return SimpleNamespace(stdout=SOURCE_REVISION + "\n")
        if "status" in command:
            return SimpleNamespace(stdout=" M 001_Scripts/make_a-vector.py\n")
        return SimpleNamespace(stdout=SOURCE_REPOSITORY + ".git\n")

    with pytest.raises(ProvenanceVerificationError, match="modified tracked files"):
        verify_source_checkout(tmp_path, runner=runner)


def test_pinned_artifact_bundle_records_verified_files(tmp_path: Path) -> None:
    config = tmp_path / "config.json"
    weights = tmp_path / "weights.safetensors"
    config.write_bytes(b"config")
    weights.write_bytes(b"weights")

    verification = verify_pinned_artifacts(pins(), config, weights)

    assert verification.source_checkout_verified is False
    assert verification.metadata()["artifacts_verified"] is True
    assert verification.metadata()["config_sha256"] == digest(b"config")
    assert verification.metadata()["weights_sha256"] == digest(b"weights")


def test_loader_is_local_only_and_lazy(tmp_path: Path) -> None:
    vae_dir = tmp_path / "vae"
    vae_dir.mkdir()
    (vae_dir / "config.json").write_bytes(b"config")
    (vae_dir / "diffusion_pytorch_model.safetensors").write_bytes(b"weights")
    fake_vae = FakeVAE(FakePosterior(np.zeros((1, *LATENT_SHAPE)), np.ones((1, *LATENT_SHAPE))))
    calls = []

    class AutoencoderKL:
        @classmethod
        def from_pretrained(cls, path, **kwargs):
            calls.append((path, kwargs))
            return fake_vae

    loaded = load_pinned_sd2_vae(
        tmp_path,
        pins(),
        torch_module=FakeTorch(),
        diffusers_module=SimpleNamespace(AutoencoderKL=AutoencoderKL),
    )

    assert loaded.vae is fake_vae
    assert calls == [
        (
            str(tmp_path),
            {
                "subfolder": "vae",
                "local_files_only": True,
                "torch_dtype": "float32",
                "use_safetensors": True,
            },
        )
    ]
    assert fake_vae.to_calls[0] == {"device": "cpu"}


def test_optional_dependency_error_is_actionable(monkeypatch) -> None:
    def missing(name):
        raise ImportError(name)

    monkeypatch.setattr("latent_art_bench.features.learned_formal.importlib.import_module", missing)
    with pytest.raises(OptionalDependencyError, match="isolated learned-formal environment"):
        _optional_module("torch", "test inference")
