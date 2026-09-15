# Portable editorial review archive

The committed record retains the fixed rubric, all 99 original reviewer JSON
files across 33 rounds, every aggregate and revision decision, six completed
external assessments (including their exact final response text), the cancelled
requests, source/PDF digests, prompts, provenance and validation receipts. Raw
opinions and scores are unchanged. Schema aliases and the two Claude delimiter
repairs remain documented beside the preserved raw responses.

The original stopping rule was met by round 33. Later Claude/Astra assessments
are separate user-requested reviews, and their scores remain tied to their
specific PDF hashes. The current paper may have been edited again; neither an
old score nor a past “canonical matches” receipt certifies later manuscript bytes.

## Audit from a fresh checkout

```sh
python3 scripts/audit_paper_reviews.py
```

This dependency-free, read-only audit verifies the rubric hash, 33 snapshot/score
bindings, all 99 raw-review digests, unique reviewer IDs, quarter-point dimensions,
all aggregate arithmetic, six external response extractions and their documented
normalization, model/session provenance consistency, paired-review lineage, and
cancellation exclusions. It does not contact a model or need ignored snapshots,
page images, CLI traces, the original absolute checkout path, or credentials.
The digest inventory below also binds the preserved external record bytes.

```sh
python3 scripts/audit_paper_reviews.py --local-snapshots
```

The optional mode additionally checks every available frozen manuscript file
against its recorded digest and the execution artifacts below against their
size and SHA-256. Missing local artifacts are listed as missing, not passed;
partially present or changed snapshots fail. Historical absolute snapshot paths
are relocated beneath this checkout's `tmp/`. `--repo-root /path/to/checkout`
can select a different checkout for either mode.

Portable checks establish consistency of the retained records. They do not
reperform visual inspection, authenticate provider claims, establish scientific
validity or recreate missing historical PDFs. Earlier detailed transport/visual
checks remain dated host receipts; their raw evidence can be checked locally
when available. Astra's page inspection is self-reported. Claude's successful
page reads were verified from its CLI traces when those receipts were written.

## Local execution evidence

Image-bearing Claude CLI JSONL traces, empty stderr logs and machine-specific
Astra runners are narrowly ignored by `.gitignore`. Request bodies, SSE streams,
completed response envelopes and frozen PDF/image snapshots already beneath
`tmp/` remain ignored. No file is deleted or rewritten by this cleanup. The
request bodies contain full manuscript/images; the runners contain machine-local
paths. They are execution evidence rather than portable review results.

The four Claude traces alone total 61,912,010 bytes. Excluding them and the local
runners reduces the approximately 63.50 MB review folder to approximately
1.57 MB of portable records including this inventory (uncompressed, before later
final-update documentation). Git compression may differ. The inventory describes
the files present at cleanup, including the deliberately cancelled `_02` runs;
those runs contribute no score. A terminal status retained before cancellation
is interpreted together with `CANCELLED.json`.

The sole JSON block below is read by the audit script. Paths are repository
relative. Digests preserve identity without requiring private/local bytes in Git.

At cleanup, both audit modes passed: 33 rounds, 99 original reviewers, six
completed external assessments, 36 available frozen manuscript snapshots and
24 local execution artifacts. A separate copy containing only the portable
record files also passed without any local snapshots or transports. Deliberately
altering a copied round mean, an original raw review and an external raw review
each caused the audit to fail. Original archive files were not changed by these
checks. Ruff and `git diff --check` passed for the cleanup changes.

