"""Retrospective matched-seed SD-Turbo audit; real calculations are opt-in.

``freeze`` validates provenance without calculating empirical summary outcomes.
``analyze`` and ``check`` require --execute-real and a frozen passing code audit.
No network, generation, feature extraction, or old-evidence writes are provided.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import itertools
import json
import os
import platform
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from latent_art_bench.painter_feature_generation_v2.features import NAMES

ROOT = Path(__file__).resolve().parents[2]
NS = "painter_cross_cohort_v1"
PLAN = Path("studies") / NS / "PLAN.md"
IMPLEMENTATION = Path("src/latent_art_bench") / f"{NS}.py"
OUT = Path("reports") / NS
ARTISTS = ("claude_monet", "alfred_sisley", "camille_pissarro", "paul_cezanne")
ARMS = ("artist_free", *ARTISTS)
SCENES = tuple(f"{p}{i}" for p in "WBRL" for i in range(1, 5))
VIEWS = {
    "all31": slice(0, 31),
    "color": slice(0, 11),
    "spatial": slice(11, 19),
    "texture": slice(19, 31),
}
DATA = Path("data/manifests/painter_feature_generation_v2")
RUN = DATA / "pfg2-sd-turbo-20260905"
METHOD = DATA / "pfg2-method-20260905"
FEATURES = METHOD / "experiments/pfg2-sd-turbo-20260905/generated_features.jsonl"
FEATURE_RECEIPT = FEATURES.with_name("generated_receipt.json")
LIBRARY = Path("data/manifests/painter_feature_generation_v1/prompt_library.json")
LEARNED_INPUTS = Path("reports/painter_learned_audit_v1/inputs.json")
REFERENCE_COUNTS = dict(zip(ARTISTS, (297, 106, 141, 105)))
DEVELOPMENT_COUNTS = dict(zip(ARTISTS, (101, 36, 48, 36)))
ANCHORS = {
    RUN
    / "generation_freeze.json": "5e0abf5117ad3c5fc01a6c6b888bc809138e9a1088b1b926f4c99ef69582c825",
    RUN / "requests.jsonl": "f4cde51372c1cdf78625968845a95c01278e05ed14fc204fd29c560d3372b52b",
    RUN / "outputs.jsonl": "1b519dff82214574af0273a35b2ea63f3afec88ce74400f803de0233fbedc9c5",
    RUN
    / "generation_events.jsonl": "9624eb74641218825d7b47c7079234302b11d6d03b33037e0515a646a395a182",
    RUN
    / "generation_receipt.json": "58dc9fdaa0c4c8d49124ee3653cbc4494d358b1d71d4956721b8f2e2aa0ef033",
    FEATURES: "eaed290dbc6a4afe5a330b29a6721f4556914517e74eb4300bb0cb422192b560",
    FEATURE_RECEIPT: "b97c1233ad8e72fbde349f7b5b52aa2ed8de63619c0ed163bd40b535f4788509",
    METHOD / "confirmation_features.jsonl": (
        "01cc5167c09b88eab6a86885b72040f76fc8a7ca8a62acd56d85a8b16b2f7717"
    ),
    METHOD / "confirmation_receipt.json": (
        "22617ada4debec0dde30cbb9c492b986e67fe0c5382f0b8d69740466d934889a"
    ),
    METHOD
    / "method_freeze.json": "0c254c629b37803c7e99f2c61485f6086f593f98cd8bc26b78a5c498f2b29200",
    METHOD / "scaler.json": "71f511235081dfc1e9846976320c69477bcbd04dd43fc9a2e271f7b0375497b9",
    METHOD / "development_receipt.json": (
        "5a724637bbf4ff1e424be0259e53ceb47c4926dba926defcff2609c7057b1b1c"
    ),
    LIBRARY: "fbe81e7cb93282dae96c3edd7df58ed3d43ee81516b6df113f3c8b56b07e09a7",
    LEARNED_INPUTS: "bd9cb00279fffb741b3579e3234ad034bb593884925ea40893c717612eccca57",
}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_number(value):
    raise ValueError(f"nonfinite JSON number: {value}")


def _json(text):
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=_invalid_number)


def read(path):
    return _json(Path(path).read_text())


def read_rows(path):
    return [_json(line) for line in Path(path).read_text().splitlines()]


def write_new(path, value):
    """Create once; completed evidence is never overwritten."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        value
        if isinstance(value, str)
        else json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    with path.open("x") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())


