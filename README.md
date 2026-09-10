# Painter naming geometry addendum: painter-naming-geometry-20260910

Final local build. This history-free numerical addendum contains the English manuscript,
its nine figure PDFs, and both post-result naming analyses. It reruns only
`painter_naming_geometry_v1` and `painter_naming_centering_v1` from retained
compact measurements. It does not regenerate or independently measure images.

Historical paper results require the immutable predecessor release
[pprv1-20260910](https://github.com/isingmodel/latent-art-bench/releases/tag/pprv1-20260910).
This addendum supplements that release; it does not claim to replay every
historical paper result. Historical hashes and input `origins` are provenance;
their original archives are intentionally not copied here.

## Verify and replay

In a fresh extracted directory, verify the package before installing:

```sh
python tools/paper_geometry_release.py verify --root .
uv sync --locked --extra analysis --extra dev
uv run --locked python -m latent_art_bench.painter_naming_geometry_v1 verify
uv run --locked python -m latent_art_bench.painter_naming_centering_v1 verify
uv run --locked pytest -q --import-mode=importlib \
  tests/painter_naming_geometry_v1 tests/painter_naming_centering_v1
```

Use the two module commands above; the original project-wide console command
depends on historical source outside this compact addendum. Installation may
download the locked software dependencies. Scientific replay reads local data
only and preserves the frozen inputs and terminal outputs. A TeX installation
is needed only to rebuild the manuscript PDF; its nine figures are included.

`ADDENDUM_MANIFEST.json` records every payload hash and source/freeze provenance;
`SHA256SUMS` also hashes that manifest. The external archive checksum authenticates
bytes relative to a trusted release checksum, not the underlying observations.
Git history, raw pixels, artwork, model weights, source checkouts, authentication
material, and Korean manuscript files are excluded. Capture validity and the
finite-panel, post-result scope remain as stated in the protocols and paper.
Reviews and implementation assistance were maintainer-run LLM work, not
institutionally independent review. No external publication is performed by
this local packaging tool.