```json
{
  "archive_version": 1,
  "portable_external_records": {
    "reports/paper_editorial_review_v1/astra_xhigh_review_01/HOST_EXTRACTION_ERROR.json": {
      "bytes": 986,
      "sha256": "edea20d9b780e10edf4f2d49b65666a0b65807058a23d1f0e934d745e91cc915"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_01/PROMPT.txt": {
      "bytes": 1591,
      "sha256": "e435a1e07f3a291e7f4e11d136af80c025d16031114db0699a954fa0e5af0814"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_01/PROVENANCE.json": {
      "bytes": 5461,
      "sha256": "dc252638f7c385746a166d0239c4431af03ad0e8af85d11490162f6840533580"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_01/RUN_STATUS.json": {
      "bytes": 1341,
      "sha256": "2bad40efd582e0216d0906ab59ac48b565d266cca2ec6db8b57a6a49e48d9381"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_01/VALIDATION.json": {
      "bytes": 1198,
      "sha256": "73b0f122c7d3264372ab0469c2ccdf012e0a06e5d63b16e787b987ef876e5397"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_01/response.txt": {
      "bytes": 8154,
      "sha256": "f3c520aac789c5aace9b15c84d8c9c9d1bf6a21cf25b722d36e36e5efb86f290"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_01/reviewer.json": {
      "bytes": 8292,
      "sha256": "b8066c9c4986d5daf6b3fb8fda5dc5e586ef63d0bbc600e2a4ffa48da6d4afcb"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_02/CANCELLED.json": {
      "bytes": 466,
      "sha256": "6d297a5ec835568f6c6cebca19d20d9837612a1b96cd131954cdb04989fd5b33"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_02/PROMPT.txt": {
      "bytes": 1591,
      "sha256": "c7e36d6e2b31730ca4988c29df6596d7e1dab60f973267375bcaff61fb86d06d"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_02/PROVENANCE.json": {
      "bytes": 2689,
      "sha256": "693bc58db7262c9a80a6943eb5f0fc641a5e17781e8f8a2a8b8fa9f3b3d21f7f"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_02/RUN_STATUS.json": {
      "bytes": 586,
      "sha256": "855e48ff79d203f9afdd5ab939ce2d126d216b61d75769ffe7079b8dc369c6b3"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_03/PROMPT.txt": {
      "bytes": 1591,
      "sha256": "848bd85ae6d4f65f9581f2a303973ec33ae6048e6b96f3524875788f0dbbbfdf"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_03/PROVENANCE.json": {
      "bytes": 7159,
      "sha256": "3d2e4108f768e69f052c32ee11037729bed3facc2e767aebb1cc6f92ed8b7a61"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_03/RUN_STATUS.json": {
      "bytes": 1015,
      "sha256": "7e605ff210fc06b2a34df0a3028bd4c3a202734093c4eca2e2fc53a7e39ef880"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_03/VALIDATION.json": {
      "bytes": 1254,
      "sha256": "85f008a6d9a1b6d4ede0504f0df488a9a78e49b9c21b865a19684fb7c9769b32"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_03/normalized_review.json": {
      "bytes": 8189,
      "sha256": "e9701aba40dd1b403da8680c209228504138f5d95eafdaa1508c24857fbd330b"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_03/response.txt": {
      "bytes": 8038,
      "sha256": "f0ba2b0ec2fdcd4ef29395d1775f72d8ce8c41785566b1557f392b05ae17f003"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_03/reviewer.json": {
      "bytes": 8176,
      "sha256": "14b94ad5312ec65cf701325a88b6f78404025e90f3e523e2db73b6f3b6758473"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_04/PROMPT.txt": {
      "bytes": 1591,
      "sha256": "bbefa914e74efed1097c4895c5279c547de97c6cdd86ccdb24b9fb1012f0008f"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_04/PROVENANCE.json": {
      "bytes": 7298,
      "sha256": "b447cee7201bbe228e66e4144aa8c6000b55a9739f1988323930aeb1e6fdaeaf"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_04/RUN_STATUS.json": {
      "bytes": 1015,
      "sha256": "6c6b071e9069e20e3a5c1437fbb39ff1da6f6a861900f53966bd6b1f33b85549"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_04/SCHEMA_DEVIATIONS.json": {
      "bytes": 159,
      "sha256": "4b6b86b9a9c283d6c9361bf4d1c0db614594295da7cfacdae95841c936bef90e"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_04/VALIDATION.json": {
      "bytes": 1524,
      "sha256": "b106759429b93e4fd4f9dbb8f136f64c0ecfd52bb1e4c959991715b250b9072f"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_04/normalized_review.json": {
      "bytes": 9669,
      "sha256": "cbce0744f3a0961f7ef72dd7c3cd223d1d500aefc96e2843731cd8c8970197dd"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_04/response.txt": {
      "bytes": 9533,
      "sha256": "ba5fbf6bd4e6798b8fa592fadfae20f349ab57a85d008238a24eefbfad32b592"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_04/reviewer.json": {
      "bytes": 9671,
      "sha256": "fff2793e2672ad29777a276fdd7de11e35d3cd48a2fbe735ce35e2dc3e010bae"
    },
    "reports/paper_editorial_review_v1/claude_code_review_01/HOST_CHECK.md": {
      "bytes": 3778,
      "sha256": "4cf6ee6f3997f0494f75a487035c34962f438a62f03fa3cb0e8c59b95b65b261"
    },
    "reports/paper_editorial_review_v1/claude_code_review_01/PROMPT.txt": {
      "bytes": 1922,
      "sha256": "d6c5623e2bcd46ab2126b57d9b1a0f62a1be2e5d98df95ea69811207750822ad"
    },
    "reports/paper_editorial_review_v1/claude_code_review_01/PROVENANCE.json": {
      "bytes": 6371,
      "sha256": "5dcc1882704122e5c67c7a93651647853f4341d33c75b57223263da1c4b420e0"
    },
    "reports/paper_editorial_review_v1/claude_code_review_01/VALIDATION.json": {
      "bytes": 1170,
      "sha256": "ea8b8f21008c541ff4ce80141a555db155312d02516ca18484492e9e49e16485"
    },
    "reports/paper_editorial_review_v1/claude_code_review_01/response.txt": {
      "bytes": 25058,
      "sha256": "e54d464e92f67a695fdbf5240a1f3744061631b6b94821fae9bdc41108604df2"
    },
    "reports/paper_editorial_review_v1/claude_code_review_01/reviewer.json": {
      "bytes": 24991,
      "sha256": "8d0b55df78fa08262d1db9f2d44b749917427bd396a41fb4cb3aef43827921a6"
    },
    "reports/paper_editorial_review_v1/claude_code_review_02/CANCELLED.json": {
      "bytes": 466,
      "sha256": "6d297a5ec835568f6c6cebca19d20d9837612a1b96cd131954cdb04989fd5b33"
    },
    "reports/paper_editorial_review_v1/claude_code_review_02/PROMPT.txt": {
      "bytes": 1922,
      "sha256": "0d544b8509373b79ac326f06037f95431f6a86f2e8045c0140f4511a6908a37b"
    },
    "reports/paper_editorial_review_v1/claude_code_review_02/PROVENANCE.json": {
      "bytes": 7021,
      "sha256": "8b44d697a83edd4db425028a19c79721aebe65ac25247814555a22a539b99403"
    },
    "reports/paper_editorial_review_v1/claude_code_review_03/PROMPT.txt": {
      "bytes": 1922,
      "sha256": "b6049dce2fa353e51d64cbc5204aaf67863c4dd6ff08f4828d352eefa8713e6f"
    },
    "reports/paper_editorial_review_v1/claude_code_review_03/PROVENANCE.json": {
      "bytes": 7324,
      "sha256": "7a835f68c6a5cd851c80bf339d07ac176fb56a0d7d8bdf73fe4096db733905a3"
    },
    "reports/paper_editorial_review_v1/claude_code_review_03/VALIDATION.json": {
      "bytes": 980,
      "sha256": "b236ce45c2031ccaa8273650f8c12943ec4d0e65f6f7f34d81752118cdb8614d"
    },
    "reports/paper_editorial_review_v1/claude_code_review_03/response.txt": {
      "bytes": 21224,
      "sha256": "43680f004af9312959b30c40df20a8742f9ccbbe56befdf2409fbfb0efbe9818"
    },
    "reports/paper_editorial_review_v1/claude_code_review_03/reviewer.json": {
      "bytes": 21507,
      "sha256": "de31a455d4374c901513e4e9f5cf5eee8afe9f3e2e9a747e9bfadadff636cfdc"
    },
    "reports/paper_editorial_review_v1/claude_code_review_04/PROMPT.txt": {
      "bytes": 1922,
      "sha256": "a543b1b00891bbbad6121f91bb963e855be805af36a5709a6210661a9ea5cfb7"
    },
    "reports/paper_editorial_review_v1/claude_code_review_04/PROVENANCE.json": {
      "bytes": 7463,
      "sha256": "d08b632bb29fb2e3ba850105acc652b6b0a85a157e9f5f635eabec4cf79e0390"
    },
    "reports/paper_editorial_review_v1/claude_code_review_04/SCHEMA_DEVIATIONS.json": {
      "bytes": 430,
      "sha256": "2d45f3b005b4cd5790e62f5cbaca024c47a42364392ed59e511a36844d1bfdff"
    },
    "reports/paper_editorial_review_v1/claude_code_review_04/VALIDATION.json": {
      "bytes": 1374,
      "sha256": "8464a78084151e63f2c75b852d9b14a1cf30ccde0bfa38f5a5ccae123cd80f7a"
    },
    "reports/paper_editorial_review_v1/claude_code_review_04/response.txt": {
      "bytes": 27632,
      "sha256": "50a0ae67fd56e28fcc6a22525421032e8fe5220f7cbe53f42de8be0d692c08e3"
    },
    "reports/paper_editorial_review_v1/claude_code_review_04/reviewer.json": {
      "bytes": 28282,
      "sha256": "5436c5098aca92f5f4dd6601eb2e988a61f4bfe3ada888152cf0f01738d8d238"
    }
  },
  "local_execution_artifacts": {
    "reports/paper_editorial_review_v1/astra_xhigh_review_01/run_review.original.ts": {
      "bytes": 6408,
      "sha256": "eb8623a1ffabd99cda040cc7e0fb4f6c1d6b1f7203afd3c8c1edbe10d73b976e"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_01/run_review.ts": {
      "bytes": 6935,
      "sha256": "fc930e402ac6836d2505488b1bb91275ac749ce40813fdeac0448e0079a8be14"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_02/run_review.ts": {
      "bytes": 6905,
      "sha256": "a66c376fd91971f0cafe8d48702b66511d262014fd46dd7b731890ee42ce40e0"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_03/run_review.ts": {
      "bytes": 6905,
      "sha256": "8265093614510e060e4ef8c9732796c8ff03d1d3eee295fb2f90d9d9982649ef"
    },
    "reports/paper_editorial_review_v1/astra_xhigh_review_04/run_review.ts": {
      "bytes": 7146,
      "sha256": "44db6817a1aaa166f640fcde4f2809c11c90dd57060a9ab1e34a07c5acf606fa"
    },
    "reports/paper_editorial_review_v1/claude_code_review_01/claude_stderr.log": {
      "bytes": 0,
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "reports/paper_editorial_review_v1/claude_code_review_01/claude_stream.jsonl": {
      "bytes": 12758937,
      "sha256": "fa44e7afd229f05ef1ad75a4f2e1f56f4f770b9fb21fb09eee2f88e641b33425"
    },
    "reports/paper_editorial_review_v1/claude_code_review_02/claude_stderr.log": {
      "bytes": 0,
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "reports/paper_editorial_review_v1/claude_code_review_02/claude_stream.jsonl": {
      "bytes": 7125514,
      "sha256": "c36cfb8b2229295895c03ab7471bed786fc8b879691fface25ce8cfc189749db"
    },
    "reports/paper_editorial_review_v1/claude_code_review_03/claude_stderr.log": {
      "bytes": 0,
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "reports/paper_editorial_review_v1/claude_code_review_03/claude_stream.jsonl": {
      "bytes": 21017331,
      "sha256": "8f1e15d2d0f8d317805afd7f5a34af44b5d5fb7a663706318c07af54a64eaef5"
    },
    "reports/paper_editorial_review_v1/claude_code_review_04/claude_stderr.log": {
      "bytes": 0,
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    },
    "reports/paper_editorial_review_v1/claude_code_review_04/claude_stream.jsonl": {
      "bytes": 21010228,
      "sha256": "66d11d450f3c53b376cff44b8ca9ed5002d1821b42ffdf2d1920cf3092e9b54e"
    },
    "tmp/paper/astra-xhigh-review-01/request-attempt-01.json": {
      "bytes": 11061097,
      "sha256": "07ff85feccb4e07faa2981e625700abd797d5c077440511e79518449584f22ac"
    },
    "tmp/paper/astra-xhigh-review-01/request.json": {
      "bytes": 11061073,
      "sha256": "b63d06fbdf7703767325efdcab811ef1483867b84a13dbfc0ee138e01f7f65f4"
    },
    "tmp/paper/astra-xhigh-review-01/response_events.jsonl": {
      "bytes": 570198,
      "sha256": "5a228202eebb3cb99ee20ea7d93903d8eb64945d22b6d929cb506bcf22a4bb38"
    },
    "tmp/paper/paired-review-02/request.json": {
      "bytes": 11061073,
      "sha256": "327e53a5521e90588b9bb05bcb0da686e7048496a30ae12a8b582eb5e990dd51"
    },
    "tmp/paper/paired-review-02/response_events.jsonl": {
      "bytes": 13663,
      "sha256": "b83b20b772787f086ab01d1729911c42f60ff109f167d0ad49275be964c6c8b9"
    },
    "tmp/paper/paired-review-03/completed_response.json": {
      "bytes": 3283,
      "sha256": "a6b9bf4f138b318af0962fc7f485e4798888f53833bc8342f67780b5f9a5cd3f"
    },
    "tmp/paper/paired-review-03/request.json": {
      "bytes": 11085798,
      "sha256": "6b543a4cc42894421499a2d318c2542f83bc08f748e62d96185195a9fb6f67aa"
    },
    "tmp/paper/paired-review-03/response_events.jsonl": {
      "bytes": 587461,
      "sha256": "2f515cc2b29504d50b7379f3f814604e0c19d6bedfd9833cb6c76209320b9503"
    },
    "tmp/paper/paired-review-04/completed_response.json": {
      "bytes": 3283,
      "sha256": "4c46344973bfa92fe30b6b2878b56f2938e2a7360d6478de71c9b383de596f38"
    },
    "tmp/paper/paired-review-04/request.json": {
      "bytes": 11086735,
      "sha256": "bcd1433c8a34c29d2b757cf331fb97925580216a20350f7c5afd6e2ce991bff2"
    },
    "tmp/paper/paired-review-04/response_events.jsonl": {
      "bytes": 656574,
      "sha256": "7e1ed393cf4e4907fbdfb56545fb359092dd6ebbadaeec837e6176189b779d02"
    }
  }
}
```
