# Why do generated paintings differ from painter references?

**A mechanism-focused research proposal, 8 September 2026**

The most useful next question is whether a painter name makes a generator less
responsive to differences between scene instructions. Our results suggest that
this can happen in measured image properties even when repeated generations of
the *same* scene remain variable. A second, separate question is how much of the
original/generated gap comes from digital reproduction and measurement. These
questions offer a stronger research direction than another broad model ranking.

This report uses “clues” for the requested “smokes”: observations that discriminate
between explanations, without yet establishing a cause. It combines primary-paper
reading with numerical and request-level case studies from the completed project.
It proposes a successor study; no new images, feature extraction, human judgments,
or generation spending were added. Case studies below are numerical and metadata
cases, not claims from newly inspecting the paintings visually.

## 1. What difference are we trying to explain?

There are three distinct outcomes:

1. **Reference discrepancy:** how far generated and reference distributions differ
   in the measured features.
2. **Prompt response:** how adding a painter name changes generated images while
   keeping the scene description fixed.
3. **Artistic interpretation:** whether viewers perceive the difference as painter
   style, composition, mark-making, content, reproduction quality, or something else.

The current study measures the first two. The third remains unvalidated. Its
strongest evidence comes from the controlled collection: 1,006 generated images,
70 Monet/Cézanne references and 221 separate development works. Earlier exploratory
collections help motivate the question but should not be pooled into this design.
The [paper](../paper/paper.pdf) and
[computational revision](../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/REPORT.md)
give the complete methods and results.

The observed comparison is approximately

\[
P\{\phi[M_R(W)]\mid A,\text{reference selection}\}
\quad\text{versus}\quad
P\{\phi[M_G(G(B,A,Z;S))]\mid\text{prompt design}\}.
\]

Here \(W\) is a physical work, \(M_R\) its reproduction history, \(G\) the image
service, \(M_G\) its delivery processing, \(B\) a scene brief, \(A\) artist
conditioning, \(Z\) generation variability, \(S\) service state, and \(\phi\) our
measurement pipeline. Reference selection also determines which periods, subjects
and works enter the comparison. This is a bookkeeping model, not an identified
causal decomposition. Energy discrepancy is nonlinear: there is no defensible
“percentage caused by capture” obtainable by subtracting arbitrary ablations.

Matching three broad scene classes helps, but does not match viewpoint, palette,
career period, support, working method or capture. Nor is a request for a recognizable
painting in an artist's style necessarily a request to sample that artist's oeuvre.
That mismatch between a conditional generation task and the reference distribution
is a fundamental candidate explanation, before invoking a defect in a model.

## 2. What the paper readings contribute

This is a focused mechanism review, not a systematic review or a claim of priority.
The following notes identify the versions and methods inspected. Links lead to
primary sources. Findings in open diffusion models are not evidence about the
undisclosed internals of Nano Banana 2, FLUX.2 Max or the OAuth service.
Version labels v1/v2/v3 identify the inspected arXiv text; venue labels identify
publication, without implying that each linked manuscript was checked against an
identical proceedings version.

