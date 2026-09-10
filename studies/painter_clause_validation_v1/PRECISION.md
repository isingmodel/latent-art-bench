# Prospective clause allocation: offline precision and numerical qualification

This record contains no new image outcomes or observed no-palette generic distribution.
The historical proxy informed the fixed 288-output allocation before collection.
The question was selected after earlier results; study design was not outcome-blind.
Implementation and assessment are by maintainer-run LLM agents, not independent humans.

Recorded source commit: `6dd1e80b7d998f39809bfa354c8f52b7dd439595`.
Input/source hashes are in precision.json.
Reproduce with `python -m latent_art_bench.painter_clause_validation_v1.precision` in a
committed source checkout before these create-once outputs exist. Final execution refuses
changed/untracked bound source, staged changes, symlinks, or existing output paths.

## Historical proxy precision

Seed 120260910; 250 trials per scenario.
There are nine scenarios for each of three allocations.
Only original primary512 OAuth vectors are used. The two historical free allocations
provide six repeats per scene with the same free prompt; named means use three repeats.
Estimated scene means are held fixed. Centered free/named residuals are rescaled by
sqrt(6/5) and sqrt(3/2), respectively, so their empirical covariance equals the unbiased
sample covariance. Named-noise pooling centers within painter first.

Generic means interpolate from pooled free means to the two-painter average named mean
at alpha 0, .5 and 1. Generic residuals use pooled free, pooled within-painter named, or
1.5 times pooled-free residuals. One G draw is shared across both painter contrasts;
each endpoint retains its own fixed reference panel and content masses.

| Scenes | Repeats | Four-arm outputs | Monet SD range | Cezanne SD range |
| --- | --- | --- | --- | --- |
| 12 | 3 | 144 | 0.149475–0.266775 | 0.133636–0.200511 |
| 24 | 3 | 288 | 0.102835–0.150203 | 0.088634–0.125109 |
| 24 | 4 | 384 | 0.093402–0.136339 | 0.074883–0.104309 |

The selected 24 x 3 x 4 = 288 allocation preserves 24 new scenes while avoiding
the 96 extra outputs of a fourth repeat. The 144-output alternative halves the scene
panel. This comparison does not establish power, a meaningful-effect threshold, or
an equivalence margin; favorable scenario means do not select the allocation.

The 12-scene comparison uses this single balanced historical subset:
`built01, built05, built06, built07, land03, land06, land07, land08, water03, water04, water06, water07`.

