# English paper prototype

`paper.tex` is a venue-neutral manuscript with anonymous author placeholders.
The current 11-page prototype specifies content weighting, full-distribution
energy, spread, sample-matched original baselines, coverage, grouped detection
and the conditional prompt statistic. It reports completed development evidence,
the completed technical pilot and verified reference measurement;
the controlled extension is explicitly marked in progress. No new-model fidelity
results or human results are fabricated. Update those sections only from verified
terminal evidence when the active study completes.

Build from this directory:

```bash
tectonic --outdir ../../tmp/paper-build paper.tex
cp ../../tmp/paper-build/paper.pdf paper.pdf
```

Create the temporary output directory first if necessary. Render and inspect every
PDF page with Poppler after substantive changes. Figure files are the preserved
numeric diagnostic plots, not redistributions of artwork pixels. The bibliography
uses the audited project bibliography and explicitly identifies the 2026 preprint.
Publication venue and any collaboration or authorship remain undecided.
