"""Arrange retained paintings and generated outputs for direct visual inspection.

This is manuscript presentation only. Selection uses existing scene/repeat IDs
and the completed source audit, never feature scores or generated appearance.
Run explicitly with retained pixels; ordinary paper builds reuse the saved PDFs.
"""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageOps

from latent_art_bench.painter_reference_quality_v1 import AUDITS, normalize_region
from latent_art_bench.painter_specificity_reference_v1.analysis import FRAME
from latent_art_bench.painter_specificity_v2 import study as s

PAPER = Path(__file__).parent
INSPECTION = s.ROOT / "reports/painter_specificity_review_v1/inspection.json"
MANIFEST = PAPER / "example_selection.json"
PAINTERS = ("Monet", "Sisley", "Pissarro", "Cézanne")
# Short labels for the retained references; full source titles remain in the manifest.
REFERENCE_TITLES = {
    "wikidata:Q10346982": "Rocks at\nPort-Goulphar",
    "wikidata:Q104774055": "The Loing and the\nMills of Moret",
    "wikidata:Q104773676": "River Oise near\nPontoise",
    "wikidata:Q19682454": "Along the Banks\nof the Marne",
}
MODELS = (
    "GPT Image 1",
    "GPT Image 2",
    "GPT Image 2.5\nFlare",
    "GPT Image 2.5\nSunburst",
    "Nano Banana 2",
    "FLUX.2 Max",
)
META = {"Creator": "Matplotlib", "CreationDate": None, "ModDate": None}


def save(path, data, check):
    if check:
        if path.read_bytes() != data:
            raise ValueError("example presentation differs: " + str(path))
    else:
        path.write_bytes(data)


def finish(fig, name, check):
    buf = io.BytesIO()
    fig.savefig(buf, format="pdf", metadata=META, dpi=300)
    plt.close(fig)
    data = buf.getvalue()
    save(PAPER / "figures" / name, data, check)


def verify(path, sha):
    if s.sha(path) != sha:
        raise ValueError("example source hash differs: " + str(path))


def draw(ax, rgb):
    ax.imshow(rgb, interpolation="antialiased", resample=True)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#bcbcbc")
        spine.set_linewidth(0.4)


def generated(ax, item):
    path = s.ROOT / item["path"]
    verify(path, item["sha256"])
    with Image.open(path) as image:
        draw(ax, ImageOps.exif_transpose(image).convert("RGB"))


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42})
    inspection = s.read(INSPECTION)
    requests = [
        r for r in s.rows(s.DATA / "requests.jsonl") if r["scene"] == 0 and r["repeat"] == 0
    ]
    expected = {r["id"] for r in requests}
    if {r["id"] for r in inspection["generated"]} != expected:
        raise ValueError("generated panel no longer matches the first scene/repeat")
    lookup = {(r["model"], r["arm"]): r for r in inspection["generated"]}
    audit = [r for path in AUDITS for r in s.read(path)["records"]]
    acquisitions = {r["work_id"]: r for r in s.rows(s.ACQUISITIONS)}
    frame = {r["work_id"]: r for r in s.rows(FRAME)}
    manifest = {
        "selection": {
            "generated": (
                "first declared scene and first repeat, all six models; "
                "all six arms in each model row of the main gallery; "
                "free/generic arms also retained in a standalone control panel"
            ),
            "references": (
                "lexicographically first reference work ID per painter with "
                "audited visual class water_organized and recorded public-domain "
                "status; use the already audited painting-region box"
            ),
            "timing": (
                "post-result presentation; no selection by generated appearance or feature score"
            ),
            "interpretation": (
                "historical reproductions are comparison examples, "
                "not generator inputs or composition-matched targets"
            ),
        },
        "scene": inspection["scene"],
        "inputs": {
            str(p.relative_to(s.ROOT)): s.sha(p)
            for p in (INSPECTION, *AUDITS, FRAME, s.ACQUISITIONS)
        },
        "references": [],
        "generated": inspection["generated"],
    }
    fig, axes = plt.subplots(7, 6, figsize=(6.7, 7.4))
    for a, artist in enumerate(s.ARTISTS):
        candidates = sorted(
            (
                r
                for r in audit
                if r["role"] == "reference"
                and r["painter_id"] == artist
                and r["visual_class"] == "water_organized"
                and "public domain" in acquisitions[r["image_id"]]["licence"].lower()
            ),
            key=lambda r: r["image_id"],
        )
        ref = candidates[0]
        item = acquisitions[ref["image_id"]]
        path = s.ROOT / item["raw_path"]
        verify(path, ref["raw_sha256"])
        rgb, normalized = normalize_region(path, ref["region_box"])
        draw(axes[0, a], rgb)
        display_title = REFERENCE_TITLES[ref["image_id"]]
        axes[0, a].set_xlabel(display_title, fontsize=6, labelpad=2, linespacing=1.05)
        manifest["references"].append(
            dict(
                id=ref["image_id"],
                artist=artist,
                title=frame[ref["image_id"]]["labels"],
                display_title=display_title,
                path=item["raw_path"],
                sha256=ref["raw_sha256"],
                url=item["url"],
                licence=item["licence"],
                region_box=ref["region_box"],
                display=normalized,
            )
        )
        for m, title in enumerate(s.TITLES):
            generated(axes[m + 1, a], lookup[title, artist])
    for a, arm in enumerate(("free", "generic"), start=4):
        axes[0, a].set_axis_off()
        for m, title in enumerate(s.TITLES):
            generated(axes[m + 1, a], lookup[title, arm])
    for m, name in enumerate(("Reference\nreproduction", *MODELS)):
        axes[m, 0].set_ylabel(name, fontsize=8, rotation=0, ha="right", va="center", labelpad=10)
    fig.subplots_adjust(left=0.18, right=0.995, bottom=0.01, top=0.94, hspace=0.11, wspace=0.10)
    for a, label in enumerate((*PAINTERS, "Artist-free", "Generic\npainting")):
        box = axes[0, a].get_position()
        fig.text((box.x0 + box.x1) / 2, 0.953, label, ha="center", va="bottom", fontsize=8)
    left = axes[0, 3].get_position().x1
    right = axes[0, 4].get_position().x0
    fig.add_artist(
        plt.Line2D(
            [(left + right) / 2] * 2,
            [0.01, 0.99],
            transform=fig.transFigure,
            color="#bcbcbc",
            linewidth=0.6,
        )
    )
    finish(fig, "specificity_original_generated.pdf", args.check)

    fig, axes = plt.subplots(2, 6, figsize=(6.7, 2.55))
    for m, title in enumerate(s.TITLES):
        for a, arm in enumerate(("free", "generic")):
            item = lookup[title, arm]
            generated(axes[a, m], item)
            axes[a, m].set_xlabel(item["id"], fontsize=5.5, labelpad=2)
        axes[0, m].set_title(MODELS[m].replace("GPT Image 2.5", "2.5"), fontsize=7, pad=5)
    for a, name in enumerate(("Artist-free", "Generic\npainting")):
        axes[a, 0].set_ylabel(name, fontsize=7.5, rotation=0, ha="right", va="center", labelpad=8)
    fig.subplots_adjust(left=0.13, right=0.995, bottom=0.08, top=0.81, hspace=0.21, wspace=0.12)
    finish(fig, "specificity_control_examples.pdf", args.check)
    save(MANIFEST, (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(), args.check)
    print(
        "Verified" if args.check else "Rendered",
        "28 original/named and 12 control examples; all 40 source hashes checked.",
    )


if __name__ == "__main__":
    main()