| Scenes/repeats | Generic alpha | Generic noise | Monet mean / SD | Cezanne mean / SD |
| --- | --- | --- | --- | --- |
| 12/3 | 0 | free | -0.129981 / 0.187022 | -0.131054 / 0.154290 |
| 12/3 | 0 | named | -0.186966 / 0.155445 | -0.104779 / 0.140674 |
| 12/3 | 0 | free_x1.5 | +0.058532 / 0.266775 | +0.039118 / 0.200511 |
| 12/3 | 0.5 | free | +0.494474 / 0.161708 | +0.136185 / 0.133636 |
| 12/3 | 0.5 | named | +0.457408 / 0.150693 | +0.138651 / 0.146428 |
| 12/3 | 0.5 | free_x1.5 | +0.722895 / 0.222423 | +0.306987 / 0.163772 |
| 12/3 | 1 | free | +0.601580 / 0.149694 | -0.308081 / 0.143310 |
| 12/3 | 1 | named | +0.548868 / 0.149475 | -0.334309 / 0.147674 |
| 12/3 | 1 | free_x1.5 | +0.872052 / 0.181136 | -0.087008 / 0.164027 |
| 24/3 | 0 | free | -0.152878 / 0.125090 | -0.081584 / 0.089103 |
| 24/3 | 0 | named | -0.206479 / 0.107586 | -0.091668 / 0.092322 |
| 24/3 | 0 | free_x1.5 | -0.024814 / 0.150203 | +0.026623 / 0.125109 |
| 24/3 | 0.5 | free | +0.358539 / 0.108650 | +0.137611 / 0.095544 |
| 24/3 | 0.5 | named | +0.321567 / 0.107271 | +0.141546 / 0.088634 |
| 24/3 | 0.5 | free_x1.5 | +0.526506 / 0.132002 | +0.274000 / 0.115595 |
| 24/3 | 1 | free | +0.352264 / 0.103184 | -0.351382 / 0.092921 |
| 24/3 | 1 | named | +0.321608 / 0.102835 | -0.350357 / 0.091578 |
| 24/3 | 1 | free_x1.5 | +0.564302 / 0.110495 | -0.131731 / 0.109969 |
| 24/4 | 0 | free | -0.166944 / 0.096594 | -0.085466 / 0.082226 |
| 24/4 | 0 | named | -0.202163 / 0.105170 | -0.094892 / 0.079659 |
| 24/4 | 0 | free_x1.5 | -0.014879 / 0.136339 | +0.032420 / 0.104309 |
| 24/4 | 0.5 | free | +0.352722 / 0.093402 | +0.141972 / 0.078874 |
| 24/4 | 0.5 | named | +0.318585 / 0.101235 | +0.145174 / 0.074883 |
| 24/4 | 0.5 | free_x1.5 | +0.533442 / 0.115723 | +0.289408 / 0.098212 |
| 24/4 | 1 | free | +0.355838 / 0.094896 | -0.348985 / 0.083277 |
| 24/4 | 1 | named | +0.312163 / 0.102442 | -0.348638 / 0.080581 |
| 24/4 | 1 | free_x1.5 | +0.593343 / 0.107328 | -0.134485 / 0.089326 |

The 250-trial SD estimates have Monte Carlo noise (about 4.5% relative standard
error under a normal-sampling approximation). Their spread across scenarios is not
a confidence interval. Historical means are themselves noisy; six/three residual
samples do not characterize tails or all 31-dimensional variation. These laws do not
identify the new generic arm, new-scene variation, service drift or interference.
Scenario mean effects are reported transparently and are not anticipated new effects.

## Artificial four-position conditional randomization qualification

Seed 120260911; 5000 complete 72-block assignments per case;
999 Monte Carlo sign draws per endpoint in this bounded check.
The planned primary analysis instead uses 99999 draws.
Both use independent pair swaps, conservative absolute ties and the plus-one rule.
The two p-values receive Holm correction at .05 with their shared generic outcomes
preserved. Other arm positions are conditioned on for each endpoint. All position
outcomes are fixed before assigning independently randomized four-arm positions.

Position drift and a rare large position outcome test nonconstant coefficients.
Two partial-null cases shift just one named arm; only rejection of the remaining
true null counts as a family error. The Wilson intervals describe artificial Monte
Carlo error, not uncertainty about service behavior or any image effect.

| Artificial case | True-null family errors / trials | Rate | Wilson 95% | Pass |
| --- | --- | --- | --- | --- |
| constant | 245 / 5000 | 0.04900 | [0.04336, 0.05534] | True |
| position_drift | 243 / 5000 | 0.04860 | [0.04298, 0.05491] | True |
| rare_large | 236 / 5000 | 0.04720 | [0.04166, 0.05343] | True |
| monet_null_cezanne_shift | 214 / 5000 | 0.04280 | [0.03753, 0.04877] | True |
| cezanne_null_monet_shift | 223 / 5000 | 0.04460 | [0.03922, 0.05068] | True |

Prespecified numerical criterion: every upper Wilson bound <= 0.065.
Numerical criterion satisfied: **True**.
Exact small four-position tests also verify the weighted-energy sign identity, and
tests compare the coefficients and Holm rule with the existing primary primitives.
This artificial check qualifies neither no-interference nor sharp-null availability
for OAuth. Treatment-dependent duration, retries, delivery and carryover remain
material service limitations. A fixed new scene panel is not a random population
sample. No effect confidence interval, map-label test or new Q inference is added.
