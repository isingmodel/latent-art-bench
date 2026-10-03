# Painter specificity v3: collection and analysis protocol

Version 1.0 **draft**, 2026-10-02. Not frozen. Generation needs the owner's written
approval of this protocol and of the cost ceiling, and the bound inputs must be
committed before `collect.freeze` writes the request frame. No image of the new
collection exists.

## What was known when this was written

- The four-painter results (`psv2-20260911`) and six rounds of language-model
  review (`reports/tmlr_review_v1`). The reviewers asked whether the shared fraction
  tracks how close the painters are; a single related group cannot say.
- The two new groups and their reference panels
  ([REFERENCES.md](REFERENCES.md), run `refs-20261002`), measured before this
  protocol is frozen, under two amendments to the reference rules recorded there
  (no minimum panel size, as for the four painters; standard Commons thumbnail
  widths and a user agent with contact information). The predictions below use
  those references and September's generic-arm outputs only.
- No output of any configuration for the eight new names.

The paper's four-painter study is unchanged, and the four painters stay its main
scientific scope. This collection is an extension, reported as added after the
four-painter results.

## Question

The paper explains its main finding this way: most of what a painter name adds is
shared by the four names because the four painters are close to one another
relative to their distance from generic outputs. Even faithful imitation would
then be mostly shared. The explanation predicts that painters far apart leave a
smaller shared fraction, and that, pair by pair, names differ more where the
painters' references differ more. Two groups test this:

- **Century group** (far apart): Jacob van Ruisdael, Canaletto, Vincent van Gogh,
  Ernst Ludwig Kirchner.
- **Hudson River School** (closely related): Albert Bierstadt, Frederic Edwin
  Church, Thomas Cole, Asher Brown Durand.

## Hypotheses and decision rules

**H1, closeness.** The century group's shared fraction N/(N+B) is lower than the
Hudson River School's. Statistic: the century-minus-Hudson difference, computed per
configuration from the same scenes and the same generic arm, averaged over the six
configurations. Supported if the 95% percentile interval of the pooled difference
from 5,000 paired scene resamples (seed 20261003) lies entirely below zero.
Per-configuration differences, with Bonferroni-adjusted intervals for six
comparisons, are secondary.

**H2, dose-response.** Across the 28 pairs of the eight new painters, the squared
distance between two names' outputs (scene-averaged, cross-repeat, so free of
repeat noise) rises with the squared distance between the two painters' reference
means. Statistic: the Spearman correlation over the 28 pairs, averaged over the six
configurations. Supported if the exact one-sided permutation p-value over all
40,320 relabellings of the eight painters' references is below 0.05.
Per-configuration correlations are secondary.

