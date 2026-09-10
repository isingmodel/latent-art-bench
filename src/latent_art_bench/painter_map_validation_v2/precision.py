"""One prospective R10 assessment after a retained v1 precision failure.

All numerical primitives, proxy laws, thresholds and seeds are reused unchanged.
Only the sole repetition count, finite-R energy target and provenance/version
change. This is simulation-informed redesign, not outcome-blind validation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
from pathlib import Path

from latent_art_bench.painter_map_validation_v1 import precision as v1

REPEATS = 10
STUDY_PATH = Path("studies/painter_map_validation_v2")
OUTPUT_PATH = STUDY_PATH / "pmvqv2-20260910"
SOURCE_PATH = Path("src/latent_art_bench/painter_map_validation_v2/precision.py")
PREVIOUS_PATH = Path("studies/painter_map_validation_v1/pmvqv1-20260910")
PREVIOUS_COMMIT = "eb70ab8c30019b4b283366c170f8bdaf1405a023"
PREVIOUS_HASHES = {
    "RUN.json": "944a8ea098b55d8ccb12c66f8b55dd55582456b080e0c77139f8100f4d0589e8",
    "precision.json": "ca5da6798dfc4c6056de6250320d85d1c17dffe1a0d274788d3ac8091557598a",
    "PRECISION.md": "c65ec527fd67289baefa7f52207a85778b84e818015546f703c589994c703555",
}
BINDINGS = tuple(
    sorted(
        set(v1.BINDINGS)
        | {
            SOURCE_PATH,
            SOURCE_PATH.with_name("__init__.py"),
            Path("tests/painter_map_validation_v2/test_precision.py"),
            STUDY_PATH / "DECISION.md",
            STUDY_PATH / "PRECISION_PROTOCOL.md",
            *(PREVIOUS_PATH / name for name in PREVIOUS_HASHES),
        }
    )
)


def read_previous(root):
    """Verify the complete immutable failed record and its original source bytes.

    No old simulation is rerun. Paths/hashes are retained; source/decision bodies
    are local provenance and are not automatically a public payload.
    """
    root = Path(root)
    raw = {}
    for name, expected in PREVIOUS_HASHES.items():
        path = root / PREVIOUS_PATH / name
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("symlink predecessor evidence forbidden")
        raw[name] = path.read_bytes()
        if hashlib.sha256(raw[name]).hexdigest() != expected:
            raise ValueError(f"immutable v1 terminal hash mismatch: {name}")
    run, result = (json.loads(raw[name]) for name in ("RUN.json", "precision.json"))
    if (
        run.get("schema") != "painter-map-precision-run/1"
        or run.get("source_commit") != PREVIOUS_COMMIT
    ):
        raise ValueError("wrong predecessor qualification identity")
    if any(result.get(k) != value for k, value in run.items()):
        raise ValueError("v1 RUN/result provenance mismatch")
    records = run["source_bindings"]
    expected_paths = {p.as_posix() for p in v1.BINDINGS}
    if len(records) != len(expected_paths) or {r["path"] for r in records} != expected_paths:
        raise ValueError("complete unique v1 source-binding inventory required")
    for row in records:
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("portable predecessor bindings required")
        path = root / relative
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("symlink predecessor source forbidden")
        data = path.read_bytes()
        committed = subprocess.run(
            ["git", "show", f"{PREVIOUS_COMMIT}:{relative.as_posix()}"],
            cwd=root,
            capture_output=True,
        )
        if (
            hashlib.sha256(data).hexdigest() != row["sha256"]
            or committed.returncode
            or committed.stdout != data
        ):
            raise ValueError(f"immutable predecessor source mismatch: {relative}")
    decision = v1.allocation_decision(result["qualification"]["records"])
    if decision["decision"] != "stop_inferential_proposal" or any(
        result["qualification"].get(k) != value for k, value in decision.items()
    ):
        raise ValueError("v1 failure and complete allocation decision must remain intact")
    return dict(
        source_commit=PREVIOUS_COMMIT,
        decision="stop_inferential_proposal",
        artifacts=[
            dict(path=(PREVIOUS_PATH / name).as_posix(), sha256=sha)
            for name, sha in sorted(PREVIOUS_HASHES.items())
        ],
    )


def allocation_decision(records):
    """One candidate, unchanged coverage/half-width rules; no fallback allocation."""
    expected = {(sh, m, rg) for sh in v1.SHAPES for m in v1.MEANS for rg in v1.REGIMES}
    if len(records) != 27 or {(r["shape"], r["mean"], r["regime"]) for r in records} != expected:
        raise ValueError("exactly all 27 declared proxy cells required")
    if any(r["R"] != REPEATS or r["outputs"] != 240 or r["trials"] != v1.TRIALS for r in records):
        raise ValueError("sole R10/240-output/10000-trial candidate required")
    for row in records:
        if not isinstance(row["median_half_width"], list) or len(row["median_half_width"]) != 2:
            raise ValueError("exactly two half-width entries required")
        lower = row["coverage_lower"]
        if not v1.np.isfinite(lower) or not 0 <= lower <= 1:
            raise ValueError("finite probability coverage bound required")
    coverage = all(row["coverage_lower"] >= v1.COVERAGE_MIN for row in records)
    width = all(
        all(
            x is not None and 0 <= x <= limit
            for x, limit in zip(row["median_half_width"], v1.WIDTH_LIMITS)
        )
        for row in records
        if row["regime"] == "baseline"
    )
    passed = coverage and width
    return dict(
        allocations=[
            dict(
                R=REPEATS,
                outputs=240,
                coverage_pass=coverage,
                baseline_width_pass=width,
                qualified=passed,
            )
        ],
        selected_R=REPEATS if passed else None,
        selected_outputs=240 if passed else None,
        decision="qualified_proxy_only" if passed else "stop_inferential_proposal",
    )


def qualify(proxy):
    """Exactly 27 new cells; immutable v1 numerical primitives receive R=10."""
    records = []
    for sh in range(3):
        for m in range(3):
            for rg in range(3):
                table = v1.scenario(proxy, sh, m, rg)
                support_hash = hashlib.sha256(
                    table.free.astype("<f8").tobytes() + table.named.astype("<f8").tobytes()
                ).hexdigest()
                seed = [v1.TRIAL_SEED, sh, m, rg, REPEATS]
                row = v1.simulate_cell(table, REPEATS, v1.TRIALS, v1.np.random.SeedSequence(seed))
                row.update(
                    shape=v1.SHAPES[sh],
                    mean=v1.MEANS[m],
                    regime=v1.REGIMES[rg],
                    trial_seed=seed,
                    support_sha256=support_hash,
                )
                records.append(row)
    return dict(records=records, **allocation_decision(records))


def bindings_at_head(root):
    root = Path(root)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, check=True, text=True
    ).stdout.strip()
    records = []
    for relative in BINDINGS:
        path = root / relative
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("portable binding paths required")
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("symlink bindings forbidden")
        data = path.read_bytes()
        for revision in (f"{commit}:{relative.as_posix()}", f":{relative.as_posix()}"):
            blob = subprocess.run(["git", "show", revision], cwd=root, capture_output=True)
            if blob.returncode or blob.stdout != data:
                raise ValueError(f"commit clean v2 source/input before qualification: {relative}")
        records.append(dict(path=relative.as_posix(), sha256=hashlib.sha256(data).hexdigest()))
    return commit, records


def report(value):
    note = (
        "V2 is one R10/240-output pre-data redesign informed by retained failed v1 simulations.\n"
        "V1 remains stopped. This record does not combine Monte Carlo confidence across versions.\n"
        "E targets the expected finite-R10 V contrast; Q keeps its conditional-mean target.\n"
        "The .05/81 lower-bound tail, .94 coverage floor and .25/1.0 baseline half-width limits\n"
        "are unchanged. No fallback, additional allocation or live gate follows from this record.\n"
    )
    return (
        v1.report(value)
        .replace(
            "# Fixed-map offline precision qualification",
            "# R10 fixed-map precision qualification v2",
            1,
        )
        .replace("\n\n", "\n\n" + note + "\n", 1)
    )


def build(root):
    """Create one provenance-bound v2 record after parent review/clean commit."""
    root = Path(root).resolve()
    output = root / OUTPUT_PATH
    if output.exists() or output.is_symlink():
        raise ValueError("v2 qualification output directory is create-once")
    commit, bindings = bindings_at_head(root)
    previous = read_previous(root)
    proxy = v1.load_proxy(root)
    environment = dict(
        python=platform.python_version(),
        numpy=v1.np.__version__,
        scipy=v1.scipy.__version__,
        platform=platform.platform(),
    )
    run = dict(
        schema="painter-map-precision-v2-run/1",
        source_commit=commit,
        source_bindings=bindings,
        environment=environment,
        predecessor=previous,
        cross_version_confidence_claim=False,
    )
    output.mkdir(parents=True, exist_ok=False)
    with (output / "RUN.json").open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(run, indent=2, sort_keys=True, allow_nan=False) + "\n")
    value = dict(run, proxy_scene_ids=proxy["scene_ids"], qualification=qualify(proxy))
    if bindings_at_head(root) != (commit, bindings) or read_previous(root) != previous:
        raise ValueError("source/lineage changed during qualification; preserve partial v2 record")
    for name, content in (
        ("precision.json", json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"),
        ("PRECISION.md", report(value)),
    ):
        with (output / name).open("x", encoding="utf-8") as handle:
            handle.write(content)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = build(args.root)["qualification"]
    print(
        json.dumps(
            dict(
                output=str(OUTPUT_PATH),
                decision=result["decision"],
                selected_outputs=result["selected_outputs"],
            )
        )
    )


if __name__ == "__main__":
    main()