def _path(root, relative):
    relative = Path(relative)
    target = (root / relative).resolve()
    if relative.is_absolute() or not target.is_relative_to(root.resolve()):
        raise ValueError("binding must remain inside repository")
    return target


def verify_bindings(bindings, root=ROOT):
    if len({x["path"] for x in bindings}) != len(bindings):
        raise ValueError("duplicate binding path")
    for item in bindings:
        if sha(_path(root, item["path"])) != item["sha256"]:
            raise ValueError("binding changed: " + item["path"])


def u_product(vectors):
    """Ordered distinct-block inner products; axis 0 is the paired repeat unit.

    Return one scalar per intermediate axis. The centered equivalent avoids
    subtracting two large, nearly equal block sums. Negative values are retained.
    """
    v = np.asarray(vectors, dtype=np.float64)
    if v.ndim < 2 or v.shape[0] < 2 or min(v.shape) < 1 or not np.isfinite(v).all():
        raise ValueError("finite K>=2 block vectors required")
    k = len(v)
    with np.errstate(over="raise", invalid="raise"):
        mean = v.mean(axis=0)
        value = np.square(mean).sum(axis=-1) - np.square(v - mean).sum(axis=(0, v.ndim - 1)) / (
            k * (k - 1)
        )
    if not np.isfinite(value).all():
        raise ValueError("unrepresentable U statistic")
    return value


def _finite_float(value):
    value = float(value)
    if not np.isfinite(value):
        raise ValueError("nonfinite statistic")
    return value


def _identity(a, b, label):
    residual = _finite_float(a - b)
    if abs(residual) > 1e-10 * max(1.0, abs(a), abs(b)):
        raise ValueError("numerical identity failed: " + label)
    return residual


def _energy(delta, references):
    """K x four-painter x D input, with full within-block arm dependence."""
    common = delta.mean(axis=1)
    centered = delta - common[:, None, :]
    c = _finite_float(4 * u_product(common))
    between = _finite_float(u_product(centered).sum())
    n = _finite_float(u_product(delta).sum())
    h = _finite_float(np.square(references).sum())
    beta = d = d_residual = None
    if h > 0:
        beta = _finite_float((centered.mean(axis=0) * references).sum() / h)
        d = _finite_float(u_product(centered - references).sum() / h)
        d_residual = _identity(d, between / h - 2 * beta + 1, "D")
    return dict(
        C=c,
        L=between,
        N=n,
        T=_finite_float(c - between),
        common_fraction=_finite_float(c / n) if n > 0 else None,
        common_fraction_reason=None if n > 0 else "nonpositive_total_naming_change",
        common_majority_descriptive=bool(n > 0 and c - between > 0),
        H=h,
        beta=beta,
        D=d,
        alignment_reason=None if h > 0 else "zero_reference_energy",
        decomposition_residual=_identity(n, c + between, "N=C+L"),
        D_identity_residual=d_residual,
    )


