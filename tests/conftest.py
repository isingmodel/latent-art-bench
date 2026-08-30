from pathlib import Path

import pytest

from latent_art_bench.config import PilotConfig, load_config

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def pilot_config(monkeypatch: pytest.MonkeyPatch) -> PilotConfig:
    monkeypatch.delenv("LATENT_ART_IMAGE_BASE_URL", raising=False)
    return load_config(REPOSITORY_ROOT / "configs/pilot_0/pilot.yaml")
