"""Compact-input replay checks; no network, images or retained-archive reads."""

import copy
import importlib.util
import math
from collections import Counter
from pathlib import Path
from statistics import mean, variance

import pytest
from scipy.stats import t

REPOSITORY = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("paper_palette_replay", REPOSITORY /
                                            "paper/replay_palette.py")
replay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(replay)


@pytest.fixture
def inputs():
    return replay.load_inputs()


def copy_compact_inputs(destination):
    for relative in replay.INPUTS:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPOSITORY / relative).read_bytes())


def test_primary_replays_with_only_three_compact_files_and_no_archive(tmp_path):
    copy_compact_inputs(tmp_path)
    result = replay.replay(tmp_path)
    assert [row["estimate"] for row in result["primary"]] == pytest.approx(
        [-0.28436771515521886, -0.01772092687727252], abs=1e-15)
    assert result["primary_covariance"][0][1] == pytest.approx(0.011200734497355182)
    assert len(list(tmp_path.rglob("*.*"))) == 3


def test_ordered_blocks_recover_fixed_scene_variances_and_intervals(inputs):
    result = replay.analyze_inputs(*inputs)
    blocks = result["blocks"]
    assert [b["block_order"] for b in blocks] == list(range(1, 25))
    assert [b["first_sequence"] for b in blocks] == list(range(0, 192, 8))
    assert Counter(b["template_id"] for b in blocks) == dict.fromkeys(replay.SCENES, 4)
    assert (blocks[0]["template_id"], blocks[0]["repetition"]) == ("built_houses", 1)
    assert (blocks[-1]["template_id"], blocks[-1]["repetition"]) == ("built_village", 1)
    assert blocks[0]["monet_interaction"] == pytest.approx(-0.660091708, abs=1e-9)
    assert blocks[-1]["cezanne_interaction"] == pytest.approx(0.223031972, abs=1e-9)
    # An independent scalar-statistics calculation checks the frozen vector API's
    # fixed-scene variance and Welch intervals, rather than using its helpers.
    for painter, primary in zip(("monet", "cezanne"), result["primary"]):
        scenes = [[b[painter + "_interaction"] for b in blocks if b["template_id"] == scene]
                  for scene in sorted(replay.SCENES)]
        pieces = [variance(values) / 144 for values in scenes]
        estimate = mean(mean(values) for values in scenes)
        se = math.sqrt(sum(pieces))
        df = sum(pieces)**2 / sum(piece**2 / 3 for piece in pieces)
        critical = t.ppf(0.9875, df)
        assert primary["estimate"] == pytest.approx(estimate, abs=1e-14)
        assert primary["standard_error"] == pytest.approx(se, abs=1e-14)
        assert primary["welch_df"] == pytest.approx(df, abs=1e-12)
        assert primary["family_interval"] == pytest.approx(
            [estimate - critical * se, estimate + critical * se], abs=1e-14)


@pytest.mark.parametrize("relative", list(replay.INPUTS))
def test_changed_compact_bytes_fail_before_analysis(tmp_path, relative):
    copy_compact_inputs(tmp_path)
    target = tmp_path / relative
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ValueError, match="compact input changed"):
        replay.replay(tmp_path)


@pytest.mark.parametrize("damage, message", [
    ("duplicate", "duplicate"), ("missing", "missing"),
    ("nan", "finite"), ("inf", "finite"), ("unmeasured", "measured"),
    ("treatment", "identity mismatch"), ("unknown", "unknown"),
])
def test_invalid_chroma_cannot_silently_change_the_analyzed_grid(inputs, damage, message):
    schedule, chroma, primary = copy.deepcopy(inputs)
    if damage == "duplicate":
        chroma.append(chroma[0].copy())
    elif damage == "missing":
        chroma.pop()
    elif damage in ("nan", "inf"):
        chroma[0]["value"] = damage
    elif damage == "unmeasured":
        chroma[0]["status"] = "failed"
    elif damage == "treatment":
        chroma[0]["arm"] = "monet"
    else:
        chroma[0]["request_id"] = "unknown"
    with pytest.raises(ValueError, match=message):
        replay.analyze_inputs(schedule, chroma, primary)


def test_reordered_schedule_cannot_relabel_collection_order(inputs):
    schedule, chroma, primary = copy.deepcopy(inputs)
    schedule[0], schedule[1] = schedule[1], schedule[0]
    with pytest.raises(ValueError, match="dispatch sequence"):
        replay.analyze_inputs(schedule, chroma, primary)


def test_primary_parity_failure_is_not_replaced_by_new_results(inputs):
    schedule, chroma, primary = copy.deepcopy(inputs)
    primary[0]["estimate"] += 0.01
    with pytest.raises(ValueError, match="primary inference differs"):
        replay.analyze_inputs(schedule, chroma, primary)
