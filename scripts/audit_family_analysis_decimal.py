#!/usr/bin/env python3
"""Replay the independent 309-case family-analysis numerical audit.

Constructed inputs only. This does not load empirical arrays or edit analyses.
Run from the repository with .venv/bin/python; optional output is create-once.
"""

import argparse
import hashlib
import json
from decimal import Decimal, localcontext
from pathlib import Path

import numpy as np
from scipy.stats import t

from latent_art_bench.painter_family_controls_v1.analysis import fieller_confidence_set

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def cases():
    result = []
    for offset in [0., 1e-2, -1e-2, 1e-6, -1e-6, 1e-10, -1e-10,
                   1e-12, -1e-12, 1e-14, -1e-14]:
        y = np.tile([-1., 1.], 4) + offset
        result.append((np.ones(8), y, ["constant", offset]))
        for slope in [-3., -.3, .3, 3.]:
            for jitter in [0., 1e-10, 1e-6, .1]:
                x = slope*y + jitter*np.array([-2., 1., 3., -1., 2., -3., 1., 2.])
                result.append((x, y, ["weak", offset, slope, jitter]))
    rng = np.random.default_rng(271828)
    for k in range(100):
        x = rng.normal(size=8)*rng.choice([1., .001])
        y = rng.normal(size=8)+rng.choice([0., .1, 2.])
        result.append((x, y, ["random", k]))
    for slope in [-3., -.3, .3, 3.]:
        for scale in [1e-300, 1e-200, 1., 1e100, 1e150]:
            y = np.arange(1., 9.)/100*scale
            x = (slope*np.arange(1., 9.)/100 + 1e-10*np.tile([-1., 1.], 4))*scale
            result.append((x, y, ["strong", slope, scale]))
    for sign in [-1, 1]:
        result.append((np.arange(1., 9.)/100, np.full(8, sign*1e-170), ["unequal", sign]))
    return result


def included(record, candidate):
    return any((a is None or candidate >= a) and (b is None or candidate <= b)
               for a, b in record["confidence_set"]["intervals"])


def verify():
    q = Decimal.from_float(float(t.ppf(.975, 7)))
    decisive, exclusions, failures = 0, [], []
    inputs = cases()
    for x, y, label in inputs:
        record = fieller_confidence_set(x, y)
        json.dumps(record, allow_nan=False)
        candidates = [-10., -3., -1., 0., 1., 3., 10.]
        raw = record["raw_signed_ratio"]
        if raw is not None and abs(raw) < 1e100:
            candidates.append(raw)
        for interval in record["confidence_set"]["intervals"]:
            for bound in interval:
                if bound is not None:
                    step = max(abs(bound), 1e-6)*1e-6
                    candidates.extend([bound-step, bound+step])
        with localcontext() as ctx:
            ctx.prec = 100
            dx, dy = list(map(Decimal.from_float, x)), list(map(Decimal.from_float, y))
            for candidate in candidates:
                d = Decimal.from_float(candidate)
                residual = [a-d*b for a, b in zip(dx, dy)]
                mean = sum(residual)/8
                variance = sum((z-mean)**2 for z in residual)/56
                left, right = mean*mean, q*q*variance
                scale = max(max(abs(a) for a in dx), abs(d)*max(abs(a) for a in dy))
                tolerance = max(max(abs(left), abs(right))*Decimal("1e-12"),
                                scale**2*Decimal("1e-28"))
                if abs(left-right) <= tolerance:
                    exclusions.append({"case": label, "candidate": candidate,
                                       "left": str(left), "right": str(right),
                                       "exclusion_tolerance": str(tolerance)})
                    continue
                decisive += 1
                oracle = left <= right
                if included(record, candidate) != oracle:
                    failures.append({"case": label, "candidate": candidate,
                                     "expected_included": oracle,
                                     "confidence_set": record["confidence_set"],
                                     "left": str(left), "right": str(right)})
    return {
        "scope": "independent constructed paired Fieller direct-inversion verification",
        "analysis_sha256": sha(ROOT/"src/latent_art_bench/painter_family_controls_v1/analysis.py"),
        "oracle_script_sha256": sha(__file__),
        "numpy_version": np.__version__, "decimal_precision": 100,
        "seed": 271828, "case_count": len(inputs), "decisive_membership_checks": decisive,
        "precision_boundary_exclusions": len(exclusions), "failure_count": len(failures),
        "exclusion_rule": (
            "abs(L-R)<=max(1e-12*max(abs(L),abs(R)),1e-28*s^2); "
            "s=max(max(abs(x)),abs(r)*max(abs(y)))"
        ),
        "excluded_comparisons": exclusions, "failures": failures,
        "empirical_arrays_read": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    summary = verify()
    serialized = json.dumps(summary, indent=2, sort_keys=True, allow_nan=False)+"\n"
    if args.output:
        with args.output.open("x") as stream:
            stream.write(serialized)
    else:
        print(serialized, end="")
    raise SystemExit(bool(summary["failure_count"]))
