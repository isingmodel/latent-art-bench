# Contribution and literature matrix

Checked 2026-09-07. This focused comparison supports revision step 1; it is not a
systematic review or a priority claim. Method details below follow the exact
accessible versions. “Not established here” records a limit of this comparison,
not proof that the authors omitted every possible control.

| Work and inspected version | Question, unit and prompting | Representation and control target | Human evidence / accessible material | Difference from the present contribution |
|---|---|---|---|---|
| [Asperti et al., AI-Pastiche, arXiv:2502.15856v1](https://arxiv.org/html/2502.15856v1), §§3–5 | Broad artistic imitation: 73 shared prompts across 12 generators in this version. | Image/prompt-level authenticity and adherence; authentic comparison images from the National Gallery of Art. Independent capture matching is not established by the inspected survey design. | Actual human surveys: authenticity classification and a separate smaller-group prompt-adherence task. The paper describes dataset access. | Direct adjacent imitation research; our paid randomized named/free contrast and distribution/variance decomposition answer a different question. Our absent human validation is a limitation, not an advantage. |
| [Fu et al., AI-WikiArt, arXiv:2508.01408v1](https://arxiv.org/html/2508.01408v1), §3 | Attribution and generated-image detection using 39,530 original paintings from 128 artists. Captions of originals condition three text-to-image generators. | Six VLMs answer correct/incorrect artist questions; paired source-caption content design, not a randomized artist-name removal study. | Evaluation is by VLMs, not an independent human panel. Authors link prompts, images and results in [their repository](https://github.com/aMa2210/WikiArt_VLM). Capture-pair validation is not established here. | Much greater artist breadth than our two cases. We estimate finite feature distributions and conditional prompt contrasts; VLM attribution accuracy does not validate our stylistic-variation construct. |
| [Asperti, arXiv:2608.25609v1](https://arxiv.org/html/2608.25609v1), §§3–5, 9–10 | Explains human/generated painting separation in CLIP using AI-WikiArt, AI-Pastiche and NGA. | CLIP PCA, image-processing controls, multiscale descriptors and gradient-based inversion investigate what moves images along separation directions. | Code/embeddings/features are linked in its availability statement. Examples described as visually subtle are not a formal human-panel validation in the inspected experiment. | Scatter separation alone is already adjacent prior work. Our contribution must be the prompt intervention and explicit proximity/variation decomposition; adding CLIP would not establish perception automatically. |
| [Kim et al., PNAS 123(30), e2517969123 (2026)](https://pubmed.ncbi.nlm.nih.gov/42497200/), retained published Methods | Art-historical context across 72,447 paintings. A separate image-to-image experiment samples 500 source paintings per century and contrasts future-context tokens with an empty prompt. | Stable Diffusion autoencoder and CLIP vectors distinguish formal/contextual information; historical alignment and generated-image year prediction are its targets. | [Code and processed data](https://github.com/aljinny/art-history) are reported available. This comparison does not establish an independent human perceptual validation of our metric. | Context-conditioned historical movement is different from our text-only artist-name intervention on a finite painter reference. Our 31 interpretable coordinates do not reproduce its learned contextual instrument. |
| Present controlled study plus declared post-result revision | Two selected painters, 24 shared briefs, named/free prompts across two paid routes and an OAuth service; 1,006 selected images and 70 references. | Frozen 31-feature distances, aggregate and within/between-brief variation, fixed conditional randomization tests, and bounded nuisance/metric diagnostics. | Numeric replay is available; ignored pixels require separate access. No human construct validation, verified capture pairs, or immutable service weights. | A reproducible case study of prompt-conditioned feature distributions. It does not establish universal style collapse, painter-oeuvre equality, perceptual inferiority, or a broad model leaderboard. |

## Version and access notes

AI-Pastiche's accessible February 2025 version is the basis for the 12-model,
73-prompt description above. Asperti's August 2026 paper describes a later
AI-Pastiche dataset with 19 generators and 1,474 images; do not silently substitute
that later inventory for the original survey's population. It also cites a
published version in *Big Data and Cognitive Computing* 9(9), 231 (2025),
[doi:10.3390/bdcc9090231](https://doi.org/10.3390/bdcc9090231). The publisher page
returned HTTP 429 during this check, so its complete final methods were not
freshly inspected. Bibliographic publication status and inspected methods version
must remain distinct.

Fresh access to Kim's PMC landing page produced an access challenge. Its official
[PubMed record](https://pubmed.ncbi.nlm.nih.gov/42497200/) and the
[authors' publication announcement](https://adsl.ssu.ac.kr/news/context-aware-multimodal-ai-art-evolution/index.html)
were accessible. Published Methods and the data-availability statement were
also inspected from the project's previously retained `tmp/pdfs/kim2026/published.txt`,
including preprocessing, A/C-vector encoding and the image-to-image experiment.
That retained text is an access aid, not newly collected evidence or a claim that
the full article was fetched again. No access challenge was circumvented.

The links described as dataset/code access are author-reported access routes;
this revision did not download those image datasets or establish bitwise replay
of their experiments. In particular, importing another study's images into our
reference frame would require its own declared exposure, rights, capture and
measurement scope.

## Claim-to-contribution rules for the revised paper

1. Lead with how the **tested prompt intervention changes empirical feature
   distributions**, then locate total variation within and between briefs.
   The experimental unit and the reference panel must appear with the claim.
2. Absolute original/generated detection is a domain-difference diagnostic. It
   is neither novel by itself nor a validated painter-style instrument; shape,
   capture, content and representation remain alternative explanations.
3. A controlled prompt comparison can survive limitations in absolute domain
   detection. Shared geometry in paid named/free arms helps that comparison,
   while prompt-induced content and processing effects remain part of the
   service outcome. No result isolates a hidden model mechanism.
4. Preservation of failures and reproducible numerics supports auditability.
   It does not supply scientific novelty, human agreement or a probability
   sample. Shared LLM reviews are not independent human peer review.
5. If human set-level judgments or new-reference replication are later completed,
   identify their new sampling frame and outcomes separately. The operational
   [validation plan](VALIDATION_PLAN.md) is currently future work, not results.

The defensible contribution is therefore a controlled, explicitly bounded
measurement study of proximity and variation under painter naming, including
the diagnostics that defeat stronger interpretations. Model recency, more
significant cells or a larger number of agreeing feature-space plots do not
substitute for that contribution.