| Reading | Relevant evidence | Implication for this project |
| --- | --- | --- |
| [Kim et al., PNAS 2026](https://pubmed.ncbi.nlm.nih.gov/42497200/), published Results and Methods | Across 72,447 paintings, CLIP context-rich vectors and autoencoder vectors have different historical organization. The image-to-image experiment uses 500 sources per century, subsequent-century keywords versus an empty prompt, and model-based temporal evaluation. | Context deserves an explicit experimental role. This does not show that artist naming recovers an oeuvre distribution, or that our 31 features capture historical meaning. |
| [Somepalli et al., *Investigating Style Similarity in Diffusion Models*, ECCV 2024](https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/08294.pdf), §§4–7; [preprint v1](https://arxiv.org/html/2404.01292v1) | CSD is trained on 511,921 images and 3,840 style tags. Artist retrieval and content-constrained generation investigate style similarity; two-artist experiments show unequal artist dominance and recurring subject tendencies. | Artist and subject associations need not be independent. A style embedding trained with artist labels would be an additional instrument, not a neutral ground truth. The preprint has a different title and additional qualitative examples. |
| [Ho and Salimans, *Classifier-Free Diffusion Guidance*, v1](https://arxiv.org/html/2207.12598v1), §§3–4 | Guidance sweeps in class-conditioned ImageNet experiments change the quality–variety tradeoff and visual properties such as saturation. | Sampling can change distributional spread. Adding an artist name is not an intervention on the guidance parameter. |
| [Karras et al., *Guiding a Diffusion Model with a Bad Version of Itself*, NeurIPS 2024, v3](https://arxiv.org/html/2406.02507v3), §§2–3, 5.2 and Appendix B.2 | Synthetic and image experiments distinguish removing poor samples from dropping legitimate variation. Same-condition autoguidance preserves more variation than ordinary classifier-free guidance in tested settings. | Reduced variation is not an inevitable consequence of improved quality. A controlled guidance intervention could test one mechanism on an inspectable model. |
| [Clark et al., *Directly Fine-Tuning Diffusion Models on Differentiable Rewards*, ICLR 2024, v2](https://arxiv.org/html/2309.17400v2), §§4–5 and Appendices B.1/B.8 | Reward optimization changes rendering tendencies across subjects; the paper documents excessive detail and eventual diversity collapse under some aesthetic optimization. | A shared preference for a particular finish could affect many scenes. Our services' actual reward functions and training histories are unknown. |
| [Rombach et al., *High-Resolution Image Synthesis with Latent Diffusion Models*, CVPR 2022, v2](https://arxiv.org/html/2112.10752v2), §§3.1–3.2, 4.1 and Appendix D.2 | Generation in a compressed representation trades computation against reconstruction fidelity. The autoencoder uses perceptual and patch-adversarial losses, not pixel reconstruction alone. | Representation and decoding can alter local statistics. “Diffusion just smooths paintings” is too simple: training also encourages plausible fine detail. |
| [Parmar et al., *On Aliased Resizing and Surprising Subtleties in GAN Evaluation*, CVPR 2022, v3](https://arxiv.org/html/2104.11222v3), §§3–4 | Controlled resizing changes evaluation features. In one JPEG-trained LSUN experiment, compressing generated outputs improves FID from 4.00 to 3.48 without changing the generator. | Measured proximity can improve through processing compatibility. Its FID magnitudes do not transfer to our energy metric. |
| [Corvi et al., *Intriguing Properties of Synthetic Images: From Generative Adversarial Networks to Diffusion Models*, CVPR Workshops 2023, v2](https://arxiv.org/html/2304.06408v2), §4 | Spectral patterns vary with generator and postprocessing; generated images can inherit compression traces from training images. | Multiscale texture clues may reflect delivery or learned reproduction statistics. A spectral peak alone does not identify a proprietary architecture. |
| [Asperti, *On the Separation of Human and AI-Generated Images in CLIP Embedding Space*, 2026 preprint, v1](https://arxiv.org/html/2608.25609v1), §§5, 8–10 | Art datasets separate in CLIP; multiscale descriptors predict part of that variation, and inversion probes its image manifestations. Training-objective interpretations are explicitly speculative in §10.2. | Highly relevant adjacent work: separation can involve subtle image statistics. Additional separation does not itself validate artistic meaning. |
| [Wang et al., DIRE, ICCV 2023, v1](https://arxiv.org/html/2303.09295v1), §3.2 and §4 | A classifier uses inversion/reconstruction error maps for real/generated detection. | A candidate probe of reconstruction behavior, with the implementation caveat immediately below. |
| [Ricker et al., AEROBLADE, CVPR 2024, v2](https://arxiv.org/html/2401.17879v2), §§4–5 and supplement §9 | Autoencoder-only reconstruction supports detection. A separate DIRE reanalysis finds near-chance accuracy after matching error-map encoding; arbitrary labels become highly predictable when one half is JPEG-encoded. | The preprocessing of a diagnostic can itself create its apparent success. This challenges a released DIRE implementation, not every reconstruction-based method. |
| [Asperti et al., AI-Pastiche, v1](https://arxiv.org/html/2502.15856v1), §§5–6 | Ideogram receives more human-authorship judgments than DALL·E 3 (49% versus 30%), but lower prompt-adherence scores (0.29 versus 0.36) in separate assessments. Adherence combines content and style through comparative −1/0/+1 judgments. Images were manually selected. | Authorship judgments, prompt adherence and distributional fidelity are different outcomes. These rankings do not demonstrate a causal tradeoff or validate our feature distances. |

Two details materially affect how these papers should guide us. Asperti's lossless
PNG re-saving test preserves already-decoded pixels; it cannot erase earlier JPEG
artifacts or unknown capture processing. That limitation follows from the operation
performed, even though the paper gives it a broader interpretation. AEROBLADE's
DIRE reanalysis is an unusually direct example of why such distinctions matter.
[Asperti §5.1](https://arxiv.org/html/2608.25609v1),
[AEROBLADE supplement §9](https://arxiv.org/html/2401.17879v2).

Kim's paper is especially useful for formulating a *context intervention*. Its
generated-image evaluation concerns movement along model-derived historical
coordinates, rather than independent proof of period authenticity. The reported
year predictor also assigns modern dates to white noise, so predicted historical
movement needs interpretation controls. Our successor should test whether explicit
scene changes survive artist conditioning, then validate what the change means.
[Kim, published generative Results and Methods](https://pubmed.ncbi.nlm.nih.gov/42497200/).

Access notes: Kim's full published text was read from the retained
`tmp/pdfs/kim2026/published.txt`; the fresh PMC page presented an access challenge,
while PubMed was accessible. AI-Pastiche's publisher returned HTTP 429, so its
method notes refer to arXiv v1, with 12 generators and 73 prompts, not a later
expanded dataset. No access challenge was bypassed. Readings and skeptical checks
were conducted by the coordinator and maintainer-run LLM subagents, not independent
human or institutional reviewers.

## 3. Eight clues in the current results

Unless stated otherwise, values use `primary512/original31`. Energy contrasts are
named minus artist-free, so negative means lower discrepancy. Trace is the sum of
scaled coordinate variances, not a count of artistic styles. The 31 coordinates
comprise 11 color, eight spatial and 12 texture features. The comparisons below
are descriptive selections from the sealed results; they are not new confirmatory
tests. Existing inference remains the eight original conditional tests.

### A. Between-brief contraction can coexist with greater within-brief variation

| Route and painter | Total named/free trace | Within-brief ratio | Between-brief-means ratio |
| --- | ---: | ---: | ---: |
| Nano Banana 2, Monet | 0.697 | 0.749 | 0.685 |
| Nano Banana 2, Cézanne | 0.466 | 0.786 | 0.378 |
| FLUX.2 Max, Monet | 0.331 | 0.309 | 0.337 |
| FLUX.2 Max, Cézanne | 0.460 | 0.489 | 0.451 |
| OAuth, Monet | 0.554 | 0.870 | 0.512 |
| OAuth, Cézanne | **0.651** | **1.139** | **0.583** |

The OAuth Cézanne exception is particularly informative. A universal account in
which naming simply reduces generation randomness cannot describe the observed
decomposition. Different briefs could converge toward a painter-associated palette
or arrangement while repetitions remain variable. Alternatively, the briefs could
retain distinct semantic content while becoming similar only in our features.

These are empirical components estimated with three repetitions per brief.
Between-brief means include sampling noise and differences between the broad
content classes; they are not noise-corrected latent scene effects. The next
experiment must manipulate a scene attribute directly rather than treating this
decomposition as causal evidence. Source: [prompt contrasts][contrasts]; see the
retained [variation figure][variation-figure].

### B. Nano Banana 2 Monet changes direction when the instrument changes

| Measurement | Naming energy contrast | Named/reference trace |
| --- | ---: | ---: |
| 512 pixels, all 31 features | −0.846229 | 0.756286 |
| 512 pixels, no texture (`no_texture19`) | −0.017542 | **1.101387** |
| 256 pixels, no texture | **+0.415938** | 0.771101 |

At 256/no-texture, twice the cross-domain distance term decreases by 0.347073,
but the generated within-domain term decreases by 0.763010. Energy subtracts the
latter, producing the positive contrast. Thus the reversal does not mean that
every generated/reference pair became farther apart. It illustrates why proximity
and contraction must be studied together.

This is evidence of representation dependence, not proof that texture causes the
artist effect. Removing coordinates changes the instrument; it does not remove
brush marks from images. Distances in different feature views also have different
units and cannot be read as a causal percentage decomposition. The FLUX comparisons
and Nano Banana 2 Cézanne keep their energy direction across all 12 fixed
pipeline/view combinations. Source: [prompt contrasts][contrasts].

### C. FLUX Monet has a specific spatial signature

In generated images, `orientation_entropy` variance falls from **9.392255 to
1.738682**, and `quadrant_jsd` variance from **6.579312 to 0.975202**. Together they
account for **67.19% of this cell's total trace decrease**, computed by subtracting
the saved coordinate contributions. These are scaled variances, not the raw
feature means.

The same coordinate does not behave uniformly across routes: `quadrant_jsd`
variance rises from 4.212839 to 4.394664 for Nano Banana 2 Monet, and from 1.810840
to 3.067558 for OAuth Cézanne. The useful lead is a route-specific change in spatial
statistics. Whether that corresponds to repeated compositions requires independent
layout coding; borders, content and processing can also change these features.
Source: [trace contributions][trace], `domain=generated`, `level=coordinates`.

### D. Relative painter alignment in feature space can coexist with limited distribution matching

OAuth's equal-content painter interaction changes from **−0.044306 artist-free
to −1.802182 named**, while its primary naming energy effects are only −0.233883
for Monet and −0.056055 for Cézanne. The interaction contrasts matching and
cross-painter energies jointly; it is not a per-image painter classification.

For OAuth Monet, detailed named prompts have trace **13.165642**, versus
**8.429432** with generic named prompts. Their energies are close, 2.332971 versus
2.370442; the preserved paired contrast is −0.037471, Holm-adjusted p=1. These
observations suggest that artist-associated alignment and scene-conditioned spread
can change separately. They do not establish equivalence between those energies.
Specificity uses equal content thirds, whereas primary proximity uses each
painter's reference-class masses. Sources: [specificity][specificity],
[metric cells][cells] and [original endpoints][endpoints].

### E. The reference mixture changes the apparent success

Monet's references contain **21 water, four built and 13 land** works; Cézanne's
contain **three, 11 and 18**. Generated detailed cells have 24 per class before
weighting. Removing water changes OAuth Monet's naming contrast to **+0.361932**;
removing land changes OAuth Cézanne's to **+0.594233**. Even deleting one Cézanne
reference, `wikidata:Q64366377`, changes its primary contrast from −0.056055 to
+0.067609.

Canonical subjects and reference selection are plausible contributors. However,
class deletion changes the target and removes corresponding generated briefs;
it does not isolate a causal property of the generator. A large new generation
sample against the same thin strata would not resolve this. Source:
[reference influence][influence] and the [reference design][main-design].

### F. Absolute separability has a concrete reproduction alternative

All **576 paid outputs are square**, compared with **zero of 70 references**.
A square/nonsquare metadata rule therefore has balanced accuracy **1.0** in every
paid cell. All reference capture workflows remain unresolved, and 56 references
lack embedded color profiles. Texture contributes 49.01% of Monet reference trace;
`lbp_entropy_8` alone contributes 17.37%.

This demonstrates a domain mismatch. It does not demonstrate that the existing
31-feature classifier uses aspect ratio, or that capture explains its entire
performance. Moreover, matching shape within a paid route means shape alone cannot
explain its named/free contrast.

A second warning concerns the meaning of detection: Monet FLUX→OAuth linear
transfer has mean within-fold AUC **0.953436→0.967593** under naming, while
fixed-threshold balanced accuracy falls **0.903509→0.873904**. A threshold can transfer
worse even when ranking improves. Sources: [square rule][square],
[metadata counts][metadata], [trace contributions][trace], [transfer][transfer].

### G. One exact scene has a treatment-linked service-metadata pattern

Every OAuth request asks for medium quality, but **424 returned images report
low quality and six report medium**. All six medium reports belong to the
artist-free `built04` scene: closely spaced houses on a steep village slope.
They span both painter-labelled allocation groups and all three repetitions:
`slot0138`, `slot0150`, `slot0478`, `slot0492`, `slot0825`, `slot0848`.

For Monet repetition zero, `slot0478` is artist-free/medium; `slot0480` is
detailed-named/low. The payload changes only by adding the Monet style sentence.
The generic-named `slot0479` is also low. The artist-free payload itself contains
no painter name, so its two painter-labelled groups are repeated identical prompts.

This is a specific clue to prompt-dependent rendering, routing **or reporting**.
Returned metadata might be inaccurate; these records cannot establish actual
quality settings. Excluding the six images or adjusting for returned quality would
condition on a possible consequence of treatment, not isolate a pure semantic
effect. Sources: [attempt dispositions][attempts], joined by `request_id` to
[requests][requests]. This join is a new descriptive reading of existing records.

### H. Lower discrepancy does not guarantee local coverage

FLUX Cézanne named has energy **0.804227** and generated/reference trace **0.492197**.
With 72 generated queries against 32 references, its coverage changes from
**0.4375 to 0.7500 to 0.96875** as neighborhood size changes from k=1 to 3 to 5.
With identical reduced sets of 15 reference anchors and equal 15-image query
counts over 100 draws, median k=3 coverage is **0.8000 generated versus 0.933333
held-out real**. Both medians reach 1.0 at k=5, but individual draws range from
0.6667 to 1.0 for generated queries and 0.8667 to 1.0 for real queries.

This is compatible with concentration near common reference regions while missing
some local variation. Sparse reference neighborhoods and reproduction noise remain
rivals. Saturation at a broad neighborhood is not distributional equivalence.
Sources: [metric cells][cells], [coverage][coverage],
[held-out controls][heldout].

## 4. Candidate explanations, ranked by what we can currently support

| Candidate | Present evidential status | Distinguishing prediction |
| --- | --- | --- |
| **A painter-associated rendering prior reduces responsiveness to briefs** | Leading mechanism hypothesis. Compatible with A, C and D; semantic suppression is untested. | An explicit visual change produces a smaller response after naming. Preserved content with contracted color/texture would indicate rendering consistency rather than content loss. |
| **An added style instruction competes with the scene instruction** | Unresolved rival: the current name toggle adds a sentence. | A painter-free style clause or a change in instruction position produces similar attenuation, weakening an artist-specific explanation. |
| **Capture, delivery and measurement create part of the observed gap** | Directly observed nuisance differences and sensitivity in B/F; their causal contribution is unquantified. | Same-work alternate captures and symmetric processing move the reference gap substantially, potentially without changing judged style. |
| **The sampled painter distribution and the prompt mixture target different contexts** | Strong design concern, concretely exposed by E/H. | Results depend on fine-content or career-period matching and replicate poorly across independent reference panels. |
| **The service changes processing in response to prompts** | Specific metadata association in G; actual rendering mediation unverified. | A randomized name toggle changes auditable processing settings or rendered properties under a reproducible endpoint. |
| **Guidance or preference training favors stereotyped, polished outputs** | Demonstrated as possible in the cited open-model studies; not identified here. | Manipulating actual guidance or a documented preference adapter changes response attenuation while other settings remain fixed. |
| **Compression/decoding or learned reproduction statistics alter fine-scale structure** | Mechanistically plausible from open-model work and B; proprietary architecture unknown. | A known encoder/decoder changes both domains and their discrepancy in prespecified ways; this tests compatibility with a processing mechanism, not hidden-service identity. |

Training-set frequency is a possible origin of a painter-associated prior: familiar
motifs, periods or reproductions may be represented unequally. Current data cannot
distinguish frequency, captioning, optimization and inference effects. Artist
recognizability is also not evidence of memorization; that would require an
appropriate source-overlap investigation. Likewise, absence of a physical canvas
does not make reproduction statistics impossible to synthesize. We observe digital
surrogates, and a model can learn their appearance.

The central distinction is **successful stylistic consistency versus loss of
responsiveness**. If different requested scenes remain different to viewers while
sharing a coherent palette or mark pattern, lower feature variance need not be a
failure. If naming suppresses explicitly requested changes, and that suppression
also prevents reaching valid reference regions, the distribution gap has a more
substantive interpretation.

## 5. The proposed research idea

**Working title: “Artist conditioning and visual responsiveness: separating
distribution contraction from reproduction artifacts.”**

The primary hypothesis is that adding an artist name changes the transmission of
specific visual instructions into generated images. A descriptive model is

\[
X_{a,b,r}=\mu_a+H_a s_b+\epsilon_{a,b,r},
\]

where \(s_b\) represents requested differences between scenes and \(H_a\) their
transmission into measured features. A smaller response in some directions can
coexist with larger repetition noise \(\epsilon\). This is a motivating model,
not a fitted result; smaller empirical between-brief variance alone does not
identify \(H_a\), and a changed prompt mixture can produce the same observation.

The contribution would be to identify *which requested differences are attenuated*,
test whether that attenuation limits access to the reference distribution, and
separate it from reproduction effects. Merely showing another separated scatter
plot would add little to the art-separation literature. Kim motivates the role of
context; the new target is controlled responsiveness within a painter-style task,
tested against independently supported reference ranges and perceptual judgments.
The initial color experiment below examines a formal property; it does not
operationalize Kim's historical or semantic context mechanism.

### Phase 1: sharpen the diagnosis without buying images

Create a new, explicitly post-result analysis scope using the saved vectors and
requests. Inspect brief-level named-minus-free mean displacements, asking whether
briefs move in a shared direction and which coordinates account for convergence.
Report all briefs, including counterexamples. Regression must explicitly account
for measurement error: three-sample means are noisy, and ordinary regression can
manufacture apparent attenuation. Independent repetition splits can diagnose
shared-noise effects but do not themselves fix regression dilution. A repeated-
measures or instrumental-variable estimator would need its own stability analysis.

Use the built04 quality pattern as a service-integrity question before making a
new OAuth mechanism claim. Reading metadata costs no generation credit; a live
replication would be a separate experiment, with its own bounds. If the endpoint
cannot verify fixed processing, retain a service-level interpretation.

Select future example panels by a recorded rule—representative briefs, strong
effects and counterexamples—not by visual attractiveness. New human examination
requires the appropriate access scope. The report has not carried it out.

### Phase 2: a small randomized response experiment

Prioritize **one route and controlled instructions**, keeping Monet and Cézanne.
FLUX.2 Max is a reasonable first candidate because its proximity directions survive
all fixed views and its spatial contraction is large. This is a deliberate
diagnostic choice based on current results, not an unbiased model ranking or an
assumption that a future service version is unchanged. Before generation, establish
that the selected attribute has a meaningful reference range in matched scene
strata and that a blinded assessment is feasible. If those requirements fail,
prioritize reference validation; a response experiment alone would drift into a
generic prompt-control benchmark.

A bounded candidate design is **192 images**:

\[
6\text{ scene templates}\times2\text{ opposed instructions}\times
4\text{ conditions}\times4\text{ repetitions}=192.
\]

The conditions are artist-free, an added generic style clause, Monet-named and
Cézanne-named: 48 images each. Share the painter-free controls across both painter
contrasts. The generic clause, matched approximately in length and placed at the
same prompt position, tests whether an extra rendering instruction alone changes
the response. Its wording must be fixed before generation. It is a defined
comparison prompt, not a universally neutral semantic baseline. Jointly randomize
all eight style-condition × instruction-polarity cells within each template and
repetition block; account for shared-control covariance. Randomizing polarity too
prevents vivid/muted instructions from systematically coinciding with service time.

Use two templates in each existing content class. For the cleanest initial
experiment, manipulate **one attribute across all six templates: muted versus
vivid color**, with the subject and layout wording otherwise identical. The
predefined primary coordinate is `chroma_median`, using a fixed development scale.
There is a modest numerical bridge: FLUX Monet's variance on this coordinate is
**1.095224 in references, 0.541599 artist-free and 0.444136 named**; Cézanne's is
**0.719729, 0.403752 and 0.257599**, respectively ([saved contributions][trace]).
These contrasts motivate examining the supported chroma range, but neither prove
missing tails nor match content or capture.

This yields a narrow controllability pilot with existing features. It is weaker
evidence about composition than case C, and is not a test of semantic adherence.
A subsequent spatial version should use a separate protocol and direct layout
coding; the large spatial clue makes that the next attribute, not a reason to
pool unrelated outcomes into one score.

For painter \(a\) and fixed template \(j\), define each condition's response
\(d_{a,j,c}=\bar x_{a,j,c,+}-\bar x_{a,j,c,-}\), then estimate

\[
\kappa_{a,j}=d_{a,j,N}-d_{j,C},\qquad
\tau_{a,j}=d_{a,j,N}-d_{j,F}.
\]

Here \(x\) is scaled `chroma_median`, N/F/C named/free/generic-clause, and +/−
vivid/muted; the shared controls have no painter subscript. The two painter-specific
averages of \(\kappa\) form the proposed primary family. Report \(\tau\) as the link
to the existing name-toggle study, and \(d_C-d_F\) as the generic-clause diagnostic.
A smaller response under naming than under this generic clause goes beyond that
specific instruction-competition control; it still does not isolate every semantic
difference between the prompts.

Report equal-template averages, every template effect, and every arm's mean and
distribution. These are finite two-level response interactions, not the linear
coefficient \(H_a\) or an internal model constraint. Different baselines, saturation
and the use of an image median can also produce a smaller vivid/muted difference.
Interpret negative \(\kappa\) as attenuation in median chroma only if the control
response is positive and the free arm verifies that the manipulation works.
Otherwise report the actual directions and the failed manipulation check. Do not
exclude templates after seeing that failure. Named-arm reversals are not smaller
positive responses. Prefer differences to unstable ratios; a later middle-level
instruction could help distinguish a shifted operating range from reduced gain.

Fix actual geometry and quality where the endpoint supports them. Follow the joint
randomized order to interleave styles and instruction polarities; record service identity,
time, settings, failures and all attempts. Predefine the technical retry rule and
missingness endpoint. Do not select successful-looking images or remove outputs
because they fail to follow a prompt. Request matching alone does not establish
matching delivered settings, as case G shows.

Four repetitions reduce mean noise somewhat; **192 is a diagnostic cap, not a power
claim**. There are six selected templates per painter, not 192 independent tests
of general prompt behavior. Before collection, use saved variability for a design
simulation, set a meaningful response threshold and the two-painter multiplicity
rule, and distinguish conditional finite-template inference from generalization
to new scenes. Preserve the joint eight-cell block assignment in inference;
do not apply independent sign flips to contrasts that share a control. The old
sharp no-treatment test is not automatically an exact test of a zero interaction;
the factorial estimand and its uncertainty procedure need their own specification. If
affordable precision is inadequate, narrow the claim rather than silently call
the sample sufficient. A second route would double this design to 384 images and
should follow a useful first result, not precede it.

### Phase 3: connect response attenuation to the original paintings

The factorial alone cannot explain the original/generated gap. It must be paired
with two validation tasks:

- **Reference and capture control.** Obtain independently documented alternate
  digital captures of the same works where feasible, and an independently selected
  reference panel with fine-content and period coding. Same-work capture contrasts
  estimate reproduction variability more cleanly than a new unrelated image set.
  Alternate captures must be independently acquired photographs/scans, not URLs or
  derivatives of one master. Record provenance, work condition, capture date,
  framing and color processing, and analyze captures as paired observations of a
  work. Restoration or physical changes between photographs are additional rivals.
  This estimates variability across documented workflows, not an isolated camera
  effect.
  Apply prespecified resolution/encoding operations symmetrically. Report crop and
  padding choices separately because either can change spatial statistics. Lossless
  re-saving is a sanity check, not capture matching.
- **Blinded interpretation and reachability.** Rate perceived vividness without
  prompts; assess scene adherence with the relevant scene instruction; assess
  painter resemblance with identified painter references. Keep naming-condition
  provenance hidden in all three tasks. Establish, using references outside the
  confirmatory endpoint, which chroma ranges occur in valid fine-content strata.
  Test on held-out works whether naming makes supported reference ranges harder
  to reach. Reference rarity, capture instability and uncertainty must remain
  visible; reaching a scalar range does not establish distributional equivalence.

If named outputs respond less but already occupy an appropriate reference range,
that may be beneficial conditioning. If they resist directions needed to represent
valid references, while capture controls and human ratings agree, the proposed
mechanism gains substantive support. Conversely, unchanged prompt response with
persistent feature contraction would weaken this explanation and favor the
measurement or prompt-mixture accounts.

Human evaluation can begin with a balanced subset of the same 192 images; it needs
no additional generated images. Rater sampling, blinding, repeated judgments and
uncertainty require a separate plan. Perceived authorship is not a substitute for
these questions, as AI-Pastiche's separate assessments illustrate.

### Phase 4: attribute a mechanism only with an actual intervention

If responsiveness is established, an inspectable model can separate possible
causes: vary actual guidance at fixed checkpoint, sampler and paired seeds; then
compare a documented preference adapter against its base at fixed guidance.
Keeping the conditioning task constant is essential. Asking a closed model for
“less polished” images is an intervention on the prompt, not on preference training.

A fixed autoencoder round trip applied to both original and generated images can
test compatibility with a processing explanation. Prespecify whether reference
displacements align with the generated-minus-reference direction, whether generated
displacements are smaller, and whether the distributional gap changes. Include
identity and ordinary compression/resizing controls: a generic lossy operation
can contract features too. Similar shifts in both domains can leave their gap
unchanged. This cannot identify the services' unknown autoencoders. The optional
stage needs local compute and a new measurement scope; learned style embeddings
are not required for the initial 192-image experiment.

## 6. What to expand, and what result would change the plan

The recommended expansion axis is **controlled visual instructions plus reference
validation**. Additional painters would broaden external validity but would not
resolve current mechanisms. Additional models would multiply hidden differences.
More repetitions of the existing broad prompts would improve precision without
separating the leading explanations.

| Future outcome | Consequence |
| --- | --- |
| Color response attenuates under naming; human contrast ratings agree | Proceed to the spatial attribute and test reference-range reachability. |
| Feature attenuation occurs but human ratings do not agree | Treat it as an instrument-specific effect; reconsider the artistic claim. |
| Prompt response is preserved despite lower aggregate variance | Favor consistent rendering or prompt-mixture explanations over responsiveness loss. |
| Same-work capture displacements are comparable to the between-domain displacement under a fixed measure | Prioritize reproduction-controlled references; do not interpret displacement ratios as causal percentages of the energy gap. |
| Actual quality/delivery varies with the name toggle | Describe the measured service policy; isolate processing before attributing effects to artist semantics. |
| Open-model guidance or adapter intervention reproduces the effect | Establish that mechanism in the tested open system; proprietary attribution still needs evidence. |
| Interactions or human comparisons remain imprecise | Report an inconclusive diagnostic. A nonsignificant contrast does not establish preserved response, perceptual agreement or disagreement. |

No images should be bought merely to reach 192. Confirm current route availability
and prices, then choose the smallest design that can resolve the planned contrast.
Historical conservative accounting is **$45.6819185 against the former $75 ceiling**;
the arithmetic difference, $29.3180815, is not a verified current API balance or a
cost estimate for this proposal. Human assessment and reference work may be more
valuable than spending that remainder on model breadth.

The current evidence supports a specific working idea: **artist naming may impose
a stable rendering prior that narrows how image properties respond to scenes,
while the reference gap also contains reproduction and sampling differences**.
Whether that constitutes a limitation in artistic imitation depends on the
controlled-response, reference and human tests above. None has yet been performed.

## Evidence pointers and reproducibility

This report leaves terminal evidence unchanged. It reads controlled run
`pdsv1-analysis-20260907` and revision run `pdrv1-numeric-20260907`. The latter's
numeric artifact has SHA-256
`a6596dadb63f2046f0498a754e5db4cf284c748c71337501f38f628e28908c34`.
All quoted values are existing table entries except explicitly described
arithmetic (the two-coordinate 67.19% share and budget difference) and the
request/quality join in case G. No new p-values, image features or fitted models
were computed. Reproduction commands remain in [the analysis catalog](ANALYSES.md).

For exact lookup, select `pipeline=primary512`, `metric_view=original31` and the
stated route/painter unless a case names another view. Internal route labels are
`nano_banana_2`, `flux_2_max`, `oauth_gpt_image_2`; painter labels are `claude_monet`
and `paul_cezanne`. Case B additionally selects `no_texture19` and
`pipeline=resolution256`. All successor experiments above need a new protocol
and the applicable access/collection gates; this proposal does not reopen a
terminal census or authorize execution.

[contrasts]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/prompt_contrasts.csv
[variation-figure]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/plots/variance_decomposition.png
[trace]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/trace_contributions.csv
[specificity]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/specificity_interactions.csv
[cells]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/metric_cells.csv
[endpoints]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/original_endpoints.csv
[influence]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/reference_influence.csv
[main-design]: ../studies/painter_distribution_study_v1/MAIN.md
[square]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/metadata_square_rule.csv
[metadata]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/metadata_counts.csv
[transfer]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/cross_route_transfer.csv
[attempts]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/attempt_dispositions.csv
[requests]: ../data/manifests/painter_distribution_study_v1/pdsv1-main-20260906/requests.jsonl
[coverage]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/coverage_summary.csv
[heldout]: ../reports/painter_distribution_revision_v1/pdrv1-numeric-20260907/heldout_real_controls.csv
