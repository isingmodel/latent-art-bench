"""Offline checks for the v3 allocation and collector (no paid request is made)."""

from __future__ import annotations

import json
from collections import Counter

import pytest

from latent_art_bench.painter_specificity_v2 import study as september
from latent_art_bench.painter_specificity_v3 import collect as c
from latent_art_bench.painter_specificity_v3 import study as s


def test_allocation_is_complete_and_balanced():
    items = s.assignments()
    assert len(items) == 6 * 14 * 10 * 2 == 1680
    assert len({r["id"] for r in items}) == 1680
    assert len({(r["model"], r["scene"], r["arm"], r["repeat"]) for r in items}) == 1680
    assert Counter(r["arm"] for r in items) == {arm: 168 for arm in s.ARMS}
    # Scenes are sequential blocks of 120 requests, as September's were blocks of 72.
    scenes = [r["scene"] for r in items]
    assert all(len(set(scenes[i: i + 120])) == 1 for i in range(0, 1680, 120))
    assert s.assignments() == items


def test_free_and_generic_payloads_match_september_exactly():
    old = {(r["model"], r["scene"], r["arm"]): r["payload"] for r in september.assignments()}
    for r in s.assignments():
        if r["arm"] in ("free", "generic"):
            assert r["payload"] == old[r["model"], r["scene"], r["arm"]]
        else:
            name = s.NAMES[s.ARTISTS.index(r["arm"])]
            assert r["payload"]["prompt"].startswith(
                f"Render as an oil painting in the style of {name}. ")
            template = old[r["model"], r["scene"], "generic"]
            assert {k: v for k, v in r["payload"].items() if k != "prompt"} == {
                k: v for k, v in template.items() if k != "prompt"}


def test_group_slices_are_six_arm_four_painter_views():
    assert s.GROUP_ARMS == {"century": (0, 1, 2, 3, 4, 5), "hudson": (0, 1, 6, 7, 8, 9)}


def test_accounting_reserves_until_charged():
    start = dict(kind="start", id="x", attempt=1)
    assert s.accounted([start], 100.0) == pytest.approx(105.0)
    end = dict(kind="end", id="x", attempt=1, cost_usd=0.05)
    assert s.accounted([start, end], 100.0) == pytest.approx(100.05)
    with pytest.raises(ValueError):
        s.accounted([start, end, end], 100.0)


def test_forecast_uses_september_costs():
    forecast = s.forecast()
    assert forecast["images"] == 1680
    assert 60 < forecast["expected_usd"] < 90


def test_collect_loop_offline_completes_and_respects_ceiling(tmp_path, monkeypatch):
    monkeypatch.setattr(s, "DATA", tmp_path / "data")
    monkeypatch.setattr(s, "WORK", tmp_path / "work")
    monkeypatch.setattr(c, "key_from_env", lambda root: "test-key")
    monkeypatch.setattr(c.time, "sleep", lambda _: None)
    clock = iter(range(0, 10**9, 10))
    monkeypatch.setattr(c.time, "monotonic", lambda: next(clock))
    (tmp_path / "data").mkdir()
    (tmp_path / "work").mkdir()
    items = s.assignments()[:12]
    with (s.DATA / "requests.jsonl").open("w") as stream:
        for r in items:
            stream.write(json.dumps(r) + "\n")
    (s.DATA / "freeze.json").write_text("{}")

    def fake_post(r, attempt, key):
        return dict(kind="end", id=r["id"], attempt=attempt, status=200, success=True,
                    retryable=False, cost_usd=0.05)

    c.collect_loop([], 100.0, 1000.0, post=fake_post)
    receipt = json.loads((s.DATA / "collection.json").read_text())
    assert receipt["successful"] == 12 and receipt["accounted_usd"] == pytest.approx(100.6)

    # A ceiling that admits nothing stops before the first start.
    monkeypatch.setattr(s, "DATA", tmp_path / "data2")
    (tmp_path / "data2").mkdir()
    (s.DATA / "requests.jsonl").write_text(json.dumps(items[0]) + "\n")
    c.collect_loop([], 100.0, 104.0, post=fake_post)
    assert not (s.DATA / "attempts.jsonl").exists()
    assert "budget admission limit" in (s.DATA / "operator_events.jsonl").read_text()
