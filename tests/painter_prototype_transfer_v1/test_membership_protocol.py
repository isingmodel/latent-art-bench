"""Synthetic row membership and local create-once protocol; no real artifacts read."""

import json
import sys

import numpy as np
import pytest

from latent_art_bench import painter_prototype_transfer_v1 as transfer


def fixture_rows():
    rows, vectors = [], []
    unit = np.eye(4)
    for scene in range(2):
        for repeat in range(2):
            for a, arm in enumerate(("free", "generic", *transfer.ARTISTS)):
                rows.append(
                    dict(
                        id=f"g-{scene}-{repeat}-{arm}",
                        view="original",
                        role="generated",
                        model="synthetic",
                        scene=scene,
                        repeat=repeat,
                        arm=arm,
                    )
                )
                vectors.append(unit[a % 4])
    for role, count in (("reference", 2), ("development", 1)):
        for a, painter in enumerate(transfer.ARTISTS):
            for i in range(count):
                image_id = f"{role}-{a}-{i}"
                rows.append(
                    dict(
                        id=image_id,
                        view="original",
                        role=role,
                        painter=painter,
                        path=f"pixels/{image_id}",
                        sha256=f"synthetic-{image_id}",
                    )
                )
                vectors.append(unit[a])
    for role, painter in (("reference", 0), ("development", 1)):
        original = next(r for r in rows if r["id"] == f"{role}-{painter}-0")
        rows.append(dict(original, view="audited_region"))
        vectors.append(unit[(painter + 1) % 4])
    return rows, np.array(vectors)


def assemble(rows, embeddings, use_regions=False):
    return transfer.assemble_rows(
        rows,
        embeddings,
        use_regions=use_regions,
        model_names=("synthetic",),
        scenes=2,
        reference_counts=(2, 2, 2, 2),
        development_counts=(1, 1, 1, 1),
    )


def test_original_and_region_views_preserve_two_finite_targets_and_generated_membership():
    rows, vectors = fixture_rows()
    original, regions = assemble(rows, vectors), assemble(rows, vectors, True)
    assert original["named"].shape == (1, 2, 2, 4, 4)
    np.testing.assert_array_equal(original["named"], regions["named"])
    assert original["generated_image_ids"] == regions["generated_image_ids"]
    assert [len(group) for group in regions["reference"]] == [2] * 4
    assert [len(group) for group in regions["development"]] == [1] * 4
    np.testing.assert_array_equal(regions["reference"][0][0], np.eye(4)[1])
    np.testing.assert_array_equal(regions["development"][1][0], np.eye(4)[2])
    np.testing.assert_array_equal(original["reference"][0][0], np.eye(4)[0])
    assert regions["source_selections"]["reference"][0] == [
        dict(id="reference-0-0", view="audited_region"),
        dict(id="reference-0-1", view="original"),
    ]
    assert all(
        "-free" not in image_id and "-generic" not in image_id
        for image_id in np.array(regions["generated_image_ids"]).flat
    )


def test_archive_row_count_duplicates_and_missing_cells_fail_closed():
    rows, vectors = fixture_rows()
    with pytest.raises(ValueError, match="match manifest"):
        assemble(rows, vectors[:-1])
    with pytest.raises(ValueError, match="duplicate"):
        assemble(rows + [rows[0]], np.vstack([vectors, vectors[0]]))
    with pytest.raises(ValueError, match="incomplete generated"):
        assemble(rows[1:], vectors[1:])
    duplicated_cell = dict(rows[0], id="different-image-same-cell")
    with pytest.raises(ValueError, match="duplicate generated"):
        assemble(rows + [duplicated_cell], np.vstack([vectors, vectors[0]]))


@pytest.mark.parametrize(
    "field,new",
    [("role", "development"), ("painter", "wrong"), ("path", "wrong"), ("sha256", "wrong")],
)
def test_region_must_match_its_original_identity(field, new):
    rows, vectors = fixture_rows()
    rows[-2] = dict(rows[-2], **{field: new})
    with pytest.raises(ValueError, match="identity differs"):
        assemble(rows, vectors, True)


def test_regions_cannot_be_added_as_works_or_substituted_for_generated_images():
    rows, vectors = fixture_rows()
    rows[-1] = dict(rows[0], view="audited_region")
    with pytest.raises(ValueError, match="historical original"):
        assemble(rows, vectors, True)
    rows, vectors = fixture_rows()
    index = next(i for i, row in enumerate(rows) if row["id"] == "reference-0-0")
    with pytest.raises(ValueError, match="historical original"):
        assemble(rows[:index] + rows[index + 1 :], np.delete(vectors, index, axis=0), True)


