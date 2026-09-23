"""Constructed unit embeddings exercise selection and fail-closed provenance."""

import copy
import json

import numpy as np
import pytest

from latent_art_bench.painter_family_controls_v1 import reference_panels as adapter
from latent_art_bench.painter_family_controls_v1.protocol import ARTISTS
from latent_art_bench.painter_family_controls_v1.transport_artifact import file_sha


def fixture():
    rows, values = [], []
    for role, counts in adapter.REFERENCE_COUNTS.items():
        for painter_index, count in enumerate(counts):
            for index in range(count):
                row = dict(
                    id=f"{role}-{painter_index}-{index}",
                    role=role,
                    painter=ARTISTS[painter_index],
                    view="original",
                    box=[0, 0, 1, 1],
                    path=f"retained/{role}-{painter_index}-{index}",
                    sha256="1" * 64,
                )
                rows.append(row)
                values.append(np.eye(4)[painter_index])
                if index < adapter.AUDITED_COUNTS[role][painter_index]:
                    rows.append(dict(row, view="audited_region", box=[0.1, 0.2, 0.9, 0.8]))
                    values.append(np.eye(4)[(painter_index + 1) % 4])
    return rows, np.asarray(values)


def test_fixed_original_and_audited_selection_raw_means_and_memberships():
    rows, values = fixture()
    panels = adapter.reference_panels(rows, values)
    assert tuple(panels) == adapter.PANEL_IDS
    for role, panel in (("reference", "primary"), ("development", "development")):
        original = panels[f"{panel}_original"]
        audited = panels[f"{panel}_audited_region"]
        np.testing.assert_array_equal(original["reference_means"], np.eye(4))
        assert original["counts"] == audited["counts"] == list(adapter.REFERENCE_COUNTS[role])
        assert original["audited_replacements_by_painter"] == [0] * 4
        assert audited["audited_replacements_by_painter"] == list(adapter.AUDITED_COUNTS[role])
        for painter in range(4):
            fraction = (
                adapter.AUDITED_COUNTS[role][painter] / adapter.REFERENCE_COUNTS[role][painter]
            )
            expected = (1 - fraction) * np.eye(4)[painter] + fraction * np.eye(4)[(painter + 1) % 4]
            np.testing.assert_allclose(audited["reference_means"][painter], expected)
            assert np.linalg.norm(audited["reference_means"][painter]) < 1
            members = audited["memberships"][painter]
            assert len(members) == adapter.REFERENCE_COUNTS[role][painter]
            for member in members:
                selected = rows[member["selected_row_index"]]
                assert selected["id"] == member["id"]
                assert selected["view"] == member["selected_view"]
                assert member["source_sha256"] == selected["sha256"]
                assert rows[member["original_row_index"]]["view"] == "original"
    # Permuting rows preserves the target; row indices still follow the actual manifest.
    permuted = adapter.reference_panels(rows[::-1], values[::-1])
    for key in panels:
        np.testing.assert_array_equal(
            permuted[key]["reference_means"], panels[key]["reference_means"]
        )


@pytest.mark.parametrize(
    "corruption",
    [
        "missing_original",
        "missing_crop",
        "duplicate",
        "painter",
        "role",
        "view",
        "crop_identity",
        "box",
        "nonunit",
        "nonfinite",
        "row_count",
        "source_hash",
    ],
)
def test_changed_membership_or_embeddings_are_rejected(corruption):
    rows, values = fixture()
    if corruption == "missing_original":
        rows, values = rows[1:], values[1:]
    elif corruption == "missing_crop":
        del rows[1]
        values = np.delete(values, 1, axis=0)
    elif corruption == "duplicate":
        rows[1] = copy.deepcopy(rows[0])
    elif corruption == "painter":
        rows[0]["painter"] = "other"
    elif corruption == "role":
        rows[0]["role"] = "other"
    elif corruption == "view":
        rows[0]["view"] = "other"
    elif corruption == "crop_identity":
        rows[1]["sha256"] = "2" * 64
    elif corruption == "box":
        rows[1]["box"] = [0, 0, float("nan"), 1]
    elif corruption == "nonunit":
        values[0] *= 0.5
    elif corruption == "nonfinite":
        values[0, 0] = np.nan
    elif corruption == "row_count":
        values = values[:-1]
    else:
        rows[0]["sha256"] = "missing"
    with pytest.raises(ValueError):
        adapter.reference_panels(rows, values)


def test_external_hash_and_historical_anchor_are_required_before_npz(tmp_path, monkeypatch):
    path = tmp_path / "candidate.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="externally bound"):
        adapter.load_prepared(path, expected_sha256="0" * 64, root=tmp_path)
    with pytest.raises(ValueError, match="schema, anchor or axes"):
        adapter.load_prepared(path, expected_sha256=file_sha(path), root=tmp_path)
    anchor = tmp_path / adapter.ANCHOR
    anchor.parent.mkdir(parents=True)
    anchor.write_text('{"bindings": {}}')
    monkeypatch.setattr(
        np, "load", lambda *args, **kwargs: pytest.fail("NPZ read before anchoring")
    )
    with pytest.raises(ValueError, match="bound file changed"):
        adapter.prepare(tmp_path / "new.json", root=tmp_path)


def test_constructed_candidate_relocation_source_edits_and_mean_tamper(tmp_path, monkeypatch):
    rows, values = fixture()
    panels = {encoder: adapter.reference_panels(rows, values) for encoder in adapter.ENCODERS}
    contracts = {encoder: {"constructed": True} for encoder in adapter.ENCODERS}
    source = tmp_path / "source.txt"
    source.write_text("constructed retained source")
    source_sha = file_sha(source)
    monkeypatch.setattr(adapter, "IMPLEMENTATION_FILES", ("source.txt",))
    # Isolate candidate mechanics from actual historical data and its immutable anchor.
    monkeypatch.setattr(
        adapter,
        "_retained",
        lambda root: (
            {adapter.ANCHOR: adapter.ANCHOR_SHA},
            panels,
            contracts,
        ),
    )
    original_verify = adapter.verify_bindings

    def verify(bindings, *, root):
        assert bindings[adapter.ANCHOR] == adapter.ANCHOR_SHA
        original_verify({k: v for k, v in bindings.items() if k != adapter.ANCHOR}, root=root)

    monkeypatch.setattr(adapter, "verify_bindings", verify)
    path = tmp_path / "candidate.json"
    digest = adapter.prepare(path, root=tmp_path)
    assert (
        adapter.load_prepared(path, expected_sha256=digest, root=tmp_path)["new_observations"] == 0
    )
    with pytest.raises(FileExistsError):
        adapter.prepare(path, root=tmp_path)
    source.write_text("edited source")
    with pytest.raises(ValueError, match="bound file changed"):
        adapter.load_prepared(path, expected_sha256=digest, root=tmp_path)
    source.write_text("constructed retained source")
    assert file_sha(source) == source_sha
    record = json.loads(path.read_text())
    record["panels"]["clip"]["primary_original"]["reference_means"][0][0] = 0.25
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="retained means"):
        adapter.load_prepared(path, expected_sha256=file_sha(path), root=tmp_path)
    del record["bindings"]["source.txt"]
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="source bindings"):
        adapter.load_prepared(path, expected_sha256=file_sha(path), root=tmp_path)
