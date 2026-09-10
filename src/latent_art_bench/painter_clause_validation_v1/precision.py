"""Offline allocation planning, not prospective outcomes or a power calculation.

The proxy fixes noisy historical OAuth scene means and resamples centered repeat
residuals. No generic-clause distribution without the earlier palette challenge
has yet been observed: its mean/noise scenarios are hypothetical. One generic cloud
is shared by both painter endpoints. Estimated precision is conditional on these
old means and empirical residual laws; it does not include new-scene uncertainty,
service drift, carryover, or uncertainty in the estimated proxy law.

The separate artificial randomization qualification fixes four position outcomes
per scene/repeat before assigning arms. It checks the numerical procedure under
sharp nulls with no interference, including partial nulls sharing one generic arm.
It cannot qualify those assumptions for the image service. There is no new Q-test,
effect confidence interval, significance test of transformed vectors, equivalence
margin, or guarantee about latent style or human perception here.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import platform
import subprocess
from pathlib import Path

import numpy as np
import scipy
from scipy.spatial.distance import cdist

PAINTERS = ("claude_monet", "paul_cezanne")
CLASSES = ("built", "land", "water")
ALLOCATIONS = ((12, 3), (24, 3), (24, 4))
PROXY_TRIALS = 250
PROXY_SEED = 120260910
NULL_TRIALS = 5000
NULL_DRAWS = 999
NULL_SEED = 120260911
PRIMARY_DRAWS = 99999
NULL_UPPER_LIMIT = 0.065
INPUT_PATH = Path("data/manifests/painter_naming_geometry_v1/pngv1-20260910/inputs.json")
OUTPUT_DIRECTORY = Path("studies/painter_clause_validation_v1")
SOURCE_PATH = Path("src/latent_art_bench/painter_clause_validation_v1/precision.py")
TEST_PATH = Path("tests/painter_clause_validation_v1/test_precision.py")
TARGETS = {
    "claude_monet": dict(built=4 / 38, land=13 / 38, water=21 / 38),
    "paul_cezanne": dict(built=11 / 32, land=18 / 32, water=3 / 32),
}
NULL_CASES = (
    "constant",
    "position_drift",
    "rare_large",
    "monet_null_cezanne_shift",
    "cezanne_null_monet_shift",
)


def _positive_integer(value, name, *, minimum=1):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return int(value)


def _finite(value, shape=None):
    raw = np.asarray(value)
    if raw.dtype.kind not in "fiu" or not np.isfinite(raw).all():
        raise ValueError("finite real numeric arrays required")
    result = raw.astype(float)
    if shape is not None and result.shape != shape:
        raise ValueError(f"array must have shape {shape}")
    return result


def _proxy_inputs(inputs):
    if inputs.get("schema") != "painter-naming-geometry-inputs/1":
        raise ValueError("expected retained geometry inputs, not new outcomes")
    expected_ids = [f"{c}{i:02d}" for c in CLASSES for i in range(1, 9)]
    old = [inputs["original"]["primary512"]["oauth_gpt_image_2"][p] for p in PAINTERS]
    references = []
    for painter, cell, count in zip(PAINTERS, old, (38, 32)):
        if (
            cell["scene_ids"] != expected_ids
            or cell["repeat_ids"] != [0, 1, 2]
            or cell["classes"] != [c for c in CLASSES for _ in range(8)]
        ):
            raise ValueError("fixed historical scene/repeat order differs")
        if inputs["targets"][painter] != TARGETS[painter]:
            raise ValueError("fixed painter reference content masses differ")
        reference = inputs["reference"]["primary512"][painter]
        if len(reference["ids"]) != count or len(set(reference["ids"])) != count:
            raise ValueError("complete unique fixed reference IDs required")
        references.append(_finite(reference["values"], (count, 31)))
    free = np.array([_finite(c["free"], (24, 3, 31)) for c in old])
    named = np.array([_finite(c["named"], (24, 3, 31)) for c in old])
    return free, named, np.array(old[0]["classes"]), expected_ids, references


def _draw_residuals(rng, mean, residuals, repetitions):
    """Independently draw an empirical centered residual for every scene/repeat."""
    count = len(mean)
    index = rng.integers(0, residuals.shape[1], size=(count, repetitions))
    return mean[:, None, :] + residuals[np.arange(count)[:, None], index]


def _energy_without_reference_self(reference, generated, weights):
    """Full V-energy minus its reference-only constant, which cancels in N-G."""
    y = generated.reshape(-1, reference.shape[1])
    return float(2 * np.mean(cdist(reference, y) @ weights) - weights @ cdist(y, y) @ weights)


def compute(inputs, trials=PROXY_TRIALS, seed=PROXY_SEED):
    """Reproduce nine hypothetical G scenarios for each of three fixed allocations.

    Order and RNG calls preserve the original disclosed exploratory calculation:
    choose the balanced 12-scene subset once, allocation, alpha, noise scenario,
    trial, shared G, Monet N, Cezanne N. The 250-trial result is an SD estimate,
    not a prediction of new arm effects or a sample-size guarantee.
    """
    trials = _positive_integer(trials, "trials", minimum=2)
    seed = _positive_integer(seed, "seed", minimum=0)
    free, named, classes, scene_ids, references = _proxy_inputs(inputs)
    pooled_free = free.transpose(1, 0, 2, 3).reshape(24, 6, 31)
    free_mean = pooled_free.mean(1)
    named_mean = named.mean(2)
    generic_named_mean = named_mean.mean(0)
    # Scale empirical residual covariance to the unbiased sample covariance.
    generic_free_residual = (pooled_free - free_mean[:, None, :]) * np.sqrt(6 / 5)
    named_residual = (named - named_mean[:, :, None, :]) * np.sqrt(3 / 2)
    generic_named_residual = named_residual.transpose(1, 0, 2, 3).reshape(24, 6, 31)
    rng = np.random.default_rng(seed)
    subset12 = np.sort(
        np.concatenate(
            [rng.choice(np.where(classes == content)[0], 4, replace=False) for content in CLASSES]
        )
    )
    records = []
    for scenes, repetitions in ALLOCATIONS:
        selected = subset12 if scenes == 12 else np.arange(24)
        selected_classes = classes[selected]
        scene_weights = [
            np.array(
                [
                    TARGETS[painter][content] / np.sum(selected_classes == content)
                    for content in selected_classes
                ]
            )
            for painter in PAINTERS
        ]
        weights = [np.repeat(w / repetitions, repetitions) for w in scene_weights]
        for alpha, noise in itertools.product((0.0, 0.5, 1.0), ("free", "named", "free_x1.5")):
            generic_residual = {
                "free": generic_free_residual,
                "named": generic_named_residual,
                "free_x1.5": 1.5 * generic_free_residual,
            }[noise][selected]
            generic_mean = ((1 - alpha) * free_mean + alpha * generic_named_mean)[selected]
            estimates = []
            for _ in range(trials):
                generic = _draw_residuals(rng, generic_mean, generic_residual, repetitions)
                named_draws = [
                    _draw_residuals(
                        rng, named_mean[k, selected], named_residual[k, selected], repetitions
                    )
                    for k in range(2)
                ]
                estimates.append(
                    [
                        _energy_without_reference_self(references[k], named_draws[k], weights[k])
                        - _energy_without_reference_self(references[k], generic, weights[k])
                        for k in range(2)
                    ]
                )
            estimates = np.array(estimates)
            sd = estimates.std(axis=0, ddof=1)
            correlation = float(np.corrcoef(estimates.T)[0, 1]) if np.all(sd > 0) else None
            records.append(
                dict(
                    J=scenes,
                    R=repetitions,
                    outputs=scenes * repetitions * 4,
                    alpha=alpha,
                    generic_noise=noise,
                    sd=sd.tolist(),
                    mean=estimates.mean(0).tolist(),
                    endpoint_correlation=correlation,
                )
            )
    summaries = []
    for scenes, repetitions in ALLOCATIONS:
        selected = [row for row in records if (row["J"], row["R"]) == (scenes, repetitions)]
        sds = np.array([row["sd"] for row in selected])
        summaries.append(
            dict(
                J=scenes,
                R=repetitions,
                outputs=scenes * repetitions * 4,
                sd_min=sds.min(0).tolist(),
                sd_max=sds.max(0).tolist(),
            )
        )
    return dict(
        schema="painter-clause-validation-proxy-precision/1",
        seed=seed,
        trials=trials,
        painters=list(PAINTERS),
        selected12=[scene_ids[index] for index in subset12],
        scenarios_per_allocation=9,
        selected_allocation=dict(J=24, R=3, outputs=288),
        generic_shared_between_endpoints=True,
        observed_new_generic_outcomes=0,
        fixed_old_estimated_means=True,
        estimand="conditional empirical-proxy SD of weighted V-energy N minus shared G",
        residual_scaling=dict(pooled_free=float(np.sqrt(6 / 5)), named=float(np.sqrt(3 / 2))),
        records=records,
        summaries=summaries,
    )


def _pair_coefficients(reference, generic, named, weights):
    """Direct identity for full weighted V-energy, separately checked in tests."""
    reference, generic, named = map(_finite, (reference, generic, named))
    weights = _finite(weights, (len(generic),))
    if (
        generic.ndim != 2
        or named.shape != generic.shape
        or reference.ndim != 2
        or reference.shape[1] != generic.shape[1]
        or not len(reference)
        or np.any(weights <= 0)
        or not np.isclose(weights.sum(), 1, rtol=0, atol=1e-12)
    ):
        raise ValueError("compatible vectors and positive normalized pair weights required")
    pooled = np.concatenate((generic, named))
    reference_cross = cdist(pooled, reference).mean(axis=1)
    pooled_within = cdist(pooled, pooled) @ np.tile(weights, 2)
    count = len(generic)
    return weights * (
        2 * (reference_cross[count:] - reference_cross[:count])
        - (pooled_within[count:] - pooled_within[:count])
    )


def _monte_carlo_pvalues(coefficients, rng, draws):
    """Independent MC assignments for two endpoints; shared outcomes remain shared."""
    values = _finite(coefficients)
    if values.ndim != 2 or values.shape[0] != 2 or values.shape[1] < 1:
        raise ValueError("two nonempty endpoint coefficient rows required")
    draws = _positive_integer(draws, "draws")
    tolerance = 32 * np.finfo(float).eps * np.abs(values).sum(axis=1)
    threshold = np.abs(values.sum(axis=1)) - tolerance
    exceedances = np.zeros(2, dtype=int)
    for start in range(0, draws, 2048):
        bits = rng.integers(0, 2, size=(min(2048, draws - start), *values.shape), dtype=np.int8)
        statistics = np.einsum("ben,en->be", 2 * bits - 1, values)
        exceedances += np.sum(np.abs(statistics) >= threshold, axis=0)
    return (1 + exceedances) / (1 + draws)


def _holm2(pvalues):
    values = _finite(pvalues, (2,))
    if np.any((values < 0) | (values > 1)):
        raise ValueError("p-values must lie in [0, 1]")
    order = np.argsort(values, kind="stable")
    result = np.empty(2)
    result[order] = np.minimum(1, np.maximum.accumulate(values[order] * (2, 1)))
    return result


def _wilson(successes, trials):
    # This interval describes synthetic Monte Carlo error, never an image effect.
    z = 1.959963984540054
    rate = successes / trials
    denominator = 1 + z * z / trials
    center = (rate + z * z / (2 * trials)) / denominator
    width = z * np.sqrt(rate * (1 - rate) / trials + z * z / (4 * trials**2)) / denominator
    return [max(0.0, float(center - width)), min(1.0, float(center + width))]


def _synthetic_case(rng, case):
    """Fix arbitrary position outcomes first; no image-derived values are used."""
    if case not in NULL_CASES:
        raise ValueError("unknown synthetic qualification case")
    scene = np.repeat(rng.normal(size=(24, 1, 3)), 3, axis=0)
    outcomes = (
        scene
        + rng.normal(size=(72, 4, 3)) * np.repeat(np.array([0.4, 0.8, 1.2]), 24)[:, None, None]
    )
    if case == "position_drift":
        outcomes += np.arange(4)[None, :, None] * np.array([0.4, -0.3, 0.2])
        outcomes += np.arange(72)[:, None, None] / 36 * np.array([0.2, 0.1, -0.3])
    elif case == "rare_large":
        outcomes[-1, -1] += np.array([16.0, -12.0, 10.0])
    references = [rng.normal(size=(count, 3)) + k * 0.2 for k, count in enumerate((38, 32))]
    weights = [np.repeat([TARGETS[p][c] / 24 for c in CLASSES], 24) for p in PAINTERS]
    true_nulls = np.array([case != "cezanne_null_monet_shift", case != "monet_null_cezanne_shift"])
    return outcomes, references, weights, true_nulls


def randomization_qualification(trials=NULL_TRIALS, draws=NULL_DRAWS, seed=NULL_SEED):
    """Artificial 72-block four-position null check with shared G and Holm2.

    Each case has ``trials`` independent complete assignments; every block has an
    independently uniform permutation of F/G/M/C. For each primary test condition
    on the other two positions and swap the remaining pair. Partial-null cases
    add a fixed vector only to the non-null named arm, preserving the other sharp
    null. Wilson intervals quantify simulation error only. The fixed numerical
    qualification threshold is upper Wilson bound <= .065 in all five cases.

    B=999 makes this bounded diagnostic affordable; the actual prospective test
    uses B=99,999. Both use conservative ties and the plus-one correction. Exact
    small four-position checks and tests against the existing primary primitive
    supplement this simulation; no claim depends on an asymptotic energy null.
    """
    trials = _positive_integer(trials, "trials")
    draws = _positive_integer(draws, "draws")
    seed = _positive_integer(seed, "seed", minimum=0)
    rng = np.random.default_rng(seed)
    rows = []
    for case in NULL_CASES:
        outcomes, references, weights, true_nulls = _synthetic_case(rng, case)
        rejected_counts = np.zeros(2, dtype=int)
        family_rejections = 0
        raw_counts = np.zeros(2, dtype=int)
        for _ in range(trials):
            # Independent row permutations: columns now give positions for F/G/M/C.
            positions = rng.permuted(np.broadcast_to(np.arange(4), (72, 4)), axis=1)
            assigned = outcomes[np.arange(72)[:, None], positions].copy()
            if case == "monet_null_cezanne_shift":
                assigned[:, 3] += np.array([6.0, -4.0, 5.0])
            elif case == "cezanne_null_monet_shift":
                assigned[:, 2] += np.array([6.0, -4.0, 5.0])
            coefficients = np.array(
                [
                    _pair_coefficients(
                        references[k], assigned[:, 1], assigned[:, 2 + k], weights[k]
                    )
                    for k in range(2)
                ]
            )
            pvalues = _monte_carlo_pvalues(coefficients, rng, draws)
            rejected = _holm2(pvalues) <= 0.05
            rejected_counts += rejected
            raw_counts += pvalues <= 0.05
            family_rejections += int(np.any(rejected & true_nulls))
        interval = _wilson(family_rejections, trials)
        rows.append(
            dict(
                case=case,
                trials=trials,
                true_nulls=true_nulls.tolist(),
                true_null_family_rejections=family_rejections,
                true_null_family_rejection_rate=family_rejections / trials,
                wilson_95=interval,
                holm_endpoint_rejections=rejected_counts.tolist(),
                raw_endpoint_rejections=raw_counts.tolist(),
                numerical_criterion_met=interval[1] <= NULL_UPPER_LIMIT,
            )
        )
    return dict(
        schema="painter-clause-validation-artificial-null/1",
        seed=seed,
        trials_per_case=trials,
        draws_per_test=draws,
        prospective_draws_per_test=PRIMARY_DRAWS,
        blocks=72,
        positions_per_block=4,
        family_size=2,
        alpha=0.05,
        generic_shared_between_endpoints=True,
        artificial_fixed_position_outcomes=True,
        service_assumptions_qualified=False,
        wilson_upper_limit=NULL_UPPER_LIMIT,
        qualified=all(row["numerical_criterion_met"] for row in rows),
        cases=rows,
    )


def _bindings_at_head(root, paths):
    """Require working and staged bytes to equal HEAD before final computation."""
    root = Path(root)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, check=True, text=True
    ).stdout.strip()
    records = []
    for relative in sorted(paths):
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("binding paths must be portable relative paths")
        path = root / relative
        if any(parent.is_symlink() for parent in (path, *path.parents)):
            raise ValueError("symlink source bindings are not allowed")
        data = path.read_bytes()
        for revision in (f"{commit}:{relative.as_posix()}", f":{relative.as_posix()}"):
            blob = subprocess.run(["git", "show", revision], cwd=root, capture_output=True)
            if blob.returncode or blob.stdout != data:
                raise ValueError(
                    f"commit source/input bytes before precision qualification: {relative}"
                )
        records.append(dict(path=relative.as_posix(), sha256=hashlib.sha256(data).hexdigest()))
    return commit, records


def report(value):
    proxy, null = value["proxy_precision"], value["randomization_qualification"]
    lines = [
        "# Prospective clause allocation: offline precision and numerical qualification",
        "",
        "This record contains no new image outcomes or observed no-palette generic distribution.",
        "The historical proxy informed the fixed 288-output allocation before collection.",
        "The question was selected after earlier results; study design was not outcome-blind.",
        "Implementation and assessment are by maintainer-run LLM agents, not independent humans.",
        "",
        f"Recorded source commit: `{value['source_commit']}`.",
        "Input/source hashes are in precision.json.",
        "Reproduce with `python -m latent_art_bench.painter_clause_validation_v1.precision` in a",
        "committed source checkout before these create-once outputs exist. Final execution refuses",
        "changed/untracked bound source, staged changes, symlinks, or existing output paths.",
        "",
        "## Historical proxy precision",
        "",
        f"Seed {proxy['seed']}; {proxy['trials']} trials per scenario.",
        "There are nine scenarios for each of three allocations.",
        "Only original primary512 OAuth vectors are used. The two historical free allocations",
        "provide six repeats per scene with the same free prompt; named means use three repeats.",
        "Estimated scene means are held fixed. Centered free/named residuals are rescaled by",
        "sqrt(6/5) and sqrt(3/2), respectively, so their empirical covariance equals the unbiased",
        "sample covariance. Named-noise pooling centers within painter first.",
        "",
        "Generic means interpolate from pooled free means to the two-painter average named mean",
        "at alpha 0, .5 and 1. Generic residuals use pooled free, pooled within-painter named, or",
        "1.5 times pooled-free residuals. One G draw is shared across both painter contrasts;",
        "each endpoint retains its own fixed reference panel and content masses.",
        "",
        "| Scenes | Repeats | Four-arm outputs | Monet SD range | Cezanne SD range |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in proxy["summaries"]:
        ranges = [f"{low:.6f}–{high:.6f}" for low, high in zip(row["sd_min"], row["sd_max"])]
        lines.append(f"| {row['J']} | {row['R']} | {row['outputs']} | {ranges[0]} | {ranges[1]} |")
    lines += [
        "",
        "The selected 24 x 3 x 4 = 288 allocation preserves 24 new scenes while avoiding",
        "the 96 extra outputs of a fourth repeat. The 144-output alternative halves the scene",
        "panel. This comparison does not establish power, a meaningful-effect threshold, or",
        "an equivalence margin; favorable scenario means do not select the allocation.",
        "",
        "The 12-scene comparison uses this single balanced historical subset:",
        "`" + ", ".join(proxy["selected12"]) + "`.",
        "",
        "| Scenes/repeats | Generic alpha | Generic noise | Monet mean / SD | Cezanne mean / SD |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in proxy["records"]:
        cells = [f"{mean:+.6f} / {sd:.6f}" for mean, sd in zip(row["mean"], row["sd"])]
        lines.append(
            f"| {row['J']}/{row['R']} | {row['alpha']:g} | {row['generic_noise']} | "
            f"{cells[0]} | {cells[1]} |"
        )
    lines += [
        "",
        "The 250-trial SD estimates have Monte Carlo noise (about 4.5% relative standard",
        "error under a normal-sampling approximation). Their spread across scenarios is not",
        "a confidence interval. Historical means are themselves noisy; six/three residual",
        "samples do not characterize tails or all 31-dimensional variation. These laws do not",
        "identify the new generic arm, new-scene variation, service drift or interference.",
        "Scenario mean effects are reported transparently and are not anticipated new effects.",
        "",
        "## Artificial four-position conditional randomization qualification",
        "",
        f"Seed {null['seed']}; {null['trials_per_case']} complete 72-block assignments per case;",
        f"{null['draws_per_test']} Monte Carlo sign draws per endpoint in this bounded check.",
        f"The planned primary analysis instead uses {null['prospective_draws_per_test']} draws.",
        "Both use independent pair swaps, conservative absolute ties and the plus-one rule.",
        "The two p-values receive Holm correction at .05 with their shared generic outcomes",
        "preserved. Other arm positions are conditioned on for each endpoint. All position",
        "outcomes are fixed before assigning independently randomized four-arm positions.",
        "",
        "Position drift and a rare large position outcome test nonconstant coefficients.",
        "Two partial-null cases shift just one named arm; only rejection of the remaining",
        "true null counts as a family error. The Wilson intervals describe artificial Monte",
        "Carlo error, not uncertainty about service behavior or any image effect.",
        "",
        "| Artificial case | True-null family errors / trials | Rate | Wilson 95% | Pass |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in null["cases"]:
        low, high = row["wilson_95"]
        lines.append(
            f"| {row['case']} | {row['true_null_family_rejections']} / {row['trials']} | "
            f"{row['true_null_family_rejection_rate']:.5f} | [{low:.5f}, {high:.5f}] | "
            f"{row['numerical_criterion_met']} |"
        )
    lines += [
        "",
        f"Prespecified numerical criterion: every upper Wilson bound <= {NULL_UPPER_LIMIT}.",
        f"Numerical criterion satisfied: **{null['qualified']}**.",
        "Exact small four-position tests also verify the weighted-energy sign identity, and",
        "tests compare the coefficients and Holm rule with the existing primary primitives.",
        "This artificial check qualifies neither no-interference nor sharp-null availability",
        "for OAuth. Treatment-dependent duration, retries, delivery and carryover remain",
        "material service limitations. A fixed new scene panel is not a random population",
        "sample. No effect confidence interval, map-label test or new Q inference is added.",
        "",
    ]
    return "\n".join(lines)


def build(root):
    """Write committed-source final planning outputs once; never opens a live gate."""
    root = Path(root).resolve()
    outputs = [root / OUTPUT_DIRECTORY / name for name in ("precision.json", "PRECISION.md")]
    if any(path.exists() or path.is_symlink() for path in outputs):
        raise ValueError("precision outputs are create-once; retain existing evidence")
    paths = {
        SOURCE_PATH,
        TEST_PATH,
        SOURCE_PATH.parent / "__init__.py",
        INPUT_PATH,
        INPUT_PATH.parent / "freeze.json",
        INPUT_PATH.parent / "receipt.json",
        Path("pyproject.toml"),
        Path("uv.lock"),
    }
    commit, bindings = _bindings_at_head(root, paths)
    inputs = json.loads((root / INPUT_PATH).read_text())
    value = dict(
        schema="painter-clause-validation-precision-record/1",
        source_commit=commit,
        source_bindings=bindings,
        environment=dict(
            python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__
        ),
        proxy_precision=compute(inputs),
        randomization_qualification=randomization_qualification(),
    )
    # Also detect any bound source edits made while the offline computations ran.
    if _bindings_at_head(root, paths) != (commit, bindings):
        raise ValueError("source commit changed during precision qualification")
    encoded = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    markdown = report(value)
    outputs[0].parent.mkdir(parents=True, exist_ok=True)
    for path, content in zip(outputs, (encoded, markdown)):
        with path.open("x", encoding="utf-8") as handle:
            handle.write(content)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = build(args.root)
    print(
        json.dumps(
            dict(
                source_commit=result["source_commit"],
                qualified=result["randomization_qualification"]["qualified"],
                outputs=[
                    str(OUTPUT_DIRECTORY / name) for name in ("precision.json", "PRECISION.md")
                ],
            )
        )
    )


if __name__ == "__main__":
    main()