def _summary(z, means):
    references = means - means.mean(axis=0)
    delta = z[:, :, 1:] - z[:, :, :1]
    pooled = _energy(delta.mean(axis=1), references)
    scenes = [_energy(delta[:, s], references) for s in range(z.shape[1])]
    keys = ("C", "L", "N", "T", "beta", "D", "decomposition_residual", "D_identity_residual")
    within = {
        k: None if scenes[0][k] is None else _finite_float(np.mean([x[k] for x in scenes]))
        for k in keys
    }
    within.update(
        H=pooled["H"],
        alignment_reason=pooled["alignment_reason"],
        common_fraction=within["C"] / within["N"] if within["N"] > 0 else None,
        common_fraction_reason=None if within["N"] > 0 else "nonpositive_total_naming_change",
        common_majority_descriptive=bool(within["N"] > 0 and within["T"] > 0),
    )
    pairs = []
    for a, b in itertools.combinations(range(4), 2):
        q = means[a] - means[b]
        h = _finite_float(q @ q)
        g = z[:, :, a + 1] - z[:, :, b + 1]
        pairs.append(
            dict(
                painters=[ARTISTS[a], ARTISTS[b]],
                reference_squared_distance=h,
                aligned_amplitude=_finite_float(g.mean(axis=(0, 1)) @ q / h) if h > 0 else None,
                scene_D=_finite_float(u_product(g - q).mean() / h) if h > 0 else None,
                reason=None if h > 0 else "zero_reference_pair_distance",
            )
        )
    return dict(
        pooled=pooled,
        within_scene=within,
        scene_minus_pooled_D=None if pooled["D"] is None else within["D"] - pooled["D"],
        scene_records=[dict(scene_index=i, **value) for i, value in enumerate(scenes)],
        pairs=pairs,
    )


def summarize(generated, reference_means):
    """Pure full-family summary, including every delete-one-block sensitivity."""
    z, means = (
        np.asarray(generated, dtype=np.float64),
        np.asarray(reference_means, dtype=np.float64),
    )
    if (
        z.ndim != 4
        or z.shape[0] < 3
        or z.shape[1] < 1
        or z.shape[2:] != (5, 31)
        or means.shape != (4, 31)
        or not np.isfinite(z).all()
        or not np.isfinite(means).all()
    ):
        raise ValueError("finite K>=3 x scenes x five arms x 31 and four reference means required")
    families = {
        name: _summary(z[..., section], means[..., section]) for name, section in VIEWS.items()
    }
    deletions = [
        dict(
            block=b,
            families={
                name: _summary(np.delete(z, b, axis=0)[..., section], means[..., section])
                for name, section in VIEWS.items()
            },
        )
        for b in range(len(z))
    ]
    ranges = {}
    for family in VIEWS:
        ranges[family] = {}
        for view in ("pooled", "within_scene"):
            ranges[family][view] = {}
            for key in ("C", "L", "N", "T", "common_fraction", "beta", "D"):
                rows = [(row["block"], row["families"][family][view][key]) for row in deletions]
                finite = [v for _, v in rows if v is not None]
                ranges[family][view][key] = dict(
                    minimum=min(finite) if finite else None,
                    maximum=max(finite) if finite else None,
                    available=len(finite),
                    unavailable_blocks=[b for b, v in rows if v is None],
                )
    return dict(
        schema_version=1,
        study=NS,
        blocks=len(z),
        scenes=z.shape[1],
        arms=list(ARMS),
        feature_names=list(NAMES),
        families=families,
        leave_one_block_out=deletions,
        sensitivity_ranges=ranges,
        inference="retrospective descriptive; no p-values or confidence intervals",
        assumptions="Correlated arms retained within matched-seed blocks; independent stable "
        "block errors motivate expectations but are not established by this audit.",
    )


