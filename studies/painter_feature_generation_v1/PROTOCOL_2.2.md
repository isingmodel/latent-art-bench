# Painter Feature Generation v1 — Protocol 2.2

Status: prospective amendment of Protocol 2.1, issued before any active image, content label,
feature, or generated output exists

Protocol ID: `painter-feature-generation-v1/2.2`

Operational date: 2026-09-04

Amends: Protocol 2.1 (`PROTOCOL_2.1.md`). **Every section of 2.1 stands unchanged except the ones
replaced below.** 2.1 and 2.0 stay at their paths as the frozen authority for the censuses executed
under them; those censuses carry over unchanged because the source registry is identical.

## 0. What this version changes, and why

Protocol 2.1 applied its heaviest machinery to R0 metadata collection: a freeze binding every
input file, a neutral review, an authorization seal, a one-shot lock, a hash-chained event ledger,
and termination of the whole census on any anomaly. Four routes were executed under those rules.
Three of the four terminated on their first run, every time because a frozen parser rejected a
valid provider representation rather than because a provider failed. Each retry cost a full
re-run and a duplicated collector module.

That machinery is aimed at one real threat: choosing what the corpus contains after seeing what
the numbers look like. But R0 metadata collection has almost no room for that choice. Asking a
museum what it holds by Monet has no favourable and unfavourable answer. The choice arrives later,
at authority reconciliation and eligibility, where 2.1 has no implementation at all.

Protocol 2.2 therefore moves the weight. R0 keeps only what makes the collection describable and
honest. The apparatus that protects against outcome-dependent selection stays, and is strengthened,
from R1 onward.

A second change has the same cause. Under 2.1 each route computed screening verdicts at collection
time and published them in the candidate manifest. The Cleveland census of 2026-09-04 showed why
this is wrong: Cleveland catalogues these works as `oil on fabric`, the frozen screen demanded the
token `canvas`, and eight of twelve paintings were published with a false negative verdict,
including every Sisley and every Cézanne. The raw strings survived, so nothing was lost. But a
verdict computed before the vocabulary is understood is worse than no verdict. **Protocol 2.2
removes screening from collection entirely.**

## 1. R0 collection: four principles

These four replace Section 5.2's freeze list, the operational procedure implied by Section 15's R0
row, and every route-specific screening contract.

### 1.1 Write the request down before running it

Each source has one committed config file that states the exact URL of every request, the method,
any body, the response format, and where the records sit in the response. The config is the request
registry: there is no separate intent-generation step, because the config already lists the exact
URLs.

The config is committed before the census runs. Editing a config after seeing its counts produces a
new census under a new census ID; it does not amend the old one.

### 1.2 Keep everything

Every response body is stored verbatim, addressed by its SHA-256, with its HTTP status, final URL,
byte count, and retrieval timestamp. Every record the provider returned appears in the manifest
with **every field the provider sent**, unmodified.

Nothing is filtered, normalized, renamed, or dropped at collection. A field that looks irrelevant
today is the field a later stage will need.

Raw response bodies are retained under the ignored research workspace. Because that workspace is
not committed, a route whose records are large or numerous must ensure the manifest itself carries
the complete records, so that losing the workspace does not require re-querying a mutable provider.

### 1.3 Do not judge at collection time

A census records what a provider returned. It does not decide whether a record is an eligible work.

No census emits an eligibility flag, a candidate flag, a screening verdict, a score, or a
disposition. Attribution, object type, medium and support, rights, geometry, and outdoor-place
eligibility are decided once, at R1 and R2, from the retained raw fields, under Sections 7.1 to 7.4
of Protocol 2.1.

Counts reported from a census are counts of returned records, and must be named that way.

### 1.4 The source list is closed

Section 5.2's registry is the complete list. Adding a route, or a work discovered outside every
route, requires a new protocol version before its pixels or features are viewed.

Collection does not stop when a count looks sufficient. A route that cannot be completed is
reported as incomplete; it is never replaced, and a painter who comes up short is never topped up
from elsewhere.

## 2. R0 procedure

```text
config 커밋  →  실행  →  manifest + receipt 커밋
```

A neutral review, an authorization seal, a one-shot execution lock, and a hash-chained event ledger
are **not required at R0**. They remain required from R1 onward (Section 4).

The maintainer authorizes each census in session before it runs. That authorization is recorded in
the receipt.

## 3. R0 failure handling

A failed request records its terminal state in the receipt and **the census continues**. The receipt
states plainly whether the census is complete.

An incomplete census is reported as incomplete and its records remain usable as far as they go. It
is not spliced with a later run: a re-run is a new census ID whose receipt names its predecessor.

A parser must never terminate a census over a field the census does not use. Because 2.2 removes
screening from collection, the only fields a census can legitimately fail on are the ones needed to
locate the records inside the response.

## 4. What does not change

Everything else in Protocol 2.1 stands. In particular:

| Stage | Requirement | Status under 2.2 |
|---|---|---|
| R1 | authority, rights, identity, technical image gates (2.1 §6, §7.1–7.3) | unchanged, and still requires a reviewed freeze and authorization seal before any image byte is fetched |
| R2 | metadata-declared eligibility and role assignment (2.1 §7.4, §8.1) | unchanged; this is where every collection-time verdict now lives |
| M0 | measurement qualification, margins, copy thresholds (2.1 §10, §13.3) | unchanged |
| G0 | model, prompt, seed, analysis freeze (2.1 §11, §13.4) | unchanged |
| G1 | generation attempt ledger | unchanged, and the hash-chained ledger is **retained here**, where dropping an unfavourable attempt is an actual temptation |
| C0 | one-time confirmation opening | unchanged |

The adequacy gates of 2.1 §9, the estimator and decision rules of §13, the reporting rules of §17,
and the quality checks of §18 are untouched.

## 5. Effect on the completed censuses

The fixed-seed audit, the broad no-`P186` discovery census, the broad-media follow-up, the Art
Institute route, and the Cleveland route were executed under 2.0 or 2.1 and remain valid exactly as
recorded. Their freezes, reviews, seals, ledgers, and receipts are not rewritten.

Their published screening verdicts are now understood as **collection-time artifacts, not
findings.** Reports must cite their returned-record counts, not their candidate counts. The
Cleveland manifest's four `metadata_and_media_candidate` rows in particular must not be reported as
Cleveland's yield; the route returned 54 records, of which twelve carry a painting classification,
and the oil-on-fabric determination belongs to R1.

## 6. Current authorized state

At Protocol 2.2 issuance (2026-09-04): five routes complete, eight named routes outstanding, zero
admitted physical works, zero downloaded images, zero confirmation works, zero generation attempts,
and zero results. The next authorized action is metadata-only collection of the remaining routes
under Section 1.
