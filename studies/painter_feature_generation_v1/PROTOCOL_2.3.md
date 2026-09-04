# Painter Feature Generation v1 — Protocol 2.3

Status: prospective amendment, issued before any active image, content label, feature, or generated
output exists

Protocol ID: `painter-feature-generation-v1/2.3`

Operational date: 2026-09-04

Amends: Protocol 2.1 (`PROTOCOL_2.1.md`) sections 5.1, 5.2, 7.1, 7.2, and the construct name in 2.1
§2.1. Protocol 2.2's four R0 collection principles stand unchanged. **Every other section of 2.1
stands.** 2.0, 2.1, and 2.2 stay at their paths as the frozen authority for the censuses executed
under them.

## 0. The decision this version records

Protocol 2.1 §5.1 forbade the discovery layer from establishing authenticity: Wikidata and Commons
could "find and crosswalk candidates; never establish authenticity alone." §7.1 therefore required
an authority record from the holding institution for exact attribution, object type, medium and
support, and accession.

The 2026-09-04 collection-identity census made that requirement unworkable. The 3,543 discovered
items carry **2,956 item–collection links across 449 distinct institutions.** The ten largest
holders cover 28.7% of those links and the fifty largest cover 56.1%. The Protocol 2.1 registry
names eight routes, four of which appear in the top ten; the Metropolitan Museum, the Barnes
Foundation (which alone holds 61 Cézannes), the Museum of Fine Arts Boston, the Philadelphia
Museum of Art, the Hasso Plattner Collection, and the National Gallery in London are all outside it.

Reaching institutional authority records for this corpus would require writing and running on the
order of fifty museum routes. That is not a schedule problem; it is a different project.

The maintainer therefore decided on 2026-09-04 to **accept Wikidata's own statements as the
authority layer.** This version records that decision, states exactly what it costs, and renames
the construct so that no report can overstate what was verified.

## 1. Source layers, amended

2.1 §5.1's three layers stand, with one change: **Wikidata occupies the authority layer as well as
the discovery layer** for this study.

| Layer | Source | Permitted use |
|---|---|---|
| authority | **Wikidata item statements** | creator, object type, material and support, collection and inventory identity, copyright status |
| discovery | Wikidata, Commons | find candidates and crosswalk identifiers |
| media | Wikimedia Commons file | deliver a measurable image with its own licence and technical receipts |

A museum route may still be run, and its record is stronger evidence where it exists. But no work
is excluded for lacking one.

## 2. Inclusion, amended (replaces 2.1 §7.1)

A candidate is included when its Wikidata item, on best-rank statements observed in a single
recorded census, satisfies all of:

1. **exactly one** `P170` creator, equal to the target painter's QID;
2. `P31` includes `Q3305213` (painting);
3. `P186` includes **both** `Q296955` (oil paint) and `Q12321255` (canvas);
4. `P195` (collection) is present; and
5. no best-rank statement contradicts 1 to 4.

Requirement 1 is strict on purpose. A work with two creator statements, or with a creator qualifier
the census did not resolve, is excluded rather than adjudicated.

Requirement 3 is a **positive** requirement, unlike the discovery census that deliberately dropped
it. Absence of `P186` is not evidence against oil on canvas, but under this version nothing else can
supply the medium, so an item without the statement cannot be included. Measured cost: about 10% of
discovered items.

Requirement 4 is retained not as a rights or identity gate but because §9's workflow-crossing rule
needs to know which institution a work sits in. An item with no collection cannot be assigned a
capture workflow and so cannot support that gate.

## 3. Media rights, amended (replaces 2.1 §7.2)

The rights basis is the **licence of the Commons file that is actually downloaded**, not the
painting's `P6216` copyright status.

This is the correct instrument. The object retrieved and processed is the Commons file; its licence
is what permits that processing. `P6216` describes the underlying work and is unevenly recorded:
374 Monet items with a collection and oil-on-canvas statements carry no `P6216` value at all, while
the other three painters have none missing. Requiring `P6216` would drop those 374 works for a
missing statement rather than for a rights problem.

