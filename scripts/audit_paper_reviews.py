"""Audit the portable editorial review archive without services or local snapshots.

Run from any directory with Python 3.9+. --local-snapshots additionally checks
available frozen manuscript bytes and ignored execution artifacts. Missing local
artifacts are reported, never represented as verified. No records are changed.
"""

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from uuid import UUID

RUBRIC_SHA = "e3c0d44034123bc097ed3a4823c3977e2b7bd13207460aba41bd1e805a3812f3"
DIMENSIONS = {"expression", "structure", "new_reader_understanding", "engagement"}
PAGES = list(range(1, 23))
RECORD_PATH = Path("reports/paper_editorial_review_v1")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def decode(text):
    return json.loads(text, object_pairs_hook=unique_keys)


def read(path):
    return decode(path.read_text(encoding="utf-8"))


def checked_relative(value):
    path = Path(value)
    require(not path.is_absolute() and ".." not in path.parts, f"Unsafe path: {value}")
    return path


def scores(review, pdf_sha):
    require(review["rubric_version"] == 1, "Unexpected rubric version")
    require(review["manuscript_pdf_sha256"] == pdf_sha, "Review PDF binding differs")
    scope = review["read_scope"]
    require(scope["full_manuscript"] is True, "Full reading not reported")
    require(scope["pdf_pages_inspected"] == PAGES, "Expected reported pages 1–22")
    values = review["scores"]
    require(set(values) == DIMENSIONS, "Unexpected score dimensions")
    require(all(type(v) in (int, float) and math.isfinite(v) and 1 <= v <= 10
                and float(v * 4).is_integer() for v in values.values()),
            "Invalid quarter-point score")
    overall = sum(values.values()) / 4
    require(overall == review["overall"], "Overall arithmetic differs")
    return overall


def normalize(raw):
    """Replay only the aliases/representation changes documented in the archive."""
    value = json.loads(json.dumps(raw))
    aliases = [(value, "manuscript_sha256", "manuscript_pdf_sha256"),
               (value["read_scope"], "pages_read", "pdf_pages_inspected")]
    aliases.extend((value[key], "new_reader_accessibility", "new_reader_understanding")
                   for key in ("scores", "score_reasons"))
    for obj, old, new in aliases:
        if old in obj:
            require(new not in obj, f"Ambiguous alias: {old}")
            obj[new] = obj.pop(old)
    if value["rubric_version"] == "1":
        value["rubric_version"] = 1
    return value


def extract_response(folder):
    """Reproduce the documented JSON extraction, never correct review content."""
    text = (folder / "response.txt").read_text(encoding="utf-8")
    encoded = text[text.index("{"):]
    try:
        return decode(encoded)
    except json.JSONDecodeError:
        # These two raw Claude answers omit the same score_reasons closing brace.
        # Preserve response.txt; this is exactly the previously documented repair.
        require(folder.name in {"claude_code_review_03", "claude_code_review_04"},
                f"Undocumented JSON repair needed: {folder.name}")
        pattern = r',\s*"strengths"\s*:'
        require(len(re.findall(pattern, encoded)) == 1, "Ambiguous delimiter repair")
        return decode(re.sub(pattern, lambda match: "}" + match.group(), encoded, count=1))


def snapshot(path):
    value = read(path)
    require(re.fullmatch(r"[0-9a-f]{64}", value["pdf_sha256"]), f"Invalid hash: {path}")
    require(value.get("rubric_sha256", RUBRIC_SHA) == RUBRIC_SHA, "Snapshot rubric differs")
    files = value["files"]
    require(files["paper.pdf"] == value["pdf_sha256"], "Snapshot PDF map differs")
    for name, sha in files.items():
        checked_relative(name)
        require(re.fullmatch(r"[0-9a-f]{64}", sha), f"Invalid file hash: {path}/{name}")
    return value


