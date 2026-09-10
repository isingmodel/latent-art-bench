# Strict Ubuntu replay: failed numerical qualification comparison

The single [hosted attempt](https://github.com/isingmodel/latent-art-bench/actions/runs/34474649751) ended **failed**. Archive verification, installation, all **75 public tests** and the final inventory check passed. The numerical command failed at the complete 27-cell qualification comparison; **the observed E/Q, interval and report replay was not reached and receives no Ubuntu reproduction credit**.

## Identity and actual scope

Run `34474649751`, attempt **1**, was a manual `workflow_dispatch` at commit `f38da21b7ea1c49b5cb5c1678a8410c65df19733`. The fetched published workflow matches SHA-256 `cee10c0a9c65d2300a3815f9a1164ab2f267623b61d3283aa072339dbd0e4831`; it is outside the unchanged numerical archive. The driver ran from 12:04:30.246540 to 12:07:55.059674 UTC on 2026-09-10. GitHub reports job completion at 12:07:58 UTC.

Ubuntu 24.04.5 / image `20260907.300.1` reported Linux x86_64, glibc 2.39, Python **3.13.11**, uv **0.9.28**, NumPy **2.5.2** and SciPy **1.18.1**. NumPy's configuration reports OpenBLAS 0.3.34.0.0. These runtime observations do not by themselves identify the numerical cause.

The public download was the same **3,059,166-byte**, **74-regular-file** archive used for the successful local replay, SHA-256 `8688085fe001e6b45ca34f6d39a5979e3e762a2678cd5ecb8169a698defb4eb6`. Its detached checksum and both manifest fingerprints agree with [LOCAL.json](LOCAL.json). Isolated stdlib `-I -S` verification passed before installation; the post-test `-I -S -B` runtime inventory also passed with all 74 payload files.

| Recorded command | Exit | Seconds |
| --- | ---: | ---: |
| `preinstall-verify` | 0 | 2.020 |
| `install-uv` | 0 | 1.880 |
| `uv-version` | 0 | 0.005 |
| `locked-install` | 0 | 1.952 |
| `numerical-runtime` | 0 | 0.468 |
| `numerical-check` | 1 | 31.015 |
| `public-tests` | 0 | 164.728 |
| `post-test-inventory` | 0 | 2.020 |

The test log reports **75 passed in 163.33 s**, with no skips. This does not replace the failed historical-data replay. Optional tests exercise artificial fixtures and do not demonstrate that the real observed comparison was reached by the numerical command.

## Exact failure and evidentiary limit

The complete numerical command returned 1 after **31.014913 s**, with empty stdout and this terminal exception:

```text
File "tools/paper_map_validation_release.py", line 679, in check
ValueError: complete 27-cell numerical qualification replay differs
```

The immutable checker first computes `precision.qualify(precision.v1.load_proxy(root))`, then compares that result with the stored qualification. It raises here before the qualification report comparison and before `observed_replay`. The comparison applies the declared 1e-10 absolute/relative floating tolerance while retaining exact identities, counts, seeds, decisions and reconstructed support hashes. The retained error does **not** identify the differing comparison leaf or provide the reconstructed result. Therefore this audit cannot establish that support hashes alone failed, that all non-hash values agreed, or that the failure was harmless floating-point drift. It also cannot diagnose a scientific implementation defect from this record. Strict Ubuntu numerical portability is unverified by this attempt; same-Mac exact replay remains separately recorded.

No rerun, cancellation, amended workflow, tolerance change, new numerical output writer, image generation or feature extraction was performed by this audit. The failed disposition is retained unchanged. Public collection eligibility remains an attestation from private terminal verification; this hosted run cannot authenticate absent pixels, service identity, costs, timing or acquisition, nor establish interval coverage, perceptual validity or separate-investigator replication.

## Receipt and log authentication

[HOSTED.json](HOSTED.json) is a **byte-for-byte copy** of the actual artifact receipt, not an edited reconstruction. Its original hosted interpreter path is preserved. Artifact `10151075031` contains 18 files and is retained locally as `tmp/paper-map-validation-release/ubuntu-audit-20260910-01/artifact.zip`; its downloaded **6,884 bytes** match both the GitHub API digest and upload log. I verified all **16** stdout/stderr hashes, the detached checksum, workflow/run identity, exact artifact inventory and equality between the receipt printed in the full job log and the artifact receipt. The raw command logs, full 297-line job log and API records remain in the ignored QA directory; the receipt binds the individual logs.

I am maintainer-run LLM reviewer 2, with implementation involvement in v2 operational code and earlier geometry/centering/clause workflows. I reviewed the exporter and performed the separate local replay; I did not implement the public exporter or operate a second hosted run. This is a completion/log audit with disclosed involvement, not an independent human review or a new score.

| Retained file | SHA-256 |
| --- | --- |
| `tmp/paper-map-validation-release/ubuntu-audit-20260910-01/reproduce.yml` | `cee10c0a9c65d2300a3815f9a1164ab2f267623b61d3283aa072339dbd0e4831` |
| `tmp/paper-map-validation-release/ubuntu-audit-20260910-01/artifact.zip` | `ecd51b281689d3baac4c0ec079f22f7fcf6e185ad05534fd28cc61b810a9b1a6` |
| `tmp/paper-map-validation-release/ubuntu-audit-20260910-01/artifact/HOSTED.json` | `80d52e66b05fd0e45191d4094cee6b369fd39af93642b818b764f693e5eb1afc` |
| `tmp/paper-map-validation-release/ubuntu-audit-20260910-01/run-api.json` | `e05393a52de55fbaacc177c2b6edddfef861d19243f217f689c219ee709e8d90` |
| `tmp/paper-map-validation-release/ubuntu-audit-20260910-01/artifacts.json` | `232c444afd3e50025bcf165ca3f951365036288f4ef67f0a2fb9b94fd5e2a3a9` |
| `tmp/paper-map-validation-release/ubuntu-audit-20260910-01/full-run.log` | `20b5dfd341dce8f99450dd6252e9223b08100e6d3485726ea242cb682608b60a` |
| `tmp/paper-map-validation-release/ubuntu-audit-20260910-01/artifact/numerical-check.stderr.log` | `289a5eae287e2673f070472b974ea64f348a21129bc1392d7616f0079631680f` |
| `tmp/paper-map-validation-release/ubuntu-audit-20260910-01/artifact/public-tests.stdout.log` | `259fc4376a4f893f3277c97f6f63374838f1fbaa10cab230cf1b093f96c790c9` |
| `tmp/paper-map-validation-release/ubuntu-audit-20260910-01/artifact/numerical-runtime.stdout.log` | `6a6e9cfbfd2c9760b5d563a8aaf7a3dd7925f313c1f01ea3d6803f37bc6ddc36` |
