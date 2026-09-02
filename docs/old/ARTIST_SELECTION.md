# Development-pilot artist selection

## Decision

The pilot targets **artists, not eras or movements**. “Impressionism” and “Post-Impressionism” remain descriptive metadata, but they are too broad to define the pilot estimand. The actual question is whether a generated distribution approaches a named artist's held-out distribution while remaining closer to that artist than to a historically defensible neighbor under one shared content domain.

For `pilot_0` through `pilot_2`, the frozen pairs were:

- Claude Monet ↔ Alfred Sisley
- Camille Pissarro ↔ Paul Cézanne

The common corpus view is `landscape_and_outdoor_place_scene`. This is a genre/content control, not a fifth target label.

## Pilot_3 artist decision

`pilot_3` began with nine candidates from the earlier research:

| Role | Artist | Declared neighbor rationale |
|---|---|---|
| Anchor | Alfred Sisley | historical landscape neighbor of Monet |
| Expansion | Armand Guillaumin | Pissarro/Cezanne circle and outdoor-place domain candidate |
| Expansion | Berthe Morisot | central Impressionist candidate; outdoor-place coverage is uncertain |
| Anchor | Camille Pissarro | historical neighbor of Cezanne |
| Anchor | Claude Monet | historical neighbor of Sisley and Boudin |
| Expansion | Eugène Boudin | coastal/outdoor painter with a documented relationship to Monet |
| Expansion | Gustave Caillebotte | urban/suburban outdoor-scene candidate |
| Anchor | Paul Cézanne | historical neighbor of Pissarro; availability is a substantive risk |
| Expansion | Pierre-Auguste Renoir | outdoor-place candidate with an explicit genre-mix risk |

Before fresh Pilot 3 metadata collection and before any pixels or features, the finite pilot was
purposively capped at four artists. It advanced Alfred Sisley, Camille Pissarro, Paul Cezanne,
and Pierre-Auguste Renoir, with reciprocal pairs Sisley--Renoir and Pissarro--Cezanne. The
choice preserved two historically defensible outdoor-place comparison pairs and used prior
catalog research only. Monet was not advanced because the prior project corpus had no eligible
Met cell under the common acquisition design. Guillaumin, Morisot, Boudin, and Caillebotte were
outside the two chosen pairs at the fixed budget. Those dispositions do not claim that their
catalog coverage is zero or infeasible.

The subsequent authoritative, metadata-only audit covers exactly the four finalists. It
re-verifies attribution, painting/domain status, rights, raw metadata response hashes/access
dates, source governance, and acquisition independence. The final allocation freezes 40
development works—five per artist from each of AIC and Met—and 12 external works. The external
holdout is three complete one-work-per-artist blocks from Minneapolis Institute of Art, Dallas
Museum of Art, and Toledo Museum of Art. Its acquisition contract names the exact official
institutional assets; Wikimedia Commons is not an image-delivery source.

Freeze A1 retains 25 metadata-only candidates as `not_selected`, with zero
replacement-eligible reserves. A later metadata, rights, acquisition, corruption, or input-
domain failure cannot trigger a substitution; it retires the affected frozen design or requires
a new untouched protocol. The three external provider blocks control institution-level delivery
without claiming a shared camera, operator, capture date, or imaging session. Source images are
restricted to internal noncommercial scholarly measurement and are not redistributed. No
artwork pixels, A-vectors, or generated outcomes entered selection.

The common domain includes museum-described outdoor-place scenes with figures, bathing, work,
leisure, or buildings; it is not a figure-free-landscape rule. This composition heterogeneity
is part of the frozen finite corpus and cannot be narrowed after outcomes are seen.

## Why these pairs

For Pilot 3, Sisley and Renoir are treated as historically adjacent Impressionist peers with
substantial outdoor-place work, while Pissarro and Cezanne retain the documented long-running
working relationship below. The graph was fixed from art-historical and content-domain
considerations; it was not derived from A-vector distances or generator outcomes.

For the earlier pilots, Monet and Sisley were appropriate neighbors because their histories
and subject domains overlap without treating them as interchangeable.
The National Gallery describes Monet as a leading French Impressionist landscape painter and records that he met Sisley in Charles Gleyre's studio. The Met records Sisley's sustained work along the Seine, in a landscape also frequented by Monet and Pissarro, and describes his direct-from-nature practice. See the [National Gallery's Monet biography](https://www.nationalgallery.org.uk/artists/claude-monet), [The Met's *The Seine at Bougival*](https://www.metmuseum.org/art/collection/search/901617), and [The Met's *Allée of Chestnut Trees*](https://www.metmuseum.org/art/collection/search/459121).

Pissarro and Cézanne are a stronger relationship-based pair than a generic “Impressionist versus Post-Impressionist” contrast. The Musée d'Orsay documents more than twenty years of collaboration and mutual influence, including shared motifs in Pontoise and Auvers. MoMA likewise describes the pair working side by side and developing through exchange rather than isolation. See [Musée d'Orsay's *Cézanne and Pissarro 1865–1885*](https://www.musee-orsay.fr/en/program/whats-on/exhibitions/presentation/cezanne-and-pissarro-1865-1885) and [MoMA's *Pioneering Modern Painting*](https://www.moma.org/calendar/exhibitions/112).

## Historical pilot_0 availability audit

The earlier `pilot_0` selection used metadata and rights availability only—never feature separability or generated outputs. A preliminary five-artist screen included Vincent van Gogh, but only about 15 defensible works met the shared-genre and source constraints, below the frozen minimum of 20; Sisley supplied 21 and preserved a defensible landscape neighbor for Monet.

The final reproducible candidate audit contains 194 records from official open-access sources. Eligible counts before the 30-work cap and selected counts are:

| Artist | Eligible candidates | Selected canonical works | AIC | CMA | Met | NGA |
|---|---:|---:|---:|---:|---:|---:|
| Claude Monet | 54 | 30 | 14 | 3 | 0 | 13 |
| Alfred Sisley | 21 | 21 | 6 | 1 | 7 | 7 |
| Camille Pissarro | 40 | 30 | 7 | 3 | 10 | 10 |
| Paul Cézanne | 27 | 27 | 5 | 3 | 10 | 9 |

The selection interleaves institutions before applying the per-artist cap, then assigns work-level train/held-out splits with a fixed seed. Exact candidate decisions, reasons, authority identifiers, source landing pages, rights bases, and selected-work manifests are stored under `configs/pilot_0/`.

## Interpretation boundary

This roster supports only an artist-level development study within the shared outdoor-place corpus. It cannot establish a movement-level effect, rank eras, or generalize to artists as a population. A future movement study would require substantially more artists per movement and a hierarchical design; adding more works by the same four artists would not solve that identification problem.
