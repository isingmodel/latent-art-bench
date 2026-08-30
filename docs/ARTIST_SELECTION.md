# Development-pilot artist selection

## Decision

The pilot targets **artists, not eras or movements**. “Impressionism” and “Post-Impressionism” remain descriptive metadata, but they are too broad to define the pilot estimand. The actual question is whether a generated distribution approaches a named artist's held-out distribution while remaining closer to that artist than to a historically defensible neighbor under one shared content domain.

The frozen pairs are:

- Claude Monet ↔ Alfred Sisley
- Camille Pissarro ↔ Paul Cézanne

The common corpus view is `landscape_and_outdoor_place_scene`. This is a genre/content control, not a fifth target label.

## Why these pairs

Monet and Sisley are appropriate neighbors because their histories and subject domains overlap without treating them as interchangeable. The National Gallery describes Monet as a leading French Impressionist landscape painter and records that he met Sisley in Charles Gleyre's studio. The Met records Sisley's sustained work along the Seine, in a landscape also frequented by Monet and Pissarro, and describes his direct-from-nature practice. See the [National Gallery's Monet biography](https://www.nationalgallery.org.uk/artists/claude-monet), [The Met's *The Seine at Bougival*](https://www.metmuseum.org/art/collection/search/901617), and [The Met's *Allée of Chestnut Trees*](https://www.metmuseum.org/art/collection/search/459121).

Pissarro and Cézanne are a stronger relationship-based pair than a generic “Impressionist versus Post-Impressionist” contrast. The Musée d'Orsay documents more than twenty years of collaboration and mutual influence, including shared motifs in Pontoise and Auvers. MoMA likewise describes the pair working side by side and developing through exchange rather than isolation. See [Musée d'Orsay's *Cézanne and Pissarro 1865–1885*](https://www.musee-orsay.fr/en/program/whats-on/exhibitions/presentation/cezanne-and-pissarro-1865-1885) and [MoMA's *Pioneering Modern Painting*](https://www.moma.org/calendar/exhibitions/112).

## Availability audit

Selection used metadata and rights availability only—never feature separability or generated outputs. A preliminary five-artist screen included Vincent van Gogh, but only about 15 defensible works met the shared-genre and source constraints, below the frozen minimum of 20; Sisley supplied 21 and preserved a defensible landscape neighbor for Monet.

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
