"""Render the complete fixed covariance scenarios, without changing frozen science."""

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "reports/painter_repeat_covariance_v1"
OUTPUT = ROOT / "paper/icml_covariance_results.tex"
ANALYSIS_SHA = "e5031ccad955b289b0d8dec110e8ee6b2ec39b43dfd8a6f2e150cc1dea1ce0c9"
INPUT_SHA = "43a44d769700b1a8fd0122d9a4e4d8e34726c121313641d892aa85b843bf2346"
GRID = [0, .1, .25, .5, .75]
TITLES = ["GPT Image 1", "GPT Image 2", "Flare", "Sunburst", "Nano Banana 2", "FLUX.2 Max"]


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(actual, expected):
    require(math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), "numeric disagreement")


def load():
    require(sha(BASE / "analysis.json") == ANALYSIS_SHA, "frozen analysis changed")
    require(sha(BASE / "inputs.json") == INPUT_SHA, "frozen input receipt changed")
    data = json.loads((BASE / "analysis.json").read_text())
    inputs = json.loads((BASE / "inputs.json").read_text())
    for path, expected in inputs["bindings"].items():
        require(sha(ROOT / path) == expected, f"bound input changed: {path}")
    require(data["inputs_sha256"] == INPUT_SHA and data["rho_grid"] == GRID, "protocol mismatch")
    require(len(data["models"]) == 6 and len(data["pairs"]) == 15, "incomplete model/pair census")
    for model in data["models"]:
        require(len(model["grid"]) == 5, "incomplete grid")
        for rho, row in zip(GRID, model["grid"]):
            require(row["rho"] == rho, "rho order")
            close(row["implied_bias"], rho / (1 - rho) * model["q"])
            close(row["adjusted_d"], model["d"] - row["implied_bias"])
            require(row["negative_adjusted_d"] == (row["adjusted_d"] < 0), "negative flag")
    for pair, (a, b) in zip(data["pairs"], itertools.combinations(data["models"], 2)):
        require((pair["model_a"], pair["model_b"]) == (a["model"], b["model"]), "pair order")
        close(pair["delta_d"], a["d"] - b["d"])
        close(pair["delta_q"], a["q"] - b["q"])
        for rho, row in zip(GRID, pair["grid"]):
            close(row["adjusted_difference"], pair["delta_d"] - rho / (1-rho) * pair["delta_q"])
        c = pair["crossing"]
        if c["rho"] is not None:
            close(pair["delta_d"] - c["rho"] / (1-c["rho"]) * pair["delta_q"], 0)
    return data


def number(value):
    return f"${value:.3f}$"


def render(data):
    lines = [
        "% Generated from complete frozen covariance results; no new inference.",
        f"% analysis_sha256: {ANALYSIS_SHA}", f"% inputs_sha256: {INPUT_SHA}",
        r"\subsection{Complete covariance scenario tables}",
        r"Three of 15 pairs have an interior positive point-order crossing: GPT Image 1 "
        r"versus GPT Image 2 ($\rho=.245650$), GPT Image 1 versus FLUX ($.688029$), "
        r"and Nano Banana 2 versus FLUX ($.250751$). The remaining 12 have no "
        r"positive interior crossing under this particular common-ratio assumption. "
        r"There are no initial ties. These values do not estimate actual dependence.",
        r"\par",
        r"\begin{table}[!htbp]",
        r"\caption{All six primary-D scenario curves. The fixed trace correlation "
        r"$\rho$ is an assumption, not a data estimate; $q$ is the observed normalized "
        r"repeat-difference statistic. The implied bias at each column is "
        r"$\rho q/(1-\rho)$, subtracted from the original $D$ at $\rho=0$. "
        r"Negative adjusted points are retained, not interpreted as negative physical "
        r"squared errors. Flare and Sunburst denote the GPT Image 2.5 configurations.}",
        r"\label{tab:covariance-models}",
        r"\centering\small\setlength{\tabcolsep}{5pt}",
        r"\begin{tabularx}{\linewidth}{@{}Xrrrrrr@{}}\toprule",
        r"Configuration & $q$ & $D(0)$ & $D(.10)$ & $D(.25)$ & $D(.50)$ & $D(.75)$\\\midrule",
    ]
    for title, model in zip(TITLES, data["models"]):
        lines.append(" & ".join([title, number(model["q"]), *[
            number(row["adjusted_d"]) for row in model["grid"]
        ]]) + r"\\")
    lines += [
        r"\bottomrule\end{tabularx}\end{table}",
        r"\begin{table}[!htbp]",
        r"\caption{All 15 paired point curves, first configuration minus second. "
        r"Positive values mean larger scenario error for the first. The last column "
        r"gives the analytic interior positive crossing, including values above the "
        r"displayed grid; -- means no such crossing. These are neither significance "
        r"thresholds nor uncertainty bounds; no original intervals are shifted.}",
        r"\label{tab:covariance-pairs}",
        r"\centering\small\setlength{\tabcolsep}{4pt}",
        r"\begin{tabularx}{\linewidth}{@{}Xrrrrrr@{}}\toprule",
        r"Pair & $\rho=0$ & $.10$ & $.25$ & $.50$ & $.75$ & Crossing $\rho$\\\midrule",
    ]
    for (a, b), pair in zip(itertools.combinations(TITLES, 2), data["pairs"]):
        threshold = pair["crossing"]["rho"]
        cells = [f"{a} $-$ {b}", *[number(row["adjusted_difference"]) for row in pair["grid"]],
                 "--" if threshold is None else f"${threshold:.6f}$"]
        lines.append(" & ".join(cells) + r"\\")
    lines += [
        r"\bottomrule\end{tabularx}\end{table}",
        r"\FloatBarrier",
        r"The 26 constructed/provenance tests verify the expectation identity with "
        r"unequal repeat variances, centering, repeat swapping, crossing and tie "
        r"cases, common covariance versus common correlation, and negative estimates. "
        r"Both primary $D$ and direct $q$ match the preserved analyses before the "
        r"new scenario calculation. The versioned record retains all 84 scene "
        r"values per statistic, grid biases and unrounded crossings. Exact replay: "
        r"\texttt{uv run --locked python -m "
        r"latent\_art\_bench.painter\_repeat\_covariance\_v1 check --execute-real}.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render(load())
    if args.check:
        require(OUTPUT.read_text() == content, "generated covariance table differs")
        print("Covariance tables: all 6 curves and 15 pairs verified; exact TeX replay passed.")
    else:
        OUTPUT.write_text(content)


if __name__ == "__main__":
    main()