def check_rounds(records):
    folders = sorted(records.glob("round_*"))
    require([p.name for p in folders] == [f"round_{n:02d}" for n in range(1, 34)],
            "Expected exactly the 33 original rounds")
    seen, summaries, snapshots = set(), [], []
    for number, folder in enumerate(folders, 1):
        snap = snapshot(folder / "snapshot.json")
        snapshots.append(snap)
        aggregate = read(folder / "aggregate.json")
        require(snap["round"] == aggregate["round"] == number, "Round number differs")
        require(aggregate["pdf_sha256"] == snap["pdf_sha256"], "Aggregate PDF differs")
        require(aggregate["rubric_sha256"] == RUBRIC_SHA, "Aggregate rubric differs")
        require(len(aggregate["reviewers"]) == 3, "Round does not contain three reviewers")
        for suffix, row in zip("abc", aggregate["reviewers"]):
            path = folder / f"reviewer_{suffix}.json"
            review = read(path)
            require(digest(path) == row["review_sha256"], f"Raw review changed: {path}")
            reviewer_id = review["reviewer_id"]
            require(reviewer_id == row["reviewer_id"] and reviewer_id not in seen,
                    f"Duplicate or inconsistent reviewer ID: {reviewer_id}")
            seen.add(reviewer_id)
            require(scores(review, snap["pdf_sha256"]) == row["overall"], "Row score differs")
            require(review["scores"] == row["scores"], "Row dimensions differ")
        mean = sum(row["overall"] for row in aggregate["reviewers"]) / 3
        require(mean == aggregate["mean"], "Round mean differs")
        require(aggregate["required_strictly_above"] == 9.25, "Threshold changed")
        require(aggregate["meets_user_threshold"] == (mean > 9.25), "Threshold result differs")
        require(set(aggregate["dimension_means"]) == DIMENSIONS, "Mean dimensions differ")
        for key, value in aggregate["dimension_means"].items():
            require(value == sum(row["scores"][key] for row in aggregate["reviewers"]) / 3,
                    "Dimension mean differs")
        if (folder / "VALIDATION.json").exists():
            validation = read(folder / "VALIDATION.json")
            require(validation["pdf_sha256"] == snap["pdf_sha256"], "Validation PDF differs")
            require(validation["evaluated_round"] == number, "Validation round differs")
        require((folder / ("DECISION.md" if number == 33 else "REVISION.md")).is_file(),
                f"Missing revision decision: {folder}")
        summaries.append({"round": number, "mean": mean, "verified": True})
    for name in ("FINAL_AUDIT.json", "paired_review_03/HISTORICAL_AUDIT.json"):
        receipt = read(records / name)
        require(receipt["rounds"] == summaries, f"Historical aggregate differs: {name}")
        require(receipt["graded_rounds_checked"] == 33 and receipt["unique_reviewers"] == 99,
                f"Historical counts differ: {name}")
    return seen, snapshots, summaries[-1]["mean"]