def validate_cell_rows(requests, outputs, features):
    """Exact all-2000 metadata census; no moments or other empirical outcomes."""
    expected = {(b, s, a) for b in range(25) for s in SCENES for a in ARMS}
    found, request_ids = set(), set()
    for row in requests:
        b = row.get("block")
        cell = (b, row.get("template_id"), row.get("condition"))
        if type(b) is not int or cell not in expected or cell in found:
            raise ValueError("duplicate, foreign, or malformed request cell")
        if row.get("request_id") != f"b{b:03d}-{cell[1]}-{cell[2]}":
            raise ValueError("request identity disagrees with cell")
        found.add(cell)
        request_ids.add(row["request_id"])
    if found != expected or len(requests) != 2000:
        raise ValueError("incomplete request census")
    by_output, by_feature = {}, {}
    for rows, key, target, status in (
        (outputs, "request_id", by_output, "generated"),
        (features, "image_id", by_feature, "measured"),
    ):
        for row in rows:
            identity = row.get(key)
            if identity not in request_ids or identity in target or row.get("status") != status:
                raise ValueError("incomplete, duplicate, foreign, or failed output/feature")
            target[identity] = row
        if set(target) != request_ids:
            raise ValueError("incomplete output/feature census")
    for req in requests:
        out, feat = by_output[req["request_id"]], by_feature[req["request_id"]]
        for row in (out, feat):
            if any(
                row.get(k) != req[k] or type(row.get(k)) is not type(req[k])
                for k in ("block", "template_id", "condition")
            ):
                raise ValueError("output/feature cell disagrees with request")
        if out.get("sha256") != feat.get("raw_sha256"):
            raise ValueError("feature pixel identity disagrees with output")
        v = np.asarray(feat.get("values"), dtype=np.float64)
        if v.shape != (31,) or not np.isfinite(v).all():
            raise ValueError("invalid raw feature vector")
        norm = feat.get("normalization", {})
        if any(
            norm.get(k) != value
            for k, value in dict(
                crop_fraction=0.0,
                short_side=512,
                original_width=512,
                original_height=512,
                normalized_width=512,
                normalized_height=512,
                color_profile="missing_assumed_srgb",
            ).items()
        ):
            raise ValueError("feature normalization contract changed")
    return by_output, by_feature