def test_wrong_target_count_and_invalid_embeddings_fail_closed():
    rows, vectors = fixture_rows()
    with pytest.raises(ValueError, match="reference painter membership"):
        transfer.assemble_rows(
            rows,
            vectors,
            use_regions=False,
            model_names=("synthetic",),
            scenes=2,
            reference_counts=(1, 2, 2, 2),
            development_counts=(1, 1, 1, 1),
        )
    vectors[0] = 0
    with pytest.raises(ValueError, match="nonunit"):
        assemble(rows, vectors)


def test_baseline_agreement_check_uses_every_confusion_cell_and_painter():
    named = np.broadcast_to(np.eye(4), (3, 2, 4, 4))
    result = transfer.evaluate_model(named, np.eye(4))
    base = result["rules"]["reference_baseline"]
    retained = {
        k: base[k] for k in ("counts", "confusion_counts", "macro_accuracy", "micro_accuracy")
    }
    retained["per_painter_accuracy"] = base["per_painter_recall"]
    transfer.assert_baseline_matches(result, retained)
    retained["confusion_counts"] = [[0] * 4 for _ in range(4)]
    with pytest.raises(ValueError, match="confusion_counts"):
        transfer.assert_baseline_matches(result, retained)


def test_nonunit_reference_means_match_training_mean_without_normalizing_either_mean():
    prototypes = np.zeros((4, 5))
    prototypes[:, :4] = 0.6 * np.eye(4)
    repeats = np.tile(prototypes, (2, 1, 1))
    repeats[0, :, 4] = 0.8
    repeats[1, :, 4] = -0.8
    named = np.tile(repeats, (3, 1, 1, 1))
    assert np.all(np.linalg.norm(prototypes, axis=1) < 1)
    np.testing.assert_allclose(np.linalg.norm(named, axis=-1), 1)
    wrong_normalized_target = (prototypes / np.linalg.norm(prototypes, axis=1)[:, None]).mean(
        axis=0
    )
    assert np.linalg.norm(wrong_normalized_target - prototypes.mean(axis=0)) > 0.1
    result = transfer.evaluate_model(named, prototypes)
    for fold in result["folds"]:
        np.testing.assert_allclose(fold["training_mean"], prototypes.mean(axis=0), atol=1e-14)
        np.testing.assert_allclose(fold["reference_mean"], prototypes.mean(axis=0), atol=1e-14)
        np.testing.assert_allclose(fold["translation"], 0, atol=1e-14)
    for key in ("predictions", "margins", "query_norms"):
        np.testing.assert_allclose(
            result["rules"]["reference_baseline"][key],
            result["rules"]["common_translation"][key],
            atol=1e-14,
        )


def test_freeze_is_hash_only_create_once_and_detects_changed_input(tmp_path, monkeypatch):
    source = tmp_path / "synthetic-source.txt"
    source.write_text("constructed input\n")
    monkeypatch.setattr(transfer, "ROOT", tmp_path)
    monkeypatch.setattr(transfer, "OUT", tmp_path / "report")
    monkeypatch.setattr(transfer, "binding_paths", lambda: [source])
    monkeypatch.setattr(transfer, "verify_original_bindings", lambda: None)
    monkeypatch.setattr(
        transfer, "evaluate_model", lambda *args: pytest.fail("freeze computed outcomes")
    )
    transfer.freeze()
    assert transfer.verify_freeze()["translation_scale"] == 1
    with pytest.raises(FileExistsError):
        transfer.freeze()
    assert not (transfer.OUT / "analysis.json").exists()
    source.write_text("changed\n")
    with pytest.raises(ValueError, match="input changed"):
        transfer.verify_freeze()


def test_result_and_report_are_create_once_and_exact_replay_checked(tmp_path, monkeypatch):
    monkeypatch.setattr(transfer, "OUT", tmp_path)
    result = dict(synthetic=True, values=[0.25, 0.5])
    monkeypatch.setattr(transfer, "compute_real", lambda: result)
    monkeypatch.setattr(transfer, "report", lambda value: json.dumps(value) + "\n")
    transfer.execute()
    transfer.execute(check=True)
    with pytest.raises(FileExistsError):
        transfer.execute()
    original = (tmp_path / "analysis.json").read_text()
    (tmp_path / "REPORT.md").write_text("altered report\n")
    with pytest.raises(ValueError, match="replay differs"):
        transfer.execute(check=True)
    assert (tmp_path / "analysis.json").read_text() == original


@pytest.mark.parametrize("action", ["analyze", "check"])
def test_cli_requires_explicit_real_execution_flag(action, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["transfer", action])
    monkeypatch.setattr(transfer, "compute_real", lambda: pytest.fail("unapproved real execution"))
    with pytest.raises(SystemExit) as failure:
        transfer.main()
    assert failure.value.code == 2
