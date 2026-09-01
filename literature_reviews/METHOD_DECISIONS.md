# Method decision ledger

Version: painter-feature-method-decisions/1.0

Status: literature-based prospective decisions; no empirical execution authorization

## Decision rule

Each decision records the evidence-supported action, its rationale, and the observation that
could force revision. “Retain” means retain as a candidate for prospective qualification, not
declare valid.

| ID | Decision | Rationale | Revision trigger |
|---|---|---|---|
| MD-01 | Define the painter feature as a conditional distribution across eligible physical works | Painter practice varies across works, phases, genres, and media; a vector or centroid cannot represent coverage | A validated alternative latent-variable model with equal or better nuisance, coverage, and interpretability evidence |
| MD-02 | Keep painter as the target, following Pilot 2 | The research question concerns painter-associated practice, not era or movement | User-approved change in scientific question |
| MD-03 | Preserve Pilots 0–3 as frozen historical evidence | Negative, incomplete, and terminal results constrain the redesign | None within this reboot; a new version may cite but not mutate them |
| MD-04 | Use the physical work as the primary real-image unit | Files, derivatives, crops, and patches are nested in works | A different estimand explicitly targeting digital derivatives |
| MD-05 | Require independent reproductions of a work | Same-capture derivatives cannot estimate capture/source variation | A claim limited explicitly to one digitization workflow |
| MD-06 | Cross painters with multiple sources and content strata | Pilot 2's source prediction and failed cross-source transfer show aliasing risk | Empirical simulation supporting a different balanced design with equal identification |
| MD-07 | Retain CIELAB distributions and adjacent transitions as core candidates | Interpretable lineage and clear perturbation behavior | Failure of color/reproduction SESOI or source transfer |
| MD-08 | Retain multiscale Fourier, edge/orientation, and wavelet profiles | Complementary evidence on spatial structure, with known controls | Instability to crop/resampling/source beyond preregistered tolerance |
| MD-09 | Retain tie-aware ordinal-pattern distributions, not only entropy/complexity scalars | Full distribution preserves diagnostic information and tie handling | Demonstrated redundancy and stable lossless reduction under external validation |
| MD-10 | Treat composition/saliency as secondary | Content, crop, and framing are major competing explanations | Strong content-matched transfer and human incremental validity |
| MD-11 | Reject physical-material and authentication claims from ordinary RGB | Catalog RGB does not identify pigment, binder, layering, topography, or underdrawing | Addition of calibrated technical-imaging modalities under a new protocol |
| MD-12 | Retain Kim A only as a named SD2-VAE appearance replication/diagnostic | Forced-square stochastic latent mixes form, content, source, and codec; released code/artifacts are incomplete | Exact artifact reconciliation plus reproduction/content/source/human qualification |
| MD-13 | Prefer posterior mean or repeated-draw integration for a prospective VAE coordinate | A deterministic seed makes a sampled latent repeatable but not uniquely meaningful | Evidence that another stochastic estimand improves validity and propagates variance |
| MD-14 | Keep Kim C/CLIP separate as contextual/semantic | It mixes iconography, content, text-like marks, attribution signals, and possible pretraining overlap | Strong discriminant evidence that a specified coordinate predicts painterly judgments beyond context |
| MD-15 | Keep CSD provisional | Artist retrieval is promising, but caption-derived supervision, source/content leakage, and released-weight discrepancy remain | Reconciled checkpoint plus all local validity gates |
| MD-16 | Use other learned spaces only for evaluator-family sensitivity | Representation training objective determines meaning; no universal learned style ground truth exists | Independent construct validation of a specific encoder |
| MD-17 | Fit transforms only inside real development folds | Prevent leakage and tuning toward generated outputs | None; this is a protocol invariant |
| MD-18 | Make leave-source-out and leave-content-family-out performance gating | Pooled accuracy can exploit nuisance shortcuts | Predeclared narrower source-specific or content-specific claim |
| MD-19 | Include matched hard neighbors and broad negatives | One favorable neighbor cannot establish specificity | None; panel composition may change only in a new protocol version |
| MD-20 | Treat within-painter coverage separately from target likeness | Prototype collapse can improve centroid distance or recognition | A validated statistic proven to decompose both without masking either |
| MD-21 | Use MMD or energy distance as candidate set discrepancies; keep raw FID nonprimary | Small-sample FID bias and encoder dependence are unsuitable for painter cells | Large-sample validation demonstrating calibrated painter-specific performance |
| MD-22 | Report precision/density, recall/coverage, contraction, and full specificity margins | Generative distribution quality is multidimensional | Independently validated composite with prospectively justified weights |
| MD-23 | Retain named-versus-control movement as a prompt effect, not painter fidelity | It is causal under a frozen system but can be positive while outputs remain off-target | Additional absolute fit, specificity, and coverage gates all pass |
| MD-24 | Use work- and rater-crossed human triplets plus separate attribute tasks | “Style” ratings conflate content and form; disagreement is informative | Pilot evidence supporting a more reliable task without changing construct |
| MD-25 | Separate expert and nonexpert populations | Expertise can change categorization and cue use | Measurement-invariance evidence supporting pooling |
| MD-26 | Preserve all refusals and failures as outcomes | Pilot 2's incomplete grid demonstrates nonrandom availability risk | None; analysis handling may vary only prospectively |
| MD-27 | Use work-clustered/crossed inference and exchangeability blocks | Pairs, crops, reproductions, and ratings are dependent | A sampling design with demonstrably independent higher-level units |
| MD-28 | Freeze method and thresholds before sealed external or generated images | Prevent outcome-guided measurement selection | None; violations require a new exploratory version |
| MD-29 | Do not create a universal weighted painter score | The evidence does not justify commensurate scales or weights | Independent construct study validating weights and error behavior |
| MD-30 | Limit claims to the eligible sampled oeuvre and declared domain | Museum/web availability, attribution, and digitization are selective | A broader, independently sampled confirmation frame |

## Candidate disposition vocabulary

Every coordinate receives one of the following after qualification:

- qualified_core: passes all gates required for a painter-associated coordinate;
- qualified_domain_limited: passes only for a declared source, phase, content, or medium domain;
- reproduction_associated: repeatable across the tested reproduction domain but not
  painter-specific under transfer;
- digital_derivative: stable only within derivatives of one capture;
- diagnostic_only: useful for shortcut, semantic, or evaluator-family sensitivity;
- replication_only: retained to reproduce a paper under its native assumptions;
- failed: does not meet its prospective gate; or
- not_executed: required inputs or artifacts were unavailable.

No failed candidate is silently removed from the report.

## Stop conditions before empirical execution

The literature review alone does not authorize acquisition or measurement. A frozen execution
protocol must still specify:

1. target painter set and historically defensible comparison painters;
2. eligible works and attribution policy;
3. crossed source/content/phase/medium sampling table;
4. independent-reproduction panel;
5. feature-card formulas and exact artifacts;
6. perturbation SESOIs and decision thresholds;
7. precision/power simulations;
8. development, qualification, human-task, and external partitions;
9. missingness and terminal transport rules; and
10. rights, storage, and redistributability.

Until that document is reviewed and committed, external-holdout access, feature extraction,
generation transport, and image generation remain closed.
