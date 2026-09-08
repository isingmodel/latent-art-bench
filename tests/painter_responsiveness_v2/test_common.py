"""The prospective inventory and live CLI boundary use synthetic/offline inputs."""

import copy
from pathlib import Path

import pytest

from latent_art_bench.painter_responsiveness_v2 import common

ROOT = Path(__file__).resolve().parents[2]


def test_exact_inventory_is_reproducible_and_shared():
    config = common.configuration(ROOT)
    planned = common.requests(config)
    assert planned == common.requests(config)
    assert len(planned) == 192
    assert len({r["request_id"] for r in planned}) == 192
    assert len({r["block_id"] for r in planned}) == 24
    assert {r["route"] for r in planned} == {"oauth_gpt_image_2"}
    for request in planned:
        assert request["request_id"].startswith("prv2:")
        assert request["payload"]["model"] == "gpt-image-2"
        assert request["payload"]["n"] == 1
        assert config["polarity_clauses"][request["polarity"]] in request["payload"]["prompt"]
    for block in {r["block_id"] for r in planned}:
        members = [r for r in planned if r["block_id"] == block]
        assert {(r["arm"], r["polarity"]) for r in members} == {
            (a, p) for a in ("free", "generic", "monet", "cezanne") for p in ("muted", "vivid")}


def test_configuration_rejects_paid_route_or_rescaling(monkeypatch):
    original = common.read_json
    for key, value in (("route", "flux_2_max"), ("maximum_new_openrouter_spend_usd", 1),
                       ("primary_chroma_scale", 99), ("maximum_images", 200)):
        changed = copy.deepcopy(original(ROOT / common.CONFIG))
        changed[key] = value
        monkeypatch.setattr(common, "read_json", lambda p, c=changed:
                            c if p == ROOT / common.CONFIG else original(p))
        with pytest.raises(ValueError, match="fixed computational"):
            common.configuration(ROOT)


def test_cli_requires_explicit_live(monkeypatch):
    from latent_art_bench.painter_responsiveness_v2 import __main__ as cli

    monkeypatch.setattr("sys.argv", ["study", "collect", "--proxy-root", "does-not-exist"])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
