"""Supplemental read-only diagnosis of the fixed pmv2r numerical archive.

Run outside the extracted archive: --root <archive> --output <new-output>.
Exit zero means diagnostic completion, including recorded comparison failures;
it never certifies scientific qualification or repairs the closed strict replay.
No network, acquisition, extraction or formal result writer is invoked.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import math
import os
import platform
import sys
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

NAMESPACE = "paper_map_portability_diagnostic_v1"
RUN_ID = "pmpdv1-20260910"
RELEASE_ID = "pmv2r-20260910"
TOOL = "tools/paper_map_validation_release.py"
MANIFEST = "MAP_VALIDATION_RELEASE_MANIFEST.json"
PINS = {
    TOOL: "a97ee3fa87a219949c5695f5949cdda9704e8124ba9ebae6649d97fb21779015",
    MANIFEST: "186f1efd018420a2cbad1c2cd8e9ba0e9ebf7792703ea88373adfd3e93357d84",
    "SHA256SUMS": "4d0a102c0c70c555431483375b6c64a77d2f18b6825adf104b80287259fb0f26",
}
TOLERANCE = 1e-10  # Unchanged frozen helper contract, checked at runtime.


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def tagged(value):
    """Retain exceptional arithmetic explicitly without emitting invalid JSON."""
    if type(value) is float and not math.isfinite(value):
        return {"__diagnostic_nonfinite_float__": repr(value)}
    if isinstance(value, dict):
        return {k: tagged(v) for k, v in value.items()}
    if isinstance(value, list):
        return [tagged(v) for v in value]
    return value


def encoded(value):
    return (json.dumps(tagged(value), indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def compare_leaves(actual, expected):
    """All structural/leaf differences, preserving base.compare's type asymmetry.

    Missing/extra subtrees are retained whole; every shared leaf is visited.
    Exact comparison additionally distinguishes float encodings, including -0.0.
    Numeric deviations are descriptive, never an alternative tolerance gate.
    """
    differences = []

    def visit(a, e, pointer):
        def record(kind, equal=False, **extra):
            differences.append(dict(pointer=pointer, kind=kind, comparator_equal=equal, **extra))

        def child(key):
            return pointer + "/" + str(key).replace("~", "~0").replace("/", "~1")

        if isinstance(e, dict) and isinstance(a, dict):
            for key in sorted(a.keys() - e.keys()):
                differences.append(
                    dict(
                        pointer=child(key),
                        kind="extra",
                        actual=tagged(a[key]),
                        comparator_equal=False,
                    )
                )
            for key in sorted(e.keys() - a.keys()):
                differences.append(
                    dict(
                        pointer=child(key),
                        kind="missing",
                        expected=tagged(e[key]),
                        comparator_equal=False,
                    )
                )
            for key in sorted(a.keys() & e.keys()):
                visit(a[key], e[key], child(key))
            return
        if isinstance(e, list) and isinstance(a, list):
            for i in range(max(len(a), len(e))):
                if i >= len(e):
                    differences.append(
                        dict(
                            pointer=child(i),
                            kind="extra",
                            actual=tagged(a[i]),
                            comparator_equal=False,
                        )
                    )
                elif i >= len(a):
                    differences.append(
                        dict(
                            pointer=child(i),
                            kind="missing",
                            expected=tagged(e[i]),
                            comparator_equal=False,
                        )
                    )
                else:
                    visit(a[i], e[i], child(i))
            return
        floating = type(e) is float and type(a) in (float, int)
        equal = (
            (
                math.isfinite(a)
                and math.isfinite(e)
                and math.isclose(a, e, rel_tol=TOLERANCE, abs_tol=TOLERANCE)
            )
            if floating
            else type(a) is type(e) and a == e
        )
        exact = type(a) is type(e) and a == e
        if type(a) is float and type(e) is float:
            exact = exact and a.hex() == e.hex()
        if exact and equal:
            return
        detail = dict(
            actual=tagged(a),
            expected=tagged(e),
            actual_type=type(a).__name__,
            expected_type=type(e).__name__,
        )
        numeric = type(a) in (float, int) and type(e) in (float, int)
        if numeric and math.isfinite(a) and math.isfinite(e):
            delta = a - e
            scale = max(abs(a), abs(e))
            detail.update(
                signed_difference=tagged(delta),
                absolute_difference=tagged(abs(delta)),
                relative_difference=tagged(abs(delta) / scale if scale else 0.0),
                frozen_float_tolerance_applies=floating,
                tolerance_limit=tagged(max(TOLERANCE, TOLERANCE * scale)) if floating else None,
            )
        for label, value in (("actual", a), ("expected", e)):
            if type(value) is float:
                detail[label + "_hex"] = value.hex()
        record("numeric" if numeric else "type_or_value", equal, **detail)

    visit(actual, expected, "")
    return dict(
        comparator_equal=all(d["comparator_equal"] for d in differences),
        exact_equal=not differences,
        mismatch_count=sum(not d["comparator_equal"] for d in differences),
        tolerated_exact_difference_count=sum(d["comparator_equal"] for d in differences),
        differences=differences,
    )


def no_symlinks(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("symlink path prohibited")


def load_release(root):
    """Pin executable bytes before import; full inventory verification follows."""
    for relative, sha in PINS.items():
        path = root / relative
        no_symlinks(path)
        if digest(path.read_bytes()) != sha:
            raise ValueError("published executable or manifest fingerprint differs")
    spec = importlib.util.spec_from_file_location("_diagnostic_frozen_release", root / TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.base.TOLERANCE != TOLERANCE:
        raise ValueError("frozen numerical tolerance differs")
    return module


def inventory(root, release):
    result = release.verify(root, runtime=True)
    if result["files"] != 74:
        raise ValueError("exact 74-file inventory required")
    for relative, sha in PINS.items():
        if digest(release.base.file_bytes(root, relative)) != sha:
            raise ValueError("published executable or manifest changed")
    manifest = release.read(root, MANIFEST)
    return {
        **manifest["files"],
        MANIFEST: PINS[MANIFEST],
        "SHA256SUMS": PINS["SHA256SUMS"],
    }


def module_bindings(root, release, files):
    release.base.require_local_modules(root)
    modules = {
        n: m
        for n, m in sys.modules.items()
        if n == "latent_art_bench" or n.startswith("latent_art_bench.")
    }
    modules.update(frozen_release=release, frozen_helper=release.base)
    result = {}
    for name, module in sorted(modules.items()):
        path = Path(module.__file__).resolve()
        relative = path.relative_to(root).as_posix()
        sha = digest(path.read_bytes())
        if files.get(relative) != sha:
            raise ValueError("loaded scientific module is not a bound archive body")
        result[name] = dict(path=relative, sha256=sha)
    return result


def runtime_summary():
    import numpy as np
    import scipy

    config = np.show_config(mode="dicts")
    dependencies = config.get("Build Dependencies", {})
    fields = ("name", "version", "found", "detection method", "openblas configuration")
    return dict(
        python=platform.python_version(),
        implementation=platform.python_implementation(),
        system=platform.system(),
        release=platform.release(),
        machine=platform.machine(),
        byteorder=sys.byteorder,
        numpy=np.__version__,
        scipy=scipy.__version__,
        blas_lapack={
            name: {k: dependencies.get(name, {}).get(k) for k in fields}
            for name in ("blas", "lapack")
        },
        simd=config.get("SIMD Extensions", {}),
        dependency_scope="versions/backend summary; context in bound pyproject.toml/uv.lock",
    )


@contextmanager
def guarded_replay(output):
    """Forbid outbound activity and writes outside the new diagnostic directory."""
    active = True

    def audit(event, args):
        if not active:
            return
        if event.startswith(("socket.", "subprocess.")) or event in {
            "os.system",
            "os.posix_spawn",
            "os.exec",
            "os.fork",
            "os.forkpty",
        }:
            raise PermissionError("network/subprocess prohibited in numerical diagnostic")
        if event == "open":
            path, mode, flags = args
            writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT)
            )
            if writing and (
                not isinstance(path, (str, bytes, os.PathLike))
                or not Path(os.fsdecode(path)).resolve().is_relative_to(output)
            ):
                raise PermissionError("write outside diagnostic output prohibited")
        if event in {
            "os.remove",
            "os.rmdir",
            "os.rename",
            "os.link",
            "os.symlink",
            "os.chmod",
            "os.utime",
            "os.truncate",
        }:
            raise PermissionError("filesystem mutation prohibited in numerical diagnostic")
        if event == "os.mkdir" and not Path(args[0]).resolve().is_relative_to(output):
            raise PermissionError("directory outside diagnostic output prohibited")

    sys.addaudithook(audit)
    try:
        yield
    finally:
        active = False


def diagnose(root, output):
    root, output = Path(root).absolute(), Path(output).absolute()
    no_symlinks(root)
    no_symlinks(output)
    root, output = root.resolve(), output.resolve()
    if root.is_relative_to(output) or output.is_relative_to(root):
        raise ValueError("diagnostic output must be outside and disjoint from archive")
    output.mkdir(parents=True, exist_ok=False)
    script = Path(__file__).resolve()
    script_sha = digest(script.read_bytes())
    receipt = dict(
        schema="paper-map-portability-diagnostic/1",
        namespace=NAMESPACE,
        run_id=RUN_ID,
        archive=RELEASE_ID,
        script=dict(path="paper_map_portability_diagnostic.py", sha256=script_sha),
        started_at_utc=datetime.now(timezone.utc).isoformat(),
        expected_pins=PINS,
        status="diagnostic_started",
        phases={
            p: dict(status="not_reached")
            for p in ("preverify", "qualification", "observed", "postverify")
        },
        exceptions=[],
        interpreter_flags=dict(
            isolated=bool(sys.flags.isolated),
            bytecode_flag=bool(sys.flags.dont_write_bytecode),
            bytecode_disabled_during_replay=True,
        ),
        command=[
            "python",
            *(["-I"] if sys.flags.isolated else []),
            *(["-B"] if sys.flags.dont_write_bytecode else []),
            "<diagnostic-script>",
            "--root",
            "<archive>",
            "--output",
            "<output>",
        ],
        scope="supplemental diagnosis; no scientific qualification or strict-replay repair",
        private_acquisition_authenticated=False,
    )

    def save(name, raw):
        with (output / name).open("xb") as handle:
            handle.write(raw)

    def failure(stage, exc):
        # Do not serialize exception messages, arbitrary values or absolute paths.
        frames = []
        for frame in traceback.extract_tb(exc.__traceback__):
            path = Path(frame.filename).resolve()
            relative = (
                path.relative_to(root).as_posix()
                if path.is_relative_to(root)
                else ("paper_map_portability_diagnostic.py" if path == script else "<runtime>")
            )
            frames.append(dict(path=relative, line=frame.lineno, function=frame.name))
        receipt["exceptions"].append(dict(stage=stage, type=type(exc).__name__, frames=frames))
        receipt["phases"][stage] = dict(status="exception")

    old_flag = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    save("START.json", encoded(receipt))
    release, before = None, None
    try:
        with guarded_replay(output):
            release = load_release(root)
            before = inventory(root, release)
            receipt["input_bindings"] = before
            receipt["phases"]["preverify"] = dict(status="verified", files=74)
            _, _, precision = release.numerical_modules(root)
            receipt["runtime"] = runtime_summary()
            receipt["modules_before"] = module_bindings(root, release, before)

            def compare(actual, expected, name):
                result = compare_leaves(actual, expected)
                if result["comparator_equal"] != release.base.compare(actual, expected):
                    raise AssertionError("diagnostic and frozen comparator disagree")
                save(name, encoded(result))
                return {k: v for k, v in result.items() if k != "differences"}

            try:
                expected = release.read(root, f"{release.QUALIFICATION}/precision.json")
                actual = precision.qualify(precision.v1.load_proxy(root))  # Exactly one call.
                save("qualification_actual.json", encoded(actual))
                comparison = compare(actual, expected["qualification"], "qualification_diff.json")
                receipt["phases"]["qualification"] = dict(
                    status="compared",
                    **comparison,
                    stored_report_exact=precision.report(expected).encode()
                    == release.base.file_bytes(root, f"{release.QUALIFICATION}/PRECISION.md"),
                )
            except Exception as exc:
                failure("qualification", exc)

            try:
                actual, render = release.observed_replay(
                    root, release.read(root, f"{release.EXPORT}/inputs.json")
                )
                save("observed_actual.json", encoded(actual))
                expected = release.read(root, f"{release.REPORT}/analysis.json")
                comparison = compare(actual, expected, "observed_supplemental_diff.json")
                rendered = render(actual).encode()
                saved_report = release.base.file_bytes(root, f"{release.REPORT}/REPORT.md")
                save("observed_REPORT.md", rendered)
                save(
                    "observed_report.diff",
                    "".join(
                        difflib.unified_diff(
                            saved_report.decode().splitlines(keepends=True),
                            rendered.decode().splitlines(keepends=True),
                            fromfile="published/REPORT.md",
                            tofile="diagnostic/observed_REPORT.md",
                        )
                    ).encode(),
                )
                receipt["phases"]["observed"] = dict(
                    status="compared_independently",
                    exact_json=release.base.encoded(actual) == release.base.encoded(expected),
                    exact_report=rendered == saved_report,
                    supplemental_tolerance=comparison,
                    scope="supplemental comparison cannot satisfy a failed exact observed contract",
                )
            except Exception as exc:
                failure("observed", exc)

    except Exception as exc:
        failure("verification_or_runtime", exc)
    finally:
        if release is not None:
            try:
                with guarded_replay(output):
                    after = inventory(root, release)
                    if (before is not None and after != before) or (
                        digest(script.read_bytes()) != script_sha
                    ):
                        raise ValueError("archive or diagnostic source changed during replay")
                    receipt["modules_after"] = module_bindings(root, release, after)
                    receipt["phases"]["postverify"] = dict(status="verified", files=74)
            except Exception as exc:
                failure("postverify", exc)
        sys.dont_write_bytecode = old_flag
    receipt["status"] = "diagnostic_failed" if receipt["exceptions"] else "diagnostic_complete"
    receipt["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    receipt["outputs"] = {p.name: digest(p.read_bytes()) for p in sorted(output.iterdir())}
    save("RECEIPT.json", encoded(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(args.root, args.output)
    print(json.dumps({"status": result["status"], "phases": result["phases"]}, sort_keys=True))
    return 0 if result["status"] == "diagnostic_complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