def check_external(records, round33, inventory):
    snapshots = {"01": round33}
    for suffix in ("03", "04"):
        snapshots[suffix] = snapshot(records / f"paired_review_{suffix}/INPUT_SNAPSHOT.json")
    sessions, responses, reviews = set(), set(), {}
    for suffix in ("01", "03", "04"):
        snap = snapshots[suffix]
        render_maps = []
        for provider in ("claude_code", "astra_xhigh"):
            folder = records / f"{provider}_review_{suffix}"
            raw = read(folder / "reviewer.json")
            require(extract_response(folder) == raw, f"Raw response extraction differs: {folder}")
            review = normalize(raw)
            if (folder / "normalized_review.json").exists():
                require(read(folder / "normalized_review.json") == review,
                        f"Normalization changes content: {folder}")
            require(review["reviewer_id"] == folder.name, "External reviewer ID differs")
            overall = scores(review, snap["pdf_sha256"])
            prov, validation = read(folder / "PROVENANCE.json"), read(folder / "VALIDATION.json")
            binding = prov.get("inputs", prov)
            for key, expected in (("pdf_sha256", snap["pdf_sha256"]),
                                  ("rubric_sha256", RUBRIC_SHA)):
                require(binding[key] == validation[key] == expected, f"Binding differs: {folder}")
                if key in prov:
                    require(prov[key] == expected, f"Provenance binding differs: {folder}")
            if "paper_files" in prov:
                require(prov["paper_files"] == snap["files"], "Provenance source map differs")
            if "page_png_sha256" in prov:
                renders = prov["page_png_sha256"]
                require(sorted(renders) == [f"page-{n:02d}.png" for n in PAGES],
                        "Unexpected render page names")
                require(all(re.fullmatch(r"[0-9a-f]{64}", sha) for sha in renders.values()),
                        "Invalid page image digest")
                render_maps.append(renders)
            require(prov["prior_scores_and_threshold_disclosed"] is False,
                    "Prior scores were disclosed")
            require(prov["manuscript_mutation_authorized"] is False, "Review allowed edits")
            require(validation["overall_arithmetic_verified"] == overall, "Receipt score differs")
            if "review_sha256" in prov:
                require(digest(folder / "reviewer.json") == prov["review_sha256"],
                        "Provenance review digest differs")
            if "raw_response_sha256" in validation:
                require(digest(folder / "response.txt") == validation["raw_response_sha256"],
                        "Raw response digest differs")
            if provider == "claude_code":
                require(prov["model_reported"] == "claude-opus-5", "Claude model differs")
                require(validation["cli_transport_succeeded"] is True, "Claude did not complete")
                require(validation["successful_visual_page_reads_verified_in_cli_trace"] == PAGES,
                        "Claude page-read receipt differs")
                stream_path = RECORD_PATH / folder.name / "claude_stream.jsonl"
                require(validation["stream_sha256"] == inventory[str(stream_path)]["sha256"],
                        "Claude trace digest binding differs")
                if "final_response_sha256" in prov:
                    raw_text = (folder / "response.txt").read_bytes()
                    require(hashlib.sha256(raw_text[:-1]).hexdigest()
                            == prov["final_response_sha256"], "Claude response digest differs")
                session = prov.get("session_id_requested", prov.get("cli_reported_session_id"))
                UUID(session)
                require(session not in sessions, "Claude session ID reused")
                sessions.add(session)
                if suffix != "01":
                    require(session == validation["fresh_session_id"]
                            == prov["session_id_reported"] and prov["session_resume"] is False,
                            "Claude fresh-session binding differs")
            else:
                status = read(folder / "RUN_STATUS.json")
                require(status["status"] == "completed", "Astra did not complete")
                require(status["reported_model"] == status["requested_model"]
                        == prov["model_reported"] == "gpt-6-astra", "Astra model differs")
                require(status["reported_reasoning"]["effort"]
                        == status["requested_reasoning"]["effort"]
                        == prov["requested_reasoning_effort"] == "xhigh", "Astra effort differs")
                require(status["response_id"] not in responses, "Astra response ID reused")
                responses.add(status["response_id"])
                require(validation["upstream_completion_verified"] is True, "Completion missing")
                require(validation["reported_pages_inspected"] == PAGES, "Astra pages differ")
                work = Path("tmp/paper") / (
                    "astra-xhigh-review-01" if suffix == "01" else f"paired-review-{suffix}"
                )
                request = inventory[str(work / "request.json")]
                require(status["request_sha256"] == request["sha256"]
                        and status["request_bytes"] == request["bytes"], "Request binding differs")
                for source in (prov, validation):
                    for key in ("stream_sha256", "response_events_sha256"):
                        if key in source:
                            require(source[key]
                                    == inventory[str(work / "response_events.jsonl")]["sha256"],
                                    "Astra stream digest binding differs")
                if "request_sha256" in validation:
                    require(validation["request_sha256"] == status["request_sha256"],
                            "Request validation digest differs")
                text = (folder / "response.txt").read_bytes()
                require(text.endswith(b"\n"), "Missing response storage newline")
                require(hashlib.sha256(text[:-1]).hexdigest() == status["output_text_sha256"],
                        "Astra output-text digest differs")
                if suffix != "01":
                    require(prov["previous_response_id"] is None
                            and prov["responses_state"] is False,
                            "Astra conversational state was enabled")
                    require(status["response_id"] == prov["response_id"]
                            == validation["response_id"], "Response ID bindings differ")
                else:
                    require(prov["collector_recovered_text_sha256"] == status["output_text_sha256"],
                            "Recovered text digest differs")
                    for key, name in (("original_runner_sha256", "run_review.original.ts"),
                                      ("corrected_runner_sha256", "run_review.ts")):
                        runner = inventory[str(RECORD_PATH / folder.name / name)]
                        require(prov[key] == runner["sha256"],
                                "Recorded runner digest differs")
            reviews[folder.name] = {"scores": review["scores"], "overall": overall}
        if len(render_maps) == 2:
            require(render_maps[0] == render_maps[1], "Paired rendered images differ")
    cancelled = read(records / "paired_review_02/CANCELLED.json")
    for provider in ("claude_code", "astra_xhigh"):
        folder = records / f"{provider}_review_02"
        require(read(folder / "CANCELLED.json") == cancelled, "Cancellation records disagree")
        require(not (folder / "reviewer.json").exists(), "Cancelled request counted as scored")
    cancelled_prov = read(records / "claude_code_review_02/PROVENANCE.json")
    cancelled_session = cancelled_prov["session_id_requested"]
    require(cancelled_session not in sessions, "Cancelled Claude session reused")
    final = snapshot(records / "paired_review_03/FINAL_SNAPSHOT.json")
    require(final["evaluated_pdf_sha256"] == snapshots["03"]["pdf_sha256"],
            "Second revision lost its evaluated parent")
    require(final["files"] == snapshots["04"]["files"], "Review 04 did not assess second revision")
    pair = read(records / "paired_review_04/VALIDATION.json")
    require(pair["pdf_sha256"] == snapshots["04"]["pdf_sha256"]
            and pair["rubric_sha256"] == RUBRIC_SHA, "Paired aggregate binding differs")
    for key, provider in (("claude", "claude_code"), ("astra", "astra_xhigh")):
        require(pair[key] == reviews[f"{provider}_review_04"], "Paired component differs")
    require(pair["mean_overall"] == (pair["claude"]["overall"] + pair["astra"]["overall"]) / 2,
            "Paired mean differs")
    return reviews, list(snapshots.values())[1:] + [final]