def validate_census(root=ROOT):
    """Read-only provenance validation; do not compute summary outcomes."""
    root = Path(root)
    bindings = {str(path): digest for path, digest in ANCHORS.items()}
    verify_bindings([dict(path=p, sha256=h) for p, h in bindings.items()], root)
    gen, method = (
        read(root / RUN / "generation_freeze.json"),
        read(root / METHOD / "method_freeze.json"),
    )
    for document in (gen, method):
        verify_bindings(document["inputs"], root)
        for item in document["inputs"]:
            if item["path"] in bindings and bindings[item["path"]] != item["sha256"]:
                raise ValueError("conflicting inherited binding")
            bindings[item["path"]] = item["sha256"]
    if method["feature_names"] != list(NAMES) or method["short_side"] != 512:
        raise ValueError("historical feature order or analysis size changed")
    config = gen["config"]
    for key, value in dict(
        model_id="stabilityai/sd-turbo",
        revision="b261bac6fd2cf515557d5d0707481eafa0485ec2",
        dtype="float16",
        device="mps",
        height=512,
        width=512,
        num_inference_steps=1,
        guidance_scale=0.0,
        negative_prompt=None,
        repetitions=25,
    ).items():
        if config.get(key) != value:
            raise ValueError("generation configuration changed")
    requests, outputs, features = (
        read_rows(root / p) for p in (RUN / "requests.jsonl", RUN / "outputs.jsonl", FEATURES)
    )
    by_output, by_feature = validate_cell_rows(requests, outputs, features)
    library = read(root / LIBRARY)
    templates = {row["template_id"]: row for row in library["templates"]}
    seed_key, seeds = bytes.fromhex(config["master_seed"]), {}
    for index, req in enumerate(requests):
        b, scene, arm = req["block"], req["template_id"], req["condition"]
        seed = (
            int.from_bytes(
                hmac.new(seed_key, f"pfg-v2/1.0-seed|{scene}|{b}".encode(), "sha256").digest()[:8],
                "big",
            )
            >> 1
        )
        prompt = (
            templates[scene]["artist_free_prompt"]
            if arm == "artist_free"
            else (templates[scene]["named_prompts"][arm]["prompt"])
        )
        if req["seed"] != seed or req["sequence"] != index or req["prompt"] != prompt:
            raise ValueError("seed, request order, or prompt changed")
        seeds[b, scene] = seed
    if len(set(seeds.values())) != 400:
        raise ValueError("seed uniqueness changed")
    pixels = []
    for out in outputs:
        expected_path = (
            f"research_workspace/painter_feature_generation_v2/"
            f"pfg2-sd-turbo-20260905/generated/{out['request_id']}.png"
        )
        if out["image_path"] != expected_path or (out["width"], out["height"]) != (512, 512):
            raise ValueError("pixel path or geometry changed")
        if sha(_path(root, out["image_path"])) != out["sha256"]:
            raise ValueError("retained pixel hash changed")
        pixels.append(dict(id=out["request_id"], path=out["image_path"], sha256=out["sha256"]))
    learned = read(root / LEARNED_INPUTS)["rows"]
    primary = [r for r in learned if r["role"] == "reference" and r["view"] == "original"]
    main = [r for r in learned if r["role"] == "generated" and r["view"] == "original"]
    if len(main) != 1008 or len(primary) != 649:
        raise ValueError("main/reference membership count changed")
    if {r["sha256"] for r in main} & {r["sha256"] for r in outputs}:
        raise ValueError("generated cohort overlaps main image hashes")
    refs = read_rows(root / METHOD / "confirmation_features.jsonl")
    if Counter(r["status"] for r in refs) != {"measured": 649, "failed": 4}:
        raise ValueError("reference admission dispositions changed")
    refs = [r for r in refs if r["status"] == "measured"]
    if Counter(r["painter_id"] for r in refs) != REFERENCE_COUNTS:
        raise ValueError("reference painter counts changed")
    identities = {(r["image_id"], r["painter_id"], r["raw_sha256"]) for r in refs}
    if len(identities) != 649 or identities != {
        (r["id"], r["painter"], r["sha256"]) for r in primary
    }:
        raise ValueError("reference target is not exact original main membership")
    for row in primary:
        if sha(_path(root, row["path"])) != row["sha256"]:
            raise ValueError("reference original pixel changed")
    for r in refs:
        if (
            r["normalization"]["short_side"] != 512
            or r["normalization"]["crop_fraction"] != 0
            or np.asarray(r["values"]).shape != (31,)
            or not np.isfinite(r["values"]).all()
        ):
            raise ValueError("invalid original reference normalization/features")
    scaler = read(root / METHOD / "scaler.json")
    if (
        scaler["development_counts"] != DEVELOPMENT_COUNTS
        or scaler["quantile_rule"] != "equal_painter_weighted_empirical_inverse_cdf"
        or scaler["method_freeze_sha256"] != ANCHORS[METHOD / "method_freeze.json"]
        or scaler["development_feature_sha256"]
        != read(root / METHOD / "development_receipt.json")["feature_file_sha256"]
        or any(scaler["invalid_coordinates"].values())
    ):
        raise ValueError("development scaler provenance changed")
    center, scale = np.asarray(scaler["center"]), np.asarray(scaler["scale"])
    if (
        center.shape != (31,)
        or scale.shape != (31,)
        or not np.isfinite(center).all()
        or not np.isfinite(scale).all()
        or np.any(scale <= 0)
    ):
        raise ValueError("invalid frozen scaler")
    return dict(
        requests=requests,
        by_output=by_output,
        by_feature=by_feature,
        references=refs,
        scaler=scaler,
        bindings=[dict(path=p, sha256=h) for p, h in sorted(bindings.items())],
        provenance=dict(
            cohort="pfg2-sd-turbo-20260905",
            generated_count=2000,
            blocks=25,
            scenes=list(SCENES),
            arms=list(ARMS),
            reference_counts=REFERENCE_COUNTS,
            development_counts=DEVELOPMENT_COUNTS,
            generation_config=config,
            generation_utc_range=[
                min(r["at_utc"] for r in outputs),
                max(r["at_utc"] for r in outputs),
            ],
            original_pixels=pixels,
            references=primary,
            unique_scene_block_seeds=400,
            seed_pairing="all five arms share the scene/block seed",
            main_pixel_overlap=0,
            source_feature_rows=2000,
            retrospective=True,
            reference_reuse="same exposed full-frame 649-work main target",
            prior_exposure="energy-distance, coordinate, qualification, and copy diagnostics",
            prompt_rule=(
                "An oil painting on canvas of ...; insert only ' by [painter]' after canvas"
            ),
            family_prompt_available=False,
            new_generation=False,
            new_feature_extraction=False,
        ),
    )


