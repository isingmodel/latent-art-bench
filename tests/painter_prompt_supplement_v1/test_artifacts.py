"""Offline evidence and crash-recovery checks at the supplement publication boundary."""

import copy
import hashlib
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from latent_art_bench.io import canonical_json
from latent_art_bench.painter_prompt_supplement_v1 import artifacts, report, validation

REPO = Path(__file__).resolve().parents[2]
ANALYSIS_ID = "supplement-fixture"
SOURCE_ID = "source-fixture"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value) + "\n", encoding="utf-8")


def git(root, *arguments, timestamp=None):
    environment = os.environ.copy()
    if timestamp:
        environment.update(GIT_AUTHOR_DATE=timestamp, GIT_COMMITTER_DATE=timestamp)
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        env=environment,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


@pytest.fixture
def git_root(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Offline fixture")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    for name in ("first.txt", "second.txt"):
        (tmp_path / name).write_text(name + "\n")
    git(tmp_path, "add", "first.txt", "second.txt")
    git(tmp_path, "commit", "-qm", "Synthetic inputs", timestamp="2026-09-05T00:00:00+00:00")
    return tmp_path


@pytest.mark.parametrize("damage", ["empty", "partial", "duplicate"])
def test_commit_verification_requires_exact_nonempty_input_inventory(git_root, damage):
    paths = [Path("first.txt"), Path("second.txt")]
    inputs = artifacts.bindings(git_root, paths)
    record = dict(recorded_git_commit=git(git_root, "rev-parse", "HEAD"), inputs=inputs)
    artifacts._verify_commit(git_root, record, expected_paths=paths)
    record["inputs"] = (
        [] if damage == "empty" else inputs[:1] if damage == "partial" else inputs + inputs[:1]
    )
    with pytest.raises(ValueError):
        artifacts._verify_commit(git_root, record, expected_paths=paths)


def test_historical_commit_and_current_worktree_are_both_checked(git_root):
    paths = [Path("first.txt"), Path("second.txt")]
    record = dict(
        recorded_git_commit=git(git_root, "rev-parse", "HEAD"),
        inputs=artifacts.bindings(git_root, paths),
    )
    (git_root / paths[0]).write_text("uncommitted replacement")
    with pytest.raises(ValueError):
        artifacts._verify_commit(git_root, record, expected_paths=paths)
    artifacts._verify_commit(git_root, record, expected_paths=paths, current=False)
    record["inputs"] = artifacts.bindings(git_root, paths)
    with pytest.raises(ValueError):
        artifacts._verify_commit(git_root, record, expected_paths=paths)


def test_loaded_module_must_match_bound_source_bytes(tmp_path):
    relative = Path(artifacts.__file__).resolve().relative_to(REPO)
    source = tmp_path / relative
    source.parent.mkdir(parents=True)
    source.write_bytes(Path(artifacts.__file__).read_bytes())
    artifacts._verify_loaded(tmp_path, artifacts.bindings(tmp_path, [relative]))
    source.write_text("# Different implementation under the same bound relative path.\n")
    with pytest.raises(ValueError):
        artifacts._verify_loaded(tmp_path, artifacts.bindings(tmp_path, [relative]))


@pytest.fixture(scope="module")
def qualification_content():
    config = artifacts._config(REPO)
    oracles = validation.validate_oracles()

    def synthetic(seed):
        return dict(
            seed=seed,
            trials_per_cell=2000,
            family_size=48,
            alpha=0.05,
            adjustment="Holm",
            permutation_draws=99999,
            uses_empirical_outcomes_for_tuning=False,
            null_cells=[
                dict(
                    case=case,
                    dependence=dependence,
                    trials=2000,
                    family_size=48,
                    family_rejections=0,
                    family_rejection_rate=0.0,
                    family_rejection_wilson_95=list(artifacts.wilson(0, 2000)),
                )
                for case in validation.CASE_IDS
                for dependence in validation.DEPENDENCE_IDS
            ],
        )

    return (
        config,
        oracles,
        synthetic(config["development_seed"]),
        synthetic(config["validation_seed"]),
    )


def test_development_fwer_failure_cannot_be_hidden_by_passing_validation(qualification_content):
    config, oracles, development, checked = copy.deepcopy(qualification_content)
    assert artifacts._qualification_content(config, oracles, development, checked)
    development["null_cells"][0].update(
        family_rejections=200,
        family_rejection_rate=0.1,
        family_rejection_wilson_95=list(artifacts.wilson(200, 2000)),
    )
    assert not artifacts._qualification_content(config, oracles, development, checked)


@pytest.mark.parametrize("damage", ["empty", "partial", "duplicate"])
def test_qualification_checks_expected_sources_not_just_listed_hashes(
    git_root, monkeypatch, qualification_content, damage
):
    config, oracles, development, checked = copy.deepcopy(qualification_content)
    paths = [Path("first.txt"), Path("second.txt")]
    monkeypatch.setattr(artifacts, "_config", lambda *args: config)
    monkeypatch.setattr(artifacts, "_source_paths", lambda *args: paths)
    directory = artifacts.MANIFESTS / config["qualification_id"]
    for name, value in (
        ("oracles", oracles),
        ("development", development),
        ("validation", checked),
    ):
        write_json(git_root / directory / f"{name}.json", value)
    inputs = artifacts.bindings(git_root, paths)
    record = dict(
        qualification_id=config["qualification_id"],
        qualified=True,
        criterion=validation.CRITERION,
        recorded_git_commit=git(git_root, "rev-parse", "HEAD"),
        inputs=inputs,
        files=artifacts.bindings(
            git_root,
            [directory / f"{name}.json" for name in ("oracles", "development", "validation")],
        ),
    )
    write_json(git_root / directory / "decision.json", record)
    assert artifacts.check_qualification(git_root, config["qualification_id"]) == record
    record["inputs"] = (
        [] if damage == "empty" else inputs[:1] if damage == "partial" else inputs + inputs[:1]
    )
    write_json(git_root / directory / "decision.json", record)
    with pytest.raises(ValueError):
        artifacts.check_qualification(git_root, config["qualification_id"])


@pytest.mark.parametrize(
    "oracle,key,value",
    [
        ("weighted_energy_swaps", "maximum_absolute_error", 0.1),
        ("conditional_triplet_allocations", "unavailable_template_is_ineligible", False),
        ("conditional_triplet_allocations", "conditioning_strata", 0),
        ("ties_and_zero", "pvalues", [0.0, 0.0]),
        ("uniform_weight_reduction", "passed", False),
    ],
)
def test_pass_flags_do_not_override_invalid_oracle_metrics(
    qualification_content, oracle, key, value
):
    config, oracles, development, checked = copy.deepcopy(qualification_content)
    next(row for row in oracles["checks"] if row["id"] == oracle)[key] = value
    with pytest.raises(ValueError):
        artifacts._qualification_content(config, oracles, development, checked)


@pytest.mark.parametrize(
    "measurement_file",
    [
        "measurement_events.jsonl",
        "measurement_receipt.json",
        "measured_features.jsonl",
    ],
)
def test_prepare_stops_before_other_work_when_measurement_has_started(
    tmp_path, monkeypatch, measurement_file
):
    config = artifacts._config(REPO)
    write_json(tmp_path / artifacts.CONFIG, config)
    path = tmp_path / artifacts.SOURCE_MANIFESTS / config["source_run_id"] / measurement_file
    path.parent.mkdir(parents=True)
    path.write_text("")

    def forbidden(*args, **kwargs):
        pytest.fail("qualification/source access occurred after measurement was detected")

    monkeypatch.setattr(artifacts, "check_qualification", forbidden)
    monkeypatch.setattr(artifacts, "_source_paths", forbidden)
    with pytest.raises(ValueError, match="precede source measurement"):
        artifacts.prepare(tmp_path, ANALYSIS_ID)
    assert not (tmp_path / artifacts.MANIFESTS).exists()


def test_publication_requires_a_committed_unchanged_artifact(git_root):
    path = artifacts.MANIFESTS / ANALYSIS_ID / "design_freeze.json"
    write_json(git_root / path, dict(fixture=True))
    with pytest.raises(ValueError):
        artifacts._publication_commit(git_root, path)
    git(git_root, "add", path.as_posix())
    git(git_root, "commit", "-qm", "Publish freeze", timestamp="2026-09-05T00:01:00+00:00")
    commit, seconds = artifacts._publication_commit(git_root, path)
    assert commit == git(git_root, "rev-parse", "HEAD")
    assert seconds == 1788566460
    write_json(git_root / path, dict(fixture="changed"))
    with pytest.raises(ValueError):
        artifacts._publication_commit(git_root, path)


@pytest.mark.parametrize("offset", [-1, 0, 0.5, 1, 60])
def test_commit_publication_strictly_precedes_measurement_stage_start(git_root, offset):
    path = artifacts.MANIFESTS / ANALYSIS_ID / "design_freeze.json"
    frozen = dict(analysis_id=ANALYSIS_ID, source_run_id=SOURCE_ID)
    write_json(git_root / path, frozen)
    git(git_root, "add", path.as_posix())
    git(
        git_root,
        "commit",
        "-qm",
        "Publish before measurement",
        timestamp="2026-09-05T00:01:00+00:00",
    )
    started = datetime(2026, 9, 5, 0, 1, tzinfo=timezone.utc) + timedelta(seconds=offset)
    event = dict(kind="stage_start", sequence=0, previous_sha256=None, at_utc=started.isoformat())
    event["event_sha256"] = artifacts.generation.digest(event)
    write_json(
        git_root / artifacts.SOURCE_MANIFESTS / SOURCE_ID / "measurement_events.jsonl", event
    )
    if offset < 1:
        with pytest.raises(ValueError, match="publication must precede"):
            artifacts._verify_publication(git_root, ANALYSIS_ID, frozen)
    else:
        artifacts._verify_publication(git_root, ANALYSIS_ID, frozen)


@pytest.mark.parametrize("damage", ["empty", "wrong_kind", "naive_time", "broken_chain"])
def test_publication_chronology_requires_a_valid_measurement_start(git_root, damage):
    path = artifacts.MANIFESTS / ANALYSIS_ID / "design_freeze.json"
    frozen = dict(analysis_id=ANALYSIS_ID, source_run_id=SOURCE_ID)
    write_json(git_root / path, frozen)
    git(git_root, "add", path.as_posix())
    git(git_root, "commit", "-qm", "Publish freeze", timestamp="2026-09-05T00:01:00+00:00")
    event = dict(
        kind="stage_start", sequence=0, previous_sha256=None, at_utc="2026-09-05T00:02:00+00:00"
    )
    if damage == "wrong_kind":
        event["kind"] = "terminal"
    if damage == "naive_time":
        event["at_utc"] = "2026-09-05T00:02:00"
    event["event_sha256"] = artifacts.generation.digest(event)
    if damage == "broken_chain":
        event["event_sha256"] = "f" * 64
    ledger = git_root / artifacts.SOURCE_MANIFESTS / SOURCE_ID / "measurement_events.jsonl"
    write_json(ledger, event)
    if damage == "empty":
        ledger.write_text("")
    with pytest.raises(ValueError):
        artifacts._verify_publication(git_root, ANALYSIS_ID, frozen)


@pytest.fixture
def publication_case(tmp_path, monkeypatch):
    directory = tmp_path / artifacts.MANIFESTS / ANALYSIS_ID
    frozen = dict(
        analysis_id=ANALYSIS_ID,
        source_run_id=SOURCE_ID,
        recorded_git_commit="a" * 40,
    )
    write_json(directory / "design_freeze.json", frozen)
    source = tmp_path / "numeric_source.json"
    write_json(source, dict(fixture=True))
    computed = dict(
        analysis_id=ANALYSIS_ID,
        source_run_id=SOURCE_ID,
        registered_primary_status="unavailable_incomplete_grid",
        inputs=artifacts.bindings(tmp_path, [source.relative_to(tmp_path)]),
        completed_at_utc="2026-09-05T00:10:00+00:00",
        distances=[dict(value=0.125)],
    )
    monkeypatch.setattr(artifacts, "_freeze", lambda *args: (directory, frozen))
    monkeypatch.setattr(artifacts, "result", lambda *args: copy.deepcopy(computed))

    def render(value, output):
        output.mkdir(parents=True)
        (output / "REPORT.md").write_text("Synthetic report\n" + canonical_json(value))
        (output / "plots").mkdir()
        (output / "plots" / "numeric.svg").write_text("<svg>numeric fixture</svg>\n")

    monkeypatch.setattr(report, "write_bundle", render)
    return tmp_path, directory, computed, render


@pytest.mark.parametrize("orphan", ["analysis", "report", "both"])
def test_build_recovers_only_identical_recomputed_orphan_evidence(publication_case, orphan):
    root, directory, computed, render = publication_case
    target = root / artifacts.REPORTS / ANALYSIS_ID
    if orphan in ("analysis", "both"):
        write_json(directory / "analysis.json", computed)
    if orphan in ("report", "both"):
        render(computed, target)
    receipt = artifacts.build(root, ANALYSIS_ID)
    assert receipt["registered_primary_status"] == "unavailable_incomplete_grid"
    assert (directory / "report_receipt.json").is_file()
    assert artifacts.check(root, ANALYSIS_ID)["status"] == "PASS"


@pytest.mark.parametrize("damage", ["numeric", "report", "extra_file"])
def test_build_preserves_bad_orphans_and_never_publishes_receipt(publication_case, damage):
    root, directory, computed, render = publication_case
    target = root / artifacts.REPORTS / ANALYSIS_ID
    write_json(directory / "analysis.json", computed)
    render(computed, target)
    if damage == "numeric":
        computed = copy.deepcopy(computed)
        computed["distances"][0]["value"] = 99.0
        write_json(directory / "analysis.json", computed)
    elif damage == "report":
        (target / "plots" / "numeric.svg").write_text("unique corrupted report")
    else:
        (target / "unexpected.txt").write_text("unique additional file")
    before = {p.relative_to(root): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    with pytest.raises((ValueError, FileExistsError)):
        artifacts.build(root, ANALYSIS_ID)
    assert not (directory / "report_receipt.json").exists()
    assert all((root / path).read_bytes() == body for path, body in before.items())


@pytest.mark.parametrize(
    "damage",
    ["numeric", "report", "numeric_with_refreshed_receipt", "report_with_refreshed_receipt"],
)
def test_check_rejects_numeric_and_report_tampering_even_with_rehashed_receipt(
    publication_case, damage
):
    root, directory, computed, _ = publication_case
    receipt = artifacts.build(root, ANALYSIS_ID)
    target = root / artifacts.REPORTS / ANALYSIS_ID
    if damage.startswith("numeric"):
        changed = copy.deepcopy(computed)
        changed["distances"][0]["value"] = 0.375
        write_json(directory / "analysis.json", changed)
    else:
        (target / "plots" / "numeric.svg").write_text("forged graphic")
    if damage.endswith("refreshed_receipt"):
        receipt["inputs"] = artifacts.bindings(
            root,
            [
                artifacts.MANIFESTS / ANALYSIS_ID / name
                for name in ("analysis.json", "design_freeze.json")
            ],
        )
        receipt["files"] = artifacts.bindings(
            root, [p.relative_to(root) for p in target.rglob("*") if p.is_file()]
        )
        write_json(directory / "report_receipt.json", receipt)
    with pytest.raises(ValueError):
        artifacts.check(root, ANALYSIS_ID)


@pytest.mark.parametrize("orphan", ["qualification", "analysis", "report", "report_without_freeze"])
def test_audit_reports_orphans_instead_of_prepared_success(publication_case, orphan):
    root, directory, computed, render = publication_case
    if orphan == "qualification":
        write_json(
            root / artifacts.MANIFESTS / "qualification-orphan" / "oracles.json",
            dict(overall="PASS"),
        )
    elif orphan == "analysis":
        write_json(directory / "analysis.json", computed)
    elif orphan == "report":
        render(computed, root / artifacts.REPORTS / ANALYSIS_ID)
    else:
        render(computed, root / artifacts.REPORTS / "unknown-analysis")
    checked = artifacts.audit(root)
    assert checked["overall"] == "FAIL"
    assert checked["failures"]


def test_interrupted_receipt_publication_is_recovered_after_recomputing(
    publication_case, monkeypatch
):
    root, directory, _, _ = publication_case
    publish = artifacts._publish_immutable

    def interrupted(path, value):
        if path.name == "report_receipt.json":
            raise OSError("simulated disk interruption before receipt publication")
        publish(path, value)

    monkeypatch.setattr(artifacts, "_publish_immutable", interrupted)
    with pytest.raises(OSError, match="simulated disk interruption"):
        artifacts.build(root, ANALYSIS_ID)
    assert (directory / "analysis.json").is_file()
    assert (root / artifacts.REPORTS / ANALYSIS_ID / "REPORT.md").is_file()
    assert not (directory / "report_receipt.json").exists()
    monkeypatch.setattr(artifacts, "_publish_immutable", publish)
    artifacts.build(root, ANALYSIS_ID)
    assert artifacts.check(root, ANALYSIS_ID)["status"] == "PASS"


def test_immutable_publication_does_not_truncate_unique_existing_bytes(tmp_path):
    path = tmp_path / "unique.json"
    path.write_bytes(b"unique partial evidence")
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises((ValueError, FileExistsError)):
        artifacts._publish_immutable(path, dict(replacement=True))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
