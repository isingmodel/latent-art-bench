import pytest
from pydantic import ValidationError


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