def code_paths(root=ROOT):
    tests = sorted((Path(root) / "tests" / NS).glob("test_*.py"))
    if not tests:
        raise ValueError("constructed tests required")
    return [PLAN, IMPLEMENTATION, *(p.relative_to(root) for p in tests)]


def verify_audit(audit_path, root=ROOT):
    audit = read(audit_path)
    if audit.get("status") != "passed":
        raise ValueError("independent design/code audit must pass before freeze")
    verify_bindings(audit["bindings"], root)
    if not {str(p) for p in code_paths(root)} <= {b["path"] for b in audit["bindings"]}:
        raise ValueError("audit must bind exact plan, implementation and all constructed tests")
    return audit


def freeze(audit_path, root=ROOT):
    root = Path(root)
    destination = root / OUT / "inputs.json"
    if any((root / OUT / name).exists() for name in ("inputs.json", "analysis.json", "REPORT.md")):
        raise FileExistsError("namespace already frozen or analyzed")
    audit_path = Path(audit_path).resolve()
    if not audit_path.is_relative_to(root.resolve()):
        raise ValueError("audit report must be retained inside repository")
    verify_audit(audit_path, root)
    census = validate_census(root)
    bindings = {r["path"]: r["sha256"] for r in census["bindings"]}
    for path in [*code_paths(root), audit_path.relative_to(root), Path("pytest-paper.ini")]:
        bindings[str(path)] = sha(root / path)
    record = dict(
        schema_version=1,
        study=NS,
        created_utc=datetime.now(timezone.utc).isoformat(),
        audit_path=str(audit_path.relative_to(root)),
        bindings=[dict(path=p, sha256=h) for p, h in sorted(bindings.items())],
        provenance=census["provenance"],
        empirical_summaries_computed=False,
        runtime=dict(python=platform.python_version(), numpy=np.__version__),
    )
    write_new(destination, record)
    return record


def load_frozen(root=ROOT, *, execute_real=False, expected_inputs_sha256=None):
    if not execute_real:
        raise PermissionError(
            "real outcomes require explicit --execute-real after the independent audit"
        )
    root = Path(root)
    if (
        not isinstance(expected_inputs_sha256, str)
        or len(expected_inputs_sha256) != 64
        or sha(root / OUT / "inputs.json") != expected_inputs_sha256
    ):
        raise ValueError("external expected frozen-input SHA-256 is required and must match")
    frozen = read(root / OUT / "inputs.json")
    verify_bindings(frozen["bindings"], root)
    verify_audit(root / frozen["audit_path"], root)
    if frozen["runtime"] != dict(python=platform.python_version(), numpy=np.__version__):
        raise ValueError("analysis runtime differs from freeze")
    census = validate_census(root)
    if census["provenance"] != frozen["provenance"]:
        raise ValueError("frozen cohort provenance changed")
    center, scale = (np.asarray(census["scaler"][key]) for key in ("center", "scale"))
    z = np.empty((25, 16, 5, 31), dtype=np.float64)
    for req in census["requests"]:
        row = census["by_feature"][req["request_id"]]
        z[req["block"], SCENES.index(req["template_id"]), ARMS.index(req["condition"])] = (
            np.asarray(row["values"]) - center
        ) / scale
    means = np.stack(
        [
            np.mean(
                [
                    (np.asarray(row["values"]) - center) / scale
                    for row in census["references"]
                    if row["painter_id"] == artist
                ],
                axis=0,
            )
            for artist in ARTISTS
        ]
    )
    return z, means, frozen


