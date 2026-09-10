# Public numerical reproduction package

Painter Naming and the Distributional Gap Between Generated Images and Original Paintings.

This history-free package reproduces computations from retained numerical measurements.
It does not regenerate images, extract image features, validate perception, audit the
private transport archive, or establish independently collected replication.
`COVERAGE.json` maps every manuscript result family to its actual replay scope.

Use the tested Python 3.13.11 and uv 0.9.28, then run from this extracted directory:

```sh
uv sync --locked --extra analysis --python 3.13.11
uv run --locked python tools/paper_release.py check --release-id pprv1-20260910 --isolated
```

The full check recomputes the original statistical functions and compares their results
with hash-bound retained outputs. It checks every included manuscript figure PDF.
Exact float/PDF byte comparisons may expose platform differences: the receipts record
the numerical runtime. A failure must be investigated; do not change a bound hash or relax
a scientific test to make it pass. Hosted CI uses `--portable-numeric`, a prospectively
fixed 1e-10 absolute/relative tolerance for finite floating results, with exact structures,
identities, counts, seeds, decisions and p-values. Figure byte differences on that path
are reported as platform differences, not falsely called byte-identical reproduction.
Dependencies may be downloaded during installation. During numerical analysis, a Python
audit-hook guard blocks socket creation/use, subprocesses and file access outside this
tree/Python runtime. This is an ordinary Python I/O guard, not an OS sandbox or a
hostile-code containment boundary. Blocked attempts are retained in the check receipt.

The checker prints a result per computation and writes its receipt under
`reports/paper_reproducibility_v1/pprv1-20260910/`. Use `--components study1,palette` for
an explicitly partial check or `--output .replayed-results` to inspect recomputed JSON.
Full exploration and Stage A checks may take several minutes.

The original local source commit in the manifest is provenance metadata, not a claim
that the old commit or private archive is publicly available. `RELEASE_MANIFEST.json`
and `SHA256SUMS` enumerate the exact files. Release source copies preserve the original
scientific implementations. See `NUMERICAL_DATA_LICENSE.md`, `LICENSE` and `CITATION.cff`.

The included design contracts and local Git freezes document prospective local
procedures; they are not registrations in an independent preregistration registry.
`data/manifests/paper_reproducibility_v1/pprv1-20260910/source_catalog.json` supplies
recorded source URLs, work IDs, file identities and license metadata. These links
are not guarantees of current image access or permission to redistribute pixels.

The exact prompt sources are:

- Four-painter exploratory scenes: `data/manifests/painter_feature_generation_v1/prompt_library.json`
- Study 1 detailed and short scenes: `configs/painter_distribution_study_v1/research.json`
- Study 2 scenes and style/palette clauses: `configs/painter_responsiveness_v2/study.json`

The unchanged `painter_prompt_study_v1.prompts.build_library` reconstructs all 240
exploratory method/painter/control strings from the 16-scene library. The two
controlled inventories also supply the scene text reused by the temporal follow-up.

Publication and anonymous-download verification are recorded separately on the
[versioned release](https://github.com/isingmodel/latent-art-bench/releases/tag/pprv1-20260910).
The manifest's preparation status describes artifact build time, not current public
access. This archive does not by itself establish that publication or hosted verification
has occurred; consult the versioned release and its separate verification receipt.
