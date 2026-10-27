# Analysis contracts

These are retrospective reanalyses, not preregistrations. Analysis choices were made while
building on existing historical data. No customer intervention occurred.

## Experiment

Unit: one randomized customer. Expected allocation: equal thirds. Primary outcome: two-week
conversion; secondary outcomes: visit and spend. Estimand: each active email's mean outcome
minus no email, among prior purchasers. Six two-sided tests form one fixed alpha=.05 family.

Binary test: pooled two-proportion z; unpooled normal intervals. Spend: Welch t test and
intervals. Holm controls familywise error for p-values; Bonferroni gives conservative joint
intervals. Large-sample approximations and heavy-tailed spend remain limitations.

SRM alert threshold is .01; baseline standardized mean differences are descriptive. Passing
these does not certify instrumentation. Timing/exposure logs and unsubscribe outcomes are
absent. No daily stopping, novelty, exposure or CUPED result is reconstructed.

Prospective planning example: baseline .01, absolute MDE .003, 80% power, per-comparison
alpha=.05/6; normal approximation gives 30,590 customers per arm. These are illustrative
assumptions, not observed business targets or post-hoc power.

## Causal targeting

Contrast: Mens E-Mail versus No E-Mail. Exclude Womens before splitting. Outcome: visit;
known assignment probability conditional on this contrast: .5. Stratify on assignment only.
Train/validation/test: 60/20/20, seeds 2026 and 2027.

Predictors are recency, prior spend/history, prior mens/womens purchases, area class, newbie
and prior channel. Visit, conversion, spend, assignment and row ID never enter features.
Separate logistic/forest models per arm form two T-learner candidates. Validation Qini
chooses the family, which is refit on train+validation. The final test remains untouched
until scoring. Contact the highest 30% of test scores with stable deterministic ties.

IPW score: `Y*(T/p - (1-T)/(1-p))`. Multiply by frozen contact decisions and average over
all eligible customers. Qini is normalized cumulative IPW gain minus the straight random
targeting line, integrated over contact fraction. This does not reveal individual truth.

2,000 bootstrap resamples, seed 2026, estimate pointwise intervals conditional on the frozen
model/actions. The paired same-budget comparison averages `(decision-.3)*IPW_score`,
preserving each customer's shared outcome contribution. It compares against expected
random targeting at 30%, not a separately randomized realized campaign. Training and model
selection uncertainty are excluded. Identification assumes random assignment, consistency
and no interference. Visits are not sales or profit.

## Customer analytics

Raw grain: invoice line. Order grain: InvoiceNo after positive-sales cleaning. The real
extract includes one-minute variations within invoices; use earliest timestamp, reject
mixed-customer or cross-day collisions. Analyze complete months before December 2011.

Cohort means first observed positive purchase, not confirmed acquisition. Monthly repeat
rate is distinct purchasing customers divided by original observed cohort size. A complete
calendar grid creates observed zeros; future unobservable ages remain absent. Gross sales
include anonymous purchases; customer cohorts/RFM require IDs and cover a selected population.

RFM as of 1 December 2011 uses fixed illustrative thresholds for recency, frequency and spend.
It is descriptive, not CLV, a causal campaign result, or an optimized business rule.

## Forecasting

Target: Monday–Sunday weekly positive-sales revenue across countries, GBP. Incomplete
boundary weeks are excluded; missing covered days become zero recorded sales. Coverage
does not certify that missing days reflect genuine zero demand.

First 26 weeks train, next 12 choose by MAE, remaining 14 form final test. Horizon: one week.
Expanding-origin models use only prior actuals, including test weeks after they occur.
Candidates: last week, trailing four-week mean, Ridge with past lags/rolling means and trend.
Ridge alpha is fixed at 10. All final-test models are reported; there is no test tuning.
RMSE/WAPE are diagnostics. No annual seasonality, forecast interval or inventory savings
claim is supported by this short series.