def _report(result):
    text = [
        "# Retrospective SD-Turbo common-response audit",
        "",
        "All 2,000 retained outputs, all four painters, all 16 fixed scenes "
        "and all 25 paired-seed blocks.",
        "The control already requests oil painting. No shared-family control is present.",
        "Previously analyzed pixels and historical references are reused. "
        "No prospective or independent replication is claimed.",
        "",
        "| View | C | L | N | T | C/N | beta | Pooled D | Scene D |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    def fmt(v):
        return "unavailable" if v is None else f"{v:.9g}"

    for name, row in result["families"].items():
        p, w = row["pooled"], row["within_scene"]
        text.append(
            "| "
            + name
            + " | "
            + " | ".join(
                fmt(v)
                for v in [p[k] for k in ("C", "L", "N", "T", "common_fraction", "beta", "D")]
                + [w["D"]]
            )
            + " |"
        )
    text += [
        "",
        "`analysis.json` retains both decomposition targets for every family, each scene, "
        "all six painter pairs, every delete-one-block result and finite sensitivity ranges.",
        "Ratios with nonpositive N and alignment/error with zero reference energy are "
        "unavailable with reasons. Signed estimates and ratios outside [0,1] are retained.",
        "The descriptive common-majority criterion is N > 0 and T > 0; it is not a "
        "significance test. No p-values or confidence intervals are supplied.",
        "",
        "Replay: `uv run --locked python -m latent_art_bench.painter_cross_cohort_v1 "
        "check --execute-real --inputs-sha256 " + result["inputs_sha256"] + "`.",
        "",
    ]
    return "\n".join(text)


def analyze(root=ROOT, *, execute_real=False, expected_inputs_sha256=None):
    root = Path(root)
    if any(
        (root / OUT / name).exists()
        for name in ("analysis.json", "REPORT.md", "result_receipt.json")
    ):
        raise FileExistsError("analysis already exists")
    z, means, _ = load_frozen(
        root, execute_real=execute_real, expected_inputs_sha256=expected_inputs_sha256
    )
    result = summarize(z, means)
    result["inputs_sha256"] = sha(root / OUT / "inputs.json")
    write_new(root / OUT / "analysis.json", result)
    write_new(root / OUT / "REPORT.md", _report(result))
    write_new(
        root / OUT / "result_receipt.json",
        dict(
            inputs_sha256=result["inputs_sha256"],
            analysis_sha256=sha(root / OUT / "analysis.json"),
            report_sha256=sha(root / OUT / "REPORT.md"),
        ),
    )
    return result


def check(root=ROOT, *, execute_real=False, expected_inputs_sha256=None):
    root = Path(root)
    z, means, _ = load_frozen(
        root, execute_real=execute_real, expected_inputs_sha256=expected_inputs_sha256
    )
    actual = summarize(z, means)
    actual["inputs_sha256"] = sha(root / OUT / "inputs.json")
    expected = read(root / OUT / "analysis.json")
    receipt = read(root / OUT / "result_receipt.json")
    if (
        actual != expected
        or (root / OUT / "REPORT.md").read_text() != _report(actual)
        or receipt
        != dict(
            inputs_sha256=actual["inputs_sha256"],
            analysis_sha256=sha(root / OUT / "analysis.json"),
            report_sha256=sha(root / OUT / "REPORT.md"),
        )
    ):
        raise ValueError("numeric or report replay failed")
    return dict(status="passed", blocks=25, generated=2000, families=4, pairs_per_family=6)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "analyze", "check"))
    parser.add_argument("--audit-report", type=Path)
    parser.add_argument("--execute-real", action="store_true")
    parser.add_argument("--inputs-sha256")
    args = parser.parse_args(argv)
    if args.command == "freeze":
        if args.audit_report is None:
            parser.error("freeze requires --audit-report")
        result = freeze(args.audit_report)
        print(
            json.dumps(
                dict(
                    status="frozen",
                    empirical_summaries_computed=False,
                    bindings=len(result["bindings"]),
                    inputs_sha256=sha(ROOT / OUT / "inputs.json"),
                )
            )
        )
    else:
        if not args.execute_real:
            parser.error("analyze/check require --execute-real after independent design/code audit")
        if args.inputs_sha256 is None:
            parser.error("analyze/check require the external --inputs-sha256 from freeze")
        result = (
            analyze(execute_real=True, expected_inputs_sha256=args.inputs_sha256)
            if args.command == "analyze"
            else check(execute_real=True, expected_inputs_sha256=args.inputs_sha256)
        )
        print(json.dumps(dict(status="passed", command=args.command, blocks=result.get("blocks"))))


if __name__ == "__main__":
    main()