An accepted file carries a Commons open-rights marker: public domain, CC0, CC BY, or CC BY-SA. A
file under `rights_review`, or with a non-commercial or no-derivatives term, is excluded.

The repository still commits metadata and compact reports, never restricted image bytes.

## 4. The construct name, amended (replaces the name in 2.1 §2.1)

The exact construct is now:

> **Wikidata-declared outdoor-place digital-surrogate feature reproduction**

Every report must use this name, and must state that attribution, object type, medium, support, and
collection were taken from Wikidata statements observed at a recorded time, not from institutional
catalogue records.

The study no longer claims authority verification. It claims a reproducible, timestamped, closed
frame built from a crowd-maintained knowledge base.

## 5. What this costs, stated plainly

| Limitation | Consequence |
|---|---|
| Wikidata is crowd-edited with no editorial review | attribution may be wrong or outdated; there is no adjudication step |
| Misattribution among this panel is not random | Monet, Sisley, and Pissarro painted the same places in the same years; confusions run between them and bias §13.4's specificity contrast against a positive claim |
| Statements are mutable | the frame is defined by one timestamped census with retained raw responses, not by Wikidata's current state |
| `P186` incompleteness excludes about 10% | those works are lost, not misclassified |
| Commons files are web images | training-data overlap with the model under test is likelier than for museum IIIF masters; report the copy-detection rate and, where a museum route exists, the stratified result |

The first two are the substantive ones. They cannot be removed at this corpus scale, and they must
appear in the limitations section of any report, not only in a protocol file.

## 6. Measured effect on corpus adequacy

Applied to the 2026-09-04 broad census, deduplicated to distinct Wikidata items, with the §7.4
content lexicon:

| Gate | Monet | Sisley | Pissarro | Cézanne |
|---|---:|---:|---:|---:|
| discovered items | 1,257 | 812 | 766 | 708 |
| exactly one creator, `P31` painting | 1,257 | 812 | 766 | 707 |
| `P186` oil and canvas | 1,132 | 705 | 685 | 667 |
| `P195` collection present | 1,012 | 378 | 536 | 582 |
| Commons open-rights marker | 1,012 | 378 | 536 | 582 |
| reported short side ≥ 1,024 | 636 | 229 | 350 | 481 |
| lexicon outdoor-place eligible | **521** | **187** | **252** | **197** |
| margin against the 179 floor | +342 | **+8** | +73 | +18 |

All four painters clear the floor. **Sisley clears it by eight works and Cézanne by eighteen.**

Two consequences follow and are binding:

- Any later rule that removes even a few percent of Sisley's works puts the panel below the floor
  and makes the four-painter protocol NO-GO under 2.1 §9. Sisley is the study's binding constraint
  and every subsequent decision must be evaluated against his count first.
- Sisley loses 53% of his oil-on-canvas items at the `P195` gate, against 11% for Monet. His works
  are less institutionally recorded in Wikidata. Adding collection statements is not something this
  study may do, since editing the source would make the frame circular.

## 7. What does not change

2.2's four R0 collection principles; 2.1 §6 identity graph, §7.3 technical image gate, §7.4 content
lexicon, §8 role assignment and exposure control, §9 adequacy gates, §10 features, §11 generation
design, §12 output gates, §13 statistics, §14 robustness, §15 stage freezes from R1 onward, §17
reporting, and §18 quality checks.

In particular §9's workflow-crossing rule stands. Under this version a capture workflow is the
`P195` collection paired with the Commons file's documented origin; an unresolved origin remains
`unresolved` and cannot satisfy the crossing gate.

## 8. Current authorized state

At Protocol 2.3 issuance: six censuses complete, zero admitted physical works, zero downloaded
images, zero confirmation works, zero generation attempts, and zero results. The next authorized
action is to apply Sections 2 and 3 to the recorded census as an R1 determination, producing the
first per-painter physical-work counts this study has ever had.
