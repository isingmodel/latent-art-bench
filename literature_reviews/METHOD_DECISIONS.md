# Method decision ledger

Version: painter-feature-method-decisions/1.3

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
| MD-06 | Require connected joint common support across painter, source, content, medium, and phase | Pilot 2's source prediction and failed cross-source transfer show that marginal balance does not prevent joint aliasing | A different design with a demonstrated full-rank identification argument and equal or stronger overlap |
| MD-07 | Retain CIELAB distributions and adjacent transitions as core candidates | Interpretable lineage and clear perturbation behavior | Failure of color/reproduction SESOI or source transfer |
| MD-08 | Retain multiscale Fourier, edge/orientation, and wavelet profiles | Complementary evidence on spatial structure, with known controls | Instability to crop/resampling/source beyond preregistered tolerance |
| MD-09 | Retain tie-aware ordinal-pattern distributions, not only entropy/complexity scalars | Full distribution preserves diagnostic information and tie handling | Demonstrated redundancy and stable lossless reduction under external validation |
| MD-10 | Treat composition/saliency as secondary | Content, crop, and framing are major competing explanations | Strong content-matched transfer and human incremental validity |
| MD-11 | Reject physical-material and authentication claims from ordinary RGB | Catalog RGB does not identify pigment, binder, layering, topography, or underdrawing | Addition of calibrated technical-imaging modalities under a new protocol |
| MD-12 | Retain Kim A only as a named SD2-VAE appearance compatibility reconstruction/diagnostic | Forced-square stochastic latent mixes form, content, source, and codec; released code/artifacts are incomplete and A is not executable unchanged | Complete artifact recovery plus reproduction/content/source/human qualification; any repaired extractor remains an adaptation |
| MD-13 | Prefer posterior mean or repeated-draw integration for a prospective VAE coordinate | A deterministic seed makes a sampled latent repeatable but not uniquely meaningful | Evidence that another stochastic estimand improves validity and propagates variance |
| MD-14 | Keep Kim C/CLIP separate as contextual/semantic | It mixes iconography, content, text-like marks, attribution signals, and possible pretraining overlap | Strong discriminant evidence that a specified coordinate predicts painterly judgments beyond context |
| MD-15 | Keep CSD provisional | Artist retrieval is promising, but caption-derived supervision, source/content leakage, and released-weight discrepancy remain | Reconciled checkpoint plus all local validity gates |
| MD-16 | Use other learned spaces only for evaluator-family sensitivity | Representation training objective determines meaning; no universal learned style ground truth exists | Independent construct validation of a specific encoder |
| MD-17 | Fit transforms only inside real development folds | Prevent leakage and tuning toward generated outputs | None; this is a protocol invariant |
| MD-18 | Make leave-source-out and leave-content-family-out performance gating | Pooled accuracy can exploit nuisance shortcuts | Predeclared narrower source-specific or content-specific claim |
| MD-19 | Bind every matched hard neighbor to one panel-wide common support, subtract each frozen neighbor/cell SESOI before worst/tail aggregation, require both adjusted rules, and keep broad negatives diagnostic | One favorable neighbor, incompatible pairwise supports, or aggregation before heterogeneous thresholds can falsely establish specificity | None; panel composition, support, or SESOI may change only in a new protocol version |
| MD-20 | Treat within-painter coverage separately from target likeness | Prototype collapse can improve centroid distance or recognition | A validated statistic proven to decompose both without masking either |
| MD-21 | Use MMD or energy distance as candidate set discrepancies; keep raw FID nonprimary | Small-sample FID bias and encoder dependence are unsuitable for painter cells | Large-sample validation demonstrating calibrated painter-specific performance |
| MD-22 | Report precision and density, recall and coverage, contraction, and full panel-wide specificity margins | Generative distribution quality is multidimensional | Independently validated composite with prospectively justified weights |
| MD-23 | Retain named-versus-control movement as a prompt effect, not painter fidelity | It is causal under a frozen system but can be positive while outputs remain off-target | Absolute fit, panel-wide specificity, all four support metrics, coherence, and availability gates all pass |
| MD-24 | Use work- and rater-crossed human triplets plus separate attribute tasks | “Style” ratings conflate content and form; disagreement is informative | Pilot evidence supporting a more reliable task without changing construct |
| MD-25 | Separate expert and nonexpert populations | Expertise can change categorization and cue use | Measurement-invariance evidence supporting pooling |
| MD-26 | Preserve all refusals and failures as outcomes | Pilot 2's incomplete grid demonstrates nonrandom availability risk | None; analysis handling may vary only prospectively |
| MD-27 | Use work-clustered/crossed inference and exchangeability blocks | Pairs, crops, reproductions, and ratings are dependent | A sampling design with demonstrably independent higher-level units |
| MD-28 | Freeze method and thresholds before sealed external or generated images | Prevent outcome-guided measurement selection | None; violations require a new exploratory version |
| MD-29 | Do not create a universal weighted painter score | The evidence does not justify commensurate scales or weights | Independent construct study validating weights and error behavior |
| MD-30 | Limit claims to the eligible sampled oeuvre and declared domain | Museum/web availability, attribution, and digitization are selective | A broader, independently sampled confirmation frame |
| MD-31 | Standardize every painter distribution over frozen common-support weights | Unqualified painter distributions change with the convenience mixture of content, medium, phase, and capture source | Exact matched conditional inference with the same target weights and no extrapolation |
| MD-32 | Require a connected provider/capture incidence matrix and rank audit | Provider, capture, delivery, and processing effects cannot be separated when uniquely nested or rank deficient | A validated alternative design that identifies every requested variance component |
| MD-33 | Control the primary winner-selection claim experiment-wide | Family-local adjustment does not cover selection among families, coordinates, scales, encoders, painters, and endpoints | A prospectively justified omnibus or closed-testing design with equal strong error control |
| MD-34 | Make source-level nested method selection binding | Refitting a coordinate inside a leave-source fold does not undo selection after seeing every source | Explicit limitation to already-seen source workflows |
| MD-35 | Gate human claims on blinded, unfamiliar works | Attribution cues, signatures, source interfaces, and recognition can validate familiarity or stereotype instead of painterly manner | A validated task showing those cues cannot affect the stated construct |
| MD-36 | Require an unopened institution/capture workflow for a core external claim | Changing content or period alone preserves a source shortcut | A claim explicitly limited to the already-seen workflow domain |
| MD-37 | Freeze denominators, cell minima, and MNAR sensitivity | Rights, metadata, and processing exclusions can create a selectively easy complete-case corpus | A design with complete observation of the registered frame |
| MD-38 | Make any future painter-fidelity claim conjunctive | Relative prompt movement can be positive while absolute fit, panel-wide specificity, precision, density, recall, coverage, content coherence, or availability fails | A separately validated composite that cannot mask a failed component |
| MD-39 | Preserve shared controls and real references as joint resampling clusters | Reusing one control across painter contrasts creates dependence that painter-wise resampling would ignore | Independently generated and explicitly indexed controls for every target |

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
3. connected common-support and frozen target-weight tables;
4. independent-reproduction incidence matrix and design-rank audit;
5. feature-card formulas, exact available artifacts, and adaptation labels;
6. perturbation SESOIs and terminal decision thresholds;
7. precision/power simulations and hard per-cell minima;
8. source-nested development, qualification, blinded human-task, and unopened-workflow external
   partitions;
9. experiment-wide closed-testing hierarchy;
10. frozen denominators, missingness scenarios, and terminal transport rules; and
11. rights, storage, and redistributability.

Until that document is reviewed and committed, external-holdout access, feature extraction,
generation transport, and image generation remain closed.
