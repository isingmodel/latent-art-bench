import json

import numpy as np
import pytest

from latent_art_bench.painter_distribution_study_v1 import analysis as a
from latent_art_bench.painter_distribution_study_v1 import analysis_publication as r
from latent_art_bench.painter_distribution_study_v1 import study as s
from latent_art_bench.painter_feature_generation_v2.artifacts import publish


def test_real_endpoint_code_reproduces_boolean_failure_without_changing_values():
    config = dict(briefs=[dict(brief_id=f"b{i}") for i in range(24)])
    targets = {p: dict(water=1) for p in s.PAINTERS}
    endpoints, sensitivities = a.prompt_endpoints([], [], targets, config)
    original = dict(endpoints=endpoints, sensitivities=sensitivities, estimate=1.2345678901234567)
    with pytest.raises(TypeError, match="JSON serializable"):
        json.dumps(original)
    converted = r.native_payload(original)
    assert converted == original
    assert all(type(row["reject_at_05"]) is bool for row in converted["endpoints"])
    assert all(isinstance(row["reject_at_05"], np.bool_) for row in original["endpoints"])
    assert all(row["raw_p"] == row["holm_p"] == 1 for row in converted["endpoints"])
    assert len(converted["endpoints"]) == 8 and len(converted["sensitivities"]) == 256


def test_converter_does_not_silently_coerce_other_types_or_nonfinite_values():
    with pytest.raises(TypeError, match="must be a Boolean"):
        r.native_payload(dict(endpoints=[dict(reject_at_05=1)]))
    with pytest.raises(TypeError):
        r.native_payload(dict(endpoints=[], unexpected=np.int64(4)))
    with pytest.raises(ValueError):
        r.native_payload(dict(endpoints=[], estimate=float("nan")))


def test_publication_replays_and_never_replaces_terminal_results(tmp_path, monkeypatch):
    freeze = dict(recorded_git_commit="test", correction="Boolean conversion")
    monkeypatch.setattr(r, "verify", lambda root: freeze)
    publish(tmp_path / r.DIRECTORY / "publication_freeze.json", freeze)
    publish(tmp_path / r.p.DIRECTORY / "execution_freeze.json", {})
    value = dict(cells=[], endpoints=[dict(reject_at_05=np.bool_(False), holm_p=0.6)])
    monkeypatch.setattr(r.results, "analyze", lambda root: value)
    assert r.analysis(tmp_path)["status"] == "published"
    assert r.analysis(tmp_path, check=True)["numeric_replay"]
    with pytest.raises(ValueError, match="terminal"):
        r.analysis(tmp_path)
    output = tmp_path / r.DIRECTORY / "analysis.json"
    output.write_text(output.read_text().replace("0.6", "0.7"))
    with pytest.raises(ValueError, match="changed"):
        r.analysis(tmp_path, check=True)
