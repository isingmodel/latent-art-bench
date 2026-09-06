import pytest

from latent_art_bench.painter_distribution_study_v1 import pilot
from latent_art_bench.painter_distribution_study_v1 import pilot_summary as s


def test_pilot_qualification_uses_all_dispositions_and_cost_headroom():
    requests = pilot.request_grid({"scenes": ["River.", "Village.", "Field."]})
    rows = []
    for request in requests:
        identity = dict(request_id=request["request_id"], route=request["route"])
        rows.append(dict(identity, kind="attempt", request_sha256=s.digest(request)))
        rows.append(
            dict(
                identity,
                kind="terminal",
                status="image_returned",
                cost_usd=0 if request["route"] == "oauth_gpt_image_2" else 0.07,
                latency_seconds=10,
                observed=dict(width=1024, height=1024, format="PNG"),
            )
        )
    result = s.summarize(requests, rows)
    assert result["technical_qualification"]
    for index in (1, 7):
        rows[index].update(status="http_error", observed=None, cost_usd=0)
    assert not s.summarize(requests, rows)["technical_qualification"]
    with pytest.raises(ValueError, match="incomplete"):
        s.summarize(requests, rows[:-2])
    rows[1]["cost_usd"] = None
    result = s.summarize(requests, rows)
    assert not result["technical_qualification"] and result["research_projection_usd"] is None
