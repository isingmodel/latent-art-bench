# Correct the historical reference reader before new measurement

The original specificity implementation assumed that the confirmation-feature
manifest contains only its 649 valid records. A reference-only inspection during
collection found 653 rows: those 649 measured records plus four old failures.
No generated feature extraction or inference had begun. The old implementation
would stop rather than produce the intended reference array. Its frozen source
and scientific protocol remain unchanged; this versioned adapter is the corrected
measurement/replay entry point for the existing collection, not a new cohort.

The protocol has always specified the already-measured 649-work panel:
297 Monet, 106 Sisley, 141 Pissarro, 105 Cezanne. Select exactly the historical
`status=measured` records and verify all four counts and unique identities. The
four failed old records are Q19820260 (nonopaque alpha), Q26846569, Q63986323 and
Q98447005 (unprofiled non-RGB color space). They have no usable original feature
vectors and were never members of the stated 649-work target. Their disposition
is unchanged. They are neither retried nor silently dropped from a new target.

Reuse the frozen image normalization/extraction primitive, the same full and
square measurement windows, the same raw-image ancestry, scaler and primary
numerical functions. The adapter writes the originally planned new measurement
paths, with an additional reader-freeze binding in the receipt. Collection,
request order, model identity, cost, endpoints, multiplicity and uncertainty
remain unchanged. It also feeds this identical filtered reference order to the
separately declared class-mixture sensitivity. No corrected numerical output
exists yet, and no failed measurement is being overwritten.

Canonical commands are now:

```
uv run --locked python -m latent_art_bench.painter_specificity_measurement_v1.workflow measure
uv run --locked python -m latent_art_bench.painter_specificity_measurement_v1.workflow analyze
uv run --locked python -m latent_art_bench.painter_specificity_measurement_v1.workflow analyze --square
uv run --locked python -m latent_art_bench.painter_specificity_measurement_v1.workflow analyze --reference
uv run --locked python -m latent_art_bench.painter_specificity_measurement_v1.workflow analyze --reference --square
```

Add `--check` to an analysis command for exact replay. Do not invoke the old
v2 measurement command or either old reader CLI. The active collector retains
its original entry point and must not be restarted concurrently.
