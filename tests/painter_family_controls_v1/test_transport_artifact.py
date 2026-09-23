"""Constructed provenance/axis tests; no historical feature arrays are read."""

import copy

import numpy as np
import pytest

from latent_art_bench.painter_family_controls_v1.protocol import ARTISTS, MODELS
from latent_art_bench.painter_family_controls_v1.transport_artifact import (
    REFERENCE_COUNTS,
    file_sha,
    load_prepared,
    old_arrays,
    verify_bindings,
)


def fixture():
    rows, values = [], []
    for model in MODELS:
        for scene in range(14):
            for repeat in range(2):
                for painter, arm in enumerate(ARTISTS):
                    rows.append(dict(id=f"{model}-{scene}-{repeat}-{arm}", view="original",
                                     role="generated", model=model, scene=scene,
                                     repeat=repeat, arm=arm))
                    values.append(np.eye(4)[painter])
    for painter, count in enumerate(REFERENCE_COUNTS):
        for index in range(count):
            rows.append(dict(id=f"reference-{painter}-{index}", view="original",
                             role="reference", painter=ARTISTS[painter]))
            values.append(np.eye(4)[painter])
    return rows, np.array(values)


def test_explicit_membership_reorders_old_rows_and_averages_raw_references():
    rows, values = fixture()
    original = old_arrays(rows, values)
    reordered = old_arrays(rows[::-1], values[::-1])
    np.testing.assert_array_equal(original[0], reordered[0])
    np.testing.assert_array_equal(original[1], reordered[1])
    assert original[0].shape == (6, 14, 2, 4, 4)
    np.testing.assert_array_equal(original[1], np.eye(4))


@pytest.mark.parametrize("corruption", ["missing", "duplicate", "bool", "reference", "nonunit"])
def test_corrupt_old_census_is_never_silently_reweighted(corruption):
    rows, values = fixture()
    if corruption == "missing":
        rows, values = rows[1:], values[1:]
    elif corruption == "duplicate":
        rows[1] = copy.deepcopy(rows[0])
    elif corruption == "bool":
        rows[0]["scene"] = False
    elif corruption == "reference":
        rows[-1] = copy.deepcopy(rows[-2])
    else:
        values[0] *= 0.5
    with pytest.raises(ValueError):
        old_arrays(rows, values)


def test_hash_binding_detects_changes_and_path_escape(tmp_path):
    path = tmp_path / "bound.txt"
    path.write_text("constructed input")
    bindings = {"bound.txt": file_sha(path)}
    verify_bindings(bindings, root=tmp_path)
    path.write_text("modified")
    with pytest.raises(ValueError, match="bound file changed"):
        verify_bindings(bindings, root=tmp_path)
    with pytest.raises(ValueError, match="invalid artifact binding"):
        verify_bindings({"../outside": "0" * 64}, root=tmp_path)


def test_external_parameter_digest_is_mandatory_before_parsing(tmp_path):
    path = tmp_path / "parameters.json"
    path.write_text('{"translation": "constructed tamper"}')
    with pytest.raises(ValueError, match="externally bound identity"):
        load_prepared(path, expected_sha256="0" * 64)
    with pytest.raises(ValueError, match="schema, anchor or axes"):
        load_prepared(path, expected_sha256=file_sha(path))
