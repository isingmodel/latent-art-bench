"""Replay Study 2 primary inference from three hash-bound compact inputs.

Run ``uv run --locked --extra analysis python paper/replay_palette.py``.
This numerical replay reads only the saved schedule, chroma table and primary
results. It does not verify transport, source pixels, feature extraction, or
public availability. The complete archive-integrity checks remain separate.
Optional figures display post-result block contrasts, not independence tests.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from statistics import mean, variance

from latent_art_bench.painter_responsiveness_v1.design import validate_schedule
from latent_art_bench.painter_responsiveness_v1.inference import analyze_factorial

ROOT = Path(__file__).resolve().parents[1]
RUN = "prv2-oauth-recovery-20260908"
SCHEDULE = f"data/manifests/painter_responsiveness_v2/{RUN}/planned_requests.jsonl"
CHROMA = f"reports/painter_responsiveness_v2/{RUN}/experiment/generated_chroma.csv"
PRIMARY = f"reports/painter_responsiveness_v2/{RUN}/experiment/primary.csv"
INPUTS = {
    SCHEDULE: "8d47daa68f74a72fc812c5b54b47bc9b54cc5c08f0ae7ff37c7fa8b573cfff7a",
    CHROMA: "175d0d964cdfa6c0968d5f4c28acd83ed1f992d7297ebca08dd86cb66cf3495e",
    PRIMARY: "6476d8f24e36eae1b5357811a8971a5510ad9f620acd577ce49565b0c7db1d80",
}
PIPELINES = ("primary512", "resolution256", "jpeg90_512")
SCENES = {
    "water_river": ("River", "#0072B2", "o"),
    "water_bend": ("River bend", "#D55E00", "s"),
    "built_village": ("Village", "#009E73", "^"),
    "built_houses": ("Houses", "#CC79A7", "D"),
    "land_fields": ("Fields", "#E69F00", "v"),
    "land_garden": ("Garden", "#56B4E9", "P"),
}


def load_inputs(root=ROOT):
    """Read only these three compact files; reject changed retained bytes."""
    text = {}
    for relative, expected in INPUTS.items():
        raw = (Path(root) / relative).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f"retained compact input changed: {relative}")
        text[relative] = raw.decode("utf-8")
    schedule = [json.loads(line) for line in text[SCHEDULE].splitlines()]
    chroma = list(csv.DictReader(io.StringIO(text[CHROMA])))
    primary = []
    for row in csv.DictReader(io.StringIO(text[PRIMARY])):
        primary.append({
            key: value if key in ("contrast", "inference_status") else
            value == "True" if key == "reject_holm" else json.loads(value)
            for key, value in row.items()
        })
    return schedule, chroma, primary


def analyze_inputs(schedule, chroma, saved_primary, *, primary_comparator=None):
    """Validate identities and frozen inference; default to exact primary parity.

    A release adapter may supply its explicitly recorded platform comparator.
    Schedule, chroma and ordered-block validation are unaffected.
    """
    design = validate_schedule(schedule)
    if design["requests"] != 192 or design["repetitions"] != 4:
        raise ValueError("the primary replay requires exactly 192 slots and four repetitions")
    if set(design["templates"]) != set(SCENES):
        raise ValueError("the six primary scene identities changed")
    planned = {row["request_id"]: row for row in schedule}
    values = {}
    for row in chroma:
        key = row["request_id"], row["pipeline"]
        if key[0] not in planned or key[1] not in PIPELINES or key in values:
            raise ValueError("unknown or duplicate chroma identity")
        request = planned[key[0]]
        for field in ("arm", "polarity", "template_id", "content_class", "repetition"):
            actual = int(row[field]) if field == "repetition" else row[field]
            if actual != request[field]:
                raise ValueError(f"chroma/schedule identity mismatch: {field}")
        value = float(row["value"])
        if row["status"] != "measured" or not math.isfinite(value):
            raise ValueError("every primary-run chroma value must be measured and finite")
        values[key] = value
    if set(values) != {(rid, pipeline) for rid in planned for pipeline in PIPELINES}:
        raise ValueError("missing planned chroma value")
    outcomes = [dict(request_id=rid, status="measured", value=values[rid, "primary512"])
                for rid in planned]
    result = analyze_factorial(schedule, outcomes, alpha=0.05, manipulation_margin=0)
    primary_matches = (result["primary"] == saved_primary if primary_comparator is None else
                       primary_comparator(result["primary"], saved_primary))
    if not primary_matches:
        raise ValueError("primary inference differs from retained results")
    blocks = []
    for start in range(0, len(schedule), 8):
        slots = schedule[start:start + 8]
        cell = {(s["arm"], s["polarity"]): values[s["request_id"], "primary512"]
                for s in slots}
        generic = cell["generic", "vivid"] - cell["generic", "muted"]
        blocks.append(dict(
            block_order=start // 8 + 1, first_sequence=start,
            block_id=slots[0]["block_id"], template_id=slots[0]["template_id"],
            repetition=slots[0]["repetition"],
            **{p + "_interaction": cell[p, "vivid"] - cell[p, "muted"] - generic
               for p in ("monet", "cezanne")},
        ))
    diagnostics = {}
    for painter, primary in zip(("monet", "cezanne"), result["primary"]):
        grouped = [[b[painter + "_interaction"] for b in blocks if b["template_id"] == scene]
                   for scene in design["templates"]]
        variances = [variance(group) for group in grouped]
        if (not all(math.isclose(mean(group), saved, rel_tol=1e-12, abs_tol=1e-14)
                    for group, saved in zip(grouped, primary["template_estimates"]))
                or not math.isclose(sum(variances) / (6**2 * 4),
                                    primary["standard_error"]**2, rel_tol=1e-12, abs_tol=1e-14)):
            raise ValueError("ordered-block means or variance differ from primary inference")
        diagnostics[painter] = dict(
            negative_blocks=sum(b[painter + "_interaction"] < 0 for b in blocks),
            scene_variance_shares=dict(zip(design["templates"],
                                           (v / sum(variances) for v in variances))),
        )
    return dict(primary=result["primary"], primary_covariance=result["primary_covariance"],
                blocks=blocks, diagnostics=diagnostics)


def replay(root=ROOT):
    return analyze_inputs(*load_inputs(root))


def figure_bytes(result):
    """Render every block in dispatch order; no fit or independence diagnostic."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    with plt.rc_context({
        "font.family": "DejaVu Sans", "font.size": 8.2, "axes.labelsize": 8.2,
        "axes.titlesize": 9, "legend.fontsize": 8, "axes.spines.top": False,
        "axes.spines.right": False, "axes.linewidth": 0.6, "pdf.fonttype": 42,
        "pdf.compression": 6, "savefig.facecolor": "white",
    }):
        fig, axes = plt.subplots(2, 1, figsize=(160 / 25.4, 4.8), sharex=True, sharey=True)
        all_values = [b[p + "_interaction"] for b in result["blocks"]
                      for p in ("monet", "cezanne")] + [0]
        lo, hi = min(all_values), max(all_values)
        padding = max((hi - lo) * 0.1, 0.05)
        for ax, painter, primary in zip(axes, ("monet", "cezanne"), result["primary"]):
            ax.axhline(0, color="#777777", linewidth=0.8, linestyle=(0, (3, 3)))
            ax.axhline(primary["estimate"], color="#252525", linewidth=1,
                       linestyle=(0, (6, 2)))
            for scene, (_label, color, marker) in SCENES.items():
                rows = [b for b in result["blocks"] if b["template_id"] == scene]
                ax.scatter([b["block_order"] for b in rows],
                           [b[painter + "_interaction"] for b in rows],
                           c=color, marker=marker, s=29, zorder=3)
            ax.set_title("Monet" if painter == "monet" else "Cézanne", loc="left")
            ax.set_ylim(lo - padding, hi + padding)
            ax.set_xlim(0.4, 24.6)
            ax.set_xticks([1, 4, 8, 12, 16, 20, 24])
            ax.grid(axis="x", color="#ececec", linewidth=0.6)
            ax.set_axisbelow(True)
            ax.set_ylabel("Named − generic response\n(development IQR units)")
        axes[-1].set_xlabel("Collection block order")
        handles = [Line2D([], [], color=c, marker=m, linestyle="", label=label, markersize=5)
                   for label, c, m in SCENES.values()]
        fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False,
                   bbox_to_anchor=(0.57, 1), columnspacing=2)
        fig.subplots_adjust(left=0.16, right=0.985, top=0.82, bottom=0.11, hspace=0.42)
        buffer = io.BytesIO()
        fig.savefig(buffer, format="pdf", metadata={
            "Creator": "Matplotlib", "CreationDate": None, "ModDate": None,
        })
        plt.close(fig)
    return buffer.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    option = parser.add_mutually_exclusive_group()
    option.add_argument("--figure", type=Path, help="write the ordered-block PDF")
    option.add_argument("--check-figure", type=Path,
                        help="byte-check an existing ordered-block PDF")
    args = parser.parse_args()
    result = replay()
    print("Verified 192 primary outcomes, 24 ordered blocks and both retained primary results.")
    print("Numerical replay only; transport, pixels and feature extraction are not verified.")
    for row in result["primary"]:
        print(f"{row['contrast']}: estimate={row['estimate']:.9f}, "
              f"family_interval={row['family_interval']}, Holm p={row['p_holm']:.9f}")
    for painter, diagnostic in result["diagnostics"].items():
        shares = ", ".join(f"{s}={v:.4%}" for s, v in diagnostic["scene_variance_shares"].items())
        print(f"Post-result {painter}: {diagnostic['negative_blocks']}/24 negative blocks; "
              f"scene variance shares: {shares}")
    if args.figure or args.check_figure:
        raw = figure_bytes(result)
        if args.check_figure:
            if args.check_figure.read_bytes() != raw:
                raise ValueError("ordered-block figure differs")
            print(f"Verified {args.check_figure}")
        else:
            args.figure.parent.mkdir(parents=True, exist_ok=True)
            args.figure.write_bytes(raw)
            print(f"Rendered {args.figure}")


if __name__ == "__main__":
    main()
