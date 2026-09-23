"""Execute the frozen raw31 method locally and verify artifacts by full replay.

A receipt is a locally generated record, not remote attestation. Verification
recomputes every successful original from hash-checked bytes. This module does
not run a learned encoder, acquire images, fit a scaler or upgrade a study score.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import platform
import sys
import types
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import PIL
import pywt
import scipy
import skimage
from PIL import features as codecs

from . import feature_census as fc
from . import measurement31 as m
from . import protocol as p
from .transport_artifact import ROOT, file_sha

SOURCE = m.METHOD_SOURCES[0]
OUTPUT_FILES = ("inputs.json", "raw31.npz", "execution.json")
IMPLEMENTATION = tuple(
    "src/latent_art_bench/painter_family_controls_v1/" + name + ".py"
    for name in ("execution31", "feature_census", "measurement31", "protocol",
                 "transport_artifact")
) + ("uv.lock", "pyproject.toml")


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def _utc():
    return datetime.now(timezone.utc).isoformat()


def _runtime():
    # Runtime identity is conservative: another runtime needs a separate
    # qualification, rather than silently widening a numerical tolerance.
    return dict(
        python=sys.version, implementation=platform.python_implementation(),
        system=platform.platform(), machine=platform.machine(), byteorder=sys.byteorder,
        executable=str(Path(sys.executable).resolve()),
        executable_sha256=file_sha(Path(sys.executable).resolve()),
        thread_environment={name: os.environ.get(name) for name in (
            "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")},
        packages=dict(numpy=np.__version__, scipy=scipy.__version__, Pillow=PIL.__version__,
                      PyWavelets=pywt.__version__, scikit_image=skimage.__version__),
        image_codecs={name: codecs.version(name)
                      for name in ("jpg", "zlib", "webp", "littlecms2")},
    )


def _bindings(root):
    return {name: file_sha(fc._inside(Path(root).resolve(), name)) for name in IMPLEMENTATION}


@contextmanager
def _frozen_module(root, contract):
    """Compile the verified bytes themselves; never reuse imported method code."""
    path = fc._inside(Path(root).resolve(), SOURCE)
    source = fc._bound_bytes(path, contract["historical_bindings"][SOURCE])
    name = "_family31_frozen_" + uuid.uuid4().hex
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module  # dataclass resolves annotations through this entry
    try:
        exec(compile(source, str(path), "exec"), module.__dict__)
        if list(module.NAMES) != contract["feature_names"]:
            raise ValueError("executed coordinate names differ from the frozen method")
        yield module
    finally:
        del sys.modules[name]


def _compute(census, manifest, root):
    rows = manifest["rows"]
    if not rows:
        raise ValueError("an empty census cannot establish extractor execution")
    values, records = [], []
    with _frozen_module(root, manifest["measurement"]) as method:
        for row in rows:
            pixels = fc._bound_bytes(fc._inside(census.run_dir, row["path"]), row["sha256"])
            # Passing verified bytes prevents a path replacement between hashing
            # and decoding. The retained normalize routine accepts Image.open IO.
            normalized = method.normalize(io.BytesIO(pixels), short_side=512, crop_fraction=0.0)
            raw = np.asarray(method.extract(normalized.rgb), dtype="<f8")
            if raw.shape != (31,) or not np.isfinite(raw).all():
                raise ValueError("extractor did not return a finite complete raw31 row")
            values.append(raw)
            records.append(dict(
                id=row["id"], original_sha256=row["sha256"],
                normalization=normalized.metadata,
                raw_vector_sha256=fc._digest(raw.tobytes(order="C")),
            ))
    return np.stack(values), records


def _manifest(census, root, allow_simulation):
    manifest = m.feature_manifest(census, root=root)  # includes full revalidation
    if manifest["simulation_only"] and allow_simulation is not True:
        raise ValueError("simulation extraction requires explicit fixture-only opt-in")
    return manifest


def _unchanged(census, root, bindings, runtime):
    fc.revalidate_census(census)
    m._historical_contract(root)
    if _bindings(root) != bindings or _runtime() != runtime:
        raise ValueError("extractor source or runtime changed during execution")


def _write_once(path, body):
    with path.open("xb") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())


def execute(census, output, *, allow_simulation=False, root=ROOT):
    """Extract every successful image. Never overwrite, omit or impute a row.

    Output is three create-once files. execution.json is written last and is
    absent if extraction or validation fails. Keep its returned digest outside
    the output directory for later replay; do not trust a self-reported flag.
    """
    output = Path(output).resolve()
    if output.is_relative_to(census.run_dir.resolve()):
        raise ValueError("extraction outputs must be outside the terminal collector")
    if output.exists():
        raise FileExistsError(output)
    manifest = _manifest(census, root, allow_simulation)
    bindings, runtime, started = _bindings(root), _runtime(), _utc()
    output.mkdir(parents=True, exist_ok=False)
    raw, records = _compute(census, manifest, root)
    _unchanged(census, root, bindings, runtime)
    archive = io.BytesIO()
    np.savez_compressed(archive, raw_features=raw,
                        ids=np.array([row["id"] for row in manifest["rows"]]),
                        feature_names=np.array(m.NAMES))
    manifest_bytes, raw_bytes = _json_bytes(manifest), archive.getvalue()
    _write_once(output / "inputs.json", manifest_bytes)
    _write_once(output / "raw31.npz", raw_bytes)
    # Check that the real output also satisfies the existing bound-array loader.
    m.load_feature_census(
        census, output / "inputs.json", output / "raw31.npz",
        expected_manifest_sha256=fc._digest(manifest_bytes),
        expected_raw_sha256=fc._digest(raw_bytes), root=root,
    )
    receipt = dict(
        schema="painter-family-raw31-local-execution/1.0", namespace=p.NAMESPACE,
        status="complete_local_execution_record_requires_replay",
        simulation_only=manifest["simulation_only"],
        terminal_record_hashes=manifest["terminal_record_hashes"],
        manifest_sha256=fc._digest(manifest_bytes), raw_features_sha256=fc._digest(raw_bytes),
        method_contract_sha256=p.canonical_sha(manifest["measurement"]),
        implementation_bindings=bindings, runtime=runtime, rows=records,
        row_count=len(records), started_utc=started, finished_utc=_utc(),
        producer_pid=os.getpid(), replay_comparison="exact_float64_and_normalization_metadata",
        remote_attestation=False, learned_encoders_executed=0,
    )
    _write_once(output / "execution.json", _json_bytes(receipt))
    return file_sha(output / "execution.json")


def replay(census, output, *, expected_receipt_sha256, allow_simulation=False, root=ROOT):
    """Recompute all raw rows; a bound receipt alone never yields replay success."""
    output = Path(output).resolve()
    receipt = fc._json(fc._bound_bytes(output / "execution.json", expected_receipt_sha256))
    manifest = _manifest(census, root, allow_simulation)
    bindings, runtime = _bindings(root), _runtime()
    expected = dict(
        schema="painter-family-raw31-local-execution/1.0", namespace=p.NAMESPACE,
        status="complete_local_execution_record_requires_replay",
        simulation_only=manifest["simulation_only"],
        terminal_record_hashes=manifest["terminal_record_hashes"],
        method_contract_sha256=p.canonical_sha(manifest["measurement"]),
        implementation_bindings=bindings, runtime=runtime, row_count=len(manifest["rows"]),
        replay_comparison="exact_float64_and_normalization_metadata",
        remote_attestation=False, learned_encoders_executed=0,
    )
    variable = {"manifest_sha256", "raw_features_sha256", "rows", "started_utc", "finished_utc",
                "producer_pid"}
    if (set(receipt) != set(expected) | variable
            or p.canonical_sha({key: receipt[key] for key in expected}) != p.canonical_sha(expected)
            or type(receipt["producer_pid"]) is not int or receipt["producer_pid"] <= 0
            or fc._time(receipt["finished_utc"]) < fc._time(receipt["started_utc"])):
        raise ValueError("execution receipt method, runtime, census or schema changed")
    m.load_feature_census(
        census, output / "inputs.json", output / "raw31.npz",
        expected_manifest_sha256=receipt["manifest_sha256"],
        expected_raw_sha256=receipt["raw_features_sha256"], root=root,
    )
    raw_bytes = fc._bound_bytes(output / "raw31.npz", receipt["raw_features_sha256"])
    with np.load(io.BytesIO(raw_bytes), allow_pickle=False) as archive:
        supplied = archive["raw_features"]
    actual, records = _compute(census, manifest, root)
    _unchanged(census, root, bindings, runtime)
    if (supplied.dtype != actual.dtype or supplied.tobytes(order="C") != actual.tobytes(order="C")
            or p.canonical_sha(records) != p.canonical_sha(receipt["rows"])):
        raise ValueError("full raw31 replay differs from supplied vectors or normalization records")
    return dict(
        schema="painter-family-raw31-replay/1.0", status="all_rows_recomputed_exactly",
        receipt_sha256=expected_receipt_sha256, simulation_only=manifest["simulation_only"],
        rows_recomputed=len(records), normalized_rows_matched=len(records),
        max_absolute_difference=0.0, replay_pid=os.getpid(),
        raw31_extraction_reproduced=True, learned_extraction_reproduced=False,
        remote_attestation=False, runtime=runtime, implementation_bindings=bindings,
    )


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("operation", choices=("extract", "replay"))
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--run-sha256", required=True)
    parser.add_argument("--events-sha256", required=True)
    parser.add_argument("--terminal-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt-sha256")
    parser.add_argument("--allow-simulation", action="store_true")
    args = parser.parse_args()
    if args.operation == "replay" and args.receipt_sha256 is None:
        parser.error("replay requires an externally retained --receipt-sha256")
    census = fc.load_terminal_census(
        args.run, allow_simulation=args.allow_simulation,
        expected_hashes=dict(zip(fc.RECORD_FILES, (
            args.run_sha256, args.events_sha256, args.terminal_sha256))),
    )
    kwargs = dict(allow_simulation=args.allow_simulation)
    if args.operation == "extract":
        result = dict(receipt_sha256=execute(census, args.output, **kwargs))
    else:
        result = replay(census, args.output, expected_receipt_sha256=args.receipt_sha256, **kwargs)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
