"""Two explicitly authorized retries, retained separately from the terminal prompt study."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import subprocess
import tempfile
import time
from collections import Counter
from pathlib import Path

import httpx
import numpy as np

from latent_art_bench.io import hash_file, read_json, read_jsonl, utc_now
from latent_art_bench.painter_feature_distance_v1.analysis import load_source
from latent_art_bench.painter_feature_generation_v1.panel import PAINTER_IDS, SHORT_LABELS
from latent_art_bench.painter_feature_generation_v2 import features, statistics
from latent_art_bench.painter_feature_generation_v2.artifacts import (
    append_event,
    bindings,
    digest,
    events,
    publish,
    stage_lock,
    verify_bindings,
)
from latent_art_bench.painter_prompt_study_v1 import analysis, generation, measurement
from latent_art_bench.painter_prompt_study_v1.calibration_record import _verify_commit
from latent_art_bench.painter_prompt_study_v1.prompts import CONDITIONS, METHOD_IDS, TEMPLATE_IDS
from latent_art_bench.painter_prompt_supplement_v1.report import (
    COLORS,
    METHOD_LABELS,
    STYLE,
    _csv,
    _save,
    _table,
    plt,
)
from latent_art_bench.painter_prompt_supplement_v1.statistics import weighted_energy

SOURCE = "pps1-gpt-prompts-20260905"
RUN = "ppr1-two-refusals-20260906"
DIRECTORY = Path("data/manifests/painter_prompt_retry_v1") / RUN
REPORT = Path("reports/painter_prompt_retry_v1") / RUN
SEQUENCES = (415, 1718)
PROTOCOL = Path("studies/painter_prompt_retry_v1/PROTOCOL.md")
SUPPLEMENT = Path("data/manifests/painter_prompt_supplement_v1/ppss1-missingness-20260905")
TABLES = ("distances", "absolute", "contrasts", "control_comparisons", "changes", "availability")


def select_requests(requests, outputs):
    """Authorize only the two exact, previously refused request payloads."""
    if len(requests) != 1920 or len(outputs) != 1920:
        raise ValueError("expected the terminal 1920-request source")
    if [i for i, row in enumerate(outputs) if row["status"] != "generated"] != list(SEQUENCES):
        raise ValueError("source refusal roster changed")
    selected = []
    for sequence in SEQUENCES:
        request, output = requests[sequence], outputs[sequence]
        if (
            request["sequence"] != sequence
            or output["status"] != "refused"
            or output["request_id"] != request["request_id"]
            or request["alias"] != "gpt-image-1"
            or request["method_id"] != "by_name"
        ):
            raise ValueError("retry must map to an exact original refusal")
        selected.append(copy.deepcopy(request))
    return selected


def prepare(root):
    analysis.build_result(root, SOURCE)  # Validate original terminal numeric evidence.
    directory, original, requests, outputs, _ = measurement._source(root, SOURCE)
    selected = select_requests(requests, outputs)
    paths = [Path(r["path"]) for r in original["inputs"]]
    paths += [p.relative_to(root) for p in directory.iterdir() if p.is_file()]
    paths += [p.relative_to(root) for p in (root / SUPPLEMENT).iterdir() if p.is_file()]
    paths += [
        PROTOCOL,
        Path(__file__).resolve().relative_to(root),
        Path("tests/test_painter_prompt_retry_v1.py"),
    ]
    # The numeric plot helpers and weighted distance implementation are reused unchanged.
    paths += [
        Path("src/latent_art_bench/painter_prompt_supplement_v1") / name
        for name in ("__init__.py", "report.py", "statistics.py")
    ]
    records = bindings(root, paths)
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    _verify_commit(root, commit, records)
    freeze = dict(
        schema_version="painter-prompt-retry/1.0",
        run_id=RUN,
        source_run_id=SOURCE,
        source_method_id=original["source_method_id"],
        maximum_new_requests=2,
        requests=selected,
        inputs=records,
        recorded_git_commit=commit,
        authorization="User: retry for those two failed trial. then give me the main results",
        authorized_at_date="2026-09-06",
        prepared_at_utc=utc_now().isoformat(),
        original_primary_status="unavailable_incomplete_grid",
        inference="post-hoc descriptive completion; no new randomization p-values or CIs",
        config=original["config"],
        proxy_source=original["proxy_source"],
        source_refusals=[dict(sequence=i, output_sha256=digest(outputs[i])) for i in SEQUENCES],
        workspace=(generation.WORKSPACE / RUN).as_posix(),
    )
    publish(root / DIRECTORY / "retry_freeze.json", freeze)
    return dict(status="prepared", requests=2, run_id=RUN)


def load(root):
    path = root / DIRECTORY / "retry_freeze.json"
    freeze = read_json(path)
    verify_bindings(root, freeze["inputs"])
    _verify_commit(root, freeze["recorded_git_commit"], freeze["inputs"])
    recorded = subprocess.check_output(
        ["git", "show", f"HEAD:{DIRECTORY / 'retry_freeze.json'}"], cwd=root
    )
    if recorded != path.read_bytes():
        raise ValueError("retry freeze must be committed before execution")
    directory, original, requests, outputs, _ = measurement._source(root, SOURCE)
    if (
        freeze["requests"] != select_requests(requests, outputs)
        or freeze["config"] != original["config"]
        or freeze["proxy_source"] != original["proxy_source"]
        or freeze["maximum_new_requests"] != 2
        or freeze["run_id"] != RUN
        or freeze["source_run_id"] != SOURCE
    ):
        raise ValueError("retry identity, payload, budget or transport changed")
    return freeze, directory


def execute(root, proxy_root=None, *, transport=None, sleep=time.sleep):
    freeze, _ = load(root)
    workspace = root / generation.WORKSPACE / RUN
    directory = root / DIRECTORY
    config = freeze["config"]
    with stage_lock(workspace / ".writer.lock"):
        # A durable marker prohibits redispatch, including after a process interruption.
        if (directory / "generation_events.jsonl").exists():
            raise FileExistsError("retry execution is one-shot; never redispatch an intent")
        if transport is None:
            if proxy_root is None:
                raise ValueError("the original inspected proxy checkout is required")
            generation._verify_proxy(freeze, proxy_root)
        allowance = config["maximum_response_bytes"] + 65536
        if shutil.disk_usage(workspace).free < config["reserve_disk_bytes"] + 2 * allowance:
            raise OSError("insufficient free space for two bounded responses")
        ledger = directory / "generation_events.jsonl"
        append_event(
            ledger,
            dict(
                kind="start",
                freeze_sha256=hash_file(directory / "retry_freeze.json"),
                maximum_new_requests=2,
            ),
        )
        stopped, results, last_start = None, [], 0.0
        with httpx.Client(
            transport=transport,
            follow_redirects=False,
            trust_env=False,
            headers={"Accept-Encoding": "identity"},
        ) as client:
            for request in freeze["requests"]:
                if stopped:
                    row = dict(
                        generation._identity(request),
                        status="not_attempted",
                        attempted=False,
                        blocker=stopped,
                    )
                else:
                    sleep(
                        max(
                            0,
                            config["minimum_start_interval_seconds"]
                            - (time.monotonic() - last_start),
                        )
                    )
                    if transport is None:
                        generation._verify_proxy(freeze, proxy_root, verify_commit=False)
                    verify_bindings(root, freeze["inputs"])
                    if shutil.disk_usage(workspace).free < config["reserve_disk_bytes"] + allowance:
                        raise OSError("disk reserve reached before dispatch")
                    append_event(
                        ledger,
                        dict(
                            kind="attempt",
                            request_id=request["request_id"],
                            request_sha256=digest(request),
                        ),
                    )
                    last_start = time.monotonic()
                    output, _ = generation._request(client, root, RUN, request, config, allowance)
                    row = dict(generation._identity(request), **output, attempted=True)
                    if row["status"] in generation.STOP_STATUSES or row.get("outcome_uncertain"):
                        stopped = row["status"]
                append_event(ledger, dict(kind="terminal", row=row))
                results.append(row)
        publish(directory / "outputs.jsonl", results, lines=True)
        receipt = dict(
            run_id=RUN,
            terminal=True,
            attempted=sum(r["attempted"] for r in results),
            statuses=dict(Counter(r["status"] for r in results)),
            inputs=bindings(
                root,
                [
                    DIRECTORY / "retry_freeze.json",
                    DIRECTORY / "generation_events.jsonl",
                    DIRECTORY / "outputs.jsonl",
                ],
            ),
            completed_at_utc=utc_now().isoformat(),
        )
        publish(directory / "generation_receipt.json", receipt)
    return receipt


def measure(root):
    freeze, _ = load(root)
    directory = root / DIRECTORY
    verify_bindings(root, read_json(directory / "generation_receipt.json")["inputs"])
    outputs = read_jsonl(directory / "outputs.jsonl")
    with stage_lock(root / generation.WORKSPACE / RUN / ".measurement.lock"):
        ledger = directory / "measurement_events.jsonl"
        if ledger.exists():
            raise FileExistsError("retry measurement is one-shot")
        append_event(
            ledger,
            dict(
                kind="start",
                inputs=bindings(
                    root, [DIRECTORY / "generation_receipt.json", DIRECTORY / "outputs.jsonl"]
                ),
            ),
        )
        rows = []
        for request, output in zip(freeze["requests"], outputs, strict=True):
            row = measurement._measure(root, RUN, request, output, generation.MAX_RESPONSE_BYTES)
            measurement._validate_row(row, request, output, RUN)
            append_event(ledger, dict(kind="terminal", row=row))
            rows.append(row)
        publish(directory / "measured_features.jsonl", rows, lines=True)
        receipt = dict(
            run_id=RUN,
            terminal=True,
            statuses=dict(Counter(r["status"] for r in rows)),
            inputs=bindings(
                root,
                [
                    DIRECTORY / name
                    for name in (
                        "generation_receipt.json",
                        "outputs.jsonl",
                        "measurement_events.jsonl",
                        "measured_features.jsonl",
                    )
                ],
            ),
            completed_at_utc=utc_now().isoformat(),
        )
        publish(directory / "measurement_receipt.json", receipt)
    return receipt


def combine(original, retries):
    """Make a derived view; preserve original records and identify every replacement."""
    if len(original) != 1920 or len(retries) != 2:
        raise ValueError("expected 1920 original dispositions and exactly two retry dispositions")
    result = copy.deepcopy(original)
    for index, row in zip(SEQUENCES, retries, strict=True):
        old = result[index]
        if (
            old["status"] != "not_generated"
            or row["request_id"] != old["request_id"]
            or row["request_sequence"] != index
            or row["run_id"] != RUN
        ):
            raise ValueError("retry cannot replace an observed image or another slot")
        if row["status"] == "measured":
            result[index] = dict(
                row,
                replaces_source_run_id=SOURCE,
                original_disposition_sha256=digest(old),
                retried=True,
            )
    return result


def describe(real, rows, scaler):
    """Finite distances only: later retry images have no randomized original-slot assignment."""
    distances, availability = [], []
    for alias in generation.ALIASES:
        for method in METHOD_IDS:
            for condition in CONDITIONS:
                selected = [
                    r
                    for r in rows
                    if (r["alias"], r["method_id"], r["condition"]) == (alias, method, condition)
                    and r["status"] == "measured"
                ]
                counts = Counter(r["template_id"] for r in selected)
                if set(counts) != set(TEMPLATE_IDS):
                    raise ValueError("all 16 scenes must remain represented")
                array = statistics.transform(np.array([r["values"] for r in selected]), scaler)
                weights = np.array([1 / (16 * counts[r["template_id"]]) for r in selected])
                availability.append(
                    dict(
                        alias=alias,
                        method_id=method,
                        condition=condition,
                        planned=64,
                        measured=len(selected),
                    )
                )
                for painter in PAINTER_IDS:
                    for family, section in features.FAMILIES.items():
                        distances.append(
                            dict(
                                alias=alias,
                                method_id=method,
                                condition=condition,
                                painter_id=painter,
                                family=family,
                                generated_count=len(selected),
                                reference_count=len(real[painter]),
                                distance=weighted_energy(
                                    real[painter][:, section], array[:, section], weights
                                ),
                            )
                        )
    lookup = {
        (r["alias"], r["method_id"], r["condition"], r["painter_id"], r["family"]): r["distance"]
        for r in distances
    }
    absolute = [
        dict(r, finite_distance=r["distance"])
        for r in distances
        if r["condition"] == r["painter_id"]
    ]
    contrasts, controls = [], []
    for alias in generation.ALIASES:
        for painter in PAINTER_IDS:
            for family in features.FAMILIES:
                for before, after in analysis.TRANSITIONS:
                    first, second = [
                        lookup[alias, m, painter, painter, family] for m in (before, after)
                    ]
                    contrasts.append(
                        dict(
                            alias=alias,
                            painter_id=painter,
                            family=family,
                            before=before,
                            after=after,
                            before_distance=first,
                            after_distance=second,
                            estimate=second - first,
                        )
                    )
                for method in METHOD_IDS:
                    controls.append(
                        dict(
                            alias=alias,
                            painter_id=painter,
                            family=family,
                            method_id=method,
                            target_minus_artist_free=lookup[alias, method, painter, painter, family]
                            - lookup[alias, method, "artist_free", painter, family],
                        )
                    )
    return dict(
        distances=distances,
        absolute=absolute,
        contrasts=contrasts,
        control_comparisons=controls,
        availability=availability,
    )


def result(root):
    freeze, original_dir = load(root)
    receipt = read_json(root / DIRECTORY / "measurement_receipt.json")
    verify_bindings(root, receipt["inputs"])
    original = read_jsonl(original_dir / "measured_features.jsonl")
    retries = read_jsonl(root / DIRECTORY / "measured_features.jsonl")
    combined = combine(original, retries)
    real, _, _, scaler, _, reference = load_source(root, freeze["source_method_id"])
    computed = describe(real, combined, scaler)
    previous = read_json(root / SUPPLEMENT / "analysis.json")
    old = {
        (r["alias"], r["method_id"], r["condition"], r["painter_id"], r["family"]): r["distance"]
        for r in previous["distances"]
    }
    computed["changes"] = [
        dict(r, previous_distance=old[key], change=r["distance"] - old[key])
        for r in computed["distances"]
        if abs(
            r["distance"]
            - old[key := (r["alias"], r["method_id"], r["condition"], r["painter_id"], r["family"])]
        )
        > 1e-12
    ]
    return dict(
        run_id=RUN,
        source_run_id=SOURCE,
        measured=sum(r["status"] == "measured" for r in combined),
        retried_measured=sum(r["status"] == "measured" for r in retries),
        reference_counts={p: len(x) for p, x in real.items()},
        scaler_development_counts=reference["scaler_development_counts"],
        original_primary_status="unavailable_incomplete_grid",
        inference="post-hoc descriptive completion; no new p-values, CIs or confirmatory claim",
        weighting="each scene has mass 1/16; uniform within successful scene outputs",
        retries=[
            dict(sequence=r["request_sequence"], condition=r["condition"], status=r["status"])
            for r in retries
        ],
        **computed,
    )


def render(data, target):
    target.mkdir(parents=True, exist_ok=False)
    (target / "plots").mkdir()
    for table in TABLES:
        (target / f"{table}.csv").write_text(_csv(data[table]), encoding="utf-8")
    text = [
        "# Main distance results after two authorized retry attempts\n",
        f"**{data['measured']:,} measured images** in the derived 1,920-slot grid; "
        f"{data['retried_measured']} newly measured retry images. Exactly two additional "
        "requests were authorized, one for each original refusal. "
        "Original records remain unchanged.\n",
        "These are **post-hoc descriptive results**. The original complete-grid primary remains "
        "unavailable: the later retry images were not generated in their original randomized "
        "request positions. No new randomization p-values or confidence intervals are asserted.\n",
        "The comparison retains the same 649 painting surrogates, 221-work development scaler, "
        "31 color/spatial/digital-texture features and 512-short-side normalization. Every scene "
        "has weight 1/16; with all four outputs present each image has weight 1/64. Smaller "
        "V-energy means closer finite feature distributions within the same feature family. "
        "Family magnitudes are not comparable to each other.\n",
        "![Target distances](plots/target_distances.png)\n",
    ]
    lookup = {
        (r["alias"], r["method_id"], r["painter_id"], r["family"]): r["distance"]
        for r in data["absolute"]
    }
    for alias in generation.ALIASES:
        text += [
            f"## {alias}\n",
            _table(
                ["Painter", "Family", "By name", "Style instruction", "Style + aspects"],
                [
                    [SHORT_LABELS[p], f, *[f"{lookup[alias, m, p, f]:.6f}" for m in METHOD_IDS]]
                    for p in PAINTER_IDS
                    for f in features.FAMILIES
                ],
            ),
        ]
    named = [r for r in data["contrasts"] if r["before"] == "by_name"]
    aspects = [r for r in data["contrasts"] if r["before"] == "style_instruction"]
    text += [
        "## Observed comparisons\n",
        f"By-name prompting has smaller distance than explicit style instruction in "
        f"**{sum(r['estimate'] > 0 for r in named)}/24 comparisons**. Adding aspects "
        f"decreases distance in {sum(r['estimate'] < 0 for r in aspects)}/24 comparisons. "
        "These directions are descriptions, not claims of statistical significance.\n",
        "Requested aliases do not attest model snapshots. Returned size/quality differences, "
        "scene content, digital capture and service drift can affect distances. The 649 "
        "references are exposed digital surrogates, not a probability sample of entire oeuvres. "
        "This report does not rank aesthetic quality or establish reproduction/equivalence.\n",
        "All earlier exploratory tests and their assumptions remain in the separate "
        "[pre-retry supplement](../../painter_prompt_supplement_v1/"
        "ppss1-missingness-20260905/REPORT.md). "
        "Its tests are not reassigned to this completed grid.\n",
        "## Reproduction and exports\n",
        *[f"- [{name}]({name}.csv)" for name in TABLES],
        "\nFull precision is retained in CSV and analysis JSON. Changes include every altered "
        "distance cell relative to the earlier equal-scene-weighted supplement.\n",
        "```bash\nuv run --locked --extra analysis --extra learned python -m "
        "latent_art_bench.painter_prompt_retry_v1 check\n```\n",
    ]
    (target / "REPORT.md").write_text("\n".join(text), encoding="utf-8")
    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharex="col", layout="constrained")
        for i, alias in enumerate(generation.ALIASES):
            for j, family in enumerate(features.FAMILIES):
                ax = axes[i, j]
                for k, method in enumerate(METHOD_IDS):
                    ax.scatter(
                        [lookup[alias, method, p, family] for p in PAINTER_IDS],
                        np.arange(4) + (k - 1) * 0.22,
                        c=COLORS[k],
                        label=METHOD_LABELS[method],
                        s=34,
                    )
                ax.set(title=f"{alias} · {family}", xlabel="Finite feature distance")
                ax.set_yticks(range(4), [SHORT_LABELS[p] for p in PAINTER_IDS])
                ax.set_ylim(3.5, -0.5)
                ax.set_xlim(left=0)
                ax.grid(axis="x", alpha=0.2)
        fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="outside lower center", ncols=3)
        fig.suptitle(
            "Generated images versus original-painting reference\n"
            "Later retry completion; descriptive distances, no confidence intervals"
        )
        _save(fig, target, "target_distances")


def report(root):
    data = result(root)
    directory = root / DIRECTORY
    if (directory / "analysis.json").exists() or (root / REPORT).exists():
        raise FileExistsError("retry report is terminal; use check")
    render(data, root / REPORT)
    publish(directory / "analysis.json", data)
    paths = [p.relative_to(root) for p in (root / REPORT).rglob("*") if p.is_file()]
    paths += [DIRECTORY / "analysis.json", DIRECTORY / "measurement_receipt.json"]
    publish(directory / "report_receipt.json", dict(inputs=bindings(root, paths)))
    return dict(status="reported", measured=data["measured"], report=str(REPORT / "REPORT.md"))


def check(root):
    freeze, _ = load(root)
    directory = root / DIRECTORY
    for name in ("generation", "measurement", "report"):
        verify_bindings(root, read_json(directory / f"{name}_receipt.json")["inputs"])
    ledger = events(directory / "generation_events.jsonl")
    attempts = [r for r in ledger if r["kind"] == "attempt"]
    outputs = read_jsonl(directory / "outputs.jsonl")
    if (
        [r["row"] for r in ledger if r["kind"] == "terminal"] != outputs
        or len(outputs) != 2
        or len(attempts) > 2
        or len({r["request_id"] for r in attempts}) != len(attempts)
    ):
        raise ValueError("retry request accounting changed")
    expected = {r["request_id"]: digest(r) for r in freeze["requests"]}
    if any(expected.get(r["request_id"]) != r["request_sha256"] for r in attempts):
        raise ValueError("retry intent differs from exact payload")
    generation._verify_retained(root, RUN, {r["request_id"]: r for r in outputs})
    measured = read_jsonl(directory / "measured_features.jsonl")
    if [
        r["row"] for r in events(directory / "measurement_events.jsonl") if r["kind"] == "terminal"
    ] != measured:
        raise ValueError("measurement event chain disagrees")
    for request, output, row in zip(freeze["requests"], outputs, measured, strict=True):
        measurement._validate_row(row, request, output, RUN)
    data = result(root)
    if read_json(directory / "analysis.json") != data:
        raise ValueError("numeric reproduction differs")
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary) / "report"
        render(data, target)
        expected_files = {p.relative_to(target) for p in target.rglob("*") if p.is_file()}
        actual_files = {
            p.relative_to(root / REPORT) for p in (root / REPORT).rglob("*") if p.is_file()
        }
        if expected_files != actual_files or any(
            (target / p).read_bytes() != (root / REPORT / p).read_bytes() for p in expected_files
        ):
            raise ValueError("report reproduction differs")
    return dict(
        status="PASS",
        attempted=len(attempts),
        measured=data["measured"],
        original_primary_status=data["original_primary_status"],
        report_files=len(expected_files),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "execute", "measure", "report", "check"))
    parser.add_argument("--proxy-root", type=Path)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    value = (
        execute(root, args.proxy_root)
        if args.command == "execute"
        else globals()[args.command](root)
    )
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
