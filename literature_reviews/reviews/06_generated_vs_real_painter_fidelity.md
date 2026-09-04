# Generated-versus-real painter fidelity: focused evidence audit

Review status: full-text or official-method audit of the closest available studies
Protocol alignment: `painter-feature-generation-v1/2.0`; Protocol 2.1 (2026-09-04) replaced the
human coding and scene stratification described in Sections 6.2, 7, and 10 with a frozen metadata
lexicon, uniform work weights, and an automated adherence diagnostic (see `METHOD_DECISIONS.md`
MD-37 to MD-48). The remaining sections apply unchanged.

## Review question

> Which published methods can support a claim that painter-name-conditioned generated images
> reproduce measurable feature distributions of the corresponding painters' real paintings?

The word *reproduce* is deliberately stronger than recognizability. A model can produce an image
that a classifier calls “Monet” while covering only one stereotype, copying a known work, exploiting
a signature, or matching a museum's digitization pipeline. Conversely, a generated set can differ
from every individual real work yet reproduce a broad finite distribution. The unit of the claim is
therefore a generated **set** compared with an authority-backed finite population of physical works,
within one declared content and digital-reproduction frame.

## 1. Bottom line

No reviewed paper provides a validated universal score for generated-to-real painter-distribution
fidelity. The closest studies address adjacent tasks:

1. representation geometry in large art-history corpora;
2. artist/style retrieval or prompted-name recognizability;
3. content/style evaluation for neural style transfer;
4. generic generated-image fidelity and coverage; or
5. training-image copying.

Those methods supply useful components, not a turnkey answer. A defensible study must combine:

- a lawful, deduplicated, authority-backed real-work frame;
- real-only qualification of interpretable measurements;
- absolute generated-to-real distribution equivalence;
- specificity against every other painter in the fixed panel;
- improvement over paired artist-free prompts;
- coordinate-spread and scene-level coverage checks;
- source, capture, content, availability, and dependence controls; and
- a separate exact/near-copy audit.

This architecture remains a prospective proposal until the corpus, measurement qualification, and
whole-decision simulation pass. Literature citations do not turn uncollected data or unvalidated
margins into evidence.

## 2. Direct method audit