def local_path(root, original):
    """Relocate historical absolute checkout paths without editing old records."""
    path = Path(original)
    if "tmp" in path.parts:
        return root.joinpath(*path.parts[path.parts.index("tmp"):])
    return path if path.is_absolute() else root / checked_relative(original)


def check_local(root, snapshots, inventory):
    verified, missing = [], []
    for snap in snapshots:
        folder = local_path(root, snap["snapshot"])
        if not folder.exists():
            missing.append(str(folder))
            continue
        for name, expected in snap["files"].items():
            require(digest(folder / name) == expected, f"Frozen input changed: {folder / name}")
        verified.append(str(folder))
    artifacts, absent = 0, []
    for name, receipt in inventory.items():
        path = root / checked_relative(name)
        if path.is_file():
            require(path.stat().st_size == receipt["bytes"] and digest(path) == receipt["sha256"],
                    f"Local execution artifact changed: {name}")
            artifacts += 1
        else:
            absent.append(name)
    return {"snapshots_verified": len(verified), "missing_snapshots": missing,
            "execution_artifacts_verified": artifacts, "missing_execution_artifacts": absent}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--local-snapshots", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    records = root / RECORD_PATH
    require(digest(records / "RUBRIC.md") == RUBRIC_SHA, "Fixed rubric changed")
    manifest_text = (records / "ARCHIVE.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)\n```", manifest_text, re.DOTALL)
    require(len(blocks) == 1, "Expected one archive digest inventory")
    inventory = decode(blocks[0])
    for name, receipt in inventory["portable_external_records"].items():
        path = root / checked_relative(name)
        require(path.stat().st_size == receipt["bytes"] and digest(path) == receipt["sha256"],
                f"Archived external record changed: {name}")
    reviewers, snapshots, last_mean = check_rounds(records)
    external, extra_snapshots = check_external(records, snapshots[-1],
                                              inventory["local_execution_artifacts"])
    require(not reviewers.intersection(external), "Internal and external reviewer IDs overlap")
    result = {"portable_audit": "passed", "original_rounds": len(snapshots),
              "original_unique_reviewers": len(reviewers), "round_33_mean": last_mean,
              "completed_external_reviews": external, "cancelled_external_requests": 2,
              "rubric_sha256": RUBRIC_SHA,
              "portable_external_files_hashed": len(inventory["portable_external_records"]),
              "local_bytes_checked": args.local_snapshots,
              "scope": "Record integrity and arithmetic; no new review or validity assessment. "
                       "Historical scores are not assigned to later canonical edits."}
    if args.local_snapshots:
        result["local"] = check_local(root, snapshots + extra_snapshots,
                                      inventory["local_execution_artifacts"])
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, TypeError, ValueError) as error:
        raise SystemExit(f"AUDIT FAILED: {error}") from error
