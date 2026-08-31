from pathlib import Path

import pytest
from pydantic import ValidationError

from latent_art_bench.config import load_config


def test_pilot_identity_hashes_are_frozen(pilot_config) -> None:
    identities = pilot_config.measurement_identities()
    assert identities["chromatic"] == (
        "lee2018-deltae76-seamlessness-v1",
        "512397aad7c001c09ae404ad886bf136a63186cd343134e14fbd40fcbc13c577",
    )
    assert identities["learned_formal"] == (
        "kim2026-sd20-a-vector-source-v1",
        "259e7817a5493e2aac25ad660584853b27d159573cc8c694676406246ceb3187",
    )


def test_pilot_config_cannot_enable_upsampling(pilot_config) -> None:
    data = pilot_config.preprocessing.model_dump(mode="json")
    data["no_upsampling"] = False
    with pytest.raises(ValidationError):
        type(pilot_config.preprocessing).model_validate(data)


def test_pilot_1_pins_only_the_two_requested_image_models() -> None:
    config = load_config(Path("configs/pilot_1/pilot.yaml"))

    assert config.generation.models == ["gpt-image-1", "gpt-image-2"]
    assert config.generation.require_loopback is True
    assert config.measurements.learned_formal.enabled is True
    assert config.measurements.learned_formal.model_weights_sha256 == (
        "a1d993488569e928462932c8c38a0760b874d166399b14414135bd9c42df5815"
    )
    assert config.preprocessing.max_long_side == 500
