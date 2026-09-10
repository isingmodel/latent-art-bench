# Availability-triggered successor decision

Recorded 2026-09-10, before any predecessor feature extraction. This is a fixed
design decision for `painter_clause_successor_v1/pcsv1-20260910`, not an outcome
report or a new permission to bypass qualification.

## Information available and choice

The maintainer verified an error-only HTTP 400 `moderation_blocked` response at
`c:pcv_built04:r00:cezanne` in the active predecessor `pcvv1-20260910`, recorded
at 05:13:08 UTC. No image was returned. It is outside the predecessor's frozen
technical-retry contract, so its Cezanne primary endpoint will be unavailable.
The decision uses this availability information, not generated pixels, extracted
features, effect estimates, p-values, observed new-arm variance or a review score.
Availability is itself an observed outcome; the decision is not wholly
outcome-blind. The reference panel and earlier historical results were already
known.

Accepting the unavailable endpoint and generating nothing more is scientifically
legitimate. The maintainer instead prioritizes the already planned Cezanne versus
actual generic-clause question and selects exactly one fresh two-arm cohort:
all 24 unchanged scenes, two repeats, **96 outputs**, with a single primary
comparison at alpha .025. Both arms are generated anew. The original endpoint
stays unavailable; no slot, control or measurement is borrowed or pooled.

One repeat would use 48 outputs but fewer pairs and no repeated observations of
a scene/arm. Three repeats would use 144 outputs. Two repeats preserve the full
24-scene frame with moderate additional collection. The predecessor's
[historical proxy assessment](../painter_clause_validation_v1/PRECISION.md)
informs the concern about noisy fixed-scene estimates, but did not establish
power for this exact 96-output allocation. This is a resource choice, not a
variance estimate or significance guarantee. Its scope is deliberately narrower
than the predecessor: no new free arm, map/Q, retrieval or conditional-variance
analysis is added.

## Advice, involvement and limits

Reviewers 1 and 3, both maintainer-run LLM agents, considered retaining the
unavailable endpoint sound and supported one 96-output successor if answering
the existing question remained a priority. Their advice required a decision
before feature outcomes, unchanged scenes and clauses, fresh controls, disjoint
evidence, and no further replacement. Reviewer 3 authored the predecessor's
protocol/scenes and this decision/protocol, supplied manuscript and methodological
advice, and reviewed the predecessor implementation. Reviewer 1 previously
implemented statistical components and is implementing the successor analysis;
Reviewer 2 implements collection. These are involved maintainer-run agents,
not independent human or institutional reviewers. No score is assigned.

The maintainer adopts the stricter .025 successor threshold. Original Monet's
unchanged Holm-two rule with original Cezanne unavailable also gives a .025
threshold. Their joint .05 error statement requires the conditional validity of
both tests, including selection using prior availability; it does not assume
independent draws or prove absence of service carryover. No threshold changes if
Monet later fails. Painter and collection/assignment-context differences are
not isolated by comparing the two cohorts.

The new result may favor either clause, remain unresolved or be unavailable.
All cases are reported. The refused brief is retained verbatim, and moderation
refusals are not technically retried. There will be no additional Monet cohort
if its endpoint fails and no further Cezanne successor if this one fails or is
unresolved. The predecessor must become terminal and the new source, reviews,
qualification and assignment freeze must pass and be committed before new live
collection. [PROTOCOL.md](PROTOCOL.md) specifies the exact scientific and
operational contract.
