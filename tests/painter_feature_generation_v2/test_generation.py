from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from latent_art_bench.io import read_json
from latent_art_bench.painter_feature_generation_v2.generate import CONFIG, PROMPTS, request_grid

ROOT = Path(__file__).resolve().parents[2]


def test_real_prompt_library_produces_exact_balanced_paired_grid():
    config, library = read_json(ROOT / CONFIG), read_json(ROOT / PROMPTS)
    requests = request_grid(config, library)
    assert len(requests) == len({r["request_id"] for r in requests}) == 2000
    assert set(Counter(r["block"] for r in requests).values()) == {80}
    assert set(Counter(r["condition"] for r in requests).values()) == {400}
    grouped = defaultdict(list)
    for request in requests:
        grouped[request["block"], request["template_id"]].append(request)
        assert isinstance(request["prompt"], str)
        assert "An oil painting on canvas" in request["prompt"]
    assert all(len({r["seed"] for r in cell}) == 1 for cell in grouped.values())
    assert requests == request_grid(config, library)
    assert [r["block"] for r in requests] == sorted(r["block"] for r in requests)
