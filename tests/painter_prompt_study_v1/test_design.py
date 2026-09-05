"""Planning uses numeric metadata only; authorization and calibration precede every write."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from latent_art_bench.io import hash_file, read_json
from latent_art_bench.painter_prompt_study_v1 import design, generation, randomization_record
from latent_art_bench.painter_prompt_study_v1.common import CONFIG, MANIFESTS, WORKSPACE
from latent_art_bench.painter_prompt_study_v1.prompts import SOURCE_PATH

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def settings():
    value = read_json(REPO / CONFIG)
    value.update(repetitions=4, maximum_requests=1920, approved_maximum_requests=0,
                 authorization=None)
    return value


@pytest.fixture
def planning_root(tmp_path, settings, monkeypatch):
    target = tmp_path / CONFIG
    target.parent.mkdir(parents=True)
    target.write_text(json.dumps(settings))
    baseline = tmp_path / SOURCE_PATH
    baseline.parent.mkdir(parents=True)
    baseline.write_bytes((REPO / SOURCE_PATH).read_bytes())
    prior = tmp_path / design.OLD_MANIFESTS / "pfg2-oauth-pilot-20260905/outputs.jsonl"
    prior.parent.mkdir(parents=True)
    prior.write_text("\n".join(json.dumps(row) for row in [
        dict(bytes=1000, latency_seconds=20), dict(bytes=3000, latency_seconds=40),
    ]) + "\n")
    monkeypatch.setattr(design.shutil, "disk_usage", lambda _: SimpleNamespace(free=100 * 1024**3))
    return tmp_path


def inventory(root):
    return {p.relative_to(root): hash_file(p) for p in root.rglob("*") if p.is_file()}


def save_settings(root, value):
    (root / CONFIG).write_text(json.dumps(value))


def test_proposed_config_is_valid_for_planning_but_not_authorized(settings):
    design.validate_config(settings)
    with pytest.raises(ValueError, match="explicit user authorization"):
        design.validate_config(settings, authorized=True)


@pytest.mark.parametrize("updates", [
    dict(repetitions=3, maximum_requests=1440), dict(repetitions=True, maximum_requests=480),
    dict(maximum_requests=960), dict(aliases=["gpt-image-2", "gpt-image-1"]),
    dict(method_ids=["by_name", "style_instruction"]), dict(paid_fallback=True),
    dict(base_url="https://api.openai.com"), dict(minimum_decoded_short_side=1024),
    dict(primary_estimator="jackknife_t"), dict(primary_estimator="paired_t"),
    dict(simultaneous_alpha=0.025),
    dict(size="auto"), dict(quality="high"), dict(output_format="jpeg"),
    dict(background="transparent"), dict(minimum_start_interval_seconds=14),
])
def test_changed_design_or_render_contract_is_rejected(settings, updates):
    settings.update(updates)
    with pytest.raises(ValueError):
        design.validate_config(settings)


@pytest.mark.parametrize("updates", [
    dict(timeout_seconds=241), dict(timeout_seconds=True), dict(timeout_seconds=float("nan")),
    dict(maximum_response_bytes=64 * 1024**2 + 1), dict(maximum_response_bytes=100.5),
    dict(reserve_disk_bytes=5 * 1024**3 - 1), dict(max_runtime_bytes=float("inf")),
    dict(minimum_start_interval_seconds=float("nan")),
    dict(minimum_start_interval_seconds=float("inf")),
])
def test_planning_validation_matches_generation_transport_and_resource_limits(settings, updates):
    settings.update(updates)
    with pytest.raises(ValueError):
        generation._validate_config(settings)
    with pytest.raises(ValueError):
        design.validate_config(settings)


@pytest.mark.parametrize("approved,authorization", [
    (1919, "Explicit fixture authorization"), (1920, ""), (1920, "   "), (1920, None),
])
def test_count_ceiling_and_authorization_text_are_both_required(settings, approved, authorization):
    settings.update(approved_maximum_requests=approved, authorization=authorization)
    with pytest.raises(ValueError, match="explicit user authorization"):
        design.validate_config(settings, authorized=True)


def test_authorized_complete_budget_accepts_exact_or_larger_approved_ceiling(settings):
    for approved in (1920, 2400):
        settings.update(approved_maximum_requests=approved,
                        authorization="Explicit fixture approval of the complete request grid")
        design.validate_config(settings, authorized=True)


def test_plan_exact_grid_and_resource_arithmetic_reads_no_images_or_mutates_files(
    planning_root, settings, monkeypatch,
):
    monkeypatch.setattr(design, "load_source",
                        lambda *args: pytest.fail("planning uses only recorded latency/bytes"))
    monkeypatch.setattr(design, "committed", lambda *args: pytest.fail("planning cannot freeze"))
    before = inventory(planning_root)
    result = design.plan(planning_root)
    assert inventory(planning_root) == before
    assert result["status"] == "planning_only_no_provider_calls"
    assert result["requests"] == 480 * settings["repetitions"] == 1920
    assert result["literal_prompts"] == 240
    assert "independent_repetition_pairs" not in result
    assert result["matched_scene_pairs_per_contrast"] == 64
    assert result["generated_images_per_named_cell"] == 64
    assert result["primary_prompt_contrasts"] == 48
    assert result["secondary_control_adjusted_contrasts"] == 48
    assert result["absolute_distance_endpoints"] == 72
    assert result["historical_mean_response_bytes"] == 2000
    assert result["historical_mean_request_seconds"] == 30
    assert result["estimated_serial_hours"] == 1920 * 30 / 3600
    assert result["estimated_uncompressed_response_gib"] == 1920 * 2000 / 1024**3
    assert result["conservative_storage_preflight_passes"] is True
    assert result["budget_approved"] is False
    assert "not quota or size guarantees" in result["assumptions"]
    assert not (planning_root / WORKSPACE).exists()


@pytest.mark.parametrize("difference,passes", [(0, True), (-1, False)])
def test_plan_checks_complete_estimated_storage_plus_reserve(
    planning_root, settings, monkeypatch, difference, passes,
):
    required = 2000 * settings["maximum_requests"] + settings["reserve_disk_bytes"]
    monkeypatch.setattr(design.shutil, "disk_usage",
                        lambda _: SimpleNamespace(free=required + difference))
    assert design.plan(planning_root)["conservative_storage_preflight_passes"] is passes


def test_plan_uses_runtime_storage_mount_for_disk_availability(planning_root, monkeypatch):
    boundary = planning_root / WORKSPACE
    boundary.parent.mkdir(parents=True, exist_ok=True)
    external = planning_root / "external-volume"
    external.mkdir()
    boundary.symlink_to(external, target_is_directory=True)
    observed = []

    def disk_usage(path):
        observed.append(Path(path).resolve())
        return SimpleNamespace(free=100 * 1024**3)

    monkeypatch.setattr(design.shutil, "disk_usage", disk_usage)
    design.plan(planning_root)
    assert observed == [external]


def test_plan_approval_requires_explicit_authorization(planning_root, settings):
    settings["approved_maximum_requests"] = settings["maximum_requests"]
    save_settings(planning_root, settings)
    assert design.plan(planning_root)["budget_approved"] is False


def test_prepare_unauthorized_stops_before_calibration_inputs_or_any_write(
    planning_root, monkeypatch,
):
    before = inventory(planning_root)
    for name in ("plan", "load_source", "build_library", "committed"):
        monkeypatch.setattr(design, name, lambda *args: pytest.fail("authorization must run first"))
    with pytest.raises(ValueError, match="explicit user authorization"):
        design.prepare(planning_root, "unauthorized-fixture", planning_root / "absent-proxy")
    assert inventory(planning_root) == before
    assert not (planning_root / MANIFESTS / "unauthorized-fixture").exists()
    assert not (planning_root / WORKSPACE).exists()


@pytest.mark.parametrize("change", [
    dict(primary_estimator="jackknife_t"), dict(simultaneous_alpha=0.025),
    dict(qualified_repetitions=[6]), dict(uses_empirical_outcomes_for_tuning=True),
])
def test_prepare_rejects_unqualified_or_retuned_calibration_before_writes(
    planning_root, settings, monkeypatch, change,
):
    settings.update(approved_maximum_requests=settings["maximum_requests"],
                    authorization="Explicit synthetic fixture authorization")
    save_settings(planning_root, settings)
    decision = dict(primary_estimator="paired_randomization", simultaneous_alpha=0.05,
                    qualified_repetitions=[4], uses_empirical_outcomes_for_tuning=False)
    decision.update(change)
    path = planning_root / MANIFESTS / settings["calibration_id"] / "decision.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(decision))
    before = inventory(planning_root)
    # Calibration-record hash validation has separate tests; exercise the design eligibility gate.
    monkeypatch.setattr(randomization_record, "validate_randomization_calibration",
                        lambda root, identifier: read_json(path))
    monkeypatch.setattr(design, "plan", lambda *args: pytest.fail("calibration must run first"))
    with pytest.raises(ValueError, match="qualified calibration"):
        design.prepare(planning_root, "calibration-fixture", planning_root / "absent-proxy")
    assert inventory(planning_root) == before
    assert not (planning_root / MANIFESTS / "calibration-fixture").exists()


def test_existing_run_is_never_overwritten_even_if_budget_is_authorized(planning_root, settings):
    settings = copy.deepcopy(settings)
    settings.update(approved_maximum_requests=settings["maximum_requests"],
                    authorization="Explicit synthetic fixture authorization")
    save_settings(planning_root, settings)
    directory = planning_root / MANIFESTS / "existing-run"
    directory.mkdir(parents=True)
    (directory / "retained.txt").write_text("unique earlier fixture evidence")
    before = inventory(planning_root)
    with pytest.raises(FileExistsError, match="never replaced"):
        design.prepare(planning_root, "existing-run", planning_root / "absent-proxy")
    assert inventory(planning_root) == before


@pytest.mark.parametrize("repetitions", [1, 2, 4])
def test_small_randomized_plan_reports_matched_scenes_without_independent_block_pair_claim(
    planning_root, settings, repetitions,
):
    settings.update(primary_estimator="paired_randomization", simultaneous_alpha=.05,
                    repetitions=repetitions, maximum_requests=480 * repetitions,
                    order_seed=20260905, permutation_seed=20260906,
                    permutation_draws=99999, multiplicity="holm")
    design.validate_config(settings)
    with pytest.raises(ValueError, match="explicit user authorization"):
        design.validate_config(settings, authorized=True)
    save_settings(planning_root, settings)
    before = inventory(planning_root)
    result = design.plan(planning_root)
    assert result["requests"] == 480 * repetitions
    assert "independent_repetition_pairs" not in result
    assert result["matched_scene_pairs_per_contrast"] == 16 * repetitions
    assert result["primary_prompt_contrasts"] == 48
    assert result["estimated_serial_hours"] == 480 * repetitions * 30 / 3600
    assert inventory(planning_root) == before


@pytest.mark.parametrize("updates", [
    dict(order_seed=None), dict(order_seed=True), dict(order_seed=-1),
    dict(permutation_seed=None), dict(permutation_seed=True), dict(permutation_seed=-1),
    dict(permutation_draws=9999), dict(multiplicity="bonferroni"), dict(simultaneous_alpha=.025),
    dict(repetitions=3, maximum_requests=1440), dict(repetitions=0, maximum_requests=0),
])
def test_small_randomized_design_rejects_unfrozen_assignment_or_inference(settings, updates):
    settings.update(primary_estimator="paired_randomization", simultaneous_alpha=.05,
                    order_seed=20260905, permutation_seed=20260906,
                    permutation_draws=99999, multiplicity="holm")
    settings.update(updates)
    with pytest.raises(ValueError):
        design.validate_config(settings)
