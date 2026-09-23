#!/usr/bin/env python3
"""Independently replay old-only parameter selection and equality checks.

Reads the already retained old feature arrays; performs no new extraction,
prediction, collection, model fitting beyond declared parameter recomputation,
or scientific scoring. Optional summary output is create-once.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from latent_art_bench.painter_family_controls_v1.transport_artifact import load_prepared

ROOT = Path(__file__).resolve().parents[1]
MODELS = ("gpt-image-1", "gpt-image-2", "gpt-image-2.5-flare", "gpt-image-2.5-sunburst",
          "google/gemini-3.1-flash-image", "black-forest-labs/flux.2-max")
PAINTERS = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def array_sha(array):
    digest = hashlib.sha256()
    digest.update(str(array.shape).encode("ascii"))
    digest.update(np.asarray(array, dtype="<f8").tobytes(order="C"))
    return digest.hexdigest()


def verify(path, expected_sha256):
    # The caller supplies a digest independently of this artifact's contents.
    record = load_prepared(path, expected_sha256=expected_sha256, root=ROOT)
    assert record["model_order"] == list(MODELS)
    assert record["painter_order"] == list(PAINTERS)
    assert record["new_observations"] == 0 and record["live_authorization"] is False
    manifest_path = ROOT/"reports/painter_learned_audit_v1/inputs.json"
    manifest = json.loads(manifest_path.read_text())
    rows = manifest["rows"]
    # This oracle does not use old_arrays or fit_transport_parameters.
    named_rows = [(i, r) for i, r in enumerate(rows) if r["role"] == "generated"
                  and r["view"] == "original" and r["arm"] in PAINTERS]
    lookup = {(r["model"], r["scene"], r["repeat"], r["arm"]): i for i, r in named_rows}
    assert len(named_rows) == len(lookup) == 672
    indices = [lookup[m, s, r, a] for m in MODELS for s in range(14)
               for r in range(2) for a in PAINTERS]
    assert len({rows[i]["id"] for i in indices}) == 672
    ref_indices = [[i for i, r in enumerate(rows) if r["role"] == "reference"
                    and r["view"] == "original" and r["painter"] == a] for a in PAINTERS]
    assert list(map(len, ref_indices)) == [297, 106, 141, 105]
    encoders = {}
    for encoder in ["clip", "csd"]:
        array_path = ROOT/f"reports/painter_learned_audit_v1/embeddings_{encoder}.npz"
        with np.load(array_path, allow_pickle=False) as archive:
            values = archive["embeddings"].astype(np.float64)
        old = values[indices].reshape(6, 14, 2, 4, -1)
        refs = np.stack([values[i].mean(axis=0) for i in ref_indices])
        classes = old.sum(axis=(1, 2))/28
        grand = classes.sum(axis=1)/4

        def normalize(array):
            return array/np.linalg.norm(array, axis=-1, keepdims=True)

        expected = {"raw_reference_means": refs, "reference_prototypes": normalize(refs),
                    "old_generated_class_means": classes, "old_generated_grand_mean": grand,
                    "translation": refs.sum(axis=0)/4-grand,
                    "generated_prototypes": normalize(classes)}
        actual = record["parameters"][encoder]
        for key, value in expected.items():
            np.testing.assert_array_equal(actual[key], value)
        assert actual["old_array_sha256"] == array_sha(old)
        assert actual["reference_array_sha256"] == array_sha(refs)
        assert actual["encoder"] == encoder
        assert record["encoder_contracts"][encoder] == manifest["models"][encoder]
        encoders[encoder] = {"old_array_shape": list(old.shape),
                            "parameter_arrays_compared": list(expected),
                            "all_parameters_exactly_equal": True, "max_absolute_difference": 0.0,
                            "old_array_digest_matches": True,
                            "reference_array_digest_matches": True,
                            "source_npz_sha256": sha(array_path)}
    loader_path = ROOT/"src/latent_art_bench/painter_family_controls_v1/transport_artifact.py"
    return {"scope": "old-only candidate provenance and independent parameter equality",
            "candidate_path": str(path.relative_to(ROOT)), "candidate_sha256": sha(path),
            "expected_sha256": expected_sha256, "oracle_script_sha256": sha(__file__),
            "loader_sha256": sha(loader_path),
            "manifest_sha256": sha(manifest_path), "old_named_count": 672,
            "reference_counts": list(map(len, ref_indices)),
            "bindings_verified": len(record["bindings"]),
            "encoders": encoders, "new_observations": 0, "live_authorization": False,
            "scientific_outcome_metrics_computed": False,
            "complete_study_freeze": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path,
                        default=ROOT/"reports/painter_family_controls_v1/old_transport_candidate_v1.json")
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    summary = verify(args.candidate.resolve(), args.expected_sha256)
    serialized = json.dumps(summary, indent=2, sort_keys=True, allow_nan=False)+"\n"
    if args.output:
        with args.output.open("x") as stream:
            stream.write(serialized)
    else:
        print(serialized, end="")
