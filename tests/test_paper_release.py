"""Public export boundaries and replay-manifest integrity."""

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "paper_release", Path(__file__).resolve().parents[1] / "tools/paper_release.py"
)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


def test_compact_payload_retains_existing_alignment_identity():
    from latent_art_bench.painter_distribution_revision_v1.metrics import _payload

    source = {"request_id": "slot0001", "sequence": 3,
              "payload": {"prompt": "A fixed scene", "seed": 19},
              "source_response_path": "private-response", "values": [1.0, 2.0]}
    public = release.sanitize(source)
    assert _payload(public) == _payload(source)
    assert public["sequence"] == 3
    assert public["values"] == [1.0, 2.0]
    assert "source_response_path" not in public
    assert "payload" in source


@pytest.mark.parametrize("value", [
    {"path": "/home/example/private.json"}, {"access_token": "hidden"},
    {"value": "data:image/png;base64,AAAA"}, {"url": "https://user:pass@example.org"},
])
def test_numerical_screen_rejects_sensitive_inputs_without_echoing(value):
    with pytest.raises(ValueError) as error:
        release.screen_numerical(value)
    assert "hidden" not in str(error.value)
    assert "user:pass" not in str(error.value)


@pytest.mark.parametrize("value", ["../file", "/absolute", "a/../../b", "a\\b"])
def test_manifest_paths_cannot_escape_release(value):
    with pytest.raises(ValueError):
        release.portable(value)


def test_manifest_rejects_modified_file_and_symlink(tmp_path):
    target = tmp_path / "input.json"
    original = b'{"values":[1,2]}\n'
    target.write_bytes(original)
    manifest = {"files": [{"path": "input.json", "sha256": hashlib.sha256(original).hexdigest()}]}
    (tmp_path / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest))
    release.verify_package(tmp_path)
    target.write_bytes(b'{"values":[1,3]}\n')
    with pytest.raises(ValueError, match="checksum"):
        release.verify_package(tmp_path)
    target.unlink()
    outside = tmp_path / "elsewhere.json"
    outside.write_bytes(original)
    target.symlink_to(outside)
    with pytest.raises(ValueError, match="checksum"):
        release.verify_package(tmp_path)


def test_export_order_and_nonfinite_rejection():
    value = {"painters": {"monet": [2.0], "cezanne": [1.0]}}
    restored = json.loads(release.encoded(value, ordered=True))
    assert list(restored["painters"]) == ["monet", "cezanne"]
    with pytest.raises(ValueError):
        release.encoded({"value": float("nan")})


def test_existing_namespace_is_never_overwritten(tmp_path):
    path = tmp_path / "retained.json"
    release.write_new(path, {"value": 1})
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        release.write_new(path, {"value": 2})
    assert path.read_bytes() == original


def test_portable_comparison_preserves_decisions_counts_and_p_values():
    expected = {"estimate": 0.25, "count": 72, "reject_holm": False, "p_holm": 0.0625}
    assert release.close_values(dict(expected, estimate=0.25 + 1e-12), expected)
    for field, value in (("estimate", 0.250001), ("count", 71), ("reject_holm", True),
                         ("p_holm", 0.0625 + 1e-12)):
        assert not release.close_values(dict(expected, **{field: value}), expected)


def test_failed_portable_replay_reports_actual_paths_without_relaxing_p_values(capsys):
    expected = {"primary": [{"estimate": 0.25, "raw_p": 0.125, "reject": False}]}
    actual = {"primary": [{"estimate": 0.25 + 1e-12, "raw_p": 0.125 + 1e-12,
                           "reject": False}]}
    with pytest.raises(ValueError, match="numerical replay differs"):
        release.assert_digest(actual, release.digest(expected), "replication",
                              reference=expected, portable_numeric=True)
    diagnostic = json.loads(capsys.readouterr().out)
    assert diagnostic["status"] == "numerical_mismatch_diagnostic"
    assert diagnostic["comparison"]["total_mismatches"] == 1
    row = diagnostic["comparison"]["displayed_mismatches"][0]
    assert row["path"] == ["primary", 0, "raw_p"]
    assert row["actual"] == actual["primary"][0]["raw_p"]
    assert row["expected"] == 0.125
    assert row["absolute_and_relative_tolerance"] == 0
    assert row["within_1e_10_if_numeric"] is True
    assert not release.close_values(actual, expected)


def test_comparison_diagnostics_bound_output_and_retain_structural_failures():
    expected = {"rows": [0, 1, 2], "decision": False, "metadata": {"known": 1}}
    actual = {"rows": [3, 4, 5], "decision": True, "metadata": {"other": 1}}
    diagnostic = release.comparison_diagnostics(actual, expected, limit=2)
    assert diagnostic["total_mismatches"] == 5
    assert len(diagnostic["displayed_mismatches"]) == 2
    assert diagnostic["truncated"] is True
    full = release.comparison_diagnostics(actual, expected)
    assert full["displayed_mismatches"][-1]["path"] == ["metadata"]
    assert full["displayed_mismatches"][-1]["actual"] == {"type": "dict", "length": 1}