| Study | Actual task and scale | Useful contribution | Does not establish |
|---|---|---|---|
| [Kim et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13416963/) | 72,447 paintings, 2,354 painters, 128 periods; 16,384-D SD2-VAE A and 1,024-D CLIP C coordinates | large-scale evidence that learned coordinates contain chronology, painter-label, and context structure | generated-to-real distribution reproduction, source invariance, or oeuvre coverage |
| [Somepalli et al. 2024](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/08294.pdf) | CSD trained on 511,921 images/3,840 tags; artist retrieval and prompted-generation experiments | a style-oriented diagnostic, prototype comparisons, and content-constrained prompting precedent | a universal cosine threshold or complete painter-distribution reproduction |
| [Moayeri et al. 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/63ef323523f3be8b58ed9277cc747485-Paper-Conference.pdf) | set-level CLIP matching and explicit visual tags across artists and generated sets | one-versus-many comparison and interpretable cue audits | that painter-name recognition is unique painterly form or distribution coverage |
| [Wright and Ommer 2022](https://arxiv.org/abs/2207.12280) | ArtFID for neural style transfer using an art encoder, style-distribution FID, LPIPS content, and human comparisons | separation of content preservation from style-distribution similarity | a free text-to-image painter endpoint without a paired content image |
| [Asperti et al. 2025](https://www.mdpi.com/2504-2289/9/9/231) | 953 generated images, 73 prompts, and 12 models | warning that style results vary by model, prompt, and evaluator | a powered painter-conditional distribution test |

The studies agree on one negative lesson: there is no representation-independent “style score.”
Every score inherits its encoder, preprocessing, reference sample, source mixture, and task.

## 3. What Kim et al. contribute—and what they do not

Kim et al. are important because their scale shows that pretrained latent spaces encode substantial
art-historical structure. Their A representation uses the first-stage Stable Diffusion 2 VAE; their
C representation uses a CLIP-family semantic/context space. Within-painter proximity or painter
classification in these spaces can demonstrate label-associated signal.

That is not the present endpoint:

- A mixes color, layout, depicted content, resizing, codec/source effects, and the VAE's training
  geometry;
- C mixes semantics, iconography, web-text association, chronology, and potential training exposure;
- A and C use different models and preprocessing, so their difference is not an experimental
  decomposition of artistic “form” and “context”;
- classification and nearest-neighbour retrieval do not test whether a generated set covers the
  target painter's within-oeuvre distribution; and
- square warping and catalogue-image heterogeneity can alter the very coordinates being compared.

The released repository at commit
[`7da12358cf34dad2184f357a048c2cf114b3c4e0`](https://github.com/aljinny/art-history/tree/7da12358cf34dad2184f357a048c2cf114b3c4e0)
also does not provide a complete executable artifact contract for exact A/C replication. The A
script has unreachable setup and an undefined model reference, and the C description does not pin
one unambiguous identical checkpoint realization. A repaired implementation would be a named local
adaptation, not the authors' exact latent realization.

Protocol consequence: Kim A and C are diagnostic evaluator families. They may reveal agreement or
representation dependence, but they cannot qualify the primary measurement, set the sample size, or
rescue a failed interpretable family.

## 4. CSD, attribution, and ArtFID answer adjacent questions

### 4.1 CSD and attribution test recognizability

CSD is more targeted to style-associated cues than generic CLIP. Its WikiArt evaluation still uses
artist identity as a proxy and random work splits. Prompted-artist validation generally treats the
requested name as the expected style label. ArtSavant-like set voting and explicit tag matching are
useful diagnostics, but a decision can be driven by subject, period, source, signature, or encoder
exposure.

Protocol consequence: CSD, CLIP, artist retrieval, and tag diagnostics explain concordance and
failure. They do not define the positive claim.

### 4.2 ArtFID separates content and style in a different design

ArtFID combines a style-distribution Fréchet term with LPIPS content preservation. That separation
is conceptually useful, but neural style transfer has a paired content input. Free text-to-image
generation does not. LPIPS therefore cannot be imported as a content-preservation endpoint without
changing the scientific question. The Fréchet term also depends on the learned representation,
Gaussian approximation, and sample size.

Protocol consequence: code content adherence separately from feature-distribution fit. Keep ArtFID
and FID diagnostic rather than binding.

## 5. The exact construct supported by the evidence

The study can estimate only:

> broad-scene-weighted digital-surrogate feature reproduction for Monet, Sisley, Pissarro, and
> Cézanne, in the closed accessible authority-backed frame, under one exact model, render contract,
> prompt census, and registered seed/request population.

It cannot identify a timeless painterly essence, physical brushwork, pigment or surface structure,
intent, authorship, or the complete oeuvre. Residual subject matter, period, conservation,
photography, and source workflow remain part of the finite target and must be disclosed.

This narrower construct is preferable to an impressive but undefined “style similarity” claim.

## 6. Real-corpus implications

### 6.1 One physical work is one unit

A museum master, Commons mirror, thumbnail, crop, book scan, and re-encoding may all represent one
painting. Counting files inflates sample size and makes source quirks look like painter replication.
The corpus therefore needs a graph:

```text
source row
  -> authority object/accession
  -> physical work
  -> capture or master family
  -> provider asset
  -> delivered file
```

Only the physical work enters the real distribution once. A second image belongs in the
independent-capture disturbance panel only when provenance demonstrates a genuinely separate
digitization event.

### 6.2 Large metadata counts are not the study sample

Discovery identifiers must survive exact creator attribution, painting status, oil-on-canvas
support, outdoor-place eligibility, item-level reuse rights, sufficient geometry, complete-view and
border checks, work deduplication, historical-exposure separation, common-scene support, and source
crossing. A claim such as “3,190 records found” is a search result, not 3,190 eligible paintings.

Protocol 2.0 therefore exhausts a frozen union of named sources and retains all eligible works. It
does not stop at a convenient quota and does not force equal painter counts. It requires at least
three common broad-scene groups, at least 20 confirmation works per painter in every retained group,
equal-scene effective sample size of at least 100 per painter, and adequate source/capture crossing.
These are screening floors; whole-decision simulation must still show adequate operating behavior.

### 6.3 Source crossing is a validity condition

If one painter is mainly represented by one museum workflow and another painter by another, a
successful comparison can be a source detector. Each painter therefore needs at least two
authority/capture workflows, the painter-by-workflow graph must be connected, a binding workflow
must occur for at least two painters, and no workflow may carry more than 0.80 of one painter's
equal-scene weight. Supported leave-one-workflow analyses must preserve the decision and direction.
Failure narrows or blocks the painter claim; adding more files from the same workflow does not cure
it.

## 7. Content and prompt implications

Painter and subject matter are historically entangled. Exact iconographic matching can remove
genuine practice and create sparse cells; ignoring content allows water, architecture, trees, and
horizons to dominate the result. Protocol 2.0 uses a declared middle ground:

- one outdoor-place domain;
- four broad visible scene groups;
- retention of every group with adequate confirmation support for all four painters;
- equal mass across retained groups and uniform mass across works within group; and
- four exact prompt paraphrases per group, fixed before active visual labels.

The artist-free and four named conditions use the same templates, seeds, and settings. The named
string differs only by the registered painter-name insertion. This paired contrast estimates what
adding the name changes under the frozen generator; it does not by itself establish absolute fit.

Every off-topic output remains assigned to its registered scene cell in the primary analysis.
Removing such outputs would condition on a post-generation success event and could manufacture
similarity. Adherent-only results are sensitivity analyses. A positive claim additionally requires
high overall and per-cell adherence.

## 8. Primary feature architecture

The literature supports candidate measurements, not invariant signatures. Protocol 2.0 therefore
requires three interpretable families:

1. **color organization**: robust Lab luminance/chroma summaries, chromatic fraction, circular hue
   concentration/entropy, and multiscale CIEDE2000 spatial differences;
2. **spatial/orientation organization**: robust Fourier slope/residual/anisotropy plus Scharr and
   PHOG orientation summaries; and
3. **digital texture organization**: stationary-wavelet scale energies, slope/curvature,
   rotation-invariant LBP summaries, and multiscale local variation.

The image pipeline preserves aspect ratio, uses one declared normalization, treats missing ICC as
an explicit assumption, and forbids painter-specific scaling. Coordinates are scaled once from the
equal-painter new-development mixture. A missing, nonfinite, or zero-IQR coordinate fails its
family rather than disappearing after inspection.

Every family must pass deterministic fixtures, perturbation checks, untouched qualification,
independent-capture tolerance, and source/crop sensitivity before generation. Calling catalogue RGB
“brushstroke measurement” would exceed the evidence; the correct term is digital texture.

## 9. Distribution statistics

### 9.1 Why energy distance is primary

[Gretton et al. 2012](https://www.jmlr.org/papers/v13/gretton12a.html) provides the kernel MMD
framework; [Székely and Rizzo 2013](https://doi.org/10.1016/j.jspi.2013.03.018) provides the
distance-based energy-statistics foundation. Neither validates the coordinate system, margin, or
sampling design. Those must be justified separately.

Energy distance is appropriate here because it compares the whole distribution in a fixed,
low-dimensional, commonly scaled family. Protocol 2.0 uses:

- the exact real-real term over the complete accessible finite population;
- the exact real-generated cross sum for observed generated draws;
- a generated self term over different independent repetition blocks; and
- equal averaging across retained scene groups.

The raw estimator is not clipped if finite-sample variation makes it slightly negative. Real works
are not bootstrapped because the estimand is the observed finite frame, not an imagined random
sample from a complete oeuvre.

### 9.2 Why one distance is still insufficient

A distribution distance can look favorable under contraction, an oversized margin, or shared
movement-level features. For every painter and every primary family, the protocol therefore binds:

1. absolute equivalence to its own real target;
2. superiority to each of the other three painters' real targets;
3. improvement over the matched artist-free control;
4. simultaneous median and IQR coverage for every coordinate;
5. equivalence within every retained scene group;
6. leave-one-work influence stability; and
7. leave-one-workflow robustness.

All three families must pass. An average cannot cancel a failed family or painter.

### 9.3 Margins cannot be chosen from the desired answer

Failure to reject a difference is not equivalence. Protocol 2.0 derives each family margin only from
new-development split stability and an independent-capture tolerance bound, then tests it
unchanged on untouched qualification data. The margin must also be no more than half the
smallest wrong-painter qualification distance. Confirmation and generated outputs cannot widen it.

The repetition count is chosen only after margins are fixed. Whole-decision simulation evaluates
the full conjunction under favorable matching-painter data and adverse wrong-painter, pooled-
control, central-mode-collapse, dispersion-collapse, coordinate-shift, and source-shift scenarios.
The smallest passing value in `{25, 50, 75, 100}` is used. If none passes, generation stops.

### 9.4 Precision/recall and FID remain diagnostics

[Kynkäänniemi et al. 2019](https://proceedings.neurips.cc/paper_files/paper/2019/hash/0234c510bc6d908b28c70ff313743079-Abstract.html)
and [Naeem et al. 2020](https://proceedings.mlr.press/v119/naeem20a.html) distinguish fidelity-like
and coverage-like neighborhood behavior. Their estimates vary with representation, dimension,
sample size, neighborhood size, hubness, and outliers. FID has additional Gaussian and finite-sample
problems. These statistics can expose a failure mode, but they do not override the registered
interpretable-family decision.

## 10. Dependence, missingness, and multiplicity

The same physical work, its crops, and alternate deliveries are not independent. Generated outputs
sharing a seed, balanced wave, provider episode, or retry history are also dependent. Local
inference resamples whole registered repetition blocks. Remote inference resamples complete balanced
common-shock waves and requires at least 25 defensibly independent blocks. A provider change or
shock crossing only part of a wave makes the endpoint inconclusive.

Historical generation showed that refusals can leave requested-label cells incomplete. Conditioning
on successful or adherent outputs changes the target distribution and can hide model-specific
missingness. Protocol 2.0 adopts a strict positive-claim rule: 100% of the registered grid must be
present, decodable, and feature-analyzable. Incomplete runs remain reportable but cannot receive a
conditional reproduction label.

All binding continuous endpoints enter one frozen max-studentized family with 9,999 whole-block
resamples. Zero or nonfinite resampling variance is inconclusive, not exact certainty. The endpoint
inventory, one-/two-sided direction, seed, order statistic, and ties-to-failure rule are frozen at
G0 after the retained scene count is known.

## 11. Copying is not reproduction

[Pizzi et al. 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Pizzi_A_Self-Supervised_Descriptor_for_Image_Copy_Detection_CVPR_2022_paper.html),
[Somepalli et al. 2023](https://openaccess.thecvf.com/content/CVPR2023/html/Somepalli_Diffusion_Art_or_Digital_Forgery_Investigating_Data_Replication_in_Diffusion_CVPR_2023_paper.html),
and [Carlini et al. 2023](https://www.usenix.org/conference/usenixsecurity23/presentation/carlini)
motivate a separate exact and near-copy search. A copied real work can improve distance while
providing poor evidence of generative coverage. Generated-to-generated duplicates also reveal
contraction; removing them would conceal it.

The detector must be calibrated on known transformations in development and validated
unchanged on qualification. Every lawful development, qualification, auxiliary, and
confirmation work is searched using frozen whole-image and crop rules. Two blinded reviewers plus a
third for disagreements adjudicate candidates. Any confirmed searched-corpus real-work copy blocks
the positive claim. No hit can only mean “none found in this finite searched corpus”; it cannot rule
out copying from an opaque training set.

## 12. Evidence-grounded execution stack

1. Freeze and exhaust the named metadata sources; keep raw receipts and one terminal disposition per
   candidate.
2. Reconcile records to physical works, verify authority attribution, oil-on-canvas support, rights,
   geometry, and capture ancestry, then acquire only eligible lawful images.
3. Create masked derivatives; double-code outdoor-place eligibility and broad scene; preserve both
   raw streams, reliability, ambiguity, missingness, and later adjudication.
4. Retain all commonly supported scene groups and all eligible works; verify ESS, source crossing,
   influence, and the independent-capture panel. Do not force equal painter counts.
5. Split only historically exposed works into development and qualification. Keep newly eligible,
   unexposed confirmation pixels and features sealed from method and generation analysts.
6. Qualify all three feature families, freeze common scaling and margins, validate on historical
   qualification, and choose `R` by whole-decision simulation.
7. Freeze one exact model, all retained prompts, render settings, paired seeds, request order,
   failure policy, copy detector, and endpoint inventory.
8. Generate the full five-condition grid without screening, rerolling, replacement, or deduplication.
9. Double-code generated adherence and complete the copy audit while confirmation features remain
   sealed.
10. Open confirmation once and execute the frozen simultaneous decision; report every painter,
    family, scene, source, quality gate, and limitation.

## 13. Evidence-based conclusion

The best current design does not prove in advance that a model reproduces Monet, Sisley, Pissarro,
or Cézanne. It defines what evidence would be strong enough to support that narrow statement and
what observations would defeat it. Its safeguards are intentionally asymmetric: more metadata rows,
one attractive example, one high classifier score, or one favorable learned encoder cannot create a
positive conclusion. The result must survive lawful corpus construction, real-only measurement
qualification, absolute and relative distribution tests, coverage, content, source, completeness,
and copying checks as one preregistered conjunction.

At the time of this review, active admissions, image downloads, qualified feature families,
registered generations, and generated-versus-real results are all zero. The literature supports the
protocol architecture; it does not substitute for executing it.
