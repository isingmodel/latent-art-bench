# Round 4 presentation and preservation check

This is an unscored coordinating-maintainer LLM check of the
[Round 4 snapshot](ROUND4_SNAPSHOT.json), commit `5ad78d0eebd1f695a9b413339b26454bc1ae40aa`.
It does not replace the three full scientific reviews or independent validation.

The complete 39-page PDF was rendered with Poppler at 100 dpi and inspected in
page overviews; the new result/method pages were also inspected individually.
After avoiding hyphenated page breaks, the seven changed pages (22–25 and 34–36)
were rendered and checked again. All pages remain within margins, with no clipped
text, overlapping figures or missing content. The new two-endpoint table remains
separate from the historical fold averages. A float boundary keeps the earlier
tables before the prospective subsection, and its two contrast definitions are
displayed together. The abstract is 239 whitespace-delimited words.

Tectonic 0.17.0 compiles the final source with no warning, unresolved reference or
overfull box; extracted text contains no unresolved citation/reference marks.
All four painters and all nine figures remain. `make figures-check` passes all
nine byte comparisons and the existing plotted-value checks; no figure values,
coordinates, source images or scientific result files changed. The final PDF has
39 pages and 482,224 bytes. Its SHA256 is
`fcdaf7d13fe95475dbe2dfa6be308f2bd067e5ec403faa3952cfdbe7fc059f89`;
the snapshot binds the TeX, bibliography, figure and relevant evidence hashes.

`git diff --check` and whole-tree Ruff pass. The historical evidence audit at
`bd3c9ca` passes all 2,902 checks with the same two pre-existing acknowledged
inputs. The full offline suite is recorded separately when its final run completes.
The new namespace's terminal/arithmetic/public replay checks have their own
reports; the historical audit does not register it.

Both user-owned Korean files retain their pre-task hashes and remain unstaged:
TeX `5fe49bca779276987c7d0bd1b6e35a4c24554887409421dfa49f7aa776c6c234`,
PDF `1cc97870da21b8a5595febe7d38f84dc1f0ded210904e4de7ad6b1a7112e1924`.
No frozen protocol, completed census, evidence hash, ignored image archive or
old public asset was replaced. Current manuscript source/PDF publication still
requires final review and separate source-build/anonymous asset verification.