Both hypotheses are tested once, in the 31 standardized-input features (the
paper's primary representation). The same statistics in CLIP and CSD are
secondary. The **outcomes are reported whichever way they fall**: if H1 fails, the
closeness explanation does not hold for these configurations, and the paper says
so.

## Predictions fixed before collection

Recorded in `refs-20261002/predictions.json` (SHA-256 `65a12c297f2f…`), from the
measured reference panels (788 works: van Ruisdael 123, Canaletto 157, van Gogh
255, Kirchner 41; Bierstadt 92, Church 47, Cole 36, Durand 37) and September's
generic-arm outputs. H is the reference spread; the faithful benchmark is the
shared fraction a generator would show if each name landed on its painter's
reference mean.

| Representation | Group | H | Faithful N*/(N*+H), range over configurations |
| --- | --- | --- | --- |
| 31 features | Four Impressionists (paper) | 5.92 | 0.848–0.952 |
| 31 features | Century group | 34.61 | 0.470–0.733 |
| 31 features | Hudson River School | 6.24 | 0.901–0.969 |
| CLIP | Four Impressionists (paper) | 0.1388 | 0.861–0.912 |
| CLIP | Century group | 0.4597 | 0.674–0.748 |
| CLIP | Hudson River School | 0.0824 | 0.927–0.943 |
| CSD | Four Impressionists (paper) | 0.3250 | 0.824–0.897 |
| CSD | Century group | 1.0478 | 0.634–0.703 |
| CSD | Hudson River School | 0.1416 | 0.922–0.955 |

The century painters are about six times farther apart than either related group
in the 31 features (three to seven times in the embeddings). Under the closeness
explanation, the century group's observed shared fraction should therefore be
clearly lower than the Hudson River School's (H1), and name distances should
follow reference distances across the 28 pairs (H2). In the 31 features, the noise
correction lowers H to 33.80 (century) and 4.21 (Hudson River School); the
four-painter value is 5.52.

## Design

- **Configurations, routes and payloads**: those of `psv2-20260911`, unchanged
  (`painter_specificity_v3/study.py` reuses September's payload function and OpenAI
  override; tests check that the free and generic payloads are byte-identical to
  September's for every configuration and scene). All six routes were listed with
  unchanged prices on 2026-10-02 (`provider_quotes_20261002.json`).
- **Scenes**: September's 14 authored outdoor scenes.
- **Arms (10)**: no clause; "Render as an oil painting."; and "Render as an oil
  painting in the style of NAME." for the eight names, written as in
  [REFERENCES.md](REFERENCES.md).
- **Repeats**: two independent requests per cell.
- **Allocation**: 6 × 14 × 10 × 2 = **1,680 images**, 280 per configuration.
- **Order**: scenes in random order; within a scene, all 120 configuration × arm ×
  repeat requests in random order (seed 2026100217). Request IDs `psv3-0000` to
  `psv3-1679`.
- **Own baselines**: the no-clause and generic arms are collected again, so every
  statistic uses baselines from the same collection.

## Collection

The September collector's rules, in a versioned copy (`collect.py`):

- at most three requests in flight, starts at least five seconds apart;
- a $5 reservation per start until its charge is known;
- at most two retries per request (20 s, then 60 s) and 24 in all; refusals are
  not retried;
- dispatch pauses on three consecutive technical failures, a client rejection, a
  diagnostic, an unknown charge or a charge above $5, or an operator pause file;
- a terminal receipt is written once, and the run cannot restart after it.

At September's pace the run takes about 4.6 hours.

## Measurement

- **31 features**: `painter_specificity_v1.workflow.measure_one`, giving the full
  view (primary) and the central 512 square (sensitivity), in the unchanged
  four-painter scaler.
- **Embeddings**: CLIP and CSD at the learned audit's pinned revisions
  (`painter_specificity_v3/embeddings.py`).

## Analysis (`painter_specificity_v3/analysis.py`, bound at freeze)

**Per group** (a six-arm slice: no clause, generic, four names), with the paper's
own functions and conventions:

- N, B, H, the shared fraction and both benchmarks;
- β, Q, D, the alignment ratio and D_held;
- the split of D along and off the reference pattern;
- the proximity identity (Eq. 4).

Intervals follow the paper:

- Student intervals over scenes for per-scene statistics;
- percentile intervals from scene resampling for ratios;
- a family of 21 per group (6 β, 15 pairwise D) with Bonferroni-adjusted Student
  intervals.

**Across groups**: H1 and H2 above.

**Drift**: the no-clause and generic outputs against September's, for each
configuration. This is the cross-collection squared distance of scene means, free
of repeat noise, against September's repeat noise. It is descriptive, and it
doubles as the later third repeat the reviewers asked for.

**Missing outputs.** Scenes enter the cross-group tests only when every
configuration, arm and repeat is present, as in the paper's common complete-scene
panel. Below 12 such scenes, H1 and H2 are reported as unavailable, and
per-configuration results use each configuration's complete scenes. Refusals are
recorded as such and never replaced.

## Cost

- **Recorded spend**: $112.293676 (`psv2-20260911/collection.json`).
- **Forecast**: $72.98 for 1,680 images at September's observed mean cost per
  configuration.
- **Ceiling**: **$200 cumulative**, set by the owner on 2026-10-03 (at most $87.71 of
  new charges). The collector holds back a request when the recorded spend, its $5
  reservations for requests in flight and one more reservation would reach the
  ceiling. At September's prices the run ends near $185.27, so it stops early only if
  charges exceed the forecast by about 13%. A budget stop is recorded in the receipt,
  and the analysis then uses the complete scenes as described above.

## Freeze

`collect.freeze(ceiling, approval)` requires the bound inputs to be committed, and
records:

- the owner's approval text and the ceiling;
- the September baseline;
- the request frame and the Git commit;
- the SHA-256 of this protocol, REFERENCES.md, the reference records, the quotes,
  the September receipt and requests, the scaler, `pyproject.toml`, `uv.lock` and
  every v3 source and test file.

No paid request precedes the freeze.