def test_restoration_preserves_measurement_stage_and_development_scale():
    source = {name: [{"pipeline": "primary512", "values": [2.0] * 31}]
              for name in ("reference", "generated", "development")}
    source["scalers"] = {"primary512": {"scaler": {"center": [0.0] * 31,
                                                  "scale": [2.0] * 31}}}
    restored = release.restored_bundle(source)
    for name in ("reference", "generated", "development"):
        assert restored[name][0]["stage"] == name
        assert restored[name][0]["scaled"] == [1.0] * 31
        assert "stage" not in source[name][0]


def test_manifest_rejects_symlinked_parent_directory(tmp_path):
    package = tmp_path / "package"
    private = tmp_path / "outside"
    package.mkdir()
    private.mkdir()
    raw = b"outside release root"
    (private / "input.json").write_bytes(raw)
    (package / "data").symlink_to(private, target_is_directory=True)
    (package / "RELEASE_MANIFEST.json").write_text(json.dumps({"files": [{
        "path": "data/input.json", "sha256": hashlib.sha256(raw).hexdigest()}]}))
    with pytest.raises(ValueError, match="checksum"):
        release.verify_package(package)


def test_delivery_export_preserves_failures_retries_and_unreported_fields():
    requests = [{"request_id": "a", "payload": {"size": "1024x1024", "quality": "medium"}},
                {"request_id": "b"}]
    slots = [{"request_id": "a", "sequence": 1, "status": "image_returned",
              "selected_attempt": 2, "response_path": "private-response",
              "observed": {"width": 1536, "height": 1024, "format": "PNG",
                           "reported": {"quality": "low", "secret": "hidden"}}},
             {"request_id": "b", "sequence": 2, "status": "not_attempted_collection_stopped",
              "selected_attempt": None, "observed": None}]
    events = [{"request_id": "a", "attempt": 1, "kind": "terminal", "status": "http_error",
               "at_utc": "2026-09-10T00:00:00+00:00", "response_headers": {"secret": "hidden"}},
              {"request_id": "a", "attempt": 2, "kind": "terminal", "status": "image_returned",
               "post_started_at_utc": "2026-09-10T00:00:01+00:00"}]
    value = release.delivery_metadata(requests, slots, events)
    assert len(value["slots"]) == 2
    assert [row["attempt"] for row in value["attempt_events"]] == [1, 2]
    assert value["slots"][0]["width"] == 1536
    assert value["slots"][0]["reported_quality"] == "low"
    assert value["slots"][1]["width"] is None
    assert value["attempt_events"][1]["width"] is None
    assert b"hidden" not in release.encoded(value)
    assert b"private-response" not in release.encoded(value)
    release.screen_numerical(value)
    with pytest.raises(ValueError, match="every allocated slot"):
        release.delivery_metadata(requests, slots[:1], events)


def test_isolation_blocks_socket_creation_and_datagram_paths(monkeypatch, tmp_path):
    hooks = []
    monkeypatch.setattr(release.sys, "addaudithook", hooks.append)
    counters = release.restrict_runtime(tmp_path)
    for event in ("socket.__new__", "socket.sendto", "socket.sendmsg", "socket.connect",
                  "socket.getaddrinfo"):
        with pytest.raises(PermissionError, match="network access is prohibited"):
            hooks[0](event, (None, ("127.0.0.1", 9)))
    assert counters["network_attempts"] == 5


def test_released_prompt_sources_reconstruct_complete_exploratory_library(tmp_path):
    from latent_art_bench.painter_prompt_study_v1.prompts import build_library

    source_root = Path(__file__).resolve().parents[1]
    for relative in release.PROMPT_SOURCES.values():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_root / relative, target)
    # This unchanged scientific function validates the retained literal-string hashes;
    # the temporary input root contains only the three explicitly released inventories.
    library = build_library(tmp_path)
    assert len(library["prompts"]) == 240
    assert len({row["template_id"] for row in library["prompts"]}) == 16
    assert {row["condition"] for row in library["prompts"]} == {
        "artist_free", "claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne"}


def test_blur_share_uses_paired_scaled_deltas_and_equal_painter_means():
    from latent_art_bench.painter_feature_generation_v2.features import FAMILIES, NAMES

    rows = []
    index = NAMES.index("lbp_entropy_8")
    scale = [1.0] * 31
    scale[index] = 2.0
    for identity, painter, lbp, other in (("a0", "monet", 4, 1), ("a1", "monet", 4, 1),
                                         ("b0", "cezanne", 0, 3)):
        for condition in ("baseline", "blur1"):
            values = [0.0] * 31
            if condition == "blur1":
                values[index] = lbp
                values[FAMILIES["texture"].start] = other
                values[0] = 100.0  # Color displacement must not enter the denominator.
            rows.append(dict(image_id=identity, painter_id=painter, stage="reference",
                             condition=condition, values=values))
    value = release.blur_texture_share(rows, {"scale": scale})
    assert value["lbp8_texture_squared_response_share"] == pytest.approx(2 / 7)
    assert value["lbp8_original_development_iqr"] == 2.0
